// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { RewindButton } from "./RewindButton";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const meta = (id: string, recording: boolean) => ({
  id, start_utc: "2026-10-05T09:00:00Z", end_utc: null, duration_s: 60, rows: 61, has_gps: false, distance_km: 0,
  max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null, synthetic: false, recording, source: "mock",
});

/** /sessions answers with `sessions` (or `status` for an error); returns the paths fetched. */
function sessionsServer(sessions: unknown[], status = 200) {
  const paths: string[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string) => {
    const url = new URL(input, "http://x");
    paths.push(url.pathname + url.search);
    return new Response(JSON.stringify(status === 200 ? { sessions, next: null } : { error: "boom" }),
      { status, headers: { "Content-Type": "application/json" } });
  }));
  return paths;
}

const replay = (over: Partial<Replay> = {}): Replay => ({ ...INACTIVE, enter: vi.fn(), ...over });

function renderRewind(r: Replay, recording: string | null = null) {
  return renderWithApp(<ReplayCtx.Provider value={r}><RewindButton /></ReplayCtx.Provider>, {
    snap: { status: "connected", ts_utc: "2026-10-05T09:00:00.000Z", signals: {}, faults: [], recording: recording ? { session: recording, since_utc: "1970-01-01T00:00:00.000Z", rows: 10 } : null },
  });
}

describe("RewindButton", () => {
  it("while recording: opens the drive in progress at its newest sample, following it, then Analysis", async () => {
    sessionsServer([meta("live", true)]);
    const r = replay();
    const { ctx } = renderRewind(r, "live");
    const btn = screen.getByRole("button", { name: "Rewind" });
    expect(btn).toHaveTextContent("⏪Rewind");
    expect(btn).toHaveAttribute("title", "Rewind to the latest sample");
    fireEvent.click(btn);
    expect(r.enter).toHaveBeenCalledWith("live", { at: "end", follow: true });
    expect(ctx.goTo).toHaveBeenCalledWith("analysis");
  });

  it("not recording: opens the newest finished session at its end, then Analysis", async () => {
    const paths = sessionsServer([meta("still-open", true), meta("s2", false), meta("s1", false)]);
    const r = replay();
    const { ctx } = renderRewind(r);
    const btn = screen.getByRole("button", { name: "Rewind" });
    expect(btn).toHaveAttribute("title", "Open the last drive at its end");
    fireEvent.click(btn);
    await waitFor(() => expect(r.enter).toHaveBeenCalledWith("s2", { at: "end" }));
    expect(ctx.goTo).toHaveBeenCalledWith("analysis");
    expect(paths).toContain("/sessions?limit=5");
  });

  it("is disabled with \"No logs yet\" when there are no sessions", async () => {
    sessionsServer([]);
    renderRewind(replay());
    const btn = screen.getByRole("button", { name: "Rewind" });
    await waitFor(() => expect(btn).toBeDisabled());
    expect(btn).toHaveAttribute("title", "No logs yet");
  });

  it("toasts when the logs cannot be loaded", async () => {
    sessionsServer([], 500);
    const r = replay();
    const { ctx } = renderRewind(r);
    fireEvent.click(screen.getByRole("button", { name: "Rewind" }));
    await waitFor(() => expect(ctx.toast).toHaveBeenCalledWith(expect.stringMatching(/^Could not load the logs/), true));
    expect(r.enter).not.toHaveBeenCalled();
    expect(ctx.goTo).not.toHaveBeenCalled();
  });

  it("is hidden during replay (Exit to live takes its place)", () => {
    sessionsServer([meta("s1", false)]);
    renderRewind(replay({ active: true, id: "s1" }), "live");
    expect(screen.queryByRole("button", { name: "Rewind" })).not.toBeInTheDocument();
  });
});
