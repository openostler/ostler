// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Snapshot } from "../api/schemas";
import { connOf, NOT_LIVE } from "../lib/connection";

/**
 * State derived from the stream of snapshots: a short value history per signal (for the
 * trend chart), when each signal last updated (staleness), and the connection sequence
 * (each new connect_phase while connecting).
 * Pure reducer — unit-tested without a server.
 */
export const HISTORY_LEN = 60;
/** A value older than this (ms) is stale: greyed, with "last seen N s ago". */
export const STALE_MS = 5000;

export type Sample = { t: number; v: number };
export type SeqStep = { phase: string; t: number; ok?: boolean };

export type LiveState = {
  module: string;
  history: Record<string, Sample[]>;
  /** Client time (ms) a fresh value last arrived, per signal. */
  seen: Record<string, number>;
  seq: SeqStep[];
  seqDone: boolean;
};

export const initialLive: LiveState = { module: "", history: {}, seen: {}, seq: [], seqDone: false };

export function reduceSnapshot(state: LiveState, snap: Snapshot, now: number): LiveState {
  const module = snap.module ?? state.module;
  // a new module → new history and a new connection sequence
  const base = module !== state.module ? initialLive : state;
  const history = base.history;
  // a snapshot sent while the link to the car is down (or flagged stale) carries no fresh values
  const conn = connOf(snap);
  const fresh = !snap.stale && !(conn && NOT_LIVE.includes(conn));
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
  const seen = fresh ? { ...base.seen } : base.seen;
  for (const [name, s] of Object.entries(snap.signals)) {
    if (typeof s.v !== "number" || !fresh) continue;
    if (s.stale) {
      // A node's last known value (NodeSource spec §6.4): never a fresh reading. With a
      // known age it shows "last seen N s ago" (at least STALE_MS, so it is never drawn
      // live); with none it keeps what was seen before, or stays "not live".
      if (typeof s.age_s === "number") seen[name] = now - Math.max(s.age_s * 1000, STALE_MS + 1);
      continue;
    }
    seen[name] = now;
    const h = [...(next[name] ?? []), { t: now, v: s.v }];
    next[name] = h.length > HISTORY_LEN ? h.slice(h.length - HISTORY_LEN) : h;
  }
  return { module, history: next, seen, seq, seqDone };
}

/** Seconds since `name` last updated, or null when it is fresh. Stale when it has not
 * updated for more than STALE_MS, or the SSE link is down. Never show stale as live. */
export function staleAge(seen: number | undefined, now: number, linkUp: boolean): number | null {
  if (seen == null) return null; // never seen: there is no value to mislabel
  const age = now - seen;
  if (age > STALE_MS || !linkUp) return Math.max(0, Math.round(age / 1000));
  return null;
}
