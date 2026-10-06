// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { connOf, isNotLive, pillFor } from "../lib/connection";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/** A compact, non-blocking strip on the module pages while the connection is not live
 * (lib/connection NOT_LIVE): the page stays usable, the button opens the ConnectionSheet.
 * Drive keeps the full StatusGate instead. Suppressed in replay (the banner says where you are). */
export function ConnectionNotice() {
  const { snap, linkUp, openConnection } = useApp();
  const { active: replaying } = useReplay();
  const conn = connOf(snap);
  if (replaying || !isNotLive(conn)) return null;
  const [dot] = pillFor(conn, linkUp);
  return (
    <div className="connnotice" role="status">
      <span className={`pdot ${dot}`} aria-hidden="true" />
      <span className="grow">No connection</span>
      <button className="connnotice-btn" onClick={openConnection}>Open connection</button>
    </div>
  );
}
