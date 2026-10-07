# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The share's raw-tap scrub (trip-sharing spec §8; R1, R2, R4), over the one identity
table (``node/identity.py``) the recorder and every export use.

- **K-line (R1).** A framed message whose data field is identity data keeps its header,
  its service and option or DID bytes and its length; the rest of the data becomes the
  placeholder and the checksum is recomputed, so the capture still parses. A record the
  node or the Brain already scrubbed (``scrubbed`` flag) is kept as it is: the flag is
  never cleared.
- **CAN ISO-TP (R2).** Messages are reassembled per (bus, CAN id) on the diagnostic ids
  (``7DF``, ``7E0``–``7EF``, ``18DA____``, ``18DB____`` and any pack-declared id) and the
  decision is made on the **reassembled** message, so a first frame cannot push the service
  out of a naive check. The placeholder is written over the data bytes of the first frame
  and every consecutive frame of an identity message, keeping the PCI bytes, lengths and
  padding; flow-control frames stay. A message that cannot be reassembled (a lost or
  out-of-sequence frame) is scrubbed from its first frame to the next first or single
  frame on that id. Single frames that are identity data count under R1.
- **Declared broadcast frames (R1).** Data after the declared prefix becomes the
  placeholder. An undeclared frame that spells a VIN is not scrubbed here: the VIN
  detector blocks the share (R3, ``bundle.py``).
- **Unframed (R4).** ``unframed`` records, per-byte K-line records, K-line records that do
  not frame (header, length, checksum) and unknown protocols are dropped.

Pure: no I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ...node.identity import (IdentityTable, is_placeholder, kline_data_offset, kline_frame_ok,
                              placeholder)
from ...node.tap import (FLAG_SCRUBBED, FLAG_UNFRAMED, PROTO_CAN, PROTO_CAN_FD,
                         PROTO_KLINE_MSG, TapRecord)


@dataclass
class ScrubCounts:
    identity: int = 0        # R1: K-line, single-frame and broadcast identity messages
    isotp_frames: int = 0    # R2: frames of multi-frame or unreassemblable messages
    unframed: int = 0        # R4: records dropped
    kept_scrubbed: int = 0   # records the node or Brain had already scrubbed


@dataclass
class IsoTpMessage:
    """One ISO-TP message (or a fragment of one) on a ``key`` (bus, raw CAN id)."""

    key: tuple
    parts: "List[Tuple[int, int, int, int]]" = field(default_factory=list)  # idx, off, n, msg_off
    data: bytearray = field(default_factory=bytearray)
    total: int = 0
    complete: bool = False
    sn: int = 1

    @property
    def multi(self) -> bool:
        return len(self.parts) > 1 or not self.complete


def can_fields(payload: bytes) -> "Tuple[int, bool, int, bytes]":
    """A tap CAN payload → ``(raw id with flag bits, extended, id, data)``."""
    raw = int.from_bytes(payload[0:4], "little")
    ext = bool(raw & 0x80000000)
    return raw, ext, raw & (0x1FFFFFFF if ext else 0x7FF), bytes(payload[5:])


def isotp_messages(frames: "Iterable[Tuple[int, tuple, bytes]]") -> "List[IsoTpMessage]":
    """Reassemble ``(index, key, data)`` frames into messages; incomplete messages and stray
    consecutive frames come back with ``complete`` False. Flow-control frames are skipped."""
    pending: "Dict[tuple, IsoTpMessage]" = {}
    out: "List[IsoTpMessage]" = []

    def close(key, complete=False):
        m = pending.pop(key, None)
        if m is not None:
            m.complete = complete
            out.append(m)

    for idx, key, data in frames:
        if not data:
            continue
        pci = data[0] >> 4
        if pci == 0:
            close(key)
            n, off = data[0] & 0x0F, 1
            if n == 0 and len(data) > 2:          # CAN FD single frame escape
                n, off = data[1], 2
            n = max(0, min(n, len(data) - off))
            out.append(IsoTpMessage(key, [(idx, off, n, 0)], bytearray(data[off:off + n]), n,
                                    True))
        elif pci == 1 and len(data) >= 2:
            close(key)
            total, off = ((data[0] & 0x0F) << 8) | data[1], 2
            if total == 0 and len(data) >= 6:     # 32-bit length escape
                total, off = int.from_bytes(data[2:6], "big"), 6
            n = max(0, min(len(data) - off, total))
            m = IsoTpMessage(key, [(idx, off, n, 0)], bytearray(data[off:off + n]), total)
            pending[key] = m
            if n >= total:
                close(key, True)
        elif pci == 2:
            m = pending.get(key)
            if m is None or (data[0] & 0x0F) != m.sn:
                close(key)
                out.append(IsoTpMessage(key, [(idx, 1, len(data) - 1, 0)],
                                        bytearray(data[1:]), 0))
                continue
            n = max(0, min(len(data) - 1, m.total - len(m.data)))
            m.parts.append((idx, 1, n, len(m.data)))
            m.data += data[1:1 + n]
            m.sn = (m.sn + 1) & 0x0F
            if len(m.data) >= m.total:
                close(key, True)
    for key in list(pending):
        close(key)
    return out


def message_keep(m: IsoTpMessage, table: IdentityTable) -> "Optional[int]":
    """Bytes of ``m`` that stay readable, or None when ``m`` is not scrubbed: an identity
    message keeps its service and DID, an unreassemblable one keeps nothing (or its service
    and DID when they already show identity)."""
    k = table.match(bytes(m.data)) if m.complete or m.data else 0
    if m.complete:
        return k or None
    return k


def scrub_kline_frame(msg: bytes, table: IdentityTable) -> "Tuple[Optional[bytes], bool]":
    """``(frame, scrubbed)``; frame None when it does not frame (dropped, R4)."""
    msg = bytes(msg)
    if not kline_frame_ok(msg):
        return None, False
    d = kline_data_offset(msg)
    data = msg[d:-1]
    k = table.match(data)
    if not k:
        return msg, False
    body = msg[:d] + data[:k] + placeholder(len(data) - k)
    return body + bytes([sum(body) & 0xFF]), True


def kline_legacy_scrubbed(msg: bytes, table: IdentityTable) -> bool:
    """A K-line payload in the node's scrubbed shape (service, option, placeholder)."""
    k = table.match(msg)
    return bool(k) and len(msg) > k and is_placeholder(msg[k:])


def scrub_records(records: "Sequence[TapRecord]", table: IdentityTable,
                  bus_ids: "Dict[int, str] | None" = None
                  ) -> "Tuple[List[TapRecord], ScrubCounts]":
    """One tap's records as they may leave in a share (events pass through)."""
    bus_ids = bus_ids or {}
    counts = ScrubCounts()
    out: "List[Optional[TapRecord]]" = []
    frames: "List[Tuple[int, tuple, bytes]]" = []
    for r in records:
        if r.is_event:
            out.append(r)
            continue
        if r.flags & FLAG_UNFRAMED:
            counts.unframed += 1
            continue
        if r.flags & FLAG_SCRUBBED:
            counts.kept_scrubbed += 1
            out.append(r)
            continue
        if r.proto == PROTO_KLINE_MSG:
            msg, hit = scrub_kline_frame(r.payload, table)
            if msg is None:
                counts.unframed += 1
                continue
            if hit:
                counts.identity += 1
                r = replace(r, payload=msg, flags=r.flags | FLAG_SCRUBBED)
            out.append(r)
            continue
        if r.proto in (PROTO_CAN, PROTO_CAN_FD) and len(r.payload) >= 5:
            raw, ext, cid, data = can_fields(r.payload)
            if table.is_diagnostic_id(cid, ext):
                frames.append((len(out), (r.bus, raw), data))
            else:
                bc = table.broadcast_frame(bus_ids.get(r.bus), cid, data)
                if bc is not None and len(data) > len(bc.prefix):
                    body = data[:len(bc.prefix)] + placeholder(len(data) - len(bc.prefix))
                    r = replace(r, payload=r.payload[:5] + body, flags=r.flags | FLAG_SCRUBBED)
                    counts.identity += 1
            out.append(r)
            continue
        counts.unframed += 1            # a per-byte K-line record or an unknown protocol
    edits: "Dict[int, bytearray]" = {}
    for m in isotp_messages(frames):
        k = message_keep(m, table)
        if k is None:
            continue
        hit = False
        for idx, off, n, moff in m.parts:
            rec = out[idx]
            assert rec is not None
            buf = edits.setdefault(idx, bytearray(rec.payload[5:]))
            for j in range(n):
                pos = moff + j
                if pos >= k:
                    buf[off + j] = placeholder(1, pos - k)[0]
                    hit = True
        if hit:
            if m.multi:
                counts.isotp_frames += len(m.parts)
            else:
                counts.identity += 1
        else:
            for idx, *_ in m.parts:
                edits.pop(idx, None)
    for idx, buf in edits.items():
        rec = out[idx]
        assert rec is not None
        if bytes(buf) != rec.payload[5:]:
            out[idx] = replace(rec, payload=rec.payload[:5] + bytes(buf),
                               flags=rec.flags | FLAG_SCRUBBED)
    return [r for r in out if r is not None], counts


__all__ = ["IsoTpMessage", "ScrubCounts", "can_fields", "isotp_messages", "kline_legacy_scrubbed",
           "message_keep", "scrub_kline_frame", "scrub_records"]
