import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import type { SessionData, SessionMeta } from "./schemas";

/** A session being recorded is re-fetched this often (its trace grows). */
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

/**
 * One session's meta + columnar data. While the session is recording (`meta.recording`) both
 * are re-fetched every LIVE_REFRESH_MS so the trace grows. The previous data stays on screen
 * while a refresh is in flight; a failed refresh keeps it and reports `error`.
 */
export function useSessionReplay(id: string | null) {
  const [state, setState] = useState<{ id: string | null; meta: SessionMeta | null; data: SessionData | null; error: string | null }>({
    id: null, meta: null, data: null, error: null,
  });
  const [tick, setTick] = useState(0);
  const recording = state.id === id && !!state.meta?.recording;

  useEffect(() => {
    if (!id) return;
    let alive = true;
    (async () => {
      const meta = await api.session(id);
      const data = await api.sessionData(id, replayChannels(meta));
      if (alive) setState({ id, meta, data, error: null });
    })().catch((e: Error) => alive && setState((s) => (s.id === id ? { ...s, error: e.message } : { id, meta: null, data: null, error: e.message })));
    return () => { alive = false; };
  }, [id, tick]);

  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setTick((n) => n + 1), LIVE_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [recording]);

  const current = state.id === id;
  return { meta: current ? state.meta : null, data: current ? state.data : null, error: current ? state.error : null };
}
