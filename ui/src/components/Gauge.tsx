import { useApp } from "../state/app";
import { convertUnit, fmt } from "../lib/format";

/** Analog gauge: a 270° arc filled from min..max, with the gap at the bottom. The circle
 * path starts at 3 o'clock; rotate(135) opens the gap downward. */
export function Gauge({ value, min, max, unit = "", dec }: {
  value: number | null; min: number; max: number; unit?: string; dec?: number;
}) {
  const { prefs } = useApp();
  const r = 40;
  const C = 2 * Math.PI * r;
  const arc = C * 0.75;
  const frac = value == null ? 0 : Math.max(0, Math.min(1, (value - min) / (max - min)));
  const shown = value == null ? null : convertUnit(value, unit, prefs.units);
  return (
    <svg viewBox="0 0 100 100" className="gsvg" role="img"
      aria-label={shown ? `${fmt(shown.v, dec)} ${shown.unit}` : "no value"}>
      <circle cx="50" cy="50" r={r} className="gtrack"
        strokeDasharray={`${arc.toFixed(1)} ${C.toFixed(1)}`} transform="rotate(135 50 50)" />
      <circle cx="50" cy="50" r={r} className="gval"
        strokeDasharray={`${(arc * frac).toFixed(1)} ${C.toFixed(1)}`} transform="rotate(135 50 50)" />
      <text x="50" y="54" className="gnum">{shown ? fmt(shown.v, dec) : "–"}</text>
      <text x="50" y="69" className="gunit">{shown ? shown.unit : unit}</text>
    </svg>
  );
}
