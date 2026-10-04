"""Tests for the BCU read-only input scan (T-16)."""
import random

import pytest

from d2diag.bcu.scan import FORBIDDEN_LIDS, INPUT_LIDS, moved, read_one, scan
from d2diag.kline import KLineTimeout
from d2diag.kwp2000 import NegativeResponse

PLACEHOLDER = bytes.fromhex("11 99 07 01 01 01 01 0a eb")


def _reader(table):
    """Fake Bcu.read_local: table[lid] = bytes | NRC int | None (silent) | callable(count)."""
    calls = {}

    def read(lid):
        calls[lid] = calls.get(lid, 0) + 1
        v = table.get(lid)
        if callable(v):
            v = v(calls[lid])
        if v is None:
            raise KLineTimeout("silent")
        if isinstance(v, int):
            raise NegativeResponse(0x21, v)
        return v
    read.calls = calls
    return read


def test_inputs_never_include_eka():
    assert 0xCC not in INPUT_LIDS and 0xCC in FORBIDDEN_LIDS


def test_forbidden_lid_is_refused_before_any_read():
    read = _reader({})
    with pytest.raises(ValueError):
        scan(read, [0xD8, 0xCC])
    assert read.calls == {}
    with pytest.raises(ValueError):
        read_one(read, 0xCC)


def test_classifies_data_denied_nrc_silent():
    read = _reader({0xD8: b"\x01\x02", 0xD9: 0x33, 0xDA: 0x31, 0xDB: None})
    res = scan(read, [0xD8, 0xD9, 0xDA, 0xDB], rng=random.Random(1))
    assert res[0xD8] == ("DATA", "01 02")
    assert res[0xD9] == ("DENIED", "7f 21 33")
    assert res[0xDA] == ("NRC 31", "")
    assert res[0xDB] == ("NO-RESPONSE", "")
    assert all(n == 2 for n in read.calls.values())  # two passes each


def test_disagreeing_passes_are_inconsistent_not_a_verdict():
    read = _reader({0xD8: lambda n: b"\x01" if n == 1 else None})
    assert scan(read, [0xD8])[0xD8][0] == "INCONSISTENT"


def test_shared_fixed_payload_is_flagged_placeholder():
    table = {lid: PLACEHOLDER for lid in (0xD8, 0xD9, 0xDA, 0xDB)}
    table[0xDC] = b"\x40"
    res = scan(_reader(table), list(table))
    assert {res[l][0] for l in (0xD8, 0xD9, 0xDA, 0xDB)} == {"PLACEHOLDER"}
    assert res[0xDC] == ("DATA", "40")


def test_moved_reports_only_changed_data():
    before = {0xD8: ("DATA", "00"), 0xD9: ("DATA", "01"), 0xDA: ("DENIED", "7f 21 33")}
    after = {0xD8: ("DATA", "04"), 0xD9: ("DATA", "01"), 0xDA: ("DENIED", "7f 21 33")}
    assert moved(before, after) == {0xD8: ("00", "04")}
