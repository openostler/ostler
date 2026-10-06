// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Pure helpers for whole-app replay (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md §4):
 * fold the events stream to the state at `t`, and synthesise the `snap` + `live` every screen
 * reads through `useApp()` from the recorded columns. No React, no fetch — unit-tested directly.
 */
import type { Field, GpsFix, Note, SessionChannel, SessionData, SessionEvent, SessionMeta, SignalValue, Snapshot } from "../api/schemas";
import { canonicalModule, defaultModule } from "../layout";
import { parseUtc, toUtc } from "../lib/time";
import { HISTORY_LEN, type LiveState, type Sample } from "./live";
import { indexAt } from "./playback";
import type { ReplayEventState } from "./replayTypes";

/** A point note's chip stays in the banner this long after the cursor passes it (ms). */
export const NOTE_SHOW_MS = 5000;
/** `live.seen` for a replayed value: never "stale" by wall clock (replay values are as recorded). */
export const REPLAY_SEEN = Number.MAX_SAFE_INTEGER;
/** Sparse rows: look back at most this many rows for a channel's last value. */
export const LOOKBACK_ROWS = 25;
/** Rows scanned back from the cursor to rebuild a channel's 60-sample history. */
export const HISTORY_SCAN_ROWS = 1500;

const TEXT = new Set(["module", "faults"]);
const ACCEL = new Set(["Acc_X", "Acc_Y", "Acc_Z", "InlineAcc", "LateralAcc", "VerticalAcc", "GPS_LonAcc", "GPS_LatAcc"]);

/** A recorded channel that is a module signal (not GPS, acceleration or a text column). */
export function isSignalChannel(c: Pick<SessionChannel, "name" | "group">): boolean {
  if (TEXT.has(c.name) || ACCEL.has(c.name) || c.name.startsWith("GPS_")) return false;
  return !["gps", "accel", "text"].includes(c.group ?? "");
}

export function initialEventState(): ReplayEventState {
  return { conn: null, status: null, module: null, active_test: null, fault_watch: false, logging: null, lastCommand: {} };
}

const str = (v: unknown): string | null => (typeof v === "string" ? v : null);

function activeTestOf(v: unknown): ReplayEventState["active_test"] {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  if (typeof o.action !== "string") return null;
  return {
    action: o.action,
    ...(typeof o.label === "string" ? { label: o.label } : {}),
    ...(typeof o.since === "number" ? { since: o.since } : {}),
    ...(typeof o.since_utc === "string" ? { since_utc: o.since_utc } : {}),
    ...(typeof o.stop === "string" ? { stop: o.stop } : {}),
  };
}

function loggingOf(v: unknown): ReplayEventState["logging"] {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  return { recording: !!o.recording, ...(typeof o.file === "string" ? { file: o.file } : {}) };
}

/** Apply one event to the state (returns a new state). Unknown types are ignored — including
 * `mode` events and a `state` line's `mode` from sessions recorded before ADR-0011. */
export function applyEvent(s: ReplayEventState, e: SessionEvent): ReplayEventState {
  const ev = e as Record<string, unknown>;
  switch (e.type) {
    case "state":
      return {
        ...s,
        conn: "conn" in ev ? str(ev.conn) : s.conn,
        status: "status" in ev ? str(ev.status) : s.status,
        module: "module" in ev ? str(ev.module) ?? s.module : s.module,
        active_test: "active_test" in ev ? activeTestOf(ev.active_test) : s.active_test,
        fault_watch: "fault_watch" in ev ? !!ev.fault_watch : s.fault_watch,
        logging: "logging" in ev ? loggingOf(ev.logging) : s.logging,
      };
    case "conn": return { ...s, conn: str(ev.conn) };
    case "status": return { ...s, status: str(ev.status) };
    case "module": return { ...s, module: str(ev.module) ?? s.module };
    case "active_test": return { ...s, active_test: activeTestOf(ev.active_test) };
    case "fault_watch": return { ...s, fault_watch: !!ev.on };
    case "logging": return { ...s, logging: loggingOf(ev) };
    case "command": {
      const action = str(ev.action);
      if (!action) return s;
      const rec = {
        t: e.t, ok: !!ev.ok,
        ...(typeof ev.message === "string" ? { message: ev.message } : {}),
        ...(typeof ev.error === "string" ? { error: ev.error } : {}),
      };
      return { ...s, lastCommand: { ...s.lastCommand, [action]: rec } };
    }
    default: return s;
  }
}

/** The event state at session time `t`: every event with `e.t <= t`, in time order. */
export function foldEvents(events: readonly SessionEvent[], t: number): ReplayEventState {
  const sorted = isSorted(events) ? events : [...events].sort((a, b) => a.t - b.t);
  let s = initialEventState();
  for (const e of sorted) {
    if (e.t > t) break;
    s = applyEvent(s, e);
  }
  return s;
}

function isSorted(events: readonly SessionEvent[]): boolean {
  for (let i = 1; i < events.length; i++) if (events[i]!.t < events[i - 1]!.t) return false;
  return true;
}

/** Range status as the server computes it (td5/identifiers.signal_status): suspect when out by
 * more than a whole span, else low / high / ok; null with no limits or no value. */
export function rangeStatus(v: number | null, limits: readonly [number, number] | null | undefined): string | null {
  if (v == null || !limits) return null;
  const [lo, hi] = limits;
  const span = hi - lo || 1;
  if (v < lo - span || v > hi + span) return "suspect";
  if (v < lo) return "low";
  if (v > hi) return "high";
  return "ok";
}

/** The `faults` text column ("a; b") back to the snapshot list. */
export function splitFaults(s: string | null | undefined): string[] {
  if (!s) return [];
  return s.split(";").map((f) => f.trim()).filter(Boolean);
}

/** Last non-null value of a column at or before row `i` (within `lookback` rows). */
export function valueAtIndex<T>(values: readonly (T | null)[] | undefined, i: number, lookback = LOOKBACK_ROWS): T | null {
  if (!values || i < 0) return null;
  for (let j = i; j >= 0 && j > i - lookback; j--) {
    const v = values[j];
    if (v != null) return v;
  }
  return null;
}

/** Text columns (module, faults), when the data route serves them (`data.text`). */
type WithText = SessionData & { text?: Record<string, (string | null)[]> };

/** Module signals at row `i`. When `fields` (the module's /fields) is non-empty, only its
 * signals are kept, so a channel from the module before a switch does not bleed through. */
export function signalsAt(meta: SessionMeta, data: SessionData, i: number, fields: Record<string, Field> = {}): Record<string, SignalValue> {
  const only = Object.keys(fields).length ? fields : null;
  const out: Record<string, SignalValue> = {};
  for (const c of meta.channels) {
    if (!isSignalChannel(c) || (only && !only[c.name])) continue;
    const col = data.ch[c.name];
    if (!col) continue;
    const v = valueAtIndex(col, i);
    if (v == null) continue;
    const f = fields[c.name];
    const sig: SignalValue = { v, u: c.units || f?.unit || "", s: rangeStatus(v, c.limits ?? f?.limits ?? null) };
    const conf = c.c ?? f?.c;
    if (conf) sig.c = conf;
    out[c.name] = sig;
  }
  return out;
}

/** The GPS fix at row `i` from the GPS channels (null when the session has none). */
export function gpsAt(data: SessionData, i: number): GpsFix | null {
  const ch = data.ch;
  if (!ch.GPS_Latitude && !ch.GPS_Longitude && !ch.GPS_Speed) return null;
  const lat = valueAtIndex(ch.GPS_Latitude, i);
  const lon = valueAtIndex(ch.GPS_Longitude, i);
  return {
    fix: lat != null && lon != null, lat, lon,
    speed_kmh: valueAtIndex(ch.GPS_Speed, i), heading: valueAtIndex(ch.GPS_Heading, i),
    sats: valueAtIndex(ch.GPS_Nsat, i), hdop: valueAtIndex(ch.GPS_HDOP, i), src: "replay", age_s: null,
  };
}

/** Up to HISTORY_LEN samples per channel at or before row `i` (t = session ms), oldest first. */
export function historyAt(data: SessionData, i: number, names: readonly string[]): Record<string, Sample[]> {
  const out: Record<string, Sample[]> = {};
  for (const n of names) {
    const col = data.ch[n];
    if (!col) continue;
    const h: Sample[] = [];
    for (let j = i; j >= 0 && j > i - HISTORY_SCAN_ROWS && h.length < HISTORY_LEN; j--) {
      const v = col[j];
      if (v != null) h.push({ t: data.t[j]!, v });
    }
    out[n] = h.reverse();
  }
  return out;
}

/** The module in view at the event state (the recorded one), else the session's first,
 * else the pack's default — canonical (a legacy alias in an old log reads as the pack's id). */
export function moduleOf(state: ReplayEventState, meta?: SessionMeta, fallback = defaultModule()): string {
  return canonicalModule(state.module ?? meta?.modules[0] ?? fallback);
}

/** Device-level snapshot fields carried over from the live stream (not car state). */
const CARRY = ["public", "allow_shutdown", "recording", "recording_sources", "source", "port"] as const;

/**
 * The snapshot + live history every screen sees at session time `t`.
 * `fields` is /fields for the module at `t` (limits fallback and signal filter);
 * `base` is the live snapshot (device-level fields are carried over).
 */
export function synthesise(args: {
  meta: SessionMeta; data: SessionData; events: readonly SessionEvent[]; t: number;
  fields?: Record<string, Field>; base?: Snapshot | null; state?: ReplayEventState;
}): { snap: Snapshot; live: LiveState; state: ReplayEventState; module: string } {
  const { meta, data, events, t, fields = {}, base } = args;
  const state = args.state ?? foldEvents(events, t);
  const i = indexAt(data.t, t);
  const module = moduleOf(state, meta);
  const signals = i < 0 ? {} : signalsAt(meta, data, i, fields);
  const text = (data as WithText).text;
  const faults = splitFaults(valueAtIndex(text?.faults, i));
  const status = state.status ?? "connected";
  const at = state.active_test;
  // the instant of the cursor: t0_utc + t; without a UTC time, the session start + t
  const zero = parseUtc(data.t0_utc) ?? parseUtc(meta.start_utc);
  const snap: Snapshot = {
    status, module, signals, faults,
    logging: state.logging ?? { recording: false },
    fault_watch: state.fault_watch,
    active_test: at ? {
      action: at.action, label: at.label ?? at.action, stop: at.stop ?? "",
      since_utc: at.since_utc ?? (at.since != null ? toUtc(at.since * 1000) : toUtc((zero ?? 0) + t)),
    } : null,
    battery_v: signals.battery?.v ?? null,
    gps: i < 0 ? null : gpsAt(data, i),
    stale: false,
    ts_utc: toUtc((zero ?? 0) + t),
  };
  if (state.conn) snap.conn = state.conn;
  for (const k of CARRY) if (base && base[k] !== undefined) (snap as Record<string, unknown>)[k] = base[k];
  const names = Object.keys(signals);
  const history = i < 0 ? {} : historyAt(data, i, names);
  const seen = Object.fromEntries(names.map((n) => [n, REPLAY_SEEN]));
  return { snap, live: { module, history, seen, seq: [], seqDone: true }, state, module };
}

/** The note the cursor is on: a range note while inside it, a point note for NOTE_SHOW_MS after. */
export function activeNote(notes: readonly Note[], t: number): Note | null {
  let best: Note | null = null;
  for (const n of notes) {
    const end = n.t_end ?? n.t + NOTE_SHOW_MS;
    if (t >= n.t && t <= end && (!best || n.t >= best.t)) best = n;
  }
  return best;
}
