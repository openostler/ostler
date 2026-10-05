/**
 * The active vehicle pack (GET /pack), held once for the whole app. App loads it at boot
 * (api/usePack.ts) and gates rendering on it; everything else reads it through `getPack()`
 * (plain functions, e.g. layout.ts accessors) or `usePack()` (components that should
 * re-render if it changes). Platform code never names a vehicle — it asks the pack.
 */
import { useSyncExternalStore } from "react";
import type { Pack } from "../api/schemas";

let current: Pack | null = null;
const listeners = new Set<() => void>();

/** Install the pack (null clears it, e.g. a test resetting the store). */
export function setPack(pack: Pack | null): void {
  current = pack;
  for (const l of listeners) l();
}

/** The loaded pack, or null before /pack has answered. */
export function getPack(): Pack | null {
  return current;
}

function subscribe(l: () => void): () => void {
  listeners.add(l);
  return () => {
    listeners.delete(l);
  };
}

/** The loaded pack as React state (re-renders when it is set). */
export function usePack(): Pack | null {
  return useSyncExternalStore(subscribe, getPack, getPack);
}
