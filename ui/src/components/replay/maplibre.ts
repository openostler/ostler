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
import type { BBox, Cursor, FeatureCollection } from "./trace";

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
  setTrace: (fc: FeatureCollection) => void;
  setColor: (expr: unknown[]) => void;
  setCursor: (c: Cursor | null) => void;
  /** True once the map fell back to the blank style. */
  isBlank: () => boolean;
  destroy: () => void;
};

const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] };

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
  trace: FeatureCollection;
  color: unknown[];
  onBlank?: () => void;
}): TraceMapHandle {
  let trace = opts.trace;
  let color = opts.color;
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
  // Style or tile failure (offline, blocked, server down) → the trace on a plain background.
  map.on("error", () => toBlank());

  // (Re-)add our layers after every style load (the blank swap drops them).
  const addTrace = () => {
    if (map.getSource("trace")) return;
    map.addSource("trace", { type: "geojson", data: trace as never });
    map.addLayer({
      id: "trace-casing", type: "line", source: "trace",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#ffffff", "line-width": 7, "line-opacity": 0.9 },
    });
    map.addLayer({
      id: "trace", type: "line", source: "trace",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": color as ExpressionSpecification, "line-width": 4 },
    });
  };
  map.on("style.load", addTrace);
  if (map.isStyleLoaded()) addTrace();

  const marker = new Marker({ element: arrowEl(), rotationAlignment: "map", pitchAlignment: "map" });
  let markerOn = false;

  return {
    setTrace(fc) {
      trace = fc;
      (map.getSource("trace") as GeoJSONSource | undefined)?.setData((fc ?? EMPTY) as never);
    },
    setColor(expr) {
      color = expr;
      if (map.getLayer("trace")) map.setPaintProperty("trace", "line-color", expr as ExpressionSpecification);
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
