import { connOf, pillFor } from "../lib/connection";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/** The persistent connection indicator in the header; tapping it opens the
 * ConnectionSheet. From snap.conn, or the legacy snap.status when conn is absent.
 * While a session is replayed it reads "Replay" (amber) and opens nothing. */
export function ConnectionPill() {
  const { snap, linkUp, openConnection } = useApp();
  const { active: replaying } = useReplay();
  const [cls, label] = pillFor(connOf(snap), linkUp);
  if (replaying) {
    return (
      <span className="pill pill-replay" aria-label="Replay — read only">
        <span className="pdot yellow" />
        <span className="pill-word">Replay</span>
      </span>
    );
  }
  return (
    <button className="pill" aria-haspopup="dialog" aria-label={label} onClick={openConnection}>
      <span className={`pdot ${cls}`} />
      <span aria-live="polite" className="pill-word">{label}</span>
    </button>
  );
}
