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
  // the global transport (on every tab while in replay)
  await expect(page.getByTestId("global-transport").getByRole("button", { name: "Play" })).toBeVisible();
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

test("traces A and B through the channel picker, then the satellite toggle", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);
  await expect(page.locator("[data-map-status]")).not.toHaveAttribute("data-map-status", "loading");

  // trace A: change it to rpm (the legend range visibly changes units)
  const maxBefore = await page.getByTestId("legend-max").textContent();
  await page.getByRole("button", { name: /^Trace A:/ }).click();
  const sheet = page.getByRole("dialog");
  await sheet.getByRole("searchbox", { name: "Search channels" }).fill("rpm");
  await expect(sheet.locator("mark").first()).toBeVisible();
  await sheet.locator("[data-channel='rpm'] .cpick-pick").click();
  await expect(page.getByTestId("legend-max")).not.toHaveText(maxBefore ?? "");

  // trace B: added as a second lane from a pinned chip / the list
  await page.getByRole("button", { name: "+ Add trace" }).click();
  await page.getByRole("dialog").locator("[data-channel] .cpick-pick").first().click();
  await expect(page.getByRole("button", { name: /^Trace B:/ })).toBeVisible();
  await expect(page.getByTestId("legend-b-max")).toBeVisible();
  const status = await page.locator("[data-map-status]").getAttribute("data-map-status");
  if (status === "failed") await expect(page.locator(".replay-svg [data-lane]")).toHaveCount(2);

  // basemap switch (only over a live WebGL map): Satellite sticks across a reload
  if (status === "map") {
    const sat = page.getByRole("group", { name: "Basemap" }).getByRole("button", { name: "Satellite" });
    await sat.click();
    await expect(sat).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("[data-basemap]")).toHaveAttribute("data-basemap", "satellite");
    expect(await page.evaluate(() => localStorage.getItem("d2diag.basemap"))).toBe("satellite");
  }
  // the demo session is synthetic: never deletable, no note tool
  await expect(page.getByRole("button", { name: "Delete" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Drag to note" })).toHaveCount(0);
  await page.screenshot({ path: "test-results/logs-traces.png", fullPage: true });
});

test("the global transport follows to another tab; ‹ Sessions exits replay", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);
  const nav = page.getByRole("navigation", { name: "Screens" });
  await nav.getByRole("button", { name: "Drive", exact: true }).click();
  await expect(page.getByTestId("global-transport")).toBeVisible();
  await nav.getByRole("button", { name: "Logs", exact: true }).click();
  await page.getByRole("button", { name: "‹ Sessions" }).click();
  await expect(page.locator("button.replay-row").first()).toBeVisible();
  await expect(page.getByTestId("global-transport")).toHaveCount(0);
});
