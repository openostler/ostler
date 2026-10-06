// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The automatic flags of the open session (specs/2026-10-05-replay-notes-capture-design.md §8):
 * `/fields` and `/faults` for every module the session touched (cached per module for the page's
 * life, fail soft), then `detectFlags` over the loaded data, then the flag manager's options.
 */
import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { FaultMeaning, Field, SessionData } from "../api/schemas";
import { detectFlags, useFlagOptions, visibleFlags, type Flag } from "../lib/flags";
import { faultLookup } from "../lib/format";

type ModuleMeta = { fields: Field[]; faults: FaultMeaning[] };

const cache = new Map<string, Promise<ModuleMeta>>();

/** A module's field metadata and fault meanings (never rejects: a failed fetch → empty). */
export function moduleMeta(module: string): Promise<ModuleMeta> {
  let p = cache.get(module);
  if (!p) {
    p = Promise.all([
      api.fields(module).then((r) => r.fields, () => [] as Field[]),
      api.faults(module).then((r) => r.faults, () => [] as FaultMeaning[]),
    ]).then(([fields, faults]) => ({ fields, faults }));
    cache.set(module, p);
  }
  return p;
}

/** Test helper: forget the per-module cache. */
export function resetFlagMetaCache(): void {
  cache.clear();
}

export interface SessionFlags {
  /** Every detected flag (before the flag manager's options). */
  all: Flag[];
  /** The flags the options let through (muted sensors and switched-off kinds removed). */
  visible: Flag[];
  /** Visible flags per kind. */
  counts: { range: number; faults: number };
}

const NO_META: { fields: Record<string, Field>; faults: FaultMeaning[] } = { fields: {}, faults: [] };

export function useSessionFlags(data: SessionData | undefined, modules: readonly string[]): SessionFlags {
  const key = [...new Set(modules)].sort().join("\u0000");
  const [meta, setMeta] = useState<{ key: string; fields: Record<string, Field>; faults: FaultMeaning[] } | null>(null);

  useEffect(() => {
    let alive = true;
    const mods = key ? key.split("\u0000") : [];
    Promise.all(mods.map(moduleMeta)).then((all) => {
      if (!alive) return;
      const fields: Record<string, Field> = {};
      const faults: FaultMeaning[] = [];
      for (const m of all) {
        for (const f of m.fields) fields[f.name] ??= f;
        faults.push(...m.faults);
      }
      setMeta({ key, fields, faults });
    });
    return () => { alive = false; };
  }, [key]);

  const cur = meta && meta.key === key ? meta : NO_META;
  const faultText = useMemo(() => {
    const look = faultLookup(cur.faults);
    return (raw: string): string | undefined => {
      const m = look(raw);
      if (!m) return undefined;
      return [m.pcode, m.description || m.name].filter(Boolean).join(" ") || undefined;
    };
  }, [cur.faults]);

  const options = useFlagOptions();
  const all = useMemo(() => (data ? detectFlags(data, cur.fields, faultText) : []), [data, cur.fields, faultText]);
  // muted sensors are left out before detection too, so the flood cap does not count them
  const muted = options.muted;
  const unmuted = useMemo(() => {
    if (!data || !muted.length) return all;
    const fields = Object.fromEntries(Object.entries(cur.fields).filter(([n]) => !muted.includes(n)));
    return detectFlags(data, fields, faultText);
  }, [all, data, cur.fields, faultText, muted]);
  const visible = useMemo(() => visibleFlags(unmuted, options), [unmuted, options]);
  const counts = useMemo(() => ({
    range: visible.filter((f) => f.kind === "range").reduce((n, f) => n + (f.folded ?? 1), 0),
    faults: visible.filter((f) => f.kind === "fault").length,
  }), [visible]);
  return { all, visible, counts };
}
