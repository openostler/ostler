// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { recordFromSolve, signalNameFor } from "./mapping";

describe("signalNameFor", () => {
  it("prefers the menu item's bound signal", () =>
    expect(signalNameFor({ name: "1. Engine Speed (rpm)", status: "ok", sig: "rpm" })).toBe("rpm"));
  it("derives a snake_case name from the menu label", () =>
    expect(signalNameFor({ name: "12. High/Low Range Switch (on/off)", status: "todo" })).toBe("high_low_range_switch"));
});

describe("recordFromSolve", () => {
  it("builds a numeric candidate record", () => {
    expect(recordFromSolve({ ok: true, mode: "numeric", lid: "09", offset: 0, kind: "u16", scale: 1, bias: 0 }, "rpm"))
      .toMatchObject({ name: "rpm", lid: "09", offset: 0, kind: "u16", scale: 1, bias: 0, confidence: "candidate" });
  });
  it("builds a bit record with raw → label states", () => {
    const rec = recordFromSolve({ ok: true, mode: "state", lid: "56", offset: 0, bit: 0, mapping: { open: 1, closed: 0 } }, "any_door");
    expect(rec).toMatchObject({ kind: "bit", bit: 0, states: { 1: "open", 0: "closed" } });
  });
  it("uses a whole byte when no single bit explains the states", () => {
    const rec = recordFromSolve({ ok: true, mode: "state", lid: "56", offset: 1, bit: null, mapping: { A: 3, B: 7 } }, "x");
    expect(rec).toMatchObject({ kind: "u8", states: { 3: "A", 7: "B" } });
  });
});
