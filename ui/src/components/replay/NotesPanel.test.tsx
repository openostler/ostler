import { fireEvent, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../../api/schemas";
import type { Flag } from "../../lib/flags";
import { INACTIVE, ReplayCtx, type Replay } from "../../state/replay";
import { renderWithApp } from "../../test/renderWithApp";
import { NotesPanel } from "./NotesPanel";

const flagState = vi.hoisted(() => ({ visible: [] as Flag[] }));
vi.mock("../../state/flags", () => ({
  useSessionFlags: () => ({ all: flagState.visible, visible: flagState.visible, counts: { range: 0, faults: 0 } }),
}));

const META = {
  id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 600, rows: 2, parts: [], modules: ["td5"],
  channels: [], has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
  synthetic: false, recording: false, source: "mock", audio: [],
} as unknown as NonNullable<Replay["session"]>;
const NOTES: Note[] = [
  { id: "n1", t: 120_000, t_end: null, text: "Misfire", tags: [], kind: "note", source: "retro", created: "" },
  { id: "n2", t: 300_000, t_end: null, text: "Rattle", tags: [], kind: "note", source: "retro", created: "" },
];
const WARN: Flag = {
  id: "range:coolant:60000", kind: "range", severity: "warn", t: 60_000, t_end: 125_000, label: "Coolant 112 °C (normal 80–105)",
  signal: "coolant", unit: "°C", peak: 112, peakT: 90_000, band: [80, 105], limits: [-40, 120],
};
const FAULT: Flag = { id: "fault:P0380:200000", kind: "fault", severity: "alarm", t: 200_000, t_end: null, label: "P0380 Glow plug", faults: ["P0380 Glow plug (Current)"], current: true };

const show = (over: Partial<Replay> = {}) => {
  const r = { ...INACTIVE, active: true, id: "s1", session: META, notes: NOTES, t: 0, follow: false, setFollow: vi.fn(), seek: vi.fn(), ...over } as Replay;
  renderWithApp(<ReplayCtx.Provider value={r}><NotesPanel /></ReplayCtx.Provider>);
  return r;
};
const rowText = () => within(screen.getByRole("list")).getAllByRole("listitem").map((li) => li.textContent);

beforeEach(() => { flagState.visible = [WARN, FAULT]; });

describe("NotesPanel flags", () => {
  it("interleaves flags with notes by time, with icon and severity word", () => {
    show();
    const rows = rowText();
    expect(rows).toHaveLength(4);
    expect(rows[0]).toMatch(/1:00–2:05.*Coolant 112 °C.*Warning/);
    expect(rows[1]).toMatch(/2:00.*Misfire/);
    expect(rows[2]).toMatch(/3:20.*P0380 Glow plug.*Alarm/);
    expect(rows[3]).toMatch(/5:00.*Rattle/);
  });

  it("filters All · Notes · Out of range · Faults", () => {
    show();
    const filter = screen.getByRole("group", { name: "Show" });
    expect(within(filter).getByRole("button", { name: "All" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(within(filter).getByRole("button", { name: "Notes" }));
    expect(rowText()).toHaveLength(2);
    fireEvent.click(within(filter).getByRole("button", { name: "Out of range" }));
    expect(rowText()).toEqual([expect.stringMatching(/Coolant/)]);
    fireEvent.click(within(filter).getByRole("button", { name: "Faults" }));
    expect(rowText()).toEqual([expect.stringMatching(/P0380/)]);
    expect(within(filter).getByRole("button", { name: "Faults" })).toHaveAttribute("aria-pressed", "true");
  });

  it("an empty filter says so", () => {
    flagState.visible = [WARN];
    show();
    fireEvent.click(screen.getByRole("button", { name: "Faults" }));
    expect(screen.getByText("No fault flags in this session.")).toBeInTheDocument();
  });

  it("tapping a flag row opens the flag sheet; a note row still jumps", () => {
    const r = show();
    fireEvent.click(screen.getByRole("button", { name: /^Alarm at 3:20: P0380/ }));
    expect(screen.getByRole("dialog")).toHaveTextContent("P0380 Glow plug");
    expect(screen.getByRole("dialog")).toHaveTextContent("Current");
    fireEvent.click(screen.getByRole("button", { name: "Jump to" }));
    expect(r.seek).toHaveBeenCalledWith(200_000);
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Jump to 2:00: Misfire/ }));
    expect(r.seek).toHaveBeenCalledWith(120_000);
  });

  it("no flags: no filter row, notes as before", () => {
    flagState.visible = [];
    show();
    expect(screen.queryByRole("group", { name: "Show" })).toBeNull();
    expect(rowText()).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Edit note" })).toHaveLength(2);
  });
});
