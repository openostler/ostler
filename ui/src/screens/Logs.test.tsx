import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import sessionDataFx from "../api/fixtures/session-data.json";
import sessionsFx from "../api/fixtures/sessions.json";
import type { Note, SessionMeta } from "../api/schemas";
import { GlobalTransport } from "../components/GlobalTransport";
import { formatDuration, formatPos } from "../components/replay/sessionFormat";
import { lineColorExpression, RAMPS, rangeOf } from "../components/replay/trace";
import { fmt } from "../lib/format";
import { ReplayProvider } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { Logs } from "./Logs";

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
      setTrace: vi.fn(), setColor: vi.fn(), setBasemap: vi.fn(), setCursor: vi.fn(), isBlank: vi.fn(() => false), destroy: vi.fn(),
    };
    return mapMock.handle;
  },
}));

const demo = sessionsFx.sessions[0] as unknown as SessionMeta;
const real: SessionMeta = {
  ...demo, id: "20261004T170000Z", start_utc: "2026-10-04T17:00:00.000Z", synthetic: false, source: "live",
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
  id: real.id, t: [0, 1000, 2000], utc: [null, null, null],
  ch: { rpm: [800, 900, 1000], coolant_temp: [80, null, 82], LateralAcc: [0.1, -0.6, 0.2], InlineAcc: [0.3, 0, -0.9] },
  track: [], decimated: false,
};
const note = (id: string, t: number, t_end: number | null = null): Note => ({
  id, t, t_end, text: `note ${id}`, tags: [], kind: "note", source: "retro", created: "2026-10-05T09:02:00.000Z",
});
const demoNotes = [note("a1b2c3d4", 20_000), note("b2c3d4e5", 30_000, 50_000)];

type Call = { path: string; method: string; body?: unknown };
let calls: Call[];

function stubServer() {
  calls = [];
  const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ path: url.pathname + url.search, method, body });
    const p = url.pathname;
    if (p === "/sessions") return json({ sessions: [demo, real] });
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

/** Logs inside the app-root replay, with the global transport (as <App> mounts it). */
const ui = () => (
  <ReplayProvider>
    <Logs />
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
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function openDemo() {
  await screen.findByText("demo");
  fireEvent.click(document.querySelector(`[data-session="${demo.id}"]`)!);
  await screen.findByRole("button", { name: "Play" });
}
async function openReal() {
  await screen.findByText("demo");
  fireEvent.click(document.querySelector(`[data-session="${real.id}"]`)!);
  await screen.findByText(/No GPS in this session/);
}

describe("Logs — session browser", () => {
  it("lists sessions by day with the row details and a demo chip", async () => {
    renderWithApp(ui());
    const row = await screen.findByText("demo");
    const btn = row.closest("button")!;
    expect(btn).toHaveTextContent(formatDuration(demo.duration_s));
    expect(btn).toHaveTextContent(`${fmt(demo.distance_km, 1)} km`);
    expect(btn).toHaveTextContent(`max ${fmt(demo.max_speed_kmh, 0)} km/h`);
    expect(btn).toHaveTextContent(formatPos(demo.start_pos));
    expect(btn).toHaveTextContent(demo.modules.join(", "));
    const other = document.querySelector(`[data-session="${real.id}"]`)!;
    expect(other).toHaveTextContent("no GPS");
    expect(within(other as HTMLElement).queryByText("demo")).toBeNull();
    expect(screen.getAllByRole("region").length).toBeGreaterThanOrEqual(2); // two day groups
    expect(screen.queryByTestId("global-transport")).toBeNull(); // live: no transport
  });
});

describe("Logs — replay", () => {
  it("opening a session enters the global replay: fallback trace, legend, readouts, no Delete; ‹ Sessions exits", async () => {
    renderWithApp(ui());
    await openDemo();
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
    expect(calls.some((c) => c.path.startsWith(`/sessions/${demo.id}/data?ch=`))).toBe(true);
    // no G-G panel without acceleration channels
    expect(document.querySelector(".replay-gg")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "‹ Sessions" }));
    await screen.findByText("demo");
    expect(screen.queryByTestId("global-transport")).toBeNull();
  });

  it("the SVG fallback draws trace B as a second, offset lane", async () => {
    renderWithApp(ui());
    await openDemo();
    await waitFor(() => expect(document.querySelector("[data-map-status]")).toHaveAttribute("data-map-status", "failed"));
    expect(document.querySelectorAll(".replay-svg [data-lane]")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "+ Add trace" }));
    fireEvent.click(within(screen.getByRole("dialog")).getByText("rpm", { selector: ".mono span" }).closest("button")!);
    const lanes = document.querySelectorAll(".replay-svg [data-lane]");
    expect([...lanes].map((l) => l.getAttribute("data-lane"))).toEqual(["a", "b"]);
  });

  it("drives the MapLibre handle: plasma A, mako B as a second lane, basemap switch", async () => {
    mapMock.fail = false;
    renderWithApp(ui());
    await openDemo();
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

    // Classic turns both lanes turbo
    fireEvent.click(screen.getByRole("button", { name: "Classic colours" }));
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith("b", lineColorExpression(RAMPS.turbo)));

    // remove trace B from its picker
    fireEvent.click(screen.getByRole("button", { name: /^Trace B: rpm/ }));
    fireEvent.click(screen.getByRole("button", { name: "Remove trace B" }));
    await waitFor(() => expect(h.setTrace).toHaveBeenLastCalledWith("b", null));
  });

  it("channel picker: pinned chips, categories, search with highlight, pin toggle persisted", async () => {
    renderWithApp(ui());
    await openDemo();
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
    renderWithApp(ui());
    await openDemo();
    const i = fxRpm.findIndex((v, k) => k > 0 && v != null && v !== fxRpm[0]);
    fireEvent.change(screen.getByRole("slider", { name: "Playback position" }), { target: { value: String(fxData.t[i]) } });
    const ro = screen.getByRole("group", { name: "Values at the cursor" });
    await waitFor(() => expect(within(ro).getByText(fmt(fxRpm[i]))).toBeInTheDocument());
  });

  it("the chart draws notes as lines and ranges as bands; no note tool on a demo session", async () => {
    renderWithApp(ui());
    await openDemo();
    await waitFor(() => expect(document.querySelector('[data-note="a1b2c3d4"]')).not.toBeNull());
    expect(document.querySelector('[data-note="a1b2c3d4"]')).toHaveClass("replay-note-line");
    expect(document.querySelector('[data-note="b2c3d4e5"]')).toHaveClass("replay-note-band");
    expect(screen.queryByRole("button", { name: "Drag to note" })).toBeNull();
  });

  it("a real session: G-G panel; a drag with the note tool opens the editor on that range", async () => {
    const width = vi.spyOn(HTMLElement.prototype, "clientWidth", "get").mockReturnValue(300);
    renderWithApp(ui());
    await openReal();
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

  it("a real session: Delete needs the typed id, posts delete_session and leaves replay", async () => {
    const { ctx } = renderWithApp(ui());
    await openReal();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    const go = screen.getByRole("button", { name: "Delete session" });
    expect(go).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: `Type ${real.id} to confirm` }), { target: { value: real.id } });
    expect(go).toBeEnabled();
    await act(async () => { fireEvent.click(go); });
    expect(calls.find((c) => c.path === "/command")?.body).toEqual({ action: "delete_session", params: { id: real.id } });
    expect(ctx.toast).toHaveBeenCalledWith("session deleted");
    await screen.findByText("demo"); // back on the list
    expect(screen.queryByTestId("global-transport")).toBeNull();
  });

  it("public mode hides Delete and the note tool", async () => {
    renderWithApp(ui(), { snap: { status: "connected", signals: {}, faults: [], public: true } });
    await openReal();
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Drag to note" })).toBeNull();
  });
});
