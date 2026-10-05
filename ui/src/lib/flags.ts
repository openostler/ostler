/**
 * Automatic flags (specs/2026-10-05-replay-notes-capture-design.md §8): derived in the UI from a
 * session's columnar data each time it is loaded — never stored. A sensor outside its `normal`
 * band (the shaded bracket on every input) for a while, or a fault code that appears, becomes a
 * flag on the transport. Manual ⚑ marks stay notes. The flag manager (in Recording options)
 * chooses which kinds are shown; the choice is per device (localStorage), display-only.
 */
import { useSyncExternalStore } from "react";
import type { Field, SessionData } from "../api/schemas";

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

/**
 * Flags from one session's data. `fields` holds field metadata by signal name for every module
 * the session touched (only fields with a `normal` band are checked). Pure; sorted by t.
 * `faultText(raw)` → the human meaning for a fault string, if known (labels fault flags).
 */
export declare function detectFlags(
  data: SessionData,
  fields: Record<string, Field>,
  faultText?: (raw: string) => string | undefined,
): Flag[];

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
