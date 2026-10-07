// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Drive modes on the server (drive-modes spec §8.3, DM2): this display's id, the stored
 * Drive-mode layouts of this vehicle and class (resolved user → car → pack on the server; the
 * shell's presets are the generated tier), and the selected mode per display.
 *
 * The server is the source of truth; localStorage stays the first paint and the offline
 * fallback (`useDriveModes`). The profile is `car` (the head unit's kiosk session) until
 * accounts land; the vehicle is the server's `current` one.
 */
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LayoutEntry } from "../api/schemas";
import type { LayoutClass } from "../shell/layoutClass";
import { facesFor, type Layout } from "./types";
import { validateLayout } from "./validate";

const DISPLAY_KEY = "ostler.display.v1";
const ID = /^[a-z0-9][a-z0-9_-]{0,63}$/;

function mint(): string {
  const bytes = new Uint8Array(6);
  try {
    crypto.getRandomValues(bytes);
  } catch {
    for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  }
  return `d${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
}

/** This display's id: `?display_id=` (a kiosk's configuration, tests), else one minted once
 * per browser and kept in localStorage (a fresh one each time when storage is blocked). */
export function displayId(search: string = window.location.search): string {
  const q = new URLSearchParams(search).get("display_id");
  if (q && ID.test(q)) return q;
  try {
    const kept = localStorage.getItem(DISPLAY_KEY);
    if (kept && ID.test(kept)) return kept;
    const id = mint();
    localStorage.setItem(DISPLAY_KEY, id);
    return id;
  } catch {
    return mint();
  }
}

/** The stored entries a display can render: Drive-mode documents for this class that the
 * shell's validator accepts (the server validated them on write; this is defence in depth). */
export function usableModes(entries: readonly LayoutEntry[], cls: LayoutClass): Layout[] {
  const out: Layout[] = [];
  for (const e of entries) {
    const doc = e.layout as unknown;
    if (!doc || (doc as Layout).kind !== "drive_mode") continue;
    if (validateLayout(doc).errors.length) continue;
    if (!facesFor(doc as Layout, cls).length) continue;
    out.push(doc as Layout);
  }
  return out;
}

const NONE: Layout[] = [];

/** The stored Drive modes for this class (empty until loaded, and when the server has none or
 * cannot be reached). */
export function useStoredModes(cls: LayoutClass): Layout[] {
  const [state, setState] = useState<{ cls: LayoutClass; modes: Layout[] }>({ cls, modes: NONE });
  useEffect(() => {
    let alive = true;
    api.layouts(cls, "drive_mode").then(
      (r) => {
        const modes = usableModes(r.layouts, cls);
        if (alive && modes.length) setState({ cls, modes });
      },
      () => undefined, // offline or no Brain: the presets alone
    );
    return () => { alive = false; };
  }, [cls]);
  return state.cls === cls ? state.modes : NONE;
}

export type Selection = { mode: string; faces?: Record<string, number>; rotation?: string[] };

/** Remember the selection on the server; never throws. A refused rotation change (Park to
 * edit: a reorder is an edit) still saves the mode and face without it. */
export async function pushSelection(display: string, cls: LayoutClass, sel: Selection): Promise<void> {
  try {
    const r = await api.setDriveSelection(display, cls, sel);
    if (r.ok === false && r.code === "park_to_edit" && sel.rotation) {
      await api.setDriveSelection(display, cls, { mode: sel.mode, faces: sel.faces });
    }
  } catch {
    /* offline: localStorage keeps it for this display */
  }
}
