// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { SessionMeta } from "../api/schemas";
import { formatDuration, rowDate, sessionTitle } from "../components/replay/sessionFormat";
import { Icon } from "../icons/Icon";
import { convertUnit } from "../lib/format";
import { VehicleCard } from "../screens/Drive";
import { useShell } from "../shell/context";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/**
 * Home (UI spec §3.4): zero-layer cards. The vehicle card holds today's Drive view (the
 * health line and the pack's tiles, the role tiles of §5.4 until the manifest arrives in
 * U3); a large Drive button opens Drive mode; the last trip opens Logs; on the phone the
 * 12 V reading moves here from the strip (§3.2). On HU-wide the always-on vehicle pane
 * carries the vehicle card, so Home leaves it out.
 */
export function Home() {
  const { layout, drive, vehicle } = useShell();
  return (
    <div className="home stack">
      <div className="screen-head"><h2>Home</h2><span className="sub">· {vehicle.name}</span></div>
      <button className="btn accent drive-btn" onClick={drive.open}>
        <Icon name="speed" size={32} /><span>Drive</span>
      </button>
      {layout === "huwide" ? null : <VehicleCard />}
      <div className="home-cards">
        <LastTrip />
        {layout === "phone" ? <BatteryCard /> : null}
      </div>
    </div>
  );
}

const LOOKUP = 5;

/** The newest finished session, from /sessions (absent while there is none). */
function LastTrip() {
  const { nav, format } = useShell();
  const { prefs } = useApp();
  const replay = useReplay();
  const [last, setLast] = useState<SessionMeta | null | undefined>(undefined);
  useEffect(() => {
    let alive = true;
    api.sessions({ limit: LOOKUP }).then(
      (r) => alive && setLast(r.sessions.find((s) => !s.recording) ?? null),
      () => alive && setLast(null),
    );
    return () => { alive = false; };
  }, [replay.active]);
  if (!last) return null;
  const dist = convertUnit(last.distance_km, "km", prefs.units);
  return (
    <button className="card home-card" onClick={() => nav.open("logs")}>
      <span className="kicker"><Icon name="history" size={18} /> Last trip</span>
      <span className="home-card-title">{sessionTitle(last)}</span>
      <span className="small muted">
        {rowDate(last)} · {formatDuration(last.duration_s)}
        {last.distance_km > 0 ? ` · ${format.quantity(dist.v, dist.unit, 1)}` : ""}
      </span>
    </button>
  );
}

/** The car battery on the phone, where the strip has no 12 V chip. */
function BatteryCard() {
  const { snap } = useApp();
  const { format } = useShell();
  if (typeof snap?.battery_v !== "number") return null;
  return (
    <div className="card home-card" role="group" aria-label="Car battery">
      <span className="kicker"><Icon name="battery_full" size={18} /> Car battery</span>
      <span className="home-card-title">{format.quantity(snap.battery_v, "V", 1)}</span>
    </div>
  );
}
