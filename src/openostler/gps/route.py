# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The synthetic demo drive: a parametric loop with a speed profile (ADR-0009).

Used by ``MockGps`` and ``tools/make_demo_session.py``. The loop is **not a road**: it is
a smooth closed curve drawn over empty open moorland (Rannoch Moor, Scottish Highlands),
far from any address. One lap takes ``PERIOD_S`` seconds and ends where it started, so the
mock source can loop forever. Everything is a pure function of ``t``, so it is
deterministic.
"""
from __future__ import annotations

import bisect
import math

PERIOD_S = 720.0  # one lap = the 12-minute demo drive
CENTER_LAT = 56.6220  # open moor south of Loch Laidon — no buildings, no addresses
CENTER_LON = -4.6800
BASE_ALT_M = 310.0
_M_PER_DEG_LAT = 111_320.0

# (t_s, speed_kmh) keyframes; cosine-eased between them.
_PROFILE = [
    (0, 0), (20, 0), (45, 50), (60, 52), (110, 48), (125, 0), (145, 0),
    (175, 88), (230, 92), (290, 87), (330, 90), (345, 40), (380, 42), (400, 80),
    (460, 86), (515, 83), (535, 0), (560, 0), (590, 62), (640, 58), (680, 60),
    (700, 0), (720, 0),
]
_DT = 0.1


def speed_at(t: float) -> float:
    """Speed (km/h) at ``t`` seconds into the lap (wraps at ``PERIOD_S``)."""
    t = t % PERIOD_S
    for (t0, v0), (t1, v1) in zip(_PROFILE, _PROFILE[1:]):
        if t0 <= t <= t1:
            if t1 == t0:
                return float(v1)
            x = (t - t0) / (t1 - t0)
            e = (1 - math.cos(math.pi * x)) / 2
            return v0 + (v1 - v0) * e
    return 0.0


def _shape(theta: float) -> "tuple[float, float]":
    """Unit loop in local metres (x east, y north) before scaling: a lopsided oval."""
    x = math.cos(theta) + 0.18 * math.cos(2 * theta) + 0.06 * math.sin(3 * theta)
    y = 0.62 * math.sin(theta) + 0.12 * math.sin(2 * theta + 0.7)
    return x, y


def _build() -> "tuple[list[float], list[float], list[float], list[float], float]":
    # distance travelled vs time
    ts, ds = [0.0], [0.0]
    n = int(PERIOD_S / _DT)
    for i in range(1, n + 1):
        t = i * _DT
        v = (speed_at(t - _DT / 2) / 3.6)
        ts.append(t)
        ds.append(ds[-1] + v * _DT)
    total = ds[-1]
    # arc length of the unit shape
    m = 4000
    pts = [_shape(2 * math.pi * k / m) for k in range(m + 1)]
    arc = [0.0]
    for a, b in zip(pts, pts[1:]):
        arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    scale = total / arc[-1]
    return ts, ds, [a * scale for a in arc], [2 * math.pi * k / m for k in range(m + 1)], scale


_TS, _DS, _ARC, _THETA, _SCALE = _build()
LAP_M = _DS[-1]


def _interp(xs: "list[float]", ys: "list[float]", x: float) -> float:
    i = bisect.bisect_right(xs, x)
    if i <= 0:
        return ys[0]
    if i >= len(xs):
        return ys[-1]
    x0, x1 = xs[i - 1], xs[i]
    return ys[i - 1] + (ys[i] - ys[i - 1]) * ((x - x0) / (x1 - x0) if x1 > x0 else 0.0)


def _pos(dist: float) -> "tuple[float, float]":
    theta = _interp(_ARC, _THETA, dist % _ARC[-1])
    x, y = _shape(theta)
    return x * _SCALE, y * _SCALE


def demo_route(t: float) -> dict:
    """Position and motion at ``t`` seconds (wraps every lap).

    Returns ``{lat, lon, speed_kmh, heading, alt_m, dist_m}``; ``dist_m`` is the distance
    driven since the start of the lap.
    """
    t = t % PERIOD_S
    dist = _interp(_TS, _DS, t)
    x, y = _pos(dist)
    x2, y2 = _pos(dist + 2.0)
    heading = math.degrees(math.atan2(x2 - x, y2 - y)) % 360.0
    lat = CENTER_LAT + y / _M_PER_DEG_LAT
    lon = CENTER_LON + x / (_M_PER_DEG_LAT * math.cos(math.radians(CENTER_LAT)))
    alt = BASE_ALT_M + 12.0 * math.sin(2 * math.pi * dist / LAP_M) + 4.0 * math.sin(
        6 * math.pi * dist / LAP_M)
    return {"lat": lat, "lon": lon, "speed_kmh": speed_at(t), "heading": heading,
            "alt_m": alt, "dist_m": dist}
