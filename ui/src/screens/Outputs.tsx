// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { ConnectionNotice } from "../components/ConnectionNotice";
import { CoverageBar } from "../components/CoverageBar";
import { ItemCard } from "../components/ItemCard";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import type { ReactNode } from "react";
import type { CatalogItem } from "../api/schemas";
import { pageOf, STABLE_EMPTY, visibleGroups } from "../lib/catalog";
import { useApp } from "../state/app";
import { formatClock } from "../state/playback";
import { useReplay, type Replay } from "../state/replay";
import { Icon } from "../icons/Icon";

/** Replay: the item whose action is the latched test at the cursor is highlighted, and each
 * item shows when one of its actions last ran ("ran at HH:MM:SS ✓/✗", from `command` events). */
function ReplayItem({ item, replay, children }: { item: CatalogItem; replay: Replay; children: ReactNode }) {
  const acts = item.actions.flatMap((a) => [a.action, ...(a.stop ? [a.stop] : [])]);
  const running = !!replay.state.active_test && acts.includes(replay.state.active_test.action);
  const last = acts.map((a) => replay.state.lastCommand[a]).filter((c) => !!c).sort((a, b) => b.t - a.t)[0];
  return (
    <div className={`replay-item${running ? " replay-running" : ""}`} data-replay-item={item.id} data-running={running || undefined}>
      {children}
      {running ? <div className="replay-itemnote small"><span className="pdot yellow" aria-hidden="true" /> running at this moment</div> : null}
      {last ? (
        <div className={`replay-itemnote small${last.ok ? "" : " bad"}`}>
          ran at {formatClock(last.t, replay.offset)} <Icon name={last.ok ? "check" : "close"} size="1.1em" className="icon-inline" />{last.ok ? "ok" : "failed"}
          {!last.ok && last.error ? <span className="dis"> · {last.error}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

/** Simple on/off/pulse actuator tests (catalog page "outputs"). Multi-step and latched
 * procedures live under Utilities. Every action confirms per the command registry. */
export function Outputs() {
  const { snap, catalog, experimental } = useApp();
  const replay = useReplay();
  const page = pageOf(catalog, "outputs");
  const groups = visibleGroups(page, experimental);
  const connected = snap?.status === "connected";

  return (
    <>
      <ScreenHead title="Outputs" />
      <ConnectionNotice />
      {experimental && page ? <CoverageBar coverage={page.coverage} label="Outputs coverage" /> : null}
      {!connected ? <StatusGate withNotice /> : null}
      {!catalog ? <div className="empty">Loading…</div> : !groups.length ? (
        <div className="empty"><div className="pretty">{experimental ? "No output tests catalogued for this module yet." : STABLE_EMPTY}</div></div>
      ) : (
        <>
          <div className="card warn">
            <div style={{ fontWeight: 700 }}>Actuator tests drive real hardware</div>
            <div className="small pretty" style={{ marginTop: 2 }}>
              Vehicle stationary, handbrake on, nobody under the car. Each test pulses a moment — it does not latch on.
            </div>
          </div>
          {groups.map(({ group, items }) => (
            <section key={group.id}>
              <div className="kicker group-title">{group.title}</div>
              <div className="grid">
                {items.map((i) => (replay.active
                  ? <ReplayItem key={i.id} item={i} replay={replay}><ItemCard item={i} disabled /></ReplayItem>
                  : <ItemCard key={i.id} item={i} disabled={!connected} />))}
              </div>
            </section>
          ))}
        </>
      )}
    </>
  );
}
