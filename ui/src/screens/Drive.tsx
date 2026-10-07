// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { createElement } from "react";
import { HealthStrip } from "../components/HealthStrip";
import { StatTile } from "../components/StatTile";
import { StatusGate } from "../components/StatusGate";
import { driveView, moduleName, tileConv } from "../layout";
import { usePack } from "../pack/store";
import { useApp } from "../state/app";
import { getView } from "../vehicles/registry";

/** Driver's view of the module in session: the per-module view the pack's layout names
 * (layout.drive). "tiles" is generic — hero gauges and stat tiles; any other kind is a view
 * the pack registered (vehicles/registry.ts). Modules without one show a placeholder. Calm
 * when healthy; neutral/"awaiting" when undecoded. Home's vehicle card and Drive mode both
 * show it (UI spec §3.4–3.5); the roles of §5.4 replace it with the manifest in U3. Drive mode
 * drops the health line (`banner={false}`): the strip's telltale chip carries it (§12.3). */
export function DriveBody({ banner = true }: { banner?: boolean } = {}) {
  const { snap, module, fields } = useApp();
  const pack = usePack();
  if (snap?.status !== "connected") return <StatusGate />;

  const view = driveView(module);
  const health = banner && view?.health ? <HealthStrip /> : null;
  if (view?.kind === "tiles") {
    return (
      <>
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
  if (packView) return <>{health}{createElement(packView, { signals: snap.signals, fields })}</>;
  return (
    <div className="empty"><div className="title">No vehicle view for this module yet</div>
      <div className="pretty">Its faults, inputs and settings are in Diagnose.</div></div>
  );
}

/** Home's vehicle card (and HU-wide's always-on vehicle pane): health and the driver's view
 * of the system in session. */
export function VehicleCard() {
  const { module } = useApp();
  return (
    <section className="vehicle-card stack" aria-label={`Vehicle: ${moduleName(module)}`}>
      <DriveBody />
    </section>
  );
}

/** Drive mode's screen: the driver's view alone, with no heading or fault banner (§12.3);
 * the shell's strip holds Back and the worst telltale. */
export function Drive() {
  return <DriveBody banner={false} />;
}
