import { defineConfig, devices } from "@playwright/test";

// Smoke test against the REAL Python server wired to the simulated sources by the test-only
// tests/e2e_server.py (ADR-0011: the product has no mock mode), with a replayed sniff log for
// the admin Map. Uses the venv/python given in PYTHON (default python3).
const PORT = 8099;
const python = process.env.PYTHON ?? "python3";

export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  retries: 0,
  workers: 1, // one shared test server: tests that switch module must not overlap
  reporter: [["list"]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    ...devices["Pixel 7"],
    browserName: "chromium",
  },
  webServer: {
    command: `${python} ../tests/e2e_server.py --host 127.0.0.1 --port ${PORT} --interval 0.3 --replay e2e/sniff-demo.txt --admin-password e2e`,
    env: { PYTHONPATH: "../src:.." }, // openostler + the tests package (tests/fake_sources.py)
    url: `http://127.0.0.1:${PORT}/snapshot`,
    reuseExistingServer: false,
    timeout: 20_000,
  },
});
