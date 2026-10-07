// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { fireEvent, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../api/schemas";
import { resetFlagOptionsCache, saveFlagOptions, DEFAULT_FLAG_OPTIONS, type Flag } from "../lib/flags";
import { PlaybackCtx, usePlaybackState } from "../state/playback";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { activeFlag, GlobalTransport } from "./GlobalTransport";

const flagState = vi.hoisted(() => ({ visible: [] as Flag[] }));
vi.mock("../state/flags", () => ({
  useSessionFlags: () => ({ all: flagState.visible, visible: flagState.visible, counts: { range: 0, faults: 0 } }),
}));
vi.mock("./RecordingOptions", () => ({ RecordingOptions: () => <div>Recording options</div> }));

const T = Array.from({ length: 601 }, (_, i) => i * 1000); // 0 … 10 min
const META = {
  id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 600, rows: 601, parts: [], modules: ["td5"],
  channels: [], has_gps: false, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
  synthetic: false, recording: false, source: "mock", audio: [],
} as unknown as NonNullable<Replay["session"]>;
const NOTE: Note = { id: "n1", t: 10_000, t_end: null, text: "Clunk", tags: [], kind: "mark", source: "live", created: "" };
const WARN: Flag = {
  id: "range:coolant:60000", kind: "range", severity: "warn", t: 60_000, t_end: 120_000, label: "Coolant 112 °C (normal 80–105)",
  signal: "coolant", unit: "°C", peak: 112, peakT: 90_000, band: [80, 105], limits: [-40, 120],
};
const ALARM: Flag = { id: "fault:P0380:200000", kind: "fault", severity: "alarm", t: 200_000, t_end: null, label: "P0380 Glow plug", faults: ["P0380 Glow plug (Current)"], current: true };

function Harness({ over }: { over: Partial<Replay> }) {
  const pb = usePlaybackState(T);
  const r = {
    ...INACTIVE, active: true, id: "s1", session: META, data: { t: T } as unknown as Replay["data"], notes: [NOTE],
    t: 0, offset: null, playback: pb, follow: false, setFollow: vi.fn(), seek: vi.fn(),
    ...over,
  } as Replay;
  return (
    <ReplayCtx.Provider value={r}>
      <PlaybackCtx.Provider value={pb}><GlobalTransport /></PlaybackCtx.Provider>
    </ReplayCtx.Provider>
  );
}
const show = (over: Partial<Replay> = {}) => renderWithApp(<Harness over={over} />);

beforeEach(() => {
  localStorage.clear();
  resetFlagOptionsCache();
  flagState.visible = [WARN, ALARM];
});

describe("activeFlag", () => {
  it("is on inside a range flag and for a few seconds after a point flag", () => {
    expect(activeFlag([WARN, ALARM], 59_000)).toBeNull();
    expect(activeFlag([WARN, ALARM], 90_000)).toBe(WARN);
    expect(activeFlag([WARN, ALARM], 202_000)).toBe(ALARM);
    expect(activeFlag([WARN, ALARM], 230_000)).toBeNull();
  });
});

describe("GlobalTransport flags", () => {
  it("draws note ticks (accent) and flag ticks (warn bar, alarm point)", () => {
    show();
    const ticks = screen.getByRole("group", { name: "Notes and flags" });
    expect(within(ticks).getByRole("button", { name: /^Note at 0:10: Clunk/ })).toHaveClass("tone-note");
    const warn = within(ticks).getByRole("button", { name: /^Warning at 1:00: Coolant/ });
    expect(warn).toHaveClass("tone-warn", "range");
    expect(within(ticks).getByRole("button", { name: /^Alarm at 3:20: P0380/ })).toHaveClass("tone-alarm");
  });

  it("hides manual note ticks when the flag manager switches them off", () => {
    saveFlagOptions({ ...DEFAULT_FLAG_OPTIONS, manual: false });
    show({ t: 10_000 });
    expect(screen.queryByRole("button", { name: /^Note at/ })).toBeNull();
    expect(screen.queryByText(/Clunk/)).toBeNull();
    expect(screen.getByRole("button", { name: /^Warning at/ })).toBeInTheDocument();
  });

  it("the chip shows the note at the cursor as a button that opens the sheet", () => {
    show({ t: 11_000 });
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Clunk");
    expect(status.querySelector('[data-icon="flag"]')).not.toBeNull();
    fireEvent.click(within(status).getByRole("button"));
    expect(screen.getByRole("dialog")).toHaveTextContent("Clunk");
    expect(screen.getByRole("button", { name: "Jump to" })).toBeInTheDocument();
  });

  it("the chip shows a warn flag with ⚠ and opens the flag sheet", () => {
    show({ t: 90_000 });
    const chip = within(screen.getByRole("status")).getByRole("button", { name: "Warning: Coolant 112 °C (normal 80–105)" });
    expect(chip).toHaveTextContent("Coolant 112 °C");
    expect(chip.querySelector('[data-icon="warning"]')).not.toBeNull();
    expect(chip).toHaveClass("gnote-warn");
    fireEvent.click(chip);
    expect(screen.getByRole("button", { name: "Mute this sensor" })).toBeInTheDocument();
  });

  it("the chip shows an alarm flag with ⛔", () => {
    show({ t: 201_000 });
    const chip = within(screen.getByRole("status")).getByRole("button", { name: "Alarm: P0380 Glow plug" });
    expect(chip).toHaveTextContent("P0380 Glow plug");
    expect(chip.querySelector('[data-icon="error"]')).not.toBeNull();
  });

  it("no chip between notes and flags", () => {
    show({ t: 40_000 });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("● Latest shows only while the session is recording and re-pins follow", () => {
    const { unmount } = renderWithApp(<Harness over={{}} />);
    expect(screen.queryByRole("button", { name: "Follow the latest sample" })).toBeNull();
    unmount();
    const setFollow = vi.fn();
    renderWithApp(<Harness over={{ session: { ...META, recording: true }, follow: false, setFollow }} />);
    const latest = screen.getByRole("button", { name: "Follow the latest sample" });
    expect(latest).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(latest);
    expect(setFollow).toHaveBeenCalledWith(true);
  });

  it("● Latest reads pressed while following", () => {
    show({ session: { ...META, recording: true }, follow: true });
    expect(screen.getByRole("button", { name: "Follow the latest sample" })).toHaveAttribute("aria-pressed", "true");
  });
});
