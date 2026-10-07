---
title: "Designer brief 45-g — widget setup pages (3 of 3): weather, now playing, radio, phone favourites, next turn, app shortcut, text label and image"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-phone-comms-addon-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Third file of widget setup pages, each in the shared OS-drawn setup frame (45-d). It
  covers weather, media now playing (Media app), radio (Radio app), phone favourites (Phone
  app, a short list while Moving), the navigation next turn (Navigation app), the app
  shortcut widget, a text label and an image. Each block gives the styles, data, options,
  example and Moving behaviour. Media, radio and phone widgets use only the templates the
  OS allows while Moving; the image widget is Parked only and its image stays on the device.
---

# 45-g — Widget setup pages: media, comms, navigation and decoration

Back to [45-a](45-launcher-a.md); shared rules in [45-e](45-launcher-e.md).

### widget-setup-weather — Weather  [New]
- **Purpose:** current conditions where the car is. Widget from: Starter widgets (Clock
  and Weather are part of the starter pack, item 53).
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: `partly_cloudy_day` "11 °C · wind 18 km/h". 2. **Look:** Now,
  Now and next 6 hours (Parked only). 3. **Data:** place: Car's position (on the Brain) or
  a saved place; outside temperature from the car is External temp · Engine (Td5) ·
  candidate. 4. **Sizes:** small, medium, wide.
- **States:** offline: last forecast with age; "Needs internet". Moving: one tile (now only).
- **Safety and driving rules:** the car's position is sent to a weather service only after
  an explicit opt-in on this page, rounded to about 10 km; location stays on the device
  otherwise (ADR-0009).
- **Components:** StatTile, Segmented, switch.
- **Spec refs:** [Drive modes §4.3][dm-4.3] · [UI §12.1][ui-12.1] · [launcher §9][lw-9].
- **Open questions:** **Decided (item 53):** Weather is part of the starter widget pack, not
  its own app. Which weather service it uses is still open.

### widget-setup-now-playing — Media now playing  [New]
- **Purpose:** title, artist, artwork and controls. Widget from: Media app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  Media app (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render (Split page); phone Day.
- **Content:** 1. Preview: still artwork, title and artist ≤ 30 characters,
  `skip_previous` `play_pause` `skip_next` `volume_up`. 2. **Look:** Card, Compact strip.
  3. **Data:** Source: Last used · a named source from the Media app. 4. **Sizes:** medium,
  wide, hero.
- **States:** "Needs a media app"; "Nothing playing". Moving: the `media` pane: static
  artwork, title and artist ≤ 30, play/pause/skip/volume; browsing only as a `short_list`.
- **Safety and driving rules:** no video, no scrolling text ([Drive modes §5.6][dm-5.6]).
- **Components:** Card, Button (icon).
- **Spec refs:** [Drive modes §5.6][dm-5.6] · [app model §15][am-15].
- **Open questions:** none.

### widget-setup-radio — Radio  [New]
- **Purpose:** station, presets and tuning. Widget from: Radio app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  Radio app.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render.
- **Content:** 1. Preview: the station name and "88.1 FM" with preset buttons 1–6. 2. **Look:**
  Station and presets, Station only. 3. **Options:** Presets shown 3 · 6. 4. **Sizes:**
  medium, wide.
- **States:** "No tuner fitted"; "Searching…". Moving: the `media` pane, presets as a
  `short_list` ≤ 6.
- **Safety and driving rules:** no keypad tuning while Moving.
- **Components:** Card, Button.
- **Spec refs:** [app model §15][am-15] · [UI §12.1][ui-12.1] · [launcher §9][lw-9] · [head-unit apps §3][hu-3].
- **Open questions:** **Decided ([head-unit apps §3][hu-3]):** while Moving, the `media`
  template shows the station name as the title and the DL Plus artist and title as a static
  second line (each ≤ 30); presets as a `short_list`. The widget ships with the Radio app
  (item 52).

### widget-setup-phone-favourites — Phone favourites  [New]
- **Purpose:** call a favourite in one tap. Widget from: Phone app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a row starts a
  call through the OS call session.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render; phone Day.
- **Content:** 1. Preview: names only ("Sam", "Home", "Garage"). 2. **Options:** Rows 1–6.
  3. **Sizes:** medium, wide.
- **States:** "No phone paired · Pair in Phone"; "No favourites yet". Moving: `short_list`
  ≤ 6 rows, ≤ 30 characters, no photos.
- **Safety and driving rules:** no avatars on driver-facing screens while Moving
  ([Phone & Comms §12][pc-12]).
- **Components:** ListRow, Segmented.
- **Spec refs:** [Phone & Comms §12][pc-12] · [app model §15][am-15].
- **Open questions:** none.

### widget-setup-nav-next-turn — Navigation next turn  [New]
- **Purpose:** the next manoeuvre and distance. Widget from: Navigation app.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens
  Navigation (Parked).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; hu7 Night-dim Moving render.
- **Content:** 1. Preview: `turn_right` "300 m · Bakewell Rd". 2. **Options:** Show ETA
  (on). 3. **Sizes:** small, medium.
- **States:** "No route"; "Off route · rerouting". Moving: one tile.
- **Safety and driving rules:** road names ≤ 30 characters; no search while Moving
  ([Navigation §5.2][nav-5.2]).
- **Components:** StatTile, Material Symbols turn glyphs.
- **Spec refs:** [Navigation §5.2][nav-5.2].
- **Open questions:** none.

### widget-setup-app-shortcut — App shortcut  [New]
- **Purpose:** one app shortcut as a card. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode; a tap opens the
  shortcut's route.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night setup; phone Day.
- **Content:** 1. Preview: `stethoscope` "Read faults · Diagnostics". 2. **Data:** Shortcut
  (from installed apps). 3. **Label** and **Icon**. 4. **Sizes:** small, medium.
- **States:** app removed: the widget goes with it. Moving: one tile that opens the
  target's Moving view, only if the target has one; otherwise Parked only.
- **Safety and driving rules:** opens a page; never runs an action ([UI §7][ui-7]).
- **Components:** Card, App icon.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [launcher §9][lw-9] · [launcher §5.3][lw-5.3].
- **Open questions:** none.

### widget-setup-text-label — Text label  [New]
- **Purpose:** a plain heading on a page. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day; hu7 Night.
- **Content:** 1. **Text** (≤ 120 characters, plain). 2. **Look:** Title, Kicker, Caption (type step); alignment.
  3. **Sizes:** small, wide.
- **States:** empty text refused. Moving: **Parked only**.
- **Safety and driving rules:** typing is Parked only.
- **Components:** text field, Segmented.
- **Spec refs:** [Drive modes §7.6][dm-7.6] · [launcher §9][lw-9].
- **Open questions:** none.

### widget-setup-image — Image  [New]
- **Purpose:** one image on a page. Widget from: Starter widgets.
- **Owner:** os
- **Opens from → goes to:** the picker or **Settings** → Save to edit mode.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day; hu7 Night.
- **Content:** 1. **Image:** pick a file (stored on the device only, EXIF stripped, never
  uploaded or exported). 2. **Crop**.
  3. **Dim at night** (on). 4. **Sizes:** medium, wide, hero.
- **States:** too large: "Images up to 2 MB". Moving: **Parked only**.
- **Safety and driving rules:** a layout export never carries the image (item 50;
  [Drive modes §8.2][dm-8.2]).
- **Components:** Card, crop tool (new component).
- **Spec refs:** [Drive modes §4.2][dm-4.2] · [launcher §9][lw-9].
- **Open questions:** **Decided (item 50):** images are stored on the device only and never
  exported in layouts.

<!-- links -->
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[dm-4.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#42-field-rules
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[nav-5.2]: ../../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre
[pc-12]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#12-widgets-and-drive-menu-app-model-15-contract
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[lw-9]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#9-the-starter-catalogue
[hu-3]: ../../../../specs/2026-10-07-head-unit-apps-design.md#3-radio
[lw-5.3]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#53-app-shortcuts
