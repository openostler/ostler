/**
 * Value formatting, unit conversion and fault parsing — pure functions, one place.
 * The store and the server speak base units (°C, km/h, km); the UI converts at render.
 */
export type Units = { temp: "C" | "F"; dist: "km" | "mi" };

export function fmt(v: unknown, dec?: number): string {
  if (typeof v !== "number" || Number.isNaN(v)) return "–";
  if (dec != null) return v.toFixed(dec);
  return Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(1);
}

export function convertUnit(v: number, unit: string, units: Units): { v: number; unit: string } {
  if (unit === "°C" && units.temp === "F") return { v: (v * 9) / 5 + 32, unit: "°F" };
  if (unit === "km/h" && units.dist === "mi") return { v: v * 0.621371, unit: "mph" };
  if (unit === "km" && units.dist === "mi") return { v: v * 0.621371, unit: "mi" };
  return { v, unit };
}

/** Current time as HH:MM (24 h): the D2 has no lit clock, so the phone's clock is shown. */
export function clockHHMM(d: Date = new Date()): string {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** "0902fa" → "09 02 fa". */
export const spacedHex = (h: string | null | undefined): string =>
  (h ?? "").replace(/\s+/g, "").replace(/(..)/g, "$1 ").trim();

export type ParsedFault = { text: string; tag: string; raw: string; current: boolean; orig: string };

/** "027: shuttle valve switch — electrical failure (Current)" → {raw:"027", text, tag:"Current"}. */
export function parseFault(str: string): ParsedFault {
  const mtag = str.match(/\(([^)]+)\)\s*$/);
  const tag = mtag?.[1] ?? "";
  let text = str.replace(/\s*\([^)]+\)\s*$/, "");
  let raw = "";
  const mraw = text.match(/^(byte\d+\.bit\d+|[0-9A-Fa-f]{2,3}[:-][0-9A-Fa-f-]+)\s*/);
  if (mraw?.[1]) raw = mraw[1];
  const mcode = text.match(/^(\d{3}):\s*/);
  if (mcode?.[1]) {
    raw = mcode[1];
    text = text.replace(/^\d{3}:\s*/, "");
  }
  return { text, tag, raw, current: /current/i.test(tag), orig: str };
}

/** Build a fault-meaning lookup from a /faults list: match the decoder's raw string by
 * full name, or map a generic `byte<off>.bit<n>` back to its `off.bit` key. */
export function faultLookup<M extends { key: string; name: string }>(
  meanings: M[],
): (raw: string) => M | undefined {
  const byName = new Map(meanings.map((m) => [m.name, m]));
  const byKey = new Map(meanings.map((m) => [m.key, m]));
  return (raw: string) => {
    const hit = byName.get(raw);
    if (hit) return hit;
    const mb = raw.match(/^byte(\d+)\.bit(\d+)/);
    return mb ? byKey.get(`${mb[1]}.${mb[2]}`) : undefined;
  };
}

export type FlagKind = "ok" | "exp" | "lo" | "hi" | "sus";
export type Flag = { cls: FlagKind; txt: string };

/** Status badge for a value: range status wins over confidence. */
export function flagFor(status: string | null | undefined, confidence: string | undefined): Flag {
  if (status === "suspect") return { cls: "sus", txt: "SUSPECT" };
  if (status === "low") return { cls: "lo", txt: "LOW" };
  if (status === "high") return { cls: "hi", txt: "HIGH" };
  if (confidence === "candidate") return { cls: "exp", txt: "EXP" };
  return { cls: "ok", txt: "OK" };
}
