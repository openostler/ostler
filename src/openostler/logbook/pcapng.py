# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""A session's raw tap as pcapng (``GET /sessions/<id>/export?fmt=pcapng``; NodeSource
spec §7, §8). Stdlib only: the blocks are written with ``struct`` per the pcapng
specification (IETF draft-ietf-opsawg-pcapng; little-endian, one section).

- One interface per tap session and bus (``if_name`` the bus id, e.g. ``kline-diag``), and
  one per tap session for its events when there are any.
- **Link types.** K-line has no registered link type, so its records use
  ``LINKTYPE_USER0`` (147) and the payload is the K-line message as tapped; CAN uses
  ``LINKTYPE_CAN_SOCKETCAN`` (227: id big-endian with the SocketCAN flag bits, length, two
  reserved bytes, data); events use ``LINKTYPE_USER1`` (148) with their CBOR payload.
- **Time.** Timestamps are each node's monotonic clock in µs since its boot (``t_us``),
  not UTC: mapping them to UTC with the tap's ``time`` events is decode-lab work (spec
  §14). The section comment says so.
- **Direction.** ``epb_flags`` marks ``rx`` inbound and ``tx_echo`` (the node's own frames
  read back) outbound; a gate-sent frame's comment says so.
- **Gaps.** A record after a ``seq`` gap carries a comment naming the lost range, and each
  interface's statistics block counts the lost records (``isb_ifdrop``).
- **Identity (ADR-0036 §3, ADR-0039 owner answer 3).** Whatever the install setting, the
  export drops unframed records and scrubs every identity reply (``node/tap.py``
  ``export_records``); the ``scrubbed`` flag is kept as a comment.
"""
from __future__ import annotations

import struct

from ..node.tap import (DIR_TX_ECHO, FLAG_GATE, FLAG_SCRUBBED, PROTO_CAN, PROTO_CAN_FD,
                        TapRecord, export_records)

SHB, IDB, EPB, ISB = 0x0A0D0D0A, 0x00000001, 0x00000006, 0x00000005
BYTE_ORDER_MAGIC = 0x1A2B3C4D
LINKTYPE_USER0, LINKTYPE_USER1, LINKTYPE_CAN_SOCKETCAN = 147, 148, 227
OPT_END, OPT_COMMENT = 0, 1
SHB_USERAPPL = 4
IF_NAME, IF_DESCRIPTION, IF_TSRESOL = 2, 3, 9
EPB_FLAGS = 2
ISB_IFDROP = 5
_INBOUND, _OUTBOUND = 0b01, 0b10
MIME = "application/x-pcapng"


def _pad(b: bytes) -> bytes:
    return b + b"\x00" * (-len(b) % 4)


def _opt(code: int, value: bytes) -> bytes:
    return struct.pack("<HH", code, len(value)) + _pad(value)


def _opts(items: "list[tuple[int, bytes]]") -> bytes:
    if not items:
        return b""
    return b"".join(_opt(c, v) for c, v in items) + struct.pack("<HH", OPT_END, 0)


def _block(btype: int, body: bytes) -> bytes:
    total = 12 + len(body)
    return struct.pack("<II", btype, total) + body + struct.pack("<I", total)


def _shb(comment: str) -> bytes:
    body = struct.pack("<IHHq", BYTE_ORDER_MAGIC, 1, 0, -1)
    body += _opts([(OPT_COMMENT, comment.encode("utf-8")),
                   (SHB_USERAPPL, b"Ostler (openostler)")])
    return _block(SHB, body)


def _idb(linktype: int, name: str, description: str) -> bytes:
    body = struct.pack("<HHI", linktype, 0, 0)
    body += _opts([(IF_NAME, name.encode("utf-8")),
                   (IF_DESCRIPTION, description.encode("utf-8")),
                   (IF_TSRESOL, bytes([6]))])
    return _block(IDB, body)


def _epb(iface: int, t_us: int, data: bytes, flags: "int | None", comments: "list[str]") -> bytes:
    body = struct.pack("<IIIII", iface, (t_us >> 32) & 0xFFFFFFFF, t_us & 0xFFFFFFFF,
                       len(data), len(data)) + _pad(data)
    items: "list[tuple[int, bytes]]" = []
    if flags is not None:
        items.append((EPB_FLAGS, struct.pack("<I", flags)))
    items += [(OPT_COMMENT, c.encode("utf-8")) for c in comments]
    return _block(EPB, body + _opts(items))


def _isb(iface: int, t_us: int, dropped: int) -> bytes:
    body = struct.pack("<III", iface, (t_us >> 32) & 0xFFFFFFFF, t_us & 0xFFFFFFFF)
    body += _opts([(ISB_IFDROP, struct.pack("<Q", dropped))])
    return _block(ISB, body)


def _socketcan(payload: bytes) -> bytes:
    """A tap CAN payload (id LE u32 with the SocketCAN bits, DLC, data) as the
    LINKTYPE_CAN_SOCKETCAN header (id BE u32, length, 3 reserved bytes) plus data."""
    can_id = int.from_bytes(payload[0:4], "little")
    data = payload[5:]
    return struct.pack(">IBBBB", can_id, len(data), 0, 0, 0) + data


class _Section:
    """The blocks of one section: interfaces are made on first use."""

    def __init__(self, comment: str) -> None:
        self.out = [_shb(comment)]
        self.ifaces: "dict[tuple, int]" = {}
        self.stats: "list[list[int]]" = []   # per interface: [last t_us, records lost]

    def iface(self, key: tuple, linktype: int, name: str, desc: str) -> int:
        if key not in self.ifaces:
            self.out.append(_idb(linktype, name, desc))
            self.ifaces[key] = len(self.stats)
            self.stats.append([0, 0])
        return self.ifaces[key]

    def packet(self, i: int, t_us: int, data: bytes, flags, comments, lost: int) -> None:
        self.out.append(_epb(i, t_us, data, flags, comments))
        self.stats[i][0] = t_us
        self.stats[i][1] += lost

    def finish(self) -> bytes:
        for i, (t_us, lost) in enumerate(self.stats):
            self.out.append(_isb(i, t_us, lost))
        return b"".join(self.out)


def _tap(sec: _Section, n: int, entry: dict, records: "list[TapRecord]") -> None:
    session = str(entry.get("session") or "")
    device = str(entry.get("device") or "")
    buses = {b.get("idx"): b for b in entry.get("buses") or [] if isinstance(b, dict)}
    # Gaps are found on the stored sequence; records the export drops (unframed) are not
    # losses, and a gap before one is reported on the next record exported.
    kept = {r.seq: r for r in export_records(records)}
    expected, pending, pending_lost, last = None, [], 0, None
    for raw in records:
        if expected is not None and raw.seq > expected:
            pending.append(f"seq gap: records {expected}..{raw.seq - 1} lost "
                           f"({raw.seq - expected})")
            pending_lost += raw.seq - expected
        expected = raw.seq + 1 if expected is None else max(expected, raw.seq + 1)
        r = kept.get(raw.seq)
        if r is None:
            continue
        comments, lost, pending, pending_lost = pending, pending_lost, [], 0
        if r.is_event:
            i = sec.iface((n, "events"), LINKTYPE_USER1, f"{device} events",
                          f"tap {session} events (CBOR), node {device}")
            comments.insert(0, f"event {r.dir} seq {r.seq}")
            data, flags = r.payload, None
        else:
            bus = buses.get(r.bus) or {}
            can = r.proto in (PROTO_CAN, PROTO_CAN_FD)
            i = sec.iface((n, r.bus), LINKTYPE_CAN_SOCKETCAN if can else LINKTYPE_USER0,
                          str(bus.get("bus_id") or f"bus{r.bus}"),
                          f"tap {session} bus {r.bus} ({bus.get('proto') or '?'}), "
                          f"node {device}")
            data = _socketcan(r.payload) if can else r.payload
            flags = _OUTBOUND if r.dir == DIR_TX_ECHO else _INBOUND
            comments.append(f"seq {r.seq}")
            if r.flags & FLAG_GATE:
                comments.append("sent by the node's gate")
            if r.flags & FLAG_SCRUBBED:
                comments.append("identity data scrubbed")
        sec.packet(i, r.t_us, data, flags, comments, lost)
        last = i
    if pending_lost and last is not None:  # a gap before records the export dropped
        sec.stats[last][1] += pending_lost


def to_pcapng(taps: "list[tuple[dict, list[TapRecord]]]", meta: dict) -> bytes:
    """``taps``: each ``meta.tap`` entry with its records (``logbook/tap.py``
    ``read_tap``). Raises ValueError when the session has no tap."""
    if not taps:
        raise ValueError("this session has no raw tap (only node sessions record one)")
    sec = _Section(f"Ostler raw tap of session {meta.get('id', '')}. Timestamps are each "
                   "node's monotonic clock in microseconds since its boot, not UTC. Identity "
                   "replies are scrubbed and unframed records dropped (ADR-0036).")
    for n, (entry, records) in enumerate(taps):
        _tap(sec, n, entry, records)
    return sec.finish()


__all__ = ["LINKTYPE_CAN_SOCKETCAN", "LINKTYPE_USER0", "LINKTYPE_USER1", "MIME", "to_pcapng"]
