// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { fireEvent, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import metaFx from "../api/fixtures/session-meta.json";
import { SessionMeta, type Note } from "../api/schemas";
import { loadFlagOptions, resetFlagOptionsCache, saveFlagOptions, DEFAULT_FLAG_OPTIONS } from "../lib/flags";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { RecordingOptions } from "./RecordingOptions";

const flagsHook = vi.hoisted(() => vi.fn(() => ({ all: [], visible: [], counts: { range: 3, faults: 1 } })));
vi.mock("../state/flags", () => ({ useSessionFlags: flagsHook }));

/* The flag manager in Recording & flags (spec §8). */

const meta = SessionMeta.parse({ ...metaFx, synthetic: false });
const NOTES = [{ id: "a" }, { id: "b" }] as Note[];

function renderOptions(r: Replay = INACTIVE) {
  return renderWithApp(<ReplayCtx.Provider value={r}><RecordingOptions onClose={vi.fn()} /></ReplayCtx.Provider>);
}
const flags = () => screen.getByRole("region", { name: "Flags" });

beforeEach(() => {
  localStorage.clear();
  resetFlagOptionsCache();
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { headers: { "Content-Type": "application/json" } })));
});
afterEach(() => {
  vi.unstubAllGlobals();
  localStorage.clear();
  resetFlagOptionsCache();
});

describe("RecordingOptions — flags", () => {
  it("is titled Recording & flags and shows three switches, on by default, without counts outside replay", () => {
    renderOptions();
    expect(screen.getByText("Recording & flags")).toBeInTheDocument();
    for (const name of ["Manual ⚑", "Sensor out of range", "Faults"]) {
      expect(within(flags()).getByRole("switch", { name })).toHaveAttribute("aria-checked", "true");
    }
    expect(within(flags()).queryByText(/·/)).toBeNull();
    expect(within(flags()).getByText("None")).toBeInTheDocument(); // no muted sensors
  });

  it("shows the open session's counts", () => {
    renderOptions({ ...INACTIVE, active: true, id: meta.id, session: meta, notes: NOTES });
    expect(flagsHook).toHaveBeenCalledWith(undefined, meta.modules ?? []);
    const row = (name: string) => within(flags()).getByRole("switch", { name }).parentElement!;
    expect(row("Manual ⚑")).toHaveTextContent("Manual ⚑ · 2");
    expect(row("Sensor out of range")).toHaveTextContent("Sensor out of range · 3");
    expect(row("Faults")).toHaveTextContent("Faults · 1");
  });

  it("a switch saves at once, per device, without Apply", () => {
    renderOptions();
    fireEvent.click(within(flags()).getByRole("switch", { name: "Sensor out of range" }));
    expect(within(flags()).getByRole("switch", { name: "Sensor out of range" })).toHaveAttribute("aria-checked", "false");
    expect(JSON.parse(localStorage.getItem("d2diag.flagOptions")!)).toMatchObject({ range: false, manual: true, faults: true });
    expect(fetch).not.toHaveBeenCalledWith(expect.stringContaining("/command"), expect.anything());
  });

  it("lists muted sensors; ✕ unmutes", () => {
    saveFlagOptions({ ...DEFAULT_FLAG_OPTIONS, muted: ["coolant_temp", "fuel_temp"] });
    renderOptions();
    const list = within(flags()).getByRole("list", { name: "Muted sensors" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(2);
    fireEvent.click(within(list).getByRole("button", { name: "Unmute coolant_temp" }));
    expect(loadFlagOptions().muted).toEqual(["fuel_temp"]);
    expect(within(flags()).queryByRole("button", { name: "Unmute coolant_temp" })).toBeNull();
  });
});
