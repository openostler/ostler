// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * ChannelPicker logic, pure (spec §5 "ChannelPicker"): the categories a session's channels
 * fall into (from the `group` the server records per channel — never hard-coded per signal;
 * vehicle-specific groups come from the pack's `layout.replay.group_categories`),
 * search over label / unit / name with highlight ranges, and the per-device pins and recents.
 */
import type { Field, SessionMeta } from "../../api/schemas";
import { groupCategories } from "../../layout";
import { channelLabel } from "./labels";

/** Platform categories; the pack's own (e.g. a chassis category) sit before Accelerometer. */
const BASE_CATEGORIES = ["GPS/Motion", "Engine", "Fuelling", "Temperatures", "Electrical", "Switches"] as const;
const TAIL_CATEGORIES = ["Accelerometer", "Other"] as const;
export type Category = string;

/** Every picker category in display order (platform ones plus the pack's). */
export function categories(): Category[] {
  const fixed = new Set<string>([...BASE_CATEGORIES, ...TAIL_CATEGORIES]);
  const extra = [...new Set(Object.values(groupCategories()))].filter((c) => !fixed.has(c));
  return [...BASE_CATEGORIES, ...extra, ...TAIL_CATEGORIES];
}

/** Raw store / session groups (any case) → picker category (platform part). */
const GROUP_MAP: Record<string, Category> = {
  gps: "GPS/Motion", motion: "GPS/Motion", position: "GPS/Motion",
  engine: "Engine", accelerator: "Engine", pressures: "Engine", pressure: "Engine", turbo: "Engine",
  fuelling: "Fuelling", fueling: "Fuelling", fuel: "Fuelling", injectors: "Fuelling",
  temperatures: "Temperatures", temperature: "Temperatures",
  electrical: "Electrical", battery: "Electrical",
  inputs: "Switches", outputs: "Switches", switches: "Switches",
  accel: "Accelerometer", accelerometer: "Accelerometer", imu: "Accelerometer",
};

/** A channel's category: its recorded group, else a guess from the GPS_/Acc naming. */
export function categoryOf(group: string | undefined, name: string): Category {
  const g = (group ?? "").trim().toLowerCase();
  const pack = groupCategories();
  const hit = GROUP_MAP[g] ?? Object.entries(pack).find(([k]) => k.toLowerCase() === g)?.[1];
  if (hit) return hit;
  if (!g) {
    if (/^(Acc_[XYZ]|InlineAcc|LateralAcc|VerticalAcc)$/.test(name)) return "Accelerometer";
    if (name.startsWith("GPS_")) return "GPS/Motion";
  }
  return "Other";
}

export type PickerChannel = { name: string; label: string; unit: string; category: Category };

/** The picker rows for the plottable `names` of a session. */
export function pickerChannels(meta: SessionMeta, names: readonly string[], fields: Record<string, Field>): PickerChannel[] {
  const byName = new Map(meta.channels.map((c) => [c.name, c]));
  return names.map((n) => {
    const c = byName.get(n);
    return { name: n, label: channelLabel(n, fields), unit: c?.units ?? fields[n]?.unit ?? "", category: categoryOf(c?.group || fields[n]?.group, n) };
  });
}

/** Rows grouped in category order (empty categories dropped; rows keep their order). */
export function groupChannels(rows: readonly PickerChannel[]): { category: Category; rows: PickerChannel[] }[] {
  return categories().map((category) => ({ category, rows: rows.filter((r) => r.category === category) })).filter((g) => g.rows.length);
}

const terms = (q: string) => q.toLowerCase().split(/\s+/).filter(Boolean);

/** Rows whose label, unit or name contain every search term (case-insensitive). */
export function searchChannels(rows: readonly PickerChannel[], q: string): PickerChannel[] {
  const ts = terms(q);
  if (!ts.length) return rows.slice();
  return rows.filter((r) => {
    const hay = `${r.label} ${r.unit} ${r.name} ${r.name.replace(/_/g, " ")}`.toLowerCase();
    return ts.every((t) => hay.includes(t));
  });
}

/** `text` cut into plain and matched pieces for highlighting the search terms. */
export function highlight(text: string, q: string): { text: string; hit: boolean }[] {
  const ts = terms(q);
  if (!ts.length || !text) return [{ text, hit: false }];
  const lower = text.toLowerCase();
  const mark = new Uint8Array(text.length);
  for (const t of ts) {
    for (let i = lower.indexOf(t); i >= 0; i = lower.indexOf(t, i + 1)) mark.fill(1, i, i + t.length);
  }
  const out: { text: string; hit: boolean }[] = [];
  for (let i = 0; i < text.length; i++) {
    const hit = mark[i] === 1;
    const last = out[out.length - 1];
    if (last && last.hit === hit) last.text += text[i];
    else out.push({ text: text[i]!, hit });
  }
  return out;
}

/* ---- pins and recents (per device) ---- */

export const PINS_KEY = "d2diag.pinnedChannels";
export const RECENT_KEY = "d2diag.recentChannels";
export const MAX_RECENT = 6;

/** Default pins (spec): road speed, rpm, accelerator pedal, lateral acceleration. */
export const DEFAULT_PINS = ["speed", "GPS_Speed", "rpm", "accel_pedal_pct", "LateralAcc"];

function readList(key: string): string[] | null {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw == null) return null;
    const v: unknown = JSON.parse(raw);
    return Array.isArray(v) ? v.filter((x): x is string => typeof x === "string") : null;
  } catch {
    return null;
  }
}
function writeList(key: string, list: string[]): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(list));
  } catch {
    /* storage blocked: pins/recents just aren't remembered */
  }
}

/** The pinned channel names (the defaults until the owner changes a pin). GPS_Speed is a
 * default only when the ECU `speed` is absent from `present`. */
export function loadPins(present?: readonly string[]): string[] {
  const stored = readList(PINS_KEY);
  if (stored) return stored;
  const has = (n: string) => !present || present.includes(n);
  return DEFAULT_PINS.filter((n) => !(n === "GPS_Speed" && has("speed")));
}

/** Toggle a pin and persist the whole list (so un-pinning a default sticks). */
export function togglePin(pins: readonly string[], name: string): string[] {
  const next = pins.includes(name) ? pins.filter((n) => n !== name) : [...pins, name];
  writeList(PINS_KEY, next);
  return next;
}

export const loadRecent = (): string[] => readList(RECENT_KEY) ?? [];

/** Put `name` first in the recents (deduplicated, at most MAX_RECENT) and persist. */
export function pushRecent(recent: readonly string[], name: string): string[] {
  const next = [name, ...recent.filter((n) => n !== name)].slice(0, MAX_RECENT);
  writeList(RECENT_KEY, next);
  return next;
}
