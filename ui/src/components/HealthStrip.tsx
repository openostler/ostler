// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { summarize } from "../lib/health";
import type { RouteName } from "../shell/routes";
import { useApp } from "../state/app";
import { Icon, type SymbolName } from "../icons/Icon";

const ICON = { ok: "check", warn: "priority_high", alarm: "priority_high", offline: "more_horiz" } as const satisfies Record<string, SymbolName>;

/** One line that answers "is the car OK?". Tapping it goes to the cause in Diagnose. */
export function HealthStrip() {
  const { snap, fields, goTo } = useApp();
  const h = summarize(snap, fields);
  if (h.level === "offline") return null; // the status gate covers this case
  const target: RouteName | null = h.current || h.logged ? "diagnose.faults" : h.outOfRange.length ? "diagnose.live" : null;
  return (
    <button className={`health ${h.level}`} onClick={() => target && goTo(target)} disabled={!target}
      aria-label={`Vehicle status: ${h.headline}`}>
      <span className="hi" aria-hidden="true"><Icon name={ICON[h.level]} size={16} /></span>
      <span>{h.headline}</span>
      {target ? <span className="rest">View<Icon name="chevron_right" size="1.2em" className="icon-inline" /></span> : null}
    </button>
  );
}
