// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

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

async function openLogs(page: Page) {
  await page.getByRole("navigation", { name: "Destinations" }).getByRole("button", { name: "Logs", exact: true }).click();
  await expect(page.locator("button.replay-row").first()).toBeVisible();
}

/** A row the user may edit and delete: not a demo log and not being recorded (the e2e server
 * creates one, logs-at-scale spec Testing). */
const ownRows = (page: Page) =>
  page.locator("button.replay-row").filter({ hasNot: page.locator(".replay-chip-demo") }).filter({ hasNot: page.locator(".replay-chip-live") });

/** A destination in the rail or bottom bar, or (Sessions, Analysis) a view inside Logs. */
const navButton = (page: Page, name: string) =>
  page.getByRole("navigation", { name: name === "Analysis" || name === "Sessions" ? "Logs views" : "Destinations" })
    .getByRole("button", { name, exact: true });

/** Open Logs and the synthetic demo session (always listed, ADR-0009): it lands on
 * Logs → Analysis (spec §7). */
async function openDemo(page: Page) {
  await openLogs(page);
  const demoRow = page.locator("button.replay-row", { hasText: "Demo log 1" }).first();
  await expect(demoRow).toBeVisible();
  await demoRow.click();
  await expect(navButton(page, "Analysis")).toHaveAttribute("aria-current", "page");
  await expect(page.getByRole("heading", { name: "Demo log 1" })).toBeVisible();
  // the global transport (on every tab while in replay)
  await expect(page.getByTestId("global-transport").getByRole("button", { name: "Play", exact: true })).toBeVisible();
}

test("the main chunk excludes maplibre; it loads only for a replay", async ({ page }) => {
  await returningUser(page);
  const requested: string[] = [];
  page.on("request", (r) => requested.push(r.url()));
  await page.goto("/");
  await expect(page.getByRole("navigation", { name: "Destinations" })).toBeVisible();
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
  // Night by default: no light slab behind the map, whatever the tiles do (visual spec §7)
  await expect(page.locator(".replay-map")).toHaveCSS("background-color", "rgb(11, 13, 16)");

  const now = page.getByTestId("clock-now");
  const start = await now.textContent();
  const scrubber = page.getByRole("slider", { name: "Playback position" });
  const max = Number(await scrubber.getAttribute("max"));
  await scrubber.fill(String(Math.round(max / 2)));
  await expect(now).not.toHaveText(start ?? "");
  const mid = await now.textContent();

  const play = page.getByRole("button", { name: "Play", exact: true });
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

test("opening a demo log lands on Analysis; the transport follows to another destination; Back to sessions returns to Logs", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);
  await expect(page.locator("[data-map-status]")).toBeVisible();
  await navButton(page, "Home").click();
  await expect(page.getByTestId("global-transport")).toBeVisible();
  await navButton(page, "Logs").click();
  await navButton(page, "Analysis").click();
  await page.getByRole("button", { name: "Back to sessions" }).click();
  await expect(navButton(page, "Logs")).toHaveAttribute("aria-current", "page");
  await expect(page.locator("button.replay-row").first()).toBeVisible();
  await expect(page.getByTestId("global-transport")).toHaveCount(0);
});

test("the demo logs are listed by name; search finds Demo log 2", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openLogs(page);
  const rows = page.locator("button.replay-row");
  await expect(rows.filter({ hasText: "Demo log 1" })).toHaveCount(1);
  await expect(rows.filter({ hasText: "Demo log 2" })).toHaveCount(1);
  await expect(page.getByText("Place names © OpenStreetMap contributors (ODbL) · GeoNames (CC BY 4.0)")).toBeVisible();

  await page.getByRole("searchbox", { name: "Search sessions" }).fill("Demo log 2");
  await expect(rows.filter({ hasText: "Demo log 1" })).toHaveCount(0);
  await expect(rows.filter({ hasText: "Demo log 2" })).toHaveCount(1);
  await page.getByRole("button", { name: "Clear", exact: true }).click();
  await expect(rows.filter({ hasText: "Demo log 1" })).toHaveCount(1);

  // the month scrubber shows when sessions span two months or more
  const scrub = page.getByRole("slider", { name: "Jump to month" });
  if (await scrub.count()) {
    await scrub.focus();
    await page.keyboard.press("End");
    await expect(page.getByRole("button", { name: "Back to newest" })).toBeVisible();
    await expect(rows.first()).toBeVisible();
    await page.getByRole("button", { name: "Back to newest" }).click();
  }
  await page.screenshot({ path: "test-results/logs-browser.png", fullPage: true });
});

// Automatic flags (spec §8) are derived in the UI, so they show on demo logs too.
test("Demo log 2 shows flag ticks; the chip opens the flag sheet (read-only on a demo)", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openLogs(page);
  await page.locator("button.replay-row", { hasText: "Demo log 2" }).first().click();
  await expect(page.getByRole("heading", { name: "Demo log 2" })).toBeVisible();
  const transport = page.getByTestId("global-transport");
  // ticks: buttons in the "Notes and flags" strip labelled "Warning at …" / "Alarm at …"
  const ticks = transport.getByRole("group", { name: "Notes and flags" }).getByRole("button", { name: /^(Warning|Alarm) at / });
  await expect(ticks.first()).toBeAttached();
  expect(await ticks.count()).toBeGreaterThan(0);
  await ticks.first().click();
  const chip = transport.locator("button[data-flag]");
  await expect(chip).toBeVisible();
  await chip.click();
  const sheet = page.getByRole("dialog");
  await expect(sheet.getByRole("button", { name: "Jump to" })).toBeVisible();
  await expect(sheet.getByRole("button", { name: "Keep as note" })).toHaveCount(0); // a demo log
  await page.screenshot({ path: "test-results/flag-sheet.png" });
  await page.keyboard.press("Escape");
  await expect(sheet).toHaveCount(0);
  // ⚑ is hidden on demo logs
  await expect(page.locator("header").getByRole("button", { name: "Mark at the cursor" })).toHaveCount(0);
});

test("a demo log's name is read-only", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openDemo(page);
  await expect(page.getByRole("heading", { name: "Demo log 1" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Edit Session name/ })).toHaveCount(0);
});

test("inline edit of a session's name and description", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openLogs(page);
  const own = ownRows(page);
  test.skip((await own.count()) === 0, "the server lists no editable (non-demo, idle) session");
  const id = await own.first().getAttribute("data-session");
  await own.first().click();
  await expect(navButton(page, "Analysis")).toHaveAttribute("aria-current", "page");
  await expect(page.getByTestId("global-transport")).toBeVisible();

  await page.getByRole("button", { name: /^Edit Session name/ }).click();
  const name = page.getByRole("textbox", { name: "Session name" });
  await name.fill("E2E test drive");
  await name.press("Enter");
  await expect(page.getByRole("heading", { name: /E2E test drive/ })).toBeVisible();

  await page.getByRole("button", { name: /^Edit Description/ }).click();
  const desc = page.getByRole("textbox", { name: "Description" });
  await desc.fill("Written by the e2e test.");
  await desc.press("Enter");
  await expect(page.getByText("Written by the e2e test.")).toBeVisible();

  // persisted: the browser lists it by its new name
  await page.getByRole("button", { name: "Back to sessions" }).click();
  await expect(page.locator(`button.replay-row[data-session="${id}"]`)).toContainText("E2E test drive");
});

// Last: it deletes the e2e server's editable session.
test("Delete on a non-demo session needs the word Delete", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  await openLogs(page);
  const own = ownRows(page);
  test.skip((await own.count()) === 0, "the server lists no deletable (non-demo, idle) session");
  const id = await own.first().getAttribute("data-session");
  await own.first().click();
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  const go = page.getByRole("button", { name: "Delete session" });
  const box = page.getByRole("textbox", { name: "Type Delete to confirm" });
  await box.fill("delete");
  await expect(go).toBeDisabled();
  await box.fill("Delete");
  await expect(go).toBeEnabled();
  await go.click();
  await expect(navButton(page, "Logs")).toHaveAttribute("aria-current", "page");
  await expect(page.locator("button.replay-row").first()).toBeVisible();
  await expect(page.locator(`button.replay-row[data-session="${id}"]`)).toHaveCount(0);
});
