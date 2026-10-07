// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef } from "react";
import { Sheet } from "../components/Sheet";
import { Icon } from "../icons/Icon";
import { iconOr } from "./icon";
import type { Layout } from "./types";

/**
 * The mode list (drive-modes spec §6): a `short_list` of at most six modes, one level, the
 * rotation first, the current one ticked; one tap picks. Opened by a long press (600 ms) or a
 * long `ok` on the Drive-mode chip. "Edit modes…" joins it Parked only when the editor ships
 * (DM2); while Moving the row is absent, not greyed.
 */
export function ModeList({ modes, current, onPick, onClose }: {
  modes: Layout[]; current: string; onPick: (id: string) => void; onClose: () => void;
}) {
  const first = useRef<HTMLButtonElement>(null);
  useEffect(() => { first.current?.focus(); }, []);
  return (
    <Sheet title="Drive modes" onClose={onClose}>
      <ul className="dm-list" aria-label="Drive modes">
        {modes.map((m, i) => (
          <li key={m.id}>
            <button type="button" ref={m.id === current || (i === 0 && !modes.some((x) => x.id === current)) ? first : undefined}
              className="dm-list-row" aria-current={m.id === current ? "true" : undefined} onClick={() => onPick(m.id)}>
              <Icon name={iconOr(m.icon, "speed")} size={24} />
              <span className="dm-list-name" dir="auto">{m.name}</span>
              {m.id === current ? <span className="dm-list-tick"><Icon name="check" size={24} /></span> : null}
            </button>
          </li>
        ))}
      </ul>
    </Sheet>
  );
}
