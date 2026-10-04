import { connOf, pillFor } from "../lib/connection";
import { useApp } from "../state/app";

/** The persistent connection indicator in the header; tapping it opens the
 * ConnectionSheet. From snap.conn, or the legacy snap.status when conn is absent. */
export function ConnectionPill() {
  const { snap, linkUp, openConnection } = useApp();
  const [cls, label] = pillFor(connOf(snap), linkUp);
  return (
    <button className="pill" aria-haspopup="dialog" aria-label={label} onClick={openConnection}>
      <span className={`pdot ${cls}`} />
      <span aria-live="polite" className="pill-word">{label}</span>
    </button>
  );
}
