"""Module detection across all buses (sniff/modules.py).

Sample frames come straight from the D2 pack's protocol state handoff
(references/ in discovery2-diag) and d2diag.sniff.library.KNOWN, one per bus.
"""

import pytest

pytestmark = pytest.mark.needs_pack
pytest.importorskip("d2diag", reason="needs the Discovery 2 pack 'd2diag' (see tests/conftest.py)")

from openostler.sniff.modules import ModuleTracker, name_for_address, scan


def _b(hexstr):
    return [int(t, 16) for t in hexstr.split()]


def test_fast_init_addresses():
    assert ("td5", "fast-init 0x13") in scan(_b("81 13 f7 81 0c"))
    assert ("slabs", "fast-init 0x29") in scan(_b("81 29 f7 81 22"))


def test_unknown_fast_init_is_tagged_not_dropped():
    sigs = scan(_b("81 44 f7 81 56"))
    assert sigs and sigs[0][0] == "unknown:0x44"
    assert name_for_address(0x44) == "unknown:0x44"


def test_airbag_addressed_framing():
    # 82 5b f7 21 02 (request) — handoff line 885
    assert any(m == "airbag" for m, _ in scan(_b("82 5b f7 21 02 f7")))


def test_eat_request_and_response():
    assert any(m == "autobox" for m, _ in scan(_b("72 05 04 00 73")))   # XOR-closed request
    assert any(m == "autobox" for m, _ in scan(_b("72 09 60 01 00 1b")))  # 72 .. 60 response


def test_ace_bulk_pairs():
    assert any(m == "ace" for m, _ in scan(_b("67 67 11 e0 e0 f0 f0 00")))


def test_bcu_eka_identifier():
    assert any(m == "bcu" for m, _ in scan(_b("02 21 cc 2f")))


def test_tracker_keeps_authoritative_module_over_content_hint():
    t = ModuleTracker()
    assert t.feed(_b("81 13 f7 81 0c")) == "td5"
    # A stray 0x72 byte that happens to XOR-close must NOT flip Td5 to the gearbox.
    assert t.feed(_b("04 61 72 00 72 0b")) == "td5"


def test_tracker_seeds_from_content_when_no_init_seen():
    t = ModuleTracker()
    # A capture that starts mid-session on the autobox (no fast init in view).
    assert t.feed(_b("72 05 04 00 73")) == "autobox"
