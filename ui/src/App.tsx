// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "./api/client";
import type { Community, FaultMeaning, Field, Snapshot } from "./api/schemas";
import { useCatalog } from "./api/useCatalog";
import { useLoadPack } from "./api/usePack";
import { useSnapshot } from "./api/useSnapshot";
import { canonicalModule, defaultModule } from "./layout";
import { faultLookup } from "./lib/format";
import { isAdminPath } from "./lib/admin";
import { isAppPath } from "./lib/paths";
import { connOf } from "./lib/connection";
import { usePack } from "./pack/store";
import type { DrivingState } from "./shell/landing";
import { landingFor } from "./shell/landing";
import { parseKiosk, railSide, useLayoutClass } from "./shell/layoutClass";
import type { RouteName } from "./shell/routes";
import { Shell } from "./shell/Shell";
import { useConnectionSheet } from "./state/connection";
import { AppCtx, type AppContext } from "./state/app";
import { initialLive, reduceSnapshot, type LiveState } from "./state/live";
import { usePrefs } from "./state/prefs";
import { READ_ONLY_ERROR, ReplayProvider, useReplay } from "./state/replay";
import { moduleOf, synthesise } from "./state/replayState";

function useToast() {
  const [toast, setToast] = useState<{ msg: string; bad: boolean } | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const show = useCallback((msg: string, bad = false) => {
    setToast({ msg, bad });
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setToast(null), 3200);
  }, []);
  return [toast, show] as const;
}

/**
 * The dashboard. `ReplayProvider` sits at the root (ADR-0010): while a session is open, the
 * context every screen reads (`useApp()`) carries a snapshot synthesised at the replay cursor,
 * the module in view follows the recorded one, and nothing is sent to the car.
 * `replay` opens a session straight away (a deep link, and the tests).
 */
export function App({ path = window.location.pathname, replay }: { path?: string; replay?: string }) {
  // an unknown page: the server sent the app shell so the not-found view can say so
  if (!isAppPath(path)) return <NotFound path={path} />;
  return <Dashboard path={path} replay={replay} />;
}

function Dashboard({ path, replay }: { path: string; replay?: string }) {
  // the vehicle pack (module ids, names, layout) loads once at boot; nothing renders before it
  const { pack, error, retry } = useLoadPack();
  if (!pack) return <PackGate error={error} onRetry={retry} />;
  return (
    <ReplayProvider initial={replay ?? null}>
      <AppShell path={path} />
    </ReplayProvider>
  );
}

/** A page the server does not have (it answered the app shell, so deep links survive). */
function NotFound({ path }: { path: string }) {
  return (
    <div className="app app-plain">
      <main id="view">
        <div className="empty" role="alert">
          <div className="title">Page not found</div>
          <div className="small muted pretty">There is no page at <code>{path}</code>.</div>
          <a className="btn accent" href="/">Open the dashboard</a>
        </div>
      </main>
    </div>
  );
}

/** Before /pack answers: a quiet loading line, or the error card with a retry. */
function PackGate({ error, onRetry }: { error: string | null; onRetry: () => void }) {
  return (
    <div className="app app-plain">
      <main id="view">
        {error ? (
          <div className="card bad" role="alert">
            <div style={{ fontWeight: 700, color: "var(--ic-red)" }}>Could not load the vehicle</div>
            <div className="small muted pretty" style={{ marginTop: 4 }}>{error} — is the dashboard server running?</div>
            <button className="btn accent" style={{ marginTop: 10 }} onClick={onRetry}>Retry</button>
          </div>
        ) : <div className="empty"><div className="title">Loading…</div></div>}
      </main>
    </div>
  );
}

const noop = () => undefined;

/**
 * The screen state (`useApp()`) and the shell's own state: route, Drive mode, sheets. The
 * shell itself (layout classes, strip, rail or bottom bar, destinations) is shell/Shell.tsx.
 */
function AppShell({ path }: { path: string }) {
  const admin = isAdminPath(path);
  const pack = usePack();
  const kiosk = useMemo(() => parseKiosk(window.location.search), []);
  const layout = useLayoutClass(kiosk);
  const side = railSide(kiosk, pack?.layout.driver_side);
  // Parked / Idling / Moving come from the server in U2; until then the state is unknown and
  // the server gate alone decides every action (shell/landing.ts).
  const driving: DrivingState = "unknown";
  const [landing] = useState<RouteName>(() => landingFor({ driving, admin }));
  const [route, setRoute] = useState<RouteName>(landing === "drive" ? "home" : landing);
  const [driveMode, setDriveMode] = useState(landing === "drive");
  // Diagnose reopens on the area last shown
  const lastArea = useRef<RouteName>("diagnose.faults");
  const goTo = useCallback((r: RouteName) => {
    if (r === "drive") {
      setDriveMode(true);
      return;
    }
    const next = r === "diagnose" ? lastArea.current : r;
    if (next.startsWith("diagnose.")) lastArea.current = next;
    setDriveMode(false);
    setRoute(next);
  }, []);

  const [prefs, setPrefs] = usePrefs();
  const [toast, showToast] = useToast();
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [community, setCommunity] = useState<Community | null>(null);
  const [fieldsByModule, setFieldsByModule] = useState<Record<string, Record<string, Field>>>({});
  const [faultsByModule, setFaultsByModule] = useState<Record<string, FaultMeaning[]>>({});
  const [live, dispatch] = useReducer(
    (s: LiveState, snap: Snapshot) => reduceSnapshot(s, snap, Date.now()),
    initialLive,
  );
  const [ackedFaults, setAcked] = useState<Set<string>>(() => new Set());
  const [sheetFaults, setSheetFaults] = useState<string[] | null>(null);

  const replay = useReplay();
  const { snap: liveSnap, linkUp: liveLinkUp, refresh: liveRefresh } = useSnapshot(dispatch);
  // module ids are canonical (a legacy alias maps to the pack id); before the first
  // snapshot the pack's default module is in view
  const liveModule = canonicalModule(liveSnap?.module ?? (live.module || defaultModule()));
  // replay: the event state at the cursor decides the module in view (never sent to the car)
  const eventState = replay.state;
  const module = replay.active ? moduleOf(eventState, replay.session, liveModule) : liveModule;
  const { catalog } = useCatalog(module);
  const conn = connOf(liveSnap);
  const connSheet = useConnectionSheet(conn, !prefs.consentDone, replay.active);

  const reloadCommunity = useCallback(() => {
    api.community().then(setCommunity, () => undefined);
  }, []);
  useEffect(reloadCommunity, [reloadCommunity]);

  // field metadata per module, fetched once per module
  useEffect(() => {
    if (fieldsByModule[module]) return;
    api.fields(module).then(
      (r) => setFieldsByModule((m) => ({ ...m, [module]: Object.fromEntries(r.fields.map((f) => [f.name, f])) })),
      () => undefined,
    );
  }, [module, fieldsByModule]);

  // fault-code meanings per module, fetched once per module (the /faults dictionary)
  useEffect(() => {
    if (faultsByModule[module]) return;
    api.faults(module).then(
      (r) => setFaultsByModule((m) => ({ ...m, [module]: r.faults })),
      () => undefined,
    );
  }, [module, faultsByModule]);
  const faultMeaning = useMemo(() => faultLookup(faultsByModule[module] ?? []), [faultsByModule, module]);

  const fields = fieldsByModule[module];
  const synth = useMemo(() => {
    if (!replay.active || !replay.session || !replay.data) return null;
    return synthesise({
      meta: replay.session, data: replay.data, events: replay.events, t: replay.t,
      fields: fields ?? {}, base: liveSnap, state: eventState,
    });
  }, [replay.active, replay.session, replay.data, replay.events, replay.t, fields, liveSnap, eventState]);
  const snap = replay.active ? synth?.snap ?? null : liveSnap;
  const linkUp = replay.active ? true : liveLinkUp;
  const refresh = replay.active ? noop : liveRefresh;

  // The fault modal became the strip's worst-telltale chip (UI spec §3.2, U1): it never pops
  // up by itself. Faults not yet seen in the sheet mark the chip as new; dismissing the sheet
  // acknowledges them, so afterwards only NEW faults draw attention.
  const unacked = !replay.active && snap?.status === "connected" ? snap.faults.filter((f) => !ackedFaults.has(f)) : [];
  const dismissFaults = () => {
    setAcked((a) => new Set([...a, ...(sheetFaults ?? [])]));
    setSheetFaults(null);
  };

  const experimental = prefs.trust === "experimental";
  const openConnection = replay.active ? () => showToast(READ_ONLY_ERROR, true) : connSheet.show;
  const ctx: AppContext = {
    snap, live: synth?.live ?? (replay.active ? { ...initialLive, module } : live), linkUp, module, catalog,
    fields: fields ?? {}, faultMeaning, refresh, prefs, setPrefs,
    experimental, admin, community, reloadCommunity, goTo, toast: showToast, ackedFaults,
    showFaultSheet: setSheetFaults, openConnection,
  };

  return (
    <AppCtx.Provider value={ctx}>
      <Shell
        layout={layout} side={side} driving={driving} kiosk={kiosk.display !== null}
        route={route} goTo={goTo}
        driveMode={driveMode} setDriveMode={setDriveMode}
        unacked={unacked.length}
        sheetFaults={sheetFaults} openFaults={() => setSheetFaults(snap?.faults ?? [])} dismissFaults={dismissFaults}
        prefsOpen={prefsOpen} setPrefsOpen={setPrefsOpen}
        connSheet={connSheet}
        toast={toast}
      />
    </AppCtx.Provider>
  );
}
