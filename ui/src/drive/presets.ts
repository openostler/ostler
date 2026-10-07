// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The seven Drive-mode presets (drive-modes spec §5; CC BY-SA 4.0 data files in ./presets),
 * which modes a display may offer, and the default mode and rotation per layout class
 * (§5.9). A mode whose `requires.capabilities` are missing (Convoy without an active ride,
 * Split / Media without a media source) is hidden from the switcher, never shown broken (§6).
 */
import type { LayoutClass } from "../shell/layoutClass";
import type { Capability, Layout } from "./types";

const FILES = import.meta.glob<Layout>("./presets/*.json", { import: "default", eager: true });

/** The preset order of the mode list. */
const ORDER = ["dashboard", "map", "diagnostic", "minimal", "offroad", "convoy", "split"];

export const PRESETS: readonly Layout[] = ORDER.map((n) => {
  const doc = FILES[`./presets/${n}.json`];
  if (!doc) throw new Error(`missing Drive-mode preset ${n}`);
  return doc;
});

export const presetById = (id: string): Layout | undefined => PRESETS.find((p) => p.id === id);

/** The mode list holds at most six modes (a `short_list`, §6); the rotation at most four. */
export const MAX_LIST = 6;
export const MAX_ROTATION = 4;

/** What this display can offer: capabilities the vehicle and add-ons provide. Before the
 * capability manifest (U3/U5) nothing provides a media source or a ride. */
export type DriveCaps = ReadonlySet<Capability>;

/** The test and kiosk seam `?caps=media_source,ride_active` (like `?display=`), standing in
 * for the capability manifest until U3/U5; unknown names are ignored. */
export function parseCaps(search: string): DriveCaps {
  const raw = new URLSearchParams(search).get("caps") ?? "";
  const known: Capability[] = ["media_source", "ride_active"];
  return new Set(raw.split(",").filter((c): c is Capability => (known as string[]).includes(c)));
}

/** A mode is available when every capability it requires is present. */
export const isAvailable = (m: Layout, caps: DriveCaps): boolean =>
  (m.requires?.capabilities ?? []).every((c) => caps.has(c));

/** The modes this display may offer, in list order (§6: hidden ones are absent). */
export const availableModes = (caps: DriveCaps): Layout[] => PRESETS.filter((m) => isAvailable(m, caps));

/** §5.9: the default mode per class. */
export function defaultMode(cls: LayoutClass, caps: DriveCaps): string {
  if (cls === "tablet" || cls === "desktop") return "ostler.diagnostic";
  if (cls === "huwide" && caps.has("media_source")) return "ostler.split";
  return "ostler.dashboard";
}

/** §5.9: the default one-tap rotation per class, keeping only available modes. */
export function defaultRotation(cls: LayoutClass, caps: DriveCaps): string[] {
  const ids: Record<LayoutClass, string[]> = {
    hu5: ["dashboard", "map", "diagnostic", "minimal"],
    hu7: ["dashboard", "map", "diagnostic", "minimal"],
    hu9: ["dashboard", "map", "diagnostic", "minimal"],
    huwide: ["dashboard", "split", "diagnostic", "minimal"],
    phone: ["dashboard", "map", "diagnostic"],
    tablet: ["diagnostic"],
    desktop: ["diagnostic"],
  };
  return ids[cls].map((n) => `ostler.${n}`).filter((id) => {
    const m = presetById(id);
    return m !== undefined && isAvailable(m, caps);
  });
}
