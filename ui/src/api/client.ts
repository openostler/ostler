// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Typed access to the Python server. Every call validates the response with its Zod
 * schema and throws ApiError on transport or shape failure — callers show a toast. The
 * body is read whatever the HTTP status: every API error is the JSON envelope
 * {ok: false, error, code?}, so a refusal parses like any other reply.
 * Admin routes rely on the browser's Basic Auth session from /admin.
 */
import type { z } from "zod";
import {
  AutomapReply,
  Catalog,
  CatalogModules,
  CommandReply,
  Community,
  DocsResponse,
  FaultsResponse,
  FieldsResponse,
  MapResponse,
  OkReply,
  PackSchema,
  VersionInfo,
  CaptureList,
  NoteList,
  NoteReply,
  SessionData,
  SessionEvents,
  SessionHistogram,
  SessionList,
  SessionMetaReply,
  SessionMeta,
  Snapshot,
  SniffResponse,
} from "./schemas";

export class ApiError extends Error {}

async function parse<S extends z.ZodType>(res: Response, schema: S, path: string): Promise<z.infer<S>> {
  let body: unknown;
  try {
    body = await res.json();
  } catch {
    throw new ApiError(`${path}: HTTP ${res.status} (not JSON)`);
  }
  const out = schema.safeParse(body);
  if (!out.success) {
    console.warn(`${path}: unexpected response`, out.error.issues, body);
    throw new ApiError(`${path}: unexpected response from the server`);
  }
  return out.data;
}

async function request(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(path, init);
  } catch {
    throw new ApiError("network error");
  }
}

export async function getJson<S extends z.ZodType>(path: string, schema: S): Promise<z.infer<S>> {
  return parse(await request(path), schema, path);
}

export async function postJson<S extends z.ZodType>(
  path: string,
  body: unknown,
  schema: S,
): Promise<z.infer<S>> {
  const res = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parse(res, schema, path);
}

/**
 * POST /command. A refusal (400/403/409, 502 when the car refuses, 504 on a timeout …)
 * still carries the {ok:false, error, code} envelope — it is returned, not thrown.
 */
export function command(action: string, params?: Record<string, unknown>) {
  return postJson("/command", params ? { action, params } : { action }, CommandReply);
}

export const api = {
  snapshot: () => getJson("/snapshot", Snapshot),
  /** The active vehicle pack's manifest (module ids, names, aliases, layout). */
  pack: () => getJson("/pack", PackSchema),
  /** Platform and pack versions and commits (Settings → Version). */
  version: () => getJson("/version", VersionInfo),
  catalog: (module: string) => getJson(`/catalog?module=${encodeURIComponent(module)}`, Catalog),
  catalogModules: () => getJson("/catalog", CatalogModules),
  /** One page of sessions, newest first (keyset paging: pass `next` back as `before`). */
  sessions: (q: { limit?: number; before?: string | null; q?: string; from?: string; to?: string;
    module?: string; has_notes?: boolean; min_km?: number } = {}) => {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(q)) if (v !== undefined && v !== null && v !== "" && v !== false) p.set(k, v === true ? "1" : String(v));
    const qs = p.toString();
    return getJson(qs ? `/sessions?${qs}` : "/sessions", SessionList);
  },
  sessionHistogram: (group: "month" | "day" = "month", year?: number) =>
    getJson(`/sessions/histogram?group=${group}${year ? `&year=${year}` : ""}`, SessionHistogram),
  updateSession: async (id: string, patch: { name?: string | null; description?: string | null }) =>
    parse(await request(`/sessions/${encodeURIComponent(id)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch),
    }), SessionMetaReply, "/sessions"),
  session: (id: string) => getJson(`/sessions/${encodeURIComponent(id)}`, SessionMeta),
  sessionData: (id: string, channels: string[], max = 2000) =>
    getJson(`/sessions/${encodeURIComponent(id)}/data?ch=${encodeURIComponent(channels.join(","))}&max=${max}`, SessionData),
  sessionEvents: (id: string) => getJson(`/sessions/${encodeURIComponent(id)}/events`, SessionEvents),
  notes: (id: string) => getJson(`/sessions/${encodeURIComponent(id)}/notes`, NoteList),
  addNote: (id: string, note: { t: number; t_end?: number | null; text?: string; tags?: string[]; kind?: string }) =>
    postJson(`/sessions/${encodeURIComponent(id)}/notes`, note, NoteReply),
  editNote: async (id: string, nid: string, patch: Record<string, unknown>) =>
    parse(await request(`/sessions/${encodeURIComponent(id)}/notes/${encodeURIComponent(nid)}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch),
    }), NoteReply, "/notes"),
  deleteNote: async (id: string, nid: string) =>
    parse(await request(`/sessions/${encodeURIComponent(id)}/notes/${encodeURIComponent(nid)}`, { method: "DELETE" }),
      NoteReply, "/notes"),
  liveNote: (note: { text?: string; tags?: string[]; kind: "mark" | "note" | "capture"; capture?: Record<string, string> }) =>
    postJson("/notes/live", note, NoteReply),
  captures: (module?: string) =>
    getJson(module ? `/captures?module=${encodeURIComponent(module)}` : "/captures", CaptureList),
  /** Audio track URL (Range-capable; for an <audio> element). */
  sessionAudioUrl: (id: string, track: string) =>
    `/sessions/${encodeURIComponent(id)}/audio/${encodeURIComponent(track)}`,
  /** A download URL (the browser fetches it; not JSON). */
  sessionExportUrl: (id: string, fmt: "csv" | "vbo" | "gpx" | "geojson" | "pcapng") =>
    `/sessions/${encodeURIComponent(id)}/export?fmt=${fmt}`,
  fields: (module: string) => getJson(`/fields?module=${encodeURIComponent(module)}`, FieldsResponse),
  faults: (module: string) => getJson(`/faults?module=${encodeURIComponent(module)}`, FaultsResponse),
  map: (module: string) => getJson(`/map?module=${encodeURIComponent(module)}`, MapResponse),
  sniff: (module?: string) =>
    getJson(module ? `/sniff?module=${encodeURIComponent(module)}` : "/sniff", SniffResponse),
  docs: () => getJson("/docs", DocsResponse),
  /** A rendered markdown fragment (HTML string), served fresh from the repo. */
  doc: async (id: string): Promise<string> => {
    const res = await request(`/doc?id=${encodeURIComponent(id)}`);
    if (!res.ok) throw new ApiError(`document not found (${res.status})`);
    return res.text();
  },
  community: () => getJson("/community", Community),
  setConsent: (consent: boolean, vehicle?: Record<string, string>) =>
    postJson("/community/consent", vehicle ? { consent, vehicle } : { consent }, OkReply),
  contribute: (record: Record<string, unknown>) => postJson("/community/contribute", record, OkReply),
  capture: (rec: { module: string; lid: string; raw: string; text: string }) =>
    postJson("/capture", rec, OkReply),
  automap: (req: {
    samples: { text: string; raws: Record<string, string> }[];
    candidate_lids: string[];
    name: string;
    unit: string;
  }) => postJson("/automap", req, AutomapReply),
  upsertSignal: (module: string, record: Record<string, unknown>) =>
    postJson("/signal", { module, record }, OkReply),
};
