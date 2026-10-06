# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Offline place names from GeoNames ``cities1000`` (spec 2026-10-06-logs-at-scale §2).

``label(lat, lon)`` names a point by the largest town whose population-scaled reach
covers it, else by the region of the nearest known place, else ``None``. The table is
loaded lazily, once, behind a lock; lookups use a 0.25° grid index.

Region names prefer GeoNames admin2 (e.g. "Highland") over admin1. For the United
Kingdom the "country" is the constituent nation (admin1: Scotland, England, Wales,
Northern Ireland), which is how people name places there.
"""
from __future__ import annotations

import gzip
import math
import os
import threading
from typing import Dict, List, Optional, Tuple

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "places.tsv.gz")
CELL_DEG = 0.25
MAX_KM = 100.0
TOWN_KM = 1.0
# (minimum population, reach in km), largest first.
REACH = ((50_000, 25.0), (5_000, 15.0), (1_000, 8.0), (0, 3.0))
MAX_REACH_KM = REACH[0][1]
_EARTH_KM = 6371.0088
_KM_PER_DEG_LAT = math.pi * _EARTH_KM / 180.0
_UK = "GB"

# A place: (name, lat, lon, cc, admin1, admin2, population)
Place = Tuple[str, float, float, str, str, str, int]


class _Table:
    def __init__(self, places: List[Place], countries: Dict[str, str]):
        self.places = places
        self.countries = countries
        self.grid: Dict[Tuple[int, int], List[int]] = {}
        for i, p in enumerate(places):
            self.grid.setdefault(_cell(p[1], p[2]), []).append(i)


_lock = threading.Lock()
_table: Optional[_Table] = None


def _cell(lat: float, lon: float) -> Tuple[int, int]:
    return (math.floor(lat / CELL_DEG), math.floor(lon / CELL_DEG))


def reach_km(population: int) -> float:
    for floor, km in REACH:
        if population >= floor:
            return km
    return REACH[-1][1]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _EARTH_KM * math.asin(min(1.0, math.sqrt(a)))


def load(path: str = DATA_PATH) -> _Table:
    """Parse a ``places.tsv.gz`` file (see ``geo.build`` for the format)."""
    places: List[Place] = []
    countries: Dict[str, str] = {}
    header_seen = False
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("#country\t"):
                _, cc, name = line.split("\t", 2)
                countries[cc] = name
                continue
            if not line or line.startswith("#"):
                continue
            if not header_seen:
                header_seen = True  # column row
                continue
            name, lat, lon, cc, a1, a2, pop = line.split("\t")
            places.append((name, float(lat), float(lon), cc, a1, a2, int(pop or 0)))
    return _Table(places, countries)


def _get() -> _Table:
    global _table
    if _table is None:
        with _lock:
            if _table is None:
                _table = load()
    return _table


def _within(table: _Table, lat: float, lon: float, radius_km: float):
    """Yield (dist_km, place) for every place within ``radius_km``, scanning grid rings."""
    dlat = radius_km / _KM_PER_DEG_LAT
    coslat = max(math.cos(math.radians(lat)), 0.01)
    dlon = min(180.0, radius_km / (_KM_PER_DEG_LAT * coslat))
    r0, c0 = _cell(lat - dlat, lon - dlon)
    r1, c1 = _cell(lat + dlat, lon + dlon)
    ncols = round(360 / CELL_DEG)
    cols = range(c0, c1 + 1) if c1 - c0 < ncols else range(0, ncols)
    for r in range(r0, r1 + 1):
        for c in cols:
            # Wrap longitude cells across the antimeridian.
            cw = (c + ncols // 2) % ncols - ncols // 2
            for i in table.grid.get((r, cw), ()):
                p = table.places[i]
                d = haversine_km(lat, lon, p[1], p[2])
                if d <= radius_km:
                    yield d, p


def _nation(table: _Table, p: Place) -> str:
    if p[3] == _UK and p[4]:
        return p[4]
    return table.countries.get(p[3], p[3])


def _region(p: Place) -> str:
    return p[5] or p[4]


def _join(*parts: str) -> str:
    out: List[str] = []
    for part in parts:
        if part and part not in out:
            out.append(part)
    return ", ".join(out)


def label(lat: float, lon: float, table: Optional[_Table] = None) -> Optional[dict]:
    """Name a point. Returns ``{"label", "town", "region", "country", "dist_km", "source"}``
    or ``None`` when nothing is known within 100 km (open sea, no data)."""
    if lat is None or lon is None:
        return None
    lat, lon = float(lat), float(lon)
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0) or math.isnan(lat) or math.isnan(lon):
        return None
    t = table if table is not None else _get()

    # 1) Towns whose own reach covers the point: largest population wins, tie -> nearest.
    best = None
    nearest = None
    for d, p in _within(t, lat, lon, MAX_REACH_KM):
        if nearest is None or (d, p) < nearest:
            nearest = (d, p)
        if d <= reach_km(p[6]):
            key = (-p[6], d, p)
            if best is None or key < best:
                best = key
    if best is not None:
        _, d, p = best
        region, country = _region(p), _nation(t, p)
        text = _join(p[0], region)
        return {"label": text if d <= TOWN_KM else "near " + text, "town": p[0],
                "region": region or None, "country": country or None,
                "dist_km": round(d, 2), "source": "geonames"}

    # 2) No town within reach: region of the nearest point within 100 km, widening rings.
    if nearest is None:
        for radius in (50.0, MAX_KM):
            for d, p in _within(t, lat, lon, radius):
                if nearest is None or (d, p) < nearest:
                    nearest = (d, p)
            if nearest is not None:
                break
    if nearest is None:
        return None
    d, p = nearest
    region, country = _region(p), _nation(t, p)
    text = _join(region, country)
    if not text:
        return None
    return {"label": text, "town": None, "region": (region if region != country else None) or None,
            "country": country or None, "dist_km": round(d, 2), "source": "geonames"}
