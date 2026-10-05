import "../admin.css";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, command } from "../api/client";
import type { SniffLid } from "../api/schemas";
import { useSniff } from "../api/useSniff";
import { SniffBadge } from "../components/SniffBadge";
import { StepHeader } from "../components/StepHeader";
import { canonicalModule, moduleName } from "../layout";
import { normHex, normLid, type LabelCapture } from "../lib/mapping";
import { useApp } from "../state/app";
import { readList, writeList } from "../state/prefs";

type LogEntry = { lid: string; raw: string; text: string; t: string };
type Label = { module: string; lid: string; raw: string; text: string };
// Legacy key ("fångst" = capture): kept so logs saved by the old pages survive.
const logKey = (module: string) => `fangstlog:${module}`;

/** One record shape for every label, sniffed or read directly: lowercase LID, spaced hex. */
const labelRecord = (module: string, lid: string, raw: string, text: string): Label =>
  ({ module, lid: normLid(lid), raw: normHex(raw), text: text.trim() });

/** Save a label: POST /capture (logs/labeled_captures.jsonl, what Decode's solver reads)
 * and a live session note of kind "capture". The note is best effort — its errors are
 * ignored and never stop the capture. */
async function saveLabel(rec: Label) {
  const note = api.liveNote({
    kind: "capture", text: `${rec.lid}: ${rec.text}`,
    capture: { module: rec.module, lid: rec.lid, raw: rec.raw, value: rec.text },
  }).catch(() => null);
  try {
    return await api.capture(rec);
  } finally {
    await note;
  }
}

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

/** Server copy of the labels (GET /captures) — the ones the Decode tab's solver uses. */
function useServerLabels(module: string) {
  const [state, setState] = useState<{ module: string; list: LabelCapture[] | null; error: string | null }>(
    { module, list: null, error: null });
  const [rev, setRev] = useState(0);
  useEffect(() => {
    let alive = true;
    api.captures(module).then(
      (r) => alive && setState({ module, list: r.captures, error: null }),
      (e: Error) => alive && setState({ module, list: [], error: e.message }),
    );
    return () => { alive = false; };
  }, [module, rev]);
  const reload = useCallback(() => setRev((r) => r + 1), []);
  const current = state.module === module ? state : { module, list: null, error: null };
  return { ...current, reload };
}

const decodeText = (l?: SniffLid) =>
  l?.decode?.length ? l.decode.map((d) => `${d.name}=${d.value}${d.unit ?? ""}`).join(", ") : "not decoded yet";

type Phase = "idle" | "armed" | "done" | "timeout";
type OnSaved = (module: string, e: Omit<LogEntry, "t">) => void;

/** Batch labelling from the sniff: arm, make the NanoCom read a screen, then label every
 * block it asked for. */
function SniffCapture({ onSaved }: { onSaved: OnSaved }) {
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
    const module = canonicalModule(sniff.data?.module ?? "?");
    let n = 0;
    for (const lid of Object.keys(batch)) {
      const text = (texts[lid] ?? "").trim();
      if (!text) continue;
      const rec = labelRecord(module, lid, byLid[lid]?.raw ?? "", text);
      try { await saveLabel(rec); } catch { /* still kept on this device */ }
      onSaved(module, rec);
      n++;
    }
    reset();
    toast(n ? `${n} label${n === 1 ? "" : "s"} saved` : "Nothing saved — type what the NanoCom showed first", !n);
  };

  const status = {
    idle: "Press “New capture”, then open a live-data screen on the NanoCom.",
    armed: `Listening… make the NanoCom read a screen now (${left}s)`,
    done: `The NanoCom read ${Object.keys(batch).length} block(s) — type what it showed for each, then save.`,
    timeout: "Nothing heard — check the NanoCom is on a live-data screen, then try again.",
  }[phase];

  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 8 }}>Label what the NanoCom reads</div>
      <p className="help pretty">
        With the sniff tap on the K-line, every block the NanoCom asks for shows up here with its raw bytes.
        Type what the NanoCom displayed for each block — values in the order it shows them.
      </p>
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
              <div className="row"><b className="lid">21 {normLid(lid)}</b><span className="small dis" style={{ marginLeft: "auto" }}>read ×{count}</span></div>
              <div className="mono small" style={{ wordBreak: "break-all" }}>{normHex(byLid[lid]?.raw ?? "")}</div>
              <div className="small muted">our decode: {decodeText(byLid[lid])}</div>
              <input className="input" style={{ width: "100%", marginTop: 6 }} aria-label={`What the NanoCom shows for 21 ${normLid(lid)}`}
                placeholder="what the NanoCom shows, e.g. 762 rpm"
                value={texts[lid] ?? ""} onChange={(e) => setTexts((t) => ({ ...t, [lid]: e.target.value }))} />
            </div>
          ))}
          <button className="btn accent" onClick={save}>Save batch</button>
        </div>
      ) : null}
    </div>
  );
}

/** Direct read: ask the connected module for one block (read-only) and label it. */
function DirectCapture({ onSaved }: { onSaved: OnSaved }) {
  const { snap, module, toast } = useApp();
  const [lid, setLid] = useState("");
  const [last, setLast] = useState<{ lid: string; raw: string } | null>(null);
  const [text, setText] = useState("");
  const connected = snap?.status === "connected";

  const read = async () => {
    const id = normLid(lid);
    if (!id) return toast("Type a block number (LID) first, e.g. 23", true);
    toast(`Reading 21 ${id}…`);
    try {
      const r = await command("read_block", { lids: [id] });
      if (!r.ok) return toast(r.error ?? "The read failed", true);
      const raws = r.raws ?? {};
      const raw = raws[id] ?? raws[id.toUpperCase()];
      if (!raw) return toast(`The module did not answer 21 ${id}`, true);
      setLast({ lid: id, raw });
    } catch (e) {
      toast((e as Error).message, true);
    }
  };
  const save = async () => {
    if (!last) return toast("Read a block first", true);
    if (!text.trim()) return toast("Type what changed or what the value means", true);
    const rec = labelRecord(canonicalModule(module), last.lid, last.raw, text);
    try {
      const r = await saveLabel(rec);
      if (!r.ok) return toast(r.error ?? "Could not save", true);
      onSaved(rec.module, rec);
      setLast(null); setText("");
      toast(r.stored === false ? "Saved on this device (the server's capture store is off)" : "Saved");
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 8 }}>Read a LID directly · {moduleName(module)}</div>
      <p className="help pretty">
        No NanoCom needed: ask the connected module for one data block yourself. Type the block number
        (the LID, in hex) and <b>Read</b> sends <span className="mono">21 xx</span> — it only reads, never changes anything.
        Read once, change one thing on the car, read again: the bytes that changed hold that thing.
      </p>
      {!connected ? <div className="small" style={{ color: "var(--ic-yellow)", marginBottom: 8 }}>Connect {moduleName(module)} first (the connection pill in the header).</div> : null}
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); void read(); }}>
        <input className="input mono" style={{ width: 160 }} aria-label="LID to read" placeholder="LID in hex, e.g. 23"
          value={lid} onChange={(e) => setLid(e.target.value)} />
        <button className="btn accent" type="submit">Read</button>
      </form>
      {last ? <div className="hexline" style={{ marginTop: 10 }}><span className="lid">21 {last.lid}</span> {normHex(last.raw)}</div> : null}
      <input className="input" style={{ width: "100%", marginTop: 12 }} aria-label="Label for the reading"
        placeholder="what it means or what you changed, e.g. brake pressed" value={text} onChange={(e) => setText(e.target.value)} />
      <div className="row" style={{ marginTop: 10 }}>
        <span className="small muted grow pretty">Saved to the server for the Decode tab, and as a note on the current recording.</span>
        <button className="btn" onClick={save}>Save capture</button>
      </div>
    </div>
  );
}

/** Admin "Label": teach the decoder what bytes mean (sniffed or read directly). */
export function Capture() {
  const { module, toast } = useApp();
  const logModule = canonicalModule(module);
  const { log, add } = useCaptureLog(logModule);
  const server = useServerLabels(logModule);
  const onSaved = (m: string, e: Omit<LogEntry, "t">) => {
    server.reload();
    if (m === logModule) return add(e);
    // a sniff of another module: keep it in that module's log
    writeList(logKey(m), [{ ...e, t: new Date().toLocaleTimeString() }, ...readList<LogEntry>(logKey(m))].slice(0, 200));
    toast(`Saved to the ${m.toUpperCase()} list`);
  };
  return (
    <>
      <StepHeader title="Label" purpose="teach the decoder what bytes mean" steps={[
        <>Read a block — <span className="mono">21 xx</span> asks the module for data block <span className="mono">xx</span>.</>,
        <>Change one thing on the car (press the brake, open a door).</>,
        <>Read again and say what changed. The Decode tab uses these labels to work out the bytes.</>,
      ]} />
      <DirectCapture onSaved={onSaved} />
      <SniffCapture onSaved={onSaved} />
      <section>
        <div className="kicker group-title">Server labels · {logModule.toUpperCase()} · {server.list?.length ?? "…"}</div>
        <p className="help pretty">Every label saved from any device. These are what the Decode tab’s solver uses.</p>
        {server.list == null ? <div className="small dis">Loading…</div>
          : server.error ? <div className="small dis">Could not load the server labels ({server.error}).</div>
          : server.list.length ? (
            <div className="label-list" aria-label="Server labels">
              {server.list.map((c, i) => (
                <div className="item" key={`${c.lid}-${c.raw}-${i}`}>
                  <span className="lid mono">21 {normLid(c.lid)}</span> <span className="mono dis">{normHex(c.raw)}</span> → {c.value}
                </div>
              ))}
            </div>
          ) : <div className="small dis">No labels on the server yet.</div>}
      </section>
      <section>
        <div className="kicker group-title">Saved on this device · {logModule.toUpperCase()} · {log.length}</div>
        <p className="help pretty">
          A copy kept in this browser only, newest first, so you can see what you labelled even if the server
          did not get it. It is not shared and is not used by the solver.
        </p>
        {log.length ? (
          <div className="label-list">
            {log.map((r, i) => (
              <div className="item" key={`${r.t}-${r.lid}-${i}`}>
                <span className="lid mono">21 {r.lid}</span> <span className="mono dis">{r.raw}</span> → {r.text} <span className="dis">{r.t}</span>
              </div>
            ))}
          </div>
        ) : <div className="small dis">Nothing saved on this device yet.</div>}
      </section>
    </>
  );
}
