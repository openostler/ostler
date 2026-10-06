// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { summarize } from "../lib/health";
import { useApp } from "../state/app";

const ICON = { ok: "✓", warn: "!", alarm: "!", offline: "…" } as const;

/** One line that answers "is the car OK?". Tapping it goes to the cause. */
export function HealthStrip() {
  const { snap, fields, goTo } = useApp();
  const h = summarize(snap, fields);
  if (h.level === "offline") return null; // the status gate covers this case
  const target = h.current || h.logged ? "faults" : h.outOfRange.length ? "inputs" : null;
  return (
    <button className={`health ${h.level}`} onClick={() => target && goTo(target)} disabled={!target}
      aria-label={`Vehicle status: ${h.headline}`}>
      <span className="hi" aria-hidden="true">{ICON[h.level]}</span>
      <span>{h.headline}</span>
      {target ? <span className="rest">View ›</span> : null}
    </button>
  );
}
