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
    expect(document.querySelector(".app")).toHaveAttribute("data-side", "right"); // the pack's driver_side (the D2 is RHD)
    const strip = screen.getByRole("banner", { name: "Status" });
    expect(await within(strip).findByText("Car battery 12.6 V")).toBeInTheDocument();
    expect(within(strip).getByText(/^Time /)).toBeInTheDocument();
  });

  it("opens Drive mode full screen (strip kept with Back, nav hidden, no heading) and goes back", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Drive" }));
    const mode = screen.getByRole("region", { name: "Drive mode" });
    expect(within(mode).queryByRole("heading")).not.toBeInTheDocument(); // §12.3: no page chrome
    expect(within(mode).queryByRole("button", { name: /^Vehicle status/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("navigation", { name: "Destinations" })).not.toBeInTheDocument();
    const strip = screen.getByRole("banner", { name: "Status" });
    await user.click(within(strip).getByRole("button", { name: "Back" }));
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

  it("puts the rail on the side the kiosk flag names, over the pack's driver_side", async () => {
    window.history.replaceState(null, "", "/?display=headunit&side=left");
    setViewport(800, 480); // a head-unit browser reporting an odd size
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await destinations();
    expect(document.querySelector(".app")).toHaveAttribute("data-side", "left");
    expect(document.querySelector(".app")).toHaveAttribute("data-layout", "hu5");
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

/** ShellInput (shell input spec, I1) without a mouse: Drive mode's intents and the Drive menu
 * (§6, §14.2), layers closed newest first (§4.3) and the confirm rules (§7). Spatial movement
 * needs layout boxes, so it is covered by e2e/input.spec.ts. */
describe("ShellInput on a head unit (HU-7)", () => {
  beforeEach(() => setViewport(1024, 600));
  const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

  it("Drive mode: back finds the switcher and returns to the face; ok opens the Drive menu", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Drive" }));
    const chip = document.querySelector<HTMLElement>('[data-chip="drive_mode"]')!;
    // the driving state is unknown before U2, which counts as Moving on a head unit
    await user.keyboard("{Escape}");
    expect(chip).toHaveFocus();
    await user.keyboard("{Escape}");
    expect(document.querySelector("main")).toHaveFocus();
    expect(screen.getByRole("region", { name: "Drive mode" })).toBeInTheDocument(); // never leaves while Moving
    await user.keyboard("{Enter}");
    const menu = screen.getByRole("dialog");
    const rows = within(menu).getAllByRole("button");
    expect(rows.map((b) => b.textContent)).toEqual(["Drive modeDashboard", "Exit to Home", "Back to Drive"]);
    expect(rows[0]).toHaveFocus();
    // an ok in the menu's first 500 ms is ignored (§5)
    await user.keyboard("{Enter}");
    expect(screen.getByRole("dialog")).toBe(menu);
    await wait(550);
    await user.keyboard("{Enter}"); // Drive mode: opens the mode list in its place
    expect(within(screen.getByRole("dialog")).getByRole("list", { name: "Drive modes" })).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Drive mode" })).toBeInTheDocument();
  });

  it("a long back (600 ms) opens the Drive menu in Drive mode", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Drive" }));
    await user.keyboard("{Escape>}");
    await wait(650);
    await user.keyboard("{/Escape}");
    expect(within(screen.getByRole("dialog")).getByRole("list", { name: "Drive menu" })).toBeInTheDocument();
    // the release did not also act: focus is in the menu, not on the switcher
    expect(document.querySelector('[data-chip="drive_mode"]')).not.toHaveFocus();
  });

  it("a confirm sheet opens with Cancel focused, ignores ok for 500 ms, and back closes only it", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: { ...connected, faults: ["inlet air temp. circuit (Current)"] } });
    render(<App path="/" />);
    await user.click(within(await destinations()).getByRole("button", { name: "Diagnose" }));
    const clear = await screen.findByRole("button", { name: /Clear codes/ });
    clear.focus();
    await user.keyboard("{Enter}");
    const sheet = screen.getByRole("dialog");
    expect(within(sheet).getByRole("button", { name: "Cancel" })).toHaveFocus();
    expect(sheet.textContent).not.toMatch(/\d+ s\b/); // no countdown
    await user.keyboard("{Enter}"); // within 500 ms: ignored, so a double press cannot even cancel
    expect(screen.getByRole("dialog")).toBe(sheet);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(clear).toHaveFocus(); // focus returns to where it was
  });

  it("back from the page focuses the rail item of the destination, then goes Home", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const nav = await destinations();
    await user.click(within(nav).getByRole("button", { name: "More" }));
    const row = (await screen.findAllByRole("button", { name: /Preferences/ }))[0]!;
    row.focus();
    await user.keyboard("{Escape}");
    expect(within(nav).getByRole("button", { name: "More" })).toHaveFocus();
    await user.keyboard("{Escape}");
    await waitFor(() => expect(within(nav).getByRole("button", { name: "Home" })).toHaveAttribute("aria-current", "page"));
    await waitFor(() => expect(within(nav).getByRole("button", { name: "Home" })).toHaveFocus());
  });
});
