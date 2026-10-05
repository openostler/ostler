/**
 * The Logs search box and filter chips (spec §5): search (debounced 300 ms → `q`), date range
 * (`from`/`to`), module, has notes, minimum distance. Every change goes to the parent at once
 * except typing, which waits for a 300 ms pause.
 */
import { useEffect, useRef, useState } from "react";
import { filtersActive, type SessionFilters as Filters } from "../../api/useSessions";
import { moduleNames } from "../../layout";
import { dayLabelShort, MIN_KM_STEPS, SEARCH_DEBOUNCE_MS } from "./sessionFormat";


export function SessionFilters({ value, onChange }: { value: Filters; onChange: (f: Filters) => void }) {
  const [text, setText] = useState(value.q ?? "");
  const [dates, setDates] = useState(false);
  // Keep the latest props for the debounce timer without re-arming it on every render.
  const latest = useRef({ value, onChange });
  useEffect(() => { latest.current = { value, onChange }; });

  // A cleared or replaced q from outside (e.g. "Clear filters") shows in the box.
  const [shownQ, setShownQ] = useState(value.q ?? "");
  if ((value.q ?? "") !== shownQ) {
    setShownQ(value.q ?? "");
    setText(value.q ?? "");
  }

  useEffect(() => {
    if (text === (latest.current.value.q ?? "")) return;
    const id = window.setTimeout(() => {
      const { value: v, onChange: set } = latest.current;
      set({ ...v, q: text });
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(id);
  }, [text]);

  const set = (patch: Partial<Filters>) => onChange({ ...value, ...patch });
  const dateText = value.from || value.to
    ? value.from && value.from === value.to
      ? dayLabelShort(value.from)
      : `${value.from ? dayLabelShort(value.from) : "…"} – ${value.to ? dayLabelShort(value.to) : "…"}`
    : "Dates";

  return (
    <div className="logs-filters stack">
      <input className="input logs-search" type="search" placeholder="Search names, places, notes" aria-label="Search sessions"
        value={text} onChange={(e) => setText(e.target.value)} />
      <div className="logs-chips" role="group" aria-label="Filters">
        <button type="button" className="rchip" aria-pressed={!!(value.from || value.to)} aria-expanded={dates}
          onClick={() => setDates((d) => !d)}>{dateText}</button>
        <select className="rchip logs-select" aria-label="Module" value={value.module ?? ""}
          data-active={value.module ? "true" : undefined}
          onChange={(e) => set({ module: e.target.value || undefined })}>
          <option value="">Any module</option>
          {moduleNames().map(([k, name]) => <option key={k} value={k}>{name}</option>)}
        </select>
        <button type="button" className="rchip" aria-pressed={!!value.has_notes}
          onClick={() => set({ has_notes: !value.has_notes || undefined })}>Has notes</button>
        <select className="rchip logs-select" aria-label="Minimum distance" value={value.min_km ?? ""}
          data-active={value.min_km ? "true" : undefined}
          onChange={(e) => set({ min_km: e.target.value ? Number(e.target.value) : undefined })}>
          <option value="">Any distance</option>
          {MIN_KM_STEPS.map((k) => <option key={k} value={k}>≥ {k} km</option>)}
        </select>
        {filtersActive(value) ? (
          <button type="button" className="rchip" onClick={() => { setText(""); onChange({}); }}>Clear</button>
        ) : null}
      </div>
      {dates ? (
        <div className="logs-dates card" role="group" aria-label="Date range">
          <label className="small">From
            <input className="input" type="date" aria-label="From date" value={value.from ?? ""} max={value.to || undefined}
              onChange={(e) => set({ from: e.target.value || undefined })} />
          </label>
          <label className="small">To
            <input className="input" type="date" aria-label="To date" value={value.to ?? ""} min={value.from || undefined}
              onChange={(e) => set({ to: e.target.value || undefined })} />
          </label>
          {value.from || value.to ? (
            <button type="button" className="rchip" onClick={() => set({ from: undefined, to: undefined })}>Any date</button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
