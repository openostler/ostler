import { moduleName } from "../layout";
import { connOf, isNotLive } from "../lib/connection";
import { useApp } from "../state/app";

/** Shown instead of live content while not connected. Null when connected.
 * `withNotice`: the page also shows a ConnectionNotice, so only the "Connecting…" card is
 * drawn here (the notice covers the not-live states). Drive uses the full gate. */
export function StatusGate({ withNotice = false }: { withNotice?: boolean }) {
  const { snap, module, live, openConnection } = useApp();
  const st = snap?.status;
  if (st === "connected") return null;
  if (withNotice && isNotLive(connOf(snap))) return null;
  if (st === "error") {
    return (
      <div className="card bad">
        <div style={{ fontWeight: 700, color: "var(--ic-red)" }}>Not connected</div>
        <div className="small muted pretty" style={{ marginTop: 4 }}>
          {snap?.error || "The module did not answer."}
        </div>
        <button className="btn accent" style={{ marginTop: 10 }} onClick={openConnection}>
          Open connection
        </button>
      </div>
    );
  }
  const last = live.seq.length ? live.seq[live.seq.length - 1]?.phase : "connecting…";
  return (
    <div className="card" role="status">
      <div className="row" style={{ gap: 10 }}>
        <span className="pdot yellow blink" />
        <div className="grow">
          <div style={{ fontWeight: 700 }}>Connecting to {moduleName(module)}…</div>
          <div className="small dis">{last}</div>
        </div>
      </div>
    </div>
  );
}
