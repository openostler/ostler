// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Recording options (per device) and the glue that applies them: server-side sources through
 * POST /command recording_options, phone mic and motion through lib/audio + lib/motion.
 * specs/2026-10-05-replay-notes-capture-design.md §3, §5.
 */
import { useEffect, useRef, useSyncExternalStore } from "react";
import { command } from "../api/client";
import type { RecordingSources } from "../api/schemas";
import { audioUnavailable, phoneAudio, type AudioState } from "./audio";
import { loadCalibration, motionUnavailable, phoneMotion, postCalibration, RATES, type MotionState } from "./motion";

export type AudioChoice = "off" | "phone" | "pi";
export type AccelChoice = "off" | "phone" | "pi" | "gps";
export type RecordingOptionsValue = {
  audio: AudioChoice;
  accel: AccelChoice;
  hz: (typeof RATES)[number];
  /** After "hold still", also find forward from the next drive-off (GPS speed rising). */
  forwardFromGps: boolean;
};

export const DEFAULT_OPTIONS: RecordingOptionsValue = { audio: "off", accel: "off", hz: 25, forwardFromGps: false };
const KEY = "d2diag.recordingOptions";

export function loadOptions(): RecordingOptionsValue {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<RecordingOptionsValue>;
    const o = { ...DEFAULT_OPTIONS, ...raw };
    if (!["off", "phone", "pi"].includes(o.audio)) o.audio = "off";
    if (!["off", "phone", "pi", "gps"].includes(o.accel)) o.accel = "off";
    if (!(RATES as readonly number[]).includes(o.hz)) o.hz = 25;
    return o;
  } catch {
    return DEFAULT_OPTIONS;
  }
}

export function saveOptions(o: RecordingOptionsValue): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(o));
  } catch {
    /* storage blocked — the choice lasts for this page only */
  }
}

/** Reason each choice can't be used right now (null = usable). "off" is always usable. */
export type Availability = {
  audio: Record<AudioChoice, string | null>;
  accel: Record<AccelChoice, string | null>;
};

export function availability(
  sources: RecordingSources | null | undefined,
  env: { audio: string | null; motion: string | null } = { audio: audioUnavailable(), motion: motionUnavailable() },
): Availability {
  const noReport = "The Pi hasn't reported its sources";
  const piAudio = !sources ? noReport
    : sources.pi_audio.state === "unavailable" ? (sources.pi_audio.reason || "No microphone on the Pi") : null;
  const imu = !sources ? noReport
    : sources.imu.state === "unavailable" ? (sources.imu.reason || "No IMU fitted to the Pi") : null;
  const gps = !sources ? noReport : sources.gps === "none" ? "Needs a GPS receiver" : null;
  return {
    audio: { off: null, phone: env.audio, pi: piAudio },
    accel: { off: null, phone: env.motion, pi: imu, gps },
  };
}

/** Plain-English GPS line for the modal and card. */
export function gpsLabel(sources: RecordingSources | null | undefined, fix?: { fix: boolean; sats: number | null } | null): string {
  const kind = sources?.gps ?? (fix ? "usb" : "none");
  if (kind === "none") return "No GPS";
  const name = kind === "mock" ? "GPS (demo)" : "GPS (USB)";
  if (!fix) return `${name} · waiting`;
  return fix.fix ? `${name} · fix${fix.sats != null ? `, ${fix.sats} sats` : ""}` : `${name} · no fix yet`;
}

/**
 * Apply the options. Call from the Apply tap: the iOS motion permission and the mic prompt
 * are requested first, synchronously within the gesture, then the server is told.
 */
export async function applyOptions(o: RecordingOptionsValue, name?: string): Promise<{ ok: boolean; errors: string[] }> {
  const motion = phoneMotion();
  const audio = phoneAudio();
  const motionP = o.accel === "phone" ? motion.arm(o.hz) : (motion.disarm(), Promise.resolve(true));
  const micP = o.audio === "phone" ? audio.arm() : audio.disarm().then(() => true);
  const params: Record<string, unknown> = {
    audio: o.audio === "pi" ? "pi" : "off",
    imu: o.accel === "pi" ? "on" : "off",
    accel_hz: o.hz,
  };
  if (name?.trim()) params.name = name.trim();
  const cmdP = command("recording_options", params).then(
    (r) => (r.ok ? null : r.error ?? "The Pi refused the recording options"),
    () => "Could not reach the Pi",
  );
  const [mOk, aOk, cmdErr] = await Promise.all([motionP, micP, cmdP]);
  saveOptions(o);
  const errors: string[] = [];
  if (!mOk) errors.push(motion.state.error ?? "Motion access was refused");
  if (!aOk) errors.push(audio.state.error ?? "Microphone access was refused");
  if (cmdErr) errors.push(cmdErr);
  return { ok: errors.length === 0, errors };
}

export function usePhoneAudio(): AudioState {
  const a = phoneAudio();
  return useSyncExternalStore(a.subscribe, a.getState, a.getState);
}

export function usePhoneMotion(): MotionState {
  const m = phoneMotion();
  return useSyncExternalStore(m.subscribe, m.getState, m.getState);
}

/**
 * Point phone capture at the session being recorded (null = none). When phone motion is on
 * and a calibration is stored on this device, it is sent to each new session.
 * `hold` (replay) leaves capture untouched.
 */
export function useCaptureRunner(session: string | null, hold = false): void {
  const calSent = useRef<string | null>(null);
  const motionOn = usePhoneMotion().status !== "off";
  useEffect(() => {
    if (hold) return;
    phoneAudio().setSession(session);
    const m = phoneMotion();
    m.setSession(session);
    if (session && motionOn && calSent.current !== session) {
      const cal = loadCalibration();
      calSent.current = session;
      if (cal) void postCalibration(session, cal);
    }
  }, [session, hold, motionOn]);
}
