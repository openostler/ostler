// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef, useState } from "react";
import { forwardFromDrive, calibrationMatrix, phoneMotion, postCalibration, RATES, saveCalibration, loadCalibration, type Mat3 } from "../lib/motion";
import {
  applyOptions, availability, gpsLabel, loadOptions,
  type AccelChoice, type AudioChoice, type RecordingOptionsValue,
} from "../lib/recordingOptions";
import { saveFlagOptions, useFlagOptions, type FlagOptions } from "../lib/flags";
import { useApp } from "../state/app";
import { useSessionFlags } from "../state/flags";
import { useReplay } from "../state/replay";
import "../recording.css";
import { Sheet } from "./Sheet";
import { Icon } from "../icons/Icon";

const AUDIO: { v: AudioChoice; name: string }[] = [
  { v: "off", name: "Off" }, { v: "phone", name: "Phone mic" }, { v: "pi", name: "Pi mic" },
];
const ACCEL: { v: AccelChoice; name: string }[] = [
  { v: "off", name: "Off" }, { v: "phone", name: "Phone" }, { v: "pi", name: "Pi IMU" }, { v: "gps", name: "GPS-derived" },
];

function Choice<T extends string>({ label, value, options, reasons, onChange }: {
  label: string; value: T; options: { v: T; name: string }[]; reasons: Record<T, string | null>; onChange: (v: T) => void;
}) {
  return (
    <div className="opt-choices" role="radiogroup" aria-label={label}>
      {options.map((o) => {
        const why = reasons[o.v];
        return (
          <button key={o.v} type="button" role="radio" className="opt-choice" aria-checked={value === o.v}
            disabled={!!why} aria-label={why ? `${o.name} — ${why}` : o.name} onClick={() => onChange(o.v)}>
            <span>{o.name}</span>
            {why ? <span className="opt-reason">{why}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

const FLAG_KINDS: { k: "manual" | "range" | "faults"; name: string }[] = [
  { k: "manual", name: "Manual marks" }, { k: "range", name: "Sensor out of range" }, { k: "faults", name: "Faults" },
];

/**
 * The flag manager (spec §8): which kinds of flags the transport and notes show, with their
 * counts in the open replay session, and the muted sensors. Saved at once, per device,
 * display-only — independent of Apply.
 */
function FlagManager() {
  const o = useFlagOptions();
  const r = useReplay();
  const { counts } = useSessionFlags(r.data, r.session?.modules ?? []);
  const open = r.active && !!r.session;
  const count = { manual: r.notes.length, range: counts.range, faults: counts.faults };
  const set = (p: Partial<FlagOptions>) => saveFlagOptions({ ...o, ...p });
  return (
    <section className="opt-group" aria-label="Flags">
      <div className="kicker">Flags</div>
      {FLAG_KINDS.map(({ k, name }) => (
        <div key={k} className="row">
          <div className="grow">{name}{open ? <span className="muted"> · {count[k]}</span> : null}</div>
          <button type="button" className="tgl" role="switch" aria-checked={o[k]} aria-label={name}
            onClick={() => set({ [k]: !o[k] })}><span /></button>
        </div>
      ))}
      <div className="small muted">Muted sensors</div>
      {o.muted.length ? (
        <div className="row wrap" role="list" aria-label="Muted sensors">
          {o.muted.map((m) => (
            <span key={m} className="chip" role="listitem">
              {m}
              <button type="button" className="rchip" aria-label={`Unmute ${m}`}
                onClick={() => set({ muted: o.muted.filter((x) => x !== m) })}><Icon name="close" size={18} /></button>
            </span>
          ))}
        </div>
      ) : <div className="small">None</div>}
      <div className="small muted pretty">Flags are shown on this device only; they never change the log.</div>
    </section>
  );
}

type CalState = { phase: "idle" | "still" | "drive" | "done" | "error"; msg?: string };

/**
 * ⚙ Recording options (spec §3, §5): GPS status, audio source, accelerometer source and rate,
 * Calibrate ("hold still 2 s", optionally forward from GPS), session name. A source that can't
 * be used here is greyed with its reason. Apply asks the iOS motion/mic permissions and the
 * wake lock inside the tap, sends POST /command recording_options for the Pi's sources, and
 * starts phone capture. The choice is kept per device. The Flags section (the flag manager)
 * saves on its own, at once.
 */
export function RecordingOptions({ onClose }: { onClose: () => void }) {
  const { snap, toast } = useApp();
  const sources = snap?.recording_sources ?? null;
  const avail = availability(sources);
  const [opts, setOpts] = useState<RecordingOptionsValue>(() => {
    const o = loadOptions();
    return { ...o, audio: avail.audio[o.audio] ? "off" : o.audio, accel: avail.accel[o.accel] ? "off" : o.accel };
  });
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const [cal, setCal] = useState<CalState>(() => {
    const c = loadCalibration();
    return c ? { phase: "done", msg: `Calibrated (${c.method === "level+gps" ? "level + forward from GPS" : "level"})` } : { phase: "idle" };
  });
  const set = (p: Partial<RecordingOptionsValue>) => setOpts((o) => ({ ...o, ...p }));

  // GPS speed history while calibrating forward.
  const speeds = useRef<[number, number][]>([]);
  const gpsSpeed = snap?.gps?.fix ? snap.gps.speed_kmh : null;
  useEffect(() => {
    if (cal.phase === "drive" && gpsSpeed != null) speeds.current.push([Date.now(), gpsSpeed]);
  }, [cal.phase, gpsSpeed, snap?.ts_utc]);

  const session = snap?.recording?.session ?? null;
  const gpsOk = !avail.accel.gps;

  const calibrate = async () => {
    const m = phoneMotion();
    // The permission prompt must come from this tap.
    if (m.state.status === "off" || m.state.status === "denied") {
      if (!(await m.arm(opts.hz))) { setCal({ phase: "error", msg: m.state.error ?? "Motion access was refused" }); return; }
    }
    try {
      setCal({ phase: "still", msg: "Hold the phone still in its mount… (2 s)" });
      const { gravity, level } = await m.measureStill(2000);
      let yaw: number | null = null;
      let method: "level" | "level+gps" = "level";
      let note = "";
      if (opts.forwardFromGps && gpsOk) {
        speeds.current = [];
        setCal({ phase: "drive", msg: "Now drive off gently in a straight line… (up to 20 s)" });
        const samples = await m.collect(20_000);
        yaw = forwardFromDrive(samples, speeds.current, level);
        if (yaw != null) method = "level+gps";
        else note = " — no clear drive-off seen, so forward is the way the screen faces";
      }
      const matrix: Mat3 = calibrationMatrix(gravity, yaw);
      saveCalibration({ matrix, method, at: new Date().toISOString() });
      if (session && !(await postCalibration(session, { matrix, method }))) note += " — could not send it to the Pi; it will go with the next session";
      setCal({ phase: "done", msg: `Calibrated (${method === "level+gps" ? "level + forward from GPS" : "level"})${note}` });
    } catch (e) {
      setCal({ phase: "error", msg: e instanceof Error ? e.message : "Calibration failed" });
    }
  };

  const apply = async () => {
    setBusy(true);
    setErrors([]);
    const r = await applyOptions(opts, name);
    setBusy(false);
    if (r.ok) {
      toast("Recording options applied");
      onClose();
    } else {
      setErrors(r.errors);
    }
  };

  const rated = opts.accel === "phone" || opts.accel === "pi";
  const calibrating = cal.phase === "still" || cal.phase === "drive";
  return (
    <Sheet title="Recording & flags" onClose={onClose}>
      <section className="opt-group" aria-label="GPS">
        <div className="kicker">GPS</div>
        <div>{gpsLabel(sources, snap?.gps ?? null)}</div>
      </section>

      <section className="opt-group">
        <div className="kicker">Cabin audio</div>
        <Choice label="Cabin audio" value={opts.audio} options={AUDIO} reasons={avail.audio} onChange={(audio) => set({ audio })} />
        <div className="small muted pretty">Audio stays on the Pi and is never shared or shown publicly.</div>
      </section>

      <section className="opt-group">
        <div className="kicker">Accelerometer</div>
        <Choice label="Accelerometer" value={opts.accel} options={ACCEL} reasons={avail.accel} onChange={(accel) => set({ accel })} />
        {rated ? (
          <div className="seg" role="group" aria-label="Accelerometer rate">
            {RATES.map((hz) => (
              <button key={hz} type="button" aria-pressed={opts.hz === hz} onClick={() => set({ hz })}>{hz} Hz</button>
            ))}
          </div>
        ) : null}
        {opts.accel === "phone" ? (
          <div className="opt-cal card">
            <div className="small muted pretty">Mount the phone first. Calibrate tells the Pi which way is level and forward.</div>
            <label className="opt-check">
              <input type="checkbox" checked={opts.forwardFromGps && gpsOk} disabled={!gpsOk}
                onChange={(e) => set({ forwardFromGps: e.target.checked })} />
              <span>Auto-detect forward from GPS{gpsOk ? "" : " (needs GPS)"}</span>
            </label>
            <button type="button" className="btn" onClick={calibrate} disabled={calibrating}>Calibrate — hold still 2 s</button>
            {cal.msg ? <div className="small" role="status">{cal.phase === "error" ? <Icon name="warning" size="1.1em" className="icon-inline" /> : null}{cal.msg}</div> : null}
          </div>
        ) : null}
      </section>

      <section className="opt-group">
        <label className="kicker" htmlFor="rec-name">Session name</label>
        <input id="rec-name" className="input" placeholder="e.g. Rattle hunt, A82" value={name} maxLength={80}
          onChange={(e) => setName(e.target.value)} />
      </section>

      <FlagManager />

      {errors.length ? (
        <div className="card warn" role="alert">
          <b><Icon name="warning" size="1.1em" className="icon-inline" /> Not everything started</b>
          <ul className="opt-errors">{errors.map((e) => <li key={e}>{e}</li>)}</ul>
        </div>
      ) : null}
      <div className="btn-row">
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn accent" onClick={apply} disabled={busy || calibrating}>Apply</button>
      </div>
    </Sheet>
  );
}
