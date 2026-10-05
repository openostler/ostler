import type { Units } from "../../lib/format";
import { showValue } from "./labels";
import { legendGradient, type Range, type TraceLane } from "./trace";

export type LegendTrace = { lane: TraceLane; channel: string; label: string; range: Range | null; unit: string; colors: readonly string[] };

/** The trace colour keys: per trace a channel button (opens the picker), the gradient and
 * min / max at its ends; "+ Add trace" for B; the Classic (turbo) colour option. */
export function TraceLegend({ traces, units, onEdit, onAddB, classic, onClassic }: {
  traces: LegendTrace[];
  units: Units;
  onEdit: (lane: TraceLane) => void;
  /** Offered while trace B is off. */
  onAddB?: () => void;
  classic: boolean;
  onClassic: (on: boolean) => void;
}) {
  return (
    <div className="replay-legend">
      {traces.map((t) => {
        const lo = t.range ? showValue(t.range.min, t.unit, units) : null;
        const hi = t.range ? showValue(t.range.max, t.unit, units) : null;
        const L = t.lane.toUpperCase();
        const sfx = t.lane === "a" ? "" : "-b";
        return (
          <div key={t.lane} className="replay-legend-row" data-lane={t.lane}>
            <button type="button" className="rchip replay-legend-pick" aria-label={`Trace ${L}: ${t.label} — change channel`} onClick={() => onEdit(t.lane)}
              data-channel={t.channel}>
              <span className="replay-lane-tag" aria-hidden="true">{L}</span>{t.label} <span aria-hidden="true">▾</span>
            </button>
            <div className="replay-legend-key" role="img"
              aria-label={t.range && lo && hi ? `Trace ${L}, ${t.label} from ${lo.text} to ${hi.text} ${hi.unit}` : `Trace ${L}, ${t.label}: no values`}>
              <div className="replay-legend-bar" style={{ background: legendGradient(t.colors) }} />
              <div className="replay-legend-ends small">
                <span data-testid={`legend${sfx}-min`}>{lo ? `${lo.text} ${lo.unit}` : "–"}</span>
                <span data-testid={`legend${sfx}-max`}>{hi ? `${hi.text} ${hi.unit}` : "–"}</span>
              </div>
            </div>
          </div>
        );
      })}
      <div className="replay-legend-tools">
        {onAddB ? <button type="button" className="rchip" onClick={onAddB}>+ Add trace</button> : null}
        <button type="button" className="rchip" aria-pressed={classic} onClick={() => onClassic(!classic)}
          title="Rainbow (turbo) colours, as older loggers use">Classic colours</button>
      </div>
    </div>
  );
}
