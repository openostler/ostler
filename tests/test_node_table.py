# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The device table and node messages, without sockets (NodeSource spec §4, §6, §13):
staleness (retained on subscribe, EMA intervals, reboots by boot id and by t_us),
confidence never raised, unknown metrics flagged, VIN-shaped vids refused, selection, and
the firmware's fixtures (``tests/fixtures/node/``)."""
from __future__ import annotations

import json

import pytest

from openostler.node import (DeviceTable, check_vid, lower_confidence, parse_power,
                             parse_status, parse_topic, parse_vss, range_status, select,
                             subscriptions, vin_shaped)
from openostler.node.table import parse_utc, utc
from tests.fake_node import case, load, vss_messages

VID = "d2-bench"
BASE = f"ostler/v1/{VID}/node/"
WALL0 = parse_utc("2026-10-06T10:00:00.000Z")


def vss(leaf, value, *, t_us, name="rpm", module="alpha", c="proven", boot=7, ts=None,
        unit="rpm", **extra):
    body = {"value": value, "unit": unit, "ts": ts, "t_us": t_us, "source":
            f"kline-diag/{module}/21 09", "name": name, "c": c, "raw": value, **extra}
    if boot is not None:
        body["boot"] = boot
    return json.dumps(body).encode()


class T:
    """A table with a controllable clock."""

    def __init__(self, **kw):
        self.logs = []
        self.now, self.wall = 100.0, WALL0 + 60.0
        kw.setdefault("log", self.logs.append)
        self.table = DeviceTable(VID, **kw)

    def put(self, leaf, payload, retain=False, device="node", kind="vss"):
        topic = f"ostler/v1/{VID}/{device}/{kind}" + (f"/{leaf}" if leaf else "")
        return self.table.ingest(topic, payload, retain, self.now, self.wall)

    def tick(self, s):
        self.now += s
        self.wall += s

    def view(self, module="alpha"):
        return self.table.view(module, self.now, self.wall)


# ---- topics and payloads ---------------------------------------------------------------- #
def test_vin_shaped_vid_is_refused():
    assert vin_shaped("SALLTGM88YA123456") and vin_shaped("sallTGM88YA123456")
    assert not vin_shaped("d2-bench") and not vin_shaped("SALLTGM88YA12345I")  # I is no VIN char
    with pytest.raises(ValueError):
        check_vid("SALLTGM88YA123456")
    for bad in ("", "a/b", "+", "#", None):
        with pytest.raises(ValueError):
            check_vid(bad)


def test_the_p1_subscription_set_is_read_only():
    subs = subscriptions(VID)
    assert subs == [(f"ostler/v1/{VID}/+/status", 1), (f"ostler/v1/{VID}/+/power", 1),
                    (f"ostler/v1/{VID}/+/vss/+", 0)]
    for f, _ in subs:
        assert "#" not in f and "/lab/" not in f and "/act/" not in f and "/tap/" not in f


def test_parse_topic_and_payloads():
    t = parse_topic(BASE + "vss/Vehicle.Speed")
    assert (t.vid, t.device, t.kind, t.rest) == (VID, "node", "vss", "Vehicle.Speed")
    assert parse_topic("other/v1/x/y/z") is None and parse_topic("ostler/v1/x") is None
    assert parse_status(b"online") == "online" and parse_status(b"{}") is None
    assert parse_power(case("asleep")["payload"])["state"] == "asleep"
    assert parse_power(b'{"state":"dancing"}') is None and parse_power(b"[]") is None
    v = parse_vss("lr_d2.slabs.any_door", load("slabs-vectors.jsonl")[0]["payload"])  # power
    assert v is not None and v.value is None  # a power record is not a value
    v = parse_vss("lr_d2.td5.air_temp", vss("x", 21.5, t_us=5, name="air_temp", module="td5"))
    assert v.pack_leaf == ("lr_d2", "td5", "air_temp") and v.path is None
    assert v.module == "td5" and v.pack_decoded and v.boot == 7


def test_range_status_and_confidence_rules():
    assert [range_status(v, (0, 100)) for v in (50, -1, 101, -101, 201, None)] == \
        ["ok", "low", "high", "suspect", "suspect", None]
    assert range_status(5, None) is None
    assert lower_confidence("proven", "proven") == "proven"
    assert lower_confidence("proven", "candidate") == "candidate"
    assert lower_confidence("candidate", "proven") == "candidate"
    assert lower_confidence("proven", None) == "proven"
    assert lower_confidence("bogus") == "candidate" and lower_confidence() == "candidate"


# ---- values ----------------------------------------------------------------------------- #
def test_live_value_and_its_fields():
    lookup = {("alpha", "rpm"): ("proven", (0, 5000))}
    t = T(lookup=lambda m, n: lookup.get((m, n)), is_known=lambda p: p == "Vehicle.Speed")
    t.put("Vehicle.Powertrain.CombustionEngine.Speed",
          vss("x", 800, t_us=1_000_000, state="idle", ts="2026-10-06T10:00:59.000Z"))
    sig = t.view()["signals"]["rpm"]
    assert sig == {"v": 800.0, "u": "rpm", "s": "ok", "c": "proven",
                   "ts_utc": "2026-10-06T10:00:59.000Z", "age_s": 0.0, "stale": False,
                   "src": "node/kline-diag/alpha/21 09", "label": "idle", "raw": 800,
                   "m": "Vehicle.Powertrain.CombustionEngine.Speed", "m_unknown": True}
    assert any("unknown VSS path" in m for m in t.logs)
    assert t.view("beta")["signals"] == {}  # selecting a module only filters the view


def test_confidence_is_never_raised_and_a_mismatch_is_flagged_once():
    t = T(lookup=lambda m, n: ("candidate", None))
    t.put("lr_d2.alpha.rpm", vss("x", 1, t_us=1, c="proven"))
    for _ in range(3):
        assert t.view()["signals"]["rpm"]["c"] == "candidate"
    assert sum("pack store says candidate" in m for m in t.logs) == 1
    t2 = T(lookup=lambda m, n: ("proven", None))
    t2.put("lr_d2.alpha.rpm", vss("x", 1, t_us=1, c="maybe"))
    assert t2.view()["signals"]["rpm"]["c"] == "candidate"  # unknown level: candidate


def test_non_numeric_values_are_dropped_not_zeroed():
    t = T()
    assert not t.put("lr_d2.alpha.rpm", json.dumps({"value": "high", "t_us": 1, "source":
                                                    "kline-diag/alpha/21 09", "name": "rpm"}).encode())
    assert not t.put("lr_d2.alpha.rpm", json.dumps({"value": True, "t_us": 1, "source":
                                                    "kline-diag/alpha/21 09", "name": "rpm"}).encode())
    assert not t.put("lr_d2.alpha.rpm", b"not json")
    assert t.view()["signals"] == {}
    assert sum("non-numeric" in m for m in t.logs) == 1


def test_pack_id_mismatch_is_reported():
    t = T(pack_id="lr_d2")
    t.put("d2.alpha.rpm", vss("x", 1, t_us=1))
    assert any("names pack 'd2'" in m for m in t.logs)


# ---- staleness (§6.4) ------------------------------------------------------------------ #
def test_retained_on_subscribe_is_last_known_and_stale():
    t = T()
    t.put("lr_d2.alpha.rpm", vss("x", 700, t_us=5_000_000), retain=True)
    t.put("lr_d2.alpha.temp", vss("x", 80, t_us=5_000_000, name="temp",
                                  ts="2026-10-06T10:00:00.000Z"), retain=True)
    sigs = t.view()["signals"]
    assert sigs["rpm"]["stale"] and sigs["rpm"]["age_s"] is None        # age unknown
    assert sigs["temp"]["stale"] and sigs["temp"]["age_s"] == 60.0      # aged by its ts
    assert sigs["rpm"]["v"] == 700.0                                     # never zeroed
    t.tick(0.1)
    t.put("lr_d2.alpha.rpm", vss("x", 710, t_us=6_000_000))             # live
    sigs = t.view()["signals"]
    assert not sigs["rpm"]["stale"] and sigs["rpm"]["age_s"] == 0.0
    assert sigs["temp"]["stale"]                                          # still last known


def test_age_runs_on_the_node_clock():
    t = T()
    t.put("lr_d2.alpha.a", vss("x", 1, t_us=10_000_000, name="a"))
    t.put("lr_d2.alpha.b", vss("x", 2, t_us=13_000_000, name="b"))  # the device's latest
    t.tick(0.5)
    sigs = t.view()["signals"]
    assert sigs["b"]["age_s"] == 0.5 and sigs["a"]["age_s"] == 3.5
    assert sigs["a"]["stale"] is False  # 3.5 s < 3 × default interval
    t.tick(20)
    assert t.view()["signals"]["b"]["stale"] is True


def test_stale_threshold_follows_the_fields_own_pace():
    t = T()
    for i in range(6):  # a 0.5 s field
        t.put("lr_d2.alpha.rpm", vss("x", i, t_us=1_000_000 + i * 500_000))
        t.tick(0.5)
    t.tick(1.0)  # 1.5 s since the last: past 3 × 0.5 s but under the 2 s floor
    assert t.view()["signals"]["rpm"]["stale"] is False
    t.tick(0.6)
    assert t.view()["signals"]["rpm"]["stale"] is True


def test_a_late_stored_copy_never_replaces_a_live_value():
    t = T()
    t.put("lr_d2.alpha.rpm", vss("x", 900, t_us=2_000_000))
    t.put("lr_d2.alpha.rpm", vss("x", 100, t_us=1_000_000), retain=True)
    assert t.view()["signals"]["rpm"]["v"] == 900.0


def test_reboot_by_boot_id_marks_old_values():
    t = T()
    t.put("lr_d2.alpha.a", vss("x", 1, t_us=50_000_000, name="a", boot=7))
    t.put("lr_d2.alpha.b", vss("x", 2, t_us=50_000_000, name="b", boot=7))
    t.tick(1)
    t.put("lr_d2.alpha.a", vss("x", 3, t_us=900_000, name="a", boot=8))  # restarted
    sigs = t.view()["signals"]
    assert sigs["a"]["v"] == 3.0 and "before_restart" not in sigs["a"]
    assert sigs["b"]["before_restart"] and sigs["b"]["stale"] and sigs["b"]["v"] == 2.0
    assert any("boot id 7 → 8" in m for m in t.logs)
    assert t.view()["device"]["boot"] == 8


def test_retained_copies_from_an_older_boot_in_any_order():
    t = T()
    t.put("lr_d2.alpha.new", vss("x", 1, t_us=5, name="new", boot=9), retain=True)
    t.put("lr_d2.alpha.old", vss("x", 2, t_us=99_000_000, name="old", boot=8), retain=True)
    sigs = t.view()["signals"]
    assert sigs["old"].get("before_restart") and not sigs["new"].get("before_restart")


def test_reboot_inferred_from_t_us_without_a_boot_id():
    t = T()
    t.put("lr_d2.alpha.a", vss("x", 1, t_us=50_000_000, name="a", boot=None))
    t.put("lr_d2.alpha.b", vss("x", 2, t_us=50_000_000, name="b", boot=None))
    t.tick(1)
    t.put("lr_d2.alpha.a", vss("x", 3, t_us=2_000_000, name="a", boot=None))
    sigs = t.view()["signals"]
    assert sigs["b"].get("before_restart") and not sigs["a"].get("before_restart")
    assert any("t_us went backwards" in m for m in t.logs)


def test_power_since_us_backwards_is_a_reboot():
    t = T()
    t.put("", b'{"state":"awake","since_us":9000000}', kind="power")
    t.put("lr_d2.alpha.a", vss("x", 1, t_us=9_500_000, name="a", boot=None))
    t.put("", b'{"state":"awake","since_us":1000000}', kind="power")
    assert t.view()["signals"]["a"].get("before_restart")


# ---- devices, paths and selection (§6.5) ---------------------------------------------- #
def test_two_modules_on_one_vss_path_both_kept():
    t = T()
    path = "Vehicle.LowVoltageBattery.CurrentVoltage"
    t.put(path, vss("x", 13.9, t_us=1_000_000, name="battery", module="td5", unit="V"))
    t.put(path, json.dumps({"value": 12.8, "unit": "V", "t_us": 2_000_000, "boot": 7, "source":
                            "kline-diag/slabs/21 44", "name": "battery", "c": "proven"}).encode())
    assert t.view("td5")["signals"]["battery"]["v"] == 13.9
    assert t.view("slabs")["signals"]["battery"]["v"] == 12.8
    entry = t.view()["vss"][path]
    assert set(entry["sources"]) == {"node/kline-diag/td5/21 09",
                                     "node/kline-diag/slabs/21 44"}
    assert entry["sel"] == "node/kline-diag/slabs/21 44" and entry["value"] == 12.8  # fresher


def test_selection_rules():
    a = {"device": "a", "src": "a/x", "stale": False, "age_s": 3.0, "pack_decoded": False}
    b = {"device": "b", "src": "b/x", "stale": False, "age_s": 5.0, "pack_decoded": True}
    c = {"device": "c", "src": "c/x", "stale": True, "age_s": 0.1, "pack_decoded": True}
    assert select([a, b, c]) is b                  # the pack-decoded bus value first
    assert select([a, c]) is a                     # usable beats stale
    assert select([c]) is c                        # nothing usable: still shown, stale
    d = {**a, "device": "0", "src": "0/x"}
    assert select([a, d]) is d                     # ties: lowest device id
    assert select([]) is None


def test_two_devices_never_overwrite_each_other():
    t = T()
    path = "Vehicle.Exterior.AirTemperature"
    for dev, v in (("guardian", 11.0), ("sensor", 12.0)):
        t.put(path, json.dumps({"value": v, "unit": "celsius", "t_us": 1, "source": "imu/0",
                                "c": "candidate"}).encode(), device=dev)
    entry = t.view()["vss"][path]
    assert set(entry["sources"]) == {"guardian/imu/0", "sensor/imu/0"}
    assert entry["sel"] == "guardian/imu/0"
    assert t.view()["signals"] == {}  # no pack field: only in ``vss``


def test_device_state_and_last_seen():
    t = T()
    t.put("", case("online")["payload"], retain=True, kind="status")
    t.put("", case("awake")["payload"], retain=True, kind="power")
    dev = t.view()["device"]
    assert dev["status"] == "online" and dev["power"]["state"] == "awake"
    assert dev["last_seen_utc"] is None  # only stored values so far: not seen live
    t.put("lr_d2.alpha.rpm", vss("x", 1, t_us=1))
    assert t.view()["device"]["last_seen_utc"] == utc(t.wall)
    assert t.table.ingest("ostler/v1/other-car/node/status", b"online", False, 0, 0) is False
    assert t.table.ingest(BASE + "tap/01J/data", b"\x00", False, 0, 0) is False  # P2
    assert t.table.ignored == 2


# ---- the firmware's fixtures ----------------------------------------------------------- #
@pytest.mark.parametrize("name, module", [("td5-vectors.jsonl", "td5"),
                                          ("slabs-vectors.jsonl", "slabs")])
def test_firmware_fixtures_ingest_cleanly(name, module):
    t = T()
    used = 0
    last = {}
    for m in load(name):
        ok = t.table.ingest(m["topic"], m["payload"], m["retain"], t.now, t.wall)
        used += ok
        if "/vss/" in m["topic"]:
            assert ok, m["topic"]
            body = json.loads(m["payload"])
            last[body["name"]] = body
        t.tick(0.001)
    assert used == len([m for m in load(name) if "/tap/" not in m["topic"]])
    view = t.view(module)
    assert set(view["signals"]) == set(last)
    for field, body in last.items():
        sig = view["signals"][field]
        assert sig["v"] == float(body["value"]) and sig["u"] == body["unit"]
        assert sig.get("label") == body.get("state")
        assert sig["src"] == f"node/{body['source']}"
    assert view["device"]["boot"] == 7
    assert not [m for m in t.logs if "restart" in m]
    assert all(m["topic"].startswith(f"ostler/v1/{VID}/") for m in vss_messages())
