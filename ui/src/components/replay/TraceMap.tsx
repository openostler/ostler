/**
 * The replay map. MapLibre is loaded on demand (`import("./maplibre")`); when it can't start
 * (no WebGL, chunk failed to load) a plain SVG drawing of the same coloured trace stands in,
 * so a replay still works without a map.
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented.
 */
import { useEffect, useRef, useState } from "react";
import type { TraceMapHandle } from "./maplibre";
import { NO_VALUE_COLOR, RAMP, type BBox, type Cursor, type FeatureCollection } from "./trace";

type Props = { trace: FeatureCollection; color: unknown[]; bbox: BBox | null; cursor: Cursor | null };

export function TraceMap({ trace, color, bbox, cursor }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const handle = useRef<TraceMapHandle | null>(null);
  const [status, setStatus] = useState<"loading" | "map" | "blank" | "failed">("loading");
  const latest = useRef({ trace, color, cursor });
  useEffect(() => { latest.current = { trace, color, cursor }; });

  // Create once per bbox value (a live re-fetch brings a new but equal array: no rebuild).
  const bboxKey = bbox ? bbox.join(",") : "";
  useEffect(() => {
    let alive = true;
    const bounds = bboxKey ? (bboxKey.split(",").map(Number) as BBox) : null;
    import("./maplibre")
      .then((m) => {
        if (!alive || !box.current) return;
        const h = m.createTraceMap({
          container: box.current, bbox: bounds, trace: latest.current.trace, color: latest.current.color,
          onBlank: () => alive && setStatus("blank"),
        });
        h.setCursor(latest.current.cursor);
        handle.current = h;
        setStatus(h.isBlank() ? "blank" : "map");
      })
      .catch((e: unknown) => {
        console.warn("replay map unavailable", e);
        if (alive) setStatus("failed");
      });
    return () => {
      alive = false;
      handle.current?.destroy();
      handle.current = null;
    };
  }, [bboxKey]);

  useEffect(() => { handle.current?.setTrace(trace); }, [trace, status]);
  useEffect(() => { handle.current?.setColor(color); }, [color, status]);
  useEffect(() => { handle.current?.setCursor(cursor); }, [cursor, status]);

  return (
    <div className="replay-map" data-map-status={status}>
      {status === "failed" ? (
        <SvgTrace trace={trace} cursor={cursor} bbox={bbox} />
      ) : (
        <div ref={box} className="replay-map-gl" role="region" aria-label="Session map" />
      )}
      {status === "blank" ? <div className="replay-map-note">Map tiles unavailable — trace only</div> : null}
      {status === "failed" ? <div className="replay-map-note">Map unavailable on this device — trace only</div> : null}
    </div>
  );
}

/** The no-WebGL stand-in: the same segments, equirectangular (cos-lat scaled), no tiles. */
function SvgTrace({ trace, cursor, bbox }: { trace: FeatureCollection; cursor: Cursor | null; bbox: BBox | null }) {
  const pts = trace.features.flatMap((f) => f.geometry.coordinates);
  const b: BBox | null = bbox ?? (pts.length
    ? [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))]
    : null);
  if (!b) return <div className="replay-map-empty" role="img" aria-label="No GPS track">No GPS track in this session</div>;
  const k = Math.cos((((b[1] + b[3]) / 2) * Math.PI) / 180);
  const w = Math.max((b[2] - b[0]) * k, 1e-6);
  const h = Math.max(b[3] - b[1], 1e-6);
  const s = 1000 / Math.max(w, h);
  const xy = (p: readonly [number, number]) => `${((p[0] - b[0]) * k * s).toFixed(1)},${((b[3] - p[1]) * s).toFixed(1)}`;
  return (
    <svg className="replay-svg" viewBox={`-30 -30 ${w * s + 60} ${h * s + 60}`} role="img" aria-label="Session trace">
      {trace.features.map((f, i) => (
        <polyline key={i} points={f.geometry.coordinates.map(xy).join(" ")}
          stroke={RAMP[f.properties.b] ?? NO_VALUE_COLOR} strokeWidth={8} fill="none" strokeLinecap="round" strokeLinejoin="round" />
      ))}
      {cursor ? (
        <g transform={`translate(${xy([cursor.lon, cursor.lat]).replace(",", " ")}) rotate(${cursor.heading ?? 0})`} className="replay-svg-cursor">
          <path d="M0 -22 L16 18 L0 9 L-16 18 Z" />
        </g>
      ) : null}
    </svg>
  );
}
