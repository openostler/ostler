import { afterEach, describe, expect, it, vi } from "vitest";
import { AudioCapture, setPhoneAudio } from "./audio";
import { formatNoteTime, noteAt, noteSpan, sortNotes } from "./notes";
import { MotionCapture, setPhoneMotion } from "./motion";
import { applyOptions, availability, DEFAULT_OPTIONS, gpsLabel, loadOptions, saveOptions } from "./recordingOptions";

const SOURCES = {
  gps: "usb",
  pi_audio: { state: "unavailable", reason: "arecord is not installed" },
  imu: { state: "available" },
  accel_hz: 25,
};

afterEach(() => {
  setPhoneAudio(null);
  setPhoneMotion(null);
  vi.unstubAllGlobals();
});

describe("availability", () => {
  it("greys out each source with its reason", () => {
    const a = availability(SOURCES, { audio: "Needs HTTPS — see the HTTPS guide", motion: null });
    expect(a.audio).toEqual({ off: null, phone: "Needs HTTPS — see the HTTPS guide", pi: "arecord is not installed" });
    expect(a.accel).toEqual({ off: null, phone: null, pi: null, gps: null });
  });
  it("needs a GPS for GPS-derived and a report from the Pi for Pi sources", () => {
    expect(availability({ ...SOURCES, gps: "none" }, { audio: null, motion: null }).accel.gps).toBe("Needs a GPS receiver");
    const none = availability(null, { audio: null, motion: null });
    expect(none.audio.pi).toMatch(/hasn't reported/);
    expect(none.accel.pi).toMatch(/hasn't reported/);
    expect(none.audio.phone).toBeNull();
  });
  it("defaults to 'Needs HTTPS' on an insecure page (jsdom)", () => {
    expect(availability(SOURCES).audio.phone).toBe("Needs HTTPS — see the HTTPS guide");
    expect(availability(SOURCES).accel.phone).toBe("Needs HTTPS — see the HTTPS guide");
  });
});

describe("stored options", () => {
  it("round-trips and sanitises", () => {
    expect(loadOptions()).toEqual(DEFAULT_OPTIONS);
    saveOptions({ audio: "pi", accel: "phone", hz: 50, forwardFromGps: true });
    expect(loadOptions()).toEqual({ audio: "pi", accel: "phone", hz: 50, forwardFromGps: true });
    localStorage.setItem("d2diag.recordingOptions", JSON.stringify({ audio: "loud", hz: 7 }));
    expect(loadOptions()).toMatchObject({ audio: "off", hz: 25 });
    localStorage.setItem("d2diag.recordingOptions", "{not json");
    expect(loadOptions()).toEqual(DEFAULT_OPTIONS);
  });
  it("survives blocked storage", () => {
    const get = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new Error("blocked"); });
    const set = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    expect(loadOptions()).toEqual(DEFAULT_OPTIONS);
    expect(() => saveOptions(DEFAULT_OPTIONS)).not.toThrow();
    get.mockRestore();
    set.mockRestore();
  });
});

describe("gpsLabel", () => {
  it("names the source and the fix", () => {
    expect(gpsLabel({ ...SOURCES, gps: "none" })).toBe("No GPS");
    expect(gpsLabel(SOURCES, { fix: true, sats: 7 })).toBe("GPS (USB) · fix, 7 sats");
    expect(gpsLabel({ ...SOURCES, gps: "mock" }, { fix: false, sats: 0 })).toBe("GPS (demo) · no fix yet");
  });
});

describe("applyOptions", () => {
  it("tells the Pi about its sources and arms phone motion", async () => {
    const fetch = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetch);
    const motion = new MotionCapture({
      addListener: () => undefined, removeListener: () => undefined, fetch: fetch as unknown as typeof globalThis.fetch,
      now: () => 0, setInterval: () => 1, clearInterval: () => undefined, setTimeout: () => 1,
      requestPermission: vi.fn(async () => "granted"),
    });
    setPhoneMotion(motion);
    setPhoneAudio(new AudioCapture({ fetch: fetch as unknown as typeof globalThis.fetch, now: () => 0, uuid: () => "u", sleep: async () => undefined }));
    const r = await applyOptions({ audio: "pi", accel: "phone", hz: 50, forwardFromGps: false }, "  Rattle hunt ");
    expect(r).toEqual({ ok: true, errors: [] });
    const cmd = (fetch.mock.calls as unknown as [string, RequestInit][]).find(([u]) => u === "/command")!;
    expect(JSON.parse(String(cmd[1].body))).toEqual({ action: "recording_options", params: { audio: "pi", imu: "off", accel_hz: 50, name: "Rattle hunt" } });
    expect(motion.state).toMatchObject({ status: "armed", rate: 50 });
    expect(loadOptions()).toMatchObject({ audio: "pi", accel: "phone", hz: 50 });
  });

  it("collects every failure in plain English", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ ok: false, error: "IMU not found" }), { status: 400 })));
    setPhoneAudio(new AudioCapture({ fetch: vi.fn() as unknown as typeof globalThis.fetch, now: () => 0, uuid: () => "u", sleep: async () => undefined }));
    const r = await applyOptions({ audio: "phone", accel: "pi", hz: 25, forwardFromGps: false });
    expect(r.ok).toBe(false);
    expect(r.errors).toEqual(["This browser can't record audio", "IMU not found"]);
  });
});

describe("note helpers", () => {
  const n = (id: string, t: number, t_end: number | null = null) =>
    ({ id, t, t_end, text: "", tags: [], kind: "note", source: "retro", created: `2026-10-05T09:00:0${id}Z` });
  it("formats session times and ranges", () => {
    expect(formatNoteTime(0)).toBe("0:00");
    expect(formatNoteTime(125_400)).toBe("2:05");
    expect(formatNoteTime(3_725_000)).toBe("1:02:05");
    expect(noteSpan({ t: 120_000, t_end: 150_000 })).toBe("2:00–2:30");
  });
  it("sorts by time and finds the note at the cursor", () => {
    expect(sortNotes([n("2", 5000), n("1", 1000), n("3", 1000)]).map((x) => x.id)).toEqual(["1", "3", "2"]);
    expect(noteAt({ t: 1000, t_end: null }, 1800)).toBe(true);
    expect(noteAt({ t: 1000, t_end: null }, 2500)).toBe(false);
    expect(noteAt({ t: 1000, t_end: 9000 }, 5000)).toBe(true);
  });
});
