// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import sessionDataFx from "../api/fixtures/session-data.json";
import sessionsFx from "../api/fixtures/sessions.json";
import type { GpsFix, Note, SessionMeta, Snapshot } from "../api/schemas";
import { GlobalTransport } from "../components/GlobalTransport";
import { lineColorExpression, RAMPS, rangeOf } from "../components/replay/trace";
import { fmt } from "../lib/format";
import { ReplayProvider } from "../state/replay";
import { AppCtx, type AppContext } from "../state/app";
import { renderWithApp } from "../test/renderWithApp";
import { Analysis } from "./Analysis";

// jsdom has no WebGL: the map module is mocked. `fail` → createTraceMap throws (no WebGL),
// else it returns a fake handle the test inspects.
const mapMock = vi.hoisted(() => ({
  fail: true,
  handle: null as null | Record<string, ReturnType<typeof vi.fn>>,
}));
vi.mock("../components/replay/maplibre", () => ({
  createTraceMap: () => {
    if (mapMock.fail) throw new Error("WebGL not supported");
    mapMock.handle = {
      setTrace: vi.fn(), setColor: vi.fn(), setBasemap: vi.fn(), setCursor: vi.fn(), isBlank: vi.fn(() => false), retry: vi.fn(), destroy: vi.fn(),
    };
    return mapMock.handle;
  },
}));

// The fixture supplies the demo's id and channels (they match session-data.json); every
// field a test asserts on is set here, so regenerated fixtures don't move the expectations.
const demo: SessionMeta = {
  ...(sessionsFx.sessions[0] as unknown as SessionMeta),
  name: "Demo log 1", description: "A synthetic demo drive.", place: { label: "Rannoch Moor", source: "geonames" },
  place_start: null, place_end: null, note_count: 2, synthetic: true, recording: false, source: "demo",
  modules: ["td5", "slabs"], has_gps: true, distance_km: 11.21, max_speed_kmh: 92, duration_s: 720,
};
const real: SessionMeta = {
  ...demo, name: null, description: null, place: null, note_count: 0, id: "20261004T170000Z", start_utc: "2026-10-04T17:00:00.000Z", synthetic: false, source: "live",
  has_gps: false, start_pos: null, end_pos: null, bbox: null, distance_km: 0, max_speed_kmh: null,
  channels: [
    { name: "rpm", units: "rpm", group: "engine" }, { name: "coolant_temp", units: "°C", group: "engine" },
    { name: "LateralAcc", units: "g", group: "accel" }, { name: "InlineAcc", units: "g", group: "accel" },
  ],
};
// Expected values come from the contract fixtures (regenerated from the real server).
const fxData = sessionDataFx as unknown as { t: number[]; ch: Record<string, (number | null)[]> };
const fxRpm = fxData.ch.rpm!;
const fxSpeedRange = rangeOf(fxData.ch.GPS_Speed)!;
const fxRpmRange = rangeOf(fxRpm)!;
const realData = {
  id: real.id, t: [0, 1000, 2000], t0_utc: null,
  ch: { rpm: [800, 900, 1000], coolant_temp: [80, null, 82], LateralAcc: [0.1, -0.6, 0.2], InlineAcc: [0.3, 0, -0.9] },
  trace: null, decimated: false,
};
const note = (id: string, t: number, t_end: number | null = null): Note => ({
  id, t, t_end, text: `note ${id}`, tags: [], kind: "note", source: "retro", created: "2026-10-05T09:02:00.000Z",
});
const demoNotes = [note("a1b2c3d4", 20_000), note("b2c3d4e5", 30_000, 50_000)];

type Call = { path: string; method: string; body?: unknown };
let calls: Call[];
/** PATCH /sessions/<real> replies with this (null → the server echoes the patch). */
let patchReply: { status: number; body: unknown } | null;

function stubServer() {
  calls = [];
  patchReply = null;
  const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ path: url.pathname + url.search, method, body });
    const p = url.pathname;
    if (p === "/sessions") return json({ sessions: [demo, real], next: null });
    if (p === "/sessions/histogram") return json({ group: url.searchParams.get("group"), buckets: [] });
    if (p === `/sessions/${real.id}` && method === "PATCH") {
      if (patchReply) return json(patchReply.body, patchReply.status);
      return json({ ok: true, meta: { ...real, ...body } });
    }
    if (p === `/sessions/${demo.id}`) return json(demo);
    if (p === `/sessions/${demo.id}/data`) return json(sessionDataFx);
    if (p === `/sessions/${demo.id}/events`) return json({ id: demo.id, events: [] });
    if (p === `/sessions/${demo.id}/notes`) return json({ id: demo.id, notes: demoNotes });
    if (p === `/sessions/${real.id}`) return json(real);
    if (p === `/sessions/${real.id}/data`) return json(realData);
    if (p === `/sessions/${real.id}/events`) return json({ id: real.id, events: [] });
    if (p === `/sessions/${real.id}/notes` && method === "POST") return json({ ok: true, note: { ...note("c3d4e5f6", body.t, body.t_end), text: "" } });
    if (p === `/sessions/${real.id}/notes`) return json({ id: real.id, notes: [] });
    if (p === "/command") return json({ ok: true });
    return json({ error: "not found" }, 404);
  }));
}

/** Analysis inside the app-root replay, with the global transport (as <App> mounts it);
 * `open` starts the replay on that session (as Logs / Rewind would). */
const ui = (open: string | null = null) => (
  <ReplayProvider initial={open}>
    <Analysis />
    <GlobalTransport />
  </ReplayProvider>
);

beforeEach(() => {
  localStorage.clear();
  mapMock.fail = true;
  mapMock.handle = null;
  stubServer();
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(() => null);
  vi.spyOn(console, "warn").mockImplementation(() => undefined);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});


describe("Analysis — replay", () => {
  it("a session in replay: header, fallback trace, legend, readouts, no Delete; ‹ Sessions exits to Logs", async () => {
    const { ctx } = renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    expect(screen.getByTestId("global-transport")).toBeInTheDocument();
    await waitFor(() => expect(document.querySelector("[data-map-status]")).toHaveAttribute("data-map-status", "failed"));
    expect(screen.getByRole("img", { name: "Session trace" })).toBeInTheDocument();
    expect(screen.getByText(/Map unavailable/)).toBeInTheDocument();
    // default trace A: no ECU `speed` → GPS_Speed; no trace B until added
    expect(screen.getByRole("button", { name: /^Trace A: GPS Speed/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Trace B/ })).toBeNull();
    expect(screen.getByTestId("legend-min")).toHaveTextContent(`${fmt(fxSpeedRange.min)} km/h`);
    expect(screen.getByTestId("legend-max")).toHaveTextContent(`${fmt(fxSpeedRange.max)} km/h`);
    const ro = screen.getByRole("group", { name: "Values at the cursor" });
    expect(within(ro).getByText(fmt(fxRpm[0]))).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    expect(screen.getByRole("link", { name: "CSV" })).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=csv`);
    expect(screen.getByRole("link", { name: "GPX" })).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=gpx`);
    expect(screen.getByRole("link", { name: "GeoJSON" })).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=geojson`);
    // the raw-tap export is offered only for a node session with a tap
    expect(screen.queryByRole("link", { name: "Raw tap (pcapng)" })).toBeNull();
    expect(calls.some((c) => c.path.startsWith(`/sessions/${demo.id}/data?ch=`))).toBe(true);
    // no G-G panel without acceleration channels
    expect(document.querySelector(".replay-gg")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "‹ Sessions" }));
    expect(ctx.goTo).toHaveBeenCalledWith("logs");
    await screen.findByText("Nothing to show yet");
    expect(screen.queryByTestId("global-transport")).toBeNull();
  });

  it("the SVG fallback draws trace B as a second, offset lane", async () => {
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    await waitFor(() => expect(document.querySelector("[data-map-status]")).toHaveAttribute("data-map-status", "failed"));
    expect(document.querySelectorAll(".replay-svg [data-lane]")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "+ Add trace" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByText("rpm", { selector: ".mono span" }).closest("button")!);
    const lanes = document.querySelectorAll(".replay-svg [data-lane]");
    expect([...lanes].map((l) => l.getAttribute("data-lane"))).toEqual(["a", "b"]);
  });

  it("drives the MapLibre handle: plasma A, mako B as a second lane, basemap switch", async () => {
    mapMock.fail = false;
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    await waitFor(() => expect(mapMock.handle).not.toBeNull());
    const h = mapMock.handle!;
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith("a", lineColorExpression(RAMPS.plasma)));
    expect(h.setTrace).toHaveBeenCalledWith("b", null);
    expect(h.setCursor).toHaveBeenCalled();

    // + Add trace → picker → rpm
    fireEvent.click(screen.getByRole("button", { name: "+ Add trace" }));
    const sheet = screen.getByRole("dialog");
    fireEvent.change(within(sheet).getByRole("searchbox", { name: "Search channels" }), { target: { value: "rpm" } });
    fireEvent.click(within(sheet).getAllByRole("button").find((b) => b.closest("[data-channel='rpm']") && b.className === "cpick-pick")!);
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith("b", lineColorExpression(RAMPS.mako)));
    const bCalls = h.setTrace!.mock.calls.filter((c) => c[0] === "b" && c[1]);
    expect(bCalls.length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: /^Trace B: rpm/ })).toBeInTheDocument();
    expect(screen.getByTestId("legend-b-max")).toHaveTextContent(`${fmt(fxRpmRange.max)} rpm`);
    expect(screen.queryByRole("button", { name: "+ Add trace" })).toBeNull();

    // basemap switch: Satellite → the handle toggles, the choice is remembered
    fireEvent.click(within(screen.getByRole("group", { name: "Basemap" })).getByRole("button", { name: "Satellite" }));
    await waitFor(() => expect(h.setBasemap).toHaveBeenLastCalledWith("satellite"));
    expect(localStorage.getItem("d2diag.basemap")).toBe("satellite");
    expect(screen.getByRole("button", { name: "Satellite" })).toHaveAttribute("aria-pressed", "true");

    // Classic: two-colour gradients (A blue → red, B green → purple)
    fireEvent.click(screen.getByRole("button", { name: "Classic colours" }));
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith("a", lineColorExpression(RAMPS.classicA)));
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith("b", lineColorExpression(RAMPS.classicB)));

    // remove trace B from its picker
    fireEvent.click(screen.getByRole("button", { name: /^Trace B: rpm/ }));
    fireEvent.click(screen.getByRole("button", { name: "Remove trace B" }));
    await waitFor(() => expect(h.setTrace).toHaveBeenLastCalledWith("b", null));
  });

  it("channel picker: pinned chips, categories, search with highlight, pin toggle persisted", async () => {
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    fireEvent.click(screen.getByRole("button", { name: /^Chart lane 1/ }));
    const sheet = screen.getByRole("dialog");
    // default pins present in this session: GPS Speed (no ECU speed) and rpm
    const pinned = within(sheet).getByRole("group", { name: "Pinned" });
    expect(within(pinned).getAllByRole("button").map((b) => b.textContent)).toEqual(["GPS Speed", "rpm"]);
    // categories from the recorded groups
    const cats = [...sheet.querySelectorAll("[data-category]")].map((e) => e.getAttribute("data-category"));
    expect(cats).toEqual(["GPS/Motion", "Engine"]);
    const engine = within(sheet).getByRole("button", { name: /Engine/, expanded: true });
    fireEvent.click(engine);
    expect(engine).toHaveAttribute("aria-expanded", "false");
    expect(sheet.querySelector("[data-channel='rpm']")).toBeNull();
    // search opens every match and highlights it
    fireEvent.change(within(sheet).getByRole("searchbox", { name: "Search channels" }), { target: { value: "km/h" } });
    expect(sheet.querySelectorAll(".cpick-row")).toHaveLength(1);
    expect(sheet.querySelector("mark")).toHaveTextContent("km/h");
    // unpin GPS Speed (a default) — persisted — then pin it again
    fireEvent.click(within(sheet).getByRole("button", { name: "Unpin GPS Speed" }));
    expect(JSON.parse(localStorage.getItem("d2diag.pinnedChannels")!)).not.toContain("GPS_Speed");
    fireEvent.click(within(sheet).getByRole("button", { name: "Pin GPS Speed" }));
    expect(JSON.parse(localStorage.getItem("d2diag.pinnedChannels")!)).toContain("GPS_Speed");
    expect(within(sheet).getByRole("button", { name: "Unpin GPS Speed" })).toHaveAttribute("aria-pressed", "true");
    // pick it for lane 1 → becomes a recent, lane changes
    fireEvent.click(sheet.querySelector("[data-channel='GPS_Speed'] .cpick-pick")!);
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByRole("button", { name: /^Chart lane 1: GPS Speed/ })).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("d2diag.recentChannels")!)).toEqual(["GPS_Speed"]);
  });

  it("scrubbing the global transport moves the readouts", async () => {
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    const i = fxRpm.findIndex((v, k) => k > 0 && v != null && v !== fxRpm[0]);
    // Scrub only once the session data has loaded (the readouts show the first sample):
    // a change fired earlier is reset to the start when the data arrives.
    const ro = await screen.findByRole("group", { name: "Values at the cursor" });
    await within(ro).findByText(fmt(fxRpm[0]));
    fireEvent.change(screen.getByRole("slider", { name: "Playback position" }), { target: { value: String(fxData.t[i]) } });
    await waitFor(() => expect(within(ro).getByText(fmt(fxRpm[i]))).toBeInTheDocument());
  });

  it("the chart draws notes as lines and ranges as bands; no note tool on a demo session", async () => {
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    await waitFor(() => expect(document.querySelector('[data-note="a1b2c3d4"]')).not.toBeNull());
    expect(document.querySelector('[data-note="a1b2c3d4"]')).toHaveClass("replay-note-line");
    expect(document.querySelector('[data-note="b2c3d4e5"]')).toHaveClass("replay-note-band");
    expect(screen.queryByRole("button", { name: "Drag to note" })).toBeNull();
  });

  it("a real session: G-G panel; a drag with the note tool opens the editor on that range", async () => {
    const width = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(300);
    renderWithApp(ui(real.id));
    await screen.findByText(/No GPS in this session/);
    // G-G from LateralAcc/InlineAcc: max |0.9 g| → ±1 g, two rings
    const gg = document.querySelector(".replay-gg")!;
    expect(gg).toHaveAttribute("data-limit", "1");
    expect(gg.querySelectorAll("[data-ring]")).toHaveLength(2);
    expect(screen.getByTestId("gg-cursor")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Drag to note" }));
    const plot = screen.getByRole("img", { name: /^Chart of/ });
    fireEvent.pointerDown(plot, { pointerId: 1, clientX: 30 });
    fireEvent.pointerMove(plot, { pointerId: 1, clientX: 150 });
    await act(async () => { fireEvent.pointerUp(plot, { pointerId: 1, clientX: 150 }); });
    // the drag opens the notes panel's editor on that span; saving posts the range note
    fireEvent.change(await screen.findByRole("textbox", { name: "Note text" }), { target: { value: "clunk" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save" })); });
    await waitFor(() => expect(calls.find((c) => c.method === "POST" && c.path === `/sessions/${real.id}/notes`)).toBeTruthy());
    const post = calls.find((c) => c.method === "POST" && c.path === `/sessions/${real.id}/notes`)!;
    // 30 px and 150 px of 300 over 0–2 s
    expect(post.body).toMatchObject({ t: 200, t_end: 1000, text: "clunk" });
    width.mockRestore();
  });

  it("a node session with a raw tap offers the pcapng export", async () => {
    real.tap = [{ session: "01M48AFR80CDXA0ZQ1XBS3VHSS", device: "node", file: "tap/01M48AFR80CDXA0ZQ1XBS3VHSS.otap" }];
    try {
      renderWithApp(ui(real.id));
      await screen.findByText(/No GPS in this session/);
      expect(screen.getByRole("link", { name: "Raw tap (pcapng)" })).toHaveAttribute("href", `/sessions/${real.id}/export?fmt=pcapng`);
    } finally {
      delete real.tap;
    }
  });

  it("a real session: Delete needs the word Delete (case-sensitive), posts delete_session and leaves replay", async () => {
    const { ctx } = renderWithApp(ui(real.id));
    await screen.findByText(/No GPS in this session/);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    const go = screen.getByRole("button", { name: "Delete session" });
    expect(go).toBeDisabled();
    const box = screen.getByRole("textbox", { name: "Type Delete to confirm" });
    fireEvent.change(box, { target: { value: real.id } });
    expect(go).toBeDisabled();
    fireEvent.change(box, { target: { value: "delete" } });
    expect(go).toBeDisabled();
    fireEvent.change(box, { target: { value: "DELETE" } });
    expect(go).toBeDisabled();
    fireEvent.change(box, { target: { value: "Delete" } });
    expect(go).toBeEnabled();
    await act(async () => { fireEvent.click(go); });
    expect(calls.find((c) => c.path === "/command")?.body).toEqual({ action: "delete_session", params: { id: real.id } });
    expect(ctx.toast).toHaveBeenCalledWith("session deleted");
    expect(ctx.goTo).toHaveBeenCalledWith("logs"); // back to the browser
    await waitFor(() => expect(screen.queryByTestId("global-transport")).toBeNull());
  });

  it("inline name: tap, type, Enter saves through PATCH (trimmed); Escape cancels", async () => {
    renderWithApp(ui(real.id));
    await screen.findByText(/No GPS in this session/);
    fireEvent.click(screen.getByRole("button", { name: "Edit Session name" }));
    const field = screen.getByRole("textbox", { name: "Session name" });
    expect(field).toHaveFocus();
    fireEvent.change(field, { target: { value: "  Glen Coe run  " } });
    await act(async () => { fireEvent.keyDown(field, { key: "Enter" }); });
    const patch = calls.find((c) => c.method === "PATCH");
    expect(patch).toEqual({ path: `/sessions/${real.id}`, method: "PATCH", body: { name: "Glen Coe run" } });
    expect(screen.getByRole("heading", { name: /Glen Coe run/ })).toBeInTheDocument();

    // Escape: nothing is sent, the old name stays
    fireEvent.click(screen.getByRole("button", { name: "Edit Session name: Glen Coe run" }));
    const again = screen.getByRole("textbox", { name: "Session name" });
    fireEvent.change(again, { target: { value: "oops" } });
    fireEvent.keyDown(again, { key: "Escape" });
    expect(screen.queryByRole("textbox", { name: "Session name" })).toBeNull();
    expect(screen.getByRole("heading", { name: /Glen Coe run/ })).toBeInTheDocument();
    expect(calls.filter((c) => c.method === "PATCH")).toHaveLength(1);
  });

  it("inline description: blur saves; a refused PATCH rolls back with a toast", async () => {
    const { ctx } = renderWithApp(ui(real.id));
    await screen.findByText(/No GPS in this session/);
    fireEvent.click(screen.getByRole("button", { name: "Edit Description" }));
    const field = screen.getByRole("textbox", { name: "Description" });
    fireEvent.change(field, { target: { value: "Checked the rear height." } });
    await act(async () => { fireEvent.blur(field); });
    expect(calls.find((c) => c.method === "PATCH")?.body).toEqual({ description: "Checked the rear height." });
    expect(screen.getByText("Checked the rear height.")).toBeInTheDocument();

    patchReply = { status: 403, body: { ok: false, error: "read-only session" } };
    fireEvent.click(screen.getByRole("button", { name: /^Edit Description:/ }));
    const again = screen.getByRole("textbox", { name: "Description" });
    fireEvent.change(again, { target: { value: "" } });
    await act(async () => { fireEvent.blur(again); });
    expect(calls.filter((c) => c.method === "PATCH").at(-1)?.body).toEqual({ description: null });
    await waitFor(() => expect(screen.getByText("Checked the rear height.")).toBeInTheDocument());
    expect(ctx.toast).toHaveBeenCalledWith("Not saved: read-only session", true);
  });

  it("a demo log: name and description are read-only, no Delete", async () => {
    renderWithApp(ui(demo.id));
    await screen.findByRole("button", { name: "Play" });
    expect(screen.getByRole("heading", { name: "Demo log 1" })).toBeInTheDocument();
    expect(screen.getByText("A synthetic demo drive.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Edit / })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
  });

  it("public mode hides Delete, the note tool and the inline editors", async () => {
    renderWithApp(ui(real.id), { snap: { status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], public: true } });
    await screen.findByText(/No GPS in this session/);
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Edit / })).toBeNull();
    expect(screen.queryByRole("button", { name: "Drag to note" })).toBeNull();
  });
});

/* ---- live (spec §7) ---- */

const fix = (lat: number, lon: number, heading: number | null = 90): GpsFix => ({
  fix: true, lat, lon, heading, speed_kmh: 42, sats: 9, hdop: 0.9, src: "usb", age_s: 0.2,
});
const liveSnap = (over: Partial<Snapshot> = {}): Snapshot => ({
  status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", faults: [],
  signals: { rpm: { v: 1234, u: "rpm" } },
  recording: { session: real.id, since_utc: "2026-10-03T04:00:00.000Z", rows: 3, state: "recording" },
  ...over,
});
const dataCalls = () => calls.filter((c) => c.path.startsWith(`/sessions/${real.id}/data?`)).length;

/** Render live, returning a function that pushes a new snapshot (as the SSE stream would). */
function renderLive(snap: Snapshot | null) {
  const { ctx, rerender } = renderWithApp(ui(), { snap });
  const tree = (c: AppContext): ReactElement => <AppCtx.Provider value={c}>{ui()}</AppCtx.Provider>;
  return { ctx, push: (next: Snapshot | null) => rerender(tree({ ...ctx, snap: next })) };
}

describe("Analysis — live", () => {
  it("shows the recording session with a Live chip, live readouts and no transport; re-fetches every 5 s", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    renderLive(liveSnap());
    expect(await screen.findByTestId("live-chip")).toHaveTextContent("Live");
    await screen.findByText(/No GPS in this session/);
    expect(document.querySelector(`[data-session="${real.id}"]`)).not.toBeNull();
    expect(screen.queryByTestId("global-transport")).toBeNull();
    expect(screen.queryByRole("region", { name: "Notes" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Drag to note" })).toBeNull();
    // readouts: rpm from the snapshot, coolant (not in it) from the newest sample
    const ro = screen.getByRole("group", { name: "Live values" });
    expect(within(ro).getByText(fmt(1234))).toBeInTheDocument();
    expect(within(ro).getByText(fmt(82))).toBeInTheDocument();
    expect(calls.some((c) => c.path === `/sessions/${real.id}` && c.method === "GET")).toBe(true);

    const first = dataCalls();
    expect(first).toBe(1);
    await act(async () => { vi.advanceTimersByTime(5_000); });
    await waitFor(() => expect(dataCalls()).toBe(2));
    await act(async () => { vi.advanceTimersByTime(4_999); });
    expect(dataCalls()).toBe(2);
    await act(async () => { vi.advanceTimersByTime(1); });
    await waitFor(() => expect(dataCalls()).toBe(3));
  });

  it("a paused recording is still shown live", async () => {
    renderLive(liveSnap({ recording: { session: real.id, since_utc: "1970-01-01T00:00:00.000Z", rows: 3, state: "paused" } }));
    await screen.findByText(/No GPS in this session/);
    expect(screen.getByTestId("live-chip")).toBeInTheDocument();
    expect(screen.getByText(/paused/)).toBeInTheDocument();
  });

  it("the map marker follows snap.gps between fetches", async () => {
    mapMock.fail = false;
    const { push } = renderLive(liveSnap({ gps: fix(56.6, -4.8, 90) }));
    await waitFor(() => expect(mapMock.handle).not.toBeNull());
    const h = mapMock.handle!;
    await waitFor(() => expect(h.setCursor).toHaveBeenLastCalledWith({ lat: 56.6, lon: -4.8, heading: 90 }));
    const fetched = dataCalls();
    push(liveSnap({ gps: fix(56.61, -4.79, 120) }));
    await waitFor(() => expect(h.setCursor).toHaveBeenLastCalledWith({ lat: 56.61, lon: -4.79, heading: 120 }));
    expect(dataCalls()).toBe(fetched); // no re-fetch needed to move the marker
  });

  it("GPS but no recording: the map sits at the live position with the hint", async () => {
    mapMock.fail = false;
    const { push } = renderLive({ status: "connecting", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], gps: fix(56.6, -4.8, null) });
    expect(screen.getByText("Recording starts when the car connects.")).toBeInTheDocument();
    expect(screen.queryByTestId("live-chip")).toBeNull();
    await waitFor(() => expect(mapMock.handle).not.toBeNull());
    await waitFor(() => expect(mapMock.handle!.setCursor).toHaveBeenLastCalledWith({ lat: 56.6, lon: -4.8, heading: null }));
    push({ status: "connecting", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], gps: fix(56.7, -4.7, 10) });
    await waitFor(() => expect(mapMock.handle!.setCursor).toHaveBeenLastCalledWith({ lat: 56.7, lon: -4.7, heading: 10 }));
    expect(calls.filter((c) => c.path.startsWith("/sessions"))).toEqual([]);
  });

  it("nothing at all: an empty state offering Rewind", () => {
    renderLive({ status: "disconnected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], gps: { ...fix(0, 0), fix: false } });
    expect(screen.getByText("Nothing to show yet")).toBeInTheDocument();
    expect(screen.getByText(/Rewind/)).toBeInTheDocument();
    expect(document.querySelector("[data-map-status]")).toBeNull();
    expect(screen.queryByTestId("global-transport")).toBeNull();
  });
});
