// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Snapshot } from "../api/schemas";
import type { SymbolName } from "../icons/Icon";
import { connOf, pillFor } from "../lib/connection";
import { parseFault } from "../lib/format";
import { isPaused } from "../components/replay/sessionFormat";
import type { LayoutClass } from "./layoutClass";

/**
 * The persistent status strip as data (UI spec §3.2; app-model spec §9, seam 5): this module
 * turns the shell's state into chip descriptors, ordered by severity, and the shell draws
 * them (Strip.tsx). Pure, so the rules are unit-tested without React.
 *
 * Each chip pairs an icon with a word and is at least 48 px tall. U1 has the Worst
 * telltale, Link, REC, 12 V, Clock and Mark chips (plus the admin badge); Vehicle waits for
 * the garage (U6), Security and the device slot for the node and add-on manifests (U5).
 * In Drive mode the strip leads with Back, so the mode needs no page chrome (§12.3).
 */
export type ChipTone = "neutral" | "ok" | "warn" | "alarm" | "replay";
/** What tapping a chip opens; `status` chips are not interactive. */
export type ChipOpen = "faults" | "connection" | "exit-replay" | "logs" | "back";

export type ChipDescriptor = {
  id: "back" | "admin" | "telltale" | "link" | "rec" | "battery" | "clock" | "mark";
  /** `button` opens something, `status` only shows, `mark` is the shell's Mark control. */
  kind: "button" | "status" | "mark";
  icon: SymbolName | null;
  /** The visible word (always shown). */
  word: string;
  /** A badge shown next to the word on every class (power state, §3.8), with its icon. */
  note?: string;
  noteIcon?: SymbolName;
  /** Extra visible text dropped on the phone (the system holding the session). */
  detail?: string;
  /** The accessible name; it always contains the visible text (WCAG 2.5.3). */
  label: string;
  tone: ChipTone;
  /** Draw attention (a new fault); only an alarm-toned chip moves (§2.7). */
  attention?: boolean;
  /** Connection-dot class for the Link chip (pillFor). */
  dot?: string;
  open?: ChipOpen;
};

export type StripInput = {
  layout: LayoutClass;
  snap: Snapshot | null;
  /** The dashboard's own SSE stream is up. */
  linkUp: boolean;
  replaying: boolean;
  admin: boolean;
  /** The display name of the system holding the ECU session. */
  systemName: string;
  /** Faults not yet acknowledged in the fault sheet. */
  unacked: number;
  /** The clock text (HH:MM). */
  clock: string;
  /** Formats a quantity with Intl (lib/units.ts). */
  quantity: (v: number, unit: string, dec?: number) => string;
  /** Drive mode is open: the strip carries its Back control (§12.3). */
  driveMode?: boolean;
};

/** The chips the phone keeps (§3.2: chips 2–5 and 9, plus the service/admin badge and
 * Drive mode's Back); HU-5 keeps the clock too (§12.3). */
const PHONE: ReadonlySet<ChipDescriptor["id"]> = new Set(["back", "admin", "telltale", "link", "rec", "mark"]);
const HU5: ReadonlySet<ChipDescriptor["id"]> = new Set([...PHONE, "clock"]);

/** A node's power record as a badge, icon and word (ADR-0040, §3.8); null when awake or
 * unknown. Asleep is not offline: Offline is only an unexpected loss. Off is reported by the
 * device's power owner, so a device that is off and unreachable reads Off, not Offline. */
export function powerNote(snap: Snapshot | null): { word: string; icon: SymbolName } | null {
  const node = snap?.node;
  if (!node) return null;
  if (node.power?.state === "off") return { word: "Off", icon: "power_settings_new" };
  if (node.status === "offline") return { word: "Offline", icon: "warning" };
  switch (node.power?.state) {
    case "asleep": return { word: "Asleep", icon: "bedtime" };
    case "waking": return { word: "Waking…", icon: "hourglass_top" };
    case "held": return { word: "Kept awake", icon: "power_settings_new" };
    case "shutting_down": return { word: "Shutting down", icon: "power_settings_new" };
    default: return null;
  }
}

/** The worst active warning (§3.2 chip 2): current faults are an alarm, logged ones a warning. */
function telltale(snap: Snapshot | null, unacked: number): ChipDescriptor | null {
  const faults = snap?.faults ?? [];
  if (!faults.length) return null;
  const current = faults.some((f) => parseFault(f).current);
  const word = `${faults.length} fault${faults.length > 1 ? "s" : ""}`;
  return {
    id: "telltale", kind: "button", icon: current ? "error" : "warning", word,
    label: unacked ? `${word}, ${unacked} new` : word,
    tone: current ? "alarm" : "warn", attention: unacked > 0, open: "faults",
  };
}

function link(i: StripInput): ChipDescriptor {
  if (i.replaying) {
    return {
      id: "link", kind: "button", icon: "history", word: "Replay", detail: "Exit to live",
      label: "Replay — Exit to live", tone: "replay", open: "exit-replay",
    };
  }
  const [dot, rung] = pillFor(connOf(i.snap), i.linkUp);
  const power = powerNote(i.snap);
  const label = [rung, power?.word, i.systemName].filter(Boolean).join(" · ");
  return {
    id: "link", kind: "button", icon: null, word: rung, note: power?.word, noteIcon: power?.icon,
    detail: i.systemName || undefined,
    label, tone: "neutral", dot, open: "connection",
  };
}

function rec(snap: Snapshot | null, replaying: boolean): ChipDescriptor | null {
  const r = snap?.recording;
  if (replaying || !r) return null;
  const paused = isPaused(r);
  return {
    id: "rec", kind: "button", icon: "fiber_manual_record-fill", word: paused ? "Paused" : "REC",
    label: paused ? "Paused — recording, open Logs" : "REC — recording, open Logs",
    tone: paused ? "neutral" : "alarm", open: "logs",
  };
}

/** The strip's chips for this state, left to right by severity (§3.2). */
export function stripChips(i: StripInput): ChipDescriptor[] {
  const chips: (ChipDescriptor | null)[] = [
    i.driveMode ? { id: "back", kind: "button", icon: "arrow_back", word: "Back", label: "Back", tone: "neutral", open: "back" } : null,
    i.admin ? { id: "admin", kind: "status", icon: "code", word: "admin", label: "admin", tone: "neutral" } : null,
    i.replaying ? null : telltale(i.snap, i.unacked),
    link(i),
    rec(i.snap, i.replaying),
    typeof i.snap?.battery_v === "number" ? {
      id: "battery", kind: "status", icon: "battery_full", word: i.quantity(i.snap.battery_v, "V", 1),
      label: `Car battery ${i.quantity(i.snap.battery_v, "V", 1)}`, tone: "neutral",
    } : null,
    { id: "clock", kind: "status", icon: null, word: i.clock, label: `Time ${i.clock}`, tone: "neutral" },
    { id: "mark", kind: "mark", icon: "flag", word: "Mark", label: "Mark", tone: "neutral" },
  ];
  const all = chips.filter((c): c is ChipDescriptor => c !== null);
  if (i.layout === "phone") return all.filter((c) => PHONE.has(c.id));
  return i.layout === "hu5" ? all.filter((c) => HU5.has(c.id)) : all;
}
