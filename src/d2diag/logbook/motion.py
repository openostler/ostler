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
"""
