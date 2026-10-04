import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AutomapReply, MapItem, MapResponse, SniffLid } from "../api/schemas";
import { useSniff, type SniffState } from "../api/useSniff";
import { CoverageBar } from "../components/CoverageBar";
import { SniffBadge } from "../components/SniffBadge";
import { StatusTag } from "../components/StatusTag";
import { catalogModule, coverageOf } from "../lib/catalog";
import { readList, writeList } from "../state/prefs";
import { storeModule } from "../lib/format";
import { recordFromSolve, signalNameFor } from "../lib/mapping";
import { useApp } from "../state/app";

type Reading = { text: string; raws: Record<string, string> };

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

function MappedRow({ module, cat, item, status, sniff }: {
  module: string; cat: string; item: MapItem; status: string; sniff: SniffState;
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

  useEffect(() => {
    if (!readings.length) return; // nothing to solve; the result box is hidden
    let alive = true;
    api.automap({ samples: readings, candidate_lids: lid.split(/\s+/), name, unit: "" })
      .then((r) => alive && setResult(r), (e: Error) => alive && setResult({ ok: false, error: e.message }));
    return () => { alive = false; };
  }, [readings, lid, name]);

  const record = () => {
    const text = truth.trim();
    if (!text) return;
    const raws: Record<string, string> = {};
    for (const l of sniff.data?.lids ?? []) if (lid.split(/\s+/).includes(l.lid)) raws[l.lid] = l.raw;
    if (!Object.keys(raws).length) return toast("No sniff data for that LID yet — is the reference tool on the field?", true);
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
        msg += sh.ok ? " · shared ✓" : sh.queued ? " · queued (offline)" : "";
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
            {lv.raw ? <span className="mono dis">{lv.raw}</span> : null}
          </div>
          <form className="row" style={{ gap: 8, marginTop: 8 }} onSubmit={(e) => { e.preventDefault(); record(); }}>
            <input className="input grow" aria-label={`Reference tool value for ${item.name}`} value={truth}
              placeholder="value shown on the reference tool" onChange={(e) => setTruth(e.target.value)} />
            <button className="iconbtn" type="submit">save</button>
          </form>
          {readings.length ? (
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
              ) : readings.length >= 2 && result ? <div className="dis">no bytes changed — the field isn't in this LID, or the value didn't change</div> : null}
              <div className="row" style={{ gap: 8, marginTop: 6 }}>
                <span className="dis">{readings.length} reading(s)</span>
                {result?.ok ? (
                  <button className="iconbtn" disabled={saved} onClick={saveToStore} title={`write to signals/${module}.json`}>
                    {saved ? "✓ saved (candidate)" : "✓ save to store"}
                  </button>
                ) : null}
                <button className="iconbtn" onClick={clear}>clear {readings.length}</button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

/** Admin: reference-tool coverage per module, with the live sniff and the mapping loop
 * (plaintext reading → automap → save to the signal store → optional community share). */
export function CoverageMap() {
  const { module: active, toast } = useApp();
  const [module, setModule] = useState(storeModule(active));
  const [map, setMap] = useState<MapResponse | null>(null);
  const [derived, setDerived] = useState<{ module: string; byName: Map<string, string> } | null>(null);
  const sniff = useSniff(module, 1000);

  useEffect(() => {
    let alive = true;
    api.catalog(catalogModule(module)).then(
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
      <div className="screen-head"><h2>Map</h2><span className="sub">· reference-tool coverage</span></div>
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
      {!map ? <div className="empty">Loading coverage…</div> : (
        <>
          <div className="card">
            <CoverageBar coverage={cov} label="Reference-tool coverage" />
            <div className="small muted" style={{ marginTop: 8 }}>{cov.verified} of {items.length} reference-tool items mapped on {module.toUpperCase()}.</div>
            <div style={{ marginTop: 8 }}><SniffBadge sniff={sniff} /></div>
          </div>
          {map.map.map((g) => (
            <section key={g.cat}>
              <div className="kicker group-title">{g.cat} <span className="dis">{g.items.filter((i) => statusOf(i) === "verified").length}/{g.items.length}</span></div>
              <div className="grid">
                {g.items.map((it) => it.lid ? (
                  <MappedRow key={it.name} module={module} cat={g.cat} item={it} status={statusOf(it)} sniff={sniff} />
                ) : (
                  <div key={it.name} className={`ro ${edgeOf(statusOf(it))}`} data-item={it.name}>
                    <div className="ro-top"><div className="grow">
                      <div className="ro-title row" style={{ gap: 8 }}><span className="grow">{it.name}</span><StatusTag status={statusOf(it)} /></div>
                      {it.ref ? <div className="small dis pretty">{it.ref}</div> : null}
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
