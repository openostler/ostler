// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Tap-to-edit text (spec §5, the replay header's name and description). Tap → a field; Enter
 * (Shift+Enter for a new line when multiline) or leaving the field saves; Escape cancels. The
 * new value shows at once (optimistic) and rolls back when `onSave` rejects — the caller
 * toasts. Read-only renders plain text (or nothing when empty and `hideEmpty`).
 */
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

export function InlineEdit({ value, placeholder, label, onSave, readOnly = false, multiline = false, maxLength, as = "span", className, hideEmpty = false }: {
  value: string | null | undefined;
  placeholder: string;
  /** Accessible name of the field (and of the edit button: "Edit <label>"). */
  label: string;
  /** Persist the trimmed value (null when empty). Reject to roll back. */
  onSave: (v: string | null) => Promise<unknown>;
  readOnly?: boolean;
  multiline?: boolean;
  maxLength?: number;
  as?: "span" | "h2" | "p";
  className?: string;
  /** Read-only and empty → render nothing (instead of the placeholder). */
  hideEmpty?: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  // The optimistic value: shown until the prop catches up (or a failed save rolls it back).
  const [pending, setPending] = useState<{ v: string | null } | null>(null);
  const [base, setBase] = useState(value);
  if (base !== value) {
    setBase(value);
    setPending(null);
  }
  const field = useRef<HTMLInputElement & HTMLTextAreaElement>(null);
  const done = useRef(false); // Enter/Escape already settled this edit; ignore the blur after it
  useEffect(() => {
    if (editing) { field.current?.focus(); field.current?.select?.(); }
  }, [editing]);

  const current = pending ? pending.v : value ?? null;
  const Tag = as;
  const cls = ["inline-edit", className].filter(Boolean).join(" ");

  if (readOnly) {
    if (!current && hideEmpty) return null;
    return <Tag className={cls} data-empty={current ? undefined : "true"}>{current || placeholder}</Tag>;
  }

  const start = () => {
    done.current = false;
    setDraft(current ?? "");
    setEditing(true);
  };
  const commit = () => {
    if (done.current) return;
    done.current = true;
    setEditing(false);
    const next = draft.trim() || null;
    if (next === (current ?? null)) return;
    const prev = pending;
    setPending({ v: next });
    onSave(next).catch(() => setPending(prev));
  };
  const cancel = () => {
    done.current = true;
    setEditing(false);
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") { e.preventDefault(); cancel(); }
    else if (e.key === "Enter" && !(multiline && e.shiftKey)) { e.preventDefault(); commit(); }
  };

  if (editing) {
    const common = {
      ref: field, className: `input inline-edit-field ${multiline ? "multi" : ""}`, value: draft, maxLength,
      "aria-label": label, placeholder,
      onChange: (e: { target: { value: string } }) => setDraft(e.target.value),
      onKeyDown: onKey, onBlur: commit,
    };
    return (
      <Tag className={`${cls} editing`}>
        {multiline ? <textarea rows={3} {...common} /> : <input type="text" {...common} />}
      </Tag>
    );
  }
  return (
    <Tag className={cls}>
      <button type="button" className="inline-edit-btn" data-empty={current ? undefined : "true"}
        aria-label={`Edit ${label}${current ? `: ${current}` : ""}`} onClick={start}>
        {current || placeholder}
      </button>
    </Tag>
  );
}
