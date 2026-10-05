"""Shared pytest wiring: the Discovery 2 reference pack as an optional test dependency.

Platform tests run against ``tests/fake_pack.py`` and need no pack. Integration tests that
exercise the real Discovery 2 pack (``d2diag``, ADR-0015) are marked
``pytest.mark.needs_pack`` (module-level ``pytestmark``). Without the pack installed they
are skipped with a reason that says how to install it; with ``OSTLER_REQUIRE_PACK=1``
(set in CI) a missing pack is an error instead, so CI can never pass by skipping them.
"""
from __future__ import annotations

import importlib.util
import os

import pytest

PACK_DIST = "d2diag"
INSTALL = ('pip install --no-deps "d2diag @ git+https://github.com/JamesWrightDavid/'
           'discovery2-diag@split-pack" (or pip install --no-deps -e <pack checkout>)')


def pack_installed() -> bool:
    return importlib.util.find_spec(PACK_DIST) is not None


def _require_pack() -> bool:
    return os.environ.get("OSTLER_REQUIRE_PACK", "").strip() not in ("", "0")


def pytest_configure(config):
    # Modules that import the pack at the top skip themselves with pytest.importorskip;
    # in CI that must be an error, not a silent skip.
    if _require_pack() and not pack_installed():
        raise pytest.UsageError(
            f"OSTLER_REQUIRE_PACK is set but the {PACK_DIST!r} vehicle pack is not installed, "
            f"so the needs_pack integration tests would be skipped. Install it: {INSTALL}")


def pytest_collection_modifyitems(config, items):
    if pack_installed():
        return
    needing = [it for it in items if it.get_closest_marker("needs_pack")]
    skip = pytest.mark.skip(reason=f"needs the Discovery 2 pack {PACK_DIST!r}: {INSTALL}")
    for it in needing:
        it.add_marker(skip)


@pytest.fixture(autouse=True)
def _fake_pack_for_marked_tests(request):
    """Tests in a module marked ``pytest.mark.fake_pack`` run with ``FAKE_PACK`` active
    (platform logic that only needs *a* pack), except those also marked ``needs_pack``,
    which run against the installed Discovery 2 pack."""
    if request.node.get_closest_marker("fake_pack") and not request.node.get_closest_marker("needs_pack"):
        from openostler.pack import use_pack
        from tests.fake_pack import FAKE_PACK

        with use_pack(FAKE_PACK):
            yield
    else:
        yield
