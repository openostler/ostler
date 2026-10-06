# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""slcan / LAWICEL over pyserial or a TCP socket (CanLink spec §3).

Serial: the ESP32 node or a CANable in slcan mode. TCP: the WiCAN Pro on port 3333,
which ships in ``normal`` mode (set ``silent`` and disable MQTT TX first, spec §10); its
listen-only state cannot be verified over slcan, so the link reports
``listen_only: "requested"``.

Commands: ``C`` close, ``S5``/``S6`` 250k/500k, ``Z1`` timestamps, ``L`` open listen-only
or ``O`` open, ``tIIIL…``/``TIIIIIIIIL…`` frames, ``F`` status flags. LAWICEL has no
error frames: while ``poll_flags`` is set the link sends ``F`` every 200 ms and turns a
bus-error, error-passive or data-overrun flag into an error frame
(``caps.error_frames = "flags"``, weaker evidence than a real error frame; spec §4).

Lab/dev path (spec §7.1).
"""
from __future__ import annotations

import socket
import time
from collections import deque
from typing import Callable, Deque, List, Tuple

from .frame import CanFrame
from .link import CanError, CanLink, LinkCaps

SPEEDS = {10_000: "S0", 20_000: "S1", 50_000: "S2", 100_000: "S3", 125_000: "S4",
          250_000: "S5", 500_000: "S6", 800_000: "S7", 1_000_000: "S8"}
# F status bits: 0 RX FIFO full, 1 TX FIFO full, 2 error warning, 3 data overrun,
# 5 error passive, 6 arbitration lost, 7 bus error.
FLAG_OVERRUN, FLAG_PASSIVE, FLAG_BUS_ERROR = 0x08, 0x20, 0x80
ERROR_FLAGS = FLAG_OVERRUN | FLAG_PASSIVE | FLAG_BUS_ERROR
POLL_S = 0.2


class TcpStream:
    def __init__(self, host: str, port: int = 3333, timeout: float = 3.0) -> None:
        self.sock = socket.create_connection((host, port), timeout=timeout)

    def write(self, data: bytes) -> None:
        self.sock.sendall(data)

    def read(self, timeout: float) -> bytes:
        self.sock.settimeout(max(timeout, 0.0001))
        try:
            return self.sock.recv(4096)
        except socket.timeout:
            return b""

    def close(self) -> None:
        self.sock.close()


class SerialStream:
    def __init__(self, port: str, baud: int = 115200) -> None:
        import serial  # pyserial, the one runtime dependency

        self.ser = serial.Serial(port, baud, timeout=0)

    def write(self, data: bytes) -> None:
        self.ser.write(data)

    def read(self, timeout: float) -> bytes:
        self.ser.timeout = max(timeout, 0.0)
        first = self.ser.read(1)
        return first + self.ser.read(self.ser.in_waiting) if first else b""

    def close(self) -> None:
        self.ser.close()


def open_stream(spec: str):
    """``tcp://host[:port]`` → :class:`TcpStream`; anything else is a serial port."""
    if spec.startswith("tcp://"):
        host, _, port = spec[6:].partition(":")
        return TcpStream(host, int(port or 3333))
    return SerialStream(spec)


def encode_frame(frame: CanFrame) -> bytes:
    data = frame.data.hex().upper()
    if frame.extended:
        return f"T{frame.id:08X}{len(frame.data)}{data}\r".encode()
    return f"t{frame.id:03X}{len(frame.data)}{data}\r".encode()


def decode_line(line: str, ts: float = 0.0) -> "CanFrame | None":
    """A ``t``/``T`` line (with or without the ``Z1`` 4-hex timestamp) → a frame."""
    if not line or line[0] not in "tT":
        return None
    ext = line[0] == "T"
    n = 8 if ext else 3
    try:
        can_id = int(line[1:1 + n], 16)
        dlc = int(line[1 + n], 16)
        data = bytes.fromhex(line[2 + n:2 + n + 2 * dlc])
    except (ValueError, IndexError):
        return None
    if len(data) != dlc or dlc > 8:
        return None
    return CanFrame(can_id, ext, data, ts=ts)


class SlcanLink(CanLink):
    def __init__(self, stream, *, gate=None, tcp: "bool | None" = None, channel: str = "slcan0",
                 clock: Callable[[], float] = time.monotonic, poll_flags: bool = True,
                 cmd_timeout: float = 0.5) -> None:
        super().__init__(gate=gate, channel=channel, clock=clock)
        if isinstance(stream, str):
            tcp = stream.startswith("tcp://") if tcp is None else tcp
            stream = open_stream(stream)
        tcp = bool(tcp)
        self.stream = stream
        self.caps = LinkCaps(kind="slcan-tcp" if tcp else "slcan",
                             listen_only="requested" if tcp else True, set_bitrate=True,
                             one_shot=False, error_frames="flags", err_counters=False)
        self.poll_flags = poll_flags
        self.cmd_timeout = cmd_timeout
        self._buf = b""
        self._rx: "Deque[CanFrame]" = deque()
        self._replies: "Deque[str]" = deque()
        self._last_poll = -1e9
        self.flags_seen: "List[int]" = []
        self._filters: "List[Tuple[int, int, bool]]" = []

    # ---- line handling --------------------------------------------------------- #
    def _pump(self, timeout: float) -> None:
        chunk = self.stream.read(timeout)
        if not chunk:
            return
        self._buf += chunk
        while True:
            cut = min((i for i in (self._buf.find(b"\r"), self._buf.find(b"\x07")) if i >= 0),
                      default=-1)
            if cut < 0:
                return
            line, sep = self._buf[:cut].decode("ascii", "replace"), self._buf[cut:cut + 1]
            self._buf = self._buf[cut + 1:]
            if sep == b"\x07":
                self._replies.append("\a")
                continue
            fr = decode_line(line, time.time())
            if fr is not None:
                if self._accept(fr):
                    self._rx.append(fr)
            elif line[:1] == "F" and len(line) >= 3:
                try:
                    flags = int(line[1:3], 16)
                except ValueError:
                    continue
                self.flags_seen.append(flags)
                if flags & ERROR_FLAGS:
                    self._rx.append(CanFrame(0, False, bytes([flags]), error=True))
            else:
                self._replies.append(line)

    def _accept(self, fr: CanFrame) -> bool:
        if not self._filters:
            return True
        return any(fr.extended == ext and (fr.id & mask) == (cid & mask)
                   for cid, mask, ext in self._filters)

    def _cmd(self, cmd: str, *, check: bool = True) -> None:
        self._replies.clear()
        self.stream.write(cmd.encode() + b"\r")
        end = self.clock() + self.cmd_timeout
        while not self._replies:
            left = end - self.clock()
            if left <= 0:
                if check:
                    raise CanError(f"slcan: no reply to {cmd!r}")
                return
            self._pump(left)
        if self._replies.popleft() == "\a" and check:
            raise CanError(f"slcan: {cmd!r} refused")

    # ---- CanLink hooks ---------------------------------------------------------- #
    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None:
        if one_shot:
            raise CanError("slcan has no one-shot mode")
        self._cmd("C", check=False)
        if bitrate is not None:
            if bitrate not in SPEEDS:
                raise CanError(f"slcan: no standard speed for {bitrate}")
            self._cmd(SPEEDS[bitrate])
        self._cmd("Z1", check=False)
        self._cmd("L" if listen_only else "O")
        self._last_poll = -1e9

    def _hw_close(self) -> None:
        self._cmd("C", check=False)

    def _hw_recv(self, timeout):
        end = None if timeout is None else self.clock() + timeout
        while True:
            if self.poll_flags and self.clock() - self._last_poll >= POLL_S:
                self._last_poll = self.clock()
                self.stream.write(b"F\r")
            if self._rx:
                return self._rx.popleft()
            left = POLL_S if end is None else end - self.clock()
            if left <= 0:
                return None
            wait = min(left, max(0.0, self._last_poll + POLL_S - self.clock())) \
                if self.poll_flags else left
            self._pump(max(wait, 0.0005))

    def _hw_send(self, frame: CanFrame) -> None:
        self.stream.write(encode_frame(frame))

    def set_filters(self, filters) -> None:
        self._filters = list(filters)       # software filter: LAWICEL masks are chip-specific

    def flush_rx(self) -> int:
        self._pump(0.0)
        n = len(self._rx)
        self._rx.clear()
        return n


__all__ = ["SlcanLink", "TcpStream", "SerialStream", "open_stream", "encode_frame",
           "decode_line", "SPEEDS", "ERROR_FLAGS"]
