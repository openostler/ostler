import { useState } from "react";
import { command } from "../api/client";
import { ComingCard } from "../components/Coming";
import { ScreenHead } from "../components/ScreenHead";
import { UTIL_LIDS } from "../layout";
import { spacedHex } from "../lib/format";
import { useApp } from "../state/app";

/** Raw LID block dump: read-only `21 xx` reads straight off the ECU. */
export function Utilities() {
  const { module, toast } = useApp();
  const preset = UTIL_LIDS[module] ?? { example: "", note: "" };
  const [lids, setLids] = useState(preset.example);
  const [raws, setRaws] = useState<Record<string, string> | null>(null);

  const read = async () => {
    const list = lids.split(/[ ,]+/).filter(Boolean);
    if (!list.length) return toast("enter at least one LID", true);
    toast(`reading ${list.length} LID(s)…`);
    try {
      const r = await command("read_block", { lids: list });
      if (!r.ok) return toast(`Error: ${r.error ?? "?"}`, true);
      setRaws(r.raws ?? {});
      toast(`read ${Object.keys(r.raws ?? {}).length} LID(s)`);
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  return (
    <>
      <ScreenHead title="Utilities" />
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
      <ComingCard title="Coming" items={[
        { name: "ECU identifiers (1A — VIN, versions)", tag: "planned" },
        { name: "Routines & security status", tag: "planned" },
        { name: "Saved logs & reports", tag: "planned" },
      ]} />
    </>
  );
}
