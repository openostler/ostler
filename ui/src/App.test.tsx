import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { baseSnapshot, consented, installFakeServer, pushSnapshot } from "./test/fakeServer";

const connected = { ...baseSnapshot, faults: [] };
const cov = (verified: number, candidate = 0, sniff = 0, untranscribed = 0) =>
  ({ verified, candidate, sniff, untranscribed, total: verified + candidate + sniff + untranscribed });
const slabsCatalog = {
  module: "slabs", store_module: "slabs", coverage: cov(1),
  pages: [{ id: "outputs", title: "Outputs", coverage: cov(1), groups: [{ id: "out-air", title: "Air suspension", items: [{
    id: "compressor", name: "Compressor test", status: "verified", safety: "actuator", ref: "31 30 28",
    actions: [{ action: "compressor", label: "Compressor", status: "verified", safety: "actuator", confirm: "preconditions",
      preconditions: ["Vehicle stationary"], ref: "31 30 28" }],
  }] }] }],
};

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
    const coolant = (await screen.findAllByText("Coolant")).map((el) => el.closest(".srow")).find(Boolean) as HTMLElement;
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

  it("hides candidate outputs in Stable mode", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Outputs" }));
    expect(await screen.findByText(/Nothing verified here yet — switch to Experimental/)).toBeInTheDocument();
    expect(screen.queryByText("Fuel pump")).not.toBeInTheDocument();
    expect(server.commandsSent()).toEqual([]);
  });

  it("runs a verified SLABS actuator after its precondition checklist", async () => {
    const user = userEvent.setup();
    const slabs = { ...connected, module: "slabs", source: "mock-slabs", signals: {} };
    const server = installFakeServer({ snapshot: slabs, catalogs: { slabs: slabsCatalog } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Outputs" }));
    const card = (await screen.findByText("Compressor test")).closest(".card") as HTMLElement;
    await user.click(within(card).getByRole("button", { name: "Compressor" }));
    const run = within(card).getByRole("button", { name: "Compressor" });
    expect(run).toBeDisabled();
    await user.click(within(card).getByRole("checkbox", { name: "Vehicle stationary" }));
    await user.click(run);
    await waitFor(() => expect(server.commandBodies()).toEqual([{ action: "compressor" }])); // Stable: no trust param
  });

  it("sends trust=experimental with module actions in Experimental mode", async () => {
    consented({ trust: "experimental" });
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    expect(await screen.findByText(/Experimental mode/)).toBeInTheDocument();
    await user.click(await screen.findByRole("button", { name: "Outputs" }));
    const card = (await screen.findByText("4. Fuel Pump (pulse)", { selector: ".item-name" })).closest(".card") as HTMLElement;
    expect(within(card).getByText("Candidate")).toBeInTheDocument(); // status chip shown in Experimental
    await user.click(within(card).getByRole("button", { name: "Fuel pump" }));
    for (const c of within(card).getAllByRole("checkbox")) await user.click(c);
    await user.click(within(card).getByRole("button", { name: "Fuel pump" }));
    await waitFor(() => expect(server.commandBodies()).toEqual([{ action: "output_fuel_pump", params: { trust: "experimental" } }]));
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

  it("switches temperature units in Preferences", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await screen.findByText("Connected");
    await user.click(screen.getByRole("button", { name: "Preferences" }));
    await user.click(screen.getByRole("button", { name: "°F" }));
    await user.click(screen.getByRole("button", { name: "Done" }));
    expect(JSON.parse(localStorage.getItem("d2diag.v2")!).units.temp).toBe("F");
    expect(screen.getAllByText("°F").length).toBeGreaterThan(0);
  });

  it("reads a raw LID block under Utilities → Advanced, in Experimental only", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected, commands: { read_block: { ok: true, raws: { "09": "02fa" } } } });
    const { unmount } = render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Utilities" }));
    expect(await screen.findByText(/Nothing verified here yet/)).toBeInTheDocument();
    expect(screen.queryByText("Advanced")).not.toBeInTheDocument();
    unmount();
    consented({ trust: "experimental" });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Utilities" }));
    await user.click(await screen.findByRole("button", { name: /Advanced/ }));
    await user.click(screen.getByRole("button", { name: "Read" }));
    expect(await screen.findByText("02 fa")).toBeInTheDocument();
  });
});

describe("calm instrument", () => {
  beforeEach(() => consented());

  it("leads Drive with a one-line health summary that links to the cause", async () => {
    const user = userEvent.setup();
    const faults = ["027: shuttle valve switch — electrical failure (Logged)"];
    installFakeServer({ snapshot: { ...connected, faults, signals: { battery: { v: 14.1, u: "V", s: "ok", c: "proven" } } } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Dismiss" }));
    const strip = await screen.findByRole("button", { name: /Vehicle status: 1 logged fault/ });
    await user.click(strip);
    expect(await screen.findByRole("heading", { name: "Faults" })).toBeInTheDocument();
  });

  it("shows each value against its normal band, and colour only when out of range", async () => {
    installFakeServer({ snapshot: { ...connected, signals: {
      battery: { v: 14.1, u: "V", s: "ok", c: "proven" },
      air_temp: { v: 95, u: "°C", s: "high", c: "proven" },
    } } });
    render(<App path="/" />);
    expect(await screen.findByRole("img", { name: /Battery: 14.1 V, normal 12.4–14.8/ })).toBeInTheDocument();
    const intake = (await screen.findByText("Intake air")).closest(".tile") as HTMLElement;
    expect(intake).toHaveClass("alarm");
    expect(within(intake).getByText("HIGH")).toBeInTheDocument(); // word + icon, never colour alone
    const battery = screen.getByText("Battery").closest(".tile") as HTMLElement;
    expect(battery).not.toHaveClass("alarm");
    expect(within(battery).queryByText("OK")).not.toBeInTheDocument(); // healthy = nothing to see
  });

  it("filters Inputs to what needs attention", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: { ...connected, signals: {
      battery: { v: 14.1, u: "V", s: "ok", c: "proven" },
      air_temp: { v: 95, u: "°C", s: "high", c: "proven" },
    } } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Inputs" }));
    await user.click(await screen.findByRole("button", { name: /Attention · 1/ }));
    const rows = () => [...document.querySelectorAll(".srow")].map((r) => r.getAttribute("data-signal"));
    expect(rows()).toEqual(["air_temp"]);
  });

  it("follows the phone's day/night setting by default", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await screen.findByText("Connected");
    expect(document.documentElement.hasAttribute("data-theme")).toBe(false);
  });
});

describe("overhaul navigation", () => {
  beforeEach(() => consented());

  it("has the seven tabs (Logs last) and no Connect or Capabilities tab", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const nav = await screen.findByRole("navigation", { name: "Screens" });
    expect(within(nav).getAllByRole("button").map((b) => b.getAttribute("aria-label")))
      .toEqual(["Drive", "Faults", "Inputs", "Outputs", "Settings", "Utilities", "Logs"]);
    expect(screen.queryByRole("button", { name: "Connect" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Capabilities" })).not.toBeInTheDocument();
  });

  it("switches module from the header and keeps the current tab", async () => {
    const user = userEvent.setup();
    consented({ trust: "experimental" });
    const server = installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Inputs" }));
    const select = screen.getByRole("combobox", { name: "Module" });
    await waitFor(() => expect(within(select).getByRole("option", { name: "BCU (body control)" })).toBeInTheDocument());
    await user.selectOptions(select, "bcu");
    await waitFor(() => expect(server.commandBodies()).toContainEqual({ action: "select_module", params: { module: "bcu" } }));
    expect(screen.getByRole("heading", { name: "Inputs" })).toBeInTheDocument();
  });

  it("has no title; the module control and, in Experimental only, the % mapped pill", async () => {
    installFakeServer({ snapshot: connected });
    const { unmount } = render(<App path="/" />);
    const header = document.querySelector("header") as HTMLElement;
    expect(await within(header).findByRole("combobox", { name: "Module" })).toBeInTheDocument();
    await waitFor(() => expect(header.querySelector(".modctl-v")).toHaveTextContent("TD5 (engine)"));
    expect(within(header).getByText("Module")).toBeInTheDocument();
    expect(within(header).queryByText(/D2 Diag/)).not.toBeInTheDocument();
    expect(header.querySelector(".mappct")).toBeNull();
    expect(within(header).queryByText("admin")).not.toBeInTheDocument();
    unmount();
    consented({ trust: "experimental" });
    render(<App path="/" />);
    const header2 = document.querySelector("header") as HTMLElement;
    await waitFor(() => expect(header2.querySelector(".mappct")).toHaveTextContent("34% mapped")); // motor: 34 of 99 verified
  });

  it("shows a small admin chip instead of a title on /admin", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/admin" />);
    const header = document.querySelector("header") as HTMLElement;
    expect(await within(header).findByText("admin")).toHaveClass("hadmin");
  });

  it("shows a non-blocking connection notice on Settings and Utilities", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: { ...connected, status: "error", conn: "error", error: "no answer" } });
    render(<App path="/" />);
    for (const tab of ["Settings", "Utilities"]) {
      await user.click(await screen.findByRole("button", { name: tab }));
      expect(await screen.findByRole("heading", { name: tab })).toBeInTheDocument();
      const notice = document.querySelector(".connnotice") as HTMLElement;
      expect(notice).toHaveTextContent("No connection");
      expect(within(notice).getByRole("button", { name: "Open connection" })).toBeInTheDocument();
    }
    await user.click(screen.getByRole("button", { name: "Open connection" }));
    expect(within(await screen.findByRole("dialog")).getByText("Connection")).toBeInTheDocument();
  });

  it("shows no connection notice while connected", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    await screen.findByRole("heading", { name: "Settings" });
    expect(document.querySelector(".connnotice")).toBeNull();
  });

  it("lists only modules with something verified in Stable", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/" />);
    const select = await screen.findByRole("combobox", { name: "Module" });
    await waitFor(() => expect(within(select).getByRole("option", { name: "TD5 (engine)" })).toBeInTheDocument());
    expect(within(select).queryByRole("option", { name: /Body control/ })).not.toBeInTheDocument();
  });

  it("shows the car battery and opens the connection sheet from the pill", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: { ...connected, conn: "connected", battery_v: 12.64,
      port: { spec: "auto", resolved: "/dev/ttyUSB0", candidates: ["/dev/ttyUSB0", "/dev/ttyUSB1"] } } });
    render(<App path="/" />);
    expect(await screen.findByLabelText("Car battery 12.6 V")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Connected" }));
    const sheet = await screen.findByRole("dialog");
    expect(within(sheet).getByText("Connection")).toBeInTheDocument();
    await user.click(within(sheet).getByRole("radio", { name: "/dev/ttyUSB1" }));
    await user.click(within(sheet).getByRole("button", { name: "Disconnect" }));
    await waitFor(() => expect(server.commandBodies()).toEqual([
      { action: "set_port", params: { port: "/dev/ttyUSB1" } }, { action: "disconnect" },
    ]));
  });

  it("shows a latched test with Stop on every screen", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: { ...connected,
      active_test: { action: "bleed_power_on", label: "Power bleed", since: 0, stop: "bleed_power_off" } } });
    render(<App path="/" />);
    const banner = await screen.findByRole("alert");
    expect(banner).toHaveTextContent("Power bleed is running");
    await user.click(within(banner).getByRole("button", { name: "Stop" }));
    await waitFor(() => expect(server.commandsSent()).toEqual(["bleed_power_off"]));
  });

  it("Stable hides status chips, coverage bars and placeholders; Experimental shows them", async () => {
    const user = userEvent.setup();
    const bcu = { ...connected, module: "bcu", signals: {} };
    installFakeServer({ snapshot: bcu });
    const { unmount } = render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect(await screen.findByText(/Nothing verified here yet/)).toBeInTheDocument();
    expect(document.querySelector(".stag, .placeholder, [data-testid=coverage-bar]")).toBeNull();
    expect(screen.queryByText(/Experimental mode/)).not.toBeInTheDocument();
    unmount();
    consented({ trust: "experimental" });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    expect((await screen.findAllByText("sniff target")).length).toBeGreaterThan(0);
    expect(screen.getByTestId("coverage-bar")).toBeInTheDocument();
  });

  it("reads the ECU identity on Settings and shows only the masked VIN", async () => {
    const user = userEvent.setup();
    const identityCatalog = {
      module: "motor", store_module: "td5", coverage: cov(1),
      pages: [{ id: "settings", title: "Settings", coverage: cov(1), groups: [{ id: "settings-identity", title: "Identity", items: [{
        id: "identity", name: "ECU identity", status: "verified", safety: "read",
        actions: [{ action: "read_identity", label: "Read", status: "verified", safety: "read", confirm: "none" }],
      }] }] }],
    };
    installFakeServer({ snapshot: connected, catalogs: { motor: identityCatalog }, commands: {
      read_identity: { ok: true, identity: { part_no: "NNN500250", vin: "SALLTGM88XA123456", vin_masked: "SALLT********3456" } },
    } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Settings" }));
    await user.click(await screen.findByRole("button", { name: "Read" }));
    const region = await screen.findByRole("region", { name: "Identity" });
    expect(within(region).getByText("SALLT********3456")).toBeInTheDocument();
    expect(within(region).getByText("NNN500250")).toBeInTheDocument();
    expect(screen.queryByText("SALLTGM88XA123456")).not.toBeInTheDocument();
  });

  it("shows NanoCom fields not yet decoded on Inputs, in Experimental only", async () => {
    const user = userEvent.setup();
    consented({ trust: "experimental" });
    const inputsCatalog = {
      module: "motor", store_module: "td5", coverage: cov(0, 0, 1),
      pages: [{ id: "inputs", title: "Inputs", coverage: cov(0, 0, 1), groups: [{ id: "inputs-x", title: "Inputs — Switches", items: [{
        id: "brake-sw", name: "Brake switch", status: "sniff", safety: "read",
      }] }] }],
    };
    installFakeServer({ snapshot: connected, catalogs: { motor: inputsCatalog } });
    render(<App path="/" />);
    await user.click(await screen.findByRole("button", { name: "Inputs" }));
    const section = await screen.findByRole("region", { name: "From NanoCom — not yet decoded" });
    expect(within(section).getByText("Brake switch")).toBeInTheDocument();
    expect(within(section).getByText("sniff target")).toBeInTheDocument();
  });
});
