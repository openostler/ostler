import type { Recording, SessionMeta } from "../../api/schemas";
import { convertUnit, fmt, type Units } from "../../lib/format";
import { RecordingCard } from "../RecordingCard";
import { formatDuration, formatPos, groupByDay, startTime } from "./sessionFormat";

/** The session browser: the recording card (status, ⚑ Mark, Note…, Options), then sessions
 * grouped by local day. */
export function SessionList({ sessions, recording, nowS, units, onOpen }: {
  sessions: SessionMeta[];
  recording: Recording | null | undefined;
  /** Epoch seconds now (server snapshot time when known). */
  nowS: number;
  units: Units;
  onOpen: (id: string) => void;
}) {
  const groups = groupByDay(sessions);
  return (
    <div className="stack replay-sessions">
      <RecordingCard recording={recording} nowS={nowS} onOpen={onOpen} />
      {groups.length === 0 ? <p className="muted">No sessions yet. A session is recorded whenever the car is connected.</p> : null}
      {groups.map((g) => (
        <section key={g.day} className="replay-day" aria-label={g.label}>
          <h3 className="kicker">{g.label}</h3>
          <ul className="replay-rows">
            {g.sessions.map((s) => <SessionRow key={s.id} s={s} units={units} onOpen={onOpen} />)}
          </ul>
        </section>
      ))}
    </div>
  );
}

function SessionRow({ s, units, onOpen }: { s: SessionMeta; units: Units; onOpen: (id: string) => void }) {
  const dist = convertUnit(s.distance_km, "km", units);
  const top = s.max_speed_kmh != null ? convertUnit(s.max_speed_kmh, "km/h", units) : null;
  return (
    <li>
      <button className="replay-row" data-session={s.id} onClick={() => onOpen(s.id)}>
        <span className="replay-row-main">
          <b className="replay-row-time">{startTime(s)}</b>
          <span>{formatDuration(s.duration_s)}</span>
          {s.has_gps ? <span>{fmt(dist.v, 1)} {dist.unit}</span> : null}
          {top ? <span>max {fmt(top.v, 0)} {top.unit}</span> : null}
          {s.synthetic ? <span className="replay-chip-demo">demo</span> : null}
          {s.recording ? <span className="replay-chip-live">recording</span> : null}
        </span>
        <span className="replay-row-sub small muted">
          <span>{formatPos(s.start_pos)}</span>
          {s.modules.length ? <span>{s.modules.join(", ")}</span> : null}
        </span>
      </button>
    </li>
  );
}
