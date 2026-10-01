import { command } from "../api/client";
import { ComingCard } from "../components/Coming";
import { confirmAction } from "../components/confirm";
import { ScreenHead } from "../components/ScreenHead";
import { StatusGate } from "../components/StatusGate";
import { OUTPUTS, type OutputButton, type OutputDef } from "../layout";
import { useApp } from "../state/app";

export function Outputs() {
  const { snap, module, experimental, toast } = useApp();
  const list = OUTPUTS[module];

  const run = async (o: OutputDef, b: OutputButton) => {
    const what = `${o.name} — ${b.label}`;
    if (b.warn && !confirmAction(what, "Drives real hardware. Vehicle stationary, handbrake on, nobody under the car.")) return;
    toast(`${what}…`);
    try {
      const r = await command(b.action);
      toast(r.ok ? r.message ?? "ok" : `Error: ${r.error ?? "unknown"}`, !r.ok);
    } catch (e) {
      toast((e as Error).message, true);
    }
  };

  const head = <ScreenHead title="Outputs" />;
  if (!list) return <>{head}<ComingCard title="Actuator tests" items={[{ name: "No output tests mapped for this module yet", tag: "—" }]} /></>;
  if (snap?.status !== "connected") return <>{head}<StatusGate /></>;
  const groups = [...new Set(list.map((o) => o.group))];
  return (
    <>
      {head}
      <div className="card warn">
        <div style={{ fontWeight: 700 }}>Actuator tests drive real hardware</div>
        <div className="small pretty" style={{ marginTop: 2 }}>
          Vehicle stationary, handbrake on, nobody under the car. Each test pulses a moment — it does not latch on.
        </div>
      </div>
      {groups.map((g) => (
        <section key={g}>
          <div className="kicker group-title">{g}</div>
          <div className="grid">
            {list.filter((o) => o.group === g).map((o) => {
              const locked = o.tag === "experimental" && !experimental;
              return (
                <div className="card" key={o.name} style={locked ? { opacity: 0.55 } : undefined}>
                  <div className="row" style={{ gap: 8 }}>
                    <span style={{ fontWeight: 700 }}>{o.name}</span>
                    <span className={`mtag ${o.tag}`}>{o.tag}</span>
                  </div>
                  <div className="row" style={{ gap: 8, marginTop: 8 }}>
                    <span className="grow small dis mono">{o.cmd}</span>
                    {locked ? <span className="small dis">enable Experimental</span> : o.buttons.map((b) => (
                      <button key={b.action} className={`btn ${b.warn ? "danger" : ""}`} onClick={() => run(o, b)}>{b.label}</button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}
    </>
  );
}
