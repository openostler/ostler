# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The machine-readable API contracts in ``api/`` (ADR-0017): OpenAPI 3.1.1 and AsyncAPI 3.0.

- Every route ``web/server.py`` handles is in ``api/openapi.yaml`` and every documented
  route exists. Routes are read from the server's source (static analysis of the string
  literals ``_Handler`` compares its ``path`` local with), so a new ``elif path == …``
  fails here until it is documented. Admin gating is cross-checked the same way.
- The API consistency rules (specs/2026-10-06-api-consistency-design.md §7): a query
  string never 404s, every error body is the ``{ok: false, error, code?}`` envelope,
  every documented status is in the status table, unknown browser pages get the app
  shell.
- ``api/openapi.yaml`` passes ``openapi-spec-validator``; ``api/asyncapi.yaml`` is checked
  structurally (there is no light AsyncAPI validator on PyPI).
- The committed UI fixtures (real server responses, ``ui/src/api/fixtures/``) validate
  against the documented response schemas (JSON Schema 2020-12).

Needs the dev extra (pyyaml, openapi-spec-validator, jsonschema); no pack, no hardware.
"""
from __future__ import annotations

import ast
import base64
import http.client
import json
import threading
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "src" / "openostler" / "web" / "server.py"
OPENAPI = ROOT / "api" / "openapi.yaml"
ASYNCAPI = ROOT / "api" / "asyncapi.yaml"
FIXTURES = ROOT / "ui" / "src" / "api" / "fixtures"

METHODS = ("get", "post", "patch", "delete")
ACCESS = {"public", "admin"}
PUBLIC_MODE = {"open", "filtered", "refused", "hidden", "partial"}

# The prefix routes ``_Handler`` dispatches to a helper that parses the rest of the path
# itself: (method, prefix) → the helper whose literals name the sub-routes.
SUBROUTE_HELPERS = {
    ("get", "/sessions/"): "_sessions_get",
    ("post", "/sessions/"): "_sessions_post",
    ("patch", "/sessions/"): "do_PATCH",
    ("delete", "/sessions/"): "do_DELETE",
}
# Methods whose helper also serves the bare ``/sessions/<id>`` (``not rest``).
BARE_SESSION = {"get", "patch"}

# Fixture → (path, method, status) of the response it is a real sample of. Mirrors
# ui/src/api/schemas.test.ts (SCHEMA_FOR) and tests/test_ui_contract.py (CASES).
FIXTURE_ROUTES = {
    "snapshot": ("/snapshot", "get", "200"),
    "pack": ("/pack", "get", "200"),
    "version": ("/version", "get", "200"),
    "fields-td5": ("/fields", "get", "200"),
    "fields-slabs": ("/fields", "get", "200"),
    "faults-airbag": ("/faults", "get", "200"),
    "map": ("/map", "get", "200"),
    "catalog-td5": ("/catalog", "get", "200"),
    "catalog-bcu": ("/catalog", "get", "200"),
    "catalog-modules": ("/catalog", "get", "200"),
    "sessions": ("/sessions", "get", "200"),
    "session-histogram": ("/sessions/histogram", "get", "200"),
    "session-meta": ("/sessions/{id}", "get", "200"),
    "session-data": ("/sessions/{id}/data", "get", "200"),
    "session-events": ("/sessions/{id}/events", "get", "200"),
    "notes": ("/sessions/{id}/notes", "get", "200"),
    "sniff": ("/sniff", "get", "200"),
    "docs": ("/docs", "get", "200"),
    "community": ("/community", "get", "200"),
    "community-consent": ("/community/consent", "post", "200"),
    "community-queued": ("/community/contribute", "post", "202"),
    "command-ok": ("/command", "post", "200"),
    "command-error": ("/command", "post", "400"),
    "command-not-recording": ("/command", "post", "409"),
    "error-not-found": ("/{file}", "get", "404"),
    "csv-start": ("/command", "post", "200"),
    "csv-stop": ("/command", "post", "200"),
    "read-all-faults": ("/command", "post", "200"),
    "automap": ("/automap", "post", "200"),
    "capture": ("/capture", "post", "200"),
    "captures": ("/captures", "get", "200"),
}


# ---------------------------------------------------------------- loading ---------------- #
def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def openapi() -> dict:
    return _load(OPENAPI)


@pytest.fixture(scope="module")
def asyncapi() -> dict:
    return _load(ASYNCAPI)


def _resolve(doc: dict, node):
    """Follow local ``$ref``s (``#/…``) until a non-reference node."""
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        assert ref.startswith("#/"), f"unexpected non-local $ref {ref!r}"
        node = doc
        for part in ref[2:].split("/"):
            node = node[part.replace("~1", "/").replace("~0", "~")]
    return node


def _operations(doc: dict):
    """(path, method, operation) for every documented operation (path-item refs resolved)."""
    for path, item in doc["paths"].items():
        item = _resolve(doc, item)
        for method in METHODS:
            if method in item:
                yield path, method, item[method]


# ---------------------------------------------------------------- server routes ---------- #
def _handler() -> ast.ClassDef:
    tree = ast.parse(SERVER.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "_Handler":
            return node
    raise AssertionError("class _Handler not found in web/server.py")


def _method(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for node in cls.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"_Handler.{name} not found")


def _is_self_path(node) -> bool:
    return (isinstance(node, ast.Attribute) and node.attr == "path"
            and isinstance(node.value, ast.Name) and node.value.id == "self")


def _is_route_path(node) -> bool:
    """The ``path`` local every ``do_*`` routes on (``path = self._path()``)."""
    return isinstance(node, ast.Name) and node.id == "path"


def _strings(node) -> "list[str]":
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [s for e in node.elts for s in _strings(e)]
    return []


def _path_tests(test) -> "tuple[list[str], list[str]]":
    """From an ``if`` test: ([exact paths], [startswith prefixes])."""
    exact, prefixes = [], []
    for node in ast.walk(test):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(
                node.ops[0], (ast.Eq, ast.In)):
            if _is_route_path(node.left):
                exact += _strings(node.comparators[0])
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "startswith" and _is_route_path(node.func.value)):
            prefixes += [s for a in node.args for s in _strings(a)]
    return exact, prefixes


def _calls(nodes, name: str) -> bool:
    """Whether any statement in ``nodes`` calls ``self.<name>(…)``."""
    for stmt in nodes:
        for node in ast.walk(stmt):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == name and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"):
                return True
    return False


def _server_routes():
    """→ (exact, prefixes): ``exact[(method, path)] = {admin}``;
    ``prefixes[(method, prefix)] = admin``. Read from the ``if`` chains of ``do_*``."""
    cls = _handler()
    exact: "dict[tuple[str, str], dict]" = {}
    prefixes: "dict[tuple[str, str], bool]" = {}
    for method in METHODS:
        fn = _method(cls, f"do_{method.upper()}")
        for node in ast.walk(fn):
            if isinstance(node, ast.If):
                paths, pfx = _path_tests(node.test)
                admin = _calls(node.body, "_require_admin")
                for path in paths:
                    exact[(method, path)] = {"admin": admin}
                for p in pfx:
                    prefixes[(method, p)] = admin
            elif isinstance(node, ast.IfExp):  # e.g. the /assets/ cache header
                for p in _path_tests(node.test)[1]:
                    prefixes.setdefault((method, p), False)
        if method in ("patch", "delete"):
            # dispatched only through _session_parts, which takes /sessions/<id>/… paths
            assert _calls(fn.body, "_session_parts"), f"do_{method.upper()} changed shape"
            prefixes[(method, "/sessions/")] = False
    return exact, prefixes


def _subroute_literals(helper: str) -> "set[str]":
    """The path-part names a helper compares with (``rest[0] == "notes"``, ``parts ==
    ["histogram"]``, ``what == "audio"`` …)."""
    fn = _method(_handler(), helper)
    out: "set[str]" = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Compare) and not _is_route_path(node.left):
            for side in [node.left, *node.comparators]:
                out |= {s for s in _strings(side) if s and "/" not in s}
    return out


def _segment(path: str, prefix: str) -> str:
    """``/sessions/{id}/notes/{nid}`` → ``notes``; ``/sessions/histogram`` →
    ``histogram``; ``/sessions/{id}`` → ``""``."""
    parts = path[len(prefix):].split("/")
    if not parts[0].startswith("{"):
        return parts[0]
    return parts[1] if len(parts) > 1 else ""


def test_route_extraction_sees_the_server():
    """Guard the static analysis itself: known routes of each kind are found."""
    exact, prefixes = _server_routes()
    assert exact[("get", "/snapshot")] == {"admin": False}
    assert exact[("get", "/map")] == {"admin": True}
    assert exact[("get", "/admin")]["admin"] is True
    assert ("post", "/notes/live") in exact and ("post", "/command") in exact
    assert ("get", "/sessions/") in prefixes and ("post", "/sessions/") in prefixes
    assert ("get", "/assets/") in prefixes
    assert {"notes", "audio", "accel", "accel_cal"} <= _subroute_literals("_sessions_post")
    assert len(exact) > 30


def test_every_server_route_is_documented(openapi):
    exact, prefixes = _server_routes()
    documented = {(p, m) for p, m, _ in _operations(openapi)}
    missing = sorted(f"{m.upper()} {p}" for (m, p) in exact if (p, m) not in documented)
    for (m, prefix) in prefixes:
        if not any(p.startswith(prefix) and mm == m for p, mm in documented):
            missing.append(f"{m.upper()} {prefix}…")
    assert not missing, "routes the server handles but api/openapi.yaml lacks:\n  " + \
        "\n  ".join(missing)


def test_every_session_subroute_is_documented_and_real(openapi):
    documented = {(p, m) for p, m, _ in _operations(openapi)}
    for (method, prefix), helper in SUBROUTE_HELPERS.items():
        code = _subroute_literals(helper) | ({""} if method in BARE_SESSION else set())
        doc = {_segment(p, prefix) for p, m in documented if m == method and p.startswith(prefix)}
        assert doc == code, (
            f"{method.upper()} {prefix}…: server {sorted(code)} vs api/openapi.yaml {sorted(doc)}")


def test_every_documented_route_exists(openapi):
    exact, prefixes = _server_routes()
    has_static = any(  # do_GET falls back to _static_file(self.path)
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_static_file"
        for n in ast.walk(_method(_handler(), "do_GET")))
    extra = []
    for path, method, op in _operations(openapi):
        if (method, path) in exact:
            continue
        if any(m == method and path.startswith(p) for (m, p) in prefixes):
            continue
        if method == "get" and op.get("x-ostler-route") == "static" and has_static:
            continue
        extra.append(f"{method.upper()} {path}")
    assert not extra, "api/openapi.yaml documents routes the server lacks:\n  " + \
        "\n  ".join(extra)


def test_admin_gating_matches_the_server(openapi):
    exact, prefixes = _server_routes()
    wrong = []
    for path, method, op in _operations(openapi):
        code = exact.get((method, path))
        if code is None:
            code_admin = next((a for (m, p), a in prefixes.items()
                               if m == method and path.startswith(p)), False)
        else:
            code_admin = code["admin"]
        doc_admin = op.get("x-ostler-access") == "admin"
        sec = any("adminBasic" in s for s in op.get("security", []))
        if doc_admin != code_admin or sec != code_admin:
            wrong.append(f"{method.upper()} {path}: server admin={code_admin}, "
                         f"x-ostler-access={op.get('x-ostler-access')}, security={sec}")
    assert not wrong, "\n  ".join(["admin gating differs:", *wrong])


def test_no_route_matches_the_raw_request_path(openapi):
    """Spec §3: ``do_*`` route on ``path`` (no query string), never on ``self.path``, so a
    query string cannot 404; and no operation is marked as refusing one."""
    cls = _handler()
    raw = []
    for method in METHODS:
        fn = _method(cls, f"do_{method.upper()}")
        for node in ast.walk(fn):
            if isinstance(node, ast.Compare) and any(
                    _is_self_path(n) for n in [node.left, *node.comparators]):
                raw.append(f"do_{method.upper()} line {node.lineno}: compares self.path")
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and _is_self_path(node.func.value)):
                raw.append(f"do_{method.upper()} line {node.lineno}: self.path.{node.func.attr}")
    assert not raw, "\n  ".join(raw)
    marked = [f"{m.upper()} {p}" for p, m, op in _operations(openapi)
              if "x-ostler-query-string" in op]
    assert not marked, f"x-ostler-query-string is gone (spec §3): {marked}"


# ---------------------------------------------------------------- the OpenAPI document --- #
def test_openapi_is_valid(openapi):
    validator = pytest.importorskip("openapi_spec_validator")
    validator.validate(openapi)
    assert openapi["openapi"] == "3.1.1"


def test_openapi_info(openapi):
    from openostler import __version__

    info = openapi["info"]
    assert info["title"] == "Ostler"
    assert info["license"]["identifier"] == "AGPL-3.0-or-later"
    assert info["version"] == __version__, "bump api/openapi.yaml info.version with the release"


def test_every_operation_is_annotated(openapi):
    bad = []
    for path, method, op in _operations(openapi):
        where = f"{method.upper()} {path}"
        if op.get("x-ostler-access") not in ACCESS:
            bad.append(f"{where}: x-ostler-access")
        if op.get("x-ostler-public-mode") not in PUBLIC_MODE:
            bad.append(f"{where}: x-ostler-public-mode")
        codes = set(op.get("responses", {}))
        if op.get("x-ostler-access") == "admin" and "401" not in codes:
            bad.append(f"{where}: admin route without a 401 response")
        if op.get("x-ostler-public-mode") == "refused" and "403" not in codes:
            bad.append(f"{where}: refused in public mode without a 403 response")
        if not any(c.startswith("2") for c in codes):
            bad.append(f"{where}: no success response")
    assert not bad, "\n  ".join(bad)


def test_wire_conventions_are_documented(openapi):
    comp = openapi["components"]
    conv = comp["x-ostler-wire-conventions"]
    for key in ("timestamps", "units", "geo", "vehicle-id", "errors"):
        assert conv.get(key), key
    schemas = comp["schemas"]
    for name in ("Rfc3339Utc", "VssUnit", "GeoJsonPosition", "GeoJsonLineString", "Vid",
                 "ErrorReply"):
        assert name in schemas, name
    assert schemas["SessionMeta"]["properties"]["vid"] == {"$ref": "#/components/schemas/Vid"}
    assert "vid" not in schemas["SessionMeta"]["required"]


# ---------------------------------------------------------------- fixtures vs schemas ---- #
def _validator(doc: dict, pointer: str):
    jsonschema = pytest.importorskip("jsonschema")
    referencing = pytest.importorskip("referencing")
    from referencing.jsonschema import DRAFT202012

    uri = "urn:ostler:openapi"
    registry = referencing.Registry().with_resource(
        uri, referencing.Resource(contents=doc, specification=DRAFT202012))
    return jsonschema.Draft202012Validator(
        {"$ref": f"{uri}#{pointer}"}, registry=registry,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)


def _response_pointer(doc: dict, path: str, method: str, status: str) -> str:
    item = doc["paths"][path]
    base = "/paths/" + path.replace("~", "~0").replace("/", "~1")
    if "$ref" in item:
        base = item["$ref"][1:]
        item = _resolve(doc, item)
    resp = item[method]["responses"][status]
    ptr = f"{base}/{method}/responses/{status}"
    if "$ref" in resp:
        ptr = resp["$ref"][1:]
        resp = _resolve(doc, resp)
    assert "application/json" in resp["content"], f"{method} {path} {status} is not JSON"
    return f"{ptr}/content/application~1json/schema"


def test_every_fixture_is_mapped():
    names = {p.stem for p in FIXTURES.glob("*.json")}
    assert names == set(FIXTURE_ROUTES), (
        f"unmapped fixtures {sorted(names - set(FIXTURE_ROUTES))}, "
        f"stale entries {sorted(set(FIXTURE_ROUTES) - names)}")


@pytest.mark.parametrize("name", sorted(FIXTURE_ROUTES))
def test_fixture_matches_its_response_schema(openapi, name):
    path, method, status = FIXTURE_ROUTES[name]
    v = _validator(openapi, _response_pointer(openapi, path, method, status))
    data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    errors = sorted(v.iter_errors(data), key=lambda e: list(e.absolute_path))
    assert not errors, f"{name}.json vs {method.upper()} {path} {status}:\n  " + "\n  ".join(
        f"{'/'.join(map(str, e.absolute_path)) or '$'}: {e.message[:200]}" for e in errors[:10])


def test_schemas_reject_a_wrong_shape(openapi):
    """The fixture check has teeth: a broken snapshot and session fail."""
    snap = _validator(openapi, _response_pointer(openapi, "/snapshot", "get", "200"))
    assert list(snap.iter_errors({"signals": {}}))                     # no status
    assert list(snap.iter_errors({"status": "connected", "signals": {"rpm": {"v": "x"}}}))
    meta = json.loads((FIXTURES / "session-meta.json").read_text(encoding="utf-8"))
    sess = _validator(openapi, _response_pointer(openapi, "/sessions/{id}", "get", "200"))
    assert not list(sess.iter_errors(meta))
    assert list(sess.iter_errors({**meta, "start_utc": "2026-10-05 09:00"}))  # not RFC 3339 Z
    assert not list(sess.iter_errors({**meta, "vid": "v1"}))
    assert not list(sess.iter_errors({**meta, "vid": None}))


# ---------------------------------------------------------------- AsyncAPI --------------- #
def test_asyncapi_structure(asyncapi):
    from openostler import __version__

    assert asyncapi["asyncapi"] == "3.0.0"
    for key in ("info", "channels", "operations", "components"):
        assert key in asyncapi, key
    assert asyncapi["info"]["title"] == "Ostler"
    assert asyncapi["info"]["version"] == __version__
    assert asyncapi["info"]["license"]["name"] == "AGPL-3.0-or-later"
    for name, op in asyncapi["operations"].items():
        assert op["action"] in ("send", "receive"), name
        assert op["channel"]["$ref"].startswith("#/channels/"), name
        chan = op["channel"]["$ref"].split("/")[-1]
        assert chan in asyncapi["channels"], name
        for msg in op.get("messages", []):
            assert msg["$ref"].startswith(f"#/channels/{chan}/messages/"), name
            assert msg["$ref"].split("/")[-1] in asyncapi["channels"][chan]["messages"], name


def test_asyncapi_documents_the_sse_route(asyncapi, openapi):
    """The event channel is the route that streams (``_sse``), and it is in openapi too."""
    exact, _ = _server_routes()
    fn = _method(_handler(), "do_GET")
    sse = None
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and node.body and _calls(node.body[:1], "_sse"):
            sse = _path_tests(node.test)[0][0]
    assert sse, "the SSE route was not found in do_GET"
    addresses = {c["address"] for c in asyncapi["channels"].values()}
    assert sse in addresses
    resp = openapi["paths"][sse]["get"]["responses"]["200"]["content"]
    assert "text/event-stream" in resp


def test_asyncapi_payload_is_the_openapi_snapshot(asyncapi, openapi):
    msgs = asyncapi["components"]["messages"]
    ref = msgs["snapshot"]["payload"]["$ref"]
    file, _, pointer = ref.partition("#")
    assert (ASYNCAPI.parent / file).resolve() == OPENAPI.resolve()
    v = _validator(openapi, pointer)
    snap = json.loads((FIXTURES / "snapshot.json").read_text(encoding="utf-8"))
    assert not list(v.iter_errors(snap))
    for ex in msgs["snapshot"].get("examples", []):
        assert not list(v.iter_errors(ex["payload"])), ex["name"]


# ---------------------------------------------------------------- consistency (spec §7) -- #
# specs/2026-10-06-api-consistency-design.md: the error envelope, the status table, query
# strings and the app shell, statically against api/openapi.yaml and at runtime against a
# fake-pack DiagServer.
STATUS_TABLE = {"200", "202", "206", "400", "401", "403", "404", "409", "413", "416", "500",
                "502", "503", "504"}
ADMIN_PW = "pw"


def _is_app_op(op: dict) -> bool:
    return "app" in op.get("tags", [])


def test_every_documented_status_is_in_the_status_table(openapi):
    bad = [f"{m.upper()} {p}: {c}" for p, m, op in _operations(openapi)
           for c in op.get("responses", {}) if c not in STATUS_TABLE]
    assert not bad, "statuses outside the spec §2 table:\n  " + "\n  ".join(bad)


def test_every_documented_error_is_the_envelope(openapi):
    """Every 4xx/5xx of a non-app operation is ``ErrorReply`` (416 has no body)."""
    assert "NotFoundHtml" not in openapi["components"]["responses"]
    err = openapi["components"]["schemas"]["ErrorReply"]
    assert err["properties"]["code"]["pattern"] == "^[a-z][a-z0-9_]*$"
    assert "code" not in err["required"]
    bad = []
    for path, method, op in _operations(openapi):
        for status, resp in op.get("responses", {}).items():
            if status[0] not in "45" or status == "416":
                continue
            if _is_app_op(op) and status == "401":
                continue  # an app page's 401 stays bodiless (the Basic Auth prompt)
            resp = _resolve(openapi, resp)
            schema = (resp.get("content") or {}).get("application/json", {}).get("schema", {})
            refs = [schema.get("$ref")] + [s.get("$ref") for s in schema.get("allOf", [])]
            if "#/components/schemas/ErrorReply" not in refs:
                bad.append(f"{method.upper()} {path} {status}")
    assert not bad, "error responses that are not ErrorReply:\n  " + "\n  ".join(bad)


def test_fixtures_agree_with_their_status():
    """An ``ok: false`` fixture is a non-2xx reply; a 2xx fixture never says ``ok: false``."""
    bad = []
    for name, (_path, _method, status) in FIXTURE_ROUTES.items():
        data = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
        failed = isinstance(data, dict) and data.get("ok") is False
        if failed == status.startswith("2"):
            bad.append(f"{name}: status {status}, ok={data.get('ok')}")
    assert not bad, "\n  ".join(bad)


@pytest.fixture
def fake_server(tmp_path):
    """A fake-pack DiagServer with an admin password, polling, a doc and a community
    client that is offline (contributions queue)."""
    from openostler.community import Community
    from openostler.pack import use_pack
    from openostler.web.docs import DocLibrary
    from openostler.web.server import DiagServer
    from tests.fake_pack import FAKE_PACK

    doc = tmp_path / "notes.md"
    doc.write_text("# Notes\n\nA test document.\n", encoding="utf-8")
    community = Community(config_path=str(tmp_path / "community.json"),
                          endpoint="https://community.invalid/x",
                          poster=lambda url, body: {"ok": False, "error": "offline"})
    with use_pack(FAKE_PACK) as pack:
        srv = DiagServer(pack.sources("auto"), host="127.0.0.1", port=0, poll_interval=0.05,
                         stream_interval=0.05, csv_dir=str(tmp_path), menus=pack.menus,
                         geocoder=None, admin_password=ADMIN_PW, community=community,
                         docs=DocLibrary().add_file(doc))
        srv.start_polling()
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            yield srv
        finally:
            srv.shutdown()
            srv.server_close()
            srv.stop()


def _call(srv, method: str, path: str, body=None, auth: bool = True, headers=None):
    """→ (status, headers, body bytes); never raises on an HTTP error status."""
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=15)
    hdrs = dict(headers or {})
    if auth:
        hdrs["Authorization"] = "Basic " + base64.b64encode(f"admin:{ADMIN_PW}".encode()).decode()
    data = None if body is None else json.dumps(body).encode()
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    try:
        conn.request(method, path, body=data, headers=hdrs)
        resp = conn.getresponse()
        if resp.getheader("Content-Type", "").startswith("text/event-stream"):
            return resp.status, dict(resp.getheaders()), b""  # the SSE stream never ends
        return resp.status, dict(resp.getheaders()), resp.read()
    finally:
        conn.close()


def _envelope_ok(openapi, status: int, headers: dict, body: bytes, where: str):
    assert headers.get("Content-Type") == "application/json", where
    reply = json.loads(body)
    errors = list(_validator(openapi, "/components/schemas/ErrorReply").iter_errors(reply))
    assert not errors, f"{where}: {errors[0].message}"
    assert reply["ok"] is False and reply["error"], where
    return reply


# query strings a documented exact route needs to answer its success status
_BASE_QUERY = {"/doc": "id=notes"}
_POST_BODY = {"/community/consent": {"consent": False}}


def test_a_query_string_never_404s(openapi, fake_server):
    """Spec §7: every documented exact GET and POST route answers the same status with
    ``?_=1`` as without it, and never 404."""
    checked = []
    for path, method, op in _operations(openapi):
        if method not in ("get", "post") or "{" in path or op.get("x-ostler-route"):
            continue
        base = path + (f"?{_BASE_QUERY[path]}" if path in _BASE_QUERY else "")
        extra = ("&" if "?" in base else "?") + "_=1"
        body = _POST_BODY.get(path, {}) if method == "post" else None
        plain = _call(fake_server, method.upper(), base, body)[0]
        query = _call(fake_server, method.upper(), base + extra, body)[0]
        assert query == plain and query != 404, f"{method.upper()} {path}: {plain} vs {query}"
        checked.append(path)
    assert {"/snapshot", "/events", "/command", "/docs", "/community", "/"} <= set(checked)


@pytest.mark.parametrize("method,path,auth", [
    ("GET", "/no/such/route", True), ("POST", "/no/such/route", True),
    ("PATCH", "/no/such/route", True), ("DELETE", "/no/such/route", True),
    ("PUT", "/snapshot", True), ("GET", "/doc?id=nope", True), ("GET", "/nope.js", True),
    ("GET", "/docs", False), ("POST", "/signal", False), ("GET", "/sessions/nope/data", True),
])
def test_errors_are_the_envelope(openapi, fake_server, method, path, auth):
    status, headers, body = _call(fake_server, method, path, {} if method != "GET" else None,
                                  auth=auth)
    assert status >= 400, (method, path, status)
    reply = _envelope_ok(openapi, status, headers, body, f"{method} {path}")
    if not auth:
        assert status == 401 and reply["code"] == "auth_required"
        assert headers["WWW-Authenticate"] == 'Basic realm="Ostler admin"'
    elif method == "PUT":
        assert status == 501
    else:
        assert status == 404 and reply["code"] == "not_found"


def test_an_admin_page_keeps_its_bodiless_401(fake_server):
    status, headers, body = _call(fake_server, "GET", "/admin", auth=False)
    assert status == 401 and body == b"" and "WWW-Authenticate" in headers


def test_unknown_browser_pages_get_the_app_shell(openapi, fake_server):
    html = {"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
    status, headers, body = _call(fake_server, "GET", "/somewhere/deep", headers=html)
    assert status == 200 and headers["Content-Type"].startswith("text/html")
    assert body == _call(fake_server, "GET", "/")[2]  # the same shell as /
    for accept in ({"Accept": "application/json"}, {}, {"Accept": "*/*"}):
        status, headers, body = _call(fake_server, "GET", "/somewhere/deep", headers=accept)
        assert status == 404
        _envelope_ok(openapi, status, headers, body, f"/somewhere/deep {accept}")
    status, headers, body = _call(fake_server, "GET", "/nope.js", headers=html)
    assert status == 404  # a missing file is never the app
    _envelope_ok(openapi, status, headers, body, "/nope.js")
    status, headers, body = _call(fake_server, "POST", "/somewhere/deep", {}, headers=html)
    assert status == 404  # only GET


def test_the_car_refusing_is_502_and_a_poll_timeout_504(openapi, fake_server):
    from openostler.kwp2000.kwp2000 import NegativeResponse

    src = fake_server.source
    calls = []

    def command(action, params=None):
        calls.append(action)
        if action == "raise_nrc":
            raise NegativeResponse(0x31, 0x22)
        if action == "text_nrc":  # a source that catches its own exception
            return {"ok": False, "error": "NegativeResponse: negative response to service "
                                          "0x31: NRC 0x22 (conditionsNotCorrect)"}
        return {"ok": True, "message": action}

    src.command = command
    for action in ("raise_nrc", "text_nrc"):
        status, headers, body = _call(fake_server, "POST", "/command", {"action": action})
        reply = _envelope_ok(openapi, status, headers, body, action)
        assert status == 502 and reply["code"] == "car_refused" and reply["nrc"] == 0x22
    fake_server._stop.set()               # the poll thread stops answering
    fake_server._poller.join(timeout=2)
    fake_server.command_timeout = 0.2
    status, headers, body = _call(fake_server, "POST", "/command", {"action": "clear_faults"})
    reply = _envelope_ok(openapi, status, headers, body, "timeout")
    assert status == 504 and reply["code"] == "car_timeout"


def test_a_queued_contribution_is_202_ok(openapi, fake_server):
    assert _call(fake_server, "POST", "/community/consent", {"consent": True})[0] == 200
    status, _, body = _call(fake_server, "POST", "/community/contribute",
                            {"module": "alpha", "name": "x"})
    reply = json.loads(body)
    assert status == 202 and reply["ok"] is True and reply["queued"] is True
    v = _validator(openapi, _response_pointer(openapi, "/community/contribute", "post", "202"))
    assert not list(v.iter_errors(reply))
    _call(fake_server, "POST", "/community/consent", {"consent": False})
    status, headers, body = _call(fake_server, "POST", "/community/contribute", {"x": 1})
    assert status == 409 and _envelope_ok(openapi, status, headers, body, "off")["code"] \
        == "community_off"


def test_the_status_table_corrections(openapi, tmp_path, monkeypatch):
    """Spec §2 "Corrections": the statuses that used to be 200 or 400."""
    from openostler.pack import use_pack
    from openostler.web.server import DiagServer
    from tests.fake_pack import FAKE_PACK

    (tmp_path / "captures").mkdir()  # a directory: appending to it fails (OSError)
    with use_pack(FAKE_PACK) as pack:
        srv = DiagServer(pack.sources("auto"), host="127.0.0.1", port=0, poll_interval=0.05,
                         stream_interval=0.05, csv_dir=str(tmp_path), menus=pack.menus,
                         geocoder=None, record_sessions=False,
                         captures_path=str(tmp_path / "captures"))
        srv.start_polling()
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            def code_of(method, path, body=None):
                status, headers, raw = _call(srv, method, path, body, auth=False)
                reply = _envelope_ok(openapi, status, headers, raw, f"{method} {path}")
                return status, reply.get("code")

            assert code_of("POST", "/calib", {"samples": [[1, 1]]}) == (400, "bad_request")
            assert code_of("POST", "/calib", {"samples": [[1, 1], [2, 2]], "lid": "zz"})[0] == 400
            assert code_of("POST", "/automap", {"samples": []}) == (400, "bad_request")
            assert code_of("POST", "/automap", {
                "samples": [{"text": "10", "raws": {"09": "00"}}, {"text": "20", "raws": {"09": "00"}}],
                "candidate_lids": ["09"]}) == (400, "no_match")
            assert code_of("POST", "/capture", {"module": "alpha", "lid": "01"}) == (500, "internal")
            assert code_of("POST", "/signal", {"module": "nope", "record": {}}) == (400, "bad_request")
            from openostler import signals

            def broken(module, rec):
                raise OSError("read-only file system")
            monkeypatch.setattr(signals, "upsert_field", broken)
            assert code_of("POST", "/signal", {"module": "alpha", "record": {
                "name": "x", "lid": "01", "offset": 0}}) == (500, "internal")
            assert code_of("POST", "/community/consent", {"consent": True}) == (409, "community_off")
            assert code_of("POST", "/command", {"action": "shutdown"}) == (409, "conflict")
            assert code_of("POST", "/command", {"action": "split_session"}) == (503, "unavailable")
            assert code_of("POST", "/command", {"action": "no_such"})[0] == 400
            assert code_of("POST", "/command", "not an object") == (400, "bad_request")
            assert _call(srv, "POST", "/command", {"action": "disconnect"})[0] == 200
            assert code_of("POST", "/command", {"action": "clear_faults"}) == (409, "disconnected")
            assert code_of("GET", "/sessions/20000101T000000Z/data") == (404, "not_found")

            def unreadable(*a, **kw):
                raise OSError("disk gone")
            store = srv.session_store
            monkeypatch.setattr(store, "meta", lambda sid, public=False: {"id": sid})
            monkeypatch.setattr(store, "data", unreadable)
            assert code_of("GET", "/sessions/20000101T000000Z/data") == (500, "internal")
        finally:
            srv.shutdown()
            srv.server_close()
            srv.stop()
