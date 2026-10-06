// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import metaFx from "../api/fixtures/session-meta.json";
import { SessionMeta, type Note, type Snapshot } from "../api/schemas";
import { AudioCapture, setPhoneAudio, type AudioDeps } from "../lib/audio";
import { MotionCapture, setPhoneMotion, type MotionDeps, type Vec3 } from "../lib/motion";
import { AppCtx } from "../state/app";
import { INACTIVE, ReplayCtx, type Replay } from "../state/replay";
import { renderWithApp } from "../test/renderWithApp";
import { MarkButton } from "./MarkButton";
import { RecordingCard } from "./RecordingCard";
import { RecordingOptions } from "./RecordingOptions";
import { NotesPanel } from "./replay/NotesPanel";
import { ReplayAudio } from "./replay/ReplayAudio";

/* ---- fakes ---- */

type Call = { path: string; method: string; body?: unknown };
const NOTE: Note = { id: "abcd1234", t: 61_000, t_end: null, text: "", tags: [], kind: "mark", source: "live", created: "2026-10-05T09:01:01.000Z" };

function stubServer(reply: (c: Call) => unknown = () => ({ ok: true })) {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const url = new URL(input, "http://dash.local");
    const c: Call = { path: url.pathname + url.search, method: init?.method ?? "GET" };
    if (typeof init?.body === "string") c.body = JSON.parse(init.body);
    calls.push(c);
    const body = reply(c);
    return new Response(JSON.stringify(body), { status: (body as { ok?: boolean })?.ok === false ? 400 : 200, headers: { "Content-Type": "application/json" } });
  }));
  return calls;
}

function fakeMotion() {
  let handler: ((e: DeviceMotionEvent) => void) | null = null;
  let now = 1_000;
  const timeouts: { fn: () => void; at: number }[] = [];
  const deps: MotionDeps = {
    addListener: (fn) => { handler = fn; }, removeListener: () => { handler = null; },
    fetch: vi.fn(async () => new Response("{}")) as unknown as typeof fetch,
    now: () => now, setInterval: () => 1, clearInterval: () => undefined,
    setTimeout: (fn, ms) => { timeouts.push({ fn, at: now + ms }); return 1; },
    requestPermission: vi.fn(async () => "granted"),
  };
  const emit = (v: Vec3) => {
    now += 1000 / 60;
    handler?.({ accelerationIncludingGravity: { x: v[0], y: v[1], z: v[2] } } as unknown as DeviceMotionEvent);
    for (const t of [...timeouts]) if (t.at <= now) { timeouts.splice(timeouts.indexOf(t), 1); t.fn(); }
  };
  const m = new MotionCapture(deps);
  setPhoneMotion(m);
  return { m, deps, emit };
}

function fakeAudio() {
  const deps: AudioDeps = { fetch: vi.fn() as unknown as typeof fetch, now: () => 0, uuid: () => "u", sleep: async () => undefined };
  const a = new AudioCapture(deps);
  setPhoneAudio(a);
  return a;
}

const SOURCES = {
  gps: "usb",
  pi_audio: { state: "unavailable", reason: "arecord is not installed" },
  imu: { state: "available" },
  accel_hz: 25,
};
const recordingSnap = (over: Partial<Snapshot> = {}): Snapshot => ({
  status: "connected", signals: {}, faults: [], ts: 1_791_000_720,
  recording: { session: "S1", since: 1_791_000_000, rows: 1440 },
  recording_sources: SOURCES,
  gps: { fix: true, lat: 56.6, lon: -4.6, speed_kmh: 0, heading: 0, sats: 7, hdop: 1, src: "usb", age_s: 0 },
  ...over,
});

const meta = SessionMeta.parse({
  ...metaFx,
  synthetic: false,
  audio: [{ track: "trk1", mime: "audio/webm;codecs=opus", start_ms: 10_000, end_ms: 600_000, source: "phone", bytes: 1000 }],
});

function withReplay(ui: ReactElement, over: Partial<Replay> = {}, snap?: Snapshot) {
  const replay: Replay = {
    ...INACTIVE, active: true, id: meta.id, session: meta, notes: [], t: 0,
    seek: vi.fn(), refreshNotes: vi.fn(), addNote: vi.fn(async () => NOTE), ...over,
  };
  const r = renderWithApp(<ReplayCtx.Provider value={replay}>{ui}</ReplayCtx.Provider>, snap ? { snap } : {});
  return { replay, ...r, rerenderReplay: (o: Partial<Replay>) =>
    r.rerender(<AppCtx.Provider value={r.ctx}><ReplayCtx.Provider value={{ ...replay, ...o }}>{ui}</ReplayCtx.Provider></AppCtx.Provider>) };
}

beforeEach(() => {
  fakeAudio();
  fakeMotion();
});
afterEach(() => {
  setPhoneAudio(null);
  setPhoneMotion(null);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

/* ---- ⚑ ---- */

describe("MarkButton (header ⚑)", () => {
  it("is hidden when nothing is recording, and in replay", () => {
    stubServer();
    const { unmount } = renderWithApp(<MarkButton />);
    expect(screen.queryByRole("button", { name: "Mark this moment" })).toBeNull();
    unmount();
    withReplay(<MarkButton />, {}, recordingSnap());
    expect(screen.queryByRole("button", { name: "Mark this moment" })).toBeNull();
  });

  it("one tap saves a mark, then 'What happened?' PATCHes it", async () => {
    const calls = stubServer((c) => c.path === "/notes/live" ? { ok: true, note: NOTE, session: "S1" } : { ok: true, note: { ...NOTE, text: "clunk" } });
    const { ctx } = renderWithApp(<MarkButton />, { snap: recordingSnap() });
    fireEvent.click(screen.getByRole("button", { name: "Mark this moment" }));
    await screen.findByText("What happened?");
    expect(calls[0]).toEqual({ path: "/notes/live", method: "POST", body: { kind: "mark" } });
    expect(ctx.toast).toHaveBeenCalledWith("⚑ Marked");
    fireEvent.change(screen.getByRole("textbox", { name: "What happened?" }), { target: { value: " clunk " } });
    fireEvent.click(screen.getByRole("button", { name: "noise" }));
    expect(screen.getByRole("button", { name: "noise" })).toHaveAttribute("aria-pressed", "true");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByText("What happened?")).toBeNull());
    expect(calls[1]).toEqual({ path: "/sessions/S1/notes/abcd1234", method: "PATCH", body: { text: "clunk", tags: ["noise"] } });
  });

  it("is greyed while the session is paused (no connection); an absent state means recording", () => {
    stubServer();
    const paused = recordingSnap();
    const { unmount } = renderWithApp(<MarkButton />, { snap: { ...paused, recording: { ...paused.recording!, state: "paused" } } });
    expect(screen.queryByRole("button", { name: "Mark this moment" })).toBeNull();
    expect(screen.getByRole("button", { name: "Connect to the car to mark" })).toBeDisabled();
    unmount();
    renderWithApp(<MarkButton />, { snap: { ...paused, recording: { ...paused.recording!, state: "recording" } } });
    expect(screen.getByRole("button", { name: "Mark this moment" })).toBeInTheDocument();
  });

  it("points phone capture at the recording session", () => {
    stubServer();
    const audio = new AudioCapture({ fetch: vi.fn() as unknown as typeof fetch, now: () => 0, uuid: () => "u", sleep: async () => undefined });
    const spy = vi.spyOn(audio, "setSession");
    setPhoneAudio(audio);
    renderWithApp(<MarkButton />, { snap: recordingSnap() });
    expect(spy).toHaveBeenCalledWith("S1");
  });
});

/* ---- options ---- */

describe("RecordingOptions", () => {
  it("greys out unusable sources with their reason", () => {
    stubServer();
    renderWithApp(<RecordingOptions onClose={vi.fn()} />, { snap: recordingSnap({ recording_sources: { ...SOURCES, gps: "none" }, gps: null }) });
    expect(screen.getByText("No GPS")).toBeInTheDocument();
    const audio = screen.getByRole("radiogroup", { name: "Cabin audio" });
    expect(within(audio).getByRole("radio", { name: /Phone mic — Needs HTTPS — see the HTTPS guide/ })).toBeDisabled();
    expect(within(audio).getByRole("radio", { name: /Pi mic — arecord is not installed/ })).toBeDisabled();
    expect(within(audio).getByRole("radio", { name: "Off" })).toBeEnabled();
    const accel = screen.getByRole("radiogroup", { name: "Accelerometer" });
    expect(within(accel).getByRole("radio", { name: /GPS-derived — Needs a GPS receiver/ })).toBeDisabled();
    expect(within(accel).getByRole("radio", { name: "Pi IMU" })).toBeEnabled();
  });

  it("Apply sends recording_options, keeps the choice per device and closes", async () => {
    const calls = stubServer();
    const onClose = vi.fn();
    const { ctx } = renderWithApp(<RecordingOptions onClose={onClose} />, { snap: recordingSnap() });
    fireEvent.click(screen.getByRole("radio", { name: "Pi IMU" }));
    fireEvent.click(screen.getByRole("button", { name: "50 Hz" }));
    fireEvent.change(screen.getByLabelText("Session name"), { target: { value: "Rattle hunt" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(calls.find((c) => c.path === "/command")?.body).toEqual({
      action: "recording_options", params: { audio: "off", imu: "on", accel_hz: 50, name: "Rattle hunt" },
    });
    expect(JSON.parse(localStorage.getItem("d2diag.recordingOptions")!)).toMatchObject({ accel: "pi", hz: 50 });
    expect(ctx.toast).toHaveBeenCalledWith("Recording options applied");
  });

  it("shows why Apply failed and stays open", async () => {
    stubServer(() => ({ ok: false, error: "IMU not found on /dev/i2c-1" }));
    const onClose = vi.fn();
    renderWithApp(<RecordingOptions onClose={onClose} />, { snap: recordingSnap() });
    fireEvent.click(screen.getByRole("radio", { name: "Pi IMU" }));
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("IMU not found on /dev/i2c-1");
    expect(onClose).not.toHaveBeenCalled();
  });

  it("calibrates the phone: hold still 2 s → level matrix → accel_cal", async () => {
    vi.stubGlobal("isSecureContext", true);
    vi.stubGlobal("DeviceMotionEvent", class {});
    const calls = stubServer();
    const { emit, deps } = fakeMotion();
    renderWithApp(<RecordingOptions onClose={vi.fn()} />, { snap: recordingSnap() });
    fireEvent.click(screen.getByRole("radio", { name: "Phone" }));
    fireEvent.click(screen.getByRole("button", { name: /Calibrate/ }));
    await waitFor(() => expect(deps.requestPermission).toHaveBeenCalled());
    await screen.findByText(/Hold the phone still/);
    await act(async () => { for (let i = 0; i < 130; i++) emit([0, 9.81, 0]); });
    expect(await screen.findByText("Calibrated (level)")).toBeInTheDocument();
    const cal = JSON.parse(localStorage.getItem("d2diag.accelCal")!);
    expect(cal.method).toBe("level");
    await waitFor(() => expect(calls.some((c) => c.path === "/sessions/S1/accel_cal")).toBe(true));
    const sent = calls.find((c) => c.path === "/sessions/S1/accel_cal")!.body as { matrix: number[][]; source: string };
    expect(sent.source).toBe("phone");
    expect(sent.matrix).toEqual(cal.matrix);
  });

  it("reports a calibration where the phone moved", async () => {
    vi.stubGlobal("isSecureContext", true);
    vi.stubGlobal("DeviceMotionEvent", class {});
    stubServer();
    const { emit } = fakeMotion();
    renderWithApp(<RecordingOptions onClose={vi.fn()} />, { snap: recordingSnap() });
    fireEvent.click(screen.getByRole("radio", { name: "Phone" }));
    fireEvent.click(screen.getByRole("button", { name: /Calibrate/ }));
    await screen.findByText(/Hold the phone still/);
    await act(async () => { for (let i = 0; i < 130; i++) emit([i % 2 ? 3 : -3, 9.81, 0]); });
    expect(await screen.findByText(/hold it still for 2 s/)).toBeInTheDocument();
  });
});

/* ---- Logs card ---- */

describe("RecordingCard", () => {
  it("shows duration, modules and sources", () => {
    stubServer();
    renderWithApp(<RecordingCard recording={recordingSnap().recording!} nowS={1_791_000_720} modules={["td5", "slabs"]} />,
      { snap: recordingSnap({ recording_sources: { ...SOURCES, pi_audio: { state: "on" }, imu: { state: "on" } } }) });
    expect(screen.getByText("Recording now · 12 min")).toBeInTheDocument();
    expect(screen.getByText(/1440 rows · td5, slabs/)).toBeInTheDocument();
    const src = screen.getByLabelText("Sources");
    expect(src).toHaveTextContent("GPS (USB) · fix, 7 sats");
    expect(src).toHaveTextContent("Pi mic");
    expect(src).toHaveTextContent("Pi IMU 25 Hz");
  });

  it("paused: says 'Paused — no connection' and offers no ⚑ Mark, Note… or Split", () => {
    stubServer();
    const snap = recordingSnap();
    const rec = { ...snap.recording!, state: "paused" };
    renderWithApp(<RecordingCard recording={rec} nowS={1_791_000_720} onOpen={vi.fn()} />, { snap: { ...snap, recording: rec } });
    expect(screen.getByText("Paused — no connection")).toBeInTheDocument();
    expect(screen.queryByText(/Recording now ·/)).toBeNull();
    expect(screen.queryByRole("button", { name: "Mark this moment" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Note…" })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Split/ })).toBeNull();
    expect(screen.getByRole("button", { name: "Recording options" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Paused — no connection — open" })).toBeInTheDocument();
  });

  it("renders nothing without a recording", () => {
    renderWithApp(<RecordingCard recording={null} nowS={0} />);
    expect(screen.queryByLabelText("Recording now")).toBeNull();
  });

  it("⚑ Mark, Note…, Split and Options", async () => {
    const calls = stubServer((c) => c.path === "/notes/live" ? { ok: true, note: { ...NOTE, kind: (c.body as { kind: string }).kind }, session: "S1" } : { ok: true });
    const onOpen = vi.fn();
    renderWithApp(<RecordingCard recording={recordingSnap().recording!} nowS={1_791_000_720} onOpen={onOpen} />, { snap: recordingSnap() });

    fireEvent.click(screen.getByRole("button", { name: /Recording now, 12 min — open/ }));
    expect(onOpen).toHaveBeenCalledWith("S1");

    fireEvent.click(screen.getByRole("button", { name: "Mark this moment" }));
    await screen.findByText("What happened?");
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(calls.at(-1)).toMatchObject({ path: "/notes/live", body: { kind: "mark" } });

    fireEvent.click(screen.getByRole("button", { name: "Note…" }));
    fireEvent.change(await screen.findByRole("textbox", { name: "What happened?" }), { target: { value: "smells hot" } });
    fireEvent.click(screen.getByRole("button", { name: "fault" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(calls.at(-1)).toEqual({ path: "/notes/live", method: "POST", body: { kind: "note", text: "smells hot", tags: ["fault"] } }));

    fireEvent.click(screen.getByRole("button", { name: /Split/ }));
    await waitFor(() => expect(calls.at(-1)).toMatchObject({ path: "/command", body: { action: "split_session" } }));

    fireEvent.click(screen.getByRole("button", { name: "Recording options" }));
    expect(await screen.findByText("Recording & flags")).toBeInTheDocument();
  });

  it("offers Resume when this phone should be capturing but isn't", () => {
    stubServer();
    localStorage.setItem("d2diag.recordingOptions", JSON.stringify({ audio: "phone" }));
    renderWithApp(<RecordingCard recording={recordingSnap().recording!} nowS={1_791_000_720} />, { snap: recordingSnap() });
    expect(screen.getByRole("button", { name: "Resume phone capture" })).toBeInTheDocument();
  });
});

/* ---- replay notes ---- */

const NOTES: Note[] = [
  { id: "n2", t: 300_000, t_end: 330_000, text: "Rattle over cattle grid", tags: ["noise"], kind: "note", source: "retro", created: "2026-10-05T10:00:00Z" },
  { id: "n1", t: 120_000, t_end: null, text: "", tags: [], kind: "mark", source: "live", created: "2026-10-05T09:02:00Z" },
];

describe("NotesPanel", () => {
  it("lists notes by time with ranges, and jumps to one", () => {
    const { replay } = withReplay(<NotesPanel />, { notes: NOTES, t: 120_400 });
    const rows = screen.getAllByRole("listitem");
    expect(rows[0]).toHaveTextContent("2:00");
    expect(rows[0]).toHaveTextContent("Mark");
    expect(rows[0]).toHaveClass("here");
    expect(rows[1]).toHaveTextContent("5:00–5:30");
    expect(rows[1]).toHaveTextContent("range");
    expect(rows[1]).toHaveTextContent("noise");
    fireEvent.click(screen.getByRole("button", { name: /Jump to 5:00–5:30/ }));
    expect(replay.seek).toHaveBeenCalledWith(300_000);
  });

  it("adds a note at the cursor", async () => {
    stubServer();
    const { replay } = withReplay(<NotesPanel />, { notes: NOTES, t: 45_250 });
    fireEvent.click(screen.getByRole("button", { name: "+ Add note at cursor" }));
    expect(screen.getByTestId("note-start")).toHaveTextContent("0:45");
    fireEvent.change(screen.getByRole("textbox", { name: "Note text" }), { target: { value: "Turbo whistle" } });
    fireEvent.click(screen.getByRole("button", { name: "test" }));
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(replay.addNote).toHaveBeenCalledWith({ t: 45_250, t_end: null, text: "Turbo whistle", tags: ["test"] }));
  });

  it("edits (text, tags, range to cursor) and deletes", async () => {
    const calls = stubServer((c) => c.method === "DELETE" ? { ok: true } : { ok: true, note: NOTES[1] });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const { replay } = withReplay(<NotesPanel />, { notes: NOTES, t: 150_000 });
    fireEvent.click(screen.getAllByRole("button", { name: "Edit note" })[0]!);
    expect(screen.getByText("Edit mark")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Note text" }), { target: { value: "Misfire" } });
    fireEvent.click(screen.getByRole("button", { name: "Make a range to cursor" }));
    expect(screen.getByTestId("note-end")).toHaveTextContent("2:30");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(calls.at(-1)).toEqual({
      path: `/sessions/${meta.id}/notes/n1`, method: "PATCH", body: { text: "Misfire", tags: [], t: 120_000, t_end: 150_000 },
    }));
    expect(replay.refreshNotes).toHaveBeenCalled();

    fireEvent.click(screen.getAllByRole("button", { name: "Edit note" })[1]!);
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    await waitFor(() => expect(calls.at(-1)).toEqual({ path: `/sessions/${meta.id}/notes/n2`, method: "DELETE" }));
  });

  it("rejects a range that ends before it starts", () => {
    withReplay(<NotesPanel />, { notes: NOTES, t: 100_000 });
    fireEvent.click(screen.getAllByRole("button", { name: "Edit note" })[0]!);
    fireEvent.click(screen.getByRole("button", { name: "Make a range to cursor" }));
    expect(screen.getByRole("alert")).toHaveTextContent("The end must be after the start");
    expect(screen.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("opens the editor on request (a chart marker or a dragged range)", () => {
    const done = vi.fn();
    withReplay(<NotesPanel request={{ t: 10_000, t_end: 20_000 }} onRequestDone={done} />, { notes: NOTES });
    expect(screen.getByText("Add note")).toBeInTheDocument();
    expect(screen.getByTestId("note-end")).toHaveTextContent("0:20");
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(done).toHaveBeenCalled();
  });

  it("is read-only on a demo session", () => {
    withReplay(<NotesPanel />, { notes: NOTES, session: { ...meta, synthetic: true } });
    expect(screen.getByRole("button", { name: "+ Add note at cursor" })).toBeDisabled();
    fireEvent.click(screen.getAllByRole("button", { name: "View note" })[1]!);
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.getAllByText("Demo sessions can't be annotated.").length).toBeGreaterThan(0);
  });

  it("renders nothing outside replay", () => {
    renderWithApp(<NotesPanel />);
    expect(screen.queryByLabelText("Notes")).toBeNull();
  });
});

/* ---- replay audio ---- */

describe("ReplayAudio", () => {
  let play: ReturnType<typeof vi.fn>, pause: ReturnType<typeof vi.fn>;
  beforeEach(() => {
    let paused = true;
    play = vi.fn(function () { paused = false; return Promise.resolve(); });
    pause = vi.fn(function () { paused = true; });
    vi.spyOn(HTMLMediaElement.prototype, "play").mockImplementation(play as unknown as () => Promise<void>);
    vi.spyOn(HTMLMediaElement.prototype, "pause").mockImplementation(pause as unknown as () => void);
    vi.spyOn(HTMLMediaElement.prototype, "paused", "get").mockImplementation(() => paused);
  });

  const audioEl = () => document.querySelector("audio[data-track=trk1]") as HTMLAudioElement;

  it("renders nothing for a session without audio", () => {
    withReplay(<ReplayAudio />, { session: { ...meta, audio: [] } });
    expect(document.querySelector("audio")).toBeNull();
  });

  it("follows the cursor: seek on jumps, playbackRate at 1×/2×, silent above", () => {
    const { rerenderReplay } = withReplay(<ReplayAudio />, { t: 70_000 });
    const el = audioEl();
    expect(el.getAttribute("src")).toBe(`/sessions/${meta.id}/audio/trk1`);
    expect(el.currentTime).toBe(60);
    expect(play).not.toHaveBeenCalled();
    const sameElement = () => expect(audioEl()).toBe(el);

    rerenderReplay({ t: 70_100, playing: true, speed: 2 });
    expect(el.playbackRate).toBe(2);
    expect(play).toHaveBeenCalledTimes(1);
    expect(el.currentTime).toBe(60); // drift < 0.3 s: no seek

    rerenderReplay({ t: 200_000, playing: true, speed: 2 });
    expect(el.currentTime).toBe(190); // jump → seek

    rerenderReplay({ t: 200_000, playing: true, speed: 4 });
    expect(pause).toHaveBeenCalled();
    expect(screen.getByText("silent above 2×")).toBeInTheDocument();

    rerenderReplay({ t: 5_000, playing: true, speed: 1 }); // before the track starts
    expect(el.paused).toBe(true);
    sameElement();
  });

  it("mute and ±0.5 s offset are kept per device", () => {
    const { rerenderReplay } = withReplay(<ReplayAudio />, { t: 70_000 });
    fireEvent.click(screen.getByRole("button", { name: "Mute audio" }));
    expect(audioEl().muted).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Audio later by 0.5 s" }));
    fireEvent.click(screen.getByRole("button", { name: "Audio later by 0.5 s" }));
    fireEvent.click(screen.getByRole("button", { name: "Audio earlier by 0.5 s" }));
    expect(screen.getByLabelText("Audio offset 0.5 s")).toHaveTextContent("+0.5 s");
    rerenderReplay({ t: 80_000 });
    expect(audioEl().currentTime).toBe(70.5);
    expect(JSON.parse(localStorage.getItem("d2diag.replayAudio")!)).toEqual({ muted: true, offset: 0.5 });
  });
});
