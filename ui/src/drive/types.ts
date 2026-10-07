// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * `ostler.layout/1` as TypeScript (drive-modes spec §4; the published shape is
 * schemas/ostler-layout.schema.json, the limits src/openostler/layout_limits.json). DM1
 * defines `drive_mode` layouts in full; Home, rail and strip layouts come with DM3.
 */
import limitsJson from "../../../src/openostler/layout_limits.json";
import type { LayoutClass } from "../shell/layoutClass";

export type Pair = [number | null, number | null];
export type Bind = { path: string } | { pack: string; signal: string } | { drive_tile: number };
export type Style = "number" | "arc" | "bar" | "chip" | "text" | "sparkline" | "inclinometer" | "compass";
export type Size = "small" | "medium" | "wide" | "hero";

export type Widget = {
  slot: string;
  widget: string;
  at: [number, number];
  size: Size;
  span?: [number, number];
  bind?: Bind;
  bind2?: Bind;
  style?: Style;
  unit?: string;
  dec?: number;
  range?: Pair;
  levels?: { normal?: Pair; warning?: Pair; critical?: Pair };
  label?: string;
  label2?: string;
  icon?: string;
  hidden?: boolean;
  refresh_hz?: number;
  animate?: boolean;
  config?: Record<string, unknown>;
  values?: { bind: Bind; label?: string; dec?: number }[];
};

export type Grid = { cols: number; rows: number };
/** [col, row, cols, rows] in the Moving grid. */
export type Place = [number, number, number, number];
export type Moving = { show: string[]; grid: Grid; place: Record<string, Place> };
export type Face = { face: string; name: string; grid: Grid; widgets: Widget[]; moving?: Moving };

export type Capability = "media_source" | "ride_active";

export type Layout = {
  format: "ostler.layout/1";
  kind: "drive_mode" | "home" | "rail" | "strip";
  id: string;
  name: string;
  icon?: string;
  description?: string;
  version?: number;
  base?: { preset: string; version: number };
  license?: string;
  author?: string;
  vehicle_hint?: { pack?: string };
  requires?: { addons?: string[]; signals_any?: string[]; capabilities?: Capability[] };
  theme_hint?: null | "night_dim";
  classes: Partial<Record<LayoutClass, Face[]>>;
};

type ClassLimits = {
  moving_required: boolean;
  content: [number, number] | null;
  parked_grid: [number, number];
  min_tile: [number, number] | null;
  min_pane: [number, number] | null;
  max_panes: number;
  type: { digits: number; label: number; hero: number };
};
export type Template = "tiles" | "value" | "map" | "media" | "call";
export type Limits = {
  format: string;
  max_bytes: number;
  faces: { min: number; max: number };
  text: { name: number; face: number; label: number; description: number };
  moving: { max_tiles: number; max_refresh_hz: number; digits_floor_px: number; label_floor_px: number };
  classes: Record<LayoutClass, ClassLimits>;
  fallback: Partial<Record<LayoutClass, LayoutClass>>;
  widgets: Record<string, { template: Template | null; styles: Style[] }>;
  templates: Record<Template, { kind: "tile" | "pane"; cost?: number }>;
};

/** The shared limits (one file for the shell and the server validator). */
export const LIMITS = limitsJson as unknown as Limits;

/** The template a widget renders through while Moving (null: Parked only; undefined:
 * unknown, e.g. an add-on widget, which fails closed as an empty tile). */
export const templateOf = (widget: string): Template | null | undefined => LIMITS.widgets[widget]?.template;

/** The faces of a layout for a class, with the fixed fallback order (hu5 ← hu7 ← hu9,
 * tablet ← desktop; never by scaling, §4.2). */
export function facesFor(layout: Layout, cls: LayoutClass): Face[] {
  let c: LayoutClass | undefined = cls;
  const seen = new Set<LayoutClass>();
  while (c && !seen.has(c)) {
    const f = layout.classes[c];
    if (f?.length) return f;
    seen.add(c);
    c = LIMITS.fallback[c];
  }
  return [];
}
