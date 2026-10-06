// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The map trace: GPS track → line segments colour-bucketed by a channel, the legend, and the
 * cursor position/heading. Pure (no MapLibre), so the maths is unit-tested in jsdom.
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented: the trace is cut
 * into runs of equal colour bucket, each a GeoJSON LineString whose `b` property drives a
 * data-driven `line-color` expression.
 */
import type { SessionData, SessionMeta } from "../../api/schemas";
import { indexAt, valueAt } from "../../state/playback";

export const BUCKETS = 20;

/**
 * Trace ramps (spec §5 "Map"): perceptually ordered, CVD-safe, sampled from the matplotlib /
 * seaborn tables. Both are trimmed so neither end is near black (plasma loses its darkest
 * 12 %, mako its darkest 22 % and lightest 3 %), and both run dark = low → light = high so
 * the two lanes read the same way. Trace A = plasma (warm), B = mako (cool). "Classic colours"
 * are plain two-colour gradients: A blue → red (low → high, the RS3/RaceChrono convention),
 * B green → purple, so the two lanes stay distinguishable.
 */
export const RAMP_STOPS = {
  plasma: ["#4b03a1", "#6e00a8", "#8e0ca4", "#ac2694", "#c43e7f", "#d9586a", "#e97257", "#f79044", "#fdaf31", "#fbd324", "#f0f921"],
  mako: ["#3b2e5d", "#413e7f", "#3c5397", "#366a9f", "#3480a4", "#3496a9", "#39abac", "#48c0ad", "#6dd3ad", "#a4e0bb", "#ceeed7"],
  classicA: ["#2166ac", "#b2182b"],
  classicB: ["#1b7837", "#762a83"],
} as const;
export type RampName = keyof typeof RAMP_STOPS;
/** Track points with no value for the channel. */
export const NO_VALUE_COLOR = "#9aa1a9";

function hexToRgb(h: string): [number, number, number] {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const toHex = (c: number[]) => `#${c.map((x) => Math.round(x).toString(16).padStart(2, "0")).join("")}`;

/** WCAG relative luminance (0 … 1) of a #rrggbb colour. */
export function luminance(hex: string): number {
  const [r, g, b] = hexToRgb(hex).map((c) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  }) as [number, number, number];
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** `n` colours evenly sampled along the stops (linear in sRGB between neighbouring steps). */
export function ramp(n = BUCKETS, stops: readonly string[] = RAMP_STOPS.plasma): string[] {
  if (n === 1) return [stops[0]!];
  return Array.from({ length: n }, (_, i) => {
    const pos = (i / (n - 1)) * (stops.length - 1);
    const k = Math.min(stops.length - 2, Math.floor(pos));
    const f = pos - k;
    const a = hexToRgb(stops[k]!);
    const b = hexToRgb(stops[k + 1]!);
    return toHex(a.map((x, j) => x + (b[j]! - x) * f));
  });
}
export const RAMPS: Record<RampName, string[]> = {
  plasma: ramp(BUCKETS, RAMP_STOPS.plasma),
  mako: ramp(BUCKETS, RAMP_STOPS.mako),
  classicA: ramp(BUCKETS, RAMP_STOPS.classicA),
  classicB: ramp(BUCKETS, RAMP_STOPS.classicB),
};
/** Trace A's default ramp. */
export const RAMP = RAMPS.plasma;

/** The ramp for a lane: A plasma, B mako; "classic" = two-colour gradients (A blue → red, B green → purple). */
export const laneRamp = (lane: TraceLane, classic = false): string[] =>
  lane === "a" ? (classic ? RAMPS.classicA : RAMPS.plasma) : (classic ? RAMPS.classicB : RAMPS.mako);

/** The two traces. A is drawn on the left of the direction of travel, B on the right. */
export type TraceLane = "a" | "b";
/** MapLibre `line-offset` per lane, px (positive = right of the line direction). */
export const LANE_OFFSET: Record<TraceLane, number> = { a: -3, b: 3 };
/** Douglas–Peucker tolerance for the drawn track, metres. */
export const SMOOTH_M = 1;

export type Range = { min: number; max: number };

/** Min/max ignoring nulls (null when the channel has no values at all). */
export function rangeOf(values: readonly (number | null)[] | undefined): Range | null {
  let min = Infinity;
  let max = -Infinity;
  for (const v of values ?? []) {
    if (v == null || !Number.isFinite(v)) continue;
    if (v < min) min = v;
    if (v > max) max = v;
  }
  return min === Infinity ? null : { min, max };
}

/** The bucket (0 … n-1) a value falls into; null for a missing value. A flat channel
 * (min = max) lands in the middle bucket. */
export function bucketOf(v: number | null, r: Range | null, n = BUCKETS): number | null {
  if (v == null || !r) return null;
  if (r.max <= r.min) return Math.floor(n / 2);
  const f = (v - r.min) / (r.max - r.min);
  return Math.min(n - 1, Math.max(0, Math.floor(f * n)));
}

/** MapLibre `line-color`: match the feature's bucket `b` to the ramp; -1 → no-value grey. */
export function lineColorExpression(colors: readonly string[] = RAMP): unknown[] {
  const pairs = colors.flatMap((c, i) => [i, c]);
  return ["match", ["get", "b"], ...pairs, NO_VALUE_COLOR];
}

/** CSS gradient for the legend bar (the same ramp, low → high, left → right). */
export const legendGradient = (colors: readonly string[] = RAMP) => `linear-gradient(to right, ${colors.join(", ")})`;

export type LineFeature = {
  type: "Feature";
  properties: { b: number };
  geometry: { type: "LineString"; coordinates: [number, number][] };
};
export type FeatureCollection = { type: "FeatureCollection"; features: LineFeature[] };

/**
 * Cut the track into runs of equal bucket. Each run is one LineString that starts at the
 * last point of the previous run, so the coloured line has no gaps between runs.
 */
export function traceSegments(data: Pick<SessionData, "t" | "ch" | "track">, channel: string, r: Range | null = rangeOf(data.ch[channel])): FeatureCollection {
  const values = data.ch[channel];
  const features: LineFeature[] = [];
  const track = data.track;
  let cur: LineFeature | null = null;
  for (let i = 0; i < track.length; i++) {
    const [lon, lat, ms] = track[i]!;
    const b = bucketOf(valueAt(data.t, values, ms), r) ?? -1;
    const pt: [number, number] = [lon, lat];
    const last = cur as LineFeature | null;
    if (last && last.properties.b === b) {
      last.geometry.coordinates.push(pt);
      continue;
    }
    const prev: [number, number] | undefined = last?.geometry.coordinates[last.geometry.coordinates.length - 1];
    cur = { type: "Feature", properties: { b }, geometry: { type: "LineString", coordinates: prev ? [prev, pt] : [pt] } };
    features.push(cur);
  }
  // A lone first point can't draw a line; keep only drawable runs.
  return { type: "FeatureCollection", features: features.filter((f) => f.geometry.coordinates.length > 1) };
}

/** Initial bearing from a to b, degrees clockwise from north (0 … 360). */
export function bearing(a: readonly [number, number], b: readonly [number, number]): number {
  const toRad = Math.PI / 180;
  const [lon1, lat1] = [a[0] * toRad, a[1] * toRad];
  const [lon2, lat2] = [b[0] * toRad, b[1] * toRad];
  const y = Math.sin(lon2 - lon1) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(lon2 - lon1);
  return ((Math.atan2(y, x) / toRad) + 360) % 360;
}

export type Cursor = { lon: number; lat: number; heading: number | null };

/** The cursor on the track at session time `ms`: interpolated position; heading from the
 * GPS_Heading channel when present, else the bearing of the current track segment. */
export function cursorAt(data: Pick<SessionData, "t" | "ch" | "track">, ms: number, times: readonly number[] = data.track.map((p) => p[2])): Cursor | null {
  const tr = data.track;
  if (!tr.length) return null;
  const i = indexAt(times, ms);
  const a = tr[i]!;
  const b = tr[Math.min(tr.length - 1, i + 1)]!;
  const span = b[2] - a[2];
  const f = span > 0 ? Math.min(1, Math.max(0, (ms - a[2]) / span)) : 0;
  const lon = a[0] + (b[0] - a[0]) * f;
  const lat = a[1] + (b[1] - a[1]) * f;
  let heading = valueAt(data.t, data.ch.GPS_Heading, ms);
  if (heading == null) {
    const [p, q] = i + 1 < tr.length ? [a, b] : [tr[Math.max(0, i - 1)]!, a];
    heading = p[0] === q[0] && p[1] === q[1] ? null : bearing([p[0], p[1]], [q[0], q[1]]);
  }
  return { lon, lat, heading };
}

export type BBox = [number, number, number, number];

/** [minLon, minLat, maxLon, maxLat] of the track (null when empty). */
export function bboxOf(track: SessionData["track"]): BBox | null {
  if (!track.length) return null;
  const b: BBox = [Infinity, Infinity, -Infinity, -Infinity];
  for (const [lon, lat] of track) {
    b[0] = Math.min(b[0], lon); b[1] = Math.min(b[1], lat);
    b[2] = Math.max(b[2], lon); b[3] = Math.max(b[3], lat);
  }
  return b;
}

/** Channels never offered for the trace or chart: text channels and the raw coordinates. */
const NOT_PLOTTABLE = new Set(["module", "faults", "GPS_Latitude", "GPS_Longitude"]);

export const plottable = (meta: SessionMeta): string[] =>
  meta.channels.map((c) => c.name).filter((n) => !NOT_PLOTTABLE.has(n));

/** Default trace channel: ECU `speed`, else `GPS_Speed`, else the first plottable one. */
export function defaultTraceChannel(names: readonly string[]): string | null {
  if (names.includes("speed")) return "speed";
  if (names.includes("GPS_Speed")) return "GPS_Speed";
  return names[0] ?? null;
}

/**
 * Douglas–Peucker simplification of the track (lon, lat, t kept together) with a tolerance in
 * metres, on a local equirectangular projection. It removes GPS jitter so the offset lanes
 * stay parallel instead of zig-zagging (spec §5: "~1 m smooth").
 */
export function simplifyTrack(track: SessionData["track"], toleranceM = SMOOTH_M): SessionData["track"] {
  if (track.length < 3 || toleranceM <= 0) return track.slice();
  const lat0 = track[0]![1];
  const mPerDegLat = 111_320;
  const mPerDegLon = 111_320 * Math.cos((lat0 * Math.PI) / 180);
  const xy = track.map(([lon, lat]) => [lon * mPerDegLon, lat * mPerDegLat] as const);
  const keep = new Uint8Array(track.length);
  keep[0] = 1;
  keep[track.length - 1] = 1;
  const stack: [number, number][] = [[0, track.length - 1]];
  const tol2 = toleranceM * toleranceM;
  while (stack.length) {
    const [i, j] = stack.pop()!;
    const [ax, ay] = xy[i]!;
    const [bx, by] = xy[j]!;
    const dx = bx - ax;
    const dy = by - ay;
    const len2 = dx * dx + dy * dy;
    let worst = -1;
    let worstD = tol2;
    for (let k = i + 1; k < j; k++) {
      const [px, py] = xy[k]!;
      let f = len2 > 0 ? ((px - ax) * dx + (py - ay) * dy) / len2 : 0;
      f = Math.max(0, Math.min(1, f));
      const ex = ax + f * dx - px;
      const ey = ay + f * dy - py;
      const d = ex * ex + ey * ey;
      if (d > worstD) { worstD = d; worst = k; }
    }
    if (worst > 0) {
      keep[worst] = 1;
      stack.push([i, worst], [worst, j]);
    }
  }
  return track.filter((_, k) => keep[k]);
}

/**
 * A polyline moved sideways by `d` px (positive = right of the direction of travel, as
 * MapLibre's `line-offset`) in screen space (y down). Each vertex moves along the average of
 * its neighbouring segment normals (a mitred join, capped at 2 × d for sharp turns). Used by
 * the SVG fallback to draw the two lanes the way the map does.
 */
export function offsetPolyline(pts: readonly (readonly [number, number])[], d: number): [number, number][] {
  if (pts.length < 2 || d === 0) return pts.map((p) => [p[0], p[1]]);
  const normals: [number, number][] = [];
  for (let i = 0; i + 1 < pts.length; i++) {
    const dx = pts[i + 1]![0] - pts[i]![0];
    const dy = pts[i + 1]![1] - pts[i]![1];
    const len = Math.hypot(dx, dy);
    // Right-hand normal in y-down screen space: (−dy, dx) / len.
    normals.push(len > 0 ? [-dy / len, dx / len] : normals[normals.length - 1] ?? [0, 0]);
  }
  return pts.map((p, i) => {
    const n0 = normals[Math.max(0, i - 1)]!;
    const n1 = normals[Math.min(normals.length - 1, i)]!;
    let nx = n0[0] + n1[0];
    let ny = n0[1] + n1[1];
    const len = Math.hypot(nx, ny);
    if (len < 1e-9) { nx = n1[0]; ny = n1[1]; } else {
      // Mitre: scale so the offset from each segment is d (capped at 2d).
      const cos = (nx * n1[0] + ny * n1[1]) / len;
      const k = Math.min(2, 1 / Math.max(cos, 0.5));
      nx = (nx / len) * k;
      ny = (ny / len) * k;
    }
    return [p[0] + nx * d, p[1] + ny * d];
  });
}
