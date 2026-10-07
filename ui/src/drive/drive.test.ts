// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { Field, Snapshot } from "../api/schemas";
import { packFixture } from "../test/packFixture";
import sizeTokens from "../../tokens/size.tokens.json";
import casesJson from "../../../tests/fixtures/layouts/cases.json";
import { compassPoint, levelOf, read, type BindContext } from "./bind";
import { showsMoving } from "./moving";
import { availableModes, defaultMode, defaultRotation, parseCaps, PRESETS } from "./presets";
import { facesFor, LIMITS, type Layout, type Limits } from "./types";
import { useDriveModes } from "./useDriveModes";
import { graphemes, ruleCodes, validateLayout } from "./validate";

type Case = { name: string; doc: unknown; errors: string[]; warnings: string[] };
// the same cases run through the server validator (tests/test_layouts.py)
const CASES = (casesJson as unknown as { cases: Case[] }).cases;
const CLASSES = ["hu5", "hu7", "hu9", "huwide", "phone", "tablet", "desktop"] as const;

describe("the ostler.layout/1 validator (drive-modes spec §8.2)", () => {
  it.each(CASES.map((c) => [c.name, c] as const))("%s", (_name, c) => {
    const r = validateLayout(c.doc);
    expect(ruleCodes(r)).toEqual(c.errors);
    for (const w of c.warnings) expect(r.warnings.map((i) => i.rule)).toContain(w);
  });

  it("refuses a class whose Moving type falls below 56 px digits or 24 px labels", () => {
    const good = CASES.find((c) => c.name === "valid three tiles on HU-7")!.doc;
    expect(ruleCodes(validateLayout(good))).toEqual([]);
    for (const [key, v] of [["digits", 48], ["label", 20]] as const) {
      const lim = JSON.parse(JSON.stringify(LIMITS)) as Limits;
      lim.classes.hu7.type[key] = v;
      expect(ruleCodes(validateLayout(good, undefined, lim))).toContain("moving.type_floor");
    }
  });

  it("refuses a file over 256 KB and counts graphemes, not code points", () => {
    expect(ruleCodes(validateLayout({}, 256 * 1024 + 1))).toContain("size.too_big");
    expect(graphemes("é")).toBe(1);
    expect(graphemes("Coolant")).toBe(7);
  });

  it("keeps the Moving type tokens in step with the shared limits, at or above the floors", () => {
    const layout = (sizeTokens as unknown as { layout: Record<string, Record<string, { $value: { value: number } }>> }).layout;
    for (const cls of CLASSES) {
      const t = LIMITS.classes[cls].type;
      expect(layout[cls]!["drive-num"]!.$value.value, cls).toBe(t.digits);
      expect(layout[cls]!["drive-label"]!.$value.value, cls).toBe(t.label);
      expect(layout[cls]!["drive-hero"]!.$value.value, cls).toBe(t.hero);
      expect(t.digits).toBeGreaterThanOrEqual(LIMITS.moving.digits_floor_px);
      expect(t.label).toBeGreaterThanOrEqual(LIMITS.moving.label_floor_px);
    }
  });
});

describe("the seven presets (§5)", () => {
  it("ship and validate for every class, with a Moving section wherever one is required", () => {
    expect(PRESETS.map((p) => p.id)).toEqual(["ostler.dashboard", "ostler.map", "ostler.diagnostic", "ostler.minimal",
      "ostler.offroad", "ostler.convoy", "ostler.split"]);
    for (const p of PRESETS) {
      expect(validateLayout(p).errors, p.id).toEqual([]);
      for (const cls of CLASSES) {
        const faces = facesFor(p, cls);
        expect(faces.length, `${p.id} ${cls}`).toBeGreaterThan(0);
        if (LIMITS.classes[cls].moving_required) for (const f of faces) expect(f.moving, `${p.id} ${cls} ${f.face}`).toBeDefined();
      }
    }
  });

  it("hide Convoy without a ride and Split / Media without a media source (§6)", () => {
    const none = availableModes(parseCaps(""));
    expect(none.map((m) => m.id)).not.toContain("ostler.convoy");
    expect(none.map((m) => m.id)).not.toContain("ostler.split");
    expect(availableModes(parseCaps("?caps=media_source,ride_active,bogus"))).toHaveLength(7);
  });

  it("default to Dashboard on head units and the phone, Diagnostic on tablet and desktop (§5.9)", () => {
    const caps = parseCaps("");
    for (const cls of ["hu5", "hu7", "hu9", "huwide", "phone"] as const) expect(defaultMode(cls, caps)).toBe("ostler.dashboard");
    expect(defaultMode("huwide", parseCaps("?caps=media_source"))).toBe("ostler.split");
    expect(defaultMode("desktop", caps)).toBe("ostler.diagnostic");
    expect(defaultRotation("hu7", caps)).toEqual(["ostler.dashboard", "ostler.map", "ostler.diagnostic", "ostler.minimal"]);
    expect(defaultRotation("huwide", caps)).toEqual(["ostler.dashboard", "ostler.diagnostic", "ostler.minimal"]);
    for (const cls of CLASSES) expect(defaultRotation(cls, caps).length).toBeLessThanOrEqual(4);
  });

  it("render the Moving section on driver-facing classes unless the head unit is known to be parked", () => {
    expect(showsMoving("hu7", "unknown")).toBe(true);
    expect(showsMoving("hu7", "moving")).toBe(true);
    expect(showsMoving("hu7", "parked")).toBe(false);
    expect(showsMoving("phone", "parked")).toBe(true);
    expect(showsMoving("desktop", "moving")).toBe(false);
  });
});

describe("bindings never invent a value (§4.2, ADR-0006)", () => {
  const field = (name: string, metric: string | null): Field => ({
    name, unit: "", c: "proven", limits: null, label: name, group: "x", description: "", derived: false, span: null, normal: null, metric,
  });
  const snap = (over: Partial<Snapshot> = {}): Snapshot => ({ status: "connected", signals: {}, faults: [], ts_utc: "", ...over }) as Snapshot;
  const ctx = (over: Partial<BindContext> = {}): BindContext => ({ snap: snap(), module: "td5", fields: {}, pack: packFixture, ...over });

  it("reads a field of the system in session by its VSS path", () => {
    const r = read({ path: "Vehicle.Speed" }, ctx({
      fields: { speed: field("speed", "Vehicle.Speed") }, snap: snap({ signals: { speed: { v: 42, u: "km/h" } } }),
    }));
    expect(r).toMatchObject({ state: "live", v: 42, unit: "km/h", name: "speed" });
  });

  it("falls back to GPS for speed, labelled by source", () => {
    const gps = { fix: true, lat: 1, lon: 2, speed_kmh: 30, heading: 10, alt_m: 300, sats: 8, hdop: 1, src: "mock", age_s: 0 };
    expect(read({ path: "Vehicle.Speed" }, ctx({ snap: snap({ gps }) }))).toMatchObject({ v: 30, source: "GPS" });
    expect(read({ path: "Vehicle.CurrentLocation.Altitude" }, ctx({ snap: snap({ gps }) }))).toMatchObject({ v: 300, source: "GPS" });
  });

  it("says why when there is no value: not in session, not on this car, no IMU", () => {
    expect(read({ path: "Vehicle.Powertrain.Transmission.IsLowRangeEngaged" }, ctx()))
      .toMatchObject({ state: "absent", v: null, why: "Not in this session", whyDetail: "Read by SLABS" });
    expect(read({ path: "Vehicle.Powertrain.FuelSystem.RelativeLevel" }, ctx())).toMatchObject({ v: null, why: "Not available on this car" });
    expect(read({ path: "Vehicle.Orientation.Roll" }, ctx())).toMatchObject({ v: null, why: "Needs the node's IMU" });
    expect(read({ pack: "lr_d2", signal: "slabs.height_fl" }, ctx())).toMatchObject({ why: "Not in this session" });
  });

  it("reads the pack's Drive tiles by position for the Diagnostic preset", () => {
    const r = read({ drive_tile: 0 }, ctx({ snap: snap({ signals: { manifold_press: { v: 1.2, u: "bar" } } }) }));
    expect(r).toMatchObject({ state: "live", v: 1.2, name: "manifold_press" });
    expect(r.tile?.label).toBe("Boost");
    expect(read({ drive_tile: 11 }, ctx()).state).toBe("absent");
  });

  it("levels and compass words", () => {
    expect(levelOf(115, { warning: [105, 112], critical: [112, null] })).toBe("critical");
    expect(levelOf(106, { warning: [105, 112], critical: [112, null] })).toBe("warning");
    expect(levelOf(90, { warning: [105, 112] })).toBeNull();
    expect(compassPoint(214)).toBe("SW");
    expect(compassPoint(359)).toBe("N");
  });
});

describe("the switcher's state (§6)", () => {
  const caps = parseCaps("");
  it("cycles the rotation, lists ≤ 6, steps faces with wrap, and remembers per display", () => {
    const { result, unmount } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps }));
    expect(result.current.active.id).toBe("ostler.dashboard");
    expect(result.current.list.length).toBeLessThanOrEqual(6);
    expect(result.current.list.slice(0, 4).map((m) => m.id)).toEqual(result.current.rotation.map((m) => m.id));
    act(() => result.current.cycle());
    expect(result.current.active.id).toBe("ostler.map");
    act(() => result.current.pick("ostler.offroad"));
    expect(result.current.active.id).toBe("ostler.offroad");
    act(() => result.current.stepFace(1));
    expect(result.current.faces[result.current.face]!.face).toBe("trail");
    act(() => result.current.stepFace(1));
    expect(result.current.face).toBe(0); // wraps
    act(() => result.current.stepFace(-1));
    expect(result.current.active.id).toBe("ostler.offroad"); // faces never change the mode
    unmount();
    // a new screen on the same display opens where it was left
    const again = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps }));
    expect(again.result.current.active.id).toBe("ostler.offroad");
    expect(again.result.current.faces[again.result.current.face]!.face).toBe("trail");
    // another display (class) keeps its own
    const phone = renderHook(() => useDriveModes({ cls: "phone", pack: "lr_d2", caps }));
    expect(phone.result.current.active.id).toBe("ostler.dashboard");
  });

  it("refuses a hidden mode and adds a pack-hinted mode to a short rotation", () => {
    const { result } = renderHook(() => useDriveModes({ cls: "phone", pack: "lr_d2", caps }));
    act(() => result.current.pick("ostler.split"));
    expect(result.current.active.id).toBe("ostler.dashboard");
    act(() => result.current.pick("ostler.offroad"));
    expect(result.current.rotation.map((m: Layout) => m.id)).toContain("ostler.offroad");
    expect(result.current.rotation.length).toBeLessThanOrEqual(4);
  });
});
