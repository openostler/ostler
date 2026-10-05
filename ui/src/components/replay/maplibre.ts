/**
 * The ONLY module that imports MapLibre GL. It is loaded with `import("./maplibre")` from
 * TraceMap, so MapLibre (and its CSS and worker) live in lazy chunks, never the main one
 * (spec: "lazy-loaded with import()"; guarded by maplibreChunk.test.ts).
 *
 * Approach informed by DovesDataviewer (GPL-3.0), independently implemented.
 */
import type { ExpressionSpecification, StyleSpecification } from "@maplibre/maplibre-gl-style-spec";
import { AttributionControl, Map as MlMap, Marker, NavigationControl, setWorkerUrl, type GeoJSONSource } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import { casingFor, layerVisible, type Basemap, type SatSource } from "./basemap";
import { LANE_OFFSET, type BBox, type Cursor, type FeatureCollection, type TraceLane } from "./trace";

setWorkerUrl(workerUrl);

/** OpenFreeMap vector tiles (no key; attribution carried by the style). ADR-0009. */
export const ONLINE_STYLE = "https://tiles.openfreemap.org/styles/liberty";
/** Before the online style answers, give up after this long and draw the trace alone. */
const STYLE_TIMEOUT_MS = 8_000;

/** Offline / failed style: a plain background, so only the trace shows. */
export const BLANK_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "bg", type: "background", paint: { "background-color": "#eef0f2" } }],
};

export type TraceMapHandle = {
  /** A lane's segments; null hides that lane (trace B is optional). */
  setTrace: (lane: TraceLane, fc: FeatureCollection | null) => void;
  setColor: (lane: TraceLane, expr: unknown[]) => void;
  /** Streets / Satellite / Hybrid: only layout visibility changes, so the traces survive. */
  setBasemap: (b: Basemap) => void;
  setCursor: (c: Cursor | null) => void;
  /** True once the map fell back to the blank style. */
  isBlank: () => boolean;
  destroy: () => void;
};

const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] };
const LANES: TraceLane[] = ["a", "b"];
/** Our own layers (never touched by the basemap switch). */
const OWN = (id: string) => id.startsWith("trace-");

function arrowEl(): HTMLElement {
  const el = document.createElement("div");
  el.className = "replay-arrow";
  el.setAttribute("aria-hidden", "true");
  el.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M12 2 L20 21 L12 16.5 L4 21 Z"/></svg>';
  return el;
}

/** Create the replay map. Throws when WebGL is unavailable (the caller shows a fallback). */
export function createTraceMap(opts: {
  container: HTMLElement;
  bbox: BBox | null;
  traces: Record<TraceLane, FeatureCollection | null>;
  colors: Record<TraceLane, unknown[]>;
  basemap: Basemap;
  satellite: SatSource;
  onBlank?: () => void;
}): TraceMapHandle {
  const traces = { ...opts.traces };
  const colors = { ...opts.colors };
  let basemap = opts.basemap;
  let blank = typeof navigator !== "undefined" && navigator.onLine === false;

  const map = new MlMap({
    container: opts.container,
    style: blank ? BLANK_STYLE : ONLINE_STYLE,
    attributionControl: false,
    ...(opts.bbox ? { bounds: opts.bbox, fitBoundsOptions: { padding: 32 } } : {}),
    dragRotate: false,
    pitchWithRotate: false,
  });
  map.addControl(new AttributionControl({ compact: false }), "bottom-right");
  map.addControl(new NavigationControl({ showCompass: false }), "top-right");
  map.touchZoomRotate.disableRotation();

  const toBlank = () => {
    if (blank) return;
    blank = true;
    map.setStyle(BLANK_STYLE, { diff: false });
    opts.onBlank?.();
  };
  const timer = window.setTimeout(() => { if (!map.isStyleLoaded()) toBlank(); }, STYLE_TIMEOUT_MS);
  // Style or vector tile failure (offline, blocked, server down) → the trace on a plain
  // background. An imagery tile failing only leaves holes in the imagery.
  map.on("error", (e) => { if ((e as { sourceId?: string }).sourceId !== "satellite") toBlank(); });

  const applyBasemap = () => {
    for (const l of map.getStyle()?.layers ?? []) {
      if (OWN(l.id)) continue;
      map.setLayoutProperty(l.id, "visibility", layerVisible(l, basemap) ? "visible" : "none");
    }
    const casing = casingFor(basemap);
    for (const lane of LANES) {
      const id = `trace-${lane}-casing`;
      if (!map.getLayer(id)) continue;
      map.setPaintProperty(id, "line-color", casing.color);
      map.setPaintProperty(id, "line-opacity", casing.opacity);
    }
  };

  // (Re-)add the imagery and our layers after every style load (the blank swap drops them).
  const addLayers = () => {
    if (!map.getSource("satellite")) {
      map.addSource("satellite", {
        type: "raster", tiles: [opts.satellite.tiles], tileSize: 256, maxzoom: opts.satellite.maxzoom,
        attribution: opts.satellite.attribution,
      });
      // Below the first label layer, so Hybrid keeps the names on top of the imagery.
      const firstSymbol = map.getStyle()?.layers?.find((l) => l.type === "symbol")?.id;
      map.addLayer({ id: "satellite", type: "raster", source: "satellite", layout: { visibility: "none" } }, firstSymbol);
    }
    const casing = casingFor(basemap);
    for (const lane of LANES) {
      const src = `trace-${lane}`;
      if (map.getSource(src)) continue;
      const offset = LANE_OFFSET[lane];
      map.addSource(src, { type: "geojson", data: (traces[lane] ?? EMPTY) as never });
      map.addLayer({
        id: `trace-${lane}-casing`, type: "line", source: src,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": casing.color, "line-width": 7, "line-opacity": casing.opacity, "line-offset": offset },
      });
      map.addLayer({
        id: `trace-${lane}`, type: "line", source: src,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": colors[lane] as ExpressionSpecification, "line-width": 4, "line-offset": offset },
      });
    }
    applyBasemap();
  };
  map.on("style.load", addLayers);
  if (map.isStyleLoaded()) addLayers();

  const marker = new Marker({ element: arrowEl(), rotationAlignment: "map", pitchAlignment: "map" });
  let markerOn = false;

  return {
    setTrace(lane, fc) {
      traces[lane] = fc;
      (map.getSource(`trace-${lane}`) as GeoJSONSource | undefined)?.setData((fc ?? EMPTY) as never);
    },
    setColor(lane, expr) {
      colors[lane] = expr;
      if (map.getLayer(`trace-${lane}`)) map.setPaintProperty(`trace-${lane}`, "line-color", expr as ExpressionSpecification);
    },
    setBasemap(b) {
      basemap = b;
      if (map.isStyleLoaded()) applyBasemap();
    },
    setCursor(c) {
      if (!c) {
        if (markerOn) marker.remove();
        markerOn = false;
        return;
      }
      marker.setLngLat([c.lon, c.lat]).setRotation(c.heading ?? 0);
      marker.getElement().classList.toggle("no-heading", c.heading == null);
      if (!markerOn) marker.addTo(map);
      markerOn = true;
    },
    isBlank: () => blank,
    destroy() {
      window.clearTimeout(timer);
      marker.remove();
      map.remove();
    },
  };
}
