# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acceleration channels (ADR-0010; spec §3). Core: never imports web.

Contract:
* ``to_vehicle(sample_xyz, matrix) -> (inline_g, lateral_g, vertical_g)`` — matrix is 3x3
  sensor→vehicle; inline + when accelerating, lateral + in a LEFT turn, vertical + up with
  gravity removed; inputs m/s² (accelerationIncludingGravity), outputs g.
* ``level_matrix(gravity_xyz, forward_xyz=None) -> matrix`` — from a stationary gravity average
  (+ optional forward vector, e.g. GPS-correlated).
* ``GpsAccel()``: ``feed(t_ms, speed_kmh, heading_deg) -> (lon_g, lat_g) | None`` — Δv/Δt and
  v·Δψ/Δt, smoothed.
Channel names: ``Acc_X/Y/Z`` (raw m/s²), ``InlineAcc``/``LateralAcc``/``VerticalAcc`` (g),
``GPS_LonAcc``/``GPS_LatAcc`` (g).

Conventions. The vehicle frame is x forward, y left, z up (right-handed; ISO 8855). Inputs
are *specific force* as ``accelerationIncludingGravity`` reports it: at rest the vector
points UP with magnitude g (a phone lying face up reads ``(0, 0, +9.81)``). ``matrix`` rows
are the vehicle x/y/z axes expressed in sensor coordinates, so ``v = M · s``.
"""
from __future__ import annotations

import math
from collections import deque

G = 9.80665
IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _norm(v):
    n = math.sqrt(sum(x * x for x in v))
    if n < 1e-9:
        raise ValueError("zero-length vector")
    return tuple(x / n for x in v)


def _dot(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def valid_matrix(matrix) -> bool:
    try:
        return (len(matrix) == 3 and all(len(r) == 3 for r in matrix)
                and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                        and math.isfinite(x) for r in matrix for x in r))
    except TypeError:
        return False


def rotate(sample_xyz, matrix=IDENTITY):
    """``M · s`` (sensor → vehicle), in the input units."""
    return tuple(_dot(row, sample_xyz) for row in matrix)


def to_vehicle(sample_xyz, matrix=IDENTITY) -> "tuple[float, float, float]":
    """Specific force in m/s² (sensor frame) → ``(inline_g, lateral_g, vertical_g)``.
    Gravity (+1 g on the vehicle's up axis at rest) is removed from vertical."""
    x, y, z = rotate(sample_xyz, matrix)
    return x / G, y / G, z / G - 1.0


def level_matrix(gravity_xyz, forward_xyz=None) -> "list[list[float]]":
    """The sensor→vehicle matrix from a stationary average of the specific force (points up)
    and optionally a forward direction in sensor coordinates (e.g. the mean specific force
    while accelerating in a straight line minus gravity). Without one, the sensor axis most
    perpendicular to gravity (x, else y) is taken as forward."""
    z = _norm(gravity_xyz)
    if forward_xyz is None:
        ax = (1.0, 0.0, 0.0) if abs(z[0]) < 0.9 else (0.0, 1.0, 0.0)
        forward_xyz = ax
    f = tuple(forward_xyz)
    d = _dot(f, z)
    x = _norm(tuple(fi - d * zi for fi, zi in zip(f, z)))
    y = _cross(z, x)  # x × y = z  ⇒  y = z × x (left)
    return [list(x), list(y), list(z)]


def _wrap180(d: float) -> float:
    return (d + 180.0) % 360.0 - 180.0


class GpsAccel:
    """Longitudinal and lateral acceleration (g) from GPS speed and heading.

    Each value is a difference across a ~``window_ms`` sliding window (a centred-ish
    smoother that keeps the 5–10 Hz GPS noise down). Heading is clockwise from north, so a
    left turn makes it decrease; lateral is ``−v·dψ/dt`` and positive in a left turn.
    Heading is ignored below ``min_kmh`` (stationary GPS heading is noise)."""

    def __init__(self, window_ms: float = 1000.0, min_kmh: float = 3.0,
                 gap_ms: float = 5000.0) -> None:
        self.window_ms, self.min_kmh, self.gap_ms = window_ms, min_kmh, gap_ms
        self._buf: "deque[tuple[float, float, float | None]]" = deque()
        self._psi = 0.0  # unwrapped heading

    def reset(self) -> None:
        self._buf.clear()

    def feed(self, t_ms, speed_kmh, heading_deg) -> "tuple[float, float] | None":
        if t_ms is None or speed_kmh is None:
            return None
        t_ms, v = float(t_ms), float(speed_kmh) / 3.6
        if self._buf:
            if t_ms <= self._buf[-1][0]:
                return None  # a repeated or out-of-order epoch
            if t_ms - self._buf[-1][0] > self.gap_ms:
                self._buf.clear()  # a GPS outage: start over
        psi = None
        if heading_deg is not None and speed_kmh >= self.min_kmh:
            last = next((p for _, _, p in reversed(self._buf) if p is not None), None)
            h = float(heading_deg)
            psi = h if last is None else last + _wrap180(h - last)
        self._buf.append((t_ms, v, psi))
        while len(self._buf) > 2 and t_ms - self._buf[1][0] >= self.window_ms:
            self._buf.popleft()
        if len(self._buf) < 2:
            return None
        t0, v0, p0 = self._buf[0]
        dt = (t_ms - t0) / 1000.0
        if dt <= 0:
            return None
        lon = (v - v0) / dt / G
        lat = 0.0
        if p0 is not None and psi is not None:
            vm = (v + v0) / 2.0
            lat = -vm * math.radians(psi - p0) / dt / G
        return lon, lat


__all__ = ["G", "IDENTITY", "to_vehicle", "level_matrix", "rotate", "valid_matrix",
           "GpsAccel"]
