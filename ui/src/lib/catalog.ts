// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The /catalog rules the UI applies (ADR-0008, specs/2026-10-05-ui-overhaul-design.md
 * "Modes"): what is visible in Stable vs Experimental, page/group filtering and coverage
 * helpers. Pure functions, unit-tested; the server derives every status.
 */
import type {
  Catalog,
  CatalogAction,
  CatalogCoverage,
  CatalogGroup,
  CatalogItem,
  CatalogModule,
  CatalogPage,
} from "../api/schemas";

export const STATUSES = ["verified", "candidate", "sniff", "untranscribed"] as const;
export type Status = (typeof STATUSES)[number];

export const STATUS_WORD: Record<Status, string> = {
  verified: "Verified",
  candidate: "Candidate",
  sniff: "Sniff target",
  untranscribed: "Not transcribed",
};

/** Shown on a page with nothing verified while in Stable mode (spec, Modes table). */
export const STABLE_EMPTY = "Nothing verified here yet — switch to Experimental to see what's in progress.";

export const EMPTY_COVERAGE: CatalogCoverage = { verified: 0, candidate: 0, sniff: 0, untranscribed: 0, total: 0 };

/** Stable shows verified, non-gated items only; Experimental shows all four statuses
 * (gated items stay visible but locked, see actionLocked). */
export function visible(item: CatalogItem, experimental: boolean): boolean {
  if (experimental) return true;
  return item.status === "verified" && item.safety !== "gated";
}

/** A gated or planned action is never runnable: lock icon, no button. */
export function actionLocked(a: CatalogAction): boolean {
  return a.safety === "gated" || a.status === "planned";
}

/** Stable: only verified, runnable actions. Experimental: all (locked ones render a lock). */
export function actionVisible(a: CatalogAction, experimental: boolean): boolean {
  if (experimental) return true;
  return a.status === "verified" && !actionLocked(a);
}

/** An item with no live value: renders as a PlaceholderReadout (never a value). */
export function isPlaceholder(item: CatalogItem): boolean {
  return item.placeholder || item.status === "untranscribed" || item.status === "sniff";
}

export function pageOf(catalog: Catalog | null | undefined, id: string): CatalogPage | undefined {
  return catalog?.pages.find((p) => p.id === id);
}

export type VisibleGroup = { group: CatalogGroup; items: CatalogItem[] };

/** The page's groups with their visible items; a group left empty is dropped. */
export function visibleGroups(page: CatalogPage | undefined, experimental: boolean): VisibleGroup[] {
  if (!page) return [];
  return page.groups
    .map((group) => ({ group, items: group.items.filter((i) => visible(i, experimental)) }))
    .filter((g) => g.items.length > 0);
}

export type GroupNode = VisibleGroup & { children: VisibleGroup[] };

/** Utilities sub-menus: top-level groups with their direct children (two levels at most;
 * a deeper or orphaned group is shown at the top level). Empty branches are dropped. */
export function groupTree(page: CatalogPage | undefined, experimental: boolean): GroupNode[] {
  if (!page) return [];
  const ids = new Set(page.groups.map((g) => g.id));
  const byId = new Map(page.groups.map((g) => [g.id, g]));
  const isTop = (g: CatalogGroup) => {
    if (!g.parent || !ids.has(g.parent)) return true;
    const p = byId.get(g.parent);
    return !!p?.parent && ids.has(p.parent); // a third level is flattened to the top
  };
  const vis = (group: CatalogGroup): VisibleGroup => ({ group, items: group.items.filter((i) => visible(i, experimental)) });
  return page.groups
    .filter(isTop)
    .map((g) => ({
      ...vis(g),
      children: page.groups.filter((c) => c.parent === g.id && !isTop(c)).map(vis).filter((c) => c.items.length > 0),
    }))
    .filter((n) => n.items.length > 0 || n.children.length > 0);
}

/** Count statuses over a list of items. */
export function coverageOf(items: { status: string }[]): CatalogCoverage {
  const c = { ...EMPTY_COVERAGE };
  for (const i of items) {
    if ((STATUSES as readonly string[]).includes(i.status)) c[i.status as Status] += 1;
    c.total += 1;
  }
  return c;
}

/** Verified share in whole percent (0 for an empty page). */
export function coveragePct(c: CatalogCoverage): number {
  return c.total ? Math.round((100 * c.verified) / c.total) : 0;
}

/** Header dropdown: Stable lists modules with ≥ 1 verified item (plus the current one,
 * so the selection never vanishes); Experimental lists all. */
export function modulesFor(mods: CatalogModule[], experimental: boolean, current?: string): CatalogModule[] {
  if (experimental) return mods;
  return mods.filter((m) => m.coverage.verified > 0 || m.module === current);
}

/** Every visible item of a page (flattened). */
export function pageItems(page: CatalogPage | undefined, experimental: boolean): CatalogItem[] {
  return visibleGroups(page, experimental).flatMap((g) => g.items);
}

/** The identity returned by read_identity as display rows. Only the masked VIN is ever
 * shown: any other key naming a VIN is dropped. */
export function identityRows(identity: unknown): [string, string][] {
  if (!identity || typeof identity !== "object") return [];
  return Object.entries(identity as Record<string, unknown>)
    .filter(([k, v]) => v != null && v !== "" && (!/vin/i.test(k) || k === "vin_masked"))
    .map(([k, v]) => [k, typeof v === "object" ? JSON.stringify(v) : String(v)]);
}
