import { BodyCar } from "../components/BodyCar";
import { HealthStrip } from "../components/HealthStrip";
import { ScreenHead } from "../components/ScreenHead";
import { SlabsCar } from "../components/SlabsCar";
import { StatTile } from "../components/StatTile";
import { StatusGate } from "../components/StatusGate";
import { DRIVE_TILES } from "../layout";
import { useApp } from "../state/app";

/** Driver's dashboard: a per-module vehicle view on one shared Discovery base. TD5 shows
 * the hero tiles, SLABS the wheels/heights, BCU the body (lamps/doors). Other modules show a
 * placeholder until they get a view. Calm when healthy; neutral/"awaiting" when undecoded. */
export function Drive() {
  const { snap, module, fields } = useApp();
  const recording = !!snap?.logging?.recording;
  const head = <ScreenHead title="Drive">{recording ? <span className="status hi"><span className="si">●</span>REC</span> : null}</ScreenHead>;
  if (snap?.status !== "connected") return <>{head}<StatusGate /></>;

  if (module === "slabs") return <>{head}<HealthStrip /><SlabsCar signals={snap.signals} fields={fields} /></>;
  if (module === "bcu") return <>{head}<BodyCar signals={snap.signals} /></>;
  if (module === "motor") {
    return (
      <>
        {head}
        <HealthStrip />
        <div className="drive2">
          {DRIVE_TILES.map((t) => (
            <StatTile key={t.signal} name={t.signal} label={t.label} sig={snap.signals[t.signal]} field={fields[t.signal]}
              gauge={t.gauge} dec={t.dec} unit={t.unit} conv={t.conv} />
          ))}
        </div>
      </>
    );
  }
  return (
    <>
      {head}
      <div className="empty"><div className="title">No vehicle view for this module yet</div>
        <div className="pretty">Its faults, inputs and settings are on the other tabs.</div></div>
    </>
  );
}
