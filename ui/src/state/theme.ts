// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useSyncExternalStore } from "react";

/**
 * Themes (visual design system spec §1, §2, §3.1). Night is the default on every layout class;
 * Day is an equal choice; Night dim (head units after dusk) and Deep night (OLED black) are the
 * night variants; Auto follows the OS. The tokens put Night at `:root` and the others under
 * `:root[data-theme=…]`, and the app always writes a concrete `data-theme` (Auto resolved)
 * before the first render (main.tsx), so the CSS never guesses (no inline script: the CSP is
 * `script-src 'self'`).
 */
export type ThemePref = "auto" | "light" | "dark" | "dim" | "oled";
export type Theme = Exclude<ThemePref, "auto">;

export const THEME_PREFS: { id: ThemePref; label: string }[] = [
  { id: "auto", label: "Auto" },
  { id: "light", label: "Day" },
  { id: "dark", label: "Night" },
  { id: "dim", label: "Night dim" },
  { id: "oled", label: "Deep night" },
];

const THEMES: readonly Theme[] = ["light", "dark", "dim", "oled"];
export const isThemePref = (v: unknown): v is ThemePref => v === "auto" || THEMES.includes(v as Theme);

/** The concrete theme for a preference. Auto follows the OS (light → Day, else Night). A head
 * unit's sun or headlight signal (Auto → Night dim after dusk) has no source yet; it plugs in
 * here as `night`. */
export function resolveTheme(pref: ThemePref, env: { osLight: boolean; night?: boolean }): Theme {
  if (pref !== "auto") return pref;
  if (env.night) return "dim";
  return env.osLight ? "light" : "dark";
}

const osLight = () =>
  typeof window !== "undefined" && typeof window.matchMedia === "function" ? window.matchMedia("(prefers-color-scheme: light)") : null;

let stopFollowing: (() => void) | null = null;

/** Write the resolved theme on <html data-theme> (and the browser's theme-color), and while the
 * preference is Auto, follow the OS as it changes. Safe to call again: the last call wins. */
export function applyTheme(pref: ThemePref): void {
  stopFollowing?.();
  stopFollowing = null;
  const root = document.documentElement;
  const mq = osLight();
  const set = () => {
    root.setAttribute("data-theme", resolveTheme(pref, { osLight: !!mq?.matches }));
    const bg = getComputedStyle(root).getPropertyValue("--bg").trim();
    if (bg) document.querySelector('meta[name="theme-color"]')?.setAttribute("content", bg);
  };
  set();
  if (pref === "auto" && mq) {
    mq.addEventListener("change", set);
    stopFollowing = () => mq.removeEventListener("change", set);
  }
}

const current = (): Theme => {
  const t = document.documentElement.getAttribute("data-theme");
  return THEMES.includes(t as Theme) ? (t as Theme) : "dark";
};
function subscribe(onChange: () => void): () => void {
  const obs = new MutationObserver(onChange);
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => obs.disconnect();
}

/** The theme in force now (re-renders when it changes), for Canvas and MapLibre, which read
 * colours through `token()` and must redraw on a theme switch. */
export const useTheme = (): Theme => useSyncExternalStore(subscribe, current, () => "dark");

/** True for the dark themes (Night, Night dim, Deep night). */
export const isDark = (t: Theme) => t !== "light";
