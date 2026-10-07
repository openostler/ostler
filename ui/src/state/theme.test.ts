// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_PREFS, loadPrefs } from "./prefs";
import { applyTheme, resolveTheme } from "./theme";

afterEach(() => {
  vi.unstubAllGlobals();
  applyTheme("dark");
});

/** A controllable prefers-color-scheme: light query. */
function fakeOs(light: boolean) {
  const listeners = new Set<() => void>();
  const mq = {
    matches: light,
    addEventListener: (_: string, fn: () => void) => listeners.add(fn),
    removeEventListener: (_: string, fn: () => void) => listeners.delete(fn),
  };
  vi.stubGlobal("matchMedia", () => mq);
  return { set(v: boolean) { mq.matches = v; listeners.forEach((f) => f()); }, listeners };
}

describe("themes (visual design system spec §1, §2)", () => {
  it("defaults to Night and keeps an explicit choice", () => {
    expect(DEFAULT_PREFS.theme).toBe("dark");
    expect(resolveTheme("light", { osLight: false })).toBe("light");
    expect(resolveTheme("dim", { osLight: true })).toBe("dim");
    expect(resolveTheme("oled", { osLight: true })).toBe("oled");
  });

  it("resolves Auto from the OS, and to Night dim when a night signal says so", () => {
    expect(resolveTheme("auto", { osLight: true })).toBe("light");
    expect(resolveTheme("auto", { osLight: false })).toBe("dark");
    expect(resolveTheme("auto", { osLight: true, night: true })).toBe("dim");
  });

  it("always writes a concrete data-theme and follows the OS only while on Auto", () => {
    const os = fakeOs(true);
    applyTheme("auto");
    expect(document.documentElement.dataset.theme).toBe("light");
    os.set(false);
    expect(document.documentElement.dataset.theme).toBe("dark");
    applyTheme("oled");
    expect(document.documentElement.dataset.theme).toBe("oled");
    expect(os.listeners.size).toBe(0);
    os.set(true);
    expect(document.documentElement.dataset.theme).toBe("oled");
  });

  it("drops an unknown stored theme", () => {
    localStorage.setItem("d2diag.v2", JSON.stringify({ theme: "sepia" }));
    expect(loadPrefs().theme).toBe("dark");
    localStorage.setItem("d2diag.v2", JSON.stringify({ theme: "dim" }));
    expect(loadPrefs().theme).toBe("dim");
  });
});
