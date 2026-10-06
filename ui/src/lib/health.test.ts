// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it } from "vitest";
import type { Snapshot } from "../api/schemas";
import { summarize } from "./health";

const snap = (over: Partial<Snapshot>): Snapshot => ({ status: "connected", signals: {}, faults: [], ...over });

describe("summarize", () => {
  it("is calm when everything is normal", () => {
    const h = summarize(snap({ signals: { rpm: { v: 800, u: "rpm", s: "ok" } } }), {});
    expect(h).toMatchObject({ level: "ok", headline: "All normal" });
  });
  it("raises an alarm for current faults and names a single out-of-range value", () => {
    const h = summarize(snap({
      signals: { coolant_temp: { v: 112, u: "°C", s: "high" } },
      faults: ["inlet air temp. circuit (Current)", "air flow circuit (Logged Low)"],
    }), { coolant_temp: { label: "Coolant" } as never });
    expect(h.level).toBe("alarm");
    expect(h.headline).toBe("1 current fault · Coolant high · 1 logged fault");
  });
  it("only warns for logged faults", () => {
    expect(summarize(snap({ faults: ["027: shuttle valve (Logged)"] }), {}).level).toBe("warn");
  });
  it("reports offline when not connected", () => {
    expect(summarize(snap({ status: "error" }), {})).toMatchObject({ level: "offline", headline: "Not connected" });
    expect(summarize(null, {}).level).toBe("offline");
  });
});
