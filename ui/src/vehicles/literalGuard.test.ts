/**
 * Phase 0 (spec 2026-10-06 §5): platform UI code never names a vehicle module. Module ids,
 * names and layout come from GET /pack; only a pack's own UI (src/vehicles/<pack>/) may
 * spell them. Tests, test helpers and fixtures are exempt.
 */
import { describe, expect, it } from "vitest";

const SOURCES = import.meta.glob<string>(
  ["/src/**/*.{ts,tsx}", "!/src/**/*.test.{ts,tsx}", "!/src/test/**", "!/src/api/fixtures/**", "!/src/vehicles/*/**"],
  { query: "?raw", import: "default", eager: true },
);
// a module id as a whole string literal: "td5", 'slabs', `bcu`, "motor"
const LITERAL = /(["'`])(motor|td5|slabs|bcu)\1/g;

describe("platform UI has no vehicle module literals", () => {
  const files = Object.entries(SOURCES).map(([p, text]) => ({ path: p.replace(/^\/src\//, ""), text }));

  it("scans the platform sources (and not the packs)", () => {
    expect(files.length).toBeGreaterThan(50);
    expect(files.some((f) => f.path === "screens/Drive.tsx")).toBe(true);
    expect(files.some((f) => f.path === "vehicles/registry.ts")).toBe(true);
    expect(files.some((f) => f.path.startsWith("vehicles/lr_d2/"))).toBe(false);
  });

  it("finds no \"motor\" | \"td5\" | \"slabs\" | \"bcu\" string literal", () => {
    const hits = files.flatMap((f) =>
      f.text.split("\n").flatMap((line, i) => (line.match(LITERAL) ? [`${f.path}:${i + 1}: ${line.trim()}`] : [])));
    expect(hits).toEqual([]);
  });

  it("the pattern catches a literal (self-test)", () => {
    expect('if (module === "slabs")'.match(LITERAL)).toEqual(['"slabs"']);
    expect("Chassis/SLABS · td5_x".match(LITERAL)).toBeNull();
  });
});
