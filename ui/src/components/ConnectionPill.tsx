// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { connOf, pillFor } from "../lib/connection";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/** The persistent connection indicator in the header; tapping it opens the
 * ConnectionSheet. From snap.conn, or the legacy snap.status when conn is absent.
 * While a session is replayed it becomes the (flashing, amber) way back:
 * "Replay · Exit to live" — tapping it leaves the replay. */
export function ConnectionPill() {
  const { snap, linkUp, openConnection } = useApp();
  const { active: replaying, exit } = useReplay();
  const [cls, label] = pillFor(connOf(snap), linkUp);
  if (replaying) {
    return (
      <button className="pill pill-replay" aria-label="Replay — Exit to live" onClick={exit}>
        <span className="pdot yellow" />
        <span className="pill-word">Replay<span className="pill-exit"> · Exit to live</span></span>
      </button>
    );
  }
  return (
    <button className="pill" aria-haspopup="dialog" aria-label={label} onClick={openConnection}>
      <span className={`pdot ${cls}`} />
      <span aria-live="polite" className="pill-word">{label}</span>
    </button>
  );
}
