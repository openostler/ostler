// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { coveragePct } from "../lib/catalog";
import { moduleName } from "../layout";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { useSystems } from "../state/systems";
import { Icon } from "../icons/Icon";

/** The compact "current system" switcher in Diagnose's identity bar (UI spec §4.2; it was the
 * header's module picker before U1): one bordered control (muted "Module" label, the module
 * name, ▾) over a native <select>, plus — Experimental only — an "NN% mapped" pill (verified
 * over total, from GET /catalog; "NN%" alone on narrow phones). Switching sends select_module
 * and keeps the current area. In replay it shows the recorded module, read-only. */
export function ModuleSelect() {
  const { module } = useApp();
  const replay = useReplay();
  const { options, current, select, experimental } = useSystems();
  const cov = experimental ? current.coverage : undefined;

  if (replay.active) {
    return (
      <div className="hmod">
        <div className="modctl modctl-replay" role="group" aria-label={`Module ${moduleName(module)} (recorded)`}>
          <span className="modctl-txt">
            <span className="modctl-k">Module</span>
            <span className="modctl-v">{moduleName(module)}</span>
          </span>
        </div>
      </div>
    );
  }
  return (
    <div className="hmod">
      <div className="modctl">
        <span className="modctl-txt" aria-hidden="true">
          <span className="modctl-k">Module</span>
          <span className="modctl-v">{current.label}</span>
        </span>
        <span className="modctl-chev" aria-hidden="true"><Icon name="keyboard_arrow_down" size="1.2em" /></span>
        <select className="modsel" aria-label="Module" value={module} onChange={(e) => void select(e.target.value)}>
          {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
        </select>
      </div>
      {cov ? (
        <span className="mappct" title={`${cov.verified} of ${cov.total} items verified`}>
          {coveragePct(cov)}%<span className="mappct-w"> mapped</span>
        </span>
      ) : null}
    </div>
  );
}
