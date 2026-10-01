import { bandFractions, position, short, type Span } from "../lib/range";

/**
 * Where a value sits against its healthy band (ISA-101 moving analog indicator):
 * grey track = the span, darker grey = normal band, marker = the value. The marker
 * turns alarm-coloured only when the server flags the value low/high; a value outside
 * the band but inside the limits stays neutral — its position says enough.
 */
export function RangeBar({ value, span, normal, alarm, label, unit = "" }: {
  value: number | null;
  span: Span;
  normal?: Span | null;
  alarm?: boolean;
  label: string;
  unit?: string;
}) {
  const W = 100;
  const band = bandFractions(normal, span);
  const pos = value == null ? null : position(value, span);
  const desc = `${label}: ${value == null ? "no value" : `${short(value)} ${unit}`.trim()}` +
    (normal ? `, normal ${short(normal[0])}–${short(normal[1])}` : "");
  return (
    <div className="stat-viz">
      <svg className="rangebar" viewBox={`0 0 ${W} 18`} preserveAspectRatio="none" role="img" aria-label={desc}>
        <rect className="track" x="0" y="6" width={W} height="6" rx="3" />
        {band ? <rect className="band" x={band[0] * W} y="6" width={(band[1] - band[0]) * W} height="6" /> : null}
        {pos ? (
          pos.clamped ? (
            // off the scale: an arrow at the end it ran past
            <path className={`mark${alarm ? " alarm" : ""}`}
              d={pos.clamped === "high" ? `M${W - 4} 2 L${W} 9 L${W - 4} 16 Z` : "M4 2 L0 9 L4 16 Z"} />
          ) : (
            <rect className={`mark${alarm ? " alarm" : ""}`} x={pos.f * W - 1.25} y="1" width="2.5" height="16" rx="1.25" />
          )
        ) : null}
      </svg>
      <div className="range-legend" aria-hidden="true">
        <span>{short(span[0])}</span>
        {normal ? <span>normal {short(normal[0])}–{short(normal[1])}{unit ? ` ${unit}` : ""}</span> : <span />}
        <span>{short(span[1])}</span>
      </div>
    </div>
  );
}
