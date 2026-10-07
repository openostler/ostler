// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { createElement, useRef } from "react";
import { HealthStrip } from "../components/HealthStrip";
import { StatTile } from "../components/StatTile";
import { StatusGate } from "../components/StatusGate";
import { driveView, moduleName, tileConv } from "../layout";
import { usePack } from "../pack/store";
import { useApp } from "../state/app";
import { getView } from "../vehicles/registry";
import { DriveFace } from "../drive/DriveFace";
import type { DriveModes } from "../drive/useDriveModes";
import type { DrivingState } from "../shell/landing";
import type { LayoutClass } from "../shell/layoutClass";

/** Driver's view of the module in session (Home's vehicle card): the per-module view the
 * pack's layout names (layout.drive). "tiles" is generic — hero gauges and stat tiles; any other kind is a view
 * the pack registered (vehicles/registry.ts). Modules without one show a placeholder. Calm
 * when healthy; neutral/"awaiting" when undecoded. Home's vehicle card and Drive mode both
 * show it (UI spec §3.4–3.5); the roles of §5.4 replace it with the manifest in U3. Drive mode
 * shows it as the Diagnostic preset (drive/DriveFace.tsx, drive-modes spec §5.1). */
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

/**
 * Drive mode's screen (UI spec §12.3, drive-modes spec §6): the active mode's current face
 * alone, with no heading or fault banner; the shell's strip holds Back, the Drive-mode chip
 * and the worst telltale. A horizontal swipe switches the mode's faces, wrapping, and so do
 * `left`/`right` through ShellInput (shell/useShellInput.ts, shell input spec §6); they never
 * change the mode (the chip does). Arrow keys inside the strip or a sheet keep their own meaning.
 */
export function Drive({ modes, cls, driving }: { modes: DriveModes; cls: LayoutClass; driving: DrivingState }) {
  const { snap } = useApp();
  const { faces, face, stepFace, active } = modes;
  const start = useRef<{ x: number; y: number } | null>(null);
  const current = faces[face];
  if (!current) return <div className="empty"><div className="title">This mode has nothing for this screen</div></div>;
  if (active.id === "ostler.diagnostic" && snap?.status !== "connected") return <StatusGate />;
  return (
    <div className="dm" data-mode={active.id} data-face-index={face}
      onPointerDown={(e) => { start.current = { x: e.clientX, y: e.clientY }; }}
      onPointerUp={(e) => {
        const s = start.current;
        start.current = null;
        if (!s) return;
        const dx = e.clientX - s.x;
        if (Math.abs(dx) > 60 && Math.abs(dx) > 2 * Math.abs(e.clientY - s.y)) stepFace(dx < 0 ? 1 : -1);
      }}>
      <DriveFace face={current} cls={cls} driving={driving} />
      {faces.length > 1 ? (
        <div className="dm-pager" aria-hidden="true">
          {faces.map((f, i) => <span key={f.face} className={i === face ? "on" : undefined} />)}
        </div>
      ) : null}
      <span className="visually-hidden" aria-live="polite">{`${active.name}: ${current.name}${faces.length > 1 ? `, face ${face + 1} of ${faces.length}` : ""}`}</span>
    </div>
  );
}
