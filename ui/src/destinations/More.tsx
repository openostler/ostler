// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { ComponentType } from "react";
import { Icon, type SymbolName } from "../icons/Icon";
import { Capture } from "../screens/Capture";
import { CoverageMap } from "../screens/CoverageMap";
import { Docs } from "../screens/Docs";
import { useShell, type ShellSheet } from "../shell/context";
import type { RouteName } from "../shell/routes";

/**
 * More (UI spec §3.4): Preferences (the header cog before U1) and Connection, and, on
 * /admin, **Developer** with today's admin pages (Decode, Label, Docs). Garage, Network,
 * Integrations and Privacy arrive with their phases (U5, U6); service mode replaces /admin
 * in U2.
 */
type DeveloperPage = { route: RouteName; label: string; icon: SymbolName; component: ComponentType };

const DEVELOPER_PAGES: DeveloperPage[] = [
  { route: "more.decode", label: "Decode", icon: "swap_horiz", component: CoverageMap },
  { route: "more.label", label: "Label", icon: "edit_note", component: Capture },
  { route: "more.docs", label: "Docs", icon: "description", component: Docs },
];

export function More() {
  const { nav, session } = useShell();
  const page = session.admin ? DEVELOPER_PAGES.find((p) => p.route === nav.route) : undefined;
  if (page) return <Developer page={page} />;
  return (
    <div className="more stack">
      <div className="screen-head"><h2>More</h2></div>
      <div className="morelist">
        <SheetRow sheet="preferences" icon="settings" label="Preferences" hint="Trust, sharing, display, units, recording" />
        <SheetRow sheet="connection" icon="cable" label="Connection" hint="Port, link and adapter" />
      </div>
      {session.admin ? (
        <section className="stack" aria-labelledby="more-dev">
          <h3 id="more-dev" className="kicker group-title">Developer</h3>
          <div className="morelist">
            {DEVELOPER_PAGES.map((p) => (
              <button key={p.route} className="morerow" onClick={() => nav.open(p.route)}>
                <Icon name={p.icon} /><span className="grow">{p.label}</span><Icon name="chevron_right" />
              </button>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function SheetRow({ sheet, icon, label, hint }: { sheet: ShellSheet; icon: SymbolName; label: string; hint: string }) {
  const { sheets } = useShell();
  return (
    <button className="morerow" aria-haspopup="dialog" onClick={() => sheets.open(sheet)}>
      <Icon name={icon} />
      <span className="grow morerow-txt"><span>{label}</span><span className="small muted">{hint}</span></span>
      <Icon name="chevron_right" />
    </button>
  );
}

/** A developer page under More, with its siblings one tap away. */
function Developer({ page }: { page: DeveloperPage }) {
  const { nav } = useShell();
  const Page = page.component;
  return (
    <div className="stack">
      <div className="subnav">
        <button className="btn subnav-back" onClick={() => nav.open("more")}>‹ More</button>
        <nav className="seg" aria-label="Developer">
          {DEVELOPER_PAGES.map((p) => (
            <button key={p.route} aria-current={p.route === page.route ? "page" : undefined}
              onClick={() => nav.open(p.route)}>{p.label}</button>
          ))}
        </nav>
      </div>
      <Page />
    </div>
  );
}
