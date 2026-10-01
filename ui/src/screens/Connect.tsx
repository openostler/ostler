import { command } from "../api/client";
import { MODULES, moduleName } from "../layout";
import { useApp } from "../state/app";

export function Connect() {
  const { snap, module, live, refresh, toast, goTo } = useApp();
  const st = snap?.status;
  const mode = snap?.mode ?? "—";
  const recording = !!snap?.logging?.recording;

  const select = async (id: string) => {
    if (id === module) return;
    if (recording && !window.confirm(
      `Recording is on.\nSwitching to ${moduleName(id)} rotates the log to a new file — the current ` +
      `module's data pauses while ${moduleName(id)} is active (the K-line carries one session at a time).\n\nSwitch anyway?`,
    )) return;
    try {
      const r = await command("select_module", { module: id });
      if (!r.ok) toast(r.error ?? "could not switch module", true);
    } catch (e) {
      toast((e as Error).message, true);
    }
    goTo("faults"); // land on Faults after connecting
  };

  return (
    <>
      <h2>Connect</h2>
      <div className="small muted">One session at a time — the K-line is shared.</div>
      <div className="card">
        <div className="row" style={{ gap: 8, marginBottom: 8 }}>
          <span className={`pdot ${st === "connected" ? "green" : st === "error" ? "red" : "yellow"}`} />
          <span style={{ fontWeight: 700 }}>Interface — {mode === "live" ? "live vehicle" : "mock (no car)"}</span>
        </div>
        <dl className="kv">
          <dt>SOURCE</dt><dd>{snap?.source ?? "—"}</dd>
          <dt>LINE</dt><dd>10 400 baud · 8N1 · half duplex</dd>
          <dt>MODE</dt><dd>{mode} · switch in Settings</dd>
        </dl>
      </div>
      <section>
        <div className="kicker group-title">Select module</div>
        <div className="stack">
          {MODULES.map((m) => {
            const on = m.id === snap?.module;
            const isLive = on && st === "connected"; // selected AND the session is up
            return (
              <button key={m.id} className="opt" aria-pressed={on} disabled={!m.connectable}
                onClick={() => select(m.id)}>
                <div className="grow">
                  <div className="on-name">{m.name}</div>
                  <div className="on-desc">{m.desc}</div>
                </div>
                <span className={`mtag ${isLive ? "connected" : m.tag}`}>{isLive ? "connected" : m.tag}</span>
              </button>
            );
          })}
        </div>
      </section>
      {st === "error" ? (
        <div className="card bad">
          <div style={{ fontWeight: 700, color: "var(--ic-red)" }}>No connection</div>
          <div className="small muted pretty" style={{ marginTop: 4 }}>{snap?.error || "The module did not answer."}</div>
          <ul className="small muted" style={{ margin: "8px 0 0", paddingLeft: 18 }}>
            <li>Ignition on, vehicle stationary.</li>
            <li>Check the KKL cable and OBD pin 7.</li>
            <li>SLABS answers best with the engine running.</li>
          </ul>
          <button className="btn accent" style={{ marginTop: 10 }} onClick={refresh}>Retry</button>
        </div>
      ) : live.seq.length ? (
        <div className="card">
          <span className="kicker">Connection sequence</span>
          <div style={{ marginTop: 4 }}>
            {live.seq.map((s, i) => {
              const last = i === live.seq.length - 1;
              const active = last && !live.seqDone && st !== "connected";
              const prev = live.seq[i - 1];
              return (
                <div className="seq-row" key={`${s.phase}-${s.t}`}>
                  <span className={`pdot ${s.ok ? "green" : active ? "yellow blink" : ""}`} />
                  <span className={`grow ${s.ok ? "ok" : ""}`}>{s.phase}</span>
                  <span className="small dis">{prev ? `+${Math.round(s.t - prev.t)} ms` : "0 ms"}</span>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}
    </>
  );
}
