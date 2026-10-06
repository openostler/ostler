// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Sample } from "../state/live";
import { HISTORY_LEN } from "../state/live";

const COLORS = ["var(--ic-blue)", "var(--ic-green)", "var(--ic-yellow)"];

/** Up to three channels over the last ~60 samples, each scaled to its own range. */
export function Trend({ channels, history, labelOf, unitOf }: {
  channels: string[];
  history: Record<string, Sample[]>;
  labelOf: (n: string) => string;
  unitOf: (n: string) => string;
}) {
  const shown = channels.slice(0, 3);
  return (
    <div className="card">
      {shown.length ? (
        <div className="row wrap" style={{ gap: 14, marginBottom: 6 }}>
          {shown.map((n, i) => {
            const vs = (history[n] ?? []).map((p) => p.v);
            const cur = vs.length ? vs[vs.length - 1] : null;
            return (
              <span key={n} className="row small muted" style={{ gap: 6 }}>
                <span style={{ width: 14, height: 2, background: COLORS[i] }} />
                {labelOf(n)}
                <b style={{ color: "var(--fg)" }}>{cur != null ? cur.toFixed(1) : "–"}{unitOf(n)}</b>
                {vs.length ? (
                  <span className="dis">({Math.min(...vs).toFixed(1)}–{Math.max(...vs).toFixed(1)})</span>
                ) : null}
              </span>
            );
          })}
        </div>
      ) : null}
      <svg viewBox="0 0 640 160" preserveAspectRatio="none" style={{ width: "100%", height: 150, display: "block" }}
        role="img" aria-label="Trend of the selected channels over the last minute">
        {[40, 80, 120].map((y) => <line key={y} x1="0" y1={y} x2="640" y2={y} stroke="var(--border)" />)}
        {shown.map((n, i) => {
          const h = history[n] ?? [];
          if (h.length < 2) return null;
          const vs = h.map((p) => p.v);
          const lo = Math.min(...vs);
          const span = Math.max(...vs) - lo || 1;
          const pts = h
            .map((p, j) => `${((j / (HISTORY_LEN - 1)) * 640).toFixed(1)},${(150 - ((p.v - lo) / span) * 140).toFixed(1)}`)
            .join(" ");
          return <polyline key={n} fill="none" stroke={COLORS[i]} strokeWidth="2" points={pts} />;
        })}
      </svg>
      <div className="row small dis" style={{ justifyContent: "space-between" }}>
        <span>−60 s</span><span>−30 s</span><span>NOW</span>
      </div>
    </div>
  );
}
