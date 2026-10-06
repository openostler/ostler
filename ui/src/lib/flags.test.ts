// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { beforeEach, describe, expect, it } from "vitest";
import type { Field, SessionData } from "../api/schemas";
import {
  DEFAULT_FLAG_OPTIONS, FLAG_RULES, detectFlags, faultKey, loadFlagOptions, resetFlagOptionsCache, saveFlagOptions,
  visibleFlags, type Flag,
} from "./flags";

const field = (name: string, over: Partial<Field> = {}): Field => ({
  name, unit: "°C", c: "verified", limits: [-40, 130], label: `Sig ${name}`, group: "Engine", description: "",
  derived: false, span: [0, 100], normal: [20, 80], ...over,
});

/** 1 Hz session of `n` seconds; `vals(s)` gives each signal's value at second s. */
const session = (n: number, ch: Record<string, (s: number) => number | null>, faults?: (s: number) => string | null): SessionData => {
  const t = Array.from({ length: n }, (_, i) => i * 1000);
  const data: SessionData = {
    id: "s", t, t0_utc: null, trace: null, decimated: false,
    ch: Object.fromEntries(Object.entries(ch).map(([k, f]) => [k, t.map((_, i) => f(i))])),
  };
  if (faults) data.text = { faults: t.map((_, i) => faults(i)) };
  return data;
};

const inside = 50;
const between = (lo: number, hi: number, v: number) => (s: number) => (s >= lo && s < hi ? v : inside);

describe("detectFlags — out of range", () => {
  const fields = { a: field("a") };

  it("a 2 s spike is not a flag", () => {
    expect(detectFlags(session(60, { a: between(10, 12, 90) }), fields)).toEqual([]);
  });

  it("a 4 s excursion is one flag with its peak", () => {
    const data = session(60, { a: (s) => (s >= 10 && s < 15 ? [85, 90, 95, 88, 86][s - 10]! : inside) });
    const f = detectFlags(data, fields);
    expect(f).toHaveLength(1);
    expect(f[0]).toMatchObject({
      id: "range:a:10000", kind: "range", severity: "warn", t: 10_000, t_end: 14_000, signal: "a", unit: "°C",
      peak: 95, peakT: 12_000, band: [20, 80], limits: [-40, 130],
    });
    expect(f[0]!.label).toBe("Sig a 95.0 °C (normal 20–80)");
  });

  it("a low excursion takes the lowest value as the peak", () => {
    const data = session(60, { a: (s) => (s >= 10 && s < 15 ? [10, 5, 12, 15, 18][s - 10]! : inside) });
    expect(detectFlags(data, fields)[0]).toMatchObject({ peak: 5, peakT: 11_000 });
  });

  it("two excursions 5 s apart merge into one", () => {
    const data = session(60, { a: (s) => ((s >= 10 && s < 15) || (s >= 20 && s < 25) ? (s === 22 ? 99 : 90) : inside) });
    const f = detectFlags(data, fields);
    expect(f).toHaveLength(1);
    expect(f[0]).toMatchObject({ t: 10_000, t_end: 24_000, peak: 99, peakT: 22_000 });
  });

  it("excursions further apart than mergeGapMs stay separate", () => {
    const gap = FLAG_RULES.mergeGapMs / 1000 + 2;
    const data = session(80, { a: (s) => ((s >= 10 && s < 15) || (s >= 14 + gap && s < 19 + gap) ? 90 : inside) });
    expect(detectFlags(data, fields)).toHaveLength(2);
  });

  it("hovering at the edge within the deadband does not flap", () => {
    // deadband = 2 % of span 0–100 = 2: 79.5 is back inside normal but not past hi − db = 78
    const data = session(120, { a: (s) => (s < 10 ? inside : s % 2 ? 80.5 : 79.5) });
    const f = detectFlags(data, fields);
    expect(f).toHaveLength(1);
    expect(f[0]).toMatchObject({ t: 11_000, t_end: 119_000, peak: 80.5 });
  });

  it("the deadband uses normal when the field has no span", () => {
    // normal 20–80 span 60 → db 1.2: 78.5 is past hi − db, so the excursion ends
    const f = { a: field("a", { span: null }) };
    const data = session(60, { a: (s) => (s >= 10 && s < 15 ? 90 : s >= 15 && s < 17 ? 78.5 : s >= 17 && s < 22 ? 90 : inside) });
    expect(detectFlags(data, f)).toHaveLength(1); // ended, then a second excursion merged (gap 2 s)
    const g = session(60, { a: (s) => (s >= 10 && s < 15 ? 90 : s >= 15 && s < 17 ? 78.5 : inside) });
    expect(detectFlags(g, f)[0]).toMatchObject({ t_end: 14_000 });
  });

  it("a null gap longer than 5 s splits an excursion (each too short to flag)", () => {
    const data = session(60, { a: (s) => (s >= 10 && s < 12 ? 90 : s >= 12 && s < 19 ? null : s >= 19 && s < 21 ? 90 : inside) });
    expect(detectFlags(data, fields)).toEqual([]);
    // a short gap (≤ 5 s) keeps it one excursion
    const short = session(60, { a: (s) => (s >= 10 && s < 12 ? 90 : s >= 12 && s < 15 ? null : s >= 15 && s < 17 ? 90 : inside) });
    expect(detectFlags(short, fields)).toHaveLength(1);
  });

  it("is an alarm when the value leaves limits", () => {
    const f = { a: field("a", { limits: [0, 100] }) };
    expect(detectFlags(session(60, { a: between(10, 15, 105) }), f)[0]!.severity).toBe("alarm");
    expect(detectFlags(session(60, { a: between(10, 15, 95) }), f)[0]!.severity).toBe("warn");
    expect(detectFlags(session(60, { a: between(10, 15, 105) }), { a: field("a", { limits: null }) })[0]!.severity).toBe("warn");
  });

  it("runs to the end of the data when still outside", () => {
    const f = detectFlags(session(30, { a: (s) => (s >= 25 ? 90 : inside) }), fields);
    expect(f[0]).toMatchObject({ t: 25_000, t_end: 29_000 });
  });

  it("a value out of range from the first reading that only recovers is not flagged (warm-up)", () => {
    // a cold engine: 5 °C at the start, warming steadily into the band by 40 s
    expect(detectFlags(session(120, { a: (s) => Math.min(50, 5 + s) }), fields)).toEqual([]);
    // the engine not running yet: stuck at 0 for a while, then into the band
    expect(detectFlags(session(60, { a: (s) => (s < 20 ? 0 : inside) }), fields)).toEqual([]);
  });

  it("an excursion from the first reading that gets worse is still flagged", () => {
    const f = detectFlags(session(60, { a: (s) => (s < 10 ? 10 - s : inside) }), fields);
    expect(f).toMatchObject([{ t: 0, t_end: 9_000, peak: 1, peakT: 9_000 }]);
  });

  it("an excursion that starts after the first reading is flagged even if it only recovers", () => {
    const f = detectFlags(session(60, { a: (s) => (s >= 10 && s < 20 ? 5 + (s - 10) : inside) }), fields);
    expect(f).toMatchObject([{ t: 10_000, peak: 5 }]);
  });

  it("ignores fields without a normal band and fields not in the data", () => {
    const data = session(60, { a: between(10, 20, 90), b: between(10, 20, 90) });
    expect(detectFlags(data, { a: field("a", { normal: null }), c: field("c") })).toEqual([]);
  });

  it("treats decimated min/max pairs as points", () => {
    const t = [0, 0, 5000, 5000, 10_000, 10_000, 15_000, 15_000];
    const data: SessionData = { id: "s", t, t0_utc: null, trace: null, decimated: true,
      ch: { a: [50, 50, 50, 90, 85, 92, 50, 50] } };
    expect(detectFlags(data, fields)).toMatchObject([{ t: 5000, t_end: 10_000, peak: 92 }]);
  });

  it("folds a flood: 20 signals at once → floodMax kept + one folded", () => {
    const names = Array.from({ length: 20 }, (_, i) => `s${String(i).padStart(2, "0")}`);
    const fs = Object.fromEntries(names.map((n) => [n, field(n, n === "s19" ? { limits: [0, 85] } : {})]));
    const data = session(60, Object.fromEntries(names.map((n, i) => [n, between(10 + (i % 3), 20, 90)])));
    const f = detectFlags(data, fs);
    expect(f).toHaveLength(FLAG_RULES.floodMax + 1);
    const folded = f.find((x) => x.folded);
    expect(folded).toMatchObject({ kind: "range", folded: 20 - FLAG_RULES.floodMax, severity: "alarm", t_end: 19_000 });
    expect(folded!.label).toBe(`${20 - FLAG_RULES.floodMax} more out of range`);
    expect(folded!.id).toBe(`range:folded:${folded!.t}`);
    expect(f.map((x) => x.t)).toEqual([...f.map((x) => x.t)].sort((a, b) => a - b));
  });

  it("flags in separate windows are not folded", () => {
    const names = Array.from({ length: 8 }, (_, i) => `s${i}`);
    const fs = Object.fromEntries(names.map((n) => [n, field(n)]));
    const data = session(700, Object.fromEntries(names.map((n, i) => [n, between(10 + i * 70, 20 + i * 70, 90)])));
    const f = detectFlags(data, fs);
    expect(f).toHaveLength(8);
    expect(f.some((x) => x.folded)).toBe(false);
  });
});

describe("detectFlags — faults", () => {
  const A = "027: shuttle valve switch — electrical failure (Logged)";
  const Acur = "027: shuttle valve switch — electrical failure (Current)";
  const B = "031: pressure switch (Current)";

  it("a fault appearing mid-drive is one point flag", () => {
    const f = detectFlags(session(60, {}, (s) => (s < 20 ? "" : B)), {});
    expect(f).toEqual([{
      id: "fault:031:20000", kind: "fault", severity: "alarm", t: 20_000, t_end: null, label: "pressure switch",
      faults: [B], current: true,
    }]);
  });

  it("labels with faultText when known", () => {
    const f = detectFlags(session(60, {}, (s) => (s < 20 ? null : B)), {}, (raw) => (raw === B ? "P0380 Glow plug" : undefined));
    // first non-null row has B → the stored flag
    expect(f[0]).toMatchObject({ id: "fault:stored:20000", label: "P0380 Glow plug" });
  });

  it("codes present at the first read are one stored flag at the start", () => {
    const f = detectFlags(session(60, {}, (s) => (s < 3 ? null : `${A}; ${B}`)), {});
    expect(f).toEqual([{
      id: "fault:stored:3000", kind: "fault", severity: "alarm", t: 3000, t_end: null, label: "2 stored faults",
      faults: [A, B], current: true,
    }]);
    const one = detectFlags(session(60, {}, () => A), {});
    expect(one).toMatchObject([{ label: "shuttle valve switch — electrical failure", severity: "warn", current: false }]);
  });

  it("a Current ↔ Logged change is not a new flag", () => {
    const f = detectFlags(session(60, {}, (s) => (s < 10 ? "" : s < 20 ? A : s < 30 ? Acur : A)), {});
    expect(f).toHaveLength(1);
    expect(f[0]).toMatchObject({ t: 10_000, severity: "warn" });
    expect(faultKey(A)).toBe(faultKey(Acur));
  });

  it("a fault that clears and returns is not flagged again", () => {
    expect(detectFlags(session(60, {}, (s) => (s < 10 || (s >= 20 && s < 30) ? "" : B)), {})).toHaveLength(1);
  });

  it("no faults column → no fault flags; merged with range flags sorted by t", () => {
    expect(detectFlags(session(10, {}), {})).toEqual([]);
    const f = detectFlags(session(60, { a: between(30, 40, 90) }, (s) => (s < 5 ? "" : B)), { a: field("a") });
    expect(f.map((x) => x.kind)).toEqual(["fault", "range"]);
  });

  it("is fast for 3000 rows × 60 signals", () => {
    const names = Array.from({ length: 60 }, (_, i) => `s${i}`);
    const fs = Object.fromEntries(names.map((n) => [n, field(n)]));
    const data = session(3000, Object.fromEntries(names.map((n, i) => [n, (s: number) => 50 + 40 * Math.sin((s + i * 7) / 30)])));
    const t0 = performance.now();
    detectFlags(data, fs);
    expect(performance.now() - t0).toBeLessThan(200);
  });
});

describe("visibleFlags", () => {
  const flags: Flag[] = [
    { id: "range:a:0", kind: "range", severity: "warn", t: 0, t_end: 5000, label: "a", signal: "a" },
    { id: "range:b:0", kind: "range", severity: "warn", t: 0, t_end: 5000, label: "b", signal: "b" },
    { id: "range:folded:0", kind: "range", severity: "warn", t: 0, t_end: 5000, label: "2 more", folded: 2 },
    { id: "fault:031:0", kind: "fault", severity: "alarm", t: 0, t_end: null, label: "f" },
  ];
  it("respects the switches and muted sensors", () => {
    expect(visibleFlags(flags, DEFAULT_FLAG_OPTIONS)).toHaveLength(4);
    expect(visibleFlags(flags, { ...DEFAULT_FLAG_OPTIONS, range: false }).map((f) => f.id)).toEqual(["fault:031:0"]);
    expect(visibleFlags(flags, { ...DEFAULT_FLAG_OPTIONS, faults: false })).toHaveLength(3);
    expect(visibleFlags(flags, { ...DEFAULT_FLAG_OPTIONS, muted: ["a"] }).map((f) => f.id)).toEqual(["range:b:0", "range:folded:0", "fault:031:0"]);
  });
});

describe("flag options", () => {
  beforeEach(() => {
    localStorage.clear();
    resetFlagOptionsCache();
  });
  it("defaults, saves and reloads", () => {
    expect(loadFlagOptions()).toEqual(DEFAULT_FLAG_OPTIONS);
    saveFlagOptions({ manual: false, range: true, faults: false, muted: ["x"] });
    resetFlagOptionsCache();
    expect(loadFlagOptions()).toEqual({ manual: false, range: true, faults: false, muted: ["x"] });
  });
});
