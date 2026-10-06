// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { AutomapReply, MapItem } from "../api/schemas";

/** Signal name for a menu row without an explicit `sig`: "3. Road Speed (km/h)" → "road_speed". */
export function signalNameFor(item: MapItem): string {
  return item.sig || item.name.replace(/^\d+\.\s*/, "").replace(/\s*\([^)]*\)/g, "").trim()
    .replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "").toLowerCase();
}

/** Store record from an automap result (written via POST /signal as a candidate). */
export function recordFromSolve(r: AutomapReply, name: string): Record<string, unknown> {
  const rec: Record<string, unknown> = {
    name, lid: r.lid, offset: r.offset, unit: "", confidence: "candidate",
    source: "Map mapping (differential/plaintext)",
  };
  if (r.mode === "state" || r.mapping) {
    const states = Object.fromEntries(Object.entries(r.mapping ?? {}).map(([label, raw]) => [raw, label]));
    Object.assign(rec, r.bit != null ? { kind: "bit", bit: r.bit, states } : { kind: "u8", states });
  } else {
    Object.assign(rec, { kind: r.kind, scale: r.scale, bias: r.bias ?? 0 });
  }
  return rec;
}

/** One solver input: what the reference tool showed (`text`) and the raw bytes per LID. */
export type Reading = { text: string; raws: Record<string, string> };
/** A label saved on the Label tab (server copy from GET /captures). */
export type LabelCapture = { lid: string; raw: string; value: string };

/** LID as the store spells it: "0x2B" / " 2b " → "2b". */
export const normLid = (lid: string): string => lid.trim().replace(/^0x/i, "").toLowerCase();
/** Raw bytes as the store spells them: "02FA" / "02 fa" → "02 fa". */
export const normHex = (raw: string): string =>
  raw.replace(/\s+/g, "").toLowerCase().replace(/(..)/g, "$1 ").trim();

/** Solver input = this device's readings + the Label tab's server labels for the same
 * LIDs. Duplicates (same LID and raw bytes) are dropped; a local reading wins. Returns the
 * merged list and how many came from the server. */
export function mergeReadings(
  local: Reading[],
  captures: LabelCapture[],
  lids: string[],
): { readings: Reading[]; fromLabels: number } {
  const wanted = new Map(lids.filter(Boolean).map((l) => [normLid(l), l] as const)); // key as the solver spells it
  const seen = new Set<string>();
  for (const r of local) for (const [l, raw] of Object.entries(r.raws)) seen.add(`${normLid(l)}|${normHex(raw)}`);
  const extra: Reading[] = [];
  for (const c of captures) {
    const lid = normLid(c.lid);
    const raw = normHex(c.raw);
    const key = `${lid}|${raw}`;
    const as = wanted.get(lid);
    if (as == null || !raw || !c.value.trim() || seen.has(key)) continue;
    seen.add(key);
    extra.push({ text: c.value.trim(), raws: { [as]: raw } });
  }
  return { readings: [...local, ...extra], fromLabels: extra.length };
}
