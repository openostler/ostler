// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import sessionData from "../../api/fixtures/session-data.json";
import { SessionData } from "../../api/schemas";
import {
  bboxOf, bearing, BUCKETS, bucketOf, cursorAt, defaultTraceChannel, LANE_OFFSET, laneRamp, legendGradient, lineColorExpression,
  luminance, NO_VALUE_COLOR, offsetPolyline, RAMP, ramp, RAMPS, rangeOf, simplifyTrack, traceSegments,
} from "./trace";

/** WCAG contrast ratio between two colours. */
const contrast = (a: string, b: string) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x) as [number, number];
  return (hi + 0.05) / (lo + 0.05);
};

describe("trace colour buckets", () => {
  it.each(["plasma", "mako", "classicA", "classicB"] as const)("%s has 20 distinct colours", (name) => {
    expect(RAMPS[name]).toHaveLength(BUCKETS);
    expect(new Set(RAMPS[name]).size).toBe(BUCKETS);
    expect(ramp(1)).toHaveLength(1);
  });

  it.each(["plasma", "mako"] as const)("%s runs dark → light with strong end contrast and no near-black end", (name) => {
    const r = RAMPS[name];
    for (let i = 1; i < r.length; i++) expect(luminance(r[i]!)).toBeGreaterThan(luminance(r[i - 1]!));
    // bucket 0 vs 19: luminance difference and contrast ratio
    expect(luminance(r[19]!) - luminance(r[0]!)).toBeGreaterThan(0.6);
    expect(contrast(r[0]!, r[19]!)).toBeGreaterThan(7);
    // trimmed: the low end is not near black (pure black is 0; #1a1a1a is ≈ 0.010)
    expect(luminance(r[0]!)).toBeGreaterThan(0.03);
  });

  it("Classic colours are plain two-colour gradients: A blue → red, B green → purple", () => {
    expect(RAMPS.classicA[0]).toBe("#2166ac");
    expect(RAMPS.classicA[BUCKETS - 1]).toBe("#b2182b");
    expect(RAMPS.classicB[0]).toBe("#1b7837");
    expect(RAMPS.classicB[BUCKETS - 1]).toBe("#762a83");
  });

  it("trace A is plasma, B mako; Classic gives each lane its own two-colour gradient", () => {
    expect(RAMP).toBe(RAMPS.plasma);
    expect(laneRamp("a")).toBe(RAMPS.plasma);
    expect(laneRamp("b")).toBe(RAMPS.mako);
    expect(laneRamp("a", true)).toBe(RAMPS.classicA);
    expect(laneRamp("b", true)).toBe(RAMPS.classicB);
    for (let i = 0; i < BUCKETS; i++) expect(RAMPS.classicA[i]).not.toBe(RAMPS.classicB[i]);
    // the two lanes are told apart at every bucket (warm vs cool)
    for (let i = 0; i < BUCKETS; i++) expect(RAMPS.plasma[i]).not.toBe(RAMPS.mako[i]);
  });

  it("buckets values into 0…19, nulls to none, flat channels to the middle", () => {
    const r = { min: 0, max: 100 };
    expect(bucketOf(0, r)).toBe(0);
    expect(bucketOf(4.9, r)).toBe(0);
    expect(bucketOf(5, r)).toBe(1);
    expect(bucketOf(99.9, r)).toBe(19);
    expect(bucketOf(100, r)).toBe(19);
    expect(bucketOf(150, r)).toBe(19);
    expect(bucketOf(null, r)).toBeNull();
    expect(bucketOf(3, { min: 3, max: 3 })).toBe(10);
    expect(bucketOf(3, null)).toBeNull();
  });

  it("range ignores nulls", () => {
    expect(rangeOf([null, 3, -1, null, 8])).toEqual({ min: -1, max: 8 });
    expect(rangeOf([null])).toBeNull();
  });

  it("the line-color expression maps each bucket to its colour, else grey", () => {
    const e = lineColorExpression();
    expect(e[0]).toBe("match");
    expect(e[1]).toEqual(["get", "b"]);
    expect(e[2]).toBe(0);
    expect(e[3]).toBe(RAMP[0]);
    expect(e[2 + 2 * 19]).toBe(19);
    expect(e[3 + 2 * 19]).toBe(RAMP[19]);
    expect(e[e.length - 1]).toBe(NO_VALUE_COLOR);
  });

  it("the legend gradient runs the same ramp low → high", () => {
    const g = legendGradient();
    expect(g.startsWith("linear-gradient(to right, " + RAMP[0])).toBe(true);
    expect(g.endsWith(RAMP[19] + ")")).toBe(true);
  });
});

describe("trace segments", () => {
  const data = {
    t: [0, 1000, 2000, 3000, 4000],
    ch: { speed: [0, 0, 50, 100, null] as (number | null)[] },
    track: [[0, 0, 0], [0.001, 0, 1000], [0.002, 0, 2000], [0.003, 0, 3000], [0.004, 0, 4000]] as [number, number, number][],
  };

  it("merges runs of the same bucket and joins runs end to start", () => {
    const fc = traceSegments(data, "speed");
    expect(fc.features.map((f) => f.properties.b)).toEqual([0, 10, 19]);
    // 0 → 0 merged, then each run starts where the last ended
    expect(fc.features[0]!.geometry.coordinates).toEqual([[0, 0], [0.001, 0]]);
    expect(fc.features[1]!.geometry.coordinates[0]).toEqual([0.001, 0]);
    // the null at 4 s reads back to the last value (sparse rows), so it stays in bucket 19
    expect(fc.features[2]!.geometry.coordinates).toEqual([[0.002, 0], [0.003, 0], [0.004, 0]]);
  });

  it("a channel with no values draws the no-value colour (-1)", () => {
    const fc = traceSegments({ ...data, ch: {} }, "speed");
    expect(fc.features).toHaveLength(1);
    expect(fc.features[0]!.properties.b).toBe(-1);
  });

  it("works on the contract fixture", () => {
    const d = SessionData.parse(sessionData);
    const fc = traceSegments(d, "GPS_Speed");
    expect(fc.features.length).toBeGreaterThan(0);
    const lons = d.track.map((p) => p[0]);
    const lats = d.track.map((p) => p[1]);
    expect(bboxOf(d.track)).toEqual([Math.min(...lons), Math.min(...lats), Math.max(...lons), Math.max(...lats)]);
  });
});

describe("parallel lanes", () => {
  it("A sits 3 px left of the line, B 3 px right", () => {
    expect(LANE_OFFSET).toEqual({ a: -3, b: 3 });
  });

  it("offsets a straight line sideways by exactly d (right = +y when heading +x, screen y-down)", () => {
    const line: [number, number][] = [[0, 0], [10, 0], [20, 0]];
    expect(offsetPolyline(line, 3)).toEqual([[0, 3], [10, 3], [20, 3]]);
    const left = offsetPolyline(line, -3);
    left.forEach((p, i) => { expect(p[0]).toBeCloseTo(line[i]![0]); expect(p[1]).toBeCloseTo(-3); });
  });

  it("keeps the lanes parallel round a corner (each segment stays d away)", () => {
    const corner: [number, number][] = [[0, 0], [10, 0], [10, 10]];
    const o = offsetPolyline(corner, 3);
    // first segment y = 3, last segment x = 7 (right of travel going +y is −x)
    expect(o[0]![1]).toBeCloseTo(3);
    expect(o[1]![0]).toBeCloseTo(7);
    expect(o[1]![1]).toBeCloseTo(3);
    expect(o[2]![0]).toBeCloseTo(7);
    expect(offsetPolyline(corner, 0)).toEqual(corner);
  });

  it("Douglas–Peucker at ~1 m drops GPS jitter, keeps corners, ends and times", () => {
    const m = 1 / 111_320; // ≈ 1 m of latitude in degrees
    const track: [number, number, number][] = [];
    for (let i = 0; i <= 20; i++) track.push([0, i * 10 * m + (i % 2 ? 0.3 * m : 0), i * 1000]); // north, 30 cm zig-zag
    for (let i = 1; i <= 10; i++) track.push([i * 10 * m, 200 * m, 20_000 + i * 1000]); // then east
    const s = simplifyTrack(track, 1);
    expect(s[0]).toEqual(track[0]);
    expect(s[s.length - 1]).toEqual(track[track.length - 1]);
    expect(s.some((p) => p[2] === 20_000)).toBe(true); // the corner survives
    expect(s.length).toBeLessThanOrEqual(4);
    // a 5 m wiggle is real and survives
    const bump = [[0, 0, 0], [5 * m, 50 * m, 1000], [0, 100 * m, 2000]] as [number, number, number][];
    expect(simplifyTrack(bump, 1)).toHaveLength(3);
    expect(simplifyTrack([[0, 0, 0]], 1)).toHaveLength(1);
  });
});

describe("cursor", () => {
  it("bearing: north 0, east 90, south 180, west 270", () => {
    expect(bearing([0, 0], [0, 1])).toBeCloseTo(0);
    expect(bearing([0, 0], [1, 0])).toBeCloseTo(90);
    expect(bearing([0, 1], [0, 0])).toBeCloseTo(180);
    expect(bearing([1, 0], [0, 0])).toBeCloseTo(270);
  });

  it("interpolates position; heading from GPS_Heading, else the track", () => {
    const base = { t: [0, 1000], track: [[0, 0, 0], [0, 0.01, 1000]] as [number, number, number][] };
    const c = cursorAt({ ...base, ch: {} }, 500)!;
    expect(c.lat).toBeCloseTo(0.005);
    expect(c.heading).toBeCloseTo(0);
    expect(cursorAt({ ...base, ch: { GPS_Heading: [123, 124] } }, 500)!.heading).toBe(123);
    expect(cursorAt({ t: [], ch: {}, track: [] }, 0)).toBeNull();
  });

  it("default channel: speed, else GPS_Speed, else the first", () => {
    expect(defaultTraceChannel(["rpm", "GPS_Speed", "speed"])).toBe("speed");
    expect(defaultTraceChannel(["rpm", "GPS_Speed"])).toBe("GPS_Speed");
    expect(defaultTraceChannel(["rpm"])).toBe("rpm");
    expect(defaultTraceChannel([])).toBeNull();
  });
});
