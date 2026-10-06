# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ISO-TP (ISO 15765-2), our own pure-Python implementation (CanLink spec §6, owner Q8).

- :func:`segment` and :class:`Reassembler` are the pure state machine (SF ``0L``, FF
  ``1LLL``, CF ``2N``, FC ``3S BS STmin``); the shared vectors in
  ``tests/vectors/can/isotp.json`` check them, and the node's C port runs the same files.
- :class:`IsoTpChannel` is one ``(tx_id, rx_id)`` pair: it sends multi-frame messages
  (waits for FC within N_Bs, honours BS, STmin, WAIT up to ``max_wft``, aborts on OVFLW)
  and receives them (sends FC ``30 BS STmin``, N_Cr per CF).
- :class:`IsoTpMux` sends one request and collects **one message per responding ECU**
  until P2 passes with every started message complete, or P2* after ``7F xx 78``.
- :class:`IsoTpSniffer` reassembles someone else's session without sending FC.
- :class:`KernelIsoTpChannel` is the optional Linux ``CAN_ISOTP`` socket for physical
  channels; opening one and every payload pass the :class:`~openostler.can.gate.TxGate`.

Every frame we send goes through ``CanLink.send``, so the gate sees each one. can-isotp is
only the dev-time reference of the differential test (T16), never imported here.
"""
from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .frame import CanFrame, pad
from .link import CanError, CanLink, TxRefused

CTS, WAIT, OVFLW = 0, 1, 2
MAX_LEN = 4095


class IsoTpError(CanError):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class IsoTpTimeout(IsoTpError):
    pass


@dataclass(frozen=True)
class IsoTpParams:
    """ISO 15765-4 defaults; a pack may override them."""

    n_as: float = 0.025
    n_ar: float = 0.025
    n_bs: float = 0.075
    n_cr: float = 0.150
    p2: float = 0.050
    p2_star: float = 5.0
    pad: int = 0x55            # open question 4: 0x55 drafted
    bs: int = 0                # our FC: BS 0 and STmin 0, as ISO 15765-4 asks of testers
    stmin: int = 0             # open question 2: a slow controller may want more
    max_wft: int = 10
    max_pending: int = 6


def stmin_seconds(b: int) -> float:
    """STmin byte → seconds: ``00``–``7F`` ms, ``F1``–``F9`` 100–900 µs, reserved = 127 ms."""
    if 0x00 <= b <= 0x7F:
        return b / 1000.0
    if 0xF1 <= b <= 0xF9:
        return (b - 0xF0) / 10000.0
    return 0.127


def segment(payload: bytes, pad_byte: "int | None" = 0x55) -> "List[bytes]":
    """``payload`` → the SF, or the FF and its CFs (SN from 1, wrapping F → 0), each
    padded to 8 bytes when ``pad_byte`` is not None."""
    payload = bytes(payload)
    n = len(payload)
    if not 1 <= n <= MAX_LEN:
        raise IsoTpError("length", f"ISO-TP payload of {n} bytes (1..{MAX_LEN})")
    p = (lambda b: pad(b, pad_byte)) if pad_byte is not None else bytes
    if n <= 7:
        return [p(bytes([n]) + payload)]
    out = [bytes([0x10 | (n >> 8), n & 0xFF]) + payload[:6]]
    sn = 1
    for i in range(6, n, 7):
        out.append(p(bytes([0x20 | sn]) + payload[i:i + 7]))
        sn = (sn + 1) & 0x0F
    return out


def fc_bytes(status: int = CTS, bs: int = 0, stmin: int = 0,
             pad_byte: "int | None" = 0x55) -> bytes:
    b = bytes([0x30 | status, bs, stmin])
    return pad(b, pad_byte) if pad_byte is not None else b


class Reassembler:
    """The receive state machine for one CAN id. :meth:`feed` → ``(event, value)``:

    ``message`` (the whole payload) · ``first`` (an FF: send FC) · ``progress`` (a CF;
    value True when a block of ``bs`` CFs is full) · ``aborted`` (reason) · ``ignored``
    (reason: a stray CF, an FC, a malformed PCI)."""

    def __init__(self, bs: int = 0) -> None:
        self.bs = bs
        self.buf = bytearray()
        self.total = 0
        self.sn = 0
        self.block = 0
        self.stray = 0

    @property
    def active(self) -> bool:
        return self.total > 0

    def reset(self) -> None:
        self.buf = bytearray()
        self.total = self.sn = self.block = 0

    def feed(self, data: bytes) -> "Tuple[str, object]":
        data = bytes(data)
        if not data:
            return ("ignored", "empty")
        pci = data[0] >> 4
        if pci == 0:
            n = data[0] & 0x0F
            if not 1 <= n <= 7 or len(data) < 1 + n:
                return ("ignored", "malformed")
            self.reset()                     # an SF mid-message ends that message
            return ("message", bytes(data[1:1 + n]))
        if pci == 1:
            if len(data) < 8:
                return ("ignored", "malformed")
            total = ((data[0] & 0x0F) << 8) | data[1]
            if total < 8:                    # 0 = the 32-bit FD escape (out of scope)
                return ("ignored", "malformed")
            self.reset()
            self.total = total
            self.buf = bytearray(data[2:8])
            self.sn = 1
            return ("first", total)
        if pci == 2:
            if not self.active:
                self.stray += 1
                return ("ignored", "stray")
            if data[0] & 0x0F != self.sn:
                self.reset()
                return ("aborted", "sequence")
            need = min(7, self.total - len(self.buf))
            if len(data) - 1 < need:
                self.reset()
                return ("aborted", "short")
            self.buf += data[1:1 + need]
            self.sn = (self.sn + 1) & 0x0F
            if len(self.buf) >= self.total:
                msg = bytes(self.buf)
                self.reset()
                return ("message", msg)
            self.block += 1
            full = bool(self.bs) and self.block >= self.bs
            if full:
                self.block = 0
            return ("progress", full)
        if pci == 3:
            return ("ignored", "fc")
        return ("ignored", "malformed")


def precise_wait(seconds: float) -> None:
    """Sleep with sub-millisecond precision (as ``kline._precise_wait``): STmin values of
    100–900 µs need it."""
    if seconds <= 0:
        return
    deadline = time.perf_counter() + seconds
    if seconds > 0.050:
        time.sleep(seconds - 0.050)
    while time.perf_counter() < deadline:
        pass


class _Base:
    def __init__(self, link: CanLink, extended: bool, params: "IsoTpParams | None",
                 clock: "Optional[Callable[[], float]]",
                 sleep: "Optional[Callable[[float], None]]") -> None:
        self.link = link
        self.extended = extended
        self.params = params or IsoTpParams()
        self.clock = clock or link.clock
        self.sleep = sleep or precise_wait

    def _frame(self, can_id: int, data: bytes) -> CanFrame:
        return CanFrame(can_id, self.extended, data)

    def _recv_until(self, deadline: float) -> "CanFrame | None":
        left = deadline - self.clock()
        return self.link.recv(left) if left > 0 else None


class IsoTpChannel(_Base):
    """One ISO-TP channel ``(tx_id, rx_id, extended)`` over a :class:`CanLink`."""

    def __init__(self, link: CanLink, tx_id: int, rx_id: int, *, extended: bool = False,
                 params: "IsoTpParams | None" = None,
                 clock: "Optional[Callable[[], float]]" = None,
                 sleep: "Optional[Callable[[float], None]]" = None) -> None:
        super().__init__(link, extended, params, clock, sleep)
        self.tx_id, self.rx_id = tx_id, rx_id
        self.other = 0                   # frames from other ids, ignored

    # ---- TX ---------------------------------------------------------------- #
    def send(self, payload: bytes, *, grant=None) -> None:
        frames = segment(payload, self.params.pad)
        self.link.send(self._frame(self.tx_id, frames[0]), grant=grant)
        if len(frames) == 1:
            return
        cfs = frames[1:]
        i = 0
        while i < len(cfs):
            bs, st = self._await_cts()
            gap = stmin_seconds(st)
            n = len(cfs) - i if bs == 0 else min(bs, len(cfs) - i)
            for k in range(n):
                if k:
                    self.sleep(gap)
                self.link.send(self._frame(self.tx_id, cfs[i]), grant=grant)
                i += 1

    def _await_cts(self) -> "Tuple[int, int]":
        waits = 0
        deadline = self.clock() + self.params.n_bs
        while True:
            fr = self._recv_until(deadline)
            if fr is None:
                raise IsoTpTimeout("n_bs", "no flow control within N_Bs")
            if fr.error or fr.id != self.rx_id or fr.extended != self.extended:
                self.other += 1
                continue
            if not fr.data or fr.data[0] >> 4 != 3:
                continue
            status = fr.data[0] & 0x0F
            if status == CTS:
                return (fr.data[1] if len(fr.data) > 1 else 0,
                        fr.data[2] if len(fr.data) > 2 else 0)
            if status == WAIT:
                waits += 1
                if waits > self.params.max_wft:
                    raise IsoTpError("max_wft", "too many FC WAIT frames")
                deadline = self.clock() + self.params.n_bs
                continue
            if status == OVFLW:
                raise IsoTpError("overflow", "receiver reported overflow")
            raise IsoTpError("fc_status", f"invalid FC status {status}")

    # ---- RX ---------------------------------------------------------------- #
    def recv(self, timeout: float, *, grant=None) -> "bytes | None":
        """The next whole message from ``rx_id``, or None when none starts in time."""
        asm = Reassembler(self.params.bs)
        deadline = self.clock() + timeout
        while True:
            fr = self._recv_until(deadline)
            if fr is None:
                if asm.active:
                    raise IsoTpTimeout("n_cr", "consecutive frame timeout (N_Cr)")
                return None
            if fr.error or fr.id != self.rx_id or fr.extended != self.extended:
                self.other += 1
                continue
            ev, val = asm.feed(fr.data)
            if ev == "message":
                return val  # type: ignore[return-value]
            if ev == "first" or (ev == "progress" and val):
                self.link.send(self._frame(self.tx_id, fc_bytes(
                    CTS, self.params.bs, self.params.stmin, self.params.pad)), grant=grant)
            if asm.active:
                deadline = self.clock() + self.params.n_cr
            if ev == "aborted":
                raise IsoTpError(f"malformed: {val}", f"ISO-TP message aborted ({val})")


class IsoTpMux(_Base):
    """One functional (or physical) request, many reassemblers keyed by reply id."""

    def __init__(self, link: CanLink, *, extended: bool = False,
                 reply_ok: Callable[[int], bool], fc_id_for: Callable[[int], int],
                 params: "IsoTpParams | None" = None,
                 clock: "Optional[Callable[[], float]]" = None,
                 sleep: "Optional[Callable[[float], None]]" = None) -> None:
        super().__init__(link, extended, params, clock, sleep)
        self.reply_ok = reply_ok
        self.fc_id_for = fc_id_for
        self.dropped = 0                 # frames after an ECU's message, or foreign
        self.aborted: "Dict[int, str]" = {}

    def request(self, payload: bytes, tx_id: int, *, grant=None,
                target: "int | None" = None,
                timeout: "float | None" = None) -> "Dict[int, bytes]":
        """Send ``payload`` as one padded SF and collect one message per ECU."""
        payload = bytes(payload)
        if len(payload) > 7:
            raise IsoTpError("length", "an OBD request is always a single frame")
        p = self.params
        self.link.flush_rx()
        self.link.send(self._frame(tx_id, segment(payload, p.pad)[0]), grant=grant)
        start = self.clock()
        deadline = start + (p.p2 if timeout is None else timeout)
        asm: "Dict[int, Reassembler]" = {}
        cf_due: "Dict[int, float]" = {}
        pending: "Dict[int, float]" = {}
        pend_n: "Dict[int, int]" = {}
        done: "Dict[int, bytes]" = {}
        self.aborted = {}
        while True:
            now = self.clock()
            for rid in [r for r, a in asm.items() if a.active and now >= cf_due[r]]:
                asm[rid].reset()
                self.aborted[rid] = "timeout"
            busy = [cf_due[r] for r, a in asm.items() if a.active]
            limit = max([deadline, *pending.values(), *busy])
            if target is not None and target in done:
                break
            if now >= limit:
                break
            fr = self.link.recv(limit - now)
            if fr is None:
                continue
            if fr.error or fr.extended != self.extended or not self.reply_ok(fr.id):
                continue
            if fr.id in done:
                self.dropped += 1
                continue
            a = asm.setdefault(fr.id, Reassembler(p.bs))
            ev, val = a.feed(fr.data)
            if ev == "first" or (ev == "progress" and val):
                self.link.send(self._frame(self.fc_id_for(fr.id),
                                           fc_bytes(CTS, p.bs, p.stmin, p.pad)), grant=grant)
            if a.active:
                cf_due[fr.id] = self.clock() + p.n_cr
            if ev == "aborted":
                self.aborted[fr.id] = f"malformed: {val}"
            elif ev == "message":
                msg: bytes = val  # type: ignore[assignment]
                if len(msg) >= 3 and msg[0] == 0x7F and msg[1] == payload[0] and msg[2] == 0x78:
                    pend_n[fr.id] = pend_n.get(fr.id, 0) + 1
                    if pend_n[fr.id] <= p.max_pending:
                        pending[fr.id] = self.clock() + p.p2_star
                    continue
                pending.pop(fr.id, None)
                done[fr.id] = msg
        return done


class IsoTpSniffer:
    """Reassembles both directions of someone else's session; never sends (listen-only)."""

    def __init__(self) -> None:
        self._asm: "Dict[Tuple[int, bool], Reassembler]" = {}
        self.aborted = 0

    def feed(self, frame: CanFrame) -> "Tuple[int, bool, bytes] | None":
        if frame.error:
            return None
        key = (frame.id, frame.extended)
        ev, val = self._asm.setdefault(key, Reassembler()).feed(frame.data)
        if ev == "aborted":
            self.aborted += 1
        if ev == "message":
            return (frame.id, frame.extended, val)  # type: ignore[return-value]
        return None

    def run(self, link: CanLink, duration: float) -> "List[Tuple[int, bool, bytes]]":
        out: "List[Tuple[int, bool, bytes]]" = []
        deadline = link.clock() + duration
        while True:
            left = deadline - link.clock()
            if left <= 0:
                return out
            fr = link.recv(left)
            if fr is not None:
                got = self.feed(fr)
                if got is not None:
                    out.append(got)


# ---- Linux kernel CAN_ISOTP (optional, SocketCAN only) ------------------------ #
SOL_CAN_ISOTP = 106             # SOL_CAN_BASE (100) + CAN_ISOTP (6), linux/can/isotp.h
CAN_ISOTP_OPTS, CAN_ISOTP_RECV_FC = 1, 2
CAN_ISOTP_LISTEN_MODE, CAN_ISOTP_TX_PADDING, CAN_ISOTP_RX_PADDING = 0x001, 0x004, 0x008
CAN_EFF_FLAG = 0x80000000


class KernelIsoTpChannel:
    """A physical channel on the kernel's ``CAN_ISOTP`` (Linux ≥ 5.10). The kernel then
    times CFs and sends FCs itself, so opening one goes through the gate: its tx id must
    be a Tier 0 diagnostic id or allowlisted; payloads pass the gate before ``send()``."""

    def __init__(self, link, tx_id: int, rx_id: int, *, extended: bool = False,
                 params: "IsoTpParams | None" = None, listen: bool = False, grant=None,
                 sock_factory: "Optional[Callable[..., object]]" = None) -> None:
        from .gate import is_diag_request_id
        self.link, self.tx_id, self.rx_id = link, tx_id, rx_id
        self.extended, self.params = extended, params or IsoTpParams()
        self.listen = listen
        if not listen and not link.rate_confirmed:
            from .link import RateNotConfirmed
            raise RateNotConfirmed()
        if not listen and not is_diag_request_id(tx_id, extended):
            gate = link._gate()
            if not any(e.id == tx_id and e.extended == extended for e in gate._entries):
                raise TxRefused("not_allowlisted", "kernel ISO-TP tx id is neither a "
                                                   "diagnostic id nor allowlisted")
        factory = sock_factory or socket.socket
        proto = getattr(socket, "CAN_ISOTP", None)
        if proto is None:
            raise CanError("CAN_ISOTP is not available on this platform")
        self.sock = factory(socket.AF_CAN, socket.SOCK_DGRAM, proto)
        flags = CAN_ISOTP_TX_PADDING | CAN_ISOTP_RX_PADDING
        if listen:
            flags |= CAN_ISOTP_LISTEN_MODE
        p = self.params
        self.sock.setsockopt(SOL_CAN_ISOTP, CAN_ISOTP_OPTS,  # type: ignore[attr-defined]
                             struct.pack("=IIBBBB", flags, 0, 0, p.pad, p.pad, 0))
        self.sock.setsockopt(SOL_CAN_ISOTP, CAN_ISOTP_RECV_FC,  # type: ignore[attr-defined]
                             struct.pack("=BBB", p.bs, p.stmin, p.max_wft))
        flag = CAN_EFF_FLAG if extended else 0
        self.sock.bind((link.channel, rx_id | flag, tx_id | flag))  # type: ignore[attr-defined]

    def send(self, payload: bytes, *, grant=None) -> None:
        from .gate import TIER0
        if self.listen:
            raise TxRefused("listen_only", "a listen-mode ISO-TP socket never sends")
        first = segment(payload, self.params.pad)[0]
        self.link._gate().check(CanFrame(self.tx_id, self.extended, first),
                                TIER0 if grant is None else grant,
                                rate_ok=self.link.rate_confirmed, link_kind=self.link.caps.kind)
        self.sock.send(bytes(payload))  # type: ignore[attr-defined]

    def recv(self, timeout: float) -> "bytes | None":
        self.sock.settimeout(timeout)  # type: ignore[attr-defined]
        try:
            return bytes(self.sock.recv(MAX_LEN))  # type: ignore[attr-defined]
        except socket.timeout:
            return None

    def close(self) -> None:
        self.sock.close()  # type: ignore[attr-defined]


__all__ = ["IsoTpParams", "IsoTpChannel", "IsoTpMux", "IsoTpSniffer", "KernelIsoTpChannel",
           "Reassembler", "IsoTpError", "IsoTpTimeout", "segment", "fc_bytes",
           "stmin_seconds", "precise_wait", "CTS", "WAIT", "OVFLW"]
