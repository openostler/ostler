/**
 * One session's replay page in Logs, over the app-root replay (ADR-0010, spec §4–5): the map
 * with traces A and B, the G-G panel, readouts at the cursor, the chart strip with notes and
 * the notes panel. The cursor and playing state come from `useReplay()`; the transport is the
 * global one <App> shows on every tab.
 */
import { useMemo, useState } from "react";
import { api, command } from "../../api/client";
import type { SessionData, SessionMeta } from "../../api/schemas";
import { useApp } from "../../state/app";
import { valueAt } from "../../state/playback";
import { useReplay } from "../../state/replay";
import { confirmReady } from "../confirm";
import { Chart, type Lane } from "./Chart";
import { ChannelPicker } from "./ChannelPicker";
import { pickerChannels } from "./channels";
import { GGPanel } from "./GGPanel";
import { channelLabel, channelUnits, showValue } from "./labels";
import { TraceLegend, type LegendTrace } from "./Legend";
import { NotesPanel, type NoteRequest } from "./NotesPanel";
import { formatDuration, startTime } from "./sessionFormat";
import {
  bboxOf, cursorAt, defaultTraceChannel, laneRamp, lineColorExpression, plottable, rangeOf, simplifyTrack, traceSegments,
  type TraceLane,
} from "./trace";
import { TraceMap, type MapTrace } from "./TraceMap";

const MAX_LANES = 3;
const CLASSIC_KEY = "d2diag.classicRamp";

function loadClassic(): boolean {
  try { return window.localStorage.getItem(CLASSIC_KEY) === "1"; } catch { return false; }
}
function saveClassic(on: boolean) {
  try { window.localStorage.setItem(CLASSIC_KEY, on ? "1" : "0"); } catch { /* not remembered */ }
}

/** Which slot the channel picker is filling. */
type PickFor = { kind: "trace"; lane: TraceLane } | { kind: "lane"; index: number } | null;

export function Replay({ onDeleted }: { onDeleted: () => void }) {
  const r = useReplay();
  const back = <button className="rchip replay-back" onClick={r.exit}>‹ Sessions</button>;
  if (!r.session || !r.data) {
    return (
      <div className="stack">
        {back}
        <p className={r.error ? "muted" : "muted small"}>{r.error ? `Could not load this session: ${r.error}` : "Loading session…"}</p>
      </div>
    );
  }
  return <ReplayView key={r.session.id} meta={r.session} data={r.data} onDeleted={onDeleted} />;
}

function ReplayView({ meta, data, onDeleted }: { meta: SessionMeta; data: SessionData; onDeleted: () => void }) {
  const { fields, prefs, snap } = useApp();
  const replay = useReplay();
  const time = replay.t;
  const names = useMemo(() => plottable(meta).filter((n) => data.ch[n]), [meta, data]);
  const channels = useMemo(() => pickerChannels(meta, names, fields), [meta, names, fields]);

  // ---- traces ----
  const [traceA, setTraceA] = useState<string | null>(null);
  const [traceB, setTraceB] = useState<string | null>(null);
  const [classic, setClassicState] = useState(loadClassic);
  const setClassic = (on: boolean) => { setClassicState(on); saveClassic(on); };
  const a = traceA && names.includes(traceA) ? traceA : defaultTraceChannel(names);
  const b = traceB && names.includes(traceB) ? traceB : null;
  const smooth = useMemo(() => ({ t: data.t, ch: data.ch, track: simplifyTrack(data.track) }), [data]);
  const rangeA = useMemo(() => (a ? rangeOf(data.ch[a]) : null), [data, a]);
  const rangeB = useMemo(() => (b ? rangeOf(data.ch[b]) : null), [data, b]);
  const colorsA = laneRamp("a", classic);
  const colorsB = laneRamp("b", classic);
  const mapA = useMemo<MapTrace | null>(() => (a ? { fc: traceSegments(smooth, a, rangeA), colors: colorsA, color: lineColorExpression(colorsA) } : null), [smooth, a, rangeA, colorsA]);
  const mapB = useMemo<MapTrace | null>(() => (b ? { fc: traceSegments(smooth, b, rangeB), colors: colorsB, color: lineColorExpression(colorsB) } : null), [smooth, b, rangeB, colorsB]);
  const trackTimes = useMemo(() => data.track.map((p) => p[2]), [data]);
  const cursor = useMemo(() => cursorAt(data, time, trackTimes), [data, time, trackTimes]);
  const bbox = meta.bbox ?? bboxOf(data.track);

  // ---- chart lanes ----
  const [picked, setPicked] = useState<string[] | null>(null);
  const lanesNames = useMemo(() => {
    if (picked) return picked.filter((n) => names.includes(n));
    const first = defaultTraceChannel(names);
    const rest = names.filter((n) => n !== first && !n.startsWith("GPS_"));
    return [first, ...rest].filter((n): n is string => !!n).slice(0, MAX_LANES);
  }, [picked, names]);

  const [pickFor, setPickFor] = useState<PickFor>(null);
  const label = (n: string) => channelLabel(n, fields);
  const lanes: Lane[] = lanesNames.map((n) => ({ name: n, label: label(n), unit: showValue(0, channelUnits(meta, n), prefs.units).unit }));
  const readouts = [...lanesNames, ...(data.ch.GPS_Speed && !lanesNames.includes("GPS_Speed") ? ["GPS_Speed"] : [])];
  const date = new Date(meta.start_utc).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
  const start = data.t[0] ?? 0;
  const end = data.t[data.t.length - 1] ?? 0;
  const canNote = !meta.synthetic && !snap?.public;
  const speedCh = names.includes("speed") ? "speed" : names.includes("GPS_Speed") ? "GPS_Speed" : null;

  const legend: LegendTrace[] = [
    ...(a ? [{ lane: "a" as const, channel: a, label: label(a), range: rangeA, unit: channelUnits(meta, a), colors: colorsA }] : []),
    ...(b ? [{ lane: "b" as const, channel: b, label: label(b), range: rangeB, unit: channelUnits(meta, b), colors: colorsB }] : []),
  ];

  // The chart hands note work to the notes panel: a tapped marker opens its editor, a drag
  // with the note tool opens a new range note there.
  const [noteReq, setNoteReq] = useState<NoteRequest | null>(null);

  const picker = (() => {
    if (!pickFor) return null;
    const close = () => setPickFor(null);
    if (pickFor.kind === "trace") {
      const lane = pickFor.lane;
      return (
        <ChannelPicker title={`Trace ${lane.toUpperCase()} colour`} channels={channels} value={lane === "a" ? a : b} onClose={close}
          onPick={(n) => (lane === "a" ? setTraceA(n) : setTraceB(n))}
          onRemove={lane === "b" && b ? () => setTraceB(null) : undefined} removeLabel="Remove trace B" />
      );
    }
    const i = pickFor.index;
    const cur = lanesNames[i] ?? null;
    return (
      <ChannelPicker title={cur ? `Chart lane ${i + 1}` : "Add a chart lane"} channels={channels} value={cur} onClose={close}
        onPick={(n) => {
          // Replace this lane (a channel already in another lane swaps places with it).
          const next = [...lanesNames];
          const j = next.indexOf(n);
          if (cur) {
            next[i] = n;
            if (j >= 0 && j !== i) next[j] = cur;
          } else if (j < 0) next.push(n);
          setPicked(next.slice(0, MAX_LANES));
        }}
        onRemove={cur && lanesNames.length > 1 ? () => setPicked(lanesNames.filter((x) => x !== cur)) : undefined} removeLabel="Remove this lane" />
    );
  })();

  return (
    <div className="replay stack" data-session={meta.id}>
      <div className="replay-head">
        <button className="rchip replay-back" onClick={replay.exit}>‹ Sessions</button>
        <div className="replay-title">
          <h2>{date} · {startTime(meta)}</h2>
          <span className="muted small">
            {formatDuration(meta.duration_s)}
            {meta.synthetic ? <span className="replay-chip-demo">demo</span> : null}
            {meta.recording ? <span className="replay-chip-live">recording</span> : null}
            {data.decimated ? <span title="Long session: each point keeps the min and max of its span"> · overview</span> : null}
          </span>
        </div>
        <SessionActions meta={meta} canDelete={!meta.synthetic && !snap?.public} onDeleted={onDeleted} />
      </div>

      {meta.has_gps || data.track.length ? (
        <div className="card replay-mapcard">
          <TraceMap a={mapA} b={mapB} bbox={bbox} cursor={cursor} />
          {legend.length ? (
            <TraceLegend traces={legend} units={prefs.units} onEdit={(lane) => setPickFor({ kind: "trace", lane })}
              onAddB={b ? undefined : () => setPickFor({ kind: "trace", lane: "b" })} classic={classic} onClassic={setClassic} />
          ) : null}
        </div>
      ) : <p className="card muted small">No GPS in this session — chart only.</p>}

      <GGPanel data={data} names={names} speed={speedCh} t={time} />

      <div className="replay-readouts" role="group" aria-label="Values at the cursor">
        {readouts.map((n) => {
          const v = showValue(valueAt(data.t, data.ch[n], time), channelUnits(meta, n), prefs.units);
          return (
            <div key={n} className="replay-readout" data-channel={n}>
              <span className="replay-readout-label small">{label(n)}</span>
              <span className="replay-readout-value"><b>{v.text}</b>{v.unit ? <span className="u"> {v.unit}</span> : null}</span>
            </div>
          );
        })}
      </div>

      <div className="replay-lanes" role="group" aria-label="Chart channels">
        {lanesNames.map((n, i) => (
          <button key={n} type="button" className="rchip" data-channel={n} aria-label={`Chart lane ${i + 1}: ${label(n)} — change channel`}
            onClick={() => setPickFor({ kind: "lane", index: i })}>
            <span className="replay-swatch" style={{ background: `var(--series-${i + 1})` }} aria-hidden="true" />{label(n)} <span aria-hidden="true">▾</span>
          </button>
        ))}
        {lanesNames.length < MAX_LANES && names.length > lanesNames.length ? (
          <button type="button" className="rchip" onClick={() => setPickFor({ kind: "lane", index: lanesNames.length })}>+ Add lane</button>
        ) : null}
      </div>
      <Chart t={data.t} ch={data.ch} lanes={lanes} time={time} start={start} end={end} offset={replay.offset} onSeek={replay.seek}
        notes={replay.notes} onAddRange={canNote ? (t0, t1) => setNoteReq({ t: t0, t_end: t1 }) : undefined} onNoteTap={(n) => setNoteReq({ id: n.id })} />

      <NotesPanel request={noteReq} onRequestDone={() => setNoteReq(null)} />
      {picker}
    </div>
  );
}

function SessionActions({ meta, canDelete, onDeleted }: { meta: SessionMeta; canDelete: boolean; onDeleted: () => void }) {
  const { toast } = useApp();
  const [confirming, setConfirming] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const ready = confirmReady("typed", { ticked: [], typed, name: meta.id });

  const del = async () => {
    setBusy(true);
    try {
      const r = await command("delete_session", { id: meta.id });
      if (r.ok) {
        toast("session deleted");
        onDeleted();
      } else toast(String(r.error ?? "could not delete the session"), true);
    } catch (e) {
      toast((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="replay-actions">
      <details className="replay-menu">
        <summary className="rchip">Export</summary>
        <div className="replay-menu-body card">
          {(["csv", "vbo", "gpx"] as const).map((f) => (
            <a key={f} className="btn block" href={api.sessionExportUrl(meta.id, f)} download>{f.toUpperCase()}</a>
          ))}
        </div>
      </details>
      {canDelete && !confirming ? <button className="rchip replay-delete" onClick={() => setConfirming(true)}>Delete</button> : null}
      {canDelete && confirming ? (
        <div className="confirm card replay-confirm" role="group" aria-label="Confirm delete session">
          <label className="stack small" style={{ gap: 6 }}>
            <span>Deleting removes this session from the device. Type <b className="mono">{meta.id}</b> to confirm.</span>
            <input className="input mono" value={typed} aria-label={`Type ${meta.id} to confirm`} onChange={(e) => setTyped(e.target.value)} />
          </label>
          <div className="btn-row" style={{ marginTop: 10 }}>
            <button className="btn" onClick={() => { setConfirming(false); setTyped(""); }}>Cancel</button>
            <button className="btn danger" disabled={!ready || busy} onClick={() => void del()}>Delete session</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
