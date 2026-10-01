import { expect, test, type Page } from "@playwright/test";

/** Skip the first-start consent screen (stored per device, like a returning user), and
 * acknowledge the fault sheet whenever it pops up — the mock car has stored faults. */
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

test("live mock data streams into Drive and Inputs", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await expect(page.getByRole("status").filter({ hasText: "Connected" })).toBeVisible();
  await expect(page.locator('[data-signal="battery"]')).toContainText("V");
  await page.screenshot({ path: "test-results/drive.png", fullPage: true });

  await page.getByRole("button", { name: "Inputs" }).click();
  await expect(page.getByText("Temperatures")).toBeVisible();
  const rpm = page.locator('.srow[data-signal="rpm"] .cv-num');
  const first = await rpm.textContent();
  await expect.poll(async () => rpm.textContent(), { timeout: 5000 }).not.toBe(first); // SSE updates
  await page.screenshot({ path: "test-results/inputs.png", fullPage: true });
});

test("switching to SLABS and reading faults", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Connect" }).click();
  await page.getByRole("button", { name: /SLABS — ABS/ }).click();
  await expect(page.getByRole("heading", { name: "Faults" })).toBeVisible();
  await expect(page.locator("header")).toContainText("SLABS");
  await page.screenshot({ path: "test-results/faults-slabs.png", fullPage: true });
  // restore TD5: the mock server is shared by every test
  await page.getByRole("navigation").getByRole("button", { name: "Connect", exact: true }).click();
  await page.getByRole("button", { name: /TD5 — Engine/ }).click();
  await expect(page.locator("header")).toContainText("TD5");
});

test("admin mode shows coverage with the live sniff, and the docs", async ({ browser }) => {
  const context = await browser.newContext({ httpCredentials: { username: "admin", password: "e2e" } });
  const page = await context.newPage();
  await returningUser(page);
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "Map" })).toBeVisible();
  await expect(page.getByText(/reference-tool items mapped on TD5/)).toBeVisible();
  await expect(page.getByText(/ours: 7\d\d rpm/).first()).toBeVisible({ timeout: 10_000 });
  await page.screenshot({ path: "test-results/admin-map.png", fullPage: false });
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
    await nav(page, "Connect").click();
    await page.getByRole("button", { name: /SLABS — ABS/ }).click();
    await expect(page.getByRole("heading", { name: "Faults" })).toBeVisible(); // lands on Faults after a switch
    await dismissIfShown(page); // SLABS has its own stored faults
    await nav(page, "Drive").click();
    await expect(page.getByRole("img", { name: /Wheel speeds/ })).toBeVisible();
    await page.waitForTimeout(1500);
    await dismissIfShown(page);
    await page.screenshot({ path: `test-results/${scheme}-drive-slabs.png`, fullPage: true });
    // leave the shared mock server on TD5 for other tests
    await dismissIfShown(page);
    await nav(page, "Connect").click();
    await page.getByRole("button", { name: /TD5 — Engine/ }).click();
    await expect(page.getByRole("heading", { name: "Faults" })).toBeVisible();
    await context.close();
  });
}

