// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Route names (app-model spec §9, seam 6): screens navigate with `goTo(<route name>)`, never
 * by tab id or path. A route is `<destination>` or `<destination>.<view>`; "drive" opens
 * Drive mode, which is a mode over the shell, not a destination (UI spec §3.5).
 */
export const ROUTES = [
  "home",
  "drive",
  "diagnose",
  "diagnose.faults",
  "diagnose.live",
  "diagnose.tests",
  "diagnose.procedures",
  "diagnose.settings",
  "logs",
  "logs.analysis",
  "security",
  "more",
  "more.decode",
  "more.label",
  "more.docs",
] as const;
export type RouteName = (typeof ROUTES)[number];

export type DestinationId = "home" | "diagnose" | "logs" | "security" | "more";

export const isRoute = (r: string): r is RouteName => (ROUTES as readonly string[]).includes(r);

/** The destination a route belongs to (Drive mode sits over Home). */
export function destinationOf(r: RouteName): DestinationId {
  const head = r.split(".")[0];
  return head === "drive" ? "home" : (head as DestinationId);
}

/** The view part of a route ("diagnose.faults" → "faults"; "diagnose" → null). */
export const viewOf = (r: RouteName): string | null => r.split(".")[1] ?? null;

/** The Diagnose function areas (UI spec §3.4, §4.2) in canonical order. Overview waits for
 * Scan all (U3); an area with no items disappears. */
export const DIAGNOSE_AREAS = ["faults", "live", "tests", "procedures", "settings"] as const;
export type DiagnoseArea = (typeof DIAGNOSE_AREAS)[number];
