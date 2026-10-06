// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { RouteName } from "./routes";

/**
 * Driving state (UI spec §3.5). The platform computes it so the server can enforce it; until
 * U2 ships that, the shell knows no state ("unknown") and enforces no lockout itself; the
 * server gate stays the authority on every action. U2 adds the head-unit rule "unknown
 * speed counts as Moving" together with the lockouts it implies.
 */
export type DrivingState = "parked" | "idling" | "moving" | "unknown";

/**
 * The screen the app opens on (§3.4, "landing follows the driving state"): Drive mode when
 * Moving, Security when Parked and armed, the developer pages on /admin (kept for one
 * release, ADR-0018 Q8; service mode is U2), otherwise Home.
 */
export function landingFor(s: { driving: DrivingState; armed?: boolean; admin?: boolean }): RouteName {
  if (s.driving === "moving") return "drive";
  if (s.admin) return "more.decode";
  if (s.driving === "parked" && s.armed) return "security";
  return "home";
}
