# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Privacy zones: saved places that every shared route hides (trip-sharing spec §5.2).

- A zone is a place (home, work, a friend's house) with a radius of 500 m, 1 km, 1.5 km or
  2 km (:data:`RADII_M`; 1 km is the default, for "Home").
- **Fixed random offset.** When a zone is saved, an offset ``o`` is drawn **once** from a
  uniform disc of radius ``0.5 r`` with the OS CSPRNG (:mod:`secrets`) and stored with the
  zone. The hiding circle is centred on ``c′ = c + o``, so the true place is always at least
  ``0.5 r`` inside it. The offset is **never re-rolled**: editing a zone keeps it unless the
  place moves by more than ``r`` (or the radius shrinks below twice the offset), which
  draws a new one and says so (:meth:`ZoneStore.update` returns ``redrawn``).
- :class:`ZoneStore` keeps them on the owner's device only, in
  ``<state dir>/privacy_zones.json`` (owner-only permissions), so the offset survives a
  restart and two shares of one trip hide exactly the same area. Zone positions and radii
  never enter a bundle (``share.json`` carries only a count).

Residual risk (said to the owner in the UI): many shared trips entering one zone let an
attacker fit the circle and find ``c′``; the true place is then within ``0.5 r`` of it.
"""
from __future__ import annotations

import json
import math
import os
import secrets
from dataclasses import asdict, dataclass, replace
from typing import List, Tuple

from ..recorder import haversine_m

RADII_M = (500, 1000, 1500, 2000)
DEFAULT_RADIUS_M = 1000
FILE = "privacy_zones.json"
_R_EARTH = 6_371_008.8


class ZoneRefused(ValueError):
    """A zone radius that is not one of the choices (500 m is the floor)."""


def _draw_offset(radius_m: float) -> "Tuple[float, float]":
    """``(east, north)`` metres, uniform on a disc of radius ``0.5 r`` (CSPRNG)."""
    u = secrets.randbits(53) / (1 << 53)
    v = secrets.randbits(53) / (1 << 53)
    rho = 0.5 * radius_m * math.sqrt(u)
    th = 2 * math.pi * v
    return rho * math.cos(th), rho * math.sin(th)


@dataclass(frozen=True)
class PrivacyZone:
    id: str
    name: str
    lat: float
    lon: float
    radius_m: int
    offset_e_m: float
    offset_n_m: float

    @property
    def centre(self) -> "Tuple[float, float]":
        """``c′``: the place moved by its fixed offset, ``(lat, lon)``."""
        dlat = math.degrees(self.offset_n_m / _R_EARTH)
        dlon = math.degrees(self.offset_e_m / (_R_EARTH * max(math.cos(math.radians(self.lat)), 1e-6)))
        return self.lat + dlat, self.lon + dlon

    def contains(self, lat: float, lon: float) -> bool:
        clat, clon = self.centre
        return haversine_m(lat, lon, clat, clon) < self.radius_m


def _check_radius(radius_m) -> int:
    if radius_m not in RADII_M:
        raise ZoneRefused(f"a zone radius is one of {', '.join(str(r) for r in RADII_M)} m "
                          f"(got {radius_m!r}); 500 m is the floor")
    return int(radius_m)


def new_zone(name: str, lat: float, lon: float,
             radius_m: int = DEFAULT_RADIUS_M) -> PrivacyZone:
    """A zone with a freshly drawn offset (the only place an offset is drawn)."""
    r = _check_radius(radius_m)
    e, n = _draw_offset(r)
    return PrivacyZone(secrets.token_hex(8), str(name), float(lat), float(lon), r, e, n)


class ZoneStore:
    """The owner's privacy zones (``<state dir>/privacy_zones.json``)."""

    def __init__(self, state_dir: str) -> None:
        self.path = os.path.join(state_dir, FILE)

    def list(self) -> "List[PrivacyZone]":
        try:
            with open(self.path, encoding="utf-8") as fh:
                doc = json.load(fh)
        except (OSError, ValueError):
            return []
        out = []
        for z in doc.get("zones") or [] if isinstance(doc, dict) else []:
            try:
                out.append(PrivacyZone(str(z["id"]), str(z["name"]), float(z["lat"]),
                                       float(z["lon"]), int(z["radius_m"]),
                                       float(z["offset_e_m"]), float(z["offset_n_m"])))
            except (KeyError, TypeError, ValueError):
                continue
        return out

    def _write(self, zones: "List[PrivacyZone]") -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        tmp = self.path + ".tmp"
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump({"v": 1, "zones": [asdict(z) for z in zones]}, fh, indent=1)
            fh.write("\n")
        os.replace(tmp, self.path)

    def add(self, name: str, lat: float, lon: float,
            radius_m: int = DEFAULT_RADIUS_M) -> PrivacyZone:
        z = new_zone(name, lat, lon, radius_m)
        self._write(self.list() + [z])
        return z

    def update(self, zid: str, *, name: "str | None" = None, lat: "float | None" = None,
               lon: "float | None" = None,
               radius_m: "int | None" = None) -> "Tuple[PrivacyZone, bool]":
        """Edit a zone; ``(zone, redrawn)``. The offset is kept unless the place moved by
        more than its radius or the new radius is under twice the offset."""
        zones = self.list()
        for i, z in enumerate(zones):
            if z.id != zid:
                continue
            r = _check_radius(radius_m) if radius_m is not None else z.radius_m
            nlat = z.lat if lat is None else float(lat)
            nlon = z.lon if lon is None else float(lon)
            moved = haversine_m(z.lat, z.lon, nlat, nlon)
            redraw = moved > z.radius_m or math.hypot(z.offset_e_m, z.offset_n_m) > 0.5 * r
            e, n = _draw_offset(r) if redraw else (z.offset_e_m, z.offset_n_m)
            zones[i] = replace(z, name=z.name if name is None else str(name), lat=nlat,
                               lon=nlon, radius_m=r, offset_e_m=e, offset_n_m=n)
            self._write(zones)
            return zones[i], redraw
        raise KeyError(zid)

    def remove(self, zid: str) -> None:
        zones = self.list()
        if not any(z.id == zid for z in zones):
            raise KeyError(zid)
        self._write([z for z in zones if z.id != zid])


__all__ = ["DEFAULT_RADIUS_M", "PrivacyZone", "RADII_M", "ZoneRefused", "ZoneStore", "new_zone"]
