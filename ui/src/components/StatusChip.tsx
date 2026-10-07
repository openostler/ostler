// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Flag } from "../lib/format";
import { Icon, type SymbolName } from "../icons/Icon";

const ICON: Record<Flag["cls"], SymbolName | null> = { ok: null, exp: "diamond", lo: "arrow_drop_down", hi: "arrow_drop_up", sus: "help" };

/** Status as icon + word (never colour alone). Healthy values show nothing at all. */
export function StatusChip({ flag, showOk = false, compact = false }: { flag: Flag; showOk?: boolean; compact?: boolean }) {
  if (flag.cls === "ok" && !showOk) return null;
  const word = flag.cls === "exp" ? "UNVERIFIED" : flag.txt;
  // compact: an unverified mark on a small tile is the icon only (alarms always keep the word)
  if (compact && flag.cls === "exp") {
    return <span className="status exp compact" role="img" title="Unverified mapping" aria-label="unverified"><span className="si"><Icon name="diamond" size="1.1em" /></span></span>;
  }
  return (
    <span className={`status ${flag.cls}`}>
      {ICON[flag.cls] ? <span className="si" aria-hidden="true"><Icon name={ICON[flag.cls]!} size="1.1em" /></span> : null}
      {word}
    </span>
  );
}
