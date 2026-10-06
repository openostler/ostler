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

Pure: no I/O, no clock, no ``web`` import and no path to a car bus (ADR-0032).
"""
from __future__ import annotations

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


__all__ = ["CONTENT_TYPE", "EV_OVERFLOW", "EV_TIME", "FLAG_GATE", "FLAG_SCRUBBED", "FLAG_UNFRAMED", "FLAG_UNSYNCED",
           "HEADER_LEN", "IdentityScrub", "PLACEHOLDER", "PROTO_CAN", "PROTO_CAN_FD",
           "PROTO_KLINE_BYTE", "PROTO_KLINE_MSG", "TYPE_DATA", "TYPE_EVENT", "TapRecord",
           "encode_record", "export_records", "parse_header", "parse_records", "scrub_kline",
           "valid_session"]
