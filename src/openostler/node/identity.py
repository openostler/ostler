# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The identity table: which bus messages are identity data (ADR-0036; trip-sharing spec
§8.1). One table for every path: the recorder's tap check, every export and every share
(``node/tap.py`` :class:`~openostler.node.tap.IdentityScrub`, ``logbook/share``).

**Platform list** (UI spec §8.3, trip-sharing spec §8.1 item 2), on every transport, K-line
included:

- ``49 …`` (OBD Mode 09 replies: VIN ``02``, calibration ids ``04``, ECU name ``0A``) and
  ``5A …`` (KWP2000 ReadEcuIdentification replies, ``5A 87``, ``5A 90`` and any other) keep
  their service and option byte;
- ``62 F1 90`` (UDS VIN) and ``62 F1 8C`` (UDS ECU serial) keep the service and DID;
- SecurityAccess with data: a seed (``67 xx`` + data) or a key (``27 xx`` + data) keeps the
  service and sub-function. ``27 01`` (a bare seed request) and ``67 02`` alone are not data.

**Pack declarations** (trip-sharing spec §8.1 item 1; ``VehiclePack.identity``): a mapping
``{services: [hex], dids: [hex], local_ids: [{service, id}], broadcast_frames: [{bus,
can_id, bytes}], diag_ids: [hex], seed_key: bool}``. A service may be named by its request
or its positive reply (``1A`` and ``5A`` are the same entry); a declared DID is read on
``62``; a local id is a ``(service, id)`` pair (``21 9A`` → replies ``61 9A …``); a broadcast
frame is a CAN id (with an optional bus id and data prefix) whose data after the prefix is
identity; ``diag_ids`` adds CAN ids to the ISO-TP set. ``seed_key`` is accepted for the
declaration's sake; the platform scrubs seed/key exchanges on every pack.

:meth:`IdentityTable.match` takes a whole service message (the K-line frame's data field, or
a reassembled ISO-TP message) and returns how many leading bytes stay readable (the service
and its option or DID), or 0 when the message is not identity data. Everything after those
bytes becomes the fixed placeholder (:data:`PLACEHOLDER`, repeated to the length).

Pure stdlib: no I/O and no import outside ``openostler.node`` (``tests/test_layering.py``).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Tuple

PLACEHOLDER = b"SCRUBBED"

# KWP2000 / OBD / UDS service ids
SID_OBD_INFO_REPLY = 0x49     # Mode 09
SID_ECU_ID_REPLY = 0x5A       # ReadEcuIdentification (1A)
SID_RDBI_REPLY = 0x62         # UDS ReadDataByIdentifier (22)
SID_SECURITY_REQ = 0x27       # SecurityAccess
SID_SECURITY_REPLY = 0x67
PLATFORM_DIDS = (0xF190, 0xF18C)   # UDS VIN, ECU serial number


def placeholder(n: int, start: int = 0) -> bytes:
    """``n`` bytes of the repeated placeholder, starting at phase ``start``."""
    if n <= 0:
        return b""
    reps = (start % len(PLACEHOLDER) + n) // len(PLACEHOLDER) + 1
    s = start % len(PLACEHOLDER)
    return (PLACEHOLDER * reps)[s:s + n]


def is_placeholder(b: bytes, start: int = 0) -> bool:
    """True when ``b`` is the placeholder (any length, at phase ``start``)."""
    return bytes(b) == placeholder(len(b), start)


def _hex(v: Any) -> "int | None":
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        s = v.strip().replace(" ", "")
        if s.lower().startswith("0x"):
            s = s[2:]
        try:
            return int(s, 16)
        except ValueError:
            return None
    return None


def _hexbytes(v: Any) -> bytes:
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, str):
        try:
            return bytes.fromhex(v.replace(" ", ""))
        except ValueError:
            return b""
    return b""


def _reply(sid: int) -> int:
    """A request SID's positive reply (``1A`` → ``5A``); a reply stays itself."""
    return sid + 0x40 if sid < 0x40 else sid


@dataclass(frozen=True)
class BroadcastFrame:
    can_id: int
    bus: Optional[str] = None     # a bus id (``can-body``) or None for any bus
    prefix: bytes = b""           # data bytes that stay readable (e.g. a mux index)


@dataclass(frozen=True)
class IdentityTable:
    """Which messages are identity data. :meth:`platform` is the list every path applies;
    :meth:`with_declaration` adds a pack's declarations (never removes)."""

    services: "frozenset[int]" = frozenset({SID_OBD_INFO_REPLY, SID_ECU_ID_REPLY})
    dids: "frozenset[int]" = frozenset(PLATFORM_DIDS)
    local_ids: "frozenset[Tuple[int, int]]" = frozenset()
    broadcast: "Tuple[BroadcastFrame, ...]" = ()
    diag_ids: "frozenset[int]" = frozenset()

    @classmethod
    def platform(cls) -> "IdentityTable":
        return cls()

    def with_declaration(self, decl: "Mapping[str, Any] | None") -> "IdentityTable":
        """This table plus a pack's ``identity`` declaration (unknown keys and unreadable
        entries are ignored; nothing is ever removed)."""
        if not decl:
            return self
        services = set(self.services)
        for s in decl.get("services") or ():
            v = _hex(s)
            if v is not None and 0 <= v <= 0xFF:
                services.add(_reply(v))
        dids = set(self.dids)
        for d in decl.get("dids") or ():
            v = _hex(d)
            if v is not None and 0 <= v <= 0xFFFF:
                dids.add(v)
        local = set(self.local_ids)
        for e in decl.get("local_ids") or ():
            if isinstance(e, Mapping):
                s, i = _hex(e.get("service")), _hex(e.get("id"))
                if s is not None and i is not None and 0 <= s <= 0xFF and 0 <= i <= 0xFF:
                    local.add((_reply(s), i))
        broadcast = list(self.broadcast)
        for e in decl.get("broadcast_frames") or ():
            if isinstance(e, Mapping):
                cid = _hex(e.get("can_id"))
                if cid is not None:
                    bus = e.get("bus")
                    broadcast.append(BroadcastFrame(cid, str(bus) if bus not in (None, "")
                                                    else None, _hexbytes(e.get("bytes"))))
        diag = set(self.diag_ids)
        for d in decl.get("diag_ids") or ():
            v = _hex(d)
            if v is not None:
                diag.add(v)
        return IdentityTable(frozenset(services), frozenset(dids), frozenset(local),
                             tuple(broadcast), frozenset(diag))

    # ---- messages --------------------------------------------------------------------- #
    def match(self, msg: bytes) -> int:
        """Readable leading bytes of an identity message, or 0 when ``msg`` is not one."""
        msg = bytes(msg)
        if not msg:
            return 0
        sid = msg[0]
        if sid in self.services:
            return min(2, len(msg))
        if sid == SID_RDBI_REPLY and len(msg) >= 3 and \
                int.from_bytes(msg[1:3], "big") in self.dids:
            return 3
        if sid in (SID_SECURITY_REQ, SID_SECURITY_REPLY) and len(msg) > 2:
            return 2
        if len(msg) >= 2 and (sid, msg[1]) in self.local_ids:
            return 2
        return 0

    def service_bytes(self) -> "frozenset[int]":
        """Every service byte that can start an identity message (for byte runs that cannot
        be framed)."""
        return frozenset(self.services | {SID_RDBI_REPLY, SID_SECURITY_REQ,
                                          SID_SECURITY_REPLY}
                         | {s for s, _ in self.local_ids})

    # ---- CAN -------------------------------------------------------------------------- #
    def is_diagnostic_id(self, can_id: int, extended: bool) -> bool:
        """An ISO-TP diagnostic id: ``7DF``, ``7E0``–``7EF``, 29-bit ``18DA____`` and
        ``18DB____``, or a pack-declared id."""
        if can_id in self.diag_ids:
            return True
        if extended:
            return (can_id >> 16) in (0x18DA, 0x18DB)
        return can_id == 0x7DF or 0x7E0 <= can_id <= 0x7EF

    def broadcast_frame(self, bus_id: "str | None", can_id: int,
                        data: bytes) -> "BroadcastFrame | None":
        """The declared broadcast frame this CAN frame is, or None."""
        for b in self.broadcast:
            if b.can_id != can_id or (b.bus is not None and bus_id is not None
                                      and b.bus != bus_id):
                continue
            if bytes(data[:len(b.prefix)]) == b.prefix:
                return b
        return None


def kline_data_offset(msg: bytes) -> int:
    """Offset of a K-line frame's data field, or -1. KWP2000 (format byte, optional target
    and source, optional length byte; ``tap.c`` ``data_offset``) and ISO 9141-2 / KWP CARB
    headers (``48 6B xx``, ``68 6A xx``, three header bytes)."""
    msg = bytes(msg)
    if len(msg) < 3:
        return -1
    if msg[0] in (0x48, 0x68) and msg[1] in (0x6B, 0x6A) and len(msg) > 4:
        return 3
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


def kline_frame_ok(msg: bytes) -> bool:
    """A whole K-line frame: a known header, the length agreeing (KWP2000) and the
    checksum (sum of the bytes before it, mod 256) correct."""
    msg = bytes(msg)
    d = kline_data_offset(msg)
    if d < 0 or len(msg) < d + 2:
        return False
    if msg[0] in (0x48, 0x68) and msg[1] in (0x6B, 0x6A):
        n_data = len(msg) - d - 1
    else:
        n_data = msg[0] & 0x3F or msg[d - 1]
    if d + n_data + 1 != len(msg):
        return False
    return sum(msg[:-1]) & 0xFF == msg[-1]


def iter_runs(data: bytes, alphabet: "frozenset[int]", min_len: int) -> "Iterable[Tuple[int, bytes]]":
    """``(offset, run)`` for every maximal run of ``alphabet`` bytes at least ``min_len``
    long."""
    start = None
    for i, b in enumerate(bytes(data) + b"\x00"):
        if b in alphabet and i < len(data):
            if start is None:
                start = i
        elif start is not None:
            if i - start >= min_len:
                yield start, bytes(data[start:i])
            start = None


__all__ = ["BroadcastFrame", "IdentityTable", "PLACEHOLDER", "PLATFORM_DIDS", "is_placeholder",
           "iter_runs", "kline_data_offset", "kline_frame_ok", "placeholder"]
