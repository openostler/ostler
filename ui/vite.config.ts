// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/// <reference types="vitest/config" />
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";
import { tokensCss, type TokenTree } from "./tokens/tokens";

/** The design tokens (ui/tokens/*.tokens.json, W3C format) as `virtual:design-tokens.css`. */
function designTokens(): Plugin {
  const ID = "virtual:design-tokens.css";
  const RESOLVED = `\0${ID}`;
  const files = {
    dark: "color.dark.tokens.json", dim: "color.dim.tokens.json", oled: "color.oled.tokens.json", light: "color.tokens.json",
    data: "data.tokens.json", size: "size.tokens.json",
  } as const;
  const path = (f: string) => fileURLToPath(new URL(`./tokens/${f}`, import.meta.url));
  const read = (f: string) => JSON.parse(readFileSync(path(f), "utf8")) as TokenTree;
  return {
    name: "ostler-design-tokens",
    resolveId: (id) => (id === ID ? RESOLVED : undefined),
    load(id) {
      if (id !== RESOLVED) return undefined;
      for (const f of Object.values(files)) this.addWatchFile(path(f));
      return tokensCss({
        dark: read(files.dark), dim: read(files.dim), oled: read(files.oled), light: read(files.light),
        data: read(files.data), size: read(files.size),
      });
    },
  };
}

/** App-model seam 7 (app-model spec §9): the built page allows scripts from its own origin
 * only (no inline script), so the shell can later refuse unknown code. Build only: the dev
 * server injects an inline React refresh preamble. */
function contentSecurityPolicy(): Plugin {
  return {
    name: "ostler-csp",
    apply: "build",
    transformIndexHtml: () => [{
      tag: "meta", injectTo: "head-prepend",
      attrs: { "http-equiv": "Content-Security-Policy", content: "script-src 'self'; object-src 'none'; base-uri 'self'" },
    }],
  };
}

// The Python server owns every API route. In dev, Vite proxies them to it
// (`PYTHONPATH=src python3 tests/e2e_server.py` — the test-only simulated car; the product
// itself has no mock mode, ADR-0011), so hot reload works without a car. Override the target with D2DIAG_API=http://pi.local:8080.
const API = process.env.D2DIAG_API ?? "http://localhost:8080";
const API_ROUTES = [
  "/events", "/snapshot", "/command", "/fields", "/map", "/sniff", "/signals",
  "/docs", "/doc", "/capture", "/automap", "/signal", "/calib", "/community", "/catalog", "/sessions",
  "/notes", "/captures", "/pack",
];

export default defineConfig({
  plugins: [react(), designTokens(), contentSecurityPolicy()],
  build: {
    // Committed build output, shipped as package-data: the Pi never needs Node.
    outDir: fileURLToPath(new URL("../src/openostler/web/static", import.meta.url)),
    emptyOutDir: true,
    sourcemap: false,
    // MapLibre is reached only through `import("./components/replay/maplibre")`, so Rollup
    // splits it (and its CSS) into a lazy chunk; its worker is a separate `?worker&url`
    // bundle. maplibreChunk.test.ts guards that nothing imports it statically.
    chunkSizeWarningLimit: 1200,
  },
  worker: { format: "es" },
  server: {
    proxy: Object.fromEntries(API_ROUTES.map((r) => [r, { target: API, changeOrigin: true }])),
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    css: false,
  },
});
