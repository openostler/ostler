// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, type ReactNode } from "react";

/** Bottom sheet over the app. Tapping the scrim or pressing Escape closes it. */
export function Sheet({ title, onClose, children, titleClass }: {
  title: ReactNode; onClose: () => void; children: ReactNode; titleClass?: string;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="sheet" role="dialog" aria-modal="true">
      <div className="sheet-scrim" onClick={onClose} />
      <div className="sheet-body">
        <div className="grip" />
        <div className={`sheet-title ${titleClass ?? ""}`}>{title}</div>
        {children}
      </div>
    </div>
  );
}
