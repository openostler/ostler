# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session logbook over HTTP (specs/2026-10-05-session-logbook-design.md, ADR-0009).

The server side only: routes, the public-mode filter, 404/400, ``delete_session``
refusals, the snapshot ``gps``/``recording`` fields and that the recorder is fed. The
recorder/store/exports themselves are tested in their own files. Polls are driven by hand
(``poll_once`` + ``record_poll``) so nothing depends on thread timing.
"""

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")

import json
import os
import threading
import time
import urllib.error
import urllib.request


from tests.fake_sources import FakeTd5Source, FakeSlabsSource
from openostler.web.server import DiagServer


class FakeFix:
    """Just enough of ``gps.Fix`` for the server and the mock sources."""

    def __init__(self, speed_kmh=42.0, lat=10.0012, lon=20.0034):
        self.utc_ms = int(time.time() * 1000)
        self.lat, self.lon = lat, lon
        self.speed_kmh, self.heading, self.alt_m = speed_kmh, 90.0, 12.0
        self.sats, self.hdop, self.fix = 9, 0.9, True
        self.mono = time.monotonic()

    def snapshot(self) -> dict:
        return {"fix": self.fix, "lat": self.lat, "lon": self.lon,
                "speed_kmh": self.speed_kmh, "heading": self.heading, "sats": self.sats,
                "hdop": self.hdop, "src": "mock", "age_s": 0.0}


class FakeGps:
    src = "mock"

    def __init__(self, fix=None):
        self.fix = fix
        self.started = self.stopped = False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def latest(self):
        if self.fix is not None:
            self.fix.lat += 0.0001  # moving along so the track has points
            self.fix.utc_ms += 500
            self.fix.mono = time.monotonic()
        return self.fix


def _make_synthetic(root) -> str:
    """A closed synthetic session in ``root`` (independent of the committed demo)."""
    from openostler.logbook.recorder import SessionRecorder

    clock = {"t": 1_700_000_000.0, "m": 100.0}
    rec = SessionRecorder(str(root), clock=lambda: clock["t"], mono=lambda: clock["m"],
                          synthetic=True, source="demo")
    fix = FakeFix(speed_kmh=50.0)
    for _ in range(6):
        rec.feed({"conn": "connected", "status": "connected", "module": "motor",
                  "signals": {"speed": {"v": 50.0, "u": "km/h"}, "rpm": {"v": 1900, "u": "rpm"}},
                  "faults": []}, fix)
        fix.lat += 0.0002
        fix.utc_ms += 500
        clock["t"] += 0.5
        clock["m"] += 0.5
    sid = rec.status()["session"]
    rec.close()
    return sid


def _server(tmp_path, public=False, gps="default", **kw):
    _make_synthetic(tmp_path / "sessions")
    if gps == "default":
        gps = FakeGps(FakeFix())
    src = FakeTd5Source(gps=gps)
    srv = DiagServer(src, host="127.0.0.1", port=0, csv_dir=str(tmp_path), public=public,
                     gps=gps, **kw)
    return srv


def _record(srv, n=4):
    for _ in range(n):
        srv.poll_once()
        srv.record_poll()


@pytest.fixture
def served():
    """Start serving a DiagServer (HTTP only, no poll thread). Yields a (srv, get) pair."""
    made = []

    def _start(srv):
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        made.append(srv)
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def get(path):
            try:
                with urllib.request.urlopen(base + path, timeout=5) as r:
                    return r.status, dict(r.headers), r.read()
            except urllib.error.HTTPError as e:
                return e.code, dict(e.headers), e.read()

        def post(body):
            req = urllib.request.Request(base + "/command", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    return r.status, json.loads(r.read())
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read())

        return get, post

    yield _start
    for srv in made:
        srv.shutdown()
        srv.stop()
        srv.server_close()


def _real_session(srv) -> str:
    sid = (srv.latest.get("recording") or {}).get("session")
    assert sid, srv.latest.get("recording")
    return sid


def _synthetic_id(srv) -> str:
    demos = [m for m in srv.session_store.list() if m.get("synthetic")]
    assert demos, "a synthetic session must be listed"
    return demos[0]["id"]


# ---- snapshot + recorder ------------------------------------------------- #

def test_mock_snapshot_carries_gps_and_recording(tmp_path):
    srv = _server(tmp_path)
    try:
        _record(srv, 3)
        snap = srv.latest
        assert snap["gps"]["src"] == "mock" and snap["gps"]["fix"] is True
        assert set(snap["gps"]) >= {"fix", "lat", "lon", "speed_kmh", "heading", "sats",
                                    "hdop", "src", "age_s"}
        rec = snap["recording"]
        assert rec and set(rec) >= {"session", "since", "rows"}
        # the recorder was fed: its session directory exists under <csv_dir>/sessions
        assert (tmp_path / "sessions" / rec["session"]).is_dir()
        json.dumps(snap)  # the SSE payload stays JSON-serialisable
    finally:
        srv.stop()
        srv.server_close()


def test_no_gps_source_gives_null_gps(tmp_path):
    srv = _server(tmp_path, gps=None)
    try:
        _record(srv, 2)
        assert srv.latest["gps"] is None
        assert srv.latest["recording"]  # connected mock still records without GPS
    finally:
        srv.stop()
        srv.server_close()


def test_gps_source_without_fix_reports_no_fix(tmp_path):
    srv = _server(tmp_path, gps=FakeGps(None))
    try:
        srv.poll_once()
        assert srv.latest["gps"]["fix"] is False and srv.latest["gps"]["src"] == "mock"
    finally:
        srv.stop()
        srv.server_close()


def test_stop_closes_recorder_and_gps(tmp_path):
    gps = FakeGps(FakeFix())
    srv = _server(tmp_path, gps=gps)
    try:
        srv.start_polling()
        assert gps.started
        deadline = time.monotonic() + 5
        while not (srv.latest.get("recording") or {}).get("session"):
            assert time.monotonic() < deadline, "the poll loop never fed the recorder"
            time.sleep(0.05)
        sid = srv.latest["recording"]["session"]
    finally:
        srv.stop()
        srv.server_close()
    assert gps.stopped
    meta = json.loads((tmp_path / "sessions" / sid / "meta.json").read_text())
    assert meta["recording"] is False and meta["end_utc"]


def test_record_sessions_off_never_writes(tmp_path):
    srv = _server(tmp_path, record_sessions=False)
    try:
        _record(srv, 3)
        assert srv.latest["recording"] is None
        metas = srv.session_store.list()
        assert metas and all(m["synthetic"] for m in metas)  # only the fixture's session
    finally:
        srv.stop()
        srv.server_close()


def test_mock_speed_follows_gps():
    d = FakeTd5Source(gps=FakeGps(FakeFix(speed_kmh=63.0))).poll()
    assert d["signals"]["speed"]["v"] == pytest.approx(63.0, abs=0.5)
    assert d["signals"]["rpm"]["v"] > 1500  # driving, not idling
    parked = FakeTd5Source(gps=FakeGps(FakeFix(speed_kmh=0.0))).poll()
    assert parked["signals"]["speed"]["v"] == 0
    # no GPS / no fix → the old self-contained mock behaviour
    assert "speed" in FakeTd5Source().poll()["signals"]
    assert "speed" in FakeTd5Source(gps=FakeGps(None)).poll()["signals"]
    s = FakeSlabsSource(gps=FakeGps(FakeFix(speed_kmh=30.0))).poll()["signals"]
    assert s["wheel_speed_fl"]["v"] > FakeSlabsSource().poll()["signals"]["wheel_speed_fl"]["v"]


def test_no_vin_or_identity_in_any_session_file(tmp_path):
    srv = _server(tmp_path)
    try:
        _record(srv, 2)
        holder = {"result": None, "event": threading.Event()}
        srv._commands.put(({"action": "read_identity",
                            "params": {"trust": "experimental"}}, holder))
        srv._drain_commands()
        assert holder["result"]["ok"]
        ident = holder["result"]["identity"]
        _record(srv, 3)
        sid = _real_session(srv)
    finally:
        srv.stop()
        srv.server_close()
    files = list((tmp_path / "sessions" / sid).rglob("*"))
    assert any(f.name == "meta.json" for f in files)
    # ADR-0010 §1: the identity read is an event with only {action, ok} — no payload.
    events = [json.loads(x) for x in
              (tmp_path / "sessions" / sid / "events.jsonl").read_text().splitlines()]
    ident_ev = [e for e in events if e.get("action") == "read_identity"]
    assert ident_ev and all(set(e) == {"t", "type", "action", "ok"} for e in ident_ev)
    for f in files:
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            text = text.replace('"action":"read_identity"', "")  # the bare action name only
            for needle in (ident["part_no"], ident["vin_masked"], "vin", "VIN", "identity"):
                assert needle not in text, f"{needle!r} leaked into {f.name}"


# ---- routes ---------------------------------------------------------------- #

def test_sessions_routes_private(tmp_path, served):
    srv = _server(tmp_path)
    _record(srv, 6)
    sid = _real_session(srv)
    get, _ = served(srv)

    code, _, body = get("/sessions")
    assert code == 200
    ids = [m["id"] for m in json.loads(body)["sessions"]]
    assert sid in ids and _synthetic_id(srv) in ids

    code, _, body = get(f"/sessions/{sid}")
    assert code == 200 and json.loads(body)["id"] == sid

    code, _, body = get(f"/sessions/{sid}/data?ch=rpm,speed&max=100")
    assert code == 200
    data = json.loads(body)
    assert set(data) >= {"id", "t", "utc", "ch", "track", "decimated"}
    assert "rpm" in data["ch"]

    code, _, _ = get(f"/sessions/{sid}/data?max=lots")
    assert code == 400


def test_sessions_unknown_and_malformed_ids_are_404_json(tmp_path, served):
    srv = _server(tmp_path, gps=None)
    get, _ = served(srv)
    for path in ("/sessions/20000101T000000Z", "/sessions/20000101T000000Z/data",
                 "/sessions/20000101T000000Z/export?fmt=gpx", "/sessions/..%2F..%2Fetc",
                 "/sessions/.hidden", "/sessions/x/bogus"):
        code, headers, body = get(path)
        assert code == 404, path
        assert headers["Content-Type"] == "application/json"
        assert json.loads(body)["ok"] is False


def test_export_is_an_attachment_and_bad_format_is_400(tmp_path, served):
    srv = _server(tmp_path)
    get, _ = served(srv)
    demo = _synthetic_id(srv)
    for fmt in ("csv", "vbo", "gpx"):
        code, headers, body = get(f"/sessions/{demo}/export?fmt={fmt}")
        assert code == 200, fmt
        cd = headers["Content-Disposition"]
        assert cd.startswith("attachment;") and "filename=" in cd and f".{fmt}" in cd
        assert body
    code, _, body = get(f"/sessions/{demo}/export?fmt=xlsx")
    assert code == 400 and json.loads(body)["ok"] is False


def test_public_mode_serves_only_synthetic_sessions(tmp_path, served):
    srv = _server(tmp_path, public=True)
    _record(srv, 4)
    real = _real_session(srv)  # recording still happens on the device
    demo = _synthetic_id(srv)
    get, _ = served(srv)

    code, _, body = get("/sessions")
    metas = json.loads(body)["sessions"]
    assert code == 200 and metas and all(m["synthetic"] for m in metas)
    assert real not in [m["id"] for m in metas]
    for path in (f"/sessions/{real}", f"/sessions/{real}/data",
                 f"/sessions/{real}/export?fmt=gpx"):
        assert get(path)[0] == 404, path
    assert get(f"/sessions/{demo}")[0] == 200
    assert get(f"/sessions/{demo}/data?ch=speed")[0] == 200
    assert get(f"/sessions/{demo}/export?fmt=vbo")[0] == 200


# ---- delete_session ---------------------------------------------------------- #

def test_delete_session_refused_in_public_mode(tmp_path, served):
    srv = _server(tmp_path, public=True)
    _record(srv, 3)
    real = _real_session(srv)
    srv.close_recorder()
    _, post = served(srv)
    code, res = post({"action": "delete_session", "params": {"id": real}})
    assert code == 400 and not res["ok"] and "public" in res["error"]
    assert (tmp_path / "sessions" / real).is_dir()


def test_delete_session_refuses_synthetic_recording_and_unknown(tmp_path, served):
    srv = _server(tmp_path)
    _record(srv, 3)
    real = _real_session(srv)
    _, post = served(srv)
    code, res = post({"action": "delete_session", "params": {"id": _synthetic_id(srv)}})
    assert code == 400 and "synthetic" in res["error"]
    code, res = post({"action": "delete_session", "params": {"id": real}})
    assert code == 400 and "recorded" in res["error"]  # still open
    code, res = post({"action": "delete_session", "params": {"id": "20000101T000000Z"}})
    assert code == 400
    code, res = post({"action": "delete_session", "params": {"id": "../etc"}})
    assert code == 400


def test_delete_session_deletes_a_closed_real_session(tmp_path, served):
    srv = _server(tmp_path)
    _record(srv, 3)
    real = _real_session(srv)
    srv.close_recorder()
    get, post = served(srv)
    code, res = post({"action": "delete_session", "params": {"id": real}})
    assert code == 200 and res["ok"], res
    assert not (tmp_path / "sessions" / real).exists()
    assert get(f"/sessions/{real}")[0] == 404


# ---- dashboard CLI (ADR-0011: always live) --------------------------------- #

def _load_dashboard(monkeypatch):
    import importlib.util
    import pathlib
    import signal

    from openostler.web import server as server_mod

    captured = {}
    monkeypatch.setattr(server_mod.DiagServer, "serve", lambda self: captured.update(srv=self))
    monkeypatch.setattr(signal, "signal", lambda *a: None)  # keep pytest's SIGTERM handling
    path = pathlib.Path(__file__).resolve().parent.parent / "tools" / "dashboard.py"
    spec = importlib.util.spec_from_file_location("_dashboard_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, captured


@pytest.mark.parametrize("argv", [["--mock"], ["--gps", "mock"], ["--imu", "mock"]])
def test_dashboard_has_no_demo_mode(argv, monkeypatch, capsys):
    import sys

    mod, captured = _load_dashboard(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["dashboard.py", *argv, "--port", "0"])
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 2 and "srv" not in captured  # argparse error, nothing served
    assert "usage:" in capsys.readouterr().err


def test_dashboard_runs_live_with_the_geocoder(tmp_path, monkeypatch):
    """The Docker/homelab command: live sources, not public, recorder on, OSM geocoder on."""
    import sys

    from openostler.geo.nominatim import DEFAULT_URL
    from d2diag.sources import InfoDataSource, SlabsDataSource, Td5DataSource

    mod, captured = _load_dashboard(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["dashboard.py", "--host", "127.0.0.1", "--port", "0",
                                      "--gps", "none", "--imu", "none",
                                      "--sessions-dir", str(tmp_path / "s")])
    assert mod.main() == 0
    srv = captured["srv"]
    try:
        assert srv._public is False and "mode" not in srv.latest
        assert isinstance(srv._modules["td5"], Td5DataSource)
        assert isinstance(srv._modules["slabs"], SlabsDataSource)
        assert all(isinstance(srv._modules[m], InfoDataSource)
                   for m in ("airbag", "ace", "autobox", "bcu"))
        assert srv.gps is None and srv.latest["gps"] is None
        assert srv._sessions_dir == str(tmp_path / "s") and srv._recorder is not None
        assert srv._index_path == os.path.join(str(tmp_path / "s"), "index.sqlite")
        assert srv._enricher is not None and srv._enricher.url == DEFAULT_URL
    finally:
        srv.stop()
        srv.server_close()

    for extra, has in ((["--geocoder", "off"], False), (["--public"], False),
                       (["--geocoder", "http://geo.invalid"], True)):
        monkeypatch.setattr(sys, "argv", ["dashboard.py", "--host", "127.0.0.1", "--port", "0",
                                          "--gps", "none", "--imu", "none",
                                          "--sessions-dir", str(tmp_path / "s"), *extra])
        assert mod.main() == 0
        srv = captured["srv"]
        try:
            assert (srv._enricher is not None) is has, extra
        finally:
            srv.stop()
            srv.server_close()


# ---- paging, search, histogram (spec 2026-10-06 §3) ------------------------ #

DAY = 86_400.0
_WORDS = ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot")


def _make_real(root, start_s: float, name=None, fix=None, synthetic=False) -> str:
    """A closed session in ``root`` starting at ``start_s`` (epoch s)."""
    from openostler.logbook.recorder import SessionRecorder

    clock = {"t": start_s, "m": 100.0}
    rec = SessionRecorder(str(root), clock=lambda: clock["t"], mono=lambda: clock["m"],
                          synthetic=synthetic, source="live")
    for _ in range(4):
        rec.feed({"conn": "connected", "status": "connected", "module": "motor",
                  "signals": {"rpm": {"v": 900, "u": "rpm"}}, "faults": []}, fix)
        if fix is not None:
            fix.lat += 0.001
            fix.utc_ms += 500
        clock["t"] += 0.5
        clock["m"] += 0.5
    sid = rec.status()["session"]
    rec.close()
    if name is not None:
        from openostler.logbook.store import SessionStore
        SessionStore(str(root)).update_meta(sid, name=name)
    return sid


def _logbook(tmp_path, n=5, **kw):
    """A server over ``n`` closed real sessions one day apart (2025-01-01 … ) + demos."""
    root = tmp_path / "sessions"
    base = 1_735_725_600.0  # 2025-01-01T10:00:00Z
    ids = [_make_real(root, base + i * DAY, name=f"Drive {_WORDS[i]}") for i in range(n)]
    srv = DiagServer(FakeTd5Source(), host="127.0.0.1", port=0, csv_dir=str(tmp_path), **kw)
    return srv, ids


def _req(served, srv):
    get, _ = served(srv)
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    def call(method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(base + path, data=data, method=method,
                                   headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
    return call


def test_sessions_are_keyset_paged_newest_first(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=5)
    call = _req(served, srv)
    seen, cursor = [], None
    while True:
        code, body = call("GET", "/sessions?limit=2" + (f"&before={cursor}" if cursor else ""))
        assert code == 200 and set(body) == {"sessions", "next"}
        assert len(body["sessions"]) <= 2
        seen += [m["id"] for m in body["sessions"]]
        cursor = body["next"]
        if cursor is None:
            break
    real = [i for i in seen if i in ids]
    assert real == sorted(ids, reverse=True)       # newest first, each exactly once
    assert len(seen) == len(set(seen))
    assert any(i not in ids for i in seen)          # the committed demo logs are listed too
    assert srv.session_store.index is srv._index is not None
    assert os.path.exists(tmp_path / "sessions" / "index.sqlite")
    code, body = call("GET", "/sessions")           # default limit 50 → everything
    assert code == 200 and body["next"] is None and len(body["sessions"]) == len(seen)


def test_sessions_filters_and_bad_parameters(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=4)
    call = _req(served, srv)
    code, body = call("GET", "/sessions?q=charlie")
    assert code == 200 and [m["id"] for m in body["sessions"]] == [ids[2]]
    code, body = call("GET", "/sessions?from=2025-01-02&to=2025-01-03")
    assert code == 200 and sorted(m["id"] for m in body["sessions"]) == ids[1:3]
    code, body = call("GET", "/sessions?module=motor&min_km=0")
    assert code == 200 and set(ids) <= {m["id"] for m in body["sessions"]}
    code, body = call("GET", "/sessions?has_notes=1")
    assert code == 200 and not set(ids) & {m["id"] for m in body["sessions"]}
    code, body = call("GET", "/sessions?limit=1000")  # capped at 200, not refused
    assert code == 200
    for bad in ("limit=lots", "limit=0", "from=yesterday", "to=2025-13", "min_km=far",
                "before=not%20a%20cursor"):
        code, body = call("GET", f"/sessions?{bad}")
        assert code == 400 and body["ok"] is False, bad


def test_sessions_histogram(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=3)
    call = _req(served, srv)
    code, body = call("GET", "/sessions/histogram")
    assert code == 200 and body["group"] == "month"
    by = {b["key"]: b for b in body["buckets"]}
    assert by["2025-01"]["count"] == 3 and set(by["2025-01"]) == {"key", "count", "km"}
    code, body = call("GET", "/sessions/histogram?group=day&year=2025")
    assert code == 200 and body["group"] == "day"
    assert {b["key"] for b in body["buckets"]} == {"2025-01-01", "2025-01-02", "2025-01-03"}
    # the scrubber jumps with before=<end of a month> (an ISO date)
    code, body = call("GET", "/sessions?before=2025-01-02T23:59:59Z")
    assert code == 200 and {m["id"] for m in body["sessions"]} & set(ids) == set(ids[:2])
    assert call("GET", "/sessions/histogram?group=week")[0] == 400
    assert call("GET", "/sessions/histogram?group=day&year=soon")[0] == 400


def test_public_paging_and_histogram_list_only_synthetic(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=3, public=True)
    call = _req(served, srv)
    code, body = call("GET", "/sessions?limit=200")
    assert code == 200 and body["sessions"] and all(m["synthetic"] for m in body["sessions"])
    assert not set(ids) & {m["id"] for m in body["sessions"]}
    code, body = call("GET", "/sessions/histogram?group=day&year=2025")
    assert code == 200 and body["buckets"] == []


# ---- PATCH /sessions/<id> ---------------------------------------------------- #

def test_patch_session_name_and_description(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=2)
    call = _req(served, srv)
    sid = ids[0]
    code, body = call("PATCH", f"/sessions/{sid}",
                      {"name": "  Glen   Coe run  ", "description": "  cold start\nrough idle  "})
    assert code == 200 and body["ok"] is True
    assert body["meta"]["name"] == "Glen Coe run"
    assert body["meta"]["description"] == "cold start\nrough idle"
    assert json.loads((tmp_path / "sessions" / sid / "meta.json").read_text())["name"] == \
        "Glen Coe run"
    # the index follows: search finds the new name, the old one is gone
    assert [m["id"] for m in call("GET", "/sessions?q=Glen")[1]["sessions"]] == [sid]
    assert sid not in [m["id"] for m in call("GET", "/sessions?q=alpha")[1]["sessions"]]
    # caps, empty → null, partial updates
    code, body = call("PATCH", f"/sessions/{sid}", {"name": "x" * 200})
    assert code == 200 and len(body["meta"]["name"]) == 80
    assert body["meta"]["description"] == "cold start\nrough idle"   # untouched
    code, body = call("PATCH", f"/sessions/{sid}", {"description": "y" * 3000, "name": "   "})
    assert code == 200 and body["meta"]["name"] is None
    assert len(body["meta"]["description"]) == 2000


def test_patch_session_refusals(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=1)
    call = _req(served, srv)
    demo = _synthetic_id(srv)
    assert call("PATCH", f"/sessions/{demo}", {"name": "mine"}) == (
        403, {"ok": False, "error": "synthetic sessions are read-only"})
    assert call("PATCH", f"/sessions/{ids[0]}", {"name": 5})[0] == 400
    assert call("PATCH", f"/sessions/{ids[0]}", {})[0] == 400
    assert call("PATCH", f"/sessions/{ids[0]}", {"colour": "red"})[0] == 400
    assert call("PATCH", "/sessions/20000101T000000Z", {"name": "x"})[0] == 404
    assert call("PATCH", "/sessions/..%2Fetc", {"name": "x"})[0] == 404


def test_patch_session_refused_in_public_mode(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=1, public=True)
    call = _req(served, srv)
    for sid in (ids[0], _synthetic_id(srv)):
        assert call("PATCH", f"/sessions/{sid}", {"name": "x"}) == (
            403, {"ok": False, "error": "not available in public mode"})
    assert json.loads((tmp_path / "sessions" / ids[0] / "meta.json").read_text())["name"] \
        == "Drive alpha"


def test_delete_session_leaves_the_index(tmp_path, served):
    srv, ids = _logbook(tmp_path, n=2)
    call = _req(served, srv)
    assert ids[0] in [m["id"] for m in call("GET", "/sessions")[1]["sessions"]]
    res = srv.enqueue_command({"action": "delete_session", "params": {"id": ids[0]}})
    assert res["ok"], res
    assert ids[0] not in [m["id"] for m in call("GET", "/sessions")[1]["sessions"]]


# ---- place-name enrichment (spec 2026-10-06 §2) ----------------------------- #

class FakeEnricher:
    def __init__(self):
        self.submitted, self.started, self.stopped = [], False, False

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def submit(self, key, lat, lon, callback):
        self.submitted.append((key, lat, lon, callback))


def test_closed_session_points_go_to_the_enricher(tmp_path, served):
    enr = FakeEnricher()
    gps = FakeGps(FakeFix(speed_kmh=30.0, lat=56.6500, lon=-4.9000))
    srv = DiagServer(FakeTd5Source(gps=gps), host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                     gps=gps, enricher=enr)
    call = _req(served, srv)
    srv.index(wait=5)
    _record(srv, 4)
    sid = _real_session(srv)
    assert enr.submitted == []                       # nothing while it is recording
    srv.close_recorder()
    keys = {k: (lat, lon, cb) for k, lat, lon, cb in enr.submitted}
    assert set(keys) == {f"{sid}|start", f"{sid}|end"}
    meta = srv.session_store.meta(sid)
    lat, lon, cb = keys[f"{sid}|start"]
    assert (round(lat, 3), round(lon, 3)) == (meta["start_pos"][1], meta["start_pos"][0])
    cb(f"{sid}|start", "Glencoe, Highland")
    cb(f"{sid}|end", None)                           # no result: nothing written
    meta = srv.session_store.meta(sid)
    assert meta["place_start"]["label"] == "Glencoe, Highland"
    assert meta["place_start"]["source"] == "osm"
    assert (meta.get("place_end") or {}).get("source") != "osm"
    assert [m["id"] for m in call("GET", "/sessions?q=Glencoe")[1]["sessions"]] == [sid]
    srv.stop()
    assert enr.stopped

    # a restart queues what still lacks an OSM label (the end point), never demo logs
    enr2 = FakeEnricher()
    srv2 = DiagServer(FakeTd5Source(), host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                      enricher=enr2)
    try:
        srv2.start_polling()
        assert srv2.index(wait=5) is not None
        deadline = time.monotonic() + 5
        while not enr2.submitted and time.monotonic() < deadline:
            time.sleep(0.02)
        assert [k for k, *_ in enr2.submitted] == [f"{sid}|end"]
        assert enr2.started
    finally:
        srv2.stop()
        srv2.server_close()


def test_no_enricher_in_public_mode_or_when_off(tmp_path):
    srv = DiagServer(FakeTd5Source(), host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                     public=True, enricher=FakeEnricher(), geocoder="http://geo.invalid")
    try:
        assert srv._enricher is None
    finally:
        srv.server_close()
    srv = DiagServer(FakeTd5Source(), host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                     geocoder="off")
    try:
        assert srv._enricher is None
    finally:
        srv.server_close()


# ---- legacy "motor" sessions: migrated on read, never rewritten (Phase 0 §2) ---- #

LEGACY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures",
                      "legacy_session_motor")
LEGACY_ID = "20260528T202640Z"


def test_legacy_motor_session_lists_filters_and_replays_as_td5(tmp_path, served):
    import shutil

    root = tmp_path / "sessions"
    shutil.copytree(os.path.join(LEGACY, LEGACY_ID), root / LEGACY_ID)
    before = {p.name: p.read_bytes() for p in (root / LEGACY_ID).iterdir()}
    assert b'"motor"' in before["meta.json"] and b'"motor"' in before["events.jsonl"]
    src = FakeTd5Source(gps=None)
    srv = DiagServer(src, host="127.0.0.1", port=0, csv_dir=str(tmp_path),
                     sessions_dir=str(root), record_sessions=False, geocoder=None)
    get, _ = served(srv)

    def j(path):
        code, _h, body = get(path)
        assert code == 200, (path, code, body)
        return json.loads(body)

    listed = [m for m in j("/sessions")["sessions"] if m["id"] == LEGACY_ID]
    assert listed and listed[0]["modules"] == ["td5", "slabs"]
    for want in ("td5", "motor", "MOTOR"):
        ids = [m["id"] for m in j(f"/sessions?module={want}")["sessions"]]
        assert LEGACY_ID in ids, want
    assert j(f"/sessions/{LEGACY_ID}")["modules"] == ["td5", "slabs"]
    events = j(f"/sessions/{LEGACY_ID}/events")["events"]
    assert [e["module"] for e in events if "module" in e] == ["td5", "slabs", "slabs"]
    data = j(f"/sessions/{LEGACY_ID}/data?ch=rpm&max=100")
    assert set(data["text"]["module"]) == {"td5", "slabs"}
    caps = j("/captures?module=td5")["captures"]
    assert any(c.get("session") == LEGACY_ID and c["module"] == "td5" for c in caps)
    assert [c["session"] for c in j("/captures?module=motor")["captures"]] == \
        [c["session"] for c in caps]
    # read-migration only: the files on disk are untouched
    assert {p.name: p.read_bytes() for p in (root / LEGACY_ID).iterdir()
            if p.name in before} == before
