import { CoverageBar } from "../components/CoverageBar";
import { ItemCard } from "../components/ItemCard";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { pageOf, STABLE_EMPTY, visibleGroups } from "../lib/catalog";
import { useApp } from "../state/app";

/** Simple on/off/pulse actuator tests (catalog page "outputs"). Multi-step and latched
 * procedures live under Utilities. Every action confirms per the command registry. */
export function Outputs() {
  const { snap, catalog, experimental } = useApp();
  const page = pageOf(catalog, "outputs");
  const groups = visibleGroups(page, experimental);
  const connected = snap?.status === "connected";

  return (
    <>
      <ScreenHead title="Outputs" />
      {experimental && page ? <CoverageBar coverage={page.coverage} label="Outputs coverage" /> : null}
      {!connected ? <StatusGate /> : null}
      {!catalog ? <div className="empty">Loading…</div> : !groups.length ? (
        <div className="empty"><div className="pretty">{experimental ? "No output tests catalogued for this module yet." : STABLE_EMPTY}</div></div>
      ) : (
        <>
          <div className="card warn">
            <div style={{ fontWeight: 700 }}>Actuator tests drive real hardware</div>
            <div className="small pretty" style={{ marginTop: 2 }}>
              Vehicle stationary, handbrake on, nobody under the car. Each test pulses a moment — it does not latch on.
            </div>
          </div>
          {groups.map(({ group, items }) => (
            <section key={group.id}>
              <div className="kicker group-title">{group.title}</div>
              <div className="grid">
                {items.map((i) => <ItemCard key={i.id} item={i} disabled={!connected} />)}
              </div>
            </section>
          ))}
        </>
      )}
    </>
  );
}
