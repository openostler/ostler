// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Chart-strip maths, pure. X is session time (never sample index), so a decimated series
 * (min/max per bucket, duplicate timestamps) lands on the same pixels as the full one and
 * the y-range keeps its peaks.
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented.
 */
import type { Note } from "../../api/schemas";
import { clamp, indexAt } from "../../state/playback";

export type View = { t0: number; t1: number };

export const MIN_VIEW_MS = 2_000;

export const xOf = (ms: number, v: View, width: number) => (v.t1 > v.t0 ? ((ms - v.t0) / (v.t1 - v.t0)) * width : 0);
export const msOf = (x: number, v: View, width: number) => (width > 0 ? v.t0 + (clamp(x, 0, width) / width) * (v.t1 - v.t0) : v.t0);

/** Min/max of the samples inside the view (nulls ignored), padded 5 % (a flat line gets ±1). */
export function yRange(t: readonly number[], values: readonly (number | null)[] | undefined, v: View): { lo: number; hi: number } | null {
  if (!values) return null;
  let lo = Infinity;
  let hi = -Infinity;
  const i0 = Math.max(0, indexAt(t, v.t0));
  for (let i = i0; i < t.length && t[i]! <= v.t1; i++) {
    const y = values[i];
    if (y == null || !Number.isFinite(y)) continue;
    if (y < lo) lo = y;
    if (y > hi) hi = y;
  }
  if (lo === Infinity) return null;
  if (hi === lo) return { lo: lo - 1, hi: hi + 1 };
  const pad = (hi - lo) * 0.05;
  return { lo: lo - pad, hi: hi + pad };
}

/**
 * Pixel polylines for one lane: one run per stretch of non-null samples (a null breaks the
 * line — a gap, never a drop to zero). One sample either side of the view is kept so the
 * line reaches the edges.
 */
export function lanePaths(
  t: readonly number[],
  values: readonly (number | null)[] | undefined,
  v: View,
  width: number,
  height: number,
  r: { lo: number; hi: number },
): [number, number][][] {
  if (!values || !t.length) return [];
  const runs: [number, number][][] = [];
  let run: [number, number][] = [];
  const i0 = Math.max(0, indexAt(t, v.t0) - 1);
  const yOf = (y: number) => height - ((y - r.lo) / (r.hi - r.lo)) * height;
  for (let i = i0; i < t.length; i++) {
    const y = values[i];
    if (y == null || !Number.isFinite(y)) {
      if (run.length) runs.push(run);
      run = [];
    } else {
      run.push([xOf(t[i]!, v, width), yOf(y)]);
    }
    if (t[i]! > v.t1) break;
  }
  if (run.length) runs.push(run);
  return runs;
}

/** Zoom to [a, b] (any order), at least MIN_VIEW_MS wide, inside [start, end]. */
export function zoomTo(a: number, b: number, start: number, end: number): View {
  let t0 = Math.min(a, b);
  let t1 = Math.max(a, b);
  const min = Math.min(MIN_VIEW_MS, end - start);
  if (t1 - t0 < min) {
    const mid = (t0 + t1) / 2;
    t0 = mid - min / 2;
    t1 = mid + min / 2;
  }
  if (t0 < start) { t1 += start - t0; t0 = start; }
  if (t1 > end) { t0 -= t1 - end; t1 = end; }
  return { t0: Math.max(start, t0), t1: Math.min(end, t1) };
}

/** Scale a view by `factor` (< 1 zooms in) around the time `at`. */
export function zoomAround(v: View, at: number, factor: number, start: number, end: number): View {
  return zoomTo(at - (at - v.t0) * factor, at + (v.t1 - at) * factor, start, end);
}

/** The zoomed window paged so that `time` is inside it (the cursor never leaves the chart
 * during playback); null zoom → the whole session. */
export function viewFor(zoom: View | null, time: number, start: number, end: number): View {
  if (!zoom) return { t0: start, t1: end };
  const w = zoom.t1 - zoom.t0;
  if (w <= 0 || (time >= zoom.t0 && time <= zoom.t1)) return zoom;
  const pages = Math.floor((time - zoom.t0) / w);
  return zoomTo(zoom.t0 + pages * w, zoom.t1 + pages * w, start, end);
}

/** About `n` round tick values across [lo, hi] (1, 2, 5 × 10^k steps). */
export function niceTicks(lo: number, hi: number, n = 3): number[] {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? 10 * mag;
  const out: number[] = [];
  for (let x = Math.ceil(lo / step) * step; x <= hi + 1e-9; x += step) out.push(+x.toFixed(10));
  return out;
}

/** Notes inside the view, as pixel spans (a point note has x0 = x1). */
export function noteSpans(notes: readonly Note[], v: View, width: number): { note: Note; x0: number; x1: number }[] {
  return notes
    .filter((n) => (n.t_end ?? n.t) >= v.t0 && n.t <= v.t1)
    .map((n) => ({ note: n, x0: Math.max(0, xOf(n.t, v, width)), x1: Math.min(width, xOf(n.t_end ?? n.t, v, width)) }));
}
