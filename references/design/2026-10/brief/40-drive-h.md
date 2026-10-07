---
title: "Designer brief 40-h — OS rules for widget setup pages, the signal picker, the Moving preview, layout import and export, import errors and Update from preset"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Drive editing detail brief file, revised for the owner's Android-style direction. Each
  widget's setup page, its look and the dashboard builder wizard now belong to the launcher
  brief (45-launcher); this file keeps the OS rules those pages must honour: the signal
  binding with honest confidence words and "Not in this session" using real Discovery 2 Td5
  limits, thresholds that only change colour on a level change, the map and app-widget
  setup limits, the Parked and Moving preview with failed rules in words, layout import and
  export as files (with a step list), the import error screen and "Update from preset".
  All are Parked-only editors on a head unit.
---

# 40-h — Widget setup rules, preview, import and export

Back to [40-a](40-drive-a.md) for the terms and the file list. Screen look and flow: see the
45-launcher files. Every screen here is an editor: Parked only on a head unit (or Idling
with Park evidence), `shell-locked-view` while Moving ([Drive modes §8.1][dm-8.1] R1).

### drive-widget-settings — Widget setup page: signal tile or gauge (OS rules)  [Existing]
- **Purpose:** bind a tile to a signal and set when it warns.
- **Owner:** os
- **Opens from → goes to:** placing a tile or **Settings** in the item sheet; layout in
  45-launcher; **Signal** → `drive-signal-picker`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with the live tile beside the page.
- **Content the OS requires (example: Boost gauge):** live preview ("1.2 bar"); Signal
  "Turbo pressure · Engine (Td5) · proven"; Style only those valid for the signal (Sparkline
  marked "Parked only"); Units "Follow Settings" or fixed; Range defaulting from the signal's
  limits (0.8–2.6 bar); Thresholds Normal, Warning, Critical as min/max pairs defaulting from
  its normal band (0.9–2.3 bar), with a live band; **Use defaults**.
- **States:** thresholds out of order or outside the range refused in words. "Not in this
  session · Read by Engine (Td5)", "Not available on this car". Moving: locked.
- **Safety and driving rules:** no setting adds animation or a sparkline to the Moving
  section; colour changes only on a level change, with its word ([Drive modes §4.2][dm-4.2]).
- **Components:** Sheet, Segmented, Gauge (live band preview).
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [app model §15.2][am-15.2].
- **Open questions:** none.

### drive-signal-picker — Signal picker  [New]
- **Purpose:** choose the VSS signal a tile reads, honestly showing what this car has.
- **Owner:** os
- **Opens from → goes to:** **Signal** on a widget setup page and the proposed By signal tab.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; desktop Night with the path field.
- **Content:** filter chip **Available on this car** (on); search; groups by system: **Engine
  (Td5)** RPM, Speed, Coolant, Turbo pressure, Ambient pressure, Air flow (measured),
  Accelerator pedal, Battery; **SLABS** Battery, Transfer box low range, Height left (raw),
  Height right (raw); **GPS** Speed, Heading, Altitude. Each row: unit, confidence word
  ("proven", "candidate"), "Not in this session" when its system does not hold K-line.
  Desktop only: "Type a VSS path".
- **States:** filter off: missing paths marked "Not available on this car". Moving: locked.
- **Safety and driving rules:** bindings are VSS paths, so a dashboard travels between cars;
  unmapped Td5 signals (Intake air) only in pack-hinted layouts ([Drive modes §5.1][dm-5.1]).
- **Components:** Sheet, ListRow (confidence word), Chip (filter).
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §4.2][dm-4.2].
- **Open questions:** none.

### drive-widget-settings-map — Widget setup page: map (OS rules)  [New]
- **Purpose:** the limits on a map widget's setup.
- **Owner:** os
- **Opens from → goes to:** **Settings** on a map widget; layout in 45-launcher.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content the OS requires:** Follow "Heading up" and Trail "This trip" (the preset values);
  layers only from installed apps (convoy markers from Map for an opted-in ride, route from
  Navigation; otherwise "Needs Navigation"); overlay tiles count against the 6.
- **States:** "Needs GPS" in the preview. Moving: locked.
- **Safety and driving rules:** nothing adds names, free panning or search to the Moving
  `map` template ([UI §12.1][ui-12.1]).
- **Components:** Sheet, ListRow, Segmented.
- **Spec refs:** [Drive modes §4.3][dm-4.3] · [UI §13.5][ui-13.5].
- **Open questions:** other follow and trail values are not in the spec yet.

### drive-widget-settings-addon — Widget setup page: app widget (OS rules)  [New]
- **Purpose:** an app widget's setup, drawn by the OS from the app's settings schema.
- **Owner:** os
- **Opens from → goes to:** **Settings** on an app widget, for example Map "Convoy distance".
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content the OS requires:** header "Convoy distance · Map"; schema fields (enum as
  Segmented "To: Leader · Sweep", bounded number, switch, string ≤ 30, signal row); "Shown
  while moving as: tiles" (or map, media, call, short list) or "Parked only".
- **States:** app disabled: "Needs Map · open App info". "Widget stopped". Moving: locked.
- **Safety and driving rules:** apps draw no setup UI of their own for widgets; the OS caps
  text and refresh ([app model §15.2][am-15.2]).
- **Components:** Sheet, Segmented, ListRow, switch.
- **Spec refs:** [app model §15.1][am-15.1] · [app model §15.2][am-15.2].
- **Open questions:** the new direction lets "every app bring its own setup flow"; confirm
  widget setup stays OS-drawn from the schema (as approved), with app setup flows only for
  the app itself.

### drive-mode-preview — Preview: Parked and Moving side by side  [Existing]
- **Purpose:** see exactly what the driver will see, and why anything fails.
- **Owner:** os
- **Opens from → goes to:** **Preview** in edit mode or the dashboard builder (45-launcher);
  the import preview.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  desktop Night (two panes at HU-7 size); hu7 Night (stacked).
- **Content:** class picker; **Parked** and **Moving** panes, the Moving one drawn by the
  car's renderer; rules in words with status icons ("Tile 7 shows only when parked", "Map
  pane too small on HU-5: 300 px, needs 340"); counter "Moving: 6 of 6 tiles, 1 of 2 panes".
- **States:** all pass: "Ready for driving". A head-unit failure: Save refused, "Fix for
  driving first". Moving: locked.
- **Safety and driving rules:** validator rule 6 is strict per class ([Drive modes §8.2][dm-8.2]).
- **Components:** Card, ListRow. Status tokens.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

### drive-layout-import — Layout import and export  [Existing]
**Flow (import):**

| Step | Screen | User does | Can fail · recovery |
|---|---|---|---|
| 1 | `drive-layout-import` | opens a file, pastes a link or scans a QR | unreadable · `drive-layout-import-error` |
| 2 | `drive-mode-preview` | checks Parked and Moving at this class, warnings, apps it wants | Moving rule fails · refused, class and rule named |
| 3 | Drive home pages (45-launcher) | **Add** puts it in the page list, not the swipe order | server refusal · reason shown |

- **Purpose:** share a Drive home page, Home, dock or strip layout as a file, and bring one in.
- **Owner:** os
- **Opens from → goes to:** **Share** on a page or editor; **Add page → Import**. Dashboard
  presets from the Store are 70-store's.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (export sheet); hu7 Night (import preview).
- **Content (export):** name, description (≤ 120), author (optional), licence "CC BY-SA 4.0";
  **Save as file** (`.ostler-layout.json`), **Copy link**, **QR**, **Share**; "Vehicle and
  personal details are removed."
- **Content (import):** **Open file**, **Paste link**, **Scan QR**; preview card: name, icon,
  author, "Made for: Land Rover Discovery 2" (a hint, never an id), warnings ("Height left:
  not available on this car"), apps it wants ("Needs Social"), **Add**.
- **States:** "Reading layout…"; "Added"; Moving on HU: locked.
- **Safety and driving rules:** no VIN, vehicle id, plate, user id or place in a file
  ([Drive modes §8.4][dm-8.4]).
- **Components:** Sheet, Button, Card (preview).
- **Spec refs:** [Drive modes §8.4][dm-8.4] · [UI §15.2][ui-15.2].
- **Open questions:** none.

### drive-layout-import-error — Import refused  [New]
- **Purpose:** say plainly why a layout was refused.
- **Owner:** os
- **Opens from → goes to:** import step 1 or 2; **Try another file** or **Close**.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night.
- **Content:** `error` icon and one reason per line: "Made for a newer Ostler"; "Not a layout
  file"; "Too large (over 256 KB)"; "Refused on HU-5: 7 tiles while moving, 6 allowed"; "The
  fault telltale can move but can't be removed"; "The app drawer must stay in the dock".
  Non-refusing warnings under "Will show as" with **Add anyway**.
- **States:** refusal, or warnings only.
- **Safety and driving rules:** any Moving-section or guardrail failure refuses the whole
  file ([Drive modes §8.2][dm-8.2]).
- **Components:** Card (tone), ListRow, Button.
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

### drive-update-from-preset — Update from preset  [New]
- **Purpose:** bring a preset's newer changes into an edited copy, slot by slot.
- **Owner:** os
- **Opens from → goes to:** **Update from preset** on a page made from a preset (shown when
  the preset is newer); **Apply** per slot, **Apply all** or **Keep mine**.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  desktop Night; hu7 Night.
- **Content:** "Dashboard has changed since you edited it."; per slot yours vs the preset's;
  the Moving preview updates as slots apply.
- **States:** nothing to update: absent. Moving: locked.
- **Safety and driving rules:** the result is validated like any save.
- **Components:** Card, ListRow, Button.
- **Spec refs:** [Drive modes §8.3][dm-8.3].
- **Open questions:** none.

[am-15.1]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-15.2]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#51-diagnostic-todays-six-tiles
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-13.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
