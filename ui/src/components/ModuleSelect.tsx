// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { command } from "../api/client";
import { useCatalogModules } from "../api/useCatalog";
import { canonicalModule, moduleName, moduleNames } from "../layout";
import { coveragePct, modulesFor } from "../lib/catalog";
import { useApp } from "../state/app";

/** Header module picker: one bordered control (muted "Module" label, the module name, ▾)
 * over a native <select>, plus — Experimental only — an "NN% mapped" pill (verified over
 * total, from GET /catalog; "NN%" alone on narrow phones). Switching sends select_module and keeps the current tab.
 * Stable lists only modules with something verified. */
export function ModuleSelect() {
  const { snap, module, experimental, toast } = useApp();
  // ids are canonical; an alias from an older server maps onto the pack id
  const mods = useCatalogModules(module)?.map((m) => ({ ...m, module: canonicalModule(m.module) }));
  const recording = !!snap?.logging?.recording;

  const options: { id: string; label: string }[] = mods
    ? modulesFor(mods, experimental, module).map((m) => ({ id: m.module, label: m.name }))
    : moduleNames().map(([id, label]) => ({ id, label }));
  if (!options.some((o) => o.id === module)) options.unshift({ id: module, label: moduleName(module) });
  const current = options.find((o) => o.id === module)?.label ?? moduleName(module);
  const cov = experimental ? mods?.find((m) => m.module === module)?.coverage : undefined;

  const select = async (id: string) => {
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
  };

  return (
    <div className="hmod">
      <div className="modctl">
        <span className="modctl-txt" aria-hidden="true">
          <span className="modctl-k">Module</span>
          <span className="modctl-v">{current}</span>
        </span>
        <span className="modctl-chev" aria-hidden="true">▾</span>
        <select className="modsel" aria-label="Module" value={module} onChange={(e) => void select(e.target.value)}>
          {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
        </select>
      </div>
      {cov ? (
        <span className="mappct" title={`${cov.verified} of ${cov.total} items verified`}>
          {coveragePct(cov)}%<span className="mappct-w"> mapped</span>
        </span>
      ) : null}
    </div>
  );
}
