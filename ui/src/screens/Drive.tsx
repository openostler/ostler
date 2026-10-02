import { ComingCard } from "../components/Coming";
import { HealthStrip } from "../components/HealthStrip";
import { ScreenHead } from "../components/ScreenHead";
import { SlabsCar } from "../components/SlabsCar";
import { StatTile } from "../components/StatTile";
import { StatusGate } from "../components/StatusGate";
import { DRIVE_TILES } from "../layout";
import { useApp } from "../state/app";

/** Driver's dashboard: the health line first, then the few values that matter, each
 * shown against its healthy band. Calm when everything is normal.
 * Only TD5 and SLABS stream live driver signals; other modules show a placeholder. */
export function Drive() {
  const { snap, module, fields } = useApp();
  const recording = !!snap?.logging?.recording;
  const head = <ScreenHead title="Drive">{recording ? <span className="status hi"><span className="si">●</span>REC</span> : null}</ScreenHead>;
  if (snap?.status !== "connected") return <>{head}<StatusGate /></>;
  if (module !== "motor" && module !== "slabs") {
    return <>{head}<ComingCard title="Live signals"
      items={[{ name: "No live driver signals for this module yet — see Faults", tag: "—" }]} /></>;
  }
  return (
    <>
      {head}
      <HealthStrip />
      {module === "slabs" ? (
        <SlabsCar signals={snap.signals} fields={fields} />
      ) : (
        <div className="drive2">
          {DRIVE_TILES.map((t) => (
            <StatTile key={t.signal} name={t.signal} label={t.label} sig={snap.signals[t.signal]} field={fields[t.signal]}
              gauge={t.gauge} dec={t.dec} unit={t.unit} conv={t.conv} />
          ))}
        </div>
      )}
    </>
  );
}
