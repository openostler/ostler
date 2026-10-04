import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { connOf, shouldAutoOpen, type Conn } from "../lib/connection";
import { useConnectionSheet } from "./connection";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

const hook = (conn: Conn | null, blocked = false) =>
  renderHook(({ c, b }) => useConnectionSheet(c, b), { initialProps: { c: conn, b: blocked } });

describe("connOf", () => {
  it("prefers snap.conn and falls back to the legacy status", () => {
    expect(connOf({ status: "connected", conn: "lost", signals: {}, faults: [] })).toBe("lost");
    expect(connOf({ status: "connected", signals: {}, faults: [] })).toBe("connected");
    expect(connOf({ status: "no-cable", signals: {}, faults: [] })).toBe("error");
    expect(connOf({ status: "connecting", signals: {}, faults: [] })).toBe("connecting");
    expect(connOf(null)).toBeNull();
  });
  it("auto-opens only in error | lost | disconnected, not when dismissed or blocked", () => {
    const base = { open: false, dismissedFor: null, blocked: false };
    expect(shouldAutoOpen({ ...base, conn: "lost" })).toBe(true);
    expect(shouldAutoOpen({ ...base, conn: "connecting" })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: "error", dismissedFor: "error" })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: "error", blocked: true })).toBe(false);
  });
});

describe("ConnectionSheet auto-open", () => {
  it("opens 3 s after the connection is lost", () => {
    const { result } = hook("lost");
    act(() => vi.advanceTimersByTime(2900));
    expect(result.current.open).toBe(false);
    act(() => vi.advanceTimersByTime(200));
    expect(result.current.open).toBe(true);
  });

  it("does not open while connected or connecting", () => {
    const { result, rerender } = hook("connected");
    act(() => vi.advanceTimersByTime(5000));
    rerender({ c: "connecting", b: false });
    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.open).toBe(false);
  });

  it("never opens over Consent", () => {
    const { result, rerender } = hook("error", true);
    act(() => vi.advanceTimersByTime(5000));
    expect(result.current.open).toBe(false);
    rerender({ c: "error", b: false }); // consent answered
    act(() => vi.advanceTimersByTime(3100));
    expect(result.current.open).toBe(true);
  });

  it("stays closed once dismissed, until conn changes", () => {
    const { result, rerender } = hook("error");
    act(() => vi.advanceTimersByTime(3100));
    act(() => result.current.dismiss());
    act(() => vi.advanceTimersByTime(10_000));
    expect(result.current.open).toBe(false);
    rerender({ c: "connecting", b: false });
    rerender({ c: "error", b: false });
    act(() => vi.advanceTimersByTime(3100));
    expect(result.current.open).toBe(true);
  });

  it("closes an auto-opened sheet when the connection comes back", () => {
    const { result, rerender } = hook("lost");
    act(() => vi.advanceTimersByTime(3100));
    rerender({ c: "connected", b: false });
    expect(result.current.open).toBe(false);
  });

  it("opens on demand from the pill", () => {
    const { result } = hook("connected");
    act(() => result.current.show());
    expect(result.current.open).toBe(true);
  });
});
