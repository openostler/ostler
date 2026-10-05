import { formatClock, SKIP_MS, SPEEDS, usePlayback } from "../../state/playback";

/** A note on the scrubber: a tick (point) or a span (range); tapping it seeks there. */
export type TransportTick = { id: string; t: number; t_end?: number | null; label: string };

/** The replay transport: play/pause, ±10 s, speed, and an accessible scrubber with
 * start/current/end clock times, plus optional note ticks. Pinned above the tab bar —
 * app-wide as GlobalTransport while a session is replayed (ADR-0010). */
export function Transport({ offset, follow, onFollow, ticks }: {
  /** utc − session ms (null: show session time). */
  offset: number | null;
  /** Shown only for a session that is recording now. */
  follow?: boolean;
  onFollow?: (on: boolean) => void;
  ticks?: readonly TransportTick[];
}) {
  const p = usePlayback();
  const now = formatClock(p.time, offset);
  const span = Math.max(p.end - p.start, 1);
  const pct = (ms: number) => `${Math.min(100, Math.max(0, ((ms - p.start) / span) * 100))}%`;
  const range = (
    <input type="range" className="replay-range" aria-label="Playback position" aria-valuetext={now}
      min={p.start} max={Math.max(p.end, p.start + 1)} step="any" value={p.time}
      disabled={p.end <= p.start}
      onChange={(e) => p.seek(Number(e.target.value))} />
  );
  return (
    <div className="replay-transport" role="group" aria-label="Playback">
      <div className="replay-scrub">
        <span className="replay-clock small muted" data-testid="clock-start">{formatClock(p.start, offset)}</span>
        {ticks ? (
          <div className="replay-rangewrap">
            {range}
            <div className="replay-ticks" role="group" aria-label="Notes">
              {ticks.map((n) => (
                <button key={n.id} type="button" className={`replay-tick${n.t_end != null ? " range" : ""}`}
                  style={{ left: pct(n.t), ...(n.t_end != null ? { width: `calc(${pct(n.t_end)} - ${pct(n.t)})` } : {}) }}
                  aria-label={`Note at ${formatClock(n.t, offset)}: ${n.label}`} title={n.label}
                  onClick={() => p.seek(n.t)} />
              ))}
            </div>
          </div>
        ) : range}
        <span className="replay-clock small muted" data-testid="clock-end">{formatClock(p.end, offset)}</span>
      </div>
      <div className="replay-buttons">
        <button className="rchip" aria-label="Back 10 seconds" onClick={() => p.skip(-SKIP_MS)}>⏪</button>
        <button className="rchip replay-play" aria-label="Play" aria-pressed={p.playing} onClick={p.toggle}>
          <span aria-hidden="true">{p.playing ? "❚❚" : "▶"}</span>
        </button>
        <button className="rchip" aria-label="Forward 10 seconds" onClick={() => p.skip(SKIP_MS)}>⏩</button>
        <span className="replay-now" data-testid="clock-now" aria-live="off">{now}</span>
        <div className="replay-speeds" role="group" aria-label="Playback speed">
          {SPEEDS.map((s) => (
            <button key={s} className="rchip" aria-pressed={p.speed === s} onClick={() => p.setSpeed(s)}>{s}×</button>
          ))}
        </div>
        {onFollow ? (
          <button className="rchip replay-follow" aria-pressed={!!follow} onClick={() => onFollow(!follow)}>Follow live</button>
        ) : null}
      </div>
    </div>
  );
}
