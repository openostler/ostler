# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The share's raw-tap files (trip-sharing spec §9.1): one ``tap/bus<N>.pcapng`` per bus
and, for CAN buses, ``tap/bus<N>.candump``. Stdlib only; the pcapng blocks are written with
``logbook/pcapng.py``'s block writers (IETF draft-ietf-opsawg-pcapng, little-endian, one
section).

- **pcapng.** Interface 0 is the bus: K-line as ``LINKTYPE_USER0`` (the scrubbed K-line
  message), CAN as ``LINKTYPE_CAN_SOCKETCAN``. Interface 1, when present, holds the tap's
  events as ``LINKTYPE_USER1``: the event code only, except ``time`` events, which carry
  ``{t_us}`` on the share's time base (CBOR, ``utc_ns`` removed). The interface is named
  ``bus<N>`` and described by its protocol only: no session, node or device id, no packet
  comments. Direction is ``epb_flags`` (inbound or outbound).
- **candump** (CAN only): ``(sec.usec) bus<N> id#data``, the format of ``candump -l``;
  ``id##<flags>data`` for CAN FD.
- **Time.** Relative bundles stamp ``1970-01-01T00:00:00Z + t`` (t from the first visible
  sample); real-time bundles stamp UTC.

:func:`read_pcapng` and :func:`read_candump` are the verifier's strict readers.
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..pcapng import (_INBOUND, _OUTBOUND, EPB, IDB, ISB, LINKTYPE_CAN_SOCKETCAN, LINKTYPE_USER0,
                      LINKTYPE_USER1, SHB, _block, _epb, _idb, _isb, _opts, _socketcan)
from ..pcapng import BYTE_ORDER_MAGIC, OPT_COMMENT, SHB_USERAPPL

SHB_COMMENT = ("Ostler share (ostler.share/1): the scrubbed raw tap of one bus. Identity "
               "replies are replaced with the placeholder SCRUBBED and unframed records are "
               "dropped (ADR-0036).")


@dataclass(frozen=True)
class Packet:
    t_us: int
    data: bytes          # K-line: the message; CAN: the tap payload (id LE, DLC, data)
    outbound: bool = False


@dataclass(frozen=True)
class EventPacket:
    t_us: int
    code: int
    payload: bytes = b""


def cbor_t_us(t_us: int) -> bytes:
    """CBOR ``{"t_us": t_us}`` (a rebased ``time`` event, ``utc_ns`` removed)."""
    def uint(v: int) -> bytes:
        if v < 24:
            return bytes([v])
        for info, n in ((24, 1), (25, 2), (26, 4), (27, 8)):
            if v < (1 << (8 * n)):
                return bytes([info]) + v.to_bytes(n, "big")
        raise ValueError("CBOR integer too large")
    return b"\xa1" + bytes([0x60 | 4]) + b"t_us" + uint(max(0, int(t_us)))


def _shb(comment: str) -> bytes:
    body = struct.pack("<IHHq", BYTE_ORDER_MAGIC, 1, 0, -1)
    body += _opts([(OPT_COMMENT, comment.encode("utf-8")),
                   (SHB_USERAPPL, b"Ostler (openostler)")])
    return _block(SHB, body)


def write_pcapng(n: int, proto: str, packets: "List[Packet]", events: "List[EventPacket]",
                 time_note: str) -> bytes:
    """One bus's tap as pcapng."""
    can = proto == "can"
    out = [_shb(SHB_COMMENT + " " + time_note),
           _idb(LINKTYPE_CAN_SOCKETCAN if can else LINKTYPE_USER0, f"bus{n}", proto)]
    if events:
        out.append(_idb(LINKTYPE_USER1, f"bus{n}-events", "tap events (code only)"))
    last = [0, 0]
    items: "List[Tuple[int, int, bytes, Optional[int]]]" = []
    for p in packets:
        items.append((p.t_us, 0, _socketcan(p.data) if can else p.data,
                      _OUTBOUND if p.outbound else _INBOUND))
    for e in events:
        items.append((e.t_us, 1, bytes([e.code]) + e.payload, None))
    items.sort(key=lambda x: (x[0], x[1]))
    for t, iface, data, flags in items:
        out.append(_epb(iface, max(0, t), data, flags, []))
        last[iface] = t
    out.append(_isb(0, max(0, last[0]), 0))
    if events:
        out.append(_isb(1, max(0, last[1]), 0))
    return b"".join(out)


def candump_line(t_us: int, n: int, payload: bytes, fd: bool) -> str:
    raw = int.from_bytes(payload[0:4], "little")
    ext = bool(raw & 0x80000000)
    cid = raw & (0x1FFFFFFF if ext else 0x7FF)
    ident = f"{cid:08X}" if ext else f"{cid:03X}"
    t = max(0, int(t_us))
    sep = "##0" if fd else "#"
    return f"({t // 1_000_000}.{t % 1_000_000:06d}) bus{n} {ident}{sep}{payload[5:].hex().upper()}"


def write_candump(n: int, packets: "List[Tuple[Packet, bool]]") -> str:
    return "".join(candump_line(p.t_us, n, p.data, fd) + "\n"
                   for p, fd in sorted(packets, key=lambda x: x[0].t_us))


# ---- readers (the verifier) ------------------------------------------------------------ #
@dataclass
class PcapngRead:
    linktypes: "List[int]"
    names: "List[str]"
    packets: "List[Tuple[int, int, bytes]]"     # (iface, t_us, data)
    strings: "List[str]"                        # every option string (comments, names)


def _options(buf: bytes) -> "List[Tuple[int, bytes]]":
    out, off = [], 0
    while off + 4 <= len(buf):
        code, ln = struct.unpack_from("<HH", buf, off)
        off += 4
        if code == 0:
            break
        if off + ln > len(buf):
            raise ValueError("option runs past its block")
        out.append((code, buf[off:off + ln]))
        off += ln + (-ln % 4)
    return out


def read_pcapng(data: bytes) -> PcapngRead:
    """Parse a little-endian pcapng file strictly; ValueError on anything malformed."""
    if len(data) < 28 or struct.unpack_from("<I", data, 0)[0] != SHB:
        raise ValueError("not a pcapng file")
    res = PcapngRead([], [], [], [])
    off = 0
    resol: "List[int]" = []
    while off < len(data):
        if off + 12 > len(data):
            raise ValueError("truncated block")
        btype, total = struct.unpack_from("<II", data, off)
        if total < 12 or total % 4 or off + total > len(data) or \
                struct.unpack_from("<I", data, off + total - 4)[0] != total:
            raise ValueError("bad block length")
        body = data[off + 8:off + total - 4]
        if btype == SHB:
            if struct.unpack_from("<I", body, 0)[0] != BYTE_ORDER_MAGIC:
                raise ValueError("not little-endian pcapng")
            res.strings += [v.decode("utf-8", "replace") for _c, v in _options(body[16:])]
        elif btype == IDB:
            lt = struct.unpack_from("<H", body, 0)[0]
            res.linktypes.append(lt)
            name, ts = "", 6
            for code, v in _options(body[8:]):
                if code == 2:
                    name = v.decode("utf-8", "replace")
                if code == 9 and v:
                    ts = v[0]
                if code in (2, 3):
                    res.strings.append(v.decode("utf-8", "replace"))
            res.names.append(name)
            resol.append(ts)
        elif btype == EPB:
            iface, hi, lo, cap, _orig = struct.unpack_from("<IIIII", body, 0)
            if iface >= len(res.linktypes) or 20 + cap > len(body):
                raise ValueError("packet on an unknown interface or past its block")
            t = (hi << 32) | lo
            if resol[iface] != 6:
                raise ValueError("timestamps must be in microseconds")
            res.packets.append((iface, t, bytes(body[20:20 + cap])))
            res.strings += [v.decode("utf-8", "replace") for c, v in
                            _options(body[20 + cap + (-cap % 4):]) if c == 1]
        elif btype == ISB:
            pass
        else:
            raise ValueError(f"unexpected block type 0x{btype:08X}")
        off += total
    return res


def socketcan_to_tap(data: bytes) -> bytes:
    """A ``LINKTYPE_CAN_SOCKETCAN`` packet back to the tap payload shape."""
    if len(data) < 8:
        raise ValueError("short SocketCAN packet")
    cid, ln = struct.unpack_from(">IB", data, 0)
    return cid.to_bytes(4, "little") + bytes([ln]) + data[8:8 + ln]


_CANDUMP = re.compile(r"^\((\d+)\.(\d{6})\) (\S+) ([0-9A-F]{3}|[0-9A-F]{8})(#|##[0-9A-F])"
                      r"([0-9A-F]*)$")


def read_candump(text: str) -> "List[Tuple[int, str, int, bool, bytes]]":
    """``(t_us, iface, can id, extended, data)`` per line; ValueError on a malformed line."""
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        m = _CANDUMP.match(line)
        if not m or len(m.group(6)) % 2:
            raise ValueError(f"line {i} is not a candump frame")
        ext = len(m.group(4)) == 8
        out.append((int(m.group(1)) * 1_000_000 + int(m.group(2)), m.group(3),
                    int(m.group(4), 16), ext, bytes.fromhex(m.group(6))))
    return out


__all__ = ["EventPacket", "Packet", "PcapngRead", "candump_line", "cbor_t_us", "read_candump",
           "read_pcapng", "socketcan_to_tap", "write_candump", "write_pcapng"]
