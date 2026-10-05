"""Session logbook over HTTP (specs/2026-10-05-session-logbook-design.md, ADR-0009).

The server side only: routes, the public-mode filter, 404/400, ``delete_session``
refusals, the snapshot ``gps``/``recording`` fields and that the recorder is fed. The
recorder/store/exports themselves are tested in their own files. Polls are driven by hand
(``poll_once`` + ``record_poll``) so nothing depends on thread timing.
"""
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from d2diag.web import MockDataSource, MockSlabsDataSource
from d2diag.web.server import DiagServer


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
    from d2diag.logbook.recorder import SessionRecorder

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
    src = MockDataSource(gps=gps)
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
    d = MockDataSource(gps=FakeGps(FakeFix(speed_kmh=63.0))).poll()
    assert d["signals"]["speed"]["v"] == pytest.approx(63.0, abs=0.5)
    assert d["signals"]["rpm"]["v"] > 1500  # driving, not idling
    parked = MockDataSource(gps=FakeGps(FakeFix(speed_kmh=0.0))).poll()
    assert parked["signals"]["speed"]["v"] == 0
    # no GPS / no fix → the old self-contained mock behaviour
    assert "speed" in MockDataSource().poll()["signals"]
    assert "speed" in MockDataSource(gps=FakeGps(None)).poll()["signals"]
    s = MockSlabsDataSource(gps=FakeGps(FakeFix(speed_kmh=30.0))).poll()["signals"]
    assert s["wheel_speed_fl"]["v"] > MockSlabsDataSource().poll()["signals"]["wheel_speed_fl"]["v"]


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


# ---- dashboard CLI -------------------------------------------------------- #

def test_dashboard_mock_docker_run_is_not_public_and_uses_mock_gps(tmp_path, monkeypatch):
    """The Docker/homelab command (`--mock --host 0.0.0.0`) is mock, NOT public, with the
    mock GPS and the recorder on (sessions there are mock-generated)."""
    import importlib.util
    import pathlib
    import sys

    from d2diag.web import server as server_mod

    captured = {}

    def fake_serve(self):
        captured["srv"] = self

    monkeypatch.setattr(server_mod.DiagServer, "serve", fake_serve)
    import signal
    monkeypatch.setattr(signal, "signal", lambda *a: None)  # keep pytest's SIGTERM handling
    path = pathlib.Path(__file__).resolve().parent.parent / "tools" / "dashboard.py"
    spec = importlib.util.spec_from_file_location("_dashboard_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["dashboard.py", "--mock", "--host", "127.0.0.1",
                                      "--port", "0", "--sessions-dir", str(tmp_path / "s")])
    assert mod.main() == 0
    srv = captured["srv"]
    try:
        assert srv._public is False and srv._mode == "mock"
        assert srv.gps is not None and srv.gps.src == "mock"
        assert srv._sessions_dir == str(tmp_path / "s")
        assert srv._recorder is not None
    finally:
        srv.stop()
        srv.server_close()

    # --gps none → no GPS source, snapshot gps null
    monkeypatch.setattr(sys, "argv", ["dashboard.py", "--mock", "--gps", "none", "--host",
                                      "127.0.0.1", "--port", "0",
                                      "--sessions-dir", str(tmp_path / "s")])
    assert mod.main() == 0
    srv = captured["srv"]
    try:
        assert srv.gps is None and srv.latest["gps"] is None
    finally:
        srv.stop()
        srv.server_close()
