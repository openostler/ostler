// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/** Note helpers for the replay timeline (spec §2, §5) — pure. */
import type { Note } from "../api/schemas";
import type { SymbolName } from "../icons/Icon";

const pad = (n: number) => String(n).padStart(2, "0");

/** Session ms → "m:ss" or "h:mm:ss". */
export function formatNoteTime(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${m}:${pad(s % 60)}`;
}

/** "1:20" or "1:20–1:45" for a range. */
export function noteSpan(n: Pick<Note, "t" | "t_end">): string {
  return n.t_end != null ? `${formatNoteTime(n.t)}–${formatNoteTime(n.t_end)}` : formatNoteTime(n.t);
}

/** Notes by time (then creation). */
export function sortNotes(notes: readonly Note[]): Note[] {
  return [...notes].sort((a, b) => a.t - b.t || a.created.localeCompare(b.created));
}

/** True when the cursor is on the note: inside its range, or within `tolMs` of a point note. */
export function noteAt(n: Pick<Note, "t" | "t_end">, cursor: number, tolMs = 1000): boolean {
  return n.t_end != null ? cursor >= n.t && cursor <= n.t_end : Math.abs(cursor - n.t) <= tolMs;
}

/** The Material Symbol per note kind (visual spec §6). */
export const KIND_ICON: Record<string, SymbolName> = { mark: "flag", note: "edit", capture: "radio_button_checked" };

/** Quick tags offered on every note (spec §5). */
export const QUICK_TAGS = ["issue", "fault", "noise", "driving", "test"] as const;
