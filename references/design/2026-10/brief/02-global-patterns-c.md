---
title: "Designer brief — global patterns (c): long jobs, undo, empty vehicle, updates, service mode, wake and accessibility"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md]
summary: >
  The last set of global patterns. Long-running jobs (firmware flash, Export all, capture,
  Scan all, Tier 3 procedures) with progress, Stop and what survives leaving the page;
  destructive actions and their undo windows (edit undo, 30-day add back, 7-day undo reset,
  remove device, delete trip); the empty vehicle when no pack matches (unknown vehicle,
  generic OBD-II, choose your vehicle); the update-available state; the service-mode frame;
  the Brain wake, queued and Needs the Brain states; and accessibility: the D-pad focus ring,
  focus zones, target and text sizes per class, contrast, reduced motion and names.
---

# Global patterns (c): long jobs, undo, empty vehicle, updates, frames, accessibility

### ia-long-job — Long-running jobs  [Proposed]
- **Purpose:** one way to show work that takes seconds to minutes, and what happens if you leave. *Why:* Scan all, Export all, capture, procedures and firmware updates each need progress, and no spec gives them one shared look.
- **Owner:** os
- **Opens from → goes to:** the job's start button → progress card → result; a strip-adjacent job chip while it runs.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone, desktop and HU-7 for Export all, Scan all and a firmware update; Day on phone.
- **Content:** 1. Title naming the job and target: "Scanning 6 systems", "Exporting *n* trips", "Updating Node 1 firmware". 2. Progress: determinate bar with "3 of 6" or "45 %" as text, or per-row status for scans ("Engine · OK", "SLABS · Faults 1", "Airbag · Scanning"). 3. Time: "About 2 min left" only when known. 4. **Stop** (or **Cancel** before it starts). 5. What leaving does: "You can leave this page; the export carries on" or "Keep this page open; leaving stops the procedure". 6. Result: "Export ready · *size* · **Save**", "Scan saved to Trips", or the error with **Retry**.
- **States:** running · paused by the car ("Paused: ignition off") · failed (rung or reason named) · done · Brain asleep: queued only if the action allows it · offline: running jobs on the Brain carry on; the page reconnects to them.
- **Safety and driving rules:** Moving stops or refuses Tier 1–3 jobs; Export and Scan reads may carry on but their pages lock; a firmware update is refused unless Parked and the 12 V reading is above its floor; no animated progress on head units while Moving.
- **Components:** Progress (new, [03-components-c](03-components-c.md)), ListRow, Button (Stop), Toast.
- **Spec refs:** [UI §4.3][ui-4.3] (scan rows, Stop), [UI §7][ui-7] (Tier 3 abort anywhere), [UI §12.2][ui-12.2] (Export all). Used by `trips-export-all`, `diagnose-scan-report`, `diagnose-procedure-step`, `hw-firmware-update` and `decode-lab` capture.
- **Open questions:** should a running job show a strip chip? Recommend no new chip: the Link chip's sheet lists jobs.

### ia-destructive-undo — Destructive actions and undo  [New]
- **Purpose:** make every loss either undoable or confirmed once in plain words.
- **Owner:** os
- **Opens from → goes to:** Delete, Remove, Reset, Revoke buttons → confirm or toast with Undo.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7 for each row below; Day on phone.
- **Content (the ladder, lightest first):**

  | Action | Pattern | Words |
  |---|---|---|
  | Move, resize, rename in edit mode | Undo and Redo in the edit bar (50 steps) | — |
  | Remove a Home or Drive widget | toast with Undo; settings kept 30 days ("Add back") | "Widget removed · Undo" |
  | Reset layout | sheet, Cancel focused; "Undo reset" for 7 days | "Reset Home on this screen?" |
  | Delete a trip | sheet, Cancel focused; no undo | "Delete this trip? Its recording is deleted too." |
  | Revoke a share | two taps, no undo | "Revoke link? People with it lose access now." |
  | Remove a device | sheet naming what changes | "Remove Node 2? It is unpaired and its retained data is deleted." |
  | Delete the last passkey of the last owner | refused, with why | "You can't remove the last way to sign in." |

- **States:** Moving: these buttons are absent on a driver-facing display.
- **Safety and driving rules:** Cancel focused; danger style only on the confirming button.
- **Components:** Sheet, Button (danger), Toast.
- **Spec refs:** [Drive modes §7.1][dm-7.1], [§7.7][dm-7.7], [§7.8][dm-7.8], [UI §3.7][ui-3.7], [accounts §14.7][acc-14.7].

### ia-empty-vehicle — Empty vehicle (no pack matched)  [New]
- **Purpose:** what Home and the Diagnostics app show when no vehicle pack matches the car.
- **Owner:** os
- **Opens from → goes to:** first connection or a new car → "Help decode it" (Decode lab), "Choose your vehicle", or generic OBD-II.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** 1. Home banner (dismissible): "Unknown vehicle — help decode it". 2. Coarse identity only: make, model year, region, and "*n* modules answered without a definition"; never the VIN. 3. On an OBD car: generic OBD-II tiles (speed, rpm, coolant, battery) with `candidate` overlays marked. 4. On a non-OBD car: **Choose your vehicle** (make → model → engine, only questions that change the topology), which opens the matching vehicle pack in the Store, and **Start a pack**. 5. **Help decode it** (opens the Decode lab app at Scan, service mode; "Get Decode lab" when it is not installed).
- **States:** no adapter or node yet: the onboarding flow instead (`setup-vehicle-add`, `setup-source`, `setup-first-contact` in [10-onboarding-c](10-onboarding-c.md)) · Moving: the banner hides; tiles show what generic OBD-II reads.
- **Safety and driving rules:** read-only; nothing is sent to find the bus unless Parked.
- **Components:** Banner, StatTile (candidate), ListRow, Button.
- **Spec refs:** [UI §4.4][ui-4.4], [UI §8.2][ui-8.2], [UI §5.4][ui-5.4].

### ia-update-available — Update available  [New]
- **Purpose:** say that Ostler, a vehicle pack, an app, a widget or theme pack, or a device's firmware has a newer version.
- **Owner:** os
- **Opens from → goes to:** the Store's Updates tab, the app drawer (a dot on the app icon), Settings → Updates, a device page → the update → `ia-long-job`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** 1. A dot on the Store icon and the app's icon in the app drawer, and a meta line "Update available" on its App info. 2. On the page: current and new version, what changes in one line, size, **Update**, and "Later". 3. Firmware: "Update when parked, ignition on".
- **States:** owner only (others see the row without the button) · remote path: read-only · Moving: no prompts.
- **Safety and driving rules:** updates are owner operations on local links; nothing updates itself while Moving.
- **Components:** ListRow, Badge (dot), Button.
- **Spec refs:** [app model §7.1][am-7.1] item 5 · [Store §9][st-9]. The pages behind it: `settings-updates` in [30-settings-e](30-settings-e.md#settings-updates--updates--new), `hw-firmware-update` and `hw-brain-update` in [20-hardware-e](20-hardware-e-updates-input.md#hw-firmware-update--update-device-firmware--proposed).

### Pattern: the service-mode frame
- **Screen block:** `shell-service-mode` in [40-drive-b](40-drive-b.md#shell-service-mode--service-mode-frame-and-strip-badge--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** make it impossible to forget that admin and Experimental items are on.
- **Opens from → goes to:** long-press on the version line in Settings → About, then the server password → frame on every page → **Exit service mode**.
- **Content:** 1. A thick frame round the viewport in `warn` with `line-strong` inner edge. 2. Strip badge "Service mode". 3. Experimental items and status tags appear; Settings shows Developer and the Decode lab app opens.
- **States:** refused while Moving: "Not while moving"; it exits by itself when the car moves.
- **Safety and driving rules:** shell-drawn, outside any layout ([Drive modes §8.1 R3][dm-8.1]).
- **Components:** Frame (new), Chip (badge).
- **Spec refs:** [UI §3.5][ui-3.5].

### Pattern: Brain asleep, waking and queued
- **Screen block:** `shell-brain-wake` in [40-drive-b](40-drive-b.md#shell-brain-wake--brain-wake-sheet-queued-button-needs-the-brain--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** be honest when the Brain sleeps, and wake it only with consent and a cost.
- **Opens from → goes to:** a view or action that needs the Brain → wake sheet or queued button → result.
- **Content:** 1. Card "Needs the Brain" with **Wake** (on full Trips, replay, clips). 2. Remote wake sheet: "This needs the Brain. Wake it? About 30 s · uses about 30 mAh (today: 180 mAh left) · battery 12.5 V", "2 of 6 remote wakes left today", **Wake and run** / **Cancel**. 3. Button while waking: "Waking Brain… 12 s". 4. Queued: "Queued · runs when the Brain is ready · expires 14:35 · Cancel". 5. Refusals: "Brain not woken: battery 11.9 V", "Limit reached: 6 wakes this hour".
- **States:** local requests wake without a sheet · node alone: no Brain prompts exist · Moving: no wake prompt.
- **Safety and driving rules:** approvals never queue; Tier 2+ never queues ([UI §3.8][ui-3.8]).
- **Components:** Card, Sheet, Button (queued state).
- **Spec refs:** [UI §3.8][ui-3.8].

### Pattern: focus and accessibility
- **Screen block:** `shell-focus-states` in [40-drive-a](40-drive-a.md#shell-focus-states--d-pad-focus-states-across-the-kit--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** every control works from a D-pad, keyboard or remote, and reads well for everyone.
- **Opens from → goes to:** any non-pointer input; a tap clears the ring.
- **Content:**
  1. **Ring:** 3 px `focus-ring-color` (accent) outside the element with a 2 px `bg` gap; no glow, shadow, size change or animation; a focused ListRow also takes `accent-soft`.
  2. **Zones:** strip, dock, page, sheet; a sheet traps focus until `back`.
  3. **Engaged** controls (slider, setpoint, scrubber, map) show an engaged state; arrows adjust; map shows a centre target.
  4. **Touch and D-pad together:** first tap focuses a Drive menu row, second activates.

  | Measure | Phone, tablet, desktop | Head unit Parked | Moving template |
  |---|---|---|---|
  | Smallest text | 12 px | 18 px | 24 px |
  | Targets | 48 px | 76 px | 76 px |
  | Icons | 20 / 24 px | 32 / 40 px | 40 px |
  | Text contrast | ≥ 4.5:1 | ≥ 4.5:1 | ≥ 4.5:1 |
  | Focus ring contrast | ≥ 3:1 | ≥ 3:1 | ≥ 3:1 |

  5. Reduced motion: every duration 0; the alarm pulse becomes a static ring.
  6. Names: a renamed item's accessible name is the custom name, its default the description; names use `dir="auto"`.
- **States:** Moving in Drive mode: only `alert_card` takes focus, on its safest button.
- **Safety and driving rules:** Cancel focused in every gate confirm ([shell input §7][si-7]).
- **Components:** every kit component.
- **Spec refs:** [shell input §4][si-4], [§9][si-9], [§10][si-10], [visual §4][vds-4], [visual §5][vds-5], [Drive modes §7.6][dm-7.6].

[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-7.7]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#77-hide-replace-and-reachability-v02
[dm-7.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#78-reset-layout-always-reachable-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-4]: ../../../../specs/2026-10-07-shell-input-design.md#4-focus-zones-and-spatial-navigation
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[si-9]: ../../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[si-10]: ../../../../specs/2026-10-07-shell-input-design.md#10-accessibility
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.7]: ../../../../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-5.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-8.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#82-generic_obd2-and-unknown-vehicle--help-decode-it
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[st-9]: ../../../../specs/2026-10-07-store-design.md#9-updates
