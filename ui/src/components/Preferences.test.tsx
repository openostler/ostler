import { fireEvent, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { renderWithApp } from "../test/renderWithApp";
import { Preferences } from "./Preferences";

vi.mock("../state/flags", () => ({
  useSessionFlags: () => ({ all: [], visible: [], counts: { range: 0, faults: 0 } }),
}));

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { headers: { "Content-Type": "application/json" } })));
});
afterEach(() => vi.unstubAllGlobals());

describe("Preferences — Recording & flags", () => {
  it("opens the recording options and flag manager without a recording, and comes back", () => {
    renderWithApp(<Preferences onClose={vi.fn()} />, { snap: { status: "connected", signals: {}, faults: [], recording: null } });
    fireEvent.click(screen.getByRole("button", { name: "Recording & flags" }));
    expect(screen.getByText("Recording & flags")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Flags" })).toBeInTheDocument();
    expect(screen.queryByText("Preferences")).toBeNull(); // one sheet at a time
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByText("Preferences")).toBeInTheDocument();
  });
});

describe("Preferences — Version", () => {
  it("shows the platform and pack versions with links to their commits", async () => {
    const body = {
      platform: { name: "Ostler", version: "0.0.1", commit: "b9dd0f4df891d73250238b2d07cbc0428ca83180",
        source: "https://github.com/openostler/ostler" },
      pack: { id: "lr_d2", name: "Land Rover Discovery 2", version: "0.1.0", commit: "db2afd97114448", source: null },
      built: "2026-10-05T22:10:00Z", started: "2026-10-05T22:11:00Z",
    };
    vi.stubGlobal("fetch", vi.fn(async (url: string) => new Response(
      JSON.stringify(String(url).endsWith("/version") ? body : {}), { headers: { "Content-Type": "application/json" } })));
    renderWithApp(<Preferences onClose={vi.fn()} />, { snap: { status: "connected", signals: {}, faults: [], recording: null } });
    const link = await screen.findByRole("link", { name: "b9dd0f4" });
    expect(link).toHaveAttribute("href", "https://github.com/openostler/ostler/commit/b9dd0f4df891d73250238b2d07cbc0428ca83180");
    expect(screen.getByText("Land Rover Discovery 2")).toBeInTheDocument();
    expect(screen.getByText("db2afd9")).toBeInTheDocument(); // no source URL → plain text
    expect(screen.getByText("Built")).toBeInTheDocument();
  });
});
