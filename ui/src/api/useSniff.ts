import { useEffect, useRef, useState } from "react";
import { api } from "./client";
import type { SniffResponse } from "./schemas";

export type SniffState = {
  data: SniffResponse | null;
  /** LIDs whose read count rose since the previous poll — the tool is polling them now. */
  active: Set<string>;
  /** Bus lines per second since the previous poll. */
  fps: number;
  /** False when the server answered but has no sniffer configured (no --sniff/--replay). */
  configured: boolean;
  error: string | null;
};

/** Poll /sniff (the passive ESP32 tap on the reference tool's traffic) while mounted.
 * `onPoll` runs after every successful poll (outside render) with the new state. */
export function useSniff(
  module: string | undefined,
  intervalMs = 1000,
  onPoll?: (s: SniffState) => void,
): SniffState {
  const [state, setState] = useState<SniffState>({ data: null, active: new Set(), fps: 0, configured: true, error: null });
  const prev = useRef<{ counts: Record<string, number>; lines: number | null; t: number }>({ counts: {}, lines: null, t: 0 });
  const onPollRef = useRef(onPoll);
  useEffect(() => {
    onPollRef.current = onPoll;
  });

  useEffect(() => {
    prev.current = { counts: {}, lines: null, t: 0 };
    let alive = true;
    const poll = async () => {
      try {
        const d = await api.sniff(module);
        if (!alive) return;
        const now = performance.now();
        const p = prev.current;
        const active = new Set<string>();
        const counts: Record<string, number> = {};
        for (const l of d.lids) {
          const before = p.counts[l.lid];
          if (before != null && l.count > before) active.add(l.lid);
          counts[l.lid] = l.count;
        }
        const lines = d.lines ?? 0;
        const dt = p.t ? (now - p.t) / 1000 : 0;
        const fps = p.lines != null && dt > 0 ? Math.max(0, Math.round((lines - p.lines) / dt)) : 0;
        prev.current = { counts, lines, t: now };
        const next = { data: d, active, fps, configured: d.status != null, error: null };
        setState(next);
        onPollRef.current?.(next);
      } catch (e) {
        if (alive) setState((s) => ({ ...s, error: (e as Error).message }));
      }
    };
    void poll();
    const id = window.setInterval(poll, intervalMs);
    return () => {
      alive = false;
      window.clearInterval(id);
    };
  }, [module, intervalMs]);

  return state;
}
