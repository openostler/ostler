// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useState } from "react";
import { api } from "./client";
import type { Catalog, CatalogModule } from "./schemas";

/**
 * The /catalog page structure for the current module (ADR-0008), refetched whenever the
 * module changes. A catalog for another module is never returned while the new one loads.
 */
export function useCatalog(module: string) {
  const [state, setState] = useState<{ key: string; catalog: Catalog | null; error: string | null }>({
    key: "", catalog: null, error: null,
  });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    api.catalog(module).then(
      (catalog) => alive && setState({ key: module, catalog, error: null }),
      (e: Error) => alive && setState({ key: module, catalog: null, error: e.message }),
    );
    return () => { alive = false; };
  }, [module, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  const current = state.key === module;
  return { catalog: current ? state.catalog : null, error: current ? state.error : null, reload };
}

/** Diagnose's system list with coverage (GET /catalog); null until loaded or
 * when the server has no /catalog (then the caller falls back to the known module names). */
export function useCatalogModules(refreshKey: string) {
  const [mods, setMods] = useState<CatalogModule[] | null>(null);
  useEffect(() => {
    let alive = true;
    api.catalogModules().then((r) => alive && setMods(r.modules), () => undefined);
    return () => { alive = false; };
  }, [refreshKey]);
  return mods;
}
