// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

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
  plugins: [react()],
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
