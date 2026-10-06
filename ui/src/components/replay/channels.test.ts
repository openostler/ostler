// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { afterEach, describe, expect, it } from "vitest";
import sessionsFx from "../../api/fixtures/sessions.json";
import type { SessionMeta } from "../../api/schemas";
import {
  categories, categoryOf, DEFAULT_PINS, groupChannels, highlight, loadPins, loadRecent, MAX_RECENT, pickerChannels, PINS_KEY,
  pushRecent, searchChannels, togglePin, type PickerChannel,
} from "./channels";

const demo = sessionsFx.sessions[0] as unknown as SessionMeta;

afterEach(() => localStorage.clear());

describe("picker categories", () => {
  it("maps raw groups (any case) to the spec's categories", () => {
    expect(categoryOf("gps", "GPS_Speed")).toBe("GPS/Motion");
    expect(categoryOf("Engine", "rpm")).toBe("Engine");
    expect(categoryOf("Accelerator", "accel_pedal_pct")).toBe("Engine");
    expect(categoryOf("Fuelling", "inj_qty")).toBe("Fuelling");
    expect(categoryOf("temperatures", "coolant_temp")).toBe("Temperatures");
    expect(categoryOf("Electrical", "battery")).toBe("Electrical");
    expect(categoryOf("Inputs", "brake_switch")).toBe("Switches");
    expect(categoryOf("Wheels", "wheel_speed_fl")).toBe("Chassis/SLABS");
    expect(categoryOf("Ride height", "height_fl")).toBe("Chassis/SLABS");
    expect(categoryOf("accel", "LateralAcc")).toBe("Accelerometer");
    expect(categoryOf("", "InlineAcc")).toBe("Accelerometer");
    expect(categoryOf("", "GPS_Nsat")).toBe("GPS/Motion");
    expect(categoryOf("mystery", "x")).toBe("Other");
  });

  it("groups a session's channels in category order, dropping empty categories", () => {
    const names = demo.channels.map((c) => c.name).filter((n) => !n.startsWith("GPS_L"));
    const rows = pickerChannels(demo, names, {});
    const groups = groupChannels(rows);
    const order = groups.map((g) => g.category);
    expect(order).toEqual([...order].sort((a, b) => categories().indexOf(a) - categories().indexOf(b)));
    expect(order[0]).toBe("GPS/Motion");
    expect(groups.find((g) => g.category === "Engine")!.rows.map((r) => r.name)).toEqual(["rpm", "speed", "manifold_press", "accel_pedal_pct"]);
    expect(groups.find((g) => g.category === "Temperatures")!.rows.map((r) => r.name)).toEqual(["coolant_temp", "air_temp"]);
    expect(rows.find((r) => r.name === "coolant_temp")!.unit).toBe("°C");
    // labels from /fields when known
    expect(pickerChannels(demo, ["rpm"], { rpm: { label: "Engine speed" } as never })[0]!.label).toBe("Engine speed");
  });
});

describe("picker search", () => {
  const rows: PickerChannel[] = [
    { name: "coolant_temp", label: "Coolant temperature", unit: "°C", category: "Temperatures" },
    { name: "rpm", label: "Engine speed", unit: "rpm", category: "Engine" },
    { name: "GPS_Speed", label: "GPS speed", unit: "km/h", category: "GPS/Motion" },
  ];
  it("matches label, unit and name, every term, any case", () => {
    expect(searchChannels(rows, "speed").map((r) => r.name)).toEqual(["rpm", "GPS_Speed"]);
    expect(searchChannels(rows, "°c").map((r) => r.name)).toEqual(["coolant_temp"]);
    expect(searchChannels(rows, "coolant_TEMP").map((r) => r.name)).toEqual(["coolant_temp"]);
    expect(searchChannels(rows, "gps km/h").map((r) => r.name)).toEqual(["GPS_Speed"]);
    expect(searchChannels(rows, "  ")).toHaveLength(3);
    expect(searchChannels(rows, "boost")).toEqual([]);
  });
  it("highlights every matched piece", () => {
    expect(highlight("Engine speed", "speed")).toEqual([{ text: "Engine ", hit: false }, { text: "speed", hit: true }]);
    expect(highlight("GPS speed", "gp sp")).toEqual([
      { text: "GP", hit: true }, { text: "S ", hit: false }, { text: "sp", hit: true }, { text: "eed", hit: false },
    ]);
    expect(highlight("rpm", "")).toEqual([{ text: "rpm", hit: false }]);
  });
});

describe("pins and recents", () => {
  it("defaults: speed, rpm, accelerator pedal, LateralAcc (GPS_Speed only without ECU speed)", () => {
    expect(DEFAULT_PINS).toEqual(["speed", "GPS_Speed", "rpm", "accel_pedal_pct", "LateralAcc"]);
    expect(loadPins(["speed", "GPS_Speed", "rpm"])).toEqual(["speed", "rpm", "accel_pedal_pct", "LateralAcc"]);
    expect(loadPins(["GPS_Speed", "rpm"])).toEqual(["speed", "GPS_Speed", "rpm", "accel_pedal_pct", "LateralAcc"]);
  });
  it("a pin toggle persists the whole list (so removing a default sticks)", () => {
    const p = togglePin(loadPins(["speed"]), "rpm");
    expect(p).not.toContain("rpm");
    expect(loadPins(["speed"])).toEqual(p);
    expect(togglePin(p, "coolant_temp")).toContain("coolant_temp");
    expect(JSON.parse(localStorage.getItem(PINS_KEY)!)).toContain("coolant_temp");
  });
  it("recents: newest first, deduplicated, capped", () => {
    let r = loadRecent();
    for (const n of ["a", "b", "c", "a", "d", "e", "f", "g"]) r = pushRecent(r, n);
    expect(r).toEqual(["g", "f", "e", "d", "a", "c"]);
    expect(r).toHaveLength(MAX_RECENT);
    expect(loadRecent()).toEqual(r);
  });
  it("survives blocked or corrupt storage", () => {
    localStorage.setItem(PINS_KEY, "{not json");
    expect(loadPins(["speed"])).toContain("rpm");
  });
});
