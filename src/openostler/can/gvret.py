# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GVRET binary protocol (ESP32RET firmware, ESP32-CAN-X2, SavvyCAN-compatible) over
pyserial or a TCP socket (CanLink spec §3).

Numbers checked against ESP32RET (MIT, © 2018 Collin Kidder) at ``ae857ea9``
(``src/gvret_comm.h``, ``gvret_comm.cpp``, ``commbuffer.cpp``); facts only, no code:

- ``E7`` switches the device to binary mode; every command starts ``F1 <cmd>``.
- ``F1 00`` build frame (host → device): id u32 LE (bit 31 = extended), bus, length,
  data, one checksum byte (unchecked, sent as 0).
- ``F1 00`` frame (device → host): micros u32 LE, id u32 LE (bit 31 = extended),
  ``length | bus << 4``, data, a 0 byte.
- ``F1 05`` setup CAN bus: per bus a u32 LE, speed in the low 20 bits; bit 31 = "enable
  and listen-only flags are valid", bit 30 = enabled, bit 29 = listen-only.
- ``F1 09`` keep-alive → ``F1 09 DE AD``.

GVRET reports no error frames and no error counters (``caps.error_frames = False``), and
has no one-shot mode. Lab/dev path (spec §7.1).
"""
from __future__ import annotations

import struct
import time
from collections import deque
from typing import Callable, Deque, List, Tuple

from .frame import CanFrame
from .link import CanError, CanLink, LinkCaps
from .slcan import open_stream

BINARY_MODE = b"\xE7\xE7"
CMD_FRAME, CMD_SETUP, CMD_PARAMS, CMD_KEEPALIVE = 0x00, 0x05, 0x06, 0x09
FLAG_VALID, FLAG_ENABLED, FLAG_LISTEN_ONLY = 0x80000000, 0x40000000, 0x20000000
KEEPALIVE_S = 1.0


def setup_bus(bitrate: int, *, listen_only: bool, enabled: bool = True) -> bytes:
    word = (bitrate & 0xFFFFF) | FLAG_VALID | (FLAG_ENABLED if enabled else 0) | \
        (FLAG_LISTEN_ONLY if listen_only else 0)
    return bytes([0xF1, CMD_SETUP]) + struct.pack("<II", word, 0)   # bus 1 disabled


def build_frame(frame: CanFrame, bus: int = 0) -> bytes:
    cid = frame.id | (0x80000000 if frame.extended else 0)
    return bytes([0xF1, CMD_FRAME]) + struct.pack("<IBB", cid, bus, len(frame.data)) + \
        frame.data + b"\x00"


def parse(buf: bytes) -> "Tuple[List[tuple], bytes]":
    """Cut device output into ``("frame", CanFrame)`` / ``("keepalive",)`` / ``("params",
    bytes)`` items; → (items, the unconsumed tail)."""
    items: "List[tuple]" = []
    i = 0
    while i < len(buf):
        if buf[i] != 0xF1:
            i += 1
            continue
        if i + 1 >= len(buf):
            break
        cmd = buf[i + 1]
        if cmd == CMD_FRAME:
            if i + 11 > len(buf):
                break
            us, cid, lb = struct.unpack_from("<IIB", buf, i + 2)
            n = lb & 0x0F
            end = i + 11 + n + 1
            if n > 8:
                i += 1
                continue
            if end > len(buf):
                break
            ext = bool(cid & 0x80000000)
            items.append(("frame", CanFrame(cid & 0x1FFFFFFF if ext else cid & 0x7FF, ext,
                                            buf[i + 11:i + 11 + n], ts=us / 1e6,
                                            channel=f"can{lb >> 4}")))
            i = end
        elif cmd == CMD_KEEPALIVE:
            if i + 4 > len(buf):
                break
            items.append(("keepalive",))
            i += 4
        elif cmd == CMD_PARAMS:
            if i + 12 > len(buf):
                break
            items.append(("params", bytes(buf[i + 2:i + 12])))
            i += 12
        else:
            i += 2
    return items, bytes(buf[i:])


class GvretLink(CanLink):
    caps = LinkCaps(kind="gvret", listen_only=True, set_bitrate=True, one_shot=False,
                    error_frames=False, err_counters=False)

    def __init__(self, stream, *, gate=None, bus: int = 0, channel: str = "gvret0",
                 clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__(gate=gate, channel=channel, clock=clock)
        self.stream = open_stream(stream) if isinstance(stream, str) else stream
        self.bus = bus
        self._buf = b""
        self._rx: "Deque[CanFrame]" = deque()
        self._last_ka = -1e9
        self.keepalives = 0
        self._filters: "List[Tuple[int, int, bool]]" = []

    def _pump(self, timeout: float) -> None:
        chunk = self.stream.read(timeout)
        if not chunk:
            return
        items, self._buf = parse(self._buf + chunk)
        for it in items:
            if it[0] == "frame":
                fr = it[1]
                if not self._filters or any(fr.extended == e and (fr.id & m) == (c & m)
                                            for c, m, e in self._filters):
                    self._rx.append(fr)
            elif it[0] == "keepalive":
                self.keepalives += 1

    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None:
        if one_shot:
            raise CanError("GVRET has no one-shot mode")
        if bitrate is None:
            raise CanError("GVRET needs a bitrate")
        self.stream.write(BINARY_MODE)
        self.stream.write(setup_bus(bitrate, listen_only=listen_only))

    def _hw_close(self) -> None:
        self.stream.write(bytes([0xF1, CMD_SETUP]) + struct.pack("<II", FLAG_VALID, 0))

    def _hw_recv(self, timeout):
        end = None if timeout is None else self.clock() + timeout
        while True:
            if self.clock() - self._last_ka >= KEEPALIVE_S:
                self._last_ka = self.clock()
                self.stream.write(bytes([0xF1, CMD_KEEPALIVE]))
            if self._rx:
                return self._rx.popleft()
            left = KEEPALIVE_S if end is None else end - self.clock()
            if left <= 0:
                return None
            self._pump(min(left, KEEPALIVE_S))

    def _hw_send(self, frame: CanFrame) -> None:
        self.stream.write(build_frame(frame, self.bus))

    def set_filters(self, filters) -> None:
        self._filters = list(filters)

    def flush_rx(self) -> int:
        self._pump(0.0)
        n = len(self._rx)
        self._rx.clear()
        return n


__all__ = ["GvretLink", "setup_bus", "build_frame", "parse"]
