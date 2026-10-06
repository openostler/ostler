# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""``LoggingCanLink``: wraps any :class:`CanLink` and logs every frame (CanLink spec §8).

It keeps ``LoggingTransport``'s discipline (line-buffered, fsync every 2 s, since power
can be cut in the car) and writes two files, either optional:

- JSONL ``{"ts", "dir", "id", "ext", "dlc", "data", "err"}`` (``dir`` is ``rx`` or ``tx``);
- candump ``(1696600000.123456) can0 7E8#0641000000000000``, which stays parseable.

A stateful scrubber (:class:`~openostler.obd.vin.CanIdentityScrubber`) follows ISO-TP
messages per id and blanks VIN and serial payloads (``49 02``, ``49 04``, ``62 F1 90``,
``62 F1 8C``) across FF and CFs: JSONL holds ``<redacted n bytes>`` and candump holds zero
bytes of the same length (ADR-0036: never recorded by default). Captures stay out of git.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Callable, Optional, TextIO

from ..obd.vin import CanIdentityScrubber, redacted
from .frame import CanFrame
from .link import CanLink


class LoggingCanLink:
    """A :class:`CanLink` decorator; everything it does not log is delegated."""

    def __init__(self, inner: CanLink, *, jsonl: "str | Path | None" = None,
                 candump: "str | Path | None" = None, channel: "str | None" = None,
                 wall: Callable[[], float] = time.time, fsync_interval: float = 2.0) -> None:
        self._inner = inner
        self._channel = channel or inner.channel
        self._wall = wall
        self._paths = (Path(jsonl) if jsonl else None, Path(candump) if candump else None)
        self._fh: "list[Optional[TextIO]]" = [None, None]
        self._fsync_interval = fsync_interval
        self._last_fsync = 0.0
        self._scrub = CanIdentityScrubber()
        self._open_files()

    def _open_files(self) -> None:
        for i, p in enumerate(self._paths):
            if p is not None and self._fh[i] is None:
                self._fh[i] = open(p, "a", buffering=1, encoding="utf-8")

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return getattr(self._inner, name)

    # ---- the logged calls ---------------------------------------------------- #
    def open(self, bitrate, *, listen_only: bool = True) -> None:
        self._open_files()
        self._inner.open(bitrate, listen_only=listen_only)

    def recv(self, timeout):
        fr = self._inner.recv(timeout)
        if fr is not None:
            self._log("rx", fr)
        return fr

    def send(self, frame: CanFrame, *, grant=None) -> None:
        self._inner.send(frame, grant=grant)
        self._log("tx", frame)

    def send_oneshot(self, frame: CanFrame, *, probe, timeout: float = 0.1):
        out = self._inner.send_oneshot(frame, probe=probe, timeout=timeout)
        self._log("tx", frame)
        for fr in out.replies:
            self._log("rx", fr)
        return out

    def close(self) -> None:
        try:
            self._inner.close()
        finally:
            for i, fh in enumerate(self._fh):
                if fh is not None:
                    try:
                        fh.flush()
                        os.fsync(fh.fileno())
                    except OSError:
                        pass
                    fh.close()
                    self._fh[i] = None

    # ---- writing -------------------------------------------------------------- #
    def _log(self, direction: str, fr: CanFrame) -> None:
        ts = self._wall()
        data: "bytes | None" = fr.data
        if not fr.error:
            data = self._scrub.scrub(fr.id | (0x80000000 if fr.extended else 0), fr.data)
        ident = fr.id_text if not fr.error else "ERR"
        jfh, cfh = self._fh
        if jfh is not None:
            jfh.write(json.dumps({
                "ts": round(ts, 6), "dir": direction, "id": ident, "ext": fr.extended,
                "dlc": fr.dlc,
                "data": redacted(len(fr.data)) if data is None else fr.data.hex(" ").upper(),
                "err": fr.error}, separators=(",", ":")) + "\n")
        if cfh is not None:
            body = bytes(len(fr.data)) if data is None else fr.data
            cid = "20000000" if fr.error else fr.id_text     # candump's CAN_ERR_FLAG
            cfh.write(f"({ts:.6f}) {self._channel} {cid}#{body.hex().upper()}\n")
        now = time.monotonic()
        if now - self._last_fsync >= self._fsync_interval:
            for fh in self._fh:
                if fh is not None:
                    fh.flush()
                    try:
                        os.fsync(fh.fileno())
                    except OSError:
                        pass
            self._last_fsync = now


__all__ = ["LoggingCanLink"]
