// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useState } from "react";
import type { Units } from "../lib/format";
import { applyTheme, isThemePref, type ThemePref } from "./theme";

/** Per-device preferences. Same localStorage key as the legacy v2 page, so a phone keeps
 * its trust/consent/units choices across the switch. Storage may be unavailable
 * (private mode) — then defaults apply for the session. */
export type Prefs = {
  trust: "trusted" | "experimental";
  consentDone: boolean;
  share: boolean | null;
  /** Night ("dark") by default; "auto" follows the OS (state/theme.ts, visual spec §1). */
  theme: ThemePref;
  units: Units;
};

const KEY = "d2diag.v2";
export const DEFAULT_PREFS: Prefs = {
  trust: "trusted",
  consentDone: false,
  share: null,
  theme: "dark",
  units: { temp: "C", dist: "km" },
};

export function loadPrefs(): Prefs {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<Prefs>;
    const p = { ...DEFAULT_PREFS, ...raw, units: { ...DEFAULT_PREFS.units, ...(raw.units ?? {}) } };
    return isThemePref(p.theme) ? p : { ...p, theme: DEFAULT_PREFS.theme };
  } catch {
    return DEFAULT_PREFS;
  }
}

function savePrefs(p: Prefs): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* storage blocked — preferences last for this session only */
  }
}

export function usePrefs() {
  const [prefs, setPrefs] = useState<Prefs>(loadPrefs);
  useEffect(() => applyTheme(prefs.theme), [prefs.theme]);
  const update = useCallback((patch: Partial<Prefs>) => {
    setPrefs((p) => {
      const next = { ...p, ...patch, units: { ...p.units, ...(patch.units ?? {}) } };
      savePrefs(next);
      return next;
    });
  }, []);
  return [prefs, update] as const;
}

/** JSON list in localStorage (capture log, map readings); never throws. */
export function readList<T>(key: string): T[] {
  try {
    const v = JSON.parse(localStorage.getItem(key) ?? "[]") as unknown;
    return Array.isArray(v) ? (v as T[]) : [];
  } catch {
    return [];
  }
}
export function writeList<T>(key: string, list: T[]): void {
  try {
    localStorage.setItem(key, JSON.stringify(list));
  } catch {
    /* storage blocked */
  }
}
