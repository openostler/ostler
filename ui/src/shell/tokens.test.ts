// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import dark from "../../tokens/color.dark.tokens.json";
import dim from "../../tokens/color.dim.tokens.json";
import oled from "../../tokens/color.oled.tokens.json";
import light from "../../tokens/color.tokens.json";
import data from "../../tokens/data.tokens.json";
import size from "../../tokens/size.tokens.json";
import { cssValue, flatten, TOKEN_TYPES, tokensCss, type TokenFiles, type TokenTree } from "../../tokens/tokens";
import { LAYOUT_CLASSES } from "./layoutClass";

const t = (x: unknown) => x as TokenTree;
const files: TokenFiles = { dark: t(dark), dim: t(dim), oled: t(oled), light: t(light), data: t(data), size: t(size) };
const css = tokensCss(files);
const THEMES = { Night: files.dark, "Night dim": files.dim, "Deep night": files.oled, Day: files.light } as const;

// Every stylesheet of the app as text (Vite glob, no Node APIs).
const SHEETS = import.meta.glob<string>("/src/**/*.css", { query: "?raw", import: "default", eager: true });

/** A colour token's #rrggbb (aliases followed within the same file). */
function hex(tree: TokenTree, name: string): string {
  const tok = flatten(tree).find(([p]) => p.slice(1).join("-") === name)?.[1];
  if (!tok) throw new Error(`no colour ${name}`);
  const v = tok.$value as { hex?: string } | string;
  if (typeof v === "string") return hex(tree, v.replace(/^\{\w+\.|\}$/g, ""));
  return v.hex ?? "";
}
/** WCAG 2 contrast ratio of two #rrggbb colours. */
function contrast(a: string, b: string): number {
  const lum = (h: string) => {
    const [r, g, bl] = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
    return 0.2126 * (r ?? 0) + 0.7152 * (g ?? 0) + 0.0722 * (bl ?? 0);
  };
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return ((hi ?? 0) + 0.05) / ((lo ?? 0) + 0.05);
}

describe("W3C design tokens (ui/tokens/*.tokens.json, visual design system spec §2)", () => {
  it("uses the DTCG shape: every token has a known $type and a $value", () => {
    for (const tree of Object.values(files)) {
      const tokens = flatten(tree);
      expect(tokens.length).toBeGreaterThan(5);
      for (const [p, tok] of tokens) expect(TOKEN_TYPES, p.join(".")).toContain(tok.$type);
    }
  });

  it("gives every theme file the same names as the Night file", () => {
    const names = (x: TokenTree) => flatten(x).map(([p]) => p.join(".")).sort();
    for (const tree of [files.dim, files.oled, files.light]) expect(names(tree)).toEqual(names(files.dark));
    const group = (g: string) => flatten(files.data[g] as TokenTree).map(([p]) => p.join(".")).sort();
    expect(group("day")).toEqual(group("night"));
  });

  it("puts Night at :root and the other themes under data-theme (spec §2)", () => {
    expect(css).toMatch(/^:root \{\n {2}color-scheme: dark;\n {2}--bg: #0b0d10;/m);
    expect(css).toMatch(/:root\[data-theme="dim"\] \{[^}]*--bg: #07090b;/);
    expect(css).toMatch(/:root\[data-theme="oled"\] \{[^}]*--bg: #000000;/);
    expect(css).toMatch(/:root\[data-theme="light"\] \{\n {2}color-scheme: light;[^}]*--bg: #f3f5f7;[^}]*--speed-1: #bea0eb;/);
    expect(css).not.toContain("prefers-color-scheme"); // Auto is resolved in JS (state/theme.ts)
    expect(css).toContain("--accent: #22a6e0;");
    expect(css).toContain("--speed-1: #5d3fa8;");
    expect(css).toContain("--plasma-1: #4b03a1;");
  });

  it("writes every DTCG type as CSS and resolves aliases to var()", () => {
    expect(css).toContain("--overlay: rgba(0, 0, 0, 0.651);");
    expect(css).toContain("--surface: var(--surface-1);"); // legacy alias, retired in V3.5
    expect(css).toContain("--chart-axis: var(--text-3);");
    expect(css).toContain("--trace-casing: var(--bg);");
    expect(css).toContain("--glow-accent: 0px 0px 0px 1px rgba(34, 166, 224, 0.4), 0px 0px 24px 0px rgba(34, 166, 224, 0.251);");
    expect(css).toMatch(/:root\[data-theme="dim"\] \{[^}]*--glow-accent: none;/);
    expect(css).toContain("--elev-1: inset 0px 1px 0px 0px rgba(255, 255, 255, 0.051);");
    expect(css).toContain("--dur-base: 200ms;");
    expect(css).toContain("--ease-standard: cubic-bezier(0.2, 0, 0, 1);");
    expect(css).toContain('--font-base: Figtree, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;');
    expect(css).toContain("--weight-bold: 700;");
    expect(css).toContain("--unit-ratio: 0.45;");
    expect(css).toContain("--radius-md: 16px;");
    expect(css).toContain("--chip-min-h: 48px;");
    expect(css).toMatch(/@media \(prefers-reduced-motion: reduce\) \{\n:root \{\n {2}--dur-fast: 0ms;/);
    expect(cssValue({ $value: { value: 76, unit: "px" } })).toBe("76px");
    expect(() => cssValue({ $value: "{color.nope}" })).toThrow(/unknown token alias/);
  });

  it("sizes the shell and the type scale for every layout class (§3.1, visual spec §4)", () => {
    for (const cls of LAYOUT_CLASSES) {
      const block = css.split(`.app[data-layout="${cls}"] {`)[1]?.split("}")[0] ?? "";
      for (const v of ["rail-w", "strip-h", "nav-item", "target", "gap", "type-hero", "type-num-xl", "type-num-l", "type-title",
        "type-body", "type-label", "type-kicker", "type-caption", "type-min", "type-primary", "type-secondary"]) {
        expect(block, `${cls} --${v}`).toContain(`--${v}:`);
      }
    }
    expect(css).toMatch(/\.app\[data-layout="hu5"\] \{[^}]*--rail-w: 80px;[^}]*--strip-h: 48px;[^}]*--target: 76px;/);
    expect(css).toMatch(/\.app\[data-layout="hu7"\] \{[^}]*--rail-w: 96px;[^}]*--strip-h: 56px;[^}]*--target: 76px;/);
    expect(css).toMatch(/\.app\[data-layout="hu9"\] \{[^}]*--rail-w: 112px;[^}]*--strip-h: 64px;/);
    expect(css).toMatch(/\.app\[data-layout="huwide"\] \{[^}]*--vehicle-pane: 520px;/);
    expect(css).toMatch(/\.app\[data-layout="phone"\] \{[^}]*--strip-h: 48px;[^}]*--nav-item: 72px;/);
    expect(css).toMatch(/\.app\[data-layout="phone"\] \{[^}]*--type-hero: 64px;[^}]*--type-num-xl: 40px;[^}]*--type-min: 12px;/);
    expect(css).toMatch(/\.app\[data-layout="hu5"\] \{[^}]*--type-num-xl: 64px;[^}]*--type-min: 18px;/);
    expect(css).toMatch(/\.app\[data-layout="huwide"\] \{[^}]*--type-hero: 120px;/);
    expect(css).toMatch(/\.app\[data-layout="hu7"\] \{[^}]*--type-primary: var\(--type-title\);[^}]*--type-secondary: var\(--type-body\);/);
  });

  it("defines every custom property a stylesheet uses", () => {
    const all = Object.values(SHEETS).join("\n") + css;
    const defined = new Set([...all.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
    const used = new Set([...all.matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]));
    expect([...used].filter((v) => !defined.has(v))).toEqual([]);
  });
});

// Shell input spec §9 (visual spec §5): one focus ring for every focusable, from tokens: 3 px of
// focus-ring-color (the accent) outside a 2 px bg gap; WCAG 2.4.13 wants ≥ 3:1 against what it
// sits on in every theme. No stylesheet draws its own focus outline or glow.
describe("the focus ring tokens (shell input spec §9)", () => {
  it("defines the width, gap and colour once, the colour following the theme's accent", () => {
    expect(css).toContain("--focus-ring-width: 3px;");
    expect(css).toContain("--focus-ring-gap: 2px;");
    expect(css).toMatch(/^:root \{[^}]*--focus-ring-color: var\(--accent\);/m);
    for (const theme of ["dim", "oled", "light"]) {
      expect(css).toMatch(new RegExp(`:root\\[data-theme="${theme}"\\] \\{[^}]*--focus-ring-color: var\\(--accent\\);`));
    }
  });

  for (const [theme, tree] of Object.entries(THEMES)) {
    it(`${theme}: the ring is at least 3:1 against bg and every surface`, () => {
      const low = ["bg", "surface-1", "surface-2", "surface-3"].map((bg) => [bg, contrast(hex(tree, "accent"), hex(tree, bg))] as const)
        .filter(([, ratio]) => ratio < 3).map(([bg, ratio]) => `${bg} ${ratio.toFixed(2)}`);
      expect(low).toEqual([]);
    });
  }

  it("is the only focus style: every :focus-visible rule uses the tokens, none glows", () => {
    const rules = Object.entries(SHEETS).flatMap(([file, text]) =>
      [...text.matchAll(/([^{}]*:focus-visible[^{}]*)\{([^}]*)\}/g)].map((m) => ({ file, sel: m[1]!.trim(), body: m[2]! })));
    expect(rules.length).toBeGreaterThan(0);
    for (const r of rules) {
      const outline = /outline:\s*([^;]+)/.exec(r.body)?.[1]?.trim();
      if (outline && outline !== "none") expect(outline, `${r.file} ${r.sel}`).toContain("var(--focus-ring-width)");
      const shadow = /box-shadow:\s*([^;]+)/.exec(r.body)?.[1]?.trim();
      // the gap is a spread-only shadow: zero blur, so never a glow
      if (shadow && shadow !== "none") expect(shadow, `${r.file} ${r.sel}`).toMatch(/^(inset )?0 0 0 var\(--focus-ring-gap\) var\(--bg\)$/);
    }
  });
});

// Visual design system spec §3.2: text on the surfaces it may sit on, ≥ 4.5:1 (WCAG 1.4.3), in
// every theme. The spec's own exceptions are asserted as exceptions, so a change shows up.
describe("contrast of the allowed text/surface pairs (spec §3.2)", () => {
  const AA = 4.5;
  const PAIRS: [string, string][] = [
    ["text-1", "bg"], ["text-1", "surface-1"], ["text-1", "surface-2"], ["text-1", "surface-3"],
    ["text-2", "bg"], ["text-2", "surface-1"], ["text-2", "surface-2"], ["text-2", "surface-3"],
    ["text-3", "bg"], ["text-3", "surface-1"], ["text-3", "surface-2"],
    ["accent", "bg"], ["accent", "surface-1"], ["accent", "surface-2"],
    ["on-accent", "accent"],
    ["warn-ink", "surface-1"], ["warn-ink", "surface-2"], ["info", "surface-1"],
    ["ok", "surface-1"], ["alarm", "surface-1"],
    // status words on a status tint wear text-1
    ["text-1", "ok-bg"], ["text-1", "warn-bg"], ["text-1", "alarm-bg"],
  ];
  for (const [theme, tree] of Object.entries(THEMES)) {
    it(`${theme}: every allowed pair is at least 4.5:1`, () => {
      const low = PAIRS.map(([fg, bg]) => [`${fg} on ${bg}`, contrast(hex(tree, fg), hex(tree, bg))] as const)
        .filter(([, r]) => r < AA).map(([n, r]) => `${n} ${r.toFixed(2)}`);
      expect(low).toEqual([]);
    });
  }

  it("keeps the dark themes' warn readable as text; Day warn is for icons and edges only (3:1)", () => {
    for (const tree of [files.dark, files.dim, files.oled]) expect(contrast(hex(tree, "warn"), hex(tree, "surface-1"))).toBeGreaterThanOrEqual(AA);
    const dayWarn = contrast(hex(files.light, "warn"), hex(files.light, "surface-1"));
    expect(dayWarn).toBeGreaterThanOrEqual(3);
    expect(dayWarn).toBeLessThan(AA); // hence warn-ink for words
  });

  it("bans text-3 on surface-3 (Night 4.0:1) and keeps accent on surface-3 at the spec's 4.5 (Day 4.45)", () => {
    expect(contrast(hex(files.dark, "text-3"), hex(files.dark, "surface-3"))).toBeLessThan(AA);
    for (const tree of Object.values(THEMES)) expect(contrast(hex(tree, "accent"), hex(tree, "surface-3"))).toBeGreaterThanOrEqual(4.44);
  });

  it("matches the spec's published ratios", () => {
    const r = (tree: TokenTree, fg: string, bg: string) => Number(contrast(hex(tree, fg), hex(tree, bg)).toFixed(1));
    expect(r(files.dark, "text-1", "bg")).toBe(17.3);
    expect(r(files.dim, "text-2", "surface-1")).toBe(6.5);
    expect(r(files.oled, "on-accent", "accent")).toBe(7.6);
    expect(r(files.light, "warn-ink", "surface-1")).toBe(5.3);
  });

  it("keeps the speed ramp ordered by lightness in both theme groups (spec §3.3)", () => {
    const lumOf = (h: string) => contrast(h, "#000000");
    const ramp = (g: string) => [1, 2, 3, 4, 5, 6].map((i) => lumOf(hex(t({ x: files.data[g] }), `speed-${i}`)));
    const night = ramp("night");
    const day = ramp("day");
    expect(night).toEqual([...night].sort((a, b) => a - b)); // dark themes: light = fast
    expect(day).toEqual([...day].sort((a, b) => b - a)); // Day: dark = fast
  });
});
