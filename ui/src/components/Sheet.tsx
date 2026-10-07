// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useLayoutEffect, useRef, type ReactNode } from "react";
import { pushLayer } from "../shell/focus";

/**
 * Bottom sheet over the app. Tapping the scrim or `back` (Escape, through ShellInput) closes
 * it. It is the `sheet` focus zone (shell input spec §4.1): the only focus trap, and the
 * newest layer `back` closes; focus returns to where it was when the sheet closes, and `ok`
 * presses in its first 500 ms are ignored (§5).
 */
export function Sheet({ title, onClose, children, titleClass, className }: {
  title: ReactNode; onClose: () => void; children: ReactNode; titleClass?: string; className?: string;
}) {
  const close = useRef(onClose);
  useLayoutEffect(() => { close.current = onClose; });
  useEffect(() => pushLayer(() => close.current(), { sheet: true }), []);
  return (
    <div className={`sheet${className ? ` ${className}` : ""}`} role="dialog" aria-modal="true" data-zone="sheet">
      <div className="sheet-scrim" onClick={onClose} />
      <div className="sheet-body">
        <div className="grip" />
        <div className={`sheet-title ${titleClass ?? ""}`}>{title}</div>
        {children}
      </div>
    </div>
  );
}
