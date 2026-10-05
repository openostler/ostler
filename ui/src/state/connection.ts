import { useCallback, useEffect, useState } from "react";
import { autoOpenDelay, isNotLive, REPROMPT_MS, shouldAutoOpen, type Conn } from "../lib/connection";

/**
 * Open/closed state of the ConnectionSheet (spec 2026-10-06 §5). It opens by itself as soon
 * as the connection is error | lost | disconnected (on load, after Consent, and when leaving
 * a replay), and after 1 s of `reconnecting`. It never opens over Consent (`blocked`) or
 * during a replay (`replaying`). Once dismissed it stays closed through the not-live states
 * until a new attempt (connecting) or a live connection — except the re-prompt: if the
 * connection is still not live REPROMPT_MS after a dismissal, it re-opens (each dismissal
 * restarts that timer). Leaving a replay forgets a dismissal. An auto-opened sheet closes
 * again when the connection comes back.
 *
 * `downSince` is when the connection left `connected` (or when it was first seen down),
 * null while connected — the sheet shows "No connection for 1 m 20 s".
 */
export function useConnectionSheet(conn: Conn | null, blocked: boolean, replaying = false) {
  const [open, setOpen] = useState(false);
  const [auto, setAuto] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [seenConn, setSeenConn] = useState<Conn | null>(conn);
  const [seenReplay, setSeenReplay] = useState(replaying);
  const [downSince, setDownSince] = useState<number | null>(() => (conn && conn !== "connected" ? Date.now() : null));
  // the dismissal the re-prompt timer counts from (a counter, so each dismissal restarts it); null = not armed
  const [dismissal, setDismissal] = useState<number | null>(null);

  // conn changed → a new attempt or a live link forgets a dismissal; an auto-opened sheet closes when connected
  if (conn !== seenConn) {
    setSeenConn(conn);
    if (conn === "connecting" || conn === "connected") setDismissed(false);
    if (conn === "connected") {
      setDownSince(null);
      setDismissal(null);
      if (auto) {
        setOpen(false);
        setAuto(false);
      }
    } else if (conn) {
      setDownSince((t) => t ?? Date.now()); // first seen down; kept through lost → reconnecting → error
    }
  }

  // leaving a replay → back to the live car: a dismissal from before no longer applies
  if (replaying !== seenReplay) {
    setSeenReplay(replaying);
    if (!replaying) {
      setDismissed(false);
      setDismissal(null);
    }
  }

  const held = blocked || replaying;
  const want = shouldAutoOpen({ conn, open, dismissed, blocked: held });
  const delay = want ? autoOpenDelay(conn) : null;
  useEffect(() => {
    if (delay === null) return;
    const id = window.setTimeout(() => {
      setOpen(true);
      setAuto(true);
    }, delay);
    return () => window.clearTimeout(id);
  }, [delay, conn]);

  // re-prompt: still not live REPROMPT_MS after the last dismissal → open again
  const notLive = isNotLive(conn);
  useEffect(() => {
    if (dismissal === null || open || held || !notLive) return;
    const id = window.setTimeout(() => {
      setOpen(true);
      setAuto(true);
    }, REPROMPT_MS);
    return () => window.clearTimeout(id);
  }, [dismissal, open, held, notLive]);

  const show = useCallback(() => {
    setOpen(true);
    setAuto(false);
  }, []);
  const dismiss = useCallback(() => {
    setOpen(false);
    setAuto(false);
    setDismissed(true);
    setDismissal((n) => (n ?? 0) + 1);
  }, []);

  return { open: open && !held, show, dismiss, downSince };
}
