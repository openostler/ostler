// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * "This year" strip (spec §5, Strava-calendar style): one cell per day of `year`, weeks as
 * columns (Monday on top), shaded by distance (count when no distance). Days with sessions
 * are buttons; tapping one filters the list to that day. Scrolls sideways on a phone, opened
 * at today's end.
 */
import { useEffect, useRef } from "react";
import type { SessionHistogram } from "../../api/schemas";
import { dayLabelShort, heatLevel, localDay } from "./sessionFormat";

export function YearHeatmap({ year, hist, selected, onPick }: {
  year: number;
  hist: SessionHistogram | null;
  /** The day currently filtered to ("YYYY-MM-DD"), shown pressed. */
  selected?: string | null;
  onPick: (day: string) => void;
}) {
  const scroller = useRef<HTMLDivElement>(null);
  const has = !!hist && hist.buckets.some((b) => b.key.startsWith(`${year}-`) && b.count > 0);
  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollLeft = el.scrollWidth; // the newest weeks first
  }, [has]);
  if (!hist || !has) return null;

  const byDay = new Map(hist.buckets.map((b) => [b.key, b]));
  const useKm = hist.buckets.some((b) => b.km > 0);
  const max = Math.max(...hist.buckets.map((b) => (useKm ? b.km : b.count)));
  const first = new Date(year, 0, 1);
  const lead = (first.getDay() + 6) % 7; // Monday-first offset
  const days: Date[] = [];
  for (let d = new Date(first); d.getFullYear() === year; d.setDate(d.getDate() + 1)) days.push(new Date(d));
  const total = days.reduce((n, d) => n + (byDay.get(localDay(d))?.count ?? 0), 0);

  return (
    <section className="logs-heat" aria-label={`This year: ${total} session${total === 1 ? "" : "s"} in ${year}`}>
      <h3 className="kicker">This year</h3>
      <div className="logs-heat-scroll" ref={scroller}>
        <div className="logs-heat-grid">
          {Array.from({ length: lead }, (_, i) => <span key={`pad${i}`} className="logs-heat-cell pad" />)}
          {days.map((d) => {
            const key = localDay(d);
            const b = byDay.get(key);
            if (!b || b.count <= 0) return <span key={key} className="logs-heat-cell" data-day={key} />;
            const level = heatLevel(useKm ? b.km : b.count, max);
            const label = `${dayLabelShort(key)}: ${b.count} session${b.count === 1 ? "" : "s"}${b.km > 0 ? `, ${b.km.toFixed(1)} km` : ""}`;
            return (
              <button key={key} type="button" className="logs-heat-cell on" data-day={key} data-level={level}
                aria-label={label} title={label} aria-pressed={selected === key} onClick={() => onPick(key)} />
            );
          })}
        </div>
      </div>
    </section>
  );
}
