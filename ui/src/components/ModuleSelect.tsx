import { command } from "../api/client";
import { useCatalogModules } from "../api/useCatalog";
import { MODULE_NAME, moduleName } from "../layout";
import { coveragePct, modulesFor } from "../lib/catalog";
import { useApp } from "../state/app";

/** Header module picker: name and verified coverage % (from GET /catalog). Switching
 * sends select_module and keeps the current tab. Stable lists only modules with
 * something verified. */
export function ModuleSelect() {
  const { snap, module, experimental, toast } = useApp();
  const mods = useCatalogModules(module);
  const recording = !!snap?.logging?.recording;

  const options: { id: string; label: string }[] = mods
    ? modulesFor(mods, experimental, module).map((m) => ({
      id: m.module,
      label: experimental ? `${m.name} · ${coveragePct(m.coverage)}%` : m.name,
    }))
    : Object.keys(MODULE_NAME).map((id) => ({ id, label: moduleName(id) }));
  if (!options.some((o) => o.id === module)) options.unshift({ id: module, label: moduleName(module) });

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
    <select className="modsel" aria-label="Module" value={module} onChange={(e) => void select(e.target.value)}>
      {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
    </select>
  );
}
