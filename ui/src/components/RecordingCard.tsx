// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { api, command } from "../api/client";
import type { Recording } from "../api/schemas";
import { applyOptions, gpsLabel, loadOptions, usePhoneAudio, usePhoneMotion } from "../lib/recordingOptions";
import { parseUtc } from "../lib/time";
import { useApp } from "../state/app";
import "../recording.css";
import { NoteSheet } from "./NoteSheet";
import { isPaused } from "./replay/sessionFormat";
import { RecordingOptions } from "./RecordingOptions";

/** "45 s", "12 min", "1 h 05 min" from seconds. */
const dur = (s: number) => {
  if (s < 60) return `${Math.max(0, Math.floor(s))} s`;
  const m = Math.floor(s / 60);
  return m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, "0")} min`;
};

type Src = { key: string; label: string; tone?: "on" | "lost" };

/**
 * The Logs "Recording now" card (spec §5): duration, modules, sources, then ⚑ Mark, Note…,
 * ⚙ Options (RecordingOptions) and Split. Sources include this phone's mic/motion state; a
 * lost phone source is shown with ⚠ and a Resume button (the browser needs a tap). While the
 * server has paused the session (no connection, logs-at-scale spec §1, §5) the card says
 * "Paused — no connection" and offers only Options: nothing can be marked or split.
 */
export function RecordingCard({ recording, nowS, modules, onOpen, onSplit }: {
  /** The session being recorded; null/undefined renders nothing. */
  recording: Recording | null | undefined;
  /** Epoch seconds now (server snapshot time when known). */
  nowS: number;
  /** Modules seen this session (defaults to the module in view). */
  modules?: string[];
  /** Open the session in replay (the card's title becomes a button). */
  onOpen?: (id: string) => void;
  /** Override Split (default: POST /command split_session). */
  onSplit?: () => void;
}) {
  const { snap, toast, module } = useApp();
  const audio = usePhoneAudio();
  const motion = usePhoneMotion();
  const [sheet, setSheet] = useState<"note" | "mark" | "options" | null>(null);
  const [markId, setMarkId] = useState<{ id: string; session: string } | null>(null);
  const rs = snap?.recording_sources ?? null;
  const saved = loadOptions();
  if (!recording) return null;

  const srcs: Src[] = [{ key: "gps", label: gpsLabel(rs, snap?.gps ?? null), tone: rs?.gps && rs.gps !== "none" ? "on" : undefined }];
  if (rs?.pi_audio.state === "on") srcs.push({ key: "pi_audio", label: "Pi mic", tone: "on" });
  if (rs?.imu.state === "on") srcs.push({ key: "imu", label: `Pi IMU ${rs.accel_hz} Hz`, tone: "on" });
  if (audio.status === "recording") srcs.push({ key: "mic", label: "Phone mic", tone: "on" });
  else if (audio.status === "lost" || audio.status === "denied" || audio.status === "error")
    srcs.push({ key: "mic", label: `⚠ Phone mic ${audio.status === "lost" ? "lost" : "off"}`, tone: "lost" });
  if (motion.status === "recording") srcs.push({ key: "motion", label: `Phone motion ${motion.rate} Hz`, tone: "on" });
  else if (motion.status === "denied" || motion.status === "error") srcs.push({ key: "motion", label: "⚠ Phone motion off", tone: "lost" });
  const wantsPhone = (saved.audio === "phone" && audio.status !== "recording") || (saved.accel === "phone" && motion.status !== "recording" && motion.status !== "armed");

  const mark = async () => {
    try {
      const r = await api.liveNote({ kind: "mark" });
      if (!r.note) { toast(r.error ?? "Could not save the mark", true); return; }
      toast("⚑ Marked");
      setMarkId({ id: r.note.id, session: r.session ?? recording.session });
      setSheet("mark");
    } catch {
      toast("Could not save the mark", true);
    }
  };

  const saveMark = async (text: string, tags: string[]) => {
    if (!markId || (!text && !tags.length)) return true;
    try {
      const r = await api.editNote(markId.session, markId.id, { text, tags });
      if (r.ok === false || r.error) { toast(r.error ?? "Could not save the note", true); return false; }
      return true;
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };

  const saveNote = async (text: string, tags: string[]) => {
    if (!text && !tags.length) return true;
    try {
      const r = await api.liveNote({ kind: "note", text, tags });
      if (!r.note) { toast(r.error ?? "Could not save the note", true); return false; }
      toast("Note saved");
      return true;
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };

  const split = async () => {
    if (onSplit) { onSplit(); return; }
    try {
      const r = await command("split_session");
      toast(r.ok ? "New session started" : r.error ?? "Could not split the session", !r.ok);
    } catch {
      toast("Could not reach the Pi", true);
    }
  };

  /** Re-arm phone capture with the saved choice (the browser needs this tap). */
  const resume = async () => {
    const r = await applyOptions(saved);
    if (!r.ok) toast(r.errors[0] ?? "Phone capture could not start", true);
  };

  const mods = modules?.length ? modules : module ? [module] : [];
  const sinceMs = parseUtc(recording.since_utc);
  const elapsed = dur(sinceMs == null ? 0 : nowS - sinceMs / 1000);
  const paused = isPaused(recording);
  const title = paused ? "Paused — no connection" : `Recording now · ${elapsed}`;
  const head = (
    <>
      <span className={`rec-dot${paused ? " paused" : ""}`} aria-hidden="true" />
      <b>{title}</b>
      <span className="muted small">{recording.rows} rows{mods.length ? ` · ${mods.join(", ")}` : ""}</span>
    </>
  );
  return (
    <section className={`card rec-card${paused ? " paused" : ""}`} aria-label={paused ? "Recording paused" : "Recording now"}>
      {onOpen ? (
        <button className="rec-head rec-open"
          onClick={() => onOpen(recording.session)} aria-label={`${paused ? "Paused — no connection" : `Recording now, ${elapsed}`} — open`}>{head}</button>
      ) : <div className="rec-head">{head}</div>}
      <div className="rec-sources" aria-label="Sources">
        {srcs.map((s) => <span key={s.key} className={`rec-src ${s.tone ?? ""}`}>{s.label}</span>)}
      </div>
      {wantsPhone ? (
        <button className="btn" onClick={resume}>Resume phone capture</button>
      ) : null}
      {paused ? (
        <div className="rec-actions paused">
          <p className="muted small">Nothing is written until the car is connected again.</p>
          <button className="btn" onClick={() => setSheet("options")} aria-label="Recording options">⚙ Options</button>
        </div>
      ) : (
        <div className="rec-actions">
          <button className="btn" onClick={mark} aria-label="Mark this moment">⚑ Mark</button>
          <button className="btn" onClick={() => setSheet("note")}>Note…</button>
          <button className="btn" onClick={() => setSheet("options")} aria-label="Recording options">⚙ Options</button>
          <button className="btn" onClick={split} aria-label="Split — start a new session">Split</button>
        </div>
      )}
      {sheet === "note" && !paused ? <NoteSheet title="Add a note" onSave={saveNote} onClose={() => setSheet(null)} /> : null}
      {sheet === "mark" && !paused ? <NoteSheet hint="Marked — add what happened" onSave={saveMark} onClose={() => setSheet(null)} /> : null}
      {sheet === "options" ? <RecordingOptions onClose={() => setSheet(null)} /> : null}
    </section>
  );
}
