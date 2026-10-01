import { useState } from "react";
import { command } from "../api/client";
import type { FaultScanEntry } from "../api/schemas";
import { confirmAction } from "../components/confirm";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { moduleName } from "../layout";
import { parseFault, type ParsedFault } from "../lib/format";
import { useApp } from "../state/app";

function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function FaultGroup({ items, label, edge, dot, note }: {
  items: ParsedFault[]; label: string; edge: string; dot: string; note: string;
}) {
  if (!items.length) return null;
  return (
    <section>
      <div className="row group-title" style={{ gap: 8 }}>
        <span className={`pdot ${dot}`} /><span className="kicker">{label}</span>
        <span className="small dis">{note}</span>
      </div>
      <div className="grid">
        {items.map((f) => (
          <div className={`ro ${edge}`} key={`${f.raw}${f.text}${f.tag}`}>
            <div className="ro-top"><div className="grow">
              <div className="ro-title">{f.text}</div>
              <div className="small dis">{[f.raw, f.tag].filter(Boolean).join(" · ")}</div>
            </div></div>
          </div>
        ))}
      </div>
    </section>
  );
}

const SCAN_ICON: Record<string, string> = { ok: "✓", faults: "⚠", error: "✕", unimplemented: "·" };

/** Read-all-faults scan: every module in turn, establish → read → release. Read-only. */
function FaultScan() {
  const { toast } = useApp();
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<{ at: string; mode: string; entries: FaultScanEntry[] } | null>(null);
  const run = async () => {
    setBusy(true);
    try {
      const r = await command("read_all_faults");
      if (!r.ok) toast(r.error ?? "scan failed", true);
      else setReport({ at: new Date().toLocaleTimeString(), mode: String(r.mode ?? ""), entries: r.report ?? [] });
    } catch (e) {
      toast((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="card">
      <div className="row"><span className="kicker grow">All modules</span>
        <button className="iconbtn" onClick={run} disabled={busy}>{busy ? "Scanning…" : "Scan all modules"}</button>
      </div>
      <div className="small muted pretty" style={{ marginTop: 6 }}>
        Reads every module one at a time (the bus is shared). Takes up to 45 s.
      </div>
      {report ? (
        <div className="stack" style={{ marginTop: 10 }}>
          <div className="small dis">{report.mode} · {report.at}</div>
          {report.entries.map((e) => (
            <div key={e.module} className={`ro ${e.status === "ok" ? "edge-green" : e.status === "faults" ? "edge-yellow" : e.status === "error" ? "edge-red" : "edge-grey"}`}>
              <div className="ro-top"><div className="grow">
                <div className="ro-title">{SCAN_ICON[e.status] ?? "·"} {e.module}</div>
                {e.faults.map((f) => <div key={f} className="small">{f}</div>)}
                {e.error ? <div className="small" style={{ color: "var(--ic-red)" }}>{e.error}</div> : null}
                {e.note ? <div className="small dis">{e.note}</div> : null}
              </div></div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function Faults() {
  const { snap, module, refresh, toast } = useApp();
  const faults = snap?.faults ?? [];
  const parsed = faults.map(parseFault);
  const current = parsed.filter((f) => f.current);
  const logged = parsed.filter((f) => !f.current);
  const watch = !!snap?.fault_watch;

  const toggleWatch = async () => {
    const on = !watch;
    toast(on ? "fault watch ON — polling every cycle" : "fault watch off");
    try { await command("set_fault_watch", { on }); } catch (e) { toast((e as Error).message, true); }
    refresh();
  };
  const clear = async () => {
    if (!confirmAction(`Clear ${faults.length} fault code(s) from ${moduleName(module)}?`,
      "Writes to the ECU and cannot be undone. Ignition on, engine off.")) return;
    toast("clearing…");
    try {
      const r = await command("clear_faults");
      toast(r.ok ? r.message ?? "clear sent — re-reading…" : r.error ?? "clear failed", !r.ok);
    } catch (e) {
      toast((e as Error).message, true);
    }
    window.setTimeout(refresh, 1500);
  };
  const writeFile = () => {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const lines = ["D2 Diag — fault report", `Module: ${moduleName(module)}`, `Time:   ${new Date().toISOString()}`,
      `Codes:  ${faults.length}`, "", ...(faults.length ? faults.map((f) => `  ${f}`) : ["  (no fault codes)"])];
    const name = `faults-${module}-${stamp}.txt`;
    download(name, lines.join("\n") + "\n");
    toast(`wrote ${name}`);
  };

  const head = (
    <ScreenHead title="Faults">
      <button className={`iconbtn ${watch ? "on" : ""}`} aria-pressed={watch} onClick={toggleWatch}
        title="Polls faults every cycle (~0.5 s) instead of every ~5 s">
        <span className="d" />{watch ? "Watch ON" : "Fault watch"}
      </button>
      <button className="iconbtn" onClick={refresh}><span className="d" />Read</button>
    </ScreenHead>
  );
  if (snap?.status !== "connected") return <>{head}<StatusGate /><FaultScan /></>;
  return (
    <>
      {head}
      <FaultGroup items={current} label="Current" edge="edge-red" dot="red" note="present now" />
      <FaultGroup items={logged} label="Logged" edge="edge-yellow" dot="yellow" note="stored history" />
      {!parsed.length ? (
        <div className="empty"><div className="title">No fault codes</div>
          <div className="pretty">This module reports a clean fault memory.</div></div>
      ) : (
        <div className="card">
          <span className="kicker">Report</span>
          <div className="small muted pretty" style={{ paddingTop: 8 }}>
            {parsed.length} code(s) on {moduleName(module)}. Clear writes to the ECU — ignition on,
            engine off, re-read after one drive cycle.
          </div>
          <div className="row" style={{ gap: 8, marginTop: 10 }}>
            <button className="iconbtn" onClick={writeFile}>Write to file</button>
            <button className="iconbtn danger" style={{ marginLeft: "auto" }} onClick={clear}><span className="d" />Clear codes</button>
          </div>
        </div>
      )}
      <FaultScan />
    </>
  );
}
