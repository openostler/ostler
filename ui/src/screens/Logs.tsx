import { useState } from "react";
import { Replay } from "../components/replay/Replay";
import { SessionBrowser } from "../components/replay/SessionBrowser";
import { EMPTY_VIEW, type BrowserView } from "../components/replay/sessionFormat";
import "../replay.css";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { useNow } from "../state/useNow";

/** The Logs tab (ADR-0009/0010, specs/2026-10-06-logs-at-scale-design.md §5): the session
 * browser; opening a session enters the app-wide replay (every tab then replays it), and this
 * tab shows its map, chart and notes. The browser's search, filters and scrubber position live
 * here, so they survive a replay; the browser itself remounts on the way back, which re-lists
 * (a session may have been renamed, deleted, or grown while open). */
export function Logs() {
  const { snap, prefs } = useApp();
  const replay = useReplay();
  const now = useNow(30_000);
  const [view, setView] = useState<BrowserView>(EMPTY_VIEW);

  if (replay.active) {
    return <Replay onDeleted={() => replay.exit()} />;
  }
  return (
    <div className="stack logs">
      <div className="screen-head"><h2>Logs</h2><span className="sub">· recorded sessions</span></div>
      {/* re-list when a recording starts or stops (a new session appears / gets its end) */}
      <SessionBrowser recording={snap?.recording} nowS={snap?.ts ?? now / 1000} units={prefs.units}
        onOpen={replay.enter} refreshKey={snap?.recording?.session ?? ""} view={view} onView={setView} />
    </div>
  );
}
