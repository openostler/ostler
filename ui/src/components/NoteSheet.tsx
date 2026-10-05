import { useState, type ReactNode } from "react";
import { QUICK_TAGS } from "../lib/notes";
import "../recording.css";
import { Sheet } from "./Sheet";

/** Tag toggles: the quick tags plus any extra tags the note already has. */
export function TagPicker({ tags, onChange }: { tags: string[]; onChange: (tags: string[]) => void }) {
  const all = [...QUICK_TAGS, ...tags.filter((t) => !(QUICK_TAGS as readonly string[]).includes(t))];
  return (
    <div className="note-tags" role="group" aria-label="Tags">
      {all.map((t) => {
        const on = tags.includes(t);
        return (
          <button key={t} type="button" className="note-tag" aria-pressed={on}
            onClick={() => onChange(on ? tags.filter((x) => x !== t) : [...tags, t])}>{t}</button>
        );
      })}
    </div>
  );
}

/**
 * "What happened?" — free text plus quick tags. Used after ⚑ (the mark is already saved; this
 * fills it in) and by "Note…" on the recording card.
 */
export function NoteSheet({ title = "What happened?", initialText = "", initialTags = [], saveLabel = "Save", hint, onSave, onClose }: {
  title?: ReactNode;
  initialText?: string;
  initialTags?: string[];
  saveLabel?: string;
  /** A line under the title (e.g. "Marked at 12:04:31"). */
  hint?: ReactNode;
  /** Resolve to true to close the sheet; false keeps it open (e.g. the save failed). */
  onSave: (text: string, tags: string[]) => Promise<boolean> | boolean;
  onClose: () => void;
}) {
  const [text, setText] = useState(initialText);
  const [tags, setTags] = useState<string[]>(initialTags);
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      if (await onSave(text.trim(), tags)) onClose();
    } finally {
      setBusy(false);
    }
  };
  return (
    <Sheet title={title} onClose={onClose}>
      {hint ? <div className="small muted">{hint}</div> : null}
      <textarea className="note-text" aria-label="What happened?" placeholder="e.g. clunk from the rear on the speed bump"
        value={text} onChange={(e) => setText(e.target.value)} autoFocus />
      <TagPicker tags={tags} onChange={setTags} />
      <div className="btn-row">
        <button className="btn" onClick={onClose}>Close</button>
        <button className="btn accent" onClick={save} disabled={busy}>{saveLabel}</button>
      </div>
    </Sheet>
  );
}
