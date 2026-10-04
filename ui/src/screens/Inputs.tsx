import { useState } from "react";
import { command } from "../api/client";
import type { CatalogItem } from "../api/schemas";
import { CoverageBar } from "../components/CoverageBar";
import { HealthStrip } from "../components/HealthStrip";
import { PlaceholderReadout } from "../components/PlaceholderReadout";
import { Readout } from "../components/Readout";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { Trend } from "../components/Trend";
import { GROUP_ORDER, moduleName } from "../layout";
import { pageOf, visibleGroups } from "../lib/catalog";
import { useApp } from "../state/app";

function useCsv() {
  const { snap, module, toast } = useApp();
  const [pending, setPending] = useState<boolean | null>(null); // optimistic state while the command runs
  const recording = pending ?? !!snap?.logging?.recording;
  const toggle = async () => {
    const starting = !recording;
    if (starting && module === "slabs" && !window.confirm(
      "SLABS only communicates while stationary — comms drop as soon as the car moves.\n" +
      "This log will NOT capture a drive. To log a drive (rpm, speed, boost, temps), switch to TD5 first.\n\n" +
      "Start the SLABS log anyway?",
    )) return;
    setPending(starting);
    toast(starting ? "recording…" : "stopping…");
    try {
      const r = await command(starting ? "start_csv" : "stop_csv");
      if (r.ok) {
        const parts = [r.message ?? "ok", r.file, !starting && r.rows != null ? `${r.rows} rows` : null];
        toast(parts.filter(Boolean).join(" · "));
      } else toast(r.error ?? "error", true);
    } catch (e) {
      toast((e as Error).message, true);
    } finally {
      setPending(null);
    }
  };
  return { recording, toggle };
}

type Filter = "all" | "attention" | "unverified";

/** Experimental: catalog inputs with no live value (not in the store yet, or sniff /
 * untranscribed NanoCom fields) as honest placeholders — never a value. */
function NotDecoded({ items }: { items: { title: string; items: CatalogItem[] }[] }) {
  if (!items.length) return null;
  return (
    <section aria-label="From NanoCom — not yet decoded">
      <div className="kicker group-title">From NanoCom — not yet decoded</div>
      {items.map((g) => (
        <div key={g.title} className="stack" style={{ marginBottom: 12 }}>
          <div className="small dis">{g.title}</div>
          <div className="grid">{g.items.map((i) => <PlaceholderReadout key={i.id} item={i} />)}</div>
        </div>
      ))}
    </section>
  );
}

export function Inputs() {
  const { snap, module, fields, live, catalog, experimental, openConnection } = useApp();
  const [plot, setPlot] = useState<string[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const { recording, toggle } = useCsv();

  const signals = snap?.signals ?? {};
  // every expected field (placeholders without a cable) plus anything live; the _mm
  // heights duplicate the raw heights on SLABS, so they live on Drive only
  const unverified = (n: string) => (signals[n]?.c ?? fields[n]?.c) === "candidate";
  // Stable shows verified (proven) signals only
  const all = [...new Set([...Object.keys(fields), ...Object.keys(signals)])]
    .filter((n) => !n.endsWith("_mm") && (experimental || !unverified(n)));
  const needsAttention = (n: string) => ["low", "high", "suspect"].includes(signals[n]?.s ?? "");
  const names = all.filter((n) => filter === "all" || (filter === "attention" ? needsAttention(n) : unverified(n)));
  const groupOf = (n: string) => fields[n]?.group ?? "Other";
  const labelOf = (n: string) => fields[n]?.label ?? n;
  const byGroup = new Map<string, string[]>();
  for (const n of names) byGroup.set(groupOf(n), [...(byGroup.get(groupOf(n)) ?? []), n]);
  const order = [...GROUP_ORDER.filter((g) => byGroup.has(g)), ...[...byGroup.keys()].filter((g) => !GROUP_ORDER.includes(g))];
  const channels = all.filter((n) => typeof signals[n]?.v === "number").sort((a, b) => labelOf(a).localeCompare(labelOf(b)));
  const togglePlot = (n: string) =>
    setPlot((p) => (p.includes(n) ? p.filter((x) => x !== n) : p.length < 3 ? [...p, n] : p));

  const page = pageOf(catalog, "inputs");
  const placeholders = experimental
    ? visibleGroups(page, true)
      .map(({ group, items }) => ({ title: group.title, items: items.filter((i) => !i.sig || !(i.sig in fields || i.sig in signals)) }))
      .filter((g) => g.items.length)
    : [];
  const coverage = experimental && page ? <CoverageBar coverage={page.coverage} label="Inputs coverage" /> : null;

  const head = (
    <ScreenHead title="Inputs">
      {recording && snap?.logging?.file ? (
        <span className="small dis mono">{snap.logging.file}{snap.logging.rows != null ? ` · ${snap.logging.rows} rows` : ""}</span>
      ) : null}
      <button className={`iconbtn ${recording ? "rec" : ""}`} aria-pressed={recording} onClick={toggle}>
        <span className="d" />{recording ? "Stop" : "Log CSV"}
      </button>
    </ScreenHead>
  );
  if (snap?.status !== "connected") return <>{head}<StatusGate />{coverage}<NotDecoded items={placeholders} /></>;
  return (
    <>
      {head}
      {module === "slabs" ? (
        <div className="card warn small">SLABS only communicates while stationary — to log a drive (rpm, boost, temps), switch to TD5.</div>
      ) : null}
      <HealthStrip />
      {coverage}
      <div className="seg" role="group" aria-label="Show">
        {([["all", "All"], ["attention", `Attention · ${all.filter(needsAttention).length}`], ["unverified", "Unverified"]] as const)
          .filter(([id]) => experimental || id !== "unverified").map(([id, text]) => (
          <button key={id} aria-pressed={filter === id} onClick={() => setFilter(id)}>{text}</button>
        ))}
      </div>
      {names.length ? (
        order.map((g) => {
          const items = (byGroup.get(g) ?? []).sort((a, b) => labelOf(a).localeCompare(labelOf(b)));
          const bad = items.filter(needsAttention).length;
          return (
            <section key={g}>
              <div className="kicker group-title">{g}{bad ? <span style={{ color: "var(--alarm)" }}> · {bad} need attention</span> : null}</div>
              <div className="grid">
                {items.map((n) => <Readout key={n} name={n} sig={signals[n]} field={fields[n]} />)}
              </div>
            </section>
          );
        })
      ) : filter !== "all" ? (
        <div className="empty"><div className="title">{filter === "attention" ? "Nothing needs attention" : "No unverified signals"}</div></div>
      ) : (
        <div className="empty"><div className="title">No live inputs yet</div>
          <div className="pretty">Connect {moduleName(module)} from the connection pill in the header. The K-line carries one session at a time.</div>
          <button className="btn" onClick={openConnection}>Open connection</button></div>
      )}
      <NotDecoded items={placeholders} />
      {all.length ? (
        <section>
          <div className="row group-title"><span className="kicker">Compare · 60 s</span>
            <span className="small dis" style={{ marginLeft: "auto" }}>tap up to three channels to plot</span></div>
          <Trend channels={plot} history={live.history} labelOf={labelOf} unitOf={(n) => signals[n]?.u ?? ""} />
          <div className="small dis pretty" style={{ margin: "6px 2px 0" }}>
            History is held in this session only — switching module or reloading discards it. Log to CSV to keep it.
          </div>
          <div className="chanwrap" style={{ marginTop: 8 }}>
            {channels.length ? channels.map((n) => (
              <button key={n} className={`chan ${plot.includes(n) ? "on" : ""}`} aria-pressed={plot.includes(n)}
                onClick={() => togglePlot(n)}>
                <span className={`pdot ${plot.includes(n) ? "blue" : ""}`} />{labelOf(n)}
              </button>
            )) : <span className="dis">waiting for live values…</span>}
          </div>
        </section>
      ) : null}
    </>
  );
}
