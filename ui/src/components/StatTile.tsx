import type { Field, SignalValue } from "../api/schemas";
import { flagFor } from "../lib/format";
import { useApp } from "../state/app";
import { Gauge } from "./Gauge";
import { RangeBar } from "./RangeBar";
import { Sparkline } from "./Sparkline";
import { StatusChip } from "./StatusChip";
import { Value } from "./Value";

/** A Drive tile: label + status, the big value, then its context — a range bar against
 * the healthy band and the last minute as a sparkline (or a gauge for hero tiles). */
export function StatTile({ name, label, sig, field, gauge, dec, unit, conv }: {
  name: string; label: string; sig?: SignalValue; field?: Field; gauge?: boolean;
  dec?: number; unit?: string; conv?: (v: number) => number;
}) {
  const { live } = useApp();
  const flag = flagFor(sig?.s, sig?.c ?? field?.c);
  const alarm = flag.cls === "hi" || flag.cls === "lo";
  const raw = typeof sig?.v === "number" ? sig.v : null;
  const v = raw != null && conv ? conv(raw) : raw;
  const u = unit ?? (sig?.u || field?.unit || "");
  const span = field?.span ?? null;
  // a converted value (e.g. L/100km → L/mil) no longer fits the stored band
  const normal = conv ? null : field?.normal ?? null;
  const samples = (live.history[name] ?? []).map((s) => (conv ? { ...s, v: conv(s.v) } : s));
  const viewSpan = span && conv ? ([conv(span[0]), conv(span[1])] as const) : span;
  return (
    <div className={`tile${alarm ? " alarm" : ""}${gauge ? " hero" : ""}`} data-signal={name}>
      <div className="stat-top"><span className="stat-label">{label}</span><StatusChip flag={flag} compact /></div>
      {gauge && viewSpan ? (
        <div className="gwrap2"><Gauge value={v} span={viewSpan} normal={normal} unit={u} dec={dec} alarm={alarm} label={label} /></div>
      ) : (
        <>
          <div className={`stat-value${alarm ? " alarm" : ""}`}><Value value={v} unit={u} dec={dec} /></div>
          {viewSpan ? <RangeBar value={v} span={viewSpan} normal={normal} alarm={alarm} label={label} unit={u} /> : null}
          <Sparkline samples={samples} label={label} />
        </>
      )}
    </div>
  );
}
