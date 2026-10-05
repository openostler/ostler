import type { Snapshot } from "../api/schemas";

/** The connection state machine (spec "Snapshot additions"). */
export type Conn = "disconnected" | "connecting" | "connected" | "lost" | "reconnecting" | "error";

/** snap.conn when the server sends it, else derived from the legacy snap.status. */
export function connOf(snap: Snapshot | null): Conn | null {
  if (!snap) return null;
  const c = snap.conn;
  if (c === "disconnected" || c === "connecting" || c === "connected" || c === "lost" || c === "reconnecting" || c === "error") return c;
  if (snap.status === "connected") return "connected";
  if (snap.status === "error" || snap.status === "no-cable") return "error";
  return "connecting";
}

/**
 * States in which the ConnectionSheet opens by itself (spec 2026-10-06 §5): error, lost and
 * disconnected at once (AUTO_OPEN_MS = 0 — on load, and when leaving replay); `reconnecting`
 * after RECONNECTING_MS, so a quick retry that succeeds never flashes the sheet.
 */
export const AUTO_OPEN: readonly Conn[] = ["error", "lost", "disconnected", "reconnecting"];
export const AUTO_OPEN_MS = 0;
export const RECONNECTING_MS = 1000;

/** How long `conn` must hold before the sheet opens by itself (null = it never does). */
export function autoOpenDelay(conn: Conn | null): number | null {
  if (!conn || !AUTO_OPEN.includes(conn)) return null;
  return conn === "reconnecting" ? RECONNECTING_MS : AUTO_OPEN_MS;
}

/** States in which values in the snapshot are not fresh readings from the car. */
export const NOT_LIVE: readonly Conn[] = ["lost", "reconnecting", "error", "disconnected"];

/** True when `conn` is a NOT_LIVE state (null = no snapshot yet, not counted). */
export const isNotLive = (conn: Conn | null): boolean => !!conn && NOT_LIVE.includes(conn);

/** After the sheet is dismissed, it re-opens if the connection is still not live this long later. */
export const REPROMPT_MS = 60_000;

/** "45 s", "1 m 20 s", "2 h 5 m" — how long the link has been down. */
export function fmtDown(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} m ${s % 60} s`;
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} m`;
}

/** Pill: dot class + word. `linkUp` false = the dashboard's own SSE stream dropped. */
export function pillFor(conn: Conn | null, linkUp: boolean): [string, string] {
  if (conn && !linkUp) return ["yellow blink", "Reconnecting"];
  switch (conn) {
    case "connected": return ["green", "Connected"];
    case "lost": return ["red", "Connection lost"];
    case "reconnecting": return ["yellow blink", "Reconnecting"];
    case "error": return ["red", "No connection"];
    case "disconnected": return ["", "Disconnected"];
    default: return ["yellow blink", "Connecting"];
  }
}

/**
 * Whether the sheet should auto-open: in an AUTO_OPEN state, not already open, not over
 * Consent or a replay (`blocked`), and not dismissed — a dismissal holds through the
 * not-live states (lost → reconnecting → error …) until a new attempt (connecting) or a live
 * connection; the 60 s re-prompt (REPROMPT_MS) covers a long outage.
 */
export function shouldAutoOpen(s: { conn: Conn | null; open: boolean; dismissed: boolean; blocked: boolean }): boolean {
  if (s.open || s.blocked || s.dismissed) return false;
  return autoOpenDelay(s.conn) !== null;
}
