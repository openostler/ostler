// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The Drive menu's rows (shell input spec §6; UI spec §12.1 `short_list`): at most six rows,
 * one level, at most 30 characters a row (label and state together), each a driver-safe item
 * with its state on the right. Pure, so the limits are unit-tested.
 *
 * Only items that exist today are offered, never a stand-in: **Mark** (while a live recording
 * can take one), **Drive mode** (opens the mode list; its state is the current mode), **Exit to
 * Home** (what the strip's Back chip does) and **Back to Drive** (closes the menu). The spec's
 * Mute alerts, media, climate setpoint and Arm rows join when alerts, a media source, Comfort
 * and Security exist; add-on rows (`contributes.drive_menu`) when the app model does. A row that
 * would need a confirm sheet while Moving is never offered.
 */
import type { SymbolName } from "../icons/Icon";

export type DriveMenuRowId = "mark" | "mode" | "exit" | "back";
export type DriveMenuRow = { id: DriveMenuRowId; label: string; state?: string; icon: SymbolName };

export const MAX_ROWS = 6;
export const MAX_CHARS = 30;

/** Cut a row's state (never its label) so label + space + state fits 30 characters. */
export function fitRow(r: DriveMenuRow): DriveMenuRow {
  if (!r.state) return { ...r, label: [...r.label].slice(0, MAX_CHARS).join("") };
  const room = MAX_CHARS - [...r.label].length - 1;
  const chars = [...r.state];
  if (chars.length <= room) return r;
  return { ...r, state: room > 1 ? `${chars.slice(0, room - 1).join("")}…` : undefined };
}

export function driveMenuRows(i: { canMark: boolean; mode: { name: string; icon: SymbolName } }): DriveMenuRow[] {
  const rows: (DriveMenuRow | null)[] = [
    i.canMark ? { id: "mark", label: "Mark", icon: "flag" } : null,
    { id: "mode", label: "Drive mode", state: i.mode.name, icon: i.mode.icon },
    { id: "exit", label: "Exit to Home", icon: "home" },
    { id: "back", label: "Back to Drive", icon: "close" },
  ];
  return rows.filter((r): r is DriveMenuRow => r !== null).map(fitRow).slice(0, MAX_ROWS);
}
