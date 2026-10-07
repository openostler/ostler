---
title: "Designer brief 40-a — shell chrome: status strip, dock, focus states, telltale sheet, connection sheet, vehicle switcher"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-07-maintenance-garage-addon-design.md]
summary: >
  First of the shell, Home, Drive and alerts brief files (40-a to 40-i). It covers the
  shell's always-present chrome: the status strip with every chip and badge in the normal and
  Drive contexts and its per-class chip budget, the dock (was the rail: bottom on
  phones, driver side on head units; slots per class, Home and the app drawer anchored), the D-pad focus states across the
  component kit, the worst-telltale fault sheet (full list Parked, `telltale_list` while
  Moving), the connection sheet (connection ladder, Brain power, queued actions, adapter
  verdicts and the always-present Reset layout row) and the active-vehicle switcher. Examples
  use the Discovery 2 Td5 pack: Td5 and SLABS signals and real fault codes.
---

# 40-a — Shell chrome

Files in this set: **40-a** chrome · [40-b](40-drive-b.md) driving states, service mode,
Brain wake · [40-c](40-drive-c.md) Home, app drawer, edit-mode rules · [40-d](40-drive-d.md) picker
rules, dock and strip editors, Reset · [40-e](40-drive-e.md) and [40-f](40-drive-f.md) Drive
home pages · [40-g](40-drive-g.md) page switcher, Drive menu, page list, page editor rules · [40-h](40-drive-h.md)
widget settings, preview, import · [40-i](40-drive-i.md) alerts and calls.

**Terms (owner's direction of 2026-10-07: Ostler is an Android-style OS).** Screen IDs are
unchanged, but the words are Android's: the **rail** is now the **dock** (bottom on phones,
on the driver's side on wide head units); **More** is the **app drawer**; Drive **modes and
their faces** are **Drive home pages** in one flat swipeable carousel with page dots
(presets only add pages; model in [45-launcher-a](45-launcher-a.md)) (an ID like
`drive-dashboard-cluster` is the "Dashboard · Cluster" home page). Diagnostics, Trips,
Security, Map, Social, Phone, Media and the rest are **apps**; the strip, sheets, alerts,
calls, the Moving rules and Park to edit stay with the **OS**. Each block has an **Owner**
line. Edit mode, drag and resize, the widget picker gallery, widget setup pages and the
wizards are drawn in the launcher brief (45-launcher files); these files keep their OS rules.

Conventions for every block: the D2 is right-hand drive, so the dock is drawn on the
**right** on head units; draw a left-hand-drive frame only where noted. "HU" means every head-unit class
(HU-5, HU-7, HU-9/10, HU-wide). Head units are always driver-facing ([UI §12.1][ui-12.1]).

### shell-strip — Status strip (all chips)  [Existing]
- **Purpose:** one row of status chips at the top of every screen, never scrolling; each chip
  is a word plus an icon and opens a sheet.
- **Owner:** os
- **Opens from → goes to:** always present. Telltale → `shell-telltale-sheet`; Link →
  `shell-connection-sheet`; Vehicle → `shell-vehicle-switcher`; REC → the Trips app; Drive
  page chip → cycles home pages or `drive-switcher`; comms chip → `call-template`; long-press anywhere →
  `shell-strip-editor` (Parked) or `shell-park-to-edit` (Moving).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night normal strip; hu7 Night-dim Moving Drive strip; phone Day; hu5 Night (tightest).
- **Content (left to right, default order; the user may reorder, [Drive modes §7.5][dm-7.5]):**
  1. **Back** (Drive strip only): `arrow_back` "Back". Anchor item.
  2. **Drive page chip** (`drive_mode`, Drive strip only): the current home page's icon and name, for example `dashboard`
     "Dashboard". Anchor item; its word is always the page name.
  3. **Vehicle** (only with more than one vehicle in the garage): the active vehicle's name.
  4. **Worst telltale**: `error` + "2 faults" in `alarm` when a fault is current, `warning` +
     "1 fault" in `warn` when only logged; a "new" count after the word. Safety item.
  5. **Security** (only with a node): "Disarmed", "Armed" or "Alerting". Safety item.
  6. **Link**: connection-ladder rung word plus the system holding the K-line session, for
     example "Data flowing · Td5"; power notes "Brain asleep", "Waking Brain · 12 s" with a
     ring, "1 queued"; in replay it reads "Replay · Exit to live".
  7. **REC**: red dot + "REC", or "Paused".
  8. **Device slot**: climate setpoint or a live-camera chip; two on HU-wide.
  9. **12 V**: `battery_full` + "13.9 V" (Td5 or SLABS `battery`, else the node).
  10. **Clock**: "14:32". 11. **Mark**: `flag` "Mark" (taps a mark; safe at any speed).
  12. Context chips when active: comms chip "Ride: Peak · PTT" or "Call · 04:12"
      ([Social §13][soc-13]); profile chip "Car" on a head unit ([Accounts §14.7][acc-14.7]);
      Ghost or "Visible · 12 min" visibility chip ([Accounts §14.3][acc-14.3]).
  13. Shell-drawn badges, not chips: service-mode badge, replay badge, admin badge.
- **Chip budget (never scroll):** phone 5, HU-5 6, HU-7 7, HU-9/10 8, HU-wide 10, tablet and
  desktop 10. Today's phone set is telltale, Link, REC, Mark (and admin); the phone Drive
  strip gives Link's and REC's places to Back and Drive mode. HU-5 adds the clock.
- **States:** no vehicle: Link reads "No adapter", no telltale. Offline: Link "Offline" in
  amber with the last-seen age; values stale grey. Loading: Link "Connecting…". Parked: all
  chips for the class. Idling: as Parked. Moving: same chips; Drive strip leads with Back and
  Drive mode. Passenger: a "Passenger view" badge joins (`shell-passenger-view`). Locked: n/a.
  Attention: only an `alarm` chip pulses (the one motion allowed while Moving); reduced motion
  shows a static ring.
- **Safety and driving rules:** telltale and Security can move but never hide, and their icon
  and word are fixed; Back and Drive mode are always in the Drive strip; no app chips
  ([Drive modes §8.1][dm-8.1] R3, R4, R9). No glow on head units.
- **Components:** Chip (status), Button (Back). Tokens `type-label`, `ok`/`warn`/`alarm`,
  `accent-soft` only on a selected chip, focus-ring tokens.
- **Spec refs:** [UI §3.2][ui-3.2] · [UI §15.1][ui-15.1] · [UI §15.2][ui-15.2] ·
  [Drive modes §6][dm-6] · [Drive modes §7.5][dm-7.5] · [visual §8][vds-8] ·
  [Maintenance §8][mg-8].
- **Open questions:** **Decided (item 58):** no Maintenance strip chip; apps add no strip
  chips. Service due shows as a Home card or the Service due widget only.

### shell-rail — Dock (was the rail and the phone bottom bar)  [Existing]
- **Purpose:** the pinned slots (phone 5, HU-5 and HU-7 5, HU-9/10 6, HU-wide 7, tablet and
  desktop 7; decided, item 17): at the bottom on the phone, on the driver's side on every
  head unit, HU-wide included (item 44).
- **Owner:** os
- **Opens from → goes to:** always present outside full-screen Drive on the phone; each slot
  opens its app or Home; the app-drawer slot opens the drawer; long-press on an item or the gap opens `shell-rail-editor` (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (right side), phone Night and Day, hu5 Night, desktop Night with labels.
- **Content (default for a full install):** 1. **Home** `home`. 2. **Diagnostics** app
  `stethoscope`. 3. **Trips** app `history` (the live code still says "Logs"). 4. **Security**
  app `shield` (only with a node). 5. **App drawer** (was More; `apps` or the user's icon),
  always present. Home and the App drawer are anchors: they move, never go (item 16). The
  head-unit **Drive** button is retired (item 16). Guardian's dock is Security · Settings ·
  App drawer (item 42); the drawer is always there. Variant: Social pinned
  as "Ride" in slot 4.
- **Sizes:** side dock 80 (HU-5), 96 (HU-7), 112 (HU-9/10, HU-wide), 88 (tablet), 88 with
  labels (desktop); phone dock 72 + safe area, floating pill. 76 px targets on HU, 72–86 px
  items on phone. Labels ≤ 12 graphemes.
- **States:** active item: `accent-soft` pill and accent icon. Parked, Idling: full. Moving:
  HU shows the driving page full screen; a dock item whose target has no Moving view is not
  drawn and its slot stays empty; the drawer opens a `short_list` of ≤ 6 driving apps
  ([launcher §5.1][lw-5.1], [§5.2][lw-5.2]).
  Left-hand drive: dock on the left.
- **Safety and driving rules:** the app drawer is in the dock exactly once and never hidden;
  a pinned app keeps its own driving rule; pinning unlocks nothing ([Drive modes §7.3][dm-7.3]).
- **Components:** TabBar (floating pill on phone, side dock on HU). Focus-ring tokens.
- **Spec refs:** [UI §3.3][ui-3.3] · [UI §3.4][ui-3.4] · [UI §15.2][ui-15.2] ·
  [Drive modes §7.3][dm-7.3] · [visual §8][vds-8].
- **Open questions:** **Decided (item 16, [launcher §5][lw-5.1]):** the approved launcher
  spec names them the dock and the app drawer.

### shell-focus-states — D-pad focus states across the kit  [Existing]
- **Purpose:** one sheet of every kit component in its focused and engaged states, so a
  D-pad, keyboard or steering-wheel button can drive every screen.
- **Owner:** os
- **Opens from → goes to:** not a page; a reference sheet the designer draws once.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  and Night-dim; phone Day; one Moving Drive frame on hu7 Night-dim.
- **Content:**
  1. **The ring:** 3 px `focus-ring-color` (accent) outside the element with a 2 px `bg`
     gap; no glow, shadow, size change or animation; the element's box is identical focused
     and unfocused.
  2. **Per component:** Button (primary, secondary, ghost, danger), Segmented option, Chip,
     ListRow (ring plus `accent-soft` fill), dock item, strip chip, StatTile that acts, map
     control, Scrubber thumb, Sheet buttons.
  3. **Engaged:** a slider, setpoint, scrubber or map after `ok`: a visible "engaged" state
     (ring plus a word such as "Adjusting"); on a Parked map a centre target for "Navigate
     here" and "Save place".
  4. **Zones:** strip, dock (`rail` in the input spec), main, sheet. An open sheet traps focus; the first focus lands on
     **Cancel** in every confirm sheet.
  5. **Drive mode while Moving:** home pages are not focusable; `back` focuses the Drive-mode chip
     wherever it sits; an `alert_card` takes focus on its safest button (Play, not Reply).
  6. **Touch plus D-pad:** in the Drive menu a first tap focuses a row, a second activates it.
  7. **Edit mode:** a widget picked up by `ok` shows a doubled ring.
- **States:** Parked: every component. Moving: only the Drive strip chip, Drive menu rows and
  alert buttons take focus. Focus shows only after a non-pointer intent; a tap clears it.
- **Safety and driving rules:** no glow on focus in Drive mode or on head units at night;
  `ok` presses within 500 ms of a sheet opening are ignored ([shell input §5][si-5]).
- **Components:** Button, ListRow, Chip, Segmented, StatTile, Scrubber, map control. Tokens
  `focus-ring-width`, `focus-ring-color`, `focus-ring-gap`, `accent-soft`.
- **Spec refs:** [shell input §4][si-4] · [shell input §9][si-9] · [shell input §10][si-10] ·
  [shell input §14][si-14] · [visual §8][vds-8].
- **Open questions:** none.

### shell-telltale-sheet — Worst-telltale sheet  [Existing]
- **Purpose:** the fault list behind the telltale chip; it replaces any fault modal.
- **Owner:** os
- **Opens from → goes to:** the telltale chip, or by itself when a new current fault arrives;
  rows go to Diagnose → *system* → Faults (Parked); "Get help with this fault" goes to the
  help flow ([UI §13.2][ui-13.2]); Close returns where the user was.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night-dim Moving (`telltale_list`); phone Day.
- **Content (Parked):**
  1. Title "Faults" with the count; a line per system: "Engine (Td5) · 2", "SLABS · 1".
  2. Fault rows: status icon and word ("Current" `alarm`, "Logged" `warn`), code and name,
     for example "P0403 · EGR inlet throttle (logged low)"; system; the meaning and the cause
     line ("Check the EGR inlet throttle actuator, its vacuum or feedback and the wiring");
     confidence word ("proven"). A SLABS example: "Right front wheel speed sensor: output too
     low".
  3. Actions per row: **Open in Diagnose**, **Get help with this fault**.
  4. Footer: **Acknowledge** (stops the chip's "new" count; only new faults alert after).
- **Content (Moving, `telltale_list`):** one line per fault, ≤ 30 characters, 24 px type,
  status icon first: "Engine: P0403 EGR throttle", "SLABS: RF wheel sensor low". No
  descriptions, no actions except **Close**.
- **States:** empty: "No faults" with `ok`. Loading: "Reading faults…". Not in session: "SLABS
  not in this session; last read 14:02" in stale grey. Offline: last list with its age.
  Parked, Idling: full. Moving: `telltale_list`. Passenger: as Moving.
- **Safety and driving rules:** a safety item: shell-drawn, never removed or covered
  ([Drive modes §8.1][dm-8.1] R3); while Moving lines ≤ 30 characters ([UI §3.5][ui-3.5]).
- **Components:** Sheet, ListRow, Chip (status). Tokens `ok`/`warn`/`alarm`, `*-bg`,
  `warn-ink`, `type-body` (≥ 24 px Moving).
- **Spec refs:** [UI §3.2][ui-3.2] · [UI §3.5][ui-3.5] · [UI §12.1][ui-12.1] ·
  [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

### shell-connection-sheet — Link chip sheet  [Existing]
- **Purpose:** what is connected, which rung failed, what the Brain is doing, queued actions,
  and the always-reachable Reset layout.
- **Owner:** os
- **Opens from → goes to:** the Link chip, or by itself when the link drops; rows go to Settings
  → Network (Parked), the adapter flow, `shell-brain-wake`, `shell-reset-confirm`.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked with a failed rung; hu7 Night-dim Moving; phone Day.
- **Content:**
  1. **Ladder**, one row per rung with a tick or the failure: No adapter → Adapter (type and
     quality hint) → Bus ("K-line init") → ECU session ("Engine (Td5)") → Data flowing; plus
     12 V. A failed rung says what to try ("Turn the ignition on and try again").
  2. **Adapter** (no node): kind and verdict chips "ELM: limited", "Clone: read-only",
     "Listen-only: requested", "Soft gate"; **Use an adapter** ([adapters §9][sa-9]).
  3. **Brain:** power word ("Asleep · checks in ≈ 6 min", "Waking… 12 s", "Kept awake" with by whom
     and until when); refused wakes with reasons ("Brain not woken: battery 11.9 V").
  4. **Queued actions:** name, target, "expires 14:35", **Cancel**.
  5. **Roles:** a lost role holder as a row ("No holder: parked broker"), never a new chip.
  6. **Reset layout** row, at the bottom, always present ([Drive modes §7.8][dm-7.8]).
- **States:** no vehicle: ladder stops at "No adapter". Offline: whole sheet stale with its
  age. Parked: full. Moving: rows read-only; Reset layout says "Park to edit". Replay: "Exit
  to live" at the top.
- **Safety and driving rules:** nothing here approves a car action; Cancel on a queued action
  is not a gate action. Reset is an edit, so Parked only on HU ([Drive modes §8.1][dm-8.1] R1).
- **Components:** Sheet, ListRow, Button (Cancel), Chip (verdict). Status tokens, `warn-ink`.
- **Spec refs:** [UI §4.5][ui-4.5] · [UI §3.8][ui-3.8] · [UI §3.7][ui-3.7] ·
  [adapters §9][sa-9] · [Drive modes §7.8][dm-7.8].
- **Open questions:** none.

### shell-vehicle-switcher — Active-vehicle switcher sheet  [Existing]
- **Purpose:** pick the active vehicle when the garage holds more than one.
- **Owner:** os
- **Opens from → goes to:** the Vehicle chip; a card makes that vehicle active; **Edit in
  Garage** goes to Settings → Garage.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night,
  phone Day.
- **Content:** 1. Title "Vehicles". 2. One card per vehicle: its name, pack ("Land Rover
  Discovery 2 · Td5"), a last-known line with its age (battery and "last seen" age), the
  active one ticked. 3. A note when two share a port: "Switching stops the K-line session on
  this port first." 4. **Edit in Garage**.
- **States:** one vehicle: neither the chip nor the sheet exists. Loading: card skeletons.
  Offline: ages only. Parked: full. Moving: locked view ("Available when parked"), because
  system switching is locked.
- **Safety and driving rules:** switching is a system switch, refused while Moving
  ([UI §3.5][ui-3.5]); the VIN never shows, only the name the owner gave.
- **Components:** Sheet, Card (vehicle card with age). Tokens `accent-soft` (active).
- **Spec refs:** [UI §4.1][ui-4.1] · [UI §3.5][ui-3.5].
- **Open questions:** none.

[acc-14.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[dm-6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#6-the-switcher
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-7.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#75-strip-v02
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[sa-9]: ../../../../specs/2026-10-07-source-adapters-design.md#9-ui-summary-detail-in-u-phase-specs
[si-10]: ../../../../specs/2026-10-07-shell-input-design.md#10-accessibility
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[si-4]: ../../../../specs/2026-10-07-shell-input-design.md#4-focus-zones-and-spatial-navigation
[si-5]: ../../../../specs/2026-10-07-shell-input-design.md#5-repeat-and-long-press
[si-9]: ../../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[soc-13]: ../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-13.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#132-get-help-with-this-fault-diagnose-changes-34s-diagnose-row
[ui-15.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#151-drive-modes-changes-123
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip
[ui-3.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[lw-5.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#51-the-dock
[lw-5.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#52-the-drawer
