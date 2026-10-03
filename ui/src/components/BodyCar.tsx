import { BODY_DOORS, BODY_LAMPS, BODY_READOUTS, type BodyDoor } from "../layout";
import type { SignalValue } from "../api/schemas";
import { fmt } from "../lib/format";
import { VehicleBase } from "./VehicleBase";

/** Body (BCU) vehicle view: a top-down Discovery with the exterior lamps, doors/openings and
 * a readout list, driven by the BCU read-inputs. Honest by construction — a zone whose signal
 * is absent from the snapshot renders "awaiting mapping" (dashed), never a made-up state. */

const DOOR_POS: Record<BodyDoor["place"], { x: number; y: number; w: number; h: number; lx: number; ly: number }> = {
  frontR: { x: 203, y: 176, w: 8, h: 56, lx: 196, ly: 168 },
  frontL: { x: 89, y: 176, w: 8, h: 56, lx: 104, ly: 168 },
  front: { x: 118, y: 88, w: 64, h: 8, lx: 150, ly: 110 },
  rear: { x: 118, y: 368, w: 64, h: 8, lx: 150, ly: 362 },
};

export function BodyCar({ signals }: { signals: Record<string, SignalValue> }) {
  const present = (n: string) => signals[n] !== undefined;
  const on = (n: string) => typeof signals[n]?.v === "number" && (signals[n]!.v as number) !== 0;
  const anyLive = BODY_LAMPS.some((l) => present(l.signal)) || BODY_DOORS.some((d) => present(d.signal));

  const lampClass = (sig: string, tone: string) =>
    !present(sig) ? "lamp absent" : on(sig) ? `lamp on tone-${tone}` : "lamp off";
  const doorClass = (sig: string) => (!present(sig) ? "door absent" : on(sig) ? "door open" : "door closed");

  const readout = (r: (typeof BODY_READOUTS)[number]) => {
    const s = signals[r.signal];
    const text = !s ? "—" : r.kind === "flag" ? (on(r.signal) ? "ON" : "off")
      : `${fmt(typeof s.v === "number" ? s.v : null, r.dec ?? 0)}${r.unit ? " " + r.unit : ""}`;
    const cls = !s ? "dis" : r.kind === "flag" && on(r.signal) ? "ok" : "";
    return (
      <div className="ro-line" key={r.signal}>
        <span className="grow">{r.label}</span>
        <span className={cls}>{text}</span>
      </div>
    );
  };

  return (
    <div className="tile" style={{ gridColumn: "1 / -1" }}>
      <VehicleBase ariaLabel="Body control — lamps, doors and openings">
        {BODY_DOORS.map((d) => {
          const p = DOOR_POS[d.place];
          return (
            <g key={d.id}>
              <rect className={doorClass(d.signal)} x={p.x} y={p.y} width={p.w} height={p.h} rx="3" />
              <text className="v-zlbl" x={p.lx} y={p.ly}>{d.label}{present(d.signal) && on(d.signal) ? " · open" : ""}</text>
            </g>
          );
        })}
        {BODY_LAMPS.map((l) => (
          <g key={l.id}>
            <circle className={lampClass(l.signal, l.tone)} cx={l.x} cy={l.y} r="7" />
            <text className="v-llbl" x={l.x} y={l.y + 18}>{l.label}</text>
          </g>
        ))}
      </VehicleBase>

      <div className="small muted pretty" style={{ margin: "4px 2px 8px" }}>
        {anyLive
          ? "Body states — candidate (demo/mock; not a proven decode). Sniff with the run-sheet to confirm."
          : "Awaiting mapping — connect the BCU and sniff its read-inputs to populate these zones."}
      </div>
      <div className="stack">{BODY_READOUTS.map(readout)}</div>
    </div>
  );
}
