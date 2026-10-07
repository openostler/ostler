// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The ONE confirmation for anything that writes to an ECU or drives hardware (actuators,
 * clear faults, shutdown): the shell-drawn `ConfirmSheet` (components/ConfirmSheet.tsx), which
 * opens with Cancel focused, ignores `ok` for its first 500 ms and never counts down (shell
 * input spec §7). This module holds the rules every caller shares.
 */
export const SAFETY = "Vehicle stationary, handbrake on, ignition on, nobody under the car.";

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
