import { useState } from "react";
import type { Note } from "../../api/schemas";
import { formatNoteTime } from "../../lib/notes";
import "../../recording.css";
import { TagPicker } from "../NoteSheet";
import { Sheet } from "../Sheet";

export type NoteDraft = { text: string; tags: string[]; t: number; t_end: number | null };

/**
 * Edit (or create) one note on the replay timeline: text, tags, start and optional end
 * (a range). "Use cursor" moves either end to the replay cursor. Delete asks first.
 * `readOnly` (e.g. a demo session) shows the note without editing controls.
 */
export function NoteEditor({ note, t, t_end = null, cursor, readOnly, onSave, onDelete, onClose }: {
  /** The note being edited; absent when creating. */
  note?: Note;
  /** Start of a new note (ignored when editing). */
  t?: number;
  t_end?: number | null;
  /** The replay cursor (session ms), for "Use cursor". */
  cursor: number;
  readOnly?: string | null;
  onSave: (d: NoteDraft) => Promise<boolean>;
  onDelete?: () => Promise<boolean>;
  onClose: () => void;
}) {
  const [d, setD] = useState<NoteDraft>(() => ({
    text: note?.text ?? "",
    tags: note?.tags ?? [],
    t: note?.t ?? t ?? cursor,
    t_end: note ? note.t_end ?? null : t_end,
  }));
  const [busy, setBusy] = useState(false);
  const set = (p: Partial<NoteDraft>) => setD((x) => ({ ...x, ...p }));
  const badRange = d.t_end != null && d.t_end <= d.t;

  const run = async (fn: () => Promise<boolean>) => {
    setBusy(true);
    try {
      if (await fn()) onClose();
    } finally {
      setBusy(false);
    }
  };
  const del = () => {
    if (!onDelete || !window.confirm("Delete this note?")) return;
    void run(onDelete);
  };

  const title = !note ? "Add note" : readOnly ? "Note" : note.kind === "mark" ? "Edit mark" : "Edit note";
  return (
    <Sheet title={title} onClose={onClose}>
      <div className="note-when" aria-label="When">
        <span className="muted">Start</span><b data-testid="note-start">{formatNoteTime(d.t)}</b>
        {!readOnly ? <button type="button" className="rchip" onClick={() => set({ t: cursor })}>Use cursor</button> : null}
      </div>
      <div className="note-when" aria-label="End">
        <span className="muted">End</span><b data-testid="note-end">{d.t_end != null ? formatNoteTime(d.t_end) : "—"}</b>
        {!readOnly ? (
          <>
            <button type="button" className="rchip" onClick={() => set({ t_end: cursor })}>
              {d.t_end != null ? "Use cursor" : "Make a range to cursor"}
            </button>
            {d.t_end != null ? <button type="button" className="rchip" onClick={() => set({ t_end: null })}>Point note</button> : null}
          </>
        ) : null}
      </div>
      {badRange ? <div className="small" role="alert">⚠ The end must be after the start.</div> : null}
      {note?.capture ? (
        <div className="small muted">Capture: {note.capture.module} LID {note.capture.lid} = {note.capture.value} (raw {note.capture.raw})</div>
      ) : null}
      {readOnly ? (
        <>
          <p>{d.text || <span className="muted">(no text)</span>}</p>
          {d.tags.length ? <div className="small muted">{d.tags.join(" · ")}</div> : null}
          <div className="small muted">{readOnly}</div>
          <button className="btn" onClick={onClose}>Close</button>
        </>
      ) : (
        <>
          <textarea className="note-text" aria-label="Note text" placeholder="What happened here?"
            value={d.text} onChange={(e) => set({ text: e.target.value })} />
          <TagPicker tags={d.tags} onChange={(tags) => set({ tags })} />
          <div className="btn-row">
            {note && onDelete ? <button className="btn danger" onClick={del} disabled={busy}>Delete</button> : null}
            <button className="btn" onClick={onClose}>Cancel</button>
            <button className="btn accent" disabled={busy || badRange}
              onClick={() => void run(() => onSave({ ...d, text: d.text.trim() }))}>Save</button>
          </div>
        </>
      )}
    </Sheet>
  );
}
