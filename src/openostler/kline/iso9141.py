# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A thin ISO 9141-2 session on a profile-built :class:`KLine` (spec K-line profiles §3–4).

``request(data)`` sends ``68 6A F1 … cs`` and returns the verified reply frames;
``keepalive_if_due()`` sends the profile's ``01 00`` request when nothing went out for the
keep-alive interval (ISO 9141-2 has no TesterPresent); ``release()`` sends nothing, since
ISO 9141-2 has no StopCommunication: the session is left *abandoned* and the next init
waits P3max. J1979 services on top of it are U4's.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .kline import KLine, KLineError

if TYPE_CHECKING:  # pragma: no cover
    from .frame_iso9141 import Iso9141Frame


class Iso9141Session:
    def __init__(self, kline: KLine) -> None:
        if kline.profile is None or kline.profile.framing != "iso9141":
            raise ValueError("Iso9141Session needs a KLine built from an iso9141 profile")
        self._k = kline
        self.profile = kline.profile

    def init(self):
        """5-baud init with the profile's address; → the :class:`SlowInitReply`."""
        return self._k.slow_init_reply()

    def request(self, data: bytes) -> "list[Iso9141Frame]":
        return self._k.request_iso9141(data)

    def keepalive_if_due(self) -> bool:
        """Send ``profile.keepalive`` when ``now - last_tx >= keepalive_interval``. A
        failed keep-alive is logged, never raised. → True when one was sent."""
        p = self.profile
        if p.keepalive is None:
            return False
        last = self._k.last_tx
        if last is not None and self._k.now() - last < p.keepalive_interval:
            return False
        try:
            frames = self._k.request_iso9141(p.keepalive)
            ok, err = bool(frames), (None if frames else "no reply")
        except (KLineError, ValueError) as exc:
            ok, err = False, f"{type(exc).__name__}: {exc}"
        self._k.emit("keepalive", ok=ok, error=err, frame=p.keepalive.hex(" "))
        return True

    def release(self) -> None:
        """ISO 9141-2 has no release frame: send nothing, mark the session abandoned."""
        self._k.mark_released(False)
        self._k.emit("release", confirmed=False, sent=None)

    def close(self) -> None:
        self._k.close()


__all__ = ["Iso9141Session"]
