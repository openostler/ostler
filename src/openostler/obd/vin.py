# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""In-memory VIN handling and the identity scrub patterns (spec §4.7, ADR-0036).

The VIN is decoded locally and never logged: :func:`handle` passes it to the caller's
``on_vin`` synchronously and keeps no reference; an exception from the callback is
replaced by one that carries no text from it. No result, exception, ``repr`` or log line
of the J1979 layer carries the VIN.

The scrub patterns are shared with the transports (``LoggingTransport``, later
``LoggingCanLink``): an identity reply is written as ``<redacted n bytes>`` and every other
byte is kept. Identity replies are the Mode 09 VIN (``49 02``) and calibration IDs
(``49 04``, ADR-0036 §1), and the UDS VIN and ECU serial reads (``62 F1 90``,
``62 F1 8C``).
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from .link import ObdError

# Service-message prefixes that are identity data (ADR-0036 §1).
IDENTITY_PREFIXES: "Tuple[bytes, ...]" = (b"\x49\x02", b"\x49\x04", b"\x62\xF1\x90",
                                          b"\x62\xF1\x8C")


class IdentityError(ObdError):
    """An identity read failed. Never carries identity bytes or callback text."""


def handle(vin: str, on_vin: "Callable[[str], object]") -> None:
    """Hand ``vin`` to ``on_vin`` (U4's local decoder) and drop it. A failing callback
    raises :class:`IdentityError` with no context, so its text never surfaces."""
    failed = False
    try:
        on_vin(vin)
    except Exception:  # the callback's text may hold the VIN
        failed = True
    finally:
        del vin
    if failed:
        raise IdentityError("the VIN callback failed") from None


def is_identity_message(msg: bytes) -> bool:
    """True when a whole service message is an identity reply."""
    return any(bytes(msg[:len(p)]) == p for p in IDENTITY_PREFIXES)


def redacted(n: int) -> str:
    return f"<redacted {n} bytes>"


def scrub_message(msg: bytes) -> str:
    """Spaced hex of a service message, or ``<redacted n bytes>`` for an identity reply."""
    if is_identity_message(msg):
        return redacted(len(msg))
    return bytes(msg).hex(" ").upper()


def _iso9141_identity(raw: bytes, i: int) -> int:
    """At ``48 6B <ecu> 49 02|04 …`` → the frame length (data up to 7 bytes + cs)."""
    seg = raw[i:]
    if len(seg) >= 5 and seg[:2] == b"\x48\x6B" and is_identity_message(seg[3:5]):
        # 48 6B ecu 49 xx seq d d d d cs — the longest ISO 9141-2 frame is 11 bytes; a
        # shorter one ends where the checksum verifies.
        for n in range(6, min(11, len(seg)) + 1):
            if sum(seg[:n - 1]) & 0xFF == seg[n - 1]:
                return n
        return min(11, len(seg))
    return 0


def _kwp_identity(raw: bytes, i: int) -> int:
    """At a KWP2000 frame ``8x|Cx tgt src 49 02|04 …`` (or ``0x`` unaddressed) whose data
    starts with an identity prefix → the whole frame length, else 0."""
    seg = raw[i:]
    if not seg:
        return 0
    fmt = seg[0]
    mode = fmt >> 6
    idx = 3 if mode in (2, 3) else 1 if mode == 0 else -1
    if idx < 0:
        return 0
    length = fmt & 0x3F
    if length == 0:
        if len(seg) <= idx:
            return 0
        length = seg[idx]
        idx += 1
    end = idx + length + 1
    if length < 2 or end > len(seg):
        return 0
    if sum(seg[:end - 1]) & 0xFF != seg[end - 1]:
        return 0
    return end if is_identity_message(seg[idx:idx + 3]) else 0


def scrub_kline(raw: bytes) -> "List[Tuple[str, bytes | int]]":
    """Split a raw K-line byte run into ``("data", bytes)`` and ``("redacted", n)`` parts:
    every ISO 9141-2 or KWP2000 frame that carries an identity reply becomes one redacted
    part. Other bytes are kept unchanged."""
    raw = bytes(raw)
    out: "List[Tuple[str, bytes | int]]" = []
    keep = bytearray()
    i = 0
    while i < len(raw):
        n = _iso9141_identity(raw, i) or _kwp_identity(raw, i)
        if n:
            if keep:
                out.append(("data", bytes(keep)))
                keep.clear()
            out.append(("redacted", n))
            i += n
        else:
            keep.append(raw[i])
            i += 1
    if keep:
        out.append(("data", bytes(keep)))
    return out


def scrub_kline_hex(raw: bytes) -> str:
    """:func:`scrub_kline` as one spaced-hex log line."""
    parts = []
    for kind, v in scrub_kline(raw):
        parts.append(redacted(v) if kind == "redacted" else bytes(v).hex(" ").upper())
    return " ".join(parts)


class CanIdentityScrubber:
    """Stateful ISO-TP scrub per CAN id (CanLink spec §8): a single frame or first frame
    whose message starts with an identity prefix is redacted, and so are its consecutive
    frames until the message length is consumed. Flow-control frames pass."""

    def __init__(self) -> None:
        self._left: "Dict[int, int]" = {}

    def scrub(self, can_id: int, data: bytes) -> "Optional[bytes]":
        """→ the frame data to log, or None when it must be replaced by a placeholder."""
        data = bytes(data)
        if not data:
            return data
        pci = data[0] >> 4
        if pci == 0:                                 # single frame
            n = data[0] & 0x0F
            return None if is_identity_message(data[1:1 + n]) else data
        if pci == 1:                                 # first frame
            total = ((data[0] & 0x0F) << 8) | data[1]
            if is_identity_message(data[2:5]):
                self._left[can_id] = total - 6
                return None
            self._left.pop(can_id, None)
            return data
        if pci == 2 and can_id in self._left:        # consecutive frame
            self._left[can_id] -= 7
            if self._left[can_id] <= 0:
                del self._left[can_id]
            return None
        return data


__all__ = ["IDENTITY_PREFIXES", "IdentityError", "handle", "is_identity_message",
           "scrub_message", "scrub_kline", "scrub_kline_hex", "redacted",
           "CanIdentityScrubber"]
