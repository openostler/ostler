// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DocEntry } from "../api/schemas";
import { useApp } from "../state/app";
import { Icon } from "../icons/Icon";

/** Admin: the repo's canonical markdown (docs/ + references/), rendered by the server
 * fresh on every request — a window on the source, never a copy. */
export function Docs() {
  const { toast } = useApp();
  const [docs, setDocs] = useState<DocEntry[] | null>(null);
  const [open, setOpen] = useState<{ id: string; html: string } | null>(null);

  useEffect(() => {
    api.docs().then((r) => setDocs(r.docs), (e: Error) => { setDocs([]); toast(e.message, true); });
  }, [toast]);

  const show = async (id: string) => {
    try {
      setOpen({ id, html: await api.doc(id) });
      document.getElementById("view")?.scrollTo({ top: 0 });
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  if (open) {
    const title = docs?.find((d) => d.id === open.id)?.title ?? "";
    return (
      <>
        <div className="screen-head">
          <button className="iconbtn" onClick={() => setOpen(null)}><Icon name="arrow_back" size={18} />Documents</button>
          <span className="sub">{title}</span>
        </div>
        {/* Server-rendered from the repo's own markdown (web/markdown.py escapes inline HTML). */}
        <article className="card doc" dangerouslySetInnerHTML={{ __html: open.html }} />
      </>
    );
  }
  const groups = [...new Set((docs ?? []).map((d) => d.group || "Reference"))];
  return (
    <>
      <div className="screen-head"><h2>Docs</h2><span className="sub">· the repo's reference docs</span></div>
      {docs == null ? <div className="empty">Loading…</div> : !docs.length ? <div className="empty">No documents configured.</div> : (
        groups.map((g) => (
          <section key={g}>
            <div className="kicker group-title">{g}</div>
            <div className="stack">
              {docs.filter((d) => (d.group || "Reference") === g).map((d) => (
                <button key={d.id} className="opt" onClick={() => show(d.id)}>
                  <div className="on-name">{d.title}</div>
                </button>
              ))}
            </div>
          </section>
        ))
      )}
    </>
  );
}
