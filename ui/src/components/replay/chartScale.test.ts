import { describe, expect, it } from "vitest";
import { lanePaths, msOf, niceTicks, noteSpans, viewFor, xOf, yRange, zoomAround, zoomTo } from "./chartScale";

/** A min/max-per-bucket reduction like the server's /data decimation (pairs share a time). */
function decimate(t: number[], v: number[], bucket: number) {
  const dt: number[] = [];
  const dv: number[] = [];
  for (let i = 0; i < t.length; i += bucket) {
    const sl = v.slice(i, i + bucket);
    const lo = Math.min(...sl);
    const hi = Math.max(...sl);
    dt.push(t[i]!, t[i]!);
    dv.push(sl.indexOf(lo) < sl.indexOf(hi) ? lo : hi, sl.indexOf(lo) < sl.indexOf(hi) ? hi : lo);
  }
  return { t: dt, v: dv };
}

describe("chart scaling is decimation-agnostic", () => {
  const t = Array.from({ length: 1000 }, (_, i) => i * 100);
  const v = t.map((ms) => Math.sin(ms / 3000) * 50 + 50 + (ms === 42_300 ? 40 : 0)); // one spike
  const d = decimate(t, v, 10);
  const view = { t0: 0, t1: 99_900 };

  it("keeps the same y-range (peaks survive)", () => {
    const full = yRange(t, v, view)!;
    const dec = yRange(d.t, d.v, view)!;
    expect(dec.lo).toBeCloseTo(full.lo, 6);
    expect(dec.hi).toBeCloseTo(full.hi, 6);
  });

  it("places a timestamp on the same pixel whatever the sample count", () => {
    const W = 400;
    const pFull = lanePaths(t, v, view, W, 60, { lo: 0, hi: 150 })[0]!;
    const pDec = lanePaths(d.t, d.v, view, W, 60, { lo: 0, hi: 150 })[0]!;
    // the sample at 42 000 ms is x = 168 in both
    expect(pFull.find(([x]) => Math.abs(x - xOf(42_000, view, W)) < 1e-9)).toBeTruthy();
    expect(pDec.find(([x]) => Math.abs(x - xOf(42_000, view, W)) < 1e-9)).toBeTruthy();
    expect(xOf(42_000, view, W)).toBeCloseTo(168.168, 2);
  });

  it("x ↔ ms round-trips and clamps", () => {
    expect(msOf(xOf(12_345, view, 400), view, 400)).toBeCloseTo(12_345);
    expect(msOf(-50, view, 400)).toBe(0);
    expect(msOf(9999, view, 400)).toBe(99_900);
  });
});

describe("nulls are gaps", () => {
  it("splits the line at a null, never drops to zero", () => {
    const runs = lanePaths([0, 1, 2, 3, 4], [1, 2, null, 4, 5], { t0: 0, t1: 4 }, 100, 10, { lo: 0, hi: 10 });
    expect(runs).toHaveLength(2);
    expect(runs[0]).toHaveLength(2);
    expect(runs[1]).toHaveLength(2);
  });

  it("an all-null channel has no range", () => {
    expect(yRange([0, 1], [null, null], { t0: 0, t1: 1 })).toBeNull();
    expect(yRange([0, 1], [3, 3], { t0: 0, t1: 1 })).toEqual({ lo: 2, hi: 4 });
  });
});

describe("zoom", () => {
  it("zoomTo orders, enforces a minimum width and stays inside the session", () => {
    expect(zoomTo(9000, 1000, 0, 60_000)).toEqual({ t0: 1000, t1: 9000 });
    expect(zoomTo(5000, 5100, 0, 60_000)).toEqual({ t0: 4050, t1: 6050 });
    expect(zoomTo(-100, 500, 0, 60_000)).toEqual({ t0: 0, t1: 2000 });
    expect(zoomTo(59_900, 60_000, 0, 60_000)).toEqual({ t0: 58_000, t1: 60_000 });
  });

  it("pinch zooms around a point", () => {
    expect(zoomAround({ t0: 0, t1: 20_000 }, 10_000, 0.5, 0, 60_000)).toEqual({ t0: 5000, t1: 15_000 });
  });

  it("the zoomed window pages to follow the cursor", () => {
    expect(viewFor(null, 5, 0, 100)).toEqual({ t0: 0, t1: 100 });
    const z = { t0: 0, t1: 10_000 };
    expect(viewFor(z, 5000, 0, 60_000)).toBe(z);
    expect(viewFor(z, 25_000, 0, 60_000)).toEqual({ t0: 20_000, t1: 30_000 });
  });

  it("nice ticks", () => {
    expect(niceTicks(0, 100, 4)).toEqual([0, 50, 100]);
    expect(niceTicks(0, 1, 5)).toEqual([0, 0.2, 0.4, 0.6, 0.8, 1]);
  });
});

describe("note markers", () => {
  const n = (id: string, t: number, t_end: number | null = null) =>
    ({ id, t, t_end, text: "", tags: [], kind: "note", source: "retro", created: "" });
  it("points become lines, ranges bands, clipped to the view; out-of-view notes drop", () => {
    const spans = noteSpans([n("a", 500), n("b", 200, 1500), n("c", 5000)], { t0: 0, t1: 1000 }, 100);
    expect(spans.map((s) => [s.note.id, s.x0, s.x1])).toEqual([["a", 50, 50], ["b", 20, 100]]);
  });
});
