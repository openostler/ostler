import { api, command } from "../api/client";
import { useApp } from "../state/app";
import { confirmAction } from "./confirm";
import { RadioOpt } from "./RadioOpt";
import { Sheet } from "./Sheet";

export function Settings({ onClose }: { onClose: () => void }) {
  const { prefs, setPrefs, snap, community, reloadCommunity, toast, admin } = useApp();
  const share = community ? !!community.consent : prefs.share === true;
  const mode = snap?.mode ?? "mock";
  const modes = snap?.modes ?? [];

  const setShare = (v: boolean) => {
    setPrefs({ share: v });
    api.setConsent(v).then(reloadCommunity, () => toast("could not save the sharing choice", true));
  };
  const setMode = async (v: string) => {
    onClose();
    try {
      const r = await command("set_mode", { mode: v });
      toast(r.ok ? r.message ?? `mode: ${v}` : r.error ?? "could not switch", !r.ok);
    } catch (e) {
      toast(String((e as Error).message), true);
    }
  };
  const shutdown = async () => {
    if (!confirmAction("Shut down the Pi now?", "The dashboard goes offline. Wait for the green LED to stop before cutting power.")) return;
    try {
      const r = await command("shutdown");
      if (r.ok) { onClose(); toast("Shutting down the Pi…"); } else toast(r.error ?? "Shutdown refused", true);
    } catch {
      onClose(); toast("Shutting down the Pi…"); // the request drops as the Pi powers off
    }
  };

  return (
    <Sheet title="Settings" onClose={onClose}>
      <section role="radiogroup" aria-label="Trust">
        <div className="kicker" style={{ marginBottom: 8 }}>Trust</div>
        <div className="stack">
          <RadioOpt name="Trusted" desc="Only routines proven on the car. Unverified stays hidden."
            on={prefs.trust === "trusted"} onSelect={() => setPrefs({ trust: "trusted" })} />
          <RadioOpt name="Experimental" desc="Exposes partial modules and unverified tests. They can misbehave."
            on={prefs.trust === "experimental"} onSelect={() => setPrefs({ trust: "experimental" })} />
        </div>
      </section>
      {modes.length >= 2 && !snap?.public ? (
        <section>
          <div className="kicker" style={{ marginBottom: 8 }}>Data source</div>
          <div className="btn-row">
            <button className={`btn ${mode === "mock" ? "accent" : ""}`} aria-pressed={mode === "mock"} onClick={() => setMode("mock")}>Mock</button>
            <button className={`btn ${mode === "live" ? "accent" : ""}`} aria-pressed={mode === "live"} onClick={() => setMode("live")}>Live vehicle</button>
          </div>
        </section>
      ) : null}
      <section>
        <div className="kicker" style={{ marginBottom: 8 }}>Data sharing</div>
        <div className="row card">
          <div className="grow">
            <div style={{ fontWeight: 700 }}>Share anonymous traces</div>
            <div className="small muted pretty">Raw fault blocks and unmapped bits — no VIN, no location, no identifiers.</div>
          </div>
          <button className="tgl" role="switch" aria-checked={share} aria-label="Share anonymous traces"
            onClick={() => setShare(!share)}><span /></button>
        </div>
      </section>
      <section>
        <div className="kicker" style={{ marginBottom: 8 }}>Display</div>
        <div className="btn-row">
          {(["light", "dark"] as const).map((t) => (
            <button key={t} className={`btn ${prefs.theme === t ? "accent" : ""}`} aria-pressed={prefs.theme === t}
              onClick={() => setPrefs({ theme: t })}>{t === "light" ? "Light" : "Dark"}</button>
          ))}
        </div>
      </section>
      <section>
        <div className="kicker" style={{ marginBottom: 8 }}>Units</div>
        <div className="btn-row" style={{ marginBottom: 8 }}>
          {(["C", "F"] as const).map((u) => (
            <button key={u} className={`btn ${prefs.units.temp === u ? "accent" : ""}`} aria-pressed={prefs.units.temp === u}
              onClick={() => setPrefs({ units: { ...prefs.units, temp: u } })}>°{u}</button>
          ))}
        </div>
        <div className="btn-row">
          <button className={`btn ${prefs.units.dist === "km" ? "accent" : ""}`} aria-pressed={prefs.units.dist === "km"}
            onClick={() => setPrefs({ units: { ...prefs.units, dist: "km" } })}>km · km/h</button>
          <button className={`btn ${prefs.units.dist === "mi" ? "accent" : ""}`} aria-pressed={prefs.units.dist === "mi"}
            onClick={() => setPrefs({ units: { ...prefs.units, dist: "mi" } })}>miles · mph</button>
        </div>
      </section>
      {!admin ? (
        <section>
          <div className="kicker" style={{ marginBottom: 8 }}>Advanced</div>
          <a className="btn block" href="/admin" style={{ lineHeight: "48px" }}>Mapping console (admin)</a>
          <div className="small muted pretty" style={{ marginTop: 6 }}>
            Same app in admin mode: adds the coverage Map, Capture and Docs. Password protected.
          </div>
        </section>
      ) : null}
      {snap?.allow_shutdown ? (
        <section>
          <div className="kicker" style={{ marginBottom: 8 }}>Power</div>
          <button className="btn danger block" onClick={shutdown}>Shut down Pi</button>
          <div className="small muted pretty" style={{ marginTop: 6 }}>
            Powers off the Raspberry Pi safely. Wait for the green LED to stop before cutting power.
          </div>
        </section>
      ) : null}
      <button className="btn accent" onClick={onClose}>Done</button>
    </Sheet>
  );
}
