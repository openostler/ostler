import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { baseSnapshot, consented, installFakeServer } from "./test/fakeServer";

const connected = { ...baseSnapshot, faults: [] };

beforeEach(() => {
  consented();
  vi.spyOn(window, "confirm").mockReturnValue(true);
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("admin mode", () => {
  it("is only on /admin", async () => {
    installFakeServer({ snapshot: connected });
    const { unmount } = render(<App path="/" />);
    await screen.findByRole("button", { name: "Drive" });
    expect(screen.queryByRole("button", { name: "Map" })).not.toBeInTheDocument();
    unmount();
    render(<App path="/admin" />);
    for (const tab of ["Map", "Capture", "Docs"]) expect(await screen.findByRole("button", { name: tab })).toBeInTheDocument();
  });

  it("maps a field from a reference-tool reading and saves it to the store", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({
      snapshot: connected,
      automap: { ok: true, mode: "numeric", lid: "09", offset: 0, kind: "u16", scale: 1, bias: 0, r2: 1, clean: true, how: "fit", signal: 'Signal("rpm", 0x09, 0)' },
    });
    render(<App path="/admin" />);
    const row = (await screen.findByText("1. Engine Speed (rpm)")).closest(".ro") as HTMLElement;
    expect(within(row).getByText("762 rpm")).toBeInTheDocument(); // live decode from /sniff
    await user.type(within(row).getByRole("textbox"), "762");
    await user.click(within(row).getByRole("button", { name: "save" }));
    expect(await within(row).findByText(/21 09@0 u16/)).toBeInTheDocument();
    const automap = server.calls.find((c) => c.path === "/automap");
    expect(automap?.body).toMatchObject({ samples: [{ text: "762", raws: { "09": "02 fa" } }], candidate_lids: ["09"], name: "rpm" });
    await user.click(within(row).getByRole("button", { name: /save to store/ }));
    await waitFor(() => expect(server.calls.find((c) => c.path === "/signal")?.body)
      .toMatchObject({ module: "td5", record: { name: "rpm", lid: "09", kind: "u16", confidence: "candidate" } }));
    // the reading is kept under the legacy v1 key, so older readings still load
    const key = Object.keys(localStorage).find((k) => k.startsWith("read:td5|") && k.endsWith("|1. Engine Speed (rpm)"));
    expect(JSON.parse(localStorage.getItem(key!)!)).toEqual([{ text: "762", raws: { "09": "02 fa" } }]);
  });

  it("captures a directly read LID with a label", async () => {
    const user = userEvent.setup();
    const server = installFakeServer({ snapshot: connected, commands: { read_block: { ok: true, raws: { "23": "2710" } } } });
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Capture" }));
    await user.type(screen.getByRole("textbox", { name: "LID to read" }), "23");
    await user.click(screen.getByRole("button", { name: "Read" }));
    expect(await screen.findByText("27 10")).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Label for the reading" }), "ambient 1.0 bar");
    await user.click(screen.getByRole("button", { name: "Save capture" }));
    await waitFor(() => expect(server.calls.find((c) => c.path === "/capture")?.body)
      .toEqual({ module: "td5", lid: "23", raw: "27 10", text: "ambient 1.0 bar" }));
    expect(await screen.findByText(/ambient 1.0 bar/)).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("fangstlog:td5")!)[0]).toMatchObject({ lid: "23", text: "ambient 1.0 bar" });
  });

  it("lists and opens the repo docs", async () => {
    const user = userEvent.setup();
    installFakeServer({ snapshot: connected, docHtml: "<h1>Notes</h1><p>A <em>test</em> document.</p>" });
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Docs" }));
    await user.click(await screen.findByRole("button", { name: "Notes" }));
    expect(await screen.findByText("test")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "← Documents" }));
    expect(await screen.findByRole("button", { name: "Notes" })).toBeInTheDocument();
  });
});
