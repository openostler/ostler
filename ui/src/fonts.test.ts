// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import html from "../index.html?raw";

// Every stylesheet and source file of the app as text (Vite glob, no Node APIs).
const FILES = import.meta.glob<string>(["/src/**/*.{css,ts,tsx}", "!/src/**/*.test.{ts,tsx}"], { query: "?raw", import: "default", eager: true });

describe("self-hosted Figtree (visual spec §4, V1b; UI audit P7)", () => {
  it("never asks Google Fonts (or any host) for a font", () => {
    const hits = Object.entries({ ...FILES, "index.html": html }).filter(([, src]) => /fonts\.(googleapis|gstatic)\.com/.test(src)).map(([f]) => f);
    expect(hits).toEqual([]);
  });

  it("declares the two Figtree subsets as variable woff2 and preloads the Latin one", () => {
    const css = FILES["/src/styles.css"] ?? "";
    expect(css.match(/@font-face \{[^}]*font-family: Figtree;[^}]*font-weight: 400 700;[^}]*font-display: swap;/g)).toHaveLength(2);
    expect(css).toContain('url("/fonts/figtree-latin.woff2") format("woff2")');
    expect(css).toContain('url("/fonts/figtree-latin-ext.woff2") format("woff2")');
    expect(html).toContain('<link rel="preload" href="/fonts/figtree-latin.woff2" as="font" type="font/woff2" crossorigin />');
  });
});
