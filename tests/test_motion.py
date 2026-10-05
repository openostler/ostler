"""Acceleration: rotation, sign conventions, GPS-derived acceleration and the recorder's
accel channels (ADR-0010; replay-notes-capture spec §3)."""
import json
import math

import pytest

from d2diag.gps.nmea import Fix
from d2diag.logbook.motion import G, GpsAccel, level_matrix, to_vehicle
from d2diag.logbook.recorder import SessionRecorder
from d2diag.logbook.store import SessionStore, read_part

T0 = 1791277200.0


def approx3(v, want, tol=1e-6):
    assert v == pytest.approx(want, abs=tol)


def test_identity_signs():
    approx3(to_vehicle((0, 0, G)), (0, 0, 0))                  # at rest, face up
    approx3(to_vehicle((0.5 * G, 0, G)), (0.5, 0, 0))          # accelerating: inline +
    approx3(to_vehicle((-0.7 * G, 0, G)), (-0.7, 0, 0))        # braking: inline −
    approx3(to_vehicle((0, 0.3 * G, G)), (0, 0.3, 0))          # left turn (force to the left)
    approx3(to_vehicle((0, -0.3 * G, G)), (0, -0.3, 0))        # right turn
    approx3(to_vehicle((0, 0, 1.2 * G)), (0, 0, 0.2))          # bump: vertical + up


def test_level_matrix_phone_upright_in_a_dash_mount():
    # Phone portrait, screen facing the driver: sensor y is up, sensor −z points forward,
    # so sensor −x points left. Rest reading (specific force) is +g on sensor y.
    m = level_matrix((0.0, G, 0.0), forward_xyz=(0.0, 0.0, -1.0))
    approx3(m[0], (0, 0, -1))
    approx3(m[1], (-1, 0, 0))
    approx3(m[2], (0, 1, 0))
    for i in range(3):  # orthonormal
        for j in range(3):
            assert sum(m[i][k] * m[j][k] for k in range(3)) == pytest.approx(float(i == j), abs=1e-9)
    approx3(to_vehicle((0, G, 0), m), (0, 0, 0))
    approx3(to_vehicle((0, G, -0.4 * G), m), (0.4, 0, 0))     # accelerating
    approx3(to_vehicle((-0.3 * G, G, 0), m), (0, 0.3, 0))     # left turn


def test_level_matrix_tilted_and_noisy_forward():
    tilt = math.radians(20)
    g = (0.0, G * math.sin(tilt), G * math.cos(tilt))           # phone tilted back 20°
    m = level_matrix(g, forward_xyz=(0.0, 1.0, 0.1))            # forward not exactly level
    approx3(to_vehicle(g, m), (0, 0, 0))
    m2 = level_matrix((0.0, 0.0, G))                            # no forward: sensor x
    approx3(m2[0], (1, 0, 0))
    approx3(m2[1], (0, 1, 0))


def test_gps_accel_longitudinal_and_lateral_signs():
    ga = GpsAccel()
    out = None
    for i in range(21):  # 0 → 36 km/h in 2 s at 10 Hz, heading steady
        out = ga.feed(i * 100, 36.0 * i / 20, 90.0)
    assert out[0] == pytest.approx(10 / 2 / G, rel=1e-3) and out[1] == pytest.approx(0)
    ga = GpsAccel()
    for i in range(21):  # 36 km/h, heading falling 9°/s across north: a LEFT turn
        out = ga.feed(i * 100, 36.0, (5.0 - 0.9 * i) % 360)
    assert out[0] == pytest.approx(0, abs=1e-9)
    assert out[1] == pytest.approx(10 * math.radians(9) / G, rel=1e-3) and out[1] > 0
    ga = GpsAccel()
    for i in range(21):  # right turn
        out = ga.feed(i * 100, 36.0, 350.0 + 0.9 * i)
    assert out[1] < 0
    ga = GpsAccel()
    assert ga.feed(0, 0.0, 10.0) is None
    assert ga.feed(100, 0.5, 200.0) == (pytest.approx(0.5 / 3.6 / 0.1 / G), 0.0)  # slow: no lat
    assert ga.feed(100, 1.0, 0.0) is None  # repeated epoch


class Clock:
    def __init__(self):
        self.t = 0.0


def _rec(tmp_path):
    c = Clock()
    r = SessionRecorder(str(tmp_path / "s"), clock=lambda: T0 + c.t, mono=lambda: c.t,
                        min_free_bytes=0, accel_hz=50)
    return c, r


def _snap():
    return {"conn": "connected", "module": "motor", "mode": "live", "faults": [],
            "signals": {"rpm": {"v": 900}}}


def test_feed_accel_raw_until_calibrated_then_vehicle(tmp_path):
    c, r = _rec(tmp_path)
    assert r.feed_accel([[T0 * 1000, 0, 0, G]], "phone") == 0  # nothing recording
    r.feed(_snap(), None)
    sid = r.status()["session"]
    c.t = 1.0
    r.feed(_snap(), None)
    ep = T0 * 1000
    n = r.feed_accel([[ep + 200, 0.1, 9.8, 0.2], [ep + 400, 0.1, 9.8, -3.0],
                      ["bad"], [ep + 1e9, 0, 0, 0], [ep - 5000, 0, 0, 0],
                      [ep + 600, float("nan"), 0, 0]], "phone")
    assert n == 2
    m = level_matrix((0.0, G, 0.0), forward_xyz=(0.0, 0.0, -1.0))
    cal = r.set_accel_cal(m, "phone", "level+gps")
    assert cal["method"] == "level+gps"
    assert r.feed_accel([[ep + 1100, 0.0, G, -0.5 * G]], "phone") == 1
    with pytest.raises(KeyError):
        r.feed_accel([[ep + 1200, 0, 0, 0]], "phone", session="20000101T000000Z")
    with pytest.raises(ValueError):
        r.set_accel_cal([[1, 0], [0, 1]], "phone", "level")
    r.close()
    store = SessionStore(str(tmp_path / "s"), demo_root=None)
    meta = store.meta(sid)
    assert meta["accel_cal"] == {"matrix": [list(map(float, row)) for row in m],
                                 "source": "phone", "method": "level+gps"}
    chans = {x["name"]: x for x in meta["channels"]}
    assert chans["Acc_X"]["units"] == "m/s²" and chans["InlineAcc"]["units"] == "g"
    assert chans["LateralAcc"]["group"] == "accel" and chans["LateralAcc"]["c"] is None
    d = store.data(sid, ["rpm", "Acc_Y", "InlineAcc", "LateralAcc"])
    assert d["t"] == [0, 200, 400, 1000, 1100]  # sparse rows at their own times, in order
    assert d["ch"]["Acc_Y"] == [None, 9.8, 9.8, None, 9.807]
    assert d["ch"]["InlineAcc"] == [None, None, None, None, 0.5]
    assert d["ch"]["rpm"] == [900, None, None, 900, None]
    ev = [e for e in store.events(sid) if e["type"] == "accel_cal"]
    assert len(ev) == 1 and ev[0]["source"] == "phone" and ev[0]["t"] == 1000
    _, rows = read_part(str(tmp_path / "s" / sid / "data-1.csv"))
    assert rows[0]["Utc"] == int(ep + 200)


def test_imu_source_is_vehicle_aligned_and_cal_carries_to_next_session(tmp_path):
    c, r = _rec(tmp_path)
    r.feed(_snap(), None)
    ep = T0 * 1000
    r.feed_accel([[ep + 20, 0.2 * G, -0.1 * G, G]], "imu")
    sid = r.status()["session"]
    r.set_accel_cal([[1, 0, 0], [0, 1, 0], [0, 0, 1]], "phone", "manual")
    r.close()
    d = SessionStore(str(tmp_path / "s"), demo_root=None).data(sid, ["InlineAcc", "LateralAcc"])
    assert d["ch"]["InlineAcc"][-1] == pytest.approx(0.2) and d["ch"]["LateralAcc"][-1] == pytest.approx(-0.1)
    c.t = 10.0
    r.feed(_snap(), None)
    sid2 = r.status()["session"]
    r.close()
    meta2 = json.loads((tmp_path / "s" / sid2 / "meta.json").read_text())
    assert meta2["accel_cal"]["source"] == "phone"
    header = (tmp_path / "s" / sid / "data-1.csv").read_text().split("\n")[0]
    assert '"Acc_X"|"m/s²"|50' in header


def test_gps_accel_channels_in_recorder(tmp_path):
    c, r = _rec(tmp_path)
    for i in range(30):  # a left turn at 36 km/h
        c.t = i * 0.2
        r.feed(_snap(), Fix(utc_ms=int((T0 + c.t) * 1000), lat=56.62 + i * 1e-5, lon=-4.68,
                            speed_kmh=36.0, heading=(100.0 - 2.0 * i) % 360, alt_m=300.0,
                            sats=9, hdop=0.8, fix=True, mono=c.t))
    sid = r.status()["session"]
    r.close()
    d = SessionStore(str(tmp_path / "s"), demo_root=None).data(sid, ["GPS_LonAcc", "GPS_LatAcc"])
    lat = [v for v in d["ch"]["GPS_LatAcc"] if v is not None]
    assert d["ch"]["GPS_LatAcc"][0] is None and len(lat) == 29
    assert lat[-1] == pytest.approx(10 * math.radians(10) / G, rel=0.02)
    assert all(abs(v) < 1e-3 for v in d["ch"]["GPS_LonAcc"] if v is not None)
