// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { trackTime } from "../../lib/audio";
import type { AudioTrack } from "../../api/schemas";
import { useReplay } from "../../state/replay";
import "../../recording.css";

const KEY = "d2diag.replayAudio";
const NO_TRACKS: AudioTrack[] = [];
type AudioPrefs = { muted: boolean; offset: number };

function loadPrefs(): AudioPrefs {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<AudioPrefs>;
    return { muted: raw.muted === true, offset: typeof raw.offset === "number" && Number.isFinite(raw.offset) ? raw.offset : 0 };
  } catch {
    return { muted: false, offset: 0 };
  }
}
function savePrefs(p: AudioPrefs) {
  try { localStorage.setItem(KEY, JSON.stringify(p)); } catch { /* storage blocked */ }
}

/** Seek only when the element drifts more than this from the cursor (s). */
const DRIFT_S = 0.3;

/**
 * Session audio, synced to the replay cursor (spec §3, §5). One hidden <audio> per
 * `meta.audio` track; `start_ms`/`end_ms` are session ms. Plays at 1× and 2× with the
 * matching playbackRate; faster than 2× it stays silent. Mute and a ±0.5 s offset (to line
 * the sound up with the data) are kept per device. Renders nothing without audio.
 */
export function ReplayAudio() {
  const r = useReplay();
  const tracks = r.active && r.session ? r.session.audio : NO_TRACKS;
  const [prefs, setPrefs] = useState<AudioPrefs>(loadPrefs);
  const els = useRef(new Map<string, HTMLAudioElement>());

  const update = (patch: Partial<AudioPrefs>) => {
    setPrefs((p) => {
      const n = { ...p, ...patch };
      n.offset = Math.round(n.offset * 10) / 10;
      savePrefs(n);
      return n;
    });
  };

  const fast = r.speed > 2;
  useEffect(() => {
    for (const tr of tracks) {
      const el = els.current.get(tr.track);
      if (el) sync(el, tr, r.t, r.playing && !fast, r.speed, prefs, r.offset);
    }
  }, [tracks, r.t, r.playing, r.speed, fast, prefs, r.offset]);

  useEffect(() => {
    const map = els.current;
    return () => { for (const el of map.values()) safePause(el); };
  }, []);

  if (!tracks.length || !r.session) return null;
  const id = r.session.id;
  const sign = prefs.offset > 0 ? "+" : prefs.offset < 0 ? "−" : "±";
  return (
    <div className="replay-audio" role="group" aria-label="Session audio">
      {tracks.map((tr) => (
        <audio key={tr.track} data-track={tr.track} preload="auto" hidden src={api.sessionAudioUrl(id, tr.track)}
          ref={(el) => { if (el) els.current.set(tr.track, el); else els.current.delete(tr.track); }} />
      ))}
      <button className="rchip" aria-pressed={!prefs.muted} aria-label={prefs.muted ? "Unmute audio" : "Mute audio"}
        onClick={() => update({ muted: !prefs.muted })}>
        <span aria-hidden="true">{prefs.muted ? "🔇" : "🔊"}</span>Audio
      </button>
      <button className="rchip" aria-label="Audio earlier by 0.5 s" onClick={() => update({ offset: prefs.offset - 0.5 })}>−0.5 s</button>
      <span className="off" aria-live="polite" aria-label={`Audio offset ${prefs.offset} s`}>{sign}{Math.abs(prefs.offset).toFixed(1)} s</span>
      <button className="rchip" aria-label="Audio later by 0.5 s" onClick={() => update({ offset: prefs.offset + 0.5 })}>+0.5 s</button>
      {fast ? <span className="small muted">silent above 2×</span> : null}
    </div>
  );
}

function safePause(el: HTMLAudioElement) {
  try { if (!el.paused) el.pause(); } catch { /* not ready */ }
}

function sync(el: HTMLAudioElement, tr: AudioTrack, t: number, audible: boolean, speed: number, prefs: AudioPrefs, utcOffset: number | null) {
  const want = trackTime(tr, t, prefs.offset, utcOffset);
  if (want == null || (Number.isFinite(el.duration) && want > el.duration)) {
    safePause(el);
    return;
  }
  if (Math.abs(el.currentTime - want) > DRIFT_S) {
    try { el.currentTime = want; } catch { /* metadata not loaded yet */ }
  }
  el.muted = prefs.muted;
  if (speed <= 2) el.playbackRate = speed;
  if (audible && el.paused) {
    try {
      const p = el.play() as Promise<void> | undefined;
      p?.catch?.(() => undefined); // autoplay refused until the next tap — harmless
    } catch { /* not supported */ }
  } else if (!audible) {
    safePause(el);
  }
}
