"""The catalog on the Discovery 2 reference pack's real menus: drift guards and invariants
(integration; needs the ``d2diag`` pack installed, see tests/conftest.py)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")

from openostler import catalog, commands, pack, signals  # noqa: E402
from openostler.menus import MENUS  # noqa: E402


def _items(cat: dict) -> "list[dict]":
    return [i for p in cat["pages"] for g in p["groups"] for i in g["items"]]


def test_store_module_for_is_the_canonical_id():
    # Deprecated wrapper over openostler.pack.canonical_module (aliases from the pack).
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
    allowed = pack.active_pack().unlinked_ok.get(module, frozenset())
    store = {r["name"] for r in signals.load_records(module)}
    missing = store - linked - allowed
    assert not missing, f"{module}: store signals neither linked nor in UNLINKED_OK: {sorted(missing)}"
    assert not (allowed & linked), f"{module}: UNLINKED_OK names that are linked: {allowed & linked}"
    assert allowed <= store, f"{module}: UNLINKED_OK names not in the store: {allowed - store}"


def test_store_modules_all_have_menus():
    stores = sorted(signals._dir().glob("*.json"))
    assert stores, "the pack's signal store is empty"
    for p in stores:
        assert p.stem in MENUS, p.stem


def test_module_summary():
    rows = catalog.module_summary()
    assert [r["store_module"] for r in rows] == list(MENUS)
    assert rows[0]["module"] == "td5"                      # canonical ids, no UI alias
    for r in rows:
        assert r["module"] == r["store_module"]
        assert r["name"] == pack.active_pack().module(r["module"]).name
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
