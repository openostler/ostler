/**
 * Replay playback: one clock over a session's time base (`t`, session ms) that drives the
 * map cursor, the chart cursor and the readouts (specs/2026-10-05-session-logbook-design.md).
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented: the clock is a
 * pure function of an anchor (wall time + session time) and a speed, so seeking or changing
 * speed only re-anchors it, and the rAF loop never depends on the per-frame time.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

export const SPEEDS = [1, 2, 4, 8] as const;
export type Speed = (typeof SPEEDS)[number];
/** ⏪ / ⏩ jump. */
export const SKIP_MS = 10_000;

export const clamp = (v: number, lo: number, hi: number): number => Math.min(hi, Math.max(lo, v));

/** The index of the last sample at or before `ms` (binary search; `t` ascending). Before the
 * first sample → 0; empty → -1. Duplicate times (min/max decimation pairs) → the last one. */
export function indexAt(t: readonly number[], ms: number): number {
  if (t.length === 0) return -1;
  let lo = 0;
  let hi = t.length - 1;
  if (ms < t[0]!) return 0;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (t[mid]! <= ms) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

/** The value of a sparse channel at `ms`: the sample at or before it, or the nearest earlier
 * non-null within `lookback` samples (sparse rows leave a channel empty between polls). */
export function valueAt(t: readonly number[], values: readonly (number | null)[] | undefined, ms: number, lookback = 25): number | null {
  if (!values) return null;
  const i = indexAt(t, ms);
  for (let j = i; j >= 0 && j > i - lookback; j--) {
    const v = values[j];
    if (v != null) return v;
  }
  return null;
}

export type Anchor = { wall: number; time: number };

/** Session time now, from an anchor: elapsed wall time × speed, clamped to [start, end]. */
export function clockAt(anchor: Anchor, wallNow: number, speed: number, start: number, end: number): { time: number; ended: boolean } {
  const time = anchor.time + (wallNow - anchor.wall) * speed;
  if (time >= end) return { time: end, ended: true };
  return { time: Math.max(start, time), ended: false };
}

/** Epoch ms ↔ session ms offset, from the first row with a known UTC (null: no UTC at all). */
export function utcOffset(t: readonly number[], utc: readonly (number | null)[]): number | null {
  for (let i = 0; i < utc.length && i < t.length; i++) {
    const u = utc[i];
    if (u != null) return u - t[i]!;
  }
  return null;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Session time as m:ss (h:mm:ss past an hour). */
export function formatSessionTime(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${m}:${pad(s % 60)}`;
}

/** Clock label for the scrubber: local wall time (HH:MM:SS) when UTC is known, else session time. */
export function formatClock(ms: number, offset: number | null): string {
  if (offset == null) return formatSessionTime(ms);
  const d = new Date(offset + ms);
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

export type Playback = {
  time: number;
  start: number;
  end: number;
  playing: boolean;
  speed: Speed;
  /** Index into `t` at the cursor. */
  index: number;
  play: () => void;
  pause: () => void;
  toggle: () => void;
  seek: (ms: number) => void;
  skip: (deltaMs: number) => void;
  setSpeed: (s: Speed) => void;
};

export type PlaybackOpts = {
  /** Follow live: hold the cursor at the newest sample. */
  pinToEnd?: boolean;
  /** Called on any user seek or play (so the caller can drop Follow live). */
  onUserMove?: () => void;
  /** A new key (e.g. a new session id in the root replay provider) rewinds to the start and pauses. */
  resetKey?: string | null;
};

/**
 * The playback controller over a time base. One clock serves both a single Logs replay and the
 * app-root ReplayProvider (ADR-0010): `resetKey` lets the long-lived root clock start over when
 * another session is opened.
 */
export function usePlaybackState(t: readonly number[], opts: PlaybackOpts = {}): Playback {
  const start = t.length ? t[0]! : 0;
  const end = t.length ? t[t.length - 1]! : 0;
  const [state, setState] = useState<{ time: number; playing: boolean; speed: Speed }>({ time: start, playing: false, speed: 1 });
  const [key, setKey] = useState(opts.resetKey);
  if (opts.resetKey !== key) {
    setKey(opts.resetKey);
    setState((s) => ({ ...s, time: start, playing: false }));
  }
  // While pinned the clock's own time tracks the newest sample, so dropping the pin (a seek,
  // ±skip or Play) carries on from where the cursor was shown, not from a stale time.
  if (opts.pinToEnd && (state.time !== end || state.playing)) {
    setState((s) => ({ ...s, time: end, playing: false }));
  }
  const anchor = useRef<Anchor>({ wall: 0, time: start });
  const bounds = useRef({ start, end, speed: state.speed, time: state.time });
  const onUserMove = useRef(opts.onUserMove);
  useEffect(() => {
    bounds.current = { start, end, speed: state.speed, time: state.time };
    onUserMove.current = opts.onUserMove;
  });

  // The loop is (re)started only when playing flips or speed changes; each frame reads refs.
  useEffect(() => {
    if (!state.playing) return;
    anchor.current = { wall: performance.now(), time: bounds.current.time };
    let raf = 0;
    const frame = () => {
      const b = bounds.current;
      const { time, ended } = clockAt(anchor.current, performance.now(), b.speed, b.start, b.end);
      setState((s) => ({ ...s, time, playing: !ended }));
      if (!ended) raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(raf);
  }, [state.playing, state.speed]);

  const seek = useCallback((ms: number) => {
    const b = bounds.current;
    const time = clamp(ms, b.start, b.end);
    anchor.current = { wall: performance.now(), time };
    bounds.current = { ...b, time };
    onUserMove.current?.();
    setState((s) => ({ ...s, time }));
  }, []);
  const play = useCallback(() => {
    const b = bounds.current;
    onUserMove.current?.();
    setState((s) => ({ ...s, playing: true, time: s.time >= b.end ? b.start : s.time }));
  }, []);
  const pause = useCallback(() => setState((s) => ({ ...s, playing: false })), []);
  const toggle = useCallback(() => (state.playing ? pause() : play()), [state.playing, pause, play]);
  const skip = useCallback((d: number) => seek(bounds.current.time + d), [seek]);
  const setSpeed = useCallback((speed: Speed) => setState((s) => ({ ...s, speed })), []);

  const time = opts.pinToEnd ? end : clamp(state.time, start, end);
  const index = useMemo(() => indexAt(t, time), [t, time]);
  return {
    time, start, end, index, speed: state.speed, playing: state.playing && !opts.pinToEnd,
    play, pause, toggle, seek, skip, setSpeed,
  };
}

export const PlaybackCtx = createContext<Playback | null>(null);

/** The nearest playback clock: a Logs replay's own provider, else the root ReplayProvider's
 * (which provides PlaybackCtx while a session is open, so this keeps working as screens move
 * to `useReplay()`). Throws when neither is present. */
export function usePlayback(): Playback {
  const p = useContext(PlaybackCtx);
  if (!p) throw new Error("usePlayback() outside <PlaybackCtx.Provider>");
  return p;
}

/** A Speed from any number (unknown → 1×). */
export const toSpeed = (n: number): Speed => ((SPEEDS as readonly number[]).includes(n) ? (n as Speed) : 1);
