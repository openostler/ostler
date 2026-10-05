import { useState } from "react";
import { api } from "../api/client";
import type { Note } from "../api/schemas";
import { useCaptureRunner } from "../lib/recordingOptions";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import "../recording.css";
import { NoteSheet } from "./NoteSheet";

const clock = (iso: string | undefined) => {
  const d = iso ? new Date(iso) : new Date();
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
};

/**
 * Header ⚑ (spec §5). One tap saves a `mark` at once (the moment is never lost to typing),
 * then "What happened?" PATCHes the mark with text and tags. Shown only while the Pi is
 * recording and not in replay. Always mounted: it also points phone audio/motion capture at
 * the session being recorded (lib/recordingOptions `useCaptureRunner`).
 */
export function MarkButton() {
  const { snap, toast } = useApp();
  const replay = useReplay();
  const session = replay.active ? null : snap?.recording?.session ?? null;
  useCaptureRunner(session, replay.active);
  if (!session) return null;
  return <Mark toast={toast} />;
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
      if (r.note) { note = r.note; session = r.session ?? null; toast("⚑ Marked"); }
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
      <button className="chip mark-btn" aria-label="Mark this moment" title="Mark this moment"
        aria-busy={busy} onClick={tap}>⚑</button>
      {mark ? (
        <NoteSheet hint={mark.note ? `Marked at ${clock(mark.note.created)}` : "Not saved yet — Save stores it now"}
          onSave={save} onClose={() => setMark(null)} />
      ) : null}
    </>
  );
}
