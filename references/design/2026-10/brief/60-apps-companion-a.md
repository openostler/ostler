---
title: "Designer brief — Companion phone app: connect, home, car status, remote access and alarm alerts"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Page content for the companion phone app (one store app per platform, Android and iOS): the
  native parts that are fixed in the binary and the frames around the Ostler OS it loads from the
  user's Brain or Ostler Cloud. Covers connecting and pairing (Brain, or the node alone on Ostler
  Diagnostics), the companion home (proposed), car status from the node's retained data, remote
  access over Tailscale or the relay (read-only, with the wake sheet and quota), and alarm alerts
  that reach the phone with the Brain off. States, rules and components.
---

# Companion phone app, part a

Example numbers and names in quotes are label formats, not data.

The companion app is the phone's way into Ostler, the way Home Assistant's companion app works:
with a Brain or Ostler Cloud reachable it loads the OS and apps from that server; offline with
only a node it uses its bundled shell ([App model §7.1](../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build)). **Native and fixed in the binary:** BLE and
local Wi-Fi to the node, push, background location, pairing and Tier 2–3 approval over local
links ([ADR-0042](../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) decision 3). It never loads third-party code. Part b:
[60-apps-companion-b.md](60-apps-companion-b.md). The bridge setup is `phone-bridge-setup`.

**Connect (flow).**

| Step | Screen | The user does | Can fail · recovery |
|---|---|---|---|
| 1 | companion-connect | picks "My car has a Brain" or "Just the Ostler node" | nothing found: "Turn the ignition on, be near the car" |
| 2 | companion-connect | scans the Brain's QR or presses the node's button / enters its label code | wrong code: tries left; timeout: retry |
| 3 | accounts-s1 or accounts-s2 | creates the owner (first run) or signs in | lost owner: console reset on a Brain; node re-pair on Diagnostics alone |
| 4 | companion-notifications | allows notifications (alarm alerts first) | denied: banner "Alarm alerts are off" stays |
| 5 | companion-home | lands | — |

### companion-connect — Connect to your car  [New]
- **Owner:** os
- **Purpose:** find and pair with the Brain or the node, then sign in.
- **Opens from → goes to:** first launch; Settings → Cars → "Add a car" → accounts-s1 or s2 →
  companion-notifications → companion-home.
- **Layout classes:** phone. **Draw first:** phone Night and Day.
- **Content (top to bottom):**
  1. Choice: "My car has an Ostler Brain" · "Just the Ostler node (Ostler Diagnostics)".
  2. Brain: "Scan the code on the car screen" (camera) or "Enter the address"; found devices
     list by the name the owner advertises.
  3. Node: "Press the button on the node, or enter the code on its label", BLE search with
     "Looking for your node…".
  4. Pinned key line: "Connected securely to ostler-xxxx.local".
- **States:** loading: search spinner · nothing found · Bluetooth off: "Turn on Bluetooth" ·
  location permission needed for BLE (Android) · Moving: phone Moving banner; allowed as a
  passenger device.
- **Safety and driving rules:** pairing is a physical step at the car ([Accounts §2.1](../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap)).
- **Components:** Card, ListRow, Button, QRCode.
- **Spec refs:** [Accounts §2.1](../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap) · [Accounts §14.10](../../../../specs/2026-10-06-accounts-sharing-design.md#1410-where-authdb-lives-and-recovery) · [App model §7.1](../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build)

### companion-home — Companion home  [Proposed]
- **Owner:** os
- **Why the app needs it:** before the OS's own Home loads from the Brain, the phone needs a
  native start that shows which car and which link it is on, and works when no server answers.
- **Purpose:** the phone's start: pick the car, see the link, then the car's Home.
- **Opens from → goes to:** app launch → the Home served by the Brain (phone layout), or
  companion-car-status when only the node or cached data is reachable; car switcher.
- **Layout classes:** phone. **Draw first:** phone Night and Day; phone Night offline.
- **Content (top to bottom):**
  1. Car switcher row: "Discovery" with the link Chip (Car Wi-Fi · LAN · Tailscale · Relay ·
     Bluetooth to node · Offline).
  2. The car's Home (from the server) below, or the car-status card set when offline.
  3. Bottom dock (the OS's dock, phone layout).
- **States:** loading: "Connecting to Discovery…" · offline: cached cards with ages · Brain
  asleep: "Brain asleep · Wake" on remote paths · no car: companion-connect.
- **Safety and driving rules:** phone Moving banner while Moving ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Chip (link), Card, TabBar (dock).
- **Spec refs:** [App model §7.1](../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build) · [UI §3.8](../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06)

### companion-car-status — Car status (from the node)  [New]
- **Owner:** os
- **Purpose:** the essentials from the node's retained data, Brain or not.
- **Opens from → goes to:** companion-home offline; a push → the alarm or fault detail.
- **Layout classes:** phone. **Draw first:** phone Night (Brain asleep); phone Day.
- **Content (top to bottom):**
  1. Security: "Armed · since 22:10" or "Alerting" (alarm token, icon and word).
  2. Last position on a small map with age "updated 6 min ago", or "Location off".
  3. 12 V "12.5 V" with age; worst telltale "2 faults · Warning".
  4. Last trip row (if the Trips app is installed).
  5. Node power line: "Node asleep (deep) · wakes on ignition, door or motion · last seen
     3 h" when unreachable.
- **States:** stale values grey with their age, missing as "—" · loading · offline (cached) ·
  Moving: banner; view-only.
- **Safety and driving rules:** remote paths are read-only; arming and disarm need Security
  rights and are audited ([ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override)).
- **Components:** Card, StatTile, Chip (status), Sheet over map.
- **Spec refs:** [UI §3.8](../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06) · [ADR-0033 §7](../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths) · [ADR-0032](../../../../decisions/adr-0032-one-node-optional-brain.md)

### companion-remote — Remote access to the car  [New]
- **Owner:** os
- **Purpose:** reach the car away from it, read-only, and wake the Brain within the quota.
- **Opens from → goes to:** companion-home link Chip → this sheet; any action on a remote path
  → the wake sheet or the refusal.
- **Layout classes:** phone. **Draw first:** phone Night (remote, Brain asleep wake sheet);
  phone Night (read-only banner).
- **Content (top to bottom):**
  1. Link list: Car Wi-Fi · Home LAN · Tailscale "ostler-xxxx.ts.net" · Ostler Cloud relay;
     current one ticked with latency.
  2. Banner on remote paths: "Remote: view only. Arming and disarming the alarm work; other
     actions need you at the car."
  3. Wake sheet: "This needs the Brain. Wake it? About 30 s · uses about 30 mAh (today: 180 mAh
     left) · battery 12.5 V" with **Wake and run**, **Cancel**, "2 of 6 remote wakes left today".
  4. Refusals: "Brain not woken: battery 11.9 V", "Limit reached: 6 wakes this hour".
  5. If the install override is on: persistent "Remote control enabled" badge.
- **States:** no remote path set up: "Set up remote access in Settings → Network" · relay
  down · Moving: n/a (away from the car).
- **Safety and driving rules:** remote paths read-only plus arm and disarm, audited; the wake
  sheet cannot be skipped ([ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override), [UI §3.8](../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06), [UI §7.2](../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033)).
- **Components:** ListRow, Sheet, Button, Chip.
- **Spec refs:** [ADR-0033 §6](../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override) · [UI §3.8](../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06) · [UI §7.2](../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033)

### companion-alarm-alert — Alarm alert on the phone  [New]
- **Owner:** os
- **Purpose:** the alarm reaches the phone even with the Brain off and no internet.
- **Opens from → goes to:** a push or local-link notification → full-screen alert → Security
  app page (if installed) or companion-car-status.
- **Layout classes:** phone. **Draw first:** phone Night (lock-screen notification and
  full-screen alert); phone Day.
- **Content (top to bottom):**
  1. Notification: "Discovery: alarm · door opened · 02:14", alarm icon and word.
  2. Full screen: alarm state "Alerting", event list, last position with age, 12 V.
  3. Buttons: "Disarm" (needs Security rights, audited), "Call 999" (opens the phone dialer),
     "View position".
  4. Via line: "Sent by the node over SMS" or "over the car Wi-Fi".
- **States:** delivered late: "Sent 02:14 · received 02:20" · no position: "No fix".
- **Safety and driving rules:** alarm alerts cannot be removed or hidden; they never wait for the
  Brain ([ADR-0033 §7](../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths), [Drive modes §8.1](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules)).
- **Components:** alert_card, Card, Button, Chip (status).
- **Spec refs:** [ADR-0033 §7](../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths) · [ADR-0032](../../../../decisions/adr-0032-one-node-optional-brain.md) · [Drive modes §8.1](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules)
