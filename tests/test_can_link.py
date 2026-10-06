# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The ``CanLink`` state machine (CanLink spec §1–§2; test T4): listen-only by default,
no transmit before the rate is confirmed, active only for a permitted send, back to
listen-only after the session or 30 s idle. No hardware."""
from __future__ import annotations

import pytest

from openostler.can import CanFrame, LinkCaps, RateNotConfirmed, TxGate, TxRefused
from openostler.can.frame import pad
from openostler.can.link import ACTIVE, CLOSED, CONFIRMED, LISTENING, CanError
from tests.fake_can import FakeCanBus, FakeCanLink

REQ = CanFrame(0x7DF, False, pad(b"\x02\x01\x00"))


def test_frame_validation_and_text():
    assert CanFrame(0x7E8, data=b"\x01").dlc == 1
    assert CanFrame(0x18DAF110, True).id_text == "18DAF110"
    assert repr(CanFrame(0x7E8, data=b"\x41")) == "CanFrame(7E8#41)"
    with pytest.raises(ValueError):
        CanFrame(0x800)
    with pytest.raises(ValueError):
        CanFrame(0x7E8, data=bytes(9))
    assert CanFrame(0x7E8, data=bytes(64), fd=True).dlc == 64   # reserved for FD


def test_t4_send_before_confirmation_raises_and_puts_nothing_on_the_bus():
    bus = FakeCanBus()
    link = FakeCanLink(bus)
    with pytest.raises(CanError):
        link.send(REQ)                                     # closed
    link.open(500_000, listen_only=False)                  # intent only: still listen-only
    assert link.state == LISTENING and link.hw_listen_only
    with pytest.raises(RateNotConfirmed) as ei:
        link.send(REQ)
    assert isinstance(ei.value, TxRefused) and ei.value.code == "rate_not_confirmed"
    bus.sleep(0.1)
    assert bus.transmitted == [] and link.opens == [(500_000, True, False)]


def test_open_is_listen_only_and_a_permitted_send_goes_active_then_back():
    bus = FakeCanBus()
    link = FakeCanLink(bus, gate=TxGate(clock=bus.now))
    link.open(500_000)
    link.confirm_rate("detected", frozenset({11}))
    assert link.state == CONFIRMED and link.listen_only
    assert link.describe()["listen_only"] is True
    link.send(REQ)
    assert link.state == ACTIVE and not link.hw_listen_only
    assert link.describe()["listen_only"] is False
    bus.sleep(29.0)
    link.recv(0.0)
    assert link.state == ACTIVE
    bus.sleep(1.5)
    link.recv(0.0)                                         # 30 s without a permitted TX
    assert link.state == CONFIRMED and link.hw_listen_only
    link.send(REQ)
    link.end_session()
    assert link.state == CONFIRMED and link.listen_only
    link.close()
    assert link.state == CLOSED and link.bitrate is None


def test_refused_frame_never_turns_listen_only_off():
    bus = FakeCanBus()
    link = FakeCanLink(bus, gate=TxGate(clock=bus.now))
    link.open(500_000)
    link.confirm_rate("declared")
    with pytest.raises(TxRefused):
        link.send(CanFrame(0x7DF, False, pad(b"\x01\x04")))       # Mode 04, no allowlist
    assert link.hw_listen_only and link.state == CONFIRMED and bus.transmitted == []


def test_a_link_without_tx_and_an_unverifiable_listen_only_are_reported():
    bus = FakeCanBus()
    link = FakeCanLink(bus, caps=LinkCaps(kind="python-can", tx=False, listen_only=False))
    link.open(500_000)
    link.confirm_rate("declared")
    with pytest.raises(TxRefused) as ei:
        link.send(REQ)
    assert ei.value.code == "no_tx"
    wican = FakeCanLink(bus, caps=LinkCaps(kind="slcan-tcp", listen_only="requested"))
    wican.open(500_000)
    assert wican.describe()["listen_only"] == "requested"


def test_default_gate_is_tier0_only_and_moving():
    bus = FakeCanBus()
    link = FakeCanLink(bus)
    link.open(500_000)
    link.confirm_rate("manual")
    link.send(REQ)
    assert link.gate.state() == "moving"
    with pytest.raises(ValueError):
        link.confirm_rate("guessed")


def test_wrong_rate_link_hears_only_error_frames():
    bus = FakeCanBus(250_000)
    bus.periodic(0x100, period=0.01, count=3)
    link = FakeCanLink(bus)
    link.open(500_000)
    frames = [link.recv(0.05) for _ in range(3)]
    assert all(f is not None and f.error for f in frames)
    assert link.error_counters()[1] == 24
