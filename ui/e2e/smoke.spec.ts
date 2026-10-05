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

test("first start asks for consent before anything else", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Before you connect")).toBeVisible();
  await page.getByRole("radio", { name: /Don't share/ }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Before you connect")).toBeHidden();
});

test("simulated live data streams into Drive and Inputs", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await expect(page.locator('[data-signal="battery"]')).toContainText("V");
  await page.screenshot({ path: "test-results/drive.png", fullPage: true });

  await page.getByRole("button", { name: "Inputs" }).click();
  await expect(page.getByText("Temperatures")).toBeVisible();
  const rpm = page.locator('.srow[data-signal="rpm"] .cv-num');
  const first = await rpm.textContent();
  await expect.poll(async () => rpm.textContent(), { timeout: 5000 }).not.toBe(first); // SSE updates
  await page.screenshot({ path: "test-results/inputs.png", fullPage: true });
});

/** Pick a module in the header dropdown and wait for the server to switch. */
async function switchModule(page: Page, id: string) {
  const select = page.getByRole("combobox", { name: "Module" });
  await expect(select.locator(`option[value="${id}"]`)).toHaveCount(1);
  await select.selectOption(id);
  await expect(select).toHaveValue(id);
}

test("the seven tabs, no Connect or Capabilities", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  const tabs = page.getByRole("navigation", { name: "Screens" }).getByRole("button");
  await expect(tabs).toHaveCount(7);
  for (const t of ["Drive", "Faults", "Inputs", "Outputs", "Settings", "Utilities", "Logs"]) {
    await expect(page.getByRole("navigation").getByRole("button", { name: t, exact: true })).toBeVisible();
  }
  await expect(page.getByRole("button", { name: "Connect", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Capabilities" })).toHaveCount(0);
});

test("header: no title, one Module control, % mapped only in Experimental, fits 360 px", async ({ page }) => {
  await returningUser(page);
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto("/");
  const header = page.locator("header");
  await expect(page.getByRole("button", { name: "Connected" })).toBeVisible();
  await expect(header.getByText("D2 Diag")).toHaveCount(0);
  await expect(header.getByRole("combobox", { name: "Module" })).toBeVisible();
  await expect(header.locator(".modctl-v")).toHaveText("TD5 (engine)");
  await expect(header.locator(".mappct")).toHaveCount(0);
  const fits = async () => header.evaluate((h) => h.scrollWidth <= h.clientWidth);
  expect(await fits()).toBe(true);
  // seven tabs fit without scrolling
  expect(await page.locator("nav.tabs").evaluate((n) => n.scrollWidth <= n.clientWidth)).toBe(true);

  await page.addInitScript(() => localStorage.setItem("d2diag.v2",
    JSON.stringify({ consentDone: true, share: false, trust: "experimental" })));
  await page.reload();
  await expect(header.locator(".mappct")).toHaveText(/^\d+% mapped$/);
  expect(await fits()).toBe(true);
  // Experimental lists every module, named ABBR (plain words)
  const select = header.getByRole("combobox", { name: "Module" });
  await expect(select.locator('option[value="autobox"]')).toHaveText("EAT (auto gearbox)");
  await expect(select.locator('option[value="airbag"]')).toHaveText("SRS (airbag)");
  await page.screenshot({ path: "test-results/header-360.png" });
});

test("switching to SLABS from the header keeps the tab", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await page.getByRole("navigation").getByRole("button", { name: "Faults", exact: true }).click();
  await switchModule(page, "slabs");
  await expect(page.getByRole("heading", { name: "Faults" })).toBeVisible();
  await expect(page.locator(".screen-head")).toContainText("SLABS");
  await page.screenshot({ path: "test-results/faults-slabs.png", fullPage: true });
  // restore TD5: the test server is shared by every test
  await switchModule(page, "motor");
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
  await page.getByRole("navigation").getByRole("button", { name: "Outputs", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Outputs" })).toBeVisible();
  await expect(page.locator(".stag")).toHaveCount(0);
  await expect(page.getByTestId("coverage-bar")).toHaveCount(0);
  await page.getByRole("button", { name: "Preferences" }).click();
  await page.getByRole("radio", { name: /Experimental/ }).click();
  await page.getByRole("button", { name: "Done" }).click();
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
  await page.getByRole("navigation").getByRole("button", { name: "Label", exact: true }).click();
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
async function consentOnly(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false })),
  );
}
const dismissIfShown = (page: Page) =>
  page.getByRole("button", { name: "Dismiss" }).click({ timeout: 3000 }).catch(() => undefined);

const nav = (page: Page, name: string) =>
  page.getByRole("navigation").getByRole("button", { name, exact: true });

for (const scheme of ["dark", "light"] as const) {
  test(`screenshots in ${scheme} mode`, async ({ browser }) => {
    const context = await browser.newContext({ colorScheme: scheme, viewport: { width: 412, height: 915 }, deviceScaleFactor: 2 });
    const page = await context.newPage();
    await consentOnly(page);
    await page.goto("/");
    await expect(page.getByRole("button", { name: /Vehicle status/ })).toBeVisible();
    await page.waitForTimeout(2500); // let the sparklines fill
    await dismissIfShown(page);
    await page.screenshot({ path: `test-results/${scheme}-drive-td5.png` });
    await nav(page, "Inputs").click();
    await page.waitForTimeout(300);
    await page.screenshot({ path: `test-results/${scheme}-inputs.png` });
    await nav(page, "Faults").click();
    await page.screenshot({ path: `test-results/${scheme}-faults.png` });
    await nav(page, "Drive").click();
    await switchModule(page, "slabs"); // the tab stays on Drive
    await dismissIfShown(page); // SLABS has its own stored faults
    await expect(page.getByRole("img", { name: /Wheel speeds/ })).toBeVisible();
    await page.waitForTimeout(1500);
    await dismissIfShown(page);
    await page.screenshot({ path: `test-results/${scheme}-drive-slabs.png`, fullPage: true });
    // leave the shared test server on TD5 for other tests
    await dismissIfShown(page);
    await switchModule(page, "motor");
    await expect(page.getByRole("heading", { name: "Drive" })).toBeVisible();
    await context.close();
  });
}

