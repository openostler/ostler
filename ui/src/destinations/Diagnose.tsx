// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { ComponentType } from "react";
import { ModuleSelect } from "../components/ModuleSelect";
import { getPack } from "../pack/store";
import { Faults } from "../screens/Faults";
import { Inputs } from "../screens/Inputs";
import { ModuleSettings } from "../screens/ModuleSettings";
import { Outputs } from "../screens/Outputs";
import { Utilities } from "../screens/Utilities";
import { useShell } from "../shell/context";
import type { LayoutClass } from "../shell/layoutClass";
import { DIAGNOSE_AREAS, viewOf, type DiagnoseArea } from "../shell/routes";
import { useApp } from "../state/app";
import { useReplay } from "../state/replay";
import { useSystems, type SystemOption } from "../state/systems";

/**
 * Diagnose (UI spec §3.4, §4.2): the identity bar, the system list and the function areas of
 * the system in session, holding today's Faults, Inputs, Outputs, Utilities and Settings
 * screens. Module select moved here from the header. On HU-9/10, HU-wide, tablet and desktop
 * the system list sits beside the detail; on HU-7 and the phone a compact switcher in the
 * identity bar replaces it. With one system there is no system level (§4.2 collapse rule).
 */
const AREA_SCREENS: Record<DiagnoseArea, ComponentType> = {
  faults: Faults,
  live: Inputs,
  tests: Outputs,
  procedures: Utilities,
  settings: ModuleSettings,
};

/** Today's names for the canonical areas (the D2's NanoCom words, ADR-0018 Q2). A pack may
 * relabel them with `layout.areas`; the capability manifest carries them per system in U3. */
const AREA_LABELS: Record<DiagnoseArea, string> = {
  faults: "Faults",
  live: "Inputs",
  tests: "Outputs",
  procedures: "Utilities",
  settings: "Settings",
};

function areaLabel(area: DiagnoseArea): string {
  const labels = (getPack()?.layout as { areas?: Partial<Record<DiagnoseArea, unknown>> } | undefined)?.areas;
  const l = labels?.[area];
  return typeof l === "string" && l ? l : AREA_LABELS[area];
}

/** Classes wide enough for the list pane (§3.1: "Diagnose = list 380 + detail"). */
const LIST_PANE: ReadonlySet<LayoutClass> = new Set(["hu9", "huwide", "tablet", "desktop"]);

export function Diagnose() {
  const { nav, layout } = useShell();
  const systems = useSystems();
  const v = viewOf(nav.route);
  const area: DiagnoseArea = (DIAGNOSE_AREAS as readonly string[]).includes(v ?? "") ? (v as DiagnoseArea) : "faults";
  const listPane = LIST_PANE.has(layout) && systems.multi;
  const Screen = AREA_SCREENS[area];
  return (
    <div className={`diag${listPane ? " diag-split" : ""}`}>
      {listPane ? <SystemList options={systems.options} current={systems.current.id} onSelect={systems.select} /> : null}
      <div className="diag-detail stack">
        <IdentityBar compact={!listPane && systems.multi} name={systems.current.label} />
        <nav className="areas" aria-label="Areas">
          {DIAGNOSE_AREAS.map((a) => (
            <button key={a} className="area-tab" aria-current={a === area ? "page" : undefined}
              onClick={() => nav.open(`diagnose.${a}`)}>{areaLabel(a)}</button>
          ))}
        </nav>
        <Screen />
      </div>
    </div>
  );
}

/** The identity bar: the system in session, with the compact switcher where there is no list. */
function IdentityBar({ compact, name }: { compact: boolean; name: string }) {
  return (
    <div className="diag-id">
      {compact ? <ModuleSelect /> : <div className="diag-sysname"><span className="modctl-k">System</span> {name}</div>}
    </div>
  );
}

/** The flat system list (2–12 systems, §4.2). Selecting one moves the ECU session to it. */
function SystemList({ options, current, onSelect }: {
  options: SystemOption[]; current: string; onSelect: (id: string) => Promise<void>;
}) {
  const { snap } = useApp();
  const replay = useReplay();
  return (
    <nav className="syslist" aria-label="Systems">
      <div className="kicker">Systems</div>
      {options.map((o) => {
        const on = o.id === current;
        const faults = on && snap?.status === "connected" ? snap.faults.length : null;
        return (
          <button key={o.id} className="sysrow" aria-current={on ? "true" : undefined} disabled={replay.active && !on}
            onClick={() => void onSelect(o.id)}>
            <span className="sysrow-name">{o.label}</span>
            <span className="sysrow-state small">
              {!on ? "" : replay.active ? "Recorded" : faults === null ? "Selected"
                : faults ? `${faults} fault${faults > 1 ? "s" : ""}` : "In session"}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
