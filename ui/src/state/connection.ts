import { useCallback, useEffect, useState } from "react";
import { AUTO_OPEN_MS, isNotLive, REPROMPT_MS, shouldAutoOpen, type Conn } from "../lib/connection";

/**
 * Open/closed state of the ConnectionSheet. It opens by itself AUTO_OPEN_MS after the
 * connection enters error | lost | disconnected, never over Consent (`blocked`), and once
 * dismissed it stays closed until `conn` changes — except the re-prompt: if the
 * connection is still not live REPROMPT_MS after a dismissal, it re-opens (each dismissal
 * restarts that timer). An auto-opened sheet closes again when the connection comes back.
 *
 * `downSince` is when the connection left `connected` (or when it was first seen down),
 * null while connected — the sheet shows "No connection for 1 m 20 s".
 */
export function useConnectionSheet(conn: Conn | null, blocked: boolean) {
  const [open, setOpen] = useState(false);
  const [auto, setAuto] = useState(false);
  const [dismissedFor, setDismissedFor] = useState<Conn | null>(null);
  const [seenConn, setSeenConn] = useState<Conn | null>(conn);
  const [downSince, setDownSince] = useState<number | null>(() => (conn && conn !== "connected" ? Date.now() : null));
  // the dismissal the re-prompt timer counts from (a counter, so each dismissal restarts it); null = not armed
  const [dismissal, setDismissal] = useState<number | null>(null);

  // conn changed → a past dismissal no longer applies; an auto-opened sheet closes when connected
  if (conn !== seenConn) {
    setSeenConn(conn);
    setDismissedFor(null);
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

  const want = shouldAutoOpen({ conn, open, dismissedFor, blocked });
  useEffect(() => {
    if (!want) return;
    const id = window.setTimeout(() => {
      setOpen(true);
      setAuto(true);
    }, AUTO_OPEN_MS);
    return () => window.clearTimeout(id);
  }, [want, conn]);

  // re-prompt: still not live REPROMPT_MS after the last dismissal → open again
  const notLive = isNotLive(conn);
  useEffect(() => {
    if (dismissal === null || open || blocked || !notLive) return;
    const id = window.setTimeout(() => {
      setOpen(true);
      setAuto(true);
    }, REPROMPT_MS);
    return () => window.clearTimeout(id);
  }, [dismissal, open, blocked, notLive]);

  const show = useCallback(() => {
    setOpen(true);
    setAuto(false);
  }, []);
  const dismiss = useCallback(() => {
    setOpen(false);
    setAuto(false);
    setDismissedFor(conn);
    setDismissal((n) => (n ?? 0) + 1);
  }, [conn]);

  return { open: open && !blocked, show, dismiss, downSince };
}
