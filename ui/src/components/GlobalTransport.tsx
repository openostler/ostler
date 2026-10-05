import { useMemo } from "react";
import { useReplay } from "../state/replay";
import { activeNote } from "../state/replayState";
import { Transport, type TransportTick } from "./replay/Transport";

/** The app-wide replay transport (ADR-0010): a bar above the tab bar on every tab while a
 * session is open — play/pause, ±10 s, 1–8× and a scrubber with the session's note ticks
 * (tap one to seek to it). The note the cursor is passing (and load errors) float just above
 * the scrubber, drawn over the page so nothing shifts. Rendered only by <App>. */
export function GlobalTransport() {
  const r = useReplay();
  const ticks = useMemo<TransportTick[]>(
    () => r.notes.map((n) => ({ id: n.id, t: n.t, t_end: n.t_end ?? null, label: n.text || n.tags.join(", ") || n.kind })),
    [r.notes],
  );
  if (!r.active) return null;
  const note = r.data ? activeNote(r.notes, r.t) : null;
  const overlay = r.error ? <span className="gnote gnote-err" role="alert">Could not load this session: {r.error}</span>
    : r.loading || !r.data ? <span className="gnote" role="status">Loading session…</span>
      : note ? (
        <span className="gnote" data-note={note.id} title={note.text} role="status">⚑ {note.text || note.tags.join(", ") || note.kind}</span>
      ) : null;
  return (
    <div className="gtransport" data-testid="global-transport">
      {overlay ? <div className="gnote-layer" aria-live="polite">{overlay}</div> : null}
      {r.playback && r.data ? <Transport offset={r.offset} ticks={ticks} /> : null}
    </div>
  );
}
