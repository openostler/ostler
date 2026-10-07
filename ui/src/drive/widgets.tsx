// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The core Drive-mode widgets (drive-modes spec §9 "core widgets"), drawn through the
 * existing kit (Gauge, RangeBar, Sparkline, StatusChip, Icon) and the tokens. While Moving a
 * widget is its template (§4.3): calm tiles with ≥ 56 px digits and ≥ 24 px labels, no
 * sparkline, no animation; panes for the map, media and push to talk. A value is never
 * invented: a missing one says why in words (bind.ts).
 */
import { lazy, Suspense, useMemo } from "react";
import { Gauge } from "../components/Gauge";
import { RangeBar } from "../components/RangeBar";
import { Sparkline } from "../components/Sparkline";
import { StatusChip } from "../components/StatusChip";
import { Icon } from "../icons/Icon";
import { convertUnit, flagFor, fmt } from "../lib/format";
import type { Span } from "../lib/range";
import { useApp } from "../state/app";
import { compassPoint, levelOf, read, type BindContext, type Reading } from "./bind";
import type { Widget } from "./types";

const TraceMap = lazy(() => import("../components/replay/TraceMap").then((m) => ({ default: m.TraceMap })));

export type WidgetProps = { w: Widget; ctx: BindContext; moving: boolean };

/** VSS unit keys as people read them (units.yaml keys the presets use). */
const UNIT_WORDS: Record<string, string> = { Celsius: "°C", degrees: "°", percent: "%" };
const unitWord = (u: string) => UNIT_WORDS[u] ?? u;

/** The number and its unit as displayed (the user's units; `dec` from the widget). */
function useShown(r: Reading, w: Widget): { num: string; unit: string } {
  const { prefs } = useApp();
  const unit = unitWord(w.unit ?? r.unit);
  if (r.v === null) return { num: "–", unit };
  const c = convertUnit(r.v, unit, prefs.units);
  return { num: fmt(c.v, w.dec ?? r.tile?.dec), unit: c.unit };
}

/** Why there is no value: words, never a zero (ADR-0006). */
function Absent({ r }: { r: Reading }) {
  return (
    <div className="dm-absent">
      <span className="dm-why">{r.why}</span>
      {r.whyDetail ? <span className="dm-why-detail">{r.whyDetail}</span> : null}
    </div>
  );
}

function label(w: Widget, r: Reading): string {
  return w.label ?? r.tile?.label ?? r.field?.label ?? r.name ?? w.slot;
}

/** Tile, gauge and hero (styles number, bar, arc; sparkline Parked only). */
export function Readout({ w, ctx, moving }: WidgetProps) {
  const { live } = useApp();
  const r = read(w.bind, ctx);
  const shown = useShown(r, w);
  const name = label(w, r);
  const level = levelOf(r.v, w.levels);
  const server = flagFor(r.sig?.s, r.sig?.c ?? r.field?.c);
  // the widget's own levels (§4.2) add to the server's range status; colour always with a word
  const flag = server.cls === "ok" || server.cls === "exp"
    ? level === "critical" ? { cls: "hi" as const, txt: "HIGH" } : server
    : server;
  const alarm = flag.cls === "hi" || flag.cls === "lo";
  const warn = level === "warning" && !alarm;
  const hero = w.widget === "ostler.hero";
  const style = w.style ?? (r.tile?.gauge ? "arc" : "bar");
  const span = (w.range && w.range[0] !== null && w.range[1] !== null ? (w.range as Span) : null)
    ?? (r.field?.span && !r.conv ? (r.field.span as Span) : null);
  const normal = r.conv ? null : (r.field?.normal as Span | null | undefined) ?? null;
  const samples = useMemo(() => (r.name && !moving ? (live.history[r.name] ?? []) : []), [live.history, r.name, moving]);
  const cls = `tile dm-tile${hero ? " dm-hero" : ""}${alarm ? " alarm" : warn ? " warn" : ""}${r.state === "stale" ? " stale" : ""}`;
  return (
    <div className={cls} data-signal={r.name} data-style={style}>
      <div className="dm-top">
        <span className="dm-label" dir="auto">{name}</span>
        {r.source ? <span className="dm-source">{r.source}</span> : null}
        {r.state === "stale" ? <span className="dm-source">stale</span> : null}
        {r.state !== "absent" && style !== "arc" && shown.unit ? <span className="dm-unit dm-unit-top" aria-hidden="true">{shown.unit}</span> : null}
        {warn ? <span className="status sus"><span className="si" aria-hidden="true"><Icon name="warning" size="1.1em" /></span>HIGH</span>
          : <StatusChip flag={flag} compact />}
      </div>
      {r.state === "absent" ? <Absent r={r} /> : style === "arc" && span ? (
        <div className="gwrap2"><Gauge value={r.v} span={span} normal={normal} unit={unitWord(w.unit ?? r.unit)} dec={w.dec ?? r.tile?.dec} alarm={alarm} label={name} /></div>
      ) : (
        <>
          <div className={`dm-value${alarm ? " alarm" : ""}`}>
            <span className="dm-num">{shown.num}</span>
            {shown.unit ? <span className="dm-unit">{shown.unit}</span> : null}
          </div>
          {style === "bar" && span ? <RangeBar value={r.v} span={span} normal={normal} alarm={alarm} label={name} unit={shown.unit} /> : null}
          {!moving && r.name ? <Sparkline samples={samples} label={name} /> : null}
        </>
      )}
    </div>
  );
}

/** A two-state chip, or two of them as one tile (low range and diff lock, §5.5). */
export function ChipTile({ w, ctx }: WidgetProps) {
  const rows = [{ b: w.bind, l: w.label ?? "On" }, ...(w.bind2 ? [{ b: w.bind2, l: w.label2 ?? "On" }] : [])];
  return (
    <div className="tile dm-tile dm-chips">
      {rows.map(({ b, l }) => {
        const r = read(b, ctx);
        return (
          <div className="dm-chiprow" key={l}>
            <span className="dm-label" dir="auto">{l}</span>
            {/* one line each, so two states fit one tile; the word is the tile's title too */}
            {r.state === "absent" ? <span className="dm-why" title={r.whyDetail ? `${r.why}. ${r.whyDetail}` : r.why}>{r.why}</span>
              : <span className="dm-state">{r.v ? "On" : "Off"}</span>}
          </div>
        );
      })}
    </div>
  );
}

/** Pitch or roll: the number and a static silhouette turned by it, stepped (§5.5). */
export function Inclinometer({ w, ctx }: WidgetProps) {
  const r = read(w.bind, ctx);
  const name = w.label ?? "Tilt";
  const level = levelOf(r.v, w.levels);
  const rear = w.config?.view === "rear";
  return (
    <div className={`tile dm-tile dm-incline${level === "critical" ? " alarm" : ""}`}>
      <div className="dm-top"><span className="dm-label" dir="auto">{name}</span></div>
      {r.state === "absent" ? <Absent r={r} /> : (
        <div className="dm-incline-body">
          <svg viewBox="-50 -30 100 60" className="dm-silhouette" role="img" aria-label={`${name} ${fmt(r.v ?? 0, 0)} degrees`}>
            <g transform={`rotate(${Math.round(r.v ?? 0)})`}>
              {rear ? <path d="M-30 10 h60 v-22 h-12 l-6 -12 h-24 l-6 12 h-12 Z" /> : <path d="M-40 10 h80 v-18 h-22 l-8 -12 h-34 l-6 12 h-10 Z" />}
            </g>
          </svg>
          <div className="dm-value"><span className="dm-num">{fmt(r.v ?? 0, 0)}</span><span className="dm-unit">°</span></div>
        </div>
      )}
    </div>
  );
}

/** Heading from the GPS course: frozen below a crawl, so it says stale there (§5.5). */
export function Compass({ w, ctx }: WidgetProps) {
  const r = read(w.bind, ctx);
  const speed = ctx.snap?.gps?.speed_kmh ?? null;
  const crawling = r.source === "GPS" && speed !== null && speed < 3;
  return (
    <div className={`tile dm-tile${crawling ? " stale" : ""}`}>
      <div className="dm-top">
        <span className="dm-label" dir="auto">{w.label ?? "Heading"}</span>
        {r.source ? <span className="dm-source">{r.source}</span> : null}
        {crawling ? <span className="dm-source">stale</span> : null}
        {r.v !== null ? <span className="dm-unit dm-unit-top" aria-hidden="true">{compassPoint(r.v)}</span> : null}
      </div>
      {r.state === "absent" || r.v === null ? <Absent r={r} /> : (
        <div className="dm-value">
          <span className="dm-num">{`${fmt(r.v, 0)}°`}</span>
          <span className="dm-unit">{compassPoint(r.v)}</span>
        </div>
      )}
    </div>
  );
}

/** One status line, at most two values (the `value` template). */
export function StatusLine({ w, ctx }: WidgetProps) {
  const { prefs } = useApp();
  const parts = (w.values ?? []).map((v) => {
    const r = read(v.bind, ctx);
    if (r.v === null) return `${v.label ?? ""} ${r.why ?? "–"}`.trim();
    const c = convertUnit(r.v, unitWord(r.unit), prefs.units);
    return `${v.label ?? ""} ${fmt(c.v, v.dec)} ${c.unit}`.trim();
  });
  return (
    <div className="tile dm-tile dm-line">
      <span className="dm-line-text" dir="auto">{parts.join(" · ")}</span>
    </div>
  );
}

/** The map pane: own position only while Moving (UI spec §12.1 `map`). */
export function MapPane({ ctx }: WidgetProps) {
  const fix = ctx.snap?.gps;
  const on = !!fix?.fix;
  const lat = fix?.lat ?? null;
  const lon = fix?.lon ?? null;
  const heading = fix?.heading ?? null;
  const cursor = useMemo(() => (on && lat !== null && lon !== null ? { lat, lon, heading } : null), [on, lat, lon, heading]);
  return (
    <div className="dm-pane dm-map" data-pane="map">
      <Suspense fallback={<div className="dm-absent"><span className="dm-why">Loading the map</span></div>}>
        <TraceMap a={null} b={null} bbox={null} cursor={cursor} drive label="Drive map" />
      </Suspense>
      {cursor ? null : <div className="dm-map-note"><span className="dm-why">{fix ? "No GPS fix" : "Needs GPS"}</span></div>}
    </div>
  );
}

/** A pane whose data comes from an add-on that is not there yet (media, push to talk). */
export function NeedsPane({ w }: WidgetProps) {
  const what = w.widget === "ostler.media" ? { icon: "music_note" as const, text: "Needs a media add-on" }
    : { icon: "groups" as const, text: "Needs the Social add-on" };
  return (
    <div className="dm-pane dm-needs" data-pane={w.widget === "ostler.media" ? "media" : "call"}>
      <Icon name={what.icon} size={40} />
      <span className="dm-why">{what.text}</span>
    </div>
  );
}

/** An unknown or add-on widget: an empty cell while Moving (R2), a placeholder Parked. */
export function Unknown({ w, moving }: WidgetProps) {
  return moving ? <div className="tile dm-tile dm-empty" aria-label={`${w.label ?? w.slot}: needs an add-on`} role="img" />
    : <div className="tile dm-tile"><div className="dm-top"><span className="dm-label" dir="auto">{w.label ?? w.slot}</span></div>
      <div className="dm-absent"><span className="dm-why">Needs an add-on</span></div></div>;
}

export function DriveWidget(p: WidgetProps) {
  switch (p.w.widget) {
    case "ostler.tile": case "ostler.gauge": case "ostler.hero": case "ostler.sparkline": return <Readout {...p} />;
    case "ostler.chip": return <ChipTile {...p} />;
    case "ostler.inclinometer": return <Inclinometer {...p} />;
    case "ostler.compass": return <Compass {...p} />;
    case "ostler.status_line": return <StatusLine {...p} />;
    case "ostler.map": return <MapPane {...p} />;
    case "ostler.media": case "ostler.ptt": return <NeedsPane {...p} />;
    default: return <Unknown {...p} />;
  }
}
