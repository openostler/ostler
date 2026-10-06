// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState } from "react";
import { api } from "../api/client";
import { useApp } from "../state/app";
import { RadioOpt } from "./RadioOpt";

/** First start: trust level and data sharing must be chosen before anything connects. */
export function Consent() {
  const { prefs, setPrefs, reloadCommunity } = useApp();
  const [trust, setTrust] = useState(prefs.trust);
  const [share, setShare] = useState<boolean | null>(prefs.share);
  const ready = share !== null;
  const accept = () => {
    if (share === null) return;
    setPrefs({ trust, share, consentDone: true });
    api.setConsent(share).then(reloadCommunity, () => undefined);
  };
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="consent-title">
      <div style={{ flex: 1, overflowY: "auto", padding: "24px 16px", display: "flex", flexDirection: "column", gap: 16 }}>
        <div>
          <div className="kicker">First start</div>
          <div id="consent-title" style={{ fontSize: 24, lineHeight: "32px", fontWeight: 700 }}>Before you connect</div>
        </div>
        <div className="muted pretty">
          This tool writes to real ECUs over the K-line. Two choices decide what it may do. Both
          change later in Preferences (⚙).
        </div>
        <section role="radiogroup" aria-label="Trust">
          <div className="kicker" style={{ marginBottom: 8 }}>Trust</div>
          <div className="stack">
            <RadioOpt name="Stable" desc="Only what is verified on a car." on={trust === "trusted"} onSelect={() => setTrust("trusted")} />
            <RadioOpt name="Experimental" desc="Shows work in progress and enables unverified tests." on={trust === "experimental"} onSelect={() => setTrust("experimental")} />
          </div>
        </section>
        <section role="radiogroup" aria-label="Data sharing">
          <div className="kicker" style={{ marginBottom: 8 }}>Data sharing</div>
          <div className="stack">
            <RadioOpt name="Share anonymous traces" desc="Helps name unknown bits. No VIN, no location." on={share === true} onSelect={() => setShare(true)} />
            <RadioOpt name="Don't share" desc="Nothing leaves the device." on={share === false} onSelect={() => setShare(false)} />
          </div>
          <div className="small dis pretty" style={{ marginTop: 8 }}>
            Sharing is off unless chosen here. Nothing leaves the device before this screen is answered.
          </div>
        </section>
      </div>
      <div style={{ padding: 16, borderTop: "1px solid var(--border)", background: "var(--bg-surface)", display: "flex", flexDirection: "column", gap: 8 }}>
        <button className={`btn ${ready ? "accent" : ""}`} disabled={!ready} onClick={accept}>Continue</button>
        <div className="small dis" style={{ textAlign: "center" }}>
          {ready ? `${trust === "trusted" ? "Stable" : "Experimental"} · sharing ${share ? "on" : "off"} · changeable in Preferences (⚙).` : "Answer data sharing to continue."}
        </div>
      </div>
    </div>
  );
}
