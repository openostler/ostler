# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SocketCAN on the stdlib (``socket.AF_CAN``, ``CAN_RAW``; Linux, CanLink spec §3).

- :class:`SocketCanLink` opens a raw socket with ``CAN_RAW_ERR_FILTER = CAN_ERR_MASK`` so
  error frames arrive as frames (``error=True``), ``CAN_RAW_FILTER`` for acceptance
  filters, and ``CAN_RAW_RECV_OWN_MSGS`` only for the one-shot probe, whose TX
  confirmation (``MSG_CONFIRM``) is the ACK.
- :class:`CanIfControl` sets bitrate, ``listen-only``, ``one-shot``, ``berr-reporting``
  and ``restart-ms`` with iproute2 (``ip link set …``; needs ``CAP_NET_ADMIN``, granted by
  the systemd unit's ``AmbientCapabilities``) and reads ``ip -details -json link show``
  to learn the interface kind and the ctrlmodes the driver supports. On ``vcan`` there is
  no bitrate or ctrlmode: ``set_bitrate`` and ``listen_only`` are false and the rate must
  be declared.

Lab/dev path (spec §7.1): production CAN I/O is the node's TWAI controller.
"""
from __future__ import annotations

import json
import select
import socket
import struct
import subprocess
import time
from typing import Callable, List, Optional, Sequence, Tuple

from .frame import CanFrame
from .link import CanError, CanLink, LinkCaps, OneShotResult

CAN_EFF_FLAG, CAN_RTR_FLAG, CAN_ERR_FLAG = 0x80000000, 0x40000000, 0x20000000
CAN_EFF_MASK, CAN_SFF_MASK, CAN_ERR_MASK = 0x1FFFFFFF, 0x7FF, 0x1FFFFFFF
CAN_ERR_CNT = 0x200                     # data[6] = TX error counter, data[7] = RX
SOL_CAN_RAW = getattr(socket, "SOL_CAN_RAW", 101)
CAN_RAW_FILTER = getattr(socket, "CAN_RAW_FILTER", 1)
CAN_RAW_ERR_FILTER = getattr(socket, "CAN_RAW_ERR_FILTER", 2)
CAN_RAW_RECV_OWN_MSGS = getattr(socket, "CAN_RAW_RECV_OWN_MSGS", 4)
MSG_CONFIRM = getattr(socket, "MSG_CONFIRM", 0x800)
FRAME_FMT = "=IB3x8s"
FRAME_SIZE = struct.calcsize(FRAME_FMT)  # 16
ARPHRD_CAN = 280


def pack_frame(frame: CanFrame) -> bytes:
    can_id = frame.id | (CAN_EFF_FLAG if frame.extended else 0)
    return struct.pack(FRAME_FMT, can_id, len(frame.data), frame.data.ljust(8, b"\x00"))


def unpack_frame(raw: bytes, ts: float = 0.0, channel: str = "") -> CanFrame:
    can_id, dlc, data = struct.unpack(FRAME_FMT, raw[:FRAME_SIZE])
    dlc = min(dlc, 8)
    if can_id & CAN_ERR_FLAG:
        return CanFrame(can_id & CAN_ERR_MASK, False, data[:dlc], ts=ts, error=True,
                        channel=channel)
    ext = bool(can_id & CAN_EFF_FLAG)
    return CanFrame(can_id & (CAN_EFF_MASK if ext else CAN_SFF_MASK), ext, data[:dlc],
                    ts=ts, channel=channel)


def pack_filters(filters: "Sequence[Tuple[int, int, bool]]") -> bytes:
    out = b""
    for can_id, mask, ext in filters:
        flag = CAN_EFF_FLAG if ext else 0
        out += struct.pack("=II", can_id | flag, mask | CAN_EFF_FLAG)
    return out


class CanIfControl:
    """iproute2 control of one SocketCAN interface (open question 3: ``ip`` now)."""

    def __init__(self, ifname: str, *, run: "Optional[Callable[..., object]]" = None,
                 ip: str = "ip") -> None:
        self.ifname = ifname
        self._run = run or (lambda argv: subprocess.run(argv, check=True, capture_output=True,
                                                        text=True, timeout=5))
        self.ip = ip
        self.commands: "List[List[str]]" = []

    def _call(self, *args: str) -> str:
        argv = [self.ip, *args]
        self.commands.append(argv)
        out = self._run(argv)
        return getattr(out, "stdout", "") or ""

    def details(self) -> dict:
        try:
            doc = json.loads(self._call("-details", "-json", "link", "show", "dev", self.ifname))
        except (OSError, ValueError, subprocess.SubprocessError):
            return {}
        return doc[0] if isinstance(doc, list) and doc else {}

    def caps(self) -> LinkCaps:
        d = self.details()
        info = d.get("linkinfo", {})
        kind = info.get("info_kind")
        if kind == "vcan":
            return LinkCaps(kind="socketcan", listen_only=False, set_bitrate=False,
                            one_shot=False, error_frames=True, err_counters=False)
        if kind != "can":
            # Unknown (no iproute2, or not a CAN device): report, never assume.
            return LinkCaps(kind="socketcan", listen_only=False, set_bitrate=False,
                            one_shot=False, error_frames=True, err_counters=False)
        data = info.get("info_data", {})
        supported = {m.upper() for m in data.get("ctrlmode_supported", [])}
        return LinkCaps(kind="socketcan", listen_only="LISTEN-ONLY" in supported,
                        set_bitrate=True, one_shot="ONE-SHOT" in supported,
                        error_frames=True, err_counters="berr_counter" in data)

    def configure(self, bitrate: "int | None", *, listen_only: bool, one_shot: bool,
                  berr: bool = True, restart_ms: int = 0) -> None:
        self._call("link", "set", self.ifname, "down")
        args = ["link", "set", self.ifname, "type", "can"]
        if bitrate:
            args += ["bitrate", str(bitrate)]
        args += ["listen-only", "on" if listen_only else "off",
                 "one-shot", "on" if one_shot else "off",
                 "berr-reporting", "on" if berr else "off", "restart-ms", str(restart_ms)]
        self._call(*args)
        self._call("link", "set", self.ifname, "up")

    def error_counters(self) -> "Tuple[int, int] | None":
        bc = self.details().get("linkinfo", {}).get("info_data", {}).get("berr_counter")
        return (int(bc.get("tx", 0)), int(bc.get("rx", 0))) if bc else None


class SocketCanLink(CanLink):
    def __init__(self, ifname: str = "can0", *, gate=None,
                 ifcontrol: "CanIfControl | None | bool" = None,
                 sock_factory: "Optional[Callable[..., object]]" = None,
                 clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__(gate=gate, channel=ifname, clock=clock)
        self.ifc = CanIfControl(ifname) if ifcontrol is None else (ifcontrol or None)
        self.caps = self.ifc.caps() if isinstance(self.ifc, CanIfControl) else \
            LinkCaps(kind="socketcan", listen_only=False, set_bitrate=False, one_shot=False)
        self._factory = sock_factory or socket.socket
        self.sock = None
        self._select = select.select           # replaceable in tests (no AF_CAN in CI)
        self._tec_rec: "Tuple[int, int] | None" = None

    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None:
        if self.ifc is not None and self.caps.set_bitrate:
            self.ifc.configure(bitrate, listen_only=listen_only and bool(self.caps.listen_only),
                               one_shot=one_shot and self.caps.one_shot)
            self._drop_socket()
        if self.sock is None:
            af = getattr(socket, "AF_CAN", None)
            if af is None:
                raise CanError("SocketCAN needs Linux (socket.AF_CAN)")
            s = self._factory(af, socket.SOCK_RAW, getattr(socket, "CAN_RAW", 1))
            s.setsockopt(SOL_CAN_RAW, CAN_RAW_ERR_FILTER, struct.pack("=I", CAN_ERR_MASK))
            s.bind((self.channel,))
            self.sock = s
        self.sock.setsockopt(SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS,  # type: ignore[attr-defined]
                             struct.pack("=i", 1 if one_shot else 0))

    def _drop_socket(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()  # type: ignore[attr-defined]
            finally:
                self.sock = None

    def _hw_close(self) -> None:
        self._drop_socket()

    def _read(self, timeout: "float | None") -> "Tuple[CanFrame, int] | None":
        if timeout is not None:
            r, _w, _x = self._select([self.sock], [], [], max(0.0, timeout))
            if not r:
                return None
        raw, _anc, flags, _addr = self.sock.recvmsg(FRAME_SIZE)  # type: ignore[attr-defined]
        fr = unpack_frame(raw, time.time(), self.channel)
        if fr.error and fr.id & CAN_ERR_CNT and len(fr.data) >= 8:
            self._tec_rec = (fr.data[6], fr.data[7])
        return fr, flags

    def _hw_recv(self, timeout):
        got = self._read(timeout)
        return got[0] if got else None

    def _hw_send(self, frame: CanFrame) -> None:
        self.sock.send(pack_frame(frame))  # type: ignore[attr-defined]

    def _hw_oneshot(self, frame: CanFrame, timeout: float) -> OneShotResult:
        self.sock.send(pack_frame(frame))  # type: ignore[attr-defined]
        acked = error = False
        replies: "List[CanFrame]" = []
        end = self.clock() + timeout
        while True:
            got = self._read(end - self.clock())
            if got is None:
                break
            fr, flags = got
            if fr.error:
                error = True
            elif flags & MSG_CONFIRM and fr.id == frame.id and fr.data == frame.data:
                acked = True
            else:
                replies.append(fr)
        return OneShotResult(acked and not error, error, tuple(replies))

    def set_filters(self, filters) -> None:
        self.sock.setsockopt(SOL_CAN_RAW, CAN_RAW_FILTER,  # type: ignore[attr-defined]
                             pack_filters(filters))

    def flush_rx(self) -> int:
        n = 0
        while self.sock is not None and self._read(0.0) is not None:
            n += 1
        return n

    def error_counters(self):
        if self.ifc is not None and self.caps.err_counters:
            return self.ifc.error_counters()
        return self._tec_rec


__all__ = ["SocketCanLink", "CanIfControl", "pack_frame", "unpack_frame", "pack_filters",
           "ARPHRD_CAN", "CAN_EFF_FLAG", "CAN_ERR_FLAG", "CAN_ERR_MASK"]
