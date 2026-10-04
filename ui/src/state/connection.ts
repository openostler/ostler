import { useCallback, useEffect, useState } from "react";
import { AUTO_OPEN_MS, shouldAutoOpen, type Conn } from "../lib/connection";

/**
 * Open/closed state of the ConnectionSheet. It opens by itself AUTO_OPEN_MS after the
 * connection enters error | lost | disconnected, never over Consent (`blocked`), and once
 * dismissed it stays closed until `conn` changes. An auto-opened sheet closes again when
 * the connection comes back.
 */
export function useConnectionSheet(conn: Conn | null, blocked: boolean) {
  const [open, setOpen] = useState(false);
  const [auto, setAuto] = useState(false);
  const [dismissedFor, setDismissedFor] = useState<Conn | null>(null);
  const [seenConn, setSeenConn] = useState<Conn | null>(conn);

  // conn changed → a past dismissal no longer applies; an auto-opened sheet closes when connected
  if (conn !== seenConn) {
    setSeenConn(conn);
    setDismissedFor(null);
    if (auto && conn === "connected") {
      setOpen(false);
      setAuto(false);
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

  const show = useCallback(() => {
    setOpen(true);
    setAuto(false);
  }, []);
  const dismiss = useCallback(() => {
    setOpen(false);
    setAuto(false);
    setDismissedFor(conn);
  }, [conn]);

  return { open: open && !blocked, show, dismiss };
}
