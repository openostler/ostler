// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState, type ReactNode } from "react";
import type { GpsFix } from "../api/schemas";
import { useLiveSession } from "../api/useSessions";
import { AnalysisView } from "../components/replay/AnalysisView";
import { BackToSessions, ReplayHeader } from "../components/replay/Replay";
import type { BBox, Cursor } from "../components/replay/trace";
import { TraceMap } from "../components/replay/TraceMap";
import "../replay.css";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/** Half-size (degrees) of the box the GPS-only map frames around the live position. */
const LIVE_BOX_DEG = 0.01;

/** The live marker from a GPS fix (null without a position). */
function gpsCursor(gps: GpsFix | null | undefined): Cursor | null {
  if (!gps?.fix || gps.lat == null || gps.lon == null) return null;
  return { lon: gps.lon, lat: gps.lat, heading: gps.heading };
}

/**
 * The Analysis tab (spec §7): the whole analysis view (map, legend, picker, chart, G-G,
 * notes). In replay it follows the global cursor under the session header; live it shows the
 * session being recorded, re-fetched every 5 s with the cursor pinned to the newest sample
 * and the marker on the live GPS fix. Without a recording it shows the live position, or an
 * empty state pointing at Rewind.
 */
export function Analysis() {
  const replay = useReplay();
  return (
    <div className="replay analysis stack">
      {replay.active ? <ReplayAnalysis /> : <LiveAnalysis />}
    </div>
  );
}

function ReplayAnalysis() {
  const r = useReplay();
  const { goTo } = useApp();
  if (!r.session || !r.data) {
    return (
      <>
        <BackToSessions />
        <p className={r.error ? "muted" : "muted small"}>{r.error ? `Could not load this session: ${r.error}` : "Loading session…"}</p>
      </>
    );
  }
  return (
    <div className="stack" data-session={r.session.id} key={r.session.id}>
      <ReplayHeader meta={r.session} data={r.data} onDeleted={() => { r.exit(); goTo("logs"); }} />
      <AnalysisView data={r.data} meta={r.session} cursorT={r.t} onSeek={r.seek} />
    </div>
  );
}

function LiveHead({ children }: { children?: ReactNode }) {
  return (
    <div className="screen-head analysis-head">
      <h2>Analysis</h2>
      {children}
    </div>
  );
}

function LiveAnalysis() {
  const { snap } = useApp();
  const rec = snap?.recording ?? null;
  const recording = !!rec && (rec.state == null || rec.state === "recording" || rec.state === "paused");
  const live = useLiveSession(recording ? rec.session : null);
  const cursor = gpsCursor(snap?.gps);

  if (recording) {
    const chip = <span className="analysis-live" data-testid="live-chip"><span className="analysis-live-dot" aria-hidden="true" />Live</span>;
    if (!live.meta || !live.data) {
      return (
        <>
          <LiveHead>{chip}</LiveHead>
          <p className="muted small">{live.error ? `Could not load the recording: ${live.error}` : "Loading the recording…"}</p>
        </>
      );
    }
    const newest = live.data.t[live.data.t.length - 1] ?? 0;
    return (
      <>
        <LiveHead>
          {chip}
          {rec.state === "paused" ? <span className="sub">· paused — car disconnected</span> : <span className="sub">· recording now</span>}
        </LiveHead>
        <div data-session={live.meta.id}>
          <AnalysisView key={live.meta.id} data={live.data} meta={live.meta} cursorT={newest}
            live={{ cursor, signals: snap?.signals ?? {}, gpsSpeed: snap?.gps?.speed_kmh ?? null }} />
        </div>
      </>
    );
  }

  if (cursor) return <GpsOnly cursor={cursor} />;

  return (
    <>
      <LiveHead />
      <div className="card analysis-empty">
        <h3>Nothing to show yet</h3>
        <p className="muted small">
          No recording and no GPS fix. Use <b>Rewind</b> in the header to open the latest log, or pick one in Logs.
        </p>
      </div>
    </>
  );
}

/** Live position on the map, no recording yet. The map is framed once around the first fix;
 * the marker then follows. */
function GpsOnly({ cursor }: { cursor: Cursor }) {
  const [bbox] = useState<BBox>(() => [cursor.lon - LIVE_BOX_DEG, cursor.lat - LIVE_BOX_DEG, cursor.lon + LIVE_BOX_DEG, cursor.lat + LIVE_BOX_DEG]);
  return (
    <>
      <LiveHead />
      <div className="card replay-mapcard">
        <TraceMap a={null} b={null} bbox={bbox} cursor={cursor} />
      </div>
      <p className="muted small analysis-hint">Recording starts when the car connects.</p>
    </>
  );
}
