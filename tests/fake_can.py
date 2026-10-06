# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""An in-memory CAN bus with a virtual clock (CanLink spec §9). No hardware, no threads.

- :class:`FakeCanBus`: a bus at one bitrate. Links attach with their own configured rate;
  **a link at the wrong rate receives only error frames** (and its RX error counter
  grows); a listen-only link never puts a frame on the bus (asserted); every transmitted
  frame is recorded with its sender.
- :class:`FakeCanLink`: a :class:`CanLink` on the bus with chosen :class:`LinkCaps`.
- :class:`FakeObdEcu`: answers J1979 requests over ISO-TP, honours FC (BS, STmin, WAIT),
  and can reply late, drop a CF or send ``7F xx 78`` first.
- :class:`FakeIsoTpPeer`: receives a tester's multi-frame message with a scripted FC
  sequence (T10).

Time only moves when a link waits (``recv``) or someone calls :meth:`FakeCanBus.sleep`.
"""
from __future__ import annotations

import heapq
import itertools
from collections import deque
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

from openostler.can.frame import CanFrame, pad
from openostler.can.isotp import segment, stmin_seconds
from openostler.can.link import CanLink, LinkCaps, OneShotResult

FRAME_TIME = 0.0003            # one 8-byte frame at 500 kbit/s is ~0.23 ms


class FakeCanBus:
    def __init__(self, bitrate: "int | None" = 500_000, start: float = 0.0) -> None:
        self.bitrate = bitrate
        self.t = float(start)
        self._q: "list" = []
        self._seq = itertools.count()
        self.links: "List[FakeCanLink]" = []
        self.nodes: "list" = []
        self.transmitted: "List[Tuple[float, str, CanFrame]]" = []

    # ---- time -------------------------------------------------------------- #
    def now(self) -> float:
        return self.t

    __call__ = now

    def sleep(self, s: float) -> None:
        self.run_until(self.t + max(0.0, s))

    def at(self, t: float, fn: Callable[[], None]) -> None:
        heapq.heappush(self._q, (t, next(self._seq), fn))

    def run_until(self, t: float, stop: "Optional[Callable[[], bool]]" = None) -> None:
        while self._q and self._q[0][0] <= t:
            when, _s, fn = heapq.heappop(self._q)
            self.t = max(self.t, when)
            fn()
            if stop is not None and stop():
                return
        self.t = max(self.t, t)

    # ---- the wire ---------------------------------------------------------- #
    def _participants(self, sender) -> bool:
        return bool([n for n in self.nodes if n is not sender]) or any(
            ln is not sender and ln.rate is not None for ln in self.links)

    def put(self, frame: CanFrame, sender, *, delay: float = FRAME_TIME) -> None:
        """A node (traffic, an ECU) puts a frame on the bus after ``delay``."""
        self.at(self.t + delay, lambda: self._deliver(frame, sender))

    def _deliver(self, frame: CanFrame, sender) -> None:
        frame = CanFrame(frame.id, frame.extended, frame.data, ts=self.t)
        self.transmitted.append((self.t, getattr(sender, "name", "?"), frame))
        for ln in self.links:
            if ln is sender or ln.rate is None:
                continue
            ln._hear(frame if ln.rate == self.bitrate else None)
        for n in list(self.nodes):
            if n is not sender:
                n.on_frame(frame)

    def transmit(self, sender: "FakeCanLink", frame: CanFrame) -> "Tuple[bool, bool]":
        """A link transmits. → ``(acked, error)``."""
        assert not sender.hw_listen_only, "a listen-only link put a frame on the bus"
        if sender.rate != self.bitrate:
            if self._participants(sender):
                sender.tec += 8
                sender._hear(None)
                for ln in self.links:
                    if ln is not sender and ln.rate is not None:
                        ln._hear(None)
                return (False, True)
            return (False, False)
        acked = bool(self.nodes) or any(ln is not sender and ln.rate == self.bitrate
                                        and not ln.hw_listen_only for ln in self.links)
        self.at(self.t + FRAME_TIME, lambda: self._deliver(frame, sender))
        return (acked, False)

    def tester_frames(self, name: str = "tester") -> "List[Tuple[float, CanFrame]]":
        return [(t, f) for t, s, f in self.transmitted if s == name]

    # ---- traffic ----------------------------------------------------------- #
    def periodic(self, can_id: int, data: bytes = b"\x00" * 8, period: float = 0.010, *,
                 extended: bool = False, count: "int | None" = None,
                 start: "float | None" = None) -> "Traffic":
        tr = Traffic(self, CanFrame(can_id, extended, data), period, count)
        self.nodes.append(tr)
        tr.start(self.t if start is None else start)
        return tr

    def error_at(self, t: float) -> None:
        """An error frame (a glitch) at ``t`` that every open link hears."""
        def fire() -> None:
            for ln in self.links:
                if ln.rate is not None:
                    ln._hear(None)
        self.at(t, fire)


class Traffic:
    """A periodic sender (another ECU's broadcast)."""

    name = "traffic"

    def __init__(self, bus: FakeCanBus, frame: CanFrame, period: float,
                 count: "int | None") -> None:
        self.bus, self.frame, self.period, self.left = bus, frame, period, count

    def start(self, t: float) -> None:
        self.bus.at(t, self._tick)

    def _tick(self) -> None:
        if self.left is not None:
            if self.left <= 0:
                return
            self.left -= 1
        self.bus._deliver(self.frame, self)
        self.bus.at(self.bus.t + self.period, self._tick)

    def on_frame(self, frame: CanFrame) -> None:
        pass


class FakeCanLink(CanLink):
    def __init__(self, bus: FakeCanBus, *, caps: "LinkCaps | None" = None, gate=None,
                 name: str = "tester", channel: str = "can0") -> None:
        super().__init__(gate=gate, channel=channel, clock=bus.now)
        self.bus = bus
        self.name = name
        self.caps = caps or LinkCaps(kind="fake", one_shot=True, err_counters=True)
        self._rx: "deque[CanFrame]" = deque()
        self.rate: "int | None" = None
        self.hw_listen_only = True
        self.hw_one_shot = False
        self.tec = self.rec = 0
        self.opens: "List[Tuple[int | None, bool, bool]]" = []
        self.filters: "list" = []
        bus.links.append(self)

    def _hear(self, frame: "CanFrame | None") -> None:
        if frame is None:
            self.rec += 8
            if self.caps.error_frames is True:
                self._rx.append(CanFrame(0, False, b"", ts=self.bus.t, error=True))
            return
        self._rx.append(frame)

    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None:
        self.rate = bitrate
        self.hw_listen_only = listen_only
        self.hw_one_shot = one_shot
        self.opens.append((bitrate, listen_only, one_shot))

    def _hw_close(self) -> None:
        self.rate = None
        self._rx.clear()

    def _hw_recv(self, timeout):
        if not self._rx:
            until = self.bus.t + (timeout if timeout is not None else 3600.0)
            self.bus.run_until(until, stop=lambda: bool(self._rx))
        return self._rx.popleft() if self._rx else None

    def _hw_send(self, frame: CanFrame) -> None:
        self.bus.transmit(self, frame)

    def _hw_oneshot(self, frame: CanFrame, timeout: float) -> OneShotResult:
        acked, error = self.bus.transmit(self, frame)
        replies: "List[CanFrame]" = []
        end = self.bus.t + timeout
        while True:
            fr = self._hw_recv(end - self.bus.t) if end > self.bus.t else None
            if fr is None:
                break
            if fr.error:
                error = True
            replies.append(fr)
        return OneShotResult(acked and not error, error, tuple(replies))

    def set_filters(self, filters) -> None:
        self.filters = list(filters)

    def flush_rx(self) -> int:
        n = len(self._rx)
        self._rx.clear()
        return n

    def error_counters(self):
        return (self.tec, self.rec) if self.caps.err_counters else None


Reply = Union[str, bytes, Sequence[str], Callable[[int], object], None]


def _b(x: "str | bytes") -> bytes:
    return bytes.fromhex(x) if isinstance(x, str) else bytes(x)


class FakeObdEcu:
    """A J1979 ECU on the bus answering over ISO-TP. ``reply_id`` is ``0x7E8`` (11-bit)
    or ``0x18DAF110`` (29-bit). ``responses`` maps a request payload (hex) to the reply
    message (hex), or a callable(count). It pads with ``0xAA`` to show RX ignores pads."""

    def __init__(self, bus: FakeCanBus, reply_id: int, responses: "Dict[str, Reply]", *,
                 extended: bool = False, delay: float = 0.005, stmin: int = 0, bs: int = 0,
                 drop_cf: "int | None" = None, bad_sn_at: "int | None" = None,
                 pending: int = 0, pending_gap: float = 1.0,
                 late: "Dict[str, float] | None" = None, name: "str | None" = None) -> None:
        self.bus, self.reply_id, self.extended = bus, reply_id, extended
        self.responses = {_b(k): v for k, v in responses.items()}
        self.delay, self.stmin, self.bs = delay, stmin, bs
        self.drop_cf, self.bad_sn_at = drop_cf, bad_sn_at
        self.pending, self.pending_gap = pending, pending_gap
        self.late = {_b(k): v for k, v in (late or {}).items()}
        self.name = name or f"ecu{reply_id:X}"
        self.phys = (0x18DA00F1 | ((reply_id & 0xFF) << 8)) if extended else reply_id - 8
        self.func = 0x18DB33F1 if extended else 0x7DF
        self.requests: "List[bytes]" = []
        self.fcs: "List[bytes]" = []
        self._counts: "Dict[bytes, int]" = {}
        self._cfs: "List[bytes]" = []
        self._sent_cf = 0
        bus.nodes.append(self)

    def _put(self, data: bytes, delay: float) -> None:
        self.bus.put(CanFrame(self.reply_id, self.extended, data), self, delay=delay)

    def on_frame(self, frame: CanFrame) -> None:
        if frame.error or frame.extended != self.extended or frame.id not in (self.func, self.phys):
            return
        d = frame.data
        pci = d[0] >> 4 if d else -1
        if pci == 0:
            payload = d[1:1 + (d[0] & 0x0F)]
            self.requests.append(payload)
            self._answer(payload)
        elif pci == 3 and frame.id == self.phys and self._cfs:
            self.fcs.append(d[:3])
            self._on_fc(d)

    def _answer(self, payload: bytes) -> None:
        rep = self.responses.get(payload)
        if callable(rep):
            n = self._counts.get(payload, 0)
            self._counts[payload] = n + 1
            rep = rep(n)
        if rep is None:
            return
        msg = _b(rep) if isinstance(rep, (str, bytes)) else _b(" ".join(rep))
        delay = self.late.get(payload, self.delay)
        for i in range(self.pending):
            self._put(pad(bytes([3, 0x7F, payload[0], 0x78]), 0xAA),
                      delay + i * self.pending_gap)
        delay += self.pending * self.pending_gap
        frames = segment(msg, 0xAA)
        if len(frames) == 1:
            self._put(frames[0], delay)
            return
        self._cfs = frames[1:]
        self._sent_cf = 0
        self._put(frames[0], delay)

    def _on_fc(self, d: bytes) -> None:
        status, bs, st = d[0] & 0x0F, d[1], d[2]
        if status != 0:
            return
        gap = max(stmin_seconds(st), FRAME_TIME)
        n = len(self._cfs) if bs == 0 else min(bs, len(self._cfs))
        t = FRAME_TIME
        for _ in range(n):
            cf = self._cfs.pop(0)
            idx = self._sent_cf
            self._sent_cf += 1
            if idx == self.drop_cf:
                continue
            if idx == self.bad_sn_at:
                cf = bytes([0x20 | ((cf[0] + 5) & 0x0F)]) + cf[1:]
            self._put(cf, t)
            t += gap


class FakeIsoTpPeer:
    """Receives a tester's multi-frame message on ``rx_id`` and answers each FF and each
    block with the next scripted FC (hex) from ``fc_script`` on ``tx_id``."""

    name = "peer"

    def __init__(self, bus: FakeCanBus, rx_id: int, tx_id: int, fc_script: "List[str]", *,
                 extended: bool = False, fc_delay: float = 0.002) -> None:
        self.bus, self.rx_id, self.tx_id, self.extended = bus, rx_id, tx_id, extended
        self.script = [_b(s) for s in fc_script]
        self.fc_delay = fc_delay
        self.frames: "List[Tuple[float, bytes]]" = []
        self._block = 0
        self._bs = 0
        bus.nodes.append(self)

    def _next_fc(self) -> None:
        if not self.script:
            return
        fc = self.script.pop(0)
        if fc[0] == 0x30:
            self._bs, self._block = fc[1], 0
        self.bus.put(CanFrame(self.tx_id, self.extended, pad(fc, 0xAA)), self,
                     delay=self.fc_delay)
        if fc[0] == 0x31:                         # WAIT: the next FC follows on its own
            self.bus.at(self.bus.t + self.fc_delay + 0.001, self._next_fc)

    def on_frame(self, frame: CanFrame) -> None:
        if frame.id != self.rx_id or frame.extended != self.extended:
            return
        self.frames.append((self.bus.t, frame.data))
        pci = frame.data[0] >> 4
        if pci == 1:
            self._next_fc()
        elif pci == 2 and self._bs:
            self._block += 1
            if self._block >= self._bs:
                self._next_fc()


class FakeSlcanDevice:
    """A LAWICEL adapter on the bus, seen through its byte stream (T7): it reports bus
    errors only as ``F`` status flags, never as frames. Pass it to ``SlcanLink`` as the
    stream; ``read`` advances the bus clock."""

    SPEED = {"S5": 250_000, "S6": 500_000}

    def __init__(self, bus: FakeCanBus, name: str = "tester") -> None:
        self.bus, self.name = bus, name
        self.rate: "int | None" = None
        self._speed: "int | None" = None
        self.hw_listen_only = True
        self.flags = 0
        self.tec = 0
        self.out = bytearray()
        self.commands: "List[str]" = []
        self._in = b""
        bus.links.append(self)  # type: ignore[arg-type]

    # the bus side (duck-typed like FakeCanLink)
    def _hear(self, frame: "CanFrame | None") -> None:
        if frame is None:
            self.flags |= 0x80                   # bus error, reported on the next F
            return
        from openostler.can.slcan import encode_frame
        self.out += encode_frame(frame)

    # the stream side
    def write(self, data: bytes) -> None:
        self._in += data
        while b"\r" in self._in:
            line, _, self._in = self._in.partition(b"\r")
            self._command(line.decode())

    def _command(self, cmd: str) -> None:
        self.commands.append(cmd)
        if cmd in self.SPEED:
            self._speed = self.SPEED[cmd]
        elif cmd == "C":
            self.rate = None
        elif cmd in ("L", "O"):
            self.rate, self.hw_listen_only = self._speed, cmd == "L"
        elif cmd == "F":
            self.out += f"F{self.flags:02X}\r".encode()
            self.flags = 0
            return
        elif cmd[:1] in ("t", "T"):
            from openostler.can.slcan import decode_line
            fr = decode_line(cmd)
            if fr is not None:
                self.bus.transmit(self, fr)      # type: ignore[arg-type]
            self.out += b"z\r"
            return
        self.out += b"\r"

    def read(self, timeout: float) -> bytes:
        if not self.out:
            self.bus.run_until(self.bus.t + timeout, stop=lambda: bool(self.out))
        data, self.out = bytes(self.out), bytearray()
        return data
