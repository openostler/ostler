// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { Suspense, useEffect, useMemo, useState, type ReactNode } from "react";
import { useAction } from "../api/useAction";
import { ActiveTestBanner } from "../components/ActiveTestBanner";
import { ConnectionSheet } from "../components/ConnectionSheet";
import { Consent } from "../components/Consent";
import { FaultSheet } from "../components/FaultSheet";
import { GlobalTransport } from "../components/GlobalTransport";
import { Preferences } from "../components/Preferences";
import { ReplayAudio } from "../components/replay/ReplayAudio";
import { moduleName } from "../layout";
import { formatClock, formatQuantity } from "../lib/units";
import { usePack } from "../pack/store";
import { Drive, VehicleCard } from "../screens/Drive";
import { useApp } from "../state/app";
import type { useConnectionSheet } from "../state/connection";
import { useReplay } from "../state/replay";
import { Boundary } from "./Boundary";
import { ShellCtx, type ShellContext, type ShellSheet } from "./context";
import { destinationsFor, type Capabilities } from "./destinations";
import type { DrivingState } from "./landing";
import { hasRail, isHeadUnit, type LayoutClass, type Side } from "./layoutClass";
import { Nav } from "./Nav";
import { destinationOf, type RouteName } from "./routes";
import { Strip } from "./Strip";
import { stripChips, type ChipOpen } from "./strip";

/** No capability manifest before U3/U5: nothing device-gated shows (shell/destinations.ts). */
const NO_CAPABILITIES: Capabilities = { devices: [] };

const quantity = (v: number | null | undefined, unit: string, dec?: number) => formatQuantity(v, unit, dec);
const clock = (d: Date) => formatClock(d);

/** The clock text, refreshed every 10 s. */
function useClock(): string {
  const [now, setNow] = useState(() => clock(new Date()));
  useEffect(() => {
    const id = window.setInterval(() => setNow(clock(new Date())), 10_000);
    return () => window.clearInterval(id);
  }, []);
  return now;
}

export type ShellProps = {
  layout: LayoutClass;
  side: Side;
  driving: DrivingState;
  kiosk: boolean;
  route: RouteName;
  goTo: (r: RouteName) => void;
  driveMode: boolean;
  setDriveMode: (on: boolean) => void;
  unacked: number;
  sheetFaults: string[] | null;
  openFaults: () => void;
  dismissFaults: () => void;
  prefsOpen: boolean;
  setPrefsOpen: (on: boolean) => void;
  connSheet: ReturnType<typeof useConnectionSheet>;
  toast: { msg: string; bad: boolean } | null;
};

/**
 * The shell (UI spec §3; app-model spec §2): the layout class on the root, the status strip,
 * the rail or bottom bar, one destination at a time in its own lazy chunk and error boundary,
 * Drive mode over it all, and the sheets the shell alone draws. It provides `useShell()`.
 */
export function Shell(p: ShellProps) {
  const app = useApp();
  const pack = usePack();
  const replay = useReplay();
  const request = useAction();
  const time = useClock();
  const { snap, linkUp, module, prefs, admin, experimental } = app;
  const headUnit = isHeadUnit(p.layout);
  const entries = useMemo(() => destinationsFor(NO_CAPABILITIES), []);
  const here = destinationOf(p.route);
  const entry = entries.find((e) => e.id === here) ?? entries[0]!;

  const openSheet = (s: ShellSheet) => {
    if (s === "preferences") p.setPrefsOpen(true);
    else if (s === "connection") app.openConnection();
    else p.openFaults();
  };
  const shell: ShellContext = {
    layout: p.layout, side: p.side, headUnit, driving: p.driving,
    vehicle: { pack: pack?.id ?? "", name: pack?.name ?? "", system: module, systemName: moduleName(module) },
    signals: snap?.signals ?? {},
    actions: { request },
    nav: { route: p.route, open: p.goTo },
    drive: { active: p.driveMode, open: () => p.setDriveMode(true), close: () => p.setDriveMode(false) },
    sheets: { open: openSheet },
    session: { admin, experimental, replaying: replay.active, kiosk: p.kiosk },
    toast: app.toast,
    format: { quantity, clock },
  };

  const chips = stripChips({
    layout: p.layout, snap, linkUp, replaying: replay.active, admin, systemName: moduleName(module),
    unacked: p.unacked, clock: time, quantity, driveMode: p.driveMode,
  });
  const onChip = (o: ChipOpen) => {
    if (o === "faults") p.openFaults();
    else if (o === "connection") app.openConnection();
    else if (o === "exit-replay") replay.exit();
    else if (o === "back") p.setDriveMode(false);
    else p.goTo("logs");
  };

  const Destination = entry.component;
  let content: ReactNode;
  if (p.driveMode) {
    // one screen, no page chrome (§12.3): Back is the strip's first chip, faults its telltale
    content = (
      <section className="drivemode stack" aria-label="Drive mode">
        <Boundary key="drive" name="Drive mode"><Drive /></Boundary>
      </section>
    );
  } else {
    content = (
      <Boundary key={entry.id} name={entry.label}>
        <Suspense fallback={<div className="empty" role="status"><div className="title">Loading…</div></div>}>
          <Destination />
        </Suspense>
      </Boundary>
    );
  }
  const vehiclePane = p.layout === "huwide" && !p.driveMode;
  const nav = p.driveMode ? null : (
    <Nav entries={entries} route={p.route} rail={hasRail(p.layout)} driveButton={headUnit}
      onOpen={p.goTo} onDrive={() => p.setDriveMode(true)} />
  );

  return (
    <ShellCtx.Provider value={shell}>
      <div className={`app${replay.active ? " replaying" : ""}`} data-layout={p.layout} data-side={p.side}
        data-drive={p.driveMode ? "on" : undefined}>
        <div className="column">
          <Strip chips={chips} onOpen={onChip} />
          {replay.active ? null : <ActiveTestBanner />}
          {experimental && !replay.active ? (
            <div className="expbanner"><span className="pdot yellow" />Experimental mode — unverified items and tests shown</div>
          ) : null}
          <div className="body">
            {vehiclePane ? (
              <aside className="vehiclepane" aria-label="Vehicle pane">
                <Boundary name="Vehicle"><VehicleCard /></Boundary>
              </aside>
            ) : null}
            <main id="view" className={replay.active ? "replay-edge" : undefined}>{content}</main>
          </div>
          <GlobalTransport />
          <ReplayAudio />
          {p.toast ? <div className={`toast${p.toast.bad ? " bad" : ""}`} role="status">{p.toast.msg}</div> : null}
        </div>
        {nav}
        {p.sheetFaults && !p.prefsOpen && !p.connSheet.open && prefs.consentDone
          ? <FaultSheet faults={p.sheetFaults} onDismiss={p.dismissFaults} /> : null}
        {p.connSheet.open && !p.prefsOpen ? <ConnectionSheet onClose={p.connSheet.dismiss} downSince={p.connSheet.downSince} /> : null}
        {p.prefsOpen ? <Preferences onClose={() => p.setPrefsOpen(false)} /> : null}
        {!prefs.consentDone ? <Consent /> : null}
      </div>
    </ShellCtx.Provider>
  );
}
