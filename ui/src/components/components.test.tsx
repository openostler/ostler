import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { CatalogAction } from "../api/schemas";
import { initialLive } from "../state/live";
import { installFakeServer } from "../test/fakeServer";
import { renderWithApp } from "../test/renderWithApp";
import { ActionButton } from "./ActionButton";
import { ConnectionNotice } from "./ConnectionNotice";
import { ConnectionSheet } from "./ConnectionSheet";
import { confirmReady } from "./confirm";
import { CoverageBar } from "./CoverageBar";
import { PlaceholderReadout } from "./PlaceholderReadout";
import { Readout } from "./Readout";
import { StatusTag } from "./StatusTag";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("StatusTag", () => {
  it("shows an icon and a word per status, never colour alone", () => {
    render(<><StatusTag status="verified" /><StatusTag status="candidate" /><StatusTag status="sniff" /><StatusTag status="untranscribed" /></>);
    for (const w of ["Verified", "Candidate", "Sniff target", "Not transcribed"]) expect(screen.getByText(w)).toBeInTheDocument();
    expect(document.querySelectorAll(".stag .si")).toHaveLength(4);
  });
});

describe("CoverageBar", () => {
  it("draws the four parts with a legend", () => {
    render(<CoverageBar coverage={{ verified: 2, candidate: 1, sniff: 1, untranscribed: 0, total: 4 }} />);
    expect(screen.getByRole("img", { name: /2 verified, 1 candidate, 1 sniff, 0 not transcribed of 4/ })).toBeInTheDocument();
    expect(screen.getByText("2/4 verified")).toBeInTheDocument();
    expect(screen.getByText("Not transcribed · 0")).toBeInTheDocument();
    const parts = [...document.querySelectorAll(".cbar > span")].map((s) => [s.className, (s as HTMLElement).style.width]);
    expect(parts).toEqual([["verified", "50%"], ["candidate", "25%"], ["sniff", "25%"]]);
  });
});

describe("PlaceholderReadout", () => {
  it("says why there is no value, and never shows one", () => {
    const base = { id: "p", name: "Pressures", safety: "read", ref: "", note: "", placeholder: true, actions: [] };
    render(<><PlaceholderReadout item={{ ...base, status: "untranscribed", pages: 4 }} />
      <PlaceholderReadout item={{ ...base, id: "q", name: "Gear", status: "sniff", placeholder: false }} /></>);
    expect(screen.getByText("not transcribed (4 pages)")).toBeInTheDocument();
    expect(screen.getByText("sniff target")).toBeInTheDocument();
    expect(document.querySelector(".cv-num")).toBeNull();
  });
});

describe("stale Readout", () => {
  const sig = { v: 800, u: "rpm", s: "ok", c: "proven" };
  it("is live while fresh", () => {
    renderWithApp(<Readout name="rpm" sig={sig} />, { live: { ...initialLive, seen: { rpm: Date.now() } } });
    expect(screen.getByText("800")).toBeInTheDocument();
    expect(screen.queryByText(/last seen/)).not.toBeInTheDocument();
    expect(document.querySelector(".srow")).not.toHaveClass("stale");
  });
  it("greys a value not updated for more than 5 s", () => {
    renderWithApp(<Readout name="rpm" sig={sig} />, { live: { ...initialLive, seen: { rpm: Date.now() - 8000 } } });
    expect(screen.getByText("last seen 8 s ago")).toBeInTheDocument();
    expect(document.querySelector(".srow")).toHaveClass("stale");
  });
  it("is stale whenever the SSE link is down", () => {
    renderWithApp(<Readout name="rpm" sig={sig} />, { linkUp: false, live: { ...initialLive, seen: { rpm: Date.now() - 1000 } } });
    expect(screen.getByText("last seen 1 s ago")).toBeInTheDocument();
  });
  it("never shows a value it has not seen arrive live", () => {
    renderWithApp(<Readout name="rpm" sig={sig} />);
    expect(screen.getByText("not live")).toBeInTheDocument();
  });
});

describe("ActionButton confirm levels", () => {
  const act = (over: Partial<CatalogAction>): CatalogAction => ({
    action: "compressor", label: "Compressor", status: "verified", safety: "actuator", confirm: "none",
    preconditions: [], ref: "", ...over,
  });

  it("pure rule", () => {
    expect(confirmReady("none", { ticked: [], typed: "", name: "X" })).toBe(true);
    expect(confirmReady("preconditions", { ticked: [true, false], typed: "", name: "X" })).toBe(false);
    expect(confirmReady("preconditions", { ticked: [true, true], typed: "", name: "X" })).toBe(true);
    expect(confirmReady("typed", { ticked: [], typed: "Key prog", name: "Key programming" })).toBe(false);
    expect(confirmReady("typed", { ticked: [], typed: "Key programming", name: "Key programming" })).toBe(true);
  });

  it("none → runs on tap", async () => {
    const server = installFakeServer();
    renderWithApp(<ActionButton action={act({})} itemName="Compressor test" />);
    await userEvent.click(screen.getByRole("button", { name: "Compressor" }));
    await waitFor(() => expect(server.commandsSent()).toEqual(["compressor"]));
  });

  it("preconditions → every condition ticked first", async () => {
    const user = userEvent.setup();
    const server = installFakeServer();
    renderWithApp(<ActionButton action={act({ confirm: "preconditions", preconditions: ["Ignition on", "Engine off"] })} itemName="Compressor test" />);
    await user.click(screen.getByRole("button", { name: "Compressor" }));
    const run = screen.getByRole("button", { name: "Compressor" });
    expect(run).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: "Ignition on" }));
    expect(run).toBeDisabled();
    await user.click(screen.getByRole("checkbox", { name: "Engine off" }));
    await user.click(run);
    await waitFor(() => expect(server.commandsSent()).toEqual(["compressor"]));
  });

  it("typed → the item name typed exactly", async () => {
    const user = userEvent.setup();
    const server = installFakeServer();
    renderWithApp(<ActionButton action={act({ confirm: "typed", safety: "service" })} itemName="Bleed" />, { experimental: true });
    await user.click(screen.getByRole("button", { name: "Compressor" }));
    const run = screen.getByRole("button", { name: "Compressor" });
    await user.type(screen.getByRole("textbox", { name: "Type Bleed to confirm" }), "Blee");
    expect(run).toBeDisabled();
    await user.type(screen.getByRole("textbox"), "d");
    await user.click(run);
    await waitFor(() => expect(server.commandBodies()).toEqual([{ action: "compressor", params: { trust: "experimental" } }]));
  });

  it("gated or planned → a lock and no button", () => {
    renderWithApp(<>
      <ActionButton action={act({ safety: "gated", status: "planned", confirm: "typed" })} itemName="Keys" />
      <ActionButton action={act({ action: "x", status: "planned" })} itemName="X" />
    </>, { experimental: true });
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("Gated")).toBeInTheDocument();
    expect(screen.getByText("Planned")).toBeInTheDocument();
  });

  it("experimental actions exist only in Experimental mode", () => {
    const { unmount } = renderWithApp(<ActionButton action={act({ status: "experimental" })} itemName="X" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    unmount();
    renderWithApp(<ActionButton action={act({ status: "experimental" })} itemName="X" />, { experimental: true });
    expect(screen.getByRole("button", { name: "Compressor" })).toBeInTheDocument();
  });

  it("shows a refusal (400 {ok:false,error}) as a toast", async () => {
    installFakeServer({ commands: { compressor: { ok: false, error: "refused: experimental action needs Experimental mode" } } });
    const { ctx } = renderWithApp(<ActionButton action={act({})} itemName="X" />);
    await userEvent.click(screen.getByRole("button", { name: "Compressor" }));
    await waitFor(() => expect(ctx.toast).toHaveBeenCalledWith("refused: experimental action needs Experimental mode", true));
  });
});

describe("ConnectionNotice", () => {
  it("shows a strip with Open connection only while not live", async () => {
    const user = userEvent.setup();
    const { ctx, unmount } = renderWithApp(<ConnectionNotice />, { snap: { status: "connected", conn: "lost", signals: {}, faults: [] } });
    expect(screen.getByText("No connection")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Open connection" }));
    expect(ctx.openConnection).toHaveBeenCalled();
    unmount();
    renderWithApp(<ConnectionNotice />, { snap: { status: "connecting", conn: "connecting", signals: {}, faults: [] } });
    expect(screen.queryByText("No connection")).not.toBeInTheDocument();
  });
});

describe("ConnectionSheet", () => {
  it("says how long the link has been down", () => {
    renderWithApp(<ConnectionSheet onClose={vi.fn()} downSince={Date.now() - 80_000} />,
      { snap: { status: "error", conn: "error", signals: {}, faults: [] } });
    expect(screen.getByText("No connection for 1 m 20 s")).toBeInTheDocument();
  });
});
