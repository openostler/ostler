---
title: "Designer brief: App framework (part D): three worked setup flows"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, references/research/code_review_lubelogger.md, references/research/ha_integrations_dashboards.md]
summary: >
  Part D of the app-framework brief: the setup flow template of part C filled in three
  times. A vehicle pack integration, Land Rover Discovery 2 (Td5), found on the node,
  confirmed, given its source and its fitted systems (TD5, SLABS, BCU, ACE, EAT, SRS),
  contacted on K-line and summarised. A backend-only integration, the LubeLogger bridge,
  with only a setup page: server address and an Edit-scoped key with validation errors,
  vehicle mapping and what syncs. A feature app's first run, the Radio app finding its DAB
  receiver on the Brain, choosing a region and scanning for stations.
---

# App framework brief, part D: three worked setup flows

The frame, step kinds and rules: [part C](90-appframe-c.md). Every step below is drawn in
`app-flow-frame` and is Parked only on driver-facing displays. Values written ‹like this›
come from the car or the device; draw neutral sample text, never a fake reading.

## 1. Vehicle pack: Land Rover Discovery 2 (Td5)

The pack (`lr_d2`) is an integration loaded by the OS. Its flow runs from
Settings → Apps → Integrations, from a Discovered card, or inside first run, where the
onboarding brief draws steps 2–3 as `setup-vehicle-name` and `setup-source`.

| # | Screen id | Step kind | User does | Fails → recovery |
|---|---|---|---|---|
| 1 | `app-setup-d2-found` | Discovered | confirms the car the node found | no match → Generic OBD-II or "Help decode it" |
| 2 | `setup-vehicle-name` (onboarding) | Form | names the car, driver side | — |
| 3 | `setup-source` (onboarding) | Form | node, adapter or later | adapter only with no node ([ADR-0044][adr-44]) |
| 4 | `app-setup-d2-modules` | Form | ticks the systems this car has | unsure → "Find out" ticks all; Scan sorts it |
| 5 | `app-setup-d2-contact` | Hardware detect | parks, ignition on, waits | a module silent → "No response", continue |
| 6 | `app-setup-d2-done` | Success | reads the summary | partial → **Fix** |

### app-setup-d2-found — Discovery 2 found  [New]
- **Owner:** os (content from the `lr_d2` pack)
- **Purpose:** confirm that the car on the node is a Discovery 2 Td5.
- **Opens from → goes to:** the "New car found" card (`app-discovered`) **Add** → step 2.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Day.
- **Content (top to bottom):** 1. `directions_car` "Found: Land Rover Discovery 2 (Td5)".
  2. How: "On the node's K-line · TD5 engine ECU answered". 3. What: "Identity read from
  the ECU · SAL…****" with the line "Ostler never keeps the VIN." 4. Will be set up with:
  "Land Rover Discovery 2 (Td5)", Chip **Vehicle pack**, meta "K-line · 6 systems". 5.
  **Add** · **Ignore**.
- **States:** pack not installed: **Get the pack** (Store); two packs match: a choice list;
  car already set up: abort "Already set up" **Open it**; Moving: locked.
- **Safety and driving rules:** the identity read is a read, Parked; VIN masked
  ([ADR-0036][adr-36]).
- **Components:** Card, ListRow, Chip, Button.
- **Spec refs:** [UI §4.4][ui-4.4] · [UI §4.5][ui-4.5] · [HA integrations §4.1][ha-4.1] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-setup-d2-modules — Which systems this car has  [New]
- **Owner:** os (content from the `lr_d2` pack)
- **Purpose:** pick the fitted systems from the pack's list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. Intro "K-line talks to one system at a time. Tick the
  ones your car has." 2. ListRows with a tick, pack order, each with a one-line note:
  **TD5 (engine)** "45 live values, faults, tests" (ticked, fixed); **SLABS (ABS + air
  suspension)** "Ride heights, faults, tests"; **BCU (body control)** "Faults not mapped
  yet"; **ACE (active cornering)** "Optional on the D2"; **EAT (auto gearbox)** "Automatic
  cars only"; **SRS (airbag)** "Read only. Faults only." 3. Link **Not sure? Find out** →
  ticks all; Scan all marks the silent ones "Not fitted" for you to confirm. 4. **Continue**.
- **States:** a system with no live data shows Chip "Not supported yet" (BCU, ACE, EAT);
  Moving: locked.
- **Safety and driving rules:** nothing is sent in this step.
- **Components:** ListRow (tick), Chip, SchemaForm (new).
- **Spec refs:** [UI §4.2–4.3][ui-4.3] · [UI §5.1][ui-5.1] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-setup-d2-contact — First contact on K-line  [New]
- **Owner:** os (content from the `lr_d2` pack)
- **Purpose:** prove the source reaches each system, honestly.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. Checklist ticked from live data: "Parked", "Ignition on",
  "Battery ‹V›, above the floor". 2. Rows per system: name, Chip `Waiting` → `Talking` →
  `OK` (`ok`) or `No response` (`warn`) or `Not supported yet`; "TD5 · fast init · OK",
  "SLABS · fast init · OK", "SRS · slow init · OK". 3. Caption "One system at a time on
  K-line." 4. **Continue**, enabled when TD5 answered; **Try again** on a silent row.
- **States:** bus silent: `ia-error-bus-silent`; node offline: `ia-error-node-offline`; a
  module refuses: its row `warn` with the reason; engine running not needed; Moving:
  locked and the check stops.
- **Safety and driving rules:** reads only, Parked, through the node's gate (or the
  adapter's soft gate with no node) ([ADR-0044][adr-44]).
- **Components:** Checklist (new), ListRow, Chip (status), Button.
- **Spec refs:** [UI §4.3][ui-4.3] · [UI §4.5][ui-4.5] · [Adapters §7][sa-7] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-setup-d2-done — Discovery 2 set up  [New]
- **Owner:** os (content from the `lr_d2` pack)
- **Purpose:** summarise the car, its source and its systems.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Day.
- **Content (top to bottom):** 1. "Discovery 2 Td5 is set up". 2. Rows: "Source: Ostler
  Diagnostics node · local, live"; "Systems: TD5, SLABS, SRS answered · ACE not fitted";
  "Live values: TD5 45, SLABS 18 (wheel speeds candidate)". 3. Next: **Build a dashboard**
  (→ the dashboard builder with the Off-road (D2) preset suggested), **Open Diagnostics**
  (if installed, else **Get Diagnostics**). 4. **Finish**.
- **States:** partial: "BCU: No response" in `warn` with **Fix** (back to step 5); no
  Diagnostics app: Card "Install Diagnostics to read faults and live data"; Moving: locked.
- **Safety and driving rules:** none beyond Parked.
- **Components:** ListRow, Card, Button.
- **Spec refs:** [HA integrations §5][ha-5] (C14, push or poll shown) · [Drive modes §5.9][dm-5.9] · [app UI model §6][ua-6].
- **Open questions:** none.

## 2. Backend-only integration: the LubeLogger bridge

The bridge (`ostler-app-lubelogger`, optional, off by default) has no pages: App info and
this setup page are all it shows. It needs the Maintenance app ([Maintenance §11][mg-11]).

| # | Screen id | Step kind | User does | Fails → recovery |
|---|---|---|---|---|
| 1 | `app-setup-lube-server` | Form | enters the server address and an API key | unreachable, key refused, view-only key, sign-in off → inline errors |
| 2 | `app-setup-lube-sync` | Form | maps the car, picks what syncs | no vehicles on the server → "Add one in LubeLogger first" |
| 3 | `app-flow-success` | Success | "LubeLogger bridge is set up · Discovery 2 Td5 ↔ ‹vehicle›" | — |

### app-setup-lube-server — LubeLogger server  [New]
- **Owner:** os (content from the LubeLogger bridge)
- **Purpose:** connect to the owner's own LubeLogger with a key that can edit.
- **Opens from → goes to:** after install, App info **Configure** → step 2.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** phone Night
  with each error, tablet Night.
- **Content (top to bottom):** 1. Intro "Keep Maintenance and your LubeLogger in step."
  2. **Server address** Text field, help "On your network or over Tailscale". 3. **API key**
  secret field, help "In LubeLogger, make a key with Edit permission." 4. Errors:
  "Can't reach ‹address›."; "LubeLogger refused this key."; "This key can only view.
  Make one with Edit permission."; `warn` Card "Sign-in is off on this server. Anyone on
  your network can change it." with **Continue anyway** · **Cancel**. 5. **Continue**.
- **States:** checking; ok → step 2; remote path other than Tailscale: refused; Moving:
  locked.
- **Safety and driving rules:** the key lives in the Brain's secret store and is sent only
  as a header; the bridge never touches the car.
- **Components:** Text field (secret), Card (tone), Button, SchemaForm (new).
- **Spec refs:** [Maintenance §11][mg-11] · [LubeLogger review §5][lube-5] · [app UI model §6][ua-6].
- **Open questions:** none.

### app-setup-lube-sync — Car and what syncs  [New]
- **Owner:** os (content from the LubeLogger bridge)
- **Purpose:** map each car and choose the directions.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Per car: "Discovery 2 Td5 → " a choice of the server's
  vehicles (‹names from the server›) or "Don't sync". 2. Switches: "Send odometer and engine
  hours at trip end"; "Bring reminders into Due"; "Turn a confirmed fault into a Critical
  plan" (per car, off by default). 3. Card: "Sends: the `maintenance` data of the cars you
  map, to ‹address›. Never location, never the VIN." 4. **Continue**.
- **States:** server has no vehicles; Maintenance not installed (abort "Needs Maintenance");
  Moving: locked.
- **Safety and driving rules:** what leaves is named by its data class
  ([Accounts §14.1][acc-14.1]).
- **Components:** ListRow, Switch (new), Card, Button.
- **Spec refs:** [Maintenance §11][mg-11] · [Accounts §14.1][acc-14.1] · [app UI model §6][ua-6].
- **Open questions:** is sending to the owner's own server a grant to record in Sharing?

## 3. Feature app first run: Radio finds its DAB receiver

Radio (owner `app:radio`) plays DAB+ through a receiver on the Brain. Its tuner pages are
drawn in `80-hu-*`; this is only its first run.

| # | Screen id | Step kind | User does | Fails → recovery |
|---|---|---|---|---|
| 1 | `app-setup-radio-detect` | Hardware detect | plugs the receiver into the Brain | not found → checklist, **Check again** |
| 2 | `app-setup-radio-scan` | Form + progress | picks region, scans | nothing found → antenna tip, **Scan again** |
| 3 | `app-flow-success` | Success | "Radio is set up · ‹n› stations"; Next: **Add the Radio widget** | — |

### app-setup-radio-detect — Find the radio receiver  [New]
- **Owner:** app:radio
- **Purpose:** find a DAB+ receiver on the Brain.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night (found,
  not found), phone Night.
- **Content (top to bottom):** 1. "Looking for a radio receiver on the Brain".
  2. Found row: `radio` "Si468x tuner HAT · I²C" (the first tuner path, item 36) or "USB
  DAB+ receiver · USB port ‹n›", Chip `ok` "Ready". 3. Not
  found: checklist "Plugged into the Brain?", "Aerial connected?"; **Check again**.
- **States:** Brain asleep: "Needs the Brain" with **Wake**; no Brain (Diagnostics alone):
  abort "Radio needs the Brain"; Moving: locked.
- **Safety and driving rules:** Parked; the receiver is not a car bus device.
- **Components:** as `app-flow-hardware`.
- **Spec refs:** [App model §13][am-13] (`needs_brain`) · [App model §4.4][am-4.4] · [app UI model §4][ua-4] · [head-unit apps §3][hu-3].
- **Open questions:** **Decided (item 36):** the first supported receiver is an Si468x-based
  HAT or module (DAB+ decoded in hardware); a USB SDR dongle comes second.

### app-setup-radio-scan — Region and scan  [New]
- **Owner:** app:radio
- **Purpose:** choose region, scan Band III, show progress.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night scanning.
- **Content (top to bottom):** 1. **Region** choice (prefilled from Units and region).
  2. Switch "Also FM, if the receiver has it". 3. **Scan** → progress bar "Scanning Band III
  · channel ‹5A–13F›" and a counter "‹n› stations". 4. **Continue** when done.
- **States:** none found ("Try near a window or check the aerial", **Scan again**); stopped
  by Moving: resumes when Parked; Moving: locked.
- **Safety and driving rules:** Parked only; while Moving later, Radio uses only the `media`
  template ([UI §12.1][ui-12.1]).
- **Components:** Segmented or list (region), Switch (new), progress bar (new), Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [App model §15][am-15] (widgets) · [app UI model §4][ua-4] · [head-unit apps §3][hu-3].
- **Open questions:** none.

<!-- refs -->
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[adr-36]: ../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md
[adr-44]: ../../../../decisions/adr-0044-adapters-on-the-brain-without-a-node.md
[am-13]: ../../../../specs/2026-10-06-app-model-design.md#13-power-states-wake-and-queued-actions-accepted-2026-10-06
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[ha-4.1]: ../../../../references/research/ha_integrations_dashboards.md#41-entities-devices-and-areas
[ha-5]: ../../../../references/research/ha_integrations_dashboards.md#5-copy--avoid--decide-for-ostler
[lube-5]: ../../../../references/research/code_review_lubelogger.md#5-http-api
[mg-11]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#11-later
[sa-7]: ../../../../specs/2026-10-07-source-adapters-design.md#7-safety-with-no-hardware-gate
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-5.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#51-shape
[ua-6]: ../../../../specs/2026-10-07-app-ui-model-design.md#6-backend-only-apps-integrations
[ua-4]: ../../../../specs/2026-10-07-app-ui-model-design.md#4-the-setup-flow
[hu-3]: ../../../../specs/2026-10-07-head-unit-apps-design.md#3-radio
