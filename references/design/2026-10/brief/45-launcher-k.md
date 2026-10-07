---
title: "Designer brief 45-k — launcher: gauge styles, text size, the theme preview and Home settings"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Last launcher brief file. It finishes the theme wizard with gauge style packs (calm by
  default, never glowing or using the accent for a value), text size (larger steps only,
  never below the floors, refused where a number would clip) and the preview of a theme on
  a home page and the Drive page before applying. It then gives Home settings: grid size,
  dock size and position, labels, screen rotation, the default page and the Drive rotation.
  Examples use the Discovery 2 Td5 Cluster page.
---

# 45-k — Gauge styles, text size, theme preview and Home settings

Back to [45-a](45-launcher-a.md); the theme wizard's step list is in
[45-j](45-launcher-j.md). Park to edit applies on a driver-facing display
([Drive modes §8.1][dm-8.1] R1).

### launcher-theme-gauges — Gauge style  [Proposed]
- **Why the app needs it:** the owner asked for gauge style packs; the visual spec defines
  one gauge.
- **Purpose:** restyle every gauge at once.
- **Owner:** os
- **Opens from → goes to:** the theme hub or step 4; the line in the style picker (45-d).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; hu7 Night-dim Moving sample.
- **Content:** 1. Packs as cards, each showing Coolant 88 °C in range and 108 °C at
  Warning: **Calm** (default: 240° arc, `band` normal range, `text-2` value arc), **Classic**
  (ticks and numerals), **Bold** (12 px track on phone, 16 px on HU), packs from the Store.
  2. A **While driving** sample beside each.
- **States:** a Store pack that breaks a rule (glow, accent value, animation) is refused at
  install, never listed. Moving: locked view.
- **Safety and driving rules:** calm gauges: status colour and word only out of range; no
  glow; ≤ 4 Hz stepped while Moving ([visual §8][vds-8], [Drive modes §4.3][dm-4.3]).
- **Components:** Card, Gauge.
- **Spec refs:** [visual §8][vds-8] · [visual §1][vds-1].
- **Open questions:** none.

### launcher-theme-text — Text size  [Proposed]
- **Why the app needs it:** larger text helps older eyes and bumpy roads; the visual spec
  sets the type per class with no user step.
- **Purpose:** make text larger.
- **Owner:** os
- **Opens from → goes to:** the hub or step 5; Settings → Accessibility (30-settings files).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day; hu7 Night.
- **Content:** 1. Segmented **Default · Large · Larger** (one or two type steps up).
  2. Sample: a list row, a tile "Turbo pressure 1.2 bar" and a dock label. 3. Line: "Some
  widgets may need a larger size."
- **States:** a step that would make a placed widget clip on this screen is still allowed,
  but the widget shows "Too small for this text size · Resize" in edit mode. Moving: locked
  view.
- **Safety and driving rules:** never smaller than the floors (12 px; 18 px Parked HU;
  24 px Moving; Drive digits ≥ 56 px) ([visual §4][vds-4]).
- **Components:** Segmented, ListRow, StatTile.
- **Spec refs:** [visual §4][vds-4] · [shell input §10][si-10].
- **Open questions:** does Larger apply inside the Moving templates too, or only Parked?

### launcher-theme-preview — Theme preview and apply  [Proposed]
- **Why the app needs it:** a theme must be seen on Home and on the Drive page before it
  applies, so night readability is checked first.
- **Purpose:** compare before and after, then apply.
- **Owner:** os
- **Opens from → goes to:** step 6 of the wizard. **Apply** → the home page; **Back** → the
  last step; **Undo** on the toast after applying.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; hu7 Night-dim; phone Day.
- **Content:** 1. Two previews at this screen's size: **Home** (with the wallpaper) and the
  **Drive page** (Cluster, on plain `bg`). 2. Segmented **Night · Night dim · Day** to check
  each. 3. A summary list of the choices. 4. **Apply** (primary), **Back**.
- **States:** saving: "Saving…"; error: "Couldn't apply. Your old theme is kept." Moving:
  locked view.
- **Safety and driving rules:** the Drive page preview shows no wallpaper, no glow and the
  fixed status colours ([visual §1][vds-1]).
- **Components:** Card (preview), Segmented, ListRow, Button.
- **Spec refs:** [visual §1][vds-1] · [visual §3.1][vds-3.1].
- **Open questions:** none.

### launcher-home-settings — Home settings  [Proposed]
- **Why the app needs it:** Android's Home settings hold grid, dock and rotation choices;
  the specs fix the grid per class and have no such page.
- **Purpose:** the launcher's own settings for this screen.
- **Owner:** os
- **Opens from → goes to:** **Home settings** in the launcher menu; Settings → Display →
  Home (30-settings files). Rows go to the dock editor, the home pages list or sheets.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. **Grid size:** HU-7 "6 × 4 (default) · 4 × 3 (larger)"; phone "4 × 6 · 4 × 5";
     tablet "8 × 6 · 6 × 4". Never denser than the spec grid on a head unit.
  2. **Dock:** Size Standard · Large (HU 96 → 112 px on HU-7); Position Side · Bottom
     (tablet, desktop and HU-wide only; side is the default on head units); **Edit dock** →
     `shell-rail-editor`.
  3. **Labels:** Show app names on home pages (on) · in the dock (on).
  4. **Screen rotation:** Allow rotation (phone and tablet only).
  5. **Default page:** "Home" → the home pages list.
  6. **Drive rotation:** the In Drive pages in tap order → the home pages list.
  7. **Add new apps' icons to home** (off; they always go to the app drawer).
  8. **Lock car layouts** (owner only; read-only for others) (30-settings files).
- **States:** a grid change that would push widgets off a page: "Some widgets will move to a
  new page" with Cancel focused. Moving: locked view.
- **Safety and driving rules:** grid and dock sizes keep 76 px targets and the Moving tile
  minimums ([Drive modes §4.4][dm-4.4]).
- **Components:** ListRow, Segmented, switch, Sheet.
- **Spec refs:** [Drive modes §4.4][dm-4.4] · [Drive modes §7.3][dm-7.3] ·
  [Drive modes §8.3][dm-8.3].
- **Open questions:** should a bottom dock be offered on HU-7 and smaller head units? This
  brief offers it only on HU-wide.

<!-- links -->
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-4.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#44-grids-and-minimum-sizes-per-class
[dm-7.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[si-10]: ../../../../specs/2026-10-07-shell-input-design.md#10-accessibility
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
