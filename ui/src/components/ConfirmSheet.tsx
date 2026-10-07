// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef, type ReactNode } from "react";
import { Sheet } from "./Sheet";

/**
 * The confirm sheet for an action that reaches the gate (shell input spec §7; UI spec §7):
 * it opens with **Cancel focused**, so the confirm button is reached by an arrow and a double
 * press cannot approve; `ok` presses in its first 500 ms are ignored (the Sheet's guard); it
 * never counts down. `children` carry the action's own friction (preconditions to tick, the
 * name to type: components/confirm.ts `confirmReady`).
 */
export function ConfirmSheet({ title, detail, confirmLabel, danger = false, ready = true, onConfirm, onCancel, children }: {
  title: string;
  detail?: ReactNode;
  confirmLabel: string;
  danger?: boolean;
  /** The confirm button is enabled only when the friction is satisfied. */
  ready?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  children?: ReactNode;
}) {
  const cancel = useRef<HTMLButtonElement>(null);
  useEffect(() => { cancel.current?.focus(); }, []);
  return (
    <Sheet title={title} onClose={onCancel} className="confirm-sheet">
      <div className="stack" data-confirm="">
        {detail ? <div className="small muted pretty">{detail}</div> : null}
        {children}
        <div className="btn-row">
          <button ref={cancel} type="button" className="btn" data-focus="" onClick={onCancel}>Cancel</button>
          <button type="button" className={`btn ${danger ? "danger" : "accent"}`} data-focus="" disabled={!ready}
            onClick={onConfirm}>{confirmLabel}</button>
        </div>
      </div>
    </Sheet>
  );
}
