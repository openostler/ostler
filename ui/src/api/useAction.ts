import { useCallback } from "react";
import { useApp } from "../state/app";
import { command } from "./client";
import type { CommandReply } from "./schemas";

/**
 * Send a module action over /command. In Experimental mode every module action carries
 * `params.trust = "experimental"` so the server may run experimental actions (it refuses
 * them otherwise, ADR-0008). A refusal (HTTP 400 {ok:false, error}) or a transport error
 * is shown as a toast; the reply (or null on transport error) is returned.
 */
export function useAction() {
  const { experimental, toast } = useApp();
  return useCallback(
    async (action: string, params?: Record<string, unknown>, opts: { quiet?: boolean } = {}): Promise<CommandReply | null> => {
      const p = experimental ? { ...params, trust: "experimental" } : params;
      try {
        const r = await command(action, p);
        if (!r.ok) toast(r.error ?? `${action} refused`, true);
        else if (!opts.quiet) toast(r.message ?? `${action} ok`);
        return r;
      } catch (e) {
        toast((e as Error).message, true);
        return null;
      }
    },
    [experimental, toast],
  );
}
