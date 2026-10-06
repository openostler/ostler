// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import { parseUtc, toUtc } from "./time";

describe("RFC 3339 timestamps", () => {
  it("parses UTC and offset date-times to epoch ms", () => {
    expect(parseUtc("2026-10-06T09:00:00.000Z")).toBe(1_791_277_200_000);
    expect(parseUtc("2026-10-06T09:00:00Z")).toBe(1_791_277_200_000);
    expect(parseUtc("2026-10-06T11:00:00.250+02:00")).toBe(1_791_277_200_250);
  });

  it("treats a naive or malformed time as unknown", () => {
    for (const bad of [null, undefined, "", "2026-10-06 09:00:00", "2026-10-06T09:00:00", "soon"]) {
      expect(parseUtc(bad)).toBeNull();
    }
  });

  it("formats epoch ms as UTC with milliseconds and Z", () => {
    expect(toUtc(1_791_277_200_250)).toBe("2026-10-06T09:00:00.250Z");
    expect(parseUtc(toUtc(1_791_277_200_250))).toBe(1_791_277_200_250);
  });
});
