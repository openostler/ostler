import { afterEach, describe, expect, it } from "vitest";
import {
  BASEMAP_KEY, casingFor, ESRI_IMAGERY, insideConus, layerVisible, loadBasemap, SAT_URL_KEY, satelliteSource, saveBasemap, USGS_IMAGERY,
} from "./basemap";

afterEach(() => localStorage.clear());

describe("basemap", () => {
  it("Esri World Imagery by default, with its required attribution", () => {
    const s = satelliteSource([-4.7, 56.5, -4.5, 56.7], null); // Scotland
    expect(s).toBe(ESRI_IMAGERY);
    expect(s.tiles).toBe("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}");
    expect(s.attribution).toBe("Powered by Esri · Esri, Maxar, Earthstar Geographics, and the GIS User Community");
  });

  it("USGS Imagery Only inside the conterminous US (whole bbox), Esri otherwise", () => {
    expect(satelliteSource([-105.3, 39.9, -105.1, 40.1], null)).toBe(USGS_IMAGERY); // Boulder
    expect(USGS_IMAGERY.attribution).toBe("USGS The National Map");
    expect(insideConus([-150, 61, -149, 62])).toBe(false); // Alaska
    expect(insideConus([-125.5, 48, -124, 49])).toBe(false); // straddles the edge
    expect(insideConus(null)).toBe(false);
  });

  it("d2diag.satUrl overrides the source; a malformed value is ignored", () => {
    localStorage.setItem(SAT_URL_KEY, "https://tiles.example/{z}/{x}/{y}.jpg");
    expect(satelliteSource([-4.7, 56.5, -4.5, 56.7]).tiles).toBe("https://tiles.example/{z}/{x}/{y}.jpg");
    localStorage.setItem(SAT_URL_KEY, "javascript:alert(1)");
    expect(satelliteSource([-4.7, 56.5, -4.5, 56.7])).toBe(ESRI_IMAGERY);
  });

  it("remembers the choice per device", () => {
    expect(loadBasemap()).toBe("streets");
    saveBasemap("hybrid");
    expect(localStorage.getItem(BASEMAP_KEY)).toBe("hybrid");
    expect(loadBasemap()).toBe("hybrid");
    localStorage.setItem(BASEMAP_KEY, "nonsense");
    expect(loadBasemap()).toBe("streets");
  });

  it("visibility: imagery on Satellite/Hybrid, labels hidden on Satellite only", () => {
    const sat = { id: "satellite", type: "raster" };
    const label = { id: "place_label", type: "symbol" };
    const road = { id: "road", type: "line" };
    expect([layerVisible(sat, "streets"), layerVisible(sat, "satellite"), layerVisible(sat, "hybrid")]).toEqual([false, true, true]);
    expect([layerVisible(label, "streets"), layerVisible(label, "satellite"), layerVisible(label, "hybrid")]).toEqual([true, false, true]);
    expect(layerVisible(road, "satellite")).toBe(true);
  });

  it("casing: white on streets, near-black at 0.7 on imagery", () => {
    expect(casingFor("streets").color).toBe("#ffffff");
    expect(casingFor("satellite")).toEqual({ color: "#101317", opacity: 0.7 });
    expect(casingFor("hybrid")).toEqual({ color: "#101317", opacity: 0.7 });
  });
});
