// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The `ostler.layout/1` validator, shell side (drive-modes spec §8.2; R2: "the validator and
 * the renderer share one implementation"). It mirrors `openostler.layouts` on the server: the
 * same limits file and the same shared cases (tests/fixtures/layouts/cases.json) run through
 * both. Errors refuse a save or an import; warnings render as honest placeholders. The shell
 * has no VSS leaf list, so an unknown path is a server-side warning only.
 *
 * Strict Moving rules per class (§4.3, §4.4): ≤ 6 tiles (a status line counts two), the pane
 * limit per class and one pane of a kind, minimum tile and pane sizes, the 56 px digit and
 * 24 px label floors, refresh ≤ 4 Hz, no sparkline, no Parked-only widget, no animation.
 */
import type { LayoutClass } from "../shell/layoutClass";
import { LIMITS, type Limits } from "./types";

export type Issue = { rule: string; message: string; cls?: string; face?: string; slot?: string };
export type Report = { errors: Issue[]; warnings: Issue[] };

const KINDS = ["drive_mode", "home", "rail", "strip"];
const SIZES = ["small", "medium", "wide", "hero"];
const STYLES = ["number", "arc", "bar", "chip", "text", "sparkline", "inclinometer", "compass"];
const ID = /^[a-z0-9][a-z0-9_.-]{0,63}$/;
const SLOT = /^[a-z0-9_]{1,16}$/;
const WIDGET = /^[a-z0-9_]+(\.[a-z0-9_]+)+$/;
const ICON = /^[a-z0-9_]+(-fill)?$/;
const PATH = /^Vehicle(\.[A-Za-z0-9_]+)+$/;
const URL_RE = /\b(?:https?:\/\/|www\.)|[a-z0-9-]+\.(?:com|net|org|io|app|dev)\b/i;
// C0/C1 controls and the bidi embedding, override and isolate characters (§4.2, §7.6)
// eslint-disable-next-line no-control-regex
const CONTROL = /[\u0000-\u001f\u007f-\u009f‪-‮⁦-⁩]/g;

type Obj = Record<string, unknown>;
const isObj = (v: unknown): v is Obj => typeof v === "object" && v !== null && !Array.isArray(v);
const isInt = (v: unknown): v is number => typeof v === "number" && Number.isInteger(v);
const isNum = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v);
const isPair = (v: unknown): v is [number | null, number | null] =>
  Array.isArray(v) && v.length === 2 && v.every((x) => x === null || isNum(x));

/** User-perceived characters (§7.6: names are counted in grapheme clusters). */
export function graphemes(text: string): number {
  if (typeof Intl !== "undefined" && "Segmenter" in Intl) {
    return [...new Intl.Segmenter(undefined, { granularity: "grapheme" }).segment(text)].length;
  }
  return [...text.normalize("NFC")].length;
}

/** Plain text as the shell shows it: controls and bidi overrides stripped, trimmed. */
export const cleanText = (text: string): string => text.replace(CONTROL, "").trim();

class Checker {
  report: Report = { errors: [], warnings: [] };
  constructor(private lim: Limits) {}

  err(rule: string, message: string, where: Omit<Issue, "rule" | "message"> = {}) {
    this.report.errors.push({ rule, message, ...where });
  }
  warn(rule: string, message: string, where: Omit<Issue, "rule" | "message"> = {}) {
    this.report.warnings.push({ rule, message, ...where });
  }
  schema(message: string, where: Omit<Issue, "rule" | "message"> = {}) {
    this.err("schema", message, where);
  }

  text(value: unknown, limit: number, what: string, required: boolean, where: Omit<Issue, "rule" | "message"> = {}) {
    if (value === undefined || (value === null && !required)) {
      if (required) this.schema(`${what} must be text`, where);
      return;
    }
    if (typeof value !== "string" || (required && !value.trim())) {
      this.schema(`${what} must be text`, where);
      return;
    }
    if (new RegExp(CONTROL.source).test(value)) this.warn("text.control", `${what}: control or bidi characters are stripped`, where);
    if (URL_RE.test(value)) this.err("text.url", `${what} may not contain a link`, where);
    if (graphemes(cleanText(value)) > limit) this.err("text.too_long", `${what} is longer than ${limit} characters`, where);
  }

  run(doc: unknown, rawSize?: number): Report {
    if (rawSize !== undefined && rawSize > this.lim.max_bytes) this.err("size.too_big", "The file is larger than 256 KB");
    if (!isObj(doc)) {
      this.schema("A layout is a JSON object");
      return this.report;
    }
    if (doc.format !== this.lim.format) {
      if (typeof doc.format === "string" && doc.format.startsWith("ostler.layout/")) this.err("format.unknown", "Made for a newer Ostler");
      else this.schema("format must be ostler.layout/1");
      return this.report;
    }
    const kind = doc.kind;
    if (typeof kind !== "string" || !KINDS.includes(kind)) {
      this.schema("kind must be drive_mode, home, rail or strip");
      return this.report;
    }
    if (typeof doc.id !== "string" || !ID.test(doc.id)) this.schema("id must be lower-case letters, digits, '.', '_' or '-'");
    this.text(doc.name, this.lim.text.name, "The name", true);
    this.text(doc.description, this.lim.text.description, "The description", false);
    if ("icon" in doc && !(typeof doc.icon === "string" && ICON.test(doc.icon))) this.schema("icon must be a Material Symbols name");
    const hint = doc.vehicle_hint;
    if (hint !== undefined && !(isObj(hint) && Object.keys(hint).every((k) => k === "pack"))) this.schema("vehicle_hint may name a pack only");
    if (doc.theme_hint !== undefined && doc.theme_hint !== null && doc.theme_hint !== "night_dim") this.schema("theme_hint may only darken (night_dim)");
    const classes = doc.classes;
    if (!isObj(classes) || !Object.keys(classes).length) {
      this.schema("classes must hold at least one layout class");
      return this.report;
    }
    for (const [cls, faces] of Object.entries(classes)) {
      if (!(cls in this.lim.classes)) {
        this.schema(`Unknown layout class ${cls}`);
        continue;
      }
      if (kind === "drive_mode") this.faces(cls as LayoutClass, faces, doc);
      else if (!(Array.isArray(faces) && faces.length === 1 && isObj(faces[0]))) this.schema(`A ${kind} layout has one face per class`, { cls });
    }
    return this.report;
  }

  faces(cls: LayoutClass, faces: unknown, doc: Obj) {
    const fl = this.lim.faces;
    if (!Array.isArray(faces) || faces.length < fl.min || faces.length > fl.max) {
      this.schema(`${cls}: a mode has 1 to 3 faces`, { cls });
      return;
    }
    const ids = new Set<string>();
    for (const face of faces) {
      if (!isObj(face)) {
        this.schema(`${cls}: a face is an object`, { cls });
        continue;
      }
      let fid = face.face;
      if (typeof fid !== "string" || !SLOT.test(fid)) {
        this.schema(`${cls}: a face needs an id`, { cls });
        fid = "?";
      } else if (ids.has(fid)) this.schema(`${cls}: face ${fid} appears twice`, { cls, face: fid });
      ids.add(fid as string);
      this.face(cls, fid as string, face, doc);
    }
  }

  face(cls: LayoutClass, fid: string, face: Obj, doc: Obj) {
    const where = { cls, face: fid };
    this.text(face.name, this.lim.text.face, "The face name", true, where);
    const grid = this.grid(face.grid, where);
    let widgets = face.widgets;
    if (!Array.isArray(widgets) || widgets.length > 24) {
      this.schema(`${cls}/${fid}: widgets must be a list of at most 24`, where);
      widgets = [];
    }
    const bySlot = new Map<string, Obj>();
    for (const w of widgets as unknown[]) {
      const slot = this.widget(cls, fid, w, grid, doc);
      if (slot === null) continue;
      if (bySlot.has(slot)) this.err("widget.duplicate_slot", `Slot ${slot} is used twice`, { ...where, slot });
      bySlot.set(slot, w as Obj);
    }
    if (face.moving === undefined) {
      if (this.lim.classes[cls].moving_required) this.err("moving.missing", `${cls}: every face needs a Moving section`, where);
      return;
    }
    this.moving(cls, fid, face.moving, bySlot);
  }

  grid(g: unknown, where: Omit<Issue, "rule" | "message">): [number, number] | null {
    if (!isObj(g)) {
      this.schema("grid needs cols and rows", where);
      return null;
    }
    const { cols: c, rows: r } = g;
    if (!(isInt(c) && c >= 1 && c <= 12 && isInt(r) && r >= 1 && r <= 8)) {
      this.schema("grid: 1-12 columns and 1-8 rows", where);
      return null;
    }
    return [c, r];
  }

  bind(b: unknown, doc: Obj, what: string, where: Omit<Issue, "rule" | "message">) {
    if (!isObj(b)) {
      this.schema(`${what} must be an object`, where);
      return;
    }
    const keys = Object.keys(b).sort().join(",");
    if (keys === "path") {
      if (typeof b.path !== "string" || !PATH.test(b.path)) this.schema(`${what}: a VSS path starts with Vehicle.`, where);
    } else if (keys === "pack,signal") {
      const hint = isObj(doc.vehicle_hint) ? doc.vehicle_hint.pack : undefined;
      if (hint !== b.pack) this.err("bind.pack", `${what}: a pack signal needs vehicle_hint.pack ${String(b.pack)}`, where);
    } else if (keys === "drive_tile") {
      if (!(isInt(b.drive_tile) && b.drive_tile >= 0 && b.drive_tile <= 11)) this.schema(`${what}: drive_tile is 0-11`, where);
    } else this.schema(`${what}: one of path, pack+signal or drive_tile`, where);
  }

  widget(cls: string, fid: string, w: unknown, grid: [number, number] | null, doc: Obj): string | null {
    if (!isObj(w)) {
      this.schema(`${cls}/${fid}: a widget is an object`, { cls, face: fid });
      return null;
    }
    const slot = w.slot;
    if (typeof slot !== "string" || !SLOT.test(slot)) {
      this.schema(`${cls}/${fid}: a widget needs a slot id`, { cls, face: fid });
      return null;
    }
    const where = { cls, face: fid, slot };
    const kind = w.widget;
    if (typeof kind !== "string" || !WIDGET.test(kind)) this.schema(`Slot ${slot}: widget must be an id like ostler.gauge`, where);
    else if (!(kind in this.lim.widgets)) this.warn("widget.unknown", `Slot ${slot}: ${kind} needs an add-on`, where);
    const at = w.at;
    const atOk = Array.isArray(at) && at.length === 2 && at.every((v) => isInt(v) && v >= 0);
    if (!atOk) this.schema(`Slot ${slot}: at is [column, row]`, where);
    else if (grid && (at[0] >= grid[0] || at[1] >= grid[1])) this.err("widget.outside_grid", `Slot ${slot} is outside the ${grid[0]}×${grid[1]} grid`, where);
    const span = w.span;
    if (span !== undefined) {
      if (!(Array.isArray(span) && span.length === 2 && span.every((v) => isInt(v) && v >= 1))) this.schema(`Slot ${slot}: span is [columns, rows]`, where);
      else if (grid && atOk && (at[0] + span[0] > grid[0] || at[1] + span[1] > grid[1])) {
        this.err("widget.outside_grid", `Slot ${slot} runs outside the ${grid[0]}×${grid[1]} grid`, where);
      }
    }
    if (!SIZES.includes(w.size as string)) this.schema(`Slot ${slot}: size is small, medium, wide or hero`, where);
    if (w.style !== undefined) {
      const allowed = typeof kind === "string" ? this.lim.widgets[kind]?.styles : undefined;
      if (!STYLES.includes(w.style as string)) this.schema(`Slot ${slot}: unknown style ${String(w.style)}`, where);
      else if (allowed && !(allowed as string[]).includes(w.style as string)) this.err("widget.style", `Slot ${slot}: ${String(kind)} cannot be drawn as ${String(w.style)}`, where);
    }
    for (const key of ["bind", "bind2"] as const) if (key in w) this.bind(w[key], doc, `Slot ${slot} ${key}`, where);
    if (w.values !== undefined) {
      if (!Array.isArray(w.values) || w.values.length > 2) this.schema(`Slot ${slot}: a status line has at most 2 values`, where);
      else {
        for (const v of w.values) {
          if (isObj(v) && "bind" in v) {
            this.bind(v.bind, doc, `Slot ${slot} value`, where);
            this.text(v.label, this.lim.text.label, `Slot ${slot} value label`, false, where);
          } else this.schema(`Slot ${slot}: each value needs a bind`, where);
        }
      }
    }
    this.text(w.label, this.lim.text.label, `Slot ${slot} label`, false, where);
    this.text(w.label2, this.lim.text.label, `Slot ${slot} label`, false, where);
    if ("icon" in w && !(typeof w.icon === "string" && ICON.test(w.icon))) this.schema(`Slot ${slot}: icon must be a Material Symbols name`, where);
    if ("dec" in w && !(isInt(w.dec) && w.dec >= 0 && w.dec <= 4)) this.schema(`Slot ${slot}: dec is 0-4`, where);
    if ("refresh_hz" in w && !(isNum(w.refresh_hz) && w.refresh_hz > 0)) this.schema(`Slot ${slot}: refresh_hz must be above 0`, where);
    this.levels(w, slot, where);
    return slot;
  }

  levels(w: Obj, slot: string, where: Omit<Issue, "rule" | "message">) {
    let rng: [number | null, number | null] | null = null;
    if (w.range !== undefined) {
      if (!isPair(w.range)) this.schema(`Slot ${slot}: range is [min, max]`, where);
      else {
        rng = w.range;
        if (rng[0] !== null && rng[1] !== null && rng[0] >= rng[1]) this.err("levels.order", `Slot ${slot}: the range runs low to high`, where);
      }
    }
    const lv = w.levels;
    if (lv === undefined) return;
    if (!isObj(lv) || !Object.keys(lv).every((k) => ["normal", "warning", "critical"].includes(k))) {
      this.schema(`Slot ${slot}: levels are normal, warning and critical`, where);
      return;
    }
    for (const [name, p] of Object.entries(lv)) {
      if (!isPair(p)) {
        this.schema(`Slot ${slot}: ${name} is [min, max]`, where);
        continue;
      }
      const [lo, hi] = p;
      if (lo !== null && hi !== null && lo > hi) this.err("levels.order", `Slot ${slot}: ${name} runs low to high`, where);
      if (rng && rng[0] !== null && rng[1] !== null) {
        for (const v of [lo, hi]) {
          if (v !== null && (v < rng[0] || v > rng[1])) this.err("levels.range", `Slot ${slot}: ${name} is outside the range`, where);
        }
      }
    }
  }

  moving(cls: LayoutClass, fid: string, mv: unknown, bySlot: Map<string, Obj>) {
    const where = { cls, face: fid };
    const lim = this.lim;
    const cl = lim.classes[cls];
    if (!isObj(mv)) {
      this.schema("moving needs show, grid and place", where);
      return;
    }
    const show = mv.show;
    if (!(Array.isArray(show) && show.length && show.every((s) => typeof s === "string")) || new Set(show).size !== show.length) {
      this.schema("moving.show lists slot ids once each", where);
      return;
    }
    const grid = this.grid(mv.grid, where);
    let place = mv.place;
    if (!isObj(place)) {
      this.schema("moving.place gives each slot [col, row, cols, rows]", where);
      place = {};
    }
    const floors = lim.moving;
    if (cl.type.digits < floors.digits_floor_px || cl.type.label < floors.label_floor_px) {
      this.err("moving.type_floor", `${cls}: Moving digits need ${floors.digits_floor_px} px and labels ${floors.label_floor_px} px`, where);
    }
    let tiles = 0;
    const panes = new Map<string, number>();
    const cells = new Map<string, string>();
    for (const slot of show as string[]) {
      const w = bySlot.get(slot);
      const sw = { ...where, slot };
      if (!w) {
        this.err("moving.unknown_slot", `Moving shows ${slot}, which is not on this face`, sw);
        continue;
      }
      if (w.hidden === true) this.err("moving.hidden", `Slot ${slot} is hidden and cannot show while Moving`, sw);
      const spec = lim.widgets[w.widget as string];
      let template: string | null;
      if (!spec) {
        // fail closed (R2): it renders as an empty cell and still counts as a tile
        this.warn("moving.unknown_widget", `Slot ${slot}: an unknown widget renders as an empty cell while Moving`, sw);
        template = "tiles";
      } else {
        template = spec.template;
        if (template === null) this.err("moving.parked_only", `Slot ${slot} shows only when parked`, sw);
      }
      if (w.style === "sparkline") this.err("moving.sparkline", `Slot ${slot}: no sparkline while Moving`, sw);
      if (w.animate === true) this.err("moving.animation", `Slot ${slot}: no animation while Moving`, sw);
      if (isNum(w.refresh_hz) && w.refresh_hz > floors.max_refresh_hz) {
        this.err("moving.refresh", `Slot ${slot}: refresh at most ${floors.max_refresh_hz} Hz while Moving`, sw);
      }
      const t = template ? lim.templates[template as keyof Limits["templates"]] : undefined;
      const kind = t?.kind ?? null;
      if (kind === "tile") tiles += t?.cost ?? 1;
      else if (kind === "pane") panes.set(template as string, (panes.get(template as string) ?? 0) + 1);
      const p = (place as Obj)[slot];
      if (!(Array.isArray(p) && p.length === 4 && p.every((v) => isInt(v) && v >= 0) && p[2] >= 1 && p[3] >= 1)) {
        this.err("moving.place", `Slot ${slot} has no place in the Moving grid`, sw);
        continue;
      }
      const [x0, y0, pw, ph] = p as [number, number, number, number];
      if (grid && (x0 + pw > grid[0] || y0 + ph > grid[1])) {
        this.err("moving.place", `Slot ${slot} runs outside the Moving grid`, sw);
        continue;
      }
      // a tile may sit over a pane (the map's speed overlay, §4.3); two tiles or two panes may not share a cell
      const layer = kind === "pane" ? "pane" : "tile";
      for (let x = x0; x < x0 + pw; x++) {
        for (let y = y0; y < y0 + ph; y++) {
          const key = `${x},${y},${layer}`;
          const other = cells.get(key);
          if (other !== undefined) this.err("moving.overlap", `Slots ${other} and ${slot} overlap`, sw);
          cells.set(key, slot);
        }
      }
      if (grid && cl.content && kind) {
        const wPx = (cl.content[0] / grid[0]) * pw;
        const hPx = (cl.content[1] / grid[1]) * ph;
        const need = kind === "tile" ? cl.min_tile : cl.min_pane;
        if (need && (wPx + 0.5 < need[0] || hPx + 0.5 < need[1])) {
          this.err(kind === "tile" ? "moving.tile_too_small" : "moving.pane_too_small",
            `${kind === "tile" ? "Tile" : "Pane"} ${slot} too small on ${cls}: ${Math.round(wPx)}×${Math.round(hPx)} px, needs ${need[0]}×${need[1]}`, sw);
        }
      }
    }
    if (tiles > floors.max_tiles) this.err("moving.too_many_tiles", `${cls}: ${tiles} tiles while Moving, at most ${floors.max_tiles}`, where);
    const total = [...panes.values()].reduce((a, b) => a + b, 0);
    if (total > cl.max_panes) this.err("moving.too_many_panes", `${cls}: at most ${cl.max_panes} panes while Moving`, where);
    for (const [t, n] of panes) if (n > 1) this.err("moving.duplicate_pane", `${cls}: at most one ${t} pane while Moving`, where);
  }
}

/** Check an `ostler.layout/1` document (`rawSize`: the file's byte length). */
export function validateLayout(doc: unknown, rawSize?: number, limits: Limits = LIMITS): Report {
  return new Checker(limits).run(doc, rawSize);
}

/** The error rule codes, sorted and unique (what the shared cases compare). */
export const ruleCodes = (r: Report): string[] => [...new Set(r.errors.map((i) => i.rule))].sort();
