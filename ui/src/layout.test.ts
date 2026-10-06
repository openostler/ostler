// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import {
  bodyLayout, canonicalModule, defaultModule, driveView, groupOrder, moduleName, moduleNames, moduleNotices, tileConv, utilLids,
} from "./layout";
import { setPack } from "./pack/store";
import { packFixture } from "./test/packFixture";

describe("module names (from /pack)", () => {
  it("leads with the abbreviation, the plain name in brackets", () => {
    expect(moduleName("autobox")).toBe("EAT (auto gearbox)");
    expect(moduleName("airbag")).toBe("SRS (airbag)");
    expect(moduleName("td5")).toBe("TD5 (engine)");
    expect(moduleName("slabs")).toBe("SLABS (ABS + air suspension)");
  });

  it("every name follows the same ABBR (plain words) shape", () => {
    for (const [, name] of moduleNames()) expect(name).toMatch(/^[A-Z0-9]+ \([^)]+\)$/);
  });

  it("lists the pack's modules in pack order", () => {
    expect(moduleNames().map(([id]) => id)).toEqual(packFixture.modules.map((m) => m.id));
  });

  it("maps legacy aliases to the canonical id (and names them)", () => {
    expect(canonicalModule("motor")).toBe("td5");
    expect(canonicalModule("gearbox")).toBe("autobox");
    expect(canonicalModule("td5")).toBe("td5");
    expect(moduleName("motor")).toBe("TD5 (engine)");
  });

  it("falls back to the id for an unknown module", () => {
    expect(moduleName("nope")).toBe("nope");
    expect(canonicalModule("nope")).toBe("nope");
  });
});

describe("layout accessors", () => {
  it("reads the pack layout", () => {
    expect(defaultModule()).toBe("td5");
    expect(groupOrder()[0]).toBe("Engine");
    expect(driveView("td5")).toMatchObject({ kind: "tiles", health: true });
    expect(driveView("motor")?.kind).toBe("tiles");
    expect(driveView("slabs")).toMatchObject({ kind: "slabs_car", health: true });
    expect(driveView("airbag")).toBeNull();
    expect(bodyLayout().groups.map((g) => g.title)).toContain("Lighting");
    expect(utilLids("td5").example).toMatch(/^09 /);
    expect(utilLids("airbag")).toEqual({ example: "", note: "" });
    expect(moduleNotices("slabs").inputs_banner).toMatch(/stationary/);
    expect(moduleNotices("td5")).toEqual({});
  });

  it("scales a tile (L/100km → L/mil)", () => {
    const fuel = driveView("td5")!.tiles!.find((t) => t.unit === "L/mil")!;
    expect(tileConv(fuel)!(73)).toBeCloseTo(7.3);
    expect(tileConv({ signal: "x", label: "X" })).toBeUndefined();
  });

  it("falls back sensibly before the pack loads", () => {
    setPack(null);
    expect(moduleName("td5")).toBe("td5");
    expect(canonicalModule("motor")).toBe("motor");
    expect(moduleNames()).toEqual([]);
    expect(groupOrder()).toEqual([]);
    expect(driveView("td5")).toBeNull();
    expect(bodyLayout()).toEqual({ signals: {}, groups: [] });
    expect(utilLids("td5")).toEqual({ example: "", note: "" });
    expect(defaultModule()).toBe("");
  });
});
