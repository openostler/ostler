---
title: "Designer brief 45-h — launcher: the home pages list, the page editor, preview, import and export, and preset dashboards"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Fifth launcher brief file: managing home pages and adding preset dashboards. It
  re-expresses four existing Drive-mode screens in launcher terms: the home pages list (the
  flat overview of all pages: reorder, default page, In Drive rotation, delete, share), the
  page editor's Moving section, the Parked and Moving preview with failed rules in words,
  and import and export as files, links and QR. It then adds the preset gallery and a preset
  preview, where each of the seven presets (Diagnostic, Dashboard, Map, Convoy / Ride,
  Off-road D2, Split / Media, Minimal / Night) adds its pages to the one flat carousel.
---

# 45-h — Home pages list, page editor, preview, import and presets

Back to [45-a](45-launcher-a.md). One flat carousel: a preset **adds pages**; it is not a
named set (this replaces the page-set model in 40-drive-e, 40-drive-f and 40-drive-g).
Every screen here is Park to edit on a driver-facing display and shows the locked view while
Moving (40-drive-b; [Drive modes §8.1][dm-8.1] R1).

### drive-modes-list — Home pages list  [Existing]
- **Purpose:** the overview of every home page on this screen: Android's page overview,
  plus which pages appear while driving.
- **Owner:** os
- **Opens from → goes to:** **Edit pages** in the launcher menu; long-press on the page
  dots; **Edit pages…** in the Drive page list (Parked). A page opens in edit mode; **Add
  pages** opens `launcher-presets`; **Build dashboards** opens the builder (45-i).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Night; desktop Night with the class picker.
- **Content (top to bottom):**
  1. A row of **page thumbnails** in carousel order (drag to reorder): Home, Cluster, Map,
     Tiles, Minimal, Tilt, Trail. Each: a live mini render, the name (≤ 30), the default
     `home` glyph on one.
  2. Per page, a menu: **Set as default page**, **In Drive** switch (with the Moving counter
     "5 of 6 tiles, 1 of 2 panes"), **Rename**, **Icon**, **Duplicate**, **Share**, **Delete**
     (an empty page deletes at once; a full page asks, Cancel focused, with Undo for 30 days).
  3. **Drive rotation** strip: the In Drive pages in tap order (≤ 4 cycle; the page list
     shows up to 6).
  4. Buttons **Add pages** · **Import** · **Build dashboards**.
- **States:** a page needing a missing app: "Needs Social · Get in Store", hidden from Drive.
  A page whose Moving section fails: `warn` chip "Fix for driving first". Loading:
  thumbnail skeletons. Moving: locked view.
- **Safety and driving rules:** Home cannot be deleted; page 1 cannot be In Drive; every In
  Drive page has a valid Moving section ([Drive modes §8.2][dm-8.2]).
- **Components:** Page thumbnail (new component), switch, ListRow (drag), Sheet, Button.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §5.9][dm-5.9] ·
  [Drive modes §8.4][dm-8.4].
- **Open questions:** none.

### drive-mode-editor — Page editor: Moving section  [Existing]
- **Purpose:** for a page that is In Drive, choose which widgets the driver sees while
  Moving and in what order.
- **Owner:** os
- **Opens from → goes to:** edit mode on an In Drive page → **Moving section** tab; the
  `warn` chip on a page. **Preview** → `drive-mode-preview`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Cluster page; desktop Night editing HU-5.
- **Content:**
  1. The Parked grid of the page (as edit mode).
  2. **Moving strip** below: the widgets in the Moving section in reading order (drag to
     reorder), each with a pin `push_pin` to add or remove: Speed (hero), RPM, Coolant,
     Turbo pressure, Battery; Graph shows "Parked only" and cannot be pinned.
  3. Counter Chip "Moving: 5 of 6 tiles · 0 of 2 panes" per class.
  4. Class tabs (HU-5, HU-7, HU-9/10, HU-wide, phone) because each class is authored, never
     scaled.
- **States:** over the limit: the pin is refused with the rule in words. Moving: locked view.
- **Safety and driving rules:** ≤ 6 tiles; panes per class; no Parked-only widget
  ([Drive modes §4.3][dm-4.3], R2).
- **Components:** Segmented (class tabs), StatTile, Chip (counter), Button.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §4.3][dm-4.3] ·
  [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

### drive-mode-preview — Page preview: Parked and Moving  [Existing]
- **Purpose:** see exactly what the driver will see, and why anything fails.
- **Owner:** os
- **Opens from → goes to:** **Preview** in the edit bar, the page editor, a preset preview
  and an import. **Back** returns.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with one failed rule; phone Day.
- **Content:** 1. Two panes at the target class's size: **Parked** and **While driving**
  (Night dim, the template render). 2. Class Segmented. 3. **Rules** list in words, `warn`
  icon each: "Graph shows only when parked", "Map pane too small on HU-5: 300 px, needs 340".
- **States:** all pass: `ok` "Ready for driving". Moving: locked view.
- **Safety and driving rules:** the Moving pane uses the same renderer as the car
  ([Drive modes §8.1][dm-8.1] R2).
- **Components:** Card, ListRow, Segmented.
- **Spec refs:** [Drive modes §7.4][dm-7.4] · [Drive modes §8.2][dm-8.2].
- **Open questions:** none.

### drive-layout-import — Import and export pages  [Existing]
- **Purpose:** share pages as a file, link or QR, and add pages from one.
- **Owner:** os
- **Opens from → goes to:** **Share** or **Import** in the home pages list. Import →
  preview → **Add pages** puts them at the end of the carousel, not In Drive.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night export; hu7 Night import preview.
- **Content:** **Export:** pages to include (ticks), **Save as file**, **Copy link**, **QR**,
  **Share**; licence line "CC BY-SA 4.0"; author (optional). **Import:** **Open file**,
  **Paste link**, **Scan QR**; then the preview (`drive-mode-preview`), the apps it wants
  ("Needs Social"), warnings, **Add pages**.
- **States:** refused file: 40-drive-h (`drive-layout-import-error`). Offline: file and QR
  work. Moving: locked view.
- **Safety and driving rules:** export strips identity (no VIN, places or plates) and
  never carries images: wallpapers and Image widgets stay on the device (item 50)
  ([Drive modes §8.4][dm-8.4], [Drive modes §8.2][dm-8.2]).
- **Components:** Sheet, Button, Card (preview).
- **Spec refs:** [Drive modes §8.4][dm-8.4].
- **Open questions:** **Decided ([Store §4][st-4]):** the Store hosts shared pages as
  dashboard preset items, checked by the layout validator.

### launcher-presets — Preset dashboards  [New]
- **Purpose:** a gallery of the seven presets, each adding ready-made pages.
- **Owner:** os
- **Opens from → goes to:** **Add pages** in the home pages list; the builder's templates
  step (45-i); a card opens `launcher-preset-preview`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content:** one card per preset with a live thumbnail of its first page at this class,
  its name, the pages it adds and needs: **Dashboard** (Cluster, Map) · **Diagnostic**
  (Tiles, System) · **Map** (Map) · **Convoy / Ride** (Map and talk, Ride; needs Social) ·
  **Off-road D2** (Tilt, Trail; "Made for the D2") · **Split / Media** (Split; needs a media
  app) · **Minimal / Night** (Minimal). A badge **Added** on presets already used. Footer:
  **More presets in the Store**.
- **States:** a preset needing a missing app: "Needs Social · Get in Store". Moving: locked.
- **Safety and driving rules:** every preset passes the Moving validator for every class
  ([Drive modes §5][dm-5]).
- **Components:** Card, Page thumbnail (new), Chip (needs), Button.
- **Spec refs:** [Drive modes §5][dm-5] · [Drive modes §5.8][dm-5.8].
- **Open questions:** none.

### launcher-preset-preview — Preset preview  [New]
- **Purpose:** see a preset's pages before adding them.
- **Owner:** os
- **Opens from → goes to:** a preset card. **Add pages** → back to the home pages list
  with the new pages highlighted; **Add and use in Drive** also marks them In Drive.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Off-road D2; phone Night.
- **Content:** 1. Title, description ("Pitch, roll, low range, altitude and the trail").
  2. Pages as a mini carousel with dots, each Parked and While driving. 3. **Data on this
  car**, honestly: Low range "SLABS · proven · only in a SLABS session"; Pitch, roll "Needs
  the node's IMU"; Altitude "GPS". 4. Buttons.
- **States:** already added: **Add again** makes copies. Moving: locked view.
- **Safety and driving rules:** as the preview.
- **Components:** Card, Page dots, ListRow, Button.
- **Spec refs:** [Drive modes §5.5][dm-5.5] · [Drive modes §8.3][dm-8.3].
- **Open questions:** none.

<!-- links -->
[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#5-the-seven-presets
[dm-5.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[dm-5.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#58-faces-per-preset
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-7.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#82-validation
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[dm-8.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#84-import-and-export
[st-4]: ../../../../specs/2026-10-07-store-design.md#4-what-the-store-hosts
