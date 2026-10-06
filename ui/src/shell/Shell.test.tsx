// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../App";
import { baseSnapshot, consented, installFakeServer } from "../test/fakeServer";
import { setViewport } from "../test/setup";
import { Boundary } from "./Boundary";

const connected = { ...baseSnapshot, faults: [], battery_v: 12.64 };
const destinations = () => screen.findByRole("navigation", { name: "Destinations" });

beforeEach(() => {
  consented();
  vi.spyOn(window, "confirm").mockReturnValue(true);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("the shell on a head unit (HU-7, 1024×600)", () => {
  beforeEach(() => setViewport(1024, 600));

  it("draws the rail with a Drive-mode button, and the full strip", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const nav = await destinations();
    expect(nav).toHaveClass("rail");
    expect(within(nav).getAllByRole("button").map((b) => b.textContent)).toEqual(["Home", "Diagnose", "Logs", "More", "Drive"]);
    expect(document.querySelector(".app")).toHaveAttribute("data-layout", "hu7");
    expect(document.querySelector(".app")).toHaveAttribute("data-side", "left"); // no driver_side in the pack yet
    const strip = screen.getByRole("banner", { name: "Status" });
    expect(await within(strip).findByText("Car battery 12.6 V")).toBeInTheDocument();
    expect(within(strip).getByText(/^Time /)).toBeInTheDocument();
  });

  it("opens Drive mode full screen (strip kept, nav hidden) and goes back", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Drive" }));
    const mode = screen.getByRole("region", { name: "Drive mode" });
    expect(within(mode).getByRole("heading", { name: "Drive" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Destinations" })).not.toBeInTheDocument();
    expect(screen.getByRole("banner", { name: "Status" })).toBeInTheDocument();
    await user.click(within(mode).getByRole("button", { name: "Back" }));
    expect(await destinations()).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Drive mode" })).not.toBeInTheDocument();
  });

  it("opens Drive mode from Home's large Drive button too", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const home = await screen.findByRole("heading", { name: "Home" });
    await user.click(within(home.closest(".home") as HTMLElement).getByRole("button", { name: "Drive" }));
    expect(screen.getByRole("region", { name: "Drive mode" })).toBeInTheDocument();
  });

  it("puts the rail on the side the kiosk flag names", async () => {
    window.history.replaceState(null, "", "/?display=headunit&side=right");
    setViewport(800, 480); // a head-unit browser reporting an odd size
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await destinations();
    expect(document.querySelector(".app")).toHaveAttribute("data-side", "right");
    expect(document.querySelector(".app")).toHaveAttribute("data-layout", "hu7");
  });

  it("keeps the compact system switcher on HU-7 (no room for the list pane)", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Diagnose" }));
    expect(await screen.findByRole("combobox", { name: "Module" })).toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Systems" })).not.toBeInTheDocument();
  });
});

describe("the shell on HU-9/10 (1280×720)", () => {
  beforeEach(() => setViewport(1280, 720));

  it("lists the systems beside the detail; selecting one moves the ECU session (module select into Diagnose)", async () => {
    const user = userEvent.setup();
    consented({ trust: "experimental" });
    const server = installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Diagnose" }));
    const list = await screen.findByRole("navigation", { name: "Systems" });
    await waitFor(() => expect(within(list).getByRole("button", { name: /BCU \(body control\)/ })).toBeInTheDocument());
    expect(within(list).getByRole("button", { name: /TD5 \(engine\)/ })).toHaveAttribute("aria-current", "true");
    expect(screen.queryByRole("combobox", { name: "Module" })).not.toBeInTheDocument();
    await user.click(within(list).getByRole("button", { name: /BCU/ }));
    await waitFor(() => expect(server.commandBodies()).toContainEqual({ action: "select_module", params: { module: "bcu" } }));
  });

  it("reopens Diagnose on the area last shown", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const nav = await destinations();
    await user.click(within(nav).getByRole("button", { name: "Diagnose" }));
    await user.click(within(await screen.findByRole("navigation", { name: "Areas" })).getByRole("button", { name: "Settings" }));
    await user.click(within(nav).getByRole("button", { name: "Logs" }));
    await user.click(within(nav).getByRole("button", { name: "Diagnose" }));
    expect(within(await screen.findByRole("navigation", { name: "Areas" })).getByRole("button", { name: "Settings" }))
      .toHaveAttribute("aria-current", "page");
  });
});

describe("the shell on HU-wide (1920×720)", () => {
  beforeEach(() => setViewport(1920, 720));

  it("keeps the vehicle pane on beside every destination", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const pane = await screen.findByRole("complementary", { name: "Vehicle pane" });
    expect(within(pane).getByRole("region", { name: /^Vehicle:/ })).toBeInTheDocument();
    await user.click(within(await destinations()).getByRole("button", { name: "Logs" }));
    expect(screen.getByRole("complementary", { name: "Vehicle pane" })).toBeInTheDocument();
  });
});

describe("error boundary per destination (app-model spec §5)", () => {
  it("shows App stopped in place of a crashed view and retries on demand", async () => {
    const user = userEvent.setup();
    let crash = true;
    const Crashy = () => {
      if (crash) throw new Error("boom");
      return <p>fine</p>;
    };
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    render(<Boundary name="Diagnose"><Crashy /></Boundary>);
    expect(screen.getByRole("alert")).toHaveTextContent("App stopped");
    expect(screen.getByRole("alert")).toHaveTextContent("Diagnose: boom");
    crash = false;
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(screen.getByText("fine")).toBeInTheDocument();
  });
});
