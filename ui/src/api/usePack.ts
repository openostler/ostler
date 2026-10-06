// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useState } from "react";
import { getPack, setPack, usePack } from "../pack/store";
import { api } from "./client";

/**
 * Load GET /pack once at boot into the pack store. The pack is local and fast, so App
 * gates its first render on it (no D2 labels flash before it loads). `retry` re-fetches
 * after a failure. An already-installed pack (tests seed one) is used as is.
 */
export function useLoadPack(): { pack: ReturnType<typeof getPack>; error: string | null; retry: () => void } {
  const pack = usePack();
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (getPack()) return;
    let alive = true;
    api.pack().then(
      (p) => { if (alive) { setError(null); setPack(p); } },
      (e: Error) => { if (alive) setError(e.message); },
    );
    return () => { alive = false; };
  }, [attempt]);

  const retry = useCallback(() => {
    setError(null);
    setAttempt((n) => n + 1);
  }, []);
  return { pack, error, retry };
}
export { usePack } from "../pack/store";
