import type { Units } from "../../lib/format";
import { showValue } from "./labels";
import { legendGradient, type Range } from "./trace";

/** The trace colour key: a channel picker over the gradient, min and max at its ends. */
export function TraceLegend({ channels, channel, onChannel, label, range, unit, units }: {
  channels: { name: string; label: string }[];
  channel: string;
  onChannel: (c: string) => void;
  label: (name: string) => string;
  range: Range | null;
  unit: string;
  units: Units;
}) {
  const lo = range ? showValue(range.min, unit, units) : null;
  const hi = range ? showValue(range.max, unit, units) : null;
  return (
    <div className="replay-legend">
      <label className="replay-legend-pick">
        <span className="kicker">Trace colour</span>
        <select className="input" aria-label="Trace channel" value={channel} onChange={(e) => onChannel(e.target.value)}>
          {channels.map((c) => <option key={c.name} value={c.name}>{c.label}</option>)}
        </select>
      </label>
      <div className="replay-legend-key" role="img"
        aria-label={range && lo && hi ? `${label(channel)} from ${lo.text} to ${hi.text} ${hi.unit}` : `${label(channel)}: no values`}>
        <div className="replay-legend-bar" style={{ background: legendGradient() }} />
        <div className="replay-legend-ends small">
          <span data-testid="legend-min">{lo ? `${lo.text} ${lo.unit}` : "–"}</span>
          <span data-testid="legend-max">{hi ? `${hi.text} ${hi.unit}` : "–"}</span>
        </div>
      </div>
    </div>
  );
}
