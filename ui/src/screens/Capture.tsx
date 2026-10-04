import { useRef, useState } from "react";
import { api, command } from "../api/client";
import type { SniffLid } from "../api/schemas";
import { useSniff } from "../api/useSniff";
import { ScreenHead } from "../components/ScreenHead";
import { SniffBadge } from "../components/SniffBadge";
import { moduleName } from "../layout";
import { spacedHex, storeModule } from "../lib/format";
import { useApp } from "../state/app";
import { readList, writeList } from "../state/prefs";

type LogEntry = { lid: string; raw: string; text: string; t: string };
// Legacy key ("fångst" = capture): kept so logs saved by the old pages survive.
const logKey = (module: string) => `fangstlog:${module}`;

function useCaptureLog(module: string) {
  const [log, setLog] = useState<LogEntry[]>(() => readList<LogEntry>(logKey(module)));
  const [shownFor, setShownFor] = useState(module);
  if (shownFor !== module) { // module changed: show that module's log (no effect needed)
    setShownFor(module);
    setLog(readList<LogEntry>(logKey(module)));
  }
  const add = (e: Omit<LogEntry, "t">) => {
    const next = [{ ...e, t: new Date().toLocaleTimeString() }, ...readList<LogEntry>(logKey(module))].slice(0, 200);
    writeList(logKey(module), next);
    setLog(next);
  };
  return { log, add };
}

const decodeText = (l?: SniffLid) =>
  l?.decode?.length ? l.decode.map((d) => `${d.name}=${d.value}${d.unit ?? ""}`).join(", ") : "(no mapping yet)";

type Phase = "idle" | "armed" | "done" | "timeout";

/** Batch capture from the sniff: arm, press READ on the reference tool, then label every
 * LID it polled. Each label → POST /capture (logs/labeled_captures.jsonl, automap's dataset). */
function SniffCapture({ onSaved }: { onSaved: (module: string, e: Omit<LogEntry, "t">) => void }) {
  const { toast } = useApp();
  const [phase, setPhase] = useState<Phase>("idle");
  const [batch, setBatch] = useState<Record<string, number>>({}); // lid → reads seen while armed
  const [texts, setTexts] = useState<Record<string, string>>({});
  const [left, setLeft] = useState(4);
  const armed = useRef<{ on: boolean; base: Record<string, number>; at: number; last: number; batch: Record<string, number> }>(
    { on: false, base: {}, at: 0, last: 0, batch: {} });

  // Each sniff poll while armed: collect LIDs whose count rose; stop 4 s after the last
  // new data (done) or after 4 s with nothing at all (timeout).
  const sniff = useSniff(undefined, 500, (s) => {
    const a = armed.current;
    if (!a.on) return;
    const t = Date.now();
    let grew = false;
    for (const l of s.data?.lids ?? []) {
      const b = a.base[l.lid];
      if (b == null || l.count > b) {
        a.batch = { ...a.batch, [l.lid]: (a.batch[l.lid] ?? 0) + 1 };
        a.base[l.lid] = l.count;
        grew = true;
      }
    }
    if (grew) { a.last = t; setBatch(a.batch); }
    const any = Object.keys(a.batch).length > 0;
    if (any && t - a.last > 4000) { a.on = false; setPhase("done"); }
    else if (!any && t - a.at > 4000) { a.on = false; setPhase("timeout"); }
    setLeft(Math.max(0, 4 - Math.round((t - (a.last || a.at)) / 1000)));
  });

  const lids = sniff.data?.lids ?? [];
  const byLid = Object.fromEntries(lids.map((l) => [l.lid, l]));

  const arm = () => {
    armed.current = { on: true, base: Object.fromEntries(lids.map((l) => [l.lid, l.count])), at: Date.now(), last: 0, batch: {} };
    setBatch({}); setTexts({}); setLeft(4); setPhase("armed");
  };
  const reset = () => { armed.current.on = false; setBatch({}); setTexts({}); setPhase("idle"); };
  const save = async () => {
    const module = sniff.data?.module ?? "?";
    let n = 0;
    for (const lid of Object.keys(batch)) {
      const text = (texts[lid] ?? "").trim();
      if (!text) continue;
      const raw = byLid[lid]?.raw ?? "";
      try { await api.capture({ module, lid, raw, text }); } catch { /* still logged locally */ }
      onSaved(module, { lid, raw, text });
      n++;
    }
    reset();
    toast(`${n} capture(s) saved`);
  };

  const status = {
    idle: "Press “New capture”, read on the reference tool, then describe the codes.",
    armed: `Waiting for a read… press READ on the reference tool (${left}s)`,
    done: `${Object.keys(batch).length} LID(s) captured — describe and save.`,
    timeout: "No data arrived — press READ on the reference tool and try again.",
  }[phase];

  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 8 }}>From the reference-tool sniff</div>
      <SniffBadge sniff={sniff} showActive={false} />
      <div className={`small ${phase === "timeout" ? "" : "muted"}`} style={{ margin: "8px 0", color: phase === "timeout" ? "var(--ic-red)" : undefined }} role="status">{status}</div>
      <div className="btn-row">
        <button className="btn accent" onClick={arm} disabled={!sniff.configured}>⬤ New capture</button>
        <button className="btn" onClick={reset}>↺ Cancel</button>
      </div>
      {Object.keys(batch).length ? (
        <div className="stack" style={{ marginTop: 12 }}>
          {Object.entries(batch).map(([lid, count]) => (
            <div className="ro" key={lid} style={{ padding: "10px 14px" }}>
              <div className="row"><b className="lid">21 {lid}</b><span className="small dis" style={{ marginLeft: "auto" }}>×{count}</span></div>
              <div className="mono small" style={{ wordBreak: "break-all" }}>{byLid[lid]?.raw ?? ""}</div>
              <div className="small muted">our mapping: {decodeText(byLid[lid])}</div>
              <input className="input" style={{ width: "100%", marginTop: 6 }} aria-label={`What the reference tool shows for 21 ${lid}`}
                placeholder="what does the reference tool show? (values in displayed order)"
                value={texts[lid] ?? ""} onChange={(e) => setTexts((t) => ({ ...t, [lid]: e.target.value }))} />
            </div>
          ))}
          <button className="btn accent" onClick={save}>Save batch</button>
        </div>
      ) : null}
    </div>
  );
}

/** Direct capture: read one LID from the connected ECU (read-only) and label it. */
function DirectCapture({ onSaved }: { onSaved: (module: string, e: Omit<LogEntry, "t">) => void }) {
  const { snap, module, toast } = useApp();
  const [lid, setLid] = useState("");
  const [last, setLast] = useState<{ lid: string; raw: string } | null>(null);
  const [text, setText] = useState("");
  const connected = snap?.status === "connected";

  const read = async () => {
    const id = lid.trim().replace(/^0x/i, "");
    if (!id) return toast("enter a LID", true);
    toast(`reading 21 ${id}…`);
    try {
      const r = await command("read_block", { lids: [id] });
      if (!r.ok) return toast(r.error ?? "read failed", true);
      const raws = r.raws ?? {};
      const raw = raws[id] ?? raws[id.toLowerCase()] ?? raws[id.toUpperCase()];
      if (!raw) return toast(`no answer for 21 ${id}`, true);
      setLast({ lid: id.toUpperCase(), raw });
    } catch (e) {
      toast((e as Error).message, true);
    }
  };
  const save = async () => {
    if (!last) return toast("read a LID first", true);
    if (!text.trim()) return toast("add a label", true);
    const rec = { module: storeModule(module), lid: last.lid.toLowerCase(), raw: spacedHex(last.raw), text: text.trim() };
    try {
      const r = await api.capture(rec);
      if (!r.ok) return toast(r.error ?? "error", true);
      onSaved(rec.module, rec);
      setLast(null); setText("");
      toast(r.stored === false ? "ok (capture store off)" : "saved");
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 8 }}>Read a LID directly · {moduleName(module)}</div>
      {!connected ? <div className="small" style={{ color: "var(--ic-yellow)", marginBottom: 8 }}>Connect {moduleName(module)} (connection pill in the header) to read live values.</div> : null}
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); void read(); }}>
        <input className="input mono" style={{ width: 160 }} aria-label="LID to read" placeholder="LID hex — e.g. 23"
          value={lid} onChange={(e) => setLid(e.target.value)} />
        <button className="btn accent" type="submit">Read</button>
      </form>
      {last ? <div className="hexline" style={{ marginTop: 10 }}><span className="lid">21 {last.lid}</span> {spacedHex(last.raw)}</div> : null}
      <input className="input" style={{ width: "100%", marginTop: 12 }} aria-label="Label for the reading"
        placeholder="what does this value mean? e.g. left height 149, right 162" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="row" style={{ marginTop: 10 }}>
        <span className="small muted grow pretty">Appends {"{module, lid, raw, text}"} to logs/labeled_captures.jsonl — the dataset the auto-mapper reads.</span>
        <button className="btn" onClick={save}>Save capture</button>
      </div>
    </div>
  );
}

export function Capture() {
  const { module, toast } = useApp();
  const logModule = storeModule(module);
  const { log, add } = useCaptureLog(logModule);
  const onSaved = (m: string, e: Omit<LogEntry, "t">) => {
    if (m === logModule) return add(e);
    // a sniff of another module: keep it in that module's log
    writeList(logKey(m), [{ ...e, t: new Date().toLocaleTimeString() }, ...readList<LogEntry>(logKey(m))].slice(0, 200));
    toast(`saved to the ${m} log`);
  };
  return (
    <>
      <ScreenHead title="Capture" />
      <SniffCapture onSaved={onSaved} />
      <DirectCapture onSaved={onSaved} />
      <section>
        <div className="kicker group-title">Saved on this device · {logModule} · {log.length}</div>
        {log.length ? (
          <div className="stack">
            {log.map((r, i) => (
              <div className="small" key={`${r.t}-${r.lid}-${i}`}>
                <span className="lid mono">21 {r.lid}</span> <span className="mono dis">{r.raw}</span> → {r.text} <span className="dis">{r.t}</span>
              </div>
            ))}
          </div>
        ) : <div className="small dis">None saved yet.</div>}
      </section>
    </>
  );
}
