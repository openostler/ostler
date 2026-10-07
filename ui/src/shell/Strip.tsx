// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef } from "react";
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
  if (open === "drive_mode") return <ModeChip c={c} cls={cls} onOpen={onOpen} />;
  return (
    <button className={cls} aria-label={c.label} aria-haspopup={open === "faults" || open === "connection" ? "dialog" : undefined}
      onClick={() => onOpen(open)}>
      <Face c={c} />
    </button>
  );
}

/** ShellInput's long press (shell input spec §5): 600 ms held. */
export const LONG_PRESS_MS = 600;

/**
 * The Drive-mode chip (drive-modes spec §6): a tap (or a short Enter or Space) cycles the
 * rotation; a long press (600 ms, touch, mouse or a held Enter) opens the mode list. The
 * long press fires while held, so the release does not also cycle.
 */
function ModeChip({ c, cls, onOpen }: { c: ChipDescriptor; cls: string; onOpen: (o: ChipOpen) => void }) {
  const timer = useRef<number | undefined>(undefined);
  const fired = useRef(false);
  const keyDown = useRef(false);
  const since = useRef(0);
  useEffect(() => () => window.clearTimeout(timer.current), []);
  const long = () => {
    window.clearTimeout(timer.current);
    if (fired.current) return;
    fired.current = true;
    onOpen("drive_mode_list");
  };
  const start = () => {
    fired.current = false;
    since.current = performance.now();
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(long, LONG_PRESS_MS);
  };
  // a busy screen may run the release before the timer: the time held decides
  const cancel = () => {
    window.clearTimeout(timer.current);
    if (since.current && performance.now() - since.current >= LONG_PRESS_MS) long();
    since.current = 0;
  };
  return (
    <button className={cls} data-chip="drive_mode" aria-label={c.label} aria-haspopup="dialog"
      aria-description="Tap for the next mode, hold for the list"
      onPointerDown={(e) => { if (e.button === 0) start(); }}
      onPointerUp={cancel}
      onPointerLeave={() => { window.clearTimeout(timer.current); since.current = 0; }}
      onPointerCancel={() => { window.clearTimeout(timer.current); since.current = 0; }}
      onContextMenu={(e) => e.preventDefault()}
      onKeyDown={(e) => {
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault(); // the release decides: short cycles, long has listed already
        if (!keyDown.current) {
          keyDown.current = true;
          start();
        }
      }}
      onKeyUp={(e) => {
        if (e.key !== "Enter" && e.key !== " ") return;
        keyDown.current = false;
        cancel();
        if (!fired.current) onOpen("drive_mode");
        fired.current = false;
      }}
      onClick={(e) => {
        // pointer taps land here (keyboard activation is handled on key up)
        if (e.detail === 0) return;
        cancel();
        if (fired.current) {
          fired.current = false;
          return;
        }
        onOpen("drive_mode");
      }}>
      <Face c={c} />
    </button>
  );
}
