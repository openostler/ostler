// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { RewindButton } from "../components/RewindButton";
import { Analysis } from "../screens/Analysis";
import { Logs } from "../screens/Logs";
import { useShell } from "../shell/context";
import { viewOf } from "../shell/routes";

/**
 * Logs (UI spec §3.4): the session browser and, as the session detail, Analysis (live, or the
 * replayed session). Rewind moved here from the header. Replay itself stays app-wide
 * (ADR-0010): the transport follows the user to every destination.
 */
export function LogsDestination() {
  const { nav } = useShell();
  const analysis = viewOf(nav.route) === "analysis";
  return (
    <div className="logsdest stack">
      <div className="subnav">
        <nav className="seg" aria-label="Logs views">
          <button aria-current={analysis ? undefined : "page"} onClick={() => nav.open("logs")}>Sessions</button>
          <button aria-current={analysis ? "page" : undefined} onClick={() => nav.open("logs.analysis")}>Analysis</button>
        </nav>
        <RewindButton />
      </div>
      {analysis ? <Analysis /> : <Logs />}
    </div>
  );
}
