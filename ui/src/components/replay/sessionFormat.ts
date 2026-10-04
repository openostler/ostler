/** Session-browser formatting and grouping — pure, local time zone. */
import type { SessionMeta } from "../../api/schemas";

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
