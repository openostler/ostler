// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { STATUS_WORD, type Status } from "../lib/catalog";

const ICON: Record<Status, string> = { verified: "✓", candidate: "◆", sniff: "○", untranscribed: "◌" };

/** THE item-status chip (ADR-0008): icon + word, never colour alone. Callers show it in
 * Experimental mode only — Stable hides every status chip. */
export function StatusTag({ status }: { status: string }) {
  const s = (status in ICON ? status : "sniff") as Status;
  return (
    <span className={`stag ${s}`} data-status={s}>
      <span className="si" aria-hidden="true">{ICON[s]}</span>
      {STATUS_WORD[s]}
    </span>
  );
}
