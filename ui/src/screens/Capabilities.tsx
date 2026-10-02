import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { MapResponse } from "../api/schemas";
import { storeModule } from "../lib/format";
import { useApp } from "../state/app";

/** Read-only catalogue of what the NanoCom exposes per module, and how far this project
 * can read it today. Backed by the same per-module menu data as the admin Map tab, but
 * without the sniff/mapping/write machinery — a plain "what data could become available"
 * view. No live values are shown for undecoded fields (data-honesty rule). */

const STATUS: Record<string, [string, string, string]> = {
  ok: ["green", "edge-green", "decoded"],
  maybe: ["yellow", "edge-yellow", "candidate"],
};
const statusOf = (s: string) => STATUS[s] ?? ["", "edge-grey", "sniff target"];

export function Capabilities() {
  const { module: active, toast } = useApp();
  const [module, setModule] = useState(storeModule(active));
  const [map, setMap] = useState<MapResponse | null>(null);

  useEffect(() => {
    let alive = true;
    api.map(module).then((d) => alive && setMap(d), (e: Error) => toast(e.message, true));
    return () => { alive = false; };
  }, [module, toast]);

  const items = map?.map.flatMap((g) => g.items) ?? [];
  const ok = items.filter((i) => i.status === "ok").length;
  const maybe = items.filter((i) => i.status === "maybe").length;
  const todo = items.length - ok - maybe;
  const total = items.length || 1;
  const pct = (n: number) => `${((n / total) * 100).toFixed(1)}%`;

  return (
    <>
      <div className="screen-head"><h2>Capabilities</h2><span className="sub">· what the NanoCom exposes</span></div>
      <div className="small muted pretty" style={{ marginBottom: 10 }}>
        Every function the NanoCom reaches on each module, and how far this project decodes it.
        Mapped from the tool's own menus — see the Docs tab (NanoCom feature map).
      </div>
      <div className="row wrap" style={{ gap: 8 }} role="tablist" aria-label="Module">
        {(map?.modules ?? [module]).map((m) => {
          const c = map?.coverage[m];
          return (
            <button key={m} className={`chan ${m === module ? "on" : ""}`} role="tab" aria-selected={m === module}
              onClick={() => setModule(m)}>
              {m.toUpperCase()}{c ? <span className="dis">{c.total ? Math.round((100 * c.ok) / c.total) : 0}%</span> : null}
            </button>
          );
        })}
      </div>
      {!map ? <div className="empty">Loading…</div> : items.length === 0 ? (
        <div className="empty"><div className="title">No catalogue for this module yet</div>
          <div className="pretty">Its NanoCom functions haven't been transcribed into the coverage map.</div></div>
      ) : (
        <>
          <div className="card">
            <div className="row wrap" style={{ gap: 16, marginBottom: 10 }}>
              <span className="row small" style={{ gap: 6 }}><span className="pdot green" />Decoded · {ok}</span>
              <span className="row small" style={{ gap: 6 }}><span className="pdot yellow" />Candidate · {maybe}</span>
              <span className="row small" style={{ gap: 6 }}><span className="pdot" />Sniff target · {todo}</span>
            </div>
            <div className="bar" role="img" aria-label={`${ok} of ${items.length} decoded`}>
              <span className="ok" style={{ width: pct(ok) }} /><span className="maybe" style={{ width: pct(maybe) }} />
              <span className="todo" style={{ width: pct(todo) }} />
            </div>
            <div className="small muted" style={{ marginTop: 8 }}>
              {ok} of {items.length} fields decoded on {module.toUpperCase()} · {maybe} candidate · {todo} still to sniff.
            </div>
          </div>
          {map.map.map((g) => (
            <section key={g.cat}>
              <div className="kicker group-title">{g.cat}
                <span className="dis"> {g.items.filter((i) => i.status === "ok").length}/{g.items.length}</span></div>
              <div className="grid">
                {g.items.map((it) => {
                  const [dot, edge, word] = statusOf(it.status);
                  return (
                    <div key={it.name} className={`ro ${edge}`} data-item={it.name}>
                      <div className="ro-top"><div className="grow">
                        <div className="ro-title">
                          <span className={`pdot ${dot}`} style={{ display: "inline-block", marginRight: 6 }} />{it.name}
                          <span className="small dis" style={{ marginLeft: 8 }}>{word}</span>
                        </div>
                        {it.ref ? <div className="small dis pretty">{it.ref}</div> : null}
                      </div></div>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </>
      )}
    </>
  );
}
