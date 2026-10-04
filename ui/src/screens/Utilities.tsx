import { useState } from "react";
import { useAction } from "../api/useAction";
import { CoverageBar } from "../components/CoverageBar";
import { ProcedureSheet } from "../components/ProcedureSheet";
import { ScreenHead } from "../components/ScreenHead";
import { Sheet } from "../components/Sheet";
import { StatusTag } from "../components/StatusTag";
import { UTIL_LIDS } from "../layout";
import { coverageOf, groupTree, pageOf, STABLE_EMPTY, type GroupNode, type VisibleGroup } from "../lib/catalog";
import { spacedHex } from "../lib/format";
import { useApp } from "../state/app";

/** Raw LID block dump: read-only `21 xx` reads straight off the ECU (Advanced, Experimental only). */
function LidDump() {
  const { module, toast } = useApp();
  const run = useAction();
  const preset = UTIL_LIDS[module] ?? { example: "", note: "" };
  const [lids, setLids] = useState(preset.example);
  const [raws, setRaws] = useState<Record<string, string> | null>(null);

  const read = async () => {
    const list = lids.split(/[ ,]+/).filter(Boolean);
    if (!list.length) return toast("enter at least one LID", true);
    const r = await run("read_block", { lids: list }, { quiet: true });
    if (!r?.ok) return;
    setRaws(r.raws ?? {});
    toast(`read ${Object.keys(r.raws ?? {}).length} LID(s)`);
  };

  return (
    <div className="card">
      <div className="kicker" style={{ marginBottom: 8 }}>Raw LID block dump</div>
      <div className="small muted pretty" style={{ marginBottom: 8 }}>
        Read raw <span className="mono">21 xx</span> data straight off the ECU — read-only. {preset.note}
      </div>
      <form className="row" style={{ gap: 8 }} onSubmit={(e) => { e.preventDefault(); void read(); }}>
        <label className="visually-hidden" htmlFor="lidin">LIDs to read</label>
        <input id="lidin" className="input mono grow" value={lids} placeholder="e.g. 54 43 50"
          onChange={(e) => setLids(e.target.value)} />
        <button className="btn accent" type="submit">Read</button>
      </form>
      {raws ? (
        <div className="stack" style={{ marginTop: 12, gap: 4 }}>
          {Object.keys(raws).length ? Object.entries(raws).map(([lid, hex]) => (
            <div key={lid} className="row mono small" style={{ gap: 12 }}>
              <span className="lid">21 {lid}</span><span className="grow" style={{ wordBreak: "break-all" }}>{spacedHex(hex)}</span>
            </div>
          )) : <span className="dis">no LID answered</span>}
        </div>
      ) : null}
    </div>
  );
}

type Open = { group: VisibleGroup; children: VisibleGroup[] } | "advanced" | null;

function GroupCard({ node, onOpen }: { node: GroupNode; onOpen: (o: Open) => void }) {
  const { experimental } = useApp();
  const all = [...node.items, ...node.children.flatMap((c) => c.items)];
  const cov = coverageOf(all);
  return (
    <div className="card util" data-group={node.group.id}>
      <button className="util-head" onClick={() => onOpen({ group: node, children: node.children })}>
        <span className="grow item-name">{node.group.title}</span>
        <span className="small dis">{all.length} item{all.length === 1 ? "" : "s"}</span>
        <span aria-hidden="true" className="dis">›</span>
      </button>
      {experimental && cov.total ? (
        <div className="row wrap" style={{ gap: 6, marginTop: 6 }}>
          {(["verified", "candidate", "sniff", "untranscribed"] as const).filter((s) => cov[s]).map((s) => <StatusTag key={s} status={s} />)}
        </div>
      ) : null}
      {node.children.length ? (
        <div className="submenu">
          {node.children.map((c) => (
            <button key={c.group.id} className="sub" onClick={() => onOpen({ group: c, children: [] })}>
              <span className="grow">{c.group.title}</span>
              <span className="small dis">{c.items.length}</span>
              <span aria-hidden="true" className="dis">›</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/** Multi-step and latched procedures, calibrations, security and key programming
 * (catalog page "utilities"), as group cards with at most one sub-menu level. Each opens
 * a ProcedureSheet. The raw LID dump is under "Advanced", Experimental only. */
export function Utilities() {
  const { catalog, experimental } = useApp();
  const [open, setOpen] = useState<Open>(null);
  const page = pageOf(catalog, "utilities");
  const tree = groupTree(page, experimental);

  return (
    <>
      <ScreenHead title="Utilities" />
      {experimental && page ? <CoverageBar coverage={page.coverage} label="Utilities coverage" /> : null}
      {!catalog && !experimental ? <div className="empty">Loading…</div> : !tree.length && !experimental ? (
        <div className="empty"><div className="pretty">{STABLE_EMPTY}</div></div>
      ) : (
        <div className="grid">
          {tree.map((n) => <GroupCard key={n.group.id} node={n} onOpen={setOpen} />)}
          {experimental ? (
            <div className="card util" data-group="advanced">
              <button className="util-head" onClick={() => setOpen("advanced")}>
                <span className="grow item-name">Advanced</span>
                <span className="small dis">raw LID dump</span>
                <span aria-hidden="true" className="dis">›</span>
              </button>
            </div>
          ) : null}
        </div>
      )}
      {open === "advanced" ? (
        <Sheet title="Advanced" onClose={() => setOpen(null)}>
          <LidDump />
          <button className="btn accent" onClick={() => setOpen(null)}>Done</button>
        </Sheet>
      ) : open ? (
        <ProcedureSheet group={open.group} subgroups={open.children} onClose={() => setOpen(null)} />
      ) : null}
    </>
  );
}
