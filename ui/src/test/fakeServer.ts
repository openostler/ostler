// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act } from "@testing-library/react";
import { vi } from "vitest";
import catalogBcu from "../api/fixtures/catalog-bcu.json";
import catalogModulesFx from "../api/fixtures/catalog-modules.json";
import catalogTd5 from "../api/fixtures/catalog-td5.json";
import communityFx from "../api/fixtures/community.json";
import docsFx from "../api/fixtures/docs.json";
import fieldsTd5 from "../api/fixtures/fields-td5.json";
import fieldsSlabs from "../api/fixtures/fields-slabs.json";
import mapFx from "../api/fixtures/map.json";
import packFx from "../api/fixtures/pack.json";
import snapshotFx from "../api/fixtures/snapshot.json";
import sniffFx from "../api/fixtures/sniff.json";

/** A fake of the Python server for component tests: fetch is routed to the contract
 * fixtures (real server responses), EventSource is a stub the test pushes snapshots to. */
export type Call = { path: string; method: string; body?: unknown };

export class FakeEventSource {
  static last: FakeEventSource | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(public url: string) {
    FakeEventSource.last = this;
  }
  close() {}
}

export function pushSnapshot(snap: unknown) {
  act(() => {
    FakeEventSource.last?.onopen?.();
    FakeEventSource.last?.onmessage?.({ data: JSON.stringify(snap) });
  });
}

export const baseSnapshot = snapshotFx as Record<string, unknown>;

export function installFakeServer(opts: {
  snapshot?: unknown;
  commands?: Record<string, unknown>;
  docHtml?: string;
  automap?: unknown;
  /** /catalog?module=… replies by module id (default: the contract fixtures). */
  catalogs?: Record<string, unknown>;
  /** /catalog (no module) reply. */
  catalogModules?: unknown;
} = {}) {
  const calls: Call[] = [];
  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  const commands: Record<string, unknown> = { ...opts.commands };
  const catalogs: Record<string, unknown> = { td5: catalogTd5, bcu: catalogBcu, ...opts.catalogs };
  const emptyCatalog = (module: string) => ({
    module, store_module: module, coverage: { verified: 0, candidate: 0, sniff: 0, untranscribed: 0, total: 0 },
    pages: ["faults", "inputs", "outputs", "settings", "utilities"].map((id) => ({
      id, title: id, coverage: { verified: 0, candidate: 0, sniff: 0, untranscribed: 0, total: 0 }, groups: [],
    })),
  });

  vi.stubGlobal("EventSource", FakeEventSource);
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;
    calls.push({ path: url.pathname + url.search, method, body });
    switch (url.pathname) {
      case "/pack": return json(packFx);
      case "/snapshot": return json(opts.snapshot ?? snapshotFx);
      case "/fields": return json(url.searchParams.get("module") === "slabs" ? fieldsSlabs : fieldsTd5);
      case "/faults": return json({ module: url.searchParams.get("module"), faults: [] });
      case "/community": return json(communityFx);
      case "/community/consent": return json({ ok: true, consent: !!body?.consent });
      case "/map": return json(mapFx);
      case "/catalog": {
        const m = url.searchParams.get("module");
        if (!m) return json(opts.catalogModules ?? catalogModulesFx);
        return json(catalogs[m] ?? emptyCatalog(m));
      }
      case "/sniff": return json(sniffFx);
      case "/docs": return json(docsFx);
      case "/doc": return new Response(opts.docHtml ?? "<h1>Notes</h1><p>Body.</p>", { headers: { "Content-Type": "text/html" } });
      case "/capture": return json({ ok: true, stored: true });
      case "/signal": return json({ ok: true, module: body?.module, name: body?.record?.name });
      case "/automap": return json(opts.automap ?? { ok: false, error: "need more samples" });
      case "/command": {
        const reply = commands[body?.action] ?? { ok: true, message: `${body?.action} ok` };
        return json(reply, (reply as { ok: boolean }).ok ? 200 : 400);
      }
      default: return new Response("not found", { status: 404 });
    }
  }));
  const sent = () => calls.filter((c) => c.path === "/command").map((c) => c.body as { action: string; params?: Record<string, unknown> });
  return { calls, commandsSent: () => sent().map((b) => b.action), commandBodies: sent };
}

/** Skip the first-start consent screen. */
export function consented(extra: Record<string, unknown> = {}) {
  localStorage.setItem("d2diag.v2", JSON.stringify({ consentDone: true, share: false, ...extra }));
}
