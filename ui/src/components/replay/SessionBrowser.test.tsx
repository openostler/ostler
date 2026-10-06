// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import sessionsFx from "../../api/fixtures/sessions.json";
import { SessionList as SessionListSchema, type SessionMeta } from "../../api/schemas";
import { DEFAULT_PREFS } from "../../state/prefs";
import { renderWithApp } from "../../test/renderWithApp";
import { SessionBrowser } from "./SessionBrowser";
import { groupByYearMonth, indexAt, monthEndCursor, heatLevel, sessionTitle, isPaused } from "./sessionFormat";

// Only the fixture's shape is borrowed; every field a test asserts on is set here.
const base: SessionMeta = {
  ...SessionListSchema.parse(sessionsFx).sessions[0]!,
  name: null, description: null, place: null, place_start: null, place_end: null, note_count: 0,
  modules: ["td5", "slabs"], has_gps: true, distance_km: 11.2, duration_s: 720,
};
const mk = (id: string, iso: string, over: Partial<SessionMeta> = {}): SessionMeta =>
  ({ ...base, id, start_utc: iso, synthetic: false, source: "live", recording: false, ...over });

const s1 = mk("20261005T090000Z", "2026-10-05T09:00:00.000Z", { name: "Demo log 1", synthetic: true, source: "demo", note_count: 2,
  place: { label: "Rannoch Moor", source: "geonames" } });
const s2 = mk("20261002T120000Z", "2026-10-02T12:00:00.000Z", { place: { label: "Fort William", source: "osm" } });
const s3 = mk("20260815T120000Z", "2026-08-15T12:00:00.000Z", { name: "Ride height check", place: { label: "Oban", source: "geonames" }, note_count: 1 });
const s4 = mk("20251220T120000Z", "2025-12-20T12:00:00.000Z");

type Call = { path: string; params: URLSearchParams };
let calls: Call[];
let pages: (p: URLSearchParams) => { sessions: SessionMeta[]; next: string | null };
let months: { key: string; count: number; km: number }[];
let days: { key: string; count: number; km: number }[];

const json = (b: unknown, status = 200) => new Response(JSON.stringify(b), { status, headers: { "Content-Type": "application/json" } });
function stub() {
  calls = [];
  pages = () => ({ sessions: [s1, s2, s3, s4], next: null });
  months = [{ key: "2026-10", count: 2, km: 30 }, { key: "2026-08", count: 1, km: 5 }, { key: "2025-12", count: 1, km: 0 }];
  days = [{ key: "2026-10-05", count: 1, km: 11.2 }, { key: "2026-10-02", count: 1, km: 40 }, { key: "2026-08-15", count: 1, km: 5 }];
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = new URL(input, "http://dash.local");
    calls.push({ path: url.pathname, params: url.searchParams });
    if (url.pathname === "/sessions") return json(pages(url.searchParams));
    if (url.pathname === "/sessions/histogram") {
      return url.searchParams.get("group") === "day" ? json({ group: "day", buckets: days }) : json({ group: "month", buckets: months });
    }
    return json({ error: "not found" }, 404);
  }));
}
const listCalls = () => calls.filter((c) => c.path === "/sessions");
const lastList = () => listCalls().at(-1)!.params;

const browser = (onOpen = vi.fn()) => (
  <SessionBrowser recording={null} nowS={1_791_000_000} units={DEFAULT_PREFS.units} onOpen={onOpen} />
);

beforeEach(() => {
  stub();
  vi.useFakeTimers({ toFake: ["Date"], now: new Date(2026, 9, 5, 18, 0) });
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("sessionFormat (logs at scale)", () => {
  it("groups newest first by local year → month", () => {
    const local = (y: number, m: number, d: number) => new Date(y, m - 1, d, 12).toISOString();
    const g = groupByYearMonth([mk("a", local(2025, 12, 20)), mk("b", local(2026, 10, 5)), mk("c", local(2026, 8, 1)), mk("d", local(2026, 10, 2))]);
    expect(g.map((y) => y.year)).toEqual([2026, 2025]);
    expect(g[0]!.months.map((m) => m.key)).toEqual(["2026-10", "2026-08"]);
    expect(g[0]!.months[0]!.sessions.map((s) => s.id)).toEqual(["b", "d"]);
    expect(g[1]!.months[0]!.key).toBe("2025-12");
  });

  it("title falls back name → place → Untitled session", () => {
    expect(sessionTitle(s1)).toBe("Demo log 1");
    expect(sessionTitle(s2)).toBe("Fort William");
    expect(sessionTitle({ ...s4, name: "   " })).toBe("Untitled session");
  });

  it("month-end cursor: the last UTC ms of the month with an id after every id", () => {
    expect(monthEndCursor("2026-08")).toBe(`${Date.UTC(2026, 8, 1) - 1}:~`);
    expect(monthEndCursor("2025-12")).toBe(`${Date.UTC(2026, 0, 1) - 1}:~`);
    expect("20260831T235959Z" < "~").toBe(true);
  });

  it("scrubber hit-testing and heat levels", () => {
    expect(indexAt(0, 0, 100, 4)).toBe(0);
    expect(indexAt(60, 0, 100, 4)).toBe(2);
    expect(indexAt(500, 0, 100, 4)).toBe(3);
    expect(indexAt(-5, 0, 100, 4)).toBe(0);
    expect(heatLevel(0, 10)).toBe(0);
    expect(heatLevel(1, 10)).toBe(1);
    expect(heatLevel(10, 10)).toBe(4);
  });

  it("paused: only an explicit non-recording state", () => {
    expect(isPaused({ state: "paused" })).toBe(true);
    expect(isPaused({ state: "recording" })).toBe(false);
    expect(isPaused({})).toBe(false);
    expect(isPaused(null)).toBe(false);
  });
});

describe("SessionBrowser", () => {
  it("rows: name or place, place line, modules by display name, notes, demo chip; sticky year/month headers", async () => {
    renderWithApp(browser());
    const row1 = (await screen.findByText("Demo log 1")).closest("button")!;
    expect(row1).toHaveTextContent("Rannoch Moor");
    expect(row1).toHaveTextContent("2 notes");
    expect(within(row1).getByText("demo")).toBeInTheDocument();
    expect(row1).toHaveTextContent("TD5 (engine)");
    const row2 = document.querySelector(`[data-session="${s2.id}"]`)!;
    expect(row2.querySelector(".replay-row-title")).toHaveTextContent("Fort William");
    expect(row2.querySelector(".replay-row-place")).toBeNull();
    expect(document.querySelector(`[data-session="${s3.id}"]`)).toHaveTextContent("1 note");
    expect(document.querySelector(`[data-session="${s4.id}"] .replay-row-title`)).toHaveTextContent("Untitled session");
    expect(screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent)).toEqual(expect.arrayContaining(["2026", "2025"]));
    expect([...document.querySelectorAll(".logs-month")].map((m) => m.getAttribute("data-month"))).toEqual(["2026-10", "2026-08", "2025-12"]);
    expect(lastList().get("limit")).toBe("50");
    expect(lastList().get("before")).toBeNull();
  });

  it("opening a row calls onOpen with its id", async () => {
    const onOpen = vi.fn();
    renderWithApp(browser(onOpen));
    fireEvent.click((await screen.findByText("Ride height check")).closest("button")!);
    expect(onOpen).toHaveBeenCalledWith(s3.id);
  });

  it("pages with `next`: Load more appends the following page; no button on the last page", async () => {
    pages = (p) => (p.get("before") === "c1" ? { sessions: [s3, s4], next: null } : { sessions: [s1, s2], next: "c1" });
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    expect(screen.queryByText("Ride height check")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Load more" }));
    await screen.findByText("Ride height check");
    expect(lastList().get("before")).toBe("c1");
    expect(document.querySelectorAll("[data-session]")).toHaveLength(4);
    expect(screen.queryByRole("button", { name: "Load more" })).toBeNull();
  });

  it("infinite scroll: the sentinel coming into view loads the next page", async () => {
    let fire: (() => void) | null = null;
    class IO {
      constructor(cb: (e: { isIntersecting: boolean }[]) => void) { fire = () => cb([{ isIntersecting: true }]); }
      observe() {}
      disconnect() {}
    }
    vi.stubGlobal("IntersectionObserver", IO);
    pages = (p) => (p.get("before") === "c1" ? { sessions: [s3], next: null } : { sessions: [s1, s2], next: "c1" });
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    await act(async () => { fire!(); });
    await screen.findByText("Ride height check");
    expect(listCalls().filter((c) => c.params.get("before") === "c1")).toHaveLength(1);
  });

  it("month scrubber: keys and drag jump with before=<end of that month>; Back to newest resets", async () => {
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    const scrub = await screen.findByRole("slider", { name: "Jump to month" });
    expect(scrub).toHaveAttribute("aria-valuemax", "2");
    expect(scrub).toHaveAttribute("aria-valuetext", expect.stringMatching(/2026/));
    fireEvent.keyDown(scrub, { key: "ArrowDown" });
    await waitFor(() => expect(lastList().get("before")).toBe(monthEndCursor("2026-08")));
    expect(screen.getByText(/From August 2026 back/)).toBeInTheDocument();

    // drag to the bottom third → December 2025
    vi.spyOn(scrub, "getBoundingClientRect").mockReturnValue({ top: 0, height: 300, left: 0, width: 36, bottom: 300, right: 36, x: 0, y: 0, toJSON: () => ({}) });
    fireEvent.pointerDown(scrub, { pointerId: 1, clientY: 10 });
    fireEvent.pointerMove(scrub, { pointerId: 1, clientY: 290 });
    expect(document.querySelector(".logs-scrub-bubble")).toHaveTextContent(/Dec/);
    fireEvent.pointerUp(scrub, { pointerId: 1, clientY: 290 });
    await waitFor(() => expect(lastList().get("before")).toBe(monthEndCursor("2025-12")));

    fireEvent.click(screen.getByRole("button", { name: "Back to newest" }));
    await waitFor(() => expect(lastList().get("before")).toBeNull());
  });

  it("search is debounced 300 ms and sends one q for a burst of typing", async () => {
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    const box = screen.getByRole("searchbox", { name: "Search sessions" });
    const before = listCalls().length;
    fireEvent.change(box, { target: { value: "m" } });
    fireEvent.change(box, { target: { value: "mo" } });
    fireEvent.change(box, { target: { value: "moor" } });
    await new Promise((r) => setTimeout(r, 150));
    expect(listCalls()).toHaveLength(before);
    await waitFor(() => expect(lastList().get("q")).toBe("moor"));
    expect(listCalls().filter((c) => c.params.has("q"))).toHaveLength(1);
  });

  it("filter chips: module, has notes, min distance and a date range go to the query; Clear resets", async () => {
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    fireEvent.change(screen.getByRole("combobox", { name: "Module" }), { target: { value: "slabs" } });
    await waitFor(() => expect(lastList().get("module")).toBe("slabs"));
    fireEvent.click(screen.getByRole("button", { name: "Has notes" }));
    await waitFor(() => expect(lastList().get("has_notes")).toBe("1"));
    expect(screen.getByRole("button", { name: "Has notes" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.change(screen.getByRole("combobox", { name: "Minimum distance" }), { target: { value: "5" } });
    await waitFor(() => expect(lastList().get("min_km")).toBe("5"));
    fireEvent.click(screen.getByRole("button", { name: "Dates" }));
    fireEvent.change(screen.getByLabelText("From date"), { target: { value: "2026-08-01" } });
    fireEvent.change(screen.getByLabelText("To date"), { target: { value: "2026-08-31" } });
    await waitFor(() => expect(lastList().get("to")).toBe("2026-08-31"));
    const p = lastList();
    expect([p.get("module"), p.get("has_notes"), p.get("min_km"), p.get("from")]).toEqual(["slabs", "1", "5", "2026-08-01"]);

    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    await waitFor(() => expect([...lastList().keys()]).toEqual(["limit"]));
  });

  it("the This-year heatmap: tapping a day filters from/to that day; tapping it again clears", async () => {
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    const heat = await screen.findByRole("region", { name: /This year: 3 sessions in 2026/ });
    expect(within(heat).getAllByRole("button")).toHaveLength(3);
    const cell = heat.querySelector('[data-day="2026-10-02"]') as HTMLButtonElement;
    expect(cell.tagName).toBe("BUTTON");
    expect(cell).toHaveAttribute("data-level", "4"); // the longest day
    expect(heat.querySelector('[data-day="2026-10-03"]')!.tagName).toBe("SPAN"); // no sessions
    fireEvent.click(cell);
    await waitFor(() => expect(lastList().get("from")).toBe("2026-10-02"));
    expect(lastList().get("to")).toBe("2026-10-02");
    expect(heat.querySelector('[data-day="2026-10-02"]')).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(heat.querySelector('[data-day="2026-10-02"]')!);
    await waitFor(() => expect(lastList().get("from")).toBeNull());
  });

  it("empty and no-results states", async () => {
    pages = () => ({ sessions: [], next: null });
    renderWithApp(browser());
    await screen.findByText(/No sessions yet/);
    fireEvent.change(screen.getByRole("searchbox", { name: "Search sessions" }), { target: { value: "zzz" } });
    await screen.findByText(/No sessions match “zzz”/, undefined, { timeout: 2000 });
    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    await screen.findByText(/No sessions yet/);
    expect(screen.getByRole("searchbox", { name: "Search sessions" })).toHaveValue("");
  });

  it("no histogram (older server): no scrubber, no heatmap, the list still works", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: string) => {
      const url = new URL(input, "http://dash.local");
      return url.pathname === "/sessions" ? json({ sessions: [s1, s2] }) : json({ error: "not found" }, 404);
    }));
    renderWithApp(browser());
    await screen.findByText("Demo log 1");
    expect(screen.queryByRole("slider", { name: "Jump to month" })).toBeNull();
    expect(screen.queryByRole("region", { name: /This year/ })).toBeNull();
  });
});
