import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./client";
import type { SessionData, SessionHistogram, SessionMeta } from "./schemas";

/** A session being recorded is re-fetched this often while replayed (its trace grows; state/replay.tsx). */
export const LIVE_REFRESH_MS = 5_000;

/** Page size for the Logs browser (the server caps it at 200). */
export const PAGE_SIZE = 50;

/** The Logs filters (spec §3 query parameters; `from`/`to` are ISO dates, inclusive). */
export type SessionFilters = {
  q?: string;
  from?: string;
  to?: string;
  module?: string;
  has_notes?: boolean;
  min_km?: number;
};

export const filtersActive = (f: SessionFilters) =>
  !!(f.q?.trim() || f.from || f.to || f.module || f.has_notes || f.min_km);

type Query = Omit<SessionFilters, "has_notes"> & { has_notes: boolean };

type PagesState = {
  /** The request key these pages answer (a different key → the first page is loading). */
  forKey: string | null;
  sessions: SessionMeta[] | null;
  next: string | null;
  error: string | null;
  /** A further page is being fetched. */
  more: boolean;
};

/**
 * Keyset-paged GET /sessions (newest first). Any change to `filters`, `anchor` (a `before`
 * cursor the first page starts at, e.g. the month scrubber's) or `refreshKey` drops the
 * pages and loads the first one again; `loadMore` appends the page after `next`.
 */
export function useSessionPages(filters: SessionFilters, anchor: string | null = null, refreshKey = "") {
  const [state, setState] = useState<PagesState>({ forKey: null, sessions: null, next: null, error: null, more: false });
  const [nonce, setNonce] = useState(0);
  const q: Query = {
    q: filters.q?.trim() || undefined, from: filters.from || undefined, to: filters.to || undefined,
    module: filters.module || undefined, has_notes: !!filters.has_notes, min_km: filters.min_km || undefined,
  };
  const filterKey = JSON.stringify(q);
  const reqKey = JSON.stringify([filterKey, anchor, refreshKey, nonce]);
  const live = useRef(reqKey); // the newest request key: a late page for an older one is dropped
  const busy = useRef(false);

  useEffect(() => {
    live.current = reqKey;
    busy.current = true;
    const f = JSON.parse(filterKey) as Query;
    api.sessions({ ...f, limit: PAGE_SIZE, before: anchor }).then(
      (r) => {
        if (live.current !== reqKey) return;
        busy.current = false;
        setState({ forKey: reqKey, sessions: r.sessions, next: r.next ?? null, error: null, more: false });
      },
      (e: Error) => {
        if (live.current !== reqKey) return;
        busy.current = false;
        setState((s) => ({ ...s, forKey: reqKey, error: e.message, more: false }));
      },
    );
  }, [reqKey, filterKey, anchor]);

  const cursor = state.forKey === reqKey ? state.next : null;
  const loadMore = useCallback(() => {
    if (!cursor || busy.current) return;
    busy.current = true;
    setState((s) => ({ ...s, more: true }));
    const f = JSON.parse(filterKey) as Query;
    api.sessions({ ...f, limit: PAGE_SIZE, before: cursor }).then(
      (r) => {
        if (live.current !== reqKey) return;
        busy.current = false;
        setState((s) => {
          const seen = new Set((s.sessions ?? []).map((x) => x.id));
          return { ...s, sessions: [...(s.sessions ?? []), ...r.sessions.filter((x) => !seen.has(x.id))], next: r.next ?? null, error: null, more: false };
        });
      },
      (e: Error) => {
        if (live.current !== reqKey) return;
        busy.current = false;
        setState((s) => ({ ...s, error: e.message, more: false }));
      },
    );
  }, [cursor, filterKey, reqKey]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  const fresh = state.forKey === reqKey;
  return {
    /** The loaded pages; the previous query's rows stay shown while the first page reloads. */
    sessions: state.sessions,
    next: cursor,
    error: state.error,
    /** The first page of the current query is in flight. */
    loading: !fresh,
    loadingMore: state.more,
    loadMore,
    reload,
  };
}

/** GET /sessions/histogram (month buckets, or day buckets of one year). Null until loaded or
 * when the server has no histogram (the scrubber and heatmap then stay hidden). */
export function useSessionHistogram(group: "month" | "day", year?: number, refreshKey = "") {
  const [hist, setHist] = useState<SessionHistogram | null>(null);
  useEffect(() => {
    let alive = true;
    api.sessionHistogram(group, year).then(
      (h) => alive && setHist(h),
      () => alive && setHist(null),
    );
    return () => { alive = false; };
  }, [group, year, refreshKey]);
  return hist;
}

/** Channels worth fetching for replay: everything numeric (the trace and chart pickers
 * switch without another request). Text channels never come back as numbers. */
const SKIP = new Set(["module", "faults"]);
export const replayChannels = (meta: SessionMeta) => meta.channels.map((c) => c.name).filter((n) => !SKIP.has(n));

/** Points fetched for the live Analysis view (as for replay; the data route decimates past it). */
export const LIVE_MAX_POINTS = 3000;

export type LiveSession = { meta: SessionMeta | null; data: SessionData | null; error: string | null };

/**
 * The session being recorded, for the live Analysis tab (spec §7): its meta and data
 * (every numeric channel), re-fetched every LIVE_REFRESH_MS while `id` is set. The previous
 * fetch stays shown until the next one lands; a new `id` starts empty.
 */
export function useLiveSession(id: string | null): LiveSession {
  const [state, setState] = useState<LiveSession & { id: string | null }>({ id: null, meta: null, data: null, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!id) return;
    const timer = window.setInterval(() => setTick((n) => n + 1), LIVE_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [id]);

  useEffect(() => {
    if (!id) return;
    let alive = true;
    api.session(id)
      .then((meta) => api.sessionData(id, replayChannels(meta), LIVE_MAX_POINTS).then((data) => ({ meta, data })))
      .then(
        (r) => alive && setState({ id, meta: r.meta, data: r.data, error: null }),
        (e: Error) => alive && setState((s) => (s.id === id ? { ...s, error: e.message } : { id, meta: null, data: null, error: e.message })),
      );
    return () => { alive = false; };
  }, [id, tick]);

  return state.id === id && id ? { meta: state.meta, data: state.data, error: state.error } : { meta: null, data: null, error: null };
}
