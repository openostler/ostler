import { describe, expect, it } from "vitest";
import { bandFractions, inBand, position, short } from "./range";

describe("range geometry", () => {
  it("places a value along the span and clamps at the ends", () => {
    expect(position(50, [0, 100])).toEqual({ f: 0.5, clamped: null });
    expect(position(-5, [0, 100])).toEqual({ f: 0, clamped: "low" });
    expect(position(130, [0, 100])).toEqual({ f: 1, clamped: "high" });
  });
  it("clips the normal band to the span", () => {
    expect(bandFractions([80, 100], [-20, 120])).toEqual([100 / 140, 120 / 140]);
    expect(bandFractions([-50, 200], [0, 100])).toEqual([0, 1]);
    expect(bandFractions(null, [0, 1])).toBeNull();
  });
  it("tells whether a value is healthy", () => {
    expect(inBand(91, [80, 100])).toBe(true);
    expect(inBand(105, [80, 100])).toBe(false);
    expect(inBand(1, null)).toBeNull();
  });
  it("shortens legend numbers", () => {
    expect(short(4800)).toBe("4.8k");
    expect(short(0.85)).toBe("0.85");
    expect(short(-20)).toBe("-20");
  });
});
