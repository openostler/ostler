// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef, useState } from "react";
import { Sheet } from "../components/Sheet";
import { Icon } from "../icons/Icon";
import type { DriveMenuRow, DriveMenuRowId } from "./driveMenu";

/**
 * The Drive menu (shell input spec §6): a `short_list` sheet opened by `ok` (or a long `back`)
 * in Drive mode, the first row focused. Touch and the D-pad share one selected state: a first
 * tap selects a row, a second activates it (teardown §5.6); `ok` activates the focused row.
 */
export function DriveMenu({ rows, onPick, onClose }: {
  rows: DriveMenuRow[]; onPick: (id: DriveMenuRowId) => void; onClose: () => void;
}) {
  const first = useRef<HTMLButtonElement>(null);
  const [armed, setArmed] = useState<DriveMenuRowId | null>(null);
  useEffect(() => { first.current?.focus(); }, []);
  return (
    <Sheet title="Drive menu" onClose={onClose} className="drive-menu">
      <ul className="dm-list" aria-label="Drive menu">
        {rows.map((r, i) => (
          <li key={r.id}>
            <button type="button" ref={i === 0 ? first : undefined} className="dm-list-row" data-focus="" data-row={r.id}
              data-armed={armed === r.id ? "" : undefined}
              onClick={(e) => {
                // a pointer's first tap selects; keyboard (detail 0) and a second tap activate
                if (e.detail > 0 && armed !== r.id) {
                  setArmed(r.id);
                  return;
                }
                onPick(r.id);
              }}>
              <Icon name={r.icon} size={24} />
              <span className="dm-list-name">{r.label}</span>
              {r.state ? <span className="dm-list-state">{r.state}</span> : null}
            </button>
          </li>
        ))}
      </ul>
    </Sheet>
  );
}
