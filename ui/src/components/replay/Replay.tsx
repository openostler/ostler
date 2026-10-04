/**
 * One session's replay: map with a channel-coloured trace, chart strip, readouts at the
 * cursor and the transport bar, all driven by one PlaybackCtx (specs/2026-10-05-session-logbook-design.md).
 */
import { useMemo, useState } from "react";
import { api, command } from "../../api/client";
import type { SessionData, SessionMeta } from "../../api/schemas";
import { useSessionReplay } from "../../api/useSessions";
import { useApp } from "../../state/app";
import { PlaybackCtx, usePlaybackState, utcOffset, valueAt } from "../../state/playback";
import { confirmReady } from "../confirm";
import { Chart, type Lane } from "./Chart";
import { channelLabel, channelUnits, showValue } from "./labels";
import { TraceLegend } from "./Legend";
import { formatDuration, startTime } from "./sessionFormat";
import { bboxOf, cursorAt, defaultTraceChannel, lineColorExpression, plottable, rangeOf, traceSegments } from "./trace";
import { TraceMap } from "./TraceMap";
import { Transport } from "./Transport";

const MAX_LANES = 3;
/** GPS housekeeping channels: offered for the trace, not picked for the chart by default. */
const GPS_AUX = new Set(["GPS_Heading", "GPS_Nsat", "GPS_HDOP", "GPS_Altitude"]);
const COLOR = lineColorExpression();

export function Replay({ id, onBack, onDeleted }: { id: string; onBack: () => void; onDeleted: () => void }) {
  const { meta, data, error } = useSessionReplay(id);
  if (!meta || !data) {
    return (
      <div className="stack">
        <button className="rchip replay-back" onClick={onBack}>‹ Sessions</button>
        <p className={error ? "muted" : "muted small"}>{error ? `Could not load this session: ${error}` : "Loading session…"}</p>
      </div>
    );
  }
  return <ReplayView key={id} meta={meta} data={data} onBack={onBack} onDeleted={onDeleted} />;
}

function ReplayView({ meta, data, onBack, onDeleted }: { meta: SessionMeta; data: SessionData; onBack: () => void; onDeleted: () => void }) {
  const { fields, prefs, snap } = useApp();
  const names = useMemo(() => plottable(meta).filter((n) => data.ch[n]), [meta, data]);
  const [traceCh, setTraceCh] = useState<string | null>(null);
  const trace = traceCh && names.includes(traceCh) ? traceCh : defaultTraceChannel(names);
  const [picked, setPicked] = useState<string[] | null>(null);
  const lanesNames = useMemo(() => {
    if (picked) return picked.filter((n) => names.includes(n));
    const first = defaultTraceChannel(names);
    const rest = names.filter((n) => n !== first && !n.startsWith("GPS_"));
    return [first, ...rest].filter((n): n is string => !!n).slice(0, MAX_LANES);
  }, [picked, names]);
  const [follow, setFollow] = useState(meta.recording);
  const live = meta.recording && follow;

  const pb = usePlaybackState(data.t, { pinToEnd: live, onUserMove: () => setFollow(false) });
  const offset = useMemo(() => utcOffset(data.t, data.utc), [data]);

  const range = useMemo(() => (trace ? rangeOf(data.ch[trace]) : null), [data, trace]);
  const segments = useMemo(() => (trace ? traceSegments(data, trace, range) : { type: "FeatureCollection" as const, features: [] }), [data, trace, range]);
  const trackTimes = useMemo(() => data.track.map((p) => p[2]), [data]);
  const cursor = useMemo(() => cursorAt(data, pb.time, trackTimes), [data, pb.time, trackTimes]);
  const bbox = meta.bbox ?? bboxOf(data.track);

  const label = (n: string) => channelLabel(n, fields);
  const lanes: Lane[] = lanesNames.map((n) => ({ name: n, label: label(n), unit: showValue(0, channelUnits(meta, n), prefs.units).unit }));
  const readouts = [...lanesNames, ...(data.ch.GPS_Speed && !lanesNames.includes("GPS_Speed") ? ["GPS_Speed"] : [])];
  const date = new Date(meta.start_utc).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });

  return (
    <PlaybackCtx.Provider value={pb}>
      <div className="replay stack" data-session={meta.id}>
        <div className="replay-head">
          <button className="rchip replay-back" onClick={onBack}>‹ Sessions</button>
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
            <TraceMap trace={segments} color={COLOR} bbox={bbox} cursor={cursor} />
            {trace ? (
              <TraceLegend channels={names.map((n) => ({ name: n, label: label(n) }))} channel={trace} onChannel={setTraceCh}
                label={label} range={range} unit={channelUnits(meta, trace)} units={prefs.units} />
            ) : null}
          </div>
        ) : <p className="card muted small">No GPS in this session — chart only.</p>}

        <div className="replay-readouts" role="group" aria-label="Values at the cursor">
          {readouts.map((n) => {
            const v = showValue(valueAt(data.t, data.ch[n], pb.time), channelUnits(meta, n), prefs.units);
            return (
              <div key={n} className="replay-readout" data-channel={n}>
                <span className="replay-readout-label small">{label(n)}</span>
                <span className="replay-readout-value"><b>{v.text}</b>{v.unit ? <span className="u"> {v.unit}</span> : null}</span>
              </div>
            );
          })}
        </div>

        <LanePicker names={names} label={label} lanes={lanesNames} onChange={setPicked} />
        <Chart t={data.t} ch={data.ch} lanes={lanes} time={pb.time} start={pb.start} end={pb.end} offset={offset} onSeek={pb.seek} />

        <Transport offset={offset} follow={live} onFollow={meta.recording ? setFollow : undefined} />
      </div>
    </PlaybackCtx.Provider>
  );
}

function LanePicker({ names, label, lanes, onChange }: { names: string[]; label: (n: string) => string; lanes: string[]; onChange: (l: string[]) => void }) {
  const others = names.filter((n) => !GPS_AUX.has(n) || lanes.includes(n));
  return (
    <details className="replay-menu replay-lanes">
      <summary className="rchip">Chart channels ({lanes.length}/{MAX_LANES})</summary>
      <div className="replay-menu-body card">
        {[...others, ...names.filter((n) => !others.includes(n))].map((n) => {
          const on = lanes.includes(n);
          return (
            <label key={n} className="row check">
              <input type="checkbox" checked={on} disabled={!on && lanes.length >= MAX_LANES}
                onChange={() => onChange(on ? lanes.filter((x) => x !== n) : [...lanes, n])} />
              <span>{label(n)}</span>
            </label>
          );
        })}
      </div>
    </details>
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
