// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import metaFx from "../api/fixtures/session-meta.json";
import { SessionMeta, type Note, type Snapshot } from "../api/schemas";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { MarkButton } from "./MarkButton";

/* ⚑ in each state (spec §8): live recording, paused, idle, replay (editable / demo / public). */

type Call = { path: string; method: string; body?: unknown };
const NOTE: Note = { id: "n9", t: 42_000, t_end: null, text: "", tags: [], kind: "note", source: "retro", created: "2026-10-05T09:01:01.000Z" };

function stubServer(reply: (c: Call) => unknown = () => ({ ok: true })) {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const c: Call = { path: url.pathname + url.search, method: init?.method ?? "GET" };
    if (typeof init?.body === "string") c.body = JSON.parse(init.body);
    calls.push(c);
    return new Response(JSON.stringify(reply(c)), { headers: { "Content-Type": "application/json" } });
  }));
  return calls;
}

const meta = SessionMeta.parse({ ...metaFx, synthetic: false });
const snap = (over: Partial<Snapshot> = {}): Snapshot => ({ status: "connected", signals: {}, faults: [], ...over });
const recording = (state?: string) => snap({ recording: { session: "S1", since: 0, rows: 10, ...(state ? { state } : {}) } as Snapshot["recording"] });

function inReplay(over: Partial<Replay> = {}, s: Snapshot = snap()) {
  const replay: Replay = {
    ...INACTIVE, active: true, id: meta.id, session: meta, notes: [], t: 42_000.4,
    addNote: vi.fn(async () => NOTE), refreshNotes: vi.fn(), ...over,
  };
  return { replay, ...renderWithApp(<ReplayCtx.Provider value={replay}><MarkButton /></ReplayCtx.Provider>, { snap: s }) };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("MarkButton states", () => {
  it("live recording: an enabled ⚑ Mark this moment", () => {
    stubServer();
    renderWithApp(<MarkButton />, { snap: recording() });
    expect(screen.getByRole("button", { name: "Mark this moment" })).toBeEnabled();
  });

  it("paused: greyed, titled 'Connect to the car to mark'", () => {
    stubServer();
    renderWithApp(<MarkButton />, { snap: recording("paused") });
    const btn = screen.getByRole("button", { name: "Connect to the car to mark" });
    expect(btn).toBeDisabled();
    expect(btn).toHaveAttribute("title", "Connect to the car to mark");
  });

  it("not recording and not replaying: nothing", () => {
    stubServer();
    renderWithApp(<MarkButton />);
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("replay of a demo log: hidden", () => {
    stubServer();
    inReplay({ session: { ...meta, synthetic: true } });
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("replay in public mode: hidden", () => {
    stubServer();
    inReplay({}, snap({ public: true }));
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("replay: ⚑ adds a retro mark at the cursor, then 'What happened?' PATCHes it", async () => {
    const calls = stubServer(() => ({ ok: true, note: { ...NOTE, text: "clunk" } }));
    const { replay, ctx } = inReplay({}, recording());
    fireEvent.click(screen.getByRole("button", { name: "Mark at the cursor" }));
    await screen.findByText("What happened?");
    expect(replay.addNote).toHaveBeenCalledWith({ t: 42_000 });
    expect(ctx.toast).toHaveBeenCalledWith("⚑ Marked");
    expect(screen.getByText("Marked at 0:42")).toBeInTheDocument();
    expect(calls.some((c) => c.path === "/notes/live")).toBe(false); // never a live mark in replay
    fireEvent.change(screen.getByRole("textbox", { name: "What happened?" }), { target: { value: "clunk" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByText("What happened?")).toBeNull());
    expect(calls).toContainEqual({ path: `/sessions/${meta.id}/notes/n9`, method: "PATCH", body: { text: "clunk", tags: [] } });
    expect(replay.refreshNotes).toHaveBeenCalled();
    expect(ctx.toast).toHaveBeenCalledWith("Note saved");
  });

  it("replay: when the mark could not be saved, Save stores the note at the same time", async () => {
    stubServer();
    const addNote = vi.fn(async () => null as Note | null);
    const { ctx } = inReplay({ addNote });
    fireEvent.click(screen.getByRole("button", { name: "Mark at the cursor" }));
    await screen.findByText(/Not saved yet/);
    expect(ctx.toast).toHaveBeenCalledWith(expect.stringMatching(/^Could not save the mark/), true);
    addNote.mockResolvedValueOnce(NOTE);
    fireEvent.change(screen.getByRole("textbox", { name: "What happened?" }), { target: { value: "hiss" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(addNote).toHaveBeenLastCalledWith({ t: 42_000, text: "hiss", tags: [] }));
    await waitFor(() => expect(screen.queryByText("What happened?")).toBeNull());
  });
});
