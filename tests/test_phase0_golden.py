"""Phase 0 golden diff: the VehiclePack move must not change platform outputs except the
``motor`` → ``td5`` id (specs/2026-10-06-phase0-vehiclepack-decoupling-design.md §8).

The fixture was captured from the code before Step 0 by ``tests/phase0_golden.py``. A
section that differs is a behaviour change: fix the code, or (for a reviewed, intended
change) regenerate with ``python3 tests/phase0_golden.py --write``.
"""
from __future__ import annotations

import json

import pytest

from tests import phase0_golden


def _tool():
    return phase0_golden


@pytest.fixture(scope="module")
def golden():
    g = _tool()
    want = json.loads(g.FIXTURE.read_text(encoding="utf-8"))
    return want, g.capture()


def test_golden_sections_match(golden):
    want, got = golden
    assert sorted(got) == sorted(want)
    for key in sorted(want):
        assert got[key] == want[key], f"phase0 golden section {key!r} changed"


def test_normalise_maps_motor_to_td5():
    g = _tool()
    assert g.normalise({"motor": ["motor", "· motor: rpm", "motorway"]}) == \
        {"td5": ["td5", "· td5: rpm", "motorway"]}
