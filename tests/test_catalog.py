"""The catalog (ADR-0008): derivation rules on synthetic menus + invariants on the real ones."""
from __future__ import annotations

import pytest

from d2diag import catalog, commands, signals
from d2diag.commands import Command
from d2diag.menus import MENUS
from d2diag.signals import Signal

FAKE = "fake"


@pytest.fixture
def fake(monkeypatch):
    """A synthetic module: a tiny store, a few registry actions, and a menu set per test."""
    store = [
        Signal("good", 0x10, 0, confidence="proven"),
        Signal("meh", 0x11, 0, confidence="candidate"),
        Signal("dup", 0x1B, 4, confidence="candidate", length=8),
        Signal("dup", 0x1B, 6, confidence="proven", length=10),
    ]
    real_load = signals.load_signals
    monkeypatch.setattr(catalog.signals, "load_signals",
                        lambda m: store if m == FAKE else real_load(m))
    for c in (
        Command("ok_act", FAKE, "Verified", status="verified", safety="actuator"),
        Command("exp_act", FAKE, "Experimental", status="experimental", safety="read"),
        Command("plan_act", FAKE, "Planned", status="planned", safety="service"),
        Command("gate_act", FAKE, "Gated", status="planned", safety="gated"),
        Command("gate2_act", FAKE, "Gated 2", status="planned", safety="gated"),
    ):
        monkeypatch.setitem(commands.REGISTRY, (FAKE, c.action), c)

    def set_menu(groups):
        monkeypatch.setitem(MENUS, FAKE, groups)
        return groups
    return set_menu


def _items(cat: dict) -> "list[dict]":
    return [i for p in cat["pages"] for g in p["groups"] for i in g["items"]]


def _one(fake, item: dict, page: str = "inputs") -> dict:
    fake([{"id": "g", "page": page, "cat": "G", "items": [{"id": "x", "name": "X", **item}]}])
    return _items(catalog.build_catalog(FAKE))[0]


# ---- derivation rules -------------------------------------------------------------------- #
def test_sig_proven_is_verified_and_read(fake):
    it = _one(fake, {"sig": "good"})
    assert (it["status"], it["safety"], it["lid"], it["actions"]) == ("verified", "read", "10", [])


def test_sig_candidate_is_candidate(fake):
    assert _one(fake, {"sig": "meh"})["status"] == "candidate"


def test_sig_first_record_without_at(fake):
    assert _one(fake, {"sig": "dup"})["status"] == "candidate"  # 1B@4 comes first


def test_sig_at_picks_the_variant(fake):
    assert _one(fake, {"sig": "dup", "at": "1B@6"})["status"] == "verified"
    assert _one(fake, {"sig": "dup", "at": "1b@4"})["status"] == "candidate"


def test_unknown_sig_or_at_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"sig": "nope"})
    with pytest.raises(ValueError):
        _one(fake, {"sig": "dup", "at": "1B@9"})


def test_actions_all_verified(fake):
    it = _one(fake, {"actions": ["ok_act"]}, page="outputs")
    assert (it["status"], it["safety"]) == ("verified", "actuator")
    assert it["actions"][0]["action"] == "ok_act"


def test_actions_worst_non_gated_wins(fake):
    assert _one(fake, {"actions": ["ok_act", "exp_act"]}, "outputs")["status"] == "candidate"
    assert _one(fake, {"actions": ["ok_act", "exp_act", "plan_act"]}, "outputs")["status"] == "sniff"
    # a gated action does not drag the status down, but it sets the safety
    it = _one(fake, {"actions": ["ok_act", "gate_act"]}, "utilities")
    assert (it["status"], it["safety"]) == ("verified", "gated")


def test_actions_all_gated_is_sniff_and_gated(fake):
    it = _one(fake, {"actions": ["gate_act", "gate2_act"]}, "utilities")
    assert (it["status"], it["safety"]) == ("sniff", "gated")


def test_action_safety_is_most_severe(fake):
    assert _one(fake, {"actions": ["exp_act", "plan_act"]}, "utilities")["safety"] == "service"


def test_unregistered_action_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"actions": ["missing"]}, "outputs")


def test_hand_status_and_placeholder(fake):
    assert _one(fake, {"status": "sniff"})["status"] == "sniff"
    it = _one(fake, {"untranscribed": True, "pages": 4})
    assert (it["status"], it["placeholder"], it["pages"]) == ("untranscribed", True, 4)
    with pytest.raises(ValueError):
        _one(fake, {"status": "ok"})  # legacy vocabulary is not accepted


def test_hand_verified_only_on_session_and_faults(fake):
    assert _one(fake, {"status": "verified"}, "session")["status"] == "verified"
    assert _one(fake, {"status": "verified"}, "faults")["status"] == "verified"
    with pytest.raises(ValueError):
        _one(fake, {"status": "verified"}, "inputs")


def test_link_plus_hand_status_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"sig": "good", "status": "sniff"})
    with pytest.raises(ValueError):
        _one(fake, {"actions": ["ok_act"], "status": "verified"}, "outputs")


def test_pages_fixed_order_session_folds_into_faults(fake):
    fake([
        {"id": "u", "page": "utilities", "cat": "U", "items": [{"id": "a", "name": "A", "status": "sniff"}]},
        {"id": "s", "page": "session", "cat": "S", "items": [{"id": "b", "name": "B", "status": "verified"}]},
    ])
    cat = catalog.build_catalog(FAKE)
    assert [p["id"] for p in cat["pages"]] == ["faults", "inputs", "outputs", "settings", "utilities"]
    faults = cat["pages"][0]
    assert [g["id"] for g in faults["groups"]] == ["s"]
    assert faults["coverage"]["verified"] == 1
    empty = cat["pages"][1]
    assert empty["groups"] == [] and empty["coverage"]["total"] == 0
    assert cat["coverage"] == {"verified": 1, "candidate": 0, "sniff": 1, "untranscribed": 0, "total": 2}


def test_item_and_group_shape(fake):
    fake([{"id": "g", "page": "inputs", "cat": "Inputs — X", "nanocom": "m/inputs", "items": [
        {"id": "x", "name": "X", "sig": "good", "ref": "21 10", "note": "n"}]}])
    cat = catalog.build_catalog(FAKE)
    assert set(cat) == {"store_module", "coverage", "pages"}
    group = cat["pages"][1]["groups"][0]
    assert group == {"id": "g", "title": "Inputs — X", "parent": None, "nanocom": "m/inputs",
                     "items": group["items"]}
    assert set(group["items"][0]) == {"id", "name", "status", "safety", "sig", "lid", "ref", "note",
                                      "placeholder", "pages", "actions"}


def test_legacy_status_and_menu(fake):
    assert [catalog.legacy_status(s) for s in catalog.STATUSES] == ["ok", "maybe", "todo", "todo"]
    fake([{"id": "g", "page": "inputs", "cat": "G", "items": [
        {"id": "a", "name": "A", "sig": "good", "lid": "10"},
        {"id": "b", "name": "B", "sig": "meh"},
        {"id": "c", "name": "C", "status": "sniff"}]}])
    assert catalog.legacy_menu(FAKE) == [{"cat": "G", "items": [
        {"name": "A", "status": "ok", "ref": "", "lid": "10", "sig": "good"},
        {"name": "B", "status": "maybe", "ref": "", "sig": "meh"},
        {"name": "C", "status": "todo", "ref": ""}]}]


def test_ui_module_aliases():
    assert catalog.store_module_for("motor") == "td5"
    assert catalog.store_module_for("eat") == catalog.store_module_for("gearbox") == "autobox"
    assert catalog.store_module_for("slabs") == "slabs"
    assert catalog.build_catalog("motor")["store_module"] == "td5"


# ---- invariants on the real menus -------------------------------------------------------- #
MODULES = list(MENUS)


@pytest.mark.parametrize("module", MODULES)
def test_real_menu_builds(module):
    """Every sig resolves (and every `at` matches), every action is registered, no item has a
    link plus a hand status, hand verified only on session/fault pages (build raises otherwise)."""
    catalog.build_catalog(module)


@pytest.mark.parametrize("module", MODULES)
def test_every_sig_and_at_resolves(module):
    for g in MENUS[module]:
        for it in g["items"]:
            if it.get("sig"):
                assert catalog.find_record(module, it["sig"], it.get("at")), (module, it["id"])
            if it.get("at"):
                assert it.get("sig"), f"{module}/{it['id']}: 'at' without 'sig'"


@pytest.mark.parametrize("module", MODULES)
def test_every_action_registered(module):
    for g in MENUS[module]:
        for it in g["items"]:
            for a in it.get("actions", []):
                assert commands.get(module, a) is not None, (module, it["id"], a)


@pytest.mark.parametrize("module", MODULES)
def test_no_link_with_hand_status(module):
    for g in MENUS[module]:
        for it in g["items"]:
            if it.get("sig") or it.get("actions"):
                assert "status" not in it, (module, it["id"])
            else:
                assert it.get("status") in catalog.STATUSES or it.get("untranscribed"), (module, it["id"])


@pytest.mark.parametrize("module", MODULES)
def test_hand_verified_only_on_session_or_faults(module):
    for g in MENUS[module]:
        for it in g["items"]:
            if it.get("status") == "verified":
                assert g["page"] in catalog.HAND_VERIFIED_PAGES, (module, it["id"])


@pytest.mark.parametrize("module", MODULES)
def test_gated_items_have_no_runnable_action(module):
    for it in _items(catalog.build_catalog(module)):
        if it["safety"] == "gated":
            for a in it["actions"]:
                assert commands.refusal(module, a["action"], trust="experimental") is not None, it["id"]


def test_airbag_is_read_or_gated_only():
    items = _items(catalog.build_catalog("airbag"))
    assert items
    for it in items:
        assert it["safety"] in ("read", "gated"), it["id"]
        for a in it["actions"]:
            assert commands.refusal("airbag", a["action"], trust="experimental") is not None
    assert commands.for_module("airbag") == [] or all(
        c.safety == "gated" for c in commands.for_module("airbag"))


@pytest.mark.parametrize("module", MODULES)
def test_unique_ids_and_valid_groups(module):
    groups = MENUS[module]
    gids = [g["id"] for g in groups]
    assert len(gids) == len(set(gids)), module
    ids = [it["id"] for g in groups for it in g["items"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    assert not dupes, (module, dupes)
    by_id = {g["id"]: g for g in groups}
    for g in groups:
        assert g["page"] in catalog.GROUP_PAGES, (module, g["id"])
        assert g["items"] or any(c.get("parent") == g["id"] for c in groups), (module, g["id"], "empty")
        parent = g.get("parent")
        if parent:  # at most two levels: a parent must exist, share the page and be top-level
            assert parent in by_id, (module, g["id"])
            assert by_id[parent]["page"] == g["page"], (module, g["id"])
            assert not by_id[parent].get("parent"), (module, g["id"], "nested deeper than two levels")


@pytest.mark.parametrize("module", MODULES)
def test_coverage_sums(module):
    cat = catalog.build_catalog(module)
    keys = ("verified", "candidate", "sniff", "untranscribed", "total")
    for k in keys:
        assert sum(p["coverage"][k] for p in cat["pages"]) == cat["coverage"][k]
    for cov in [cat["coverage"]] + [p["coverage"] for p in cat["pages"]]:
        assert cov["total"] == sum(cov[k] for k in keys[:4])
    assert cat["coverage"]["total"] == len(_items(cat)) == sum(len(g["items"]) for g in MENUS[module])


@pytest.mark.parametrize("module", ["td5", "slabs"])
def test_drift_guard_every_store_signal_is_linked(module):
    linked = {it["sig"] for g in MENUS[module] for it in g["items"] if it.get("sig")}
    allowed = catalog.UNLINKED_OK.get(module, set())
    store = {r["name"] for r in signals.load_records(module)}
    missing = store - linked - allowed
    assert not missing, f"{module}: store signals neither linked nor in UNLINKED_OK: {sorted(missing)}"
    assert not (allowed & linked), f"{module}: UNLINKED_OK names that are linked: {allowed & linked}"
    assert allowed <= store, f"{module}: UNLINKED_OK names not in the store: {allowed - store}"


def test_store_modules_all_have_menus():
    import pathlib
    store_dir = pathlib.Path(signals.__file__).parent
    for p in store_dir.glob("*.json"):
        assert p.stem in MENUS, p.stem


def test_module_summary():
    rows = catalog.module_summary()
    assert [r["store_module"] for r in rows] == list(MENUS)
    assert rows[0]["module"] == "motor"
    for r in rows:
        assert set(r) == {"module", "store_module", "name", "coverage"}
        assert r["coverage"] == catalog.build_catalog(r["store_module"])["coverage"]
        assert r["name"] != r["store_module"]


@pytest.mark.parametrize("module", MODULES)
def test_legacy_menu_shape(module):
    legacy = catalog.legacy_menu(module)
    assert [g["cat"] for g in legacy] == [g["cat"] for g in MENUS[module]]
    for g in legacy:
        for it in g["items"]:
            assert {"name", "status", "ref"} <= set(it) <= {"name", "status", "ref", "lid", "sig"}
            assert it["status"] in {"ok", "maybe", "todo"}


def test_keeps_names_the_sniff_test_relies_on():
    fuel = next(g for g in MENUS["td5"] if "Fuelling" in g["cat"])
    assert fuel["page"] == "inputs"
    assert any("Switches" in g["cat"] for g in MENUS["slabs"])
