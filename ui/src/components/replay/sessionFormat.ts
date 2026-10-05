/** Session-browser formatting and grouping — pure, local time zone. */
import type { Recording, SessionMeta } from "../../api/schemas";
import type { SessionFilters } from "../../api/useSessions";

const pad = (n: number) => String(n).padStart(2, "0");

/** YYYY-MM-DD of an instant in local time. */
export const localDay = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

/** "Today", "Yesterday", else e.g. "Mon 5 Oct 2026". */
export function dayLabel(day: string, now: Date = new Date()): string {
  if (day === localDay(now)) return "Today";
  const y = new Date(now);
  y.setDate(y.getDate() - 1);
  if (day === localDay(y)) return "Yesterday";
  const [Y, M, D] = day.split("-").map(Number) as [number, number, number];
  return new Date(Y, M - 1, D).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short", year: "numeric" });
}

export type DayGroup = { day: string; label: string; sessions: SessionMeta[] };

/** Sessions grouped by local start day, newest day first and newest session first within it. */
export function groupByDay(sessions: readonly SessionMeta[], now: Date = new Date()): DayGroup[] {
  const sorted = [...sessions].sort((a, b) => Date.parse(b.start_utc) - Date.parse(a.start_utc));
  const groups: DayGroup[] = [];
  for (const s of sorted) {
    const day = localDay(new Date(s.start_utc));
    let g = groups[groups.length - 1];
    if (!g || g.day !== day) {
      g = { day, label: dayLabel(day, now), sessions: [] };
      groups.push(g);
    }
    g.sessions.push(s);
  }
  return groups;
}

/** Local HH:MM of the session start. */
export function startTime(s: Pick<SessionMeta, "start_utc">): string {
  const d = new Date(s.start_utc);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** "45 s", "12 min", "1 h 05 min". */
export function formatDuration(sec: number): string {
  if (sec < 60) return `${Math.max(0, Math.round(sec))} s`;
  const m = Math.round(sec / 60);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${pad(m % 60)} min`;
}

/** Rounded start position as "lat, lon" (3 decimals ≈ 100 m), or "no GPS". */
export function formatPos(p: SessionMeta["start_pos"]): string {
  return p ? `${p[1].toFixed(3)}, ${p[0].toFixed(3)}` : "no GPS";
}

/** Whole minutes recorded so far ("Recording now · N min"). */
export function recordingMinutes(sinceEpochS: number, nowEpochS: number): number {
  return Math.max(0, Math.floor((nowEpochS - sinceEpochS) / 60));
}

/* ---- Logs at scale (specs/2026-10-06-logs-at-scale-design.md §5) ---- */

/** The row/header title: the user's name, else the place label, else "Untitled session". */
export function sessionTitle(s: Pick<SessionMeta, "name" | "place">): string {
  return s.name?.trim() || s.place?.label || "Untitled session";
}

/** The place line under a named session (null when the title already is the place). */
export function sessionPlace(s: Pick<SessionMeta, "name" | "place" | "place_end">): string | null {
  const start = s.place?.label ?? null;
  const end = s.place_end?.label ?? null;
  const route = start && end && end !== start ? `${start} → ${end}` : start;
  if (!s.name?.trim()) return end && start && end !== start ? `→ ${end}` : null;
  return route;
}

/** "Sun 5 Oct · 09:00" (local). */
export function rowDate(s: Pick<SessionMeta, "start_utc">): string {
  const d = new Date(s.start_utc);
  return `${d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })} · ${startTime(s)}`;
}

/** YYYY-MM of an instant in local time. */
export const localMonth = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}`;

/** "October 2026" for "2026-10". */
export function monthLabel(key: string, style: "long" | "short" = "long"): string {
  const [Y, M] = key.split("-").map(Number) as [number, number];
  return new Date(Y, M - 1, 1).toLocaleDateString(undefined, { month: style, year: "numeric" });
}

export type MonthGroup = { key: string; label: string; sessions: SessionMeta[] };
export type YearGroup = { year: number; months: MonthGroup[] };

/** Sessions grouped by local year → month, newest first (the list is already newest first
 * from the server; sorting again keeps appended pages stable). */
export function groupByYearMonth(sessions: readonly SessionMeta[]): YearGroup[] {
  const sorted = [...sessions].sort((a, b) => Date.parse(b.start_utc) - Date.parse(a.start_utc) || (a.id < b.id ? 1 : -1));
  const years: YearGroup[] = [];
  for (const s of sorted) {
    const d = new Date(s.start_utc);
    const year = d.getFullYear();
    const key = localMonth(d);
    let y = years[years.length - 1];
    if (!y || y.year !== year) {
      y = { year, months: [] };
      years.push(y);
    }
    let m = y.months[y.months.length - 1];
    if (!m || m.key !== key) {
      m = { key, label: new Date(year, d.getMonth(), 1).toLocaleDateString(undefined, { month: "long" }), sessions: [] };
      y.months.push(m);
    }
    m.sessions.push(s);
  }
  return years;
}

/**
 * The keyset cursor that starts a page at the end of month `key` ("YYYY-MM"), for the month
 * scrubber (spec §5: "jumps with before=<end of that month>"). The server's cursor is
 * "<start_ms>:<id>" and pages return rows strictly before it in (start_ms, id) order; using
 * the last UTC millisecond of the month with id "~" (sorts after every session id) includes
 * every session that starts in that month. UTC, because the server's month buckets are UTC.
 */
export function monthEndCursor(key: string): string {
  const [Y, M] = key.split("-").map(Number) as [number, number];
  return `${Date.UTC(Y, M, 1) - 1}:~`; // Date.UTC month is 0-based, so M = the next month
}

/** "5 Oct 2026" for an ISO date "2026-10-05". */
export function dayLabelShort(day: string): string {
  const [Y, M, D] = day.split("-").map(Number) as [number, number, number];
  return new Date(Y, M - 1, D).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

/** The server pauses the session while the car is disconnected (logs-at-scale spec §1);
 * an absent state is "recording" (older servers). */
export const isPaused = (r: Pick<Recording, "state"> | null | undefined) => !!r?.state && r.state !== "recording";

/** Bucket index under a pointer at `clientY` in a strip spanning `top`..`top+height`. */
export function indexAt(clientY: number, top: number, height: number, n: number): number {
  if (n <= 1 || height <= 0) return 0;
  const f = Math.min(1, Math.max(0, (clientY - top) / height));
  return Math.min(n - 1, Math.floor(f * n));
}

/** Shade step 1–4 of a day against the busiest day (0 = no sessions). */
export function heatLevel(v: number, max: number): number {
  if (v <= 0 || max <= 0) return 0;
  return Math.min(4, Math.max(1, Math.ceil((v / max) * 4)));
}

/** Logs search debounce (spec §5). */
export const SEARCH_DEBOUNCE_MS = 300;
/** Minimum-distance choices, in km (the server filters in km). */
export const MIN_KM_STEPS = [1, 5, 10, 50] as const;

/** What the browser shows: kept by the caller so it survives a trip into replay and back. */
export type BrowserView = { filters: SessionFilters; anchor: { month: string; cursor: string } | null };
export const EMPTY_VIEW: BrowserView = { filters: {}, anchor: null };

export const ATTRIBUTION = "Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)";
