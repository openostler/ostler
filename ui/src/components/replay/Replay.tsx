// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * The replay session header on the Analysis tab (spec §7): "‹ Sessions" (exit replay, back to
 * Logs), the inline name and description, when/where, Export and Delete. The analysis body
 * itself is `AnalysisView`.
 */
import { useState } from "react";
import { api, command } from "../../api/client";
import type { SessionData, SessionMeta } from "../../api/schemas";
import { useApp } from "../../state/app";
import { useReplay } from "../../state/replay";
import { confirmReady } from "../confirm";
import { InlineEdit } from "./InlineEdit";
import { formatDuration, startTime } from "./sessionFormat";

/** Server caps (spec §3 PATCH /sessions/<id>). */
const NAME_MAX = 80;
const DESC_MAX = 2000;
/** The word typed to confirm a delete (case-sensitive, spec §5). */
export const DELETE_WORD = "Delete";

/** "‹ Sessions": leave replay and return to the Logs browser. */
export function BackToSessions() {
  const { goTo } = useApp();
  const replay = useReplay();
  return <button className="rchip replay-back" onClick={() => { replay.exit(); goTo("logs"); }}>‹ Sessions</button>;
}

export function ReplayHeader({ meta, data, onDeleted }: { meta: SessionMeta; data: SessionData; onDeleted: () => void }) {
  const { snap, toast } = useApp();
  const date = new Date(meta.start_utc).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
  /** Name, description and Delete: never on a demo log or in public mode (spec §3, §5). */
  const canEdit = !meta.synthetic && !snap?.public;
  const place = meta.place?.label ?? null;
  const save = async (patch: { name?: string | null; description?: string | null }) => {
    try {
      const r = await api.updateSession(meta.id, patch);
      if (!r.ok) throw new Error(r.error ?? "could not save");
    } catch (e) {
      toast(`Not saved: ${(e as Error).message}`, true);
      throw e;
    }
  };
  return (
    <div className="replay-head">
      <BackToSessions />
      <div className="replay-title">
        <InlineEdit as="h2" className="replay-name" value={meta.name} placeholder="Untitled session" label="Session name"
          maxLength={NAME_MAX} readOnly={!canEdit} onSave={(v) => save({ name: v })} />
        <span className="muted small replay-when">
          {date} · {startTime(meta)} · {formatDuration(meta.duration_s)}
          {place ? <> · {place}</> : null}
          {meta.synthetic ? <span className="replay-chip-demo">demo</span> : null}
          {meta.recording ? <span className="replay-chip-live">recording</span> : null}
          {data.decimated ? <span title="Long session: each point keeps the min and max of its span"> · overview</span> : null}
        </span>
        <InlineEdit as="p" className="replay-desc small" value={meta.description} placeholder="Add a description" label="Description"
          multiline maxLength={DESC_MAX} readOnly={!canEdit} hideEmpty onSave={(v) => save({ description: v })} />
      </div>
      <SessionActions meta={meta} canDelete={canEdit && !meta.recording} onDeleted={onDeleted} />
    </div>
  );
}

function SessionActions({ meta, canDelete, onDeleted }: { meta: SessionMeta; canDelete: boolean; onDeleted: () => void }) {
  const { toast } = useApp();
  const [confirming, setConfirming] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const ready = confirmReady("typed", { ticked: [], typed, name: DELETE_WORD });

  const del = async () => {
    setBusy(true);
    try {
      const r = await command("delete_session", { id: meta.id });
      if (r.ok) {
        toast("session deleted");
        onDeleted();
      } else toast(String(r.error ?? "could not delete the session"), true);
    } catch (e) {
      toast((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="replay-actions">
      <details className="replay-menu">
        <summary className="rchip">Export</summary>
        <div className="replay-menu-body card">
          {(["csv", "vbo", "gpx"] as const).map((f) => (
            <a key={f} className="btn block" href={api.sessionExportUrl(meta.id, f)} download>{f.toUpperCase()}</a>
          ))}
        </div>
      </details>
      {canDelete && !confirming ? <button className="rchip replay-delete" onClick={() => setConfirming(true)}>Delete</button> : null}
      {canDelete && confirming ? (
        <div className="confirm card replay-confirm" role="group" aria-label="Confirm delete session">
          <label className="stack small" style={{ gap: 6 }}>
            <span>Deleting removes this session from the device. Type <b className="mono">{DELETE_WORD}</b> to confirm.</span>
            <input className="input mono" value={typed} autoComplete="off" autoCapitalize="off" spellCheck={false}
              aria-label={`Type ${DELETE_WORD} to confirm`} onChange={(e) => setTyped(e.target.value)} />
          </label>
          <div className="btn-row" style={{ marginTop: 10 }}>
            <button className="btn" onClick={() => { setConfirming(false); setTyped(""); }}>Cancel</button>
            <button className="btn danger" disabled={!ready || busy} onClick={() => void del()}>Delete session</button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
