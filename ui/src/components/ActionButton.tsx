import { useState } from "react";
import type { CatalogAction, CommandReply } from "../api/schemas";
import { useAction } from "../api/useAction";
import { actionLocked } from "../lib/catalog";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { confirmReady, SAFETY } from "./confirm";

/**
 * One registry action as a button, with the confirm the registry asks for:
 * none → runs on tap; preconditions → a checklist the user ticks; typed → type the item
 * name. Gated or planned → a lock, no button. Experimental actions exist only in
 * Experimental mode. In replay every action is a lock with the word "replay" (read-only).
 */
export function ActionButton({ action, itemName, disabled, onResult }: {
  action: CatalogAction;
  itemName: string;
  disabled?: boolean;
  onResult?: (r: CommandReply) => void;
}) {
  const { experimental } = useApp();
  const { active: replaying } = useReplay();
  const run = useAction();
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const conditions = action.preconditions.length ? action.preconditions : [SAFETY];
  const [ticked, setTicked] = useState<boolean[]>(() => conditions.map(() => false));
  const [typed, setTyped] = useState("");

  if (actionLocked(action)) {
    const why = action.safety === "gated" ? "Gated — never sent by this tool" : "Planned — not implemented yet";
    return (
      <span className="locked" title={why} aria-label={`${action.label}: ${why}`} data-action={action.action}>
        <span aria-hidden="true">🔒</span>{action.safety === "gated" ? "Gated" : "Planned"}
      </span>
    );
  }
  if (action.status !== "verified" && !experimental) return null;
  if (replaying) {
    return (
      <span className="locked replay-lock" title="Replay — read only" aria-label={`${action.label}: replay, read only`} data-action={action.action}>
        <span aria-hidden="true">🔒</span>{action.label} · replay
      </span>
    );
  }

  const fire = async () => {
    setBusy(true);
    setConfirming(false);
    setTicked(conditions.map(() => false));
    setTyped("");
    const r = await run(action.action);
    setBusy(false);
    if (r?.ok) onResult?.(r);
  };
  const tap = () => (action.confirm === "none" ? void fire() : setConfirming(true));
  const danger = action.safety === "actuator" || action.safety === "service";
  const ready = confirmReady(action.confirm, { ticked, typed, name: itemName });

  return (
    <div className="action" data-action={action.action}>
      {!confirming ? (
        <button className={`btn ${danger ? "danger" : ""}`} disabled={disabled || busy} onClick={tap}>
          {busy ? `${action.label}…` : action.label}
        </button>
      ) : (
        <div className="confirm card" role="group" aria-label={`Confirm ${action.label}`}>
          {action.confirm === "typed" ? (
            <label className="stack small" style={{ gap: 6 }}>
              <span>Type <b>{itemName}</b> to confirm.</span>
              <input className="input" value={typed} aria-label={`Type ${itemName} to confirm`}
                onChange={(e) => setTyped(e.target.value)} />
            </label>
          ) : (
            <div className="stack small" style={{ gap: 6 }}>
              <span className="kicker">Before you run it</span>
              {conditions.map((c, i) => (
                <label key={c} className="row check" style={{ gap: 8 }}>
                  <input type="checkbox" checked={ticked[i] ?? false}
                    onChange={(e) => setTicked((t) => t.map((x, j) => (j === i ? e.target.checked : x)))} />
                  <span className="pretty">{c}</span>
                </label>
              ))}
            </div>
          )}
          <div className="btn-row" style={{ marginTop: 10 }}>
            <button className="btn" onClick={() => setConfirming(false)}>Cancel</button>
            <button className={`btn ${danger ? "danger" : "accent"}`} disabled={!ready || disabled} onClick={() => void fire()}>
              {action.label}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
