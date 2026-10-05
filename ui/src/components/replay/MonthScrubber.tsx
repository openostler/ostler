/**
 * The right-edge month scrubber (spec §5, Google Photos style): one tick per month that has
 * sessions (from GET /sessions/histogram?group=month), newest at the top, year labels at
 * each year's first tick. Drag or tap previews the month in a bubble and jumps on release;
 * the arrow keys step one month and jump at once. A slider for assistive tech.
 */
import { useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import type { SessionHistogram } from "../../api/schemas";
import { indexAt, monthLabel } from "./sessionFormat";

type Bucket = SessionHistogram["buckets"][number];

export function MonthScrubber({ buckets, current, onJump }: {
  /** Month buckets; any order (shown newest first). */
  buckets: readonly Bucket[];
  /** The month ("YYYY-MM") at the top of the list now, if known. */
  current?: string | null;
  onJump: (month: string) => void;
}) {
  const months = [...buckets].filter((b) => b.count > 0).sort((a, b) => (a.key < b.key ? 1 : -1));
  const ref = useRef<HTMLDivElement>(null);
  const [preview, setPreview] = useState<number | null>(null);
  const dragging = useRef(false);
  if (months.length < 2) return null;

  const cur = Math.max(0, months.findIndex((m) => m.key === current));
  const at = (e: ReactPointerEvent) => {
    const r = ref.current!.getBoundingClientRect();
    return indexAt(e.clientY, r.top, r.height, months.length);
  };
  const shown = preview ?? cur;
  const bubble = preview != null ? months[preview] : null;
  const max = Math.max(...months.map((m) => m.count));

  return (
    <div ref={ref} className="logs-scrubber" role="slider" tabIndex={0} aria-label="Jump to month" aria-orientation="vertical"
      aria-valuemin={0} aria-valuemax={months.length - 1} aria-valuenow={shown}
      aria-valuetext={monthLabel(months[shown]!.key)}
      onPointerDown={(e) => {
        dragging.current = true;
        ref.current?.setPointerCapture?.(e.pointerId);
        setPreview(at(e));
      }}
      onPointerMove={(e) => { if (dragging.current) setPreview(at(e)); }}
      onPointerUp={(e) => {
        if (!dragging.current) return;
        dragging.current = false;
        const i = at(e);
        setPreview(null);
        onJump(months[i]!.key);
      }}
      onPointerCancel={() => { dragging.current = false; setPreview(null); }}
      onKeyDown={(e) => {
        const step = e.key === "ArrowDown" || e.key === "PageDown" ? 1 : e.key === "ArrowUp" || e.key === "PageUp" ? -1 : 0;
        const to = e.key === "Home" ? 0 : e.key === "End" ? months.length - 1 : Math.min(months.length - 1, Math.max(0, cur + step));
        if (to === cur && e.key !== "Home") return;
        e.preventDefault();
        onJump(months[to]!.key);
      }}>
      {months.map((m, i) => {
        const yearStart = i === 0 || months[i - 1]!.key.slice(0, 4) !== m.key.slice(0, 4);
        return (
          <span key={m.key} className="logs-tick" data-month={m.key} data-current={i === shown ? "true" : undefined}>
            {yearStart ? <span className="logs-tick-year">{m.key.slice(0, 4)}</span> : null}
            <span className="logs-tick-bar" style={{ width: `${4 + Math.round((m.count / max) * 10)}px` }} />
          </span>
        );
      })}
      {bubble ? (
        <span className="logs-scrub-bubble" style={{ top: `${((preview! + 0.5) / months.length) * 100}%` }} aria-hidden="true">
          {monthLabel(bubble.key, "short")}
        </span>
      ) : null}
    </div>
  );
}
