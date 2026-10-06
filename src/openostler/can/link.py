# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The frame-level ``CanLink`` beside the byte ``Transport`` (ADR-0020, CanLink spec §2).

Every backend opens **listen-only** by default. ``send()`` raises
:class:`RateNotConfirmed` until the bitrate is confirmed or declared (ADR-0023) and
:class:`TxRefused` unless the link's :class:`~openostler.can.gate.TxGate` passes the frame
(spec §7). The first permitted ``send()`` turns listen-only off (``confirmed`` →
``active``); the link drops back to listen-only when the OBD session ends
(:meth:`CanLink.end_session`) or after 30 s without a permitted transmit.

This Python link is the lab/reference (spec §7.1, ADR-0032): production CAN I/O is the
node's TWAI controller and its C ``TxGate``.
"""
from __future__ import annotations

import abc
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .frame import CanFrame

CLOSED, LISTENING, CONFIRMED, ACTIVE = "closed", "listening", "confirmed", "active"
STATES = (CLOSED, LISTENING, CONFIRMED, ACTIVE)
RATE_SOURCES = ("detected", "declared", "manual", "probe")
ACTIVE_IDLE_S = 30.0            # back to listen-only after this long without a permitted TX


class CanError(Exception):
    """A CAN link error (closed link, backend failure)."""


class TxRefused(CanError):
    """The transmit gate refused a frame. ``code`` is machine-readable (spec §7)."""

    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class RateNotConfirmed(TxRefused):
    """``send()`` before the bitrate is confirmed or declared (ADR-0023)."""

    def __init__(self, message: str = "bitrate not confirmed: the link stays listen-only") -> None:
        super().__init__("rate_not_confirmed", message)


@dataclass(frozen=True)
class LinkCaps:
    """What a backend can do. A capability we cannot verify is reported as such
    (``listen_only="requested"``), never assumed (spec §2)."""

    kind: str = "fake"                       # socketcan | slcan | slcan-tcp | gvret | python-can
    tx: bool = True
    listen_only: "bool | str" = True         # True | False | "requested"
    set_bitrate: bool = True
    one_shot: bool = False
    error_frames: "bool | str" = True       # True | False | "flags" (slcan status polling)
    err_counters: bool = False
    timestamps: bool = True
    fd: bool = False
    max_rx_rate: "int | None" = None         # frames/s the controller keeps up with

    def to_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass(frozen=True)
class OneShotResult:
    """The outcome of one one-shot probe frame (spec §4 step 4)."""

    acked: bool
    error: bool
    replies: "Tuple[CanFrame, ...]" = ()


@dataclass
class _Status:
    state: str = CLOSED
    bitrate: "int | None" = None
    listen_only: bool = True
    rate_source: str = ""
    id_widths: "frozenset[int]" = field(default_factory=frozenset)


class CanLink(abc.ABC):
    """A frame-level CAN link. Backends implement the ``_hw_*`` hooks; the state machine,
    the gate and the listen-only rules live here, once for every backend."""

    caps: LinkCaps = LinkCaps()

    def __init__(self, *, gate=None, channel: str = "can0",
                 clock: Callable[[], float] = time.monotonic,
                 active_idle_s: float = ACTIVE_IDLE_S) -> None:
        self.gate = gate
        self.channel = channel
        self.clock = clock
        self.active_idle_s = active_idle_s
        self._st = _Status()
        self._last_tx: "float | None" = None

    # ---- state ------------------------------------------------------------ #
    @property
    def state(self) -> str:
        return self._st.state

    @property
    def bitrate(self) -> "int | None":
        return self._st.bitrate

    @property
    def rate_source(self) -> str:
        return self._st.rate_source

    @property
    def id_widths(self) -> "frozenset[int]":
        return self._st.id_widths

    @property
    def listen_only(self) -> bool:
        return self._st.listen_only

    @property
    def rate_confirmed(self) -> bool:
        return self._st.state in (CONFIRMED, ACTIVE)

    def describe(self) -> dict:
        """The link chip's facts (ADR-0020: the mode is always shown)."""
        lo = self.caps.listen_only if self._st.listen_only else False
        return {"kind": self.caps.kind, "channel": self.channel, "state": self.state,
                "bitrate": self.bitrate, "rate_source": self.rate_source or None,
                "listen_only": lo, "id_widths": sorted(self.id_widths)}

    # ---- lifecycle -------------------------------------------------------- #
    def open(self, bitrate: "int | None", *, listen_only: bool = True) -> None:
        """Open at ``bitrate``. Every link opens listen-only, whatever ``listen_only``
        says: ``listen_only=False`` only states the intent to transmit later, and the
        first ``send()`` the gate permits (after the rate is confirmed) turns it off."""
        if self._st.state != CLOSED:
            self.close()
        self._hw_open(bitrate, listen_only=True, one_shot=False)
        self._st = _Status(LISTENING, bitrate, True)

    def close(self) -> None:
        if self._st.state != CLOSED:
            try:
                self._hw_close()
            finally:
                self._st = _Status()
                self._last_tx = None

    def confirm_rate(self, source: str, widths: "frozenset[int] | None" = None) -> None:
        """Mark the open rate confirmed (detection, a declared or a manual rate)."""
        if self._st.state == CLOSED:
            raise CanError("link is closed")
        if source not in RATE_SOURCES:
            raise ValueError(f"unknown rate source {source!r}")
        self._st.state = CONFIRMED if self._st.state == LISTENING else self._st.state
        self._st.rate_source = source
        if widths is not None:
            self._st.id_widths = frozenset(widths)

    def end_session(self) -> None:
        """The OBD session ended: back to listen-only (spec §2)."""
        if self._st.state == ACTIVE:
            self._hw_set_listen_only(True)
            self._st.listen_only = True
            self._st.state = CONFIRMED

    def _relax_if_idle(self) -> None:
        if (self._st.state == ACTIVE and self._last_tx is not None
                and self.clock() - self._last_tx >= self.active_idle_s):
            self.end_session()

    # ---- RX --------------------------------------------------------------- #
    def recv(self, timeout: "float | None") -> "CanFrame | None":
        """The next frame, or None at the timeout. Error frames have ``error=True``."""
        if self._st.state == CLOSED:
            raise CanError("link is closed")
        self._relax_if_idle()
        return self._hw_recv(timeout)

    @abc.abstractmethod
    def set_filters(self, filters: "List[Tuple[int, int, bool]]") -> None:
        """``(id, mask, extended)`` acceptance filters; an empty list accepts all."""

    @abc.abstractmethod
    def flush_rx(self) -> int:
        """Drop every queued frame; → the number dropped."""

    def error_counters(self) -> "Tuple[int, int] | None":
        """``(tec, rec)``, or None when the backend cannot read them."""
        return None

    # ---- TX --------------------------------------------------------------- #
    def _gate(self):
        if self.gate is None:
            from .gate import TxGate
            # Tier 0 only: no allowlist, and the driving state unknown (counts as Moving).
            self.gate = TxGate(clock=self.clock)
        return self.gate

    def send(self, frame: CanFrame, *, grant=None) -> None:
        """Send one frame through the gate. ``grant`` is ``TIER0`` (the default) for a
        diagnostic read or its flow control, else a ``TxGrant`` (spec §7)."""
        from .gate import TIER0
        if self._st.state == CLOSED:
            raise CanError("link is closed")
        if not self.rate_confirmed:
            raise RateNotConfirmed()
        if not self.caps.tx:
            raise TxRefused("no_tx", f"{self.caps.kind} link cannot transmit")
        self._gate().check(frame, TIER0 if grant is None else grant,
                           rate_ok=True, link_kind=self.caps.kind)
        if self._st.listen_only:
            self._hw_set_listen_only(False)
            self._st.listen_only = False
            self._st.state = ACTIVE
        self._hw_send(frame)
        self._last_tx = self.clock()

    def send_oneshot(self, frame: CanFrame, *, probe, timeout: float = 0.1) -> OneShotResult:
        """The silent-bus probe (spec §4 step 4): one frame, one-shot, at an unconfirmed
        rate, only with a ``ProbeGrant`` minted while Parked. The link returns to
        listen-only afterwards, whatever happened."""
        if self._st.state == CLOSED:
            raise CanError("link is closed")
        self._gate().check_probe(frame, probe, one_shot=bool(self.caps.one_shot),
                                 link_kind=self.caps.kind)
        try:
            self._hw_open(self._st.bitrate, listen_only=False, one_shot=True)
            return self._hw_oneshot(frame, timeout)
        finally:
            self._hw_open(self._st.bitrate, listen_only=True, one_shot=False)
            self._st.listen_only = True

    # ---- backend hooks ---------------------------------------------------- #
    @abc.abstractmethod
    def _hw_open(self, bitrate: "int | None", *, listen_only: bool, one_shot: bool) -> None: ...

    @abc.abstractmethod
    def _hw_close(self) -> None: ...

    @abc.abstractmethod
    def _hw_recv(self, timeout: "float | None") -> "CanFrame | None": ...

    @abc.abstractmethod
    def _hw_send(self, frame: CanFrame) -> None: ...

    def _hw_set_listen_only(self, on: bool) -> None:
        self._hw_open(self._st.bitrate, listen_only=on, one_shot=False)

    def _hw_oneshot(self, frame: CanFrame, timeout: float) -> OneShotResult:
        raise TxRefused("no_one_shot", f"{self.caps.kind} link has no one-shot mode")


def deadline_recv(link: CanLink, deadline: float,
                  clock: "Optional[Callable[[], float]]" = None) -> "CanFrame | None":
    """``link.recv`` until ``deadline`` on ``clock`` (the link's by default)."""
    clock = clock or link.clock
    left = deadline - clock()
    if left <= 0:
        return None
    return link.recv(left)


__all__ = ["CanLink", "LinkCaps", "OneShotResult", "CanError", "TxRefused",
           "RateNotConfirmed", "CLOSED", "LISTENING", "CONFIRMED", "ACTIVE", "STATES",
           "RATE_SOURCES", "ACTIVE_IDLE_S", "deadline_recv"]
