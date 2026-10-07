// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The analysis body (spec §7): the map with traces A and B and their legend, the G-G panel,
 * readouts at the cursor, the chart strip and, in replay, the notes panel. The Analysis tab
 * drives it either from the global replay (`useReplay()`: cursor, seek, notes) or live from
 * the session being recorded (cursor pinned to the newest sample, marker and readouts from
 * the live snapshot, no notes, no seeking).
 */
import { useMemo, useState } from "react";
import type { SessionData, SessionMeta, SignalValue } from "../../api/schemas";
import { convertUnit } from "../../lib/format";
import { useApp } from "../../state/app";
import { utcOffset, valueAt } from "../../state/playback";
import { useReplay } from "../../state/replay";
import { useTheme } from "../../state/theme";
import { Chart, type Lane } from "./Chart";
import { ChannelPicker } from "./ChannelPicker";
import { pickerChannels } from "./channels";
import { GGPanel } from "./GGPanel";
import { channelLabel, channelUnits, showValue } from "./labels";
import { TraceLegend, type LegendTrace } from "./Legend";
import { NotesPanel, type NoteRequest } from "./NotesPanel";
import {
  bboxOf, cursorAt, defaultTraceChannel, laneRamp, lineColorExpression, plottable, rangeOf, simplifyTrack, speedBand, speedBandLabels,
  speedColors, trackOf, traceSegments, type BBox, type Cursor, type SpeedUnit, type TraceLane,
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

/** Live overrides: the map marker (from `snap.gps`, between fetches) and the readouts (from
 * `snap.signals`; a channel the snapshot lacks falls back to the newest fetched sample). */
export type LiveOverride = {
  cursor: Cursor | null;
  signals: Record<string, SignalValue>;
  /** GPS speed from the live fix (GPS_Speed is not a snapshot signal). */
  gpsSpeed?: number | null;
};

const noop = () => undefined;

export function AnalysisView({ data, meta, cursorT, onSeek, live }: {
  data: SessionData;
  meta: SessionMeta;
  /** The cursor in session ms (live: the newest sample). */
  cursorT: number;
  onSeek?: (ms: number) => void;
  /** Present in live mode. */
  live?: LiveOverride;
}) {
  const { fields, prefs, snap } = useApp();
  const replay = useReplay();
  const time = cursorT;
  const names = useMemo(() => plottable(meta).filter((n) => data.ch[n]), [meta, data]);
  const channels = useMemo(() => pickerChannels(meta, names, fields), [meta, names, fields]);

  // ---- traces ----
  const [traceA, setTraceA] = useState<string | null>(null);
  const [traceB, setTraceB] = useState<string | null>(null);
  const [classic, setClassicState] = useState(loadClassic);
  const setClassic = (on: boolean) => { setClassicState(on); saveClassic(on); };
  const a = traceA && names.includes(traceA) ? traceA : defaultTraceChannel(names);
  const b = traceB && names.includes(traceB) ? traceB : null;
  // the GPS track, from the GeoJSON trace (positions + their session ms)
  const track = useMemo(() => trackOf(data.trace), [data]);
  const smooth = useMemo(() => ({ t: data.t, ch: data.ch, track: simplifyTrack(track) }), [data, track]);
  const rangeA = useMemo(() => (a ? rangeOf(data.ch[a]) : null), [data, a]);
  const rangeB = useMemo(() => (b ? rangeOf(data.ch[b]) : null), [data, b]);
  // Speed always wears the violet speed ramp in absolute bands (visual spec §3.3); other
  // channels the lane's plasma/mako (or classic) ramp over their own range.
  const theme = useTheme();
  const units = prefs.units;
  const speedUnit = (ch: string | null): SpeedUnit | null => {
    const u = ch ? convertUnit(0, channelUnits(meta, ch), units).unit : "";
    return u === "km/h" || u === "mph" ? u : null;
  };
  const suA = speedUnit(a);
  const suB = speedUnit(b);
  // eslint-disable-next-line react-hooks/exhaustive-deps -- the tokens change with the theme
  const speedRamp = useMemo(() => speedColors(), [theme]);
  const colorsA = suA ? speedRamp : laneRamp("a", classic);
  const colorsB = suB ? speedRamp : laneRamp("b", classic);
  const mapA = useMemo<MapTrace | null>(() => {
    if (!a) return null;
    const unit = channelUnits(meta, a);
    const bands = suA ? (v: number | null) => speedBand(v == null ? null : convertUnit(v, unit, units).v, suA) : undefined;
    return { fc: traceSegments(smooth, a, rangeA, bands), colors: colorsA, color: lineColorExpression(colorsA) };
  }, [smooth, a, rangeA, colorsA, suA, meta, units]);
  const mapB = useMemo<MapTrace | null>(() => {
    if (!b) return null;
    const unit = channelUnits(meta, b);
    const bands = suB ? (v: number | null) => speedBand(v == null ? null : convertUnit(v, unit, units).v, suB) : undefined;
    return { fc: traceSegments(smooth, b, rangeB, bands), colors: colorsB, color: lineColorExpression(colorsB) };
  }, [smooth, b, rangeB, colorsB, suB, meta, units]);
  const trackTimes = useMemo(() => track.map((p) => p[2]), [track]);
  const atCursor = useMemo(() => cursorAt({ t: data.t, ch: data.ch, track }, time, trackTimes), [data, track, time, trackTimes]);
  const cursor = live?.cursor ?? atCursor;
  // Live: the map is framed once (a growing bbox would rebuild it every fetch); the marker
  // then follows the car.
  const fresh = meta.bbox ?? bboxOf(track);
  const [firstBox, setFirstBox] = useState<BBox | null>(fresh);
  if (!firstBox && fresh) setFirstBox(fresh);
  const bbox = live ? firstBox : fresh;

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
  // a speed lane is drawn in speed-4, the speed ramp's line colour (visual spec §8, area line)
  const toneOf = (n: string, i: number) => (speedUnit(n) ? "speed-4" : `series-${i + 1}`);
  const lanes: Lane[] = lanesNames.map((n, i) => ({ name: n, label: label(n), unit: showValue(0, channelUnits(meta, n), prefs.units).unit, tone: toneOf(n, i) }));
  const readouts = [...lanesNames, ...(data.ch.GPS_Speed && !lanesNames.includes("GPS_Speed") ? ["GPS_Speed"] : [])];
  const start = data.t[0] ?? 0;
  const end = data.t[data.t.length - 1] ?? 0;
  const offset = useMemo(() => utcOffset(data), [data]);
  const canNote = !live && !meta.synthetic && !snap?.public;
  const speedCh = names.includes("speed") ? "speed" : names.includes("GPS_Speed") ? "GPS_Speed" : null;
  const valueOf = (n: string): number | null => {
    if (live) {
      const s = live.signals[n];
      if (s && s.v != null) return s.v;
      if (n === "GPS_Speed" && live.gpsSpeed != null) return live.gpsSpeed;
    }
    return valueAt(data.t, data.ch[n], time);
  };

  const legend: LegendTrace[] = [
    ...(a ? [{ lane: "a" as const, channel: a, label: label(a), range: rangeA, unit: channelUnits(meta, a), colors: colorsA,
      bands: suA ? speedBandLabels(suA) : undefined, bandUnit: suA ?? undefined }] : []),
    ...(b ? [{ lane: "b" as const, channel: b, label: label(b), range: rangeB, unit: channelUnits(meta, b), colors: colorsB,
      bands: suB ? speedBandLabels(suB) : undefined, bandUnit: suB ?? undefined }] : []),
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
    <div className="analysis-view stack" data-live={live ? "true" : undefined}>
      {meta.has_gps || track.length || live?.cursor ? (
        <div className="card replay-mapcard">
          <TraceMap a={mapA} b={mapB} bbox={bbox} cursor={cursor} />
          {legend.length ? (
            <TraceLegend traces={legend} units={prefs.units} onEdit={(lane) => setPickFor({ kind: "trace", lane })}
              onAddB={b ? undefined : () => setPickFor({ kind: "trace", lane: "b" })} classic={classic} onClassic={setClassic} />
          ) : null}
        </div>
      ) : <p className="card muted small">No GPS in this session — chart only.</p>}

      <GGPanel data={data} names={names} speed={speedCh} t={time} />

      <div className="replay-readouts" role="group" aria-label={live ? "Live values" : "Values at the cursor"}>
        {readouts.map((n) => {
          const v = showValue(valueOf(n), channelUnits(meta, n), prefs.units);
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
            <span className="replay-swatch" style={{ background: `var(--${toneOf(n, i)})` }} aria-hidden="true" />{label(n)} <span aria-hidden="true">▾</span>
          </button>
        ))}
        {lanesNames.length < MAX_LANES && names.length > lanesNames.length ? (
          <button type="button" className="rchip" onClick={() => setPickFor({ kind: "lane", index: lanesNames.length })}>+ Add lane</button>
        ) : null}
      </div>
      <Chart t={data.t} ch={data.ch} lanes={lanes} time={time} start={start} end={end} offset={offset} onSeek={onSeek ?? noop}
        notes={live ? [] : replay.notes} onAddRange={canNote ? (t0, t1) => setNoteReq({ t: t0, t_end: t1 }) : undefined}
        onNoteTap={live ? undefined : (n) => setNoteReq({ id: n.id })} />

      {live ? null : <NotesPanel request={noteReq} onRequestDone={() => setNoteReq(null)} />}
      {picker}
    </div>
  );
}
