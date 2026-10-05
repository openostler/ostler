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
