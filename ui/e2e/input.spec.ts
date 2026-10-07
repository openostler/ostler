// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * ShellInput I1 (specs/2026-10-07-shell-input-design.md §4–§7, §9, §13, §14), keyboard only:
 * at every layout class, every destination and the Drive menu are reached with the arrows,
 * Enter and Escape (Tab only to leave the page's own start); the focused item always wears the
 * ring (3 px accent outside a 2 px bg gap, no glow, no size change); Drive mode's `back` finds
 * the switcher by `data-chip="drive_mode"` wherever it sits; `back` reaches Home in ≤ 3
 * presses; a long `ok` on a rail item is reserved and activates nothing; confirm sheets open
 * with Cancel focused and ignore `ok` for 500 ms. The driving state is unknown before U2, which
 * counts as Moving on driver-facing classes (fail closed).
 */
const CLASSES = [
  { name: "HU-5", cls: "hu5", width: 800, height: 480, mobile: false, rail: true, driveItem: true },
  { name: "HU-7", cls: "hu7", width: 1024, height: 600, mobile: false, rail: true, driveItem: true },
  { name: "HU-9/10", cls: "hu9", width: 1280, height: 720, mobile: false, rail: true, driveItem: true },
  { name: "HU-wide", cls: "huwide", width: 1920, height: 720, mobile: false, rail: true, driveItem: true },
  { name: "Phone", cls: "phone", width: 393, height: 852, mobile: true, rail: false, driveItem: false },
  { name: "Tablet", cls: "tablet", width: 834, height: 1112, mobile: false, rail: true, driveItem: false },
  { name: "Desktop", cls: "desktop", width: 1440, height: 900, mobile: false, rail: true, driveItem: false },
] as const;

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const SHOTS = process.env.SHOTS_DIR ?? "test-results";

type El = {
  tagName: string; textContent: string | null; dataset: Record<string, string>; getAttribute(n: string): string | null;
  getBoundingClientRect(): { x: number; y: number; width: number; height: number };
  closest(s: string): El | null;
};
type Win = {
  document: { activeElement: El | null; body: El; documentElement: El };
  getComputedStyle(e: El): { outlineStyle: string; outlineWidth: string; outlineColor: string; outlineOffset: string; boxShadow: string; getPropertyValue(n: string): string };
};

async function returningUser(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false }));
  });
  await page.route(/openfreemap\.org/, (r) => r.abort()); // the map pane falls back offline
}

const nav = (page: Page) => page.getByRole("navigation", { name: "Destinations" });
const strip = (page: Page) => page.getByRole("banner", { name: "Status" });
const chip = (page: Page) => page.locator('[data-chip="drive_mode"]');

/** What has focus: its accessible name or text, and its zone. */
const focused = (page: Page) => page.evaluate(() => {
  const g = globalThis as unknown as Win;
  const a = g.document.activeElement;
  if (!a || a === g.document.body) return { name: "", zone: "" };
  return {
    name: (a.getAttribute("aria-label") ?? a.textContent ?? "").trim(),
    zone: a.closest("[data-zone]")?.getAttribute("data-zone") ?? "",
  };
});

/** The focus ring on the focused element (§9): computed style, against the theme's accent. */
const ring = (page: Page) => page.evaluate(() => {
  const g = globalThis as unknown as Win;
  const a = g.document.activeElement!;
  const cs = g.getComputedStyle(a);
  const probe = g.getComputedStyle(g.document.documentElement);
  return {
    style: cs.outlineStyle, width: cs.outlineWidth, color: cs.outlineColor, offset: cs.outlineOffset, shadow: cs.boxShadow,
    accent: probe.getPropertyValue("--accent").trim(),
  };
});

const hexToRgb = (h: string) => {
  const n = parseInt(h.replace("#", ""), 16);
  return `rgb(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255})`;
};

/** Assert the focused item wears the ring: 3 px solid accent, a 2 px gap, no blurred shadow. */
async function expectRing(page: Page) {
  const r = await ring(page);
  expect(r.style).toBe("solid");
  expect(r.width).toBe("3px");
  expect(r.color).toBe(hexToRgb(r.accent));
  expect(Math.abs(parseFloat(r.offset))).toBeGreaterThanOrEqual(2); // outside, or just inside the edge-tight chrome
  // the gap is a spread-only shadow in bg: blur 0, never a glow
  expect(r.shadow).toMatch(/^rgb\([^)]*\) 0px 0px 0px 2px( inset)?$/);
}

/** Hold a key for 600 ms+ (ShellInput's long press). */
async function hold(page: Page, key: string) {
  await page.keyboard.down(key);
  await page.waitForTimeout(700);
  await page.keyboard.up(key);
}

/** Tab (native order) until `target` has focus: how a keyboard user leaves the page start. */
async function tabTo(page: Page, target: Locator, max = 60) {
  for (let i = 0; i < max; i++) {
    if (await target.evaluate((e) => (globalThis as unknown as Win).document.activeElement === (e as unknown as El))) return;
    await page.keyboard.press("Tab");
  }
  throw new Error("not reached by Tab");
}

/** Arrow along the rail or bottom bar until the item named `name` has focus. */
async function arrowTo(page: Page, name: string, dir: "ArrowDown" | "ArrowUp" | "ArrowRight" | "ArrowLeft") {
  for (let i = 0; i < 8; i++) {
    if ((await focused(page)).name === name) return;
    await page.keyboard.press(dir);
  }
  expect((await focused(page)).name).toBe(name);
}

/** Arrow along the strip (left to its start, then right) until the chip matching `name` has focus. */
async function chipTo(page: Page, name: RegExp) {
  for (const dir of ["ArrowLeft", "ArrowRight"]) {
    for (let i = 0; i < 12 && !name.test((await focused(page)).name); i++) await page.keyboard.press(dir);
  }
  expect((await focused(page)).name).toMatch(name);
}

for (const c of CLASSES) {
  test.describe(`${c.name} ${c.width}×${c.height}, keyboard only`, () => {
    test.use({ viewport: { width: c.width, height: c.height }, isMobile: c.mobile, hasTouch: c.mobile });
    const query = c.cls === "desktop" || c.cls === "tablet" ? `?display=${c.cls}` : "";
    const along = c.rail ? "ArrowDown" : "ArrowRight";
    const backAlong = c.rail ? "ArrowUp" : "ArrowLeft";

    test("every destination, `back` to Home in ≤ 3 presses, and the Drive menu", async ({ page }) => {
      await returningUser(page);
      await page.goto(`/${query}`);
      await expect(page.locator(".app")).toHaveAttribute("data-layout", c.cls);
      await expect(strip(page).getByRole("button", { name: /^Connected/ })).toBeVisible();

      // into the rail: on a head unit an arrow starts in main; elsewhere Tab does; then the long
      // `back` (`menu`) jumps to the rail item of the destination shown (§4.3)
      if (c.cls.startsWith("hu")) await page.keyboard.press("ArrowDown");
      else await page.keyboard.press("Tab");
      expect((await focused(page)).zone).not.toBe("");
      await hold(page, "Escape");
      expect(await focused(page)).toEqual({ name: "Home", zone: "rail" });
      await expectRing(page);

      for (const d of ["Diagnose", "Logs", "More"]) {
        await arrowTo(page, d, along);
        await page.keyboard.press("Enter");
        await expect(nav(page).getByRole("button", { name: d, exact: true })).toHaveAttribute("aria-current", "page");
        expect((await focused(page)).name).toBe(d); // a short ok activates on release and keeps focus
      }

      // a long ok on a rail item is reserved for edit mode (§14.1, DM3): nothing activates
      await arrowTo(page, "Logs", backAlong);
      await hold(page, "Enter");
      await expect(nav(page).getByRole("button", { name: "More", exact: true })).toHaveAttribute("aria-current", "page");

      // `back` reaches Home in ≤ 3 presses from a page item (§4.3): page → rail → Home
      await arrowTo(page, "More", along);
      await page.keyboard.press(c.rail ? "ArrowLeft" : "ArrowUp"); // into main, across the driver side
      if (c.rail && (await focused(page)).zone !== "main") await page.keyboard.press("ArrowRight"); // a left-hand rail
      expect((await focused(page)).zone).toBe("main");
      await expectRing(page);
      await page.keyboard.press("Escape");
      expect(await focused(page)).toEqual({ name: "More", zone: "rail" });
      await page.keyboard.press("Escape");
      await expect(nav(page).getByRole("button", { name: "Home", exact: true })).toHaveAttribute("aria-current", "page");
      await expect.poll(async () => (await focused(page)).name).toBe("Home");

      // Drive mode: the rail's Drive item on head units, Home's Drive button elsewhere
      if (c.driveItem) {
        await arrowTo(page, "Drive", along);
        await page.keyboard.press("Enter");
      } else {
        await tabTo(page, page.locator(".home").getByRole("button", { name: "Drive", exact: true }));
        await page.keyboard.press("Enter");
      }
      await expect(page.getByRole("region", { name: "Drive mode" })).toBeVisible();
      await expect(page.getByRole("dialog")).toHaveCount(0); // entering did not also open the menu

      // `ok` opens the Drive menu: a short_list of ≤ 6 rows, ≤ 30 characters, one level (§6)
      await page.keyboard.press("Enter");
      const menu = page.getByRole("dialog");
      await expect(menu.getByRole("list", { name: "Drive menu" })).toBeVisible();
      const rows = menu.locator(".dm-list-row");
      const texts = (await rows.allInnerTexts()).map((t) => t.replace(/\s+/g, " ").trim());
      expect(texts.length).toBeGreaterThan(0);
      expect(texts.length).toBeLessThanOrEqual(6);
      for (const t of texts) expect([...t].length).toBeLessThanOrEqual(30);
      await expect(menu.locator("ul ul, [role=menu] [role=menu]")).toHaveCount(0);
      await expect(rows.first()).toBeFocused();
      await expectRing(page);
      // arrows stay in the sheet (the only trap), and `back` closes it
      for (let i = 0; i < texts.length + 2; i++) await page.keyboard.press("ArrowDown");
      expect((await focused(page)).zone).toBe("sheet");
      await page.keyboard.press("Escape");
      await expect(page.getByRole("dialog")).toHaveCount(0);
      await expect(page.getByRole("region", { name: "Drive mode" })).toBeVisible();
    });

    test("focus never resizes the item; axe passes with the ring on the strip, the rail and the Drive menu", async ({ page }) => {
      await returningUser(page);
      await page.goto(`/${query}`);
      await expect(strip(page).getByRole("button", { name: /^Connected/ })).toBeVisible();
      const link = strip(page).getByRole("button", { name: /^Connected/ });
      const before = await link.boundingBox();
      await page.keyboard.press(c.cls.startsWith("hu") ? "ArrowDown" : "Tab");
      await hold(page, "Escape"); // the rail
      // up the rail (or bar) and into the strip
      for (let i = 0; i < 8 && (await focused(page)).zone !== "strip"; i++) await page.keyboard.press("ArrowUp");
      await chipTo(page, /^Connected/);
      await expectRing(page);
      expect(await link.boundingBox()).toEqual(before); // no size change (§9)
      const scan = async () => (await new AxeBuilder({ page }).withTags(WCAG).exclude(".logs-heat-grid").analyze()).violations
        .map((v) => `${v.id}: ${v.nodes.slice(0, 2).map((n) => n.target.join(" ")).join(" | ")}`);
      expect(await scan()).toEqual([]);
    });
  });
}

// The Drive strip's switcher, found by id wherever it sits (§14.2–§14.4), at the head-unit classes.
for (const c of CLASSES.filter((x) => x.cls.startsWith("hu") || x.cls === "phone")) {
  test.describe(`${c.name}: Drive mode while Moving`, () => {
    test.use({ viewport: { width: c.width, height: c.height }, isMobile: c.mobile, hasTouch: c.mobile });

    test("one back from any face focuses drive_mode wherever it sits; one ok changes mode; left/right switch faces", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).focus();
      await page.keyboard.press("Enter");
      await expect(chip(page)).toHaveText("Dashboard");
      // the strip in a shuffled visual order (the editor that reorders it is DM3): the chip last
      await chip(page).evaluate((e) => { (e as unknown as { style: { order: string } }).style.order = "99"; });
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "cluster");
      await page.keyboard.press("ArrowRight"); // the face, not the strip
      await expect(page.locator(".dm-face")).not.toHaveAttribute("data-face", "cluster");
      await page.keyboard.press("Escape");
      await expect(chip(page)).toBeFocused();
      await expectRing(page);
      await page.keyboard.press("Enter");
      await expect(chip(page)).not.toHaveText("Dashboard");
      // left/right inside the strip move between chips and never switch faces
      const face = await page.locator(".dm-face").getAttribute("data-face");
      await page.keyboard.press("ArrowLeft");
      expect((await focused(page)).zone).toBe("strip");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", face!);
      // back from a chip other than the switcher goes to the switcher; from it, to the face
      await page.keyboard.press("Escape");
      await expect(chip(page)).toBeFocused();
      await page.keyboard.press("Escape");
      expect((await focused(page)).zone).toBe("main");
      // nothing scrolls under the arrows
      for (const k of ["ArrowUp", "ArrowDown", "ArrowDown"]) await page.keyboard.press(k);
      expect(await page.locator("main").evaluate((m) => (m as unknown as { scrollTop: number }).scrollTop)).toBe(0);
      await expect(page.getByRole("region", { name: "Drive mode" })).toBeVisible(); // never left while Moving
    });
  });
}

test.describe("confirm sheets (§7)", () => {
  test.use({ viewport: { width: 1024, height: 600 }, isMobile: false, hasTouch: false });

  test("open with Cancel focused, ignore ok for 500 ms, never count down", async ({ page }) => {
    await returningUser(page);
    const sent: string[] = [];
    page.on("request", (r) => { if (r.url().endsWith("/command")) sent.push(r.postData() ?? ""); });
    await page.goto("/");
    await nav(page).getByRole("button", { name: "Diagnose", exact: true }).focus();
    await page.keyboard.press("Enter");
    const clear = page.getByRole("button", { name: /Clear codes/ });
    await clear.focus(); // the simulated car has stored faults
    await page.keyboard.press("Enter");
    const sheet = page.getByRole("dialog");
    await expect(sheet.getByRole("button", { name: "Cancel" })).toBeFocused();
    await expectRing(page);
    // the confirm button is reached by an arrow; ok within 500 ms of opening does nothing
    await page.keyboard.press("ArrowRight");
    await expect(sheet.getByRole("button", { name: "Clear codes" })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(sheet).toBeVisible();
    expect(sent.filter((b) => b.includes("clear_faults"))).toEqual([]);
    // no countdown: no timer text or progress in the sheet, and it is still open later
    await expect(sheet.locator("progress, [role=progressbar], [role=timer]")).toHaveCount(0);
    await page.waitForTimeout(600);
    await expect(sheet).toBeVisible();
    expect(await sheet.innerText()).not.toMatch(/\b\d+\s?s\b/);
    // after the guard, ok on Cancel cancels; focus returns to Clear codes
    await page.keyboard.press("ArrowLeft");
    await expect(sheet.getByRole("button", { name: "Cancel" })).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(clear).toBeFocused();
    expect(sent.filter((b) => b.includes("clear_faults"))).toEqual([]);
  });
});

test("phone: arrows scroll the page until focus is on a focusable (Decision 8)", async ({ page }) => {
  await page.setViewportSize({ width: 393, height: 852 });
  await returningUser(page);
  await page.goto("/");
  await expect(strip(page).getByRole("button", { name: /^Connected/ })).toBeVisible();
  await page.keyboard.press("ArrowDown");
  expect((await focused(page)).zone).toBe("");
});

// Screenshots for the owner (Night): the ring on the strip and the rail, and the open Drive menu.
for (const s of [{ w: 800, h: 480 }, { w: 1024, h: 600 }] as const) {
  test(`screenshots: focus ring and Drive menu at ${s.w}×${s.h}`, async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: s.w, height: s.h }, colorScheme: "dark" });
    await returningUser(page);
    await page.goto("/");
    await expect(strip(page).getByRole("button", { name: /^Connected/ })).toBeVisible();
    await page.keyboard.press("ArrowDown");
    await hold(page, "Escape");
    await page.keyboard.press("ArrowDown");
    expect((await focused(page)).name).toBe("Diagnose");
    await page.waitForTimeout(300);
    await page.screenshot({ path: `${SHOTS}/focus-rail-${s.w}x${s.h}.png` });
    for (let i = 0; i < 8 && (await focused(page)).zone !== "strip"; i++) await page.keyboard.press("ArrowUp");
    await chipTo(page, /^Connected/);
    await page.screenshot({ path: `${SHOTS}/focus-strip-${s.w}x${s.h}.png` });
    await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).focus();
    await page.keyboard.press("Enter");
    await page.waitForTimeout(800);
    await page.keyboard.press("Enter");
    await expect(page.getByRole("list", { name: "Drive menu" })).toBeVisible();
    await page.screenshot({ path: `${SHOTS}/drive-menu-${s.w}x${s.h}.png` });
    await page.close();
  });
}
