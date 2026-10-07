// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { expect, test, type Page } from "@playwright/test";

/** Skip the first-start consent screen (stored per device, like a returning user), and
 * acknowledge the fault sheet whenever it pops up — the simulated car has stored faults. */
async function returningUser(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false })),
  );
  await page.addLocatorHandler(page.getByRole("button", { name: "Dismiss" }), async (btn) => {
    await btn.click();
  });
}

/** A destination in the rail or bottom bar. */
const dest = (page: Page, name: string) =>
  page.getByRole("navigation", { name: "Destinations" }).getByRole("button", { name, exact: true });

/** Open a Diagnose area (Faults, Inputs, Outputs, Utilities, Settings). */
async function area(page: Page, name: string) {
  await dest(page, "Diagnose").click();
  await page.getByRole("navigation", { name: "Areas" }).getByRole("button", { name, exact: true }).click();
}

test("first start asks for consent before anything else", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Before you connect")).toBeVisible();
  await page.getByRole("radio", { name: /Don't share/ }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Before you connect")).toBeHidden();
});

// Visual spec §4 (V1b, UI audit P7): Figtree is self-hosted, so an offline car renders it and
// no page load asks a third party for a font.
test("renders the self-hosted Figtree with every other host blocked", async ({ page }) => {
  await returningUser(page);
  const offsite: string[] = [];
  await page.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, (route) => {
    offsite.push(route.request().url());
    return route.abort();
  });
  const fonts: string[] = [];
  page.on("response", (r) => { if (r.url().includes("/fonts/")) fonts.push(`${r.status()} ${r.headers()["content-type"]}`); });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  const loaded = await page.evaluate(async () => {
    const d = (globalThis as unknown as { document: { fonts: { ready: Promise<unknown>; check(f: string): boolean } } }).document;
    await d.fonts.ready;
    return { bold: d.fonts.check("700 16px Figtree"), regular: d.fonts.check("400 16px Figtree") };
  });
  expect(loaded).toEqual({ bold: true, regular: true });
  expect(fonts).toContain("200 font/woff2");
  expect(offsite.filter((u) => /fonts\.(googleapis|gstatic)\.com/.test(u))).toEqual([]);
});

test("simulated live data streams into Home and Inputs", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await expect(page.locator('[data-signal="battery"]')).toContainText("V");
  await page.screenshot({ path: "test-results/drive.png", fullPage: true });

  await area(page, "Inputs");
  await expect(page.getByText("Temperatures")).toBeVisible();
  const rpm = page.locator('.srow[data-signal="rpm"] .cv-num');
  const first = await rpm.textContent();
  await expect.poll(async () => rpm.textContent(), { timeout: 5000 }).not.toBe(first); // SSE updates
  await page.screenshot({ path: "test-results/inputs.png", fullPage: true });
});

/** Pick a module in Diagnose's switcher and wait for the server to switch. */
async function switchModule(page: Page, id: string) {
  const select = page.getByRole("combobox", { name: "Module" });
  if (!(await select.isVisible())) await dest(page, "Diagnose").click();
  await expect(select.locator(`option[value="${id}"]`)).toHaveCount(1);
  await select.selectOption(id);
  await expect(select).toHaveValue(id);
}

test("the destinations hold today's screens (UI spec §3.4), no Connect or Capabilities", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Destinations" }).getByRole("button"))
    .toHaveText(["Home", "Diagnose", "Logs", "More"]);
  await dest(page, "Diagnose").click();
  await expect(page.getByRole("navigation", { name: "Areas" }).getByRole("button"))
    .toHaveText(["Faults", "Inputs", "Outputs", "Utilities", "Settings"]);
  await dest(page, "Logs").click();
  await expect(page.getByRole("navigation", { name: "Logs views" }).getByRole("button")).toHaveText(["Sessions", "Analysis"]);
  await dest(page, "More").click();
  await expect(page.getByRole("button", { name: /^Preferences/ })).toBeVisible();
  await expect(page.getByRole("button", { name: "Connect", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Capabilities" })).toHaveCount(0);
});

test("strip: no title, fits 360 px; Diagnose: one Module control, % mapped only in Experimental", async ({ page }) => {
  await returningUser(page);
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto("/");
  const strip = page.locator("header");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await expect(page).toHaveTitle("Ostler"); // the document title, as the Web App Manifest's name
  await expect(strip.getByText(/D2 Diag|Ostler/)).toHaveCount(0);
  await expect(strip.getByRole("combobox")).toHaveCount(0); // module select moved to Diagnose
  const fits = async () => strip.evaluate((h) => h.scrollWidth <= h.clientWidth);
  expect(await fits()).toBe(true);
  const barFits = () => page.locator("nav.bar").evaluate((n) => n.scrollWidth <= n.clientWidth);
  expect(await barFits()).toBe(true);
  await dest(page, "Diagnose").click();
  const id = page.locator(".diag-id");
  await expect(id.getByRole("combobox", { name: "Module" })).toBeVisible();
  await expect(id.locator(".modctl-v")).toHaveText("TD5 (engine)");
  await expect(id.locator(".mappct")).toHaveCount(0);
  // Rewind lives in Logs now, with its word
  await dest(page, "Logs").click();
  await expect(page.getByRole("button", { name: "Rewind" })).toBeVisible();
  await page.setViewportSize({ width: 393, height: 852 });
  expect(await fits()).toBe(true);
  expect(await barFits()).toBe(true);
  await page.setViewportSize({ width: 360, height: 780 });

  await page.addInitScript(() => localStorage.setItem("d2diag.v2",
    JSON.stringify({ consentDone: true, share: false, trust: "experimental" })));
  await page.reload();
  await dest(page, "Diagnose").click();
  await expect(id.locator(".mappct")).toHaveText(/^\d+% mapped$/);
  expect(await fits()).toBe(true);
  // Experimental lists every module, named ABBR (plain words)
  const select = id.getByRole("combobox", { name: "Module" });
  await expect(select.locator('option[value="autobox"]')).toHaveText("EAT (auto gearbox)");
  await expect(select.locator('option[value="airbag"]')).toHaveText("SRS (airbag)");
  await page.screenshot({ path: "test-results/header-360.png" });
});

// The e2e server is connected and recording: Rewind opens the drive in progress at its newest
// sample and follows it as each 5 s refresh grows it (spec §8).
test("Rewind opens the drive in progress on Analysis in replay; Exit to live returns", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await dest(page, "Logs").click(); // Rewind moved from the header to Logs (U1)
  const rewind = page.getByRole("button", { name: "Rewind" });
  await expect(rewind).toBeEnabled();
  await rewind.click();
  const exit = page.locator("header").getByRole("button", { name: "Replay — Exit to live" });
  await expect(exit).toBeVisible();
  await expect(exit).toContainText("Replay");
  await expect(page.getByRole("region", { name: "Replay" })).toHaveCount(0); // no top banner
  await expect(page.getByRole("navigation", { name: "Logs views" }).getByRole("button", { name: "Analysis" }))
    .toHaveAttribute("aria-current", "page");
  await expect(rewind).toHaveCount(0); // Exit to live takes its place
  const slider = page.getByTestId("global-transport").getByRole("slider", { name: "Playback position" });
  // read both in one go (a refresh between two reads would split them)
  const at = () => slider.evaluate((el) => {
    const r = el as unknown as { max: string; value: string };
    return { max: Number(r.max), value: Number(r.value) };
  });
  await expect.poll(async () => (await at()).max).toBeGreaterThan(0);
  const first = await at();
  expect(first.value).toBe(first.max); // at the newest sample, not 30 s back
  // following: the next refresh moves the end and the cursor with it
  await expect.poll(async () => (await at()).max, { timeout: 12_000 }).toBeGreaterThan(first.max);
  const later = await at();
  expect(later.value).toBeGreaterThan(first.value);
  expect(later.value).toBe(later.max);
  await page.screenshot({ path: "test-results/rewind-analysis.png" });
  await exit.click();
  await expect(exit).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await expect(rewind).toBeVisible();
});

test("switching to SLABS in Diagnose keeps the area", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await area(page, "Faults");
  await switchModule(page, "slabs");
  await expect(page.getByRole("heading", { name: "Faults" })).toBeVisible();
  await expect(page.locator(".screen-head")).toContainText("SLABS");
  await page.screenshot({ path: "test-results/faults-slabs.png", fullPage: true });
  // restore TD5: the test server is shared by every test
  await switchModule(page, "td5");
  await expect(page.locator(".screen-head")).toContainText("TD5");
});

// The sheet's immediate open with no connection (0 ms on load, 1 s into reconnecting, never in
// replay) is covered in vitest (state/connection.test.ts, App.test.tsx): this server is connected.
test("the connection pill opens the connection sheet", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Connected" }).click();
  const sheet = page.getByRole("dialog");
  await expect(sheet.getByText("Connection", { exact: true })).toBeVisible();
  await expect(sheet.getByText("10 400 baud · 8N1 · half duplex")).toBeVisible();
  // live only (ADR-0011): no Data source block, no Mock/Live switch, no mode row
  await expect(sheet.getByText("Data source")).toHaveCount(0);
  await expect(sheet.getByRole("button", { name: "Mock" })).toHaveCount(0);
  await expect(sheet.getByText("MODE", { exact: true })).toHaveCount(0);
  await page.screenshot({ path: "test-results/connection-sheet.png" });
  await sheet.getByRole("button", { name: "Done" }).click();
  await expect(sheet).toBeHidden();
});

test("Stable hides status chips and coverage; Experimental shows them", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await area(page, "Outputs");
  await expect(page.getByRole("heading", { name: "Outputs" })).toBeVisible();
  await expect(page.locator(".stag")).toHaveCount(0);
  await expect(page.getByTestId("coverage-bar")).toHaveCount(0);
  await dest(page, "More").click();
  await page.getByRole("button", { name: /^Preferences/ }).click();
  await page.getByRole("radio", { name: /Experimental/ }).click();
  await page.getByRole("button", { name: "Done" }).click();
  await area(page, "Outputs");
  await expect(page.getByText(/Experimental mode/)).toBeVisible();
  await expect(page.getByTestId("coverage-bar")).toBeVisible();
  await expect(page.locator(".stag").first()).toBeVisible();
  await page.screenshot({ path: "test-results/outputs-experimental.png", fullPage: true });
});

test("admin mode shows Decode with the live sniff and its help, Label, and the docs", async ({ browser }) => {
  const context = await browser.newContext({ httpCredentials: { username: "admin", password: "e2e" } });
  const page = await context.newPage();
  await returningUser(page);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Decode" })).toBeVisible();
  await expect(page.getByText(/match our values to the NanoCom/)).toBeVisible();
  await expect(page.getByRole("list", { name: "How it works" }).getByRole("listitem")).toHaveCount(3);
  await expect(page.getByText(/NanoCom items decoded on TD5/)).toBeVisible();
  await expect(page.getByText(/ours: 7\d\d rpm/).first()).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Glossary" }).click();
  await expect(page.getByRole("region", { name: "Glossary terms" })).toContainText("ReadDataByLocalIdentifier");
  await page.screenshot({ path: "test-results/admin-decode.png", fullPage: false });
  await page.keyboard.press("Escape");
  await page.getByRole("navigation", { name: "Developer" }).getByRole("button", { name: "Label", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Label" })).toBeVisible();
  await expect(page.getByText(/teach the decoder what bytes mean/)).toBeVisible();
  await expect(page.getByText("Read a LID directly", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Docs" }).click();
  await page.getByRole("button", { name: /Test backlog/ }).first().click();
  await expect(page.locator("article.doc h1")).toContainText("Test backlog");
  await context.close();
});

test("admin requires the password", async ({ page }) => {
  const res = await page.goto("/admin");
  expect(res?.status()).toBe(401);
});

/** Returning user without the auto-dismiss handler (screenshots dismiss explicitly). */
async function consentOnly(page: Page, theme: "dark" | "light" = "dark") {
  await page.addInitScript((t) =>
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false, theme: t })), theme,
  );
}
const dismissIfShown = (page: Page) =>
  page.getByRole("button", { name: "Dismiss" }).click({ timeout: 3000 }).catch(() => undefined);


for (const scheme of ["dark", "light"] as const) {
  test(`screenshots in ${scheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: scheme, viewport: { width: 412, height: 915 }, deviceScaleFactor: 2 });
    const page = await context.newPage();
    await consentOnly(page, scheme);
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Vehicle status/ })).toBeVisible();
    await page.waitForTimeout(2500); // let the sparklines fill
    await dismissIfShown(page);
    await page.screenshot({ path: `test-results/${scheme}-drive-td5.png` });
    await area(page, "Inputs");
    await page.waitForTimeout(300);
    await page.screenshot({ path: `test-results/${scheme}-inputs.png` });
    await area(page, "Faults");
    await page.screenshot({ path: `test-results/${scheme}-faults.png` });
    await switchModule(page, "slabs");
    await dest(page, "Home").click();
    await dismissIfShown(page); // SLABS has its own stored faults
    await expect(page.getByRole("img", { name: /Wheel speeds/ })).toBeVisible();
    await page.waitForTimeout(1500);
    await dismissIfShown(page);
    await page.screenshot({ path: `test-results/${scheme}-drive-slabs.png`, fullPage: true });
    // leave the shared test server on TD5 for other tests
    await dismissIfShown(page);
    await switchModule(page, "td5");
    await expect(page.locator(".diag-id .modctl-v")).toHaveText("TD5 (engine)");
    await context.close();
  });
}


test("an unknown page gets the app's not-found view; an unknown API path the JSON 404", async ({ page, request }) => {
  await returningUser(page);
  const res = await page.goto("/no/such/page?x=1");
  expect(res?.status()).toBe(200); // the server answered the app shell (a deep link survives a reload)
  await expect(page.getByText("Page not found")).toBeVisible();
  await page.getByRole("link", { name: "Open the dashboard" }).click();
  await expect(page.getByRole("navigation", { name: "Destinations" })).toBeVisible();

  const api = await request.get("/no/such/page", { headers: { Accept: "application/json" } });
  expect(api.status()).toBe(404);
  expect(await api.json()).toEqual({ ok: false, error: "not found", code: "not_found" });
  const asset = await request.get("/assets/missing.js");
  expect(asset.status()).toBe(404);
  expect((await request.get("/snapshot?_=1")).status()).toBe(200); // a query string is fine
});

test("a session exports as GeoJSON and its replay data carries the trace and t0_utc", async ({ request }) => {
  const { sessions } = await (await request.get("/sessions")).json();
  const demo = sessions.find((s: { synthetic: boolean; has_gps: boolean }) => s.synthetic && s.has_gps);
  const res = await request.get(`/sessions/${demo.id}/export?fmt=geojson`);
  expect(res.status()).toBe(200);
  expect(res.headers()["content-type"]).toContain("application/geo+json");
  const fc = await res.json();
  expect(fc.type).toBe("FeatureCollection");
  expect(fc.features[0].geometry.type).toBe("LineString");
  const data = await (await request.get(`/sessions/${demo.id}/data?max=50`)).json();
  expect(data.trace.geometry.type).toBe("LineString");
  expect(data.trace.properties.t_ms).toHaveLength(data.trace.geometry.coordinates.length);
  expect(data.t0_utc).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
});
