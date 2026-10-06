// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { Field, Snapshot } from "../api/schemas";
import { parseFault } from "./format";

export type Health = {
  level: "ok" | "warn" | "alarm" | "offline";
  /** Signals the server flags low/high/suspect (from the store's limits). */
  outOfRange: string[];
  current: number;
  logged: number;
  headline: string;
};

/**
 * The one-glance answer to "is the car OK?" — ISA-101 style: nothing to see when
 * healthy. Current faults or an out-of-range value are alarms; logged faults or a
 * suspect reading are warnings. Pure, so it is unit-tested.
 */
export function summarize(snap: Snapshot | null, fields: Record<string, Field>): Health {
  if (!snap || snap.status !== "connected") {
    return { level: "offline", outOfRange: [], current: 0, logged: 0, headline: snap?.status === "error" ? "Not connected" : "Connecting…" };
  }
  const outOfRange = Object.entries(snap.signals)
    .filter(([, s]) => s.s === "low" || s.s === "high")
    .map(([n]) => n);
  const suspect = Object.values(snap.signals).filter((s) => s.s === "suspect").length;
  const parsed = snap.faults.map(parseFault);
  const current = parsed.filter((f) => f.current).length;
  const logged = parsed.length - current;
  const label = (n: string) => fields[n]?.label ?? n;

  const parts: string[] = [];
  if (current) parts.push(`${current} current fault${current > 1 ? "s" : ""}`);
  if (outOfRange.length === 1) parts.push(`${label(outOfRange[0]!)} ${snap.signals[outOfRange[0]!]?.s === "high" ? "high" : "low"}`);
  else if (outOfRange.length > 1) parts.push(`${outOfRange.length} values out of range`);
  if (logged) parts.push(`${logged} logged fault${logged > 1 ? "s" : ""}`);
  if (suspect) parts.push(`${suspect} suspect reading${suspect > 1 ? "s" : ""}`);

  const level = current || outOfRange.length ? "alarm" : logged || suspect ? "warn" : "ok";
  return { level, outOfRange, current, logged, headline: parts.length ? parts.join(" · ") : "All normal" };
}
