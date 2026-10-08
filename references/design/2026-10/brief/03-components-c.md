---
title: "Designer brief — components (c): new components and the kit sheets"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  The last part of the component inventory. New components other areas will need: the
  wizard frame and stepper, the wiring diagram card, the calibration gauge, the firmware and
  job progress, and the key-test grid. Then the kit sheets to draw first, one frame each:
  controls, data display, surfaces and feedback, the OS frame, the launcher (home grid, dock,
  app drawer, folder, page dots, widget frame, picker card, wallpaper), the Moving
  templates, the wizard frame, the key-test grid and the hardware set (Proposed). Amended 2026-10-07 (openness round, ADR-0047): style values are the default look under visual §13 and the theme engine; safety rules unchanged.
---

# Components (c): new components and kit sheets

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("apply the
> loosenings"; [ADR-0047](../../../../decisions/adr-0047-openness-round.md)):** Blur on head units is a theme choice. Style values here are the default look;
> themes, add-ons and users may change them within [visual §13](../../../../specs/2026-10-07-visual-design-system-design.md#13-design-language-themes-amendment-2026-10-07) and the
> [theme engine](../../../../specs/2026-10-07-theme-engine-design.md#11-decisions-for-the-owner). Safety rules are unchanged.

## 1. New components other areas need

| Component | Purpose | Variants | Sizes | States | Tokens | Used by |
|---|---|---|---|---|---|---|
| **Wizard frame** (stepper) | one frame for every multi-step flow | numbered steps across the top (P: "Step 2 of 5" text), body, footer with **Back**, **Next** or the step's own verb, **Abort** for Tier 3 | step header 48 (P) / 76 (H) | step done (tick), current (`accent`), to do (`text-3`), failed (`alarm` + reason); preconditions re-checked each step; 12 V floor line | `surface-1`, `accent`, status tones | first run (`setup-*`), app setup flows, `diagnose-procedure-*`, `hw-install-*`, dashboard builder and theme wizards |
| **Wiring diagram card** | how to connect a device, one connection per card | pin-to-pin row, connector photo slot (line drawing), fuse rating, wire colour as a word | full width; diagram area 16:9 | to do, checked (tick), measured from live data ("12.4 V at pin 16") | `line`, `text-2`, `warn` for fuses | `hw-install-wiring`, `hw-install-power` |
| **Calibration gauge** | show a live value approaching a target while the user adjusts | linear (SLABS heights, Height left and Height right), level bubble (IMU) | full width bar; HeroStat value | out of tolerance (`warn` + word), inside tolerance (`ok` + "Hold still"), stable for n s, done; stale stops the step | `band` for tolerance, `ok`, `warn` | `hw-imu-calibrate`, SLS height calibration procedure |
| **Progress** (job and firmware) | long work with honest progress | determinate bar with text %, per-row status list, indeterminate "Waiting for the device…" | bar 8 (P) / 12 (H); text beside it | running, paused (reason), failed (Retry), done; no animation on head units while Moving | `accent` (live), `surface-3` | `ia-long-job`, `hw-firmware-update`, `hw-brain-update`, `trips-export-all`, Scan all |
| **Key-test grid** | tick each input as it arrives | one cell per intent (up, down, left, right, ok, back, menu, mark, zoom, ptt) with press, long press and repeat marks | cells 76 on every class | waiting, seen (tick + "long press" or "repeat"), all OK | `ok`, `text-3` | `shell-buttons`, `hw-buttons-key-test` |

## 2. Kit sheets (draw these first)

Each kit sheet is one frame that shows every variant and state of a group, so the reviewer
checks the kit once before pages use it ([visual §11][vds-11]: V2 kit before V3 pages).

### ia-kit-controls — Kit sheet: controls  [New]
- **Purpose:** every control in every state, so pages only combine them.
- **Owner:** os
- **Opens from → goes to:** a design frame, not an app page.
- **Layout classes:** phone · tablet · hu7 · hu9. **Draw first:** Night on phone and HU-7; Night dim on HU-7; Day on phone.
- **Content:** Button (4 variants × default, pressed, focus, disabled with reason, loading, queued) · Segmented (2, 3, 4 options) · Chip (filter, choice, status ok/warn/alarm, capability, countdown) · ListRow (icon, meta, trailing value, chevron, switch, `short_list` row) · Card (plain, tappable, tone) · Text field (empty, filled, error, typed confirm) · Toggle.
- **States:** focus ring on each; disabled with its reason line.
- **Safety and driving rules:** head-unit column at 76 px targets; no glow in Night dim (default look).
- **Components:** Button, Segmented, Chip, ListRow, Card, Text field, Toggle.
- **Spec refs:** [visual §8][vds-8], [shell input §9][si-9].

### ia-kit-data — Kit sheet: data display  [New]
- **Purpose:** numbers, gauges and charts with their honest states.
- **Owner:** os
- **Opens from → goes to:** a design frame.
- **Layout classes:** phone · tablet · hu7 · hu9. **Draw first:** Night on phone and HU-7; Night dim + Moving on HU-7 (tiles); Day on phone.
- **Content:** Value and StatTile with D2 signals (RPM, Boost, Coolant, Battery, Fuel temp, Height left, Height right) each as live, stale ("· 3 min"), candidate, missing "—", warn and alarm · HeroStat · Gauge in range and out of range · RangeBar · Sparkline · Donut · DistributionBars · Area line · Chart lanes · Scrubber · Ladder · Status tag · Vehicle silhouette.
- **States:** every honest state side by side; a number one step smaller where it would clip.
- **Safety and driving rules:** Moving tiles ≥ 56 px digits, no sparkline, no animation.
- **Components:** as listed in [03-components-b §2](03-components-b.md#2-data-display).
- **Spec refs:** [visual §3.3][vds-3.3], [visual §8][vds-8].

### ia-kit-surfaces — Kit sheet: surfaces and feedback  [New]
- **Purpose:** every layer that sits over a page.
- **Owner:** os
- **Opens from → goes to:** a design frame.
- **Layout classes:** phone · tablet · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** Sheet (bottom, passenger-side, full height) · Sheet over map (peek, half, full) · confirm sheet with Cancel focused · Toast (four variants) · Banner (offline, remote, Moving) · Inline notice · Empty state · Skeleton · Checklist · ActiveTestBanner · App stopped card.
- **States:** scrim, focus trap, open and close (the only motion).
- **Safety and driving rules:** no blur on head units in the default look; a theme may add it, guarded by the Drive-mode render check.
- **Components:** as listed.
- **Spec refs:** [visual §5][vds-5], [visual §8][vds-8].

### ia-kit-shell — Kit sheet: the OS frame  [New]
- **Purpose:** the strip, badges and frames every page sits inside.
- **Owner:** os
- **Opens from → goes to:** a design frame.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on every class; Night dim + Moving on HU-5 and HU-7; Day on phone.
- **Content:** Status strip (normal and Drive) per class with its chip budget · every strip chip in ok, warn, alarm, stale · strip badges · page chip · Frame (service mode, Passenger view) · Locked view card.
- **States:** the alarm pulse (static ring with reduced motion).
- **Safety and driving rules:** telltale and Security chips fixed in icon and word.
- **Components:** Status strip, Strip chip, Strip badge, Page chip, Frame, Locked view card.
- **Spec refs:** [UI §3.2][ui-3.2], [Drive modes §7.5][dm-7.5].

### ia-kit-launcher — Kit sheet: launcher  [New]
- **Purpose:** the Android-style launcher parts.
- **Owner:** os
- **Opens from → goes to:** a design frame; the pages are drawn in `45-launcher-*`.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7; Night dim on HU-7; Day on phone.
- **Content:** the dock holds 5 slots on phone, HU-5 and HU-7, 6 on HU-9/10 and 7 on HU-wide, tablet and desktop (item 17) · Home page grid (viewing, editing with cell outlines and **+**) · page indicator dots (with the "+" new-page dot) · Dock at the bottom (phone) and driver side (HU-7, right-hand drive) with the App drawer button · Dock item states · App drawer grid with search, Settings and Store first, Hidden apps · App icon with badge and lock · Folder closed and open · Shortcut · Widget frame (viewing, editing with resize handles, picked up, safety without ×, Widget stopped) · Widget picker gallery card (available, needs an app, Parked only) · Wallpaper layer (solid, theme image, Night dim, Drive mode) · Edit bar · Item sheet.
- **States:** drag over an edge shows "New page"; a full dock asks which app to move to the drawer.
- **Safety and driving rules:** editing is Park to edit; in Drive mode the dock and dots hide and the page chip takes over; safety widgets have no remove control.
- **Components:** as in [03-components-a §2](03-components-a.md#2-launcher).
- **Spec refs:** [Drive modes §7.1–§7.3][dm-7.1], [Drive modes §8.1][dm-8.1] · [launcher §5.1][lw-5.1] · [launcher §6.2][lw-6.2].
- **Open questions:** **Decided (item 44):** on HU-wide the dock sits on the driver side, as
  the rail today.

### ia-kit-moving-templates — Kit sheet: Moving templates  [New]
- **Purpose:** the eleven templates the OS draws while Moving, at their limits.
- **Owner:** os
- **Opens from → goes to:** a design frame.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** Night dim + Moving on HU-5 and HU-7; Night on HU-9 and HU-wide.
- **Content:** one example of each template at its limit (six tiles; six-row `short_list` with 30-character rows; `alert_card` with sender, app, Play, Reply; `call` with three buttons; `map` with route and next manoeuvre; `media`; `value`; `setpoint`; `arm`; `camera_live`; `telltale_list`).
- **States:** focus on the safest button; stale tile.
- **Safety and driving rules:** text ≥ 24 px, targets 76 px, no animation (glow and gradient are the theme's choice, under the render check).
- **Components:** the templates in [03-components-b §3](03-components-b.md#3-moving-templates-os-only).
- **Spec refs:** [UI §12.1][ui-12.1], [Drive modes §4.3][dm-4.3].

### ia-kit-wizard — Kit sheet: wizard frame  [New]
- **Purpose:** one frame for first run, app setup, procedures and install guides.
- **Owner:** os
- **Opens from → goes to:** a design frame.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** stepper (5 steps: done, current, to do, failed), body slot, footer (Back, Next, Abort), a precondition strip ("Parked", "Ignition on", "Battery above the floor"), a typed confirm step, an aborted state.
- **States:** a precondition lost mid-step stops the step with its reason.
- **Safety and driving rules:** Tier 3 steps Parked only; abort anywhere ([UI §7][ui-7]).
- **Components:** Wizard frame, Checklist, Text field, Button.
- **Spec refs:** [UI §7][ui-7].

### ia-kit-key-test — Kit sheet: key-test grid  [New]
- **Purpose:** the grid that ticks each button as it arrives.
- **Owner:** os
- **Opens from → goes to:** a design frame; the page is `hw-buttons-key-test`.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on HU-7 and phone.
- **Content:** ten intent cells in waiting, seen, long press and repeat; "All buttons OK".
- **States:** a late or retained event changes nothing.
- **Safety and driving rules:** Parked only.
- **Components:** Key-test grid.
- **Spec refs:** [shell input §8][si-8].

### ia-kit-hardware — Kit sheet: hardware set-up  [Proposed]
- **Purpose:** wiring cards, calibration gauges and firmware progress. *Why:* install, calibration and firmware pages need them and no spec draws them.
- **Owner:** os
- **Opens from → goes to:** a design frame; pages in `20-hardware-*`.
- **Layout classes:** phone · tablet · hu7. **Draw first:** Night on phone and HU-7; Day on phone.
- **Content:** Wiring diagram card (to do, checked, measured) · Calibration gauge (SLABS heights out of and inside tolerance; IMU level bubble) · Progress (firmware: determinate, waiting for the device, failed, done).
- **States:** stale input stops the calibration step.
- **Safety and driving rules:** firmware and calibration are Parked only.
- **Components:** Wiring diagram card, Calibration gauge, Progress.
- **Spec refs:** [UI §7][ui-7].

[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-7.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#75-strip-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-8]: ../../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[si-9]: ../../../../specs/2026-10-07-shell-input-design.md#9-focus-visuals
[ui-3.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[vds-3.3]: ../../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[vds-11]: ../../../../specs/2026-10-07-visual-design-system-design.md#11-migration-small-prs-approved-2026-10-07-all-before-u2-build-work
[lw-5.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#51-the-dock
[lw-6.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#62-edit-mode
