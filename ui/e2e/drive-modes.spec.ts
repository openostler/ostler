// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { expect, test, type Page } from "@playwright/test";

/**
 * DM1 (specs/2026-10-07-drive-modes-and-editing-design.md §6, §10): the Drive-mode chip
 * switches modes (tap cycles the rotation, a long press lists ≤ 6, found by id, remembered per
 * display), the arrow keys switch faces and never the mode, Dashboard is the head-unit
 * default, hidden modes stay hidden, and every face of every preset fits one screen at every
 * head-unit size and the phone with the Moving rules: ≤ 6 tiles, digits ≥ 56 px, labels
 * ≥ 24 px, no glow, no animation or transition. The driving state is not known before U2, so
 * Drive mode renders the Moving sections (fail closed).
 */
const SIZES = [
  { w: 800, h: 480, cls: "hu5" }, { w: 1024, h: 600, cls: "hu7" }, { w: 1280, h: 720, cls: "hu9" },
  { w: 1280, h: 480, cls: "huwide" }, { w: 1920, h: 720, cls: "huwide" }, { w: 393, h: 852, cls: "phone" },
] as const;

/** The one-tap rotation after Dashboard per class (§5.9; HU-wide's Split / Media is hidden
 * without a media source). */
const ROTATION: Record<string, string[]> = {
  hu5: ["Map", "Diagnostic", "Minimal", "Dashboard"], hu7: ["Map", "Diagnostic", "Minimal", "Dashboard"],
  hu9: ["Map", "Diagnostic", "Minimal", "Dashboard"], huwide: ["Diagnostic", "Minimal", "Dashboard"],
  phone: ["Map", "Diagnostic", "Dashboard"],
};

/** Every preset with the faces it has (drive-modes spec §5.8), and the capability seam that
 * offers it (§10's ride and media-source fixtures; the list holds at most six). */
const PRESETS = [
  { query: "", presets: [{ name: "Dashboard", faces: 2 }, { name: "Map", faces: 1 }, { name: "Diagnostic", faces: 1 },
    { name: "Minimal", faces: 1 }, { name: "Off-road", faces: 2 }] },
  { query: "?caps=ride_active", presets: [{ name: "Convoy", faces: 2 }] },
  { query: "?caps=media_source", presets: [{ name: "Split", faces: 1 }] },
] as const;

type El = {
  scrollHeight: number; clientHeight: number; scrollWidth: number; clientWidth: number; dataset: Record<string, string>;
  textContent: string | null; closest(s: string): El | null;
  getBoundingClientRect(): { top: number; left: number; bottom: number; right: number; width: number; height: number };
};
type Win = {
  innerWidth: number; innerHeight: number;
  document: { querySelector(s: string): El | null; querySelectorAll(s: string): El[] };
  getComputedStyle(e: El): { fontSize: string; animationName: string; transitionDuration: string; visibility: string; display: string };
};

async function returningUser(page: Page, opts: { blockTiles?: boolean } = {}) {
  await page.addInitScript(() => {
    localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false }));
  });
  // the basemap host is out of reach in CI: the map pane falls back to the position on `bg`
  if (opts.blockTiles !== false) await page.route(/openfreemap\.org/, (r) => r.abort());
}

const strip = (page: Page) => page.getByRole("banner", { name: "Status" });
const chip = (page: Page) => page.locator('[data-chip="drive_mode"]');

async function openDrive(page: Page, query = "") {
  await page.goto(`/${query}`);
  await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
  await expect(page.getByRole("region", { name: "Drive mode" })).toBeVisible();
}

/** A long press on the chip (600 ms, ShellInput §5). */
async function longPress(page: Page) {
  const box = await chip(page).boundingBox();
  if (!box) throw new Error("no Drive-mode chip");
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.waitForTimeout(750);
  await page.mouse.up();
}

async function pickMode(page: Page, name: string) {
  await longPress(page);
  const list = page.getByRole("dialog");
  await list.getByRole("button", { name, exact: true }).click();
  await expect(list).toHaveCount(0);
  await expect(chip(page)).toHaveAccessibleName(`Drive mode: ${name}`);
}

for (const s of SIZES) {
  test.describe(`Drive modes at ${s.w}×${s.h}`, () => {
    test.use({ viewport: { width: s.w, height: s.h }, isMobile: s.w < 600, hasTouch: true });

    test("the Drive-mode chip: after Back, Dashboard by default, tap cycles, long press lists, remembered", async ({ page }) => {
      await returningUser(page);
      await page.goto("/");
      await expect(page.locator(".app")).toHaveAttribute("data-layout", s.cls);
      await expect(chip(page)).toHaveCount(0); // only in Drive mode
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();

      // found by id, right after Back, ≥ 48 px, Dashboard the default here (§5.9)
      await expect(chip(page)).toBeVisible();
      const ids = await strip(page).locator(".schip").evaluateAll((els) => els.map((e) => (e as unknown as El).dataset.chip ?? e.className));
      expect(String(ids[0])).toContain("schip-back");
      expect(ids[1]).toBe("drive_mode");
      const box = await chip(page).boundingBox();
      expect(box!.height).toBeGreaterThanOrEqual(48);
      await expect(chip(page)).toHaveText("Dashboard");
      // the Drive strip stays one row that never scrolls (§3.2, drive-modes §7.5)
      expect(await strip(page).evaluate((e) => {
        const el = e as unknown as El;
        return el.scrollWidth <= el.clientWidth + 1;
      })).toBe(true);

      // tap cycles the rotation (≤ 4) and the word follows
      const rotation = ROTATION[s.cls];
      for (const next of rotation) {
        await chip(page).click();
        await expect(chip(page)).toHaveText(next);
        await expect(page.locator(".dm")).toHaveAttribute("data-mode", `ostler.${next.toLowerCase()}`);
      }

      // a long press lists ≤ 6, current ticked; the hidden modes are absent (no ride, no media source)
      await longPress(page);
      const list = page.getByRole("dialog");
      const rows = list.locator(".dm-list-row");
      expect(await rows.count()).toBeLessThanOrEqual(6);
      await expect(rows.first()).toHaveText(/Dashboard/);
      await expect(list.locator('[aria-current="true"]')).toHaveText(/Dashboard/);
      await expect(list.getByRole("button", { name: "Convoy" })).toHaveCount(0);
      await expect(list.getByRole("button", { name: "Split" })).toHaveCount(0);
      await expect(list.getByText(/Edit modes/)).toHaveCount(0); // no editor in DM1, and never while Moving
      await list.getByRole("button", { name: "Off-road", exact: true }).click();
      await expect(chip(page)).toHaveText("Off-road");

      // the arrow keys switch faces, never the mode; closing the list returned focus to the chip
      // (ShellInput §4.3), where arrows move between chips, so `back` returns to the face (§14.2)
      await expect(chip(page)).toBeFocused();
      await page.keyboard.press("Escape");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "tilt");
      await page.keyboard.press("ArrowRight");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "trail");
      await page.keyboard.press("ArrowRight");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "tilt");
      await page.keyboard.press("ArrowLeft");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "trail");
      await expect(chip(page)).toHaveText("Off-road");

      // remembered per display, with its face
      await page.reload();
      await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
      await expect(chip(page)).toHaveText("Off-road");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "trail");
      // a tap from a mode outside the rotation (or at its end) goes to the rotation's start
      await chip(page).click();
      await expect(chip(page)).toHaveText("Dashboard");
    });

    test("keyboard: a short Enter on the chip cycles, a held Enter lists", async ({ page }) => {
      await returningUser(page);
      await openDrive(page);
      const next = ROTATION[s.cls][0]!;
      await chip(page).focus();
      await page.keyboard.press("Enter");
      await expect(chip(page)).toHaveText(next);
      await page.keyboard.down("Enter");
      await page.waitForTimeout(750);
      await page.keyboard.up("Enter");
      await expect(page.getByRole("dialog")).toBeVisible();
      await expect(chip(page)).toHaveText(next); // the long press did not also cycle
      // arrow keys inside the strip do not switch faces
      await page.keyboard.press("Escape");
      await pickMode(page, "Dashboard");
      await chip(page).focus();
      await page.keyboard.press("ArrowRight");
      await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "cluster");
    });

    test("every face of every preset fits one screen with the Moving rules", async ({ page }) => {
      test.setTimeout(120_000);
      await returningUser(page);
      const problems: string[] = [];
      for (const group of PRESETS) for (const p of group.presets) {
        if (p === group.presets[0]) await openDrive(page, group.query);
        await pickMode(page, p.name);
        for (let f = 0; f < p.faces; f++) {
          if (f > 0) await page.keyboard.press("ArrowRight");
          await page.waitForTimeout(400); // values land; the face steps ≤ 4 Hz
          const r = await page.evaluate(() => {
            const g = globalThis as unknown as Win;
            const main = g.document.querySelector("main")!;
            const face = g.document.querySelector(".dm-face")!;
            const px = (e: El) => parseFloat(g.getComputedStyle(e).fontSize);
            const shown = (e: El) => { const b = e.getBoundingClientRect(); return b.width > 0 && b.height > 0; };
            const all = [...g.document.querySelectorAll(".dm-face *")];
            const out = (e: El) => {
              const b = e.getBoundingClientRect();
              return b.top < -0.5 || b.left < -0.5 || b.bottom > g.innerHeight + 0.5 || b.right > g.innerWidth + 0.5;
            };
            return {
              face: face.dataset.face,
              moving: face.dataset.moving,
              scrolls: main.scrollHeight > main.clientHeight + 1 || main.scrollWidth > main.clientWidth + 1,
              outside: [...g.document.querySelectorAll(".dm-cell")].filter(out).map((e) => e.dataset.slot),
              // every widget stays inside its cell, so overlays never run into each other
              spill: [...g.document.querySelectorAll(".dm-cell > *")].filter((e) => {
                const c = e.closest(".dm-cell")!.getBoundingClientRect();
                const b = e.getBoundingClientRect();
                return b.left < c.left - 1 || b.top < c.top - 1 || b.right > c.right + 1 || b.bottom > c.bottom + 1;
              }).map((e) => e.closest(".dm-cell")!.dataset.slot),
              tiles: g.document.querySelectorAll(".dm-face .dm-tile").length + g.document.querySelectorAll(".dm-face .dm-line").length,
              small: [...g.document.querySelectorAll(".dm-face .dm-num, .dm-face .g2-num, .dm-face .dm-state, .dm-face .dm-line-text")]
                .filter(shown).filter((e) => px(e) < 56).map((e) => `${e.textContent}: ${px(e)}px`),
              labels: [...g.document.querySelectorAll(".dm-face .dm-label, .dm-face .dm-unit, .dm-face .dm-why, .dm-face .dm-source")]
                .filter(shown).filter((e) => px(e) < 24).map((e) => `${e.textContent}: ${px(e)}px`),
              clipped: [...g.document.querySelectorAll(".dm-face .dm-value")].filter((e) => e.scrollWidth > e.clientWidth + 1)
                .map((e) => e.textContent)
                .concat([...g.document.querySelectorAll(".dm-face .dm-tile")].filter((e) => e.scrollHeight > e.clientHeight + 1)
                  .map((e) => `${e.closest(".dm-cell")?.dataset.slot} (too tall)`)),
              glow: g.document.querySelectorAll(".dm-face [data-glow]").length,
              moves: all.filter((e) => {
                const cs = g.getComputedStyle(e);
                return cs.animationName !== "none" || cs.transitionDuration.split(",").some((d) => parseFloat(d) > 0);
              }).length,
            };
          });
          const where = `${p.name}/${r.face}`;
          if (r.moving !== "true") problems.push(`${where}: not the Moving section`);
          if (r.scrolls) problems.push(`${where}: main scrolls`);
          if (r.outside.length) problems.push(`${where}: outside the viewport: ${r.outside.join(", ")}`);
          if (r.spill.length) problems.push(`${where}: spills out of its cell: ${r.spill.join(", ")}`);
          if (r.tiles > 7) problems.push(`${where}: ${r.tiles} tiles`); // ≤ 6 tiles; a status line is one element worth two
          if (r.small.length) problems.push(`${where}: digits under 56 px: ${r.small.join("; ")}`);
          if (r.labels.length) problems.push(`${where}: labels under 24 px: ${r.labels.join("; ")}`);
          if (r.clipped.length) problems.push(`${where}: clipped: ${r.clipped.join("; ")}`);
          if (r.glow) problems.push(`${where}: glow`);
          if (r.moves) problems.push(`${where}: ${r.moves} animated or transitioning elements`);
          await page.screenshot({ path: `test-results/dm-${s.w}x${s.h}-${p.name.toLowerCase().replace(/[^a-z]/g, "")}-${r.face}.png` });
        }
      }
      expect(problems).toEqual([]);
    });

    test("the D2's honest states: no IMU, no SLABS session, no fuel level", async ({ page }) => {
      await returningUser(page);
      await openDrive(page);
      await pickMode(page, "Off-road");
      const face = page.locator(".dm-face");
      await expect(face.locator('[data-slot="pitch"]')).toContainText("Needs the node's IMU");
      await expect(face.locator('[data-slot="roll"]')).toContainText("Needs the node's IMU");
      // low range is read by SLABS; the Td5 holds the session
      await expect(face.locator('[data-slot="range"]')).toContainText("Not in this session");
      await expect(face.locator('[data-slot="range"] [title*="Read by SLABS"]')).toHaveCount(1);
      // the centre diff lock has no VSS leaf yet
      await expect(face.locator('[data-slot="range"]')).toContainText("Not available on this car");
      if (s.w === 1920) {
        await pickMode(page, "Dashboard");
        await expect(face.locator('[data-slot="fuel"]')).toContainText("Not available on this car");
      }
    });
  });
}

test.describe("Drive modes on a desktop", () => {
  test.use({ viewport: { width: 1440, height: 900 }, isMobile: false, hasTouch: false });

  test("Diagnostic is the default where no one drives, drawn as the full grid", async ({ page }) => {
    await returningUser(page);
    await page.goto("/?display=desktop");
    await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
    await expect(chip(page)).toHaveText("Diagnostic");
    await expect(page.locator(".dm-face")).toHaveAttribute("data-moving", "false");
    await expect(page.locator(".dm-face .tile")).toHaveCount(6);
  });
});

// DM2 (§8.3, §10 "the choice survives a reload per display and profile"): the selected mode
// lives on the server per display; localStorage is only the first paint and the offline fallback.
test.describe("Drive modes on the server", () => {
  test.use({ viewport: { width: 1024, height: 600 }, isMobile: false, hasTouch: true });
  const display = `e2e-${Date.now().toString(36)}`;
  const selection = `/ui/drive-mode/current/car/${display}/hu7`;

  test("the selected mode and face survive a reload with the browser's storage cleared", async ({ page, browser }) => {
    await returningUser(page);
    expect((await (await page.request.get(selection)).json()).selection).toBeNull();
    await openDrive(page, `?display_id=${display}`);
    await expect(chip(page)).toHaveText("Dashboard");
    await pickMode(page, "Off-road");
    await page.keyboard.press("Escape");
    await page.keyboard.press("ArrowRight");
    await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "trail");
    await expect.poll(async () => (await (await page.request.get(selection)).json()).selection)
      .toMatchObject({ mode: "ostler.offroad", faces: { "ostler.offroad": 1 } });

    // nothing left in this browser but the consent: only the server remembers
    await page.evaluate(() => {
      localStorage.removeItem("ostler.drive.v1");
      localStorage.removeItem("ostler.display.v1");
    });
    await page.reload();
    await page.locator(".home").getByRole("button", { name: "Drive", exact: true }).click();
    await expect(chip(page)).toHaveText("Off-road");
    await expect(page.locator(".dm-face")).toHaveAttribute("data-face", "trail");
    // another display (another browser) keeps its own default; the same display id elsewhere
    // (a kiosk's configured id) opens where this one was left
    const other = await browser.newContext({ viewport: { width: 1024, height: 600 }, hasTouch: true });
    const p2 = await other.newPage();
    await returningUser(p2);
    await openDrive(p2, `?display_id=${display}-other`);
    await expect(chip(p2)).toHaveText("Dashboard");
    await openDrive(p2, `?display_id=${display}`);
    await expect(chip(p2)).toHaveText("Off-road");
    await other.close();
  });

  test("Park to edit: a head unit's layout write is refused while the driving state is unknown", async ({ page }) => {
    const res = await page.request.put("/ui/layouts/current/car/hu7/drive_mode/user.e2e", {
      headers: { "Ostler-Layout-Class": "hu7", "Content-Type": "application/json" },
      data: { format: "ostler.layout/1", kind: "drive_mode", id: "user.e2e", name: "x", classes: {} },
    });
    expect(res.status()).toBe(409);
    expect(await res.json()).toMatchObject({ ok: false, code: "park_to_edit", driving_state: "unknown" });
  });
});

// Screenshots for the owner (Night, the default theme): Dashboard and Map at HU-5, HU-7 and the phone.
for (const s of [{ w: 800, h: 480 }, { w: 1024, h: 600 }, { w: 393, h: 852 }] as const) {
  test(`screenshots: Dashboard and Map at ${s.w}×${s.h}`, async ({ browser }) => {
    const page = await browser.newPage({ viewport: { width: s.w, height: s.h }, isMobile: s.w < 600, hasTouch: true, colorScheme: "dark" });
    await returningUser(page);
    await openDrive(page);
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `test-results/dm-shot-dashboard-${s.w}x${s.h}.png` });
    await pickMode(page, "Map");
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `test-results/dm-shot-map-${s.w}x${s.h}.png` });
    await page.close();
  });
}
