/**
 * Typed access to the Python server. Every call validates the response with its Zod
 * schema and throws ApiError on transport or shape failure — callers show a toast.
 * Admin routes rely on the browser's Basic Auth session from /admin.
 */
import type { z } from "zod";
import {
  AutomapReply,
  CommandReply,
  Community,
  DocsResponse,
  FieldsResponse,
  MapResponse,
  OkReply,
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

/** POST /command. A 400 still carries {ok:false, error} — it is returned, not thrown. */
export function command(action: string, params?: Record<string, unknown>) {
  return postJson("/command", params ? { action, params } : { action }, CommandReply);
}

export const api = {
  snapshot: () => getJson("/snapshot", Snapshot),
  fields: (module: string) => getJson(`/fields?module=${encodeURIComponent(module)}`, FieldsResponse),
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
