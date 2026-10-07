// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * ShellInput wired to the page (shell input spec §2–§7, §14; I1): one keydown/keyup listener
 * in the capture phase turns keys into intents (shell/input.ts) and acts on them through the
 * focus zones (shell/focus.ts). Tab and Shift+Tab keep native order; text fields and controls
 * that own their keys are never intercepted (§10).
 *
 * - **Arrows** move focus spatially inside the zone, then into the neighbouring zone (never on
 *   a held repeat, and never out of a sheet). On phone, tablet and desktop they act only once
 *   focus is on a focusable, so arrow scrolling keeps working (Decision 8); on head units they
 *   always navigate. In Drive mode with focus on the face, `left`/`right` switch faces (DM1's
 *   `stepFace`) and `up`/`down` do nothing (no map zoom yet), so nothing scrolls.
 * - **ok** (Enter): native activation in `main` and sheets; on a strip chip or rail item it
 *   activates on release, because a long `ok` there is reserved for edit mode (§14.1, DM3)
 *   and must not also activate. In Drive mode with focus on the face, `ok` opens the Drive menu.
 *   Presses within 500 ms of a sheet opening are ignored, and Enter never repeats.
 * - **back** (Escape): closes the top layer; else in Drive mode while Moving (unknown counts
 *   as Moving on driver-facing classes, fail closed) focuses the `drive_mode` chip, and from
 *   the chip returns to the face (§14.2); else from `main` focuses the rail item of the current
 *   destination; else goes up to Home (§4.3). It never leaves Drive mode while Moving.
 * - **menu** (Escape held 600 ms): Drive mode opens the Drive menu; elsewhere focuses the rail.
 */
import { useEffect, useLayoutEffect, useRef } from "react";
import {
  focusablesIn, focusVisible, forget, lastSheetOpened, nearest, neighbours, ownsKeys, pick, rectOf, remember, remembered,
  topLayer, topSheet, zoneOf, type Zone,
} from "./focus";
import { createIntentMachine, keyIntent, OK_GUARD_MS, type Direction, type IntentEvent } from "./input";
import { isHeadUnit, type LayoutClass } from "./layoutClass";
import type { DrivingState } from "./landing";

export type ShellInputDeps = {
  layout: LayoutClass;
  driving: DrivingState;
  driveMode: boolean;
  /** Switch the current mode's faces (DM1), wrapping. */
  stepFace: (dir: 1 | -1) => void;
  openDriveMenu: () => void;
  /** Leave Drive mode (Parked only by `back`; the strip's Back chip is the touch path). */
  exitDrive: () => void;
  /** Up one route level: to Home from any other destination. */
  goHome: () => void;
};

/** Moving for input purposes: known Moving, or unknown on a driver-facing class (UI spec §3.5
 * "unknown speed counts as Moving"; tablet and desktop are not driver-facing). */
export function movingForInput(layout: LayoutClass, driving: DrivingState): boolean {
  if (driving === "moving") return true;
  if (driving !== "unknown") return false;
  return isHeadUnit(layout) || layout === "phone";
}

const ZONE_ROOT: Record<Exclude<Zone, "sheet">, string> = {
  strip: "[data-zone='strip']", rail: "[data-zone='rail']", main: "[data-zone='main']",
};

const modeChip = () => document.querySelector<HTMLElement>("[data-zone='strip'] [data-chip='drive_mode']");
const currentRailItem = () =>
  document.querySelector<HTMLElement>("[data-zone='rail'] [aria-current='page']")
  ?? document.querySelector<HTMLElement>("[data-zone='rail'] [data-focus]");

/** The element focus is on, or null when it rests on the page itself. */
function activeEl(): HTMLElement | null {
  const a = document.activeElement;
  return a && a !== document.body && a instanceof HTMLElement ? a : null;
}

/** Is `el` a focus target (not just a zone container such as `main` holding focus)? */
const isItem = (el: HTMLElement | null): el is HTMLElement =>
  !!el && (el.matches("[data-focus], button, a[href], input, select, textarea") || (el.tabIndex >= 0 && !el.matches("[data-zone]")));

/** Land in `zone` (§4.2, §14.3): the item last focused there, else in Drive mode the
 * `drive_mode` chip for the strip, else the nearest to `from`. */
function landIn(zone: Exclude<Zone, "sheet">, from: { x: number; y: number }, driveMode: boolean): HTMLElement | null {
  const mem = remembered(zone);
  if (mem) return mem;
  if (zone === "strip" && driveMode) {
    const chip = modeChip();
    if (chip) return chip;
  }
  const root = document.querySelector(ZONE_ROOT[zone]);
  if (!root) return null;
  const items = focusablesIn(root, zone);
  const i = nearest(from, items.map(rectOf));
  return items[i] ?? null;
}

/** Move focus from `el` in `dir` (§4.2). Returns whether focus moved. */
function move(el: HTMLElement, dir: Direction, repeat: boolean, driveMode: boolean): boolean {
  const zone = zoneOf(el);
  if (!zone) return false;
  const from = rectOf(el);
  const root = zone === "sheet" ? topSheet() : document.querySelector(ZONE_ROOT[zone]);
  if (!root) return false;
  const inside = focusablesIn(root, zone).filter((x) => x !== el);
  const i = pick(from, inside.map(rectOf), dir);
  if (i >= 0) {
    focusVisible(inside[i]!);
    return true;
  }
  // a zone's edge: the trap holds in a sheet; a held repeat never crosses (§5)
  if (zone === "sheet" || repeat) return false;
  // the neighbouring zone first (§4.2: rail ↔ main across the driver side, strip above main)
  for (const z of neighbours(zone, dir)) {
    const r = document.querySelector(ZONE_ROOT[z]);
    const candidates = r ? focusablesIn(r, z) : [];
    const j = pick(from, candidates.map(rectOf), dir);
    if (j < 0) continue;
    focusVisible(landIn(z, { x: from.x + from.w / 2, y: from.y + from.h / 2 }, driveMode) ?? candidates[j]!);
    return true;
  }
  return false;
}


/** Focus `main` itself: the face in Drive mode (no item there to hold focus). */
function focusMain(): void {
  const main = document.querySelector<HTMLElement>("[data-zone='main'] main, main[data-zone='main']") ?? document.querySelector<HTMLElement>("main");
  main?.focus({ preventScroll: true });
}

/** Do the arrows navigate now (§4.5, Decision 8)? Always on head units, in Drive mode and in
 * a sheet; on the phone, tablet and desktop only once focus is on a focusable. */
function arrowsNavigate(d: ShellInputDeps, el: HTMLElement | null): boolean {
  return isHeadUnit(d.layout) || d.driveMode || !!topSheet() || isItem(el);
}

export function useShellInput(deps: ShellInputDeps): void {
  const ref = useRef(deps);
  useLayoutEffect(() => { ref.current = deps; });
  const wasDrive = useRef(deps.driveMode);

  // entering Drive mode: the strip is entered on the switcher the first time (§14.3)
  useEffect(() => {
    if (deps.driveMode && !wasDrive.current) forget("strip");
    wasDrive.current = deps.driveMode;
  }, [deps.driveMode]);

  useEffect(() => {
    // keys whose release we take over (a guarded or repeated activation key)
    const swallowUp = new Set<string>();
    // what the `ok` press now held started on: a strip or rail item (activated on a short
    // release; a long ok there is reserved), Drive mode's face (the Drive menu), or anything
    // else (activated natively on key down)
    let okPress: { kind: "item"; el: HTMLElement } | { kind: "face" } | { kind: "native" } | null = null;

    const onIntent = (e: IntentEvent) => {
      const d = ref.current;
      const moving = movingForInput(d.layout, d.driving);
      const el = activeEl();
      const zone = zoneOf(el);
      const layer = topLayer();
      const sheet = topSheet();
      switch (e.intent) {
        case "up": case "down": case "left": case "right": {
          if (sheet) {
            // the only trap: focus stays in the sheet (§4.1)
            if (!el || zone !== "sheet" || !sheet.contains(el)) {
              const first = focusablesIn(sheet, "sheet")[0];
              if (first) focusVisible(first);
              return;
            }
            move(el, e.intent, e.repeat, d.driveMode);
            return;
          }
          if (d.driveMode && zone !== "strip" && !isItem(el)) {
            // the face (§6): left/right switch faces, once per press; up/down would zoom a map
            // face (no zoom yet), so nothing else happens and nothing scrolls
            if (!e.repeat && (e.intent === "left" || e.intent === "right")) d.stepFace(e.intent === "right" ? 1 : -1);
            return;
          }
          if (isItem(el)) {
            move(el, e.intent, e.repeat, d.driveMode);
            return;
          }
          // nothing focused on a head unit: start in main, where focus last was (else nearest
          // the top-left), else the rail
          if (!e.repeat) {
            const target = landIn("main", { x: 0, y: 0 }, d.driveMode) ?? landIn("rail", { x: 0, y: 0 }, d.driveMode);
            if (target) focusVisible(target);
          }
          return;
        }
        case "ok": {
          const p = okPress;
          okPress = null;
          if (p?.kind === "item" && p.el.isConnected) p.el.click();
          else if (p?.kind === "face" && d.driveMode && !topSheet()) d.openDriveMenu();
          return;
        }
        case "long_ok":
          // reserved for edit mode (§14.1; DM3): nothing activates, and the release does nothing
          okPress = null;
          return;
        case "back": {
          if (layer) {
            layer.close();
            return;
          }
          if (sheet) return; // a dialog with no way out but its own choice (consent)
          if (d.driveMode) {
            if (moving) {
              // §14.2: the switcher wherever it sits; from the switcher, back to the face
              const chip = modeChip();
              if (el && el === chip) focusMain();
              else if (chip) focusVisible(chip);
              return;
            }
            d.exitDrive(); // Parked: §4.3, up one level
            return;
          }
          if (zone === "main" && isItem(el)) {
            const rail = currentRailItem();
            if (rail) {
              focusVisible(rail);
              return;
            }
          }
          d.goHome();
          // the rail item of the destination now shown (Home), once it has rendered
          window.setTimeout(() => {
            const rail = currentRailItem();
            if (rail && !topSheet()) focusVisible(rail);
          }, 0);
          return;
        }
        case "menu": {
          if (sheet) return; // a sheet holds focus until it closes (§4.1)
          if (d.driveMode) d.openDriveMenu();
          else {
            const rail = currentRailItem();
            if (rail) focusVisible(rail);
          }
          return;
        }
      }
    };
    const machine = createIntentMachine(onIntent);

    const swallow = (e: KeyboardEvent) => {
      e.preventDefault();
      e.stopImmediatePropagation();
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      const target = e.target instanceof Element ? e.target : null;
      // text fields and controls that own their keys: never intercepted; their Escape reaches
      // the bubble listener below unless the field used it
      if (ownsKeys(target)) return;
      const d = ref.current;
      const el = activeEl();
      // activation keys never repeat, and are ignored for 500 ms after a sheet opens (§5, §7)
      if (e.key === "Enter" || e.key === " ") {
        if (e.repeat || performance.now() - lastSheetOpened() < OK_GUARD_MS) {
          swallow(e);
          swallowUp.add(e.key);
          return;
        }
      }
      const intent = keyIntent(e.key);
      if (!intent) return;
      if (e.key === "Enter") {
        if (el?.closest("[data-own-ok]")) return; // the switcher has its own short and long ok (§14.1)
        const zone = zoneOf(el);
        if ((zone === "strip" || zone === "rail") && isItem(el)) {
          swallow(e);
          okPress = { kind: "item", el };
        } else if (d.driveMode && zone !== "strip" && zone !== "sheet" && !isItem(el)) {
          swallow(e);
          okPress = { kind: "face" };
        } else {
          okPress = { kind: "native" }; // activated by the browser on key down
        }
        machine.keydown(e.key, e.repeat);
        return;
      }
      if (e.key === "Escape") {
        swallow(e);
        machine.keydown(e.key, e.repeat);
        return;
      }
      if (!arrowsNavigate(d, el)) return; // arrow scrolling stays (Decision 8)
      swallow(e);
      machine.keydown(e.key, e.repeat);
    };
    // Escape from a text field the field did not use: `back` (it leaves the field's sheet)
    const onKeyDownBubble = (e: KeyboardEvent) => {
      if (e.key !== "Escape" || e.defaultPrevented) return;
      if (!ownsKeys(e.target instanceof Element ? e.target : null)) return;
      e.preventDefault();
      machine.keydown(e.key, e.repeat);
    };
    const onKeyUp = (e: KeyboardEvent) => {
      if (swallowUp.delete(e.key)) {
        swallow(e);
        return;
      }
      if (!keyIntent(e.key)) return;
      machine.keyup(e.key); // a release with no press held here does nothing
    };
    const onFocusIn = (e: FocusEvent) => remember(e.target instanceof Element ? e.target : null);
    const onBlur = () => {
      machine.reset();
      okPress = null;
    };

    window.addEventListener("keydown", onKeyDown, true);
    window.addEventListener("keydown", onKeyDownBubble);
    window.addEventListener("keyup", onKeyUp, true);
    window.addEventListener("focusin", onFocusIn);
    window.addEventListener("blur", onBlur);
    return () => {
      machine.reset();
      window.removeEventListener("keydown", onKeyDown, true);
      window.removeEventListener("keydown", onKeyDownBubble);
      window.removeEventListener("keyup", onKeyUp, true);
      window.removeEventListener("focusin", onFocusIn);
      window.removeEventListener("blur", onBlur);
    };
  }, []);
}
