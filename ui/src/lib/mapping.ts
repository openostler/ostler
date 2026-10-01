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
