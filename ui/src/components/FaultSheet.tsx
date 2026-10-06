// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { parseFault } from "../lib/format";
import { moduleName } from "../layout";
import { useApp } from "../state/app";
import { Sheet } from "./Sheet";

/** Faults shown once (at startup or when new ones appear). Dismissing acknowledges them,
 * so afterwards only NEW faults alert while driving. */
export function FaultSheet({ faults, onDismiss }: { faults: string[]; onDismiss: () => void }) {
  const { module, faultMeaning } = useApp();
  return (
    <Sheet onClose={onDismiss} titleClass="fault-title"
      title={<span style={{ color: "var(--ic-red)" }}>⚠ {faults.length} fault{faults.length > 1 ? "s" : ""}</span>}>
      <div className="small muted pretty">
        Stored/active on {moduleName(module)}. Dismiss to keep driving — after this you are only
        alerted about NEW faults.
      </div>
      <div className="stack">
        {faults.map((f) => {
          const p = parseFault(f);
          const m = faultMeaning(f);
          return (
            <div key={f} className={`ro ${p.current ? "edge-red" : "edge-yellow"}`}>
              <div className="ro-top">
                <div className="grow">{p.raw ? <b>{p.raw} · </b> : null}{p.text}</div>
                {m?.pcode ? <span className="flag">{m.pcode}</span> : null}
                {p.tag ? <span className={`flag ${p.current ? "hi" : "sus"}`}>{p.tag}</span> : null}
              </div>
              {m?.cause ? <div className="small muted pretty">{m.cause}</div> : null}
            </div>
          );
        })}
      </div>
      <button className="btn accent" onClick={onDismiss}>Dismiss</button>
    </Sheet>
  );
}
