// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { api } from "../../api/client";
import type { Note } from "../../api/schemas";
import type { Flag } from "../../lib/flags";
import { KIND_ICON, noteAt, noteSpan, sortNotes } from "../../lib/notes";
import { useApp } from "../../state/app";
import { useSessionFlags } from "../../state/flags";
import { useReplay } from "../../state/replay";
import "../../recording.css";
import { FlagSheet, SEVERITY } from "../FlagSheet";
import { NoteEditor, type NoteDraft } from "./NoteEditor";
import { Icon } from "../../icons/Icon";

/** Ask the panel to open its editor: an existing note by id (a chart/scrubber marker tap),
 * or a new note at a time or range (a drag on the chart). */
export type NoteRequest = { id: string } | { t: number; t_end?: number | null };

/** The list filter (spec §8): All · Notes · Out of range · Faults. */
type Filter = "all" | "notes" | "range" | "fault";
const FILTERS: { v: Filter; name: string }[] = [
  { v: "all", name: "All" }, { v: "notes", name: "Notes" }, { v: "range", name: "Out of range" }, { v: "fault", name: "Faults" },
];
type Row = { note: Note; t: number } | { flag: Flag; t: number };

/**
 * The replay notes list (spec §5, §8): every note and automatic flag by time, tap a note to jump
 * the cursor there, ✎ to edit or delete, tap a flag for the flag sheet, and "Add note at cursor".
 * Range notes show "start–end". A filter (All · Notes · Out of range · Faults) shows when the
 * session has flags. Demo (synthetic) sessions are read-only. Reads everything from useReplay(); `request` lets the chart open
 * the editor for a marker or a dragged range.
 */
export function NotesPanel({ request = null, onRequestDone }: {
  request?: NoteRequest | null;
  onRequestDone?: () => void;
} = {}) {
  const r = useReplay();
  const { toast } = useApp();
  const [local, setLocal] = useState<NoteRequest | null>(null);
  const [filter, setFilter] = useState<Filter>("all");
  const [flagOpen, setFlagOpen] = useState<Flag | null>(null);
  const flags = useSessionFlags(r.data, r.session?.modules ?? []).visible;
  const open = local ?? request;
  const close = () => { setLocal(null); if (request) onRequestDone?.(); };

  if (!r.active || !r.session) return null;
  const sid = r.session.id;
  const readOnly = r.session.synthetic ? "Demo sessions can't be annotated." : null;
  const notes = sortNotes(r.notes);
  const rows: Row[] = [
    ...(filter === "all" || filter === "notes" ? notes.map((n) => ({ note: n, t: n.t })) : []),
    ...(filter === "notes" ? [] : flags.filter((f) => filter === "all" || f.kind === filter).map((f) => ({ flag: f, t: f.t }))),
  ].sort((a, b) => a.t - b.t); // stable: a note stays ahead of a flag at the same time

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
      {flags.length ? (
        <div className="notes-filter" role="group" aria-label="Show">
          {FILTERS.map((f) => (
            <button key={f.v} type="button" className="rchip" aria-pressed={filter === f.v} onClick={() => setFilter(f.v)}>{f.name}</button>
          ))}
        </div>
      ) : null}
      {rows.length === 0 ? (
        filter === "all" || filter === "notes"
          ? <p className="muted small">No notes yet. Tap Mark while recording, or add one at the cursor.</p>
          : <p className="muted small">No {filter === "range" ? "out-of-range" : "fault"} flags in this session.</p>
      ) : (
        <ul className="notes-list">
          {rows.map((row) => "flag" in row ? (
            <li key={row.flag.id} className={`note-row flag-row ${row.flag.severity}${noteAt(row.flag, r.t) ? " here" : ""}`} data-flag={row.flag.id}>
              <button className="note-jump" onClick={() => setFlagOpen(row.flag)}
                aria-label={`${SEVERITY[row.flag.severity].word} at ${noteSpan(row.flag)}: ${row.flag.label}`}>
                <span className="note-t">{noteSpan(row.flag)}</span>
                <span className={`note-kind flag-icon ${row.flag.severity}`} aria-hidden="true"><Icon name={SEVERITY[row.flag.severity].icon} size={18} /></span>
                <span className="note-body">
                  {row.flag.label}
                  <span className={`note-chip flag-word ${row.flag.severity}`}>{SEVERITY[row.flag.severity].word}</span>
                </span>
              </button>
            </li>
          ) : (
            <li key={row.note.id} className={`note-row${noteAt(row.note, r.t) ? " here" : ""}`} data-note={row.note.id}>
              <button className="note-jump" onClick={() => r.seek(row.note.t)} aria-label={`Jump to ${noteSpan(row.note)}: ${row.note.text || row.note.kind}`}>
                <span className="note-t">{noteSpan(row.note)}</span>
                <span className="note-kind" aria-hidden="true"><Icon name={KIND_ICON[row.note.kind] ?? "edit"} size={18} /></span>
                <span className="note-body">
                  {row.note.text || <span className="muted">{row.note.kind === "mark" ? "Mark" : "(no text)"}</span>}
                  {row.note.t_end != null ? <span className="note-chip">range</span> : null}
                  {row.note.tags.map((tag) => <span key={tag} className="note-chip">{tag}</span>)}
                </span>
              </button>
              <button className="note-edit" aria-label={readOnly ? "View note" : "Edit note"} onClick={() => setLocal({ id: row.note.id })}>
                <Icon name={readOnly ? "more_horiz" : "edit"} size={20} />
              </button>
            </li>
          ))}
        </ul>
      )}
      {flagOpen ? <FlagSheet item={{ flag: flagOpen }} onClose={() => setFlagOpen(null)} /> : null}
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
