# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The J1979 request model (spec §2): ``ObdRequestLink``, ``EcuReply``, request pacing,
reply validation and the service guard.

A transport adapter (``kline/obd_link.py``, later ``can/obd.py``) implements
:class:`ObdRequestLink`: it sends one OBD request and returns **every** responder's whole
service messages keyed by ECU address, with headers, checksums and ISO-TP PCI removed. This
module adds what every adapter shares: pacing (one request in flight, 50 ms per ECU, the
``0x21`` back-off), the validation that drops a late reply to an earlier request, and the
guard that refuses Mode 08 always and Mode 04 outside :meth:`J1979.clear_dtcs`.

Pure and stdlib-only; it imports nothing from ``kline``, ``kwp2000`` or ``can``.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Protocol, Tuple

FLAVORS = ("can11", "can29", "iso9141", "kwp")
CAN_FLAVORS = ("can11", "can29")
KLINE_FLAVORS = ("iso9141", "kwp")

NEGATIVE = 0x7F
NRC_BUSY_REPEAT = 0x21          # busyRepeatRequest: back off and repeat
NRC_CONDITIONS_NOT_CORRECT = 0x22
NRC_RESPONSE_PENDING = 0x78     # handled by the adapter (wait up to P2*, at most 6 times)

MODE_CLEAR = 0x04               # reaches the car only through J1979.clear_dtcs (spec §5)
MODE_NEVER = 0x08               # never sent, not even its bitmap (owner Q6, spec §5)

# Modes whose positive reply echoes the PID / MID / InfoType asked for (spec §2.1).
ECHO_MODES = frozenset({0x01, 0x02, 0x05, 0x06, 0x09})


class ObdError(Exception):
    """Base for J1979 errors. Messages never carry reply bytes of an identity read."""


class ForbiddenService(ObdError):
    """A request the platform never sends (Mode 08) or sends only through a grant (04)."""


@dataclass(frozen=True)
class EcuReply:
    """One ECU's whole service messages for one request."""

    ecu: str                        # "7E8", "18DAF110", or the K-line source byte "10"
    messages: Tuple[bytes, ...]     # headers, checksums and PCI removed


class ObdRequestLink(Protocol):
    """What a transport adapter offers the J1979 layer (spec §2.1)."""

    flavor: str                     # "can11" | "can29" | "iso9141" | "kwp"

    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None,
                timeout: "float | None" = None) -> "Dict[str, EcuReply]": ...


def guard_payload(payload: bytes, *, allow_clear: bool = False) -> None:
    """Refuse a Mode 08 request always and a Mode 04 request unless ``allow_clear``.

    Every adapter calls this with ``allow_clear=True`` (the J1979 layer has already
    checked the grant); the J1979 layer calls it with ``False`` outside ``clear_dtcs``."""
    if not payload:
        raise ObdError("empty OBD request")
    if payload[0] == MODE_NEVER:
        raise ForbiddenService("Mode 08 is never sent (spec §5, owner Q6)")
    if payload[0] == MODE_CLEAR and not allow_clear:
        raise ForbiddenService("Mode 04 is sent only by J1979.clear_dtcs with a ClearGrant")


# ------------------------------------------------------------------ results -- #

@dataclass(frozen=True)
class EcuStatus:
    """The typed outcome for one ECU: ``ok``, ``negative`` (with ``nrc``), ``malformed``
    (with ``reason``) or ``no_reply``. Never a sentinel value."""

    ecu: str
    status: str
    messages: Tuple[bytes, ...] = ()
    nrc: "int | None" = None
    reason: "str | None" = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def __repr__(self) -> str:  # messages are left out: an identity reply must never print
        extra = f", nrc=0x{self.nrc:02X}" if self.nrc is not None else ""
        extra += f", reason={self.reason!r}" if self.reason else ""
        return f"EcuStatus(ecu={self.ecu!r}, status={self.status!r}{extra}, " \
               f"messages={len(self.messages)})"


def _echoes(payload: bytes, msg: bytes) -> bool:
    mode = payload[0]
    if mode not in ECHO_MODES or len(payload) < 2:
        return True
    if len(msg) < 2:
        return False
    if mode in (0x01, 0x02):
        # A multi-PID request (CAN, up to 6 PIDs) is echoed PID by PID; the first PID of
        # the reply must be one asked for. Mode 02 pairs each PID with its frame number.
        asked = payload[1::2] if mode == 0x02 else payload[1:]
        return msg[1] in asked
    return msg[1] == payload[1]


def classify(payload: bytes, replies: "Dict[str, EcuReply]",
             expected: "tuple[str, ...]" = ()) -> "tuple[Dict[str, EcuStatus], int]":
    """Turn raw replies into typed per-ECU results (spec §2.1).

    A message counts only when its service byte is ``request + 0x40`` and it echoes the
    PID, MID or InfoType asked for; ``7F <sid> <nrc>`` is a negative reply. Anything else
    (a late frame from the previous request) is dropped and counted. ECUs in ``expected``
    that sent nothing are ``no_reply``. → ``(results, dropped)``."""
    sid = payload[0]
    out: "Dict[str, EcuStatus]" = {}
    dropped = 0
    for ecu, reply in replies.items():
        good: "list[bytes]" = []
        nrc: "int | None" = None
        for msg in reply.messages:
            msg = bytes(msg)
            if len(msg) >= 3 and msg[0] == NEGATIVE and msg[1] == sid:
                nrc = msg[2]
            elif msg and msg[0] == (sid + 0x40) & 0xFF and _echoes(payload, msg):
                good.append(msg)
            else:
                dropped += 1
        if good:
            out[ecu] = EcuStatus(ecu, "ok", tuple(good))
        elif nrc is not None:
            out[ecu] = EcuStatus(ecu, "negative", nrc=nrc)
    for ecu in expected:
        out.setdefault(ecu, EcuStatus(ecu, "no_reply"))
    return out, dropped


# ------------------------------------------------------------------- pacing -- #

@dataclass
class Pacer:
    """Request pacing shared by every adapter (spec §2.1, ADR-0020): at least ``min_gap``
    between requests to the same ECU (a functional request counts for every ECU)."""

    min_gap: float = 0.050
    backoff: "tuple[float, ...]" = (0.050, 0.100, 0.200)
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep
    _last: "Dict[str, float]" = field(default_factory=dict)

    def wait(self, target: "str | None") -> None:
        if target is None:
            last = max(self._last.values(), default=None)
        else:
            cands = [v for k, v in self._last.items() if k in (target, "*")]
            last = max(cands, default=None)
        if last is None:
            return
        due = last + self.min_gap - self.clock()
        if due > 0:
            self.sleep(due)

    def mark(self, target: "str | None", ecus: "tuple[str, ...]" = ()) -> None:
        now = self.clock()
        self._last["*" if target is None else target] = now
        for e in ecus:
            self._last[e] = now


class PacedLink:
    """Wraps an :class:`ObdRequestLink`: one request in flight, the pacer, the ``0x21``
    back-off (50, 100, then 200 ms) and the payload guard."""

    def __init__(self, link: ObdRequestLink, pacer: "Optional[Pacer]" = None) -> None:
        self._link = link
        self.flavor = link.flavor
        self.pacer = pacer if pacer is not None else Pacer()
        self._lock = threading.Lock()

    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None, timeout: "float | None" = None,
                allow_clear: bool = False) -> "Dict[str, EcuReply]":
        guard_payload(payload, allow_clear=allow_clear)
        with self._lock:
            replies = self._once(payload, target, expect_messages, timeout)
            for delay in self.pacer.backoff:
                busy = [e for e, r in replies.items() if _only_busy(r, payload[0])]
                if not busy:
                    break
                self.pacer.sleep(delay)
                again = self._once(payload, target, expect_messages, timeout)
                for e in busy:
                    if e in again:
                        replies[e] = again[e]
                for e, r in again.items():
                    replies.setdefault(e, r)
            return replies

    def _once(self, payload, target, expect_messages, timeout) -> "Dict[str, EcuReply]":
        self.pacer.wait(target)
        replies = dict(self._link.request(payload, target=target,
                                          expect_messages=expect_messages, timeout=timeout))
        self.pacer.mark(target, tuple(replies))
        return replies


def _only_busy(reply: EcuReply, sid: int) -> bool:
    msgs = [bytes(m) for m in reply.messages]
    return bool(msgs) and all(len(m) >= 3 and m[0] == NEGATIVE and m[1] == sid
                              and m[2] == NRC_BUSY_REPEAT for m in msgs)


__all__ = ["FLAVORS", "CAN_FLAVORS", "KLINE_FLAVORS", "EcuReply", "ObdRequestLink",
           "EcuStatus", "ObdError", "ForbiddenService", "guard_payload", "classify",
           "Pacer", "PacedLink", "NEGATIVE", "NRC_BUSY_REPEAT",
           "NRC_CONDITIONS_NOT_CORRECT", "NRC_RESPONSE_PENDING", "MODE_CLEAR",
           "MODE_NEVER"]
