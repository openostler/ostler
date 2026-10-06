// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The G-G panel (spec §5 "Map"): lateral vs inline acceleration, 0.5 g rings, each sample
 * coloured by speed (the mako ramp — speed is magnitude), and a dot at the replay cursor.
 * Shown only when the session has acceleration channels.
 */
import { useMemo } from "react";
import type { SessionData } from "../../api/schemas";
import { fmt } from "../../lib/format";
import { valueAt } from "../../state/playback";
import { ggChannels, ggLimit, ggPoints, ggRings, ggXY } from "./gg";
import { bucketOf, NO_VALUE_COLOR, RAMPS, rangeOf } from "./trace";

const SIZE = 220;

export function GGPanel({ data, names, speed, t }: { data: SessionData; names: readonly string[]; speed: string | null; t: number }) {
  const ch = useMemo(() => ggChannels(names), [names]);
  const cloud = useMemo(() => (ch ? ggPoints(data, ch, speed) : null), [data, ch, speed]);
  const sr = useMemo(() => (speed ? rangeOf(data.ch[speed]) : null), [data, speed]);
  if (!ch || !cloud || !cloud.points.length) return null;
  const limit = ggLimit(cloud.maxAbs);
  const c = SIZE / 2;
  const k = c / limit;
  const lat = valueAt(data.t, data.ch[ch.lat], t, 5);
  const lon = valueAt(data.t, data.ch[ch.lon], t, 5);
  const cur = lat != null && lon != null ? ggXY(lat, lon, limit, SIZE) : null;
  const gps = ch.lat.startsWith("GPS_");
  return (
    <div className="card replay-gg" data-limit={limit}>
      <div className="replay-gg-head">
        <span className="kicker">G-G</span>
        <span className="small muted">{gps ? "from GPS" : "accelerometer"} · coloured by speed</span>
      </div>
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="replay-gg-svg" role="img"
        aria-label={`Lateral against inline acceleration, ±${fmt(limit, 1)} g${cur ? `; now ${fmt(lat, 2)} g lateral, ${fmt(lon, 2)} g inline` : ""}`}>
        <line x1={0} y1={c} x2={SIZE} y2={c} className="replay-gg-axis" />
        <line x1={c} y1={0} x2={c} y2={SIZE} className="replay-gg-axis" />
        {ggRings(limit).map((r) => (
          <g key={r}>
            <circle cx={c} cy={c} r={r * k} className="replay-gg-ring" data-ring={r} />
            <text x={c + 3} y={c - r * k + 11} className="replay-gg-tick">{fmt(r, 1)} g</text>
          </g>
        ))}
        {cloud.points.map((p, i) => {
          const [x, y] = ggXY(p.lat, p.lon, limit, SIZE);
          const b = bucketOf(p.speed, sr);
          return <circle key={i} cx={x} cy={y} r={2} fill={b == null ? NO_VALUE_COLOR : RAMPS.mako[b]} fillOpacity={0.75} />;
        })}
        {cur ? <circle cx={cur[0]} cy={cur[1]} r={6} className="replay-gg-cursor" data-testid="gg-cursor" /> : null}
        <text x={4} y={c - 4} className="replay-gg-tick">Left</text>
        <text x={SIZE - 4} y={c - 4} textAnchor="end" className="replay-gg-tick">Right</text>
        <text x={c + 3} y={SIZE - 4} className="replay-gg-tick">Brake</text>
      </svg>
    </div>
  );
}
