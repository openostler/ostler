---
title: "Designer brief 45-d — launcher: the widget picker gallery and the widget setup frame, style picker and data-source picker"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Fourth launcher brief file. It covers the widget picker as an Android-style gallery grouped
  by app, with search and previews at each size (re-expressing shell-widget-picker), and the
  widget setup frame that every widget's setup page shares (re-expressing
  drive-widget-settings): the OS draws it from the widget's settings schema, with an optional
  custom page from the widget's app. It then gives the style picker (the look) and the
  data-source picker (a signal chosen by search, with proven and candidate badges, its unit,
  range and warning thresholds), using real Discovery 2 Td5 and SLABS signals.
---

# 45-d — Widget picker and the widget setup frame

Back to [45-a](45-launcher-a.md). The OS rules for these screens (only installed apps'
widgets, Moving limits per slot, honest signal states) are in 40-drive-d and 40-drive-h.
Everything here is Park to edit on a driver-facing display: while Moving these routes show
the locked view with **Open on phone** (40-drive-b; [Drive modes §8.1][dm-8.1] R1).

### shell-widget-picker — Widget picker gallery  [Existing]
- **Purpose:** browse every widget the installed apps offer and drag one onto a page.
- **Owner:** os
- **Opens from → goes to:** **Widgets** in the launcher menu; **Add** in edit mode;
  **Replace with…** in the item sheet. Dragging a preview onto the page (or **Add** with the
  D-pad) places it and opens its setup page if it has required settings; otherwise it lands
  with its defaults.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (bottom sheet, full height); hu7 Night (passenger-side sheet 520 px, no blur);
  phone Day; desktop Night.
- **Content (top to bottom):**
  1. **Search** "Search widgets" (by name, app or signal: "boost" finds Analogue gauge and
     Bar gauge preset to Turbo pressure).
  2. **Tabs:** **By app** · **By signal** (the By signal tab is approved, item 47; 40-drive-d).
  3. **Groups by app**, A to Z, each a collapsible row with the app icon, name and count:
     **System** first (2, drawn by the OS: Warning lights, Alarm status), then **Camera**
     (1), **Map** (1), **Maintenance** (1: Service due), **Media** (1: Now playing),
     **Navigation** (1: Next turn), **Phone** (2: Favourites, Recent calls), **Radio** (1),
     **Social** (2: Push to talk, Ride status), **Starter widgets** (16, with Clock and Weather, item 53), **Trips** (2: Trip
     computer, Last trip).
  4. **Expanded group:** one card per widget: a **live preview at its default size** on the
     page's real grid scale, the name, a one-line description ≤ 60 characters, the sizes
     as chips ("1×1 · 2×1 · 2×2") and a badge **Works while driving** (`directions_car`)
     or **Parked only**.
  5. **App shortcuts** group at the end (`launcher-shortcut-picker`, 45-b).
  6. Footer: **Get more widgets** → the Store app's widget packs (70-store files).
- **States:** an app installed but stopped: its group greyed, "Turned off · App info".
  A widget whose data this car lacks: preview "—" and "Not available on this car". Search
  with no hits: "No widgets match 'egr'. Try By signal." Loading: preview skeletons.
  Offline: Store footer says "Offline". Target is a Drive page's Moving section: Parked-only
  widgets carry "Parked only" and drop outside the Moving section.
- **Safety and driving rules:** no widget can break the Moving limits for the slot it lands
  in; safety widgets already on a page are not offered twice ([app model §15][am-15],
  [Drive modes §7.2][dm-7.2]).
- **Components:** Sheet, text field, Segmented, ListRow (app group), Widget preview card
  (new component), Chip (sizes, badge).
- **Spec refs:** [Drive modes §7.2][dm-7.2] · [app model §15][am-15] ·
  [Drive modes §9][dm-9] · [launcher §7.1][lw-7.1].
- **Open questions:** should the gallery show widgets of apps not yet installed (with
  **Get**), as a Store teaser? This brief says no; only the footer links to the Store.

### drive-widget-settings — Widget setup frame (shared by every widget)  [Existing]
- **Purpose:** Android's widget configure page: set a widget's look, data, colours, label
  and Moving behaviour, with a live preview. The OS draws it from the widget's settings
  schema; an app may add **one custom setup page** behind a **More settings** row.
- **Owner:** os
- **Opens from → goes to:** placing a widget that has required settings; **Settings** in
  the item popup. **Save** (or **Add** on first placement) returns to edit mode with the
  widget placed; **Cancel** removes a just-placed widget.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (preview on the left, settings on the passenger side); phone Day (preview on
  top); phone Night; desktop Night.
- **Content (top to bottom; rows a widget does not use are absent):**
  1. **Header:** Back, "Set up: Analogue gauge", the app line "Starter widgets", **Save**.
  2. **Preview** at the chosen size on the page's background, live values; a Segmented
     **Parked · While driving** shows the template render the driver will see; a size chip
     row under it.
  3. **Look** row → `widget-style-picker` ("Calm arc").
  4. **Data** row → `widget-data-source` ("Turbo pressure · Engine (Td5) · proven").
  5. **Colours:** "Follow theme" (default, on). Off offers only token-based choices: the
     value colour `text-1` or `text-2`, the band `band`. Status colours are fixed.
  6. **Label** (≤ 30 characters, default the signal's name) and **Icon** (optional).
  7. **Widget options** from the schema: enums as Segmented, bounded numbers as steppers,
     switches, text ≤ 30.
  8. **While driving:** a read-only line saying how the widget appears in a Moving
     section ("Shown as one tile", "Shown as the map pane", or "Parked only · hidden while
     driving").
  9. **More settings** (only if the app provides a custom page) → that page, inside the same
     frame and header.
  10. **Use defaults** and, for a placed widget, **Remove widget**.
- **States:** loading: preview skeleton. Validation: thresholds out of order refused in words
  ("Warning must be below Critical"). Not in session: preview "Not in this session · read by
  Engine (Td5)". Offline: preview stale grey. App stopped: "Widget stopped · App info".
  Moving: locked view.
- **Safety and driving rules:** no option adds animation, a sparkline or text beyond 30
  characters to the Moving render; colour changes only on a level change and always with its
  word ("High"); apps draw no widget settings UI except the optional custom page, and that
  page is Parked only ([app model §15][am-15], [Drive modes §4.2][dm-4.2]).
- **Components:** Sheet (HU passenger side) or full page (phone), Segmented, ListRow,
  switch, stepper (new component), Gauge, StatTile, Button.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [app model §15][am-15] ·
  [Drive modes §4.3][dm-4.3] · [visual §8][vds-8] · [launcher §7.2][lw-7.2] ·
  [launcher §7.3][lw-7.3].
- **Open questions:** **Decided (item 51):** the OS draws every widget setup page from the
  widget's schema; an app may add one custom Parked page behind "More settings", validated
  against the schema.

### widget-style-picker — Look (style picker)  [New]
- **Purpose:** choose how a widget draws its value: the Android "look" step.
- **Owner:** os
- **Opens from → goes to:** **Look** in the setup frame; a tap picks and returns.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night for Coolant; phone Night.
- **Content:** a grid of live preview cards, one per style the signal's type allows
  ([Drive modes §4.2][dm-4.2]): for Coolant (a number) **Number**, **Arc** (240°), **Bar**,
  **Sweep** (stepped segments), **Graph** (Parked only); for Transfer box low range (a
  two-state signal) **Chip** only; for Heading **Compass** and **Number**. Each card: the
  preview at the current size, the style name, "Parked only" where it applies. The gauge
  style pack from the theme wizard (45-k) restyles every card at once; a line names it
  ("Gauge style: Calm").
- **States:** a style not valid for the signal is absent, not greyed. Moving: locked view.
- **Safety and driving rules:** Graph never enters a Moving section; no style animates
  while Moving ([Drive modes §4.3][dm-4.3]).
- **Components:** Widget preview card (new), Sheet.
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [visual §8][vds-8].
- **Open questions:** none.

### widget-data-source — Data (data-source picker)  [New]
- **Purpose:** choose the signal a widget shows and set its unit, range and warning
  thresholds.
- **Owner:** os
- **Opens from → goes to:** **Data** in the setup frame; **Signal** opens the signal search
  (`drive-signal-picker`, rules in 40-drive-h); **Done** returns.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with Turbo pressure; phone Night with the search open; desktop Night with the VSS
  path field.
- **Content (top to bottom):**
  1. **Signal** row with search: "Turbo pressure · Engine (Td5)" and a **proven** badge
     (`ok` word) or **candidate** badge (dashed underline, `warn-ink` word, as EGR or
     External temp). Results grouped **Engine (Td5)**: RPM, Speed, Coolant, Turbo pressure,
     Battery, Intake air, Fuel, Ambient pressure, Air flow (measured), Injector 1–5;
     **SLABS**: Height left (raw), Height right (raw), Transfer box low range, Centre diff
     lock, Battery; **GPS**: Speed, Heading, Altitude; **Node IMU**: Pitch, Roll (not
     published on the D2 yet). Filter chip **Available on this car** (on).
  2. **Unit:** "Follow Settings (bar)" or fixed (bar, kPa, psi).
  3. **Decimals:** 0 · 1 · 2.
  4. **Range:** min and max, default from the signal (Turbo pressure 0.8–2.6 bar; Coolant
     −20–120 °C).
  5. **Thresholds:** Normal, Warning, Critical as min/max pairs with a live band on the
     preview; defaults from the signal's normal band (Turbo pressure 0.9–2.3 bar; Coolant
     normal 80–100 °C, warning 105–112, critical from 112 as in the Dashboard preset).
  6. **Source when several systems give it:** Speed "Engine (Td5) when in session, else GPS"
     (labelled by source).
- **States:** "Not in this session" when SLABS holds the K-line (rpm and coolant), "Not
  available on this car", "Needs the node's IMU". Thresholds outside the range refused.
  Offline: last values with age. Moving: locked view.
- **Safety and driving rules:** bindings are VSS paths so pages travel between cars; pack
  signals without a VSS path (Intake air) only in pack-hinted pages; missing reads "—",
  never 0 ([Drive modes §4.2][dm-4.2], [Drive modes §5.1][dm-5.1]).
- **Components:** Sheet, text field (search), ListRow (badge), Chip (filter), Segmented,
  stepper (new), Gauge (band preview).
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [Drive modes §7.4][dm-7.4] ·
  [visual §8][vds-8].
- **Open questions:** none.

<!-- links -->
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#51-diagnostic-todays-six-tiles
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[lw-7.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#71-the-picker-gallery
[lw-7.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#72-the-widget-setup-page
[lw-7.3]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#73-a-custom-setup-page
