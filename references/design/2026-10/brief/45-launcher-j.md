---
title: "Designer brief 45-j — launcher: the theme wizard (Wallpaper & style), wallpaper, colours and icon packs"
area: references
status: draft
version: 0.3
updated: 2026-10-08
depends_on: [specs/2026-10-07-theme-engine-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Seventh launcher brief file: the theme wizard, Android's Wallpaper & style. It follows the
  theme engine spec: the wizard picks the OS skin and its options, widget packs, the icon
  pack, the background and the sound pack, and the background belongs to the user. It gives
  the step list and the blocks for the hub page, wallpaper and background (built in, from
  the Store, or the owner's own image), colours and mode (any accent the skin offers; Night,
  Day, Auto or Deep night) and icon packs (glyph sets mapped to Material Symbols names, with
  fallbacks). Safety comes from the engine's Drive-mode render check, protected surfaces and
  required parts. Gauge styles, text size, the preview and Home settings follow in 45-k. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 45-j — Theme wizard: hub, wallpaper, colours and icons

Back to [45-a](45-launcher-a.md). The [theme engine spec][te] decides what a theme is: an
OS skin, plus separate widget, icon, wallpaper and sound packs, or a bundle of them. The
engine is part of the OS; skins and packs come from the Store. Skins can change anything,
status colours included, and look the same while Moving ([visual §13][vds-13]). Safety comes
from the engine's Drive-mode render check, protected surfaces and required parts (its
decisions 5–7). The background belongs to the user: choosing a skin never changes it. On a
driver-facing display the wizard is Park to edit ([Drive modes §8.1][dm-8.1] R1).

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `launcher-theme-wallpaper` | picks a wallpaper | image too large or unreadable → "Pick an image under 8 MB (JPEG or PNG)" |
| 2 | `launcher-theme-colours` | picks the OS skin, its options, an accent and Night, Day or Auto | the skin fails the Drive-mode render check → the Drive page keeps the built-in look, with a note saying why |
| 3 | `launcher-theme-icons` | picks an icon pack | a pack lacks an icon → that icon falls back to Material Symbols |
| 4 | `launcher-theme-gauges` | picks a gauge style (45-k) | — |
| 5 | `launcher-theme-text` | picks a text size (45-k) | a size would clip on this screen → not offered |
| 6 | `launcher-theme-preview` | checks Home and the Drive page, then applies (45-k) | save fails → nothing changes; **Try again** |

### launcher-theme — Wallpaper & style  [New]
- **Purpose:** the hub for every look setting, also run as a wizard in first setup.
- **Owner:** os
- **Opens from → goes to:** **Wallpaper & style** in the launcher menu; Settings → Display →
  Wallpaper & style (30-settings-a); setup step 12; **Change the theme** at the end of the
  builder. Rows go to steps 1–6; in setup **Next** walks them in order.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day; phone Night.
- **Content:** 1. A live **preview strip**: the current home page and the Drive page side by
  side. 2. Rows with the current value: **OS skin** "Night", **Wallpaper** "Contour",
  **Colours** "Cyan · Auto", **Icons** "Material outlined", **Gauges** "Calm",
  **Sounds** "Default", **Text size** "Default". 3. **Get themes** → Store skins, packs and
  bundles. 4. **Use the default theme**.
- **States:** a Store pack updating: "Updating theme pack". Offline: Get themes greyed.
  Moving: locked view.
- **Safety and driving rules:** a skin may restyle anything, but the Moving content rules
  stay, and the Drive-mode render check, protected surfaces and required parts apply
  ([theme engine][te] decisions 5–7).
- **Components:** ListRow, Card (preview), Button.
- **Spec refs:** [visual §1][vds-1] · [visual §3.1][vds-3.1] · [UI §12.5][ui-12.5] · [launcher §11][lw-11].
- **Open questions:** should a theme be per display, per profile, or both? This brief says
  per profile and display, like layouts ([Drive modes §8.3][dm-8.3]).

### launcher-theme-wallpaper — Wallpaper and background  [New]
- **Purpose:** choose what sits behind the home pages.
- **Owner:** os
- **Opens from → goes to:** the hub or wizard step 1. **Set** returns or goes to step 2.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with Contour; hu7 Night-dim showing the dimmed wallpaper; phone Day.
- **Content:**
  1. **Built in** (drawn from tokens): **Plain** (`bg`), **Contour** (topographic lines in
     `line`), **Grid** (fine `line` grid), **Dusk** (a flat `surface-1` to `bg` split; no
     gradient on head units).
  2. **From the Store:** wallpaper packs, each with a thumbnail and **Get**.
  3. **Your own image:** **Choose image** (Parked; stored on the device only, EXIF stripped,
     never uploaded and never exported in layouts, item 50), then **Crop** for this screen's
     size.
  4. **Dim at night** (on by default): in Night dim and Deep night the wallpaper sits
     under the `overlay` scrim. Dim, blur, scrim and position are the user's sliders.
  5. **Apply to:** This screen · All my screens.
- **States:** image error as in the table. A light image in Night: a note "Dimmed so text stays
  readable". Moving: locked view.
- **Safety and driving rules:** the background belongs to the user; choosing a skin never
  changes it unless "Use this theme's background" is ticked. It shows the same while Moving;
  the Drive-mode render check guards contrast ([theme engine][te] §2.3, decision 5).
- **Components:** Card (thumbnail grid), crop tool (new component), switch, Segmented.
- **Spec refs:** [visual §1][vds-1] · [visual §5][vds-5] · [UI §12.5][ui-12.5] · [launcher §11][lw-11].
- **Open questions:** **Decided (item 50):** wallpaper images are stored on the device only
  and never exported in layouts.

### launcher-theme-colours — Colours and light or dark  [New]
- **Purpose:** choose the accent and the theme mode.
- **Owner:** os
- **Opens from → goes to:** the hub or step 2.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:**
  1. **Theme:** Segmented **Night · Day · Auto**; **Deep night (OLED)** switch; on head
     units a line "After dusk the screen uses Night dim".
  2. **OS skin:** the 22 built-in skins and installed ones as cards, then **Options** for
     the skin's own choices (for example Heritage's gauge faces and dial layout).
  3. **Accent:** any accent the skin offers; **Cyan** is the Night default.
  4. **Map style follows theme** switch (map theme stays independent, [UI §13.5][ui-13.5]).
  5. A small preview card: a button, a selected chip and a gauge in and out of range.
- **States:** a skin that fails the Drive-mode render check: the Drive page keeps the
  built-in look, with the reason. Moving: locked view.
- **Safety and driving rules:** skins may restyle status colours, glow and blur; the
  Drive-mode render check (telltale and alarm visible, Drive digits ≥ 56 px, contrast
  ≥ 4.5:1) guards them ([theme engine][te] decision 5, [visual §13][vds-13]).
- **Components:** Segmented, switch, colour swatch (new component), Card.
- **Spec refs:** [visual §3.1][vds-3.1] · [visual §3.3][vds-3.3] · [UI §13.5][ui-13.5] · [launcher §11][lw-11].
- **Open questions:** **Decided (item 48), superseded 2026-10-08:** any accent; no locked
  tokens ([theme engine][te], [visual §13][vds-13]).

### launcher-theme-icons — Icon packs  [New]
- **Purpose:** choose the look of app and dock icons.
- **Owner:** os
- **Opens from → goes to:** the hub or step 3.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Night.
- **Content:**
  1. Packs as cards with eight sample icons (Home, Diagnostics, Trips, Security, Map,
     Phone, Store, App drawer): **Material outlined** (default), **Material rounded**,
     **Material sharp**, and packs from the Store.
  2. Each pack is an **alternative glyph set that maps to Material Symbols names**: an icon
     a pack lacks falls back to the Material outlined glyph; the card shows "Covers 212 of
     300 icons".
  3. A note: "Warning lights and alarm icons must stay visible in every pack."
- **States:** pack missing icons: the fallback line. Moving: locked view.
- **Safety and driving rules:** packs map to Material Symbols names and may restyle the
  safety glyphs, but the telltale and alarm are required parts and must pass the Drive-mode
  render check ([theme engine][te] decisions 5 and 7).
- **Components:** Card, App icon (new).
- **Spec refs:** [visual §6][vds-6] · [Drive modes §7.6][dm-7.6] · [launcher §11][lw-11] ·
  [app UI model §9][ua-9].
- **Open questions:** **Decided (item 49), superseded 2026-10-08:** icon packs map to
  Material Symbols names; safety glyphs are required parts, not fixed glyphs
  ([theme engine][te]).

<!-- links -->
[te]: ../../../../specs/2026-10-07-theme-engine-design.md
[vds-13]: ../../../../specs/2026-10-07-visual-design-system-design.md#13-design-language-themes-amendment-2026-10-07
[dm-7.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#76-icons-and-names-v02
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[ui-12.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#125-visual-design-system-changes-2-principle-7
[ui-13.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-3.3]: ../../../../specs/2026-10-07-visual-design-system-design.md#33-data-ramps-and-chart-colours-datatokensjson
[vds-5]: ../../../../specs/2026-10-07-visual-design-system-design.md#5-space-radius-elevation-glow-motion
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[lw-11]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#11-the-theme-wizard
[ua-9]: ../../../../specs/2026-10-07-app-ui-model-design.md#9-object-kinds
