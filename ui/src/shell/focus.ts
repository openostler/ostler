// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Focus zones and spatial navigation (shell input spec §4; I1). Four zones: `strip` (status
 * chips), `rail` (destinations; the bottom bar on the phone), `main` (the page) and `sheet`
 * (any sheet or dialog; it traps focus until `back` or a choice closes it). A zone is the
 * nearest ancestor with `data-zone`.
 *
 * Movement (§4.2) is geometric: an arrow moves to the nearest focusable whose centre lies in
 * the 90° cone of the direction, scored by the distance along the axis plus twice the
 * off-axis distance (the TV-platform rule). The maths (`score`, `pick`) is pure and
 * unit-tested on fixture layouts; the DOM half reads boxes with getBoundingClientRect.
 *
 * Layers (§4.3): every sheet, dialog or popover that `back` closes registers here, newest on
 * top, with the time it opened (for the 500 ms `ok` guard, §5) and the element focused before
 * it (focus returns there when it closes).
 */
import type { Direction } from "./input";

export type Zone = "strip" | "rail" | "main" | "sheet";
export type Rect = { x: number; y: number; w: number; h: number };

const centre = (r: Rect) => ({ x: r.x + r.w / 2, y: r.y + r.h / 2 });

/**
 * The score of moving from `from` to `to` in `dir` (lower is nearer), or null when `to`'s
 * centre is outside the direction's 90° cone (the off-axis distance may not exceed the
 * distance along the axis) or not ahead at all.
 */
export function score(from: Rect, to: Rect, dir: Direction): number | null {
  const a = centre(from);
  const b = centre(to);
  const dx = b.x - a.x;
  const dy = b.y - a.y;
  const along = dir === "right" ? dx : dir === "left" ? -dx : dir === "down" ? dy : -dy;
  const off = Math.abs(dir === "left" || dir === "right" ? dy : dx);
  if (along <= 0 || off > along) return null;
  return along + 2 * off;
}

/** The index of the best candidate from `from` in `dir`, or -1 when none is in the cone.
 * Ties keep the earlier candidate (document order). */
export function pick(from: Rect, candidates: Rect[], dir: Direction): number {
  let best = -1;
  let bestScore = Infinity;
  candidates.forEach((c, i) => {
    const s = score(from, c, dir);
    if (s !== null && s < bestScore) {
      best = i;
      bestScore = s;
    }
  });
  return best;
}

/** The candidate nearest to a point (entering a zone with nothing remembered there). */
export function nearest(point: { x: number; y: number }, candidates: Rect[]): number {
  let best = -1;
  let bestD = Infinity;
  candidates.forEach((c, i) => {
    const m = centre(c);
    const d = Math.hypot(m.x - point.x, m.y - point.y);
    if (d < bestD) {
      best = i;
      bestD = d;
    }
  });
  return best;
}

/** The zones to try, in order, when a move leaves `zone` (§4.2): the rail (or bottom bar) and
 * the strip neighbour main; main's neighbour is the strip upwards and the rail sideways. */
export function neighbours(zone: Exclude<Zone, "sheet">, dir: Direction): Exclude<Zone, "sheet">[] {
  if (zone === "main") return dir === "up" ? ["strip", "rail"] : ["rail", "strip"];
  return zone === "strip" ? ["main", "rail"] : ["main", "strip"];
}

/* ------------------------------------------------------------------ DOM */

/** What can hold focus (spec §4.1's `data-focus`, plus the native focusables the kit will
 * carry it on). Disabled controls and `tabindex="-1"` containers are left out. */
const FOCUSABLE = [
  "[data-focus]", "button:not([disabled])", "a[href]", "input:not([disabled]):not([type=hidden])",
  "select:not([disabled])", "textarea:not([disabled])", "[tabindex]:not([tabindex='-1'])",
].join(", ");

export const zoneOf = (el: Element | null): Zone | null =>
  (el?.closest?.("[data-zone]")?.getAttribute("data-zone") as Zone | undefined) ?? null;

/** Text entry and controls that own their arrows and Enter (§4.4, §10): the shell never
 * intercepts keys there. */
export function ownsKeys(el: Element | null): boolean {
  if (!el) return false;
  if (el.closest("[role=application]")) return true;
  const tag = el.tagName;
  if (tag === "TEXTAREA" || tag === "SELECT") return true;
  if ((el as HTMLElement).isContentEditable) return true;
  if (tag === "INPUT") {
    const type = (el as HTMLInputElement).type;
    return !["button", "submit", "reset", "checkbox"].includes(type);
  }
  const role = el.getAttribute("role");
  return role === "slider" || role === "spinbutton" || role === "listbox" || role === "textbox";
}

const visible = (el: Element): boolean => {
  if (el.closest("[inert], [aria-hidden='true']")) return false;
  const r = el.getBoundingClientRect();
  return r.width > 0 && r.height > 0;
};

export const rectOf = (el: Element): Rect => {
  const r = el.getBoundingClientRect();
  return { x: r.left, y: r.top, w: r.width, h: r.height };
};

/** The focusable, visible elements in a zone root (nested zones excluded). */
export function focusablesIn(root: Element, zone: Zone): HTMLElement[] {
  return [...root.querySelectorAll<HTMLElement>(FOCUSABLE)].filter((el) => zoneOf(el) === zone && visible(el));
}

/** The topmost open sheet (the last in the document wins, as it paints on top). */
export function topSheet(doc: Document = document): HTMLElement | null {
  const all = doc.querySelectorAll<HTMLElement>("[data-zone='sheet']");
  return all.length ? all[all.length - 1]! : null;
}

/** Focus an element and show the ring (focus moved by a non-pointer intent, §4.5). */
export function focusVisible(el: HTMLElement): void {
  el.focus({ preventScroll: true, focusVisible: true } as FocusOptions);
  // focus moves scroll the item into view in `main` (§4.2); never in the strip or rail
  if (zoneOf(el) === "main") el.scrollIntoView?.({ block: "nearest", inline: "nearest" });
}

/* ------------------------------------------------------------------ memory */

const memory = new Map<Zone, HTMLElement>();

/** Remember the element focused in its zone (§4.2: a zone is re-entered where it was left). */
export function remember(el: Element | null): void {
  const z = zoneOf(el);
  if (z && z !== "sheet" && el instanceof HTMLElement) memory.set(z, el);
}
export function remembered(zone: Zone): HTMLElement | null {
  const el = memory.get(zone);
  return el && el.isConnected && visible(el) ? el : null;
}
export function forget(zone: Zone): void {
  memory.delete(zone);
}

/* ------------------------------------------------------------------ layers */

export type Layer = { id: number; close: () => void; opened: number; restore: Element | null; sheet: boolean };
let layers: Layer[] = [];
let nextId = 1;

/** Register a sheet or popover that `back` closes; returns its unregister. `sheet: true`
 * layers start the `ok` guard (§5). */
export function pushLayer(close: () => void, opts: { sheet: boolean; now?: number }): () => void {
  const layer: Layer = {
    id: nextId++, close, opened: opts.now ?? performance.now(),
    restore: typeof document !== "undefined" ? document.activeElement : null, sheet: opts.sheet,
  };
  layers = [...layers, layer];
  return () => {
    const wasTop = layers[layers.length - 1]?.id === layer.id;
    layers = layers.filter((l) => l.id !== layer.id);
    // focus returns to where it was when the layer opened, if that is still there
    const back = layer.restore as HTMLElement | null;
    if (wasTop && back && back !== document.body && back.isConnected && typeof back.focus === "function") {
      const active = document.activeElement;
      if (!active || active === document.body || !active.isConnected) back.focus({ preventScroll: true });
    }
  };
}
export const topLayer = (): Layer | null => layers[layers.length - 1] ?? null;
/** The newest sheet layer's opening time, for the 500 ms `ok` guard. */
export const lastSheetOpened = (): number => {
  for (let i = layers.length - 1; i >= 0; i--) if (layers[i]!.sheet) return layers[i]!.opened;
  return -Infinity;
};
/** Tests only: forget every layer and remembered element. */
export function resetFocusState(): void {
  layers = [];
  memory.clear();
}
