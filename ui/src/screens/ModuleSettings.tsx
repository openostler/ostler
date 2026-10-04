import { useState } from "react";
import type { CommandReply } from "../api/schemas";
import { ConnectionNotice } from "../components/ConnectionNotice";
import { CoverageBar } from "../components/CoverageBar";
import { ItemCard } from "../components/ItemCard";
import { PlaceholderReadout } from "../components/PlaceholderReadout";
import { ScreenHead } from "../components/ScreenHead";
import { StatusTag } from "../components/StatusTag";
import { identityRows, isPlaceholder, pageOf, STABLE_EMPTY, visibleGroups } from "../lib/catalog";
import { useApp } from "../state/app";

/** The module's Settings page (catalog page "settings"): identity and configuration,
 * read-only. The identity Read (read_identity) shows what the ECU returns, with the VIN
 * masked — the full VIN is never shown. */
export function ModuleSettings() {
  const { catalog, experimental, snap } = useApp();
  const [identity, setIdentity] = useState<[string, string][] | null>(null);
  const page = pageOf(catalog, "settings");
  const groups = visibleGroups(page, experimental);
  const connected = snap?.status === "connected";
  const onResult = (r: CommandReply) => {
    if ("identity" in r) setIdentity(identityRows(r.identity));
  };

  return (
    <>
      <ScreenHead title="Settings" />
      <ConnectionNotice />
      {experimental && page ? <CoverageBar coverage={page.coverage} label="Settings coverage" /> : null}
      {!catalog ? <div className="empty">Loading…</div> : !groups.length ? (
        <div className="empty"><div className="pretty">{experimental ? "Nothing catalogued here yet." : STABLE_EMPTY}</div></div>
      ) : groups.map(({ group, items }) => (
        <section key={group.id}>
          <div className="kicker group-title">{group.title}</div>
          <div className="grid">
            {items.map((i) => {
              if (i.actions.length) {
                return <ItemCard key={i.id} item={i} disabled={!connected} onResult={onResult} />;
              }
              if (isPlaceholder(i)) return <PlaceholderReadout key={i.id} item={i} />;
              return (
                <div className="card item" key={i.id} data-item={i.id}>
                  <div className="row" style={{ gap: 8 }}>
                    <span className="grow item-name">{i.name}</span>
                    {experimental ? <StatusTag status={i.status} /> : null}
                  </div>
                  {i.ref ? <div className="small dis mono">{i.ref}</div> : null}
                  {i.note ? <div className="small muted pretty">{i.note}</div> : null}
                </div>
              );
            })}
          </div>
        </section>
      ))}
      {identity ? (
        <div className="card" role="region" aria-label="Identity">
          <div className="kicker" style={{ marginBottom: 8 }}>Identity (read from the ECU)</div>
          {identity.length ? (
            <dl className="kv">
              {identity.map(([k, v]) => <div key={k} style={{ display: "contents" }}><dt>{k.replace(/_/g, " ").toUpperCase()}</dt><dd className="mono">{v}</dd></div>)}
            </dl>
          ) : <span className="dis">The ECU returned no identity fields.</span>}
        </div>
      ) : null}
    </>
  );
}
