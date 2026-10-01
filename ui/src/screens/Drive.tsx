import { useEffect, useState } from "react";
import { Gauge } from "../components/Gauge";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { Value } from "../components/Value";
import { DRIVE_TILES } from "../layout";
import { clockHHMM, flagFor } from "../lib/format";
import { useApp } from "../state/app";

function useClock(): string {
  const [now, setNow] = useState(clockHHMM);
  useEffect(() => {
    const id = window.setInterval(() => setNow(clockHHMM()), 10_000);
    return () => window.clearInterval(id);
  }, []);
  return now;
}

/** Driver's dashboard: a curated, glanceable set, big enough to read on the move. */
export function Drive() {
  const { snap, fields, ackedFaults, showFaultSheet } = useApp();
  const clock = useClock();
  const recording = !!snap?.logging?.recording;
  const head = (
    <ScreenHead title="Drive">{recording ? <span className="flag hi">● REC</span> : null}</ScreenHead>
  );
  if (snap?.status !== "connected") return <>{head}<StatusGate /></>;

  const unacked = snap.faults.filter((f) => !ackedFaults.has(f));
  // square cells: 4 columns; a pair of tiles containing a gauge is 2 rows tall
  let rows = 0;
  for (let i = 0; i < DRIVE_TILES.length; i += 2) rows += DRIVE_TILES.slice(i, i + 2).some((t) => t.gauge) ? 2 : 1;

  return (
    <>
      {head}
      {unacked.length ? (
        <button className="card bad tap" style={{ textAlign: "left" }} onClick={() => showFaultSheet(unacked)}>
          <span style={{ fontWeight: 700, color: "var(--ic-red)" }}>
            ⚠ {unacked.length} new fault{unacked.length > 1 ? "s" : ""}
          </span>
          <span className="small muted" style={{ marginLeft: 8 }}>tap to view</span>
        </button>
      ) : null}
      <div className="drive" style={{ aspectRatio: `4 / ${rows}` }}>
        {DRIVE_TILES.map((t) => {
          if (t.clock) {
            return (
              <div className="dtile" key="clock">
                <div className="dlabel">{t.label}</div>
                <div className="dval"><span className="cv-num">{clock}</span></div>
              </div>
            );
          }
          const name = t.signal ?? "";
          const s = snap.signals[name];
          let v = typeof s?.v === "number" ? s.v : null;
          if (v != null && t.conv) v = t.conv(v);
          const unit = t.unit ?? (s?.u || fields[name]?.unit || "");
          if (t.gauge) {
            return (
              <div className="dtile gauge" key={name} data-signal={name}>
                <div className="dlabel">{t.label}</div>
                <div className="gwrap"><Gauge value={v} min={t.gauge.min} max={t.gauge.max} unit={unit} dec={t.dec} /></div>
              </div>
            );
          }
          const fl = flagFor(s?.s, s?.c);
          return (
            <div className={`dtile${fl.cls === "lo" || fl.cls === "hi" ? " warn" : ""}`} key={name} data-signal={name}>
              <div className="dlabel">{t.label}</div>
              <div className="dval"><Value value={v} unit={unit} dec={t.dec} /></div>
            </div>
          );
        })}
      </div>
    </>
  );
}
