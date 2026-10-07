// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CatalogAction } from "../api/schemas";
import { useAction } from "../api/useAction";
import { ActionButton } from "../components/ActionButton";
import { ConnectionNotice } from "../components/ConnectionNotice";
import { GlobalTransport } from "../components/GlobalTransport";
import { Strip } from "../shell/Strip";
import { stripChips } from "../shell/strip";
import { renderWithApp } from "../test/renderWithApp";
import { AppCtx, type AppContext } from "./app";
import { initialLive } from "./live";
import { usePlaybackState } from "./playback";
import { DEFAULT_PREFS } from "./prefs";
import { LIVE_REFRESH_MS } from "../api/useSessions";
import { INACTIVE, READ_ONLY_ERROR, ReplayCtx, ReplayProvider, startCursor, useReplay, type Replay } from "./replay";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const replaying = (over: Partial<Replay> = {}): Replay => ({
  ...INACTIVE, active: true, id: "s1", exit: vi.fn(),
  session: {
    id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 60, rows: 2, parts: [], modules: ["td5"],
    channels: [], has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
    synthetic: false, recording: false, source: "mock", audio: [],
  },
  notes: [{ id: "n1", t: 1000, t_end: null, text: "Clunk", tags: [], kind: "mark", source: "live", created: "" }],
  t: 2000, offset: null,
  ...over,
});

const withReplay = (r: Replay, ui: ReactNode) => <ReplayCtx.Provider value={r}>{ui}</ReplayCtx.Provider>;

const appCtx = (over: Partial<AppContext> = {}): AppContext => ({
  snap: { status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [] }, live: initialLive, linkUp: true, module: "td5", catalog: null,
  fields: {}, faultMeaning: () => undefined, refresh: vi.fn(), prefs: { ...DEFAULT_PREFS, consentDone: true }, setPrefs: vi.fn(),
  experimental: false, admin: false, community: null, reloadCommunity: vi.fn(), goTo: vi.fn(), toast: vi.fn(),
  ackedFaults: new Set(), showFaultSheet: vi.fn(), openConnection: vi.fn(), ...over,
});

const fan: CatalogAction = {
  action: "output_ac_fan", label: "A/C Fan", status: "verified", safety: "actuator", confirm: "none", preconditions: [], ref: "",
};

describe("read-only actions in replay", () => {
  it("useAction refuses without fetching", async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    const ctx = appCtx();
    const { result } = renderHook(() => useAction(), {
      wrapper: ({ children }) => <AppCtx.Provider value={ctx}>{withReplay(replaying(), children)}</AppCtx.Provider>,
    });
    const r = await result.current("clear_faults");
    expect(r).toEqual({ ok: false, error: READ_ONLY_ERROR });
    expect(READ_ONLY_ERROR).toBe("Replay — read only");
    expect(fetchSpy).not.toHaveBeenCalled();
    expect(ctx.toast).toHaveBeenCalledWith(READ_ONLY_ERROR, true);
  });

  it("ActionButton is a lock with the word replay", () => {
    renderWithApp(withReplay(replaying(), <ActionButton action={fan} itemName="A/C Fan" />));
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByLabelText("A/C Fan: replay, read only")).toHaveTextContent("A/C Fan · replay");
    expect(screen.getByLabelText("A/C Fan: replay, read only").querySelector('[data-icon="lock"]')).not.toBeNull();
  });

  it("ActionButton is a normal button when live", () => {
    renderWithApp(<ActionButton action={fan} itemName="A/C Fan" />);
    expect(screen.getByRole("button", { name: "A/C Fan" })).toBeInTheDocument();
  });

  it("the strip's Link chip reads Replay · Exit to live and exits on click; the connection notice is hidden", () => {
    const r = replaying();
    const snap = { status: "error", ts_utc: "2026-10-05T09:00:00.000Z", conn: "error", signals: {}, faults: [] };
    const chips = stripChips({
      layout: "hu7", snap, linkUp: true, replaying: true, admin: false, systemName: "TD5 (engine)",
      unacked: 0, clock: "09:00", quantity: (v, u) => `${v} ${u}`,
    });
    const onOpen = vi.fn((o: string) => o === "exit-replay" && r.exit());
    renderWithApp(withReplay(r, <><Strip chips={chips} onOpen={onOpen} /><ConnectionNotice /></>), { snap });
    const pill = screen.getByRole("button", { name: "Replay — Exit to live" });
    expect(pill).toHaveTextContent("ReplayExit to live");
    expect(pill).toHaveClass("tone-replay");
    expect(screen.queryByText("No connection")).not.toBeInTheDocument();
    fireEvent.click(pill);
    expect(onOpen).toHaveBeenCalledWith("exit-replay");
    expect(r.exit).toHaveBeenCalled();
  });
});

describe("GlobalTransport note overlay", () => {
  it("shows the note at the cursor in an overlay above the scrubber", () => {
    const { container } = render(withReplay(replaying({ data: {} as Replay["data"] }), <GlobalTransport />));
    const layer = container.querySelector(".gnote-layer");
    expect(layer).not.toBeNull();
    expect(layer).toHaveTextContent("Clunk");
    expect(layer?.querySelector('[data-icon="flag"]')).not.toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent("Clunk");
  });

  it("shows loading and errors in the overlay", () => {
    const { rerender } = render(withReplay(replaying({ loading: true, session: undefined }), <GlobalTransport />));
    expect(screen.getByText("Loading session…")).toBeInTheDocument();
    rerender(withReplay(replaying({ error: "HTTP 404", session: undefined }), <GlobalTransport />));
    expect(screen.getByRole("alert")).toHaveTextContent(/Could not load this session: HTTP 404/);
  });

  it("renders nothing when live", () => {
    const { container } = render(<GlobalTransport />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("ReplayProvider", () => {
  it("is inactive by default and enter() loads meta, data, events and notes", async () => {
    const paths: string[] = [];
    const T = [0, 1000, 2000];
    const bodies: Record<string, unknown> = {
      "/sessions/s1": { id: "s1", start_utc: "2026-10-05T09:00:00Z", end_utc: null, duration_s: 2, rows: 3, has_gps: false,
        distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null, synthetic: false, recording: false,
        source: "mock", channels: [{ name: "rpm", units: "rpm" }, { name: "faults", units: "" }] },
      "/sessions/s1/data": { id: "s1", t: T, t0_utc: null, ch: { rpm: [1, 2, 3] }, trace: null, decimated: false },
      "/sessions/s1/events": { id: "s1", events: [{ t: 0, type: "module", module: "slabs" }] },
      "/sessions/s1/notes": { id: "s1", notes: [] },
    };
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const url = new URL(input, "http://x");
      paths.push(url.pathname + url.search);
      return new Response(JSON.stringify(bodies[url.pathname]), { headers: { "Content-Type": "application/json" } });
    }));
    const { result } = renderHook(() => useReplay(), { wrapper: ({ children }) => <ReplayProvider>{children}</ReplayProvider> });
    expect(result.current.active).toBe(false);
    act(() => result.current.enter("s1"));
    expect(result.current.active).toBe(true);
    expect(result.current.loading).toBe(true);
    await vi.waitFor(() => expect(result.current.data).toBeTruthy());
    expect(result.current.state.module).toBe("slabs");
    expect(paths).toContain("/sessions/s1/data?ch=rpm&max=3000"); // numeric channels only
    act(() => result.current.seek(1500));
    expect(result.current.t).toBe(1500);
    act(() => result.current.exit());
    expect(result.current.active).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  const meta = (recording: boolean) => ({ id: "s1", start_utc: "2026-10-05T09:00:00Z", end_utc: null, duration_s: 90,
    rows: 91, has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
    synthetic: false, recording, source: "mock", channels: [{ name: "rpm", units: "rpm" }] });
  /** /sessions/s1 whose data is `0 … lastS` seconds, growing by `grow` s on every data fetch. */
  const sessionServer = (lastS: number, recording = false, grow = 0) => {
    let n = lastS;
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const url = new URL(input, "http://x");
      let body: unknown = meta(recording);
      if (url.pathname.endsWith("/data")) {
        const t = Array.from({ length: n + 1 }, (_, i) => i * 1000);
        n += grow;
        body = { id: "s1", t, t0_utc: null, ch: { rpm: t.map(() => 800) }, trace: null, decimated: false };
      } else if (url.pathname.endsWith("/events")) body = { id: "s1", events: [] };
      else if (url.pathname.endsWith("/notes")) body = { id: "s1", notes: [] };
      return new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } });
    }));
  };
  const hook = () => renderHook(() => useReplay(), { wrapper: ({ children }) => <ReplayProvider>{children}</ReplayProvider> });

  it("enter(id, {at}) starts the cursor at a session time once the data loads", async () => {
    sessionServer(90);
    const { result } = hook();
    act(() => result.current.enter("s1", { at: 42_000 }));
    await vi.waitFor(() => expect(result.current.data).toBeTruthy());
    await vi.waitFor(() => expect(result.current.t).toBe(42_000));
    expect(result.current.playing).toBe(false);
  });

  it("enter(id) without at starts at the first sample", async () => {
    sessionServer(90);
    const { result } = hook();
    act(() => result.current.enter("s1"));
    await vi.waitFor(() => expect(result.current.data).toBeTruthy());
    expect(result.current.t).toBe(0);
  });

  it("enter(id, {at: \"end\"}) starts at the last sample", async () => {
    expect(startCursor([0, 1000, 90_000], "end")).toBe(90_000);
    expect(startCursor([], "end")).toBe(0);
    expect(startCursor([0, 1000], 500)).toBe(500);
    sessionServer(90);
    const { result } = hook();
    act(() => result.current.enter("s1", { at: "end" }));
    await vi.waitFor(() => expect(result.current.t).toBe(90_000));
    expect(result.current.playing).toBe(false);
    expect(result.current.follow).toBe(false);
  });

  it("without follow a still-recording session's refresh never moves the cursor", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    try {
      sessionServer(90, true, 20);
      const { result } = hook();
      act(() => result.current.enter("s1", { at: "end" }));
      await vi.waitFor(() => expect(result.current.t).toBe(90_000));
      act(() => { vi.advanceTimersByTime(LIVE_REFRESH_MS); });
      await vi.waitFor(() => expect(result.current.data?.t.at(-1)).toBe(110_000));
      expect(result.current.t).toBe(90_000);
    } finally {
      vi.useRealTimers();
    }
  });

  it("follow keeps the cursor on the newest sample as data grows; a seek drops it; setFollow(true) re-pins", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    try {
      sessionServer(90, true, 20);
      const { result } = hook();
      act(() => result.current.enter("s1", { at: "end", follow: true }));
      await vi.waitFor(() => expect(result.current.t).toBe(90_000));
      expect(result.current.follow).toBe(true);
      act(() => { vi.advanceTimersByTime(LIVE_REFRESH_MS); });
      await vi.waitFor(() => expect(result.current.data?.t.at(-1)).toBe(110_000));
      expect(result.current.t).toBe(110_000);
      expect(result.current.playing).toBe(false);
      expect(result.current.follow).toBe(true);

      act(() => result.current.seek(50_000));
      expect(result.current.follow).toBe(false);
      expect(result.current.t).toBe(50_000);
      act(() => { vi.advanceTimersByTime(LIVE_REFRESH_MS); });
      await vi.waitFor(() => expect(result.current.data?.t.at(-1)).toBe(130_000));
      expect(result.current.t).toBe(50_000);

      act(() => result.current.setFollow(true));
      expect(result.current.t).toBe(130_000);
      // ±10 s from the pinned cursor carries on from the newest sample
      act(() => result.current.playback!.skip(-10_000));
      expect(result.current.follow).toBe(false);
      expect(result.current.t).toBe(120_000);
    } finally {
      vi.useRealTimers();
    }
  });

  it("play drops follow; exit and entering without follow reset it", async () => {
    sessionServer(90, true);
    const { result } = hook();
    act(() => result.current.enter("s1", { at: "end", follow: true }));
    await vi.waitFor(() => expect(result.current.t).toBe(90_000));
    act(() => result.current.play());
    expect(result.current.follow).toBe(false);
    act(() => result.current.pause());
    act(() => result.current.setFollow(true));
    act(() => result.current.exit());
    expect(result.current.follow).toBe(false);
    act(() => result.current.enter("s1", { follow: true }));
    expect(result.current.follow).toBe(true);
    act(() => result.current.enter("s1"));
    expect(result.current.follow).toBe(false);
    expect(INACTIVE.follow).toBe(false);
  });

  it("usePlaybackState rewinds and pauses when resetKey changes", () => {
    const T = [0, 1000, 2000];
    const { result, rerender } = renderHook(({ k }) => usePlaybackState(T, { resetKey: k }), { initialProps: { k: "a" } });
    act(() => result.current.seek(1500));
    expect(result.current.time).toBe(1500);
    rerender({ k: "b" });
    expect(result.current.time).toBe(0);
    expect(result.current.playing).toBe(false);
  });
});
