---
title: "Designer brief: App framework (part F): pack pages and app errors"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, references/research/ha_integrations_dashboards.md]
summary: >
  Part F of the app-framework brief: the pages for things that are not apps once they are
  installed, and the OS error pages for apps. A widget pack lists its widgets with Add to
  home; a theme pack previews the four themes and applies; an icon pack maps apps to
  Material Symbols styles; a wallpaper pack picks a wallpaper per screen; a dashboard
  preset previews Parked and Moving and applies through the dashboard builder; a sound or
  EQ preset applies in the Audio app. The errors are an app that stopped and an app that
  needs an update for this OS version (both New, named by the app model), and an app that
  is not available on this car.
---

# App framework brief, part F: pack pages and app errors

Rules and terms: [part A](90-appframe-a.md). Packs come from the Store (`70-store-*`); each
page below opens from the Store's **Open** after install, from Settings → Apps (packs list
with the kind Chip **Pack**) and from the launcher's wallpaper and style menu
(`45-launcher-*`). Applying a pack is editing: **Park to edit** on driver-facing displays
([Drive modes §8.1][dm-8.1] R1). No pack can change the safety colours, the fault telltale,
alarm alerts or the Moving templates (R3).

### app-pack-widgets — Widget pack  [New]
- **Owner:** os (content: the pack, for example app:widgets-starter)
- **Purpose:** show every widget in the pack and add one to a home page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** 1. Header: icon, "Starter widgets", Chip **Pack**, "‹n›
  widgets". 2. Grid of live previews (Parked) bound to the active car: Gauge "Coolant",
  StatTile "Battery", tiles "RPM", "Turbo pressure", the warnings widget. Each: title, size
  Chips, "While moving: tiles" or "Parked only", **Add to home** → widget setup
  (`45-launcher-*`). 3. **App info** link.
- **States:** no car: previews show "—" with "No car connected"; a widget needs an app not
  installed: "Needs Diagnostics" with **Get it**; Moving: locked.
- **Safety and driving rules:** placing is Park to edit; previews never show fake values.
- **Components:** Card (preview), Chip, Button, Gauge, StatTile.
- **Spec refs:** [App model §15][am-15] (15.1, 15.6) · [Drive modes §7.2][dm-7.2] · [app UI model §9][ua-9] · [launcher §8][lw-8].
- **Open questions:** none.

### app-pack-theme — Theme pack  [New]
- **Owner:** os
- **Purpose:** preview a theme pack and apply it.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night and Night dim.
- **Content (top to bottom):** 1. Header, Chip **Theme**. 2. Segmented **Night · Night dim ·
  Deep night · Day** switching a preview of a home page and a Drive page. 3. What it
  changes: "Accent, surfaces, gauge style"; what it never changes, with `shield`: "Warning
  and alarm colours, text sizes". 4. **Apply** (primary) → the theme wizard
  (`45-launcher-*`) on the colours step; **Apply as is**.
- **States:** a theme failing a contrast check: **Apply** disabled, "Fails contrast in
  Night dim"; applied: Chip "In use"; Moving: locked.
- **Safety and driving rules:** tokens only, no raw colours; no glow on head units at night
  ([visual §3.1][vds-3.1], [visual §1][vds-1]).
- **Components:** Segmented, Card (preview), Button.
- **Spec refs:** [visual §3.1][vds-3.1] · [visual §1][vds-1] · [app UI model §9][ua-9] · [launcher §11][lw-11].
- **Open questions:** **Decided (item 48):** a theme pack may bring accents beyond cyan, as
  validated colour sets that pass contrast in every theme; warning and alarm colours never
  change.

### app-pack-icons — Icon pack  [New]
- **Owner:** os
- **Purpose:** preview and apply an icon pack: a glyph set mapped to Material Symbols names
  (item 49); a name the pack lacks falls back to Material outlined.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Header, Chip **Icons**. 2. A before and after grid of the
  dock and the app drawer. 3. Style line: "Outlined · weight ‹n› · fill off". 4. **Apply**;
  "Your own icon changes are kept" caption.
- **States:** applied; Moving: locked.
- **Safety and driving rules:** safety items keep their icons; user overrides win
  ([App model §15][am-15] 15.8).
- **Components:** Card, Button.
- **Spec refs:** [visual §6][vds-6] · [Drive modes §7.6][dm-7.6] · [app UI model §9][ua-9] · [launcher §11][lw-11].
- **Open questions:** **Decided (item 49):** yes, an icon pack ships its own glyphs (SVG, no
  images or code), each mapped to a Material Symbols name; safety icons never change.

### app-pack-wallpaper — Wallpaper pack  [New]
- **Owner:** os
- **Purpose:** pick a wallpaper from the pack for each screen.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. Grid of wallpapers. 2. Preview behind a home page and
  the app drawer, in Night and Day. 3. **Set** → "This screen · All my screens".
- **States:** dimmed preview in Night dim; Moving: locked.
- **Safety and driving rules:** a wallpaper shows on home pages only, dimmed at night, and
  never behind a Moving template or Drive page.
- **Components:** Card, Segmented, Button.
- **Spec refs:** [visual §1][vds-1] · [visual §3.1][vds-3.1] · [app UI model §9][ua-9] · [launcher §11][lw-11].
- **Open questions:** **Decided (item 19):** on driver-facing displays the Moving sections
  draw on the plain `bg` surface, never on a wallpaper.

### app-pack-preset — Dashboard preset  [New]
- **Owner:** os
- **Purpose:** preview a dashboard preset Parked and Moving, then apply it with the builder.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night, phone Night.
- **Content (top to bottom):** 1. Header, "Off-road (D2)", Chip **Preset**. 2. Side by
  side: Parked and Moving previews on the active car's signals (Pitch, Roll, Low range and
  diff lock, Altitude, breadcrumb map), "What hides while moving" list. 3. Checks: `ok`
  "Fits HU-7"; `warn` "Pitch and roll: needs the node's IMU"; `warn` "Low range: only in a
  SLABS session"; failed rules named as in `drive-mode-preview`. 4. **Apply with the
  builder** → the dashboard builder (`45-launcher-*`) as a new home page.
- **States:** a signal missing on this car ("—", "Not available on this car"); Moving:
  locked.
- **Safety and driving rules:** the preset passes the layout validator; nothing replaces an
  existing page without the builder's confirm.
- **Components:** Card, Chip (status), Button.
- **Spec refs:** [Drive modes §5.9][dm-5.9] · [Drive modes §8.4][dm-8.4] · [app UI model §9][ua-9] · [launcher §10.1][lw-10.1].
- **Open questions:** none.

### app-pack-sound — Sound or EQ preset  [New]
- **Owner:** os (applies in app:audio)
- **Purpose:** show the preset's curve and send it to Audio.
- **Layout classes:** phone · tablet · hu7 · hu9 · huwide. **Draw first:** hu7 Night.
- **Content (top to bottom):** 1. Header, Chip **Sound**. 2. The curve (Area line) with
  bands. 3. **Apply in Audio** → the Audio app's EQ page (`80-hu-*`).
- **States:** Audio not installed: **Get Audio**; Moving: locked.
- **Safety and driving rules:** Parked only; chimes and alarm sounds are not affected.
- **Components:** Area line, Button.
- **Spec refs:** [visual §8][vds-8] · [app UI model §9][ua-9] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### app-error-stopped — App stopped  [New]
- **Owner:** os
- **Purpose:** say an app or widget stopped, keep the rest working, offer a way back.
- **Opens from → goes to:** in the app's place → **Reopen**, **App info**, **App log**.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (page), hu7 Night dim Moving (widget placeholder), phone Night.
- **Content (top to bottom):** page: `error` icon (`alarm`), "Diagnostics stopped", "The
  rest of Ostler is working. Fault warnings still show.", **Reopen**, **App info**. Widget:
  the widget's frame with "Widget stopped" and its title; after three stops in a drive,
  the placeholder stays until Parked.
- **States:** Moving: widget placeholder only, no buttons; Parked: buttons.
- **Safety and driving rules:** the strip, dock, Drive pages and safety items keep running
  ([App model §15][am-15] 15.6).
- **Components:** Card (tone), Button.
- **Spec refs:** [App model §5][am-5] · [App model §15][am-15] 15.6.
- **Open questions:** none.

### app-error-needs-update — Needs an update  [New]
- **Owner:** os
- **Purpose:** explain that the app and this OS version do not match, and fix it.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** Card in `warn-bg`: "Maintenance needs an update to work with
  this Ostler" or "Maintenance needs Ostler ‹range›"; Buttons **Update app** or **Update
  Ostler** (→ `settings-updates`), **Turn off**.
- **States:** no update yet: "Waiting for the publisher"; offline: "Needs the internet";
  not owner: "Ask the owner"; Moving: the card shows, buttons wait for Parked.
- **Safety and driving rules:** updates only Parked.
- **Components:** Card (tone), Button.
- **Spec refs:** [App model §7][am-7] (versioning) · [App model §4.2][am-4.2].
- **Open questions:** none.

### app-error-incompatible — Not available on this car  [Proposed]
- **Owner:** os
- **Why the app needs it:** `requires` hides chrome when a device or signal is missing;
  when the owner opens such an app on purpose it must say why.
- **Purpose:** explain why an app cannot run with this car or setup.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night, hu7 Night.
- **Content (top to bottom):** icon, title "Security isn't available on this car", the
  reasons as ListRows: "Needs an Ostler node. This car is read through an adapter." Other
  examples: "Camera needs a camera"; "Navigation needs the Brain". Buttons: **What's
  needed** (→ the hardware pages, `20-hardware-*`), **Switch car**, **App info**.
- **States:** another car in the Garage fits: "Works with ‹car›"; Moving: locked.
- **Safety and driving rules:** none.
- **Components:** ListRow, Button.
- **Spec refs:** [App model §4.2][am-4.2] · [App model §14][am-14] (14.1) · [UI §6][ui-6].
- **Open questions:** none.

<!-- refs -->
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[am-15]: ../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-5]: ../../../../specs/2026-10-06-app-model-design.md#5-lifecycle-and-isolation
[am-7]: ../../../../specs/2026-10-06-app-model-design.md#7-optional-apps-from-their-own-repos
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[ua-9]: ../../../../specs/2026-10-07-app-ui-model-design.md#9-object-kinds
[lw-8]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#8-the-widget-sdk-contract
[lw-11]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#11-the-theme-wizard
[lw-10.1]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#101-presets
[hu-4]: ../../../../specs/2026-10-07-head-unit-apps-design.md#4-audio
