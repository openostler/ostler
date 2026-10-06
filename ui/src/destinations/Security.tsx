// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

/**
 * Security (UI spec §3.4, §6): alarm state, events and the tracker map, present with any
 * node. Its registry entry requires a node in the capability manifest, which arrives in U5,
 * so in U1 the shell never shows it; this holds the slot so the registry is complete.
 */
export function Security() {
  return (
    <div className="stack">
      <div className="screen-head"><h2>Security</h2></div>
      <div className="empty"><div className="title">No node reported yet</div>
        <div className="pretty">The alarm and tracker appear when a node publishes its capability manifest.</div></div>
    </div>
  );
}
