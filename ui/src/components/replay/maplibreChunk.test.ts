/**
 * Build-free guard for the spec rule "MapLibre is lazy-loaded with import(), never in the main
 * chunk": only replay/maplibre.ts may import maplibre-gl, and nothing may import that module
 * statically (TraceMap reaches it with a dynamic import()).
 */
import { describe, expect, it } from "vitest";

// Every source file under src/ as text (Vite glob, so no Node APIs are needed).
const SOURCES = import.meta.glob<string>(["/src/**/*.{ts,tsx}", "!/src/**/*.test.{ts,tsx}"], {
  query: "?raw", import: "default", eager: true,
});

describe("maplibre stays out of the main chunk", () => {
  const all = Object.entries(SOURCES).map(([p, text]) => ({ path: p.replace(/^\/src\//, ""), text }));

  it("only components/replay/maplibre.ts imports maplibre-gl at runtime", () => {
    expect(all.length).toBeGreaterThan(20);
    const runtime = /^\s*import\s+(?!type\b)[^;]*from\s+["']maplibre-gl(\/[^"']*)?["']|^\s*import\s+["']maplibre-gl/m;
    const hits = all.filter((f) => runtime.test(f.text)).map((f) => f.path);
    expect(hits).toEqual(["components/replay/maplibre.ts"]);
  });

  it("the maplibre module is only reached through dynamic import()", () => {
    const staticImport = /^\s*import\s+(?!type\b)[^;]*from\s+["'][^"']*\/maplibre["']/m;
    expect(all.filter((f) => staticImport.test(f.text)).map((f) => f.path)).toEqual([]);
    const dynamic = all.filter((f) => f.path !== "components/replay/maplibre.ts" && /import\(\s*["']\.\/maplibre["']\s*\)/.test(f.text)).map((f) => f.path);
    expect(dynamic).toEqual(["components/replay/TraceMap.tsx"]);
  });
});
