// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { symbolPath, type SymbolName } from "./symbols";

export type { SymbolName } from "./symbols";

/** One Material Symbol, sized by `size` (px, default 24), coloured by the text colour. */
export function Icon({ name, size = 24, className }: { name: SymbolName; size?: number; className?: string }) {
  return (
    <svg className={`icon${className ? ` ${className}` : ""}`} width={size} height={size} viewBox="0 -960 960 960"
      aria-hidden="true" focusable="false">
      <path d={symbolPath(name)} fill="currentColor" />
    </svg>
  );
}
