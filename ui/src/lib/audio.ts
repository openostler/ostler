// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Phone cabin audio (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md §3).
 *
 * MediaRecorder at 24 kbps Opus (WebM) where supported, else AAC in MP4 (iOS Safari), with a
 * 5 s timeslice. Each chunk is POSTed raw to
 *   /sessions/<id>/audio?track=<uuid>&seq=<n>&mime=<type>&start=<epoch ms, seq 0 only>
 * in order (one upload at a time, a few retries; the server re-orders up to 10 chunks).
 *
 * Browsers stop the mic when the page is hidden, so the recorder reports "lost" and, when the
 * page is visible again, re-acquires the mic and the screen Wake Lock and starts a new track.
 * All browser globals come in through `AudioDeps` so tests drive a fake MediaRecorder.
 */

export const OPUS = "audio/webm;codecs=opus";
export const MP4 = "audio/mp4";
export const BITRATE = 24_000;
export const TIMESLICE_MS = 5_000;

/** The first supported container: Opus/WebM, then MP4/AAC, else "" (browser default). */
export function pickMime(isTypeSupported: (t: string) => boolean): string {
  try {
    if (isTypeSupported(OPUS)) return OPUS;
    if (isTypeSupported(MP4)) return MP4;
  } catch {
    /* some browsers throw on unknown types */
  }
  return "";
}

/** Query string for one chunk upload. `start` (epoch ms) is sent only on seq 0. */
export function chunkUrl(session: string, track: string, seq: number, mime: string, startMs: number): string {
  const q = new URLSearchParams({ track, seq: String(seq), mime });
  if (seq === 0) q.set("start", String(Math.round(startMs)));
  return `/sessions/${encodeURIComponent(session)}/audio?${q.toString()}`;
}

/* ------------------------------------------------------------------ replay sync */

/** Where `el` should be (s into the track) for cursor `t` (session ms), or null if outside it. */
export function trackTime(tr: { start_ms: number; end_ms?: number | null }, t: number, offsetS: number, utcOffset: number | null = null): number | null {
  // start_ms is session ms; tolerate an epoch value from an older recorder.
  const start = tr.start_ms > 1e11 && utcOffset != null ? tr.start_ms - utcOffset : tr.start_ms;
  const end = tr.end_ms == null ? null : tr.end_ms > 1e11 && utcOffset != null ? tr.end_ms - utcOffset : tr.end_ms;
  if (t < start || (end != null && t > end)) return null;
  const s = (t - start) / 1000 + offsetS;
  return s < 0 ? null : s;
}

/* ------------------------------------------------------------------ wake lock */

type Sentinel = { release(): Promise<void>; released?: boolean; addEventListener?: (t: "release", fn: () => void) => void };
type WakeLockApi = { request(type: "screen"): Promise<Sentinel> };

/** Holds the screen awake while capture runs; re-acquire after the page is visible again. */
export class WakeLockKeeper {
  private sentinel: Sentinel | null = null;
  private want = false;
  constructor(private api: WakeLockApi | undefined) {}
  get held(): boolean { return !!this.sentinel && !this.sentinel.released; }
  async acquire(): Promise<boolean> {
    this.want = true;
    if (!this.api) return false;
    if (this.held) return true;
    try {
      this.sentinel = await this.api.request("screen");
      return true;
    } catch {
      return false; // refused (low battery, hidden page) — capture still runs
    }
  }
  /** Re-request if we still want it (the browser drops it whenever the page is hidden). */
  async reacquire(): Promise<boolean> {
    return this.want ? this.acquire() : false;
  }
  async release(): Promise<void> {
    this.want = false;
    const s = this.sentinel;
    this.sentinel = null;
    try { await s?.release(); } catch { /* already released */ }
  }
}

/* ------------------------------------------------------------------ recorder */

export type AudioStatus = "off" | "armed" | "recording" | "lost" | "denied" | "error";
export type AudioState = {
  status: AudioStatus;
  mime: string;
  track: string | null;
  /** Chunks uploaded on this track. */
  chunks: number;
  bytes: number;
  error?: string;
};

interface RecorderLike {
  state: string;
  mimeType: string;
  ondataavailable: ((e: { data: Blob }) => void) | null;
  onerror: ((e: unknown) => void) | null;
  onstop: (() => void) | null;
  start(timeslice?: number): void;
  stop(): void;
}
type RecorderCtor = {
  new (stream: MediaStream, opts?: { mimeType?: string; audioBitsPerSecond?: number }): RecorderLike;
  isTypeSupported(t: string): boolean;
};

export interface AudioDeps {
  getUserMedia?: (c: MediaStreamConstraints) => Promise<MediaStream>;
  MediaRecorder?: RecorderCtor;
  fetch: typeof fetch;
  now: () => number;
  uuid: () => string;
  wakeLock?: WakeLockApi;
  /** visibilitychange source (document). */
  doc?: { visibilityState: string; addEventListener(t: "visibilitychange", fn: () => void): void; removeEventListener(t: "visibilitychange", fn: () => void): void };
  sleep: (ms: number) => Promise<void>;
}

const uuid4 = () => {
  const c = globalThis.crypto as Crypto | undefined;
  if (c?.randomUUID) return c.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (ch) => {
    const r = (Math.random() * 16) | 0;
    return (ch === "x" ? r : (r & 3) | 8).toString(16);
  });
};

export function browserAudioDeps(): AudioDeps {
  const nav = typeof navigator !== "undefined" ? navigator : undefined;
  const MR = (globalThis as { MediaRecorder?: RecorderCtor }).MediaRecorder;
  return {
    getUserMedia: nav?.mediaDevices?.getUserMedia ? (c) => nav.mediaDevices.getUserMedia(c) : undefined,
    MediaRecorder: MR,
    fetch: (...a) => fetch(...a),
    now: () => Date.now(),
    uuid: uuid4,
    wakeLock: (nav as { wakeLock?: WakeLockApi } | undefined)?.wakeLock,
    doc: typeof document !== "undefined" ? document : undefined,
    sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
  };
}

/** Why the phone mic can't be used here, or null when it can. */
export function audioUnavailable(): string | null {
  if (typeof window === "undefined") return "Not in a browser";
  if (!window.isSecureContext) return "Needs HTTPS — see the HTTPS guide";
  if (!navigator.mediaDevices?.getUserMedia) return "This browser can't use the microphone";
  if (!("MediaRecorder" in window)) return "This browser can't record audio";
  return null;
}

/**
 * The phone audio recorder. `arm()` from a tap (mic permission + wake lock), then
 * `setSession(id)` as the recording session changes; it records while armed with a session.
 */
export class AudioCapture {
  private deps: AudioDeps;
  private listeners = new Set<(s: AudioState) => void>();
  private st: AudioState = { status: "off", mime: "", track: null, chunks: 0, bytes: 0 };
  private stream: MediaStream | null = null;
  private rec: RecorderLike | null = null;
  private session: string | null = null;
  private seq = 0;
  private startMs = 0;
  private queue: Promise<void> = Promise.resolve();
  private armed = false;
  readonly wake: WakeLockKeeper;

  constructor(deps?: AudioDeps) {
    this.deps = deps ?? browserAudioDeps();
    this.wake = new WakeLockKeeper(this.deps.wakeLock);
  }

  get state(): AudioState { return this.st; }
  getState = () => this.st;
  subscribe = (fn: (s: AudioState) => void) => {
    this.listeners.add(fn);
    return () => { this.listeners.delete(fn); };
  };
  private set(patch: Partial<AudioState>) {
    this.st = { ...this.st, ...patch };
    for (const fn of this.listeners) fn(this.st);
  }

  /** Ask for the mic and the wake lock. Call from the tap handler (before other awaits). */
  async arm(): Promise<boolean> {
    if (!this.deps.getUserMedia || !this.deps.MediaRecorder) {
      this.set({ status: "error", error: "This browser can't record audio" });
      return false;
    }
    const micP = this.acquireMic();
    void this.wake.acquire();
    const ok = await micP;
    if (!ok) return false;
    this.armed = true;
    this.deps.doc?.addEventListener("visibilitychange", this.onVisibility);
    if (this.session) this.startTrack();
    else this.set({ status: "armed", error: undefined });
    return true;
  }

  private async acquireMic(): Promise<boolean> {
    if (this.stream && this.stream.getAudioTracks().some((t) => t.readyState === "live")) return true;
    try {
      this.stream = await this.deps.getUserMedia!({
        audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true, channelCount: 1 },
      });
      for (const t of this.stream.getAudioTracks()) t.addEventListener?.("ended", this.onEnded);
      return true;
    } catch (e) {
      const denied = (e as { name?: string })?.name === "NotAllowedError";
      this.set({ status: denied ? "denied" : "error", error: denied ? "Microphone access was refused" : "The microphone could not start" });
      return false;
    }
  }

  async disarm(): Promise<void> {
    this.armed = false;
    this.deps.doc?.removeEventListener("visibilitychange", this.onVisibility);
    this.stopTrack();
    this.releaseMic();
    await this.wake.release();
    this.set({ status: "off", track: null });
  }

  setSession(id: string | null) {
    if (id === this.session) return;
    this.stopTrack();
    this.session = id;
    if (this.armed && id && this.stream) this.startTrack();
    else if (this.armed) this.set({ status: id ? this.st.status : "armed" });
  }

  private startTrack() {
    const MR = this.deps.MediaRecorder!;
    const mime = pickMime((t) => MR.isTypeSupported(t));
    let rec: RecorderLike;
    try {
      rec = new MR(this.stream!, { ...(mime ? { mimeType: mime } : {}), audioBitsPerSecond: BITRATE });
    } catch {
      this.set({ status: "error", error: "The recorder could not start" });
      return;
    }
    const track = this.deps.uuid();
    const session = this.session!;
    this.rec = rec;
    this.seq = 0;
    this.startMs = this.deps.now();
    const type = rec.mimeType || mime || "audio/webm";
    rec.ondataavailable = (e) => {
      if (!e.data || e.data.size === 0) return;
      this.enqueue(session, track, this.seq++, type, e.data);
    };
    rec.onerror = () => { if (this.rec === rec) this.lost("The recorder stopped"); };
    rec.onstop = () => { if (this.rec === rec && this.armed) this.lost(); };
    rec.start(TIMESLICE_MS);
    this.set({ status: "recording", mime: type, track, chunks: 0, bytes: 0, error: undefined });
  }

  private stopTrack() {
    const rec = this.rec;
    this.rec = null; // detach first so onstop doesn't report "lost"
    if (rec && rec.state !== "inactive") {
      try { rec.stop(); } catch { /* already stopped */ }
    }
  }

  private releaseMic() {
    for (const t of this.stream?.getTracks() ?? []) {
      t.removeEventListener?.("ended", this.onEnded);
      t.stop();
    }
    this.stream = null;
  }

  private lost(error = "Audio stopped while the screen was off") {
    this.stopTrack();
    this.releaseMic();
    this.set({ status: "lost", error });
  }

  private onEnded = () => { if (this.armed) this.lost("The microphone was taken away"); };

  private onVisibility = () => {
    if (!this.armed) return;
    if (this.deps.doc?.visibilityState === "hidden") {
      // Most phones cut the mic here; flush what we have and report it honestly.
      if (this.rec) this.lost();
      return;
    }
    void this.resume();
  };

  /** Re-acquire the mic and wake lock and start a fresh track (after "lost"). */
  async resume(): Promise<boolean> {
    if (!this.armed) return false;
    void this.wake.reacquire();
    if (this.rec && this.rec.state === "recording") return true;
    if (!(await this.acquireMic())) return false;
    if (this.session) this.startTrack();
    else this.set({ status: "armed", error: undefined });
    return true;
  }

  private enqueue(session: string, track: string, seq: number, mime: string, blob: Blob) {
    const start = this.startMs;
    this.queue = this.queue.then(() => this.upload(session, track, seq, mime, start, blob));
  }

  private async upload(session: string, track: string, seq: number, mime: string, start: number, blob: Blob) {
    const url = chunkUrl(session, track, seq, mime, start);
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const r = await this.deps.fetch(url, { method: "POST", headers: { "Content-Type": mime }, body: blob });
        if (r.ok) {
          if (this.st.track === track) this.set({ chunks: this.st.chunks + 1, bytes: this.st.bytes + blob.size });
          return;
        }
        if (r.status >= 400 && r.status < 500) {
          this.set({ error: `audio upload refused (HTTP ${r.status})` });
          return;
        }
      } catch {
        /* network blip — retry */
      }
      await this.deps.sleep(1000 * (attempt + 1));
    }
    this.set({ error: "audio upload failed — check the connection to the Pi" });
  }

  /** Resolves when every queued chunk has been sent (tests). */
  drain(): Promise<void> { return this.queue; }
}

let shared: AudioCapture | null = null;
/** The one phone audio recorder for this page. */
export function phoneAudio(): AudioCapture {
  if (!shared) shared = new AudioCapture();
  return shared;
}
/** Tests: replace (or clear) the shared recorder. */
export function setPhoneAudio(a: AudioCapture | null) { shared = a; }
