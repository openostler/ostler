import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import sessionDataFx from "../api/fixtures/session-data.json";
import sessionsFx from "../api/fixtures/sessions.json";
import type { SessionMeta } from "../api/schemas";
import { formatDuration, formatPos } from "../components/replay/sessionFormat";
import { lineColorExpression, rangeOf } from "../components/replay/trace";
import { fmt } from "../lib/format";
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
    mapMock.handle = { setTrace: vi.fn(), setColor: vi.fn(), setCursor: vi.fn(), isBlank: vi.fn(() => false), destroy: vi.fn() };
    return mapMock.handle;
  },
}));

const demo = sessionsFx.sessions[0] as unknown as SessionMeta;
const real: SessionMeta = {
  ...demo, id: "20261004T170000Z", start_utc: "2026-10-04T17:00:00.000Z", synthetic: false, source: "live",
  has_gps: false, start_pos: null, end_pos: null, bbox: null, distance_km: 0, max_speed_kmh: null,
  channels: [{ name: "rpm", units: "rpm", group: "engine" }, { name: "coolant_temp", units: "°C", group: "engine" }],
};
// Expected values come from the contract fixtures (regenerated from the real server).
const fxData = sessionDataFx as unknown as { t: number[]; ch: Record<string, (number | null)[]> };
const fxRpm = fxData.ch.rpm!;
const fxSpeedRange = rangeOf(fxData.ch.GPS_Speed)!;
const fxRpmRange = rangeOf(fxRpm)!;
const realData = { id: real.id, t: [0, 1000, 2000], utc: [null, null, null], ch: { rpm: [800, 900, 1000], coolant_temp: [80, null, 82] }, track: [], decimated: false };

type Call = { path: string; method: string; body?: unknown };
let calls: Call[];

function stubServer() {
  calls = [];
  const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const method = init?.method ?? "GET";
    calls.push({ path: url.pathname + url.search, method, body: init?.body ? JSON.parse(String(init.body)) : undefined });
    const p = url.pathname;
    if (p === "/sessions") return json({ sessions: [demo, real] });
    if (p === `/sessions/${demo.id}`) return json(demo);
    if (p === `/sessions/${demo.id}/data`) return json(sessionDataFx);
    if (p === `/sessions/${real.id}`) return json(real);
    if (p === `/sessions/${real.id}/data`) return json(realData);
    if (p === "/command") return json({ ok: true });
    return json({ error: "not found" }, 404);
  }));
}

beforeEach(() => {
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

describe("Logs — session browser", () => {
  it("lists sessions by day with the row details and a demo chip", async () => {
    renderWithApp(<Logs />);
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
  });

  it("shows the Recording now card while recording", async () => {
    renderWithApp(<Logs />, {
      snap: { status: "connected", signals: {}, faults: [], ts: 10_000 + 7 * 60 + 5, recording: { session: real.id, since: 10_000, rows: 120 } },
    });
    expect(await screen.findByText("Recording now · 7 min")).toBeInTheDocument();
  });
});

describe("Logs — replay", () => {
  it("opens the demo session: fallback trace without WebGL, legend, readouts, no Delete", async () => {
    renderWithApp(<Logs />);
    await openDemo();
    await waitFor(() => expect(document.querySelector("[data-map-status]")).toHaveAttribute("data-map-status", "failed"));
    expect(screen.getByRole("img", { name: "Session trace" })).toBeInTheDocument();
    expect(screen.getByText(/Map unavailable/)).toBeInTheDocument();
    // default trace channel: no ECU `speed` → GPS_Speed
    expect(screen.getByRole("combobox", { name: "Trace channel" })).toHaveValue("GPS_Speed");
    expect(screen.getByTestId("legend-min")).toHaveTextContent(`${fmt(fxSpeedRange.min)} km/h`);
    expect(screen.getByTestId("legend-max")).toHaveTextContent(`${fmt(fxSpeedRange.max)} km/h`);
    // readouts at the cursor (the first sample)
    const ro = screen.getByRole("group", { name: "Values at the cursor" });
    expect(within(ro).getByText(fmt(fxRpm[0]))).toBeInTheDocument();
    // synthetic → never deletable; exports are links
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
    const csv = screen.getByRole("link", { name: "CSV" });
    expect(csv).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=csv`);
    expect(screen.getByRole("link", { name: "VBO" })).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=vbo`);
    expect(screen.getByRole("link", { name: "GPX" })).toHaveAttribute("href", `/sessions/${demo.id}/export?fmt=gpx`);
    expect(calls.some((c) => c.path.startsWith(`/sessions/${demo.id}/data?ch=`))).toBe(true);
  });

  it("drives the MapLibre handle: trace colour expression, re-bucketed trace on channel change, cursor", async () => {
    mapMock.fail = false;
    renderWithApp(<Logs />);
    await openDemo();
    await waitFor(() => expect(mapMock.handle).not.toBeNull());
    const h = mapMock.handle!;
    await waitFor(() => expect(h.setColor).toHaveBeenCalledWith(lineColorExpression()));
    expect(h.setCursor).toHaveBeenCalled();
    const n = h.setTrace!.mock.calls.length;
    fireEvent.change(screen.getByRole("combobox", { name: "Trace channel" }), { target: { value: "rpm" } });
    await waitFor(() => expect(h.setTrace!.mock.calls.length).toBeGreaterThan(n));
    expect(screen.getByTestId("legend-max")).toHaveTextContent(`${fmt(fxRpmRange.max)} rpm`);
  });

  it("scrubbing moves the readouts", async () => {
    renderWithApp(<Logs />);
    await openDemo();
    const i = fxRpm.findIndex((v, k) => k > 0 && v != null && v !== fxRpm[0]);
    fireEvent.change(screen.getByRole("slider", { name: "Playback position" }), { target: { value: String(fxData.t[i]) } });
    const ro = screen.getByRole("group", { name: "Values at the cursor" });
    expect(within(ro).getByText(fmt(fxRpm[i]))).toBeInTheDocument();
  });

  it("a real session: chart-only without GPS, Delete needs the typed id and posts delete_session", async () => {
    const { ctx } = renderWithApp(<Logs />);
    await screen.findByText("demo");
    fireEvent.click(document.querySelector(`[data-session="${real.id}"]`)!);
    await screen.findByText(/No GPS in this session/);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    const go = screen.getByRole("button", { name: "Delete session" });
    expect(go).toBeDisabled();
    fireEvent.change(screen.getByRole("textbox", { name: `Type ${real.id} to confirm` }), { target: { value: real.id } });
    expect(go).toBeEnabled();
    await act(async () => { fireEvent.click(go); });
    expect(calls.find((c) => c.path === "/command")?.body).toEqual({ action: "delete_session", params: { id: real.id } });
    expect(ctx.toast).toHaveBeenCalledWith("session deleted");
    await screen.findByText("demo"); // back on the list
  });

  it("public mode hides Delete", async () => {
    renderWithApp(<Logs />, { snap: { status: "connected", signals: {}, faults: [], public: true } });
    await screen.findByText("demo");
    fireEvent.click(document.querySelector(`[data-session="${real.id}"]`)!);
    await screen.findByText(/No GPS in this session/);
    expect(screen.queryByRole("button", { name: "Delete" })).toBeNull();
  });

  it("a recording session re-fetches every 5 s and offers Follow live", async () => {
    const live = { ...real, recording: true };
    vi.mocked(fetch).mockImplementation(async (input) => {
      const p = new URL(String(input), "http://dash.local").pathname;
      calls.push({ path: p, method: "GET" });
      const body = p === "/sessions" ? { sessions: [live] } : p.endsWith("/data") ? realData : live;
      return new Response(JSON.stringify(body), { headers: { "Content-Type": "application/json" } });
    });
    renderWithApp(<Logs />);
    await screen.findByText("recording");
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] });
    try {
      fireEvent.click(document.querySelector(`[data-session="${real.id}"]`)!);
      await screen.findByRole("button", { name: "Follow live" });
      expect(screen.getByRole("button", { name: "Follow live" })).toHaveAttribute("aria-pressed", "true");
      const before = calls.filter((c) => c.path.endsWith("/data")).length;
      await act(async () => { vi.advanceTimersByTime(5000); });
      await waitFor(() => expect(calls.filter((c) => c.path.endsWith("/data")).length).toBeGreaterThan(before));
    } finally {
      vi.useRealTimers();
    }
  });
});
