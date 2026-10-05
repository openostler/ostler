"""Replay API over HTTP (specs/2026-10-05-replay-notes-capture-design.md, ADR-0010).

The server side only: the events/notes/audio/accel routes, the public and synthetic
refusals, command events, ``recording_options`` + the snapshot ``recording_sources``,
mock ``read_block``, the ``/captures`` merge and the TLS switch. The recorder, notes log,
audio writer and IMU are tested in their own files. Polls are driven by hand.
"""
import json
import os
import shutil
import ssl
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from d2diag.web import MockDataSource, MockSlabsDataSource
from d2diag.web.server import DiagServer, _parse_range

DEMO = "20261005T090000Z"  # the committed synthetic demo session
REPO = Path(__file__).resolve().parents[1]


def _server(tmp_path, **kw):
    kw.setdefault("csv_dir", str(tmp_path))
    return DiagServer(MockDataSource(), host="127.0.0.1", port=0, **kw)


def _record(srv, n=3):
    for _ in range(n):
        srv.poll_once()
        srv.record_poll()


def _sid(srv):
    return srv.latest["recording"]["session"]


def _events(srv, sid):
    path = Path(srv._sessions_dir) / sid / "events.jsonl"
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


@pytest.fixture
def http():
    """Serve a DiagServer (no poll thread); yields ``start(srv) -> req``.

    ``req(method, path, body=None, headers=None)`` → (code, headers, bytes); a dict body is
    sent as JSON, bytes raw."""
    made = []

    def start(srv, scheme="http", context=None):
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        made.append(srv)
        base = f"{scheme}://127.0.0.1:{srv.server_address[1]}"

        def req(method, path, body=None, headers=None):
            data = json.dumps(body).encode() if isinstance(body, dict) else body
            r = urllib.request.Request(base + path, data=data, method=method,
                                       headers=dict(headers or {}))
            if isinstance(body, dict):
                r.add_header("Content-Type", "application/json")
            try:
                with urllib.request.urlopen(r, timeout=5, context=context) as resp:
                    return resp.status, dict(resp.headers), resp.read()
            except urllib.error.HTTPError as e:
                return e.code, dict(e.headers), e.read()
        return req

    yield start
    for srv in made:
        srv.shutdown()
        srv.server_close()
        srv.stop()


def _j(resp):
    return resp[0], json.loads(resp[2])


# ---- events ---------------------------------------------------------------- #

def test_events_route_and_command_events_without_params(tmp_path, http):
    srv = _server(tmp_path)
    _record(srv)
    sid = _sid(srv)
    # an inline command and a queued module command with params (read_block LIDs)
    assert srv.enqueue_command({"action": "set_fault_watch", "params": {"on": True}})["ok"]
    holder = {"result": None, "event": threading.Event()}
    srv._commands.put(({"action": "read_block", "params": {"lids": ["09"],
                                                          "trust": "experimental"}}, holder))
    srv._drain_commands()
    assert holder["result"]["ok"] and holder["result"]["raws"]["09"]
    _record(srv, 1)
    srv.close_recorder()  # events.jsonl is synced at most once a second while recording
    req = http(srv)
    code, body = _j(req("GET", f"/sessions/{sid}/events"))
    assert code == 200 and body["id"] == sid
    events = body["events"]
    assert events[0]["type"] == "state"
    cmds = [e for e in events if e["type"] == "command"]
    assert {c["action"] for c in cmds} >= {"set_fault_watch", "read_block"}
    for c in cmds:
        assert set(c) <= {"t", "type", "action", "ok", "message", "error"}
    text = (Path(srv._sessions_dir) / sid / "events.jsonl").read_text()
    assert "lids" not in text and "trust" not in text
    assert holder["result"]["raws"]["09"] not in text  # never the read payload
    # unknown and demo sessions
    assert req("GET", "/sessions/nope/events")[0] == 404
    code, body = _j(req("GET", f"/sessions/{DEMO}/events"))
    assert code == 200 and isinstance(body["events"], list)


def test_refused_module_command_is_an_event(tmp_path):
    srv = _server(tmp_path)
    _record(srv)
    res = srv.enqueue_command({"action": "output_no_such_thing"})
    assert not res["ok"]
    sid = _sid(srv)
    srv.close_recorder()
    ev = [e for e in _events(srv, sid) if e["type"] == "command"]
    assert ev and ev[-1]["action"] == "output_no_such_thing" and ev[-1]["ok"] is False


# ---- notes ----------------------------------------------------------------- #

def test_notes_crud(tmp_path, http):
    srv = _server(tmp_path)
    _record(srv)
    sid = _sid(srv)
    req = http(srv)
    code, body = _j(req("POST", f"/sessions/{sid}/notes",
                        {"t": 1500, "t_end": 4000, "text": "rough idle", "tags": ["issue"]}))
    assert code == 200 and body["ok"] and body["session"] == sid
    note = body["note"]
    assert note["source"] == "retro" and note["kind"] == "note" and note["t_end"] == 4000
    nid = note["id"]
    code, body = _j(req("PATCH", f"/sessions/{sid}/notes/{nid}", {"text": "rough idle, cold"}))
    assert code == 200 and body["note"]["text"] == "rough idle, cold" and body["note"]["edited"]
    code, body = _j(req("GET", f"/sessions/{sid}/notes"))
    assert code == 200 and [n["text"] for n in body["notes"]] == ["rough idle, cold"]
    code, headers, csv_body = req("GET", f"/sessions/{sid}/export?fmt=notes")
    assert code == 200 and headers["Content-Type"].startswith("text/csv")
    assert b"rough idle, cold" in csv_body
    code, body = _j(req("DELETE", f"/sessions/{sid}/notes/{nid}"))
    assert code == 200 and body == {"ok": True}
    assert _j(req("GET", f"/sessions/{sid}/notes"))[1]["notes"] == []
    # errors
    assert req("DELETE", f"/sessions/{sid}/notes/{nid}")[0] == 404
    assert req("PATCH", f"/sessions/{sid}/notes/zzzz", {"text": "x"})[0] == 404
    assert req("POST", f"/sessions/{sid}/notes", {"text": "no t"})[0] == 400
    assert req("POST", f"/sessions/{sid}/notes", {"t": 5, "t_end": 1})[0] == 400
    assert req("POST", f"/sessions/{sid}/notes", {"t": 5, "kind": "bogus"})[0] == 400
    assert req("POST", f"/sessions/{sid}/notes", b"not json",
               {"Content-Type": "application/json"})[0] == 400
    assert req("POST", "/sessions/nope/notes", {"t": 1})[0] == 404


def test_synthetic_sessions_are_read_only(tmp_path, http):
    srv = _server(tmp_path)
    req = http(srv)
    assert _j(req("GET", f"/sessions/{DEMO}/notes"))[0] == 200
    for method, path, body in (
            ("POST", f"/sessions/{DEMO}/notes", {"t": 1, "text": "x"}),
            ("PATCH", f"/sessions/{DEMO}/notes/a1b2c3d4", {"text": "x"}),
            ("DELETE", f"/sessions/{DEMO}/notes/a1b2c3d4", None),
            ("POST", f"/sessions/{DEMO}/accel", {"samples": []}),
            ("POST", f"/sessions/{DEMO}/accel_cal", {"matrix": [[1, 0, 0]] * 3}),
            ("POST", f"/sessions/{DEMO}/audio?track=abc&seq=0", b"x")):
        code, out = _j(req(method, path, body))
        assert code == 403 and out["error"] == "synthetic sessions are read-only", path


def test_public_mode_refuses_writes_and_hides_real_sessions(tmp_path, http):
    priv = _server(tmp_path)
    _record(priv)
    sid = _sid(priv)
    priv.close_recorder()
    priv.server_close()
    srv = _server(tmp_path, public=True)
    req = http(srv)
    # real sessions do not exist in public mode; the demo does (read-only)
    assert req("GET", f"/sessions/{sid}/notes")[0] == 404
    assert req("GET", f"/sessions/{sid}/events")[0] == 404
    assert _j(req("GET", f"/sessions/{DEMO}/notes"))[0] == 200
    for method, path, body in (
            ("POST", f"/sessions/{sid}/notes", {"t": 1}),
            ("PATCH", f"/sessions/{sid}/notes/a1b2c3d4", {"text": "x"}),
            ("DELETE", f"/sessions/{sid}/notes/a1b2c3d4", None),
            ("POST", "/notes/live", {"kind": "mark"}),
            ("POST", f"/sessions/{sid}/accel", {"samples": []}),
            ("POST", f"/sessions/{sid}/accel_cal", {"matrix": [[1, 0, 0]] * 3}),
            ("POST", f"/sessions/{sid}/audio?track=abc&seq=0", b"x"),
            ("POST", f"/sessions/{DEMO}/notes", {"t": 1})):
        code, out = _j(req(method, path, body))
        assert code == 403 and out["error"] == "not available in public mode", path
    assert not (Path(srv._sessions_dir) / sid / "notes.jsonl").exists()


def test_live_note_starts_a_session(tmp_path, http):
    srv = _server(tmp_path)
    assert srv.latest.get("recording") is None  # nothing polled: nothing recording
    req = http(srv)
    code, body = _j(req("POST", "/notes/live", {"kind": "mark"}))
    assert code == 200 and body["ok"]
    sid = body["session"]
    assert body["note"]["source"] == "live" and body["note"]["kind"] == "mark"
    assert srv.latest["recording"]["session"] == sid
    code, body = _j(req("POST", "/notes/live", {"kind": "note", "text": "noise", "tags": ["noise"]}))
    assert code == 200 and body["session"] == sid
    notes = _j(req("GET", f"/sessions/{sid}/notes"))[1]["notes"]
    assert [n["kind"] for n in notes] == ["mark", "note"]
    assert req("POST", "/notes/live", {"kind": "nope"})[0] == 400


def test_live_note_without_recorder(tmp_path, http):
    srv = _server(tmp_path, record_sessions=False)
    req = http(srv)
    assert req("POST", "/notes/live", {"kind": "mark"})[0] == 503


# ---- audio ----------------------------------------------------------------- #

def test_audio_chunks_range_and_privacy(tmp_path, http):
    srv = _server(tmp_path)
    _record(srv)
    sid = _sid(srv)
    req = http(srv)
    base = f"/sessions/{sid}/audio?track=t1&mime=audio/webm"
    assert _j(req("POST", base + "&seq=1", b"WORLD"))[0] == 200  # early: held
    code, body = _j(req("POST", base + "&seq=0&start=0", b"HELLO"))
    assert code == 200 and body["bytes"] == 10
    assert _j(req("POST", base + "&seq=2&end=1", b"!"))[1]["closed"] is True
    meta = json.loads((Path(srv._sessions_dir) / sid / "meta.json").read_text())
    assert any(a["track"] == "t1" and a["source"] == "phone" for a in meta.get("audio", []))

    code, headers, data = req("GET", f"/sessions/{sid}/audio/t1")
    assert code == 200 and data == b"HELLOWORLD!"
    assert headers["Accept-Ranges"] == "bytes" and headers["Content-Type"] == "audio/webm"
    code, headers, data = req("GET", f"/sessions/{sid}/audio/t1", headers={"Range": "bytes=2-5"})
    assert code == 206 and data == b"LLOW" and headers["Content-Range"] == "bytes 2-5/11"
    code, headers, data = req("GET", f"/sessions/{sid}/audio/t1", headers={"Range": "bytes=-3"})
    assert code == 206 and data == b"LD!"
    code, headers, data = req("GET", f"/sessions/{sid}/audio/t1", headers={"Range": "bytes=7-"})
    assert code == 206 and data == b"RLD!"
    code, headers, _ = req("GET", f"/sessions/{sid}/audio/t1", headers={"Range": "bytes=50-60"})
    assert code == 416 and headers["Content-Range"] == "bytes */11"
    assert req("GET", f"/sessions/{sid}/audio/nope")[0] == 404
    assert req("GET", f"/sessions/{sid}/audio/..%2fmeta.json")[0] == 404

    # bad requests
    assert req("POST", f"/sessions/{sid}/audio?track=bad/track&seq=0", b"x")[0] in (400, 404)
    assert req("POST", f"/sessions/{sid}/audio?track=t2&seq=x", b"x")[0] == 400
    assert req("POST", f"/sessions/{sid}/audio?track=t2&seq=0&mime=text/html", b"x")[0] == 400
    big = b"\0" * (2 * 1024 * 1024 + 1)
    assert req("POST", f"/sessions/{sid}/audio?track=t3&seq=0", big)[0] == 413

    srv.close_recorder()
    states = [e["state"] for e in _events(srv, sid) if e["type"] == "audio"]
    assert states == ["start", "stop"]
    # never served in public mode, even with the file present
    srv._public = True
    assert req("GET", f"/sessions/{sid}/audio/t1")[0] == 404


def test_audio_into_a_session_that_is_not_recording(tmp_path, http):
    srv = _server(tmp_path)
    _record(srv)
    sid = _sid(srv)
    srv.close_recorder()
    req = http(srv)
    assert req("POST", f"/sessions/{sid}/audio?track=t1&seq=0", b"x")[0] == 409


def test_range_parser():
    assert _parse_range(None, 10) is None
    assert _parse_range("bytes=0-", 10) == (0, 9)
    assert _parse_range("bytes=3-100", 10) == (3, 9)
    assert _parse_range("bytes=-4", 10) == (6, 9)
    assert _parse_range("bytes=10-", 10) == "invalid"
    assert _parse_range("bytes=5-2", 10) == "invalid"
    assert _parse_range("bytes=0-1,4-5", 10) is None  # multi-range: served whole
    assert _parse_range("items=1-2", 10) == "invalid"


# ---- acceleration ---------------------------------------------------------- #

def test_accel_and_calibration(tmp_path, http):
    srv = _server(tmp_path)
    _record(srv)
    sid = _sid(srv)
    since_ms = srv.latest["recording"]["since"] * 1000
    req = http(srv)
    cal = {"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 1]], "source": "phone", "method": "level"}
    code, body = _j(req("POST", f"/sessions/{sid}/accel_cal", cal))
    assert code == 200 and body["accel_cal"]["method"] == "level"
    samples = [[since_ms + 100 + 40 * i, 1.0, 0.5, 9.8] for i in range(5)]
    code, body = _j(req("POST", f"/sessions/{sid}/accel", {"source": "phone", "samples": samples}))
    assert code == 200 and body["samples"] == 5 and body["rows"] == 5
    ev = [e for e in _events(srv, sid) if e["type"] == "accel_cal"]
    assert len(ev) == 1 and ev[0]["matrix"] == cal["matrix"]
    srv.close_recorder()
    data = srv.session_store.data(sid, ["Acc_X", "InlineAcc"])
    assert any(v is not None for v in data["ch"]["Acc_X"])
    # validation
    assert req("POST", f"/sessions/{sid}/accel", {"samples": [[1, 2, 3]]})[0] == 400
    assert req("POST", f"/sessions/{sid}/accel", {"samples": "x"})[0] == 400
    assert req("POST", f"/sessions/{sid}/accel_cal", {"matrix": [[1, 0]]})[0] == 400
    # the session ended: nothing is recording it any more
    assert req("POST", f"/sessions/{sid}/accel", {"samples": samples})[0] == 409


# ---- recording options / sources ------------------------------------------- #

class FakePiAudio:
    MIME = "audio/wav"

    def __init__(self, ok=True):
        self.ok, self.running, self.started = ok, False, []

    def available(self):
        return (True, None) if self.ok else (False, "arecord not found (install alsa-utils)")

    def start(self, session_dir):
        self.running = True
        self.started.append(session_dir)
        return "pitrack1"

    def stop(self):
        self.running = False
        return 0


def test_recording_options_and_sources(tmp_path):
    pi = FakePiAudio()
    srv = _server(tmp_path, audio="pi", imu="mock", pi_audio=pi)
    rs = srv.latest["recording_sources"]
    assert rs == {"gps": "none", "pi_audio": {"state": "available", "reason": None},
                  "imu": {"state": "available", "reason": None}, "accel_hz": 25}
    _record(srv)
    sid = _sid(srv)
    res = srv.enqueue_command({"action": "recording_options",
                               "params": {"audio": "pi", "imu": "on", "accel_hz": 50}})
    assert res == {"ok": True, "options": {"audio": "pi", "imu": "on", "accel_hz": 50}}
    assert pi.started and pi.started[0].endswith(sid)
    rs = srv.latest["recording_sources"]
    assert rs["pi_audio"]["state"] == "on" and rs["imu"]["state"] == "on"
    assert rs["accel_hz"] == 50
    srv._imu_reader.poll_once()  # deterministic: one sample without waiting on the thread
    _record(srv, 1)
    assert srv._recorder._s.accel_rows >= 1
    # off again
    res = srv.enqueue_command({"action": "recording_options",
                               "params": {"audio": "off", "imu": "off"}})
    assert res["ok"] and not pi.running and srv._imu_reader is None
    assert srv.latest["recording_sources"]["imu"]["state"] == "available"
    srv.close_recorder()
    pi_states = [e["state"] for e in _events(srv, sid)
                 if e["type"] == "audio" and e["source"] == "pi"]
    assert pi_states == ["start", "stop"]
    # validation
    for bad in ({"audio": "phone"}, {"imu": 1}, {"accel_hz": 30}, {"accel_hz": True}):
        res = srv.enqueue_command({"action": "recording_options", "params": bad})
        assert not res["ok"] and res["options"]["audio"] == "off"
    srv.stop()
    srv.server_close()


def test_recording_sources_unavailable(tmp_path):
    srv = _server(tmp_path)  # --audio off, --imu none
    rs = srv.recording_sources()
    assert rs["pi_audio"]["state"] == "unavailable" and "--audio pi" in rs["pi_audio"]["reason"]
    assert rs["imu"]["state"] == "unavailable" and rs["imu"]["reason"]
    res = srv.enqueue_command({"action": "recording_options", "params": {"audio": "pi"}})
    assert not res["ok"] and "Pi audio unavailable" in res["error"]
    res = srv.enqueue_command({"action": "recording_options", "params": {"imu": "on"}})
    assert not res["ok"] and "IMU unavailable" in res["error"]
    srv2 = _server(tmp_path, audio="pi", pi_audio=FakePiAudio(ok=False))
    st = srv2.recording_sources()["pi_audio"]
    assert st == {"state": "unavailable", "reason": "arecord not found (install alsa-utils)"}
    srv.server_close()
    srv2.server_close()


# ---- mock read_block ------------------------------------------------------- #

def test_mock_read_block_round_trips_through_the_store():
    from d2diag.signals import load_signals

    src = MockDataSource()
    snap = src.poll()
    res = src.command("read_block", {"lids": ["09", "10", "1a", "ee"]})
    assert res["ok"] and set(res["raws"]) == {"09", "10", "1a"}  # unknown LID skipped
    sigs = {s.name: s for s in load_signals("td5")}
    raw = bytes.fromhex(res["raws"]["09"])
    assert sigs["rpm"].decode(raw) == pytest.approx(snap["signals"]["rpm"]["v"], abs=1)
    raw = bytes.fromhex(res["raws"]["1a"])
    assert sigs["coolant_temp"].decode(raw) == pytest.approx(
        snap["signals"]["coolant_temp"]["v"], abs=0.1)
    again = src.command("read_block", {"lids": ["09"]})
    assert again["raws"]["09"] == res["raws"]["09"]  # deterministic per poll
    assert src.command("read_block", {"lids": ["zz"]}) == {
        "ok": False, "error": 'invalid lids (expected hex strings such as "09")'}
    slabs = MockSlabsDataSource()
    s_snap = slabs.poll()
    res = slabs.command("read_block", {"lids": ["54"]})
    ssig = {s.name: s for s in load_signals("slabs")}
    assert ssig["height_left"].decode(bytes.fromhex(res["raws"]["54"])) == pytest.approx(
        s_snap["signals"]["height_left"]["v"], abs=1)


def test_mock_read_block_through_the_command_route(tmp_path):
    srv = _server(tmp_path)
    srv.poll_once()
    holder = {"result": None, "event": threading.Event()}
    srv._commands.put(({"action": "read_block", "params": {"lids": ["09"]}}, holder))
    srv._drain_commands()
    assert holder["result"]["ok"] and len(holder["result"]["raws"]["09"]) == 4
    srv.server_close()


def test_no_swedish_in_sources():
    text = (REPO / "src/d2diag/web/sources.py").read_text(encoding="utf-8")
    assert "ogiltiga" not in text and "Swedish label" not in text


# ---- captures -------------------------------------------------------------- #

def test_capture_becomes_a_note_and_captures_merge(tmp_path, http):
    cap_path = tmp_path / "labeled_captures.jsonl"
    cap_path.write_text(json.dumps({"t": "2026-10-01 10:00:00", "module": "slabs",
                                    "lid": "54", "raw": "8f 9f", "text": "143"}) + "\n")
    srv = _server(tmp_path, captures_path=str(cap_path))
    _record(srv)
    sid = _sid(srv)
    req = http(srv)
    cap = {"module": "td5", "lid": "09", "raw": "02 fa", "text": "762 rpm"}
    assert _j(req("POST", "/capture", cap)) == (200, {"ok": True, "stored": True})
    # the UI's Label save also posts the same capture as a live note: one note, not two
    code, body = _j(req("POST", "/notes/live", {"kind": "capture", "text": "762 rpm",
                                                "capture": {**cap, "value": "762 rpm"}}))
    assert code == 200
    notes = _j(req("GET", f"/sessions/{sid}/notes"))[1]["notes"]
    assert len(notes) == 1 and notes[0]["kind"] == "capture"
    assert notes[0]["capture"] == {"module": "td5", "lid": "09", "raw": "02 fa",
                                   "value": "762 rpm"}

    code, body = _j(req("GET", "/captures"))
    assert code == 200
    rows = {(c["module"], c["lid"]): c for c in body["captures"]}
    assert set(rows) == {("td5", "09"), ("slabs", "54")}  # the jsonl duplicate is merged
    assert rows[("td5", "09")]["session"] == sid and rows[("td5", "09")]["t"] is not None
    assert rows[("slabs", "54")] == {"module": "slabs", "lid": "54", "raw": "8f 9f",
                                     "value": "143", "t": None, "session": None}
    only = _j(req("GET", "/captures?module=motor"))[1]["captures"]
    assert [c["lid"] for c in only] == ["09"]


def test_capture_without_recording_starts_no_session(tmp_path, http):
    srv = _server(tmp_path, captures_path=str(tmp_path / "c.jsonl"))
    req = http(srv)
    assert _j(req("POST", "/capture", {"module": "td5", "lid": "09", "raw": "02 fa",
                                       "text": "762"}))[0] == 200
    assert srv._recording_status() is None
    assert _j(req("GET", "/captures"))[1]["captures"][0]["session"] is None


def test_captures_is_admin_gated(tmp_path, http):
    srv = _server(tmp_path, admin_password="pw")
    req = http(srv)
    assert req("GET", "/captures")[0] == 401


# ---- TLS -------------------------------------------------------------------- #

def _self_signed(tmp_path):
    if shutil.which("openssl") is None:
        pytest.skip("openssl not available")
    cert, key = tmp_path / "c.pem", tmp_path / "k.pem"
    r = subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(key), "-out", str(cert), "-days", "1",
                        "-subj", "/CN=localhost"], capture_output=True, timeout=60)
    if r.returncode != 0:
        pytest.skip("openssl could not make a certificate")
    return str(cert), str(key)


def test_tls_serves_https(tmp_path, http):
    cert, key = _self_signed(tmp_path)
    srv = _server(tmp_path)
    srv.enable_tls(cert, key)
    ctx = ssl.create_default_context(cafile=cert)
    ctx.check_hostname = False
    req = http(srv, scheme="https", context=ctx)
    code, _, body = req("GET", "/snapshot")
    assert code == 200 and "recording_sources" in json.loads(body)
    # a plain-HTTP client is dropped without killing the server
    with pytest.raises((urllib.error.URLError, ConnectionError, OSError)):
        urllib.request.urlopen(f"http://127.0.0.1:{srv.server_address[1]}/snapshot", timeout=3)
    assert req("GET", "/snapshot")[0] == 200


def test_dashboard_tls_flags_must_come_together():
    r = subprocess.run([sys.executable, str(REPO / "tools/dashboard.py"), "--mock",
                        "--tls-cert", "x.pem"], capture_output=True, text=True, timeout=60,
                       env={**os.environ, "PYTHONPATH": str(REPO / "src")})
    assert r.returncode == 2 and "--tls-cert and --tls-key must be given together" in r.stderr


def test_demo_sniff_log_is_committed_and_packaged():
    demo = REPO / "src/d2diag/web/demo/sniff-demo.txt"
    from d2diag.web.sniffer import SnifferFeed

    feed = SnifferFeed.from_file(str(demo), delay=0, loop=False)
    feed._run()
    snap = feed.snapshot("td5")
    assert snap["frames"] > 100 and {x["lid"] for x in snap["lids"]} >= {"09", "10"}
    assert "demo/*.txt" in (REPO / "pyproject.toml").read_text()
    assert "src/d2diag/web/demo/sniff-demo.txt" in (REPO / "Dockerfile").read_text()


# ---- split / name / data passthrough ---------------------------------------- #

def test_split_session(tmp_path):
    srv = _server(tmp_path)
    _record(srv)
    first = _sid(srv)
    res = srv.enqueue_command({"action": "split_session"})
    assert res["ok"] and res["session"] != first
    assert srv.latest["recording"]["session"] == res["session"]
    meta = json.loads((Path(srv._sessions_dir) / first / "meta.json").read_text())
    assert meta["recording"] is False  # the old one is closed
    _record(srv, 1)
    assert _sid(srv) == res["session"]
    srv.stop()
    srv.server_close()
    # nothing recording: a split just starts one
    srv2 = _server(tmp_path / "b")
    res = srv2.enqueue_command({"action": "split_session"})
    assert res["ok"] and srv2.latest["recording"]["session"] == res["session"]
    srv2.stop()
    srv2.server_close()


def test_split_session_refused_in_public_mode(tmp_path):
    srv = _server(tmp_path, public=True)
    res = srv.enqueue_command({"action": "split_session"})
    assert not res["ok"] and "public mode" in res["error"]
    srv.server_close()


def test_recording_options_accepts_a_session_name(tmp_path):
    srv = _server(tmp_path)
    named = []
    if not hasattr(srv._recorder, "set_name"):
        srv._recorder.set_name = named.append  # the recorder's hook when it has one
    res = srv.enqueue_command({"action": "recording_options",
                               "params": {"name": "  Morning   run "}})
    assert res["ok"] and srv._session_name == "Morning run"
    assert not named or named == ["Morning run"]
    res = srv.enqueue_command({"action": "recording_options", "params": {"name": 5}})
    assert not res["ok"] and res["error"] == "name must be a string"
    srv.server_close()


def test_session_data_passes_store_keys_through(tmp_path, http):
    srv = _server(tmp_path)
    real = srv.session_store.data
    srv.session_store.data = lambda *a, **k: {**real(*a, **k),
                                              "text": {"faults": [], "module": []}}
    req = http(srv)
    code, body = _j(req("GET", f"/sessions/{DEMO}/data?ch=rpm&max=10"))
    assert code == 200 and body["text"] == {"faults": [], "module": []}
