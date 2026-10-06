// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/** Geometry for range bars and gauges: where a value and the normal band sit on a span. */
export type Span = readonly [number, number];

/** Fraction (0..1) of `v` along `span`, clamped; `clamped` says which end it hit. */
export function position(v: number, span: Span): { f: number; clamped: "low" | "high" | null } {
  const [lo, hi] = span;
  if (hi === lo) return { f: 0.5, clamped: null };
  const f = (v - lo) / (hi - lo);
  if (f < 0) return { f: 0, clamped: "low" };
  if (f > 1) return { f: 1, clamped: "high" };
  return { f, clamped: null };
}

/** The normal band as fractions of the span (clipped), or null when there is none. */
export function bandFractions(normal: Span | null | undefined, span: Span): [number, number] | null {
  if (!normal) return null;
  const a = position(normal[0], span).f;
  const b = position(normal[1], span).f;
  return b > a ? [a, b] : null;
}

/** Is `v` inside the healthy band? Null when no band is defined. */
export function inBand(v: number, normal: Span | null | undefined): boolean | null {
  if (!normal) return null;
  return v >= normal[0] && v <= normal[1];
}

/** Compact number for range legends: 4800 → "4.8k", 0.85 → "0.85". */
export function short(n: number): string {
  if (Math.abs(n) >= 1000) return `${+(n / 1000).toFixed(1)}k`;
  return `${+n.toFixed(2)}`;
}
