"""The read-only address scanner: detects responders and sends only init + 82."""
from d2diag.kline import KLine
from d2diag.kline.frame import encode
from d2diag.kwp2000 import KWP2000
from d2diag.modscan import AddressScanner, render_table

from .fakes import FakeKLineEcu

# Forbidden service IDs: a read-only scan must never emit any of these.
_FORBIDDEN = {0x21, 0x27, 0x2E, 0x30, 0x31, 0x3B, 0x14}


def _scanner(responses):
    fake = FakeKLineEcu(responses)
    kwp = KWP2000(KLine(fake), tolerant=True)
    kwp.open()
    return AddressScanner(kwp, sleep=lambda _s: None, settle=0.0), fake


def test_fast_init_detects_a_responder_and_releases():
    start13 = bytes(encode(b"\x81", 0x13, 0xF7, addressed=True))
    scanner, fake = _scanner({start13: b"\xc1\x57\x8f"})

    rows = scanner.scan(fast=[0x13, 0x29], slow=[])
    by_addr = {r["address"]: r for r in rows}

    assert by_addr["0x13"]["status"] == "responded"
    assert by_addr["0x13"]["module"] == "td5"
    assert "c1" in by_addr["0x13"]["keybytes"]
    # 0x29 has no response wired → silent, and named from the table.
    assert by_addr["0x29"]["status"] == "silent" and by_addr["0x29"]["module"] == "slabs"


def test_slow_init_reports_keybytes_and_unknown_name():
    scanner, _ = _scanner({})  # the fake answers any slow init with 55 e9 8f
    rows = scanner.scan(fast=[], slow=[0x18, 0x40])
    by_addr = {r["address"]: r for r in rows}

    assert by_addr["0x40"]["status"] == "responded" and by_addr["0x40"]["keybytes"] == "e9 8f"
    assert by_addr["0x40"]["module"] == "bcu"
    # 0x18 has no name in the table → tagged unknown, never dropped.
    assert by_addr["0x18"]["module"] == "unknown:0x18"


def test_scan_sends_only_init_and_stopcommunication():
    start13 = bytes(encode(b"\x81", 0x13, 0xF7, addressed=True))
    scanner, fake = _scanner({start13: b"\xc1\x57\x8f"})
    scanner.scan(fast=[0x13, 0x29], slow=[0x40])

    for frame in fake.sent:
        payload = frame[1:-1] if len(frame) >= 3 else frame
        assert not (set(payload) & _FORBIDDEN), f"read-only scan sent {frame.hex(' ')}"


def test_render_table_has_a_row_per_probe():
    scanner, _ = _scanner({})
    table = render_table(scanner.scan(fast=[], slow=[0x40, 0x18]))
    assert "0x40" in table and "0x18" in table and "bcu" in table
