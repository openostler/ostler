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
  const rpm = page.locator('.ro[data-signal="rpm"] .cv-num');
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
