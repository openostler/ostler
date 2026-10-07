// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { symbolPath, type SymbolName } from "./symbols";

export type { SymbolName } from "./symbols";

/** One Material Symbol, sized by `size` (px, default 24; or a CSS length such as "1.2em" to sit
 * in a line of text), coloured by the text colour. The only icon set (visual spec §6): never an
 * emoji, dingbat or Unicode arrow in UI text (glyphs.test.ts). */
export function Icon({ name, size = 24, className }: { name: SymbolName; size?: number | string; className?: string }) {
  return (
    <svg className={`icon${className ? ` ${className}` : ""}`} width={size} height={size} viewBox="0 -960 960 960"
      aria-hidden="true" focusable="false" data-icon={name}>
      <path d={symbolPath(name)} fill="currentColor" />
    </svg>
  );
}
