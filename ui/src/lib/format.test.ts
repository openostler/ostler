// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { clockHHMM, convertUnit, flagFor, fmt, parseFault, spacedHex } from "./format";

describe("fmt", () => {
  it("uses one decimal below 100 and none above", () => {
    expect(fmt(13.987)).toBe("14.0");
    expect(fmt(771.32)).toBe("771");
    expect(fmt(-120.4)).toBe("-120");
  });
  it("honours an explicit decimal count", () => expect(fmt(1.234, 2)).toBe("1.23"));
  it("renders non-numbers as a dash", () => {
    expect(fmt(null)).toBe("–");
    expect(fmt(Number.NaN)).toBe("–");
  });
});

describe("convertUnit", () => {
  const metric = { temp: "C", dist: "km" } as const;
  const imperial = { temp: "F", dist: "mi" } as const;
  it("passes base units through", () => expect(convertUnit(90, "°C", metric)).toEqual({ v: 90, unit: "°C" }));
  it("converts °C to °F", () => expect(convertUnit(100, "°C", imperial)).toEqual({ v: 212, unit: "°F" }));
  it("converts km/h to mph", () => expect(convertUnit(100, "km/h", imperial).v).toBeCloseTo(62.1371));
  it("leaves unrelated units alone", () => expect(convertUnit(1.2, "bar", imperial)).toEqual({ v: 1.2, unit: "bar" }));
});

describe("parseFault", () => {
  it("splits a SLABS code, text and tag", () => {
    expect(parseFault("027: shuttle valve switch — electrical failure (Current)")).toEqual({
      raw: "027", text: "shuttle valve switch — electrical failure", tag: "Current", current: true,
      orig: "027: shuttle valve switch — electrical failure (Current)",
    });
  });
  it("treats Logged as not current", () => {
    const f = parseFault("air flow circuit (Logged Low)");
    expect(f).toMatchObject({ text: "air flow circuit", tag: "Logged Low", current: false, raw: "" });
  });
  it("keeps byte.bit references", () => expect(parseFault("byte3.bit4 RF sensor").raw).toBe("byte3.bit4"));
});

describe("flagFor", () => {
  it("lets range status win over confidence", () => expect(flagFor("high", "candidate").cls).toBe("hi"));
  it("marks candidates as experimental", () => expect(flagFor("ok", "candidate").cls).toBe("exp"));
  it("is ok for proven values in range", () => expect(flagFor(null, "proven").cls).toBe("ok"));
});

it("formats hex and clock", () => {
  expect(spacedHex("0902fa")).toBe("09 02 fa");
  expect(spacedHex("09 02fa")).toBe("09 02 fa");
  expect(clockHHMM(new Date(2026, 0, 1, 7, 5))).toBe("07:05");
});
