// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useRef, useState } from "react";
import type { Snapshot } from "../api/schemas";
import type { DrivingState } from "../shell/landing";
import { isHeadUnit, type LayoutClass } from "../shell/layoutClass";
import { LIMITS } from "./types";

/** The snapshot as the face shows it: at most one update per `ms` (≤ 4 Hz, §4.3). */
export function useStepped(snap: Snapshot | null, ms = 1000 / LIMITS.moving.max_refresh_hz): Snapshot | null {
  const [shown, setShown] = useState(snap);
  const last = useRef(0);
  useEffect(() => {
    const wait = last.current + ms - Date.now();
    const show = () => {
      last.current = Date.now();
      setShown(snap);
    };
    if (wait <= 0) {
      show();
      return undefined;
    }
    const id = window.setTimeout(show, wait);
    return () => window.clearTimeout(id);
  }, [snap, ms]);
  return shown;
}

/** Does this display render the Moving section? Every class whose faces must carry one
 * (head units and the phone) does, unless the car is known to be Parked or Idling on a head
 * unit; tablet and desktop are not driver-facing and show the full grid. */
export function showsMoving(cls: LayoutClass, driving: DrivingState): boolean {
  if (!LIMITS.classes[cls].moving_required) return false;
  if (isHeadUnit(cls)) return !(driving === "parked" || driving === "idling");
  return true;
}

