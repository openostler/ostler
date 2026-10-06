// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback } from "react";
import { command } from "../api/client";
import type { CatalogModule } from "../api/schemas";
import { useCatalogModules } from "../api/useCatalog";
import { canonicalModule, moduleName, moduleNames } from "../layout";
import { modulesFor } from "../lib/catalog";
import { useApp } from "./app";

export type SystemOption = { id: string; label: string; coverage?: CatalogModule["coverage"] };

/**
 * The vehicle's systems (UI spec §4.2) for Diagnose: the list pane, the compact switcher and
 * the identity bar share it. Stable lists only systems with something verified (ADR-0008);
 * Experimental lists every one. `select` switches the system holding the ECU session
 * (`select_module`, a server-state command; K-line carries one session at a time), asking
 * first while a recording is on. `multi` is the collapse rule: with one system there is no
 * system level.
 */
export function useSystems() {
  const { snap, module, experimental, toast } = useApp();
  // ids are canonical; an alias from an older server maps onto the pack id
  const mods = useCatalogModules(module)?.map((m) => ({ ...m, module: canonicalModule(m.module) }));
  const recording = !!snap?.logging?.recording;

  const options: SystemOption[] = mods
    ? modulesFor(mods, experimental, module).map((m) => ({ id: m.module, label: m.name, coverage: m.coverage }))
    : moduleNames().map(([id, label]) => ({ id, label }));
  if (!options.some((o) => o.id === module)) options.unshift({ id: module, label: moduleName(module) });
  const current = options.find((o) => o.id === module) ?? { id: module, label: moduleName(module) };

  const select = useCallback(async (id: string) => {
    if (id === module) return;
    if (recording && !window.confirm(
      `Recording is on.\nSwitching to ${moduleName(id)} rotates the log to a new file — the current ` +
      `module's data pauses while ${moduleName(id)} is active (the K-line carries one session at a time).\n\nSwitch anyway?`,
    )) return;
    try {
      const r = await command("select_module", { module: id });
      if (!r.ok) toast(r.error ?? "could not switch module", true);
    } catch (e) {
      toast((e as Error).message, true);
    }
  }, [module, recording, toast]);

  return { options, current, select, multi: options.length > 1, experimental };
}
