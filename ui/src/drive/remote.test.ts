// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { parseCaps, PRESETS, withStored } from "./presets";
import { displayId, usableModes } from "./remote";
import type { Layout } from "./types";
import { useDriveModes } from "./useDriveModes";

/** A user's copy of a preset, as the server stores it (a full copy with its base). */
function copyOf(id: string, name: string, newId = id): Layout {
  const p = PRESETS.find((m) => m.id === id)!;
  return { ...structuredClone(p), id: newId, name, base: { preset: id, version: 1 } };
}

type Call = { url: string; method: string; headers: Record<string, string>; body: unknown };

/** A fake server for /ui/drive-mode and /ui/layouts: `selection` is what GET answers. */
function fakeServer(opts: { selection?: Record<string, unknown> | null; delay?: number; fail?: boolean; putCode?: string } = {}) {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const method = init?.method ?? "GET";
    calls.push({ url: input, method, headers: (init?.headers ?? {}) as Record<string, string>,
      body: init?.body ? JSON.parse(init.body as string) : undefined });
    if (opts.fail) throw new TypeError("offline");
    if (opts.delay) await new Promise((r) => setTimeout(r, opts.delay));
    const parts = input.split("?")[0]!.split("/");
    if (method === "PUT" && opts.putCode) {
      return new Response(JSON.stringify({ ok: false, error: "Park to edit", code: opts.putCode }), { status: 409 });
    }
    const reply = { vid: "v1", profile: parts[4], display: parts[5], class: parts[6],
      selection: method === "PUT" ? JSON.parse(init!.body as string) : (opts.selection ?? null) };
    return new Response(JSON.stringify(method === "PUT" ? { ok: true, ...reply } : reply), { status: 200 });
  }));
  return calls;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("this display's id", () => {
  it("is ?display_id= when valid, else minted once and kept", () => {
    expect(displayId("?display_id=dash-left")).toBe("dash-left");
    const a = displayId("?display_id=Bad Id");
    expect(a).toMatch(/^d[0-9a-f]{12}$/);
    expect(displayId("")).toBe(a);
    localStorage.clear();
    expect(displayId("")).not.toBe(a);
  });
});

describe("stored modes (§8.3)", () => {
  it("keep valid Drive-mode documents for this class only", () => {
    const good = copyOf("ostler.dashboard", "Mine", "user.mine");
    const bad = { ...copyOf("ostler.dashboard", "Bad", "user.bad"), format: "nope" };
    const rail = { ...good, kind: "rail", id: "user.rail" };
    const entries = [good, bad, rail, null].map((layout) => ({ source: "car" as const, etag: '"x"', layout: layout as never }));
    expect(usableModes(entries, "hu7").map((m) => m.id)).toEqual(["user.mine"]);
  });

  it("replace a preset by id and follow the presets otherwise", () => {
    const mine = copyOf("ostler.map", "My map");
    const extra = copyOf("ostler.dashboard", "Extra", "user.extra");
    const merged = withStored([mine, extra]);
    expect(merged.find((m) => m.id === "ostler.map")!.name).toBe("My map");
    expect(merged.at(-1)!.id).toBe("user.extra");
    expect(merged.length).toBe(PRESETS.length + 1);
    expect(withStored([])).toBe(PRESETS);
  });

  it("show a stored copy of the active mode in place of the preset", () => {
    const caps = parseCaps("");
    const mine = copyOf("ostler.dashboard", "My dash");
    const { result } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps, stored: [mine] }));
    expect(result.current.active.id).toBe("ostler.dashboard");
    expect(result.current.active.name).toBe("My dash");
  });
});

describe("the selected mode on the server (§8.3)", () => {
  const caps = parseCaps("");
  const server = { display: "hu-test" };

  it("takes the server's selection over the first paint", async () => {
    localStorage.setItem("ostler.drive.v1", JSON.stringify({ "lr_d2/hu7": { mode: "ostler.map" } }));
    const calls = fakeServer({ selection: { mode: "ostler.offroad", faces: { "ostler.offroad": 1 } } });
    const { result } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps, server }));
    expect(result.current.active.id).toBe("ostler.map"); // first paint from localStorage
    await waitFor(() => expect(result.current.active.id).toBe("ostler.offroad"));
    expect(result.current.faces[result.current.face]!.face).toBe("trail");
    expect(calls[0]!.url).toBe("/ui/drive-mode/current/car/hu-test/hu7");
    // and keeps it as the offline fallback
    expect(JSON.parse(localStorage.getItem("ostler.drive.v1")!)["lr_d2/hu7"].mode).toBe("ostler.offroad");
  });

  it("sends every switch with this display's class", async () => {
    const calls = fakeServer();
    const { result } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps, server }));
    await waitFor(() => expect(calls.length).toBe(1));
    act(() => result.current.cycle());
    await waitFor(() => expect(calls.length).toBe(2));
    const put = calls[1]!;
    expect(put.method).toBe("PUT");
    expect(put.url).toBe("/ui/drive-mode/current/car/hu-test/hu7");
    expect(put.headers["Ostler-Layout-Class"]).toBe("hu7");
    expect(put.body).toEqual({ mode: "ostler.map" });
  });

  it("lets a switch made before the server answers win", async () => {
    fakeServer({ selection: { mode: "ostler.offroad" }, delay: 30 });
    const { result } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps, server }));
    act(() => result.current.pick("ostler.minimal"));
    await new Promise((r) => setTimeout(r, 60));
    expect(result.current.active.id).toBe("ostler.minimal");
  });

  it("keeps working offline from localStorage", async () => {
    localStorage.setItem("ostler.drive.v1", JSON.stringify({ "lr_d2/hu7": { mode: "ostler.diagnostic" } }));
    fakeServer({ fail: true });
    const { result } = renderHook(() => useDriveModes({ cls: "hu7", pack: "lr_d2", caps, server }));
    await new Promise((r) => setTimeout(r, 10));
    expect(result.current.active.id).toBe("ostler.diagnostic");
    act(() => result.current.cycle());
    expect(result.current.active.id).toBe("ostler.minimal");
  });

  it("resends without the rotation when a reorder is refused (Park to edit)", async () => {
    const calls = fakeServer({ putCode: "park_to_edit" });
    const { result } = renderHook(() => useDriveModes({ cls: "phone", pack: "lr_d2", caps, server }));
    await waitFor(() => expect(calls.length).toBe(1));
    act(() => result.current.pick("ostler.offroad")); // joins the rotation (§5.9)
    await waitFor(() => expect(calls.length).toBe(3));
    expect((calls[1]!.body as { rotation?: string[] }).rotation).toContain("ostler.offroad");
    expect(calls[2]!.body).toEqual({ mode: "ostler.offroad" });
  });
});
