"""Tests for the module maps (Map tab) and the coverage calculation (legacy shape)."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")


from openostler import catalog
from openostler.menus import MENUS
from openostler.web.server import DiagServer
from tests.fake_sources import FakeTd5Source, FakeSlabsSource


def test_all_modules_have_populated_maps():
    for name in ("td5", "slabs", "bcu", "ace", "autobox", "airbag"):
        menu = MENUS[name]
        assert menu, f"{name} has an empty map"
        for group in menu:
            # a Utilities parent (e.g. BCU key programming) may hold only sub-groups
            has_children = any(g.get("parent") == group["id"] for g in menu)
            assert group["items"] or has_children, f"{name}/{group['cat']} is missing items"
            for item in group["items"]:
                assert {"id", "name"} <= set(item)
        for group in catalog.legacy_menu(name):
            for item in group["items"]:
                assert set(item) >= {"name", "status", "ref"}
                assert item["status"] in {"ok", "maybe", "todo"}


def test_coverage_counts_match_maps():
    srv = DiagServer(
        {"motor": FakeTd5Source(), "slabs": FakeSlabsSource()},
        port=0, menus=MENUS, active="slabs",
    )
    try:
        cov = srv.coverage()
        assert set(cov) == set(MENUS)
        for name in MENUS:
            menu = catalog.legacy_menu(name)
            tot = sum(len(g["items"]) for g in menu)
            ok = sum(1 for g in menu for i in g["items"] if i["status"] == "ok")
            mb = sum(1 for g in menu for i in g["items"] if i["status"] == "maybe")
            assert cov[name] == {"ok": ok, "maybe": mb, "total": tot}
            assert cov[name]["ok"] + cov[name]["maybe"] <= tot
    finally:
        srv.server_close()


def test_airbag_has_no_output_actuators():
    """SRS is pyrotechnic — the map must not list activatable outputs as tests."""
    names = [i["name"].lower() for g in MENUS["airbag"] for i in g["items"]]
    # the only output row should be the confirmed 'no output page'
    assert any("no output" in n for n in names)
    assert not any("force on" in n or "activate" in n for n in names)
    assert not any(i.get("actions") for g in MENUS["airbag"] for i in g["items"])
