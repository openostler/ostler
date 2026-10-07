// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The Drive-mode switcher's state (drive-modes spec §6): the active mode and face, the
 * one-tap rotation (≤ 4) and the mode list (≤ 6), remembered per display.
 *
 * DM1 keeps this in the browser's localStorage under the display's vehicle and layout class
 * (the head unit's kiosk session is the Car profile); server storage per display × profile ×
 * vehicle, and R1/R7 on the server, arrive with the editor in DM2 (§8.3). Nothing here
 * switches by itself: only the driver's tap or pick changes the mode (Decision 6).
 */
import { useCallback, useMemo, useState } from "react";
import type { LayoutClass } from "../shell/layoutClass";
import { availableModes, defaultMode, defaultRotation, MAX_LIST, MAX_ROTATION, presetById, type DriveCaps } from "./presets";
import { facesFor, type Face, type Layout } from "./types";

const KEY = "ostler.drive.v1";

type DisplayState = { mode?: string; faces?: Record<string, number>; rotation?: string[] };
type Stored = Record<string, DisplayState>;

function load(): Stored {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as unknown;
    return raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Stored) : {};
  } catch {
    return {};
  }
}

function save(display: string, s: DisplayState): void {
  try {
    localStorage.setItem(KEY, JSON.stringify({ ...load(), [display]: s }));
  } catch {
    /* storage blocked: the choice lasts for this session only */
  }
}

export type DriveModes = {
  /** The mode on screen and its faces for this class. */
  active: Layout;
  faces: Face[];
  face: number;
  /** The one-tap rotation (≤ 4) and the list (≤ 6: the rotation first, then the others). */
  rotation: Layout[];
  list: Layout[];
  /** Tap: the next mode of the rotation (or the list when the rotation has one mode). */
  cycle: () => void;
  pick: (id: string) => void;
  /** Faces wrap (§6). */
  stepFace: (dir: 1 | -1) => void;
  listOpen: boolean;
  openList: () => void;
  closeList: () => void;
};

export function useDriveModes({ cls, pack, caps }: { cls: LayoutClass; pack: string; caps: DriveCaps }): DriveModes {
  const display = `${pack || "none"}/${cls}`;
  const [state, setState] = useState<DisplayState>(() => load()[display] ?? {});
  const [shownFor, setShownFor] = useState(display);
  // another display key (a resize into another class): read its own remembered state
  if (shownFor !== display) {
    setShownFor(display);
    setState(load()[display] ?? {});
  }
  const [listOpen, setListOpen] = useState(false);

  const available = useMemo(() => availableModes(caps), [caps]);
  const isOffered = useCallback((id: string | undefined) => !!id && available.some((m) => m.id === id), [available]);
  const rotationIds = useMemo(() => {
    const ids = (state.rotation ?? defaultRotation(cls, caps)).filter(isOffered).slice(0, MAX_ROTATION);
    return ids.length ? ids : [defaultMode(cls, caps)];
  }, [state.rotation, cls, caps, isOffered]);
  const activeId = isOffered(state.mode) ? state.mode! : defaultMode(cls, caps);
  const active = presetById(activeId) ?? available[0]!;
  const faces = facesFor(active, cls);
  const face = Math.min(Math.max(0, state.faces?.[active.id] ?? 0), Math.max(0, faces.length - 1));

  const rotation = rotationIds.map((id) => presetById(id)).filter((m): m is Layout => !!m);
  const list = [...rotation, ...available.filter((m) => !rotationIds.includes(m.id))].slice(0, MAX_LIST);

  const update = useCallback((next: DisplayState) => {
    setState(next);
    save(display, next);
  }, [display]);

  const pick = useCallback((id: string) => {
    const m = presetById(id);
    if (!m || !isOffered(id)) return;
    // a mode the pack hints joins the rotation the first time it is picked (§5.9)
    let rot = state.rotation;
    if (m.vehicle_hint?.pack === pack && !rotationIds.includes(id) && rotationIds.length < MAX_ROTATION) rot = [...rotationIds, id];
    update({ ...state, mode: id, rotation: rot });
    setListOpen(false);
  }, [state, update, isOffered, pack, rotationIds]);

  const cycle = useCallback(() => {
    if (rotationIds.length < 2) {
      setListOpen(true);
      return;
    }
    const i = rotationIds.indexOf(activeId);
    update({ ...state, mode: rotationIds[(i + 1) % rotationIds.length] });
  }, [rotationIds, activeId, state, update]);

  const stepFace = useCallback((dir: 1 | -1) => {
    if (faces.length < 2) return;
    const next = (face + dir + faces.length) % faces.length;
    update({ ...state, faces: { ...state.faces, [active.id]: next } });
  }, [faces.length, face, state, update, active.id]);

  return {
    active, faces, face, rotation, list, cycle, pick, stepFace, listOpen,
    openList: useCallback(() => setListOpen(true), []),
    closeList: useCallback(() => setListOpen(false), []),
  };
}
