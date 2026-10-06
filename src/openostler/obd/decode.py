# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pure J1979 decoders (spec §4): bytes in, frozen dataclasses out, no I/O.

Each decoder takes one ECU's whole service messages (headers, checksums and ISO-TP PCI
already removed by the adapter). Facts come from SAE J1979 / ISO 15031-5 and ISO 15765-4,
never from muki01 code (ADR-0025). No DTC description text lives here.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .link import CAN_FLAVORS
from .pids import PidTable

CANDIDATE = "candidate"

# ------------------------------------------------------------- support bitmaps -- #

BITMAP_BLOCKS = tuple(range(0x00, 0x100, 0x20))     # 00, 20, … E0


def bitmap_pids(block: int, data: bytes) -> "frozenset[int]":
    """The PIDs a 4-byte support bitmap for ``block`` marks supported. Bit 7 of byte A is
    ``block + 1``; the last bit (``block + 0x20``) is the next block's own PID, so it is
    included and chains the next request."""
    out = set()
    for i in range(32):
        if data[i // 8] & (0x80 >> (i % 8)) and block + 1 + i <= 0xFF:
            out.add(block + 1 + i)
    return frozenset(out)


def bitmap_chains(block: int, pids: "frozenset[int]") -> bool:
    return (block + 0x20) in pids and block + 0x20 <= 0xE0


# ------------------------------------------------------------------- values -- #

@dataclass(frozen=True)
class PidValue:
    ecu: str
    mode: int
    pid: int
    signal: str
    value: float
    unit: str
    raw: bytes
    ts: float
    metric: "str | None" = None
    confidence: str = CANDIDATE
    label: "str | None" = None          # a state label (``states``), when the record has one


@dataclass(frozen=True)
class PidError:
    ecu: str
    mode: int
    pid: "int | None"
    status: str                         # malformed | negative | no_reply
    reason: "str | None" = None
    nrc: "int | None" = None


def walk_pids(table: PidTable, mode: int, msg: bytes, ecu: str, ts: float,
              frame: "int | None" = None) -> "Tuple[List[PidValue], List[PidError]]":
    """Walk a (possibly multi-PID) Mode 01/02 reply one PID at a time (spec §3, F14).

    ``41 0C a b 0D c 05 d``: each PID's length comes from the table. At a PID with no
    length the walk stops and marks the rest ``malformed: unknown_pid_length``; it never
    guesses. Mode 02 replies carry a frame number after each PID."""
    values: "List[PidValue]" = []
    errors: "List[PidError]" = []
    i = 1
    step_frame = 1 if mode == 0x02 else 0
    while i < len(msg):
        pid = msg[i]
        entry = table.entry(mode, pid)
        if entry is None or entry.length is None:
            errors.append(PidError(ecu, mode, pid, "malformed", "unknown_pid_length"))
            break
        start = i + 1 + step_frame
        data = msg[start:start + entry.length]
        if len(data) < entry.length:
            errors.append(PidError(ecu, mode, pid, "malformed", "short_reply"))
            break
        for sig, metric in zip(entry.signals, entry.metrics):
            if not sig.fits(data):
                errors.append(PidError(ecu, mode, pid, "malformed", f"field {sig.name}"))
                continue
            values.append(PidValue(ecu, mode, pid, sig.name, sig.decode(data), sig.unit,
                                   bytes(data), ts, metric, sig.confidence,
                                   sig.decode_named(data)))
        i = start + entry.length
    return values, errors


# --------------------------------------------------------------------- DTCs -- #

DTC_KINDS = {0x03: "stored", 0x07: "pending", 0x0A: "permanent"}
_LETTER = "PCBU"


@dataclass(frozen=True)
class Dtc:
    code: str           # "P0170"
    raw: str            # "0170"
    ecu: str
    kind: str           # stored | pending | permanent

    @property
    def category(self) -> str:
        """``P`` powertrain, ``C`` chassis, ``B`` body, ``U`` network."""
        return self.code[0]


@dataclass(frozen=True)
class DtcRead:
    ecu: str
    kind: str
    dtcs: "Tuple[Dtc, ...]"
    warnings: "Tuple[str, ...]" = ()

    @property
    def codes(self) -> "List[str]":
        return [d.code for d in self.dtcs]


def dtc_code(hi: int, lo: int) -> str:
    """SAE J2012 two-byte decode: the top two bits give P/C/B/U, the next two the first
    digit, the remaining three nibbles are hex. ``01 70`` → ``P0170``."""
    return f"{_LETTER[hi >> 6]}{(hi >> 4) & 0x3}{hi & 0xF:X}{lo >> 4:X}{lo & 0xF:X}"


def _dtc(hi: int, lo: int, ecu: str, kind: str) -> Dtc:
    return Dtc(dtc_code(hi, lo), f"{hi:02X}{lo:02X}", ecu, kind)


def decode_dtcs(flavor: str, mode: int, messages: "Tuple[bytes, ...]", ecu: str) -> DtcRead:
    """Decode a Mode 03/07/0A reply (spec §4.4).

    CAN: ``43 N`` then N codes. If the length is ``2 + 2N`` it is decoded counted (every
    counted code is returned, a counted ``0000`` tagged ``zero_code``); otherwise the
    uncounted reading is used (code pairs after the service byte, dropping ``00 00``
    padding) and tagged ``count_mismatch`` (owner Q7: fall back and warn, never reject).
    K-line: three codes per message, zero-padded, every message decoded."""
    kind = DTC_KINDS[mode]
    codes: "List[Dtc]" = []
    warns: "List[str]" = []
    if flavor in CAN_FLAVORS:
        for msg in messages:
            if len(msg) >= 2 and len(msg) == 2 + 2 * msg[1]:
                for j in range(2, len(msg), 2):
                    hi, lo = msg[j], msg[j + 1]
                    if hi == 0 and lo == 0 and "zero_code" not in warns:
                        warns.append("zero_code")
                    codes.append(_dtc(hi, lo, ecu, kind))
            else:
                if "count_mismatch" not in warns:
                    warns.append("count_mismatch")
                body = msg[1:]
                for j in range(0, len(body) - 1, 2):
                    hi, lo = body[j], body[j + 1]
                    if hi or lo:
                        codes.append(_dtc(hi, lo, ecu, kind))
    else:
        for msg in messages:
            body = msg[1:]
            for j in range(0, len(body) - 1, 2):
                hi, lo = body[j], body[j + 1]
                if hi or lo:
                    codes.append(_dtc(hi, lo, ecu, kind))
    return DtcRead(ecu, kind, tuple(codes), tuple(warns))


def decode_freeze_trigger(data: bytes, ecu: str) -> "Dtc | None":
    """Mode 02 PID ``02``: the two-byte DTC that stored the frame (F9). ``00 00`` means
    no frame is stored → None."""
    if len(data) < 2 or (data[0] == 0 and data[1] == 0):
        return None
    return _dtc(data[0], data[1], ecu, "stored")


# ---------------------------------------------------------------- readiness -- #

CONTINUOUS = ("misfire", "fuel_system", "components")
NON_CONTINUOUS = {
    "spark": ("catalyst", "heated_catalyst", "evap", "secondary_air", "ac_refrigerant",
              "o2_sensor", "o2_sensor_heater", "egr"),
    # Bits 2 and 4 are reserved for compression ignition.
    "compression": ("nmhc_catalyst", "nox_scr", None, "boost_pressure", None,
                    "exhaust_gas_sensor", "pm_filter", "egr_vvt"),
}


@dataclass(frozen=True)
class MonitorStatus:
    supported: bool
    complete: "bool | None"     # None when the monitor is not supported


@dataclass(frozen=True)
class Readiness:
    ecu: str
    pid: int                    # 0x01 (since clear) or 0x41 (this drive cycle)
    mil: "bool | None"          # None for PID 41
    dtc_count: "int | None"     # None for PID 41
    ignition: str               # spark | compression
    monitors: "Dict[str, MonitorStatus]" = field(default_factory=dict)

    @property
    def incomplete(self) -> "List[str]":
        return sorted(n for n, m in self.monitors.items() if m.supported and not m.complete)


def decode_readiness(data: bytes, ecu: str, pid: int = 0x01) -> Readiness:
    """PID 01 (or 41) bytes A–D (spec §4.3). An incomplete bit counts only for a supported
    monitor."""
    a, b, c, d = data[0], data[1], data[2], data[3]
    ignition = "compression" if b & 0x08 else "spark"
    mons: "Dict[str, MonitorStatus]" = {}
    for bit, name in enumerate(CONTINUOUS):
        sup = bool(b & (1 << bit))
        mons[name] = MonitorStatus(sup, (not b & (1 << (bit + 4))) if sup else None)
    for bit, name in enumerate(NON_CONTINUOUS[ignition]):
        if name is None:
            continue
        sup = bool(c & (1 << bit))
        mons[name] = MonitorStatus(sup, (not d & (1 << bit)) if sup else None)
    if pid == 0x41:
        return Readiness(ecu, pid, None, None, ignition, mons)
    return Readiness(ecu, pid, bool(a & 0x80), a & 0x7F, ignition, mons)


# ------------------------------------------------------------------- Mode 06 -- #

_UAS_PATH = Path(__file__).with_name("uas.json")
_UAS: "Optional[Dict[int, dict]]" = None


def uas_table() -> "Dict[int, dict]":
    """The Mode 06 unit-and-scaling IDs (``obd/uas.json``), keyed by UASID."""
    global _UAS
    if _UAS is None:
        doc = json.loads(_UAS_PATH.read_text(encoding="utf-8"))
        _UAS = {int(k, 16): v for k, v in doc["uas"].items()}
    return _UAS


@dataclass(frozen=True)
class MonitorTest:
    ecu: str
    mid: int
    tid: int
    uasid: int
    value: float
    min: float
    max: float
    unit: str
    passed: bool
    raw: bytes
    confidence: str = CANDIDATE
    warning: "str | None" = None     # unknown_uasid: values left raw


def _scale(uasid: int, raw: int) -> "tuple[float, str, str | None]":
    entry = uas_table().get(uasid)
    if uasid >= 0x80 and raw >= 0x8000:
        raw -= 0x10000
    if entry is None:
        return float(raw), "", "unknown_uasid"
    return raw * float(entry["scale"]) + float(entry.get("offset", 0.0)), entry["unit"], None


def decode_mode06_can(msg: bytes, ecu: str) -> "Tuple[List[MonitorTest], List[str]]":
    """``46`` then 9-byte test records ``MID TID UASID value(2) min(2) max(2)`` (ISO
    15765-4 layout; every record repeats its MID). Values are signed when the UASID's top
    bit is set. → ``(tests, errors)``."""
    tests: "List[MonitorTest]" = []
    errs: "List[str]" = []
    body = msg[1:]
    if len(body) % 9:
        errs.append("malformed: record_length")
    for j in range(0, len(body) - 8, 9):
        mid, tid, uasid = body[j], body[j + 1], body[j + 2]
        rv = (body[j + 3] << 8) | body[j + 4]
        rmin = (body[j + 5] << 8) | body[j + 6]
        rmax = (body[j + 7] << 8) | body[j + 8]
        value, unit, warn = _scale(uasid, rv)
        lo, _, _ = _scale(uasid, rmin)
        hi, _, _ = _scale(uasid, rmax)
        tests.append(MonitorTest(ecu, mid, tid, uasid, value, lo, hi, unit,
                                 lo <= value <= hi, bytes(body[j:j + 9]), warning=warn))
    return tests, errs


# ------------------------------------------------------------------- Mode 09 -- #

_VIN_RE = re.compile(rb"[A-HJ-NPR-Z0-9]{17}")   # ISO 3779: no I, O or Q
ITEM_SIZE = {0x02: 17, 0x04: 16, 0x06: 4, 0x0A: 20}
# K-line message-count InfoTypes: 01 → VIN (02), 03 → CALID (04), 05 → CVN (06).
COUNT_INFOTYPE = {0x02: 0x01, 0x04: 0x03, 0x06: 0x05, 0x08: 0x07}


def info_count(msg: bytes) -> "int | None":
    """K-line ``49 01|03|05|07 01 NN`` (or a bare ``49 xx NN``) → NN."""
    return msg[-1] if len(msg) >= 3 else None


def info_payload(flavor: str, messages: "Tuple[bytes, ...]") -> bytes:
    """Reassemble a Mode 09 item stream. CAN: one message ``49 PID NODI data…`` → data.
    K-line: ``49 PID seq d d d d`` per message, ordered by ``seq`` → the concatenation."""
    if flavor in CAN_FLAVORS:
        return bytes(messages[0][3:]) if messages else b""
    ordered = sorted((m for m in messages if len(m) >= 3), key=lambda m: m[2])
    return b"".join(bytes(m[3:]) for m in ordered)


def split_items(infotype: int, payload: bytes) -> "List[bytes]":
    n = ITEM_SIZE[infotype]
    return [payload[i:i + n] for i in range(0, len(payload) - n + 1, n)]


def calid_strings(payload: bytes) -> "List[str]":
    """CALIDs: 16-byte ASCII strings, NUL-trimmed."""
    out = []
    for item in split_items(0x04, payload):
        s = item.rstrip(b"\x00").decode("ascii", "replace")
        if s:
            out.append(s)
    return out


def cvn_strings(payload: bytes) -> "List[str]":
    """CVNs: 4-byte values as hex strings."""
    return [item.hex().upper() for item in split_items(0x06, payload)]


def ecu_name(payload: bytes) -> "Dict[str, str] | None":
    """InfoType ``0A``: 20 ASCII bytes, the acronym (4), a ``-`` delimiter, the name."""
    if len(payload) < 20:
        return None
    raw = payload[-20:].decode("ascii", "replace")
    acronym, _, name = raw.partition("-")
    return {"acronym": acronym.strip("\x00 "), "name": name.strip("\x00 ")}


def vin_text(payload: bytes) -> "str | None":
    """The 17 VIN characters from an InfoType ``02`` stream (K-line pads three leading
    zero bytes). Returns None unless 17 printable characters remain. Callers must hand the
    result straight to ``vin.handle`` and keep no reference."""
    tail = bytes(payload[-17:])
    if len(tail) != 17 or not _VIN_RE.fullmatch(tail):
        return None
    return tail.decode("ascii")


__all__ = ["bitmap_pids", "bitmap_chains", "BITMAP_BLOCKS", "PidValue", "PidError",
           "walk_pids", "Dtc", "DtcRead", "dtc_code", "decode_dtcs", "DTC_KINDS",
           "decode_freeze_trigger", "MonitorStatus", "Readiness", "decode_readiness",
           "MonitorTest", "decode_mode06_can", "uas_table", "info_payload", "info_count",
           "split_items", "calid_strings", "cvn_strings", "ecu_name", "vin_text",
           "COUNT_INFOTYPE", "ITEM_SIZE"]
