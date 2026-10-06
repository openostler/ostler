# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""NMEA 0183 parsing: RMC, GGA and VTG from any talker, checksum-validated (ADR-0009).

``parse(line)`` turns one sentence into a dict of partial fix fields, or ``None`` when the
line is not a supported sentence, has a missing or wrong checksum, or is malformed.
``FixMerger`` merges the sentences of one epoch (same UTC time of day) into a ``Fix``.

Returned keys (only those the sentence carries):

* ``type`` — ``"RMC" | "GGA" | "VTG"``; ``talker`` — e.g. ``"GP"``, ``"GN"``.
* ``tod_ms`` — UTC time of day in ms (RMC, GGA); ``utc_ms`` — epoch ms (RMC, which has the date).
* ``lat``/``lon`` — signed degrees (south and west negative); ``alt_m``; ``sats``; ``hdop``.
* ``speed_kmh`` (knots converted, or VTG's km/h field); ``heading`` (degrees true).
* ``fix`` — RMC status ``A`` → True, ``V`` → False; GGA quality ≥ 1 → True.
"""
from __future__ import annotations

import calendar
import time
from dataclasses import dataclass, field, replace

KNOT_KMH = 1.852
_TYPES = {"RMC", "GGA", "VTG"}


def checksum(body: str) -> str:
    """XOR of the characters between ``$`` and ``*`` as two upper-case hex digits."""
    c = 0
    for ch in body:
        c ^= ord(ch)
    return f"{c:02X}"


def sentence(body: str) -> str:
    """``body`` (without ``$``/``*``) → a complete sentence with its checksum."""
    return f"${body}*{checksum(body)}"


@dataclass
class Fix:
    """One merged GPS epoch. ``mono`` is ``time.monotonic()`` when it was received."""

    utc_ms: "int | None" = None
    lat: "float | None" = None
    lon: "float | None" = None
    speed_kmh: "float | None" = None
    heading: "float | None" = None
    alt_m: "float | None" = None
    sats: "int | None" = None
    hdop: "float | None" = None
    fix: bool = False
    mono: float = 0.0
    src: str = field(default="", compare=False)

    def snapshot(self, src: "str | None" = None, now: "float | None" = None) -> dict:
        """The snapshot ``gps`` dict: ``{fix, lat, lon, speed_kmh, heading, sats, hdop, src,
        age_s}``. ``now`` is a ``time.monotonic()`` reading (default: now)."""
        now = time.monotonic() if now is None else now
        age = max(0.0, now - self.mono) if self.mono else None
        return {
            "fix": bool(self.fix), "lat": self.lat, "lon": self.lon,
            "speed_kmh": self.speed_kmh, "heading": self.heading,
            "sats": self.sats, "hdop": self.hdop,
            "src": src if src is not None else (self.src or "usb"),
            "age_s": None if age is None else round(age, 1),
        }


def _float(s: str) -> "float | None":
    try:
        return float(s) if s.strip() else None
    except ValueError:
        return None


def _int(s: str) -> "int | None":
    try:
        return int(s) if s.strip() else None
    except ValueError:
        return None


def _tod_ms(s: str) -> "int | None":
    """``hhmmss[.sss]`` → ms since UTC midnight."""
    if len(s) < 6:
        return None
    try:
        hh, mm, ss = int(s[0:2]), int(s[2:4]), float(s[4:])
    except ValueError:
        return None
    if hh > 23 or mm > 59 or ss >= 61:
        return None
    return int(round((hh * 3600 + mm * 60 + ss) * 1000))


def _date_ms(s: str) -> "int | None":
    """``ddmmyy`` → epoch ms of that UTC midnight (``yy`` 80–99 → 19yy, else 20yy)."""
    if len(s) != 6 or not s.isdigit():
        return None
    yy = int(s[4:6])
    d, m, y = int(s[0:2]), int(s[2:4]), (1900 if yy >= 80 else 2000) + yy
    if not (1 <= d <= 31 and 1 <= m <= 12):
        return None
    try:
        return calendar.timegm((y, m, d, 0, 0, 0)) * 1000
    except (ValueError, OverflowError):
        return None


def _coord(value: str, hemi: str, deg_digits: int) -> "float | None":
    """``ddmm.mmmm``/``dddmm.mmmm`` plus hemisphere → signed decimal degrees."""
    if not value.strip() or hemi not in ("N", "S", "E", "W"):
        return None
    try:
        deg = int(value[:deg_digits])
        minutes = float(value[deg_digits:])
    except ValueError:
        return None
    if minutes >= 60:
        return None
    out = deg + minutes / 60.0
    return -out if hemi in ("S", "W") else out


def _split(line: str) -> "tuple[str, str, list[str]] | None":
    """Validate framing and checksum → (talker, type, fields) or None."""
    line = line.strip()
    if not line.startswith("$") or "*" not in line:
        return None  # a missing checksum is rejected
    body, _, cs = line[1:].rpartition("*")
    if len(cs) != 2 or cs.upper() != checksum(body):
        return None
    fields = body.split(",")
    tag = fields[0]
    if len(tag) != 5 or tag[2:] not in _TYPES:
        return None
    return tag[:2], tag[2:], fields[1:]


def parse(line: "str | bytes") -> "dict | None":
    """One NMEA sentence → partial fix fields, or None (see the module docstring)."""
    if isinstance(line, bytes):
        line = line.decode("ascii", "replace")
    parts = _split(line)
    if parts is None:
        return None
    talker, kind, f = parts
    out: dict = {"type": kind, "talker": talker}
    try:
        if kind == "RMC":
            # time,status,lat,N,lon,E,sog_kn,cog,date,magvar,E[,mode[,navstatus]]
            if len(f) < 9:
                return None
            tod = _tod_ms(f[0])
            if tod is not None:
                out["tod_ms"] = tod
            date = _date_ms(f[8])
            if date is not None and tod is not None:
                out["utc_ms"] = date + tod
            out["fix"] = f[1] == "A"
            out["lat"] = _coord(f[2], f[3], 2)
            out["lon"] = _coord(f[4], f[5], 3)
            kn = _float(f[6])
            out["speed_kmh"] = None if kn is None else kn * KNOT_KMH
            out["heading"] = _float(f[7])
        elif kind == "GGA":
            # time,lat,N,lon,E,quality,sats,hdop,alt,M,geoid,M,age,station
            if len(f) < 9:
                return None
            tod = _tod_ms(f[0])
            if tod is not None:
                out["tod_ms"] = tod
            out["lat"] = _coord(f[1], f[2], 2)
            out["lon"] = _coord(f[3], f[4], 3)
            q = _int(f[5])
            out["fix"] = q is not None and q >= 1
            out["sats"] = _int(f[6])
            out["hdop"] = _float(f[7])
            out["alt_m"] = _float(f[8])
        else:  # VTG: cog_true,T,cog_mag,M,sog_kn,N,sog_kmh,K[,mode]
            if len(f) < 8:
                return None
            out["heading"] = _float(f[0])
            kmh = _float(f[6])
            if kmh is None:
                kn = _float(f[4])
                kmh = None if kn is None else kn * KNOT_KMH
            out["speed_kmh"] = kmh
    except IndexError:
        return None
    return out


_FIELDS = ("lat", "lon", "speed_kmh", "heading", "alt_m", "sats", "hdop")


class FixMerger:
    """Merge sentences into a ``Fix``, one epoch per UTC time of day.

    ``feed(parsed, mono)`` returns the merged Fix after every accepted sentence: the fields
    of the current epoch over those of the previous one, so a reader never sees a field
    flicker to None between the GGA and the RMC of the same epoch. ``fix`` and ``utc_ms``
    always come from the current epoch. A VTG (no time) joins the current epoch. GGA has
    no date, so its ``utc_ms`` uses the date of the last RMC.
    """

    def __init__(self) -> None:
        self._tod: "int | None" = None
        self._date_ms: "int | None" = None
        self._prev: Fix = Fix()
        self._cur: dict = {}
        self._rmc_fix: "bool | None" = None
        self._gga_fix: "bool | None" = None
        self.latest: "Fix | None" = None

    def feed(self, d: "dict | None", mono: "float | None" = None) -> "Fix | None":
        if not d:
            return self.latest
        mono = time.monotonic() if mono is None else mono
        tod = d.get("tod_ms")
        if tod is not None and tod != self._tod:
            if self._tod is not None:
                self._prev = self._merged(self._prev.mono)
            self._tod, self._cur = tod, {}
            self._rmc_fix = self._gga_fix = None
        if d.get("utc_ms") is not None and tod is not None:
            self._date_ms = d["utc_ms"] - tod
        if d["type"] == "RMC":
            self._rmc_fix = bool(d.get("fix"))
        elif d["type"] == "GGA":
            self._gga_fix = bool(d.get("fix"))
        for k in _FIELDS:
            if d.get(k) is not None:
                self._cur[k] = d[k]
        self.latest = self._merged(mono)
        return self.latest

    def _merged(self, mono: float) -> Fix:
        vals = {k: self._cur.get(k, getattr(self._prev, k)) for k in _FIELDS}
        if self._rmc_fix is not None:
            ok = self._rmc_fix
        elif self._gga_fix is not None:
            ok = self._gga_fix
        else:
            ok = self._prev.fix
        utc = (self._date_ms + self._tod) if (self._date_ms is not None
                                              and self._tod is not None) else None
        if ok and (vals["lat"] is None or vals["lon"] is None):
            ok = False
        return replace(self._prev, **vals, fix=ok, utc_ms=utc, mono=mono)
