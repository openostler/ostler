/**
 * The MapLibre handle against a fake maplibre-gl (jsdom has no WebGL): the two offset trace
 * lanes, the satellite raster under the labels, and a basemap switch that only toggles
 * layout visibility so the trace layers survive.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

type Layer = { id: string; type: string; source?: string; layout?: Record<string, unknown>; paint?: Record<string, unknown> };

const fake = vi.hoisted(() => ({ map: null as null | FakeMapT, loaded: true }));
type FakeMapT = {
  layers: Layer[];
  sources: Record<string, Record<string, unknown> & { setData: ReturnType<typeof vi.fn> }>;
  handlers: Record<string, ((e: unknown) => void)[]>;
  setStyle: ReturnType<typeof vi.fn>;
};

vi.mock("maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url", () => ({ default: "worker.js" }));
vi.mock("maplibre-gl/dist/maplibre-gl.css", () => ({}));
vi.mock("maplibre-gl", () => {
  class FakeMap {
    layers: Layer[] = [
      { id: "background", type: "background" },
      { id: "water", type: "fill" },
      { id: "road", type: "line" },
      { id: "place_label", type: "symbol" },
      { id: "poi_label", type: "symbol" },
    ];
    sources: FakeMapT["sources"] = {};
    handlers: FakeMapT["handlers"] = {};
    touchZoomRotate = { disableRotation: () => undefined };
    setStyle = vi.fn();
    constructor() { fake.map = this as unknown as FakeMapT; }
    addControl() { return this; }
    on(ev: string, fn: (e: unknown) => void) { (this.handlers[ev] ??= []).push(fn); return this; }
    isStyleLoaded() { return fake.loaded; }
    getStyle() { return { layers: this.layers.map((l) => ({ id: l.id, type: l.type })) }; }
    addSource(id: string, s: Record<string, unknown>) { this.sources[id] = { ...s, setData: vi.fn() }; }
    getSource(id: string) { return this.sources[id]; }
    getLayer(id: string) { return this.layers.find((l) => l.id === id); }
    addLayer(l: Layer, before?: string) {
      const i = before ? this.layers.findIndex((x) => x.id === before) : -1;
      if (i >= 0) this.layers.splice(i, 0, l); else this.layers.push(l);
    }
    setLayoutProperty(id: string, k: string, v: unknown) { const l = this.getLayer(id)!; l.layout = { ...l.layout, [k]: v }; }
    setPaintProperty(id: string, k: string, v: unknown) { const l = this.getLayer(id)!; l.paint = { ...l.paint, [k]: v }; }
    remove() { /* */ }
  }
  class Marker {
    setLngLat() { return this; }
    setRotation() { return this; }
    getElement() { return document.createElement("div"); }
    addTo() { return this; }
    remove() { return this; }
  }
  class Control { }
  return { Map: FakeMap, Marker, AttributionControl: Control, NavigationControl: Control, setWorkerUrl: () => undefined };
});

import { ESRI_IMAGERY } from "./basemap";
import { createTraceMap } from "./maplibre";
import type { FeatureCollection } from "./trace";

const fc = (b: number): FeatureCollection => ({
  type: "FeatureCollection",
  features: [{ type: "Feature", properties: { b }, geometry: { type: "LineString", coordinates: [[0, 0], [0.001, 0]] } }],
});

function make(basemap: "streets" | "satellite" | "hybrid" = "streets") {
  const h = createTraceMap({
    container: document.createElement("div"), bbox: [0, 0, 1, 1],
    traces: { a: fc(3), b: null }, colors: { a: ["match", 1], b: ["match", 2] },
    basemap, satellite: ESRI_IMAGERY,
  });
  return { h, map: fake.map! };
}
const ids = (m: FakeMapT) => m.layers.map((l) => l.id);
const vis = (m: FakeMapT, id: string) => m.layers.find((l) => l.id === id)!.layout?.visibility;

describe("replay map handle", () => {
  beforeEach(() => { fake.map = null; fake.loaded = true; });

  it("adds both lanes with ±3 px line-offset, round joins, casings below their lines, imagery below the labels", () => {
    const { map } = make();
    expect(ids(map)).toEqual([
      "background", "water", "road", "satellite", "place_label", "poi_label",
      "trace-a-casing", "trace-a", "trace-b-casing", "trace-b",
    ]);
    const get = (id: string) => map.layers.find((l) => l.id === id)!;
    expect(get("trace-a").paint!["line-offset"]).toBe(-3);
    expect(get("trace-a-casing").paint!["line-offset"]).toBe(-3);
    expect(get("trace-b").paint!["line-offset"]).toBe(3);
    expect(get("trace-b").layout!["line-join"]).toBe("round");
    expect(get("trace-a").paint!["line-color"]).toEqual(["match", 1]);
    expect(map.sources.satellite!.tiles).toEqual([ESRI_IMAGERY.tiles]);
    expect(map.sources.satellite!.attribution).toBe(ESRI_IMAGERY.attribution);
    expect(vis(map, "satellite")).toBe("none");
    expect(get("trace-a-casing").paint!["line-color"]).toBe("#ffffff");
  });

  it("switching basemap toggles visibility only: the trace layers and their data survive", () => {
    const { h, map } = make();
    const before = ids(map);
    h.setTrace("b", fc(7));
    h.setBasemap("satellite");
    expect(ids(map)).toEqual(before); // nothing added or removed
    expect(vis(map, "satellite")).toBe("visible");
    expect(vis(map, "place_label")).toBe("none");
    expect(vis(map, "road")).toBe("visible");
    expect(map.layers.find((l) => l.id === "trace-a")!.layout!.visibility).toBeUndefined();
    expect(map.layers.find((l) => l.id === "trace-b-casing")!.paint!["line-color"]).toBe("#101317");
    expect(map.layers.find((l) => l.id === "trace-b-casing")!.paint!["line-opacity"]).toBe(0.7);
    h.setBasemap("hybrid");
    expect(vis(map, "satellite")).toBe("visible");
    expect(vis(map, "place_label")).toBe("visible");
    h.setBasemap("streets");
    expect(vis(map, "satellite")).toBe("none");
    expect(map.layers.find((l) => l.id === "trace-a-casing")!.paint!["line-color"]).toBe("#ffffff");
    expect(ids(map)).toEqual(before);
    expect(map.setStyle).not.toHaveBeenCalled();
    expect(map.sources["trace-b"]!.setData).toHaveBeenCalledWith(fc(7));
  });

  it("starts on the remembered basemap; trace B can be hidden; colours update per lane", () => {
    const { h, map } = make("hybrid");
    expect(vis(map, "satellite")).toBe("visible");
    h.setTrace("b", null);
    expect(map.sources["trace-b"]!.setData).toHaveBeenLastCalledWith({ type: "FeatureCollection", features: [] });
    h.setColor("b", ["match", 9]);
    expect(map.layers.find((l) => l.id === "trace-b")!.paint!["line-color"]).toEqual(["match", 9]);
  });

  it("once the style has loaded, tile/glyph/paint errors never blank the map", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const { h, map } = make();
    for (const fn of map.handlers.error ?? []) fn({ sourceId: "satellite" });
    for (const fn of map.handlers.error ?? []) fn({ sourceId: "openmaptiles", error: new Error("tile 404") });
    for (const fn of map.handlers.error ?? []) fn({ error: new Error("glyphs") });
    expect(map.setStyle).not.toHaveBeenCalled();
    expect(h.isBlank()).toBe(false);
    warn.mockRestore();
  });

  it("a failure of the base style itself (before it loads) falls back to the trace only; Retry re-applies the online style", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    fake.loaded = false;
    const onBlank = vi.fn();
    const h = createTraceMap({
      container: document.createElement("div"), bbox: [0, 0, 1, 1],
      traces: { a: fc(3), b: null }, colors: { a: ["match", 1], b: "#9aa1a9" },
      basemap: "streets", satellite: ESRI_IMAGERY, onBlank,
    });
    const map = fake.map!;
    for (const fn of map.handlers.error ?? []) fn({ error: new Error("style fetch failed") });
    expect(map.setStyle).toHaveBeenCalledTimes(1);
    expect(onBlank).toHaveBeenCalledTimes(1);
    expect(h.isBlank()).toBe(true);
    h.retry();
    expect(map.setStyle).toHaveBeenLastCalledWith("https://tiles.openfreemap.org/styles/liberty", { diff: false });
    expect(h.isBlank()).toBe(false);
    h.destroy();
    warn.mockRestore();
  });

  it("an absent trace B never gets an empty (invalid) colour expression; enabling it later colours it", () => {
    const h = createTraceMap({
      container: document.createElement("div"), bbox: [0, 0, 1, 1],
      traces: { a: fc(3), b: null }, colors: { a: ["match", 1], b: [] },
      basemap: "streets", satellite: ESRI_IMAGERY,
    });
    const map = fake.map!;
    const b = () => map.layers.find((l) => l.id === "trace-b")!;
    expect(b().paint!["line-color"]).toBe("#9aa1a9");
    h.setTrace("b", fc(5));
    h.setColor("b", ["match", ["get", "b"], 5, "#123456", "#9aa1a9"]);
    expect(b().paint!["line-color"]).toEqual(["match", ["get", "b"], 5, "#123456", "#9aa1a9"]);
    h.setColor("b", []);
    expect(b().paint!["line-color"]).toBe("#9aa1a9");
  });
});
