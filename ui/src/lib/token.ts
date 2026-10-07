// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * A design token's current value for code that cannot use `var(--…)`: Canvas drawing and
 * MapLibre paint properties (visual design system spec §2). Reads the computed custom
 * property, so it follows the theme; components never hold a hex value. Returns `fallback`
 * when the token is not defined (unit tests run without the token CSS).
 */
export function token(name: string, fallback = "", el: Element = document.documentElement): string {
  const v = getComputedStyle(el).getPropertyValue(`--${name}`).trim();
  return v || fallback;
}
