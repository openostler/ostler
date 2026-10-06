// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { symbolPath, SYMBOLS } from "./symbols";

const FILES = Object.keys(import.meta.glob("./material-symbols/*.svg", { query: "?raw", eager: true }))
  .map((f) => f.replace(/^.*\/([^/]+)\.svg$/, "$1")).sort();

describe("the vendored Material Symbols subset (UI spec §10.1)", () => {
  it("has path data for every symbol the UI names", () => {
    for (const s of SYMBOLS) expect(symbolPath(s), s).toMatch(/^[Mm][-\d]/);
  });

  it("vendors exactly the symbols in use, no more", () => {
    expect(FILES).toEqual([...SYMBOLS].sort());
  });
});
