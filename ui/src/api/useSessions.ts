import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import type { SessionMeta } from "./schemas";

/** A session being recorded is re-fetched this often while replayed (its trace grows; state/replay.tsx). */
export const LIVE_REFRESH_MS = 5_000;

/** GET /sessions (newest first). `refreshKey` re-fetches (e.g. a recording starting). */
export function useSessions(refreshKey = "") {
  const [state, setState] = useState<{ sessions: SessionMeta[] | null; error: string | null }>({ sessions: null, error: null });
  const [nonce, setNonce] = useState(0);
  useEffect(() => {
    let alive = true;
    api.sessions().then(
      (r) => alive && setState({ sessions: r.sessions, error: null }),
      (e: Error) => alive && setState((s) => ({ sessions: s.sessions, error: e.message })),
    );
    return () => { alive = false; };
  }, [nonce, refreshKey]);
  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { ...state, reload };
}

/** Channels worth fetching for replay: everything numeric (the trace and chart pickers
 * switch without another request). Text channels never come back as numbers. */
const SKIP = new Set(["module", "faults"]);
export const replayChannels = (meta: SessionMeta) => meta.channels.map((c) => c.name).filter((n) => !SKIP.has(n));
