// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import "../admin.css";
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { AutomapReply, MapItem, MapResponse, SniffLid } from "../api/schemas";
import { useSniff, type SniffState } from "../api/useSniff";
import { CoverageBar } from "../components/CoverageBar";
import { SniffBadge } from "../components/SniffBadge";
import { StatusTag } from "../components/StatusTag";
import { StepHeader } from "../components/StepHeader";
import { coverageOf } from "../lib/catalog";
import { readList, writeList } from "../state/prefs";
import { canonicalModule } from "../layout";
import { mergeReadings, recordFromSolve, signalNameFor, type LabelCapture, type Reading } from "../lib/mapping";
import { useApp } from "../state/app";

/** Derived status (ADR-0008) from /catalog by item name; the legacy /map ok/maybe/todo
 * is the fallback when the catalog is unavailable. */
const LEGACY: Record<string, string> = { ok: "verified", maybe: "candidate", todo: "sniff" };
const EDGE: Record<string, string> = { verified: "edge-green", candidate: "edge-yellow" };
const edgeOf = (status: string) => EDGE[status] ?? "edge-grey";

function liveFor(lid: string, sig: string | undefined, sniff: SniffState) {
  const byLid = new Map<string, SniffLid>((sniff.data?.lids ?? []).map((l) => [l.lid, l]));
  const ids = lid.split(/\s+/);
  const hit = ids.map((x) => byLid.get(x)).find(Boolean);
  if (!hit) return { our: null, raw: null, active: false };
  const decode = hit.decode ?? [];
  const our = sig
    ? (() => { const s = decode.find((d) => d.name === sig); return s ? `${s.value} ${s.unit ?? ""}`.trim() : null; })()
    : decode.length ? decode.map((d) => `${d.name}=${d.value}${d.unit ?? ""}`).join(", ") : null;
  return { our, raw: hit.raw, active: ids.some((x) => sniff.active.has(x)) };
}

function MappedRow({ module, cat, item, status, sniff, labels }: {
  module: string; cat: string; item: MapItem; status: string; sniff: SniffState; labels: LabelCapture[];
}) {
  const { toast, community, reloadCommunity } = useApp();
  const key = `read:${module}|${cat}|${item.name}`; // legacy key: readings saved by v1 still load
  const [readings, setReadings] = useState<Reading[]>(() => readList<Reading>(key));
  const [truth, setTruth] = useState("");
  const [result, setResult] = useState<AutomapReply | null>(null);
  const [saved, setSaved] = useState(false);
  const lid = item.lid ?? "";
  const lv = liveFor(lid, item.sig, sniff);
  const name = signalNameFor(item);
  // Solver input: this device's readings + the Label tab's server labels for these LIDs.
  const merged = useMemo(() => mergeReadings(readings, labels, lid.split(/\s+/)), [readings, labels, lid]);
  const samples = merged.readings;

  useEffect(() => {
    if (!samples.length) return; // nothing to solve; the result box is hidden
    let alive = true;
    api.automap({ samples, candidate_lids: lid.split(/\s+/), name, unit: "" })
      .then((r) => alive && setResult(r), (e: Error) => alive && setResult({ ok: false, error: e.message }));
    return () => { alive = false; };
  }, [samples, lid, name]);

  const record = () => {
    const text = truth.trim();
    if (!text) return;
    const raws: Record<string, string> = {};
    for (const l of sniff.data?.lids ?? []) if (lid.split(/\s+/).includes(l.lid)) raws[l.lid] = l.raw;
    if (!Object.keys(raws).length) {
      return toast(`Nothing heard for 21 ${lid} yet — open this value's screen on the NanoCom so it asks the module for it.`, true);
    }
    const next = [...readings, { text, raws }];
    writeList(key, next);
    setReadings(next);
    setTruth("");
    setSaved(false);
  };
  const clear = () => { writeList(key, []); setReadings([]); };
  const saveToStore = async () => {
    if (!result?.ok) return;
    const rec = recordFromSolve(result, name);
    try {
      const res = await api.upsertSignal(module, rec);
      if (!res.ok) return toast(res.error ?? "could not save", true);
      setSaved(true);
      let msg = `${name} → signals/${module}.json (candidate)`;
      if (community?.consent === true) {
        const sh = await api.contribute({
          module, lid: result.lid, offset: result.offset, kind: result.kind, name, our_value: null,
          confidence: "candidate", answer: { type: "map", value: result.signal ?? result.rule ?? "" },
        }).catch(() => ({ ok: false, queued: false }));
        // a queued contribution is accepted (HTTP 202, ok: true) but not sent yet
        msg += sh.queued ? " · saved, will send later" : sh.ok ? " · shared ✓" : "";
        reloadCommunity();
      }
      toast(msg);
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  return (
    <div className={`ro ${edgeOf(status)}`} data-item={item.name}>
      <div className="ro-top" style={{ alignItems: "flex-start" }}>
        <div className="grow">
          <div className="ro-title row" style={{ gap: 8 }}><span className="grow">{item.name}</span><StatusTag status={status} /></div>
          {item.ref ? <div className="small dis pretty">{item.ref}</div> : null}
          <div className="row small" style={{ gap: 8, marginTop: 6 }}>
            <span className={`pdot ${lv.active ? "blue blink" : ""}`} title={lv.active ? "being polled now" : "idle"} />
            <span>ours: <b>{lv.our ?? "—"}</b></span>
            {lv.raw ? <span className="mono dis" title={`raw bytes of 21 ${lid}`}>{lv.raw}</span> : <span className="dis">no bytes heard yet</span>}
          </div>
          <form className="row" style={{ gap: 8, marginTop: 8 }} onSubmit={(e) => { e.preventDefault(); record(); }}>
            <input className="input grow" aria-label={`NanoCom value for ${item.name}`} value={truth}
              placeholder="the value the NanoCom shows now" onChange={(e) => setTruth(e.target.value)} />
            <button className="iconbtn" type="submit">save</button>
          </form>
          {samples.length ? (
            <div className="small" style={{ marginTop: 8 }}>
              {result == null ? <span className="dis">solving…</span>
                : !result.ok ? <span className="dis">{result.error}</span>
                : result.mode === "numeric" ? (
                  <div>→ <b>21 {result.lid}@{result.offset} {result.kind}</b> · R²={(result.r2 ?? 0).toFixed(3)}
                    {result.clean ? " · clean scale ✓" : " · uncertain scale"}{result.how === "guess" ? " (guess, 1 reading)" : ""}
                    <div className="mono dis">{result.signal}</div></div>
                ) : <div>→ <b>{result.rule}</b></div>}
              {result?.diff?.length ? (
                <div className="dis mono">changed: {result.diff.slice(0, 8).map((d) =>
                  `21 ${d.lid} b${d.byte}: ${d.values.map((v) => v.toString(16).padStart(2, "0")).join("→")}`).join(" · ")}</div>
              ) : samples.length >= 2 && result ? <div className="dis">No bytes changed between readings — either this value is not in this block, or it did not change. Change it (press the pedal, open the door) and type the new value.</div> : null}
              <div className="row wrap" style={{ gap: 8, marginTop: 6 }}>
                <span className="dis">{readings.length} reading(s) here</span>
                {merged.fromLabels ? <span className="labels-note">+ {merged.fromLabels} label{merged.fromLabels === 1 ? "" : "s"} from Label tab</span> : null}
                {result?.ok ? (
                  <button className="iconbtn" disabled={saved} onClick={saveToStore} title={`write to signals/${module}.json`}>
                    {saved ? "✓ saved (candidate)" : "✓ save to store"}
                  </button>
                ) : null}
                {readings.length ? <button className="iconbtn" onClick={clear}>clear {readings.length}</button> : null}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/** Admin "Decode": NanoCom (reference tool) menu items per module, with the live sniff
 * and the mapping loop (NanoCom value → automap → save to the signal store → optional
 * community share). The solver also uses the labels saved on the Label tab (GET /captures). */
export function CoverageMap() {
  const { module: active, toast } = useApp();
  const [module, setModule] = useState(canonicalModule(active));
  const [map, setMap] = useState<MapResponse | null>(null);
  const [derived, setDerived] = useState<{ module: string; byName: Map<string, string> } | null>(null);
  const sniff = useSniff(module, 1000);
  const [labels, setLabels] = useState<{ module: string; list: LabelCapture[] }>({ module, list: [] });

  useEffect(() => {
    let alive = true;
    api.captures(module).then(
      (r) => alive && setLabels({ module, list: r.captures }),
      () => alive && setLabels({ module, list: [] }), // no server labels: local readings only
    );
    return () => { alive = false; };
  }, [module]);
  const labelList = useMemo(() => (labels.module === module ? labels.list : []), [labels, module]);

  useEffect(() => {
    let alive = true;
    api.catalog(module).then(
      (c) => alive && setDerived({
        module,
        byName: new Map(c.pages.flatMap((p) => p.groups.flatMap((g) => g.items.map((i) => [i.name, i.status] as const)))),
      }),
      () => alive && setDerived(null),
    );
    return () => { alive = false; };
  }, [module]);
  const statusOf = (it: MapItem) =>
    (derived?.module === module ? derived.byName.get(it.name) : undefined) ?? LEGACY[it.status] ?? "sniff";

  useEffect(() => {
    let alive = true;
    api.map(module).then((d) => alive && setMap(d), (e: Error) => toast(e.message, true));
    return () => { alive = false; };
  }, [module, toast]);

  const items = map?.map.flatMap((g) => g.items) ?? [];
  const cov = coverageOf(items.map((i) => ({ status: statusOf(i) })));

  return (
    <>
      <StepHeader title="Decode" purpose="match our values to the NanoCom" steps={[
        <>Connect the NanoCom with the ESP32 sniff tap on the K-line (the dashboard reads it with <code>--sniff PORT</code>).</>,
        <>Open the same screen on the NanoCom (e.g. Engine → Live data → Engine speed).</>,
        <>Type the value it shows next to our raw bytes, then <b>save</b>. After two or more readings the solver works out which bytes hold the value; <b>save to store</b> keeps the answer.</>,
      ]} />
      <div className="row wrap" style={{ gap: 8 }} role="tablist" aria-label="Module">
        {(map?.modules ?? [module]).map((m) => {
          const c = map?.coverage[m];
          return (
            <button key={m} className={`chan ${m === module ? "on" : ""}`} role="tab" aria-selected={m === module} onClick={() => setModule(m)}>
              {m.toUpperCase()}{c ? <span className="dis">{c.total ? Math.round((100 * c.ok) / c.total) : 0}%</span> : null}
            </button>
          );
        })}
      </div>
      {!map ? <div className="empty">Loading the NanoCom menu for {module.toUpperCase()}…</div> : !map.map.length ? (
        <div className="empty pretty">No NanoCom menu has been written down for {module.toUpperCase()} yet, so there is nothing to match here.</div>
      ) : (
        <>
          <div className="card">
            <CoverageBar coverage={cov} label="NanoCom items we can decode" />
            <div className="small muted" style={{ marginTop: 8 }}>{cov.verified} of {items.length} NanoCom items decoded on {module.toUpperCase()}.</div>
            <div style={{ marginTop: 8 }}><SniffBadge sniff={sniff} /></div>
            <div className="labels-note" style={{ marginTop: 6 }}>
              {labelList.length
                ? `${labelList.length} label${labelList.length === 1 ? "" : "s"} from Label tab feed the solver for matching blocks.`
                : "No labels from the Label tab yet — the solver uses only the readings typed here."}
            </div>
          </div>
          {map.map.map((g) => (
            <section key={g.cat}>
              <div className="kicker group-title">{g.cat} <span className="dis">{g.items.filter((i) => statusOf(i) === "verified").length}/{g.items.length}</span></div>
              <div className="grid">
                {g.items.map((it) => it.lid ? (
                  <MappedRow key={it.name} module={module} cat={g.cat} item={it} status={statusOf(it)} sniff={sniff} labels={labelList} />
                ) : (
                  <div key={it.name} className={`ro ${edgeOf(statusOf(it))}`} data-item={it.name}>
                    <div className="ro-top"><div className="grow">
                      <div className="ro-title row" style={{ gap: 8 }}><span className="grow">{it.name}</span><StatusTag status={statusOf(it)} /></div>
                      {it.ref ? <div className="small dis pretty">{it.ref}</div> : null}
                      <div className="small dis">Not linked to a data block yet — find its LID on the Label tab first.</div>
                    </div></div>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </>
      )}
    </>
  );
}
