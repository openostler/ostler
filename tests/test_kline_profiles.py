# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""K-line profiles as data (spec 2026-10-06 K-line profiles §1, §5): the schema, the
built-ins, validation, pack overrides, the 8N1 5-baud address and the JSON Schema."""
import json
from pathlib import Path

import pytest

from openostler.kline import KLine
from openostler.kline.profiles import (
    BUILTIN,
    KLineProfile,
    Timing,
    checksum,
    checksum_sum8,
    checksum_twos_complement,
    checksum_xor,
    resolve,
)
from openostler.kwp2000 import KWP2000
from openostler.pack import ModuleSpec
from openostler.transport.serial_transport import SerialTransport
from tests.fakes import FakeKLineEcu

SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "kline-profile.schema.json"

# The Discovery 2 overrides of the spec §1, as the pack declares them since migration
# step 2 (d2diag/kline_profiles.py): tester F7 everywhere, no link-level pre-init idle (the
# pack's establish keeps its own settle and retry sleeps), no abandoned idle, no P3 guard.
D2_TD5 = {"init_functional": False, "source": 0xF7, "header": "none", "length": "format",
          "pre_init_idle": 0.0, "abandoned_idle": 0.0, "keepalive": b"\x3E\x01",
          "timing": {"p3_min": 0.0}}
D2_SLABS = {"init_functional": True, "source": 0xF7, "header": "none", "length": "format",
            "pre_init_idle": 0.0, "abandoned_idle": 0.0, "keepalive": b"\x3E",
            "keepalive_interval": 1.0, "timing": {"p3_min": 0.0}}
D2_AIRBAG = {"source": 0xF7, "header": "physical", "length": "format",
             "confirm_address": "report", "pre_init_idle": 0.0, "abandoned_idle": 0.0,
             "timing": {"p3_min": 0.0}}


# ---- built-ins ------------------------------------------------------------- #
def test_three_generic_builtins_only():
    assert set(BUILTIN) == {"iso9141_2", "kwp2000_slow", "kwp2000_fast"}
    iso, slow, fast = BUILTIN["iso9141_2"], BUILTIN["kwp2000_slow"], BUILTIN["kwp2000_fast"]
    assert (iso.framing, iso.init, iso.init_address) == ("iso9141", "5baud", 0x33)
    assert iso.iso9141_header == b"\x68\x6A\xF1" and iso.length == "none"
    assert iso.keepalive == b"\x01\x00" and iso.release is None
    assert (slow.framing, slow.init, slow.header) == ("kwp2000", "5baud", "auto")
    assert (fast.init, fast.init_functional, fast.header) == ("fast", True, "auto")
    for p in (slow, fast):
        assert p.keepalive == b"\x3E\x01" and p.release == b"\x82"
    for p in BUILTIN.values():
        assert p.baud == 10400 and p.parity == "N" and p.init_address_parity == "none"
        assert p.checksum == "sum8" and p.tolerant is True
        assert p.keepalive_interval < p.timing.p3_max / 2


def test_timing_defaults_are_the_iso_14230_normal_set():
    t = Timing()
    assert (t.p1_max, t.p2_min, t.p2_max, t.p3_min, t.p3_max) == (0.020, 0.025, 0.050, 0.055, 5.0)
    assert (t.w1_max, t.w2_max, t.w3_max, t.w4, t.w5) == (0.300, 0.020, 0.020, 0.030, 0.300)
    p = BUILTIN["kwp2000_fast"]
    assert p.idle_before_init == 0.300 and p.idle_after_abandoned == 5.0


def test_checksums():
    data = bytes.fromhex("686AF10100")
    assert checksum_sum8(data) == 0xC4
    assert checksum_xor(b"\x01\x02\x04") == 0x07
    assert checksum_twos_complement(b"\x01\x02") == 0xFD
    assert (sum(b"\x01\x02") + 0xFD) & 0xFF == 0
    assert checksum(BUILTIN["iso9141_2"], data) == 0xC4
    assert checksum(resolve("kwp2000_fast", {"checksum": "xor"}), b"\x01\x02") == 0x03


# ---- validation -------------------------------------------------------------- #
def test_resolve_applies_overrides_and_nested_timing():
    p = resolve("kwp2000_fast", {"source": 0xF7, "timing": {"p3_min": 0.0}})
    assert p.source == 0xF7 and p.timing.p3_min == 0.0
    assert p.timing.p3_max == 5.0                          # untouched timing kept
    assert BUILTIN["kwp2000_fast"].timing.p3_min == 0.055  # the built-in is unchanged


def test_resolve_accepts_hex_strings_for_bytes():
    p = resolve("kwp2000_fast", {"keepalive": "3E", "release": "82"})
    assert p.keepalive == b"\x3E" and p.release == b"\x82"


def test_resolve_can_name_another_base():
    p = resolve("kwp2000_fast", {"base": "iso9141_2"})
    assert p.framing == "iso9141" and p.init == "5baud"


@pytest.mark.parametrize("overrides, msg", [
    ({"nope": 1}, "unknown key"),
    ({"timing": {"p9": 1.0}}, "unknown key"),
    ({"target": "0x13"}, "byte"),
    ({"target": 300}, "byte"),
    ({"init_functional": 1}, "bool"),
    ({"keepalive_interval": "2"}, "seconds"),
    ({"header": "weird"}, "not one of"),
    ({"keepalive_interval": 2.5}, "p3_max / 2"),
    ({"timing": {"p3_max": 3.0}}, "p3_max / 2"),
    ({"init_address_parity": "odd"}, "evidence"),
    ({"base": "kw1281"}, "unknown profile"),
])
def test_resolve_rejects_bad_overrides(overrides, msg):
    with pytest.raises(ValueError, match=msg):
        resolve("kwp2000_fast", overrides)


def test_iso9141_framing_rules():
    with pytest.raises(ValueError, match="release"):
        resolve("iso9141_2", {"release": b"\x82"})
    with pytest.raises(ValueError, match="header"):
        resolve("iso9141_2", {"header": "functional"})
    with pytest.raises(ValueError, match="iso9141 framing"):
        resolve("kwp2000_fast", {"header": "iso9141"})


def test_parity_with_evidence_is_allowed():
    p = resolve("kwp2000_slow", {"init_address_parity": "odd",
                                 "evidence": "car run 2027-01-01, 7O1 address answered"})
    assert p.init_address_parity == "odd"


def test_profile_is_frozen():
    with pytest.raises(Exception):
        BUILTIN["kwp2000_fast"].target = 0x10  # type: ignore[misc]


# ---- pack overrides (ModuleSpec.kline) -------------------------------------- #
def test_modulespec_kline_defaults_to_empty_and_keeps_old_behaviour():
    m = ModuleSpec("engine", "Engine", address=0x10, init="fast")
    assert dict(m.kline) == {}
    p = m.kline_profile()
    assert p.name == "engine" and p.init_address == 0x10 and p.target == 0x10
    assert p.init == "fast" and p.framing == "kwp2000"
    assert ModuleSpec("x", "X", address=0x40, init="slow").kline_profile().init == "5baud"
    assert ModuleSpec("x", "X", init="none").kline_profile() is None
    hash(m)  # still hashable (frozen dataclass)


def test_modulespec_base_override():
    m = ModuleSpec("obd", "OBD", address=0x33, init="slow", kline={"base": "iso9141_2"})
    assert m.kline_profile().framing == "iso9141"


@pytest.mark.parametrize("mid, address, init, overrides", [
    ("td5", 0x13, "fast", D2_TD5), ("slabs", 0x29, "fast", D2_SLABS),
    ("airbag", 0x5B, "slow", D2_AIRBAG)])
def test_d2_overrides_resolve(mid, address, init, overrides):
    p = ModuleSpec(mid, mid, address=address, init=init, kline=overrides).kline_profile()
    assert p.name == mid and p.init_address == address and p.timing.p3_min == 0.0


def test_d2_td5_profile_builds_the_same_init_frame():
    p = ModuleSpec("td5", "td5", address=0x13, init="fast", kline=D2_TD5).kline_profile()
    ecu = FakeKLineEcu()
    k = KLine.from_profile(ecu, p, init_idle=0.0)
    k.open()
    with pytest.raises(Exception):
        k.fast_init_tolerant(functional=p.init_functional)
    assert ecu.sent[0] == bytes.fromhex("8113F7810C")     # 81 13 F7 81 0C, as today
    kwp = KWP2000.from_profile(k, p)
    assert kwp._addressed is False and kwp._tolerant is True


def test_d2_airbag_profile_is_addressed_and_reports_the_address():
    p = ModuleSpec("airbag", "a", address=0x5B, init="slow", kline=D2_AIRBAG).kline_profile()
    assert p.confirm_address == "report" and p.addressed
    assert KWP2000.from_profile(KLine(FakeKLineEcu()), p)._addressed is True


# ---- the 5-baud address is 8N1 (spec §5) ------------------------------------ #
def test_5baud_bits_are_8n1_and_unchanged():
    assert SerialTransport.slow_init_bits(0x29) == [0, 1, 0, 0, 1, 0, 1, 0, 0, 1]   # not 0xA9
    assert SerialTransport.slow_init_bits(0x33) == [0, 1, 1, 0, 0, 1, 1, 0, 0, 1]
    assert SerialTransport.slow_init_bits(0x29, "none") == SerialTransport.slow_init_bits(0x29)


def test_5baud_parity_variants_exist_for_evidence_profiles():
    odd = SerialTransport.slow_init_bits(0x29, "odd")
    assert odd[1:8] == [1, 0, 0, 1, 0, 1, 0] and odd[8] == 0 and len(odd) == 10  # 3 ones → 0
    even = SerialTransport.slow_init_bits(0x29, "even")
    assert even[8] == 1
    with pytest.raises(ValueError):
        SerialTransport.slow_init_bits(0x29, "mark")


# ---- JSON Schema --------------------------------------------------------------- #
def _hexify(d: dict) -> dict:
    return {k: (v.hex(" ").upper() if isinstance(v, bytes) else v) for k, v in d.items()}


def test_profile_schema_accepts_the_d2_overrides():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    v = jsonschema.Draft202012Validator(schema)
    for o in (D2_TD5, D2_SLABS, D2_AIRBAG, {"base": "iso9141_2"}):
        assert list(v.iter_errors(_hexify(o))) == []
    assert list(v.iter_errors({"nope": 1}))
    assert list(v.iter_errors({"init_address_parity": "odd"}))   # parity needs evidence
    assert not list(v.iter_errors({"init_address_parity": "odd", "evidence": "car run"}))


def test_profile_to_dict_round_trips_through_resolve():
    p = BUILTIN["iso9141_2"]
    d = p.to_dict()
    assert d["iso9141_header"] == "68 6A F1" and d["timing"]["p3_max"] == 5.0
    assert isinstance(p, KLineProfile)
