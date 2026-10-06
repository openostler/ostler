// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import sessionDataFx from "../api/fixtures/session-data.json";
import sessionsFx from "../api/fixtures/sessions.json";
import type { Note, SessionMeta } from "../api/schemas";
import { GlobalTransport } from "../components/GlobalTransport";
import { formatDuration, rowDate } from "../components/replay/sessionFormat";
import { moduleName } from "../layout";
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


describe("Logs — session browser", () => {
  it("lists sessions under year/month headers with the row details and a demo chip", async () => {
    renderWithApp(ui());
    const row = await screen.findByText("demo");
    const btn = row.closest("button")!;
    expect(btn.querySelector(".replay-row-title")).toHaveTextContent("Demo log 1");
    expect(btn).toHaveTextContent("Rannoch Moor");
    expect(btn).toHaveTextContent("2 notes");
    expect(document.querySelector(`[data-session="${real.id}"] .replay-row-title`)).toHaveTextContent("Untitled session");
    expect(btn).toHaveTextContent(rowDate(demo));
    expect(btn).toHaveTextContent(formatDuration(demo.duration_s));
    expect(btn).toHaveTextContent(`${fmt(demo.distance_km, 1)} km`);
    expect(btn).toHaveTextContent(demo.modules.map(moduleName).join(", "));
    const other = document.querySelector(`[data-session="${real.id}"]`)!;
    expect(within(other as HTMLElement).queryByText("demo")).toBeNull();
    expect(screen.getByRole("heading", { name: "2026" })).toBeInTheDocument();
    expect(document.querySelectorAll("[data-month]").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Place names © OpenStreetMap contributors \(ODbL\) · GeoNames \(CC BY 4\.0\)/)).toBeInTheDocument();
    expect(screen.queryByTestId("global-transport")).toBeNull(); // live: no transport
  });
});

describe("Logs — opening a session", () => {
  it("enters the global replay and switches to the Analysis tab", async () => {
    const { ctx } = renderWithApp(ui());
    await screen.findByText("demo");
    fireEvent.click(document.querySelector(`[data-session="${demo.id}"]`)!);
    expect(ctx.goTo).toHaveBeenCalledWith("logs.analysis");
    // the replay is open (the global transport shows); Logs stays the browser
    await screen.findByRole("button", { name: "Play" });
    expect(calls.some((c) => c.path.startsWith(`/sessions/${demo.id}/data?ch=`))).toBe(true);
    expect(screen.getByRole("heading", { name: "Logs" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "‹ Sessions" })).toBeNull();
  });

  it("the drive in progress opens LIVE on Analysis (no replay); Rewind is how you replay it", async () => {
    const { ctx } = renderWithApp(ui(), {
      snap: { status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], recording: { session: real.id, since_utc: "1970-01-01T00:00:00.000Z", rows: 5, state: "recording" } },
    });
    await screen.findByText("demo");
    fireEvent.click(document.querySelector(`[data-session="${real.id}"]`)!);
    expect(ctx.goTo).toHaveBeenCalledWith("logs.analysis");
    expect(screen.queryByRole("button", { name: "Play" })).toBeNull();
    expect(calls.some((c) => c.path.startsWith(`/sessions/${real.id}/data?ch=`))).toBe(false);
  });
});
