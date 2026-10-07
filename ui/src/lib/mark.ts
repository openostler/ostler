// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { api } from "../api/client";
import type { Note, Snapshot } from "../api/schemas";
import { isPaused } from "../components/replay/sessionFormat";

/** Save a live `mark` at once and say so (the strip's Mark and the Drive menu's Mark row,
 * shell input spec §6). The strip's Mark then asks "What happened?"; the Drive menu's does not,
 * as there is no text entry while Moving (UI spec §3.5). */
export async function saveLiveMark(toast: (m: string, bad?: boolean) => void): Promise<{ note: Note | null; session: string | null }> {
  try {
    const r = await api.liveNote({ kind: "mark" });
    if (r.note) {
      toast("Marked");
      return { note: r.note, session: r.session ?? null };
    }
    toast(r.error ?? "Could not save the mark", true);
  } catch {
    toast("Could not save the mark — it will be saved with the note", true);
  }
  return { note: null, session: null };
}

/** Whether a live mark can be taken now (a recording that is not paused, not in replay). */
export const canLiveMark = (snap: Snapshot | null, replaying: boolean): boolean =>
  !replaying && !!snap?.recording?.session && !isPaused(snap.recording);
