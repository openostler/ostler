/**
 * The whole-app replay contract (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md §4).
 * `state/replay.tsx` implements it; every screen reads replay only through `useApp()` (which
 * synthesises `snap`/`live` at `t`) or `useReplay()` for the transport, banner and notes.
 */
import type { Note, SessionData, SessionEvent, SessionMeta } from "../api/schemas";

export interface ReplayState {
  /** True while a session is open for replay (every page is read-only). */
  active: boolean;
  session?: SessionMeta;
  data?: SessionData;
  events: SessionEvent[];
  notes: Note[];
  /** Cursor, in session milliseconds. */
  t: number;
  playing: boolean;
  /** 1 | 2 | 4 | 8 */
  speed: number;
  enter(id: string): void;
  exit(): void;
  seek(t: number): void;
  play(): void;
  pause(): void;
  setSpeed(n: number): void;
  /** Retro note at a time (or range); resolves to the stored note. */
  addNote(note: { t: number; t_end?: number | null; text?: string; tags?: string[] }): Promise<Note | null>;
  refreshNotes(): void;
}

/** Event state folded up to time t (the fields a synthesised snapshot needs). */
export interface ReplayEventState {
  conn: string | null;
  status: string | null;
  module: string | null;
  mode: string | null;
  active_test: { action: string; label?: string; since?: number; stop?: string } | null;
  fault_watch: boolean;
  logging: { recording: boolean; file?: string } | null;
  /** Last command event per action at or before t. */
  lastCommand: Record<string, { t: number; ok: boolean; message?: string; error?: string }>;
}
