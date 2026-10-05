import { describe, expect, it } from "vitest";
import { MODULE_NAME, moduleName } from "./layout";

describe("module names (spec 2026-10-06 §5)", () => {
  it("leads with the abbreviation, the plain name in brackets", () => {
    expect(moduleName("autobox")).toBe("EAT (auto gearbox)");
    expect(moduleName("airbag")).toBe("SRS (airbag)");
    expect(moduleName("motor")).toBe("TD5 (engine)");
    expect(moduleName("slabs")).toBe("SLABS (ABS + air suspension)");
  });

  it("every name follows the same ABBR (plain words) shape", () => {
    for (const name of Object.values(MODULE_NAME)) expect(name).toMatch(/^[A-Z0-9]+ \([^)]+\)$/);
  });

  it("falls back to the id for an unknown module", () => {
    expect(moduleName("nope")).toBe("nope");
  });
});
