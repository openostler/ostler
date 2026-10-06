// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { SniffBadge } from "./components/SniffBadge";
import { mergeReadings } from "./lib/mapping";
import { SCREENS } from "./screens/registry";
import { baseSnapshot, consented, installFakeServer, type Call } from "./test/fakeServer";

const connected = { ...baseSnapshot, faults: [] };

/** Add the replay-notes routes (GET /captures, POST /notes/live) on top of the fake server. */
function withLabelRoutes(server: { calls: Call[] }, captures: unknown[] = [], liveNote: unknown = { ok: true }) {
  const inner = globalThis.fetch;
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    if (url.pathname === "/captures") {
      server.calls.push({ path: url.pathname + url.search, method: "GET" });
      return json({ captures });
    }
    if (url.pathname === "/notes/live") {
      server.calls.push({ path: url.pathname, method: "POST", body: JSON.parse(String(init?.body)) });
      return liveNote instanceof Error ? Promise.reject(liveNote) : json(liveNote);
    }
    return inner(input, init);
  }));
  return server;
}

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
    expect(screen.queryByRole("button", { name: "Decode" })).not.toBeInTheDocument();
    unmount();
    render(<App path="/admin" />);
    for (const tab of ["Decode", "Label", "Docs"]) expect(await screen.findByRole("button", { name: tab })).toBeInTheDocument();
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

  it("shows the derived catalog status on the Map, not the legacy ok/maybe/todo", async () => {
    installFakeServer({ snapshot: connected });
    render(<App path="/admin" />);
    // /map says "maybe"; /catalog derives verified from the signal store
    const row = (await screen.findByText("12. Air Flow (kg/hr)")).closest(".ro") as HTMLElement;
    expect(await within(row).findByText("Verified")).toBeInTheDocument();
    expect(row).toHaveClass("edge-green");
  });

  it("captures a directly read LID with a label", async () => {
    const user = userEvent.setup();
    const server = withLabelRoutes(installFakeServer({ snapshot: connected, commands: { read_block: { ok: true, raws: { "23": "2710" } } } }));
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Label" }));
    await user.type(screen.getByRole("textbox", { name: "LID to read" }), "23");
    await user.click(screen.getByRole("button", { name: "Read" }));
    expect(await screen.findByText("27 10")).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Label for the reading" }), "ambient 1.0 bar");
    await user.click(screen.getByRole("button", { name: "Save capture" }));
    await waitFor(() => expect(server.calls.find((c) => c.path === "/capture")?.body)
      .toEqual({ module: "td5", lid: "23", raw: "27 10", text: "ambient 1.0 bar" }));
    // ...and as a live session note of kind "capture"
    await waitFor(() => expect(server.calls.find((c) => c.path === "/notes/live")?.body).toEqual({
      kind: "capture", text: "23: ambient 1.0 bar",
      capture: { module: "td5", lid: "23", raw: "27 10", value: "ambient 1.0 bar" },
    }));
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

  it("names the admin tabs Decode and Label, keeping the public tabs", () => {
    const admin = SCREENS.filter((x) => x.admin).map((x) => [x.id, x.label]);
    expect(admin).toEqual([["map", "Decode"], ["capture", "Label"], ["docs", "Docs"]]);
    expect(SCREENS.filter((x) => !x.admin).map((x) => x.label))
      .toEqual(["Drive", "Faults", "Inputs", "Outputs", "Settings", "Utilities", "Logs", "Analysis"]);
  });

  it("explains Decode with three steps and a glossary", async () => {
    const user = userEvent.setup();
    withLabelRoutes(installFakeServer({ snapshot: connected }));
    render(<App path="/admin" />);
    expect(await screen.findByRole("heading", { name: "Decode" })).toBeInTheDocument();
    expect(screen.getByText(/match our values to the NanoCom/)).toBeInTheDocument();
    const steps = within(screen.getByRole("list", { name: "How it works" })).getAllByRole("listitem");
    expect(steps).toHaveLength(3);
    expect(steps[0]).toHaveTextContent(/ESP32/);
    expect(steps[0]).toHaveTextContent(/demo feed/);
    const btn = screen.getByRole("button", { name: "Glossary" });
    expect(btn).toHaveAttribute("aria-expanded", "false");
    await user.click(btn);
    const pop = screen.getByRole("region", { name: "Glossary terms" });
    for (const term of ["LID", "21 xx", "Reference tool", "Sniff tap", "Decode / solve"]) {
      expect(within(pop).getByText(term)).toBeInTheDocument();
    }
    expect(within(pop).getByText(/ReadDataByLocalIdentifier/)).toBeInTheDocument();
    expect(within(pop).getByText(/^The NanoCom/)).toBeInTheDocument();
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("region", { name: "Glossary terms" })).not.toBeInTheDocument();
  });

  it("explains Label with three steps and the direct read", async () => {
    const user = userEvent.setup();
    withLabelRoutes(installFakeServer({ snapshot: connected }),
      [{ module: "td5", lid: "09", raw: "02 FA", value: "762 rpm", t: null, session: null }]);
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Label" }));
    expect(await screen.findByRole("heading", { name: "Label" })).toBeInTheDocument();
    expect(screen.getByText(/teach the decoder what bytes mean/)).toBeInTheDocument();
    const steps = within(screen.getByRole("list", { name: "How it works" })).getAllByRole("listitem");
    expect(steps.map((li) => li.textContent)).toEqual([
      expect.stringMatching(/21 xx asks the module for data block xx/),
      expect.stringMatching(/press the brake, open a door/),
      expect.stringMatching(/Read again and say what changed/),
    ]);
    expect(screen.getByText(/No NanoCom needed/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Glossary" })).toBeInTheDocument();
    // the server labels list, normalised to the one record shape
    const list = await screen.findByLabelText("Server labels");
    expect(list).toHaveTextContent("21 09 02 fa → 762 rpm");
    expect(screen.getByText(/kept in this browser only/)).toBeInTheDocument();
  });

  it("still saves the capture when the live note fails", async () => {
    const user = userEvent.setup();
    const server = withLabelRoutes(installFakeServer({ snapshot: connected, commands: { read_block: { ok: true, raws: { "2B": "0A0B" } } } }),
      [], new Error("offline"));
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Label" }));
    await user.type(screen.getByRole("textbox", { name: "LID to read" }), "0x2B");
    await user.click(screen.getByRole("button", { name: "Read" }));
    expect(await screen.findByText("0a 0b")).toBeInTheDocument();
    await user.type(screen.getByRole("textbox", { name: "Label for the reading" }), "door open");
    await user.click(screen.getByRole("button", { name: "Save capture" }));
    await waitFor(() => expect(server.calls.find((c) => c.path === "/capture")?.body)
      .toEqual({ module: "td5", lid: "2b", raw: "0a 0b", text: "door open" }));
    expect(server.calls.some((c) => c.path === "/notes/live")).toBe(true);
    expect(await screen.findByText(/door open/)).toBeInTheDocument();
  });

  it("feeds the Label tab's server labels into the Decode solver", async () => {
    const user = userEvent.setup();
    const server = withLabelRoutes(installFakeServer({ snapshot: connected }), [
      { module: "td5", lid: "09", raw: "03 20", value: "800", t: null, session: null },
      { module: "td5", lid: "09", raw: "02 FA", value: "762", t: null, session: null }, // same bytes as the local reading
      { module: "td5", lid: "1a", raw: "00", value: "other block", t: null, session: null },
    ]);
    render(<App path="/admin" />);
    expect(await screen.findByText(/3 labels from Label tab feed the solver/)).toBeInTheDocument();
    const row = (await screen.findByText("1. Engine Speed (rpm)")).closest(".ro") as HTMLElement;
    await user.type(within(row).getByRole("textbox"), "762");
    await user.click(within(row).getByRole("button", { name: "save" }));
    await waitFor(() => expect(server.calls.filter((c) => c.path === "/automap").at(-1)?.body).toMatchObject({
      samples: [{ text: "762", raws: { "09": "02 fa" } }, { text: "800", raws: { "09": "03 20" } }],
      candidate_lids: ["09"],
    }));
    expect(within(row).getByText("+ 1 label from Label tab")).toBeInTheDocument();
    expect(server.calls.some((c) => c.path === "/captures?module=td5")).toBe(true);
  });

  it("links the Utilities raw dump to the Label tab", async () => {
    consented({ trust: "experimental" });
    const user = userEvent.setup();
    withLabelRoutes(installFakeServer({ snapshot: connected }));
    render(<App path="/admin" />);
    await user.click(await screen.findByRole("button", { name: "Utilities" }));
    await user.click(await screen.findByRole("button", { name: /Advanced/ }));
    await user.click(screen.getByRole("button", { name: "Label these bytes →" }));
    expect(await screen.findByRole("heading", { name: "Label" })).toBeInTheDocument();
  });
});

describe("Decode helpers", () => {
  it("merges server labels for the item's LIDs, deduped by lid + raw", () => {
    const local = [{ text: "762", raws: { "09": "02 fa" } }];
    const out = mergeReadings(local, [
      { lid: "09", raw: "02FA", value: "dup" },
      { lid: "0x09", raw: "03 20", value: "800" },
      { lid: "09", raw: "03 20", value: "800 again" },
      { lid: "10", raw: "00", value: "other" },
      { lid: "09", raw: "04 00", value: "  " },
    ], ["09"]);
    expect(out).toEqual({ readings: [...local, { text: "800", raws: { "09": "03 20" } }], fromLabels: 1 });
  });

  it("the badge suggests the demo feed when no tap is connected", () => {
    render(<SniffBadge sniff={{ data: { module: null, modules: [], lids: [] }, active: new Set(), fps: 0, configured: false, demo: false, error: null }} />);
    expect(screen.getByRole("status")).toHaveTextContent("No tap connected — the homelab runs a demo feed");
  });
});
