// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The channel picker (spec §5 "ChannelPicker"): a bottom sheet with pinned and recent chips,
 * search over label / unit / name with the matches highlighted, collapsible categories and a
 * pin toggle on every row. Used for each chart lane and for traces A and B.
 */
import { useMemo, useState } from "react";
import { Sheet } from "../Sheet";
import { groupChannels, highlight, loadPins, loadRecent, pushRecent, searchChannels, togglePin, type Category, type PickerChannel } from "./channels";

export function ChannelPicker({ title, channels, value, onPick, onClose, onRemove, removeLabel = "Remove" }: {
  title: string;
  channels: PickerChannel[];
  /** The channel currently in this slot (marked as selected). */
  value: string | null;
  onPick: (name: string) => void;
  onClose: () => void;
  /** Offered for optional slots (trace B, extra chart lanes). */
  onRemove?: () => void;
  removeLabel?: string;
}) {
  const names = useMemo(() => channels.map((c) => c.name), [channels]);
  const [pins, setPins] = useState(() => loadPins(names));
  const [recent] = useState(loadRecent);
  const [q, setQ] = useState("");
  const [closed, setClosed] = useState<Set<Category>>(() => new Set());
  const byName = useMemo(() => new Map(channels.map((c) => [c.name, c])), [channels]);
  const found = useMemo(() => searchChannels(channels, q), [channels, q]);
  const groups = useMemo(() => groupChannels(found), [found]);
  const searching = q.trim() !== "";

  const pick = (n: string) => {
    pushRecent(recent, n); // persisted now: the sheet closes on pick
    onPick(n);
    onClose();
  };
  const chips = (list: string[]) => list.map((n) => byName.get(n)).filter((c): c is PickerChannel => !!c);
  const pinned = chips(pins);
  const recents = chips(recent).filter((c) => !pins.includes(c.name));

  return (
    <Sheet title={title} onClose={onClose}>
      <div className="cpick" aria-label={title} role="group">
        <input className="input cpick-search" type="search" placeholder="Search label, unit or name" aria-label="Search channels"
          value={q} onChange={(e) => setQ(e.target.value)} autoComplete="off" />
        {!searching && (pinned.length || recents.length) ? (
          <div className="cpick-chips">
            {pinned.length ? <ChipRow label="Pinned" rows={pinned} value={value} onPick={pick} /> : null}
            {recents.length ? <ChipRow label="Recent" rows={recents} value={value} onPick={pick} /> : null}
          </div>
        ) : null}
        {groups.length === 0 ? <p className="muted small">No channel matches “{q}”.</p> : null}
        <div className="cpick-groups">
          {groups.map((g) => {
            const open = searching || !closed.has(g.category);
            return (
              <section key={g.category} className="cpick-group" data-category={g.category}>
                <button type="button" className="cpick-cat" aria-expanded={open}
                  onClick={() => setClosed((s) => { const n = new Set(s); if (n.has(g.category)) n.delete(g.category); else n.add(g.category); return n; })}>
                  <span aria-hidden="true">{open ? "▾" : "▸"}</span> {g.category} <span className="muted">· {g.rows.length}</span>
                </button>
                {open ? (
                  <ul className="cpick-rows">
                    {g.rows.map((c) => {
                      const pinnedRow = pins.includes(c.name);
                      return (
                        <li key={c.name} className="cpick-row" data-channel={c.name}>
                          <button type="button" className="cpick-pick" aria-current={c.name === value ? "true" : undefined} onClick={() => pick(c.name)}>
                            <span className="cpick-label"><Hl text={c.label} q={q} /></span>
                            <span className="cpick-meta small muted">
                              {c.unit ? <><Hl text={c.unit} q={q} /> · </> : null}<span className="mono"><Hl text={c.name} q={q} /></span>
                            </span>
                          </button>
                          <button type="button" className="cpick-pin" aria-pressed={pinnedRow}
                            aria-label={`${pinnedRow ? "Unpin" : "Pin"} ${c.label}`} onClick={() => setPins((p) => togglePin(p, c.name))}>
                            {pinnedRow ? "★" : "☆"}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </section>
            );
          })}
        </div>
        {onRemove ? (
          <button type="button" className="btn block" onClick={() => { onRemove(); onClose(); }}>{removeLabel}</button>
        ) : null}
      </div>
    </Sheet>
  );
}

function ChipRow({ label, rows, value, onPick }: { label: string; rows: PickerChannel[]; value: string | null; onPick: (n: string) => void }) {
  return (
    <div className="cpick-chiprow" role="group" aria-label={label}>
      <span className="kicker">{label}</span>
      {rows.map((c) => (
        <button key={c.name} type="button" className="rchip" aria-pressed={c.name === value} onClick={() => onPick(c.name)}>{c.label}</button>
      ))}
    </div>
  );
}

function Hl({ text, q }: { text: string; q: string }) {
  return <>{highlight(text, q).map((p, i) => (p.hit ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>))}</>;
}
