import { describe, expect, it } from "vitest";
import type { Field, Note, SessionData, SessionEvent, SessionMeta } from "../api/schemas";
import { HISTORY_LEN, staleAge } from "./live";
import {
  activeNote, foldEvents, gpsAt, historyAt, isSignalChannel, NOTE_SHOW_MS, rangeStatus, signalsAt, splitFaults, synthesise,
} from "./replayState";

const meta = (over: Partial<SessionMeta> = {}): SessionMeta => ({
  id: "s1", start_utc: "2026-10-05T09:00:00.000Z", end_utc: null, duration_s: 100, rows: 101, parts: ["data.csv"],
  modules: ["motor"], has_gps: true, distance_km: 0, max_speed_kmh: null, bbox: null, start_pos: null, end_pos: null,
  synthetic: false, recording: false, source: "mock", audio: [],
  channels: [
    { name: "GPS_Latitude", units: "deg", group: "gps" },
    { name: "GPS_Longitude", units: "deg", group: "gps" },
    { name: "GPS_Speed", units: "km/h", group: "gps" },
    { name: "rpm", units: "rpm", group: "engine", c: "proven", limits: [700, 4500] },
    { name: "coolant_temp", units: "°C", group: "temperatures", c: "proven", limits: null },
    { name: "battery", units: "V", group: "electrical", c: "proven", limits: [11.5, 15.5] },
    { name: "height_fl", units: "mm", group: "suspension", c: "candidate", limits: null },
    { name: "InlineAcc", units: "g", group: "accel" },
    { name: "module", units: "", group: "text" },
  ],
  ...over,
});

const N = 101; // 0 … 100 s, one row per second
const T = Array.from({ length: N }, (_, i) => i * 1000);
const data = (): SessionData => ({
  id: "s1", t: T, utc: T.map((t) => 1_791_190_800_000 + t), decimated: false, track: [],
  ch: {
    GPS_Latitude: T.map(() => 56.6), GPS_Longitude: T.map(() => -4.6), GPS_Speed: T.map((_, i) => i),
    rpm: T.map((_, i) => (i < 60 ? 800 + i * 10 : null)), // motor stops answering at 60 s (module switch)
    coolant_temp: T.map((_, i) => (i % 2 ? null : 80 + i / 10)), // sparse
    battery: T.map(() => 14.1),
    height_fl: T.map((_, i) => (i >= 60 ? 400 : null)),
    InlineAcc: T.map(() => 0.1),
  },
});

const events: SessionEvent[] = [
  { t: 0, type: "state", conn: "connected", status: "connected", module: "motor", mode: "mock", active_test: null, fault_watch: false, logging: { recording: false } },
  { t: 10_000, type: "command", action: "output_ac_fan", ok: true, message: "A/C fan" },
  { t: 20_000, type: "active_test", active_test: { action: "output_ac_fan", label: "A/C Fan", since: 20, stop: "stop_ac_fan" } },
  { t: 25_000, type: "command", action: "read_identity", ok: false, error: "no answer" },
  { t: 30_000, type: "active_test", active_test: null },
  { t: 40_000, type: "conn", conn: "lost" },
  { t: 45_000, type: "conn", conn: "connected" },
  { t: 50_000, type: "fault_watch", on: true },
  { t: 55_000, type: "logging", recording: true, file: "x.csv" },
  { t: 60_000, type: "module", module: "slabs" },
  { t: 61_000, type: "mystery", whatever: 1 },
];

describe("event folding", () => {
  it("starts from the state line and applies changes up to t", () => {
    const s = foldEvents(events, 0);
    expect(s).toMatchObject({ conn: "connected", status: "connected", module: "motor", active_test: null, fault_watch: false });
    expect(s).not.toHaveProperty("mode");
    expect(s.lastCommand).toEqual({});
  });

  it("tracks active_test on and off", () => {
    expect(foldEvents(events, 19_999).active_test).toBeNull();
    expect(foldEvents(events, 20_000).active_test).toEqual({ action: "output_ac_fan", label: "A/C Fan", since: 20, stop: "stop_ac_fan" });
    expect(foldEvents(events, 30_000).active_test).toBeNull();
  });

  it("keeps the last command per action, without params", () => {
    const s = foldEvents(events, 26_000);
    expect(s.lastCommand.output_ac_fan).toEqual({ t: 10_000, ok: true, message: "A/C fan" });
    expect(s.lastCommand.read_identity).toEqual({ t: 25_000, ok: false, error: "no answer" });
  });

  it("follows conn, fault watch, logging and module; ignores unknown types", () => {
    expect(foldEvents(events, 41_000).conn).toBe("lost");
    expect(foldEvents(events, 46_000).conn).toBe("connected");
    const end = foldEvents(events, 100_000);
    expect(end).toMatchObject({ fault_watch: true, logging: { recording: true, file: "x.csv" }, module: "slabs" });
  });

  it("sorts out-of-order events and survives an empty stream", () => {
    expect(foldEvents([...events].reverse(), 61_000).module).toBe("slabs");
    expect(foldEvents([], 5).module).toBeNull();
  });

  it("tolerates old sessions' mode events (ADR-0011: no modes) without tracking them", () => {
    const s = foldEvents([...events, { t: 62_000, type: "mode", mode: "live" }], 70_000);
    expect(s).not.toHaveProperty("mode");
    expect(s.module).toBe("slabs");
  });

  it("a later part's state line does not forget earlier commands", () => {
    const s = foldEvents([...events.slice(0, 2), { t: 12_000, type: "state", module: "motor" }], 13_000);
    expect(s.lastCommand.output_ac_fan?.ok).toBe(true);
  });
});

describe("range status (s) from limits", () => {
  it("matches the server's ok/low/high/suspect", () => {
    expect(rangeStatus(800, [700, 4500])).toBe("ok");
    expect(rangeStatus(600, [700, 4500])).toBe("low");
    expect(rangeStatus(4600, [700, 4500])).toBe("high");
    expect(rangeStatus(9000, [700, 4500])).toBe("suspect"); // out by more than a whole span
    expect(rangeStatus(800, null)).toBeNull();
    expect(rangeStatus(null, [0, 1])).toBeNull();
  });
});

describe("snapshot synthesis", () => {
  it("builds signals with units, confidence and a recomputed s; skips GPS, accel and text", () => {
    const sig = signalsAt(meta(), data(), 10);
    expect(Object.keys(sig).sort()).toEqual(["battery", "coolant_temp", "rpm"]);
    expect(sig.rpm).toEqual({ v: 900, u: "rpm", s: "ok", c: "proven" });
    expect(sig.coolant_temp?.v).toBe(81); // row 10 itself
    expect(signalsAt(meta(), data(), 11).coolant_temp?.v).toBe(81); // sparse row → last value
    expect(isSignalChannel({ name: "GPS_Speed", group: "gps" })).toBe(false);
  });

  it("falls back to /fields limits when the session has none", () => {
    const fields = { coolant_temp: { limits: [-40, 70], unit: "°C", c: "proven" } as unknown as Field };
    expect(signalsAt(meta(), data(), 10, fields).coolant_temp?.s).toBe("high");
  });

  it("follows the recorded module, and keeps only that module's fields once known", () => {
    const before = synthesise({ meta: meta(), data: data(), events, t: 30_000 });
    expect(before.module).toBe("motor");
    expect(before.snap.module).toBe("motor");
    expect(before.snap).not.toHaveProperty("mode");
    const slabsFields = { height_fl: { limits: null, unit: "mm", c: "candidate" } as unknown as Field };
    const after = synthesise({ meta: meta(), data: data(), events, t: 70_000, fields: slabsFields });
    expect(after.module).toBe("slabs");
    expect(after.live.module).toBe("slabs");
    expect(Object.keys(after.snap.signals)).toEqual(["height_fl"]);
  });

  it("carries the event state: status, conn, active_test (snapshot shape), logging, fault watch", () => {
    const { snap } = synthesise({ meta: meta(), data: data(), events, t: 21_000 });
    expect(snap.status).toBe("connected");
    expect(snap.conn).toBe("connected");
    expect(snap.active_test).toEqual({ action: "output_ac_fan", label: "A/C Fan", since: 20, stop: "stop_ac_fan" });
    expect(snap.logging).toEqual({ recording: false });
    expect(snap.battery_v).toBe(14.1);
    const late = synthesise({ meta: meta(), data: data(), events, t: 56_000 }).snap;
    expect(late.fault_watch).toBe(true);
    expect(late.logging).toEqual({ recording: true, file: "x.csv" });
    expect(synthesise({ meta: meta(), data: data(), events, t: 41_000 }).snap.conn).toBe("lost");
  });

  it("builds GPS from the GPS channels and the clock from UTC", () => {
    const { snap } = synthesise({ meta: meta(), data: data(), events, t: 5_000 });
    expect(snap.gps).toMatchObject({ fix: true, lat: 56.6, lon: -4.6, speed_kmh: 5, src: "replay" });
    expect(snap.ts).toBe((1_791_190_800_000 + 5_000) / 1000);
    expect(gpsAt({ ...data(), ch: { rpm: [] } }, 0)).toBeNull();
  });

  it("carries device-level fields from the live snapshot, never its signals", () => {
    const base = { status: "error", signals: { rpm: { v: 1, u: "rpm" } }, faults: ["live fault"], public: true };
    const { snap } = synthesise({ meta: meta(), data: data(), events, t: 5_000, base });
    expect(snap.public).toBe(true);
    expect(snap.status).toBe("connected");
    expect(snap.faults).toEqual([]);
    expect(snap.signals.rpm?.v).toBe(850);
  });

  it("splits the faults text column when the data carries it", () => {
    expect(splitFaults("027: a; 031: b")).toEqual(["027: a", "031: b"]);
    expect(splitFaults("")).toEqual([]);
    const d = { ...data(), text: { faults: T.map((_, i) => (i === 3 ? "027: shuttle valve (Current)" : null)) } };
    expect(synthesise({ meta: meta(), data: d, events, t: 4_000 }).snap.faults).toEqual(["027: shuttle valve (Current)"]);
  });

  it("rebuilds the live history from the 60 samples before t, never stale", () => {
    const { live } = synthesise({ meta: meta(), data: data(), events, t: 80_000 });
    expect(live.history.battery).toHaveLength(HISTORY_LEN);
    expect(live.history.battery!.at(-1)).toEqual({ t: 80_000, v: 14.1 });
    expect(live.history.battery![0]!.t).toBe(21_000);
    expect(staleAge(live.seen.battery, Date.now(), true)).toBeNull();
    expect(historyAt(data(), 4, ["coolant_temp"]).coolant_temp!.map((s) => s.t)).toEqual([0, 2000, 4000]);
  });
});

describe("activeNote", () => {
  const note = (id: string, t: number, t_end: number | null = null): Note =>
    ({ id, t, t_end, text: id, tags: [], kind: "note", source: "retro", created: "" });
  it("shows a point note just after the cursor passes it, and a range while inside it", () => {
    const notes = [note("a", 1000), note("b", 10_000, 30_000)];
    expect(activeNote(notes, 999)).toBeNull();
    expect(activeNote(notes, 1000)?.id).toBe("a");
    expect(activeNote(notes, 1000 + NOTE_SHOW_MS + 1)).toBeNull();
    expect(activeNote(notes, 25_000)?.id).toBe("b");
  });
});
