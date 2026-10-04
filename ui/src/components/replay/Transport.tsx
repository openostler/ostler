import { formatClock, SKIP_MS, SPEEDS, usePlayback } from "../../state/playback";

/** The replay transport, pinned to the bottom of the Logs screen above the tabs:
 * play/pause, ±10 s, speed, and an accessible scrubber with start/current/end clock times. */
export function Transport({ offset, follow, onFollow }: {
  /** utc − session ms (null: show session time). */
  offset: number | null;
  /** Shown only for a session that is recording now. */
  follow?: boolean;
  onFollow?: (on: boolean) => void;
}) {
  const p = usePlayback();
  const now = formatClock(p.time, offset);
  return (
    <div className="replay-transport" role="group" aria-label="Playback">
      <div className="replay-scrub">
        <span className="replay-clock small muted" data-testid="clock-start">{formatClock(p.start, offset)}</span>
        <input type="range" className="replay-range" aria-label="Playback position" aria-valuetext={now}
          min={p.start} max={Math.max(p.end, p.start + 1)} step="any" value={p.time}
          disabled={p.end <= p.start}
          onChange={(e) => p.seek(Number(e.target.value))} />
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
