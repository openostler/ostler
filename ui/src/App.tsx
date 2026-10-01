import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import { api } from "./api/client";
import type { Community, Field, Snapshot } from "./api/schemas";
import { useSnapshot } from "./api/useSnapshot";
import { Consent } from "./components/Consent";
import { FaultSheet } from "./components/FaultSheet";
import { Settings } from "./components/Settings";
import { moduleName } from "./layout";
import { isAdminPath } from "./lib/admin";
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

function Pill({ snap, linkUp }: { snap: Snapshot | null; linkUp: boolean }) {
  const st = snap?.status;
  const [cls, label] = !linkUp && snap
    ? ["yellow blink", "Reconnecting"]
    : st === "connected" ? ["green", "Connected"]
    : st === "error" ? ["red", "No cable"]
    : ["yellow blink", "Connecting"];
  return (
    <div className="pill" role="status" aria-live="polite"><span className={`pdot ${cls}`} />{label}</div>
  );
}

export function App({ path = window.location.pathname }: { path?: string }) {
  const admin = isAdminPath(path);
  const screens = useMemo(() => screensFor(admin), [admin]);
  const [tab, setTab] = useState(admin ? "map" : "drive");
  const [prefs, setPrefs] = usePrefs();
  const [toast, showToast] = useToast();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [community, setCommunity] = useState<Community | null>(null);
  const [fieldsByModule, setFieldsByModule] = useState<Record<string, Record<string, Field>>>({});
  const [live, dispatch] = useReducer(
    (s: LiveState, snap: Snapshot) => reduceSnapshot(s, snap, Date.now()),
    initialLive,
  );
  const [ackedFaults, setAcked] = useState<Set<string>>(() => new Set());
  const [manualFaults, setManualFaults] = useState<string[] | null>(null);

  const { snap, linkUp, refresh } = useSnapshot(dispatch);
  const module = snap?.module ?? live.module;

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
    snap, live, module, fields: fieldsByModule[module] ?? {}, refresh, prefs, setPrefs, experimental,
    admin, community, reloadCommunity, goTo: setTab, toast: showToast, ackedFaults,
    showFaultSheet: setManualFaults,
  };
  const Current = (screens.find((s) => s.id === tab) ?? screens[0])!.component;

  return (
    <AppCtx.Provider value={ctx}>
      <div className="app">
        <header>
          <div style={{ minWidth: 0 }}>
            <div className="htitle">D2 Diag{admin ? " · admin" : ""}</div>
            <div className="hsub">{snap ? moduleName(module) : "—"}</div>
          </div>
          <div className="row" style={{ marginLeft: "auto" }}>
            <Pill snap={snap} linkUp={linkUp} />
            <button className="chip" aria-label="Settings" onClick={() => setSettingsOpen(true)}>⚙</button>
          </div>
        </header>
        {experimental ? (
          <div className="expbanner"><span className="pdot yellow" />Experimental mode — unverified routines enabled</div>
        ) : null}
        <main id="view"><Current /></main>
        <nav className="tabs" aria-label="Screens">
          {screens.map((s) => (
            <button key={s.id} aria-current={s.id === tab ? "page" : undefined} onClick={() => setTab(s.id)}>
              <span className="nd" />{s.label}
            </button>
          ))}
        </nav>
        {sheetFaults && !settingsOpen && prefs.consentDone ? <FaultSheet faults={sheetFaults} onDismiss={dismissFaults} /> : null}
        {settingsOpen ? <Settings onClose={() => setSettingsOpen(false)} /> : null}
        {!prefs.consentDone ? <Consent /> : null}
        {toast ? <div className={`toast${toast.bad ? " bad" : ""}`} role="status">{toast.msg}</div> : null}
      </div>
    </AppCtx.Provider>
  );
}
