// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The U1 icon set (UI spec §10.1): a vendored subset of Google's Material Symbols
 * (outlined, weight 400; Apache-2.0: THIRD_PARTY_LICENSES.md, REUSE.toml), copied verbatim from
 * the `@material-symbols/svg-400` package. The SVG files are read as text at build time and
 * drawn inline with `currentColor`, so no request, font or script is involved. Icons are
 * always decorative here: the shell pairs every icon with a word (UI spec §2.7).
 */
const FILES = import.meta.glob<string>("./material-symbols/*.svg", {
  query: "?raw", import: "default", eager: true,
});

/** symbol name → the path data of its single <path>. */
const PATHS: Record<string, string> = Object.fromEntries(
  Object.entries(FILES).map(([file, svg]) => [
    file.replace(/^.*\/([^/]+)\.svg$/, "$1"),
    /\sd="([^"]+)"/.exec(svg)?.[1] ?? "",
  ]),
);

export const SYMBOLS = [
  "home", "stethoscope", "history", "shield", "more_horiz", "speed", "warning", "error",
  "fiber_manual_record-fill", "flag", "battery_full", "arrow_back", "settings", "cable", "code",
  "chevron_right", "description", "bedtime", "hourglass_top", "power_settings_new", "swap_horiz",
  "edit_note",
] as const;
export type SymbolName = (typeof SYMBOLS)[number];

/** The path data for a symbol ("" when the file is missing; a test guards that). */
export const symbolPath = (name: SymbolName): string => PATHS[name] ?? "";

