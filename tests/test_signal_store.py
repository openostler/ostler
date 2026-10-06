# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for the declarative signal store (openostler.signals).

Store mechanics run against FAKE_PACK; the checks on the Discovery 2 stores are
``needs_pack`` integration tests (the D2 parity tests live in the pack repo).
"""

import pytest

import json

from openostler import signals as store
from openostler.signals import Signal, load_signals, upsert_field

pytestmark = pytest.mark.fake_pack

def test_u16le_and_s16le_decode():
    d = bytes.fromhex("00 80".replace(" ", ""))
    assert Signal("x", 1, 0, "u16le").decode(d) == 0x8000
    assert Signal("x", 1, 0, "s16le").decode(d) == 0x8000 - 0x10000  # LE: 0x8000 → -32768


def test_bit_decode_numeric_and_named():
    s = Signal("any_door", 0x56, 0, "bit", bit=0, states={0: "closed", 1: "open"})
    assert s.decode(b"\x01") == 1.0
    assert s.decode(b"\x00") == 0.0
    assert s.decode_named(b"\x01") == "open"
    assert s.decode_named(b"\x00") == "closed"


# ---- write-back round-trip (isolerad temp-dir) -------------------------- #
def test_upsert_field_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_DIR", tmp_path)
    store._CACHE.clear()
    (tmp_path / "demo.json").write_text("[]", encoding="utf-8")

    upsert_field("demo", {"name": "boost", "lid": "1C", "offset": 0, "kind": "u16",
                          "scale": 0.0001, "unit": "bar"})
    sigs = load_signals("demo")
    assert len(sigs) == 1
    assert sigs[0].name == "boost" and sigs[0].lid == 0x1C
    assert sigs[0].confidence == "candidate"  # default when not specified

    # same (lid, offset, name) → replaced, not duplicated
    upsert_field("demo", {"name": "boost", "lid": "1C", "offset": 0, "kind": "u16",
                          "scale": 0.0001, "unit": "bar", "confidence": "proven"})
    sigs = load_signals("demo")
    assert len(sigs) == 1 and sigs[0].confidence == "proven"

    # new field → append
    upsert_field("demo", {"name": "other", "lid": "0D", "offset": 0, "kind": "u8"})
    assert len(load_signals("demo")) == 2
    # LID is normalised to 2-hex uppercase on disk
    rows = json.loads((tmp_path / "demo.json").read_text(encoding="utf-8"))
    assert {r["lid"] for r in rows} == {"1C", "0D"}


def test_remove_field_supports_reassign_and_clear(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_DIR", tmp_path)
    store._CACHE.clear()
    (tmp_path / "demo.json").write_text("[]", encoding="utf-8")

    upsert_field("demo", {"name": "door", "lid": "56", "offset": 0, "kind": "bit", "bit": 0})
    upsert_field("demo", {"name": "bonnet", "lid": "56", "offset": 0, "kind": "bit", "bit": 1})

    # remove ONLY bit 0 (same lid+offset, different bit is untouched)
    assert store.remove_field("demo", "56", 0, bit=0) == 1
    rows = store.load_records("demo")
    assert len(rows) == 1 and rows[0]["name"] == "bonnet"

    # rename = remove-by-bit then upsert → no orphaned old record
    store.remove_field("demo", "56", 0, bit=1)
    upsert_field("demo", {"name": "engine cover", "lid": "56", "offset": 0, "kind": "bit", "bit": 1})
    rows = store.load_records("demo")
    assert len(rows) == 1 and rows[0]["name"] == "engine cover"

    # removing a bit that isn't assigned is a no-op
    assert store.remove_field("demo", "56", 0, bit=7) == 0


@pytest.mark.needs_pack
def test_slabs_store_has_belagt_heights_and_door():
    by = {s.name: s for s in load_signals("slabs")}
    assert by["height_left"].confidence == "proven"
    assert by["height_right"].confidence == "proven"
    assert by["any_door"].kind == "bit" and by["any_door"].states == {0: "closed", 1: "open"}


def test_legacy_swedish_confidence_is_normalised(tmp_path, monkeypatch):
    import openostler.signals as store
    from openostler.signals import normalize_confidence

    assert normalize_confidence("belagt") == "proven"
    assert normalize_confidence("kandidat") == "candidate"
    assert normalize_confidence(None) == "candidate"
    assert normalize_confidence("proven") == "proven"

    monkeypatch.setattr(store, "_DIR", tmp_path)
    store._CACHE.clear()
    (tmp_path / "old.json").write_text(
        '[{"name": "x", "lid": "09", "offset": 0, "confidence": "belagt"}]', encoding="utf-8")
    assert store.load_signals("old")[0].confidence == "proven"
    store.upsert_field("old", {"name": "y", "lid": "09", "offset": 2, "confidence": "kandidat"})
    assert store.load_records("old")[1]["confidence"] == "candidate"
    store._CACHE.clear()


# --------------------------------------------------------------------------- #
# Reply-length layouts (specs/2026-10-04-reply-length-layouts-design.md)
# --------------------------------------------------------------------------- #
@pytest.mark.needs_pack
def test_length_restricts_fits():
    sig = Signal("x", 0x1B, 4, length=10)
    assert sig.fits(bytes(10)) and not sig.fits(bytes(8)) and not sig.fits(bytes(12))
    assert Signal("y", 0x1B, 4).fits(bytes(8))  # no length → any long-enough reply


@pytest.mark.needs_pack
def test_length_variants_agree_on_unit_limits_and_labels():
    by: "dict[str, list[Signal]]" = {}
    for s in load_signals("td5"):
        by.setdefault(s.name, []).append(s)
    for name, sigs in by.items():
        if len(sigs) == 1:
            continue
        assert all(s.length is not None for s in sigs), f"{name}: duplicate without length"
        assert len({s.length for s in sigs}) == len(sigs), f"{name}: two records, same length"
        keys = {(s.unit, s.limits, s.label, s.group, s.kind, s.scale, s.bias) for s in sigs}
        assert len(keys) == 1, f"{name}: variants disagree {keys}"


@pytest.mark.needs_pack
def test_fields_list_each_name_once():
    from openostler.web.server import _fields_list
    names = [f["name"] for f in _fields_list("motor")["fields"]]
    assert len(names) == len(set(names))
    assert "accel_supply" in names


