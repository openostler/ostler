import { useApp } from "../state/app";
import { convertUnit, fmt } from "../lib/format";
import { bandFractions, position, short, type Span } from "../lib/range";

const SWEEP = 240; // degrees; the gap sits at the bottom

function arc(r: number, f0: number, f1: number) {
  const C = 2 * Math.PI * r;
  const len = C * (SWEEP / 360);
  return { dash: `${(len * (f1 - f0)).toFixed(2)} ${C.toFixed(2)}`, offset: (-len * f0).toFixed(2) };
}

/** Analog gauge: 240° track, the normal band shaded, the value as a filled arc from the
 * low end, five ticks and the span's end labels. Alarm colour only when flagged. */
export function Gauge({ value, span, normal, unit = "", dec, alarm, label }: {
  value: number | null; span: Span; normal?: Span | null; unit?: string; dec?: number; alarm?: boolean; label: string;
}) {
  const { prefs } = useApp();
  const r = 40;
  const rot = 90 + (360 - SWEEP) / 2; // start angle so the gap is centred at the bottom
  const band = bandFractions(normal, span);
  const f = value == null ? 0 : position(value, span).f;
  const shown = value == null ? null : convertUnit(value, unit, prefs.units);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((t) => {
    const a = ((rot + SWEEP * t) * Math.PI) / 180;
    return { x1: 50 + Math.cos(a) * 31, y1: 50 + Math.sin(a) * 31, x2: 50 + Math.cos(a) * 34, y2: 50 + Math.sin(a) * 34 };
  });
  const end = (t: number) => {
    const a = ((rot + SWEEP * t) * Math.PI) / 180;
    return { x: 50 + Math.cos(a) * 40, y: 50 + Math.sin(a) * 40 + 12 };
  };
  const full = arc(r, 0, 1);
  return (
    <svg viewBox="0 0 100 92" className="g2" role="img"
      aria-label={`${label}: ${shown ? `${fmt(shown.v, dec)} ${shown.unit}` : "no value"}` +
        (normal ? `, normal ${short(normal[0])}–${short(normal[1])} ${unit}` : "")}>
      <g transform={`rotate(${rot} 50 50)`}>
        <circle cx="50" cy="50" r={r} className="track" strokeDasharray={full.dash} />
        {band ? (() => { const b = arc(r, band[0], band[1]); return <circle cx="50" cy="50" r={r} className="band" strokeDasharray={b.dash} strokeDashoffset={b.offset} />; })() : null}
        {value != null ? (() => { const v = arc(r, 0, f); return <circle cx="50" cy="50" r={r} className={`val${alarm ? " alarm" : ""}`} strokeDasharray={v.dash} />; })() : null}
      </g>
      {ticks.map((t, i) => <line key={i} className="tick" {...t} />)}
      <text x="50" y="55" className="num">{shown ? fmt(shown.v, dec) : "–"}</text>
      <text x="50" y="68" className="unit">{shown ? shown.unit : unit}</text>
      <text {...end(0)} className="lim">{short(span[0])}</text>
      <text {...end(1)} className="lim">{short(span[1])}</text>
    </svg>
  );
}
