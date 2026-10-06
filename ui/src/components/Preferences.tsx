// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { api, command } from "../api/client";
import { useApp } from "../state/app";
import { confirmAction } from "./confirm";
import { RadioOpt } from "./RadioOpt";
import { RecordingOptions } from "./RecordingOptions";
import { Sheet } from "./Sheet";
import { VersionCard } from "./VersionCard";

/** ⚙ Preferences (per device): trust mode, sharing, display, units, "Recording & flags" (the
 * recording options and the flag manager, reachable without a recording), admin link, power,
 * and the running version.
 * The serial port lives in the ConnectionSheet (there is no mock mode — ADR-0011). */
export function Preferences({ onClose }: { onClose: () => void }) {
  const { prefs, setPrefs, snap, community, reloadCommunity, toast, admin } = useApp();
  const [recOpts, setRecOpts] = useState(false);
  const share = community ? !!community.consent : prefs.share === true;

  const setShare = (v: boolean) => {
    setPrefs({ share: v });
    api.setConsent(v).then(reloadCommunity, () => toast("could not save the sharing choice", true));
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

  // One sheet at a time: Recording & flags replaces Preferences and comes back to it on close.
  if (recOpts) return <RecordingOptions onClose={() => setRecOpts(false)} />;
  return (
    <Sheet title="Preferences" onClose={onClose}>
      <section role="radiogroup" aria-label="Trust">
        <div className="kicker" style={{ marginBottom: 8 }}>Trust</div>
        <div className="stack">
          <RadioOpt name="Stable" desc="Only what is verified on a car. Everything in progress stays hidden."
            on={prefs.trust === "trusted"} onSelect={() => setPrefs({ trust: "trusted" })} />
          <RadioOpt name="Experimental" desc="Shows every item with its status and coverage, and enables candidate tests. They can misbehave."
            on={prefs.trust === "experimental"} onSelect={() => setPrefs({ trust: "experimental" })} />
        </div>
      </section>
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
          {(["auto", "light", "dark"] as const).map((t) => (
            <button key={t} className={`btn ${prefs.theme === t ? "accent" : ""}`} aria-pressed={prefs.theme === t}
              onClick={() => setPrefs({ theme: t })}>{{ auto: "Auto (day/night)", light: "Day", dark: "Night" }[t]}</button>
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
      <section>
        <div className="kicker" style={{ marginBottom: 8 }}>Recording</div>
        <button className="btn block" onClick={() => setRecOpts(true)}>Recording &amp; flags</button>
        <div className="small muted pretty" style={{ marginTop: 6 }}>
          Audio and accelerometer sources, and which flags show on the transport.
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
      <section>
        <div className="kicker" style={{ marginBottom: 8 }}>Version</div>
        <VersionCard />
      </section>
      <button className="btn accent" onClick={onClose}>Done</button>
    </Sheet>
  );
}
