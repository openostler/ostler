# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The machine-readable API contracts in ``api/`` (ADR-0017): OpenAPI 3.1.1 and AsyncAPI 3.0.

- Every route ``web/server.py`` handles is in ``api/openapi.yaml`` and every documented
  route exists. Routes are read from the server's source (static analysis of the string
  literals ``_Handler`` compares the request path with), so a new ``elif self.path == …``
  fails here until it is documented. Admin gating and query-string handling are
  cross-checked the same way.
- ``api/openapi.yaml`` passes ``openapi-spec-validator``; ``api/asyncapi.yaml`` is checked
  structurally (there is no light AsyncAPI validator on PyPI).
- The committed UI fixtures (real server responses, ``ui/src/api/fixtures/``) validate
  against the documented response schemas (JSON Schema 2020-12).

Needs the dev extra (pyyaml, openapi-spec-validator, jsonschema); no pack, no hardware.
"""
from __future__ import annotations

import ast
import json
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
    "command-ok": ("/command", "post", "200"),
    "command-error": ("/command", "post", "400"),
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


def _is_split_path(node) -> bool:
    """``self.path.split("?")[0]``."""
    return (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute) and node.value.func.attr == "split"
            and _is_self_path(node.value.func.value))


def _strings(node) -> "list[str]":
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [s for e in node.elts for s in _strings(e)]
    return []


def _path_tests(test) -> "tuple[list[tuple[str, bool]], list[str]]":
    """From an ``if`` test: ([(exact path, query-string tolerant)], [startswith prefixes])."""
    exact, prefixes = [], []
    for node in ast.walk(test):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(
                node.ops[0], (ast.Eq, ast.In)):
            if _is_self_path(node.left):
                exact += [(s, False) for s in _strings(node.comparators[0])]
            elif _is_split_path(node.left):
                exact += [(s, True) for s in _strings(node.comparators[0])]
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and node.func.attr == "startswith" and _is_self_path(node.func.value)):
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
    """→ (exact, prefixes): ``exact[(method, path)] = {admin, query}``;
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
                for path, query in paths:
                    exact[(method, path)] = {"admin": admin, "query": query}
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
        if isinstance(node, ast.Compare) and not _is_self_path(node.left):
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
    assert exact[("get", "/snapshot")] == {"admin": False, "query": False}
    assert exact[("get", "/map")] == {"admin": True, "query": True}
    assert exact[("get", "/admin")]["admin"] is True
    assert exact[("post", "/notes/live")]["query"] is True
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


def test_query_string_handling_matches_the_server(openapi):
    """Routes matched with ``self.path == …`` 404 on any query string: say so."""
    exact, _ = _server_routes()
    wrong = []
    for path, method, op in _operations(openapi):
        code = exact.get((method, path))
        if code is None:
            continue
        refused = op.get("x-ostler-query-string") == "refused"
        if refused == code["query"]:
            wrong.append(f"{method.upper()} {path}: server tolerates a query={code['query']}")
    assert not wrong, "\n  ".join(["x-ostler-query-string differs:", *wrong])


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
            sse = _path_tests(node.test)[0][0][0]
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
