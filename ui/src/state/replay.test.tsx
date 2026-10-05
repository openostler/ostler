import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CatalogAction } from "../api/schemas";
import { useAction } from "../api/useAction";
import { ActionButton } from "../components/ActionButton";
import { ConnectionNotice } from "../components/ConnectionNotice";
import { ConnectionPill } from "../components/ConnectionPill";
import { GlobalTransport } from "../components/GlobalTransport";
import { ReplayBanner } from "../components/ReplayBanner";
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
    id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 60, rows: 2, parts: [], modules: ["motor"],
    channels: [], has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
    synthetic: false, recording: false, source: "mock", audio: [],
  },
  notes: [{ id: "n1", t: 1000, t_end: null, text: "Clunk", tags: [], kind: "mark", source: "live", created: "" }],
  t: 2000, offset: null,
  ...over,
});

const withReplay = (r: Replay, ui: ReactNode) => <ReplayCtx.Provider value={r}>{ui}</ReplayCtx.Provider>;

const appCtx = (over: Partial<AppContext> = {}): AppContext => ({
  snap: { status: "connected", signals: {}, faults: [] }, live: initialLive, linkUp: true, module: "motor", catalog: null,
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
    expect(screen.getByLabelText("A/C Fan: replay, read only")).toHaveTextContent("🔒A/C Fan · replay");
  });

  it("ActionButton is a normal button when live", () => {
    renderWithApp(<ActionButton action={fan} itemName="A/C Fan" />);
    expect(screen.getByRole("button", { name: "A/C Fan" })).toBeInTheDocument();
  });

  it("the pill reads Replay and the connection notice is hidden", () => {
    renderWithApp(withReplay(replaying(), <><ConnectionPill /><ConnectionNotice /></>), {
      snap: { status: "error", conn: "error", signals: {}, faults: [] },
    });
    expect(screen.getByLabelText("Replay — read only")).toHaveTextContent("Replay");
    expect(screen.queryByText("No connection")).not.toBeInTheDocument();
  });
});

describe("ReplayBanner", () => {
  it("shows REPLAY, the date, the cursor clock, the current note and Exit to live", () => {
    const r = replaying();
    render(withReplay(r, <ReplayBanner />));
    const banner = screen.getByRole("region", { name: "Replay" });
    expect(banner).toHaveTextContent("REPLAY");
    expect(screen.getByTestId("replay-clock")).toHaveTextContent("⏱ 0:02");
    expect(banner).toHaveTextContent("⚑ Clunk");
    fireEvent.click(screen.getByRole("button", { name: "Exit to live" }));
    expect(r.exit).toHaveBeenCalled();
  });

  it("keeps Exit visible while loading or on error", () => {
    const { rerender } = render(withReplay(replaying({ loading: true, session: undefined }), <ReplayBanner />));
    expect(screen.getByText("Loading session…")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exit to live" })).toBeInTheDocument();
    rerender(withReplay(replaying({ error: "HTTP 404", session: undefined }), <ReplayBanner />));
    expect(screen.getByText(/Could not load this session: HTTP 404/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exit to live" })).toBeInTheDocument();
  });

  it("renders nothing when live", () => {
    const { container } = render(<><ReplayBanner /><GlobalTransport /></>);
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
      "/sessions/s1/data": { id: "s1", t: T, utc: [null, null, null], ch: { rpm: [1, 2, 3] }, track: [], decimated: false },
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
        body = { id: "s1", t, utc: t.map(() => null), ch: { rpm: t.map(() => 800) }, track: [], decimated: false };
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

  it("enter(id, {at: \"end-30s\"}) starts 30 s before the last sample (never before 0)", async () => {
    expect(startCursor([0, 1000, 90_000], "end-30s")).toBe(60_000);
    expect(startCursor([0, 1000, 10_000], "end-30s")).toBe(0);
    expect(startCursor([], "end-30s")).toBe(0);
    expect(startCursor([0, 1000], 500)).toBe(500);
    sessionServer(90);
    const { result } = hook();
    act(() => result.current.enter("s1", { at: "end-30s" }));
    await vi.waitFor(() => expect(result.current.t).toBe(60_000));
  });

  it("a still-recording session's refresh never moves the cursor after end-30s", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    try {
      sessionServer(90, true, 20);
      const { result } = hook();
      act(() => result.current.enter("s1", { at: "end-30s" }));
      await vi.waitFor(() => expect(result.current.t).toBe(60_000));
      act(() => { vi.advanceTimersByTime(LIVE_REFRESH_MS); });
      await vi.waitFor(() => expect(result.current.data?.t.at(-1)).toBe(110_000));
      expect(result.current.t).toBe(60_000);
    } finally {
      vi.useRealTimers();
    }
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
