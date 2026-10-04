/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The Python server owns every API route. In dev, Vite proxies them to it
// (`PYTHONPATH=src python3 tools/dashboard.py --mock`), so hot reload works against
// the mock car. Override the target with D2DIAG_API=http://pi.local:8080.
const API = process.env.D2DIAG_API ?? "http://localhost:8080";
const API_ROUTES = [
  "/events", "/snapshot", "/command", "/fields", "/map", "/sniff", "/signals",
  "/docs", "/doc", "/capture", "/automap", "/signal", "/calib", "/community", "/catalog",
];

export default defineConfig({
  plugins: [react()],
  build: {
    // Committed build output, shipped as package-data: the Pi never needs Node.
    outDir: fileURLToPath(new URL("../src/d2diag/web/static", import.meta.url)),
    emptyOutDir: true,
    sourcemap: false,
  },
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
