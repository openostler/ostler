// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { STATUS_WORD, type Status } from "../lib/catalog";
import { Icon, type SymbolName } from "../icons/Icon";

const ICON: Record<Status, SymbolName> = { verified: "check", candidate: "diamond", sniff: "radio_button_unchecked", untranscribed: "pending" };

/** THE item-status chip (ADR-0008): icon + word, never colour alone. Callers show it in
 * Experimental mode only — Stable hides every status chip. */
export function StatusTag({ status }: { status: string }) {
  const s = (status in ICON ? status : "sniff") as Status;
  return (
    <span className={`stag ${s}`} data-status={s}>
      <span className="si" aria-hidden="true"><Icon name={ICON[s]} size="1.1em" /></span>
      {STATUS_WORD[s]}
    </span>
  );
}
