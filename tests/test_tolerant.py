"""Tests for the tolerant mode: burst reading that handles noise where strict fails.

Proves against RECORDED bytes (real car 2026-08-03) and a simulated turnaround
glitch that the library gets all the way to unlocked live data.
"""
import pytest

from d2diag.kline import (
    TD5_ECU_ADDRESS,
    TESTER_ADDRESS,
    KLine,
    KLineTimeout,
    encode,
)
from d2diag.kwp2000 import KWP2000
from d2diag.td5 import Td5
from d2diag.td5.keygen import key_bytes_from_seed
from tests.fakes import FakeKLineEcu

NOSLEEP = lambda *_: None  # noqa: E731 — injected into establish() so the tests are fast


def _sess(data: bytes) -> bytes:
    """Unaddressed session frame (so the ECU responses look like on the car)."""
    return encode(data, addressed=False)


def _init_req() -> bytes:
    return encode(b"\x81", addressed=True)  # 81 13 F7 81 0C


# --------------------------------------------------------------------------- #
# KLine: converse + tolerant fast init
# --------------------------------------------------------------------------- #
def test_converse_returns_echo_plus_response():
    req = _sess(b"\x3e\x01")
    resp = _sess(b"\x7e\x01")
    ecu = FakeKLineEcu({req: resp})
    with KLine(ecu) as k:
        burst = k.converse(b"\x3e\x01")
    assert burst == req + resp  # the whole burst raw: echo followed by response


def test_fast_init_tolerant_finds_c1_in_shredded_frame():
    # C1 is present but the frame is shredded by a turnaround glitch (as on the car).
    ecu = FakeKLineEcu({_init_req(): b"\x03\xc1\x38\x0e\xf8\x00"})
    with KLine(ecu) as k:
        out = k.fast_init_tolerant()
    assert out[0] == 0xC1


def test_strict_fast_init_fails_where_tolerant_succeeds():
    ecu = FakeKLineEcu({_init_req(): b"\x03\xc1\x38\x0e\xf8\x00"})
    with KLine(ecu) as k:
        with pytest.raises(KLineTimeout):
            k.fast_init()  # strict requires a valid frame → fails


# --------------------------------------------------------------------------- #
# KWP2000: tolerant request picks the response despite a bad checksum
# --------------------------------------------------------------------------- #
def test_tolerant_request_survives_bad_checksum():
    req = _sess(b"\x21\x09")
    good = _sess(b"\x61\x09\x00\x00")
    ecu = FakeKLineEcu({req: good}, corrupt=True)  # the checksum is flipped
    with KWP2000(KLine(ecu), tolerant=True) as kwp:
        data = kwp.read_local_identifier(0x09)
    assert data.startswith(b"\x00\x00")  # 61 09 found despite a bad cs


def test_strict_request_fails_on_bad_checksum():
    req = _sess(b"\x21\x09")
    good = _sess(b"\x61\x09\x00\x00")
    ecu = FakeKLineEcu({req: good}, corrupt=True)
    with KWP2000(KLine(ecu)) as kwp:  # strict
        with pytest.raises(Exception):
            kwp.read_local_identifier(0x09)


def test_tolerant_negative_response_still_raises():
    from d2diag.kwp2000 import NegativeResponse

    req = _sess(b"\x10\xa0")
    neg = _sess(b"\x7f\x10\x10")  # generalReject
    ecu = FakeKLineEcu({req: neg})
    with KWP2000(KLine(ecu), tolerant=True) as kwp:
        with pytest.raises(NegativeResponse):
            kwp.start_diagnostic_session(0xA0)


# --------------------------------------------------------------------------- #
# Td5: full establish() incl. keygen, against the sniff's exact bytes
# --------------------------------------------------------------------------- #
def _sniff_ecu(corrupt: bool = False) -> FakeKLineEcu:
    seed_hi, seed_lo = 0x10, 0xE6                 # seed from the Ekaitza sniff
    key = key_bytes_from_seed(seed_hi, seed_lo)   # our keygen → 90 86
    responses = {
        _init_req(): _sess(b"\xc1\x57\x8f"),                              # 03 c1 57 8f aa
        _sess(b"\x10\xa0"): _sess(b"\x50"),                              # 01 50 51
        _sess(b"\x27\x01"): _sess(b"\x67\x01" + bytes([seed_hi, seed_lo])),  # 04 67 01 10 e6 62
        _sess(b"\x27\x02" + key): _sess(b"\x67\x02"),                    # 02 67 02 6b
    }
    return FakeKLineEcu(responses, corrupt=corrupt)


def test_establish_full_flow_including_keygen():
    td5 = Td5(KWP2000(KLine(_sniff_ecu()), tolerant=True))
    with td5:
        c1 = td5.establish(idle=0, attempts=2, sleep=NOSLEEP)
    # The key was accepted only if our keygen matched the sniff's seed→key.
    assert c1[:3] == b"\xc1\x57\x8f"


def test_read_real_recorded_lid_1a_decodes_temps():
    # Real 21 1A response frame from the car (RDL 016, 2026-08-03, engine off):
    #   12 61 1a | 0c fc 04 f1 0c b1 05 eb 10 88 00 04 0c 95 06 51 | cb
    # coolant = offset 0 u16 = 0x0cfc = 3324 → 332.4 − 273.2 = 59.2 °C
    resp = bytes.fromhex("12611a0cfc04f10cb105eb108800040c950651cb")
    req = _sess(b"\x21\x1a")
    ecu = FakeKLineEcu({req: resp})
    with Td5(KWP2000(KLine(ecu), tolerant=True)) as td5:
        vals = td5.read_lid(0x1A)
    assert round(vals["coolant_temp"], 1) == 59.2


# --------------------------------------------------------------------------- #
# Tolerant reply is cut to its header length — the checksum no longer leaks
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("burst, service, payload, data", [
    # Td5, unaddressed `fmt` header (car 2026-10-03): echo 02 21 09 2c, reply 04 61 09 00 00 | 6e
    ("02 21 09 2c 04 61 09 00 00 6e", 0x21, b"\x09", "61 09 00 00"),
    # SLABS: glitch 00 between echo and reply, still trimmed (car 2026-10-03)
    ("02 21 54 77 00 06 61 54 92 88 0f 0f f3", 0x21, b"\x54", "61 54 92 88 0f 0f"),
    # Airbag, addressed `fmt tgt src` header (car 2026-10-04): checksum 65 must go
    ("82 5b f7 21 02 f7 8c f7 5b 61 02 90 04 90 00 00 00 00 00 00 00 65",
     0x21, b"\x02", "61 02 90 04 90 00 00 00 00 00 00 00"),
    # `fmt len` header (length byte, 48-byte style replies use it): 00 03 61 1e 00 | cs
    ("02 21 1e 41 00 03 61 1e 82 04", 0x21, b"\x1e", "61 1e 82"),
    # Negative response is trimmed too
    ("02 10 a0 b2 03 7f 10 10 a2", 0x10, b"\xa0", "7f 10 10"),
])
def test_tolerant_reply_trimmed_to_header_length(burst, service, payload, data):
    out = KWP2000._extract_response(bytes.fromhex(burst), service, payload)
    assert out == bytes.fromhex(data)


def test_tolerant_reply_trimmed_by_length_when_checksum_is_bad():
    # A flipped checksum still trims by the header length (glitch byte f8 after it too).
    out = KWP2000._extract_response(bytes.fromhex("02 21 09 2c 04 61 09 00 00 99 f8"),
                                    0x21, b"\x09")
    assert out == bytes.fromhex("61 09 00 00")


def test_tolerant_reply_without_plausible_header_is_untrimmed():
    # No header before the SID (shredded): fall back to everything after it.
    out = KWP2000._extract_response(bytes.fromhex("61 09 00 00 6e"), 0x21, b"\x09")
    assert out == bytes.fromhex("61 09 00 00 6e")


def test_tolerant_read_lid_has_no_checksum_byte():
    req = _sess(b"\x21\x1e")
    ecu = FakeKLineEcu({req: _sess(b"\x61\x1e\x00\x82")})
    with KWP2000(KLine(ecu), tolerant=True) as kwp:
        assert kwp.read_local_identifier(0x1E) == b"\x00\x82"
