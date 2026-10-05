/**
 * Layout accessors — the screen layout comes from the active vehicle pack (GET /pack →
 * `layout`), never from this file. Signal labels, groups and descriptions come from the
 * signal store via /fields; the pack only decides what goes where on screen (Drive views,
 * the body view, the raw-LID presets, module notices). Outputs, Settings and Utilities come
 * from /catalog. Every accessor works before the pack loads (raw ids, empty layout).
 */
import type { BodyGroup, BodyRow, DriveTile, DriveView, PackLayout } from "./api/schemas";
import { getPack } from "./pack/store";

export type { BodyGroup, BodyRow, DriveTile, DriveView };

const layout = (): PackLayout => getPack()?.layout ?? {};

/** A module id as the pack knows it: a legacy alias maps to its canonical id. */
export function canonicalModule(m: string): string {
  const pack = getPack();
  if (!pack) return m;
  return pack.aliases[m] ?? m;
}

/** The display name of a module ("ABBR (plain words)"), else its id. */
export function moduleName(m: string): string {
  const id = canonicalModule(m);
  return getPack()?.modules.find((x) => x.id === id)?.name ?? m;
}

/** Every module of the pack in pack order, as [id, name]. */
export function moduleNames(): [string, string][] {
  return (getPack()?.modules ?? []).map((m) => [m.id, m.name]);
}

/** Display order of signal groups (a group not listed here sorts after these). */
export function groupOrder(): string[] {
  return layout().group_order ?? [];
}

/** The module's Drive view, or null when the pack has none for it. */
export function driveView(m: string): DriveView | null {
  return layout().drive?.[canonicalModule(m)] ?? null;
}

/** A Drive tile's displayed value (`scale` converts units, e.g. ÷10 for L/mil). */
export function tileConv(t: DriveTile): ((v: number) => number) | undefined {
  const k = t.scale;
  return k === undefined || k === 1 ? undefined : (v: number) => v * k;
}

/** The body view: named signal roles (for the vehicle diagram) and the readout groups. */
export function bodyLayout(): { signals: Record<string, string>; groups: BodyGroup[] } {
  return layout().body ?? { signals: {}, groups: [] };
}

/** Utilities → raw LID dump: a sensible default request for the module. */
export function utilLids(m: string): { example: string; note: string } {
  return layout().util_lids?.[canonicalModule(m)] ?? { example: "", note: "" };
}

/** Module notices (e.g. a module that only talks while stationary). */
export function moduleNotices(m: string): { record_confirm?: string; inputs_banner?: string } {
  return layout().notices?.[canonicalModule(m)] ?? {};
}

/** Replay channel picker: extra raw-group → category entries from the pack. */
export function groupCategories(): Record<string, string> {
  return layout().replay?.group_categories ?? {};
}

/** The pack's default module ("" before load). */
export function defaultModule(): string {
  return getPack()?.default_module ?? "";
}
