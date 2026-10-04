import { describe, expect, it } from "vitest";
import sessionData from "../../api/fixtures/session-data.json";
import { SessionData } from "../../api/schemas";
import {
  bboxOf, bearing, BUCKETS, bucketOf, cursorAt, defaultTraceChannel, legendGradient, lineColorExpression,
  NO_VALUE_COLOR, RAMP, ramp, rangeOf, traceSegments,
} from "./trace";

const lum = (hex: string) => {
  const n = parseInt(hex.slice(1), 16);
  return 0.2126 * ((n >> 16) & 255) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255);
};

describe("trace colour buckets", () => {
  it("has 20 distinct colours, light → dark (sequential)", () => {
    expect(RAMP).toHaveLength(BUCKETS);
    expect(new Set(RAMP).size).toBe(BUCKETS);
    for (let i = 1; i < RAMP.length; i++) expect(lum(RAMP[i]!)).toBeLessThan(lum(RAMP[i - 1]!));
    expect(ramp(1)).toHaveLength(1);
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
