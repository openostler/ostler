import { formatClock } from "../state/playback";
import { useReplay } from "../state/replay";
import { activeNote } from "../state/replayState";

/** The amber strip shown instead of the Experimental strip while a session is replayed
 * (ADR-0010): "REPLAY · <date time> · ⏱ <cursor clock> · [Exit to live]", plus a chip with
 * the note the cursor is passing. Exit is always visible — even while loading or on error. */
export function ReplayBanner() {
  const r = useReplay();
  if (!r.active) return null;
  const start = r.session ? new Date(r.session.start_utc) : null;
  const when = start
    ? `${start.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })} ${start.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}`
    : null;
  const note = activeNote(r.notes, r.t);
  return (
    <div className="replaybanner" role="region" aria-label="Replay">
      <span className="replaybanner-tag">REPLAY</span>
      {r.error ? <span className="replaybanner-txt">Could not load this session: {r.error}</span>
        : r.loading ? <span className="replaybanner-txt">Loading session…</span>
          : (
            <>
              {when ? <span className="replaybanner-txt">· {when}</span> : null}
              <span className="replaybanner-txt replaybanner-clock" data-testid="replay-clock">· <span aria-hidden="true">⏱</span> {formatClock(r.t, r.offset)}</span>
              {note ? <span className="replaybanner-note" data-note={note.id} title={note.text}>⚑ {note.text || note.tags.join(", ") || note.kind}</span> : null}
            </>
          )}
      <button className="replaybanner-exit" onClick={r.exit}>Exit to live</button>
    </div>
  );
}
