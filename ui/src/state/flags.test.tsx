// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Field, SessionData } from "../api/schemas";
import { DEFAULT_FLAG_OPTIONS, resetFlagOptionsCache, saveFlagOptions } from "../lib/flags";
import { resetFlagMetaCache, useSessionFlags } from "./flags";

const field = (name: string): Field => ({
  name, unit: "°C", c: "verified", limits: [-40, 130], label: `Sig ${name}`, group: "Engine", description: "",
  derived: false, span: [0, 100], normal: [20, 80],
});

const t = Array.from({ length: 60 }, (_, i) => i * 1000);
const out = (from: number) => t.map((_, i) => (i >= from && i < from + 6 ? 90 : 50));
const DATA: SessionData = {
  id: "s1", t, utc: t.map(() => null), track: [], decimated: false,
  ch: { coolant: out(10), oil: out(30) },
  text: { faults: t.map((_, i) => (i < 20 ? "" : "031: pressure switch (Current)")) },
};

let calls: string[] = [];
const stubFetch = (failFields = false) => {
  calls = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = new URL(input, "http://x");
    calls.push(url.pathname + url.search);
    const module = url.searchParams.get("module")!;
    if (url.pathname === "/fields") {
      if (failFields) return new Response("nope", { status: 500 });
      const fields = module === "td5" ? [field("coolant")] : [field("oil")];
      return Response.json({ module, fields });
    }
    const faults = module === "td5" ? [{ key: "031", name: "031: pressure switch (Current)", description: "Brake pressure switch" }] : [];
    return Response.json({ module, faults });
  }));
};

beforeEach(() => {
  resetFlagMetaCache();
  localStorage.clear();
  resetFlagOptionsCache();
});
afterEach(() => {
  vi.unstubAllGlobals();
  saveFlagOptions(DEFAULT_FLAG_OPTIONS);
  resetFlagOptionsCache();
});

describe("useSessionFlags", () => {
  it("loads /fields for every module, detects, labels faults and counts", async () => {
    stubFetch();
    const { result } = renderHook(() => useSessionFlags(DATA, ["td5", "slabs"]));
    await vi.waitFor(() => expect(result.current.counts.range).toBe(2));
    expect(result.current.all.map((f) => f.id)).toEqual(["range:coolant:10000", "fault:031:20000", "range:oil:30000"]);
    expect(result.current.all[1]!.label).toBe("Brake pressure switch");
    expect(result.current.counts).toEqual({ range: 2, faults: 1 });
    expect(calls.filter((c) => c.startsWith("/fields")).sort()).toEqual(["/fields?module=slabs", "/fields?module=td5"]);
  });

  it("caches per module across hooks", async () => {
    stubFetch();
    const a = renderHook(() => useSessionFlags(DATA, ["td5"]));
    await vi.waitFor(() => expect(a.result.current.counts.range).toBe(1));
    const b = renderHook(() => useSessionFlags(DATA, ["td5"]));
    await vi.waitFor(() => expect(b.result.current.counts.range).toBe(1));
    expect(calls.filter((c) => c.startsWith("/fields"))).toHaveLength(1);
  });

  it("fails soft: no fields → fault flags only", async () => {
    stubFetch(true);
    const { result } = renderHook(() => useSessionFlags(DATA, ["td5"]));
    await vi.waitFor(() => expect(calls.length).toBeGreaterThan(1));
    await vi.waitFor(() => expect(result.current.all).toHaveLength(1));
    expect(result.current.all[0]!.kind).toBe("fault");
  });

  it("no data → nothing", () => {
    stubFetch();
    const { result } = renderHook(() => useSessionFlags(undefined, []));
    expect(result.current).toEqual({ all: [], visible: [], counts: { range: 0, faults: 0 } });
  });

  it("applies the flag manager's options (and re-renders when they change)", async () => {
    stubFetch();
    const { result } = renderHook(() => useSessionFlags(DATA, ["td5", "slabs"]));
    await vi.waitFor(() => expect(result.current.counts.range).toBe(2));
    act(() => saveFlagOptions({ ...DEFAULT_FLAG_OPTIONS, muted: ["oil"] }));
    expect(result.current.counts).toEqual({ range: 1, faults: 1 });
    expect(result.current.all).toHaveLength(3);
    act(() => saveFlagOptions({ ...DEFAULT_FLAG_OPTIONS, faults: false }));
    expect(result.current.counts).toEqual({ range: 2, faults: 0 });
    expect(result.current.visible.every((f) => f.kind === "range")).toBe(true);
  });
});
