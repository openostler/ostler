import { useEffect, useRef } from "react";
import { useSessions } from "../api/useSessions";
import { Replay } from "../components/replay/Replay";
import { SessionList } from "../components/replay/SessionList";
import "../replay.css";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { useNow } from "../state/useNow";

/** The Logs tab (ADR-0009/0010): the session browser; opening a session enters the app-wide
 * replay (every tab then replays it), and this tab shows its map, chart and notes. */
export function Logs() {
  const { snap, prefs } = useApp();
  const replay = useReplay();
  const now = useNow(30_000);
  // Re-list when a recording starts or stops (a new session appears / gets its end).
  const { sessions, error, reload } = useSessions(snap?.recording?.session ?? "");
  // …and when replay exits (a session may have been deleted, or grown while open).
  const active = replay.active;
  const wasActive = useRef(active);
  useEffect(() => {
    if (wasActive.current && !active) reload();
    wasActive.current = active;
  }, [active, reload]);

  if (replay.active) {
    return <Replay onDeleted={() => { replay.exit(); reload(); }} />;
  }
  return (
    <div className="stack logs">
      <div className="screen-head"><h2>Logs</h2><span className="sub">· recorded sessions</span></div>
      {error && !sessions ? <p className="muted">Could not load sessions: {error}</p> : null}
      {!sessions && !error ? <p className="muted small">Loading sessions…</p> : null}
      {sessions ? (
        <SessionList sessions={sessions} recording={snap?.recording} nowS={snap?.ts ?? now / 1000}
          units={prefs.units} onOpen={replay.enter} />
      ) : null}
    </div>
  );
}
