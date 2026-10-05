import { useMemo, useState } from "react";
import type { Note } from "../api/schemas";
import { useFlagOptions, type Flag } from "../lib/flags";
import { noteAt } from "../lib/notes";
import { useSessionFlags } from "../state/flags";
import { useReplay } from "../state/replay";
import { activeNote, NOTE_SHOW_MS } from "../state/replayState";
import { FlagSheet, SEVERITY, type FlagSheetItem } from "./FlagSheet";
import { Transport, type TransportTick } from "./replay/Transport";

const NO_NOTES: readonly Note[] = [];
const noteLabel = (n: Note) => n.text || n.tags.join(", ") || n.kind;

/** The flag the cursor is on: inside a range flag, or within NOTE_SHOW_MS after a point flag
 * (the same window a point note gets). The latest-starting one wins. */
export function activeFlag(flags: readonly Flag[], t: number): Flag | null {
  let best: Flag | null = null;
  for (const f of flags) {
    const on = f.t_end != null ? noteAt(f, t) : t >= f.t && t <= f.t + NOTE_SHOW_MS;
    if (on && (!best || f.t >= best.t)) best = f;
  }
  return best;
}

/** The app-wide replay transport (ADR-0010): a bar above the tab bar on every tab while a
 * session is open — play/pause, ±10 s, 1–8× and a scrubber with the session's note ticks
 * (accent) and automatic flags (warn/alarm; range flags as short bars) — tap one to seek to it.
 * The note or flag the cursor is passing (and load errors) float just above the scrubber, drawn
 * over the page so nothing shifts; tapping that chip opens the flag sheet (spec §8). While the
 * session is still recording, "● Latest" pins the cursor to the newest sample. Rendered only by <App>. */
export function GlobalTransport() {
  const r = useReplay();
  const opts = useFlagOptions();
  const flags = useSessionFlags(r.data, r.session?.modules ?? []).visible;
  const [open, setOpen] = useState<FlagSheetItem | null>(null);
  const notes = opts.manual ? r.notes : NO_NOTES;
  const ticks = useMemo<TransportTick[]>(() => [
    ...notes.map((n): TransportTick => ({ id: n.id, t: n.t, t_end: n.t_end ?? null, label: noteLabel(n), tone: "note" })),
    ...flags.map((f): TransportTick => ({ id: f.id, t: f.t, t_end: f.t_end, label: f.label, tone: f.severity })),
  ], [notes, flags]);
  if (!r.active) return null;

  const note = r.data ? activeNote(notes, r.t) : null;
  const flag = r.data ? activeFlag(flags, r.t) : null;
  // a note starting at or after the flag is the more specific thing to show
  const item: FlagSheetItem | null = note && (!flag || note.t >= flag.t) ? { note } : flag ? { flag } : null;
  const chip = item == null ? null : "note" in item ? (
    <button type="button" className="gnote gnote-btn" data-note={item.note.id} title={item.note.text}
      onClick={() => setOpen(item)}>⚑ {noteLabel(item.note)}</button>
  ) : (
    <button type="button" className={`gnote gnote-btn gnote-${item.flag.severity}`} data-flag={item.flag.id}
      title={item.flag.label} aria-label={`${SEVERITY[item.flag.severity].word}: ${item.flag.label}`}
      onClick={() => setOpen(item)}>
      <span aria-hidden="true">{SEVERITY[item.flag.severity].icon} </span>{item.flag.label}
    </button>
  );
  const overlay = r.error ? <span className="gnote gnote-err" role="alert">Could not load this session: {r.error}</span>
    : r.loading || !r.data ? <span className="gnote" role="status">Loading session…</span>
      : chip ? <span className="gnote-slot" role="status">{chip}</span> : null;
  const following = r.session?.recording ? { follow: r.follow, onFollow: () => r.setFollow(true) } : {};
  return (
    <div className="gtransport" data-testid="global-transport">
      {overlay ? <div className="gnote-layer" aria-live="polite">{overlay}</div> : null}
      {r.playback && r.data ? <Transport offset={r.offset} ticks={ticks} {...following} /> : null}
      {open ? <FlagSheet item={open} onClose={() => setOpen(null)} /> : null}
    </div>
  );
}
