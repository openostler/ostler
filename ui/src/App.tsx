// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "./api/client";
import type { Community, FaultMeaning, Field, Snapshot } from "./api/schemas";
import { useCatalog } from "./api/useCatalog";
import { useLoadPack } from "./api/usePack";
import { useSnapshot } from "./api/useSnapshot";
import { ActiveTestBanner } from "./components/ActiveTestBanner";
import { ConnectionPill } from "./components/ConnectionPill";
import { ConnectionSheet } from "./components/ConnectionSheet";
import { Consent } from "./components/Consent";
import { FaultSheet } from "./components/FaultSheet";
import { GlobalTransport } from "./components/GlobalTransport";
import { MarkButton } from "./components/MarkButton";
import { ModuleSelect } from "./components/ModuleSelect";
import { Preferences } from "./components/Preferences";
import { ReplayAudio } from "./components/replay/ReplayAudio";
import { RewindButton } from "./components/RewindButton";
import { canonicalModule, defaultModule, moduleName } from "./layout";
import { clockHHMM, faultLookup, fmt } from "./lib/format";
import { isAdminPath } from "./lib/admin";
import { isAppPath } from "./lib/paths";
import { connOf } from "./lib/connection";
import { useConnectionSheet } from "./state/connection";
import { screensFor } from "./screens/registry";
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

/** The phone's clock (the D2 has no lit clock), refreshed every 10 s. */
function Clock() {
  const [now, setNow] = useState(clockHHMM);
  useEffect(() => {
    const id = window.setInterval(() => setNow(clockHHMM()), 10_000);
    return () => window.clearInterval(id);
  }, []);
  return <span className="hdr-clock">{now}</span>;
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
    <div className="app">
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
    <div className="app">
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

function AppShell({ path }: { path: string }) {
  const admin = isAdminPath(path);
  const screens = useMemo(() => screensFor(admin), [admin]);
  const [tab, setTab] = useState(admin ? "map" : "drive");
  // goTo(): any screen (Logs → Analysis, Rewind, a health link) switches the tab by id
  const goTo = useCallback((id: string) => setTab(id), []);
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
  const [manualFaults, setManualFaults] = useState<string[] | null>(null);

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

  // Faults pop up once when connected; dismissing acknowledges them, so afterwards only
  // NEW faults alert. Derived from the snapshot (no effect); the Drive tile can also
  // open the sheet on demand.
  const unacked = !replay.active && snap?.status === "connected" ? snap.faults.filter((f) => !ackedFaults.has(f)) : [];
  const sheetFaults = manualFaults ?? (unacked.length ? unacked : null);
  const dismissFaults = () => {
    setAcked((a) => new Set([...a, ...(sheetFaults ?? [])]));
    setManualFaults(null);
  };

  const experimental = prefs.trust === "experimental";
  const ctx: AppContext = {
    snap, live: synth?.live ?? (replay.active ? { ...initialLive, module } : live), linkUp, module, catalog,
    fields: fields ?? {}, faultMeaning, refresh, prefs, setPrefs,
    experimental, admin, community, reloadCommunity, goTo, toast: showToast, ackedFaults,
    showFaultSheet: setManualFaults,
    openConnection: replay.active ? () => showToast(READ_ONLY_ERROR, true) : connSheet.show,
  };
  const Current = (screens.find((s) => s.id === tab) ?? screens[0])!.component;

  return (
    <AppCtx.Provider value={ctx}>
      <div className={`app${replay.active ? " replaying" : ""}`}>
        <header>
          {admin ? <span className="hadmin">admin</span> : null}
          {replay.active ? (
            <div className="hmod">
              <div className="modctl modctl-replay" aria-label={`Module ${moduleName(module)} (recorded)`}>
                <span className="modctl-txt">
                  <span className="modctl-k">Module</span>
                  <span className="modctl-v">{moduleName(module)}</span>
                </span>
              </div>
            </div>
          ) : <ModuleSelect />}
          <div className="hright">
            <Clock />
            <MarkButton />
            {typeof snap?.battery_v === "number" ? (
              <span className="hbatt" aria-label={`Car battery ${fmt(snap.battery_v, 1)} V`}>
                <span aria-hidden="true">⚡</span>{fmt(snap.battery_v, 1)}<span className="u">V</span>
              </span>
            ) : null}
            <RewindButton />
            <ConnectionPill />
            <button className="chip" aria-label="Preferences" onClick={() => setPrefsOpen(true)}>⚙</button>
          </div>
        </header>
        {replay.active ? null : <ActiveTestBanner />}
        {experimental && !replay.active ? (
          <div className="expbanner"><span className="pdot yellow" />Experimental mode — unverified items and tests shown</div>
        ) : null}
        <main id="view" className={replay.active ? "replay-edge" : undefined}><Current /></main>
        <GlobalTransport />
        <ReplayAudio />
        <nav className={`tabs${screens.length > 6 ? " many" : ""}`} aria-label="Screens">
          {screens.map((s) => (
            <button key={s.id} aria-label={s.label} aria-current={s.id === tab ? "page" : undefined} onClick={() => setTab(s.id)}>
              <span className="ti" aria-hidden="true">{s.icon}</span>
              <span className="tl" aria-hidden="true">{s.label}</span>
              <span className="ts" aria-hidden="true">{s.short ?? s.label}</span>
            </button>
          ))}
        </nav>
        {sheetFaults && !prefsOpen && !connSheet.open && prefs.consentDone ? <FaultSheet faults={sheetFaults} onDismiss={dismissFaults} /> : null}
        {connSheet.open && !prefsOpen ? <ConnectionSheet onClose={connSheet.dismiss} downSince={connSheet.downSince} /> : null}
        {prefsOpen ? <Preferences onClose={() => setPrefsOpen(false)} /> : null}
        {!prefs.consentDone ? <Consent /> : null}
        {toast ? <div className={`toast${toast.bad ? " bad" : ""}`} role="status">{toast.msg}</div> : null}
      </div>
    </AppCtx.Provider>
  );
}
