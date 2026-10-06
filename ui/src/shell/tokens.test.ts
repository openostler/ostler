// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import dark from "../../tokens/color.dark.tokens.json";
import light from "../../tokens/color.tokens.json";
import size from "../../tokens/size.tokens.json";
import { cssValue, flatten, tokensCss, type TokenTree } from "../../tokens/tokens";
import { LAYOUT_CLASSES } from "./layoutClass";

const files = { light: light as unknown as TokenTree, dark: dark as unknown as TokenTree, size: size as unknown as TokenTree };
const css = tokensCss(files);

// Every stylesheet of the app as text (Vite glob, no Node APIs).
const SHEETS = import.meta.glob<string>("/src/**/*.css", { query: "?raw", import: "default", eager: true });

describe("W3C design tokens (ui/tokens/*.tokens.json, UI spec §10.1)", () => {
  it("uses the DTCG shape: every token has a $type and a $value", () => {
    for (const tree of Object.values(files)) {
      const tokens = flatten(tree);
      expect(tokens.length).toBeGreaterThan(5);
      for (const [, t] of tokens) expect(["color", "dimension"]).toContain(t.$type);
    }
  });

  it("gives light and dark the same colour names", () => {
    const names = (t: TokenTree) => flatten(t).map(([p]) => p.join(".")).sort();
    expect(names(files.dark)).toEqual(names(files.light));
  });

  it("writes colours as hex or rgba and dimensions with their unit", () => {
    expect(css).toContain("--bg: #eceef1;");
    expect(css).toContain("--overlay: rgba(10, 12, 15, 0.55);");
    expect(css).toContain(':root[data-theme="dark"] {');
    expect(css).toContain('@media (prefers-color-scheme: dark) {\n:root:not([data-theme="light"]) {');
    expect(css).toContain("--chip-min-h: 48px;");
    expect(cssValue({ $value: { value: 76, unit: "px" } })).toBe("76px");
  });

  it("sizes the shell for every layout class (§3.1)", () => {
    for (const cls of LAYOUT_CLASSES) {
      const block = css.split(`.app[data-layout="${cls}"] {`)[1]?.split("}")[0] ?? "";
      for (const v of ["rail-w", "strip-h", "nav-item", "target", "gap"]) expect(block, `${cls} --${v}`).toContain(`--${v}:`);
    }
    expect(css).toMatch(/\.app\[data-layout="hu7"\] \{[^}]*--rail-w: 96px;[^}]*--strip-h: 56px;[^}]*--target: 76px;/);
    expect(css).toMatch(/\.app\[data-layout="hu9"\] \{[^}]*--rail-w: 112px;[^}]*--strip-h: 64px;/);
    expect(css).toMatch(/\.app\[data-layout="huwide"\] \{[^}]*--vehicle-pane: 520px;/);
    expect(css).toMatch(/\.app\[data-layout="phone"\] \{[^}]*--strip-h: 48px;[^}]*--nav-item: 72px;/);
  });

  it("defines every custom property a stylesheet uses", () => {
    const all = Object.values(SHEETS).join("\n") + css;
    const defined = new Set([...all.matchAll(/(--[\w-]+)\s*:/g)].map((m) => m[1]));
    const used = new Set([...all.matchAll(/var\((--[\w-]+)/g)].map((m) => m[1]));
    expect([...used].filter((v) => !defined.has(v))).toEqual([]);
  });
});
