// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { lazy, type ComponentType, type LazyExoticComponent } from "react";
import type { SymbolName } from "../icons/Icon";
import type { DestinationId, RouteName } from "./routes";

/**
 * The destination registry (app-model spec §9, seam 1), shaped like an app manifest's
 * `contributes.slots` entry so core apps can move behind manifests in phase UA without
 * touching the shell: `slot`, `order`, `requires` and `trust` decide where and whether an
 * entry shows; `component` is a lazy chunk (seam 4). It replaces the old tab list.
 */
export type Requires = {
  /** Capability-manifest devices that must be present (UI spec §6: no device, no chrome). */
  devices?: { kind: string }[];
};

export type DestinationEntry = {
  id: DestinationId;
  slot: `destination:${DestinationId}`;
  order: number;
  label: string;
  icon: SymbolName;
  /** The route the nav item opens. */
  route: RouteName;
  requires?: Requires;
  trust: "core" | "first_party" | "community";
  component: LazyExoticComponent<ComponentType>;
};

/** What the shell can match `requires` against. U1 has no capability manifest yet (U3, U5),
 * so the device list is empty and device-gated entries stay hidden. */
export type Capabilities = { devices: { kind: string }[] };

export const DESTINATIONS: DestinationEntry[] = [
  {
    id: "home", slot: "destination:home", order: 10, label: "Home", icon: "home", route: "home", trust: "core",
    component: lazy(() => import("../destinations/Home").then((m) => ({ default: m.Home }))),
  },
  {
    id: "diagnose", slot: "destination:diagnose", order: 20, label: "Diagnose", icon: "stethoscope", route: "diagnose",
    trust: "core", component: lazy(() => import("../destinations/Diagnose").then((m) => ({ default: m.Diagnose }))),
  },
  {
    id: "logs", slot: "destination:logs", order: 30, label: "Logs", icon: "history", route: "logs", trust: "core",
    component: lazy(() => import("../destinations/LogsDestination").then((m) => ({ default: m.LogsDestination }))),
  },
  {
    // Present with any node (§3.4); it fills from the node's capability manifest in U5.
    id: "security", slot: "destination:security", order: 40, label: "Security", icon: "shield", route: "security",
    requires: { devices: [{ kind: "node" }] }, trust: "core",
    component: lazy(() => import("../destinations/Security").then((m) => ({ default: m.Security }))),
  },
  {
    id: "more", slot: "destination:more", order: 50, label: "More", icon: "more_horiz", route: "more", trust: "core",
    component: lazy(() => import("../destinations/More").then((m) => ({ default: m.More }))),
  },
];

/** Five destinations at most (UI spec §3.4, a hard cap). */
export const MAX_DESTINATIONS = 5;

/** Whether an entry's requirements hold. */
export function meets(req: Requires | undefined, caps: Capabilities): boolean {
  return (req?.devices ?? []).every((d) => caps.devices.some((c) => c.kind === d.kind));
}

/** The entries to show, in order, capped at five. */
export function destinationsFor(caps: Capabilities, entries: DestinationEntry[] = DESTINATIONS): DestinationEntry[] {
  return entries
    .filter((e) => e.slot === `destination:${e.id}` && meets(e.requires, caps))
    .sort((a, b) => a.order - b.order)
    .slice(0, MAX_DESTINATIONS);
}
