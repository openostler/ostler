// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { createContext, useContext } from "react";
import type { CommandReply, Snapshot } from "../api/schemas";
import type { Toast } from "../state/app";
import type { DrivingState } from "./landing";
import type { LayoutClass, Side } from "./layoutClass";
import type { RouteName } from "./routes";

/**
 * The typed shell context (app-model spec §9, seam 2): the services the shell gives every
 * destination, split from screen state (`useApp()` keeps the module data: snapshot, fields,
 * catalog). It is the shape `@ostler/app-sdk` grows from in phase UA (app-model spec §6):
 * layout class, driving state, vehicle, signals, actions, nav, session and toast.
 */
export type ShellSheet = "preferences" | "connection" | "faults";

export type ShellContext = {
  /** The layout class (UI spec §3.1) and the rail side (§3.3). */
  layout: LayoutClass;
  side: Side;
  headUnit: boolean;
  /** Parked / Idling / Moving from the server; "unknown" until U2 (shell/landing.ts). */
  driving: DrivingState;
  /** The active vehicle and the system holding the ECU session. */
  vehicle: { pack: string; name: string; system: string; systemName: string };
  /** The signals in view (live, or synthesised at the replay cursor). */
  signals: Snapshot["signals"];
  /** The one action path (seam 3): `request` is `useAction()`, which refuses in replay and
   * adds the trust flag; confirmations stay in components/confirm.ts. */
  actions: { request: (id: string, params?: Record<string, unknown>, opts?: { quiet?: boolean }) => Promise<CommandReply | null> };
  /** Navigation by route name (seam 6). `open("drive")` enters Drive mode. */
  nav: { route: RouteName; open: (route: RouteName) => void };
  /** Drive mode (§3.5): full screen over the shell, with the strip and a back target. */
  drive: { active: boolean; open: () => void; close: () => void };
  /** The shell's sheets (approval surfaces stay shell-drawn, app-model spec §2). */
  sheets: { open: (sheet: ShellSheet) => void };
  session: { admin: boolean; experimental: boolean; replaying: boolean; kiosk: boolean };
  toast: Toast;
  /** Locale-aware formatting through Intl (lib/units.ts). */
  format: { quantity: (v: number | null | undefined, unit: string, dec?: number) => string; clock: (d: Date) => string };
};

export const ShellCtx = createContext<ShellContext | null>(null);

export function useShell(): ShellContext {
  const ctx = useContext(ShellCtx);
  if (!ctx) throw new Error("useShell() outside <ShellCtx.Provider>");
  return ctx;
}
