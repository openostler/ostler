# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``PythonCanLink``: python-can backends (PCAN, Kvaser, Vector) for desktop dongles that
have no SocketCAN driver (CanLink spec §3).

Optional: python-can (LGPL-3.0) comes only with the ``[can]`` extra and is imported
lazily, here and nowhere else; it is never installed on a Pi, where SocketCAN is stdlib.
Listen-only uses ``BusState.PASSIVE`` where the backend supports it; where it does not,
the link reports ``tx: false`` and never transmits. Lab/dev path (spec §7.1).
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from .frame import CanFrame
from .link import CanError, CanLink, LinkCaps

INSTALL_HINT = "python-can is not installed: pip install 'openostler[can]'"


def _can():
    try:
        import can  # type: ignore[import-not-found]
    except ImportError as exc:
        raise CanError(INSTALL_HINT) from exc
    return can


class PythonCanLink(CanLink):
    def __init__(self, interface: str, channel: str, *, gate=None,
                 clock: Callable[[], float] = time.monotonic, **bus_kwargs) -> None:
        super().__init__(gate=gate, channel=channel, clock=clock)
        self._can = _can()
        self.interface = interface
        self.bus_kwargs = bus_kwargs
        self.bus: "Optional[object]" = None
        self.caps = LinkCaps(kind="python-can", tx=True, listen_only=True, one_shot=False,
                             error_frames=True, err_counters=False)

    def _hw_open(self, bitrate, *, listen_only, one_shot) -> None:
        if one_shot:
            raise CanError("python-can links have no one-shot mode here")
        if self.bus is None:
            kw = dict(self.bus_kwargs)
            if bitrate is not None:
                kw["bitrate"] = bitrate
            self.bus = self._can.Bus(interface=self.interface, channel=self.channel, **kw)
        state = self._can.BusState.PASSIVE if listen_only else self._can.BusState.ACTIVE
        try:
            self.bus.state = state  # type: ignore[attr-defined]
        except Exception:  # backend without listen-only: never transmit on it
            self.caps = LinkCaps(kind="python-can", tx=False, listen_only=False,
                                 one_shot=False, error_frames=True, err_counters=False)

    def _hw_close(self) -> None:
        if self.bus is not None:
            self.bus.shutdown()  # type: ignore[attr-defined]
            self.bus = None

    def _hw_recv(self, timeout):
        msg = self.bus.recv(timeout)  # type: ignore[attr-defined]
        if msg is None:
            return None
        if getattr(msg, "is_error_frame", False):
            return CanFrame(0, False, b"", ts=msg.timestamp, error=True, channel=self.channel)
        return CanFrame(msg.arbitration_id, bool(msg.is_extended_id), bytes(msg.data),
                        ts=msg.timestamp, channel=self.channel)

    def _hw_send(self, frame: CanFrame) -> None:
        self.bus.send(self._can.Message(arbitration_id=frame.id,  # type: ignore[attr-defined]
                                        is_extended_id=frame.extended, data=frame.data))

    def set_filters(self, filters) -> None:
        self.bus.set_filters([{"can_id": c, "can_mask": m, "extended": e}  # type: ignore[attr-defined]
                              for c, m, e in filters] or None)

    def flush_rx(self) -> int:
        n = 0
        while self.bus is not None and self.bus.recv(0) is not None:  # type: ignore[attr-defined]
            n += 1
        return n


__all__ = ["PythonCanLink", "INSTALL_HINT"]
