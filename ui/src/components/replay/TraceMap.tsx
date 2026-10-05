/**
 * The replay map. MapLibre is loaded on demand (`import("./maplibre")`); when it can't start
 * (no WebGL, chunk failed to load) a plain SVG drawing of the same coloured lanes stands in,
 * so a replay still works without a map.
 *
 * Two traces (spec §5 "Map"): A, and an optional B drawn as a parallel lane (`line-offset`
 * A −3 px, B +3 px). The basemap switch (Streets / Satellite / Hybrid) only toggles layer
 * visibility, so the traces never need re-adding.
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { loadBasemap, satelliteSource, saveBasemap, type Basemap } from "./basemap";
import { BasemapSwitch } from "./BasemapSwitch";
import type { TraceMapHandle } from "./maplibre";
import { LANE_OFFSET, NO_VALUE_COLOR, offsetPolyline, type BBox, type Cursor, type FeatureCollection, type TraceLane } from "./trace";

export type MapTrace = { fc: FeatureCollection; color: unknown[]; colors: readonly string[] };
type Props = { a: MapTrace | null; b: MapTrace | null; bbox: BBox | null; cursor: Cursor | null };

const LANES: TraceLane[] = ["a", "b"];

export function TraceMap({ a, b, bbox, cursor }: Props) {
  const box = useRef<HTMLDivElement>(null);
  const handle = useRef<TraceMapHandle | null>(null);
  const [status, setStatus] = useState<"loading" | "map" | "blank" | "failed">("loading");
  const [basemap, setBasemapState] = useState<Basemap>(loadBasemap);
  const latest = useRef({ a, b, cursor, basemap });
  useEffect(() => { latest.current = { a, b, cursor, basemap }; });

  const setBasemap = (m: Basemap) => {
    setBasemapState(m);
    saveBasemap(m);
  };

  // Create once per bbox value (a live re-fetch brings a new but equal array: no rebuild).
  const bboxKey = bbox ? bbox.join(",") : "";
  useEffect(() => {
    let alive = true;
    const bounds = bboxKey ? (bboxKey.split(",").map(Number) as BBox) : null;
    import("./maplibre")
      .then((m) => {
        if (!alive || !box.current) return;
        const l = latest.current;
        const h = m.createTraceMap({
          container: box.current, bbox: bounds,
          traces: { a: l.a?.fc ?? null, b: l.b?.fc ?? null },
          colors: { a: l.a?.color ?? [], b: l.b?.color ?? [] },
          basemap: l.basemap, satellite: satelliteSource(bounds),
          onBlank: () => alive && setStatus("blank"),
        });
        h.setCursor(l.cursor);
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

  const [aFc, bFc, aColor, bColor] = [a?.fc ?? null, b?.fc ?? null, a?.color, b?.color];
  useEffect(() => { handle.current?.setTrace("a", aFc); }, [aFc, status]);
  useEffect(() => { handle.current?.setTrace("b", bFc); }, [bFc, status]);
  useEffect(() => { if (aColor) handle.current?.setColor("a", aColor); }, [aColor, status]);
  useEffect(() => { if (bColor) handle.current?.setColor("b", bColor); }, [bColor, status]);
  useEffect(() => { handle.current?.setBasemap(basemap); }, [basemap, status]);
  useEffect(() => { handle.current?.setCursor(cursor); }, [cursor, status]);

  return (
    <div className="replay-map" data-map-status={status} data-basemap={basemap}>
      {status === "failed" ? (
        <SvgTrace lanes={{ a, b }} cursor={cursor} bbox={bbox} />
      ) : (
        <div ref={box} className="replay-map-gl" role="region" aria-label="Session map" />
      )}
      {status === "map" ? <BasemapSwitch value={basemap} onChange={setBasemap} /> : null}
      {status === "blank" ? <div className="replay-map-note">Map tiles unavailable — trace only</div> : null}
      {status === "failed" ? <div className="replay-map-note">Map unavailable on this device — trace only</div> : null}
    </div>
  );
}

/** The no-WebGL stand-in: the same segments, equirectangular (cos-lat scaled), no tiles,
 * both lanes offset sideways like the map's `line-offset`. */
function SvgTrace({ lanes, cursor, bbox }: { lanes: Record<TraceLane, MapTrace | null>; cursor: Cursor | null; bbox: BBox | null }) {
  const pts = useMemo(() => LANES.flatMap((l) => lanes[l]?.fc.features.flatMap((f) => f.geometry.coordinates) ?? []), [lanes]);
  const b: BBox | null = bbox ?? (pts.length
    ? [Math.min(...pts.map((p) => p[0])), Math.min(...pts.map((p) => p[1])), Math.max(...pts.map((p) => p[0])), Math.max(...pts.map((p) => p[1]))]
    : null);
  if (!b) return <div className="replay-map-empty" role="img" aria-label="No GPS track">No GPS track in this session</div>;
  const k = Math.cos((((b[1] + b[3]) / 2) * Math.PI) / 180);
  const w = Math.max((b[2] - b[0]) * k, 1e-6);
  const h = Math.max(b[3] - b[1], 1e-6);
  const s = 1000 / Math.max(w, h);
  const xy = (p: readonly [number, number]): [number, number] => [(p[0] - b[0]) * k * s, (b[3] - p[1]) * s];
  const str = (q: readonly [number, number]) => `${q[0].toFixed(1)},${q[1].toFixed(1)}`;
  // The viewBox is ~1000 units across; the map draws 4 px lines 3 px apart in ~360 px.
  const unit = 2.5;
  const two = !!lanes.a && !!lanes.b;
  return (
    <svg className="replay-svg" viewBox={`-30 -30 ${w * s + 60} ${h * s + 60}`} role="img" aria-label="Session trace">
      {LANES.map((l) => {
        const t = lanes[l];
        if (!t) return null;
        const off = two ? LANE_OFFSET[l] * unit : 0;
        return (
          <g key={l} data-lane={l} strokeLinecap="round" strokeLinejoin="round" fill="none">
            {t.fc.features.map((f, i) => (
              <polyline key={i} points={offsetPolyline(f.geometry.coordinates.map(xy), off).map(str).join(" ")}
                stroke={t.colors[f.properties.b] ?? NO_VALUE_COLOR} strokeWidth={8} />
            ))}
          </g>
        );
      })}
      {cursor ? (
        <g transform={`translate(${str(xy([cursor.lon, cursor.lat])).replace(",", " ")}) rotate(${cursor.heading ?? 0})`} className="replay-svg-cursor">
          <path d="M0 -22 L16 18 L0 9 L-16 18 Z" />
        </g>
      ) : null}
    </svg>
  );
}
