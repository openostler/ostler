import { useMemo } from "react";
import { useReplay } from "../state/replay";
import { Transport, type TransportTick } from "./replay/Transport";

/** The app-wide replay transport (ADR-0010): a bar above the tab bar on every tab while a
 * session is open — play/pause, ±10 s, 1–8× and a scrubber with the session's note ticks
 * (tap one to seek to it). Rendered only by <App>. */
export function GlobalTransport() {
  const r = useReplay();
  const ticks = useMemo<TransportTick[]>(
    () => r.notes.map((n) => ({ id: n.id, t: n.t, t_end: n.t_end ?? null, label: n.text || n.tags.join(", ") || n.kind })),
    [r.notes],
  );
  if (!r.active || !r.playback || !r.data) return null;
  return (
    <div className="gtransport" data-testid="global-transport">
      <Transport offset={r.offset} ticks={ticks} />
    </div>
  );
}
