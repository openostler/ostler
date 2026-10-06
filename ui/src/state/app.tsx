// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { createContext, useContext } from "react";
import type { Catalog, Community, FaultMeaning, Field, Snapshot } from "../api/schemas";
import type { LiveState } from "./live";
import type { Prefs } from "./prefs";

export type Toast = (msg: string, bad?: boolean) => void;

/** Everything a screen needs, provided once by <App>. */
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
  /** Switch the active tab by screen id (registry.ts: "drive", "logs", "analysis", …).
   * Stable identity; an unknown id falls back to the first screen. */
  goTo: (tab: string) => void;
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
