// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Quantities through `Intl` (CLDR) (UI spec §10.1, U1; app-model spec §2: units format in
 * the shell). A unit CLDR knows (ECMA-402's sanctioned set, e.g. celsius, kilometer-per-hour,
 * percent) is formatted by `Intl.NumberFormat` with `style: "unit"`, so its symbol, spacing
 * and digits follow the locale. Other units (V, kPa, rpm, bar) keep their symbol after a
 * locale-formatted number, separated by a no-break space.
 */

/** Store / VSS unit keys → ECMA-402 sanctioned simple or compound units. */
const CLDR: Record<string, string> = {
  "°C": "celsius",
  Celsius: "celsius",
  "°F": "fahrenheit",
  Fahrenheit: "fahrenheit",
  "%": "percent",
  percent: "percent",
  "km/h": "kilometer-per-hour",
  mph: "mile-per-hour",
  km: "kilometer",
  mi: "mile",
  m: "meter",
  mm: "millimeter",
  s: "second",
  ms: "millisecond",
  min: "minute",
  h: "hour",
  l: "liter",
  L: "liter",
  "l/h": "liter-per-hour",
  kg: "kilogram",
  deg: "degree",
  "°": "degree",
};

/** The CLDR unit for a store/VSS unit, or null when CLDR has none. */
export const cldrUnit = (unit: string): string | null => CLDR[unit] ?? null;

const cache = new Map<string, Intl.NumberFormat>();
function nf(locale: string | undefined, opts: Intl.NumberFormatOptions): Intl.NumberFormat {
  const key = `${locale ?? ""}|${JSON.stringify(opts)}`;
  let f = cache.get(key);
  if (!f) {
    f = new Intl.NumberFormat(locale, opts);
    cache.set(key, f);
  }
  return f;
}

/** "12.6 V", "86 °C", "48 km/h" (locale-aware); "–" for a missing value, never zero. */
export function formatQuantity(v: number | null | undefined, unit: string, dec?: number, locale?: string): string {
  if (typeof v !== "number" || Number.isNaN(v)) return "–";
  const digits = dec ?? (Math.abs(v) >= 100 ? 0 : 1);
  const base: Intl.NumberFormatOptions = { minimumFractionDigits: digits, maximumFractionDigits: digits };
  const cldr = cldrUnit(unit);
  if (cldr) {
    // Intl's percent unit expects the number itself (48 → "48%"), unlike style "percent"
    return nf(locale, { ...base, style: "unit", unit: cldr, unitDisplay: "short" }).format(v);
  }
  const num = nf(locale, base).format(v);
  return unit ? `${num}\u00a0${unit}` : num;
}

/** The time of day as the locale writes it, hours and minutes (24 h where the locale does). */
export function formatClock(d: Date, locale?: string): string {
  return new Intl.DateTimeFormat(locale, { hour: "2-digit", minute: "2-digit" }).format(d);
}
