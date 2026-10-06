// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { CatalogItem, CommandReply } from "../api/schemas";
import { useAction } from "../api/useAction";
import { actionLocked, actionVisible } from "../lib/catalog";
import { useApp } from "../state/app";
import { ActionButton } from "./ActionButton";
import { PlaceholderReadout } from "./PlaceholderReadout";
import { StatusTag } from "./StatusTag";

/** One catalog item on Outputs / Settings / a procedure: name, status (Experimental
 * only), K-line reference and its actions. A latched action (one with `stop`) gets a Stop
 * button next to it. An item with nothing to run or read is a placeholder. */
export function ItemCard({ item, disabled, onResult }: {
  item: CatalogItem; disabled?: boolean; onResult?: (r: CommandReply) => void;
}) {
  const { experimental } = useApp();
  const run = useAction();
  const actions = item.actions.filter((a) => actionVisible(a, experimental));
  if (!item.actions.length && item.status !== "verified") return <PlaceholderReadout item={item} />;
  return (
    <div className="card item" data-item={item.id}>
      <div className="row" style={{ gap: 8 }}>
        <span className="grow item-name">{item.name}</span>
        {experimental ? <StatusTag status={item.status} /> : null}
      </div>
      {item.ref ? <div className="small dis mono" style={{ marginTop: 2 }}>{item.ref}</div> : null}
      {item.note ? <div className="small muted pretty" style={{ marginTop: 2 }}>{item.note}</div> : null}
      {actions.length ? (
        <div className="actions">
          {actions.map((a) => (
            <div key={a.action} className="row wrap" style={{ gap: 8 }}>
              <ActionButton action={a} itemName={item.name} disabled={disabled} onResult={onResult} />
              {a.stop && !actionLocked(a) ? (
                <button className="btn" disabled={disabled} onClick={() => void run(a.stop!)}>Stop</button>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
