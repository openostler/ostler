import { createContext, useContext } from "react";
import type { Community, FaultMeaning, Field, Snapshot } from "../api/schemas";
import type { LiveState } from "./live";
import type { Prefs } from "./prefs";

export type Toast = (msg: string, bad?: boolean) => void;

/** Everything a screen needs, provided once by <App>. */
export type AppContext = {
  snap: Snapshot | null;
  live: LiveState;
  module: string;
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
  goTo: (tab: string) => void;
  toast: Toast;
  ackedFaults: Set<string>;
  showFaultSheet: (faults: string[]) => void;
};

export const AppCtx = createContext<AppContext | null>(null);

export function useApp(): AppContext {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp() outside <AppCtx.Provider>");
  return ctx;
}
