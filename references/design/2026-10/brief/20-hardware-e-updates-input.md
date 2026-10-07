---
title: "Designer brief: hardware (e) — node firmware and Brain A/B updates; remotes, gamepads, buttons and the key test"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-shell-input-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, references/research/power_states.md, references/research/hardware.md]
summary: >
  Covers the proposed node firmware update (signed image, preconditions, download, verify,
  write with stepped progress, restart, a health check with a real test read, automatic and
  manual rollback) and the proposed Brain A/B system update (install to the idle slot,
  switch at next start, fall back if the new slot fails). Then the input screens of the
  shell-input spec phase I2: a display's Buttons page (intents, "press the key now" capture,
  sources: keyboard, Bluetooth remotes, gamepads, pack buttons; Reset to defaults) and the
  key test, which ticks every intent including the long OK (600 ms) that enters edit mode
  and arrow repeat, until "All buttons OK". Updates and bindings are Parked only and local.
---

# Hardware brief (e): updates, remotes and buttons

Shared rules are in [file (a)](20-hardware-a-devices.md#rules-every-hardware-page-follows).
**Why the update screens are Proposed:** ADR-0032 lists signed OTA as a node security need
and ADR-0040 gives OTA a 30 min lease, but no approved spec draws an update, its progress or
its rollback. A failed flash on the device that holds the car's only gate needs an honest,
recoverable flow.

## Firmware update: step list

| # | Stage (on `hw-firmware-update`) | What can fail | Recovery |
|---|---|---|---|
| 1 | Check: version, signature, notes | no update; unsigned image | nothing to do; refused, never offered |
| 2 | Preconditions | not Parked; 12 V below 12.2 V; metered data cap reached; a test running | park; charge; use another uplink; stop the test |
| 3 | Download and verify | link lost; signature fails | resumes; image discarded, "Not installed" |
| 4 | Write | power lost | the device keeps its old firmware |
| 5 | Restart and health check | new firmware does not report; K-line init fails | automatic rollback to the previous version |
| 6 | Done | — | **Roll back** stays available |

### hw-firmware-update — Update device firmware  [Proposed]
- **Owner:** os
- **Purpose:** update a node, Guardian or module safely, with progress and a way back.
- **Opens from → goes to:** `network-device` → Update firmware; an "Update available" row
  on Network. Back to the device page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (stages 2, 4, 5), hu7 Night (stage 4).
- **Content (top to bottom):**
  1. Header: device, "Installed ‹version›", "Available ‹version› · signed".
  2. Release notes (short list), "What changes for your car" line.
  3. **Before you start** checklist rows with status words: Parked, engine off; 12 V above
     12.2 V; uplink not over its cap; no test or procedure running; "The alarm stays on the
     Guardian" or, with no Guardian, "The alarm is off while Ostler Diagnostics restarts".
  4. **Update** (primary) and **Cancel**.
  5. Progress rows, stepped with words and a percentage in text: Downloading, Verifying
     signature, Writing, Restarting, Checking (manifest, K-line init, one test read).
  6. Result: "Updated to ‹version›" or "Rolled back to ‹version› · reason"; **Roll back**
     (secondary) for the last version.
- **States:** up to date; refused (with the reason); in progress (screen stays awake; Back
  asks "Leave? The update carries on"); rolled back (warn); device asleep ("Wake it first").
- **Safety and driving rules:** Parked with the engine off, local links only, owner role;
  refused when the drive state changes. The device's gate stays shut (listen-only) until the
  health check passes. Confirm opens with Cancel focused.
- **Components:** Card, ListRow (check and progress rows), Button, Sheet (confirm),
  ProgressRow (new component: label, stepped percentage text, no animated bar while Moving).
- **Spec refs:** [ADR-0032 Risks][a32r], [ADR-0040 §4.5][a40-4] (OTA lease),
  [ADR-0028][a28] (metered uplinks), [UI §3.5][ui35].
- **Open questions:** where signed images come from, and whether a node may update from the
  phone alone (Ostler Diagnostics) or only through the Brain.

### hw-brain-update — Brain system update (A/B)  [Proposed]
- **Owner:** os
- **Purpose:** update the Brain's system without risking a car that will not start its app.
- **Opens from → goes to:** `hw-brain` → Update. Back to `hw-brain`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** tablet
  Night, phone Day.
- **Content (top to bottom):** 1. **Slots** card: "Running: slot A · ‹version›", "Idle: slot B
  · ‹version›". 2. Update row: "Available ‹version›", size, "Downloads in the background on
  unmetered links". 3. **Install** (to the idle slot while the Brain runs), progress rows.
  4. "Ready · switches at the next start" with **Restart now** (Parked) and **Later**.
  5. After the switch: "Running slot B · checking"; then "Kept" or "Went back to slot A ·
  the new system did not start". 6. **Vehicle packs** row: "Pack updates are signed and need
  no restart".
- **States:** downloading paused (metered or over cap); install failed (slot B untouched);
  fallback happened (warn with reason, Logs link).
- **Safety and driving rules:** Restart now is Parked only and never while a Trip is being
  written; local only.
- **Components:** Card, ListRow, ProgressRow (new component), Button.
- **Spec refs:** [ADR-0032 Risks][a32r], [hardware research: Pi robustness][hw-p],
  [ADR-0040 §4.5][a40-4].

### shell-buttons — Display Buttons: bindings and sources  [Existing]
- **Owner:** os
- **Purpose:** set which key, remote button, gamepad control or pack button drives each
  intent on this display.
- **Opens from → goes to:** Network → *the display's device page* → Buttons. Goes to
  `hw-buttons-key-test`, the capture sheet, Reset confirm.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, hu5 Night, desktop Day.
- **Content (top to bottom):**
  1. **Sources** card: Keyboard (always), "Remotes · paired in this display's Bluetooth
     settings", "Gamepad · press any button to connect", "Pack buttons · appear when a device
     publishes them" (phase I3).
  2. **Bindings** table, one ListRow per intent: Up, Down, Left, Right, OK, Back, Menu, Mark,
     Zoom in, Zoom out, Push to talk; current binding, its source icon and word, and an
     optional long-press binding. Tap → capture Sheet "Press the key now" with **Cancel**.
  3. Fixed row: "Long OK (600 ms) opens edit mode · cannot be removed".
  4. **Test buttons** (primary) → `hw-buttons-key-test`; **Reset to defaults** (secondary,
     confirm).
- **States:** capture waiting; conflict ("Already bound to Back · Swap?"); no remote; Idling
  full with Park evidence; Moving locked view, "Available when parked"; remote hidden.
- **Safety and driving rules:** bindings belong to the display's install configuration;
  only the owner or a signed-in driver edits them, Parked only; a user's preferences never
  change a driver-facing display's bindings while Moving ([Shell input §8][si8]).
- **Components:** ListRow, Sheet, Chip (source), Button, Card.
- **Spec refs:** [Shell input §2][si2], [Shell input §3][si3], [Shell input §8][si8],
  [Shell input §14][si14].

### hw-buttons-key-test — Key test  [New]
- **Owner:** os
- **Purpose:** prove every button arrives as the right intent, with no game.
- **Opens from → goes to:** `shell-buttons` → Test buttons; `hw-install-done` for a head
  unit. Back to `shell-buttons`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (half done), hu5 Night ("All buttons OK").
- **Content (top to bottom):** 1. Title "Press each button". 2. A grid of Chips, one per
  bound intent, each turning to "OK" with a check icon when it arrives, showing its source
  ("Remote", "Gamepad"). 3. **Long OK** row: "Hold OK until it ticks (600 ms)"; ticks only on
  the long press and shows "Released without a second press" when the release does not also
  activate. 4. **Repeat** row: "Hold an arrow: first repeat 400 ms, then every 100 ms" with a
  repeat count. 5. **Long Back (Menu)** row. 6. Result: "All buttons OK". 7. **Done**.
- **States:** a key with no binding ("Unbound key · Bind it?"); a late or retained pack event
  ignored ("Old press ignored"); Back pressed once ticks it, twice leaves.
- **Safety and driving rules:** Parked only on driver-facing displays; it changes nothing.
- **Components:** Chip (status), ListRow, Button, focus ring tokens.
- **Spec refs:** [Shell input §5][si5], [Shell input §8][si8], [Shell input §14][si14].

[a28]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[a32r]: ../../../../decisions/adr-0032-one-node-optional-brain.md#risks
[a40-4]: ../../../../decisions/adr-0040-power-states-and-wake.md#4-wake-requests
[hw-p]: ../../../research/hardware.md#power-wake-and-buses-detail
[si2]: ../../../../specs/2026-10-07-shell-input-design.md#2-intents
[si3]: ../../../../specs/2026-10-07-shell-input-design.md#3-sources
[si5]: ../../../../specs/2026-10-07-shell-input-design.md#5-repeat-and-long-press
[si8]: ../../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[si14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[ui35]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
