// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Vehicle view registry (platform). A pack's UI code registers the components its layout
 * names by `kind` (layout.drive[module].kind); Drive looks them up for the active pack.
 * "tiles" is generic and never registered. Composition root: main.tsx imports each pack.
 */
import type { ComponentType } from "react";
import type { Field, SignalValue } from "../api/schemas";

export type VehicleViewProps = { signals: Record<string, SignalValue>; fields: Record<string, Field> };
export type VehicleView = ComponentType<VehicleViewProps>;

const views = new Map<string, Record<string, VehicleView>>();

/** Register (or extend) the views of pack `packId` by kind. */
export function registerViews(packId: string, byKind: Record<string, VehicleView>): void {
  views.set(packId, { ...views.get(packId), ...byKind });
}

/** The view of `kind` for pack `packId`, or undefined when none is registered. */
export function getView(packId: string | undefined, kind: string): VehicleView | undefined {
  return packId ? views.get(packId)?.[kind] : undefined;
}
