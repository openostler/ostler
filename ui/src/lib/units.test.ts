// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { cldrUnit, formatClock, formatQuantity } from "./units";

const nb = (s: string) => s.replace(/\u00a0|\u202f/g, " ");

describe("Intl (CLDR) units (UI spec §10.1)", () => {
  it("formats CLDR units with the locale's symbol and spacing", () => {
    expect(nb(formatQuantity(48, "km/h", 0, "en-GB"))).toBe("48 km/h");
    expect(nb(formatQuantity(86, "°C", 0, "en-GB"))).toBe("86°C");
    expect(nb(formatQuantity(86, "Celsius", 0, "de-DE"))).toBe("86 °C");
    expect(nb(formatQuantity(11.2, "km", 1, "en-GB"))).toBe("11.2 km");
    expect(nb(formatQuantity(48, "%", 0, "en-GB"))).toBe("48%");
    expect(cldrUnit("kPa")).toBeNull();
  });

  it("keeps other units after a locale-formatted number, joined by a no-break space", () => {
    expect(formatQuantity(12.64, "V", 1, "en-GB")).toBe("12.6 V");
    expect(formatQuantity(12.64, "V", 1, "de-DE")).toBe("12,6 V");
    expect(formatQuantity(1234, "rpm", 0, "en-GB")).toBe("1,234 rpm");
    expect(formatQuantity(3, "", 0, "en-GB")).toBe("3");
  });

  it("never turns a missing value into zero", () => {
    expect(formatQuantity(null, "V")).toBe("–");
    expect(formatQuantity(undefined, "°C")).toBe("–");
    expect(formatQuantity(Number.NaN, "V")).toBe("–");
  });

  it("writes the clock as the locale does", () => {
    const d = new Date(2026, 9, 6, 7, 5);
    expect(formatClock(d, "en-GB")).toBe("07:05");
    expect(nb(formatClock(d, "en-US"))).toMatch(/^07:05 AM$/);
  });
});
