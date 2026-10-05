/**
 * Basemap choice for the replay map (spec §5 "Map", ADR-0010): Streets (OpenFreeMap vector),
 * Satellite (raster imagery only) or Hybrid (imagery + the vector labels). Pure: the URL and
 * attribution picking, the per-device persistence and the casing colour live here so they are
 * unit-tested without MapLibre.
 */
import type { BBox } from "./trace";

export type Basemap = "streets" | "satellite" | "hybrid";
export const BASEMAPS: { id: Basemap; label: string }[] = [
  { id: "streets", label: "Streets" },
  { id: "satellite", label: "Satellite" },
  { id: "hybrid", label: "Hybrid" },
];

export type SatSource = { tiles: string; attribution: string; maxzoom: number };

/** Esri World Imagery: free with this attribution for personal, non-commercial use (ADR-0010). */
export const ESRI_IMAGERY: SatSource = {
  tiles: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  attribution: "Powered by Esri · Esri, Maxar, Earthstar Geographics, and the GIS User Community",
  maxzoom: 19,
};
/** USGS Imagery Only: public domain, conterminous US only. */
export const USGS_IMAGERY: SatSource = {
  tiles: "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}",
  attribution: "USGS The National Map",
  maxzoom: 16,
};
/** Conterminous US [minLon, minLat, maxLon, maxLat]. */
export const CONUS_BBOX: BBox = [-124.85, 24.4, -66.88, 49.39];

export const SAT_URL_KEY = "d2diag.satUrl";
export const BASEMAP_KEY = "d2diag.basemap";

function readLs(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** True when the whole session bbox is inside the conterminous US. */
export const insideConus = (b: BBox | null): boolean =>
  !!b && b[0] >= CONUS_BBOX[0] && b[1] >= CONUS_BBOX[1] && b[2] <= CONUS_BBOX[2] && b[3] <= CONUS_BBOX[3];

/** The imagery source for a session: a `d2diag.satUrl` override wins, then USGS inside the
 * US, else Esri World Imagery. */
export function satelliteSource(bbox: BBox | null, override: string | null = readLs(SAT_URL_KEY)): SatSource {
  if (override && /^https?:\/\/.*\{z\}/.test(override)) {
    return { tiles: override, attribution: "Imagery: custom source (d2diag.satUrl)", maxzoom: 19 };
  }
  return insideConus(bbox) ? USGS_IMAGERY : ESRI_IMAGERY;
}

/** The basemap last picked on this device (Streets by default). */
export function loadBasemap(): Basemap {
  const v = readLs(BASEMAP_KEY);
  return v === "satellite" || v === "hybrid" ? v : "streets";
}
export function saveBasemap(b: Basemap): void {
  try {
    window.localStorage.setItem(BASEMAP_KEY, b);
  } catch {
    /* private mode / blocked storage: the choice just isn't remembered */
  }
}

/** Trace casing: white on the light streets map, near-black on imagery. */
export const casingFor = (b: Basemap): { color: string; opacity: number } =>
  b === "streets" ? { color: "#ffffff", opacity: 0.9 } : { color: "#101317", opacity: 0.7 };

/** Layout visibility for one of the style's own (non-trace) layers under a basemap.
 * The imagery layer shows on Satellite/Hybrid; labels (symbol layers) hide on Satellite. */
export function layerVisible(layer: { id: string; type: string }, b: Basemap): boolean {
  if (layer.id === "satellite") return b !== "streets";
  if (layer.type === "symbol") return b !== "satellite";
  return true;
}
