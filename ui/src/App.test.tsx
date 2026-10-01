import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { baseSnapshot, consented, installFakeServer, pushSnapshot } from "./test/fakeServer";

const connected = { ...baseSnapshot, faults: [] };

beforeEach(() => {
  vi.spyOn(window, "confirm").mockReturnValue(true);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("first start", () => {
  it("blocks on consent until data sharing is answered, then records it", async () => {
    const server = installFakeServer({ snapshot: connected });
    const user = userEvent.setup();
    render(<App path="/" />);
    const cont = screen.getByRole("button", { name: "Continue" });
    expect(cont).toBeDisabled();
    await user.click(screen.getByRole("radio", { name: /Don't share/ }));
    await user.click(cont);
    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
    await waitFor(() => expect(server.calls.some((c) => c.path === "/community/consent")).toBe(true));
    expect(JSON.parse(localStorage.getItem("d2diag.v2")!)).toMatchObject({ consentDone: true, share: false });
  });
});

describe("live dashboard", () => {
  beforeEach(() => consented());

  it("shows the connection pill and the Drive tiles from the stream", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    pushSnapshot(connected);
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("Battery")).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /bar/ })).toBeInTheDocument(); // boost gauge
  });

  it("shows a connecting gate until the module answers", async () => {
    installFakeServer({ snapshot: { ...connected, status: "connecting", connect_phase: "sending init (try 1/3)" } });
    render(<App path="/" />);
    expect(await screen.findByText(/Connecting to TD5/)).toBeInTheDocument();
    expect(screen.getAllByText("sending init (try 1/3)").length).toBeGreaterThan(0);
  });

  it("labels and groups Inputs from /fields metadata, not hard-coded tables", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Inputs" }));
    expect(await screen.findByText("Temperatures")).toBeInTheDocument();
    const coolant = (await screen.findAllByText("Coolant")).map((el) => el.closest(".ro")).find(Boolean) as HTMLElement;
    await user.click(within(coolant).getByRole("button", { name: "About Coolant" }));
    expect(within(coolant).getByText(/Normal 86–95/)).toBeInTheDocument();
  });

  it("pops faults once and stops nagging after dismiss", async () => {
    const user = userEvent.setup();
    const faults = ["027: shuttle valve switch — electrical failure (Current)"];
    installFakeServer({ snapshot: { ...connected, faults } });
    render(<App path="/" />);
    expect(await screen.findByText("⚠ 1 fault")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    pushSnapshot({ ...connected, faults });
    expect(screen.queryByText("⚠ 1 fault")).not.toBeInTheDocument();
  });

  it("clears faults only after confirmation", async () => {
    const user = userEvent.setup();
    const faults = ["inlet air temp. circuit (Current)"];
    const server = installFakeServer({ snapshot: { ...connected, faults } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Dismiss" }));
    await user.click(screen.getByRole("button", { name: "Faults" }));
    vi.mocked(window.confirm).mockReturnValueOnce(false);
    await user.click(screen.getByRole("button", { name: /Clear codes/ }));
    expect(server.commandsSent()).not.toContain("clear_faults");
    await user.click(screen.getByRole("button", { name: /Clear codes/ }));
    await waitFor(() => expect(server.commandsSent()).toContain("clear_faults"));
  });

  it("keeps experimental outputs locked in Trusted mode", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Outputs" }));
    expect((await screen.findAllByText("enable Experimental")).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Run" })).not.toBeInTheDocument();
    expect(server.commandsSent()).toEqual([]);
  });

  it("runs a verified SLABS actuator after confirmation", async () => {
    const user = userEvent.setup();
    const slabs = { ...connected, module: "slabs", source: "mock-slabs", signals: {} };
    const server = installFakeServer({ snapshot: slabs });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Outputs" }));
    const card = (await screen.findByText("Compressor test")).closest(".card") as HTMLElement;
    await user.click(within(card).getByRole("button", { name: "Run" }));
    expect(window.confirm).toHaveBeenCalled();
    await waitFor(() => expect(server.commandsSent()).toContain("compressor"));
  });

  it("starts CSV logging from Inputs", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: connected, commands: { start_csv: { ok: true, message: "recording", file: "livedata.csv" } } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Inputs" }));
    await user.click(await screen.findByRole("button", { name: /Log CSV/ }));
    await waitFor(() => expect(server.commandsSent()).toContain("start_csv"));
    expect(await screen.findByText(/recording · livedata.csv/)).toBeInTheDocument();
  });

  it("switches temperature units in Settings", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await screen.findByText("Connected");
    await user.click(screen.getByRole("button", { name: "Settings" }));
    await user.click(screen.getByRole("button", { name: "°F" }));
    await user.click(screen.getByRole("button", { name: "Done" }));
    expect(JSON.parse(localStorage.getItem("d2diag.v2")!).units.temp).toBe("F");
    expect(screen.getAllByText("°F").length).toBeGreaterThan(0);
  });

  it("reads a raw LID block in Utilities", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected, commands: { read_block: { ok: true, raws: { "09": "02fa" } } } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Utilities" }));
    await user.click(screen.getByRole("button", { name: "Read" }));
    expect(await screen.findByText("02 fa")).toBeInTheDocument();
  });
});
