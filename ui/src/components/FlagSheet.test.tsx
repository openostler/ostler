// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, fireEvent, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Field, Note } from "../api/schemas";
import { loadFlagOptions, resetFlagOptionsCache, type Flag } from "../lib/flags";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { FlagSheet, formatDuration } from "./FlagSheet";

vi.mock("./RecordingOptions", () => ({
  RecordingOptions: ({ onClose }: { onClose: () => void }) => <div role="dialog" aria-label="Recording options"><button onClick={onClose}>Done</button></div>,
}));

const META = {
  id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 600, rows: 2, parts: [], modules: ["td5"],
  channels: [], has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
  synthetic: false, recording: false, source: "mock", audio: [],
} as unknown as NonNullable<Replay["session"]>;

const replay = (over: Partial<Replay> = {}): Replay => ({
  ...INACTIVE, active: true, id: "s1", session: META, t: 0,
  follow: false, setFollow: vi.fn(), seek: vi.fn(), addNote: vi.fn(async () => ({}) as Note),
  ...over,
} as Replay);

const COOLANT: Field = {
  name: "coolant", unit: "°C", c: "verified", limits: [-40, 120], label: "Coolant temp", group: "Engine", description: "",
  derived: false, span: [-40, 130], normal: [80, 105],
} as Field;

const RANGE: Flag = {
  id: "range:coolant:60000", kind: "range", severity: "warn", t: 60_000, t_end: 125_000,
  label: "Coolant 112 °C (normal 80–105)", signal: "coolant", unit: "°C", peak: 112, peakT: 90_000, band: [80, 105], limits: [-40, 120],
};
const FAULT: Flag = {
  id: "fault:x:0", kind: "fault", severity: "alarm", t: 0, t_end: null, label: "2 stored faults",
  faults: ["P0380 Glow plug circuit (Current)", "P0110 Air temp sensor (Logged)"], current: true,
};

function show(ui: ReactElement, r: Replay, over: Parameters<typeof renderWithApp>[1] = {}) {
  return renderWithApp(<ReplayCtx.Provider value={r}>{ui}</ReplayCtx.Provider>, { fields: { coolant: COOLANT }, ...over });
}

beforeEach(() => { localStorage.clear(); resetFlagOptionsCache(); });
afterEach(() => { vi.restoreAllMocks(); });

describe("formatDuration", () => {
  it("reads in seconds, minutes and hours", () => {
    expect(formatDuration(45_000)).toBe("45 s");
    expect(formatDuration(125_000)).toBe("2 min 5 s");
    expect(formatDuration(120_000)).toBe("2 min");
    expect(formatDuration(3_780_000)).toBe("1 h 3 min");
  });
});

describe("FlagSheet", () => {
  it("a range flag shows severity word, span, duration, peak, band and a range bar", () => {
    show(<FlagSheet item={{ flag: RANGE }} onClose={vi.fn()} />, replay());
    expect(screen.getByText("Warning")).toBeInTheDocument();
    expect(screen.getByText("⚠")).toBeInTheDocument();
    expect(screen.getByText("Coolant 112 °C (normal 80–105)")).toBeInTheDocument();
    expect(screen.getByText("1:00–2:05")).toBeInTheDocument();
    expect(screen.getByText(/1 min 5 s/)).toBeInTheDocument();
    expect(screen.getByText("112 °C")).toBeInTheDocument();
    expect(screen.getByText("1:30")).toBeInTheDocument();
    expect(screen.getByText("Normal 80–105 °C")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Coolant temp: 112 °C, normal 80–105/ })).toBeInTheDocument();
  });

  it("Jump to drops follow, seeks and closes", () => {
    const r = replay();
    const onClose = vi.fn();
    show(<FlagSheet item={{ flag: RANGE }} onClose={onClose} />, r);
    fireEvent.click(screen.getByRole("button", { name: "Jump to" }));
    expect(r.setFollow).toHaveBeenCalledWith(false);
    expect(r.seek).toHaveBeenCalledWith(60_000);
    expect(onClose).toHaveBeenCalled();
  });

  it("Keep as note adds an auto-tagged note and toasts", async () => {
    const r = replay();
    const onClose = vi.fn();
    const { ctx } = show(<FlagSheet item={{ flag: RANGE }} onClose={onClose} />, r);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Keep as note" })); });
    expect(r.addNote).toHaveBeenCalledWith({ t: 60_000, t_end: 125_000, text: RANGE.label, tags: ["auto", "range"] });
    await waitFor(() => expect(ctx.toast).toHaveBeenCalledWith("Kept as a note"));
    expect(onClose).toHaveBeenCalled();
  });

  it("Keep as note is hidden on a demo log and in public mode", () => {
    const { unmount } = show(<FlagSheet item={{ flag: RANGE }} onClose={vi.fn()} />, replay({ session: { ...META, synthetic: true } }));
    expect(screen.queryByRole("button", { name: "Keep as note" })).toBeNull();
    unmount();
    show(<FlagSheet item={{ flag: RANGE }} onClose={vi.fn()} />, replay(), { snap: { status: "connected", signals: {}, faults: [], public: true } });
    expect(screen.queryByRole("button", { name: "Keep as note" })).toBeNull();
    expect(screen.getByRole("button", { name: "Jump to" })).toBeInTheDocument();
  });

  it("Mute this sensor saves the muted signal", () => {
    const onClose = vi.fn();
    const { ctx } = show(<FlagSheet item={{ flag: RANGE }} onClose={onClose} />, replay());
    fireEvent.click(screen.getByRole("button", { name: "Mute this sensor" }));
    expect(loadFlagOptions().muted).toEqual(["coolant"]);
    expect(JSON.parse(localStorage.getItem("d2diag.flagOptions") ?? "{}").muted).toEqual(["coolant"]);
    expect(ctx.toast).toHaveBeenCalledWith(expect.stringMatching(/Muted Coolant temp/));
    expect(onClose).toHaveBeenCalled();
  });

  it("a fault flag lists each fault with Current/Logged and an alarm word", () => {
    show(<FlagSheet item={{ flag: FAULT }} onClose={vi.fn()} />, replay());
    expect(screen.getByText("Alarm")).toBeInTheDocument();
    expect(screen.getByText("⛔", { selector: ".flagsheet-title .si" })).toBeInTheDocument();
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("P0380 Glow plug circuit");
    expect(items[0]).toHaveTextContent("Current");
    expect(items[1]).toHaveTextContent("P0110 Air temp sensor");
    expect(items[1]).toHaveTextContent("Logged");
    expect(screen.queryByRole("button", { name: "Mute this sensor" })).toBeNull();
  });

  it("a folded flag says how many were folded", () => {
    show(<FlagSheet item={{ flag: { ...RANGE, label: "8 more out of range", folded: 8 } }} onClose={vi.fn()} />, replay());
    expect(screen.getByText("8 more flags folded to avoid a flood.")).toBeInTheDocument();
  });

  it("Flag settings swaps to the recording options", () => {
    const onClose = vi.fn();
    show(<FlagSheet item={{ flag: RANGE }} onClose={onClose} />, replay());
    fireEvent.click(screen.getByRole("button", { name: "Flag settings" }));
    expect(screen.getByRole("dialog", { name: "Recording options" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("a note shows its text, tags, span and Jump to", () => {
    const r = replay();
    const note: Note = { id: "n1", t: 30_000, t_end: 45_000, text: "Clunk", tags: ["noise"], kind: "note", source: "retro", created: "" };
    show(<FlagSheet item={{ note }} onClose={vi.fn()} />, r);
    expect(screen.getByText("Clunk")).toBeInTheDocument();
    expect(screen.getByText("noise")).toBeInTheDocument();
    expect(screen.getByText("0:30–0:45")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Keep as note" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Jump to" }));
    expect(r.seek).toHaveBeenCalledWith(30_000);
  });
});
