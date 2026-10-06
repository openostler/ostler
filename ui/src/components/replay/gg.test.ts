// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { ggChannels, ggLimit, ggPoints, ggRings, ggXY } from "./gg";

describe("G-G panel maths", () => {
  it("prefers the accelerometer pair, falls back to GPS-derived, else none", () => {
    expect(ggChannels(["LateralAcc", "InlineAcc", "GPS_LatAcc", "GPS_LonAcc"])).toEqual({ lat: "LateralAcc", lon: "InlineAcc" });
    expect(ggChannels(["GPS_LatAcc", "GPS_LonAcc"])).toEqual({ lat: "GPS_LatAcc", lon: "GPS_LonAcc" });
    expect(ggChannels(["LateralAcc"])).toBeNull();
    expect(ggChannels(["rpm"])).toBeNull();
  });

  it("scales to the next 0.5 g ring, never under 1 g", () => {
    expect(ggLimit(0)).toBe(1);
    expect(ggLimit(0.3)).toBe(1);
    expect(ggLimit(1)).toBe(1);
    expect(ggLimit(1.01)).toBe(1.5);
    expect(ggLimit(1.6)).toBe(2);
    expect(ggLimit(NaN)).toBe(1);
    expect(ggRings(1)).toEqual([0.5, 1]);
    expect(ggRings(1.5)).toEqual([0.5, 1, 1.5]);
  });

  it("places a left turn left of centre and acceleration above it", () => {
    expect(ggXY(0, 0, 1, 200)).toEqual([100, 100]);
    expect(ggXY(1, 0, 1, 200)).toEqual([0, 100]); // +1 g lateral (left turn) → left edge
    expect(ggXY(-0.5, 0, 1, 200)).toEqual([150, 100]);
    expect(ggXY(0, 1, 2, 200)).toEqual([100, 50]); // +1 g inline at a 2 g limit → halfway up
    expect(ggXY(0, -1, 1, 200)).toEqual([100, 200]); // braking → bottom
  });

  it("takes rows with both values, carries speed forward, thins evenly", () => {
    const data = {
      t: [0, 100, 200, 300, 400],
      ch: { LateralAcc: [0.1, null, -0.7, 0.2, 0.3], InlineAcc: [0, 0.2, 0.4, null, -1.2], speed: [10, null, 30, null, null] },
    };
    const { points, maxAbs } = ggPoints(data, { lat: "LateralAcc", lon: "InlineAcc" }, "speed");
    expect(points.map((p) => p.t)).toEqual([0, 200, 400]);
    expect(points.map((p) => p.speed)).toEqual([10, 30, 30]);
    expect(maxAbs).toBeCloseTo(1.2);
    expect(ggLimit(maxAbs)).toBe(1.5);
    const many = { t: Array.from({ length: 5000 }, (_, i) => i), ch: { a: Array(5000).fill(0.1), b: Array(5000).fill(0.2) } };
    expect(ggPoints(many, { lat: "a", lon: "b" }, null, 1000).points).toHaveLength(1000);
  });
});
