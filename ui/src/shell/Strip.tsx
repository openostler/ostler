// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { MarkButton } from "../components/MarkButton";
import { Icon } from "../icons/Icon";
import type { ChipDescriptor, ChipOpen } from "./strip";

/**
 * The persistent status strip (UI spec §3.2): one row that never scrolls, drawn by the shell
 * from chip descriptors (shell/strip.ts). It is the page's banner landmark. Apps never
 * render inside it (app-model spec §5).
 */
export function Strip({ chips, onOpen }: { chips: ChipDescriptor[]; onOpen: (o: ChipOpen) => void }) {
  return (
    <header className="strip" aria-label="Status">
      {chips.map((c) => <StripChip key={c.id} c={c} onOpen={onOpen} />)}
    </header>
  );
}

function Face({ c }: { c: ChipDescriptor }) {
  return (
    <>
      {c.dot !== undefined ? <span className={`pdot ${c.dot}`} aria-hidden="true" />
        : c.icon ? <Icon name={c.icon} size={20} /> : null}
      <span className="schip-word" aria-live={c.id === "link" ? "polite" : undefined}>{c.word}</span>
      {c.note ? <span className="schip-note">{c.noteIcon ? <Icon name={c.noteIcon} size={16} /> : null}{c.note}</span> : null}
      {c.detail ? <span className="schip-detail">{c.detail}</span> : null}
    </>
  );
}

function StripChip({ c, onOpen }: { c: ChipDescriptor; onOpen: (o: ChipOpen) => void }) {
  const cls = `schip schip-${c.id} tone-${c.tone}${c.attention ? " attention" : ""}`;
  if (c.kind === "mark") return <div className="schip-slot schip-slot-mark"><MarkButton /></div>;
  if (c.kind === "status" || !c.open) {
    // not interactive: the visible text is hidden from assistive tech and the label read instead
    return (
      <span className={cls}>
        <span className="visually-hidden">{c.label}</span>
        <span className="schip-face" aria-hidden="true"><Face c={c} /></span>
      </span>
    );
  }
  const open = c.open;
  return (
    <button className={cls} aria-label={c.label} aria-haspopup={open === "faults" || open === "connection" ? "dialog" : undefined}
      onClick={() => onOpen(open)}>
      <Face c={c} />
    </button>
  );
}
