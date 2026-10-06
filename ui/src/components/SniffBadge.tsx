// SPDX-FileCopyrightText: 2026 OpenOstler contributors
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import type { SniffState } from "../api/useSniff";

/** Freshness of the passive sniff feed (ESP32 tap listening to the NanoCom), in one line. */
export function SniffBadge({ sniff, showActive = true }: { sniff: SniffState; showActive?: boolean }) {
  const d = sniff.data;
  let cls = "";
  let text: string;
  if (sniff.error) {
    cls = "red";
    text = `Cannot reach the sniff feed: ${sniff.error}`;
  } else if (!d) {
    text = "Checking for a sniff tap…";
  } else if (!sniff.configured) {
    text = "No tap connected — the homelab runs a demo feed";
  } else if (d.status === "error") {
    cls = "red";
    text = `The sniff tap reported an error: ${d.error ?? "unknown"}`;
  } else if (d.status === "live" && d.age != null && d.age < 3) {
    cls = "green";
    const demo = sniff.demo ? " · demo feed (recorded)" : "";
    const polling = showActive && sniff.active.size ? ` · NanoCom is reading ${[...sniff.active].slice(0, 6).join(" ")}` : "";
    text = `Listening · ${sniff.fps} lines/s · ${d.frames ?? 0} reads${polling}${demo}`;
  } else if (d.age != null) {
    cls = "yellow";
    text = `Nothing heard for ${d.age}s — is the tap plugged in and the NanoCom showing a live screen?`;
  } else {
    text = `Tap connected, waiting for the NanoCom to ask for data… (${(d.source ?? "").replace(/^serial:/, "")})`;
  }
  return (
    <span className="row small" style={{ gap: 6 }} role="status">
      <span className={`pdot ${cls}`} />
      <span className={cls ? "" : "dis"}>{text}</span>
    </span>
  );
}
