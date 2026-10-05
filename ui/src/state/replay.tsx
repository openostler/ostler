/**
 * Whole-app replay (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md §4).
 *
 * `ReplayProvider` is mounted at the root of <App>. `enter(id)` loads the session's meta, data
 * (every numeric channel), events and notes; while it is open every screen is read-only and
 * `useApp()` returns a snapshot synthesised at the cursor (state/replayState.ts). `exit()`
 * returns to live. The live stream keeps running underneath; nothing is sent to the car.
 *
 * While a session is open the provider also supplies `PlaybackCtx`, so `usePlayback()` (the
 * transport, the Logs chart) reads the same clock.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Note, SessionData, SessionEvent, SessionMeta } from "../api/schemas";
import { LIVE_REFRESH_MS, replayChannels } from "../api/useSessions";
import { PlaybackCtx, toSpeed, usePlaybackState, utcOffset, type Playback } from "./playback";
import { foldEvents, initialEventState } from "./replayState";
import type { ReplayEventState, ReplayState } from "./replayTypes";

/** Points fetched for replay (the data route min/max-decimates past this). */
export const REPLAY_MAX_POINTS = 3000;
/** The refusal every action gets while a session is open. */
export const READ_ONLY_ERROR = "Replay — read only";

/** `ReplayState` plus what the banner and transport also need. */
export interface Replay extends ReplayState {
  /** The session id being opened or open (set before its data arrives). */
  id: string | null;
  loading: boolean;
  error: string | null;
  /** utc − session ms (null: the session has no UTC; show session time). */
  offset: number | null;
  /** The shared clock (null when not active). */
  playback: Playback | null;
  /** The events folded up to `t` (module, conn, active_test, lastCommand, …). */
  state: ReplayEventState;
}

const noop = () => undefined;
const EMPTY_T: number[] = [];

export const INACTIVE: Replay = {
  active: false, id: null, loading: false, error: null, offset: null, playback: null, state: initialEventState(),
  events: [], notes: [], t: 0, playing: false, speed: 1,
  enter: noop, exit: noop, seek: noop, play: noop, pause: noop, setSpeed: noop,
  addNote: async () => null, refreshNotes: noop,
};

export const ReplayCtx = createContext<Replay>(INACTIVE);

/** The replay state; outside a ReplayProvider it is inactive (live). */
export function useReplay(): Replay {
  return useContext(ReplayCtx);
}

type Loaded = { id: string; meta: SessionMeta | null; data: SessionData | null; events: SessionEvent[]; notes: Note[]; error: string | null };

/** Fetch one session for replay: meta, then data + events + notes together. Events and notes
 * are optional (a session from before ADR-0010 has none). */
export async function loadSession(id: string): Promise<Omit<Loaded, "error">> {
  const meta = await api.session(id);
  const [data, events, notes] = await Promise.all([
    api.sessionData(id, replayChannels(meta), REPLAY_MAX_POINTS),
    api.sessionEvents(id).then((r) => r.events, () => [] as SessionEvent[]),
    api.notes(id).then((r) => r.notes, () => [] as Note[]),
  ]);
  return { id, meta, data, events, notes };
}

export function ReplayProvider({ children, initial = null }: { children: ReactNode; initial?: string | null }) {
  const [id, setId] = useState<string | null>(initial);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [tick, setTick] = useState(0);
  const cur = loaded && loaded.id === id ? loaded : null;
  const meta = cur?.meta ?? undefined;
  const data = cur?.data ?? undefined;

  useEffect(() => {
    if (!id) return;
    let alive = true;
    loadSession(id).then(
      (r) => alive && setLoaded({ ...r, error: null }),
      (e: Error) => alive && setLoaded((s) => (s && s.id === id ? { ...s, error: e.message } : { id, meta: null, data: null, events: [], notes: [], error: e.message })),
    );
    return () => { alive = false; };
  }, [id, tick]);

  // a session still being recorded grows: re-fetch it while it is open
  const recording = !!meta?.recording;
  useEffect(() => {
    if (!recording) return;
    const timer = window.setInterval(() => setTick((n) => n + 1), LIVE_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [recording]);

  const pb = usePlaybackState(data?.t ?? EMPTY_T, { resetKey: id });
  const offset = useMemo(() => (data ? utcOffset(data.t, data.utc) : null), [data]);
  const events = cur?.events;
  const state = useMemo(() => foldEvents(events ?? [], pb.time), [events, pb.time]);

  const enter = useCallback((next: string) => setId(next), []);
  const { pause } = pb;
  const exit = useCallback(() => {
    pause();
    setId(null);
    setLoaded(null);
  }, [pause]);

  const refreshNotes = useCallback(() => {
    if (!id) return;
    api.notes(id).then(
      (r) => setLoaded((s) => (s && s.id === id ? { ...s, notes: r.notes } : s)),
      () => undefined,
    );
  }, [id]);

  const addNote = useCallback(async (note: { t: number; t_end?: number | null; text?: string; tags?: string[] }) => {
    if (!id) return null;
    try {
      const r = await api.addNote(id, note);
      refreshNotes();
      return r.note ?? null;
    } catch {
      return null;
    }
  }, [id, refreshNotes]);

  const { setSpeed: setPbSpeed } = pb;
  const setSpeed = useCallback((n: number) => setPbSpeed(toSpeed(n)), [setPbSpeed]);

  const active = id != null;
  const value: Replay = active ? {
    active, id, loading: !cur, error: cur?.error ?? null, offset, playback: pb, state,
    session: meta, data, events: events ?? [], notes: cur?.notes ?? [],
    t: pb.time, playing: pb.playing, speed: pb.speed,
    enter, exit, seek: pb.seek, play: pb.play, pause: pb.pause, setSpeed, addNote, refreshNotes,
  } : { ...INACTIVE, enter };

  return (
    <ReplayCtx.Provider value={value}>
      <PlaybackCtx.Provider value={active ? pb : null}>{children}</PlaybackCtx.Provider>
    </ReplayCtx.Provider>
  );
}
