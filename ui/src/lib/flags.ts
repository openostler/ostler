/**
 * Automatic flags (specs/2026-10-05-replay-notes-capture-design.md §8): derived in the UI from a
 * session's columnar data each time it is loaded — never stored. A sensor outside its `normal`
 * band (the shaded bracket on every input) for a while, or a fault code that appears, becomes a
 * flag on the transport. Manual ⚑ marks stay notes. The flag manager (in Recording options)
 * chooses which kinds are shown; the choice is per device (localStorage), display-only.
 */
import { useSyncExternalStore } from "react";
import type { Field, SessionData } from "../api/schemas";
import { splitFaults } from "../state/replayState";
import { fmt, parseFault } from "./format";

export type FlagKind = "range" | "fault";
export type FlagSeverity = "warn" | "alarm";

export interface Flag {
  /** Stable across reloads of the same data: `${kind}:${signal|code}:${t}`. */
  id: string;
  kind: FlagKind;
  /** warn: outside `normal` (or a Logged fault); alarm: outside `limits` (or a Current fault). */
  severity: FlagSeverity;
  /** Session ms. */
  t: number;
  /** End of a range flag (null: a point — faults). */
  t_end: number | null;
  /** Short title, e.g. "Coolant 112 °C (normal 80–105)" or "P0380 Glow plug circuit". */
  label: string;
  /** Range flags: the signal name, its worst value and when it happened, and the bands. */
  signal?: string;
  unit?: string;
  peak?: number;
  peakT?: number;
  band?: readonly [number, number];
  limits?: readonly [number, number] | null;
  /** Fault flags: the raw fault strings (one, or several for "stored at start"). */
  faults?: string[];
  current?: boolean;
  /** Set on the single "N more out of range" flag the flood cap folds extras into. */
  folded?: number;
}

/** Detection rules (research: RaceCapture on/off delay, EEMUA 191 deadband, flood cap). */
export const FLAG_RULES = {
  /** Outside `normal` for at least this long before it counts. */
  onDelayMs: 3_000,
  /** Back inside by this fraction of the band's span (span = `span` field, else `normal`) to end. */
  deadband: 0.02,
  /** Excursions of the same signal closer than this merge into one flag. */
  mergeGapMs: 10_000,
  /** More auto range flags than this starting within `floodWindowMs` fold into one. */
  floodMax: 6,
  floodWindowMs: 60_000,
} as const;

/** A null gap longer than this ends an excursion (the signal was not being read). */
const GAP_MS = 5_000;

type Excursion = {
  start: number; end: number; peak: number; peakT: number; dist: number; alarm: boolean;
  /** Out of range from the signal's first reading and only ever recovering towards the band
   * (a cold engine warming up, the engine not yet running) — expected, so never flagged. */
  settling: boolean;
};

/** One signal's excursions outside `normal` (before the on-delay, merge and flood rules). */
function excursions(t: readonly number[], col: readonly (number | null)[], f: Field): Excursion[] {
  const [lo, hi] = f.normal!;
  const [sLo, sHi] = f.span ?? f.normal!;
  const db = FLAG_RULES.deadband * Math.abs(sHi - sLo);
  const lim = f.limits;
  const out: Excursion[] = [];
  let cur: Excursion | null = null;
  let lastT = -Infinity;
  let firstT: number | null = null;
  const n = Math.min(t.length, col.length);
  for (let i = 0; i < n; i++) {
    const v = col[i];
    if (v == null || Number.isNaN(v)) continue;
    const tt = t[i]!;
    firstT ??= tt;
    if (cur && tt - lastT > GAP_MS) {
      out.push(cur);
      cur = null;
    }
    lastT = tt;
    const outside = v < lo || v > hi;
    if (!cur) {
      if (!outside) continue;
      cur = { start: tt, end: tt, peak: v, peakT: tt, dist: v < lo ? lo - v : v - hi, alarm: false, settling: tt === firstT };
    } else if (!outside && v > lo + db && v < hi - db) {
      out.push(cur);
      cur = null;
      continue;
    }
    cur.end = tt;
    if (outside) {
      const dist = v < lo ? lo - v : v - hi;
      if (dist > cur.dist) Object.assign(cur, { dist, peak: v, peakT: tt, settling: false });
      if (lim && (v < lim[0] || v > lim[1])) cur.alarm = true;
    }
  }
  if (cur) out.push(cur);
  // the on-delay, then merge what is left when closer than mergeGapMs
  const merged: Excursion[] = [];
  for (const e of out) {
    if (e.settling || e.end - e.start < FLAG_RULES.onDelayMs) continue;
    const prev = merged[merged.length - 1];
    if (prev && e.start - prev.end < FLAG_RULES.mergeGapMs) {
      prev.end = e.end;
      prev.alarm ||= e.alarm;
      if (e.dist > prev.dist) Object.assign(prev, { dist: e.dist, peak: e.peak, peakT: e.peakT });
    } else merged.push({ ...e });
  }
  return merged;
}

const bySeverity = (a: FlagSeverity, b: FlagSeverity): FlagSeverity => (a === "alarm" || b === "alarm" ? "alarm" : "warn");

/** The flood cap: more than floodMax range flags starting within floodWindowMs → the extras
 * fold into one "N more out of range" flag per window. `flags` sorted by t. */
function floodCap(flags: Flag[]): Flag[] {
  const kept: Flag[] = [];
  const out: Flag[] = [];
  let group: Flag[] = [];
  const flush = () => {
    if (!group.length) return;
    const first = group[0]!;
    const tEnd = Math.max(...group.map((g) => g.t_end ?? g.t));
    out.push({
      id: `range:folded:${first.t}`, kind: "range", t: first.t, t_end: tEnd,
      severity: group.reduce<FlagSeverity>((s, g) => bySeverity(s, g.severity), "warn"),
      label: `${group.length} more out of range`, folded: group.length,
    });
    group = [];
  };
  for (const f of flags) {
    let inWindow = 0;
    for (let i = kept.length - 1; i >= 0 && kept[i]!.t > f.t - FLAG_RULES.floodWindowMs; i--) inWindow++;
    if (inWindow < FLAG_RULES.floodMax) {
      kept.push(f);
      out.push(f);
      continue;
    }
    if (group.length && f.t - group[0]!.t >= FLAG_RULES.floodWindowMs) flush();
    group.push(f);
  }
  flush();
  return out;
}

const fmtBand = (v: number) => String(+v.toFixed(2));

function rangeFlags(data: SessionData, fields: Record<string, Field>): Flag[] {
  const flags: Flag[] = [];
  for (const [name, f] of Object.entries(fields)) {
    const col = data.ch[name];
    if (!f.normal || !col) continue;
    const [lo, hi] = f.normal;
    const unit = f.unit ?? "";
    for (const e of excursions(data.t, col, f)) {
      flags.push({
        id: `range:${name}:${e.start}`, kind: "range", severity: e.alarm ? "alarm" : "warn",
        t: e.start, t_end: e.end,
        label: `${f.label || name} ${fmt(e.peak)}${unit ? ` ${unit}` : ""} (normal ${fmtBand(lo)}–${fmtBand(hi)})`,
        signal: name, unit, peak: e.peak, peakT: e.peakT, band: [lo, hi], limits: f.limits ?? null,
      });
    }
  }
  flags.sort((a, b) => a.t - b.t || a.id.localeCompare(b.id));
  return floodCap(flags);
}

/** What identifies one fault across rows: its code, else its text (the Current/Logged tag off). */
export function faultKey(raw: string): string {
  const p = parseFault(raw);
  return p.raw || p.text;
}

function faultFlags(data: SessionData, faultText?: (raw: string) => string | undefined): Flag[] {
  const col = data.text?.faults;
  if (!col) return [];
  const label1 = (raw: string) => faultText?.(raw) ?? parseFault(raw).text;
  const flags: Flag[] = [];
  const seen = new Set<string>();
  let first = true;
  const n = Math.min(col.length, data.t.length);
  for (let i = 0; i < n; i++) {
    const row = col[i];
    if (row == null) continue;
    const t = data.t[i]!;
    const list = splitFaults(row);
    if (first) {
      first = false;
      const stored = list.filter((raw) => { const k = faultKey(raw); return seen.has(k) ? false : (seen.add(k), true); });
      if (stored.length) {
        const current = stored.some((raw) => parseFault(raw).current);
        flags.push({
          id: `fault:stored:${t}`, kind: "fault", severity: current ? "alarm" : "warn", t, t_end: null,
          label: stored.length === 1 ? label1(stored[0]!) : `${stored.length} stored faults`,
          faults: stored, current,
        });
      }
      continue;
    }
    for (const raw of list) {
      const key = faultKey(raw);
      if (seen.has(key)) continue;
      seen.add(key);
      const current = parseFault(raw).current;
      flags.push({
        id: `fault:${key}:${t}`, kind: "fault", severity: current ? "alarm" : "warn", t, t_end: null,
        label: label1(raw), faults: [raw], current,
      });
    }
  }
  return flags;
}

/**
 * Flags from one session's data. `fields` holds field metadata by signal name for every module
 * the session touched (only fields with a `normal` band are checked). Pure; sorted by t.
 * `faultText(raw)` → the human meaning for a fault string, if known (labels fault flags).
 */
export function detectFlags(
  data: SessionData,
  fields: Record<string, Field>,
  faultText?: (raw: string) => string | undefined,
): Flag[] {
  const all = [...rangeFlags(data, fields), ...faultFlags(data, faultText)];
  return all.sort((a, b) => a.t - b.t);
}

/* ---- the flag manager's options (per device) ---- */

export interface FlagOptions {
  /** Manual ⚑ marks and notes on the transport. */
  manual: boolean;
  /** Sensor out of its normal range. */
  range: boolean;
  /** Fault codes detected. */
  faults: boolean;
  /** Signal names never flagged. */
  muted: string[];
}

export const DEFAULT_FLAG_OPTIONS: FlagOptions = { manual: true, range: true, faults: true, muted: [] };
const KEY = "d2diag.flagOptions";
const listeners = new Set<() => void>();
let current: FlagOptions | null = null;

export function loadFlagOptions(): FlagOptions {
  if (current) return current;
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<FlagOptions>;
    current = {
      manual: raw.manual !== false,
      range: raw.range !== false,
      faults: raw.faults !== false,
      muted: Array.isArray(raw.muted) ? raw.muted.filter((s): s is string => typeof s === "string") : [],
    };
  } catch {
    current = DEFAULT_FLAG_OPTIONS;
  }
  return current;
}

export function saveFlagOptions(o: FlagOptions): void {
  current = o;
  try {
    localStorage.setItem(KEY, JSON.stringify(o));
  } catch {
    /* storage blocked — the choice lasts for this page only */
  }
  listeners.forEach((l) => l());
}

/** The current flag options; re-renders when the manager changes them. */
export function useFlagOptions(): FlagOptions {
  return useSyncExternalStore(
    (l) => { listeners.add(l); return () => listeners.delete(l); },
    loadFlagOptions,
  );
}

/** Flags the options let through (muted sensors and switched-off kinds removed). */
export function visibleFlags(flags: readonly Flag[], o: FlagOptions): Flag[] {
  return flags.filter((f) => (f.kind === "range" ? o.range && !(f.signal && o.muted.includes(f.signal)) : o.faults));
}

/** Test helper: forget the cached options (after localStorage changes). */
export function resetFlagOptionsCache(): void {
  current = null;
}
