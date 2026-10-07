# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The visible trace of a shared trip (trip-sharing spec §5, §16 "Trim and zones", "L0 and
L1 agree"): ends trim, privacy zones with fixed offsets, stats from the visible fixes only,
the rounding table and simplification. The GPS trips here are **synthetic** grid drives
(``tests/share_fixtures.py``): the repo holds no recorded drive longer than 1 km."""
from __future__ import annotations

import json
import math
import zipfile

import pytest

from openostler.logbook.recorder import haversine_m
from openostler.logbook.share import ShareOptions, ShareRefused, build_share
from openostler.logbook.share import trace as tr
from openostler.logbook.share.zones import (RADII_M, PrivacyZone, ZoneRefused, ZoneStore,
                                            new_zone)
from tests.share_fixtures import LAT0, LON0, grid_drive, offset, write_gps_session

pytestmark = pytest.mark.fake_pack


def _zone(lat, lon, r=1000, e=0.0, n=0.0, name="Home"):
    return PrivacyZone("z", name, lat, lon, r, e, n)


def _files(bundle) -> dict:
    zf = zipfile.ZipFile(__import__("io").BytesIO(bundle.data))
    return {n: zf.read(n) for n in zf.namelist()}


# ---- ends trim (§5.1) ------------------------------------------------------------------- #
def test_the_visible_trace_starts_and_ends_exactly_at_the_trim():
    rows = grid_drive(legs=((3000, 0),), step_m=7.0)       # 3 km straight east
    vt = tr.visible_trace(rows, ends_m=500)
    pts = vt.points
    start, end = (rows[0]["GPS_Latitude"], rows[0]["GPS_Longitude"]), \
        (rows[-1]["GPS_Latitude"], rows[-1]["GPS_Longitude"])
    assert haversine_m(*start, pts[0].lat, pts[0].lon) == pytest.approx(500, abs=0.5)
    assert haversine_m(*end, pts[-1].lat, pts[-1].lon) == pytest.approx(500, abs=0.5)
    assert all(haversine_m(*start, p.lat, p.lon) >= 499.5 for p in pts)
    assert all(haversine_m(*end, p.lat, p.lon) >= 499.5 for p in pts)
    total = sum(haversine_m(a["GPS_Latitude"], a["GPS_Longitude"], b["GPS_Latitude"],
                            b["GPS_Longitude"]) for a, b in zip(rows, rows[1:]))
    assert vt.distance_m() == pytest.approx(total - 1000, abs=0.5)
    assert vt.hidden_trim > 0


@pytest.mark.parametrize("ends", [0, 100, 199, 1501, -5, True, "500"])
def test_a_trim_outside_200_to_1500_m_is_refused(ends):
    with pytest.raises(tr.TrimRefused):
        tr.check_trim(ends)
    with pytest.raises(tr.TrimRefused):
        tr.visible_trace(grid_drive(), ends_m=ends)


def test_the_hdop_and_jump_filters_drop_bad_fixes():
    rows = grid_drive(legs=((2000, 0),))
    rows[50]["GPS_HDOP"] = 9.0
    rows[60] = dict(rows[60], GPS_Latitude=rows[60]["GPS_Latitude"] + 0.5)   # 55 km jump
    fx = tr.fixes(rows)
    assert len(fx) == len(rows) - 2
    assert all(abs(p.lat - LAT0) < 0.01 for p in fx)


# ---- privacy zones (§5.2) --------------------------------------------------------------- #
def test_a_trip_starting_and_ending_in_a_home_zone_shows_nothing_inside_it():
    # out 3 km east and back 3 km west on a parallel road 300 m north: starts and ends at home
    rows = grid_drive(legs=((3000, 0), (0, 300), (-3000, 0)))
    home = _zone(LAT0, LON0, 1000, 300.0, -200.0)
    vt = tr.visible_trace(rows, ends_m=500, zones=[home])
    clat, clon = home.centre
    assert vt.points and all(haversine_m(clat, clon, p.lat, p.lon) >= 1000 for p in vt.points)
    assert vt.zones_hit == 1 and vt.hidden_zone > 0


def test_a_mid_trip_zone_gives_two_segments_with_no_joining_line(tmp_path):
    rows = grid_drive(legs=((6000, 0),))
    friend = _zone(*offset(LAT0, LON0, 3000, 0), r=500, name="Friend")
    vt = tr.visible_trace(rows, ends_m=500, zones=[friend])
    assert len(vt.segments) == 2
    gap = haversine_m(vt.segments[0][-1].lat, vt.segments[0][-1].lon,
                      vt.segments[1][0].lat, vt.segments[1][0].lon)
    assert gap >= 990                                   # the whole diameter is hidden
    sess = write_gps_session(str(tmp_path), rows)
    b = build_share(sess, ShareOptions("L1", zones=[friend]))
    geo = json.loads(_files(b)["track.geojson"])
    (feat,) = geo["features"]
    assert feat["geometry"]["type"] == "MultiLineString"
    assert len(feat["geometry"]["coordinates"]) == 2 and feat["properties"] == {}
    gpx = _files(b)["track.gpx"].decode()
    assert gpx.count("<trkseg>") == 2 and "<time" not in gpx
    assert b.manifest["trim"] == {"ends_m": 500, "zones": 1}


def test_zone_offsets_are_drawn_once_within_half_the_radius_and_survive_a_restart(tmp_path):
    for _ in range(200):
        z = new_zone("Home", LAT0, LON0, 1000)
        assert math.hypot(z.offset_e_m, z.offset_n_m) <= 500
        clat, clon = z.centre
        assert haversine_m(LAT0, LON0, clat, clon) <= 500.5
    store = ZoneStore(str(tmp_path))
    z = store.add("Home", LAT0, LON0)
    again = ZoneStore(str(tmp_path)).list()           # "an app restart"
    assert again == [z]
    z2, redrawn = store.update(z.id, name="Home sweet home",
                               lat=offset(LAT0, LON0, 200, 0)[0])
    assert not redrawn and (z2.offset_e_m, z2.offset_n_m) == (z.offset_e_m, z.offset_n_m)
    far = offset(LAT0, LON0, 0, 5000)
    z3, redrawn = store.update(z.id, lat=far[0], lon=far[1])
    assert redrawn                                      # moved by more than r: a new draw
    assert (tmp_path / "privacy_zones.json").stat().st_mode & 0o077 == 0


@pytest.mark.parametrize("r", [0, 100, 499, 750, 2500])
def test_a_zone_radius_is_one_of_the_choices(r):
    assert 500 in RADII_M
    with pytest.raises(ZoneRefused):
        new_zone("Home", LAT0, LON0, r)


def test_two_shares_of_one_trip_hide_exactly_the_same_area(tmp_path):
    rows = grid_drive()
    store = ZoneStore(str(tmp_path / "state"))
    store.add("Home", LAT0, LON0, 1000)
    sess = write_gps_session(str(tmp_path / "s"), rows)
    a = build_share(sess, ShareOptions("L1", zones=store.list()))
    b = build_share(sess, ShareOptions("L1", zones=ZoneStore(str(tmp_path / "state")).list()))
    assert _files(a)["track.geojson"] == _files(b)["track.geojson"]
    assert a.manifest["id"] != b.manifest["id"]


# ---- stats from the visible trace (§5.4) ------------------------------------------------ #
def test_stats_are_those_of_the_visible_fixes_alone(tmp_path):
    rows = grid_drive(legs=((3000, 0), (0, 2000)))       # 5 km at 36 km/h, +1 m per 50 m
    sess = write_gps_session(str(tmp_path), rows)
    b = build_share(sess, ShareOptions("L1"))
    trip = json.loads(_files(b)["trip.json"])
    assert trip["distance_km"] == 4.0                   # 5 km less two 500 m ends
    assert trip["duration_min"] == 7                    # 4,000 m at 10 m/s = 6.7 min
    assert trip["moving_min"] == 7
    assert trip["avg_kmh"] == 36.0
    assert trip["elevation_gain_m"] == 80               # 4,000 m / 50
    assert trip["stops"] == 0
    blob = b"".join(_files(b).values()).decode("utf-8", "replace")
    # the hidden part's length and the trip's total appear nowhere
    for leak in ('"5.0"', ": 5.0", ": 5,", "1000", "1.0 km"):
        assert leak not in blob.replace('"ends_m": 500', "")


def test_l0_and_l1_of_one_trip_agree(tmp_path):
    for legs in (((2460, 0),), ((3549, 0),), ((2950, 600),)):
        sess = write_gps_session(str(tmp_path / str(legs)), grid_drive(legs=legs))
        l0 = json.loads(_files(build_share(sess, ShareOptions("L0")))["trip.json"])
        l1 = json.loads(_files(build_share(sess, ShareOptions("L1")))["trip.json"])
        assert l0["distance_km"] == math.floor(l1["distance_km"] + 0.5)
        assert "start_region" not in l0 and l0["level"] == "L0"


def test_the_rounding_table():
    st = {"distance_m": 12_345.0, "duration_s": 1_234.0, "moving_s": 1_100.0,
          "avg_kmh": 40.4, "max_kmh": 87.6, "gain_m": 123.0, "stops": 2}
    fine = tr.round_stats(st, card=False)
    assert fine == {"distance_km": 12.3, "duration_min": 21, "moving_min": 18,
                    "avg_kmh": 40, "max_kmh": 88, "elevation_gain_m": 120, "stops": 2}
    card = tr.round_stats(st, card=True)
    assert card == {"distance_km": 12, "duration_min": 20, "moving_min": 20, "avg_kmh": 40,
                    "max_kmh": 90}


def test_a_trip_without_gps_integrates_ecu_speed_less_its_first_and_last_two_minutes():
    rows = [{"Interval": t * 1000.0, "speed": 36.0} for t in range(0, 601)]   # 10 min
    st = tr.no_gps_stats(rows, "speed")
    assert st["duration_s"] == 600
    assert st["distance_m"] == pytest.approx(360 * 10.0)     # 6 of the 10 minutes
    assert tr.no_gps_stats(rows, None)["distance_m"] is None


def test_simplification_keeps_corners_and_drops_the_straight_runs():
    vt = tr.visible_trace(grid_drive(legs=((3000, 0), (0, 2000))), ends_m=500)
    (seg,) = tr.simplified(vt)
    assert 3 <= len(seg) <= 5                            # start, corner, end
    assert all(len(str(c).split(".")[-1]) <= 5 for p in seg for c in p[:2])


# ---- refusals ---------------------------------------------------------------------------- #
def test_a_short_trip_can_be_shared_as_a_card_only(tmp_path):
    sess = write_gps_session(str(tmp_path), grid_drive(legs=((1800, 0),)))   # 0.8 km visible
    card = json.loads(_files(build_share(sess, ShareOptions("L0")))["trip.json"])
    assert card["distance"] == "under 1 km" and "duration_min" not in card
    with pytest.raises(ShareRefused, match="under 1 km"):
        build_share(sess, ShareOptions("L1"))
    with pytest.raises(ShareRefused, match="under 1 km"):
        build_share(sess, ShareOptions("L3", audience="person", recipient="Sam", route=True))
    build_share(sess, ShareOptions("L3", audience="person"))   # no location: allowed


def test_a_public_route_needs_the_publish_act_24_h_after_the_trip(tmp_path):
    sess = write_gps_session(str(tmp_path), grid_drive())
    from tests.share_fixtures import T0

    with pytest.raises(ShareRefused, match="publish"):
        build_share(sess, ShareOptions("L1", audience="public"), clock=lambda: T0 + 2 * 86400)
    with pytest.raises(ShareRefused, match="24 h"):
        build_share(sess, ShareOptions("L1", audience="public", publish=True),
                    clock=lambda: T0 + 3600)
    b = build_share(sess, ShareOptions("L1", audience="public", publish=True),
                    clock=lambda: T0 + 2 * 86400)
    assert "max_kmh" not in json.loads(_files(b)["trip.json"])      # R15 on public cards


def test_max_speed_is_hidden_on_link_and_public_cards_by_default(tmp_path):
    sess = write_gps_session(str(tmp_path), grid_drive())
    for audience, shown in (("link", False), ("person", True), ("household", True)):
        trip = json.loads(_files(build_share(sess, ShareOptions("L0", audience=audience)))
                          ["trip.json"])
        assert ("max_kmh" in trip) is shown
    trip = json.loads(_files(build_share(sess, ShareOptions("L0", audience="link",
                                                            show_max_speed=True)))["trip.json"])
    assert trip["max_kmh"] == 35          # 36 km/h on the 5 km/h card step
