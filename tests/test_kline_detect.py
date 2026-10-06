# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""K-line auto-detection (ADR-0022, spec K-line profiles §2, §5, §7): init paths and
order, key-byte classification, the inverted address, and the muki01 regressions."""
import pytest

from openostler.kline import (
    KLine,
    KLineTimeout,
    SlowInitUnconfirmed,
    parse_slow_init_reply,
)
from openostler.kline.detect import detect
from openostler.kline.keywords import classify, odd_parity_ok
from openostler.kline.profiles import BUILTIN, resolve
from tests.fakes import (
    FakeClock,
    FakeIso9141Ecu,
    FakeKLineEcu,
    FakeKwpSlowEcu,
    kwp_fast_reply,
    slow_reply,
)

# Init frames of manufacturer protocols detect() must never send: KW1281 (VAG, 5-baud
# address 0x01 and its block framing), BMW DS2 (no init, XOR frames from the tester),
# Opel KW82 and Honda. detect() only ever sends the OBD fast init and a 5-baud 0x33.
_ALLOWED_SEND = {bytes.fromhex("C133F18166")}


def _run(ecu, **kw):
    clock = FakeClock()
    ecu.open()
    return detect(ecu, clock=clock, sleep=clock.sleep, **kw), clock


# ---- init paths --------------------------------------------------------------- #
def test_fast_init_success():
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x8F), slow_init_reply=b"")
    res, _ = _run(ecu)
    assert res.ok and res.method == "fast" and res.profile.name == "kwp2000_fast"
    assert res.key_bytes == b"\xe9\x8f"
    assert ecu.sent[0] == bytes.fromhex("C133F18166")
    assert ecu.inits == ["fast"]
    assert res.link["origin"] == "detected" and res.link["key_bytes"] == "E9 8F"
    assert res.link["timing"] == "extended" and res.link["init"] == "fast"
    assert res.kline is not None and res.kline.profile is res.profile


def test_fast_silent_then_5baud_iso9141():
    ecu = FakeIso9141Ecu()
    res, _ = _run(ecu)
    assert res.ok and res.method == "5baud" and res.profile.name == "iso9141_2"
    assert res.profile.framing == "iso9141" and res.key_bytes == b"\x08\x08"
    assert ecu.inits == ["fast", "5baud"] and ecu.slow_addresses == [0x33]
    assert res.link["protocol"] == "iso9141_2" and res.link["timing"] is None


def test_5baud_kwp():
    res, _ = _run(FakeKwpSlowEcu())
    assert res.ok and res.profile.name == "kwp2000_slow"
    assert (res.profile.header, res.profile.length, res.profile.timing_set) == \
        ("functional", "format", "extended")


def test_nothing_answers_is_no_ecu():
    ecu = FakeKLineEcu(slow_init_reply=b"")
    res, _ = _run(ecu)
    assert res.outcome == "no-ecu" and not res.ok and res.profile is None
    assert ecu.inits == ["fast", "5baud"]


def test_rx_during_w5_is_bus_busy_and_nothing_is_sent():
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(), bus_chatter=b"\x02\x3e\x01\x41")
    res, clock = _run(ecu)
    assert res.outcome == "bus-busy"
    assert ecu.sent == [] and ecu.inits == [] and ecu.breaks == []
    assert clock.sleeps == [0.3]                      # held the line idle for W5 only


def test_negative_fast_reply_is_ecu_refused_without_5baud():
    refused = bytes.fromhex("037F8110") + bytes([sum(bytes.fromhex("037F8110")) & 0xFF])
    ecu = FakeKLineEcu(fast_reply=refused, slow_init_reply=slow_reply(0x08, 0x08))
    res, _ = _run(ecu)
    assert res.outcome == "ecu-refused"
    assert ecu.inits == ["fast"]                      # no 5-baud after a refusal


def test_waits_w5_before_each_init():
    ecu = FakeIso9141Ecu()
    _res, clock = _run(ecu)
    assert clock.sleeps.count(0.3) == 2               # listen W5, then W5 before 5-baud
    assert not any(s >= 5.0 for s in clock.sleeps)    # no muki01 5.5 s idle


# ---- order and the protocols never sent ---------------------------------------- #
@pytest.mark.parametrize("ecu", [FakeIso9141Ecu, FakeKwpSlowEcu,
                                 lambda: FakeKLineEcu(slow_init_reply=b"")])
def test_order_is_fast_then_5baud_and_nothing_else_is_sent(ecu):
    e = ecu()
    _run(e)
    assert e.inits == ["fast", "5baud"]
    assert set(e.sent) <= _ALLOWED_SEND               # no KW1281/DS2/KW82/Honda frame


# ---- key bytes ------------------------------------------------------------------ #
@pytest.mark.parametrize("kw", [0x08, 0x94])
def test_equal_keywords_are_iso9141(kw):
    c = classify(kw, kw, "5baud")
    assert c.profile == "iso9141_2" and c.header == "iso9141" and c.length == "none"


@pytest.mark.parametrize("kb1, header, length, timing, bits", [
    (0xE9, "functional", "format", "extended", {"AL0", "HB1", "TP1"}),           # airbag
    (0x57, "none", "format", "normal", {"AL0", "AL1", "HB0", "TP0"}),            # SLABS
    (0xEF, "functional", "format", "extended", {"AL0", "AL1", "HB0", "HB1", "TP1"}),
    (0xD0, "functional", "format", "normal", {"TP0"}),                            # KW 2000
])
def test_kwp_key_bytes_decode(kb1, header, length, timing, bits):
    c = classify(kb1, 0x8F, "fast")
    assert (c.header, c.length, c.timing_set) == (header, length, timing)
    assert {k for k, v in c.bits.items() if v} == bits
    assert c.odd is None and 2000 <= c.key_word <= 2031


def test_separate_length_byte_when_only_al1():
    kb1 = 0x40 | 0x10 | 0x02 | 0x04            # AL1, HB0, normal
    kb1 |= 0x00 if odd_parity_ok(kb1) else 0x80
    c = classify(kb1, 0x8F, "5baud")
    assert c.length == "separate" and c.header == "none"


@pytest.mark.parametrize("kb1, kb2, why", [
    (0x69, 0x8F, "parity"),        # 0xE9 without its parity bit
    (0xE9, 0x0F, "KB2"),
    (0xC1, 0x8F, "TP"),            # TP 00
    (0xF1, 0x8F, "TP"),            # TP 11
])
def test_odd_key_bytes_keep_kwp_defaults(kb1, kb2, why):
    c = classify(kb1, kb2, "fast")
    assert c.odd and why in c.odd
    assert (c.protocol, c.header, c.length, c.timing_set) == \
        ("kwp2000", "functional", "format", "normal")


def test_odd_key_bytes_are_logged_not_failed():
    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x0F))
    res, _ = _run(ecu)
    assert res.ok
    classified = [e for e in res.log if e["event"] == "classified"]
    assert classified and "odd key bytes" in classified[0]["odd"]


def test_fast_init_never_classifies_as_iso9141():
    assert classify(0x8F, 0x8F, "fast").protocol == "kwp2000"


# ---- the inverted address (spec §5) --------------------------------------------- #
@pytest.mark.parametrize("raw, confirmed, inv", [
    (bytes.fromhex("550808F7CC"), True, 0xCC),     # ~KW2 echo, then ~address
    (bytes.fromhex("550808CC"), True, 0xCC),       # a bridge that strips the echo
    (bytes.fromhex("550808F733"), False, 0x33),    # wrong: the address, not inverted
    (bytes.fromhex("550808F7"), False, None),      # echo only
    (bytes.fromhex("550808"), False, None),        # missing
])
def test_parse_slow_init_reply(raw, confirmed, inv):
    r = parse_slow_init_reply(raw, 0x33)
    assert (r.kw1, r.kw2) == (0x08, 0x08)
    assert r.confirmed is confirmed and r.inverted_address == inv


def test_parse_slow_init_reply_without_sync():
    assert parse_slow_init_reply(b"", 0x33) is None
    assert parse_slow_init_reply(b"\x00\x01", 0x33) is None


@pytest.mark.parametrize("raw", [bytes.fromhex("550808F733"), bytes.fromhex("550808F7"),
                                 bytes.fromhex("550808")])
def test_detect_bad_inverted_address_is_init_failed(raw):
    res, _ = _run(FakeKLineEcu(slow_init_reply=raw))
    assert res.outcome == "init-failed" and res.profile is None


def test_report_mode_returns_unconfirmed():
    p = resolve("kwp2000_slow", {"confirm_address": "report"})
    k = KLine.from_profile(FakeKLineEcu(slow_init_reply=bytes.fromhex("55E98F")), p,
                           init_idle=0.0)
    k.open()
    r = k.slow_init_reply()
    assert r.confirmed is False and (r.kw1, r.kw2) == (0xE9, 0x8F)


def test_require_mode_raises():
    k = KLine.from_profile(FakeKLineEcu(slow_init_reply=bytes.fromhex("55E98F")),
                           BUILTIN["kwp2000_slow"], init_idle=0.0)
    k.open()
    with pytest.raises(SlowInitUnconfirmed):
        k.slow_init_reply()
    with pytest.raises(KLineTimeout):
        KLine.from_profile(FakeKLineEcu(slow_init_reply=b""), BUILTIN["kwp2000_slow"],
                           init_idle=0.0).slow_init_reply()


def test_legacy_slow_init_still_returns_key_bytes():
    assert KLine(FakeKLineEcu()).slow_init(0x5B) == (0xE9, 0x8F)


# ---- muki01 regression fixtures (K-line only) ------------------------------------ #
def test_unaddressed_c1_reply_and_glitch_byte_are_accepted():
    unaddressed = bytes([0x03, 0xC1, 0xE9, 0x8F]) + bytes([(0x03 + 0xC1 + 0xE9 + 0x8F) & 0xFF])
    res, _ = _run(FakeKLineEcu(fast_reply=b"\xf8" + unaddressed))
    assert res.ok and res.key_bytes == b"\xe9\x8f"


def test_key_bytes_are_decoded_not_ignored():
    res, _ = _run(FakeKLineEcu(fast_reply=kwp_fast_reply(0x57, 0x8F)))
    assert (res.profile.header, res.profile.timing_set) == ("none", "normal")


def test_any_inverted_address_is_not_accepted():
    for wrong in (0x00, 0x33, 0xCD, 0xFF):
        raw = bytes([0x55, 0x08, 0x08, 0xF7, wrong])
        assert _run(FakeKLineEcu(slow_init_reply=raw))[0].outcome == "init-failed"


def test_after_detection_requests_carry_the_detected_header():
    """The vendored copy's "Automatic" mode sent headerless frames: after detection every
    request must use the detected framing (here: functional addressed KWP frames)."""
    from openostler.kwp2000 import KWP2000

    ecu = FakeKLineEcu(fast_reply=kwp_fast_reply(0xE9, 0x8F))
    res, _ = _run(ecu)
    kwp = KWP2000.from_profile(res.kline, res.profile)
    with pytest.raises(Exception):
        kwp.request(0x3E, b"\x01", overall=0.05)
    assert ecu.sent[-1][:3] == bytes([0xC2, 0x33, 0xF1])      # C2 33 F1 3E 01 cs
