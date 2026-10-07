// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { driveMenuRows, fitRow, MAX_CHARS, MAX_ROWS } from "./driveMenu";
import { movingForInput } from "../shell/useShellInput";

/** The Drive menu (shell input spec §6; UI spec §12.1 `short_list`). */
describe("the Drive menu's rows", () => {
  const mode = { name: "Dashboard", icon: "speed" as const };

  it("offers only items that exist, in order: Mark, Drive mode, Exit to Home, Back to Drive", () => {
    expect(driveMenuRows({ canMark: true, mode }).map((r) => r.id)).toEqual(["mark", "mode", "exit", "back"]);
    // no recording to mark: the row is absent, never greyed
    expect(driveMenuRows({ canMark: false, mode }).map((r) => r.id)).toEqual(["mode", "exit", "back"]);
    expect(driveMenuRows({ canMark: true, mode }).find((r) => r.id === "mode")?.state).toBe("Dashboard");
  });

  it("holds at most six rows of at most 30 characters, one level", () => {
    const rows = driveMenuRows({ canMark: true, mode: { name: "A very long custom mode name x", icon: "speed" } });
    expect(rows.length).toBeLessThanOrEqual(MAX_ROWS);
    for (const r of rows) expect([...`${r.label}${r.state ? ` ${r.state}` : ""}`].length).toBeLessThanOrEqual(MAX_CHARS);
    expect(rows.find((r) => r.id === "mode")?.state).toMatch(/…$/);
    expect(fitRow({ id: "back", label: "Back to Drive", icon: "close" }).label).toBe("Back to Drive");
  });
});

describe("Moving for input (UI spec §3.5: unknown counts as Moving, fail closed)", () => {
  it("treats unknown as Moving on driver-facing classes only", () => {
    for (const c of ["hu5", "hu7", "hu9", "huwide", "phone"] as const) expect(movingForInput(c, "unknown")).toBe(true);
    for (const c of ["tablet", "desktop"] as const) expect(movingForInput(c, "unknown")).toBe(false);
    expect(movingForInput("desktop", "moving")).toBe(true);
    expect(movingForInput("hu7", "parked")).toBe(false);
    expect(movingForInput("hu7", "idling")).toBe(false);
  });
});
