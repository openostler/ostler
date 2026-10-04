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

/** Sequential single-hue ramp (dataviz reference blue, steps 250 → 700): light = low, dark =
 * high. Starts at 250 so the lowest bucket still clears 2:1 on the light basemap. */
const STOPS = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];
/** Track points with no value for the channel. */
export const NO_VALUE_COLOR = "#9aa1a9";

function hexToRgb(h: string): [number, number, number] {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const toHex = (c: number[]) => `#${c.map((x) => Math.round(x).toString(16).padStart(2, "0")).join("")}`;

/** `n` colours evenly sampled along the stops (linear in sRGB between neighbouring steps). */
export function ramp(n = BUCKETS, stops: readonly string[] = STOPS): string[] {
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
export const RAMP = ramp();

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
