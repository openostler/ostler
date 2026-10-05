import { useState } from "react";
import { api } from "../../api/client";
import type { Note } from "../../api/schemas";
import { KIND_ICON, noteAt, noteSpan, sortNotes } from "../../lib/notes";
import { useApp } from "../../state/app";
import { useReplay } from "../../state/replay";
import "../../recording.css";
import { NoteEditor, type NoteDraft } from "./NoteEditor";

/** Ask the panel to open its editor: an existing note by id (a chart/scrubber marker tap),
 * or a new note at a time or range (a drag on the chart). */
export type NoteRequest = { id: string } | { t: number; t_end?: number | null };

/**
 * The replay notes list (spec §5): every note by time, tap to jump the cursor there, ✎ to
 * edit or delete, and "Add note at cursor". Range notes show "start–end". Demo (synthetic)
 * sessions are read-only. Reads everything from useReplay(); `request` lets the chart open
 * the editor for a marker or a dragged range.
 */
export function NotesPanel({ request = null, onRequestDone }: {
  request?: NoteRequest | null;
  onRequestDone?: () => void;
} = {}) {
  const r = useReplay();
  const { toast } = useApp();
  const [local, setLocal] = useState<NoteRequest | null>(null);
  const open = local ?? request;
  const close = () => { setLocal(null); if (request) onRequestDone?.(); };

  if (!r.active || !r.session) return null;
  const sid = r.session.id;
  const readOnly = r.session.synthetic ? "Demo sessions can't be annotated." : null;
  const notes = sortNotes(r.notes);

  const reply = (res: { ok?: boolean; error?: string }, okMsg: string) => {
    if (res.ok === false || res.error) { toast(res.error ?? "The Pi refused the change", true); return false; }
    toast(okMsg);
    r.refreshNotes();
    return true;
  };

  const create = async (d: NoteDraft) => {
    try {
      const n = await r.addNote({ t: d.t, t_end: d.t_end, text: d.text, tags: d.tags });
      if (!n) { toast("Could not save the note", true); return false; }
      toast("Note added");
      return true;
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };
  const edit = (n: Note) => async (d: NoteDraft) => {
    try {
      return reply(await api.editNote(sid, n.id, { text: d.text, tags: d.tags, t: d.t, t_end: d.t_end }), "Note saved");
    } catch {
      toast("Could not save the note", true);
      return false;
    }
  };
  const del = (n: Note) => async () => {
    try {
      return reply(await api.deleteNote(sid, n.id), "Note deleted");
    } catch {
      toast("Could not delete the note", true);
      return false;
    }
  };

  const editing = open && "id" in open ? notes.find((n) => n.id === open.id) : undefined;
  return (
    <section className="notes-panel" aria-label="Notes">
      <div className="notes-head">
        <h3 className="kicker">Notes{notes.length ? ` · ${notes.length}` : ""}</h3>
        <button className="rchip" disabled={!!readOnly} title={readOnly ?? undefined}
          onClick={() => setLocal({ t: Math.round(r.t) })}>+ Add note at cursor</button>
      </div>
      {readOnly ? <div className="small muted">{readOnly}</div> : null}
      {notes.length === 0 ? (
        <p className="muted small">No notes yet. Tap ⚑ while recording, or add one at the cursor.</p>
      ) : (
        <ul className="notes-list">
          {notes.map((n) => (
            <li key={n.id} className={`note-row${noteAt(n, r.t) ? " here" : ""}`} data-note={n.id}>
              <button className="note-jump" onClick={() => r.seek(n.t)} aria-label={`Jump to ${noteSpan(n)}: ${n.text || n.kind}`}>
                <span className="note-t">{noteSpan(n)}</span>
                <span className="note-kind" aria-hidden="true">{KIND_ICON[n.kind] ?? "✎"}</span>
                <span className="note-body">
                  {n.text || <span className="muted">{n.kind === "mark" ? "Mark" : "(no text)"}</span>}
                  {n.t_end != null ? <span className="note-chip">range</span> : null}
                  {n.tags.map((tag) => <span key={tag} className="note-chip">{tag}</span>)}
                </span>
              </button>
              <button className="note-edit" aria-label={readOnly ? "View note" : "Edit note"} onClick={() => setLocal({ id: n.id })}>
                {readOnly ? "…" : "✎"}
              </button>
            </li>
          ))}
        </ul>
      )}
      {open && editing ? (
        <NoteEditor key={editing.id} note={editing} cursor={r.t} readOnly={readOnly}
          onSave={edit(editing)} onDelete={del(editing)} onClose={close} />
      ) : null}
      {open && !("id" in open) && !readOnly ? (
        <NoteEditor key={`new-${open.t}`} t={open.t} t_end={open.t_end ?? null} cursor={r.t} onSave={create} onClose={close} />
      ) : null}
    </section>
  );
}
