/**
 * The replay chart strip: up to 3 channels in stacked lanes on one time axis, a shared
 * cursor at the playback time. Tap or drag to seek; drag-select (Select mode or shift-drag)
 * or pinch to zoom; Reset zoom returns to the whole session. Canvas, devicePixelRatio aware,
 * in two layers (data redrawn on data/view/size change; cursor every frame).
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented.
 */
import { useEffect, useMemo, useRef, useState, type PointerEvent as RPointerEvent } from "react";
import { formatClock } from "../../state/playback";
import { lanePaths, msOf, niceTicks, viewFor, xOf, yRange, zoomAround, zoomTo, type View } from "./chartScale";

export type Lane = { name: string; label: string; unit: string };

const LANE_H = 84;
/** Top band of each lane kept for its direct label, so the line never runs under it. */
const LABEL_H = 20;
const GAP = 10;

/** Canvas sized in CSS px × devicePixelRatio, drawing in CSS px. */
function prepare(canvas: HTMLCanvasElement | null, w: number, h: number): CanvasRenderingContext2D | null {
  if (!canvas || w <= 0) return null;
  const dpr = window.devicePixelRatio || 1;
  const W = Math.round(w * dpr);
  const H = Math.round(h * dpr);
  if (canvas.width !== W) canvas.width = W;
  if (canvas.height !== H) canvas.height = H;
  let ctx: CanvasRenderingContext2D | null;
  try { ctx = canvas.getContext("2d"); } catch { return null; }
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}

const cssVar = (el: Element, name: string, dflt: string) => getComputedStyle(el).getPropertyValue(name).trim() || dflt;

export function Chart({ t, ch, lanes, time, start, end, offset, onSeek }: {
  t: number[];
  ch: Record<string, (number | null)[]>;
  lanes: Lane[];
  time: number;
  start: number;
  end: number;
  /** utc − session ms (null: no UTC) for the axis labels. */
  offset: number | null;
  onSeek: (ms: number) => void;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const base = useRef<HTMLCanvasElement>(null);
  const over = useRef<HTMLCanvasElement>(null);
  const [width, setWidth] = useState(0);
  const [zoom, setZoom] = useState<View | null>(null);
  const [selectMode, setSelectMode] = useState(false);
  const [sel, setSel] = useState<{ a: number; b: number } | null>(null);
  const gesture = useRef<{ kind: "seek" | "select" | "pinch"; pts: Map<number, number>; view: View; d0: number; mid: number } | null>(null);

  const height = lanes.length * LANE_H + Math.max(0, lanes.length - 1) * GAP;
  const paged = viewFor(zoom, time, start, end);
  const view = useMemo(() => ({ t0: paged.t0, t1: paged.t1 }), [paged.t0, paged.t1]);

  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const measure = () => setWidth(el.clientWidth);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const ranges = useMemo(() => lanes.map((l) => yRange(t, ch[l.name], view)), [lanes, t, ch, view]);

  // Data layer.
  useEffect(() => {
    const ctx = prepare(base.current, width, height);
    if (!ctx || !wrap.current) return;
    const el = wrap.current;
    const grid = cssVar(el, "--chart-grid", "#e1e0d9");
    ctx.clearRect(0, 0, width, height);
    lanes.forEach((l, i) => {
      const top = i * (LANE_H + GAP);
      const r = ranges[i];
      ctx.save();
      ctx.translate(0, top);
      ctx.strokeStyle = grid;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, LANE_H - 0.5);
      ctx.lineTo(width, LANE_H - 0.5);
      ctx.stroke();
      if (r) {
        ctx.strokeStyle = cssVar(el, `--series-${i + 1}`, "#2a78d6");
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        ctx.translate(0, LABEL_H);
        for (const run of lanePaths(t, ch[l.name], view, width, LANE_H - LABEL_H, r)) {
          ctx.beginPath();
          run.forEach(([x, y], k) => (k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
          if (run.length === 1) ctx.arc(run[0]![0], run[0]![1], 1.5, 0, Math.PI * 2);
          ctx.stroke();
        }
      }
      ctx.restore();
    });
  }, [lanes, ranges, t, ch, view, width, height]);

  // Cursor + selection layer.
  useEffect(() => {
    const ctx = prepare(over.current, width, height);
    if (!ctx || !wrap.current) return;
    ctx.clearRect(0, 0, width, height);
    if (sel) {
      ctx.fillStyle = cssVar(wrap.current, "--chart-select", "rgba(31,111,224,0.15)");
      const [a, b] = [Math.min(sel.a, sel.b), Math.max(sel.a, sel.b)];
      ctx.fillRect(a, 0, b - a, height);
    }
    const x = Math.round(xOf(time, view, width)) + 0.5;
    ctx.strokeStyle = cssVar(wrap.current, "--chart-cursor", "#101317");
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }, [time, view, width, height, sel]);

  const xIn = (e: RPointerEvent) => e.clientX - (over.current?.getBoundingClientRect().left ?? 0);

  const down = (e: RPointerEvent<HTMLCanvasElement>) => {
    e.currentTarget.setPointerCapture?.(e.pointerId);
    const x = xIn(e);
    const g = gesture.current;
    if (g && g.pts.size === 1 && e.pointerType === "touch") {
      // Second finger: pinch around the midpoint (cancels the seek/select in progress).
      const [x0] = [...g.pts.values()] as [number];
      g.pts.set(e.pointerId, x);
      gesture.current = { kind: "pinch", pts: g.pts, view, d0: Math.max(10, Math.abs(x - x0)), mid: msOf((x + x0) / 2, view, width) };
      setSel(null);
      return;
    }
    const select = selectMode || e.shiftKey;
    gesture.current = { kind: select ? "select" : "seek", pts: new Map([[e.pointerId, x]]), view, d0: 0, mid: 0 };
    if (select) setSel({ a: x, b: x });
    else onSeek(msOf(x, view, width));
  };
  const move = (e: RPointerEvent<HTMLCanvasElement>) => {
    const g = gesture.current;
    if (!g || !g.pts.has(e.pointerId)) return;
    const x = xIn(e);
    g.pts.set(e.pointerId, x);
    if (g.kind === "seek") onSeek(msOf(x, g.view, width));
    else if (g.kind === "select") setSel((s) => (s ? { ...s, b: x } : s));
    else if (g.pts.size >= 2) {
      const [a, b] = [...g.pts.values()] as [number, number];
      const d = Math.max(10, Math.abs(a - b));
      setZoom(zoomAround(g.view, g.mid, g.d0 / d, start, end));
    }
  };
  const up = (e: RPointerEvent<HTMLCanvasElement>) => {
    const g = gesture.current;
    if (!g) return;
    g.pts.delete(e.pointerId);
    if (g.kind === "select" && sel && Math.abs(sel.b - sel.a) > 8) {
      setZoom(zoomTo(msOf(sel.a, g.view, width), msOf(sel.b, g.view, width), start, end));
      setSelectMode(false);
    }
    if (g.kind === "select") setSel(null);
    if (g.pts.size === 0) gesture.current = null;
  };

  const zoomed = zoom != null;
  const ticks = niceTicks(view.t0, view.t1, 3).filter((v) => v > view.t0 && v < view.t1);

  return (
    <div className="replay-chart card">
      <div className="replay-chart-head">
        <span className="kicker">Chart</span>
        <div className="replay-chart-tools">
          <button className="rchip" aria-pressed={selectMode} onClick={() => setSelectMode((m) => !m)}
            title="Drag across the chart to zoom to that span">Select to zoom</button>
          {zoomed ? <button className="rchip" onClick={() => setZoom(null)}>Reset zoom</button> : null}
        </div>
      </div>
      {lanes.length === 0 ? <p className="muted small">No channels to chart in this session.</p> : (
        <div className="replay-chart-plot" ref={wrap} style={{ height }}>
          <canvas ref={base} className="replay-canvas" style={{ height }} aria-hidden="true" />
          <canvas ref={over} className="replay-canvas replay-canvas-over" style={{ height }}
            role="img" aria-label={`Chart of ${lanes.map((l) => l.label).join(", ")}; cursor at ${formatClock(time, offset)}. Tap or drag to seek.`}
            onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} />
          {lanes.map((l, i) => (
            <div key={l.name} className="replay-lane-label small" style={{ top: i * (LANE_H + GAP) }}>
              <span className="replay-swatch" style={{ background: `var(--series-${i + 1})` }} aria-hidden="true" />
              {l.label}{l.unit ? <span className="muted"> · {l.unit}</span> : null}
            </div>
          ))}
        </div>
      )}
      <div className="replay-chart-axis small muted" aria-hidden="true">
        <span>{formatClock(view.t0, offset)}</span>
        {ticks.length && width > 260 ? <span>{formatClock(ticks[Math.floor(ticks.length / 2)]!, offset)}</span> : null}
        <span>{formatClock(view.t1, offset)}</span>
      </div>
    </div>
  );
}
