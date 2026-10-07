// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * W3C design tokens → CSS custom properties (UI spec §10.1; visual design system spec §2). The
 * `*.tokens.json` files next to this one are the single source (Design Tokens Community Group
 * format: `$type`, `$value`, groups, `{group.token}` aliases); the Vite plugin in
 * vite.config.ts serves the CSS built here as the virtual module `virtual:design-tokens.css`,
 * so nothing generated is committed. Pure: no Node APIs, so vitest checks it without a build.
 *
 * Naming: a colour or data token's CSS name is its path without the top group, joined with
 * "-" (`color.text-1` → `--text-1`, `night.speed-1` → `--speed-1`); a size token keeps its
 * whole path (`radius.md` → `--radius-md`); `layout.<class>.<name>` becomes `--<name>` on
 * `.app[data-layout="<class>"]`. An alias `{color.surface-1}` becomes `var(--surface-1)`, so
 * it follows the theme.
 *
 * Scopes (spec §2): Night (`color.dark`) is the default at `:root`; Night dim, Deep night and
 * Day override it under `:root[data-theme="dim" | "oled" | "light"]`. The app resolves its
 * Auto preference to one of those before the first render (state/theme.ts).
 */

type Color = { colorSpace: string; components: number[]; alpha?: number; hex?: string };
type Dimension = { value: number; unit: string };
type Shadow = { color: Color | string; offsetX: Dimension; offsetY: Dimension; blur: Dimension; spread: Dimension; inset?: boolean };
type Value = Color | Dimension | Shadow | Shadow[] | number[] | string[] | string | number;
type Token = { $type?: string; $value: Value; $description?: string };
export type TokenTree = { [key: string]: TokenTree | Token | string | undefined };

/** The DTCG types tokens.ts writes (spec §2). `gradient` is a CSS gradient string here. */
export const TOKEN_TYPES = ["color", "dimension", "shadow", "duration", "cubicBezier", "fontFamily", "fontWeight", "number", "gradient"];

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
const ALIAS = /^\{([^}]+)\}$/;

function colorCss(v: Color | string): string {
  if (typeof v === "string") return v;
  if (v.colorSpace !== "srgb") throw new Error(`unsupported colour space ${v.colorSpace}`);
  const [r = 0, g = 0, b = 0] = v.components.map(channel);
  if (v.alpha !== undefined && v.alpha < 1) return `rgba(${r}, ${g}, ${b}, ${v.alpha})`;
  return v.hex ?? `rgb(${r}, ${g}, ${b})`;
}
const dimCss = (d: Dimension) => `${d.value}${d.unit}`;
const familyCss = (f: string) => (/^[\w-]+$/.test(f) ? f : `"${f}"`);

/** A token value as CSS: hex colours, rgba() with alpha, `<n><unit>` dimensions and durations,
 * box-shadow lists (`none` when empty), cubic-bezier(), font stacks and plain numbers. An alias
 * resolves through `names` (token path → CSS name) to `var(--name)`. */
export function cssValue(t: Token, names: Map<string, string> = new Map()): string {
  const v = t.$value;
  if (typeof v === "string") {
    const ref = ALIAS.exec(v)?.[1];
    if (!ref) return v;
    const name = names.get(ref);
    if (!name) throw new Error(`unknown token alias {${ref}}`);
    return `var(--${name})`;
  }
  if (typeof v === "number") return String(v);
  if (t.$type === "cubicBezier") return `cubic-bezier(${(v as number[]).join(", ")})`;
  if (t.$type === "fontFamily") return (v as string[]).map(familyCss).join(", ");
  if (t.$type === "shadow") {
    const list = Array.isArray(v) ? (v as Shadow[]) : [v as Shadow];
    if (list.length === 0) return "none";
    return list.map((s) => [s.inset ? "inset" : "", dimCss(s.offsetX), dimCss(s.offsetY), dimCss(s.blur), dimCss(s.spread), colorCss(s.color)]
      .filter(Boolean).join(" ")).join(", ");
  }
  if ("colorSpace" in (v as object)) return colorCss(v as Color);
  return dimCss(v as Dimension);
}

/** The token files tokens.ts reads (vite.config.ts and tokens.test.ts pass the same set). */
export type TokenFiles = { dark: TokenTree; dim: TokenTree; oled: TokenTree; light: TokenTree; data: TokenTree; size: TokenTree };

/** CSS name of every token path ("color.text-1" → "text-1"), for aliases and tests. */
export function tokenNames(files: TokenFiles): Map<string, string> {
  const names = new Map<string, string>();
  const add = (tree: TokenTree, name: (p: string[]) => string[]) => {
    for (const [p] of flatten(tree)) names.set(p.join("."), name(p).join("-"));
  };
  for (const f of [files.dark, files.dim, files.oled, files.light, files.data]) add(f, (p) => p.slice(1));
  add(files.size, (p) => (p[0] === "layout" ? p.slice(2) : p));
  return names;
}

/** The CSS for the token files: Night colours, Night data, the shared ramps and the shared sizes
 * on :root; Night dim, Deep night and Day (with the Day data) under their data-theme; durations
 * to 0 under prefers-reduced-motion; the shell sizes and type per layout class. */
export function tokensCss(files: TokenFiles): string {
  const names = tokenNames(files);
  const decl = (name: string[], t: Token) => `  --${name.join("-")}: ${cssValue(t, names)};`;
  const theme = (tree: TokenTree) => flatten(tree).map(([p, t]) => decl(p.slice(1), t));
  const dataGroup = (g: string) => flatten((files.data[g] as TokenTree | undefined) ?? {}).map(([p, t]) => decl(p, t));
  const sizes = flatten(files.size);
  const shared = sizes.filter(([p]) => p[0] !== "layout").map(([p, t]) => decl(p, t));
  const durations = sizes.filter(([, t]) => t.$type === "duration").map(([p]) => `  --${p.join("-")}: 0ms;`);
  const classes = new Map<string, string[]>();
  for (const [p, t] of sizes.filter(([q]) => q[0] === "layout")) {
    const cls = p[1] ?? "";
    classes.set(cls, [...(classes.get(cls) ?? []), decl(p.slice(2), t)]);
  }
  const block = (sel: string, lines: string[]) => `${sel} {\n${lines.join("\n")}\n}`;
  return [
    "/* Generated from ui/tokens/*.tokens.json (ui/tokens/tokens.ts). Edit the JSON, not this. */",
    block(":root", ["  color-scheme: dark;", ...theme(files.dark), ...dataGroup("night"), ...dataGroup("ramp"), ...shared]),
    block(':root[data-theme="dim"]', theme(files.dim)),
    block(':root[data-theme="oled"]', theme(files.oled)),
    block(':root[data-theme="light"]', ["  color-scheme: light;", ...theme(files.light), ...dataGroup("day")]),
    `@media (prefers-reduced-motion: reduce) {\n${block(":root", durations)}\n}`,
    ...[...classes].map(([cls, lines]) => block(`.app[data-layout="${cls}"]`, lines)),
  ].join("\n") + "\n";
}
