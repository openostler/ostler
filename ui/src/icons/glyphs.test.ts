// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import ts from "typescript";
import { describe, expect, it } from "vitest";

/**
 * One icon set (visual design system spec §6, §9; UI audit P8): Material Symbols through
 * `Icon`, never an emoji, a dingbat or a Unicode arrow in UI text. This scans every string,
 * template and JSX text in src/ (comments and tests are not UI text) and the CSS `content`
 * values. © ® ™ are typographic marks a credit needs, not icons, so they stay allowed.
 */
const BANNED = /[\p{Extended_Pictographic}\u2190-\u21FF\u2500-\u25FF\u2600-\u27BF\u2B00-\u2BFF\u2039\u203A]|\uFE0F/u;
const ALLOWED = new Set(["©", "®", "™"]);

const SOURCES = import.meta.glob<string>(["/src/**/*.{ts,tsx}", "!/src/**/*.test.{ts,tsx}", "!/src/test/**"], {
  query: "?raw", import: "default", eager: true,
});
const SHEETS = import.meta.glob<string>("/src/**/*.css", { query: "?raw", import: "default", eager: true });

/** The banned characters in a piece of text (allowed marks removed). */
function bannedGlyphs(text: string): string[] {
  return [...text].filter((c) => BANNED.test(c) && !ALLOWED.has(c));
}

/** Every string literal, template piece and JSX text of a TS/TSX file, with its line. */
function uiText(file: string, src: string): { line: number; text: string }[] {
  const sf = ts.createSourceFile(file, src, ts.ScriptTarget.Latest, true, file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  const out: { line: number; text: string }[] = [];
  const visit = (n: ts.Node) => {
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n) || ts.isTemplateLiteralToken(n) || ts.isJsxText(n)) {
      out.push({ line: sf.getLineAndCharacterOfPosition(n.getStart(sf)).line + 1, text: n.text });
    }
    ts.forEachChild(n, visit);
  };
  visit(sf);
  return out;
}

describe("no emoji, dingbat or Unicode arrow glyphs in the UI (visual spec §6, §9)", () => {
  it("knows the glyphs the audit found (P8) and lets the credit marks through", () => {
    expect(bannedGlyphs("⏪ ⏩ ▶ ❚❚ ⚑ ⚙ ⚠ ✓ ✕ ▾ ▸ ‹ › → ← ★ ☆ ✎ ◆ ● 🔒 🔊 ⛔").join("")).toBe("⏪⏩▶❚❚⚑⚙⚠✓✕▾▸‹›→←★☆✎◆●🔒🔊⛔");
    expect(bannedGlyphs("© OpenStreetMap contributors · 1× · 90 °C · 0–30 km/h · “quoted” …")).toEqual([]);
  });

  it("finds none in any string, template or JSX text in src/", () => {
    expect(Object.keys(SOURCES).length).toBeGreaterThan(50);
    const hits = Object.entries(SOURCES).flatMap(([file, src]) =>
      uiText(file, src).filter((t) => bannedGlyphs(t.text).length).map((t) => `${file}:${t.line} ${bannedGlyphs(t.text).join("")}`));
    expect(hits).toEqual([]);
  });

  it("finds none in CSS generated content", () => {
    const hits = Object.entries(SHEETS).flatMap(([file, css]) =>
      [...css.matchAll(/content:\s*(["'])(.*?)\1/g)].filter((m) => bannedGlyphs(m[2] ?? "").length).map((m) => `${file}: ${m[0]}`));
    expect(hits).toEqual([]);
  });
});
