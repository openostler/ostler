"""Session recorder and store (ADR-0009, specs/2026-10-05-session-logbook-design.md)."""
import json
import os
import re
from collections import namedtuple

import pytest

from d2diag.gps.nmea import Fix
from d2diag.logbook import recorder as recmod
from d2diag.logbook.demo import DEMO_ROOT
from d2diag.logbook.recorder import IDLE_S, SessionRecorder, parse_header, rotate_sessions
from d2diag.logbook.store import SessionStore, rdp, read_part, reduce_track
from d2diag.logbook.synth import generate

T0 = 1791277200.0  # 2026-10-06T09:00:00Z (a day after the demo session)
META_KEYS = {"id", "name", "start_utc", "end_utc", "duration_s", "rows", "parts", "modules",
             "channels", "has_gps", "distance_km", "max_speed_kmh", "bbox", "start_pos",
             "end_pos", "synthetic", "recording", "source", "audio", "accel_cal"}


class Clock:
    def __init__(self):
        self.t = 0.0

    def clock(self):
        return T0 + self.t

    def mono(self):
        return 1000.0 + self.t


def snap(connected=True, **signals):
    return {"conn": "connected" if connected else "lost", "module": "motor", "mode": "live",
            "faults": [], "signals": {k: {"v": v, "u": "x"} for k, v in signals.items()}}


def fix(c, lat=56.62, lon=-4.68, speed=0.0):
    return Fix(utc_ms=int(c.clock() * 1000), lat=lat, lon=lon, speed_kmh=speed, heading=90.0,
               alt_m=300.0, sats=9, hdop=0.8, fix=True, mono=c.mono())


def make(tmp_path, **kw):
    c = Clock()
    kw.setdefault("min_free_bytes", 0)
    r = SessionRecorder(str(tmp_path / "sessions"), clock=c.clock, mono=c.mono, **kw)
    return c, r


def meta_of(tmp_path, sid):
    with open(tmp_path / "sessions" / sid / "meta.json", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------ recorder -- #

def test_no_session_while_idle(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(connected=False), None)
    r.feed(snap(connected=False), fix(c, speed=2.9))
    assert r.status() is None
    assert not os.path.exists(tmp_path / "sessions") or not os.listdir(tmp_path / "sessions")


def test_starts_on_connect_and_ends_after_idle(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800), None)
    st = r.status()
    assert st["session"] == "20261006T090000Z" and st["since"] == T0 and st["rows"] == 1
    m = meta_of(tmp_path, st["session"])
    assert set(m) == META_KEYS and m["recording"] is True and m["end_utc"] is None
    assert m["source"] == "live" and m["synthetic"] is False
    while c.t < IDLE_S - 1:  # disconnected, no GPS
        c.t += 1.0
        r.feed(snap(connected=False), None)
        assert r.status() is not None
    c.t = IDLE_S
    r.feed(snap(connected=False), None)
    assert r.status() is None
    m = meta_of(tmp_path, st["session"])
    assert m["recording"] is False and m["end_utc"] == "2026-10-06T09:05:00.000Z"
    assert m["duration_s"] == 300 and m["modules"] == ["motor"]


def test_starts_on_gps_movement_and_movement_keeps_it_open(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(connected=False), fix(c, speed=3.5))
    assert r.status() is not None
    for _ in range(400):  # moving, never connected
        c.t += 1.0
        r.feed(snap(connected=False), fix(c, lat=56.62 + c.t * 1e-5, speed=20.0))
    assert r.status() is not None
    m = meta_of(tmp_path, r.status()["session"])
    assert m["has_gps"] is True and m["modules"] == []


def test_id_collision_suffix(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=1), None)
    r.close()
    r.feed(snap(rpm=1), None)
    assert r.status()["session"] == "20261006T090000Z-1"


def test_sparse_rows_and_header(tmp_path):
    c, r = make(tmp_path, poll_hz=5)
    r.feed(snap(rpm=800, coolant_temp=80.5), fix(c, speed=10))
    c.t += 0.2
    r.feed(snap(connected=False), fix(c, speed=12))  # GPS only
    c.t += 0.2
    r.feed(snap(rpm=810), None)  # rpm only
    sid = r.status()["session"]
    r.close()
    path = tmp_path / "sessions" / sid / "data.csv"
    lines = path.read_text(encoding="utf-8").split("\n")
    cells = lines[0].split(",")
    assert cells[0] == '"Interval"|"ms"|10' and cells[1] == '"Utc"|"ms"|10'
    assert all(re.fullmatch(r'"[^"]+"\|"[^"]*"\|[0-9]+', c) for c in cells)
    names = [h[0] for h in parse_header(lines[0])]
    assert names[2:9] == ["GPS_Latitude", "GPS_Longitude", "GPS_Speed", "GPS_Heading",
                          "GPS_Altitude", "GPS_Nsat", "GPS_HDOP"]
    assert names[9:11] == ["GPS_LonAcc", "GPS_LatAcc"]
    assert names[11:] == ["rpm", "coolant_temp", "module", "faults"]
    assert '"rpm"|"x"|5' in cells and '"GPS_Speed"|"km/h"|10' in cells
    _, rows = read_part(str(path))
    assert [r_["Interval"] for r_ in rows] == [0, 200, 400]
    assert rows[1].get("rpm") is None and rows[1]["GPS_Speed"] == 12
    assert rows[2].get("GPS_Latitude") is None and rows[2]["rpm"] == 810
    assert rows[0]["Utc"] == int(T0 * 1000)
    assert sorted(os.listdir(tmp_path / "sessions" / sid)) == ["data.csv", "events.jsonl",
                                                               "meta.json"]


def test_new_channel_starts_new_part(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800), None)
    c.t += 0.5
    r.feed(snap(rpm=820), None)
    c.t += 0.5
    r.feed(snap(rpm=830, battery=14.1), None)  # new channel mid-session
    sid = r.status()["session"]
    d = tmp_path / "sessions" / sid
    assert sorted(os.listdir(d)) == ["data-0.csv", "data-1.csv", "events.jsonl", "meta.json"]
    assert meta_of(tmp_path, sid)["parts"] == ["data-0.csv", "data-1.csv"]
    r.close()
    data = SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid, ["rpm", "battery"])
    assert data["t"] == [0, 500, 1000]
    assert data["ch"]["rpm"] == [800, 820, 830] and data["ch"]["battery"] == [None, None, 14.1]


def test_hourly_split(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800), None)
    c.t = 3599.0
    r.feed(snap(rpm=800), None)
    c.t = 3600.5
    r.feed(snap(rpm=801), None)
    assert meta_of(tmp_path, r.status()["session"])["parts"] == ["data-0.csv", "data-1.csv"]


def test_truncated_last_line_ignored(tmp_path):
    c, r = make(tmp_path)
    for i in range(5):
        r.feed(snap(rpm=800 + i), None)
        c.t += 0.5
    sid = r.status()["session"]
    r.close()
    p = tmp_path / "sessions" / sid / "data.csv"
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("3000,179119")  # power cut mid-row
    _, rows = read_part(str(p))
    assert len(rows) == 5
    with open(p, "a", encoding="utf-8") as fh:
        fh.write("0800000,,,\n")  # now a complete but malformed row
    _, rows = read_part(str(p))
    assert len(rows) == 5
    assert SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid)["ch"]["rpm"][-1] == 804


def test_fsync_at_most_once_per_second(tmp_path):
    calls = []
    c, r = make(tmp_path, fsync=calls.append)
    for _ in range(50):  # 10 s at 5 Hz
        r.feed(snap(rpm=800), None)
        c.t += 0.2
    # data.csv once per second, plus events.jsonl once (its state line)
    assert 10 <= len(calls) <= 12
    r.close()
    assert len(calls) <= 13


def test_meta_rewritten_every_30s(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800), None)
    sid = r.status()["session"]
    for _ in range(20):
        c.t += 1.0
        r.feed(snap(rpm=800), None)
    assert meta_of(tmp_path, sid)["rows"] == 0  # written at start, not rewritten yet
    for _ in range(11):
        c.t += 1.0
        r.feed(snap(rpm=800), None)
    m = meta_of(tmp_path, sid)
    assert m["rows"] == 31 and m["duration_s"] == 30
    assert not any(f.endswith(".tmp") for f in os.listdir(tmp_path / "sessions" / sid))


def test_never_records_vin_or_identity(tmp_path):
    c, r = make(tmp_path)
    s = snap(rpm=800)
    s["vin"] = "SALLTGM88XA123456"
    s["identity"] = {"vin": "SALLTGM88XA123456", "eka": "1234"}
    s["signals"]["vin"] = {"v": "SALLTGM88XA123456"}
    s["signals"]["ecu_serial"] = {"v": 123456}
    s["signals"]["eka_code"] = {"v": 4321}
    r.feed(s, None)
    sid = r.status()["session"]
    r.close()
    d = tmp_path / "sessions" / sid
    blob = "".join(p.read_text(encoding="utf-8") for p in d.iterdir())
    assert "SALLT" not in blob and "123456" not in blob and "4321" not in blob
    assert "serial" not in blob and "vin" not in blob.lower()


def test_gps_meta_distance_bbox_rounding(tmp_path):
    c, r = make(tmp_path)
    lat0 = 56.6201234
    for i in range(11):  # 10 steps north of 0.001° ≈ 111.3 m each
        r.feed(snap(rpm=900, speed=40), fix(c, lat=lat0 + i * 0.001, lon=-4.6806789, speed=36.0))
        c.t += 1.0
    sid = r.status()["session"]
    r.close()
    m = meta_of(tmp_path, sid)
    assert m["distance_km"] == pytest.approx(1.11, abs=0.01)
    assert m["start_pos"] == [-4.681, 56.62] and m["end_pos"] == [-4.681, 56.63]
    assert m["bbox"][1] < m["bbox"][3] and m["bbox"][0] == m["bbox"][2]
    assert m["max_speed_kmh"] == 40.0  # ECU speed beats GPS here
    names = [x["name"] for x in m["channels"]]
    assert "GPS_Speed" in names and "rpm" in names and "module" not in names


def test_gps_capped_at_10hz_and_needs_new_fix(tmp_path):
    c, r = make(tmp_path)
    f = fix(c, speed=20)
    r.feed(snap(rpm=1), f)
    c.t += 0.05
    r.feed(snap(rpm=2), fix(c, speed=20))  # too soon after the last GPS row
    c.t += 0.1
    r.feed(snap(rpm=3), f)  # same (stale) fix
    sid = r.status()["session"]
    r.close()
    _, rows = read_part(str(tmp_path / "sessions" / sid / "data.csv"))
    assert [("GPS_Latitude" in x) for x in rows] == [True, False, False]


def test_source_from_snapshot_mode_and_crash_recovery(tmp_path):
    c, r = make(tmp_path)
    s = snap(rpm=1)
    s["mode"] = "mock"
    r.feed(s, None)
    sid = r.status()["session"]
    assert meta_of(tmp_path, sid)["source"] == "mock"
    # simulate a crash: a new recorder finds the session still "recording"
    c2, r2 = make(tmp_path)
    m = meta_of(tmp_path, sid)
    assert m["recording"] is False and m["end_utc"] == "2026-10-06T09:00:00.000Z"


def test_rotation_deletes_oldest_real_first(tmp_path):
    root = tmp_path / "sessions"
    for sid, synthetic in (("20260101T000000Z", False), ("20250101T000000Z", True),
                           ("20260201T000000Z", False), ("20260301T000000Z", False)):
        (root / sid).mkdir(parents=True)
        (root / sid / "meta.json").write_text(json.dumps({"id": sid, "synthetic": synthetic}))
    Usage = namedtuple("Usage", "total used free")
    state = {"free": 50}

    def usage(_):
        return Usage(1000, 1000 - state["free"], state["free"])

    real_rmtree = recmod.shutil.rmtree

    def rmtree(p, **kw):
        state["free"] += 30
        real_rmtree(p, **kw)

    recmod.shutil.rmtree = rmtree
    try:
        gone = rotate_sessions(str(root), 100, usage=usage, keep={"20260301T000000Z"})
    finally:
        recmod.shutil.rmtree = real_rmtree
    assert gone == ["20260101T000000Z", "20260201T000000Z"]
    assert sorted(os.listdir(root)) == ["20250101T000000Z", "20260301T000000Z"]


# --------------------------------------------------------------------- store -- #

def _recorded(tmp_path):
    c, r = make(tmp_path)
    for i in range(10):
        r.feed(snap(rpm=800 + i), fix(c, speed=10.0 + i))
        c.t += 0.5
    sid = r.status()["session"]
    r.close()
    return sid


def test_store_public_filter_and_order(tmp_path):
    sid = _recorded(tmp_path)
    store = SessionStore(str(tmp_path / "sessions"))
    ids = [m["id"] for m in store.list()]
    assert sid in ids and "20261005T090000Z" in ids
    pub = store.list(public=True)
    assert pub and all(m["synthetic"] for m in pub)
    assert store.meta("20261005T090000Z", public=True)["source"] == "demo"


def test_store_list_newest_first(tmp_path):
    root = tmp_path / "sessions"
    for sid, start in (("20260101T000000Z", "2026-01-01T00:00:00.000Z"),
                       ("20260301T000000Z", "2026-03-01T00:00:00.000Z"),
                       ("20260201T000000Z", "2026-02-01T00:00:00.000Z")):
        (root / sid).mkdir(parents=True)
        (root / sid / "meta.json").write_text(json.dumps({"id": sid, "start_utc": start}))
    ids = [m["id"] for m in SessionStore(str(root), demo_root=None).list()]
    assert ids == ["20260301T000000Z", "20260201T000000Z", "20260101T000000Z"]


def test_store_unknown_and_public_hidden(tmp_path):
    sid = _recorded(tmp_path)
    store = SessionStore(str(tmp_path / "sessions"))
    for bad in ("nope", "../etc", "", "20991231T000000Z"):
        with pytest.raises(KeyError):
            store.meta(bad)
    with pytest.raises(KeyError):
        store.meta(sid, public=True)
    with pytest.raises(KeyError):
        store.data(sid, public=True)
    with pytest.raises(KeyError):
        store.export(sid, "csv", public=True)


def test_store_data_shape(tmp_path):
    sid = _recorded(tmp_path)
    d = SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid, "rpm,GPS_Speed,nope")
    assert set(d) == {"id", "t", "utc", "ch", "text", "track", "decimated"}
    assert d["text"]["module"] == ["motor"] * 10 and d["text"]["faults"] == [None] * 10
    assert set(d["ch"]) == {"rpm", "GPS_Speed"} and d["decimated"] is False
    assert len(d["t"]) == len(d["utc"]) == len(d["ch"]["rpm"]) == 10
    assert d["track"][0] == [-4.68, 56.62, 0] and len(d["track"]) == 10


def test_decimation_keeps_min_and_max(tmp_path):
    c, r = make(tmp_path)
    for i in range(5000):
        v = 1000 + (i % 37)
        if i == 1234:
            v = 4321  # a single-sample spike
        if i == 3210:
            v = -5
        r.feed(snap(rpm=v), None)
        c.t += 0.2
    sid = r.status()["session"]
    r.close()
    d = SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid, ["rpm"], max_points=500)
    assert d["decimated"] is True and len(d["t"]) <= 500
    assert max(d["ch"]["rpm"]) == 4321 and min(d["ch"]["rpm"]) == -5
    assert d["t"] == sorted(d["t"])


def test_rdp_reduces_long_track():
    import math
    pts = [[-4.68 + 0.01 * math.cos(i / 500), 56.62 + 0.01 * math.sin(i / 500), i * 100]
           for i in range(12000)]
    out = reduce_track(pts)
    assert 2 <= len(out) <= 5000 and out[0] == pts[0] and out[-1] == pts[-1]
    line = [[0, 0, 0], [1, 0.0000001, 1], [2, 0, 2]]
    assert rdp(line, 0.001) == [[0, 0, 0], [2, 0, 2]]
    assert reduce_track(pts[:100]) == pts[:100]


def test_delete_refuses_demo_and_deletes_real(tmp_path):
    sid = _recorded(tmp_path)
    store = SessionStore(str(tmp_path / "sessions"))
    with pytest.raises(PermissionError):
        store.delete("20261005T090000Z")
    assert os.path.exists(os.path.join(DEMO_ROOT, "20261005T090000Z", "data-0.csv"))
    store.delete(sid)
    assert sid not in [m["id"] for m in store.list()]
    with pytest.raises(KeyError):
        store.delete(sid)


def test_delete_refuses_live_session(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=1), None)
    with pytest.raises(PermissionError):
        SessionStore(str(tmp_path / "sessions")).delete(r.status()["session"])


def test_demo_session_is_synthetic_and_listed(tmp_path):
    store = SessionStore(str(tmp_path / "none"))
    (m,) = store.list(public=True)
    assert m["synthetic"] is True and m["source"] == "demo" and m["has_gps"] is True
    assert 600 <= m["duration_s"] <= 800 and m["rows"] >= 3000
    d = store.data(m["id"], ["speed", "rpm"])
    assert d["decimated"] is True and d["track"] and len(d["track"]) <= 5000
    size = sum(os.path.getsize(os.path.join(DEMO_ROOT, m["id"], f))
               for f in os.listdir(os.path.join(DEMO_ROOT, m["id"])))
    assert size < 600_000


def test_demo_generation_is_deterministic(tmp_path):
    sid = generate(str(tmp_path / "a"))
    sid2 = generate(str(tmp_path / "b"))
    assert sid == sid2 == "20261005T090000Z"
    files = sorted(os.listdir(tmp_path / "a" / sid))
    assert files == ["data-0.csv", "data-1.csv", "events.jsonl", "meta.json", "notes.jsonl"]
    assert files == sorted(f for f in os.listdir(os.path.join(DEMO_ROOT, sid))
                           if not f.startswith("."))
    for f in files:
        a = (tmp_path / "a" / sid / f).read_bytes()
        assert a == (tmp_path / "b" / sid / f).read_bytes()
        assert a == open(os.path.join(DEMO_ROOT, sid, f), "rb").read(), \
            f"committed demo {f} is stale: run tools/make_demo_session.py"


def test_session_with_no_rows_is_removed_on_close(tmp_path):
    """A start immediately followed by shutdown (e.g. a restart) leaves no empty session."""
    from d2diag.logbook.recorder import SessionRecorder
    rec = SessionRecorder(str(tmp_path), clock=lambda: 1_000.0, mono=lambda: 5.0)
    rec.feed({"conn": "connected", "status": "connected", "signals": {}, "faults": []}, None)
    rec.close()
    assert [p for p in tmp_path.iterdir() if p.is_dir()] == []


# ------------------------------------------------- events (ADR-0010, spec §1) -- #

def events_of(tmp_path, sid):
    from d2diag.logbook.store import read_events
    return read_events(str(tmp_path / "sessions" / sid))


def test_events_state_line_and_on_change_only(tmp_path):
    c, r = make(tmp_path)
    s = snap(rpm=800)
    s.update(status="connected", fault_watch=False, logging={"recording": False},
             active_test=None)
    r.feed(s, None)
    sid = r.status()["session"]
    for _ in range(5):  # nothing changes: no events
        c.t += 0.5
        r.feed(dict(s), None)
    c.t += 0.5
    r.feed({**s, "fault_watch": True, "logging": {"recording": True, "file": "/x/live.csv",
                                                  "rows": 3}}, None)
    c.t += 0.5
    r.feed({**s, "fault_watch": True, "logging": {"recording": True, "file": "/x/live.csv",
                                                  "rows": 9}}, None)  # rows only: no event
    c.t += 0.5
    r.feed({**s, "conn": "lost", "status": "error", "error": "timeout"}, None)
    r.close()  # events are flushed with the data (≤ 1 s), so read after close
    ev = events_of(tmp_path, sid)
    assert ev[0] == {"t": 0, "type": "state", "conn": "connected", "status": "connected",
                     "module": "motor", "mode": "live", "active_test": None,
                     "fault_watch": False, "logging": {"recording": False}}
    rest = [(e["t"], e["type"]) for e in ev[1:]]
    assert rest == [(3000, "fault_watch"), (3000, "logging"), (4000, "conn"),
                    (4000, "status"), (4000, "fault_watch"), (4000, "logging"),
                    (4000, "error")]
    assert ev[2] == {"t": 3000, "type": "logging", "recording": True, "file": "live.csv"}
    assert ev[1]["on"] is True and ev[-1]["error"] == "timeout"


def test_event_api_dedups_state_and_strips_command(tmp_path):
    c, r = make(tmp_path)
    assert r.event("command", action="x", ok=True) is None  # nothing recording
    r.feed(snap(rpm=800), None)
    sid = r.status()["session"]
    c.t += 1.0
    assert r.event("module", module="motor") is None  # unchanged
    line = r.event("command", action="output_ac_fan", ok=True, message="A/C fan",
                   params={"secret": 1}, trust="experimental", raw="30 a4")
    assert line == {"t": 1000, "type": "command", "action": "output_ac_fan", "ok": True,
                    "message": "A/C fan"}
    r.event("command", action="pump_on", ok=False, error="refused")
    r.event("audio", track="t1", state="start", source="phone", trust="x")
    r.event("active_test", active_test={"action": "pump_on", "label": "Pump",
                                        "since": 1.0, "stop": "pump_off"})
    r.event("active_test", active_test={"action": "pump_on", "label": "Pump",
                                        "since": 2.0, "stop": "pump_off"})  # same test
    r.close()
    ev = events_of(tmp_path, sid)
    assert [e["type"] for e in ev] == ["state", "command", "command", "audio", "active_test"]
    assert ev[2] == {"t": 1000, "type": "command", "action": "pump_on", "ok": False,
                     "error": "refused"}
    assert "trust" not in ev[3]
    assert ev[4]["active_test"] == {"action": "pump_on", "label": "Pump", "stop": "pump_off"}


def test_identity_read_never_lands_in_events(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800), None)
    sid = r.status()["session"]
    r.event("command", action="read_identity", ok=True,
            message="VIN SALLTGM88XA123456 · EKA 1234", vin="SALLTGM88XA123456",
            params={"vin": "SALLTGM88XA123456"})
    r.close()
    ev = events_of(tmp_path, sid)
    assert ev[-1] == {"t": 0, "type": "command", "action": "read_identity", "ok": True}
    blob = (tmp_path / "sessions" / sid / "events.jsonl").read_text(encoding="utf-8")
    assert "SALLT" not in blob and "1234" not in blob


def test_module_switch_keeps_session_and_state_line_per_part(tmp_path):
    c, r = make(tmp_path)
    for _ in range(4):
        r.feed(snap(rpm=800), None)
        c.t += 0.5
    sid = r.status()["session"]
    s = snap(height_left=150)
    s["module"] = "slabs"
    for _ in range(4):
        r.feed(s, None)
        c.t += 0.5
    assert r.status()["session"] == sid
    r.close()
    m = meta_of(tmp_path, sid)
    assert m["modules"] == ["motor", "slabs"] and m["parts"] == ["data-0.csv", "data-1.csv"]
    ev = events_of(tmp_path, sid)
    assert [(e["t"], e["type"]) for e in ev] == [(0, "state"), (2000, "module"),
                                                 (2000, "state")]
    assert ev[1]["module"] == "slabs" and ev[2]["module"] == "slabs"
    d = SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid, ["rpm"])
    assert d["text"]["module"] == ["motor"] * 4 + ["slabs"] * 4


def test_events_fsync_with_data_cadence(tmp_path):
    calls = []
    c, r = make(tmp_path, fsync=calls.append)
    r.feed(snap(rpm=800), None)
    n0 = len(calls)
    for i in range(10):  # ten commands within 0.5 s: no extra syncs
        c.t += 0.05
        r.event("command", action=f"a{i}", ok=True)
    assert len(calls) == n0
    c.t += 1.0
    r.event("command", action="late", ok=True)
    assert len(calls) == n0 + 2  # data + events, once


def test_meta_channels_carry_confidence_limits_group(tmp_path):
    c, r = make(tmp_path)
    r.feed(snap(rpm=800, egr_pos=12, made_up_sig=5), fix(c, speed=10))
    sid = r.status()["session"]
    r.close()
    chans = {x["name"]: x for x in meta_of(tmp_path, sid)["channels"]}
    assert chans["rpm"]["c"] == "proven" and chans["rpm"]["limits"] == [0, 4800]
    assert chans["rpm"]["group"] == "engine"
    assert chans["egr_pos"]["c"] == "candidate"
    assert chans["made_up_sig"]["c"] == "candidate" and chans["made_up_sig"]["limits"] is None
    assert chans["GPS_Speed"] == {"name": "GPS_Speed", "units": "km/h", "group": "gps",
                                  "c": None, "limits": None}
    assert chans["GPS_LonAcc"]["group"] == "accel" and chans["GPS_LonAcc"]["c"] is None


def test_store_completes_old_meta(tmp_path):
    root = tmp_path / "sessions"
    (root / "20260101T000000Z").mkdir(parents=True)
    (root / "20260101T000000Z" / "meta.json").write_text(json.dumps(
        {"id": "20260101T000000Z", "channels": [{"name": "rpm", "units": "rpm"}]}))
    m = SessionStore(str(root), demo_root=None).meta("20260101T000000Z")
    assert m["channels"][0] == {"name": "rpm", "units": "rpm", "group": "engine",
                                "c": "proven", "limits": [0, 4800]}
    assert m["audio"] == [] and m["accel_cal"] is None
    assert SessionStore(str(root), demo_root=None).events("20260101T000000Z") == []


def test_store_events_public_filter_and_truncation(tmp_path):
    sid = _recorded(tmp_path)
    store = SessionStore(str(tmp_path / "sessions"))
    with pytest.raises(KeyError):
        store.events(sid, public=True)
    with open(tmp_path / "sessions" / sid / "events.jsonl", "a", encoding="utf-8") as fh:
        fh.write('{"t": 5, "type": "co')
    assert [e["type"] for e in store.events(sid)] == ["state"]


def test_text_channels_follow_decimation(tmp_path):
    c, r = make(tmp_path)
    for i in range(300):
        s = snap(rpm=800 + i)
        s["faults"] = ["P0100"] if i >= 150 else []
        r.feed(s, None)
        c.t += 0.2
    sid = r.status()["session"]
    r.close()
    d = SessionStore(str(tmp_path / "sessions"), demo_root=None).data(sid, ["rpm"], max_points=20)
    assert d["decimated"] and len(d["text"]["faults"]) == len(d["t"]) == len(d["ch"]["rpm"])
    for t, f in zip(d["t"], d["text"]["faults"]):
        assert f == ("P0100" if t >= 150 * 200 else None)


def test_demo_has_events_notes_switch_and_gps_accel(tmp_path):
    store = SessionStore(str(tmp_path / "none"))
    sid = "20261005T090000Z"
    ev = store.events(sid, public=True)
    assert ev[0]["type"] == "state" and ev[0]["module"] == "motor"
    assert ev[0]["conn"] == "connected"
    assert not any(e["type"] == "conn" for e in ev)  # stays connected
    sw = [e for e in ev if e["type"] == "module"]
    assert sw == [{"t": 360000, "type": "module", "module": "slabs"}]
    tests = [e for e in ev if e["type"] == "active_test"]
    assert [bool(e["active_test"]) for e in tests] == [True, False]
    assert any(e["type"] == "command" and e["action"] == "output_ac_fan" for e in ev)
    notes = store.notes(sid, public=True)
    assert len(notes) == 3 and all(n["source"] == "retro" for n in notes)
    assert [n["t"] for n in notes] == sorted(n["t"] for n in notes)
    m = store.meta(sid, public=True)
    assert m["modules"] == ["motor", "slabs"]
    d = store.data(sid, ["height_left", "rpm", "GPS_LonAcc", "GPS_LatAcc"], max_points=100000)
    i_sw = d["t"].index(360000)
    assert all(v is None for v in d["ch"]["rpm"][i_sw:])
    assert any(v is not None for v in d["ch"]["height_left"][i_sw:])
    assert max(abs(v) for v in d["ch"]["GPS_LonAcc"] if v is not None) > 0.1
    assert max(abs(v) for v in d["ch"]["GPS_LatAcc"] if v is not None) > 0.05
    with pytest.raises(PermissionError):
        store.add_note(sid, 1000, "x")


def test_set_name_names_the_open_session_only(tmp_path):
    import json
    from d2diag.logbook.recorder import SessionRecorder
    clock = [1_000.0]
    rec = SessionRecorder(str(tmp_path), clock=lambda: clock[0], mono=lambda: clock[0])
    sid = rec.start({"conn": "connected", "status": "connected", "signals": {"rpm": {"v": 800}}})
    rec.set_name("Track day")
    meta = json.loads((tmp_path / sid / "meta.json").read_text())
    assert meta["name"] == "Track day"
    clock[0] += 10
    sid2 = rec.split()
    assert json.loads((tmp_path / sid2 / "meta.json").read_text()).get("name") is None
    rec.close()
