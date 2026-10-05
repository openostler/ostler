import { useEffect, useRef } from "react";
import type { SessionMeta } from "../../api/schemas";
import { canonicalModule, moduleName } from "../../layout";
import { convertUnit, fmt, type Units } from "../../lib/format";
import { formatDuration, groupByYearMonth, rowDate, sessionPlace, sessionTitle } from "./sessionFormat";

/**
 * The paged session list (spec §5): sticky year → month headers, one row per session (title =
 * name, else place, else "Untitled session"; then place, date and time, duration, distance,
 * modules by display name, notes and a demo chip). The end of the list loads the next page
 * when it scrolls into view (IntersectionObserver), with a "Load more" button as the fallback.
 */
export function SessionList({ sessions, units, onOpen, hasMore, loadingMore, onMore }: {
  sessions: SessionMeta[];
  units: Units;
  onOpen: (id: string) => void;
  hasMore: boolean;
  loadingMore?: boolean;
  onMore: () => void;
}) {
  const years = groupByYearMonth(sessions);
  return (
    <div className="logs-list">
      {years.map((y) => (
        <section key={y.year} className="logs-year" aria-label={String(y.year)}>
          <h3 className="logs-year-head">{y.year}</h3>
          {y.months.map((m) => (
            <section key={m.key} className="logs-month" data-month={m.key} aria-label={`${m.label} ${y.year}`}>
              <h4 className="logs-month-head kicker">{m.label}</h4>
              <ul className="replay-rows">
                {m.sessions.map((s) => <SessionRow key={s.id} s={s} units={units} onOpen={onOpen} />)}
              </ul>
            </section>
          ))}
        </section>
      ))}
      {hasMore ? <MoreSentinel busy={!!loadingMore} onMore={onMore} /> : null}
    </div>
  );
}

function MoreSentinel({ busy, onMore }: { busy: boolean; onMore: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const cb = useRef(onMore);
  useEffect(() => { cb.current = onMore; });
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) cb.current();
    }, { rootMargin: "400px 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className="logs-more">
      <button type="button" className="btn" disabled={busy} onClick={onMore}>{busy ? "Loading…" : "Load more"}</button>
    </div>
  );
}

function SessionRow({ s, units, onOpen }: { s: SessionMeta; units: Units; onOpen: (id: string) => void }) {
  const dist = convertUnit(s.distance_km, "km", units);
  const place = sessionPlace(s);
  const notes = s.note_count ?? 0;
  return (
    <li>
      <button className="replay-row" data-session={s.id} onClick={() => onOpen(s.id)}>
        <span className="replay-row-main">
          <b className="replay-row-title">{sessionTitle(s)}</b>
          {s.synthetic ? <span className="replay-chip-demo">demo</span> : null}
          {s.recording ? <span className="replay-chip-live">recording</span> : null}
        </span>
        {place ? <span className="replay-row-place small">{place}</span> : null}
        <span className="replay-row-sub small muted">
          <span>{rowDate(s)}</span>
          <span>{formatDuration(s.duration_s)}</span>
          {s.has_gps ? <span>{fmt(dist.v, 1)} {dist.unit}</span> : null}
          {s.modules.length ? <span>{[...new Set(s.modules.map(canonicalModule))].map(moduleName).join(", ")}</span> : null}
          {notes > 0 ? <span>{notes} note{notes === 1 ? "" : "s"}</span> : null}
        </span>
      </button>
    </li>
  );
}
