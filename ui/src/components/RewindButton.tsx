// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { SessionMeta } from "../api/schemas";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";

/** Sessions fetched to find the newest finished one. */
const LOOKUP = 5;

/** The newest session that is not still being recorded (the list is newest first). */
const newestFinished = (sessions: SessionMeta[]) => sessions.find((s) => !s.recording) ?? null;

/**
 * ⏪ Rewind (spec §7, §8), in the Logs destination (the header before U1, UI spec §3.2). While the Pi is recording it opens
 * the drive in progress at its newest sample, paused, and follows it as it grows; otherwise the
 * newest finished session at its last sample, paused. Then it opens Analysis (route "logs.analysis"). Hidden in replay (Exit to live takes its place);
 * disabled ("No logs yet") when there are no sessions at all. The list is fetched lazily on
 * mount and again on each tap.
 */
export function RewindButton() {
  const { snap, toast, goTo } = useApp();
  const replay = useReplay();
  const recording = snap?.recording?.session ?? null;
  /** null: not known yet (or the list failed to load) → enabled. */
  const [hasLogs, setHasLogs] = useState<boolean | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (replay.active) return;
    let alive = true;
    api.sessions({ limit: LOOKUP }).then(
      (r) => alive && setHasLogs(r.sessions.length > 0),
      () => undefined,
    );
    return () => { alive = false; };
  }, [replay.active]);

  const { enter } = replay;
  const rewind = useCallback(async () => {
    if (busy) return;
    if (recording) {
      enter(recording, { at: "end", follow: true });
      goTo("logs.analysis");
      return;
    }
    setBusy(true);
    try {
      const r = await api.sessions({ limit: LOOKUP });
      setHasLogs(r.sessions.length > 0);
      const s = newestFinished(r.sessions) ?? r.sessions[0] ?? null;
      if (!s) { toast("No logs yet", true); return; }
      enter(s.id, { at: "end" });
      goTo("logs.analysis");
    } catch (e) {
      toast(`Could not load the logs: ${(e as Error).message}`, true);
    } finally {
      setBusy(false);
    }
  }, [busy, recording, enter, goTo, toast]);

  if (replay.active) return null;
  const disabled = !recording && hasLogs === false;
  return (
    <button
      className="btn rewind-btn"
      aria-label="Rewind"
      title={disabled ? "No logs yet" : recording ? "Rewind to the latest sample" : "Open the last drive at its end"}
      disabled={disabled || busy}
      onClick={rewind}
    >
      <span aria-hidden="true">⏪</span>
      <span aria-hidden="true">Rewind</span>
    </button>
  );
}
