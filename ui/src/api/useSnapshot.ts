// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import { Snapshot } from "./schemas";

/**
 * The live snapshot: primed from /snapshot, then pushed over /events (SSE) every poll.
 * EventSource reconnects by itself; `linkUp` turns false only after the stream errors,
 * and true again on the next open or message.
 */
export function useSnapshot(onSnapshot?: (s: Snapshot) => void) {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [linkUp, setLinkUp] = useState(true);

  const accept = useCallback(
    (raw: unknown) => {
      const out = Snapshot.safeParse(raw);
      if (!out.success) {
        console.warn("snapshot: unexpected shape", out.error.issues);
        return;
      }
      setSnap(out.data);
      onSnapshot?.(out.data);
    },
    [onSnapshot],
  );

  const refresh = useCallback(() => {
    api.snapshot().then(accept, () => undefined);
  }, [accept]);

  useEffect(() => {
    refresh();
    if (typeof EventSource === "undefined") return;
    const es = new EventSource("/events");
    es.onopen = () => setLinkUp(true);
    es.onerror = () => setLinkUp(false);
    es.onmessage = (e) => {
      setLinkUp(true);
      try {
        accept(JSON.parse(e.data));
      } catch {
        /* a torn message — the next one replaces it */
      }
    };
    return () => es.close();
  }, [accept, refresh]);

  return { snap, linkUp, refresh };
}
