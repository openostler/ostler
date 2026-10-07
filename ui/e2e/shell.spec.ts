// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

/**
 * U1 Shell (specs/2026-10-06-ui-architecture-design.md §3, §10, §12.3): the five reference
 * viewports, one per layout class, with target-size asserts (§2.4: 76 px head-unit targets; §3.2: strip
 * chips ≥ 48 px; WCAG 2.2 SC 2.5.8: nothing interactive under 24 × 24 px) and an axe scan
 * (WCAG 2.2 AA) of each destination per layout class.
 */
const VIEWPORTS = [
  { name: "HU-5", cls: "hu5", width: 800, height: 480, target: 76, phone: false },
  { name: "HU-7", cls: "hu7", width: 1024, height: 600, target: 76, phone: false },
  { name: "HU-9/10", cls: "hu9", width: 1280, height: 720, target: 76, phone: false },
  { name: "HU-wide", cls: "huwide", width: 1920, height: 720, target: 76, phone: false },
  { name: "Phone", cls: "phone", width: 393, height: 852, target: 48, phone: true },
] as const;

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

/** The page's globals these tests touch (the e2e tsconfig has no DOM lib). */
type Probe = {
  cspViolations: string[];
  document: { addEventListener(type: string, fn: (e: { violatedDirective: string; blockedURI: string }) => void): void;
    documentElement: { scrollWidth: number } };
  innerWidth: number;
  innerHeight: number;
};

async function returningUser(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false }));
    // CSP (app-model seam 7): record any violation so the test can fail on it
    const g = globalThis as unknown as Probe;
    g.cspViolations = [];
    g.document.addEventListener("securitypolicyviolation", (e) => g.cspViolations.push(`${e.violatedDirective} ${e.blockedURI}`));
  });
}

/** Every visible element's box, for the target-size asserts. */
async function boxes(loc: Locator) {
  const out: { name: string; w: number; h: number }[] = [];
  for (const el of await loc.all()) {
    if (!(await el.isVisible())) continue;
    const b = await el.boundingBox();
    if (!b) continue;
    out.push({ name: (await el.getAttribute("aria-label")) ?? (await el.innerText()).trim(), w: Math.round(b.width), h: Math.round(b.height) });
  }
  return out;
}
const under = (list: { name: string; w: number; h: number }[], w: number, h = w) =>
  list.filter((b) => b.w < w || b.h < h).map((b) => `${b.name}: ${b.w}×${b.h}`);

const nav = (page: Page) => page.getByRole("navigation", { name: "Destinations" });
const openDest = (page: Page, name: string) => nav(page).getByRole("button", { name, exact: true }).click();

async function axe(page: Page) {
  // The Logs year heatmap's day cells are 10 px by design (a year at a glance); WCAG 2.2 SC
  // 2.5.8 exempts them because the Dates filter beside it does the same job at full size.
  const r = await new AxeBuilder({ page }).withTags(WCAG).exclude(".logs-heat-grid").analyze();
  return r.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join(" | ")}`);
}

for (const vp of VIEWPORTS) {
  test.describe(`${vp.name} ${vp.width}×${vp.height}`, () => {
    test.use({ viewport: { width: vp.width, height: vp.height }, isMobile: vp.phone, hasTouch: true });

    test("the layout class, the strip and the rail or bottom bar", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      const app = page.locator(".app");
      await expect(app).toHaveAttribute("data-layout", vp.cls);
      const strip = page.getByRole("banner", { name: "Status" });
      await expect(strip.getByRole("button", { name: /^Connected/ })).toBeVisible();
      await expect(nav(page)).toHaveClass(vp.phone ? "bar" : "rail");
      const items = nav(page).getByRole("button");
      await expect(items).toHaveText(vp.phone ? ["Home", "Diagnose", "Logs", "More"] : ["Home", "Diagnose", "Logs", "More", "Drive"]);

      // the strip is one row that never scrolls; the rail never scrolls
      const fits = (l: Locator) => l.evaluate((e) => e.scrollWidth <= e.clientWidth && e.scrollHeight <= e.clientHeight);
      expect(await fits(strip)).toBe(true);
      expect(await fits(nav(page))).toBe(true);
      expect(await page.evaluate(() => {
        const g = globalThis as unknown as Probe;
        return g.document.documentElement.scrollWidth <= g.innerWidth;
      })).toBe(true);
      // the phone keeps chips 2–5 and 9 (§3.2): no 12 V or clock in its strip; HU-5 adds the clock (§12.3)
      await expect(strip.locator(".schip-battery, .schip-clock")).toHaveCount(vp.phone ? 0 : vp.cls === "hu5" ? 1 : 2);
      await page.screenshot({ path: `test-results/shell-${vp.cls}-home.png` });
    });

    test("target sizes: 76 px on head units, strip chips ≥ 48 px, nothing under 24 px", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      const strip = page.getByRole("banner", { name: "Status" });
      await expect(strip.getByRole("button", { name: /^Connected/ })).toBeVisible();
      expect(under(await boxes(strip.getByRole("button")), 48)).toEqual([]);
      // the rail's items are the head-unit target; the phone's bar is 72 px tall (§3.3)
      expect(under(await boxes(nav(page).getByRole("button")), vp.phone ? 72 : vp.target)).toEqual([]);
      expect(under(await boxes(page.locator(".home").getByRole("button", { name: "Drive", exact: true })), vp.target)).toEqual([]);

      await openDest(page, "Diagnose");
      const areas = page.getByRole("navigation", { name: "Areas" });
      await expect(areas).toBeVisible();
      expect(under(await boxes(areas.getByRole("button")), 24, vp.target)).toEqual([]);
      if (vp.cls === "hu9" || vp.cls === "huwide") {
        const systems = page.getByRole("navigation", { name: "Systems" });
        await expect(systems.getByRole("button").first()).toBeVisible();
        expect(under(await boxes(systems.getByRole("button")), vp.target)).toEqual([]);
      } else {
        expect(under(await boxes(page.locator(".diag-id .modctl")), 48)).toEqual([]);
      }

      await openDest(page, "More");
      expect(under(await boxes(page.locator(".morelist").getByRole("button")), 24, vp.target)).toEqual([]);

      // WCAG 2.2 SC 2.5.8 across the shell chrome
      const chrome = page.locator(".strip, nav, .subnav, .areas").getByRole("button");
      expect(under(await boxes(chrome), 24)).toEqual([]);
    });

    test("Drive mode: full screen with the strip, Back in the strip, no heading", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
      const mode = page.getByRole("region", { name: "Drive mode" });
      await expect(mode.locator(".tile").first()).toBeVisible();
      await expect(mode.getByRole("heading")).toHaveCount(0); // §12.3: no page chrome
      await expect(nav(page)).toHaveCount(0);
      const back = page.getByRole("banner", { name: "Status" }).getByRole("button", { name: "Back" });
      expect(under(await boxes(back), 48)).toEqual([]); // a strip chip (§3.2)
      await page.screenshot({ path: `test-results/shell-${vp.cls}-drive.png` });
      await back.click();
      await expect(nav(page)).toBeVisible();
    });

    test("axe finds no WCAG 2.2 AA violations on any destination or Drive mode", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      await expect(page.getByRole("banner", { name: "Status" }).getByRole("button", { name: /^Connected/ })).toBeVisible();
      await page.waitForTimeout(500); // let the first values and sparklines land
      const found: Record<string, string[]> = {};
      found.Home = await axe(page);
      for (const d of ["Diagnose", "Logs", "More"]) {
        await openDest(page, d);
        await expect(nav(page).getByRole("button", { name: d, exact: true })).toHaveAttribute("aria-current", "page");
        await page.waitForTimeout(300);
        found[d] = await axe(page);
      }
      await openDest(page, "Home");
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
      await expect(page.getByRole("region", { name: "Drive mode" })).toBeVisible();
      found["Drive mode"] = await axe(page);
      expect(found).toEqual({ Home: [], Diagnose: [], Logs: [], More: [], "Drive mode": [] });
      expect(await page.evaluate(() => (globalThis as unknown as Probe).cspViolations)).toEqual([]);
    });
  });
}

// §12.3 (UI audit P1, D6): Drive mode is one screen at every head-unit class and the phone —
// `main` never scrolls, and every tile (the red one included) is inside the viewport, unclipped.
const DRIVE_SIZES = [[800, 480], [1024, 600], [1280, 720], [1280, 480], [1920, 720], [393, 852]] as const;

for (const [width, height] of DRIVE_SIZES) {
  test.describe(`Drive mode fits ${width}×${height}`, () => {
    test.use({ viewport: { width, height }, isMobile: width < 600, hasTouch: true });

    test("main does not scroll and every tile is inside the viewport", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
      const tiles = page.getByRole("region", { name: "Drive mode" }).locator(".tile");
      await expect(tiles).toHaveCount(6);
      await expect(page.locator(".drivemode .tile.alarm").first()).toBeVisible(); // a critical tile: the replay's hot intake air
      await page.waitForTimeout(500); // let the values and sparklines land
      const fit = await page.evaluate(() => {
        type El = { scrollHeight: number; clientHeight: number; scrollWidth: number; clientWidth: number; dataset: Record<string, string>;
          getBoundingClientRect(): { top: number; left: number; bottom: number; right: number } };
        const g = globalThis as unknown as Probe & { document: { querySelector(s: string): El; querySelectorAll(s: string): El[] } };
        const main = g.document.querySelector("main");
        const out = (t: El) => {
          const r = t.getBoundingClientRect();
          return r.top < 0 || r.left < 0 || r.bottom > g.innerHeight + 0.5 || r.right > g.innerWidth + 0.5;
        };
        const tiles = [...g.document.querySelectorAll(".drivemode .tile")];
        return {
          scrolls: main.scrollHeight > main.clientHeight + 1,
          outside: tiles.filter(out).map((t) => t.dataset.signal),
          clipped: tiles.filter((t) => t.scrollHeight > t.clientHeight + 1 || t.scrollWidth > t.clientWidth + 1).map((t) => t.dataset.signal),
        };
      });
      expect(fit).toEqual({ scrolls: false, outside: [], clipped: [] });
      await page.screenshot({ path: `test-results/drive-fit-${width}x${height}.png` });
    });
  });
}

test("the built page allows scripts from its own origin only, and links the web app manifest", async ({ page, request }) => {
  await returningUser(page);
  await page.goto("/");
  const csp = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
  expect(csp).toContain("script-src 'self'");
  expect(await page.locator("script:not([src])").count()).toBe(0); // no inline script
  const href = await page.locator('link[rel="manifest"]').getAttribute("href");
  const res = await request.get(href ?? "");
  expect(res.status()).toBe(200);
  expect(res.headers()["content-type"]).toContain("application/manifest+json");
  const manifest = await res.json();
  expect(manifest).toMatchObject({ name: "Ostler", start_url: "/", display: "standalone" });
  expect(manifest.icons.length).toBeGreaterThan(0);
});

test("faults are a telltale in the strip, not a pop-up; tapping it opens the sheet", async ({ page }) => {
  await returningUser(page);
  await page.goto("/");
  const telltale = page.getByRole("banner", { name: "Status" }).locator(".schip-telltale");
  await expect(telltale).toBeVisible(); // the simulated car has stored faults
  await expect(telltale).toHaveText(/\d+ faults?/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await telltale.click();
  const sheet = page.getByRole("dialog");
  await expect(sheet.getByRole("button", { name: "Dismiss" })).toBeVisible();
  await sheet.getByRole("button", { name: "Dismiss" }).click();
  await expect(telltale).not.toHaveClass(/attention/);
});

// Night is the default (visual spec §1), so every axe scan above runs on it; the other themes
// must hold contrast too (spec §9: axe in every theme).
for (const theme of ["dim", "oled", "light"] as const) {
  test.describe(`${theme} theme`, () => {
    test.use({ viewport: { width: 1024, height: 600 }, isMobile: false });

    test(`axe finds no WCAG 2.2 AA violations on Home and Diagnose in the ${theme} theme`, async ({ page }) => {
      await returningUser(page);
      await page.addInitScript((t) => {
        localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false, theme: t }));
      }, theme);
      await page.goto("/");
      await expect(page.locator("html")).toHaveAttribute("data-theme", theme);
      await expect(page.getByRole("banner", { name: "Status" }).getByRole("button", { name: /^Connected/ })).toBeVisible();
      await page.waitForTimeout(500);
      const home = await axe(page);
      await openDest(page, "Diagnose");
      await expect(page.getByRole("navigation", { name: "Areas" })).toBeVisible();
      expect({ home, diagnose: await axe(page) }).toEqual({ home: [], diagnose: [] });
    });
  });
}
