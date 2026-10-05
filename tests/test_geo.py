"""Place names (ADR-0011; spec 2026-10-06-logs-at-scale §2): offline GeoNames lookup,
the deterministic table builder and the Nominatim enricher (no network, fake clock)."""
import gzip
import json
import os
import threading
import zipfile

import pytest

from d2diag import geo
from d2diag.geo import build, nominatim, offline

CACHE = build.DEFAULT_CACHE
_HAVE_CACHE = all(os.path.exists(os.path.join(CACHE, n)) for n in build.INPUTS)


# --- offline: the committed table --------------------------------------------------
def test_point_in_town_is_town_region():
    r = offline.label(56.8205, -5.1100)  # ~0.5 km from Fort William centre
    assert r["label"] == "Fort William, Highland"
    assert r["town"] == "Fort William" and r["country"] == "Scotland"
    assert r["dist_km"] <= 1.0 and r["source"] == "geonames"


def test_rannoch_moor_is_near_or_region_form():
    r = offline.label(56.622, -4.680)  # Demo log 1 centre
    assert r is not None and r["source"] == "geonames"
    if r["town"]:
        assert r["label"].startswith("near ") and r["dist_km"] > 1.0
    else:
        assert r["label"] == f"{r['region']}, {r['country']}"
        assert r["country"] == "Scotland"


def test_open_atlantic_is_none():
    assert offline.label(57.0, -12.0) is None
    assert offline.label(45.0, -40.0) is None


def test_bad_input_is_none():
    assert offline.label(None, None) is None
    assert offline.label(95.0, 0.0) is None


def test_attribution_and_exports():
    assert geo.ATTRIBUTION == "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)"
    assert geo.label is offline.label
    with gzip.open(offline.DATA_PATH, "rt", encoding="utf-8") as fh:
        head = fh.read(400)
    assert "CC BY 4.0" in head and "GeoNames" in head


# --- offline: rules on a synthetic table ------------------------------------------
def _table(rows, countries=None):
    places = [(n, la, lo, cc, a1, a2, pop) for n, la, lo, cc, a1, a2, pop in rows]
    return offline._Table(places, countries or {"FR": "France", "GB": "United Kingdom"})


_KM_LAT = 1 / offline._KM_PER_DEG_LAT  # degrees of latitude per km


def test_reach_scales_with_population():
    assert offline.reach_km(60_000) == 25 and offline.reach_km(5_000) == 15
    assert offline.reach_km(1_000) == 8 and offline.reach_km(999) == 3


def test_largest_qualifying_wins_and_tie_goes_nearest():
    t = _table([
        ("Bigtown", 45.0 + 20 * _KM_LAT, 2.0, "FR", "Occitanie", "Lot", 80_000),
        ("Hamlet", 45.0 + 0.5 * _KM_LAT, 2.0, "FR", "Occitanie", "Lot", 200),
        ("Twin A", 45.0 - 6 * _KM_LAT, 2.0, "FR", "Occitanie", "Lot", 3_000),
        ("Twin B", 45.0 - 5 * _KM_LAT, 2.0, "FR", "Occitanie", "Lot", 3_000),
    ])
    r = offline.label(45.0, 2.0, table=t)
    assert r["town"] == "Bigtown" and r["label"] == "near Bigtown, Lot"
    t2 = _table([row for row in t.places if row[0] == "Hamlet"])
    assert offline.label(45.0, 2.0, table=t2)["label"] == "Hamlet, Lot"  # within 1 km
    t3 = _table([row for row in t.places if row[0].startswith("Twin")])
    assert offline.label(45.0, 2.0, table=t3)["town"] == "Twin B"


def test_out_of_reach_falls_back_to_region_then_none():
    t = _table([("Smallville", 45.0 + 10 * _KM_LAT, 2.0, "FR", "Occitanie", "", 500)])
    r = offline.label(45.0, 2.0, table=t)
    assert r["label"] == "Occitanie, France" and r["town"] is None
    far = _table([("Smallville", 45.0 + 90 * _KM_LAT, 2.0, "FR", "", "", 500)])
    assert offline.label(45.0, 2.0, table=far)["label"] == "France"
    gone = _table([("Smallville", 45.0 + 110 * _KM_LAT, 2.0, "FR", "Occitanie", "", 500)])
    assert offline.label(45.0, 2.0, table=gone) is None


def test_uk_uses_nation_and_admin2():
    t = _table([("Village", 57.0 + 30 * _KM_LAT, -4.0, "GB", "Scotland", "Highland", 1200)])
    assert offline.label(57.0, -4.0, table=t)["label"] == "Highland, Scotland"


def test_antimeridian_wraps():
    t = _table([("Eastside", -17.0, 179.99, "FJ", "Northern", "", 2_000)], {"FJ": "Fiji"})
    assert offline.label(-17.0, -179.99, table=t)["town"] == "Eastside"


# --- builder: deterministic --------------------------------------------------------
def _fake_dumps(folder):
    os.makedirs(folder, exist_ok=True)
    rows = [
        ["2649169", "Fort William", "Fort William", "", "56.81648", "-5.11208", "P", "PPL", "GB", "",
         "SCT", "V3", "", "", "15757", "", "24", "Europe/London", "2026-04-03"],
        ["1", "Old Fort", "Old Fort", "", "56.0", "-5.0", "P", "PPLH", "GB", "", "SCT", "V3", "", "",
         "5000", "", "", "Europe/London", "2026-04-03"],
        ["2", "Abc", "Abc", "", "48.1", "2.2", "P", "PPL", "FR", "", "11", "", "", "", "1200", "",
         "", "Europe/Paris", "2026-01-01"],
    ]
    zpath = os.path.join(folder, "cities1000.zip")
    with zipfile.ZipFile(zpath, "w") as zf:
        info = zipfile.ZipInfo("cities1000.txt", date_time=(2026, 10, 4, 5, 23, 0))
        zf.writestr(info, "".join("\t".join(r) + "\n" for r in rows))
    with open(os.path.join(folder, "admin1CodesASCII.txt"), "w") as fh:
        fh.write("GB.SCT\tScotland\tScotland\t2638360\nFR.11\tÎle-de-France\tIle-de-France\t3012874\n")
    with open(os.path.join(folder, "admin2Codes.txt"), "w") as fh:
        fh.write("GB.SCT.V3\tHighland\tHighland\t2646944\n")
    with open(os.path.join(folder, "countryInfo.txt"), "w") as fh:
        fh.write("#ISO\tISO3\tISO-Numeric\tfips\tCountry\n")
        fh.write("GB\tGBR\t826\tUK\tUnited Kingdom\tLondon\n")
        fh.write("FR\tFRA\t250\tFR\tFrance\tParis\n")


def test_builder_is_deterministic_and_loadable(tmp_path):
    _fake_dumps(tmp_path / "c")
    a, b = tmp_path / "a.tsv.gz", tmp_path / "b.tsv.gz"
    build.build(str(tmp_path / "c"), str(a))
    build.build(str(tmp_path / "c"), str(b))
    assert a.read_bytes() == b.read_bytes()
    t = offline.load(str(a))
    assert [p[0] for p in t.places] == ["Abc", "Fort William"]  # sorted by cc; PPLH dropped
    assert t.countries == {"FR": "France", "GB": "United Kingdom"}
    with gzip.open(a, "rt", encoding="utf-8") as fh:
        assert "# date: 2026-10-04" in fh.read()
    assert offline.label(56.8205, -5.1100, table=t)["label"] == "Fort William, Highland"


@pytest.mark.skipif(not _HAVE_CACHE, reason="GeoNames dumps not cached (run tools/build_places.py)")
def test_committed_table_matches_cached_dumps(tmp_path):
    out = tmp_path / "places.tsv.gz"
    build.build(CACHE, str(out))
    with open(offline.DATA_PATH, "rb") as fh:
        committed = fh.read()
    if out.read_bytes() != committed:
        pytest.skip("cached dumps are newer than the committed table")
    assert out.stat().st_size <= 4_500_000


# --- enricher ------------------------------------------------------------------------
FORT_WILLIAM = {"address": {"town": "Fort William", "county": "Highland", "state": "Scotland",
                            "country": "United Kingdom"}}
MOOR = {"address": {"county": "Perth and Kinross", "state": "Scotland", "country": "United Kingdom"}}


def test_label_from_address():
    assert nominatim.label_from_address(FORT_WILLIAM) == "Fort William, Highland"
    assert nominatim.label_from_address({"address": {"village": "V", "state": "S"}}) == "V, S"
    assert nominatim.label_from_address({"address": {"city": "C", "hamlet": "H"}}) == "C"
    assert nominatim.label_from_address(MOOR) == "Perth and Kinross, United Kingdom"
    assert nominatim.label_from_address({"error": "Unable to geocode"}) is None


class FakeClock:
    def __init__(self):
        self.t = 1000.0
        self.slept = []

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.slept.append(round(s, 3))
        self.t += s


def _enricher(tmp_path, fetch, url="https://nominatim.example"):
    clk = FakeClock()
    e = nominatim.Enricher(url, str(tmp_path / "logs" / "geocache.json"), fetch=fetch, clock=clk, sleep=clk.sleep)
    return e, clk


def test_rate_limit_one_per_second(tmp_path):
    calls = []

    def fetch(url, headers, timeout):
        calls.append((url, headers, timeout))
        return FORT_WILLIAM

    e, clk = _enricher(tmp_path, fetch)
    got = []
    for i in range(3):
        e.submit(f"s{i}", 56.8 + i * 0.01, -5.1, lambda k, v: got.append((k, v)))
    while e.step():
        pass
    assert got == [("s0", "Fort William, Highland"), ("s1", "Fort William, Highland"),
                   ("s2", "Fort William, Highland")]
    assert clk.slept == [1.0, 1.0]
    url, headers, timeout = calls[0]
    assert url.startswith("https://nominatim.example/reverse?") and "format=jsonv2" in url
    assert "lat=56.800" in url and "lon=-5.100" in url and "zoom=10" in url and "addressdetails=1" in url
    assert headers["User-Agent"].startswith("discovery2-diag/")
    assert "(+https://github.com/JamesWrightDavid/discovery2-diag)" in headers["User-Agent"]
    assert timeout == 10


def test_cache_hit_avoids_fetch_and_persists(tmp_path):
    calls = []
    e, _ = _enricher(tmp_path, lambda *a: calls.append(a) or FORT_WILLIAM)
    e.submit("a", 56.81648, -5.11208, lambda k, v: None)
    e.step()
    assert len(calls) == 1 and e.cached(56.8165, -5.1121) == "Fort William, Highland"
    data = json.loads((tmp_path / "logs" / "geocache.json").read_text())
    assert data == {"56.816,-5.112": "Fort William, Highland"}
    e2, _ = _enricher(tmp_path, lambda *a: calls.append(a) or MOOR)
    got = []
    e2.submit("b", 56.8161, -5.1119, lambda k, v: got.append((k, v)))
    assert got == [("b", "Fort William, Highland")] and e2.pending() == 0 and len(calls) == 1


def test_backoff_on_failure_doubles_to_an_hour(tmp_path):
    state = {"fail": True, "n": 0}

    def fetch(*a):
        state["n"] += 1
        if state["fail"]:
            raise OSError("offline")
        return MOOR

    e, clk = _enricher(tmp_path, fetch)
    got = []
    e.submit("x", 56.62, -4.68, lambda k, v: got.append(v))
    seen = []
    for _ in range(8):
        assert e.step() is False
        seen.append(e.backoff_s)
    assert seen == [60, 120, 240, 480, 960, 1920, 3600, 3600]
    assert e.pending() == 1 and got == []
    state["fail"] = False
    assert e.step() is True and got == ["Perth and Kinross, United Kingdom"] and e.backoff_s == 0
    assert clk.slept[-1] == 3600


def test_disabled_never_fetches(tmp_path):
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "geocache.json").write_text(json.dumps({"56.620,-4.680": "Rannoch, Highland"}))
    for url in (None, "off"):
        e, _ = _enricher(tmp_path, lambda *a: pytest.fail("fetched"), url=url)
        got = []
        e.submit("a", 56.62, -4.68, lambda k, v: got.append(v))
        e.submit("b", 10.0, 10.0, lambda k, v: got.append(v))
        e.start()
        e.stop()
        assert got == ["Rannoch, Highland", None] and not e.enabled


def test_thread_resolves_and_stops(tmp_path):
    done = threading.Event()
    e = nominatim.Enricher("https://n.example", str(tmp_path / "g.json"), fetch=lambda *a: FORT_WILLIAM)
    got = []
    e.start()
    try:
        e.submit("k", 56.8, -5.1, lambda k, v: (got.append((k, v)), done.set()))
        assert done.wait(5)
    finally:
        e.stop()
    assert got == [("k", "Fort William, Highland")]
