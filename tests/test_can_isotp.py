# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ISO-TP (CanLink spec §6; tests T9–T12, T14) on the fake bus, and the pure state
machine. No hardware."""
from __future__ import annotations

import pytest

from openostler.can import IsoTpChannel, IsoTpError, IsoTpSniffer, IsoTpTimeout, TxGate
from openostler.can.frame import CanFrame
from openostler.can.isotp import IsoTpParams, Reassembler, fc_bytes, segment, stmin_seconds
from openostler.can.obd import CanObdRequestLink
from tests.fake_can import FakeCanBus, FakeCanLink, FakeIsoTpPeer, FakeObdEcu
from tests.obd_fakes import ascii_hex, make_vin


def _link(bus, state="parked", allowlist=()):
    gate = TxGate(allowlist, clock=bus.now, driving_state=lambda: state)
    link = FakeCanLink(bus, gate=gate)
    link.open(500_000)
    link.confirm_rate("declared")
    return link


def _chan(link, bus, tx=0x7E0, rx=0x7E8, **kw):
    return IsoTpChannel(link, tx, rx, clock=bus.now, sleep=bus.sleep, **kw)


# ---------------------------------------------------------------- pure -- #

def test_segment_sf_ff_cf_and_padding():
    assert segment(b"\x01\x00") == [bytes.fromhex("0201005555555555")]
    assert segment(b"\x01\x00", None) == [bytes.fromhex("020100")]
    msg = bytes(range(20))
    fr = segment(msg)
    assert fr[0] == bytes.fromhex("1014000102030405")
    assert fr[1] == bytes.fromhex("2106070809 0A0B0C".replace(" ", ""))
    assert fr[2] == bytes.fromhex("220D0E0F10111213")
    assert len(segment(bytes(130))) == 1 + 18
    assert [f[0] for f in segment(bytes(130))[15:18]] == [0x2F, 0x20, 0x21]  # SN wraps F → 0
    with pytest.raises(IsoTpError):
        segment(bytes(4096))


def test_stmin_values():
    assert stmin_seconds(0x0A) == 0.010 and stmin_seconds(0x7F) == 0.127
    assert stmin_seconds(0xF1) == pytest.approx(0.0001)
    assert stmin_seconds(0xF5) == pytest.approx(0.0005)
    assert stmin_seconds(0x80) == 0.127 and stmin_seconds(0xFA) == 0.127      # reserved
    assert fc_bytes() == bytes.fromhex("3000005555555555")


def test_reassembler_new_ff_restarts_and_stray_cf_is_ignored():
    a = Reassembler()
    assert a.feed(bytes.fromhex("2101020304050607")) == ("ignored", "stray") and a.stray == 1
    first = segment(bytes(range(20)))
    second = segment(bytes(range(100, 115)))
    assert a.feed(first[0])[0] == "first" and a.feed(first[1])[0] == "progress"
    assert a.feed(second[0]) == ("first", 15)                 # a new FF restarts it
    assert a.feed(second[1])[0] == "progress"
    assert a.feed(second[2]) == ("message", bytes(range(100, 115)))
    assert a.feed(bytes.fromhex("03410D32AAAAAAAA")) == ("message", b"\x41\x0D\x32")
    assert a.feed(bytes.fromhex("3000000000000000")) == ("ignored", "fc")
    assert a.feed(bytes.fromhex("1005000102030405")) == ("ignored", "malformed")  # FF < 8


# --------------------------------------------------------------- T9: RX -- #

def test_t9_vin_over_ff_cf_fc():
    bus = FakeCanBus()
    vin = make_vin()
    ecu = FakeObdEcu(bus, 0x7E8, {"09 02": "49 02 01 " + ascii_hex(vin)})
    link = _link(bus)
    ch = _chan(link, bus)
    ch.send(b"\x09\x02")
    msg = ch.recv(1.0)
    assert msg == b"\x49\x02\x01" + vin.encode()
    assert ecu.fcs == [b"\x30\x00\x00"]                      # BS 0, STmin 0 (ISO 15765-4)
    fc = [f for _t, f in bus.tester_frames() if f.data[0] == 0x30]
    assert fc[0].id == 0x7E0 and fc[0].dlc == 8               # padded FC to reply id − 8


def test_t9_sn_wrap_over_16_cfs():
    bus = FakeCanBus()
    payload = "62 F1 00 " + " ".join(f"{i & 0xFF:02X}" for i in range(127))
    FakeObdEcu(bus, 0x7E8, {"22 F1 00": payload})
    link = _link(bus)
    ch = _chan(link, bus)
    ch.send(b"\x22\xF1\x00")
    msg = ch.recv(1.0)
    assert len(msg) == 130 and msg[3:] == bytes(i & 0xFF for i in range(127))
    sns = [f.data[0] for _t, _n, f in bus.transmitted if f.id == 0x7E8 and f.data[0] >> 4 == 2]
    assert sns[14:17] == [0x2F, 0x20, 0x21]


def test_t9_wrong_sn_aborts_and_a_dropped_cf_times_out():
    bus = FakeCanBus()
    FakeObdEcu(bus, 0x7E8, {"09 02": "49 02 01 " + ascii_hex(make_vin())}, bad_sn_at=1)
    ch = _chan(_link(bus), bus)
    ch.send(b"\x09\x02")
    with pytest.raises(IsoTpError) as ei:
        ch.recv(1.0)
    assert ei.value.code == "malformed: sequence"
    bus2 = FakeCanBus()
    FakeObdEcu(bus2, 0x7E8, {"09 02": "49 02 01 " + ascii_hex(make_vin())}, drop_cf=1)
    ch2 = _chan(_link(bus2), bus2)
    ch2.send(b"\x09\x02")
    with pytest.raises(IsoTpTimeout):
        ch2.recv(1.0)


def test_t9_stray_cf_before_the_message_is_ignored():
    bus = FakeCanBus()
    FakeObdEcu(bus, 0x7E8, {"01 0D": "41 0D 32"})
    link = _link(bus)
    ch = _chan(link, bus)
    bus.put(CanFrame(0x7E8, False, bytes.fromhex("2101020304050607")), None)
    ch.send(b"\x01\x0D")
    assert ch.recv(1.0) == b"\x41\x0D\x32"


# --------------------------------------------------------------- T10: TX -- #

ENTRY = {"id": "7E0", "data": "xx xx 22", "action": "uds_multi_read", "tier": 1}
PAYLOAD = b"\x22" + bytes(range(1, 21))                       # 21 bytes: FF + 3 CFs


def _tx_rig(script, state="parked"):
    bus = FakeCanBus()
    peer = FakeIsoTpPeer(bus, 0x7E0, 0x7E8, script)
    link = _link(bus, state, [ENTRY])
    return bus, peer, link, _chan(link, bus)


def test_t10_block_size_2_and_stmin_10ms():
    bus, peer, link, ch = _tx_rig(["30 02 0A", "30 02 0A"])
    ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    bus.sleep(0.01)                                           # let the last CF land
    cfs = [(t, d) for t, d in peer.frames if d[0] >> 4 == 2]
    assert [d[0] for _t, d in cfs] == [0x21, 0x22, 0x23]
    assert cfs[1][0] - cfs[0][0] >= 0.010 - 1e-9              # STmin inside a block
    got = b"".join(d[2:8] if d[0] >> 4 == 1 else d[1:8] for _t, d in peer.frames)
    assert got[:21] == PAYLOAD


def test_t10_stmin_f5_is_500_microseconds():
    bus, peer, link, ch = _tx_rig(["30 00 F5"])
    ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    bus.sleep(0.01)
    t = [t for t, d in peer.frames if d[0] >> 4 == 2]
    assert all(b - a >= 0.0005 - 1e-9 for a, b in zip(t, t[1:]))
    assert all(b - a < 0.010 for a, b in zip(t, t[1:]))


def test_t10_wait_frames_overflow_and_n_bs():
    bus, peer, link, ch = _tx_rig(["31 00 00"] * 3 + ["30 00 00"])
    ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    bus.sleep(0.01)
    assert len([d for _t, d in peer.frames if d[0] >> 4 == 2]) == 3
    bus, peer, link, ch = _tx_rig(["31 00 00"] * 11)
    with pytest.raises(IsoTpError) as ei:
        ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    assert ei.value.code == "max_wft"
    bus, peer, link, ch = _tx_rig(["32 00 00"])
    with pytest.raises(IsoTpError) as ei:
        ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    assert ei.value.code == "overflow"
    bus, peer, link, ch = _tx_rig([])
    t0 = bus.now()
    with pytest.raises(IsoTpTimeout) as ei:
        ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    assert ei.value.code == "n_bs" and bus.now() - t0 >= IsoTpParams().n_bs


def test_t10_multi_frame_tx_needs_allowlist_parked_and_grant():
    from openostler.can import TxRefused

    bus, peer, link, ch = _tx_rig(["30 00 00"], state="moving")
    with pytest.raises(TxRefused) as ei:
        ch.send(PAYLOAD, grant=link.gate.issue("uds_multi_read", 1))
    assert ei.value.code == "driving_state" and peer.frames == []
    bus, peer, link, ch = _tx_rig(["30 00 00"])
    with pytest.raises(TxRefused) as ei:
        ch.send(PAYLOAD)                                       # Tier 0 is single frames only
    assert ei.value.code == "no_grant"


# ----------------------------------------------------------- T11, T12: mux -- #

def test_t11_two_multi_frame_replies_interleaved_and_a_late_one_dropped():
    bus = FakeCanBus()
    n1 = b"ECM\0-" + b"EngineControl".ljust(15, b"\0")
    n2 = b"TCM\0-" + b"TransControl".ljust(15, b"\0")
    FakeObdEcu(bus, 0x7E8, {"09 0A": "49 0A 01 " + ascii_hex(n1)}, delay=0.004)
    FakeObdEcu(bus, 0x7E9, {"09 0A": "49 0A 01 " + ascii_hex(n2)}, delay=0.004)
    FakeObdEcu(bus, 0x7EA, {"09 0A": "49 0A 01 41 42"}, late={"09 0A": 0.080})
    link = _link(bus)
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    out = obd.request(b"\x09\x0A")
    assert set(out) == {"7E8", "7E9"}
    assert out["7E8"].messages == (b"\x49\x0A\x01" + n1,)
    assert out["7E9"].messages == (b"\x49\x0A\x01" + n2,)
    ids = [f.id for _t, _n, f in bus.transmitted if f.id in (0x7E8, 0x7E9)]
    last_e8 = len(ids) - 1 - ids[::-1].index(0x7E8)
    assert ids.index(0x7E9) < last_e8                         # the two messages interleave
    bus.sleep(0.1)                                            # the late SF lands now…
    again = obd.request(b"\x09\x0A")                          # …and is flushed, not read
    assert "7EA" not in again


def test_t12_response_pending_then_the_reply_after_2s():
    bus = FakeCanBus()
    FakeObdEcu(bus, 0x7E8, {"01 0D": "41 0D 32"}, pending=1, pending_gap=2.0)
    link = _link(bus)
    obd = CanObdRequestLink(link, clock=bus.now, sleep=bus.sleep)
    t0 = bus.now()
    out = obd.request(b"\x01\x0D")
    assert out["7E8"].messages == (b"\x41\x0D\x32",)
    assert 2.0 <= bus.now() - t0 < IsoTpParams().p2_star


# ----------------------------------------------------------- T14: sniffer -- #

def test_t14_sniffer_reassembles_someone_elses_session_without_fc():
    bus = FakeCanBus()
    vin = make_vin()
    FakeObdEcu(bus, 0x7E8, {"09 02": "49 02 01 " + ascii_hex(vin)})
    tester = _link(bus)
    sniff_link = FakeCanLink(bus, name="sniffer")
    sniff_link.open(500_000)                                  # listen-only, never confirmed
    CanObdRequestLink(tester, clock=bus.now).request(b"\x09\x02")
    got = IsoTpSniffer().run(sniff_link, 0.01)
    assert (0x7DF, False, b"\x09\x02") in got
    assert (0x7E8, False, b"\x49\x02\x01" + vin.encode()) in got
    assert bus.tester_frames("sniffer") == [] and sniff_link.hw_listen_only
