# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The K-line :class:`~openostler.obd.link.ObdRequestLink` adapter (J1979 spec §1, §2).

It sends one OBD request on a profile-built :class:`KLine` and returns every responder's
service messages keyed by the ECU's source byte (``"10"``, ``"18"``), with headers and
checksums removed:

- ``iso9141``: ``68 6A F1 …`` requests; the burst is cut at verified checksums
  (``frame_iso9141.split``), so a header byte is never read as data (fixture F2).
- ``kwp``: ISO 14230-4 functional ``C2 33 F1 …`` (or physical ``8x <ecu> F1 …``)
  requests; the burst is cut into checksummed KWP2000 frames addressed to the tester.

A ``7F <sid> 78`` (response pending) makes the adapter read on, up to six times; a Mode 09
sequence reads on until ``expect_messages`` arrived. The adapter refuses Mode 08 like
every adapter, and it clears ``KLine.last_burst`` after an identity read so no VIN bytes
stay in memory. Keep-alive (``01 00`` on ISO 9141-2, ``3E`` on KWP2000, ADR-0022) is
owned here: :meth:`keepalive_if_due`.
"""
from __future__ import annotations

from typing import Dict, List

from ..obd.link import NEGATIVE, NRC_RESPONSE_PENDING, EcuReply, guard_payload
from ..obd.vin import is_identity_message
from .frame import ChecksumError, FrameError
from .frame import decode as decode_kwp
from .frame_iso9141 import split
from .kline import KLine

TESTER = 0xF1
OBD_FUNCTIONAL_TARGET = 0x33
MAX_PENDING = 6


def split_kwp(burst: bytes, sent: "bytes | None" = None) -> "List[tuple[int, bytes]]":
    """Cut a KWP2000 reply burst into ``(source, data)`` for frames addressed to the
    tester. Our own echo (``sent``) is removed first; bytes that never form a checksummed
    frame are skipped."""
    b = bytes(burst)
    if sent:
        i = b.find(bytes(sent))
        if i >= 0:
            b = b[:i] + b[i + len(sent):]
    out: "List[tuple[int, bytes]]" = []
    i = 0
    while i < len(b):
        fmt = b[i]
        if fmt >> 6 not in (2, 3):
            i += 1
            continue
        n = fmt & 0x3F
        hdr = 3
        if n == 0:
            if i + 3 >= len(b):
                break
            n = b[i + 3]
            hdr = 4
        end = i + hdr + n + 1
        if n < 1 or end > len(b):
            i += 1
            continue
        try:
            fr = decode_kwp(b[i:end])
        except (FrameError, ChecksumError):
            i += 1
            continue
        if fr.target == TESTER and fr.source is not None:
            out.append((fr.source, fr.data))
        i = end
    return out


class KLineObdLink:
    """An :class:`ObdRequestLink` over a profile-built :class:`KLine`."""

    def __init__(self, kline: KLine, flavor: "str | None" = None) -> None:
        prof = kline.profile
        if flavor is None:
            if prof is None:
                raise ValueError("KLineObdLink needs a profile-built KLine or a flavor")
            flavor = "iso9141" if prof.framing == "iso9141" else "kwp"
        if flavor not in ("iso9141", "kwp"):
            raise ValueError(f"not a K-line OBD flavor: {flavor!r}")
        self._k = kline
        self.flavor = flavor

    # ---- one burst ----------------------------------------------------- #
    def _gap(self) -> float:
        p = self._k.profile
        return (p.timing.p1_max if p is not None else 0.020) + 0.040

    def _overall(self, timeout: "float | None") -> float:
        if timeout is not None:
            return timeout
        p = self._k.profile
        return p.timing.reply_timeout if p is not None else 1.0

    def _first(self, payload: bytes, target: "str | None",
               timeout: "float | None") -> "List[tuple[int, bytes]]":
        if self.flavor == "iso9141":
            return [(f.ecu, f.data) for f in self._k.request_iso9141(payload)]
        if target is None:
            raw = self._k.converse(payload, addressed=True, functional=True,
                                   target=OBD_FUNCTIONAL_TARGET, source=TESTER,
                                   overall=self._overall(timeout), gap=self._gap())
        else:
            raw = self._k.converse(payload, addressed=True, functional=False,
                                   target=int(target, 16), source=TESTER,
                                   overall=self._overall(timeout), gap=self._gap())
        return split_kwp(raw)

    def _more(self, timeout: "float | None") -> "List[tuple[int, bytes]]":
        raw = self._k._burst_read(self._gap(), self._overall(timeout))
        if self.flavor == "iso9141":
            return [(f.ecu, f.data) for f in split(raw)]
        return split_kwp(raw)

    # ---- ObdRequestLink -------------------------------------------------- #
    def request(self, payload: bytes, *, target: "str | None" = None,
                expect_messages: "int | None" = None,
                timeout: "float | None" = None) -> "Dict[str, EcuReply]":
        payload = bytes(payload)
        guard_payload(payload, allow_clear=True)
        frames = self._first(payload, target, timeout)
        by_ecu: "Dict[str, List[bytes]]" = {}
        pending = 0

        def _add(items: "List[tuple[int, bytes]]") -> int:
            waits = 0
            for src, data in items:
                if len(data) >= 3 and data[0] == NEGATIVE and data[2] == NRC_RESPONSE_PENDING:
                    waits += 1
                    continue
                by_ecu.setdefault(f"{src:02X}", []).append(bytes(data))
            return waits

        waits = _add(frames)
        while True:
            short = (expect_messages is not None
                     and max((len(m) for m in by_ecu.values()), default=0) < expect_messages)
            if not (waits or short) or pending >= MAX_PENDING:
                break
            pending += 1
            more = self._more(timeout)
            if not more:
                break
            waits = _add(more)
        identity = any(is_identity_message(m) for ms in by_ecu.values() for m in ms)
        if identity or is_identity_message(bytes([payload[0] + 0x40]) + payload[1:2]):
            self._k.last_burst = b""
        if target is not None:
            by_ecu = {e: m for e, m in by_ecu.items() if e == target.upper()}
        return {e: EcuReply(e, tuple(m)) for e, m in by_ecu.items()}

    # ---- keep-alive (ADR-0022) ------------------------------------------ #
    def keepalive_if_due(self) -> bool:
        """``01 00`` on ISO 9141-2 (no TesterPresent there) or ``3E`` on KWP2000, when
        nothing went out for the profile's keep-alive interval."""
        p = self._k.profile
        if p is None or p.keepalive is None:
            return False
        last = self._k.last_tx
        if last is not None and self._k.now() - last < p.keepalive_interval:
            return False
        try:
            if self.flavor == "iso9141":
                self._k.request_iso9141(p.keepalive)
            else:
                self._k.converse(b"\x3E", addressed=True, functional=True,
                                 target=OBD_FUNCTIONAL_TARGET, source=TESTER,
                                 overall=self._overall(None), gap=self._gap())
        except Exception as exc:  # a failed keep-alive is logged, never raised
            self._k.emit("keepalive", ok=False, error=f"{type(exc).__name__}: {exc}")
        return True


__all__ = ["KLineObdLink", "split_kwp"]
