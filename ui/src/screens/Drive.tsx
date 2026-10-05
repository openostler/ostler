import { createElement } from "react";
import { HealthStrip } from "../components/HealthStrip";
import { ScreenHead } from "../components/ScreenHead";
import { StatTile } from "../components/StatTile";
import { StatusGate } from "../components/StatusGate";
import { driveView, tileConv } from "../layout";
import { usePack } from "../pack/store";
import { useApp } from "../state/app";
import { getView } from "../vehicles/registry";

/** Driver's dashboard: the per-module view the pack's layout names (layout.drive). "tiles"
 * is generic — hero gauges and stat tiles; any other kind is a view the pack registered
 * (vehicles/registry.ts). Modules without one show a placeholder. Calm when healthy;
 * neutral/"awaiting" when undecoded. */
export function Drive() {
  const { snap, module, fields } = useApp();
  const pack = usePack();
  const recording = !!snap?.logging?.recording;
  const head = <ScreenHead title="Drive">{recording ? <span className="status hi"><span className="si">●</span>REC</span> : null}</ScreenHead>;
  if (snap?.status !== "connected") return <>{head}<StatusGate /></>;

  const view = driveView(module);
  const health = view?.health ? <HealthStrip /> : null;
  if (view?.kind === "tiles") {
    return (
      <>
        {head}
        {health}
        <div className="drive2">
          {(view.tiles ?? []).map((t) => (
            <StatTile key={t.signal} name={t.signal} label={t.label} sig={snap.signals[t.signal]} field={fields[t.signal]}
              gauge={t.gauge} dec={t.dec} unit={t.unit} conv={tileConv(t)} />
          ))}
        </div>
      </>
    );
  }
  // a registered view is a stable module-level component (looked up, never created here)
  const packView = view ? getView(pack?.id, view.kind) : undefined;
  if (packView) return <>{head}{health}{createElement(packView, { signals: snap.signals, fields })}</>;
  return (
    <>
      {head}
      <div className="empty"><div className="title">No vehicle view for this module yet</div>
        <div className="pretty">Its faults, inputs and settings are on the other tabs.</div></div>
    </>
  );
}
