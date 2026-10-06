# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The raw-tap codec on the Brain (NodeSource spec §7; the ``ostler-firmware`` raw-tap
spec §2 and its ``components/poll/src/tap.c``).

- :func:`parse_header` reads a session header (``tap/<session>/meta``, JSON, retained).
- :func:`parse_records` / :func:`encode_record` read and write the binary records of a
  batch (``tap/<session>/data``): little-endian, a 20-byte header then the payload.
- :class:`IdentityScrub` is the identity scrub, the node's rule applied again on the Brain
  (ADR-0036): a framed K-line reply whose service is ``5A`` (ReadEcuIdentification) or
  ``49`` (OBD Mode 09) keeps its service and option bytes and the rest becomes the fixed
  8-byte placeholder ``SCRUBBED``; an unframed run holding a ``5A`` or ``49`` byte is
  replaced whole; a CAN ISO-TP message starting ``49`` / ``5A`` / ``62 F1 90`` /
  ``62 F1 8C`` has its frames' data replaced. Per-byte K-line records and unknown
  protocols cannot be checked on their own and are dropped when a scrub is due. A record
  the node already flagged ``scrubbed`` is kept as it is: the flag is never cleared.
- :func:`parse_time_event` reads a ``time`` event's CBOR map ``{t_us, utc_ns, source,
  err_us}`` (raw-tap spec, amendment of 2026-10-06) and :class:`TimeMap` maps a tap's
  ``t_us`` to UTC from those marks (raw-tap §2.4): linearly between two marks, with the
  nearest mark's offset before the first and after the last; no mark, no mapping.

Pure: no I/O, no clock, no ``web`` import and no path to a car bus (ADR-0032).
"""
from __future__ import annotations

import bisect
import json
import re
import struct
from dataclasses import dataclass, replace
from typing import Iterable, Optional

HEADER_LEN = 20
_HDR = struct.Struct("<QIBBBBHH")   # t_us, seq, type, bus, dir/event, proto, flags, len

TYPE_DATA, TYPE_EVENT = 0, 1
DIR_RX, DIR_TX_ECHO = 0, 1
PROTO_KLINE_BYTE, PROTO_KLINE_MSG, PROTO_CAN, PROTO_CAN_FD = 0, 1, 2, 3
FLAG_GATE, FLAG_FRAMING, FLAG_CHECKSUM = 0x0001, 0x0002, 0x0004
FLAG_SCRUBBED, FLAG_UNFRAMED, FLAG_UNSYNCED = 0x0008, 0x0010, 0x0020
# raw-tap §2.3 event codes
EV_INIT, EV_KEEPALIVE, EV_GATE, EV_SESSION, EV_OVERFLOW, EV_TIME, EV_LINK, EV_BUS = range(1, 9)

PLACEHOLDER = b"SCRUBBED"
SID_ECU_ID_REPLY = 0x5A    # positive reply to ReadEcuIdentification (1A)
SID_OBD_INFO_REPLY = 0x49  # positive reply to OBD Mode 09 (VIN, calibration ids)
_IDENTITY_SIDS = (SID_ECU_ID_REPLY, SID_OBD_INFO_REPLY)
# CAN (ISO-TP) messages that are identity data: the services above plus the UDS VIN and
# ECU serial reads (the platform's CAN scrub, ``obd/vin.py``).
_CAN_IDENTITY = (b"\x49", b"\x5A", b"\x62\xF1\x90", b"\x62\xF1\x8C")

CONTENT_TYPE = "application/vnd.ostler.tap.v1"
_ULID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
SCRUB_VALUES = ("on", "off")


# The CBOR subset a ``time`` event uses (RFC 8949): unsigned and negative integers, text,
# null, booleans and a definite-length map of them.
_CBOR_UINT, _CBOR_NINT, _CBOR_TEXT, _CBOR_MAP, _CBOR_SIMPLE = 0, 1, 3, 5, 7
_CBOR_FALSE, _CBOR_TRUE, _CBOR_NULL = 20, 21, 22


@dataclass(frozen=True)
class TapRecord:
    t_us: int
    seq: int
    type: int
    bus: int
    dir: int        # data: 0 rx, 1 tx_echo; event: the event code
    proto: int
    flags: int
    payload: bytes

    @property
    def is_event(self) -> bool:
        return self.type == TYPE_EVENT


def valid_session(s: str) -> bool:
    """A tap session id (a ULID, one topic level)."""
    return bool(_ULID.match(s or ""))


def parse_header(payload: bytes) -> "Optional[dict]":
    """The session header when it is a JSON object with ``v: 1``; else None. ``scrub`` is
    kept only when it is ``on`` or ``off``; anything else becomes None, which the Brain
    treats as "not scrubbed by the node" (so it scrubs)."""
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    if not isinstance(obj, dict) or obj.get("v") != 1:
        return None
    if obj.get("scrub") not in SCRUB_VALUES:
        obj = {**obj, "scrub": None}
    return obj


def encode_record(r: TapRecord) -> bytes:
    if len(r.payload) > 0xFFFF:
        raise ValueError("tap record payload too long")
    return _HDR.pack(r.t_us, r.seq, r.type, r.bus, r.dir, r.proto, r.flags,
                     len(r.payload)) + bytes(r.payload)


def parse_records(buf: bytes) -> "tuple[list[TapRecord], int]":
    """The whole records in ``buf`` and the number of trailing bytes that do not form one
    (a short or truncated record; never guessed at)."""
    out: "list[TapRecord]" = []
    off, n = 0, len(buf)
    while off + HEADER_LEN <= n:
        t_us, seq, typ, bus, d, proto, flags, ln = _HDR.unpack_from(buf, off)
        end = off + HEADER_LEN + ln
        if end > n:
            break
        out.append(TapRecord(t_us, seq, typ, bus, d, proto, flags, bytes(buf[off + HEADER_LEN:end])))
        off = end
    return out, n - off


def _kline_data_offset(msg: bytes) -> int:
    """Offset of a KWP2000 frame's data field (format byte, optional target and source,
    optional length byte), or -1 (``tap.c`` ``data_offset``)."""
    if len(msg) < 3:
        return -1
    mode = (msg[0] >> 6) & 3
    if mode in (2, 3):
        idx = 3
    elif mode == 0:
        idx = 1
    else:
        return -1
    if (msg[0] & 0x3F) == 0:
        idx += 1
    return idx if idx < len(msg) else -1


def scrub_kline(msg: bytes, unframed: bool) -> "tuple[bytes, bool]":
    """The node's ``tap_scrub``: ``(payload, scrubbed)``."""
    msg = bytes(msg)
    if unframed:
        if any(b in _IDENTITY_SIDS for b in msg):
            return PLACEHOLDER, True
        return msg, False
    d = _kline_data_offset(msg)
    if d >= 0 and msg[d] in _IDENTITY_SIDS:
        keep = 2 if d + 2 <= len(msg) else 1
        return msg[d:d + keep] + PLACEHOLDER, True
    return msg, False


class IdentityScrub:
    """The Brain's identity check over one tap stream (stateful for CAN ISO-TP).

    ``check(record)`` returns the record to keep (possibly scrubbed) or None to drop it.
    ``scrubbed`` counts records the Brain had to scrub, ``dropped`` those it dropped."""

    def __init__(self) -> None:
        self._left: "dict[tuple[int, int], int]" = {}
        self.scrubbed = 0
        self.dropped = 0

    def check(self, r: TapRecord) -> "Optional[TapRecord]":
        if r.is_event or r.flags & FLAG_SCRUBBED:
            return r
        if r.proto == PROTO_KLINE_MSG:
            payload, hit = scrub_kline(r.payload, bool(r.flags & FLAG_UNFRAMED))
            if hit:
                self.scrubbed += 1
                return replace(r, payload=payload, flags=r.flags | FLAG_SCRUBBED)
            return r
        if r.proto in (PROTO_CAN, PROTO_CAN_FD):
            return self._can(r)
        # a lone K-line byte (or an unknown protocol) cannot be framed here
        self.dropped += 1
        return None

    def _can(self, r: TapRecord) -> "Optional[TapRecord]":
        if len(r.payload) < 5:
            self.dropped += 1
            return None
        can_id = int.from_bytes(r.payload[0:4], "little")
        data = r.payload[5:]
        key = (r.bus, can_id)
        hit = False
        if data:
            pci = data[0] >> 4
            if pci == 0:                                   # single frame
                n = data[0] & 0x0F
                hit = _can_identity(data[1:1 + n])
            elif pci == 1 and len(data) >= 2:              # first frame
                total = ((data[0] & 0x0F) << 8) | data[1]
                hit = _can_identity(data[2:5])
                if hit:
                    self._left[key] = total - (len(data) - 2)
                else:
                    self._left.pop(key, None)
            elif pci == 2 and key in self._left:           # consecutive frame
                self._left[key] -= len(data) - 1
                if self._left[key] <= 0:
                    del self._left[key]
                hit = True
        if not hit:
            return r
        self.scrubbed += 1
        blank = (PLACEHOLDER * (len(data) // len(PLACEHOLDER) + 1))[:len(data)]
        return replace(r, payload=r.payload[:5] + blank, flags=r.flags | FLAG_SCRUBBED)


def _can_identity(msg: bytes) -> bool:
    return any(bytes(msg[:len(p)]) == p for p in _CAN_IDENTITY)


def _cbor_head(buf: bytes, off: int) -> "tuple[int, int, int]":
    """``(major type, argument, next offset)``; raises ValueError on an indefinite length,
    a reserved argument or a short buffer."""
    if off >= len(buf):
        raise ValueError("short CBOR")
    ib = buf[off]
    major, info = ib >> 5, ib & 0x1F
    off += 1
    if info < 24:
        return major, info, off
    if info > 27:
        raise ValueError("indefinite or reserved CBOR length")
    n = 1 << (info - 24)
    if off + n > len(buf):
        raise ValueError("short CBOR")
    return major, int.from_bytes(buf[off:off + n], "big"), off + n


def _cbor_item(buf: bytes, off: int) -> "tuple[object, int]":
    major, arg, off = _cbor_head(buf, off)
    if major == _CBOR_UINT:
        return arg, off
    if major == _CBOR_NINT:
        return -1 - arg, off
    if major == _CBOR_TEXT:
        if off + arg > len(buf):
            raise ValueError("short CBOR")
        return buf[off:off + arg].decode("utf-8"), off + arg
    if major == _CBOR_SIMPLE and arg in (_CBOR_FALSE, _CBOR_TRUE, _CBOR_NULL):
        return {_CBOR_FALSE: False, _CBOR_TRUE: True, _CBOR_NULL: None}[arg], off
    raise ValueError(f"CBOR major type {major} not expected in a time event")


def parse_time_event(payload: bytes) -> "Optional[dict]":
    """A ``time`` event's payload (raw-tap spec, amendment of 2026-10-06): a CBOR map with
    the text keys ``t_us`` (unsigned), ``utc_ns`` (unsigned, ns since the Unix epoch),
    ``source`` (text) and ``err_us`` (unsigned or null). Returns ``{t_us, utc_ns, source,
    err_us}`` (unknown keys ignored, so later additions are read), or None when it is not
    such a map or ``t_us`` / ``utc_ns`` is missing or not an unsigned integer."""
    try:
        major, n, off = _cbor_head(bytes(payload), 0)
        if major != _CBOR_MAP:
            return None
        obj: "dict[str, object]" = {}
        for _ in range(n):
            k, off = _cbor_item(payload, off)
            v, off = _cbor_item(payload, off)
            if isinstance(k, str):
                obj[k] = v
    except (ValueError, UnicodeDecodeError):
        return None
    t_us, utc_ns = obj.get("t_us"), obj.get("utc_ns")
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0
               for v in (t_us, utc_ns)):
        return None
    err = obj.get("err_us")
    return {"t_us": t_us, "utc_ns": utc_ns,
            "source": obj.get("source") if isinstance(obj.get("source"), str) else None,
            "err_us": err if isinstance(err, int) and not isinstance(err, bool) and err >= 0
            else None}


def is_time_event(r: TapRecord) -> bool:
    return r.is_event and r.dir == EV_TIME


class TimeMap:
    """A tap's node clock (``t_us``) to UTC, from its ``time`` events (raw-tap §2.4 and the
    amendment of 2026-10-06). A mark is used only when its CBOR ``t_us`` equals the record
    header's (the instant it maps); a later mark for the same ``t_us`` replaces an earlier
    one. Between two marks the mapping is linear; before the first and after the last it
    keeps that mark's offset (the node clock runs at its own rate there, unchecked). With
    no mark there is no mapping (:meth:`utc_ns` returns None): a tap recorded while the
    node had no clock keeps its ``t_us``."""

    def __init__(self, records: "Iterable[TapRecord]") -> None:
        marks: "dict[int, tuple[int, str | None]]" = {}
        for r in records:
            if not is_time_event(r):
                continue
            ev = parse_time_event(r.payload)
            if ev is None or ev["t_us"] != r.t_us:
                continue
            marks[r.t_us] = (ev["utc_ns"], ev["source"])
        self._t = sorted(marks)
        self._utc = [marks[t][0] for t in self._t]
        self.sources = sorted({s for _u, s in marks.values() if s})

    def __len__(self) -> int:
        return len(self._t)

    def __bool__(self) -> bool:
        return bool(self._t)

    def utc_ns(self, t_us: int) -> "int | None":
        """UTC in ns since the Unix epoch for a node instant, or None without marks."""
        if not self._t:
            return None
        i = bisect.bisect_right(self._t, t_us)
        if i == 0:
            return self._utc[0] + (t_us - self._t[0]) * 1000
        if i == len(self._t):
            return self._utc[-1] + (t_us - self._t[-1]) * 1000
        t0, t1, u0, u1 = self._t[i - 1], self._t[i], self._utc[i - 1], self._utc[i]
        return u0 + (t_us - t0) * (u1 - u0) // (t1 - t0)


def export_records(records: "Iterable[TapRecord]") -> "list[TapRecord]":
    """What may leave the device (ADR-0036 §3, ADR-0039 owner answer 3): unframed records
    dropped and every identity reply scrubbed, whatever the install setting."""
    scrub = IdentityScrub()
    out = []
    for r in records:
        if not r.is_event and r.flags & FLAG_UNFRAMED:
            continue
        kept = scrub.check(r)
        if kept is not None:
            out.append(kept)
    return out


__all__ = ["CONTENT_TYPE", "EV_OVERFLOW", "EV_TIME", "FLAG_GATE", "FLAG_SCRUBBED", "FLAG_UNFRAMED",
           "FLAG_UNSYNCED", "HEADER_LEN", "IdentityScrub", "PLACEHOLDER", "PROTO_CAN",
           "PROTO_CAN_FD", "PROTO_KLINE_BYTE", "PROTO_KLINE_MSG", "TYPE_DATA", "TYPE_EVENT",
           "TapRecord", "TimeMap", "encode_record", "export_records", "is_time_event",
           "parse_header", "parse_records", "parse_time_event", "scrub_kline", "valid_session"]
