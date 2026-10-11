---
title: "Designer brief — the Ostler shell: tile frame and layouts, top strip and menus, driving rules, warnings and input, states and hand-offs (114 frames)"
area: references
status: draft
version: 1.0
updated: 2026-10-11
depends_on: [decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, specs/2026-10-11-gateway-settings-design.md, specs/2026-10-07-shell-input-design.md, references/research/responsive_tile_sizes.md, references/design/2026-10/brief/00-direction-mfd.md, references/design/2026-10/brief/00-structure.md, references/design/2026-10/mfd/README.md]
summary: >
  The brief for the designer who will design the Ostler shell (owner, 2026-10-11), written per page by four sub-agents and assembled. The shell is the shared layer every Ostler app bundles: it draws the tiles of the MFD screen, the top strip, the soft-key row, warnings and focus, and nothing else; settings and the Car page belong to the gateway app. It follows the review decisions: five size classes picked from the tile's own pixel box (Badge, Chip, Compact, Standard, Expanded), a 24 px text floor while moving, a strip of 48 px or less on 480 px-high screens, a per-page Expanded minimum, a settings button that opens the gateway's shared settings, soft keys declared by pages with steering-wheel Select as acknowledge, and the warning tile order (passenger side, then not an instrument page, then not a map with guidance, otherwise a band). Themes are decided by the owner (Themes v2) and the brief adds no theme rules. Four sections: A frame and layout (23 frames), B top strip and menus (33), C driving, warnings and input (33), D states and hand-offs (25), each ending with a frame list and open questions.
---

# Designer brief — the Ostler shell

**For the designer of the shell.** Read this on its own; it defines every term it uses. It
asks for what is needed and the rules that must hold, not for a particular layout. Where it
names a file such as `core-3-first-app.png` or `Ostler Themes v2.dc.html`, that file is in the
design hand-off: renders in [`../mfd/png/`](../mfd/README.md), designs in `../mfd/designs/`.

## What the shell is

- **Ostler is separate apps** (Logs, Diagnostics, Security, Maintenance, Map, Social and more),
  each a web app installed from the browser, all reading one **gateway**: the Ostler Brain in
  the car, else the Ostler Gateway Android app, else a small node, else a temporary gateway in
  the browser tab. The gateway owns all hardware, car profiles, permissions and settings.
- **The screen is an MFD** (multi-function display, as in an aircraft): a layout of **tiles**,
  each showing one **page** from any app. There are no drive modes; driving is a set of rules
  the shell applies.
- **The shell** is a library every app bundles, so whichever app is open draws the tiles.
  There is no launcher. The shell draws:
  - the tile frame, its label and the dividers between tiles;
  - the top strip: layout switcher, connection and vehicle chips, warning strip, settings
    button;
  - the soft-key row for the focused tile, the focus ring, cautions and warnings;
  - the states every tile can be in (loading, offline, stale, can't render, third-party).
- **The shell does not** have settings screens, a Car page or any car logic. Its settings
  button opens the gateway's shared settings. The gateway app is the only native app anyone
  needs; Ostler Controls (steering-wheel keys and overlays) is optional.
- **Themes are decided.** Use the owner's chosen Themes v2, Day and Night. This brief only
  notes which shell surfaces a theme touches and which safety parts it cannot change.

## Hard constraints

- **Size comes from the tile, never the device.** Each tile picks its size class from its own
  pixel box (table below). Moving up a class adds content; moving down drops the
  lowest-priority parts. Nothing is squeezed or scaled down.
- **While moving:** text at least 24 px, larger touch targets, no editing, effects off. Actions
  that are not allowed say why ("Park to change").
- **Top strip** at most 48 px tall on 480 px-high screens, so a full tile on a 5″ head unit
  still reaches Expanded. No clock in the strip.
- **Left- and right-hand drive:** the screen mirrors, strip included.
- **Caution (amber) and warning (red)** colours and safety icons are locked; themes and pages
  cannot change them. A warning takes over a tile in this order: the passenger-side tile, then
  one that is not an instrument page, then one that is not a map with guidance; otherwise it
  shows as a band. Steering-wheel Select acknowledges a warning, only while one is showing.
- **Each page declares** which size classes it supports, its Expanded minimum and its soft
  keys. A page that can't show at a size falls back to the largest supported class that fits,
  then to a Chip.

## Size classes

A class needs both the width and the height. Tiles enter a class at the first size and drop
back only below the second, so they don't flicker while a divider is dragged.

| Class | Shows | Enter at (px) | Drop below (px) |
|---|---|---|---|
| Badge | an icon and at most one value | anything smaller than Chip | — |
| Chip | one value with its name | 120 × 64 | 108 × 56 |
| Compact | the page's top few items | 220 × 140 | 204 × 128 |
| Standard | the page's normal view | 360 × 260 | 336 × 244 |
| Expanded | the full page | 640 × 420 | 608 × 400 |

Checks: a full tile on an 800 × 480 head unit (about 728 × 430) is Expanded; half of it is
Standard; a third of a 1024 × 600 screen (about 340 wide) is Compact.

## Frames to draw

Each block names its frames. The screens are: phone 393 × 852, 5″ head unit 800 × 480, 7″
1024 × 600, 10″ 1280 × 720, tablet, desktop, and Android split screen at a half and a third.
Draw left-hand drive unless a frame says right-hand drive (RHD); draw Night unless it says Day.

## How to read a block

Each block gives: **Purpose**, what it **Holds**, its **States**, the **Sizes** it uses, the
frames to **Draw**, the **Rules** that must hold, its **Interactions** and **Reference**
files. Each section ends with its frame list (ids such as A-01) and open questions. Some open
questions appear in more than one section (for example Open beside while moving, and focus
order); answer them once.

## A. Frame and layout

This section covers the tile itself and how tiles share the screen. Terms used throughout:

- **Tile:** one rectangle on screen that shows one page.
- **Page:** one screen from an app (for example Diagnose's fault list, or the gateway's Heading
  instrument). Any page can go in any tile.
- **Host app:** whichever Ostler app is open. It draws the tiles. There is no launcher.
- **Shell:** the shared layer every app bundles. It draws the frame, label, dividers, chips
  and top strip. It never draws page content beyond the small Badge and Chip summaries.
- **Size class:** one of five fixed designs a page can show (Badge, Chip, Compact,
  Standard, Expanded). The class comes from **the tile's own pixel box**, never from the
  device.
- **Driver side / passenger side:** the side of the screen nearer the driver or the
  passenger. It comes from the car profile in the gateway app. Right-hand drive (RHD)
  mirrors everything that left-hand drive (LHD) shows.
- **Main tile:** the tile the layout treats as most important. It keeps its space when the
  window gets too small.
- **Moving / Parked:** as reported by the gateway. "Unknown" counts as moving. While moving,
  text is at least 24 px, touch targets are larger, and layout editing is locked.

Where the renders conflict with the settled decisions, the decisions win. Each block says
where this happens.

### A.1 Tile frame and label

**Purpose**
- The container every page lives in. It shows what the page is, offers the label menu, and
  carries focus, caution and drag states. It does this the same way in every app.

**Holds**
- Frame: the surface, the corner shape and the gap to its neighbours.
- Label row (top of the tile, from the driver side outward): page name, a menu chevron, and
  a small link mark when the tile is linked (see A.6). While designing, or when the user turns
  on "Show sizes", it also shows "App · Size" (for example "Car · Standard").
- The page's own navigation row (tabs or back) sits under the label **only at Standard and
  Expanded**. It hides at Compact, Chip and Badge.
- Page content, drawn by the page's app.

**States**
- Normal.
- Focused: a visible focus ring, used for steering-wheel and keyboard focus. The soft-key row
  at the bottom of the screen belongs to this tile.
- Caution: an amber ring around the tile the problem is about. The tile is never taken over.
- Warning takeover: covered by another section. This section only notes that the frame must
  allow a takeover.
- Loading: the page module is still loading. Show the label and a quiet placeholder of the
  same size. Never use a spinner that changes the layout.
- Page failed to load or cannot be rendered: the tile falls back to a chip (see A.9).
- Stale or offline data: owned by the page, using the trust levels (live, estimated, stale,
  unavailable). The frame does not dim the whole tile.
- Dragging: the label is lifted while being dragged to swap or split (A.5).
- Moving vs parked: while moving, label text is at least 24 px, the chevron's touch target
  gets larger, and "App · Size" is hidden.

**Sizes** (thresholds: research note §8; a class needs both width and height)

| Class | Enters at (w × h px) | Drops back below | What it shows |
|---|---|---|---|
| Badge | anything smaller than Chip | — | Icon and state, maybe one number. No label row; the icon is the label. |
| Chip | 120 × 64 | 108 × 56 | Icon, page name and one value (the page's summary). Drawn by the shell. |
| Compact | 220 × 140 | 204 × 128 | Label row, then the single most important thing and its next step. No app navigation. |
| Standard | 360 × 260 | 336 × 244 | Label row, app navigation row, the normal design. |
| Expanded | 640 × 420 | 608 × 400 | As Standard, plus extra parts side by side. |

- The two columns form a buffer, so a tile near the edge does not flicker while a divider
  moves.
- A page can set a larger Expanded minimum for itself. Diagnose and Logs use 760 px wide.
  Below that minimum they stay Standard.
- Badge and Chip are drawn by the shell from the page's summary, unless the page supplies its
  own. This keeps them consistent across apps.
- Moving to a larger class adds parts. Moving to a smaller class removes the lowest-priority
  parts. Nothing is squeezed or scaled down.
- The page's state (selected fault, chart cursor, zoom) survives a class change.
- The brief's "Chip under about 200 × 130" is an older approximation. The table is what
  counts.

**Draw**
- One page (Diagnose suggested, because it has the most parts) at all five classes on one
  sheet, Night, at the pixel sizes in the table.
- The label row in each state (normal, focused, caution, dragging, moving), at Standard,
  7in 1024x600, Night and Day.
- Diagnose at 700 px and at 780 px wide, side by side, to show the 760 px page minimum.

**Rules**
- Label text and the chevron must stay readable and usable at 24 px while moving. Check
  whether the label row still fits at Compact.
- A colour change alone never shows focus or caution. Use a ring or shape too, because
  amber is reserved for caution.
- The page name is the page's own name. The shell never shortens it to a code. Truncate
  with an ellipsis, and keep the full name for the menu and screen readers.
- Theme touchpoint: the theme can style the frame, label and corner shape. It never changes
  the size thresholds, label touch targets or the caution ring colour.

**Interactions**
- Tap the label or chevron to open the label menu (A.2).
- Long press the label (parked only) to lift the tile and drag it (A.5).
- Tap a Chip or Badge to swap that page into the main tile.
- Focus: the steering-wheel "next" control moves focus tile by tile, starting from the
  driver side. Menu on the focused tile opens its label menu.

**Reference**
- png: `mfd-v2-workshop-parked.png`, `mfd-v2-bench-expanded.png`, `tiling-v2-00.png`,
  `core-sizes-5in.png`, `core-sizes-phone.png`.
- designs: `Ostler MFD v2.dc.html`, `Ostler Core Sizes.dc.html`.
- Conflicts with the renders, where the decisions win:
  - Class labels in the renders do not follow the thresholds. A tile about 310 px wide is
    labelled Standard, and phone tiles about 370 × 330 are labelled Compact.
  - No Badge or Chip is drawn.
  - A full 800x480 tile is labelled Standard. With a top strip of 48 px or less it is
    Expanded.

### A.2 Tile label menu

**Purpose**
- The one place for actions on a tile. It keeps the frame quiet.

**Holds**
- **Swap page:** opens the page picker. It lists pages from installed apps, groups them by
  app and shows which classes each page supports.
- **Page settings:** opens that page's settings, which belong to that page's app. They are
  not the shell's settings, and not the host app's unless it owns the page.
- **Open beside:** opens a linked tile on the passenger side (A.6).
- **Close:** removes the tile, with Undo.

**States**
- Parked: all four items are available.
- Moving: Swap page stays one tap. Page settings opens for browsing, with a "Park to change"
  pill. Open beside and Close are locked, with the reason "Not while moving" (see Open
  questions).
- Only tile left: Close is unavailable, because the last tile never closes.
- Page picker states:
  - normal;
  - no other pages installed: point to the gateway app's "Get apps";
  - a page that will not fit this tile: it is listed and marked "Shows as chip here".

**Draw**
- The menu open on a Standard tile, 7in 1024x600, Parked and Moving, LHD.
- The page picker: 7in and phone 393x852 (as a bottom sheet).

**Rules**
- The menu is anchored to the label and opens towards the screen centre, so it never runs
  off the passenger edge.
- Items keep the same order and position in every app, so they can be used without looking.

**Interactions**
- Touch: tap an item.
- Keys: up and down move through items, ok picks one, back closes the menu.

**Reference**
- png: `mfd-v2-trail-moving.png`, `tiling-v2-00.png` (the chevron on each label).
- designs: `Ostler MFD v2.dc.html`.

### A.3 Layout presets

**Purpose**
- Six starting shapes. Saved layouts are built from them.

**Holds**
- **Full:** one tile.
- **Halves:** two equal columns.
- **Two thirds:** the main tile takes ⅔ and the other takes ⅓.
- **Main + two:** the main tile, with two tiles stacked beside it.
- **Three columns:** three equal columns.
- **Quad:** a 2 × 2 grid.
- One level only: a tile never contains tiles, and a group never contains a group.

**States**
- The preset applies.
- The preset is not allowed here, because some tile would be smaller than Compact. Overflow
  (A.8) then turns the extra pages into chips. Presets are never greyed out because of the
  screen's size in inches.
- Moving: switching between saved layouts is one tap. Changing the preset of the current
  layout is layout editing, so it is locked.

**Sizes**
- Expected classes on common screens, after a 48 px strip (allow for the gaps):

| Screen | Full | Halves | Main + two | Quad |
|---|---|---|---|---|
| 5in 800x480 | Expanded | Standard | Standard + 2 Compact | Compact ×4 |
| 7in 1024x600 | Expanded | Standard | Standard + 2 Compact | Standard or Compact |
| 10in 1280x720 | Expanded | Expanded or Standard | Expanded + 2 Standard | Standard ×4 |

- Designers should check these figures against the table rather than trust this summary.

**Draw**
- All six presets on 7in 1024x600, LHD, Parked, Night, filled with real pages (Trail,
  Commute and Workshop pages are good sources).
- All six on 5in 800x480, to show which give chips.

**Rules**
- Main + two puts the main tile on the driver side (stored that way and mirrored for RHD).
- The 2 / 3 / 4 tile counts by screen size in the older brief are examples only. Pixels
  decide.

**Interactions**
- Choosing a preset is done from the layout switcher (top strip section) and in edit mode.
  This section only defines how each preset looks.

**Reference**
- png: `mfd-v2-*.png` (the layout chooser row above the screen), `v1-mfd.png` (older;
  its fixed tile limits are superseded).
- designs: `Ostler MFD v2.dc.html`.

### A.4 Right-hand and left-hand drive

**Purpose**
- Keep the driver's most important tile, and the shell controls, nearest the driver.

**Holds**
- A layout is stored as if the driver sat on the left. RHD reverses every row:
  - Main + two puts the main tile on the right;
  - the chip column moves to the left;
  - Open beside opens to the left.
- The top strip mirrors as well (covered in the top strip section).

**States**
- LHD.
- RHD.
- Driver side unknown (no car profile yet): use LHD, and show nothing extra.

**Draw**
- Main + two and Quad on 7in, LHD and RHD side by side.
- Overflow chips (A.8) on 5in, RHD.

**Rules**
- Mirroring changes position only. It never changes text direction, the order inside a
  page, or icons such as arrows that point to things in the world.
- Columns stacked top to bottom do not flip vertically.

**Interactions**
- None of its own. The driver side follows the car profile in the gateway app.

**Reference**
- png: `mfd-v2-right-hand-drive.png`.
- That render shows a clock in the strip. No clock is a settled decision.

### A.5 Dividers and direct editing

**Purpose**
- Let the owner resize, swap, split and close tiles by hand while parked.

**Holds**
- A divider is the gap between two tiles, with a drag handle. The handle is the touch
  target, and it is wider than the gap.
- Snap points at ⅓, ½ and ⅔ along the divider's axis.
- An Undo bar after a tile closes.

**States**
- Idle: the handle is visible but quiet.
- Dragging:
  - snap guides show;
  - neighbouring tiles change size class live as they pass the thresholds;
  - each tile's label shows its class while the drag is in progress.
- Near close: a tile pushed below its minimum (Compact's exit size, 204 px wide or 128 px
  tall) shows that it will close on release.
- Closed: Undo shows for about 10 seconds, then fades.
- Moving: handles are hidden or shown as locked, and dividers do not respond. Show a
  "Layout locked" indicator once (in the strip), not on every divider.

**Draw**
- A divider drag in progress (Halves to Two thirds) with snap guides, 7in, Parked.
- The near-close state and the Undo bar after release, 7in, Parked.
- A double-tap swap, before and after, 7in.
- A label being dragged onto another tile (swap target) and onto a screen edge (split
  target), 10in 1280x720.
- The same screen while moving, with handles locked, 7in, Moving.

**Rules**
- Moving: no dragging, splitting, closing or divider moves. Swapping pages through the menu
  or a chip stays one tap.
- Size classes change live during a drag. Snap targets are applied on release only.
- The last tile never closes.
- When a group is left with one tile, the group goes away. When the main tile closes, the
  largest tile left becomes the main tile.
- Theme touchpoint: the theme may style the divider. It never changes the handle's size or
  its touch target.

**Interactions**
- Drag a divider to resize.
- Double-tap a divider to swap the two sides.
- Long press a label, then drag:
  - onto a tile to swap pages;
  - onto a screen edge to split.
- Drag a tile below its minimum to close it. Tap Undo to bring it back.

**Reference**
- png: `tiling-v2-00.png`, `v1-tiling.png`.
- designs: `Ostler Tiling v2.dc.html`, `Ostler Tiling.dc.html` (v1).

### A.6 Open beside, linked tiles and the shared cursor

**Purpose**
- Let one page open a related page next to it, and keep the two pages in step.

**Holds**
- **Open beside:** long press an item (a fault, a drive or a friend) and pick "Open
  beside". The new tile opens on the passenger side of the source tile and takes half of the
  source tile's share. If the source tile sits in a stacked column, the new tile opens
  beside the whole column.
- When a layout already has four tiles, Open beside replaces the page in the nearest
  passenger-side tile instead, with Undo.
- **Link:** the two tiles share a vehicle, a time window and a signal.
- **Shared cursor:** picking a fault in Diagnose moves Logs to that moment, and the reverse
  works too.
- A small link mark on both labels.

**States**
- Linked: both labels show the link mark.
- Cursor moved: the receiving tile briefly marks the new position, and the page draws it.
- Link broken, because one page is swapped out or closed: the mark disappears from the
  remaining tile.
- The linked page is too small: it opens as a chip (still linked), and tapping it swaps it
  in.
- Moving: Open beside is locked (see Open questions). A link that already exists keeps
  working.

**Draw**
- Diagnose with a fault picked and Logs beside it at that moment, 10in 1280x720, Parked,
  LHD and RHD.
- The long-press menu showing "Open beside", 7in.
- Open beside on a 4-tile layout (replacing a tile), 7in, with Undo.

**Rules**
- A link connects two tiles side by side. It never puts one tile inside another.
- The link mark is not a colour alone.

**Interactions**
- Long press an item, then choose Open beside.
- Tap the link mark to see what is linked, with an Unlink option (parked only).

**Reference**
- png: `v1-tiling.png` (linked tiles, Open beside), `mfd-v2-bench-expanded.png`.
- designs: `Ostler Tiling.dc.html` (v1).

### A.7 Window rules: shape

**Purpose**
- Fit the layout to the window's shape before sizing the tiles.

**Holds** (the first of three rules, applied in order)
1. **Portrait** (the window is taller than it is wide): every split turns. Side-by-side
   becomes top and bottom.
2. **Short landscape window** (the tile area is less than about 320 px high): stacked tiles
   are laid out in one row, each keeping its share.

**States**
- Landscape normal.
- Portrait.
- Short landscape (one row).

**Draw**
- Phone 393x852 portrait with Main + two (Workshop: Diagnose over Logs), Parked, Night.
- 10in Android split top and bottom (about 1280 × 360), Main + two shown as one row.
- Tablet 1180x820 and desktop 1440x900 with Quad, to show that large windows keep the
  preset as it is.

**Rules**
- The shape rule changes how tiles are arranged, never which pages are shown.
- The driver side is still respected after the shape changes. In portrait, see Open
  questions.

**Interactions**
- None. The rule runs on every window resize and rotation.

**Reference**
- png: `tiling-v2-02.png` (10in top and bottom), `tiling-v2-03.png`, `tiling-v2-04.png`
  (phone), `core-sizes-phone.png`.

### A.8 Window rules: size and overflow

**Purpose**
- Make sure every tile shown is usable, and turn the rest into chips.

**Holds**
- **Rule 2, size:** each tile gets its class from its own box, then the largest class the
  page supports that is no bigger.
- **Rule 3, overflow:**
  - while any tile would fall below Compact, the smallest tile that is not the main tile
    leaves the layout and becomes a chip;
  - when two are the same size, the one nearest the passenger edge goes first;
  - the rules then run again;
  - the main tile always keeps its space.
- **Chip column (landscape):** on the passenger side, about 128 px wide.
- **Chip row (portrait):** along the bottom, about 72 px tall.
- Tapping a chip swaps that page with the main tile's page.

**States**
- No overflow.
- One or more chips.
- Every other page is a chip, leaving only the main tile.
- Chips while moving: the tap to swap still works.
- Too many chips for the column or row: see Open questions.

**Sizes**
- A chip in a 128 px column is at the Chip class (icon, name, value).
- Items in a 72 px row that are narrower than 120 px are at the Badge class (icon and value).
  This matches the renders' "289° / 1.8 / LOW" items, which are Badges.

**Draw**
- 5in 800x480 with Quad: the main tile plus a chip column on the passenger side. Draw LHD
  and RHD, Parked and Moving.
- 7in Android split third (about 340 × 600): the main tile plus a bottom chip row.

**Rules**
- A tile is never shown smaller than Compact. Chips and Badges carry the page instead.
- Chips and Badges refresh at most every 2 s, so their values must not look live-critical.
- Text in chips and Badges must still meet the 24 px floor while moving. Check that one
  value fits.

**Interactions**
- Tap a chip to swap it in.
- Focus: chips are in the focus order, after the tiles.

**Reference**
- png: `tiling-v2-01.png`, `tiling-v2-02.png` (third-width split with chip row).
- designs: `Ostler Tiling v2.dc.html`.
- Conflict with the renders: their overflow items are labelled as chips but are Badges here.

### A.9 Android split screen and pages that cannot show

**Purpose**
- Ostler sits next to other Android apps, and some pages will not load or will not fit.
  Neither case should break the layout.

**Holds**
- **Android split screen:** Ostler simply gets a smaller window, and rules 1 to 3 apply as
  they do anywhere else. There is no special split-screen mode.
- **A page that cannot be rendered** shows as a chip with the page's icon and name and a short
  reason. Reasons:
  - "Not installed";
  - "Needs an update";
  - "Blocked";
  - "Didn't load".
  Tapping it opens the page's own app, or "Get app" in the gateway app.
- **A page that does not support the class** it was given, at any size, falls back to its
  largest supported class that is no bigger. When even that does not fit, it shows as a chip.

**States**
- Split half.
- Split third.
- Split top and bottom.
- Not installed.
- Version mismatch.
- Blocked.
- Load failed, with a retry option inside the chip menu.

**Draw**
- 7in Android split half (about 506 × 600): four tiles at Compact.
- An unrenderable-page chip in each reason, 7in, Night and Day.

**Rules**
- Do not show an error over the whole tile, and never leave an empty tile. The chip is the
  error state.
- No placeholder for data that is missing. That is the page's job ("never greyed out").

**Interactions**
- Tap the chip to open the app or the gateway app's get-app flow.
- Long press opens the label menu (Swap page, Close).

**Reference**
- png: `tiling-v2-01.png` (split half and third), `tiling-v2-02.png` (split top and bottom).
- These renders include a clock. No clock is a settled decision.

### Frame list

1. A-01 — One page at all five size classes, at threshold sizes · sheet · Night, Day
2. A-02 — Tile label states (normal, focused, caution, dragging, moving) · 7in 1024x600 · Night, Day
3. A-03 — Diagnose at 700 vs 780 px wide (760 px page Expanded minimum) · 10in 1280x720 · Night
4. A-04 — Label menu open · 7in 1024x600 · Parked, Moving · LHD
5. A-05 — Page picker (Swap page) · 7in 1024x600 and phone 393x852 · Parked
6. A-06 — Six layout presets with real pages · 7in 1024x600 · LHD · Parked · Night
7. A-07 — Six layout presets · 5in 800x480 · LHD · Parked (shows which give chips)
8. A-08 — Main + two and Quad, mirrored · 7in 1024x600 · LHD vs RHD
9. A-09 — Divider drag with snap guides and live class change · 7in 1024x600 · Parked
10. A-10 — Drag below minimum, then the Undo bar after release · 7in 1024x600 · Parked
11. A-11 — Double-tap divider swap, before and after · 7in 1024x600 · Parked
12. A-12 — Label dragged onto a tile (swap) and an edge (split) · 10in 1280x720 · Parked
13. A-13 — Layout locked while moving (handles locked, strip indicator) · 7in 1024x600 · Moving
14. A-14 — Open beside: long-press menu and the new linked tile · 7in 1024x600 · Parked · LHD, RHD
15. A-15 — Open beside on a four-tile layout (replace with Undo) · 7in 1024x600 · Parked
16. A-16 — Linked Diagnose and Logs with the shared cursor · 10in 1280x720 · Parked · LHD, RHD
17. A-17 — Portrait split: Workshop (Diagnose over Logs) · phone 393x852 · Parked, Moving
18. A-18 — Short window one row: Main + two · 10in Android split top and bottom (~1280x360)
19. A-19 — Large windows keep the preset: Quad · tablet 1180x820 and desktop 1440x900
20. A-20 — Overflow, landscape: main plus a passenger chip column · 5in 800x480 · LHD, RHD · Parked, Moving
21. A-21 — Overflow, portrait: main plus a bottom chip/Badge row · 7in Android split third (~340x600)
22. A-22 — Android split half: four tiles at Compact · 7in Android split half (~506x600)
23. A-23 — Unrenderable-page chip in each reason · 7in 1024x600 · Night, Day

### Open questions

1. **Open beside and Close while moving.** Both change the layout, so this draft locks them
   and keeps only Swap page. Should Open beside still be one tap while moving, because it is
   page navigation rather than editing?
2. **Soft-key row and the height budget.** On 5in 800x480, a 48 px strip leaves a full tile
   at Expanded height (about 420 px), but a soft-key row as well would push it down to
   Standard. Should the soft-key row overlay the bottom of the focused tile, sit beside the
   chips, or count against the tile area?
3. **Label row at Compact while moving.** At 24 px, the label row takes a large part of a
   140 px-tall tile. Should the label shrink to an icon at Compact while moving, with the name
   in the menu?
4. **Driver side in portrait.** Portrait stacks tiles top to bottom. Should the main tile go
   at the top, or should the order still follow the driver side (for example, the soft keys
   on the driver side as ADR-0052 §4a suggests)?
5. **Too many chips.** What happens when the chip column or row cannot hold every chip?
   Options: scroll, a "+n" chip that opens a list, or dropping the oldest.
6. **"Show sizes" on the label.** Is "App · Size" a designer and debug aid only, or a user
   setting in the gateway's shared settings?
7. **Unlinking.** Is a visible link mark with Unlink needed, or should links end only when a
   tile is swapped or closed?

## B. Top strip and menus

The top strip is the thin bar across the top of every Ostler app. It holds the shell's own controls: the layout switcher, the car and connection status, the warning strip and the settings button. This section also covers the menus those controls open.

Terms used here:
- **Shell:** the shared layer that every Ostler app includes. It draws tiles, the top strip, soft keys and warnings. It has no settings screens and no car logic of its own.
- **Gateway app:** the one native app. It owns hardware, connections, car profiles, permissions and all shared settings. The shell only shows the gateway's state and opens the gateway app when the driver needs more.
- **Tile:** one rectangle of the screen that shows one page from any installed app.
- **Layout:** an arrangement of tiles. A **saved layout** is a named one, such as Trail, Commute or Workshop.
- **Driver's side:** the edge nearest the driver. On a left-hand-drive (LHD) car it is the left edge; on a right-hand-drive (RHD) car the whole screen is mirrored, strip included.
- **Moving / Parked:** car state from the gateway. While moving, text is at least 24 px, touch targets are larger, and editing is locked.
- **Sheet:** a panel that slides over the tiles (from the bottom on a phone, as a side or centre panel on wider screens).

### B1. Top strip

**Purpose**
- One glanceable bar: which layout is showing, which car, whether data is live, any warning, and a way into settings.

**Holds** (from the driver's side outward)
1. **Layout switcher:** layout icon and the saved layout's name, with a menu chevron.
2. **Connection chip:** the gateway's state in words (B2).
3. **Vehicle chip:** the car's name (B3). It sits directly beside the connection chip, on its outer side, and reads as one phrase with it, for example "Connected · Discovery 2". Why:
   - Together they answer one question: "which car, and is it live?". Splitting them makes the driver read two places.
   - The ADR places it "with the connection chip". The spec draft placed it last, after settings, but that put a car control at the far passenger edge, away from the status it qualifies.
   - On narrow windows the pair can merge into one chip without moving anything else.
   - The gateway design (g8) shows the car on the far driver-side edge. The order above wins, because the layout switcher must stay first (it is the most-used one-tap control while moving).
4. **Warning strip:** one item at a time (warning, then caution, then notice). It takes the remaining width.
5. **Settings button:** a gear. It is always at the passenger-side end, sitting on its own.

No clock (the phone or head unit already shows the time). No other items.

**States**
- **Normal, parked:** all five items. Layout name in full.
- **Moving:** same items, text at least 24 px, larger touch targets. The switcher still works with one tap. A small lock icon next to the layout name shows that editing is locked (it is a status, not a button).
- **Not connected / first run:** the switcher shows the current page set ("Welcome" or "Car"), the connection chip reads "No gateway", there is no vehicle chip (or "No car" in grey with a word), and the warning strip is empty.
- **Caution showing:** the warning strip shows an amber pill with the words (for example "Caution · Coolant 108 °C"). The strip never takes over a tile for a caution.
- **Warning showing:** the strip shows "WARNING" and the short text. The label stays after it is acknowledged (ACK), until the problem clears. The tile takeover is covered in the warnings section.
- **Several alerts:** one item shows, with a count ("+2"). Tap opens the list (warnings section).
- **Offline / stale:** the connection chip reads "Last seen hh:mm". The rest of the strip is unchanged. Pages mark their own stale values.
- **Viewing another car:** the vehicle chip changes (B3). The connection chip still describes the connected car.
- **RHD:** the strip is mirrored. The switcher is at the right edge and the gear at the left.

**Sizes**
- The strip responds to the app window's width (not to tile size classes).
- **Height:** 48 px or less on screens 480 px high (5 in head unit, 800x480), so a full tile there can still reach Expanded (at least about 640x420). It may be taller on phones and tablets.
- **Wide (10 in, tablet, desktop):** everything in full: layout name, "Connected · via Brain", car name, the full warning text.
- **Medium (7 in, 5 in, Android split half):** the layout name is cut short with an ellipsis, and the warning text is shortened to a keyword plus value.
- **Narrow (phone, Android split third):** layout icon plus a short name; the connection and vehicle chips merge into one chip with a status word and a shaped icon ("Live", "Last seen 10:42", "Offline"); the warning shows as a pill with a symbol and one word; and the gear stays.
- Words never drop below one short status word. A coloured dot alone is never enough (the designer's phone render shows a dot only; that is overruled).

**Draw**
- 7in 1024x600, LHD: parked normal, moving, caution, warning.
- 7in 1024x600, RHD: parked normal (mirrored).
- 5in 800x480: normal, measured to show 48 px.
- Phone 393x852: normal (merged chip), offline.
- Android split third: normal.
- 10in 1280x720: viewing another car.
- Night and Day for the 7in normal frame only. Theme styling of the strip comes from Themes v2, which is already decided; draw it in the chosen theme. No new theme rules.

**Rules**
- Order is fixed and mirrored for RHD. Users cannot reorder the strip.
- Status uses words and a shape as well as colour (for example a filled circle for live, a hollow circle for last seen, a crossed icon for offline).
- The strip never covers the focused item and never grows to push tiles while a warning shows.
- No clock.
- Themes may restyle the strip (bar, floating or line, as in Themes v2), but never change its words, order, height limit or the safety colours.

**Interactions**
- **Tap:** switcher opens B5; connection chip opens the gateway app (B2); vehicle chip opens the gateway's car switcher (B3); warning strip opens the alert detail; gear opens the gateway's shared settings (B4).
- **Focus and keys:** the strip is a focus zone above the tiles. Left and right move along it in visual order (mirrored for RHD). OK activates the item. Up from the top tile row enters the strip.
- **Steering wheel:** "next layout" switches saved layouts, even while moving. Select acknowledges a warning only while one is showing; otherwise it does nothing in the strip.
- **Long press:** none on the strip (avoids hidden actions while driving).

**Reference**
- png: core-3-first-app.png, core-sizes-phone.png, core-sizes-5in.png, mfd-v2-trail-moving.png, mfd-v2-right-hand-drive.png, mfd-v2-caution.png, mfd-v2-master-warning.png, tiling-v2-01.png, gateway-04.png
- designs: Ostler Core.dc.html, Ostler Core Sizes.dc.html, Ostler MFD v2.dc.html, Ostler Gateway.dc.html
- Conflicts where the decisions win: the clock in MFD v2 and Tiling v2 (remove it); the missing gear in MFD v2 (add it); the phone dot without words (add a word); "Brain · live" (use the gateway's words below); the strip and margins at about 90 px on 5in (keep 48 px or less).

### B2. Connection chip

**Purpose**
- Shows whether the app is getting live data from the car, in the gateway's own words. Tapping it hands off to the gateway app.

**Holds**
- A shaped status icon, a short status text from the gateway, and optionally the route ("via Brain").
- It never says "gateway" in the chip text itself.

**States** (text comes from the gateway; the shell does not invent it)
| State | Example words | Icon shape | Notes |
|---|---|---|---|
| Connected | "Connected" | filled circle | live data |
| Connected through a Brain | "Connected · via Brain" | filled circle | phone acting as a client of the car's Brain |
| Connecting | "Connecting…" | animated ring (static when moving, because effects are off) | amber |
| Last seen | "Last seen 10:42" | hollow circle | gateway lost; pages show stale values, no actions |
| No gateway | "No gateway" | crossed circle | nothing found; tap to set up |
| Browser session, not recording | "Connected · not recording" | filled circle with a small gap | temporary gateway in the browser; it records nothing when the tab closes |
| Viewing another car | unchanged; the vehicle chip carries this (B3) | — | live state still describes the connected car |

- **Loading** (the app has just opened and the gateway has not answered yet): "Connecting…".
- **Error from the gateway** (for example the hardware is busy): the gateway's short text, for example "Connected · bus busy". The detail is in the gateway app.
- **Moving vs parked:** same states and words, at 24 px or more while moving.

**Sizes**
- Full: icon, words and route. Medium: icon and words, no route. Narrow: merged with the vehicle chip, using one word ("Live", "Connecting", "10:42", "Offline", "Not recording").

**Draw**
- One state sheet at 7in scale showing all six states, in the full, medium and narrow forms (one frame).
- In context: phone 393x852 "Last seen 10:42" with the gateway hand-off (one frame).

**Rules**
- Words and shape always; colour is only a third cue.
- The shell does not decide the state or add its own wording; it shows what the gateway sends.
- The "not recording" prompt is gentle: it is the chip's wording only. Any explanation lives in the gateway app, and nothing pops up while moving.
- No animation while moving.

**Interactions**
- **Tap or OK:** opens the gateway app (its Status home). If the gateway app is not installed (browser only), it opens the gateway's web page or the "Connect your car" flow.
- No long press.

**Reference**
- png: gateway-04.png (chip states and g8 unreachable), gateway-00.png, core-1-not-connected.png
- designs: Ostler Gateway.dc.html

### B3. Vehicle chip

**Purpose**
- Says which car the app is showing. The car switcher itself is in the gateway.

**Holds**
- A car icon, the car's short name (from its gateway profile, for example "Discovery 2"), and a chevron.

**States**
- **Connected car:** "Discovery 2". It reads with the connection chip as "Connected · Discovery 2".
- **Viewing another car** (history apps only, such as Logs and Maintenance): "Viewing: Defender 110 · not connected". It uses a distinct outline style and a different icon (an eye or a clock), never colour alone. The connection chip still describes the real connected car.
- **Unknown car detected:** "New car found". Tap opens the gateway's set-up flow.
- **No car / no gateway:** hidden, or "No car" (open question).
- **Moving:** the name is shown at 24 px or more. A live app cannot view another car, so while moving the label can only be the connected car, except in history apps.

**Sizes**
- Full: icon, name and chevron. Medium: icon and a short name. Narrow: merged into the connection chip; the viewing state replaces the merged chip with "Viewing: D110".

**Draw**
- 10in 1280x720: Logs viewing another car, strip and a page (one frame).
- Phone 393x852: viewing another car, merged chip (one frame).

**Rules**
- Live data and any action that changes the car always follow the connected car, whatever the chip shows.
- The viewing state must be obvious at a glance, so it shows the words "Viewing" and "not connected".
- The shell never switches cars itself.

**Interactions**
- **Tap or OK:** opens the gateway's car switcher (garage list). In a history app, it can return to "Back to connected car".

**Reference**
- png: gateway-04.png (g8 shows "Discovery 2" in the strip), gateway-01.png, gateway-02.png
- designs: Ostler Gateway.dc.html

### B4. Settings button

**Purpose**
- One way into shared settings from any app.

**Holds**
- A gear icon with an accessible name ("Settings").

**States**
- **Normal:** gear.
- **Moving:** the gear still works. The gateway's settings open browse-only, showing "Park to change" (that screen is the gateway's).
- **Gateway not installed or unreachable:** it opens the gateway's web settings if available. Otherwise it opens the connect flow.

**Sizes**
- Always the gear icon at every width, with a 48 px or larger target (larger while moving).

**Draw**
- No separate frame; it appears in the B1 frames. Draw one hand-off frame: 7in, gear tapped, the gateway's shared settings opening (show only the transition and its first screen outline; the gateway section designs the content).

**Rules**
- The shell draws no settings screen. The gear opens the gateway's shared settings: display, account and sync, and layouts.
- Each app's own settings stay inside that app and are reached from the tile label menu ("Page settings"), not from this gear.
- The designer's Core settings sheet (Vehicles, Connections, Apps, Layouts, Themes and so on) belongs to the gateway app, not the shell.

**Interactions**
- **Tap or OK:** hands off to the gateway app, or the gateway's settings view. **Back** returns to the same layout and tiles.

**Reference**
- png: core-settings-themes.png (read it as the gateway's settings), core-3-first-app.png
- designs: Ostler Core.dc.html

### B5. Layout switcher menu

**Purpose**
- Switch saved layouts in one tap at any speed. It is also the way in to saving and managing layouts.

**Holds**
- A list of this car's and this screen's saved layouts: icon, name, and a tick on the active one. Optionally a small "Auto" tag on a layout with an automatic trigger.
- A divider.
- "Save this layout".
- "Manage layouts" (opens B6).
- "Save to phone…" (opens B8, for the current layout).

**States**
- **Normal, parked:** all items enabled.
- **Moving:** the layout list is enabled (one tap switches and closes the menu). "Save this layout", "Manage layouts" and "Save to phone" are shown disabled with "Park to edit". The list is short; if there are more than about six layouts, only the first six show (no scrolling while moving).
- **Empty** (no saved layouts yet): the current arrangement shows as "Unsaved layout", with "Save this layout" offered first.
- **Unsaved changes:** the active name shows "Edited" and "Save this layout" offers "Update Trail" or "Save as new".
- **Offline:** switching works from the cached copy. Saving shows "Will sync when connected".
- **Automatic switch just happened:** the strip name changes, with a brief note in the menu ("Switched: low range engaged"), and Undo is available for 10 s in a toast. The toast is text only while moving.

**Sizes**
- Head units: a drop-down anchored under the switcher on the driver's side. Phone: a bottom sheet. Rows are at least 64 px high while moving.

**Draw**
- 7in 1024x600, LHD: parked and moving.
- 7in 1024x600, RHD: parked.
- Phone 393x852: sheet, parked.
- 5in 800x480: moving (checks that six rows fit at 24 px).

**Rules**
- Switching is always one tap, never a confirmation.
- Editing is parked only.
- A layout belongs to a car and to a screen (head unit, phone and so on), and syncs through the gateway.
- Steering-wheel "next layout" cycles the same list in order.

**Interactions**
- **Tap:** the switcher opens the menu, and tapping a row switches.
- **Keys:** OK opens it, up and down move, OK switches, Back closes.
- **Long press:** none.

**Reference**
- png: mfd-v2-trail-moving.png, mfd-v2-convoy.png, mfd-v2-workshop-parked.png, mfd-v2-bench-expanded.png
- designs: Ostler MFD v2.dc.html (saved layout bar; read it as this menu)

### B6. Manage layouts sheet

**Purpose**
- Organise saved layouts and set automatic switching. Parked only.

**Holds**
- A filter at the top: car (from the garage) and screen ("This head unit", "This phone", "All screens").
- A list of layouts. Each row has a thumbnail of its tile arrangement, its name, its trigger tag, a drag handle and a menu (Rename, Duplicate, Delete, Save to phone).
- **Automatic switching** per layout, choosing one trigger:
  - "When the car starts"
  - "When low range engages"
  - "When parked"
  - "None"
- A note: "Layouts are stored with your car and sync to your other screens."

**States**
- **Parked:** fully editable.
- **Moving:** the sheet does not open. If it was already open when the car moves, it becomes read-only with "Park to edit". No changes are lost.
- **Empty:** "No saved layouts yet. Arrange your tiles, then Save this layout."
- **One layout:** it cannot be deleted (there must always be one).
- **Trigger conflict** (two layouts on the same trigger): an inline warning; the most recent one wins, or the conflict is blocked (open question).
- **Offline:** edits are queued and marked "Not synced yet".
- **Sync error:** "Couldn't sync. Your changes are kept on this screen." with Retry.
- **Delete:** removes the row, with Undo for 10 s.

**Sizes**
- Head units and tablet: a centre sheet, list on the left and the selected layout's detail on the right (from 1024 wide). 5in and phone: list, then detail with Back.

**Draw**
- 7in 1024x600: parked list and detail.
- 5in 800x480: list.
- Phone 393x852: list and detail (two frames).
- 7in: moving, read-only state.
- Tablet 1180x820: filter on "All screens".

**Rules**
- Parked only. Triggers fire only from gateway signals; the shell does not detect them.
- A trigger never fires while a warning takeover is showing; it waits until the takeover is acknowledged.
- Rename uses the system keyboard (parked only).
- The shell edits the layout document; the gateway stores and syncs it. The gateway's Layouts settings show the same data.

**Interactions**
- **Drag** the handle to reorder (this order is also the order for "next layout"). **Tap** a row to open its detail. **Swipe or menu** to delete, with Undo.
- **Keys:** up and down move through rows. Long OK (600 ms) on a row picks it up to reorder, then up and down move it and OK drops it.

**Reference**
- png: mfd-v2-workshop-parked.png
- designs: Ostler MFD v2.dc.html, Ostler Core.dc.html (its Layouts section)

### B7. Apps menu (page picker)

**Purpose**
- Put any installed Ostler app's page into a tile, open one beside the current tile, or go and get more apps.

**Holds**
- The installed Ostler apps (Diagnostics, Logs, Security, Maintenance, the gateway's Car and instrument pages, add-ons), each listed with its pages and each page's icon.
- Pages that suit the target tile's current size class come first. Pages that would only fit as a chip there are marked "Small here".
- Per page: "Open here" (the default tap) and "Open beside".
- "Get more apps" at the end. It hands off to the gateway app's apps gallery, showing only apps that work with this car.
- Optional: search, on head units and desktop, parked.

**States**
- **Normal:** grouped by app.
- **Moving:** "Open here" (swapping the page in a tile) still works in one tap. The list is flattened to recent and pinned pages, at most six rows. "Open beside" and "Get more apps" are disabled with "Park to change".
- **Only the gateway installed:** the Car and instrument pages are listed, plus a prominent "Get more apps".
- **Page not available:** an app that is installed but blocked, or on the wrong version, is greyed with the reason in words ("Update needed", "Not allowed for this car"). Tap hands off to the gateway.
- **Offline:** installed apps are still listed. "Get more apps" shows "Needs a connection".
- **Loading the page list:** skeleton rows, at most about 1 s.

**Sizes**
- 10in and tablet: a sheet over the target tile, two columns (apps on the left, pages on the right).
- 7in and 5in: one list with an app header for each group.
- Phone and split third: a full-height bottom sheet.

**Draw**
- 7in 1024x600: parked, opened from a tile label.
- 7in 1024x600: moving.
- 10in 1280x720: two-column.
- Phone 393x852: parked.
- 7in: gateway-only state.

**Rules**
- There is no launcher. The menu opens from the tile label ("Swap page") and from an empty tile, and always targets a tile.
- "Open beside" places the new tile on the passenger side, linked to the first. It is a layout change, so parked only (open question).
- Installs, updates and permissions are the gateway's. The shell only hands off.

**Interactions**
- **Tap** a page to open it here. **Long press** a page for Open beside, Pin and Save to phone. **Drag** a page onto a tile to put it there (parked).
- **Keys:** OK opens it; up and down move; left and right move between the app list and the page list on two-column screens; Menu (long OK) gives the long-press options.

**Reference**
- png: core-2-connected-no-apps.png, core-3-first-app.png, v1-tiling.png (Open beside)
- designs: Ostler Tiling.dc.html (v1, Open beside), Ostler Core.dc.html

### B8. Save to phone

**Purpose**
- Put a whole app, a saved layout, or a single screen on the home screen as its own icon.

**Holds**
- A sheet with three choices, labelled by what you get:
  - "This app": Diagnostics, as a normal install.
  - "This layout": "Workshop" opens straight into that layout.
  - "This screen": one page on its own, for example "Coolant gauge".
- A preview of the icon and name. The name can be edited (parked).
- The button "Add to home screen".
- A note: "Layouts come from your car's settings and stay in sync."

**States**
- **Supported** (Chrome on Android, Chrome on desktop, the Android head unit): one tap starts the browser's install prompt.
- **Already saved:** "On your home screen" with a tick. It offers to open it.
- **iPhone and iPad (Safari):**
  - There is no install prompt. The sheet shows the steps: Share, then "Add to Home Screen". Draw these as a short illustrated two-step guide.
  - Each saved icon keeps its own storage on iPhone, so it signs in to the gateway separately the first time. Layouts still come from the gateway.
  - The app's quick shortcuts on long press do not work on iPhone.
- **Browser not able to install** (for example Firefox on desktop): explains this, and offers "Copy link".
- **Gateway offline:** you can still save. The note "Will load your layout when connected" is shown.
- **Moving:** not available; the menu items show "Park to save".

**Sizes**
- Head units and tablet: a centre sheet. Phone: a bottom sheet.

**Draw**
- Phone 393x852, Android: three-choice sheet.
- Phone 393x852, iPhone: the step guide.
- 7in 1024x600: sheet opened from the layout switcher.
- Phone 393x852: an example home screen with three Ostler icons (app, layout, screen), showing how the icons stay distinct.

**Rules**
- Parked only.
- Saved icons for a layout or a screen must look different from the app's own icon (for example a badge with the layout's icon), so people can tell them apart.
- No permission requests happen here. Web permissions are the gateway's (Ostler-wide).
- Several installs from one web address are still to be bench-tested on Chrome Android and the Dudu7 head unit. Design for it, but expect it may fall back to app-plus-shortcut.

**Interactions**
- Opened from: the layout switcher ("Save to phone…"), the Manage layouts row menu, and a long press in the apps menu.
- **Tap** a choice, then "Add to home screen". **Keys:** up and down to choose, OK to confirm, Back to close.

**Reference**
- png: none drawn by the designer (new surface)
- designs: none (new)

### Frame list

1. B-01: Top strip, parked normal; 7in 1024x600; LHD; Night and Day
2. B-02: Top strip, moving (lock status, 24 px); 7in 1024x600; LHD
3. B-03: Top strip, caution pill; 7in 1024x600; LHD, moving
4. B-04: Top strip, warning label (after ACK, not cleared); 7in 1024x600; LHD, moving
5. B-05: Top strip, mirrored; 7in 1024x600; RHD, parked
6. B-06: Top strip, height check at 48 px or less with a full tile reaching Expanded; 5in 800x480; LHD
7. B-07: Top strip with merged chip, normal and "Last seen"; phone 393x852; parked
8. B-08: Top strip, narrow; Android split third; LHD, moving
9. B-09: Top strip, not connected / first run; phone 393x852 and 7in; parked
10. B-10: Connection chip state sheet (six states in full, medium and narrow forms); 7in scale
11. B-11: Connection chip tap, handing off to the gateway (g8 unreachable); phone 393x852
12. B-12: Vehicle chip, viewing another car in Logs; 10in 1280x720; parked
13. B-13: Vehicle chip, viewing another car, merged; phone 393x852
14. B-14: Settings gear handing off to the gateway's shared settings; 7in 1024x600; parked and moving
15. B-15: Layout switcher menu; 7in 1024x600; LHD, parked
16. B-16: Layout switcher menu; 7in 1024x600; LHD, moving
17. B-17: Layout switcher menu; 7in 1024x600; RHD, parked
18. B-18: Layout switcher sheet; phone 393x852; parked
19. B-19: Layout switcher, six rows at 24 px; 5in 800x480; moving
20. B-20: Manage layouts, list and detail with triggers; 7in 1024x600; parked
21. B-21: Manage layouts, list; 5in 800x480; parked
22. B-22: Manage layouts, list then detail; phone 393x852; parked (two frames)
23. B-23: Manage layouts, read-only "Park to edit"; 7in 1024x600; moving
24. B-24: Manage layouts, "All screens" filter; tablet 1180x820; parked
25. B-25: Apps menu from a tile label; 7in 1024x600; parked
26. B-26: Apps menu, flattened; 7in 1024x600; moving
27. B-27: Apps menu, two-column; 10in 1280x720; parked
28. B-28: Apps menu sheet; phone 393x852; parked
29. B-29: Apps menu, gateway-only with Get more apps; 7in 1024x600; parked
30. B-30: Save to phone, three choices; phone 393x852; Android
31. B-31: Save to phone, step guide; phone 393x852; iPhone
32. B-32: Save to phone from the layout switcher; 7in 1024x600; parked
33. B-33: Home screen with app, layout and screen icons; phone 393x852

### Open questions

1. With no gateway or no car, should the vehicle chip be hidden, or show "No car" as a placeholder so the strip does not shift when a car appears?
2. Is "Open beside" a layout edit (parked only) or a one-tap page action allowed while moving, like a page swap?
3. Two layouts on the same automatic trigger: block it in Manage layouts, or let the most recently set one win?
4. Should an automatic layout switch while moving show anything beyond the strip name changing (a text-only toast with Undo), or would that distract the driver?
5. On narrow windows, should the merged connection and vehicle chip lead with the car name or the status word when there is room for only one?
6. Should the layout switcher list cap at six rows while moving, chosen by the user's order, or by the most recently used?
7. How should an icon saved for a layout or a single screen be badged so it is told apart from the app icon at home-screen size?

## C. Driving, warnings and input

This section covers what the shell changes while the car moves, how values and actions
show their state, how cautions and warnings appear, and how the screen is used without touch
(soft keys, focus, steering-wheel buttons). Everything here is drawn by the shell, so every
app looks and behaves the same.

Terms used in this section:

- **Shell:** the shared layer every Ostler app bundles. It draws tiles, the top strip, the
  soft-key row and warnings. It has no settings screens and no car logic.
- **Tile:** one rectangle of the screen showing one page from any app.
- **Page:** one view from an app (for example Diagnose, Speed, Trail map).
- **Instrument page:** a page that shows a live car gauge the driver relies on (Speed,
  Attitude, Heading, Transfer). Called a "Drive page" in some older designs.
- **Gateway:** the one native app that talks to the car. It tells the shell whether the car
  is moving and raises alerts. The shell never decides these itself.
- **Strip:** the top bar, 48 px or less on 480 px-high screens, no clock.
- **Driver side / passenger side:** from the car profile. Left-hand drive (LHD) puts the
  driver on the left; right-hand drive (RHD) mirrors the whole layout.
- **ACK:** acknowledge. One press that says "I have seen this warning".
- **Size classes:** Badge, Chip, Compact, Standard, Expanded, chosen from the tile's own
  pixel box (section B covers them).

Where the designer's renders differ from the settled decisions, the decisions win. The main
differences for this section: the renders show a clock in the strip (remove it), a 22 px
moving floor (use 24 px), and a warning taking the driver-side map tile (use the settled tile
order below).

### C1. Moving rules

**Purpose**
- The car moving is not a separate mode or screen. It is a set of rules the shell applies to
  whatever layout is showing, so the driver keeps the same screen, made safer.

**Holds**
- Whatever layout was showing, unchanged in arrangement.
- In the strip: a "Layout locked" indicator (lock icon) in place of the layout editing
  controls.
- A "Park to change" pill wherever a change is refused for the whole surface (layout
  editing, a settings screen opened from an app).
- A one-line refusal reason on any action the driver tries that is not allowed, for example
  "Not while moving".

**States**
- **Parked:** everything available; dividers draggable; effects (blur, glow, texture,
  background image) allowed if the theme uses them.
- **Idling** (engine running, car stopped): treated like Parked for layout editing and
  effects.
- **Moving:**
  - dividers and layout editing locked (no drag, no resize, no Save layout, no close by drag);
  - switching saved layouts and swapping a page into a tile stay one tap, like an aircraft
    display's bezel key;
  - text never below 24 px; touch targets grow (about 76 px, from the visual spec's moving
    sizes);
  - blur, glow, texture and background images off; surfaces become opaque;
  - page parts marked "hide while moving" drop out first;
  - actions that are not allowed show their reason instead of acting.
- **Unknown** (the gateway cannot tell): treated exactly as Moving. Needs a quiet sign that
  the state is unknown, not that the car is moving.
- **Transitions:** Parked to Moving mid-drag cancels the drag and snaps back; an open layout
  editor closes without saving and shows "Park to change". Moving to Parked restores effects
  without a flash or reflow of content.

**Sizes**
- Applies at every size class. At Chip and Compact, the 24 px floor and larger targets mean
  fewer parts fit, so the page drops its lowest-priority parts rather than shrinking text.

**Draw**
- 7in 1024x600, Commute layout, Parked and Moving side by side, LHD, Night.
- 5in 800x480, Main + two, Moving, Night: shows the 24 px floor at its tightest.
- 7in, Moving, the layout switcher open (saved layouts one tap) and the "Park to change"
  pill on the edit entry.
- 7in, Unknown motion state, Night.
- 10in 1280x720, Moving, Day: effects off on a theme that uses them when parked.

**Rules**
- The moving state always comes from the gateway; never infer it from the device.
- Unknown counts as moving. Do not show "Moving" when the truth is "Unknown".
- Nothing about moving may hide a value or warning the driver needs; only editing and
  close-look content steps back.
- No layout shift on the change: tiles keep their positions; only content inside reflows.
- A refusal is never a dialog. It is a one-line reason in place, which fades after a few
  seconds.
- Themes: the theme's moving-safe variant is used here (opaque surfaces, no effects). Note
  where this touches the strip and tile frames; no theme rules are set here.

**Interactions**
- Tap a saved layout: switches at once, at any speed.
- Tap a chip or a tile label's Swap page: swaps at once, at any speed.
- Drag a divider while moving: nothing moves; the "Park to change" pill shows.
- Long press on a tile label while moving: only Swap page and Open beside (if the page
  allows) are offered; Close and Page settings show their reason.

**Reference**
- `mfd/png/mfd-v2-trail-moving.png` ("Layout locked" in the strip; ignore the clock),
  `mfd/png/core-*` (Core moving state), `mfd/designs/Ostler MFD v2.dc.html`,
  `Ostler Core.dc.html`.

### C2. Action permission states (shared component)

**Purpose**
- Every action that changes the car, or that may be limited while moving, shows which of
  three states it is in, the same way on every page. The shell provides this as a shared
  button component; pages declare each action's moving safety and the shell decides the
  state.

**Holds**
- The action's icon and label.
- A state marker: none (available), a question mark and "asks first" (needs confirmation),
  or a no-entry icon and a one-line reason (not allowed).

**States**
- **Available:** normal button.
- **Needs confirmation:** same button, marked "asks first"; pressing opens a confirm sheet
  with Cancel focused.
- **Not allowed, with reason:** visibly unavailable but still readable; reason in plain
  words: "Not while moving", "Needs the gateway", "Not connected", "No permission".
- **Pending:** the request has gone to the gateway and is waiting.
- **Refused by the gateway or hardware:** a one-line reason after the request; the final say
  is the gateway's, not the page's.
- **Moving vs parked:** one action can be Available parked and Not allowed moving (Clear
  faults), or Available parked and Needs confirmation moving.

**Sizes**
- Standard and Expanded: full label plus reason.
- Compact: label plus a short reason; if it does not fit, icon and reason only.
- Chip and Badge: actions are not shown; the shell's chip shows only the summary value.

**Draw**
- Component sheet: the three states plus Pending and Refused, Parked and Moving, at Compact
  and Standard, Night and Day.
- 7in, Moving: the confirm sheet over a tile, Cancel focused.

**Rules**
- Never hide an action that is not allowed; show it with its reason so the driver knows why.
- Never use colour alone; each state has an icon and a word.
- The confirm sheet never auto-confirms and never counts down for anything that changes the
  car. Cancel has focus when it opens, so a double press cannot approve.
- Typing, editing, layout editing, clearing faults, actuator tests and video are never
  allowed while moving, whatever a page declares.

**Interactions**
- Tap or OK on a not-allowed action: reason pulses in place; nothing else happens.
- Confirm sheet: arrows move between Cancel and Confirm; Back cancels.

**Reference**
- `mfd/png/gateway-04.png` ("Actions that change the car": Clear faults, asks first, Not
  while moving), `mfd/designs/Ostler Gateway.dc.html`.

### C3. Trust levels on values (shared component)

**Purpose**
- Every value shows how far it can be trusted. The shell provides a shared value component
  so every app shows trust the same way.

**Holds**
- The value and unit, plus one trust treatment.

**States**
- **Live:** normal.
- **Estimated:** a small "est." badge (word, not colour alone).
- **Stale:** dimmed, with "Last seen 10:42" (or "2 min ago").
- **Unavailable:** a dash, never 0, with a short reason where there is room ("Not live",
  "No sensor").
- **Loading** (first value not yet arrived): a dash with a quiet placeholder, never a
  spinner in a driver-facing tile.
- **Gateway unreachable:** every value on the page turns stale at once, with one page-level
  line ("Can't reach the gateway. Showing what it sent at 10:42.") and actions that need
  the gateway become Not allowed.

**Sizes**
- Badge: the state icon replaces the number when stale or unavailable.
- Chip: value plus a tiny stale or est. marker.
- Compact and up: full treatment with "Last seen" text.

**Draw**
- Component sheet: four trust levels at Chip, Compact and Standard, Night and Day, Moving
  (24 px floor) and Parked.
- Phone 393x852: a Diagnose page with the gateway unreachable (all values stale).

**Rules**
- A missing value is never shown as 0 or as the last value without the stale treatment.
- Stale dimming must still meet the 24 px floor and stay readable at night.
- Trust treatment never uses red or amber; those colours are kept for caution and warning.

**Interactions**
- None of its own; a tap on a stale value may show when and from where it was last seen
  (parked only).

**Reference**
- `mfd/png/gateway-04.png` (phone, "Last seen 10:42", Boost "—  Not live").

### C4. Caution (amber)

**Purpose**
- Tell the driver something needs attention soon, without taking over the screen.

**Holds**
- An amber ring around the tile whose page the problem is about.
- An amber pill in the strip: icon, "CAUTION", and the subject in plain words ("Engine").
- A chime (the host app plays it).

**States**
- **New (unacked):** ring, strip pill, chime once.
- **Acked:** ring and pill stay, quieter; no chime.
- **Cleared:** ring and pill go.
- **Concerned page not on screen:** strip pill only; if the page is a chip, the chip gets
  the amber ring.
- **Concerned tile is the focused tile:** ring and focus ring must both read clearly.
- **Moving vs parked:** same behaviour; caution is never refused.

**Sizes**
- Badge and Chip: amber ring on the chip; icon may switch to the caution icon.
- Compact and up: ring only; the page decides whether to show the related value.

**Draw**
- 7in, Trail layout (Quad), Moving, LHD, Night: caution on the Engine tile.
- 7in with a chip column: caution on a page that is only a chip.
- 10in, Day: caution, to check amber against a light theme.

**Rules**
- Caution never takes over a tile or the screen and never blocks touch.
- Amber means caution only. The ring is a shape as well as a colour (thicker frame, icon in
  the label).
- Caution and warning colours and safety icons are locked; themes cannot change them.

**Interactions**
- Tap the strip pill: opens the page concerned, beside or in place (open question).
- ACK intent with no warning showing: acknowledges the newest unacked caution.

**Reference**
- `mfd/png/mfd-v2-caution.png` (strip pill; the tile ring is not visible in this render).

### C5. Warning (red) takeover and band

**Purpose**
- Tell the driver about something that needs action now, in big plain words, with one
  instruction and one ACK, while keeping instrument pages visible.

**Holds**
- In the chosen tile: "WARNING" label with the safety icon, the problem in big type
  ("Coolant 112 °C"), one plain instruction ("Stop when safe and switch off"), one ACK button.
- In the strip: a red "WARNING" pill with the subject.
- A chime.

**States**
- **Takeover (unacked):** chosen by the settled order:
  1. a tile on the passenger side;
  2. then a tile that is not an instrument page;
  3. then a tile that is not a map with guidance.
- **Band:** if the chosen tile is only a chip, or no tile qualifies, a band across the bottom
  (landscape) or along the side (portrait) instead. It never covers an instrument page.
- **Acked:** the tile returns to its page; the strip's WARNING pill stays until the problem
  clears.
- **Cleared:** pill goes; quiet.
- **Re-raised or escalated** (caution becomes warning): takes over again and needs a new ACK.
- **Over a sheet or confirm:** the warning wins; the sheet closes as Cancel.
- **Moving vs parked:** same; ACK is always allowed.
- **RHD:** the passenger side is the left, so the takeover moves to the left tile.

**Sizes**
- Takeover needs at least Compact; below that, use the band.
- Compact: label, problem, ACK; instruction may wrap to two lines.
- Standard and Expanded: the same content, larger; no extra detail.

**Draw**
- 7in Quad Trail, Moving, LHD, Night: takeover on the passenger-side tile.
- Same, RHD.
- 7in Quad, after ACK: tile restored, WARNING pill still in the strip.
- 7in Android split half (Ostler beside another app), Moving: band across the bottom.
- 5in 800x480, an all-instrument layout: band, no tile covered.
- Phone 393x852 portrait: band (side or bottom; see open questions).
- 10in 1280x720, Day: takeover, to check red against a light theme.

**Rules**
- One warning, one instruction, one ACK. No codes, no extra buttons, no scrolling.
- Never cover an instrument page.
- Never cover the whole screen.
- ACK only acknowledges; it never changes the car.
- The WARNING pill stays in the strip until the gateway clears the problem, even after ACK.
- The designer's MFD v2 render puts the warning on the driver-side map tile; the settled
  order replaces this.

**Interactions**
- Tap ACK, press OK, or press steering-wheel Select: acknowledges.
- Focus jumps to ACK when the takeover appears, and returns to the previous item after.
- Touch elsewhere still works; the takeover does not block other tiles.

**Reference**
- `mfd/png/mfd-v2-master-warning.png` (takeover; wrong tile and has a clock),
  `mfd/png/tiling-v2-03.png` (frame 9e, band in a half split, "Annunciator text shortens to
  fit"), `mfd/designs/Ostler MFD v2.dc.html`, `Ostler Tiling v2.dc.html`.

### C6. Several alerts at once

**Purpose**
- Keep the screen calm when more than one problem is active.

**Holds**
- One item in the strip at a time, plus a count of the others ("+2").
- At most one takeover or band at a time.

**States**
- Strip order: unacked warnings, then unacked cautions, then acked warnings; newest first.
- Two unacked warnings: the newest takes over; after its ACK the next takes over.
- Warning and caution together: the warning takes over; the caution keeps its ring.
- All acked: the strip shows the acked warning(s) until cleared.

**Draw**
- 7in: strip states sheet (unacked warning, unacked caution, acked warning, with "+n").
- 7in Quad: one warning takeover plus one caution ring on another tile.
- 7in: the alert list opened from the strip (parked and moving).

**Rules**
- Never stack takeovers or bands.
- The count must not shorten the subject text below the 24 px floor; shorten the subject
  instead ("Coolant").

**Interactions**
- Tap the strip item: opens a short list of active alerts (read-only while moving).
- ACK repeatedly works through unacked warnings, then cautions.

**Reference**
- None drawn yet.

### C7. Soft-key row

**Purpose**
- Give the focused page up to five labelled actions in fixed positions, usable by touch,
  steering-wheel buttons or a keypad without looking for them.

**Holds**
- A row along the bottom, five fixed slots.
- Each slot: the label (and icon) declared by the focused page for that slot.
- A marker showing which tile the row belongs to (for example the focused tile's name, or a
  link to its focus ring).

**States**
- **Full:** five keys.
- **Partial:** fewer keys; empty slots stay empty so positions never shift.
- **Hidden:** the focused page declares none, or the user turned the row off.
- **Moving:** keys whose actions are not allowed show the reason ("Not while moving") and do
  nothing; keys needing confirmation open the confirm sheet.
- **Focus changes:** the row's labels change to the newly focused page's keys.
- **Warning showing:** the row stays; ACK is not a soft key.

**Sizes**
- Independent of the tile's size class; the row belongs to the screen, not the tile.

**Draw**
- 7in, Workshop layout, Diagnose focused, five keys, Parked and Moving (one key refused).
- 5in 800x480, three keys with two empty slots, Moving.
- 5in, row hidden (focused page has none).
- Phone 393x852 portrait, row at the bottom.

**Rules**
- Slots are stable: the same action stays in the same slot on a page.
- The row must not overlap the focused tile's content or the warning band.
- Labels are short words, at least 24 px while moving.
- Whether the row hides or stays empty when a page has no keys is an open question, as it
  changes the tile area.

**Interactions**
- Tap a key; or softkey-1 to softkey-5 from buttons or Ostler Controls.
- Focus can move into the row; arrows move along it.

**Reference**
- `mfd/png/v1-mfd.png` (earlier edge soft keys, READ / LIVE / HELP / CLEAR; replaced by
  one bottom row), `mfd/designs/Ostler MFD.dc.html`.

### C8. Focus ring and focus order

**Purpose**
- Make every touch action reachable without touch, with a clearly visible focus ring and a
  predictable order across tiles.

**Holds**
- A focus ring: 3 px outline with a 2 px gap, no glow, no size change, no animation.
- Focus zones: strip, tiles, soft-key row, sheets.

**States**
- **No focus shown:** after touch; the ring appears only after a key or button press.
- **Tile focused:** ring on the tile frame; its soft keys show in the row.
- **Item focused inside a tile:** ring on the item; tile frame shows it is the active tile.
- **Engaged control** (slider, map): arrows adjust instead of moving focus; a visible
  engaged state.
- **Sheet open:** focus is trapped in the sheet until Back or a choice.
- **Warning takeover:** focus on ACK.
- **Moving:** same rules; the focused item never grows or reflows.

**Sizes**
- Badge and Chip tiles are one focus stop (OK swaps or opens).
- Compact and up: focus can enter the tile.

**Draw**
- 7in Quad LHD: focus order shown as numbered overlay, plus ring on a tile and on an item.
- Same, RHD (order mirrors).
- 7in: focus on a chip in the chip column; focus in the strip.
- Ring on a light theme, Day, 10in.

**Rules**
- Order across tiles: suggest driver side first, top to bottom, then towards the passenger
  side; the strip is above, the soft-key row below. Confirm this order (open question).
- Arrow keys inside a tile move to the nearest item in that direction; at the tile's edge
  they move to the neighbouring tile.
- Focus is never shown by colour alone and is never hidden under the strip or a sheet.

**Interactions** (how input intents map)
- **up, down, left, right:** move focus; inside an engaged control, adjust.
- **ok:** activate the focused item; acknowledges if a warning is showing.
- **back:** close a sheet, release a control, or move focus out to the tile.
- **menu** (long press Back, 600 ms): jump to the strip (layout switcher).
- **mark:** mark a moment (page decides, for example a Logs note).
- **softkey-1 to softkey-5:** the focused page's soft keys.
- **next-layout:** switch to the next saved layout (allowed while moving).
- **ack:** acknowledge the warning, else the newest caution.
- **focus-next:** move focus to the next tile in the stable order.

**Reference**
- `mfd/png/v1-mfd.png` (focused ENGINE system shows a ring style).

### C9. Steering-wheel buttons

**Purpose**
- Use the buttons the car already has; Ostler adds no labelled hardware.

**Holds**
- No surface of its own; maps to the intents above. A one-time key test screen lives in the
  gateway app (not this section).

**States**
- **Warning showing:** Select acknowledges it.
- **No warning:** Select is left to the media app or head unit; a long press acts in Ostler
  (meaning to be confirmed).
- **Buttons not detected:** nothing changes on screen.

**Draw**
- 7in: a small key-reference card (low fidelity) showing what each button does with and
  without a warning.

**Rules**
- Steering-wheel buttons never change the car beyond acknowledging a warning.
- No hidden gestures: any button action must also be possible by touch.

**Interactions**
- Short press Select: ACK only while a warning shows. Long press: see open questions.

**Reference**
- None drawn.

### C10. Ostler Controls overlays (separate optional app, low fidelity)

**Purpose**
- An optional native Android app that catches steering-wheel buttons while another app
  (for example navigation) is in front, and draws two overlays over it. Sketch at low
  fidelity only.

**Holds**
- **Soft-key strip over other apps:** the same five slots, bottom by default, driver side in
  portrait; actions per saved layout.
- **Floating gauge:** one small value (for example coolant or speed), draggable.

**States**
- Overlay shown, hidden, gateway unreachable (values stale), warning raised while another app
  is in front (open question).

**Draw**
- 7in: a navigation app full screen with the soft-key strip overlay, Moving.
- 7in: the same with the floating gauge, Night.

**Rules**
- Same 24 px floor and trust levels as inside Ostler.
- Overlays must not cover the other app's turn instruction.

**Interactions**
- Tap a key; drag the gauge; tap the gauge to open Ostler.

**Reference**
- None drawn; the designer placed soft keys "later, as a separate overlay app" (REVIEW.md).

### Frame list

1. C-01: Moving rules, Commute layout, 7in 1024x600, Parked and Moving, LHD, Night.
2. C-02: Moving at the tightest size, Main + two, 5in 800x480, Moving, Night.
3. C-03: Layout switcher open while moving with "Park to change", 7in, Moving, Night.
4. C-04: Unknown motion state, 7in, Night.
5. C-05: Effects off while moving, 10in 1280x720, Parked and Moving, Day.
6. C-06: Action permission states component sheet, Compact and Standard, Parked and Moving, Night and Day.
7. C-07: Confirm sheet with Cancel focused, 7in, Moving, Night.
8. C-08: Trust levels component sheet, Chip, Compact and Standard, Moving and Parked, Night and Day.
9. C-09: Gateway unreachable, all values stale, phone 393x852, Night.
10. C-10: Caution on a tile, Trail Quad, 7in, Moving, LHD, Night.
11. C-11: Caution on a chip-only page, 7in with chip column, Moving, Night.
12. C-12: Caution, 10in 1280x720, Day.
13. C-13: Warning takeover, passenger-side tile, Trail Quad, 7in, Moving, LHD, Night.
14. C-14: Warning takeover, same layout, 7in, Moving, RHD, Night.
15. C-15: Warning after ACK (tile restored, pill stays), 7in, Moving, LHD, Night.
16. C-16: Warning band, Android split half on 7in, Moving, Night.
17. C-17: Warning band over all-instrument layout, 5in 800x480, Moving, Night.
18. C-18: Warning band, phone 393x852 portrait, Night.
19. C-19: Warning takeover, 10in 1280x720, Day.
20. C-20: Strip alert states sheet (unacked warning, unacked caution, acked warning, "+n"), 7in strip, Night and Day.
21. C-21: Warning plus caution at once, 7in Quad, Moving, Night.
22. C-22: Active alerts list from the strip, 7in, Parked and Moving.
23. C-23: Soft-key row, five keys, Diagnose focused, 7in, Parked and Moving.
24. C-24: Soft-key row partial (three keys), 5in 800x480, Moving.
25. C-25: Soft-key row hidden, 5in 800x480, Moving.
26. C-26: Soft-key row, phone 393x852 portrait, Parked.
27. C-27: Focus order overlay and rings, 7in Quad, LHD, Night.
28. C-28: Focus order overlay, 7in Quad, RHD, Night.
29. C-29: Focus on a chip and in the strip, 7in, Night.
30. C-30: Focus ring on a light theme, 10in 1280x720, Day.
31. C-31: Steering-wheel key reference card, 7in, low fidelity.
32. C-32: Ostler Controls soft-key strip over a navigation app, 7in, Moving, low fidelity.
33. C-33: Ostler Controls floating gauge over a navigation app, 7in, Night, low fidelity.

### Open questions

1. How should Unknown motion look different from Moving in the strip, without alarming the
   driver?
2. Focus order across tiles: driver side first (as suggested), or the main tile first?
3. Soft-key row when the focused page has none: hide it (tiles grow, layout shifts) or keep
   an empty row (stable layout, lost space)?
4. How does the soft-key row show which tile it belongs to?
5. Warning band on a portrait phone: along the passenger side (as the spec says) or across
   the bottom, given how narrow a side band would be?
6. Tapping a caution pill: open the page concerned in place, beside, or show the alert list?
7. Several alerts: is "+n" in the strip enough, or does the alert list need a dedicated
   entry?
8. Long press on steering-wheel Select when no warning shows: what should it do in Ostler,
   and what feedback confirms it?
9. Should Ostler Controls show a warning while another app is in front (a band over that
   app), or only chime and light its strip?
10. Where does a refusal reason appear for an action triggered by a steering-wheel button
    when the page is not focused or not on screen?

## D. States and hand-offs

This section covers what every tile and the shell look like when things are not normal: no gateway yet, a weak connection, no data yet, a page that cannot draw, a page from someone else, and only one app installed. It also lists where a theme touches the shell and what the shell never does.

Terms used here:
- **Shell:** the shared layer every Ostler app bundles. It draws tiles, the top strip, dividers, warnings, soft keys and focus. It has no screens of its own beyond these.
- **Gateway:** the one place that talks to the car and stores everything. It can be the Ostler Brain (a box in the car), the Ostler Gateway Android app on a phone or head unit, a small node, or a temporary gateway inside a browser tab. The **gateway app** is its user interface.
- **Tile:** one rectangle on screen showing one page from any app.
- **Size class:** how much a tile shows, picked from the tile's own pixel box: Badge, Chip, Compact, Standard, Expanded (see section on sizes).
- **Connection chip:** the small status pill in the top strip. The gateway supplies its words ("Connected", "Connected · via Brain", "Connecting…", "Last seen 10:42", "No gateway"). Tapping it opens the gateway app.
- **Moving / Parked:** the car's state as the gateway reports it. Unknown counts as Moving.
- **Stale:** data the app cached earlier, shown because nothing live is available.

General rules for this whole section:
- Calm, plain words. No error codes on screen. Say what is shown and what to do.
- Never an empty grid. There is always at least one real page on screen.
- Hand-offs open the gateway app (or ostler.app's connect flow in a browser). The shell never does the gateway's job itself.
- Minimum text while Moving is 24 px; touch targets are larger while Moving.

---

### D1. First run: no gateway known

**Purpose**
- What any Ostler app shows the first time it opens and no gateway has ever been found. It gets the person to the gateway's connect flow with one tap.

**Holds**
- The open app, full screen, as a single tile.
- A calm prompt inside it: a short line on what Ostler needs ("Ostler reads your car through a gateway"), one main button, and a quiet secondary link.
  - Main button: **Connect your car**. On a device that has the gateway app: opens it. Otherwise: opens ostler.app's connect flow.
  - If a gateway is found nearby on the network, the main line becomes "Gateway found nearby · Discovery 2 Td5" with **Connect**, which still hands off.
  - Secondary: "Other ways to connect" (also hands off; the list itself is the gateway's).
- Top strip: layout switcher (one item), connection chip reading "No gateway", settings button.
- Whatever the app can show without a car (for example Logs' imported files, Maintenance's notes) may sit under the prompt. Nothing pretends to be live.

**States**
- No gateway known, nothing found: prompt with **Connect your car**.
- Gateway found nearby: prompt names it, **Connect**.
- Hand-off in progress (the gateway app or connect page is opening): button shows a short busy state, then the other app takes over.
- Returned without connecting: prompt as before, no nagging, no repeat pop-ups.
- Connected on return: prompt disappears; the app shows its normal page; chip reads "Connected".
- Moving: the prompt stays but **Connect** is refused with "Park to connect" (connecting means choosing and pairing, which is not a moving task). Text at 24 px.
- Offline device (no network at all): prompt says the gateway app or a network is needed; no spinner.

**Sizes**
- Always shown full screen, so normally Standard or Expanded.
- Compact (Android split third, small windows): one line plus **Connect your car**; the explanation drops.
- Chip and Badge: not used for first run. If the window is that small, the tile shows the app icon and "Connect" as its summary value.

**Draw**
- Phone 393x852, Parked, Night.
- 7in 1024x600, Parked, Night; plus "gateway found nearby" variant.
- 5in 800x480, Moving (Connect refused).
- Desktop 1440x900, Day (browser, no gateway app: hands off to ostler.app).
- Android split third, Compact.

**Rules**
- The shell does not pair, scan, choose a gateway or ask for Bluetooth, USB or location. It only hands off.
- One prompt. No carousel, no tutorial, no welcome tour inside the shell (the gateway owns welcome).
- Never block the rest of the app: the person can still look around what the app can show offline.
- Do not say "gateway" in the connection chip; the prompt may explain it once in plain words.

**Interactions**
- Tap **Connect your car** or **Connect**: hand off.
- Focus lands on the main button first; Select activates it (except while Moving).
- Back with nothing open does nothing special; it never exits to a launcher (there is none).

**Reference**
- `png/core-1-not-connected.png`, `png/core-sizes-phone.png`, `png/core-sizes-5in.png`, `png/gateway-00.png` (the gateway's own first-run connect, which this hands off to); `designs/Ostler Core.dc.html`, `designs/Ostler Core Sizes.dc.html`.
- Conflict with the renders: Core draws "Connect your car" as a shell page with "Welcome" in the layout switcher and a built-in Car page next. The settled decision wins: that screen is the **gateway app's** welcome. Inside any other app, the shell shows only the short prompt that hands off.

---

### D2. Banners

**Purpose**
- A single thin message across the top of the tile area telling the person something they should know about where data is coming from. Gentle, not alarming.

**Holds**
- An icon, one sentence, an optional action, and a dismiss control. Exactly three banners exist:
  1. **Browser session not recording:** "This browser isn't recording. Drives aren't saved." Action: "Set up recording" (hands off to the gateway app or ostler.app).
  2. **Phone gateway:** "Logs stop when your phone leaves the car." Action: "Learn more" or "Other ways" (hands off to the gateway).
  3. **Gateway unreachable:** "Can't reach your car. Showing saved data from 10:42." Action: "Fix" (opens the gateway app).

**States**
- Hidden (default).
- One banner showing.
- Two conditions true at once: show only the highest; order is unreachable, then not recording, then phone gateway. The others wait.
- Dismissed: hidden until the condition clears and comes back, or until the next session (per banner; see open questions).
- Moving: no banner appears. A banner already showing when the car starts moving hides; the connection chip still carries the state ("Last seen 10:42"). It may return once Parked if still true and not dismissed.
- Condition clears: banner leaves quietly (no "all good" message).

**Sizes**
- The banner belongs to the shell, not a tile, so it spans the tile area under the top strip.
- On 480 px-high screens it must stay to one line and as thin as possible so the tiles keep their size class; consider an overlay that does not resize tiles (open question).
- On phone it may wrap to two lines.

**Draw**
- 7in 1024x600, Parked, Night: each of the three banners.
- 5in 800x480, Parked: unreachable banner (check tile classes do not drop).
- Phone 393x852, Parked, Day: phone gateway banner.
- 7in 1024x600, Moving: same layout with banner hidden and chip reading "Last seen 10:42".

**Rules**
- At most one at a time. Always dismissible. Never while Moving.
- Never red or amber; banners are not warnings or cautions. They must not look like the warning strip.
- Never cover a warning takeover, the soft-key row or the top strip.
- Plain words; never "gateway" unless unavoidable; no blame.

**Interactions**
- Tap the action: hand off to the gateway app.
- Tap dismiss (x): hide.
- Focus: reachable from the strip zone; not focused by default.

**Reference**
- `png/gateway-04.png` (g8 "Can't reach the gateway … Fix" card inside the app); `designs/Ostler Gateway.dc.html`.
- Conflict: g8 draws the unreachable notice as a card inside the page. The settled decision makes it a shell banner, one at a time and hidden while Moving; the page itself shows stale values (D3).

---

### D3. Offline and stale tiles

**Purpose**
- What every tile shows when live data is not arriving: the last known data, clearly marked as old, with nothing that can change the car.

**Holds**
- The page's normal layout with cached values.
- A stale marker per tile: dimmed values and "Last seen 10:42" (time; date if not today).
- Values with no cache show a dash and "Not live".
- Actions that change the car show as unavailable: "Needs connection".
- The connection chip reads "Last seen 10:42".

**States**
- Live: normal.
- Briefly late (a few seconds): no change; avoid flicker.
- Stale: dimmed values, "Last seen" time, car actions unavailable.
- Partly stale: one source dropped (for example the engine computer) while others are live; only the affected values are marked.
- No cache at all: page shows its empty state with "Not live yet".
- Reconnecting: chip "Connecting…"; tiles stay stale until live data arrives, then undim in place without layout shift.
- Viewing another car (history apps): labelled "Viewing: … · not connected". This is not stale and must not look like it.
- Moving: same marks at 24 px; "Last seen" text stays readable.

**Sizes**
- Badge: the summary value dimmed with a small stale mark (shape, not colour only).
- Chip: value dimmed plus short "10:42".
- Compact: key value dimmed, "Last seen 10:42" under it.
- Standard and Expanded: per-value marks plus a tile-level "Last seen" in the tile label.

**Draw**
- 7in 1024x600, two tiles (Diagnose and Logs), Parked, Night: all stale.
- 7in 1024x600: partly stale (one live, one stale).
- 5in 800x480, Moving: stale at 24 px.
- Phone 393x852, Day: Diagnose stale.
- Size strip: one page stale at Badge, Chip, Compact, Standard.

**Rules**
- Stale must be obvious without colour (dimming plus words or a shape).
- Never show a cached value as if live; never animate a stale gauge.
- No car-changing action while stale.
- Do not stack: one stale marker per value, one per tile.

**Interactions**
- Tap the connection chip: opens the gateway app.
- Tap a stale value: normal page behaviour (history still works).
- Disabled car actions explain themselves when tapped or focused.

**Reference**
- `png/gateway-04.png` (g8 stale Diagnose, "Last seen 10:42", "Not live", "Clear faults · Needs the gateway"); `designs/Ostler Gateway.dc.html`.

---

### D4. Loading and skeleton tiles

**Purpose**
- What a tile shows between being placed and having its page and first data.

**Holds**
- Tile frame and label (page name, app icon) straight away.
- A skeleton of the page's layout at its size class: grey blocks where values will go.
- No spinner unless loading passes a set time; then one quiet line "Still loading…".

**States**
- Page code loading: frame and label, skeleton.
- Page loaded, waiting for first data: real labels, value placeholders.
- Cached data available: show it stale (D3) instead of a skeleton.
- Slow (over a few seconds): "Still loading…".
- Failed: becomes the fallback chip (D5).
- Moving: skeletons must not shimmer or pulse; static only.

**Sizes**
- Badge and Chip: app icon and name with an empty value slot.
- Compact, Standard, Expanded: skeleton follows the page's ranked parts for that class.

**Draw**
- 7in 1024x600, three tiles loading at Standard, Compact, Chip, Night.
- Phone 393x852, single tile loading, Day.

**Rules**
- Tile sizes never jump when content arrives.
- No animation while Moving.
- Skeleton blocks must not look like real zero values.

**Interactions**
- Tile label menu works while loading (Swap page, Close).
- Focus can land on a loading tile; soft keys stay hidden until the page declares them.

**Reference**
- None drawn yet in `mfd/png/`.

---

### D5. A page that cannot render, or is unsupported at a size

**Purpose**
- A safe fallback so a tile never shows a broken or squeezed page.

**Holds**
- A shell-drawn chip: app icon, page name, and the page's summary value if available.
- A short reason in the tile label menu or on focus: "Not installed", "Needs an update", "Blocked", "Couldn't load".
- One action: open the page's own app (or get it, via the gateway, if not installed).

**States**
- Unsupported at this class: the page does not draw at the tile's size, so the shell shows the largest class it supports that fits; if none fits, the shell's chip with the summary value.
- Not installed: chip with "Get" (links out via the gateway).
- Version mismatch: chip with "Update".
- Blocked (permission refused in the gateway): chip with "Allowed in Gateway" link.
- Failed to load: chip with "Try again".
- Stale summary: chip marked stale (D3).
- Moving: chip only; "Get" and "Update" refused with "Park to …".

**Sizes**
- Badge: icon and summary value.
- Chip: icon, name, summary value.
- At Compact and larger the fallback chip sits centred in the tile with the reason line, not stretched.

**Draw**
- 7in 1024x600, Parked: one tile in each of: not installed, needs update, couldn't load.
- 5in 800x480: a page too big for its tile falling back to a chip.

**Rules**
- Never squeeze a page into a class it does not support.
- Never show raw errors or blank tiles.
- The rest of the layout is unaffected.

**Interactions**
- Tap: opens the page's own app (or the stated action).
- Tile label menu: Swap page, Close.

**Reference**
- `png/tiling-v2-01.png`, `png/tiling-v2-02.png` (overflow chips with icon and value); `designs/Ostler Tiling v2.dc.html`.
- Conflict: those overflow chips show icon and value with no name; under the five classes that is a Badge. A Chip includes the name.

---

### D6. A third-party page hosted in a frame

**Purpose**
- Show pages from apps not made by Ostler, safely, and make clear they are not Ostler's.

**Holds**
- The page inside its tile, as usual.
- A subtle marker in the tile label: a small "outside app" icon and the publisher's name or domain.
- Its car permissions come from the gateway, per app and per car; the marker leads there.

**States**
- Normal: page plus marker.
- Loading: as D4.
- Permission not yet granted: the page shows its own request; the gateway asks (never the shell).
- Permission refused: page shows what it can without car data.
- Failed or blocked: fallback chip (D5).
- Moving: same moving rules; actions it asks for go through the gateway's checks.

**Sizes**
- Same five classes; the shell tells the frame its class and size. At Badge and Chip the shell draws the chip from its summary.

**Draw**
- 7in 1024x600, Night: an Ostler page beside a third-party page.
- Close-up of the tile label marker at Chip and Standard.

**Rules**
- The marker is quiet but always present; it cannot be hidden or restyled by the page or a theme.
- A third-party page cannot draw over the top strip, warnings or soft-key row, and cannot imitate the connection chip or warning strip.
- No car action except through the gateway's permission flow.

**Interactions**
- Tap the marker or "About this app" in the tile label menu: shows publisher, link to its permissions in the gateway app.
- Tile label menu as usual.

**Reference**
- None drawn yet in `mfd/png/`. Permissions screen: `png/gateway-02.png` or `png/gateway-03.png` (per-app car permissions).

---

### D7. The empty layout: only the open app

**Purpose**
- What the screen looks like when no other Ostler app is installed.

**Holds**
- The open app's page full screen. No empty tiles, no placeholder grid.
- Top strip as normal.
- Ideas for more apps are the gateway's (on its Car page, from what the car can do). Inside another app the shell may show at most a quiet "Get more apps" item in the layout switcher, which opens the gateway.

**States**
- One app installed: full screen.
- First extra app installed: it opens beside the current one (passenger side) with Undo.
- Moving: layout locked; nothing to suggest.

**Sizes**
- Full screen, so Standard or Expanded, Compact in a split-screen window.

**Draw**
- 7in 1024x600, Parked, Night: Diagnose alone.
- Phone 393x852: same.
- 7in 1024x600: first extra app opened beside, with Undo.

**Rules**
- Never an empty grid.
- No store inside the shell; "get more apps" always links out through the gateway.

**Interactions**
- Layout switcher: "Get more apps" opens the gateway.
- Undo after a new app opens beside.

**Reference**
- `png/core-2-connected-no-apps.png`, `png/core-3-first-app.png`; `designs/Ostler Core.dc.html`.
- Conflict: Core shows the Car page with suggestions as the shell's own. That is the gateway app's Car page; the chip text "Brain · live" should be the gateway's wording ("Connected · via Brain").

---

### D8. Where themes touch the shell

**Purpose**
- A list only. Themes are decided (the designer's Themes v2, day and night). Nothing new here.

**Holds** (surfaces a theme restyles)
- Top strip.
- Dividers between tiles.
- Tile frame.
- Tile labels.
- Chips (Badge and Chip tiles, connection chip, overflow chips).
- Focus ring.
- Soft-key row.
- Also banners (D2), stale marks (D3) and skeletons (D4) inherit theme colours and shapes.

**States**
- Day and Night as Themes v2 decides: Auto, Day or Night; Auto follows the headlights, then the light sensor, then sunset.
- Moving: the theme's safe version (as already decided).

**Draw**
- No extra frames: draw this section's frames in Night, with Day versions where listed.

**Reference**
- `png/themes-v2-00.png` … `themes-v2-10.png`; `designs/Ostler Themes v2.dc.html`.

---

### D9. What the shell does not do

**Purpose**
- A firm boundary so no shell design grows these screens.

**Holds** (all belong to the gateway app)
- No settings screens. The shell draws only a settings button, which opens the gateway's shared settings.
- No Car page and no instrument pages.
- No pairing, connecting, scanning or choosing a gateway.
- No hardware: Bluetooth, USB, dongles, nodes, buses.
- No car commands; the only key action is acknowledging a warning.
- No car profiles, no vehicle switching (the shell shows the vehicle chip only).
- No permissions screens (car data or web).
- No app store; links to get apps go through the gateway.

**Rules**
- Any shell surface that needs one of these is a hand-off: tap opens the gateway app at the right section.

**Reference**
- Gateway brief: `references/design/2026-10/brief/00-structure.md`.
- Gateway settings spec: `specs/2026-10-11-gateway-settings-design.md`.
- Gateway designs: `png/gateway-00.png` … `gateway-04.png`.

---

### Frame list

1. D-01 First run, no gateway, phone 393x852, Parked, Night.
2. D-02 First run, no gateway, 7in 1024x600, Parked, Night.
3. D-03 First run, gateway found nearby, 7in 1024x600, Parked, Night.
4. D-04 First run, Connect refused, 5in 800x480, Moving, Night.
5. D-05 First run in a browser, hands off to ostler.app, desktop 1440x900, Day.
6. D-06 First run, Compact, Android split third, Parked.
7. D-07 Banner: browser not recording, 7in 1024x600, Parked, Night.
8. D-08 Banner: phone gateway, phone 393x852, Parked, Day.
9. D-09 Banner: gateway unreachable, 7in 1024x600, Parked, Night.
10. D-10 Banner: gateway unreachable, 5in 800x480, Parked (tile classes kept).
11. D-11 Banner hidden while Moving, chip "Last seen", 7in 1024x600, Moving.
12. D-12 All tiles stale, 7in 1024x600, Parked, Night.
13. D-13 Partly stale, 7in 1024x600, Parked, Night.
14. D-14 Stale at 24 px, 5in 800x480, Moving.
15. D-15 Stale Diagnose, phone 393x852, Day.
16. D-16 Stale size strip: one page at Badge, Chip, Compact, Standard.
17. D-17 Loading skeletons at Standard, Compact, Chip, 7in 1024x600, Night.
18. D-18 Single tile loading, phone 393x852, Day.
19. D-19 Fallback chips: not installed, needs update, couldn't load, 7in 1024x600, Parked.
20. D-20 Page too big falls back to a chip, 5in 800x480.
21. D-21 Third-party page beside an Ostler page, 7in 1024x600, Night.
22. D-22 Third-party marker close-up at Chip and Standard.
23. D-23 Only one app installed, 7in 1024x600, Parked, Night.
24. D-24 Only one app installed, phone 393x852.
25. D-25 First extra app opens beside with Undo, 7in 1024x600, Parked; RHD and LHD.

### Open questions

1. Should a dismissed banner stay dismissed for the session, for a day, or until its condition changes?
2. On 480 px-high screens, should a banner overlay the tiles (no resize) or push them down (risking a size-class drop)?
3. When the car starts moving with a banner showing, should it hide at once or fade after a short delay?
4. How should "Last seen" read for data older than today: date, "yesterday", or relative time?
5. Should "Get more apps" in the layout switcher exist at all, or only on the gateway's Car page?
6. How visible should the third-party marker be at Badge size, where there is barely room for an icon?
7. Should a stale tile show its "Last seen" in the tile label, in the page, or both?

## Deliverables

- **114 frames:** A-01 to A-23, B-01 to B-33, C-01 to C-33, D-01 to D-25, in one design file
  per section (`shell-A-frame-layout`, `shell-B-strip-menus`, `shell-C-driving-input`,
  `shell-D-states`) plus a PNG per frame named by its id (`A-01.png`).
- **Components** for the shared parts: tile frame at the five classes, strip, chips, soft-key
  row, focus ring, caution pill, warning takeover and band, banners, stale and third-party
  marks.
- **Answers or proposals** for the open questions, marked with the question's section and
  number.

## Changelog

- 1.0 (2026-10-11): first version, written per section by four sub-agents from ADR-0052, the
  shell, gateway settings and shell-input specs, the MFD hand-off and its review decisions.
