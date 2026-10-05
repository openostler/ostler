import { describe, expect, it, vi } from "vitest";
import {
  calibrationMatrix, decimate, Decimator, defaultForwardYaw, forwardFromDrive, forwardYaw, levelMatrix, meanVec,
  MotionCapture, mulMV, postCalibration, rotZ, toVehicleG, type Mat3, type MotionDeps, type Sample, type Vec3,
} from "./motion";

const G = 9.80665;
const close = (a: readonly number[], b: readonly number[], eps = 1e-6) =>
  a.forEach((x, i) => expect(x).toBeCloseTo(b[i]!, -Math.log10(eps)));
const isRotation = (m: Mat3) => {
  // rows orthonormal and det = +1
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    const d = m[i]![0] * m[j]![0] + m[i]![1] * m[j]![1] + m[i]![2] * m[j]![2];
    expect(d).toBeCloseTo(i === j ? 1 : 0, 5);
  }
  const det = m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  expect(det).toBeCloseTo(1, 5);
};

describe("levelMatrix", () => {
  it("is the identity for a phone lying flat, screen up", () => {
    close(levelMatrix([0, 0, G]).flat(), [1, 0, 0, 0, 1, 0, 0, 0, 1]);
  });

  it.each<[string, Vec3]>([
    ["upright in a dash mount", [0, G, 0]],
    ["landscape", [G, 0, 0]],
    ["tilted back 30°", [0, G * Math.sin(Math.PI / 6), G * Math.cos(Math.PI / 6)]],
    ["screen down", [0, 0, -G]],
    ["odd angle", [3.1, -4.2, 7.9]],
  ])("rotates the gravity reading onto +Z (%s)", (_name, g) => {
    const m = levelMatrix(g);
    isRotation(m);
    const out = mulMV(m, g);
    close(out, [0, 0, Math.hypot(...g)], 1e-5);
  });

  it("refuses a missing gravity reading", () => {
    expect(() => levelMatrix([0, 0, 0])).toThrow(/gravity/);
  });
});

describe("forward yaw", () => {
  it("defaults to 'into the screen' for an upright phone", () => {
    const level = levelMatrix([0, G, 0]); // upright: top up, screen faces the driver
    const m = mulMV(rotZ(-defaultForwardYaw(level)), mulMV(level, [0, 0, -1]));
    close(m, [1, 0, 0], 1e-6); // into the screen → vehicle forward
  });

  it("defaults to the phone's top for a phone lying flat", () => {
    const m = calibrationMatrix([0, 0, G]);
    close(mulMV(m, [0, 1, 0]), [1, 0, 0]);
  });

  it("finds forward from the mean horizontal acceleration", () => {
    expect(forwardYaw([[0, 2, 0], [0, 2.2, 0]])).toBeCloseTo(Math.PI / 2, 5);
    expect(forwardYaw([[0.1, 0.1, 0]])).toBeNull(); // too weak
    expect(forwardYaw([])).toBeNull();
  });

  it("forwardFromDrive keeps only samples while GPS speed rises", () => {
    const level = levelMatrix([0, 0, G]);
    // phone flat, rotated so its −X points forward: accelerating reads −X
    const speeds: [number, number][] = [[0, 0], [1000, 0], [2000, 7.2], [3000, 14.4], [4000, 14.4]];
    const samples: Sample[] = [];
    for (let t = 0; t <= 4000; t += 100) {
      const accel = t > 1000 && t <= 3000 ? -2 : 0;
      const noise = t <= 1000 || t > 3000 ? 3 : 0; // braking/bumps outside the window are ignored
      samples.push([t, accel + (t > 3000 ? noise : 0), 0, G]);
    }
    const yaw = forwardFromDrive(samples, speeds, level);
    expect(yaw).not.toBeNull();
    const m = calibrationMatrix([0, 0, G], yaw);
    close(mulMV(m, [-1, 0, 0]), [1, 0, 0], 1e-5);
    expect(forwardFromDrive(samples, [[0, 10], [1000, 10]], level)).toBeNull(); // steady speed
  });
});

describe("vehicle-frame sign conventions", () => {
  // Phone upright in a dash mount facing the driver: device +Y up, device −Z forward,
  // so device +X is the driver's right → vehicle −Y (left is +Y).
  const m = calibrationMatrix([0, G, 0]);
  it("is a proper rotation", () => isRotation(m));
  it("at rest reads 0 g inline/lateral/vertical", () => {
    const v = toVehicleG(m, [0, G, 0]);
    expect(v.inline).toBeCloseTo(0, 6);
    expect(v.lateral).toBeCloseTo(0, 6);
    expect(v.vertical).toBeCloseTo(0, 6);
  });
  it("accelerating forward is +inline", () => {
    // reaction force pushes back into the seat: the sensor reads +a along forward (−Z)
    expect(toVehicleG(m, [0, G, -G * 0.3]).inline).toBeCloseTo(0.3, 5);
  });
  it("a left turn is +lateral", () => {
    // turning left, centripetal acceleration points left = device −X
    expect(toVehicleG(m, [-G * 0.4, G, 0]).lateral).toBeCloseTo(0.4, 5);
  });
  it("a bump upward is +vertical", () => {
    expect(toVehicleG(m, [0, G * 1.2, 0]).vertical).toBeCloseTo(0.2, 5);
  });
});

describe("decimation", () => {
  it.each([10, 25, 50])("turns a 60 Hz stream into ~%i Hz", (rate) => {
    const s: Sample[] = Array.from({ length: 600 }, (_, i) => [i * (1000 / 60), 0, 0, G]); // 10 s
    const out = decimate(s, rate);
    expect(out.length).toBeGreaterThanOrEqual(rate * 10 - 2);
    expect(out.length).toBeLessThanOrEqual(rate * 10 + 1);
  });
  it("never upsamples a slow sensor", () => {
    const d = new Decimator(50);
    const kept = Array.from({ length: 100 }, (_, i) => d.accept(i * 100)).filter(Boolean).length;
    expect(kept).toBe(100);
  });
  it("meanVec reports the spread", () => {
    expect(meanVec([[0, 0, 1], [0, 0, 3]])).toEqual({ mean: [0, 0, 2], sd: 1 });
  });
});

/* ---- browser glue with a fake DeviceMotion ---- */

function fakeDeps(over: Partial<MotionDeps> = {}) {
  let handler: ((e: DeviceMotionEvent) => void) | null = null;
  let now = 1_000_000;
  const intervals: (() => void)[] = [];
  const timeouts: { fn: () => void; at: number }[] = [];
  const fetch = vi.fn(async (_u: string, _i?: RequestInit) => new Response("{}", { status: 200 }));
  const deps: MotionDeps = {
    addListener: (fn) => { handler = fn; },
    removeListener: () => { handler = null; },
    fetch: fetch as unknown as typeof globalThis.fetch,
    now: () => now,
    setInterval: (fn) => { intervals.push(fn); return intervals.length; },
    clearInterval: () => { intervals.length = 0; },
    setTimeout: (fn, ms) => { timeouts.push({ fn, at: now + ms }); return timeouts.length; },
    ...over,
  };
  const emit = (v: Vec3, dtMs = 1000 / 60) => {
    now += dtMs;
    handler?.({ accelerationIncludingGravity: { x: v[0], y: v[1], z: v[2] } } as unknown as DeviceMotionEvent);
    for (const t of [...timeouts]) if (t.at <= now) { timeouts.splice(timeouts.indexOf(t), 1); t.fn(); }
  };
  return { deps, fetch, emit, tick: () => intervals.forEach((f) => f()), listening: () => handler != null };
}

describe("MotionCapture", () => {
  it("asks iOS permission on arm and stays off when refused", async () => {
    const f = fakeDeps({ requestPermission: async () => "denied" });
    const m = new MotionCapture(f.deps);
    expect(await m.arm(25)).toBe(false);
    expect(m.state.status).toBe("denied");
    expect(f.listening()).toBe(false);
  });

  it("decimates to the rate and posts a batch every second", async () => {
    const f = fakeDeps({ requestPermission: async () => "granted" });
    const m = new MotionCapture(f.deps);
    expect(await m.arm(10)).toBe(true);
    expect(m.state.status).toBe("armed");
    for (let i = 0; i < 30; i++) f.emit([0, G, 0]); // no session yet: dropped
    m.setSession("S1");
    expect(m.state.status).toBe("recording");
    for (let i = 0; i < 60; i++) f.emit([0.1, G, -0.2]); // 1 s at 60 Hz
    f.tick();
    await m.flush();
    expect(f.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = f.fetch.mock.calls[0]!;
    expect(url).toBe("/sessions/S1/accel");
    const body = JSON.parse(String(init!.body)) as { source: string; samples: Sample[] };
    expect(body.source).toBe("phone");
    expect(body.samples.length).toBeGreaterThanOrEqual(9);
    expect(body.samples.length).toBeLessThanOrEqual(11);
    expect(body.samples[0]).toEqual([expect.any(Number), 0.1, 9.807, -0.2]);
    m.disarm();
    expect(f.listening()).toBe(false);
  });

  it("measureStill levels from 2 s at rest and rejects movement", async () => {
    const f = fakeDeps();
    const m = new MotionCapture(f.deps);
    const p = m.measureStill(2000);
    for (let i = 0; i < 130; i++) f.emit([0, G, 0.01 * (i % 2)]);
    const { level } = await p;
    close(mulMV(level, [0, G, 0]), [0, 0, G], 1e-2);

    const q = m.measureStill(2000);
    for (let i = 0; i < 130; i++) f.emit([i % 2 ? 2 : -2, G, 0]);
    await expect(q).rejects.toThrow(/hold it still/);
  });

  it("postCalibration sends the matrix with source phone", async () => {
    const fetch = vi.fn(async () => new Response("{}", { status: 200 }));
    const ok = await postCalibration("S 1", { matrix: calibrationMatrix([0, G, 0]), method: "level" }, fetch as unknown as typeof globalThis.fetch);
    expect(ok).toBe(true);
    const [url, init] = (fetch.mock.calls[0] as unknown as [string, RequestInit]);
    expect(url).toBe("/sessions/S%201/accel_cal");
    const body = JSON.parse(String(init.body));
    expect(body).toMatchObject({ source: "phone", method: "level" });
    expect(body.matrix).toHaveLength(3);
  });
});
