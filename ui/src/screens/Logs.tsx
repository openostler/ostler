// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { SessionBrowser } from "../components/replay/SessionBrowser";
import { EMPTY_VIEW, type BrowserView } from "../components/replay/sessionFormat";
import { parseUtc } from "../lib/time";
import "../replay.css";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { useNow } from "../state/useNow";

/** The Logs tab (ADR-0009/0010, specs/2026-10-06-logs-at-scale-design.md §5, replay spec §7):
 * the session browser only. Opening a session enters the app-wide replay and switches to the
 * Analysis tab, which shows its map, chart and notes. The browser's search, filters and
 * scrubber position live here, so they survive a replay while this tab stays mounted. */
export function Logs() {
  const { snap, prefs, goTo } = useApp();
  const replay = useReplay();
  const now = useNow(30_000);
  const [view, setView] = useState<BrowserView>(EMPTY_VIEW);
  // The drive in progress opens LIVE on Analysis (Rewind is how you replay it); any other
  // session enters replay there.
  const open = (id: string) => {
    if (id !== snap?.recording?.session) replay.enter(id);
    goTo("logs.analysis");
  };
  return (
    <div className="stack logs">
      <div className="screen-head"><h2>Logs</h2><span className="sub">· recorded sessions</span></div>
      {/* re-list when a recording starts or stops (a new session appears / gets its end) */}
      <SessionBrowser recording={snap?.recording} nowS={(parseUtc(snap?.ts_utc) ?? now) / 1000} units={prefs.units}
        onOpen={open} refreshKey={snap?.recording?.session ?? ""} view={view} onView={setView} />
    </div>
  );
}
