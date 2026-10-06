// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { command } from "../api/client";
import type { FaultScanEntry } from "../api/schemas";
import { useAction } from "../api/useAction";
import { confirmAction } from "../components/confirm";
import { ConnectionNotice } from "../components/ConnectionNotice";
import { CoverageBar } from "../components/CoverageBar";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { moduleName } from "../layout";
import { pageOf } from "../lib/catalog";
import { parseFault, type ParsedFault } from "../lib/format";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

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

function FaultGroup({ items, label, kind, note }: {
  items: ParsedFault[]; label: string; kind: "current" | "logged"; note: string;
}) {
  const { faultMeaning } = useApp();
  if (!items.length) return null;
  return (
    <section>
      <div className="row group-title" style={{ gap: 8 }}>
        <span className="kicker">{label} · {items.length}</span><span className="small dis">{note}</span>
      </div>
      <div className="stack">
        {items.map((f) => {
          const m = faultMeaning(f.orig);
          return (
            <div className={`fault ${kind}`} key={`${f.raw}${f.text}${f.tag}`}>
              <span className="ficon" aria-hidden="true">!</span>
              <div className="ftext">
                {f.text}
                {m?.cause ? <div className="small muted pretty">{m.cause}</div> : null}
              </div>
              <div className="fmeta">
                {f.raw ? <span className="code">{f.raw}</span> : null}
                {m?.pcode ? <span className="code">{m.pcode}</span> : null}
                <span>{f.tag || label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

const SCAN_ICON: Record<string, string> = { ok: "✓", faults: "⚠", error: "✕", unimplemented: "·" };

/** Read-all-faults scan: every module in turn, establish → read → release. Read-only. */
function FaultScan() {
  const { toast } = useApp();
  const { active: replaying } = useReplay();
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
        <button className="iconbtn" onClick={run} disabled={busy || replaying}>{busy ? "Scanning…" : "Scan all modules"}</button>
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
  const { snap, module, refresh, toast, catalog, experimental } = useApp();
  const { active: replaying } = useReplay();
  const run = useAction();
  const page = pageOf(catalog, "faults");
  const coverage = experimental && page ? <CoverageBar coverage={page.coverage} label="Faults coverage" /> : null;
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
    await run("clear_faults");
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
      <button className={`iconbtn ${watch ? "on" : ""}`} aria-pressed={watch} onClick={toggleWatch} disabled={replaying}
        title="Polls faults every cycle (~0.5 s) instead of every ~5 s">
        <span className="d" />{watch ? "Watch ON" : "Fault watch"}
      </button>
      <button className="iconbtn" onClick={refresh} disabled={replaying}><span className="d" />Read</button>
    </ScreenHead>
  );
  if (snap?.status !== "connected") return <>{head}<ConnectionNotice />{coverage}<StatusGate withNotice /><FaultScan /></>;
  return (
    <>
      {head}
      <ConnectionNotice />
      {coverage}
      <FaultGroup items={current} label="Current" kind="current" note="present now" />
      <FaultGroup items={logged} label="Logged" kind="logged" note="stored history — not necessarily present now" />
      {!parsed.length ? (
        <div className="health ok" role="status"><span className="hi" aria-hidden="true">✓</span>
          <span>No fault codes — this module reports a clean fault memory.</span></div>
      ) : (
        <div className="card">
          <span className="kicker">Report</span>
          <div className="small muted pretty" style={{ paddingTop: 8 }}>
            {parsed.length} code(s) on {moduleName(module)}. Clear writes to the ECU — ignition on,
            engine off, re-read after one drive cycle.
          </div>
          <div className="row" style={{ gap: 8, marginTop: 10 }}>
            <button className="iconbtn" onClick={writeFile}>Write to file</button>
            {replaying ? (
              <span className="locked replay-lock" style={{ marginLeft: "auto" }} aria-label="Clear codes: replay, read only">
                <span aria-hidden="true">🔒</span>Clear codes · replay
              </span>
            ) : (
              <button className="iconbtn danger" style={{ marginLeft: "auto" }} onClick={clear}><span className="d" />Clear codes</button>
            )}
          </div>
        </div>
      )}
      <FaultScan />
    </>
  );
}
