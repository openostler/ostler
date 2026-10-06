// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AUTO_OPEN_MS, autoOpenDelay, connOf, fmtDown, RECONNECTING_MS, REPROMPT_MS, shouldAutoOpen, type Conn } from "../lib/connection";
import { useConnectionSheet } from "./connection";

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

type Props = { c: Conn | null; b: boolean; r?: boolean };
const hook = (conn: Conn | null, blocked = false, replaying = false) =>
  renderHook(({ c, b, r }: Props) => useConnectionSheet(c, b, r),
    { initialProps: { c: conn, b: blocked, r: replaying } as Props });
/** Flush the 0 ms auto-open timer (and the effects that schedule it). */
const tick = (ms = 0) => act(() => vi.advanceTimersByTime(ms));

describe("connOf", () => {
  it("prefers snap.conn and falls back to the legacy status", () => {
    expect(connOf({ status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", conn: "lost", signals: {}, faults: [] })).toBe("lost");
    expect(connOf({ status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [] })).toBe("connected");
    expect(connOf({ status: "no-cable", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [] })).toBe("error");
    expect(connOf({ status: "connecting", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [] })).toBe("connecting");
    expect(connOf(null)).toBeNull();
  });
  it("auto-opens in error | lost | disconnected | reconnecting, not when dismissed or blocked", () => {
    const base = { open: false, dismissed: false, blocked: false };
    expect(shouldAutoOpen({ ...base, conn: "lost" })).toBe(true);
    expect(shouldAutoOpen({ ...base, conn: "reconnecting" })).toBe(true);
    expect(shouldAutoOpen({ ...base, conn: "connecting" })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: "connected" })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: null })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: "error", dismissed: true })).toBe(false);
    expect(shouldAutoOpen({ ...base, conn: "error", blocked: true })).toBe(false);
  });
  it("opens at once, except reconnecting (1 s debounce)", () => {
    expect(AUTO_OPEN_MS).toBe(0);
    expect(RECONNECTING_MS).toBe(1000);
    expect(autoOpenDelay("error")).toBe(0);
    expect(autoOpenDelay("lost")).toBe(0);
    expect(autoOpenDelay("disconnected")).toBe(0);
    expect(autoOpenDelay("reconnecting")).toBe(1000);
    expect(autoOpenDelay("connecting")).toBeNull();
  });
});

describe("ConnectionSheet auto-open", () => {
  it.each<Conn>(["error", "lost", "disconnected"])("opens immediately on load when %s", (c) => {
    const { result } = hook(c);
    tick();
    expect(result.current.open).toBe(true);
  });

  it("opens immediately when the connection drops", () => {
    const { result, rerender } = hook("connected");
    tick(5000);
    rerender({ c: "lost", b: false });
    tick();
    expect(result.current.open).toBe(true);
  });

  it("debounces reconnecting by 1 s", () => {
    const { result, rerender } = hook("connected");
    rerender({ c: "reconnecting", b: false });
    tick(900);
    expect(result.current.open).toBe(false);
    tick(200);
    expect(result.current.open).toBe(true);
  });

  it("a reconnect that succeeds inside 1 s never opens the sheet", () => {
    const { result, rerender } = hook("connected");
    rerender({ c: "reconnecting", b: false });
    tick(800);
    rerender({ c: "connected", b: false });
    tick(5000);
    expect(result.current.open).toBe(false);
  });

  it("does not open while connected or connecting", () => {
    const { result, rerender } = hook("connected");
    tick(5000);
    rerender({ c: "connecting", b: false });
    tick(5000);
    expect(result.current.open).toBe(false);
  });

  it("never opens over Consent, and opens at once when it is answered", () => {
    const { result, rerender } = hook("error", true);
    tick(5000);
    expect(result.current.open).toBe(false);
    rerender({ c: "error", b: false }); // consent answered
    tick();
    expect(result.current.open).toBe(true);
  });

  it("stays closed once dismissed through not-live states, until a new attempt", () => {
    const { result, rerender } = hook("error");
    tick();
    act(() => result.current.dismiss());
    rerender({ c: "reconnecting", b: false });
    tick(2000);
    rerender({ c: "error", b: false });
    tick(10_000);
    expect(result.current.open).toBe(false);
    rerender({ c: "connecting", b: false });
    rerender({ c: "error", b: false });
    tick();
    expect(result.current.open).toBe(true);
  });

  it("closes an auto-opened sheet when the connection comes back", () => {
    const { result, rerender } = hook("lost");
    tick();
    rerender({ c: "connected", b: false });
    expect(result.current.open).toBe(false);
  });

  it("opens on demand from the pill", () => {
    const { result } = hook("connected");
    act(() => result.current.show());
    expect(result.current.open).toBe(true);
  });
});

describe("ConnectionSheet and replay", () => {
  it("never opens during a replay", () => {
    const { result, rerender } = hook("error", false, true);
    tick(120_000);
    expect(result.current.open).toBe(false);
    rerender({ c: "lost", b: false, r: true });
    rerender({ c: "reconnecting", b: false, r: true });
    tick(120_000);
    expect(result.current.open).toBe(false);
  });

  it("opens immediately when leaving a replay while not live", () => {
    const { result, rerender } = hook("error", false, true);
    tick(5000);
    rerender({ c: "error", b: false, r: false });
    tick();
    expect(result.current.open).toBe(true);
  });

  it("leaving a replay forgets an earlier dismissal", () => {
    const { result, rerender } = hook("error");
    tick();
    act(() => result.current.dismiss());
    rerender({ c: "error", b: false, r: true });
    tick(1000);
    rerender({ c: "error", b: false, r: false });
    tick();
    expect(result.current.open).toBe(true);
  });

  it("does not open when leaving a replay while connected", () => {
    const { result, rerender } = hook("connected", false, true);
    rerender({ c: "connected", b: false, r: false });
    tick(5000);
    expect(result.current.open).toBe(false);
  });

  it("hides a sheet that was open when the replay starts", () => {
    const { result, rerender } = hook("error");
    tick();
    rerender({ c: "error", b: false, r: true });
    expect(result.current.open).toBe(false);
  });
});

describe("ConnectionSheet re-prompt", () => {
  const openAndDismiss = (conn: Conn = "error") => {
    const h = hook(conn);
    tick();
    expect(h.result.current.open).toBe(true);
    act(() => h.result.current.dismiss());
    return h;
  };

  it("re-opens REPROMPT_MS after a dismissal while still not live", () => {
    expect(REPROMPT_MS).toBe(60_000);
    const { result } = openAndDismiss();
    act(() => vi.advanceTimersByTime(59_900));
    expect(result.current.open).toBe(false);
    act(() => vi.advanceTimersByTime(200));
    expect(result.current.open).toBe(true);
  });

  it("keeps counting through not-live state changes", () => {
    const { result, rerender } = openAndDismiss("lost");
    act(() => vi.advanceTimersByTime(30_000));
    rerender({ c: "reconnecting", b: false });
    act(() => vi.advanceTimersByTime(30_100));
    expect(result.current.open).toBe(true);
  });

  it("restarts the timer on each dismissal", () => {
    const { result } = openAndDismiss();
    act(() => vi.advanceTimersByTime(60_100));
    expect(result.current.open).toBe(true);
    act(() => vi.advanceTimersByTime(10_000));
    act(() => result.current.dismiss());
    act(() => vi.advanceTimersByTime(59_000));
    expect(result.current.open).toBe(false);
    act(() => vi.advanceTimersByTime(1_100));
    expect(result.current.open).toBe(true);
  });

  it("does not re-open once the connection is live again", () => {
    const { result, rerender } = openAndDismiss();
    act(() => vi.advanceTimersByTime(20_000));
    rerender({ c: "connected", b: false });
    act(() => vi.advanceTimersByTime(120_000));
    expect(result.current.open).toBe(false);
  });

  it("never re-opens over Consent", () => {
    const { result, rerender } = openAndDismiss();
    rerender({ c: "error", b: true });
    act(() => vi.advanceTimersByTime(120_000));
    expect(result.current.open).toBe(false);
    rerender({ c: "error", b: false });
    act(() => vi.advanceTimersByTime(60_100));
    expect(result.current.open).toBe(true);
  });

  it("never re-opens during a replay", () => {
    const { result, rerender } = openAndDismiss();
    rerender({ c: "error", b: false, r: true });
    tick(120_000);
    expect(result.current.open).toBe(false);
  });
});

describe("down since", () => {
  it("stamps when the connection leaves connected and clears when it returns", () => {
    vi.setSystemTime(1_000_000);
    const { result, rerender } = hook("connected");
    expect(result.current.downSince).toBeNull();
    vi.setSystemTime(2_000_000);
    rerender({ c: "lost", b: false });
    expect(result.current.downSince).toBe(2_000_000);
    vi.setSystemTime(2_005_000);
    rerender({ c: "reconnecting", b: false });
    expect(result.current.downSince).toBe(2_000_000);
    rerender({ c: "connected", b: false });
    expect(result.current.downSince).toBeNull();
  });

  it("formats the down time", () => {
    expect(fmtDown(45_000)).toBe("45 s");
    expect(fmtDown(80_000)).toBe("1 m 20 s");
    expect(fmtDown(3_900_000)).toBe("1 h 5 m");
  });
});
