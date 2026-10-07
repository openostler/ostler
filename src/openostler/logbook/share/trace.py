# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The visible trace of a shared trip (trip-sharing spec §5; R5, R6, R7).

1. **Fixes.** Rows with a latitude and longitude, dropping fixes with HDOP > 5 or a jump
   implying more than 300 km/h from the last kept fix.
2. **Ends trim (§5.1).** Every fix with along-track distance ``s < T_start`` or
   ``s > S − T_end`` is hidden; the cut points are interpolated on their segments so the
   visible trace starts exactly at ``s = T_start`` and ends at ``S − T_end``. The default is
   500 m; 200 m is the floor (:data:`MIN_TRIM_M`) and 1,500 m the ceiling.
3. **Privacy zones (§5.2).** Every fix within ``r`` of a zone's offset centre ``c′`` is
   hidden, anywhere in the trip; a trip that crosses a zone becomes separate segments with
   no line across the gap (``zones.py`` holds the zones and their fixed offsets).
4. **Stats (§5.4)** from the visible, unsimplified fixes only, rounded per level
   (:func:`round_stats`). Nothing reports the hidden part, its length or the trip total.
5. **Simplify (§5.3).** Ramer–Douglas–Peucker with ε = 10 m on a local east-north plane,
   coordinates to 5 decimals, no point times, speeds, headings or accuracies.

Pure stdlib; no I/O.
"""
from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Tuple

from ..recorder import fmt_num, haversine_m
from .zones import PrivacyZone

DEFAULT_TRIM_M = 500
MIN_TRIM_M = 200
MAX_TRIM_M = 1500
MAX_HDOP = 5.0
MAX_JUMP_KMH = 300.0
RDP_EPSILON_M = 10.0
MOVING_KMH = 5.0
STOP_S = 60.0
GAIN_STEP_M = 3.0
GAIN_FILTER_S = 30.0
MIN_SHARE_KM = 1.0
NO_GPS_EDGE_MS = 120_000      # no-GPS distance: the first and last 2 minutes left out


class TrimRefused(ValueError):
    """An ends trim outside 200 m to 1,500 m."""


@dataclass
class Point:
    lat: float
    lon: float
    t: float                  # session ms
    alt: Optional[float] = None
    spd: Optional[float] = None     # GPS speed, km/h


@dataclass
class VisibleTrace:
    segments: "List[List[Point]]" = field(default_factory=list)
    fixes: int = 0                  # fixes kept after the HDOP/jump filter
    hidden_trim: int = 0            # fixes hidden by the ends trim
    hidden_zone: int = 0            # fixes hidden by privacy zones
    zones_hit: int = 0              # zones that hid at least one fix
    has_gps: bool = False
    # fixes the ends trim hid, more than TRIM_MARGIN_M beyond the cut (owner's device only:
    # the verifier's check 4 tests that no route fix sits on one)
    trimmed: "List[Point]" = field(default_factory=list)

    @property
    def points(self) -> "List[Point]":
        return [p for seg in self.segments for p in seg]

    def windows(self) -> "List[Tuple[float, float]]":
        """``(first t, last t)`` per visible segment, in session ms."""
        return [(seg[0].t, seg[-1].t) for seg in self.segments if seg]

    def distance_m(self) -> float:
        return sum(haversine_m(a.lat, a.lon, b.lat, b.lon)
                   for seg in self.segments for a, b in zip(seg, seg[1:]))


def check_trim(ends_m: "int | float") -> int:
    """The owner's ends trim, refused outside 200 m to 1,500 m (the 200 m floor cannot be
    lowered)."""
    if isinstance(ends_m, bool) or not isinstance(ends_m, (int, float)) or \
            not MIN_TRIM_M <= ends_m <= MAX_TRIM_M:
        raise TrimRefused(f"the ends trim must be {MIN_TRIM_M} m to {MAX_TRIM_M} m "
                          f"(got {ends_m!r}); {MIN_TRIM_M} m is the floor")
    return int(ends_m)


def _num(v) -> "float | None":
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def fixes(rows: "Iterable[dict]") -> "List[Point]":
    """The trip's fixes in time order after the HDOP and jump filters (§5.1)."""
    out: "List[Point]" = []
    for r in rows:
        lat, lon = _num(r.get("GPS_Latitude")), _num(r.get("GPS_Longitude"))
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        hdop = _num(r.get("GPS_HDOP"))
        if hdop is not None and hdop > MAX_HDOP:
            continue
        p = Point(lat, lon, float(r.get("Interval") or 0), _num(r.get("GPS_Altitude")),
                  _num(r.get("GPS_Speed")))
        if out:
            q = out[-1]
            d = haversine_m(q.lat, q.lon, p.lat, p.lon)
            dt = (p.t - q.t) / 1000.0
            if d > 0 and (dt <= 0 or d / dt * 3.6 > MAX_JUMP_KMH):
                continue
            if dt <= 0:
                continue
        out.append(p)
    return out


def _lerp(a: Point, b: Point, f: float) -> Point:
    def mix(x, y):
        return None if x is None or y is None else x + (y - x) * f
    return Point(a.lat + (b.lat - a.lat) * f, a.lon + (b.lon - a.lon) * f,
                 a.t + (b.t - a.t) * f, mix(a.alt, b.alt), mix(a.spd, b.spd))


TRIM_MARGIN_M = 2.0


def trim_ends(pts: "Sequence[Point]", start_m: float, end_m: float,
              hidden_out: "List[Point] | None" = None) -> "Tuple[List[Point], int]":
    """The fixes between ``s = start_m`` and ``s = S − end_m`` with interpolated cut points
    (§5.1), and how many fixes were hidden. ``hidden_out`` collects the hidden fixes more
    than :data:`TRIM_MARGIN_M` beyond a cut."""
    if len(pts) < 2:
        if hidden_out is not None:
            hidden_out.extend(pts)
        return [], len(pts)
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + haversine_m(a.lat, a.lon, b.lat, b.lon))
    total = s[-1]
    lo, hi = start_m, total - end_m
    if hi <= lo:
        if hidden_out is not None:
            hidden_out.extend(pts)
        return [], len(pts)
    out: "List[Point]" = []
    for i in range(1, len(pts)):
        a, b, sa, sb = pts[i - 1], pts[i], s[i - 1], s[i]
        if sb <= lo or sa >= hi:
            continue
        if sa < lo < sb:
            out.append(_lerp(a, b, (lo - sa) / (sb - sa)))
        elif not out and sa >= lo:
            out.append(a)
        if sb <= hi:
            out.append(b)
        if sa < hi < sb:
            out.append(_lerp(a, b, (hi - sa) / (sb - sa)))
    hidden = sum(1 for x in s if x < lo or x > hi)
    if hidden_out is not None:
        hidden_out.extend(p for p, x in zip(pts, s)
                          if x < lo - TRIM_MARGIN_M or x > hi + TRIM_MARGIN_M)
    return out, hidden


def visible_trace(rows: "Iterable[dict]", *, ends_m: "int | float" = DEFAULT_TRIM_M,
                  zones: "Sequence[PrivacyZone]" = ()) -> VisibleTrace:
    """The visible trace of a trip: fixes, ends trim, then privacy zones (R5)."""
    ends = check_trim(ends_m)
    fx = fixes(rows)
    vt = VisibleTrace(fixes=len(fx), has_gps=bool(fx))
    kept, vt.hidden_trim = trim_ends(fx, ends, ends, vt.trimmed)
    seg: "List[Point]" = []
    hit: "set[int]" = set()
    for p in kept:
        inside = [i for i, z in enumerate(zones) if z.contains(p.lat, p.lon)]
        if inside:
            vt.hidden_zone += 1
            hit.update(inside)
            if seg:
                vt.segments.append(seg)
                seg = []
            continue
        seg.append(p)
    if seg:
        vt.segments.append(seg)
    vt.segments = [sg for sg in vt.segments if len(sg) >= 2]
    vt.zones_hit = len(hit)
    return vt


# ---- stats (§5.4, R6) ------------------------------------------------------------------ #
def _median_filter(seg: "List[Point]") -> "List[float]":
    alts = [(p.t, p.alt) for p in seg if p.alt is not None]
    half = GAIN_FILTER_S * 1000 / 2
    out = []
    for t, _a in alts:
        win = [a for (u, a) in alts if abs(u - t) <= half]
        out.append(statistics.median(win))
    return out


def elevation_gain_m(segments: "List[List[Point]]") -> "float | None":
    """Visible altitude, 30 s median filter, sum of rises of at least 3 m."""
    if not any(p.alt is not None for seg in segments for p in seg):
        return None
    gain = 0.0
    for seg in segments:
        alts = _median_filter(seg)
        if not alts:
            continue
        ref = alts[0]
        for a in alts[1:]:
            if a - ref >= GAIN_STEP_M:
                gain += a - ref
                ref = a
            elif a < ref:
                ref = a
    return gain


def _speed_samples(rows: "Sequence[dict]", windows, speed_channel: "str | None",
                   segments) -> "List[float]":
    if speed_channel:
        out = []
        for r in rows:
            t, v = _num(r.get("Interval")), _num(r.get(speed_channel))
            if t is not None and v is not None and any(a <= t <= b for a, b in windows):
                out.append(v)
        if out:
            return out
    out = [p.spd for seg in segments for p in seg if p.spd is not None]
    if out:
        return out
    return [haversine_m(a.lat, a.lon, b.lat, b.lon) / ((b.t - a.t) / 1000) * 3.6
            for seg in segments for a, b in zip(seg, seg[1:]) if b.t > a.t]


def trace_stats(vt: VisibleTrace, rows: "Sequence[dict]" = (),
                speed_channel: "str | None" = None) -> dict:
    """Unrounded figures from the visible trace (§5.4): ``distance_m``, ``duration_s``,
    ``moving_s``, ``avg_kmh``, ``max_kmh``, ``gain_m``, ``stops``."""
    segs = vt.segments
    dist = vt.distance_m()
    duration = sum((seg[-1].t - seg[0].t) / 1000 for seg in segs)
    moving = 0.0
    stops = 0
    for seg in segs:
        still = 0.0
        for a, b in zip(seg, seg[1:]):
            dt = (b.t - a.t) / 1000
            if dt <= 0:
                continue
            v = haversine_m(a.lat, a.lon, b.lat, b.lon) / dt * 3.6
            if v >= MOVING_KMH:
                moving += dt
                if still >= STOP_S:
                    stops += 1
                still = 0.0
            else:
                still += dt
        if still >= STOP_S:
            stops += 1
    speeds = _speed_samples(rows, vt.windows(), speed_channel, segs)
    return {"distance_m": dist, "duration_s": duration, "moving_s": moving,
            "avg_kmh": dist / moving * 3.6 if moving > 0 else None,
            "max_kmh": max(speeds) if speeds else None,
            "gain_m": elevation_gain_m(segs), "stops": stops}


def no_gps_stats(rows: "Sequence[dict]", speed_channel: "str | None") -> dict:
    """A trip without fixes (§5.4): duration from the recording's relative time; distance
    only from an ECU road-speed signal, integrated over the trip less its first and last
    2 minutes."""
    ts = [t for t in (_num(r.get("Interval")) for r in rows) if t is not None]
    out = {"distance_m": None, "duration_s": (max(ts) - min(ts)) / 1000 if ts else None,
           "moving_s": None, "avg_kmh": None, "max_kmh": None, "gain_m": None, "stops": None}
    if speed_channel and ts:
        lo, hi = min(ts) + NO_GPS_EDGE_MS, max(ts) - NO_GPS_EDGE_MS
        samples = [(t, v) for t, v in ((_num(r.get("Interval")), _num(r.get(speed_channel)))
                                       for r in rows) if t is not None and v is not None]
        dist = moving = 0.0
        for (t0, v0), (t1, _v1) in zip(samples, samples[1:]):
            if lo <= t0 and t1 <= hi and t1 > t0:
                dt = (t1 - t0) / 1000
                dist += v0 / 3.6 * dt
                if v0 >= MOVING_KMH:
                    moving += dt
        if hi > lo:
            out["distance_m"] = dist
            out["moving_s"] = moving
            out["avg_kmh"] = dist / moving * 3.6 if moving > 0 else None
        speeds = [v for _t, v in samples]
        out["max_kmh"] = max(speeds) if speeds else None
    return out


def _round(v: "float | None", step: float) -> "float | int | None":
    if v is None:
        return None
    r = round(v / step) * step
    return int(r) if float(step).is_integer() else round(r, 6)


def round_stats(st: dict, card: bool) -> dict:
    """The rounding table of §5.4: ``card`` for L0 (1 km, 5 min, 5 km/h), else L1–L4
    (0.1 km, 1 min, 1 km/h, gain 10 m, stops counted). Distances in km, times in min."""
    km = None if st.get("distance_m") is None else st["distance_m"] / 1000
    dmin = None if st.get("duration_s") is None else st["duration_s"] / 60
    mmin = None if st.get("moving_s") is None else st["moving_s"] / 60
    if card:
        return {"distance_km": _round(km, 1), "duration_min": _round(dmin, 5),
                "moving_min": _round(mmin, 5), "avg_kmh": _round(st.get("avg_kmh"), 5),
                "max_kmh": _round(st.get("max_kmh"), 5)}
    return {"distance_km": _round(km, 0.1), "duration_min": _round(dmin, 1),
            "moving_min": _round(mmin, 1), "avg_kmh": _round(st.get("avg_kmh"), 1),
            "max_kmh": _round(st.get("max_kmh"), 1), "elevation_gain_m": _round(st.get("gain_m"), 10),
            "stops": st.get("stops")}


# ---- simplify and write (§5.3, R7) ---------------------------------------------------- #
def _enu(seg: "List[Point]") -> "List[Tuple[float, float]]":
    lat0 = math.radians(seg[0].lat)
    r = 6_371_008.8
    return [(math.radians(p.lon - seg[0].lon) * r * math.cos(lat0),
             math.radians(p.lat - seg[0].lat) * r) for p in seg]


def _perp(p, a, b) -> float:
    (x, y), (x1, y1), (x2, y2) = p, a, b
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def rdp(seg: "List[Point]", eps: float = RDP_EPSILON_M) -> "List[Point]":
    """Ramer–Douglas–Peucker on a local east-north plane (iterative)."""
    if len(seg) < 3:
        return list(seg)
    xy = _enu(seg)
    keep = [False] * len(seg)
    keep[0] = keep[-1] = True
    stack = [(0, len(seg) - 1)]
    while stack:
        i, j = stack.pop()
        best, idx = 0.0, -1
        for k in range(i + 1, j):
            d = _perp(xy[k], xy[i], xy[j])
            if d > best:
                best, idx = d, k
        if idx >= 0 and best > eps:
            keep[idx] = True
            stack += [(i, idx), (idx, j)]
    return [p for p, k in zip(seg, keep) if k]


def simplified(vt: VisibleTrace) -> "List[List[Tuple[float, float, Optional[float]]]]":
    """``[[(lat, lon, ele)]]`` per segment: RDP ε = 10 m, 5 decimals, elevation to 1 m."""
    out = []
    for seg in vt.segments:
        out.append([(round(p.lat, 5), round(p.lon, 5),
                     None if p.alt is None else float(round(p.alt))) for p in rdp(seg)])
    return out


def to_route_gpx(segs) -> str:
    """GPX 1.1: one ``<trkseg>`` per visible segment, ``<trkpt>`` with ``lat``, ``lon`` and
    an optional ``<ele>`` (1 m), never ``<time>``; no metadata name or time."""
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<gpx version="1.1" creator="openostler" xmlns="http://www.topografix.com/GPX/1/1">',
           "  <trk>"]
    for seg in segs:
        out.append("    <trkseg>")
        for lat, lon, ele in seg:
            pt = f'      <trkpt lat="{fmt_num(lat, 5)}" lon="{fmt_num(lon, 5)}">'
            if ele is not None:
                pt += f"<ele>{fmt_num(ele, 0)}</ele>"
            out.append(pt + "</trkpt>")
        out.append("    </trkseg>")
    out += ["  </trk>", "</gpx>"]
    return "\n".join(out) + "\n"


def to_route_geojson(segs) -> str:
    """GeoJSON: one ``MultiLineString`` Feature, no properties per point (§5.3)."""
    lines = [[[lon, lat] for lat, lon, _e in seg] for seg in segs]
    doc = {"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": {"type": "MultiLineString", "coordinates": lines},
         "properties": {}}]}
    return json.dumps(doc, separators=(",", ":")) + "\n"


__all__ = ["DEFAULT_TRIM_M", "MAX_TRIM_M", "MIN_SHARE_KM", "MIN_TRIM_M", "Point",
           "TrimRefused", "VisibleTrace", "check_trim", "elevation_gain_m", "fixes",
           "no_gps_stats", "rdp", "round_stats", "simplified", "to_route_geojson",
           "to_route_gpx", "trace_stats", "trim_ends", "visible_trace"]
