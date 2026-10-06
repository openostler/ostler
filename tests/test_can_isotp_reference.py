# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""T16 (CanLink spec §6, §11): a dev-only differential test. The same SF/FF/CF/FC
sequences (block size, STmin, WAIT, SN wrap) go through our ISO-TP and through can-isotp
(MIT), and the payloads and FC bytes must be identical. can-isotp is only this test's
reference: it is in the ``[dev]`` extra, never imported at runtime, vendored or shipped;
the test is skipped when it is absent."""
from __future__ import annotations

import time

import pytest

from openostler.can import TxGate
from openostler.can.isotp import CTS, IsoTpChannel, Reassembler, fc_bytes, segment
from tests.fake_can import FakeCanBus, FakeCanLink, FakeIsoTpPeer

isotp = pytest.importorskip("isotp")

PAD = 0x55


def _theirs(params: dict):
    rx: "list" = []
    tx: "list[bytes]" = []
    errors: "list[Exception]" = []

    def rxfn(timeout):
        return rx.pop(0) if rx else None

    addr = isotp.Address(isotp.AddressingMode.Normal_11bits, txid=0x7E0, rxid=0x7E8)
    base = {"tx_padding": PAD, "tx_data_length": 8, "rx_flowcontrol_timeout": 1000,
            "rx_consecutive_frame_timeout": 1000}
    base.update(params)
    stack = isotp.TransportLayerLogic(rxfn=rxfn, txfn=lambda m: tx.append(bytes(m.data)),
                                      address=addr, error_handler=errors.append, params=base)
    return stack, rx, tx, errors


def _msg(data: bytes):
    return isotp.CanMessage(arbitration_id=0x7E8, dlc=len(data), data=data)


def _ours_rx(frames, bs, stmin):
    a = Reassembler(bs)
    fcs: "list[bytes]" = []
    out = None
    for f in frames:
        ev, val = a.feed(f)
        if ev == "first" or (ev == "progress" and val):
            fcs.append(fc_bytes(CTS, bs, stmin, PAD))
        if ev == "message":
            out = val
    return out, fcs


def _theirs_rx(frames, bs, stmin):
    stack, rx, tx, errors = _theirs({"blocksize": bs, "stmin": stmin})
    for f in frames:
        rx.append(_msg(f))
        for _ in range(3):
            stack.process()
    got = stack.recv() if stack.available() else None
    assert not errors, errors
    return got, tx


@pytest.mark.parametrize("n,bs,stmin", [
    (20, 0, 0),             # the VIN shape: FF + 2 CFs
    (130, 0, 0),            # SN wraps F -> 0
    (130, 2, 0),            # an FC after every 2 CFs
    (61, 8, 0x0A),          # BS 8, STmin 10 ms in our FC
    (300, 0, 0xF5),         # STmin 500 µs in our FC
    (7, 0, 0),              # a single frame
])
def test_t16_rx_payload_and_fc_bytes_match(n, bs, stmin):
    payload = bytes((i * 7 + 1) & 0xFF for i in range(n))
    frames = segment(payload, 0xAA)                # the ECU pads with AA; ignored either way
    ours, our_fc = _ours_rx(frames, bs, stmin)
    theirs, their_fc = _theirs_rx(frames, bs, stmin)
    assert ours == theirs == payload
    assert our_fc == their_fc


def _ours_tx(payload: bytes, fcs: "list[str]") -> "list[bytes]":
    bus = FakeCanBus()
    peer = FakeIsoTpPeer(bus, 0x7E0, 0x7E8, fcs)
    gate = TxGate([{"id": "7E0", "data": f"xx xx {payload[0]:02X}", "action": "t16",
                    "tier": 1}], clock=bus.now, driving_state=lambda: "parked")
    link = FakeCanLink(bus, gate=gate)
    link.open(500_000)
    link.confirm_rate("declared")
    ch = IsoTpChannel(link, 0x7E0, 0x7E8, clock=bus.now, sleep=bus.sleep)
    ch.send(payload, grant=gate.issue("t16", 1))
    bus.sleep(0.05)
    return [d for _t, d in peer.frames]


def _theirs_tx(payload: bytes, fcs: "list[str]") -> "list[bytes]":
    stack, rx, tx, errors = _theirs({"wftmax": 10})
    stack.send(payload)
    queue = [bytes.fromhex(f) for f in fcs]
    bs = block = 0
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        seen = len(tx)
        stack.process()
        for d in tx[seen:]:
            due = d[0] >> 4 == 1
            if d[0] >> 4 == 2 and bs:
                block += 1
                due = block == bs
            while due and queue:                    # the receiver: WAITs, then a CTS
                fc = queue.pop(0)
                rx.append(_msg(fc.ljust(8, b"\xAA")))
                if fc[0] == 0x30:
                    bs, block = fc[1], 0
                    break
        if len(tx) > 1 and not stack.transmitting():
            break
        time.sleep(0.0005)
    assert not errors, errors
    return tx


@pytest.mark.parametrize("n,fcs", [
    (21, ["30 00 00"]),
    (21, ["30 02 00", "30 02 00"]),
    (130, ["30 00 00"]),                         # SN wrap on our side as sender
    (40, ["30 03 01", "30 03 01"]),              # BS 3, STmin 1 ms
    (21, ["31 00 00", "31 00 00", "30 00 00"]),  # WAIT x2, then CTS
])
def test_t16_tx_frames_match(n, fcs):
    payload = b"\x22" + bytes((i * 3) & 0xFF for i in range(n - 1))
    ours = _ours_tx(payload, list(fcs))
    theirs = _theirs_tx(payload, list(fcs))
    assert ours == theirs
    assert len(ours) == len(segment(payload))
