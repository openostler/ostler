import { expect, test, type Page } from "@playwright/test";

/** Returning user (consent done) who dismisses the mock car's fault sheet when it pops up. */
async function returningUser(page: Page) {
  await page.addInitScript(() =>
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false })),
  );
  await page.addLocatorHandler(page.getByRole("button", { name: "Dismiss" }), async (btn) => {
    await btn.click();
  });
}

/** Open the Logs tab and the synthetic demo session (always listed, ADR-0009). */
async function openDemo(page: Page) {
  await page.getByRole("navigation", { name: "Screens" }).getByRole("button", { name: "Logs", exact: true }).click();
  const demoRow = page.locator("button.replay-row", { hasText: "demo" }).first();
  await expect(demoRow).toBeVisible();
  await demoRow.click();
  await expect(page.getByRole("button", { name: "Play" })).toBeVisible();
}

test("the main chunk excludes maplibre; it loads only for a replay", async ({ page }) => {
  await returningUser(page);
  const requested: string[] = [];
  page.on("request", (r) => requested.push(r.url()));
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Screens" })).toBeVisible();
  expect(requested.filter((u) => /maplibre/i.test(u))).toEqual([]);
  await openDemo(page);
  await expect.poll(() => requested.some((u) => /maplibre/i.test(u))).toBe(true);
});

test("open the demo session, scrub, play and pause", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);

  // the map (or its no-WebGL stand-in) and the attribution when tiles are shown
  await expect(page.locator("[data-map-status]")).not.toHaveAttribute("data-map-status", "loading");

  const now = page.getByTestId("clock-now");
  const start = await now.textContent();
  const scrubber = page.getByRole("slider", { name: "Playback position" });
  const max = Number(await scrubber.getAttribute("max"));
  await scrubber.fill(String(Math.round(max / 2)));
  await expect(now).not.toHaveText(start ?? "");
  const mid = await now.textContent();

  const play = page.getByRole("button", { name: "Play" });
  await expect(play).toHaveAttribute("aria-pressed", "false");
  await play.click();
  await expect(play).toHaveAttribute("aria-pressed", "true");
  await expect.poll(async () => now.textContent(), { timeout: 5000 }).not.toBe(mid);
  await play.click();
  await expect(play).toHaveAttribute("aria-pressed", "false");
  const paused = await now.textContent();
  await page.waitForTimeout(1200);
  await expect(now).toHaveText(paused ?? "");

  await page.getByRole("button", { name: "Forward 10 seconds" }).click();
  await expect(now).not.toHaveText(paused ?? "");
  await page.screenshot({ path: "test-results/logs-replay.png", fullPage: true });
});

test("change the trace channel", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);
  const pick = page.getByRole("combobox", { name: "Trace channel" });
  const current = await pick.inputValue();
  const values = await pick.locator("option").evaluateAll((os) => os.map((o) => (o as unknown as { value: string }).value));
  // a channel with other units, so the legend range visibly changes (rpm in the demo drive)
  const next = values.includes("rpm") && current !== "rpm" ? "rpm" : values.find((v) => v !== current);
  expect(next).toBeTruthy();
  const maxBefore = await page.getByTestId("legend-max").textContent();
  await pick.selectOption(next!);
  await expect(pick).toHaveValue(next!);
  await expect(page.getByTestId("legend-max")).not.toHaveText(maxBefore ?? "");
  // the demo session is synthetic: never deletable
  await expect(page.getByRole("button", { name: "Delete" })).toHaveCount(0);
});
