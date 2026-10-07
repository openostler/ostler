// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { api } from "../api/client";
import { Icon } from "../icons/Icon";
import type { Note } from "../api/schemas";
import { formatNoteTime } from "../lib/notes";
import { useCaptureRunner } from "../lib/recordingOptions";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import "../recording.css";
import { NoteSheet } from "./NoteSheet";
import { isPaused } from "./replay/sessionFormat";

const clock = (iso: string | undefined) => {
  const d = iso ? new Date(iso) : new Date();
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

/** The strip chip's face: the flag symbol and the word (UI spec §3.2: icon and word). */
const MarkFace = () => <><Icon name="flag" size={20} /><span className="schip-word">Mark</span></>;

/**
 * The strip's Mark chip (UI spec §3.2 chip 9, the one action safe at any speed; spec §5, §8). Live while recording: one tap saves a `mark` at once (the moment is
 * never lost to typing), then "What happened?" PATCHes the mark with text and tags. Paused (no
 * connection): shown greyed, "Connect to the car to mark". In replay of an editable session: a
 * retro mark at the cursor, then the same sheet. Hidden on demo logs, in public mode and when
 * nothing is recording. Always mounted: it also points phone audio/motion capture at the
 * session being recorded (lib/recordingOptions `useCaptureRunner`).
 */
export function MarkButton() {
  const { snap, toast } = useApp();
  const replay = useReplay();
  const session = replay.active ? null : snap?.recording?.session ?? null;
  useCaptureRunner(session, replay.active);
  if (replay.active) {
    const meta = replay.session;
    if (!meta || meta.synthetic || snap?.public) return null;
    return <RetroMark key={meta.id} session={meta.id} toast={toast} />;
  }
  if (!session) return null;
  // Paused (no connection): the session stays open but nothing can be marked (spec §5).
  if (isPaused(snap?.recording)) {
    return (
      <button className="schip mark-btn" aria-label="Connect to the car to mark" title="Connect to the car to mark"
        disabled><MarkFace /></button>
    );
  }
  return <Mark toast={toast} />;
}

/** Replay ⚑: saves a note at the cursor at once, then "What happened?" fills it in. */
function RetroMark({ session, toast }: { session: string; toast: (m: string, bad?: boolean) => void }) {
  const r = useReplay();
  const [busy, setBusy] = useState(false);
  const [mark, setMark] = useState<{ note: Note | null; t: number } | null>(null);

  const tap = async () => {
    if (busy) return;
    const t = Math.round(r.t);
    setBusy(true);
    const note = await r.addNote({ t }).catch(() => null);
    setBusy(false);
    if (note) toast("Marked");
    else toast("Could not save the mark — it will be saved with the note", true);
    setMark({ note, t });
  };

  const save = async (text: string, tags: string[]) => {
    if (!mark) return true;
    if (mark.note && !text && !tags.length) return true; // the bare mark is already saved
    try {
      if (mark.note) {
        const res = await api.editNote(session, mark.note.id, { text, tags });
        if (res.ok === false || res.error) { toast(res.error ?? "Could not save the note", true); return false; }
        r.refreshNotes();
      } else if (!(await r.addNote({ t: mark.t, text, tags }))) {
        toast("Could not save the note", true);
        return false;
      }
      toast("Note saved");
      return true;
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };

  return (
    <>
      <button className="schip mark-btn" aria-label="Mark at the cursor" title="Mark this moment at the cursor"
        aria-busy={busy} onClick={tap}><MarkFace /></button>
      {mark ? (
        <NoteSheet hint={mark.note ? `Marked at ${formatNoteTime(mark.t)}` : "Not saved yet — Save stores it now"}
          onSave={save} onClose={() => setMark(null)} />
      ) : null}
    </>
  );
}

function Mark({ toast }: { toast: (m: string, bad?: boolean) => void }) {
  const [busy, setBusy] = useState(false);
  const [mark, setMark] = useState<{ note: Note | null; session: string | null } | null>(null);

  const tap = async () => {
    if (busy) return;
    setBusy(true);
    let note: Note | null = null, session: string | null = null;
    try {
      const r = await api.liveNote({ kind: "mark" });
      if (r.note) { note = r.note; session = r.session ?? null; toast("Marked"); }
      else toast(r.error ?? "Could not save the mark", true);
    } catch {
      toast("Could not save the mark — it will be saved with the note", true);
    } finally {
      setBusy(false);
    }
    setMark({ note, session });
  };

  const save = async (text: string, tags: string[]) => {
    if (!mark) return true;
    if (!text && !tags.length) return true; // the bare mark is already saved
    try {
      const r = mark.note && mark.session
        ? await api.editNote(mark.session, mark.note.id, { text, tags })
        : await api.liveNote({ kind: "mark", text, tags });
      if (r.ok === false || r.error) { toast(r.error ?? "Could not save the note", true); return false; }
      toast("Note saved");
      return true;
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };

  return (
    <>
      <button className="schip mark-btn" aria-label="Mark this moment" title="Mark this moment"
        aria-busy={busy} onClick={tap}><MarkFace /></button>
      {mark ? (
        <NoteSheet hint={mark.note ? `Marked at ${clock(mark.note.created)}` : "Not saved yet — Save stores it now"}
          onSave={save} onClose={() => setMark(null)} />
      ) : null}
    </>
  );
}
