// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { clamp, clockAt, formatClock, formatSessionTime, indexAt, SKIP_MS, usePlaybackState, utcOffset, valueAt } from "./playback";

describe("playback maths", () => {
  it("indexAt finds the last sample at or before t", () => {
    const t = [0, 200, 400, 600];
    expect(indexAt(t, -5)).toBe(0);
    expect(indexAt(t, 0)).toBe(0);
    expect(indexAt(t, 399)).toBe(1);
    expect(indexAt(t, 400)).toBe(2);
    expect(indexAt(t, 10_000)).toBe(3);
    expect(indexAt([], 5)).toBe(-1);
    // min/max decimation repeats a timestamp: the later twin wins
    expect(indexAt([0, 100, 100, 200], 150)).toBe(2);
  });

  it("clamp", () => {
    expect(clamp(5, 0, 3)).toBe(3);
    expect(clamp(-1, 0, 3)).toBe(0);
    expect(clamp(2, 0, 3)).toBe(2);
  });

  it("valueAt reads sparse rows back to the last value", () => {
    const t = [0, 100, 200, 300];
    expect(valueAt(t, [1, null, null, 4], 250)).toBe(1);
    expect(valueAt(t, [1, null, null, 4], 300)).toBe(4);
    expect(valueAt(t, [null, null, null, null], 300)).toBeNull();
    expect(valueAt(t, undefined, 300)).toBeNull();
  });

  it("clockAt scales elapsed wall time by speed and stops at the end", () => {
    const a = { wall: 1000, time: 5000 };
    expect(clockAt(a, 1500, 1, 0, 60_000)).toEqual({ time: 5500, ended: false });
    expect(clockAt(a, 1500, 4, 0, 60_000)).toEqual({ time: 7000, ended: false });
    expect(clockAt(a, 100_000, 8, 0, 60_000)).toEqual({ time: 60_000, ended: true });
  });

  it("utcOffset comes from the first row with a UTC", () => {
    expect(utcOffset([0, 200, 400], [null, 1_000_200, 1_000_400])).toBe(1_000_000);
    expect(utcOffset([0, 200], [null, null])).toBeNull();
  });

  it("formats session time and local clock time", () => {
    expect(formatSessionTime(0)).toBe("0:00");
    expect(formatSessionTime(75_400)).toBe("1:15");
    expect(formatSessionTime(3_725_000)).toBe("1:02:05");
    expect(formatClock(75_000, null)).toBe("1:15");
    const start = new Date(2026, 9, 5, 9, 0, 0).getTime(); // local 09:00:00
    expect(formatClock(61_000, start)).toBe("09:01:01");
  });
});

describe("usePlaybackState", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());
  const t = Array.from({ length: 101 }, (_, i) => i * 200); // 0 … 20 s at 5 Hz

  it("plays in real time, honours speed, and stops at the end", () => {
    const { result } = renderHook(() => usePlaybackState(t));
    expect(result.current.time).toBe(0);
    act(() => result.current.play());
    expect(result.current.playing).toBe(true);
    act(() => { vi.advanceTimersByTime(2000); });
    expect(result.current.time).toBeGreaterThan(1800);
    expect(result.current.time).toBeLessThan(2200);
    expect(result.current.index).toBe(indexAt(t, result.current.time));

    act(() => result.current.setSpeed(4));
    const before = result.current.time;
    act(() => { vi.advanceTimersByTime(1000); });
    expect(result.current.time - before).toBeGreaterThan(3700);
    expect(result.current.time - before).toBeLessThan(4300);

    act(() => { vi.advanceTimersByTime(10_000); });
    expect(result.current.time).toBe(20_000);
    expect(result.current.playing).toBe(false);
  });

  it("seek re-anchors the clock mid-play; skip is ±10 s, clamped", () => {
    const { result } = renderHook(() => usePlaybackState(t));
    act(() => result.current.play());
    act(() => { vi.advanceTimersByTime(1000); });
    act(() => result.current.seek(10_000));
    expect(result.current.time).toBe(10_000);
    act(() => { vi.advanceTimersByTime(1000); });
    expect(result.current.time).toBeGreaterThan(10_800);
    expect(result.current.time).toBeLessThan(11_200);
    act(() => result.current.pause());
    act(() => result.current.skip(SKIP_MS));
    expect(result.current.time).toBe(20_000);
    act(() => result.current.skip(-3 * SKIP_MS));
    expect(result.current.time).toBe(0);
  });

  it("play at the end restarts from the start", () => {
    const { result } = renderHook(() => usePlaybackState(t));
    act(() => result.current.seek(20_000));
    act(() => result.current.play());
    expect(result.current.time).toBe(0);
    expect(result.current.playing).toBe(true);
  });

  it("pinToEnd (Follow live) holds the cursor at the newest sample; a seek reports a user move", () => {
    const moved = vi.fn();
    const { result, rerender } = renderHook(({ tt }) => usePlaybackState(tt, { pinToEnd: true, onUserMove: moved }), { initialProps: { tt: t } });
    expect(result.current.time).toBe(20_000);
    rerender({ tt: [...t, 20_200, 20_400] });
    expect(result.current.time).toBe(20_400);
    act(() => result.current.seek(1000));
    expect(moved).toHaveBeenCalled();
  });
});
