# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The K-line ObdRequestLink adapter on FakeKLineEcu (J1979 spec §2; fixtures F2, F4,
F11 on K-line) and the identity scrub patterns (spec §4.7, F12)."""
from __future__ import annotations

import pytest

from openostler.kline import BUILTIN, KLine
from openostler.kline.obd_link import KLineObdLink, split_kwp
from openostler.obd import J1979, Pacer
from openostler.obd import vin as obdvin
from openostler.obd.link import ForbiddenService
from tests.fakes import FakeClock, FakeIso9141Ecu, FakeKLineEcu, iso9141_reply
from tests.obd_fakes import make_vin, table


def _iso_req(data: str) -> bytes:
    body = bytes.fromhex("686AF1" + data.replace(" ", ""))
    return body + bytes([sum(body) & 0xFF])


def _kwp(fmt: int, tgt: int, src: int, data: str) -> bytes:
    d = bytes.fromhex(data.replace(" ", ""))
    body = bytes([fmt | len(d), tgt, src]) + d
    return body + bytes([sum(body) & 0xFF])


def _iso_link(responses: dict):
    clock = FakeClock()
    ecu = FakeIso9141Ecu(responses)
    k = KLine.from_profile(ecu, BUILTIN["iso9141_2"], clock=clock, sleep=clock.sleep)
    k.open()
    return ecu, k, KLineObdLink(k), clock


def test_f2_kline_dtc_burst_never_reads_headers_as_codes():
    burst = (iso9141_reply(0x10, bytes.fromhex("43013301340300"))
             + iso9141_reply(0x10, bytes.fromhex("43017000000000")))
    _ecu, _k, link, clock = _iso_link({_iso_req("03"): burst})
    assert link.flavor == "iso9141"
    replies = link.request(b"\x03")
    assert list(replies) == ["10"] and len(replies["10"].messages) == 2
    j = J1979(link, table(), pacer=Pacer(clock=clock, sleep=clock.sleep), clock=clock)
    codes = j.read_dtcs("stored").codes()
    assert codes == ["P0133", "P0134", "P0300", "P0170"]
    assert not any(c.endswith("486B") or c.startswith("U086") for c in codes)


def test_f4_merged_kline_burst_from_two_ecus():
    burst = iso9141_reply(0x10, b"\x41\x0D\x32") + iso9141_reply(0x18, b"\x41\x0D\x31")
    _ecu, _k, link, clock = _iso_link({_iso_req("01 0D"): burst})
    j = J1979(link, table(), pacer=Pacer(clock=clock, sleep=clock.sleep), clock=clock)
    r = j.read_pids([0x0D])
    assert {(v.ecu, v.value) for v in r.values} == {("10", 50.0), ("18", 49.0)}


def test_response_pending_is_waited_out_not_returned():
    burst = iso9141_reply(0x10, b"\x7F\x01\x78") + iso9141_reply(0x10, b"\x41\x05\x5A")
    _ecu, _k, link, _clock = _iso_link({_iso_req("01 05"): burst})
    assert link.request(b"\x01\x05")["10"].messages == (b"\x41\x05\x5A",)


def test_f11_kline_vin_via_adapter_and_burst_cleared():
    vin = make_vin()
    padded = b"\0\0\0" + vin.encode()
    vin_burst = b"".join(iso9141_reply(0x10, bytes([0x49, 0x02, i + 1]) + padded[4 * i:4 * i + 4])
                         for i in range(5))
    _ecu, k, link, clock = _iso_link({_iso_req("09 01"): iso9141_reply(0x10, b"\x49\x01\x01\x05"),
                                      _iso_req("09 02"): vin_burst})
    j = J1979(link, table(), pacer=Pacer(clock=clock, sleep=clock.sleep), clock=clock)
    got: "list[str]" = []
    ident = j.read_identity(got.append)
    assert got == [vin] and ident.vin_delivered
    assert k.last_burst == b""                             # no VIN bytes left in memory


def test_kwp_functional_request_and_burst_split():
    req = _kwp(0xC0, 0x33, 0xF1, "01 0D")
    reply = _kwp(0x80, 0xF1, 0x10, "41 0D 32") + _kwp(0x80, 0xF1, 0x18, "41 0D 31")
    clock = FakeClock()
    ecu = FakeKLineEcu({req: reply})
    k = KLine.from_profile(ecu, BUILTIN["kwp2000_fast"], clock=clock, sleep=clock.sleep)
    k.open()
    link = KLineObdLink(k)
    assert link.flavor == "kwp"
    out = link.request(b"\x01\x0D")
    assert {e: r.messages for e, r in out.items()} == {"10": (b"\x41\x0D\x32",),
                                                       "18": (b"\x41\x0D\x31",)}
    assert ecu.sent[-1] == req
    # our own echo and noise are skipped
    assert split_kwp(b"\x00" + req + reply + b"\xFF", sent=req) == [
        (0x10, b"\x41\x0D\x32"), (0x18, b"\x41\x0D\x31")]


def test_kwp_physical_request_targets_one_ecu():
    req = _kwp(0x80, 0x10, 0xF1, "01 0D")
    clock = FakeClock()
    ecu = FakeKLineEcu({req: _kwp(0x80, 0xF1, 0x10, "41 0D 32")})
    k = KLine.from_profile(ecu, BUILTIN["kwp2000_fast"], clock=clock, sleep=clock.sleep)
    k.open()
    assert KLineObdLink(k).request(b"\x01\x0D", target="10")["10"].messages == (b"\x41\x0D\x32",)


def test_adapter_refuses_mode_08_and_needs_a_k_line_flavor():
    _ecu, _k, link, _clock = _iso_link({})
    with pytest.raises(ForbiddenService):
        link.request(b"\x08\x00")
    with pytest.raises(ValueError):
        KLineObdLink(KLine(FakeKLineEcu()))
    with pytest.raises(ValueError):
        KLineObdLink(KLine(FakeKLineEcu()), flavor="can11")


def test_iso9141_keepalive_is_owned_by_the_adapter():
    ecu, k, link, clock = _iso_link({})
    k.last_tx = clock.now()
    assert link.keepalive_if_due() is False
    clock.advance(2.5)
    assert link.keepalive_if_due() is True
    assert ecu.sent[-1] == bytes.fromhex("686AF10100C4")


# ------------------------------------------------------------- scrub (F12) -- #

def test_f12_scrub_kline_iso9141_and_kwp():
    vin = make_vin()
    padded = b"\0\0\0" + vin.encode()
    frames = [iso9141_reply(0x10, bytes([0x49, 0x02, i + 1]) + padded[4 * i:4 * i + 4])
              for i in range(5)]
    other = iso9141_reply(0x10, b"\x41\x0D\x32")
    raw = _iso_req("09 02") + b"".join(frames) + other
    out = obdvin.scrub_kline_hex(raw)
    assert out.count("<redacted 11 bytes>") == 5
    assert out.startswith("68 6A F1 09 02") and out.endswith(other.hex(" ").upper())
    for i in range(0, 17, 4):
        assert vin[i:i + 4].encode().hex(" ").upper() not in out
    kwp = _kwp(0x80, 0xF1, 0x10, "49 02 01" + vin.encode().hex())
    assert obdvin.scrub_kline_hex(kwp) == f"<redacted {len(kwp)} bytes>"
    assert obdvin.scrub_message(b"\x62\xF1\x90" + vin.encode()) == "<redacted 20 bytes>"
    assert obdvin.scrub_message(b"\x41\x0D\x32") == "41 0D 32"


def test_f12_can_isotp_scrub_is_stateful():
    vin = make_vin().encode()
    msg = b"\x49\x02\x01" + vin                     # 20 bytes → FF + 2 CFs
    ff = bytes([0x10, len(msg)]) + msg[:6]
    cf1 = b"\x21" + msg[6:13]
    cf2 = b"\x22" + msg[13:20]
    s = obdvin.CanIdentityScrubber()
    assert s.scrub(0x7E8, ff) is None and s.scrub(0x7E8, cf1) is None
    assert s.scrub(0x7E8, b"\x30\x00\x00") == b"\x30\x00\x00"   # FC from us passes
    assert s.scrub(0x7E8, cf2) is None
    nxt = b"\x03\x41\x0D\x32\x00\x00\x00\x00"
    assert s.scrub(0x7E8, nxt) == nxt                            # state ended
    assert s.scrub(0x7E9, b"\x10\x14\x49\x04\x01OSTL") is None   # CALID (ADR-0036)
