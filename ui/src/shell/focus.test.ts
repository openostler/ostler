// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { afterEach, describe, expect, it } from "vitest";
import { lastSheetOpened, nearest, neighbours, ownsKeys, pick, pushLayer, resetFocusState, score, topLayer, type Rect } from "./focus";

const r = (x: number, y: number, w = 40, h = 40): Rect => ({ x, y, w, h });

/** The spatial scorer (shell input spec §4.2): the 90° cone and along + 2 × off-axis. */
describe("spatial navigation maths", () => {
  const from = r(100, 100);

  it("scores along the axis plus twice the off-axis distance", () => {
    expect(score(from, r(200, 100), "right")).toBe(100);
    expect(score(from, r(200, 130), "right")).toBe(100 + 2 * 30);
    expect(score(from, r(100, 0), "up")).toBe(100);
    expect(score(from, r(80, 250), "down")).toBe(150 + 2 * 20);
    expect(score(from, r(0, 100), "left")).toBe(100);
  });

  it("keeps only centres inside the direction's 90° cone, ahead of the item", () => {
    expect(score(from, r(200, 199), "right")).toBe(100 + 2 * 99); // just inside the 45° edge
    expect(score(from, r(200, 201), "right")).toBeNull(); // just outside
    expect(score(from, r(100, 100), "right")).toBeNull(); // the same place is not ahead
    expect(score(from, r(50, 100), "right")).toBeNull(); // behind
    expect(score(from, r(100, 300), "up")).toBeNull();
  });

  it("picks the nearest by score, not by straight-line distance (the TV rule)", () => {
    // a 3×2 tile grid: from the top-left tile, right is its row neighbour, down its column one
    const grid = [r(0, 0, 100, 80), r(120, 0, 100, 80), r(240, 0, 100, 80), r(0, 100, 100, 80), r(120, 100, 100, 80), r(240, 100, 100, 80)];
    const others = grid.slice(1);
    expect(pick(grid[0]!, others, "right")).toBe(0); // grid[1]
    expect(pick(grid[0]!, others, "down")).toBe(2); // grid[3]
    expect(pick(grid[0]!, others, "left")).toBe(-1); // the zone's edge
    expect(pick(grid[0]!, others, "up")).toBe(-1);
    // a far item straight ahead beats a nearer one off to the side
    expect(pick(r(0, 0), [r(60, 50), r(150, 0)], "right")).toBe(1);
    // equal scores keep document order
    expect(pick(r(100, 100), [r(200, 80), r(200, 120)], "right")).toBe(0);
  });

  it("crosses the rail and main on the driver side, and the strip above main", () => {
    // HU-7 with a right-hand rail: main 0–928, rail 928–1024, strip 0–56
    const rail = [r(936, 70, 80, 76), r(936, 160, 80, 76), r(936, 250, 80, 76)];
    const strip = [r(10, 4, 90, 48), r(110, 4, 120, 48), r(860, 4, 60, 48)];
    const item = r(700, 170, 200, 76); // a card near the rail, below the strip
    const all = [...rail, ...strip];
    expect(pick(item, all, "right")).toBe(1); // the rail item level with it
    expect(pick(item, all, "up")).toBe(5); // the strip chip above it
    expect(neighbours("rail", "up")).toEqual(["main", "strip"]); // the bar: up enters main, not the strip
    expect(neighbours("main", "up")).toEqual(["strip", "rail"]);
    expect(neighbours("main", "right")).toEqual(["rail", "strip"]);
    expect(neighbours("strip", "down")).toEqual(["main", "rail"]);
    expect(pick(rail[1]!, [...strip, item], "left")).toBe(3); // back into main
    expect(pick(rail[0]!, [...strip, item], "left")).toBe(2); // the top rail item is nearer the strip's last chip
  });

  it("lands on the item nearest a point when entering a zone with no memory", () => {
    expect(nearest({ x: 0, y: 0 }, [r(300, 300), r(10, 20), r(0, 400)])).toBe(1);
    expect(nearest({ x: 0, y: 0 }, [])).toBe(-1);
  });
});

describe("keys a control owns (§4.4, §10)", () => {
  const el = (html: string) => {
    const d = document.createElement("div");
    d.innerHTML = html;
    return d.firstElementChild!;
  };
  it("leaves text fields, selects, sliders and applications alone; buttons and checkboxes are ours", () => {
    expect(ownsKeys(el('<input type="text">'))).toBe(true);
    expect(ownsKeys(el('<input type="range">'))).toBe(true);
    expect(ownsKeys(el("<textarea></textarea>"))).toBe(true);
    expect(ownsKeys(el("<select></select>"))).toBe(true);
    expect(ownsKeys(el('<div role="slider"></div>'))).toBe(true);
    expect(ownsKeys(el('<div role="application"><button>x</button></div>').firstElementChild)).toBe(true);
    expect(ownsKeys(el("<button>x</button>"))).toBe(false);
    expect(ownsKeys(el('<input type="checkbox">'))).toBe(false);
    expect(ownsKeys(null)).toBe(false);
  });
});

describe("layers (§4.3, §5)", () => {
  afterEach(resetFocusState);

  it("closes the newest first and times the ok guard from the newest sheet", () => {
    const closed: string[] = [];
    const a = pushLayer(() => closed.push("a"), { sheet: true, now: 100 });
    const b = pushLayer(() => closed.push("popover"), { sheet: false, now: 300 });
    expect(lastSheetOpened()).toBe(100); // a popover does not start the guard
    topLayer()!.close();
    expect(closed).toEqual(["popover"]);
    b();
    topLayer()!.close();
    expect(closed).toEqual(["popover", "a"]);
    a();
    expect(topLayer()).toBeNull();
    expect(lastSheetOpened()).toBe(-Infinity);
  });

  it("returns focus to where it was when the layer opened", () => {
    const btn = document.createElement("button");
    document.body.append(btn);
    btn.focus();
    const off = pushLayer(() => undefined, { sheet: true });
    btn.blur();
    off();
    expect(document.activeElement).toBe(btn);
    btn.remove();
  });
});
