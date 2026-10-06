// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { createContext, useContext } from "react";
import type { Catalog, Community, FaultMeaning, Field, Snapshot } from "../api/schemas";
import type { RouteName } from "../shell/routes";
import type { LiveState } from "./live";
import type { Prefs } from "./prefs";

export type Toast = (msg: string, bad?: boolean) => void;

/** The screen state every screen reads, provided once by <App>. Shell services (layout,
 * driving state, nav, sheets) are in `useShell()` (shell/context.tsx); `goTo` and `toast`
 * stay here as the same functions so today's screens keep working. */
export type AppContext = {
  snap: Snapshot | null;
  live: LiveState;
  /** False while the dashboard's own SSE stream is down (values are then stale). */
  linkUp: boolean;
  module: string;
  /** /catalog for the active module (null while loading or unavailable). */
  catalog: Catalog | null;
  /** Field metadata for the active module, by signal name (from /fields). */
  fields: Record<string, Field>;
  /** Look up a fault code's meaning (from /faults) by the decoder's raw string. */
  faultMeaning: (raw: string) => FaultMeaning | undefined;
  refresh: () => void;
  prefs: Prefs;
  setPrefs: (patch: Partial<Prefs>) => void;
  experimental: boolean;
  admin: boolean;
  community: Community | null;
  reloadCommunity: () => void;
  /** Navigate by route name (shell/routes.ts: "diagnose.faults", "logs.analysis", …; "drive"
   * opens Drive mode). Stable identity. The same function as `useShell().nav.open`. */
  goTo: (route: RouteName) => void;
  toast: Toast;
  ackedFaults: Set<string>;
  showFaultSheet: (faults: string[]) => void;
  /** Open the ConnectionSheet (from the pill, or a "not connected" gate). */
  openConnection: () => void;
};

export const AppCtx = createContext<AppContext | null>(null);

export function useApp(): AppContext {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp() outside <AppCtx.Provider>");
  return ctx;
}
