// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Sample } from "../state/live";
import { HISTORY_LEN } from "../state/live";

/** The last ~60 s of one signal: a thin neutral line, current point marked. No axes —
 * it shows shape and direction; the number above it carries the value. Waits for a few
 * samples so a fresh connection does not draw a jagged scribble. */
export function Sparkline({ samples, label }: { samples: Sample[]; label: string }) {
  if (samples.length < 5) return <svg className="spark" aria-hidden="true" />;
  const vs = samples.map((s) => s.v);
  const lo = Math.min(...vs);
  const hi = Math.max(...vs);
  const span = hi - lo || 1;
  const W = 100;
  const H = 28;
  // fills from the right as history builds up, so "now" is always at the right edge
  const x = (i: number) => ((Math.max(HISTORY_LEN, samples.length) - samples.length + i) / (Math.max(HISTORY_LEN, samples.length) - 1)) * W;
  const y = (v: number) => H - 3 - ((v - lo) / span) * (H - 6);
  const pts = samples.map((s, i) => `${x(i).toFixed(1)},${y(s.v).toFixed(1)}`).join(" ");
  const last = samples[samples.length - 1]!;
  return (
    <svg className="spark" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img"
      aria-label={`${label}, last minute: ${lo.toFixed(1)} to ${hi.toFixed(1)}`}>
      <polyline className="line" points={pts} vectorEffect="non-scaling-stroke" />
      <circle className="now" cx={x(samples.length - 1)} cy={y(last.v)} r="2" />
    </svg>
  );
}
