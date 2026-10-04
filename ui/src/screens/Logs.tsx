import { useState } from "react";
import { useSessions } from "../api/useSessions";
import { Replay } from "../components/replay/Replay";
import { SessionList } from "../components/replay/SessionList";
import "../replay.css";
import { useApp } from "../state/app";
import { useNow } from "../state/useNow";

/** The Logs tab (ADR-0009): the session browser, and a session's map replay. */
export function Logs() {
  const { snap, prefs } = useApp();
  const [open, setOpen] = useState<string | null>(null);
  const now = useNow(30_000);
  // Re-list when a recording starts or stops (a new session appears / gets its end).
  const { sessions, error, reload } = useSessions(snap?.recording?.session ?? "");

  if (open) {
    return <Replay id={open} onBack={() => { setOpen(null); reload(); }} onDeleted={() => { setOpen(null); reload(); }} />;
  }
  return (
    <div className="stack logs">
      <div className="screen-head"><h2>Logs</h2><span className="sub">· recorded sessions</span></div>
      {error && !sessions ? <p className="muted">Could not load sessions: {error}</p> : null}
      {!sessions && !error ? <p className="muted small">Loading sessions…</p> : null}
      {sessions ? (
        <SessionList sessions={sessions} recording={snap?.recording} nowS={snap?.ts ?? now / 1000}
          units={prefs.units} onOpen={setOpen} />
      ) : null}
    </div>
  );
}
