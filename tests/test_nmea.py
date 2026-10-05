"""NMEA parsing, fix merging and the GPS sources (ADR-0009). No hardware."""
import math
import os
import time

import pytest

from openostler.gps import nmea
from openostler.gps.nmea import Fix, FixMerger, parse, sentence
from openostler.gps.reader import GpsReader, MockGps, ReplayGps, open_gps, read_fixes
from openostler.gps.route import PERIOD_S, demo_route

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "demo_loop.nmea")

RMC = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
GGA = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"


def test_rmc_classic():
    d = parse(RMC)
    assert d["type"] == "RMC" and d["talker"] == "GP"
    assert d["fix"] is True
    assert d["lat"] == pytest.approx(48 + 7.038 / 60)
    assert d["lon"] == pytest.approx(11 + 31.0 / 60)
    assert d["speed_kmh"] == pytest.approx(22.4 * 1.852)
    assert d["heading"] == pytest.approx(84.4)
    assert d["tod_ms"] == (12 * 3600 + 35 * 60 + 19) * 1000
    # 23 March 1994 12:35:19 UTC
    assert d["utc_ms"] == 764426119000


def test_gga_classic():
    d = parse(GGA)
    assert d["type"] == "GGA" and d["fix"] is True
    assert d["sats"] == 8 and d["hdop"] == pytest.approx(0.9)
    assert d["alt_m"] == pytest.approx(545.4)
    assert "utc_ms" not in d  # no date in GGA


def test_checksum_rejected_or_missing():
    assert parse(RMC[:-2] + "6B") is None
    assert parse(RMC.split("*")[0]) is None  # missing checksum
    assert parse("garbage") is None
    assert parse("") is None
    assert parse(RMC.lower()) is None  # lower case changes the checksum


def test_checksum_case_and_bytes():
    assert parse(RMC[:-2] + "6a") is not None
    assert parse((RMC + "\r\n").encode()) is not None


@pytest.mark.parametrize("talker", ["GP", "GN", "GL", "GA", "BD"])
def test_any_talker(talker):
    body = "RMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W"
    d = parse(sentence(talker + body))
    assert d is not None and d["talker"] == talker and d["type"] == "RMC"


def test_unsupported_sentence():
    assert parse(sentence("GPGSV,3,1,11,01,40,083,46")) is None
    assert parse(sentence("GPXYZ,1,2")) is None


def test_empty_fields():
    d = parse(sentence("GPRMC,,V,,,,,,,,,,N"))
    assert d["fix"] is False
    assert d["lat"] is None and d["lon"] is None and d["speed_kmh"] is None
    assert "tod_ms" not in d
    g = parse(sentence("GNGGA,090000.00,,,,,0,00,99.99,,,,,,"))
    assert g["fix"] is False and g["sats"] == 0 and g["alt_m"] is None
    assert parse(sentence("GPRMC,1,2")) is None  # too short


def test_south_and_west_negative():
    d = parse(sentence("GPRMC,000001.00,A,3352.000,S,15112.000,W,0,0,010126,,,A"))
    assert d["lat"] == pytest.approx(-(33 + 52 / 60))
    assert d["lon"] == pytest.approx(-(151 + 12 / 60))


def test_vtg_kmh_and_knots():
    d = parse(sentence("GPVTG,054.7,T,034.4,M,005.5,N,010.2,K"))
    assert d["speed_kmh"] == pytest.approx(10.2) and d["heading"] == pytest.approx(54.7)
    d = parse(sentence("GPVTG,054.7,T,,M,005.5,N,,K"))
    assert d["speed_kmh"] == pytest.approx(5.5 * 1.852)


def test_merger_combines_one_epoch():
    m = FixMerger()
    f = m.feed(parse(sentence("GNGGA,090000.00,5200.000,N,00130.000,W,1,10,0.7,100.0,M,,M,,")), 1.0)
    assert f.fix and f.alt_m == 100.0 and f.speed_kmh is None and f.utc_ms is None
    f = m.feed(parse(sentence("GNRMC,090000.00,A,5200.000,N,00130.000,W,10.0,90.0,051026,,,A")), 1.1)
    assert f.alt_m == 100.0 and f.sats == 10
    assert f.speed_kmh == pytest.approx(18.52)
    assert f.utc_ms == 1791190800000  # 2026-10-05 09:00:00Z
    assert f.lat == pytest.approx(52.0) and f.lon == pytest.approx(-1.5)
    assert f.mono == 1.1
    # VTG joins the current epoch
    f = m.feed(parse(sentence("GNVTG,91.0,T,,M,,N,20.0,K,A")), 1.2)
    assert f.speed_kmh == 20.0 and f.heading == 91.0
    # next epoch: GGA alone gets its date from the last RMC; earlier fields carry over
    f = m.feed(parse(sentence("GNGGA,090000.10,5200.001,N,00130.000,W,1,10,0.7,101.0,M,,M,,")), 1.3)
    assert f.utc_ms == 1791190800100 and f.alt_m == 101.0 and f.speed_kmh == 20.0
    assert m.feed(None) is f


def test_merger_lost_fix():
    m = FixMerger()
    m.feed(parse(sentence("GNRMC,090000.00,A,5200.000,N,00130.000,W,1,1,051026,,,A")))
    f = m.feed(parse(sentence("GNRMC,090001.00,V,,,,,,,051026,,,N")))
    assert f.fix is False


def test_fix_snapshot():
    f = Fix(utc_ms=1, lat=1.0, lon=2.0, speed_kmh=3.0, heading=4.0, sats=5, hdop=0.9,
            fix=True, mono=100.0)
    s = f.snapshot(src="usb", now=102.5)
    assert set(s) == {"fix", "lat", "lon", "speed_kmh", "heading", "sats", "hdop", "src", "age_s"}
    assert s["age_s"] == 2.5 and s["src"] == "usb" and s["fix"] is True


def test_read_fixes_fixture_skips_bad_lines():
    fixes = read_fixes(FIXTURE)
    assert len(fixes) == 20
    tod, f = fixes[0]
    assert tod == (9 * 3600 + 3 * 60 + 20) * 1000
    assert f.fix and f.alt_m is not None and f.speed_kmh is not None
    p = demo_route(200)
    assert f.lat == pytest.approx(p["lat"], abs=1e-6)
    assert f.lon == pytest.approx(p["lon"], abs=1e-6) and f.lon < 0
    assert f.speed_kmh == pytest.approx(p["speed_kmh"], abs=0.01)
    assert all(x[1].lat > 50 for x in fixes)  # the bad-checksum (0,0) RMC was rejected


def test_replay_gps_runs():
    r = ReplayGps(FIXTURE, loop=False, rate=1000.0)
    assert r.src == "replay" and r.latest() is None
    r.start()
    deadline = time.monotonic() + 5
    while r.epochs < 20 and time.monotonic() < deadline:
        time.sleep(0.01)
    r.stop()
    f = r.latest()
    assert r.epochs == 20 and f.fix and f.src == "replay"
    assert f.snapshot()["src"] == "replay"


def test_mock_gps_deterministic_and_loops():
    t = {"m": 50.0}
    g = MockGps(mono=lambda: t["m"], clock=lambda: 1_000_000.0)
    assert g.latest() is None
    g.start()
    t["m"] = 50.0 + 300.0
    a = g.latest()
    p = demo_route(300.0)
    assert a.lat == pytest.approx(p["lat"], abs=1e-6) and a.fix and a.src == "mock"
    t["m"] = 50.0 + 300.0 + PERIOD_S  # one lap later: same place
    b = g.latest()
    assert (b.lat, b.lon) == (a.lat, a.lon)
    assert a.utc_ms == 1_000_000_000


def test_demo_route_closed_loop():
    a, b = demo_route(0), demo_route(PERIOD_S - 1e-6)
    assert math.hypot(a["lat"] - b["lat"], a["lon"] - b["lon"]) < 1e-5
    assert max(demo_route(t)["speed_kmh"] for t in range(0, 720, 5)) > 85


def test_gps_reader_no_device_is_quiet():
    r = GpsReader("auto", candidates=lambda: [])
    r.start()
    assert r.latest() is None and r._thread is None
    r.stop()


def test_gps_reader_pumps_fake_serial(monkeypatch):
    lines = [(s + "\r\n").encode() for s in (GGA, RMC)]

    class FakeSerial:
        def __init__(self):
            self.i = 0

        def readline(self):
            if self.i < len(lines):
                self.i += 1
                return lines[self.i - 1]
            time.sleep(0.01)
            return b""

        def close(self):
            pass

    r = GpsReader("auto", candidates=lambda: [("/dev/fake", True)])
    monkeypatch.setattr(r, "_open", lambda port: FakeSerial())
    r.start()
    deadline = time.monotonic() + 3
    while (r.latest() is None or r.latest().speed_kmh is None) and time.monotonic() < deadline:
        time.sleep(0.01)
    r.stop()
    f = r.latest()
    assert f.fix and f.alt_m == pytest.approx(545.4) and f.src == "usb"
    assert r.device == "/dev/fake"


def test_open_gps_specs():
    assert open_gps("none") is None and open_gps(None) is None
    assert isinstance(open_gps("mock"), MockGps)
    assert isinstance(open_gps("auto"), GpsReader)
    assert isinstance(open_gps(FIXTURE), ReplayGps)
    g = open_gps("/dev/ttyACM9")
    assert isinstance(g, GpsReader) and g.port == "/dev/ttyACM9"


def test_checksum_helper():
    assert nmea.checksum("GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,") == "47"
