# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The VehiclePack contract and the platform modules package A made generic, run against
FAKE_PACK (a second, non-Discovery pack) so nothing here passes by accident of D2 data
(specs/2026-10-06-phase0-vehiclepack-decoupling-design.md §1, §4, §6)."""
from __future__ import annotations

import dataclasses

import pytest

from openostler import catalog, commands, dtc, faultscan, menus, modscan, pack, signals
from openostler.pack import FaultReader
from openostler.sniff import modules
from tests.fake_pack import FAKE_PACK


@pytest.fixture
def fake():
    with pack.use_pack(FAKE_PACK) as p:
        yield p


# ---- loader ------------------------------------------------------------------------------ #
class _EP:
    """A stand-in for an importlib.metadata entry point."""

    def __init__(self, name: str, obj, value: str = "") -> None:
        self.name, self._obj, self.value = name, obj, value or f"x.{name}:PACK"
        self.loaded = 0

    def load(self):
        self.loaded += 1
        return self._obj


@pytest.fixture
def loader(monkeypatch):
    """Fresh resolution state (restored afterwards), no env override, entry points faked."""
    monkeypatch.setattr(pack, "_override", None)
    monkeypatch.setattr(pack, "_cached", None)
    monkeypatch.delenv(pack.ENV_VAR, raising=False)
    eps: "list[_EP]" = []
    monkeypatch.setattr(pack, "_entry_points", lambda: list(eps))
    return eps


def test_single_entry_point_is_used_and_cached(loader):
    ep = _EP("fake", FAKE_PACK)
    loader.append(ep)
    assert pack.active_pack() is FAKE_PACK
    assert pack.active_pack() is FAKE_PACK
    assert ep.loaded == 1                                   # cached after the first call


def test_env_override_picks_an_entry_point_by_name(loader, monkeypatch):
    other = dataclasses.replace(FAKE_PACK, id="other")
    loader += [_EP("fake", FAKE_PACK), _EP("other", other)]
    monkeypatch.setenv(pack.ENV_VAR, "other")
    assert pack.active_pack() is other


def test_env_override_accepts_a_module_attr_reference(loader, monkeypatch):
    monkeypatch.setenv(pack.ENV_VAR, "tests.fake_pack:FAKE_PACK")
    assert pack.active_pack() is FAKE_PACK


def test_env_override_naming_nothing_is_an_error(loader, monkeypatch):
    loader.append(_EP("fake", FAKE_PACK))
    monkeypatch.setenv(pack.ENV_VAR, "nope")
    with pytest.raises(LookupError, match="fake"):
        pack.active_pack()


def test_several_entry_points_without_env_is_an_error(loader):
    loader += [_EP("fake", FAKE_PACK), _EP("other", FAKE_PACK)]
    with pytest.raises(RuntimeError, match="fake.*other"):
        pack.active_pack()


def test_no_entry_point_is_a_clear_error_naming_the_group_and_the_fix(loader):
    # ADR-0015: the Phase 0 built-in fallback is gone; the platform ships no pack.
    with pytest.raises(pack.NoVehiclePackError) as exc:
        pack.active_pack()
    msg = str(exc.value)
    assert "openostler.vehicle" in msg and "pip install" in msg and pack.ENV_VAR in msg
    assert not hasattr(pack, "_BUILTIN_FALLBACK")


def test_a_non_pack_or_wrong_api_version_is_refused(loader):
    loader.append(_EP("bad", object()))
    with pytest.raises(TypeError):
        pack.active_pack()
    loader[:] = [_EP("old", dataclasses.replace(FAKE_PACK, api_version=pack.PACK_API_VERSION + 1))]
    pack.set_active_pack(None)
    with pytest.raises(RuntimeError, match="api_version"):
        pack.active_pack()


def test_set_active_pack_wins_and_use_pack_restores(loader):
    loader.append(_EP("fake", FAKE_PACK))
    other = dataclasses.replace(FAKE_PACK, id="other")
    with pack.use_pack(other):
        assert pack.active_pack() is other
    assert pack.active_pack() is FAKE_PACK


# ---- canonical ids ----------------------------------------------------------------------- #
def test_canonical(fake):
    assert fake.canonical("alpha") == "alpha" and fake.canonical("A") == "alpha"
    assert fake.canonical(" Alpha ") == "alpha"
    assert fake.canonical("zeta") == "zeta" and fake.canonical(None) is None
    assert pack.canonical_module("a") == "alpha"
    assert fake.aliases() == {"a": "alpha"}
    assert fake.module("a").name == "ALPHA (fake engine)" and fake.module("zeta") is None
    assert fake.manifest()["modules"][1] == {"id": "beta", "name": "BETA (fake body)",
                                            "aliases": [], "live": False}


# ---- commands ---------------------------------------------------------------------------- #
def test_registry_is_built_from_the_active_pack(fake):
    reg = commands.registry()
    assert set(reg) == {("alpha", "ping"), ("alpha", "zap")}
    assert commands.registry() is reg                       # cached per pack
    assert commands.REGISTRY is reg                         # old name, same object
    assert [c.action for c in commands.for_module("alpha")] == ["ping", "zap"]
    assert commands.get("alpha", "ping").label == "Ping"
    assert commands.get("td5", "output_fuel_pump") is None  # no D2 leakage


def test_registry_follows_a_pack_switch(fake):
    fake_reg = commands.registry()
    other = dataclasses.replace(FAKE_PACK, actions=FAKE_PACK.actions[:1])
    with pack.use_pack(other):
        assert set(commands.registry()) == {("alpha", "ping")}
    assert commands.registry() is fake_reg


def test_refusal_policy_on_fake_actions(fake):
    assert commands.refusal("alpha", "ping") is None                 # verified read
    assert commands.refusal("alpha", "ping", public=True) is None    # reads stay allowed
    assert "gated" in commands.refusal("alpha", "zap", trust="experimental")
    assert commands.refusal("alpha", "select_module") is None        # not a module command


# ---- catalog + menus --------------------------------------------------------------------- #
def test_menus_come_from_the_pack(fake):
    assert menus.MENUS is FAKE_PACK.menus
    assert menus.menu_for("a") == FAKE_PACK.menus["alpha"]           # alias accepted
    assert menus.menu_for("beta") == [] and menus.menu_for("zeta") == []


def test_build_catalog_on_the_fake_pack(fake):
    cat = catalog.build_catalog("a")
    assert cat["store_module"] == "alpha"
    assert cat["coverage"] == {"verified": 3, "candidate": 1, "sniff": 1, "untranscribed": 0,
                               "total": 5}
    items = {i["id"]: i for p in cat["pages"] for g in p["groups"] for i in g["items"]}
    assert items["speed"]["status"] == "verified" and items["speed"]["lid"] == "01"
    assert items["temp"]["status"] == "candidate"
    assert (items["zap"]["status"], items["zap"]["safety"]) == ("sniff", "gated")
    assert catalog.legacy_menu("alpha")[1]["items"][0] == {
        "name": "Speed", "status": "ok", "ref": "", "sig": "alpha_speed"}


def test_module_summary_on_the_fake_pack(fake):
    rows = catalog.module_summary()
    assert [(r["module"], r["store_module"], r["name"]) for r in rows] == [
        ("alpha", "alpha", "ALPHA (fake engine)")]
    assert rows[0]["coverage"]["total"] == 5
    assert catalog.store_module_for("a") == "alpha"
    assert catalog.module_name("beta") == "BETA (fake body)" and catalog.module_name("q") == "q"


def test_unlinked_ok_drift_guard_on_the_fake_pack(fake):
    linked = {it["sig"] for g in menus.menu_for("alpha") for it in g["items"] if it.get("sig")}
    store = {r["name"] for r in signals.load_records("alpha")}
    assert store - linked - fake.unlinked_ok["alpha"] == set()


# ---- stores: caches never cross packs ---------------------------------------------------- #
def test_signal_and_dtc_caches_are_keyed_by_store(fake):
    assert [s.name for s in signals.load_signals("alpha")] == ["alpha_speed", "alpha_temp"]
    assert set(dtc.load_meanings("alpha")) == {"A1"}
    with pack.use_pack(dataclasses.replace(FAKE_PACK, signals_dir=FAKE_PACK.root / "nowhere",
                                           dtc_dir=FAKE_PACK.root / "nowhere")):
        assert signals.load_signals("alpha") == []          # another store: not the cache
        assert dtc.load_meanings("alpha") == {}
    assert len(signals.load_signals("alpha")) == 2


# ---- faultscan --------------------------------------------------------------------------- #
def _with_readers(*readers, unimplemented=()):
    return dataclasses.replace(FAKE_PACK, faultscan=tuple(readers),
                               faultscan_unimplemented=tuple(unimplemented))


def test_read_all_runs_every_reader_in_order(monkeypatch):
    import openostler.ports as ports

    seen, gaps = [], []

    def boom(port):
        seen.append(("boom", port))
        raise OSError("bus dead")

    def one(port):
        seen.append(("one", port))
        return ["X1"]

    p = _with_readers(FaultReader("ONE", one, note="n1"),
                      FaultReader("BOOM", boom, note="plain", error_note="why it failed"),
                      FaultReader("NONE", lambda port: [], note="quiet"),
                      FaultReader("BOOM2", boom, note="kept on error"),
                      unimplemented=(("LATER", "no reader"),))
    monkeypatch.setattr(ports, "resolve_serial_port", lambda spec: f"real:{spec}")
    with pack.use_pack(p):
        rows = faultscan.read_all("auto", sleep=gaps.append)
    assert seen == [("one", "real:auto"), ("boom", "real:auto"), ("boom", "real:auto")]
    assert rows == [
        {"module": "ONE", "status": "faults", "faults": ["X1"], "note": "n1"},
        {"module": "BOOM", "status": "error", "faults": [], "error": "OSError: bus dead",
         "note": "why it failed"},
        {"module": "NONE", "status": "ok", "faults": [], "note": "quiet"},
        {"module": "BOOM2", "status": "error", "faults": [], "error": "OSError: bus dead",
         "note": "kept on error"},
        {"module": "LATER", "status": "unimplemented", "faults": [], "note": "no reader"},
    ]
    assert gaps == [0.5, 0.5, 0.5]                          # between modules only


def test_read_all_without_a_cable_marks_each_reader(monkeypatch, fake):
    import openostler.ports as ports

    def nope(spec):
        raise FileNotFoundError("no cable")

    monkeypatch.setattr(ports, "resolve_serial_port", nope)
    rows = faultscan.read_all("auto", sleep=lambda *_: None)
    assert rows == [
        {"module": "ALPHA", "status": "error", "faults": [], "error": "FileNotFoundError: no cable",
         "note": ""},
        {"module": "BETA", "status": "unimplemented", "faults": [],
         "note": "no fault reader in the fake pack"},
    ]


# ---- sniff detection + modscan ----------------------------------------------------------- #
def _b(s: str) -> "list[int]":
    return [int(t, 16) for t in s.split()]


def test_sniff_detection_uses_the_active_spec(fake):
    assert modules.name_for_address(0x10) == "alpha"
    assert modules.name_for_address(0x13) == "unknown:0x13"            # no D2 leakage
    assert modules.scan(_b("81 10 f7 81 00")) == [("alpha", "fast-init 0x10")]
    assert modules.scan(_b("aa 10 01")) == [("alpha", "aa-10 marker")]
    assert modules.fast_init_signal(_b("00 81 77 f7 81")) == ("unknown:0x77", 0x77)
    assert modules.FAST_INIT_ADDRESSES == {0x10: "alpha"}
    assert modules.SLOW_INIT_ADDRESSES == {} and modules.TESTER == 0xF7


def test_module_tracker_authority_and_hints():
    from openostler.pack import Detector, SniffSpec

    spec = SniffSpec(
        fast_init={0x10: "alpha"}, slow_init={0x20: "beta"}, tester=0xF1,
        authoritative=(Detector("beta", "addressed", lambda b: b[:2] == [0x82, 0x20]),),
        hints=(Detector("gamma", "g-hint", lambda b: 0x99 in b),
               Detector("delta", "d-hint", lambda b: 0x99 in b or 0x98 in b)))
    t = modules.ModuleTracker(spec)
    assert t.feed(_b("00 99")) == "gamma"          # a hint seeds from None, first hint wins
    assert t.feed(_b("00 98")) == "gamma"          # a hint never overrides a known module
    assert t.feed(_b("81 10 f1 81")) == "alpha"    # fast init (with the spec's tester) switches
    assert t.feed(_b("81 10 f7 81")) == "alpha"    # wrong tester byte: no init
    assert t.feed(_b("82 20 00")) == "beta"        # authoritative always switches
    assert t.feed(_b("01 02")) == "beta"           # no signal: stays put
    assert modules.scan(_b("82 20 99"), spec) == [("beta", "addressed"), ("gamma", "g-hint"),
                                                 ("delta", "d-hint")]
    assert modules.name_for_address(0x20, spec) == "beta"


def test_module_tracker_defaults_to_the_active_pack(fake):
    t = modules.ModuleTracker()
    assert t.feed(_b("aa 10")) == "alpha"


def test_modscan_defaults_come_from_the_spec(fake):
    assert modscan.DEFAULT_FAST == [0x10] and modscan.DEFAULT_SLOW == []
    spec = dataclasses.replace(FAKE_PACK.sniff, slow_init={0x30: "beta"}, extra_scan=(0x31, 0x30))
    assert modscan.default_slow(spec) == [0x30, 0x31]
    assert modscan.default_fast(spec) == [0x10]


def test_modscan_names_addresses_from_the_pack(fake):
    from openostler.kline import KLine
    from openostler.kline.frame import encode
    from openostler.kwp2000 import KWP2000
    from tests.fakes import FakeKLineEcu

    start = bytes(encode(b"\x81", 0x10, 0xF7, addressed=True))
    kwp = KWP2000(KLine(FakeKLineEcu({start: b"\xc1\x57\x8f"})), tolerant=True)
    kwp.open()
    rows = modscan.AddressScanner(kwp, sleep=lambda _s: None, settle=0.0).scan(fast=[0x10, 0x11],
                                                                              slow=[])
    assert [(r["module"], r["status"]) for r in rows] == [("alpha", "responded"),
                                                          ("unknown:0x11", "silent")]


def test_entry_points_read_the_new_and_the_legacy_group(monkeypatch):
    """ADR-0014: ``openostler.vehicle`` is the group; ``ostler.vehicle`` is still read for one
    release, and a pack registered under both is listed once."""
    from importlib import metadata

    class EP:
        def __init__(self, name, value):
            self.name, self.value = name, value

    groups = {
        "openostler.vehicle": [EP("lr_d2", "d2diag:PACK")],
        "ostler.vehicle": [EP("old", "x:PACK"), EP("lr_d2", "d2diag:PACK")],
    }

    class EPs:
        def select(self, group):
            return groups.get(group, [])

    monkeypatch.setattr(metadata, "entry_points", lambda: EPs())
    found = [(e.name, e.value) for e in pack._entry_points()]
    assert found == [("lr_d2", "d2diag:PACK"), ("old", "x:PACK")]
    assert pack.ENTRY_POINT_GROUP == "openostler.vehicle"
    assert pack.LEGACY_ENTRY_POINT_GROUPS == ("ostler.vehicle",)
