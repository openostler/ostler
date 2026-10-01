import type { Snapshot } from "../api/schemas";

/**
 * State derived from the stream of snapshots: a short value history per signal (for the
 * trend chart) and the connection sequence (each new connect_phase while connecting).
 * Pure reducer — unit-tested without a server.
 */
export const HISTORY_LEN = 60;

export type Sample = { t: number; v: number };
export type SeqStep = { phase: string; t: number; ok?: boolean };

export type LiveState = {
  module: string;
  history: Record<string, Sample[]>;
  seq: SeqStep[];
  seqDone: boolean;
};

export const initialLive: LiveState = { module: "motor", history: {}, seq: [], seqDone: false };

export function reduceSnapshot(state: LiveState, snap: Snapshot, now: number): LiveState {
  const module = snap.module ?? state.module;
  // a new module → new history and a new connection sequence
  const base = module !== state.module ? initialLive : state;
  const history = base.history;
  let { seq, seqDone } = base;

  const phase = snap.connect_phase;
  const lastPhase = seq.length ? seq[seq.length - 1]?.phase : undefined;
  if (phase && phase !== lastPhase) {
    seq = [...seq, { phase, t: now }];
    seqDone = false;
  }
  if (snap.status === "connected" && seq.length && !seqDone) {
    seq = [...seq, { phase: "session established", t: now, ok: true }];
    seqDone = true;
  }
  if (snap.status === "error") seqDone = false;

  const next: Record<string, Sample[]> = { ...history };
  for (const [name, s] of Object.entries(snap.signals)) {
    if (typeof s.v !== "number") continue;
    const h = [...(next[name] ?? []), { t: now, v: s.v }];
    next[name] = h.length > HISTORY_LEN ? h.slice(h.length - HISTORY_LEN) : h;
  }
  return { module, history: next, seq, seqDone };
}
