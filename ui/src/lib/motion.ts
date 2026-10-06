// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Phone accelerometer capture (ADR-0010, specs/2026-10-05-replay-notes-capture-design.md §3).
 *
 * DeviceMotion `accelerationIncludingGravity` (m/s², device frame) is decimated to the chosen
 * rate and POSTed every second to /sessions/<id>/accel as {source:"phone", samples}. The server
 * rotates it into the vehicle frame with the stored calibration matrix (POST …/accel_cal):
 * X forward (inline, + when accelerating), Y left (lateral, + in a left turn), Z up.
 *
 * The maths (levelling, forward yaw, decimation) is pure and unit-tested; the browser glue
 * takes its globals through `MotionDeps` so tests can drive a fake DeviceMotion.
 */

export type Vec3 = [number, number, number];
export type Mat3 = [Vec3, Vec3, Vec3];
export type Sample = [number, number, number, number]; // [epoch_ms, ax, ay, az]

export const RATES = [10, 25, 50] as const;
export type Rate = (typeof RATES)[number];

const G = 9.80665;

/* ------------------------------------------------------------------ pure maths */

export const identity = (): Mat3 => [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
export const norm = (v: readonly number[]) => Math.hypot(...v);
const scale = (v: Vec3, k: number): Vec3 => [v[0] * k, v[1] * k, v[2] * k];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];

export function mulMV(m: Mat3, v: Vec3): Vec3 {
  return [dot(m[0], v), dot(m[1], v), dot(m[2], v)];
}

export function mulMM(a: Mat3, b: Mat3): Mat3 {
  const col = (j: 0 | 1 | 2): Vec3 => [b[0][j], b[1][j], b[2][j]];
  const row = (i: 0 | 1 | 2): Vec3 => [dot(a[i], col(0)), dot(a[i], col(1)), dot(a[i], col(2))];
  return [row(0), row(1), row(2)];
}

/** Mean and the largest per-axis standard deviation of a set of vectors. */
export function meanVec(samples: readonly Vec3[]): { mean: Vec3; sd: number } {
  const n = samples.length;
  if (!n) return { mean: [0, 0, 0], sd: Infinity };
  const mean: Vec3 = [0, 0, 0];
  for (const s of samples) for (let i = 0; i < 3; i++) mean[i]! += s[i]! / n;
  let sd = 0;
  for (let i = 0; i < 3; i++) {
    let v = 0;
    for (const s of samples) v += (s[i]! - mean[i]!) ** 2;
    sd = Math.max(sd, Math.sqrt(v / n));
  }
  return { mean, sd };
}

/**
 * The rotation that takes the measured gravity reaction `g` (what accelerationIncludingGravity
 * reads at rest, pointing up) onto vehicle +Z. Rodrigues' formula; a 180° flip about X when
 * `g` points straight down. The yaw about Z is left as-is (see `forwardYaw`).
 */
export function levelMatrix(g: Vec3): Mat3 {
  const n = norm(g);
  if (!(n > 0.5)) throw new Error("No gravity reading — is the phone's motion sensor working?");
  const u = scale(g, 1 / n);
  const z: Vec3 = [0, 0, 1];
  const c = dot(u, z);
  if (c < -0.999999) return [[1, 0, 0], [0, -1, 0], [0, 0, -1]];
  const k = cross(u, z); // axis * sin
  const f = 1 / (1 + c);
  const [x, y, w] = k;
  return [
    [c + x * x * f, x * y * f - w, x * w * f + y],
    [x * y * f + w, c + y * y * f, y * w * f - x],
    [x * w * f - y, y * w * f + x, c + w * w * f],
  ];
}

/** Rotation about Z by `rad`. */
export function rotZ(rad: number): Mat3 {
  const c = Math.cos(rad), s = Math.sin(rad);
  return [[c, -s, 0], [s, c, 0], [0, 0, 1]];
}

/**
 * Default forward without GPS: the phone in a dash holder faces the driver, so "into the
 * screen" (device −Z) points forward; a phone lying flat points its top (+Y) forward.
 * Returns the yaw (radians, in the levelled frame) of that direction.
 */
export function defaultForwardYaw(level: Mat3): number {
  const intoScreen = mulMV(level, [0, 0, -1]);
  const h = Math.hypot(intoScreen[0], intoScreen[1]);
  const v = h > 0.5 ? intoScreen : mulMV(level, [0, 1, 0]);
  return Math.atan2(v[1], v[0]);
}

/**
 * Forward direction from GPS: the mean horizontal acceleration (levelled frame) while GPS
 * speed was rising points forward. `accel` are levelled samples taken while accelerating,
 * `still` the levelled mean at rest (subtracted to cancel residual tilt). Null if too weak.
 */
export function forwardYaw(accel: readonly Vec3[], still: Vec3 = [0, 0, 0], minMs2 = 0.4): number | null {
  if (!accel.length) return null;
  const { mean } = meanVec(accel);
  const hx = mean[0] - still[0], hy = mean[1] - still[1];
  if (Math.hypot(hx, hy) < minMs2) return null;
  return Math.atan2(hy, hx);
}

export const vecOf = (s: Sample): Vec3 => [s[1], s[2], s[3]];

/**
 * Forward yaw from a short drive-off: keep the motion samples that fall between GPS speed
 * readings where speed rose faster than `minAccel` m/s², level them, and average.
 * `speeds` are [epoch_ms, km/h]. Null when there was no clear acceleration.
 */
export function forwardFromDrive(
  samples: readonly Sample[], speeds: readonly [number, number][], level: Mat3, minAccel = 0.5,
): number | null {
  const picked: Vec3[] = [];
  for (let i = 1; i < speeds.length; i++) {
    const [t0, v0] = speeds[i - 1]!, [t1, v1] = speeds[i]!;
    const dt = (t1 - t0) / 1000;
    if (dt <= 0 || ((v1 - v0) / 3.6) / dt < minAccel) continue;
    for (const s of samples) if (s[0] >= t0 && s[0] <= t1) picked.push(mulMV(level, vecOf(s)));
  }
  return forwardYaw(picked);
}

/** The full sensor→vehicle matrix: level, then turn so `yaw` lands on +X (forward). */
export function calibrationMatrix(gravity: Vec3, yaw?: number | null): Mat3 {
  const level = levelMatrix(gravity);
  const y = yaw ?? defaultForwardYaw(level);
  return roundMat(mulMM(rotZ(-y), level));
}

const roundMat = (m: Mat3): Mat3 => m.map((r) => r.map((x) => Math.round(x * 1e6) / 1e6)) as Mat3;

/** Vehicle-frame inline/lateral/vertical in g (vertical has gravity removed). For display/tests. */
export function toVehicleG(m: Mat3, a: Vec3): { inline: number; lateral: number; vertical: number } {
  const [x, y, z] = mulMV(m, a);
  return { inline: x / G, lateral: y / G, vertical: (z - G) / G };
}

/**
 * Keeps a sample only when at least one period has passed since the last kept one
 * (5 % tolerance so a 60 Hz sensor yields a steady 25 Hz without dropping to 20).
 */
export class Decimator {
  private last = -Infinity;
  constructor(public rate: number) {}
  accept(tMs: number): boolean {
    const period = 1000 / this.rate;
    if (tMs - this.last < period * 0.95) return false;
    // stay on the grid so jitter doesn't slowly lower the rate
    this.last = tMs - this.last < period * 2 ? this.last + period : tMs;
    return true;
  }
  reset() { this.last = -Infinity; }
}

/** Decimate a whole recording (pure helper used by tests and the calibration window). */
export function decimate(samples: readonly Sample[], rate: number): Sample[] {
  const d = new Decimator(rate);
  return samples.filter((s) => d.accept(s[0]));
}

/* ------------------------------------------------------------------ browser glue */

type MotionHandler = (e: DeviceMotionEvent) => void;

export interface MotionDeps {
  addListener(fn: MotionHandler): void;
  removeListener(fn: MotionHandler): void;
  /** iOS 13+: DeviceMotionEvent.requestPermission (must run inside a tap). */
  requestPermission?: () => Promise<string>;
  fetch: typeof fetch;
  now: () => number;
  setInterval: (fn: () => void, ms: number) => unknown;
  clearInterval: (id: unknown) => void;
  setTimeout: (fn: () => void, ms: number) => unknown;
}

export function browserMotionDeps(): MotionDeps {
  const DME = (globalThis as { DeviceMotionEvent?: { requestPermission?: () => Promise<string> } }).DeviceMotionEvent;
  return {
    addListener: (fn) => window.addEventListener("devicemotion", fn),
    removeListener: (fn) => window.removeEventListener("devicemotion", fn),
    requestPermission: typeof DME?.requestPermission === "function" ? () => DME.requestPermission!() : undefined,
    fetch: (...a) => fetch(...a),
    now: () => Date.now(),
    setInterval: (fn, ms) => setInterval(fn, ms),
    clearInterval: (id) => clearInterval(id as ReturnType<typeof setInterval>),
    setTimeout: (fn, ms) => setTimeout(fn, ms),
  };
}

/** Why phone motion can't be used here, or null when it can. */
export function motionUnavailable(): string | null {
  if (typeof window === "undefined") return "Not in a browser";
  if (!window.isSecureContext) return "Needs HTTPS — see the HTTPS guide";
  if (!("DeviceMotionEvent" in window)) return "This browser has no motion sensor access";
  return null;
}

export type MotionStatus = "off" | "armed" | "recording" | "denied" | "error";
export type MotionState = { status: MotionStatus; rate: number; sent: number; error?: string };

const readVec = (e: DeviceMotionEvent): Vec3 | null => {
  const a = e.accelerationIncludingGravity;
  if (!a || a.x == null || a.y == null || a.z == null) return null;
  return [a.x, a.y, a.z];
};

const sessionPath = (id: string, leaf: string) => `/sessions/${encodeURIComponent(id)}/${leaf}`;

/**
 * Phone motion recorder. `arm()` from a tap (asks iOS permission), then `setSession(id)` whenever
 * the recording session changes; samples flow while armed and a session is set.
 */
export class MotionCapture {
  private deps: MotionDeps;
  private listeners = new Set<(s: MotionState) => void>();
  private st: MotionState = { status: "off", rate: 25, sent: 0 };
  private session: string | null = null;
  private dec = new Decimator(25);
  private buf: Sample[] = [];
  private timer: unknown = null;
  private listening = false;
  private calWaiters: ((v: Vec3) => void)[] = [];

  constructor(deps?: MotionDeps) {
    this.deps = deps ?? browserMotionDeps();
  }

  get state(): MotionState { return this.st; }
  subscribe = (fn: (s: MotionState) => void) => {
    this.listeners.add(fn);
    return () => { this.listeners.delete(fn); };
  };
  getState = () => this.st;
  private set(patch: Partial<MotionState>) {
    this.st = { ...this.st, ...patch };
    for (const fn of this.listeners) fn(this.st);
  }

  /** Ask for permission (iOS) and start listening. Call synchronously from the tap handler. */
  async arm(rate: number): Promise<boolean> {
    this.setRate(rate);
    if (this.deps.requestPermission) {
      try {
        const r = await this.deps.requestPermission();
        if (r !== "granted") { this.set({ status: "denied", error: "Motion access was refused" }); return false; }
      } catch {
        this.set({ status: "denied", error: "Motion access was refused" });
        return false;
      }
    }
    this.listen();
    this.set({ status: this.session ? "recording" : "armed", error: undefined });
    this.startTimer();
    return true;
  }

  disarm() {
    this.flush();
    this.unlisten();
    this.stopTimer();
    this.set({ status: "off" });
  }

  setRate(rate: number) {
    this.dec = new Decimator(rate);
    this.set({ rate });
  }

  setSession(id: string | null) {
    if (id === this.session) return;
    this.flush();
    this.session = id;
    this.buf = [];
    if (this.st.status === "armed" || this.st.status === "recording") {
      this.set({ status: id ? "recording" : "armed" });
    }
  }

  private onMotion: MotionHandler = (e) => {
    const v = readVec(e);
    if (!v) return;
    if (this.calWaiters.length) for (const w of this.calWaiters) w(v);
    if (!this.session || this.st.status !== "recording") return;
    const t = this.deps.now();
    if (!this.dec.accept(t)) return;
    this.buf.push([t, round3(v[0]), round3(v[1]), round3(v[2])]);
  };

  private listen() {
    if (this.listening) return;
    this.deps.addListener(this.onMotion);
    this.listening = true;
  }
  private unlisten() {
    if (!this.listening) return;
    this.deps.removeListener(this.onMotion);
    this.listening = false;
  }
  private startTimer() {
    if (this.timer != null) return;
    this.timer = this.deps.setInterval(() => this.flush(), 1000);
  }
  private stopTimer() {
    if (this.timer == null) return;
    this.deps.clearInterval(this.timer);
    this.timer = null;
  }

  /** POST the buffered samples (every second). Failures drop the batch — motion is best-effort. */
  flush(): Promise<void> {
    if (!this.session || !this.buf.length) return Promise.resolve();
    const samples = this.buf;
    this.buf = [];
    const n = samples.length;
    return this.deps
      .fetch(sessionPath(this.session, "accel"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: "phone", samples }),
      })
      .then((r) => {
        if (r.ok) this.set({ sent: this.st.sent + n, error: undefined });
        else this.set({ error: `accel upload refused (HTTP ${r.status})` });
      })
      .catch(() => this.set({ error: "accel upload failed (network)" }));
  }

  /**
   * Collect raw vectors for `ms` (listening temporarily if not armed). Used by calibration.
   * Requires permission to have been granted (arm() or a prior grant).
   */
  collect(ms: number): Promise<Sample[]> {
    return new Promise((resolve) => {
      const out: Sample[] = [];
      const wasListening = this.listening;
      this.listen();
      const w = (v: Vec3) => { out.push([this.deps.now(), v[0], v[1], v[2]]); };
      this.calWaiters.push(w);
      this.deps.setTimeout(() => {
        this.calWaiters = this.calWaiters.filter((x) => x !== w);
        if (!wasListening && this.st.status !== "armed" && this.st.status !== "recording") this.unlisten();
        resolve(out);
      }, ms);
    });
  }

  /** Hold still: average gravity over `ms`, reject movement, return the level-only matrix data. */
  async measureStill(ms = 2000): Promise<{ gravity: Vec3; level: Mat3 }> {
    const s = (await this.collect(ms)).map(vecOf);
    if (s.length < 5) throw new Error("No motion readings — allow motion access and try again");
    const { mean, sd } = meanVec(s);
    if (sd > 0.35) throw new Error("The phone moved — hold it still for 2 s and try again");
    return { gravity: mean, level: levelMatrix(mean) };
  }
}

const round3 = (x: number) => Math.round(x * 1000) / 1000;

/** POST the calibration for a session. */
export async function postCalibration(
  sessionId: string,
  cal: { matrix: Mat3; method: "level" | "level+gps" | "manual" },
  doFetch: typeof fetch = (...a) => fetch(...a),
): Promise<boolean> {
  try {
    const r = await doFetch(sessionPath(sessionId, "accel_cal"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ matrix: cal.matrix, source: "phone", method: cal.method }),
    });
    return r.ok;
  } catch {
    return false;
  }
}

/* ------------------------------------------------------------------ stored calibration */

const CAL_KEY = "d2diag.accelCal";
export type StoredCal = { matrix: Mat3; method: "level" | "level+gps" | "manual"; at: string };

export function loadCalibration(): StoredCal | null {
  try {
    const raw = localStorage.getItem(CAL_KEY);
    if (!raw) return null;
    const c = JSON.parse(raw) as StoredCal;
    return Array.isArray(c.matrix) && c.matrix.length === 3 ? c : null;
  } catch {
    return null;
  }
}

export function saveCalibration(c: StoredCal): void {
  try {
    localStorage.setItem(CAL_KEY, JSON.stringify(c));
  } catch {
    /* storage blocked — calibration lasts for this page only */
  }
}

let shared: MotionCapture | null = null;
/** The one phone motion recorder for this page. */
export function phoneMotion(): MotionCapture {
  if (!shared) shared = new MotionCapture();
  return shared;
}
/** Tests: replace (or clear) the shared recorder. */
export function setPhoneMotion(m: MotionCapture | null) { shared = m; }
