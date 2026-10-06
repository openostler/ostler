// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * W3C design tokens → CSS custom properties (UI spec §10.1, U1). The `*.tokens.json` files
 * next to this one are the single source (Design Tokens Community Group format: `$type`,
 * `$value`, groups); the Vite plugin in vite.config.ts serves the CSS built here as the
 * virtual module `virtual:design-tokens.css`, so nothing generated is committed. Pure: no
 * Node APIs, so vitest checks it without a build.
 *
 * Naming: a token's CSS name is its path without the top group, joined with "-"
 * (`color.text-1` → `--text-1`, `radius.md` → `--radius-md`). `layout.<class>.<name>`
 * becomes `--<name>` on `.app[data-layout="<class>"]`.
 */

type Color = { colorSpace: string; components: number[]; alpha?: number; hex?: string };
type Dimension = { value: number; unit: string };
type Token = { $type?: string; $value: Color | Dimension | string | number; $description?: string };
export type TokenTree = { [key: string]: TokenTree | Token | string | undefined };

const isToken = (n: unknown): n is Token => typeof n === "object" && n !== null && "$value" in n;

/** Every token under `tree` as [path, token], in file order ($-keys skipped). */
export function flatten(tree: TokenTree, path: string[] = []): [string[], Token][] {
  return Object.entries(tree).flatMap(([k, v]): [string[], Token][] => {
    if (k.startsWith("$") || v === undefined || typeof v === "string") return [];
    if (isToken(v)) return [[[...path, k], v]];
    return flatten(v, [...path, k]);
  });
}

const channel = (x: number) => Math.round(Math.min(1, Math.max(0, x)) * 255);

/** A token value as CSS: hex colours, rgba() with alpha, `<n><unit>` dimensions. */
export function cssValue(t: Token): string {
  const v = t.$value;
  if (typeof v === "string" || typeof v === "number") return String(v);
  if ("colorSpace" in v) {
    if (v.colorSpace !== "srgb") throw new Error(`unsupported colour space ${v.colorSpace}`);
    const [r = 0, g = 0, b = 0] = v.components.map(channel);
    if (v.alpha !== undefined && v.alpha < 1) return `rgba(${r}, ${g}, ${b}, ${v.alpha})`;
    return v.hex ?? `rgb(${r}, ${g}, ${b})`;
  }
  return `${v.value}${v.unit}`;
}

const decl = (path: string[], t: Token) => `  --${path.join("-")}: ${cssValue(t)};`;

/** The CSS for the three token files: light colours and shared sizes on :root, the dark set
 * for prefers-color-scheme (unless data-theme="light") and data-theme="dark", and the shell
 * sizes per layout class. */
export function tokensCss(files: { light: TokenTree; dark: TokenTree; size: TokenTree }): string {
  const light = flatten(files.light).map(([p, t]) => decl(p.slice(1), t));
  const dark = flatten(files.dark).map(([p, t]) => decl(p.slice(1), t));
  const sizes = flatten(files.size);
  const shared = sizes.filter(([p]) => p[0] !== "layout").map(([p, t]) => decl(p, t));
  const classes = new Map<string, string[]>();
  for (const [p, t] of sizes.filter(([q]) => q[0] === "layout")) {
    const cls = p[1] ?? "";
    classes.set(cls, [...(classes.get(cls) ?? []), decl(p.slice(2), t)]);
  }
  const block = (sel: string, lines: string[]) => `${sel} {\n${lines.join("\n")}\n}`;
  const darkLines = ["  color-scheme: dark;", ...dark];
  return [
    "/* Generated from ui/tokens/*.tokens.json (ui/tokens/tokens.ts). Edit the JSON, not this. */",
    block(":root", ["  color-scheme: light;", ...light, ...shared]),
    `@media (prefers-color-scheme: dark) {\n${block(':root:not([data-theme="light"])', darkLines)}\n}`,
    block(':root[data-theme="dark"]', darkLines),
    ...[...classes].map(([cls, lines]) => block(`.app[data-layout="${cls}"]`, lines)),
  ].join("\n") + "\n";
}
