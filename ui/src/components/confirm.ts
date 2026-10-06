// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The ONE confirmation for anything that writes to an ECU or drives hardware
 * (actuators, clear faults, shutdown). Kept as a plain function so every caller states
 * the same safety conditions; tests stub window.confirm.
 */
export const SAFETY = "Vehicle stationary, handbrake on, ignition on, nobody under the car.";

export function confirmAction(title: string, detail: string = SAFETY): boolean {
  return window.confirm(`${title}\n\n${detail}`);
}

/**
 * Friction proportional to consequence, per the registry's `confirm` level (ADR-0008):
 * none → run; preconditions → every listed condition ticked; typed → the item's name
 * typed exactly. Pure, so ActionButton and its tests share one rule.
 */
export function confirmReady(level: string, s: { ticked: boolean[]; typed: string; name: string }): boolean {
  if (level === "none") return true;
  if (level === "typed") return s.typed.trim() === s.name.trim();
  return s.ticked.length > 0 && s.ticked.every(Boolean); // preconditions (and anything unknown)
}
