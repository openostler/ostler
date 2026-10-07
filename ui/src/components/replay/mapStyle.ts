// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Which basemap style a theme gets (visual design system spec §7, ADR-0009 amendment of
 * 2026-10-07). This is the one place a style URL comes from. Today it is the online fallback,
 * OpenFreeMap `dark` for Night, Night dim and Deep night and `positron` for Day; when the Brain
 * serves the Ostler Night/Day styles over regional PMTiles (a later platform change), only this
 * module changes. Pure (no MapLibre), so it is unit-tested without WebGL.
 */
import type { Theme } from "../../state/theme";

/** The two map flavours: every dark theme shares Night. */
export type MapFlavour = "night" | "day";
export const flavourOf = (theme: Theme): MapFlavour => (theme === "light" ? "day" : "night");

/** OpenFreeMap vector styles (no key). Their tiles carry the OpenFreeMap, © OpenMapTiles and
 * OpenStreetMap credits (TileJSON attribution), shown in the collapsed attribution control. */
export const OPENFREEMAP_STYLES: Record<MapFlavour, string> = {
  night: "https://tiles.openfreemap.org/styles/dark",
  day: "https://tiles.openfreemap.org/styles/positron",
};

/** The credits the OpenFreeMap styles require (OpenFreeMap, © OpenMapTiles, OpenStreetMap / ODbL),
 * word for word as their TileJSON gives them, so MapLibre shows them once even before (or
 * without) the TileJSON. Lives here with the URLs: a Brain-served style brings its own. */
export const OPENFREEMAP_ATTRIBUTION =
  '<a href="https://openfreemap.org" target="_blank">OpenFreeMap</a> <a href="https://www.openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> ' +
  'Data from <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>';

/** The style URL for a theme. */
export const styleUrl = (theme: Theme): string => OPENFREEMAP_STYLES[flavourOf(theme)];
