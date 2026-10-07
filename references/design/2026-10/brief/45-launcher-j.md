---
title: "Designer brief 45-j — launcher: the theme wizard (Wallpaper & style), wallpaper, colours and icon packs"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Seventh launcher brief file: the theme wizard, Android's Wallpaper & style. It gives the
  step list and the blocks for the hub page, wallpaper and background (built in, from the
  Store, or the owner's own image, dimmed at night and never behind a Moving template),
  colours (accent palette within the token rules, and Night, Day, Auto or Deep night) and
  icon packs (alternative glyph sets that map to Material Symbols names, with fallbacks;
  safety telltales never change). Gauge styles, text size, the preview and Home settings
  follow in 45-k.
---

# 45-j — Theme wizard: hub, wallpaper, colours and icons

Back to [45-a](45-launcher-a.md). The theme engine is part of the OS; the default theme and
theme packs are apps from the Store (owner direction). Every choice here produces **token
sets**, never raw colours, and each must pass the visual spec's contrast checks in all four
themes ([visual §3.1][vds-3.1]). Status colours (ISO 2575) never change. On a driver-facing
display the wizard is Park to edit ([Drive modes §8.1][dm-8.1] R1).

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `launcher-theme-wallpaper` | picks a wallpaper | image too large or unreadable → "Pick an image under 8 MB (JPEG or PNG)" |
| 2 | `launcher-theme-colours` | picks an accent and Night, Day or Auto | a pack's accent fails contrast → not offered, with "Doesn't meet contrast" |
| 3 | `launcher-theme-icons` | picks an icon pack | a pack lacks an icon → that icon falls back to Material Symbols |
| 4 | `launcher-theme-gauges` | picks a gauge style (45-k) | — |
| 5 | `launcher-theme-text` | picks a text size (45-k) | a size would clip on this screen → not offered |
| 6 | `launcher-theme-preview` | checks Home and the Drive page, then applies (45-k) | save fails → nothing changes; **Try again** |

### launcher-theme — Wallpaper & style  [Proposed]
- **Why the app needs it:** the owner asked for a theme wizard; the visual spec fixes one
  look and has no user-facing style page beyond Night, Day and Auto.
- **Purpose:** the hub for every look setting, also run as a wizard in first setup.
- **Owner:** os
- **Opens from → goes to:** **Wallpaper & style** in the launcher menu; Settings → Display →
  Wallpaper & style (30-settings-a); setup step 12; **Change the theme** at the end of the
  builder. Rows go to steps 1–6; in setup **Next** walks them in order.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day; phone Night.
- **Content:** 1. A live **preview strip**: the current home page and the Drive page side by
  side. 2. Rows with the current value: **Wallpaper** "Contour", **Colours** "Cyan · Auto",
  **Icons** "Material outlined", **Gauges** "Calm", **Text size** "Default". 3. **Get themes**
  → Store theme packs. 4. **Use the default theme**.
- **States:** a Store pack updating: "Updating theme pack". Offline: Get themes greyed.
  Moving: locked view.
- **Safety and driving rules:** nothing here changes a Moving template's floors, a status
  colour or a safety icon ([visual §1][vds-1]).
- **Components:** ListRow, Card (preview), Button.
- **Spec refs:** [visual §1][vds-1] · [visual §3.1][vds-3.1] · [UI §12.5][ui-12.5].
- **Open questions:** should a theme be per display, per profile, or both? This brief says
  per profile and display, like layouts ([Drive modes §8.3][dm-8.3]).

### launcher-theme-wallpaper — Wallpaper and background  [Proposed]
- **Why the app needs it:** wallpapers are new in the owner's direction; no spec covers
  images behind the home pages.
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
  3. **Your own image:** **Choose image** (Parked; stored on the Brain or the device, never
     uploaded), then **Crop** for this screen's size.
  4. **Dim at night** (on, and locked on for head units): in Night dim and Deep night the
     wallpaper sits under the `overlay` scrim at 80 %.
  5. **Apply to:** This screen · All my screens.
- **States:** image error as in the table. A light image in Night: a note "Dimmed so text stays
  readable". Moving: locked view.
- **Safety and driving rules:** on head units the Drive carousel and every Moving template
  draw on plain `bg`, never on a wallpaper; widgets keep their cards, so text contrast never
  depends on the wallpaper ([visual §1][vds-1], [visual §5][vds-5]).
- **Components:** Card (thumbnail grid), crop tool (new component), switch, Segmented.
- **Spec refs:** [visual §1][vds-1] · [visual §5][vds-5] · [UI §12.5][ui-12.5].
- **Open questions:** wallpaper images are user files; confirm they stay out of exported
  layouts (as images are refused in `ostler.layout/1`).

### launcher-theme-colours — Colours and light or dark  [Proposed]
- **Why the app needs it:** the visual spec has one cyan accent; a colour choice needs an
  owner decision and token-set rules.
- **Purpose:** choose the accent and the theme mode.
- **Owner:** os
- **Opens from → goes to:** the hub or step 2.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:**
  1. **Theme:** Segmented **Night · Day · Auto**; **Deep night (OLED)** switch; on head
     units a line "After dusk the screen uses Night dim".
  2. **Accent:** swatches as named token sets: **Cyan** (default), plus those from installed
     theme packs (for example an amber accent). Each swatch has a name and passed every
     contrast pair; failing ones are not shown.
  3. **Map style follows theme** switch (map theme stays independent, [UI §13.5][ui-13.5]).
  4. A small preview card: a button, a selected chip and a gauge in and out of range.
- **States:** a pack accent too close to a status colour is refused ("Too close to the
  warning colour"). Moving: locked view.
- **Safety and driving rules:** `ok`, `warn`, `alarm` never change; data ramps never use the
  accent; no glow on head units at night ([visual §3.3][vds-3.3], [visual §5][vds-5]).
- **Components:** Segmented, switch, colour swatch (new component), Card.
- **Spec refs:** [visual §3.1][vds-3.1] · [visual §3.3][vds-3.3] · [UI §13.5][ui-13.5].
- **Open questions:** owner decision: allow accents other than cyan, as validated token
  sets?

### launcher-theme-icons — Icon packs  [Proposed]
- **Why the app needs it:** the owner asked for icon packs; the visual spec allows one icon
  set, so this needs an owner decision.
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
  3. A note: "Warning lights and alarm icons don't change."
- **States:** pack missing icons: the fallback line. Moving: locked view.
- **Safety and driving rules:** the fault telltale, warning lights and alarm glyphs are
  never replaced; no emoji or images as icons ([visual §6][vds-6], [Drive modes §8.1][dm-8.1]
  R3).
- **Components:** Card, App icon (new).
- **Spec refs:** [visual §6][vds-6] · [Drive modes §7.6][dm-7.6].
- **Open questions:** owner decision: change the one-icon-set rule to "Material Symbols
  names, any mapped glyph set, safety glyphs fixed".

<!-- links -->
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
