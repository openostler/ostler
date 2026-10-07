// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import type { Note } from "../api/schemas";
import { saveFlagOptions, useFlagOptions, type Flag, type FlagSeverity } from "../lib/flags";
import { parseFault } from "../lib/format";
import { noteSpan } from "../lib/notes";
import { short } from "../lib/range";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { RangeBar } from "./RangeBar";
import { RecordingOptions } from "./RecordingOptions";
import { Sheet } from "./Sheet";
import { Icon, type SymbolName } from "../icons/Icon";

/** What the chip, a tick or a notes-panel row opens: an automatic flag or a manual note. */
export type FlagSheetItem = { flag: Flag } | { note: Note };

/** Severity as icon + word (colour is never the only cue — ui/CLAUDE.md). */
export const SEVERITY: Record<FlagSeverity, { icon: SymbolName; word: string }> = {
  warn: { icon: "warning", word: "Warning" },
  alarm: { icon: "error", word: "Alarm" },
};

/** "45 s", "2 min 5 s", "1 h 3 min". */
export function formatDuration(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s} s`;
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  if (h) return `${h} h${m ? ` ${m} min` : ""}`;
  return `${m} min${r ? ` ${r} s` : ""}`;
}

const unitText = (unit?: string) => (unit ? ` ${unit}` : "");

/**
 * The flag sheet (spec §8): what a flag or note on the transport is about — title with severity,
 * time and duration, the peak against its normal band (out of range) or each fault with
 * Current/Logged, and Jump to · Keep as note · Mute this sensor · Flag settings.
 */
export function FlagSheet({ item, onClose }: { item: FlagSheetItem; onClose(): void }) {
  const r = useReplay();
  const { snap, fields, toast, faultMeaning } = useApp();
  const opts = useFlagOptions();
  const [settings, setSettings] = useState(false);
  if (settings) return <RecordingOptions onClose={onClose} />;

  const jump = (t: number) => {
    r.setFollow(false);
    r.seek(t);
    onClose();
  };

  if ("note" in item) {
    const n = item.note;
    return (
      <Sheet title={<span><Icon name="flag" size="1.1em" className="icon-inline" /> {n.text || n.tags.join(", ") || n.kind}</span>} onClose={onClose}>
        <div className="flagsheet">
          <div className="flagsheet-meta small">
            <span className="flagsheet-kind">Note</span> · <span className="note-t">{noteSpan(n)}</span>
            {n.t_end != null ? <> · {formatDuration(n.t_end - n.t)}</> : null}
          </div>
          {n.tags.length ? (
            <div className="flagsheet-tags">{n.tags.map((tag) => <span key={tag} className="note-chip">{tag}</span>)}</div>
          ) : null}
          <div className="flagsheet-actions">
            <button className="btn accent" onClick={() => jump(n.t)}>Jump to</button>
          </div>
        </div>
      </Sheet>
    );
  }

  const f = item.flag;
  const sev = SEVERITY[f.severity];
  const field = f.signal ? fields[f.signal] : undefined;
  const sensor = field?.label || f.signal || "";
  const canKeep = r.active && !r.session?.synthetic && !snap?.public;

  const keep = async () => {
    try {
      const n = await r.addNote({ t: f.t, t_end: f.t_end, text: f.label, tags: ["auto", f.kind] });
      if (!n) { toast("Could not save the note", true); return; }
      toast("Kept as a note");
      onClose();
    } catch {
      toast("Could not save the note", true);
    }
  };
  const mute = () => {
    if (!f.signal) return;
    if (!opts.muted.includes(f.signal)) saveFlagOptions({ ...opts, muted: [...opts.muted, f.signal] });
    toast(`Muted ${sensor} — change it in Flag settings`);
    onClose();
  };

  // the bar's scale: the field's span, else everything we know about this excursion
  const known = [f.band?.[0], f.band?.[1], f.limits?.[0], f.limits?.[1], f.peak].filter((v): v is number => typeof v === "number");
  const span = field?.span ?? (known.length ? ([Math.min(...known), Math.max(...known)] as const) : null);

  return (
    <Sheet onClose={onClose} title={
      <span className={`flagsheet-title ${f.severity}`}>
        <span className={`flag-sev ${f.severity}`}><span className="si" aria-hidden="true"><Icon name={sev.icon} size="1.1em" /></span>{sev.word}</span>
        <span className="flagsheet-label">{f.label}</span>
      </span>
    }>
      <div className="flagsheet">
        <div className="flagsheet-meta small">
          <span className="note-t">{noteSpan(f)}</span>
          {f.t_end != null ? <> · {formatDuration(f.t_end - f.t)}</> : null}
        </div>

        {f.kind === "range" && f.peak != null ? (
          <div className="flagsheet-range">
            <div>
              Peak <b>{short(f.peak)}{unitText(f.unit)}</b>
              {f.peakT != null ? <> at <span className="note-t">{noteSpan({ t: f.peakT, t_end: null })}</span></> : null}
            </div>
            {f.band ? <div className="small muted">Normal {short(f.band[0])}–{short(f.band[1])}{unitText(f.unit)}</div> : null}
            {span ? (
              <RangeBar value={f.peak} span={span} normal={f.band ?? null} alarm={f.severity === "alarm"}
                label={sensor || f.label} unit={f.unit ?? ""} />
            ) : null}
          </div>
        ) : null}

        {f.kind === "fault" && f.faults?.length ? (
          <ul className="flagsheet-faults">
            {f.faults.map((raw) => {
              const p = parseFault(raw);
              const current = p.tag ? p.current : !!f.current;
              const meaning = faultMeaning(raw) ?? faultMeaning(p.text);
              return (
                <li key={raw} className={`fault ${current ? "current" : "logged"}`}>
                  <div>
                    {p.raw ? <b className="flagsheet-code">{p.raw} </b> : null}
                    {p.text}
                    <span className={`flag-sev ${current ? "alarm" : "warn"}`}>
                      <span className="si" aria-hidden="true">{current ? SEVERITY.alarm.icon : SEVERITY.warn.icon}</span>
                      {current ? "Current" : "Logged"}
                    </span>
                  </div>
                  {meaning?.description ? <div className="small muted">{meaning.description}</div> : null}
                </li>
              );
            })}
          </ul>
        ) : null}

        {f.folded ? <p className="small muted">{f.folded} more flags folded to avoid a flood.</p> : null}

        <div className="flagsheet-actions">
          <button className="btn accent" onClick={() => jump(f.t)}>Jump to</button>
          {canKeep ? <button className="btn" onClick={() => void keep()}>Keep as note</button> : null}
          {f.kind === "range" && f.signal ? <button className="btn" onClick={mute}>Mute this sensor</button> : null}
          <button className="btn" onClick={() => setSettings(true)}>Flag settings</button>
        </div>
      </div>
    </Sheet>
  );
}
