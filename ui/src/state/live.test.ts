import { describe, expect, it } from "vitest";
import type { Snapshot } from "../api/schemas";
import { HISTORY_LEN, initialLive, reduceSnapshot } from "./live";

const snap = (over: Partial<Snapshot>): Snapshot => ({ status: "connected", signals: {}, faults: [], ...over });

describe("reduceSnapshot", () => {
  it("records numeric history and caps it", () => {
    let s = initialLive;
    for (let i = 0; i < HISTORY_LEN + 5; i++) {
      s = reduceSnapshot(s, snap({ module: "motor", signals: { rpm: { v: i, u: "rpm" } } }), i);
    }
    expect(s.history.rpm).toHaveLength(HISTORY_LEN);
    expect(s.history.rpm?.at(-1)).toEqual({ t: HISTORY_LEN + 4, v: HISTORY_LEN + 4 });
  });

  it("builds the connection sequence and closes it once connected", () => {
    let s = reduceSnapshot(initialLive, snap({ status: "connecting", connect_phase: "opening the cable" }), 0);
    s = reduceSnapshot(s, snap({ status: "connecting", connect_phase: "opening the cable" }), 5);
    s = reduceSnapshot(s, snap({ status: "connecting", connect_phase: "sending init (try 1/3)" }), 10);
    s = reduceSnapshot(s, snap({ status: "connected" }), 20);
    s = reduceSnapshot(s, snap({ status: "connected" }), 30);
    expect(s.seq.map((x) => x.phase)).toEqual(["opening the cable", "sending init (try 1/3)", "session established"]);
    expect(s.seqDone).toBe(true);
  });

  it("starts fresh when the module changes", () => {
    let s = reduceSnapshot(initialLive, snap({ module: "motor", signals: { rpm: { v: 800, u: "rpm" } } }), 0);
    s = reduceSnapshot(s, snap({ module: "slabs", signals: { height_left: { v: 120, u: "" } } }), 1);
    expect(s.module).toBe("slabs");
    expect(Object.keys(s.history)).toEqual(["height_left"]);
  });
});
