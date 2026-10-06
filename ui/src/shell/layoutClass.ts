// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useState } from "react";

/**
 * Layout classes (UI spec §3.1): chosen by aspect and height, not width alone. The kiosk
 * flag `?display=headunit&side=left|right` overrides detection, because head-unit browsers
 * report odd DPIs; `?display=<class>` names one class outright (tests, odd screens).
 */
export type LayoutClass = "hu7" | "hu9" | "huwide" | "phone" | "tablet" | "desktop";
export const LAYOUT_CLASSES: readonly LayoutClass[] = ["hu7", "hu9", "huwide", "phone", "tablet", "desktop"];
export type Side = "left" | "right";

export const HEAD_UNIT: readonly LayoutClass[] = ["hu7", "hu9", "huwide"];
export const isHeadUnit = (c: LayoutClass): boolean => HEAD_UNIT.includes(c);
/** Every class but the phone has a rail; the phone has the bottom bar (§3.3). */
export const hasRail = (c: LayoutClass): boolean => c !== "phone";

export type Viewport = { width: number; height: number; finePointer: boolean };
export type Kiosk = { display: "headunit" | LayoutClass | null; side: Side | null };

/** The head-unit class for a landscape screen: by aspect, then height. */
function headUnitClass(width: number, height: number): LayoutClass {
  if (width / Math.max(1, height) >= 2.4) return "huwide";
  return height <= 640 ? "hu7" : "hu9";
}

/** The layout class for a viewport (spec §3.1 table, top to bottom). */
export function layoutClassFor(v: Viewport, kiosk: Kiosk = { display: null, side: null }): LayoutClass {
  const { width, height } = v;
  if (kiosk.display === "headunit") return headUnitClass(width, height);
  if (kiosk.display) return kiosk.display;
  const landscape = width > height;
  if (landscape && width / Math.max(1, height) >= 2.4) return "huwide";
  if (!landscape && width < 600) return "phone";
  if (landscape && height <= 640) return "hu7";
  if (landscape && height <= 800) return "hu9";
  if (width >= 1200 && v.finePointer) return "desktop";
  if (width >= 600 && height > 800) return "tablet";
  return width < 600 ? "phone" : "tablet";
}

/** The kiosk flag from a query string (`?display=headunit&side=right`); unknown values are ignored. */
export function parseKiosk(search: string): Kiosk {
  const q = new URLSearchParams(search);
  const d = q.get("display");
  const s = q.get("side");
  const display = d === "headunit" || (LAYOUT_CLASSES as readonly string[]).includes(d ?? "") ? (d as Kiosk["display"]) : null;
  return { display, side: s === "left" || s === "right" ? s : null };
}

/**
 * The rail side (§3.3): the driver's side, from the vehicle's `driver_side` (a pack layout
 * key; the D2 is right-hand drive), with the kiosk flag as override. Left when unknown.
 */
export function railSide(kiosk: Kiosk, driverSide: unknown): Side {
  if (kiosk.side) return kiosk.side;
  return driverSide === "right" ? "right" : "left";
}

function readViewport(): Viewport {
  const fine = typeof window.matchMedia === "function" && window.matchMedia("(pointer: fine)").matches;
  return { width: window.innerWidth, height: window.innerHeight, finePointer: fine };
}

/** The live layout class: re-evaluated on resize and rotation. */
export function useLayoutClass(kiosk: Kiosk): LayoutClass {
  const [cls, setCls] = useState<LayoutClass>(() => layoutClassFor(readViewport(), kiosk));
  useEffect(() => {
    const update = () => setCls(layoutClassFor(readViewport(), kiosk));
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, [kiosk]);
  return cls;
}
