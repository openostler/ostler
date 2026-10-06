// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { describe, expect, it, vi } from "vitest";
import { AudioCapture, BITRATE, chunkUrl, MP4, OPUS, pickMime, TIMESLICE_MS, trackTime, WakeLockKeeper, type AudioDeps } from "./audio";

class FakeRecorder {
  static instances: FakeRecorder[] = [];
  static supported = new Set<string>([OPUS]);
  static isTypeSupported(t: string) { return FakeRecorder.supported.has(t); }
  state = "inactive";
  mimeType: string;
  timeslice?: number;
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onerror: ((e: unknown) => void) | null = null;
  onstop: (() => void) | null = null;
  constructor(public stream: MediaStream, public opts?: { mimeType?: string; audioBitsPerSecond?: number }) {
    this.mimeType = opts?.mimeType ?? "";
    FakeRecorder.instances.push(this);
  }
  start(ts?: number) { this.state = "recording"; this.timeslice = ts; }
  stop() {
    if (this.state === "inactive") return;
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob(["last"]) });
    this.onstop?.();
  }
  emit(bytes: string) { this.ondataavailable?.({ data: new Blob([bytes]) }); }
}

function fakeStream() {
  const listeners: (() => void)[] = [];
  const track = {
    readyState: "live",
    stop: vi.fn(() => { track.readyState = "ended"; }),
    addEventListener: (_t: string, fn: () => void) => listeners.push(fn),
    removeEventListener: () => undefined,
  };
  return {
    stream: { getAudioTracks: () => [track], getTracks: () => [track] } as unknown as MediaStream,
    track,
    end: () => { track.readyState = "ended"; listeners.forEach((f) => f()); },
  };
}

function setup(over: Partial<AudioDeps> = {}) {
  FakeRecorder.instances = [];
  let vis = "visible";
  const visListeners = new Set<() => void>();
  let n = 0;
  const streams: ReturnType<typeof fakeStream>[] = [];
  const fetch = vi.fn(async (_u: string, _i?: RequestInit) => new Response("{}", { status: 200 }));
  const release = vi.fn(async () => undefined);
  const sentinels: { release: typeof release; released: boolean }[] = [];
  const request = vi.fn(async () => { const s = { release, released: false }; sentinels.push(s); return s; });
  const deps: AudioDeps = {
    getUserMedia: vi.fn(async () => { const s = fakeStream(); streams.push(s); return s.stream; }),
    MediaRecorder: FakeRecorder as unknown as AudioDeps["MediaRecorder"],
    fetch: fetch as unknown as typeof globalThis.fetch,
    now: () => 1_791_000_000_000 + n * 1000,
    uuid: () => `track-${++n}`,
    wakeLock: { request },
    doc: {
      get visibilityState() { return vis; },
      addEventListener: (_t, fn) => visListeners.add(fn),
      removeEventListener: (_t, fn) => visListeners.delete(fn),
    },
    sleep: async () => undefined,
    ...over,
  };
  // Browsers release the screen wake lock whenever the page is hidden.
  const setVisible = (v: string) => { vis = v; if (v === "hidden") sentinels.forEach((s) => { s.released = true; }); visListeners.forEach((f) => f()); };
  return { deps, fetch, request, release, streams, setVisible };
}

const rec = () => FakeRecorder.instances[FakeRecorder.instances.length - 1]!;

describe("pickMime / chunkUrl", () => {
  it("prefers Opus/WebM, then MP4, else the browser default", () => {
    expect(pickMime((t) => t === OPUS || t === MP4)).toBe(OPUS);
    expect(pickMime((t) => t === MP4)).toBe(MP4);
    expect(pickMime(() => false)).toBe("");
    expect(pickMime(() => { throw new Error("x"); })).toBe("");
  });
  it("sends start only on seq 0", () => {
    expect(chunkUrl("S1", "abc", 0, OPUS, 1234.4)).toBe("/sessions/S1/audio?track=abc&seq=0&mime=audio%2Fwebm%3Bcodecs%3Dopus&start=1234");
    expect(chunkUrl("S1", "abc", 3, MP4, 1234)).toBe("/sessions/S1/audio?track=abc&seq=3&mime=audio%2Fmp4");
  });
  it("trackTime maps the cursor into a track (session ms) with offset", () => {
    expect(trackTime({ start_ms: 10_000, end_ms: 70_000 }, 25_000, 0)).toBe(15);
    expect(trackTime({ start_ms: 10_000, end_ms: 70_000 }, 25_000, 0.5)).toBe(15.5);
    expect(trackTime({ start_ms: 10_000, end_ms: 70_000 }, 5_000, 0)).toBeNull();
    expect(trackTime({ start_ms: 10_000, end_ms: 70_000 }, 80_000, 0)).toBeNull();
    expect(trackTime({ start_ms: 10_000 }, 10_100, -0.5)).toBeNull();
  });
});

describe("AudioCapture with a fake MediaRecorder", () => {
  it("arms (mic + wake lock), records 5 s chunks at 24 kbps and POSTs them in order", async () => {
    const f = setup();
    const a = new AudioCapture(f.deps);
    expect(await a.arm()).toBe(true);
    expect(a.state.status).toBe("armed");
    expect(f.request).toHaveBeenCalledWith("screen");
    expect(FakeRecorder.instances).toHaveLength(0);

    a.setSession("S1");
    expect(a.state.status).toBe("recording");
    expect(rec().opts).toEqual({ mimeType: OPUS, audioBitsPerSecond: BITRATE });
    expect(rec().timeslice).toBe(TIMESLICE_MS);
    rec().emit("aaaa");
    rec().emit("bb");
    await a.drain();
    expect(f.fetch).toHaveBeenCalledTimes(2);
    const [u0, i0] = f.fetch.mock.calls[0]!;
    const [u1] = f.fetch.mock.calls[1]!;
    expect(u0).toMatch(/^\/sessions\/S1\/audio\?track=track-1&seq=0&mime=audio%2Fwebm%3Bcodecs%3Dopus&start=\d+$/);
    expect(u1).toMatch(/seq=1&mime=[^&]+$/);
    expect(i0!.method).toBe("POST");
    expect(i0!.body).toBeInstanceOf(Blob);
    expect((i0!.headers as Record<string, string>)["Content-Type"]).toBe(OPUS);
    expect(a.state).toMatchObject({ chunks: 2, bytes: 6, track: "track-1" });
  });

  it("falls back to MP4 (iOS)", async () => {
    FakeRecorder.supported = new Set([MP4]);
    const f = setup();
    const a = new AudioCapture(f.deps);
    a.setSession("S1");
    await a.arm();
    expect(rec().opts?.mimeType).toBe(MP4);
    FakeRecorder.supported = new Set([OPUS]);
  });

  it("reports lost when the page is hidden, then re-acquires mic and lock on a new track", async () => {
    const f = setup();
    const a = new AudioCapture(f.deps);
    await a.arm();
    a.setSession("S1");
    const first = rec();
    f.setVisible("hidden");
    expect(a.state.status).toBe("lost");
    expect(first.state).toBe("inactive");
    expect(f.streams[0]!.track.stop).toHaveBeenCalled();
    await a.drain(); // the final chunk is still uploaded
    expect(f.fetch.mock.calls.some(([u]) => String(u).includes("track=track-1"))).toBe(true);

    f.setVisible("visible");
    await vi.waitFor(() => expect(a.state.status).toBe("recording"));
    expect(f.deps.getUserMedia).toHaveBeenCalledTimes(2);
    expect(f.request).toHaveBeenCalledTimes(2);
    expect(a.state.track).toBe("track-2");
    rec().emit("x");
    await a.drain();
    expect(String(f.fetch.mock.calls.at(-1)![0])).toMatch(/track=track-2&seq=0&.*start=/);
  });

  it("reports lost when the mic track ends", async () => {
    const f = setup();
    const a = new AudioCapture(f.deps);
    await a.arm();
    a.setSession("S1");
    f.streams[0]!.end();
    expect(a.state.status).toBe("lost");
  });

  it("a new session starts a new track; no session stops it", async () => {
    const f = setup();
    const a = new AudioCapture(f.deps);
    await a.arm();
    a.setSession("S1");
    a.setSession("S2");
    expect(FakeRecorder.instances).toHaveLength(2);
    expect(FakeRecorder.instances[0]!.state).toBe("inactive");
    expect(a.state.status).toBe("recording");
    a.setSession(null);
    expect(rec().state).toBe("inactive");
    expect(a.state.status).toBe("armed");
  });

  it("refused mic → denied, nothing recorded", async () => {
    const f = setup({ getUserMedia: async () => { throw Object.assign(new Error("no"), { name: "NotAllowedError" }); } });
    const a = new AudioCapture(f.deps);
    expect(await a.arm()).toBe(false);
    expect(a.state.status).toBe("denied");
    a.setSession("S1");
    expect(FakeRecorder.instances).toHaveLength(0);
  });

  it("retries a failed upload, and gives up on a 4xx", async () => {
    const fetch = vi.fn()
      .mockRejectedValueOnce(new Error("net"))
      .mockResolvedValueOnce(new Response("{}", { status: 200 }))
      .mockResolvedValueOnce(new Response("{}", { status: 403 }));
    const f = setup({ fetch: fetch as unknown as typeof globalThis.fetch });
    const a = new AudioCapture(f.deps);
    await a.arm();
    a.setSession("S1");
    rec().emit("a");
    rec().emit("b");
    await a.drain();
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(a.state.chunks).toBe(1);
    expect(a.state.error).toMatch(/403/);
  });

  it("disarm stops everything and releases the wake lock", async () => {
    const f = setup();
    const a = new AudioCapture(f.deps);
    await a.arm();
    a.setSession("S1");
    await a.disarm();
    expect(rec().state).toBe("inactive");
    expect(f.release).toHaveBeenCalled();
    expect(a.state.status).toBe("off");
  });
});

describe("WakeLockKeeper", () => {
  it("is a no-op without the API and re-acquires only when wanted", async () => {
    expect(await new WakeLockKeeper(undefined).acquire()).toBe(false);
    const request = vi.fn(async () => ({ release: async () => undefined, released: false }));
    const k = new WakeLockKeeper({ request });
    expect(await k.reacquire()).toBe(false);
    await k.acquire();
    await k.release();
    expect(await k.reacquire()).toBe(false);
    expect(request).toHaveBeenCalledTimes(1);
  });
});
