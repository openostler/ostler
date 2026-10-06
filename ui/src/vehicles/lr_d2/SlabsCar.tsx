// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Field, SignalValue } from "../../api/schemas";
import { fmt } from "../../lib/format";
import { RangeBar } from "../../components/RangeBar";

// Readouts sit OUTSIDE the body (x 45 / 255); wheels hug the body edge.
const WHEELS = [
  { id: "fl", x: 45, y: 82, label: "FL", wx: 94 },
  { id: "fr", x: 255, y: 82, label: "FR", wx: 186 },
  { id: "rl", x: 45, y: 242, label: "RL", wx: 94 },
  { id: "rr", x: 255, y: 242, label: "RR", wx: 186 },
] as const;

/** SLABS at a glance: a top-down Discovery with wheel speed + ABS sensor voltage at each
 * wheel and the rear ride heights against their normal band. Wheel order is still a
 * candidate on the car (test plan T-14) — the diagram says so. */
export function SlabsCar({ signals, fields }: { signals: Record<string, SignalValue>; fields: Record<string, Field> }) {
  const val = (n: string) => (typeof signals[n]?.v === "number" ? (signals[n]!.v as number) : null);
  const bad = (n: string) => signals[n]?.s === "low" || signals[n]?.s === "high";
  const height = (side: "left" | "right") => {
    const n = `height_${side}`;
    const f = fields[n];
    return (
      <div className="stat" key={side}>
        <div className="stat-top"><span className="stat-label">Height {side}</span>
          <span className="small dis">{val(`${n}_mm`) != null ? `${fmt(val(`${n}_mm`), 0)} mm` : ""}</span></div>
        <div className="stat-value" style={{ fontSize: 34 }}><span className="cv-num">{fmt(val(n), 0)}</span><span className="cv-unit">raw</span></div>
        {f?.span ? <RangeBar value={val(n)} span={f.span} normal={f.normal} alarm={bad(n)} label={`Height ${side}`} /> : null}
      </div>
    );
  };
  return (
    <div className="tile" style={{ gridColumn: "1 / -1" }}>
      <svg viewBox="0 0 300 320" className="car" role="img" aria-label="Wheel speeds and ABS sensor voltages per wheel">
        <rect className="body" x="104" y="20" width="92" height="280" rx="30" />
        <rect className="body" x="114" y="74" width="72" height="58" rx="8" opacity="0.6" />
        <text className="lbl" x="150" y="46">FRONT</text>
        {WHEELS.map((w) => {
          const s = `wheel_speed_${w.id}`;
          const a = `abs_sensor_${w.id}`;
          return (
            <g key={w.id}>
              <rect className={`wheel${bad(s) || bad(a) ? " alarm" : ""}`} x={w.wx} y={w.y - 26} width="20" height="52" rx="6" />
              <text className="lbl" x={w.x} y={w.y - 22}>{w.label}</text>
              <text className="val" x={w.x} y={w.y + 2}>{fmt(val(s), 0)}</text>
              <text className="sub" x={w.x} y={w.y + 15}>speed raw</text>
              <text className="val" x={w.x} y={w.y + 36}>{val(a) != null ? `${fmt(val(a), 2)} V` : "–"}</text>
              <text className="sub" x={w.x} y={w.y + 49}>ABS sensor</text>
            </g>
          );
        })}
        <text className="sub" x="150" y="314">wheel order unconfirmed (T-14)</text>
      </svg>
      <div className="drive2" style={{ marginTop: 8 }}>{height("left")}{height("right")}</div>
    </div>
  );
}
