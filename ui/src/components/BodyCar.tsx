import { BODY_GROUPS, BODY_SIGNALS as S } from "../layout";
import type { SignalValue } from "../api/schemas";
import { fmt } from "../lib/format";
import { VehicleBase } from "./VehicleBase";

/** Body (BCU) vehicle view: a top-down Discovery whose own headlamp/tail clusters, indicators
 * and doors light up from the BCU read-inputs, with a category-grouped readout list below.
 * Honest: a signal absent from the snapshot renders "awaiting mapping" (dashed) — never a
 * fabricated state. */

export function BodyCar({ signals }: { signals: Record<string, SignalValue> }) {
  const has = (n: string) => signals[n] !== undefined;
  const on = (n: string) => typeof signals[n]?.v === "number" && (signals[n]!.v as number) !== 0;
  const anyLive = Object.values(S).some((n) => has(n));

  // className for a light zone: absent (dashed) · on (tone) · dim-on (tone, faded) · off
  const lz = (active: boolean, present: boolean, tone: string, dim = false) =>
    !present ? "lz absent" : active ? `lz on ${tone}${dim ? " dim" : ""}` : "lz";
  const door = (sig: string) => (!has(sig) ? "door2 absent" : on(sig) ? "door2 open" : "door2");

  const headOn = on(S.side) || on(S.dipped) || on(S.main);
  const headDim = headOn && !on(S.dipped) && !on(S.main); // side only
  const headPresent = has(S.side) || has(S.dipped) || has(S.main);
  const tailOn = on(S.brake) || on(S.side);
  const tailDim = tailOn && !on(S.brake);
  const tailPresent = has(S.brake) || has(S.side);

  return (
    <div className="tile" style={{ gridColumn: "1 / -1" }}>
      <VehicleBase ariaLabel="Body control — lamps, doors and openings">
        {/* front lamps */}
        <rect className={lz(headOn, headPresent, "accent", headDim)} x="92" y="54" width="26" height="12" rx="3" />
        <rect className={lz(headOn, headPresent, "accent", headDim)} x="182" y="54" width="26" height="12" rx="3" />
        <rect className={lz(on(S.indL), has(S.indL), "amber")} x="90" y="68" width="16" height="5" rx="2" />
        <rect className={lz(on(S.indR), has(S.indR), "amber")} x="194" y="68" width="16" height="5" rx="2" />
        <rect className={lz(on(S.frontFog), has(S.frontFog), "accent")} x="124" y="66" width="12" height="6" rx="2" />
        <rect className={lz(on(S.frontFog), has(S.frontFog), "accent")} x="164" y="66" width="12" height="6" rx="2" />
        {/* rear lamps */}
        <rect className={lz(tailOn, tailPresent, "red", tailDim)} x="92" y="454" width="26" height="13" rx="3" />
        <rect className={lz(tailOn, tailPresent, "red", tailDim)} x="182" y="454" width="26" height="13" rx="3" />
        <rect className={lz(on(S.reverse), has(S.reverse), "white")} x="134" y="452" width="32" height="6" rx="2" />
        <rect className={lz(on(S.rearFog), has(S.rearFog), "red")} x="134" y="461" width="32" height="5" rx="2" />
        <rect className={lz(on(S.indL), has(S.indL), "amber")} x="90" y="470" width="16" height="5" rx="2" />
        <rect className={lz(on(S.indR), has(S.indR), "amber")} x="194" y="470" width="16" height="5" rx="2" />
        {/* doors (side) + openings (bonnet / tailgate outline only when open/absent) */}
        <rect className={door(S.doorPassenger)} x="85" y="192" width="9" height="82" rx="3" />
        <rect className={door(S.doorDriver)} x="206" y="192" width="9" height="82" rx="3" />
        {(!has(S.bonnet) || on(S.bonnet)) && (
          <rect className={door(S.bonnet)} x="92" y="72" width="116" height="74" rx="12" fill="none" />
        )}
        {(!has(S.tailgate) || on(S.tailgate)) && (
          <rect className={door(S.tailgate)} x="92" y="410" width="116" height="34" rx="10" fill="none" />
        )}
      </VehicleBase>

      <div className="small muted pretty" style={{ margin: "2px 2px 10px" }}>
        {anyLive
          ? "Body states — candidate (demo / mock; not a proven decode). Sniff with the run-sheet to confirm."
          : "Awaiting mapping — connect the BCU and sniff its read-inputs to populate these zones."}
      </div>

      {BODY_GROUPS.map((g) => (
        <section key={g.title}>
          <div className="kicker group-title">{g.title}</div>
          <div className="ro-grid">
            {g.items.map((r) => {
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
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
