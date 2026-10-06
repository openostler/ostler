// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { VisibleGroup } from "../lib/catalog";
import { useApp } from "../state/app";
import { ItemCard } from "./ItemCard";
import { Sheet } from "./Sheet";

/** A Utilities procedure (a catalog group and its sub-groups) in a bottom sheet: its
 * steps and actions, with Stop for latched ones. */
export function ProcedureSheet({ group, subgroups = [], onClose }: {
  group: VisibleGroup; subgroups?: VisibleGroup[]; onClose: () => void;
}) {
  const { snap } = useApp();
  const connected = snap?.status === "connected";
  return (
    <Sheet title={group.group.title} onClose={onClose}>
      {!connected ? <div className="small dis">Not connected — actions are disabled until the module answers.</div> : null}
      {group.items.length ? (
        <div className="stack">{group.items.map((i) => <ItemCard key={i.id} item={i} disabled={!connected} />)}</div>
      ) : null}
      {subgroups.map((c) => (
        <section key={c.group.id}>
          <div className="kicker group-title">{c.group.title}</div>
          <div className="stack">{c.items.map((i) => <ItemCard key={i.id} item={i} disabled={!connected} />)}</div>
        </section>
      ))}
      <button className="btn accent" onClick={onClose}>Done</button>
    </Sheet>
  );
}
