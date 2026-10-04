import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "./api/client";
import type { Community, FaultMeaning, Field, Snapshot } from "./api/schemas";
import { useCatalog } from "./api/useCatalog";
import { useSnapshot } from "./api/useSnapshot";
import { ActiveTestBanner } from "./components/ActiveTestBanner";
import { ConnectionPill } from "./components/ConnectionPill";
import { ConnectionSheet } from "./components/ConnectionSheet";
import { Consent } from "./components/Consent";
import { FaultSheet } from "./components/FaultSheet";
import { ModuleSelect } from "./components/ModuleSelect";
import { Preferences } from "./components/Preferences";
import { clockHHMM, faultLookup, fmt } from "./lib/format";
import { isAdminPath } from "./lib/admin";
import { connOf } from "./lib/connection";
import { useConnectionSheet } from "./state/connection";
import { screensFor } from "./screens/registry";
import { AppCtx, type AppContext } from "./state/app";
import { initialLive, reduceSnapshot, type LiveState } from "./state/live";
import { usePrefs } from "./state/prefs";

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

export function App({ path = window.location.pathname }: { path?: string }) {
  const admin = isAdminPath(path);
  const screens = useMemo(() => screensFor(admin), [admin]);
  const [tab, setTab] = useState(admin ? "map" : "drive");
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

  const { snap, linkUp, refresh } = useSnapshot(dispatch);
  const module = snap?.module ?? live.module;
  const { catalog } = useCatalog(module);
  const conn = connOf(snap);
  const connSheet = useConnectionSheet(conn, !prefs.consentDone);

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

  // Faults pop up once when connected; dismissing acknowledges them, so afterwards only
  // NEW faults alert. Derived from the snapshot (no effect); the Drive tile can also
  // open the sheet on demand.
  const unacked = snap?.status === "connected" ? snap.faults.filter((f) => !ackedFaults.has(f)) : [];
  const sheetFaults = manualFaults ?? (unacked.length ? unacked : null);
  const dismissFaults = () => {
    setAcked((a) => new Set([...a, ...(sheetFaults ?? [])]));
    setManualFaults(null);
  };

  const experimental = prefs.trust === "experimental";
  const ctx: AppContext = {
    snap, live, linkUp, module, catalog, fields: fieldsByModule[module] ?? {}, faultMeaning, refresh, prefs, setPrefs,
    experimental, admin, community, reloadCommunity, goTo: setTab, toast: showToast, ackedFaults,
    showFaultSheet: setManualFaults, openConnection: connSheet.show,
  };
  const Current = (screens.find((s) => s.id === tab) ?? screens[0])!.component;

  return (
    <AppCtx.Provider value={ctx}>
      <div className="app">
        <header>
          <div className="hmod">
            <div className="htitle">D2 Diag{admin ? " · admin" : ""}</div>
            <ModuleSelect />
          </div>
          <div className="hright">
            <Clock />
            {typeof snap?.battery_v === "number" ? (
              <span className="hbatt" aria-label={`Car battery ${fmt(snap.battery_v, 1)} V`}>
                <span aria-hidden="true">⚡</span>{fmt(snap.battery_v, 1)}<span className="u">V</span>
              </span>
            ) : null}
            <ConnectionPill />
            <button className="chip" aria-label="Preferences" onClick={() => setPrefsOpen(true)}>⚙</button>
          </div>
        </header>
        <ActiveTestBanner />
        {experimental ? (
          <div className="expbanner"><span className="pdot yellow" />Experimental mode — unverified items and tests shown</div>
        ) : null}
        <main id="view"><Current /></main>
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
        {connSheet.open && !prefsOpen ? <ConnectionSheet onClose={connSheet.dismiss} /> : null}
        {prefsOpen ? <Preferences onClose={() => setPrefsOpen(false)} /> : null}
        {!prefs.consentDone ? <Consent /> : null}
        {toast ? <div className={`toast${toast.bad ? " bad" : ""}`} role="status">{toast.msg}</div> : null}
      </div>
    </AppCtx.Provider>
  );
}
