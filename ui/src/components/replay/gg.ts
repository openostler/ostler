// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * G-G diagram maths, pure (spec §5 "Map"): which acceleration channels to plot, the axis
 * limit, and the decimated point cloud. Conventions (ADR-0010, MoTeC/ISO): LateralAcc is
 * positive in a left turn, InlineAcc positive when accelerating, both in g. The plot draws
 * acceleration where it points: a left turn lands left of centre, acceleration above it.
 */
import type { SessionData } from "../../api/schemas";

export const RING_G = 0.5;
export const MAX_POINTS = 1500;

/** The pair to plot: the vehicle-frame accelerometer, else the GPS-derived pair; null = no panel. */
export function ggChannels(names: readonly string[]): { lat: string; lon: string } | null {
  if (names.includes("LateralAcc") && names.includes("InlineAcc")) return { lat: "LateralAcc", lon: "InlineAcc" };
  if (names.includes("GPS_LatAcc") && names.includes("GPS_LonAcc")) return { lat: "GPS_LatAcc", lon: "GPS_LonAcc" };
  return null;
}

/** Axis half-width in g: the largest |value| rounded up to the next ring, never under 1 g. */
export function ggLimit(maxAbs: number): number {
  if (!Number.isFinite(maxAbs) || maxAbs <= 0) return 1;
  return Math.max(1, Math.ceil(maxAbs / RING_G - 1e-9) * RING_G);
}

/** Ring radii (g) inside a limit: 0.5, 1.0, … */
export const ggRings = (limit: number): number[] => Array.from({ length: Math.floor(limit / RING_G + 1e-9) }, (_, i) => (i + 1) * RING_G);

/** Plot coordinates for a sample in a square of `size` px: centre is 0 g. */
export function ggXY(lat: number, lon: number, limit: number, size: number): [number, number] {
  const c = size / 2;
  const k = c / limit;
  return [c - lat * k, c - lon * k];
}

export type GGPoint = { lat: number; lon: number; speed: number | null; t: number };

/** Rows where both channels have a value, evenly thinned to at most `max` points. */
export function ggPoints(data: Pick<SessionData, "t" | "ch">, ch: { lat: string; lon: string }, speed: string | null, max = MAX_POINTS): { points: GGPoint[]; maxAbs: number } {
  const la = data.ch[ch.lat];
  const lo = data.ch[ch.lon];
  const sp = speed ? data.ch[speed] : undefined;
  const all: GGPoint[] = [];
  let maxAbs = 0;
  if (!la || !lo) return { points: all, maxAbs };
  let lastSpeed: number | null = null;
  for (let i = 0; i < data.t.length; i++) {
    const s = sp?.[i];
    if (s != null) lastSpeed = s;
    const a = la[i];
    const b = lo[i];
    if (a == null || b == null || !Number.isFinite(a) || !Number.isFinite(b)) continue;
    all.push({ lat: a, lon: b, speed: lastSpeed, t: data.t[i]! });
    maxAbs = Math.max(maxAbs, Math.abs(a), Math.abs(b));
  }
  if (all.length <= max) return { points: all, maxAbs };
  const step = all.length / max;
  return { points: Array.from({ length: max }, (_, k) => all[Math.floor(k * step)]!), maxAbs };
}
