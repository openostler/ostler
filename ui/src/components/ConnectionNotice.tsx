import { connOf, isNotLive, pillFor } from "../lib/connection";
import { useApp } from "../state/app";

/** A compact, non-blocking strip on the module pages while the connection is not live
 * (lib/connection NOT_LIVE): the page stays usable, the button opens the ConnectionSheet.
 * Drive keeps the full StatusGate instead. */
export function ConnectionNotice() {
  const { snap, linkUp, openConnection } = useApp();
  const conn = connOf(snap);
  if (!isNotLive(conn)) return null;
  const [dot] = pillFor(conn, linkUp);
  return (
    <div className="connnotice" role="status">
      <span className={`pdot ${dot}`} aria-hidden="true" />
      <span className="grow">No connection</span>
      <button className="connnotice-btn" onClick={openConnection}>Open connection</button>
    </div>
  );
}
