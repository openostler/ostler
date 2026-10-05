/**
 * The Logs browser (specs/2026-10-06-logs-at-scale-design.md §5): the recording card, search
 * and filter chips, the "This year" heatmap, the paged list with sticky year/month headers,
 * the right-edge month scrubber and the place-name attribution.
 *
 * Scrubber jumps set a `before` anchor (`monthEndCursor`: the end of that month) and keep the
 * filters, so the list then pages on into older months; "Back to newest" drops the anchor.
 * The heatmap sets `from` = `to` = the tapped day (a filter, shown on the Dates chip).
 */
import { useState } from "react";
import type { Recording } from "../../api/schemas";
import { filtersActive, useSessionHistogram, useSessionPages, type SessionFilters as Filters } from "../../api/useSessions";
import type { Units } from "../../lib/format";
import { RecordingCard } from "../RecordingCard";
import { MonthScrubber } from "./MonthScrubber";
import { SessionFilters } from "./SessionFilters";
import { SessionList } from "./SessionList";
import { ATTRIBUTION, EMPTY_VIEW, localMonth, monthEndCursor, monthLabel, type BrowserView } from "./sessionFormat";
import { YearHeatmap } from "./YearHeatmap";




export function SessionBrowser({ recording, nowS, units, onOpen, refreshKey = "", view: shown, onView }: {
  recording: Recording | null | undefined;
  /** Epoch seconds now (server snapshot time when known). */
  nowS: number;
  units: Units;
  onOpen: (id: string) => void;
  /** A change re-lists from the first page (a recording starting/stopping, replay exit). */
  refreshKey?: string;
  /** Controlled view (filters + scrubber anchor); uncontrolled when omitted. */
  view?: BrowserView;
  onView?: (v: BrowserView) => void;
}) {
  const [own, setOwn] = useState<BrowserView>(EMPTY_VIEW);
  const view = shown ?? own;
  const setView = onView ?? setOwn;
  const { filters, anchor } = view;
  const setAnchor = (a: BrowserView["anchor"]) => setView({ filters, anchor: a });
  const [year] = useState(() => new Date().getFullYear());
  const pages = useSessionPages(filters, anchor?.cursor ?? null, refreshKey);
  const months = useSessionHistogram("month", undefined, refreshKey);
  const days = useSessionHistogram("day", year, refreshKey);

  const filtered = filtersActive(filters);
  const day = filters.from && filters.from === filters.to ? filters.from : null;
  const sessions = pages.sessions;
  const first = sessions?.[0];
  const current = anchor?.month ?? (first ? localMonth(new Date(first.start_utc)) : null);
  /** A new query starts from the newest session again. */
  const setF = (f: Filters) => setView({ filters: f, anchor: null });

  let body;
  if (!sessions && pages.error) body = <p className="muted">Could not load sessions: {pages.error}</p>;
  else if (!sessions) body = <p className="muted small">Loading sessions…</p>;
  else if (sessions.length === 0 && (filtered || anchor)) {
    body = (
      <div className="logs-empty card stack">
        <p className="muted">No sessions match{filters.q?.trim() ? ` “${filters.q.trim()}”` : ""}.</p>
        <button type="button" className="btn" onClick={() => setF({})}>Clear filters</button>
      </div>
    );
  } else if (sessions.length === 0) {
    body = <p className="muted logs-empty">No sessions yet. A session is recorded whenever the car is connected.</p>;
  } else {
    body = (
      <div className="logs-body">
        <SessionList sessions={sessions} units={units} onOpen={onOpen} hasMore={!!pages.next}
          loadingMore={pages.loadingMore} onMore={pages.loadMore} />
        {months ? (
          <MonthScrubber buckets={months.buckets} current={current}
            onJump={(m) => setAnchor({ month: m, cursor: monthEndCursor(m) })} />
        ) : null}
      </div>
    );
  }

  return (
    <div className="stack replay-sessions">
      <RecordingCard recording={recording} nowS={nowS} onOpen={onOpen} />
      <SessionFilters value={filters} onChange={setF} />
      <YearHeatmap year={year} hist={days} selected={day}
        onPick={(d) => setF(d === day ? { ...filters, from: undefined, to: undefined } : { ...filters, from: d, to: d })} />
      {anchor ? (
        <div className="logs-anchor small">
          <span className="muted">From {monthLabel(anchor.month)} back</span>
          <button type="button" className="rchip" onClick={() => setAnchor(null)}>Back to newest</button>
        </div>
      ) : null}
      {pages.error && sessions ? <p className="muted small">Could not load more sessions: {pages.error}</p> : null}
      <div aria-busy={pages.loading} className="logs-results">{body}</div>
      <p className="logs-attribution small muted">{ATTRIBUTION}</p>
    </div>
  );
}
