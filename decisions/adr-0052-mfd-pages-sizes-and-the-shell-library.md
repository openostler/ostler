---
title: "ADR-0052 — The MFD: pages at five size classes from their own tile, and the ostler-shell library every app bundles"
area: decisions
status: draft
version: 0.7
updated: 2026-10-12
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0047-openness-round.md, decisions/adr-0048-ostler-as-an-android-launcher.md, references/research/responsive_tile_sizes.md, references/research/driver_distraction_rules.md, references/research/ui/head_unit_ui.md, references/design/2026-10/brief/00-direction-mfd.md, references/design/2026-10/brief/00-structure.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-theme-engine-design.md, references/design/2026-10/mfd/README.md, references/design/2026-10/mfd/REVIEW.md, references/research/touch_tiling_edit_mode.md]
summary: >
  Proposed (draft for the owner, 2026-10-11), from the owner and designer's MFD brief and the owner's corrections. The screen is an aircraft-style multi-function display: a layout of tiles, each showing one page from any installed app. Each app has its own home and settings; the gateway is an app of its own (connections, devices, hardware, permissions, garage). Every app bundles a separate library repo, ostler-shell (tiling engine, window rules, size classes and snapping, page contract, moving rules, theme resolver, apps menu, layout format, vehicle chip); there is no launcher and no shell app, whichever app is open hosts the tiles. Own apps' pages are same-origin page modules; iframes only for third-party pages; tiles talk over BroadcastChannel; layouts are versioned and synced through the gateway; an unrenderable page shows as a chip. Five size classes (Badge, Chip, Compact, Standard, Expanded) picked from the tile's own box with enter and exit thresholds; JS writes data-size; layoutClass becomes deviceClass. A page contract (sizes, summary value, ranked parts, per-action moving safety, VSS data requirements, links). No drive modes: moving is a set of shell rules on actions, with a 24 px text floor kept. Shared preferences and the vehicle switcher live in the gateway. Save to phone per app, layout or screen. Warnings, theme import safety and performance in brief. Amends ADR-0049 v1.3: the MFD and the gateway's Car page replace the front-door Home and the Drive PWA. v0.5 adds, from the designer's hand-off (references/design/2026-10/mfd/): the top strip order (layout switcher, connection chip, warning strip, shared-settings button; no clock), the connection chip from the gateway, the tile label menu, each app's navigation only at Standard and Expanded, the shared cursor, warning takeover details and the theme rules; the designer's 22 px floor and four classes stay open. v0.6 (owner and designer, 2026-10-12, with the touch tiling research): no permanent divider bars; a parked-only, press-and-hold edit mode like the Android home-screen editor (grabbable edges, a page tray like a widget picker, a live snap preview with size labels and haptics, a non-drag path for the wheel and keyboard, Done); a page dropped on a tile splits it along its longer side; a frameless Chip or Compact page is a widget; a carousel of saved layouts with page dots replaces the strip's layout dropdown, and while moving layouts change only by the wheel and triggers; native Android extras (other apps' widgets as tiles, open beside) only where the Gateway Android app hosts the shell; no native tiler, overlays only for Ostler Controls. Four new owner decisions. v0.7: the owner decided 7 to 10 as recommended (Gateway app may host the shell full screen; while moving, layouts change only by the wheel and triggers; Show frame is a tile setting; no locked primary tile), so §2a is approved; the steering wheel is a D-pad moving a cursor spatially between tiles, and moving it off the screen edge pages to the adjacent layout; the soft-key row is optional (a shared setting).
---

# ADR-0052 — The MFD: pages at five size classes, and the ostler-shell library

- **Date:** 2026-10-11
- **Status:** **proposed** (draft for the owner). Written from the owner and designer's
  brief ([direction brief](../references/design/2026-10/brief/00-direction-mfd.md)) and the
  owner's corrections of 2026-10-11, which this text follows where they differ. The
  designer's hand-off of the same day (designs, renders and a review of the drift) is in
  [references/design/2026-10/mfd/](../references/design/2026-10/mfd/README.md).
- **Would amend:** [ADR-0049](adr-0049-open-vehicle-data-standard-and-app-suite.md) v1.3
  (the front-door Home and the Drive PWA are replaced by the MFD and the gateway's Car page;
  the front door merges into the gateway app), the
  [drive-modes spec](../specs/2026-10-07-drive-modes-and-editing-design.md) (no drive modes)
  and [ADR-0034](adr-0034-repo-boundaries.md) (adds `ostler-shell`; drops `ostler-app-drive`).
- **With:** [ADR-0053](adr-0053-automatic-hardware-detection-in-the-gateway.md) (hardware
  detection in the gateway). Evidence:
  [responsive tiles research](../references/research/responsive_tile_sizes.md).

## Context

- ADR-0049 v1.3 made every screen a separate PWA on one gateway, with a front door (Home,
  apps gallery, garage, devices, permissions, settings) and a separate Drive PWA.
- The owner and designer's brief (2026-10-11) replaces drive modes and the separate Drive
  app with an MFD: one layout of tiles, any app's page in any tile, the same on every
  screen.
- The owner then corrected the brief: there is no shell app or launcher; the gateway is an
  app; every app carries the shell as a library; shared settings live once.
- `ui/src/shell/layoutClass.ts` picks a **device** class from the window. That is right for
  chrome and wrong for page content, which must follow the tile's own box (research §1).

## Decision drivers

- One shell for every screen and every app; nothing extra to install.
- Pages that stay readable at any tile size by dropping parts, never squeezing them.
- Safety while moving decided by what the driver can **do**, not which pages are open.
- Low memory on cheap head units; works offline from one origin.
- One place for the car, driver side, units, theme and layouts.

## Decision

### 1. Apps, the gateway app and the MFD

- **Each app has its own home screen and its own settings**, and installs and runs alone.
- **The gateway is an app** like the others: connections, devices, hardware detection
  (ADR-0053), permissions, outputs and the garage. It also owns the **Car page** (health,
  pinned gauges, suggestions) and ships the **instrument pages** (attitude, heading,
  transfer, speed, engine). It fits into the MFD like any app.
- **The MFD:** the screen is a layout of tiles, each showing one page from any installed
  app. Layouts: Full, Halves, Two thirds, Main + two, Three columns, Quad. One level only;
  tiles never nest. Dividers snap to ⅓, ½, ⅔; double-tap swaps; dragging a tile below its
  minimum closes it, with Undo. "Open beside" opens a linked tile on the passenger side.
- **Tile limits come from pixels,** not device type: a layout is allowed only while every
  tile can get at least Compact (§3); otherwise the extra pages become chips (window rule 3).
  The brief's "2 on 5″, 3 on 7″, 4 on a tablet" are examples, not rules.
- **Window rules, in order:** (1) shape: portrait windows split vertically; under about
  320 px of tile height, tiles go in one row; (2) size class per tile (§3); (3) overflow:
  the main page keeps the space, the others become chips; tapping a chip swaps it in.
- **Driver side comes from the car** (gateway shared preference); right-hand drive mirrors
  the layout. Android split screen just gives a smaller window; the same rules apply.
- **Web entry:** `ostler.app` is the gateway app's web form (welcome, connect, get apps).
  There is no separate front-door app.

### 2. ostler-shell, a library every app bundles

- A separate library repo, **`ostler-shell`**, bundled by every app. It holds the tiling
  engine, window rules, size classes and snapping, the page contract, the moving rules, the
  theme resolver, the apps menu, the layout format and the vehicle chip.
- **No launcher, no shell app.** Whichever app is open hosts the tiles; it is a modular
  website. ADR-0048 stays parked.
- **Hosting other apps' pages:**
  - our own apps, same origin: **page modules** (React components or custom elements)
    loaded into the host's document;
  - **iframes only for third-party pages** (each can cost a renderer process; research §7),
    with the shell posting `{sizeClass, w, h}`;
  - tiles coordinate over **BroadcastChannel** (shared cursor, linked selection);
  - a page the host cannot render (not installed, version mismatch, blocked) shows as a
    **chip** that opens its own app.
- **Shell elements** (designer's hand-off, `Ostler MFD v2` and `Ostler Core`):
  - **Top strip, no clock** (Android shows the time), from the driver's side outward:
    (1) the **layout dots** and, briefly after each change, the layout's name (v0.6: the
    layout dropdown moved into edit mode, §2a); (2) the **connection chip**; (3) the warning
    strip, one item at a time; (4) the shared-settings button, which opens the shared
    preferences (§6). The vehicle chip sits with the connection chip. Right-hand drive
    mirrors the strip.
  - **Connection chip:** in every app; its value comes from the gateway ("Connected",
    "Connected · via Brain", "Connecting…", "Last seen 10:42", "No gateway"); it never says
    "gateway"; tapping it opens the gateway app.
  - **Tile label menu:** Swap page · Page settings (owned by that page's app) · Open beside ·
    Close. The label names the page and, while designing, its app and size class.
  - **Each app keeps its own navigation and settings inside its tile.** Its navigation row
    shows at Standard and Expanded and hides at Compact, Chip and Badge.
  - **Linked tiles share a cursor:** picking a fault in Diagnose moves Logs to that moment.
    A link passes a vehicle, a time window and a signal.
- **Layout format:** versioned (successor to `ostler.layout/1` in the drive-modes spec §4),
  stored in the gateway and synced. Saved layouts switch in one tap and may switch
  automatically (car started, low range, parked).

### 2a. Editing the layout and switching layouts (v0.6; approved by the owner in v0.7)

From the owner and designer's review of the playground (2026-10-12), with the
[touch tiling research](../references/research/touch_tiling_edit_mode.md):

- **No permanent divider bars.** Outside edit mode tiles are separated only by the gap and stay
  fully interactive.
- **Edit mode, like the Android home-screen editor:**
  - **Enter** by pressing and holding a tile or empty space (about 0.5 s, with a haptic), or
    from the wheel. **Parked only:** while moving it cannot open.
  - **In edit mode** the layout scales down slightly; tile edges become grabbable; each tile
    shows a remove button; a **page tray** at the bottom works like a widget picker (search,
    live previews at the class each page would land in); a large **Done** leaves.
  - **Resize** by dragging an edge. **Snap** to ⅓, ½, ⅔ and each size-class boundary, shown as
    the result itself: tiles reflow to the snapped size and show the class they will land in,
    with a light haptic per snap. No guide lines.
  - **Each page declares a size range** (smallest and largest class); edges stop there rather
    than cropping. Dragging a tile below its smallest class removes it, with Undo.
  - **Add and split:** a page dropped on a tile splits that tile along its longer side
    (Hyprland's dwindle rule); dropped on a screen edge it splits there. Presets (Full, Halves,
    2+1, Quad) stay as quick starting points.
  - **Move and swap** by dragging a tile onto another.
  - **Non-drag path** for the wheel, keyboard and switch access: the D-pad cursor (§4a) selects
    a tile, and Move before or after, Wider or Narrower, Taller or Shorter, Remove and Add beside
    apply to it, each announcing the new size (as Android's Launcher3 does).
  - **Layouts are managed here:** name, save, save as new, order, delete, automatic triggers and
    Save to phone (formerly the strip's dropdown and the Manage layouts sheet).
- **Widgets:** a page at Chip or Compact with its frame turned off is a widget; there is no
  separate widget system. "Show frame" is a tile setting in edit mode, allowed at Chip and
  Compact only (decision 9).
- **Layout carousel:** saved layouts sit side by side like home-screen pages, with dots in the
  strip. Switch by swiping on the strip or from the screen edge (never on a tile, where maps and
  charts take the swipe), by moving the D-pad cursor off the screen edge (§4a), or by an
  automatic trigger. The layout's name shows briefly after each change; the carousel stops at
  the first and last layouts (no wrap-round). **While moving,** layouts change only by the wheel
  and triggers; swiping works only when parked (decision 8).
- **Native Android apps:** there is no public Android API to place, resize or embed another
  app's window, and none of this reaches a PWA (research §4). So: **no native tiler**, and
  drawing over other apps is used only by Ostler Controls (§4a). Where the **Gateway Android app
  hosts the shell** (decision 7: an option inside the Gateway app, not a home-screen launcher),
  it may add, as extras: other apps' home-screen widgets as
  tiles (native views laid out on the tile rectangles, with the user's consent), and **Open
  beside** for a native app (best effort; freeform launch bounds only where the head unit
  supports them, recorded per unit). The browser and PWA shell tile Ostler pages everywhere.

### 3. Five size classes, from the tile's own box

Thresholds exactly as research §8 (CSS px of the tile's content box; a class needs both
width and height):

| Class | Enter upward at | Drop back below |
|---|---|---|
| Badge | anything smaller than Chip | — |
| Chip | 120 × 64 | 108 × 56 |
| Compact | 220 × 140 | 204 × 128 |
| Standard | 360 × 260 | 336 × 244 |
| Expanded | 640 × 420 | 608 × 400 |

- **JavaScript is the source of truth:** a pure function `(w, h, previous) → class`
  observes the tile frame, applies the hysteresis and writes `data-size` on the tile. CSS
  uses `container-type: size; container-name: tile` only to fine-tune within a class.
- If a page lacks the class, the shell uses the largest supported class that is no bigger.
- Moving up adds parts; moving down removes the lowest-priority parts. Nothing is squeezed.
  Page state (selected fault, cursor, zoom) survives a class change.
- **Rename `layoutClass` → `deviceClass`**, used for chrome only (rail, bar, strip), never
  for page content.

### 4. The page contract

Each page declares to the shell:

- **supported sizes** (from the five);
- **one summary value** (shown at Badge and Chip);
- **priority-ranked parts** (which go first when space shrinks);
- **moving safety per action:** `safe`, `confirm` or `not-while-moving`;
- **data requirements:** the VSS paths it uses and those it requires. The gateway uses them
  for "apps grow when data appears", "Get more apps that work with this car" and the Car
  page's suggestions;
- **links** to other pages (open beside, shared cursor);
- **soft keys:** up to five labelled actions for when the page has focus (for example "Next
  layout", "Swap page", "Back", "Mark moment"), each with its moving safety. Positions stay
  stable so they can be used without looking.

### 4a. Input: soft keys, steering-wheel buttons and Ostler Controls

- **No cockpit of buttons.** Input is the steering-wheel controls the car already has, plus an
  optional **soft-key row** along the bottom, with no labelled hardware.
- **The soft-key row is optional (v0.7, owner):** a shared setting in the gateway ("Soft-key
  row: On / Off", overridable per screen; on by default on head units, off on phones and
  desktops). When it is off the tiles take the space, and the focused page's soft keys are
  reached from its label menu and with the D-pad.
- **The steering wheel is a D-pad with a cursor (v0.7, owner):** up, down, left and right move
  the cursor (the focus ring) to the nearest tile in that direction; up from the top row reaches
  the strip. Moving the cursor off the left or right screen edge pages to the previous or next
  saved layout, like a home screen, showing its name briefly; it stops at the first and last
  layouts. This works while moving. In edit mode the same cursor selects the tile the edit
  actions apply to.
- **The shell draws the soft-key row** (when on) from the focused page's declared soft keys.
  Focus moves between tiles spatially with a visible focus ring; every action reachable by
  touch is reachable by focus too.
- **Everything maps onto `ShellInput`** ([shell-input spec](../specs/2026-10-07-shell-input-design.md)):
  steering-wheel buttons and soft keys arrive as its intents (up, down, ok, back, menu, mark)
  plus `softkey-1`…`softkey-5`, `next-layout` and `ack`.
- **Select acknowledges a warning only while one is showing** (or on a long press). Otherwise
  it is left to the media app or the head unit. Steering-wheel controls never change the car
  beyond acknowledging a warning; clearing faults and tests still need confirmation on screen.
- **Ostler Controls** is a separate, optional native Android app (Kotlin, ADR-0050). It:
  - catches steering-wheel buttons, including when Ostler is not in front;
  - draws the overlays that need "draw over other apps": the soft-key strip over other apps and
    the **floating gauge** (moved here from the gateway app, which then has no overlay);
  - sends commands (`ack`, `next-layout`, `focus-next`, `softkey-n`) to the **gateway**, which
    passes them to whichever Ostler app is showing. A native app cannot push input into a PWA.
- **Fully customisable:** key mapping per head unit with a learn mode; the number and position
  of soft keys (bottom by default, driver's side in portrait); actions per saved layout.
- **Bench-test items:** how FYT units deliver steering-wheel keys (key events or broadcasts);
  whether catching them outside Ostler needs an accessibility service; Play Store policy on
  accessibility services (F-Droid or direct download as the fallback).

### 5. No drive modes: moving is a set of shell rules

- Instrument pages are ordinary pages; "Off-road" is just a saved layout.
- **While moving, the floor is about actions,** not pages; owners choose pages:
  - no typing or editing; no layout editing (saved layouts and swaps stay one tap);
  - no clearing faults, no actuator tests (ADR-0033, ADR-0044 R5), no video;
  - blur, glow and texture off; larger targets;
  - **text minimum 24 px** (§9, decision 1).
- Settings can be browsed but not changed while moving ("Park to change").

### 6. Shared preferences and the vehicle

- **Shared preferences live once in the gateway:** car, driver side, units, theme and
  layouts. Each app's settings show a small **Shared** section editing the same values.
- **The vehicle switcher belongs to the gateway;** the shell shows a vehicle chip in every
  app. The gateway sets the **connected** car.
- History apps (Logs, Maintenance) may **view** another garage car, clearly labelled
  ("Viewing: … · not connected"). Live data and any car-changing action always follow the
  connected car.
- **The gateway owns all hardware and connections** and keeps settings at three levels:
  account (garage, sharing), **car profile** (one per car, selected automatically from
  detection) and this gateway (role, network, storage, power). Detail:
  [gateway settings spec](../specs/2026-10-11-gateway-settings-design.md).
- **Everything lives in the gateway; PWAs are viewers and controls that only connect to it.**
  Car-data permissions are the gateway's; web permissions (notifications, camera, location)
  are Ostler-wide, because all apps share one address per gateway (gateway settings spec §2).

### 7. Save to phone

- **Whole app:** a normal PWA install.
- **A saved layout or a single screen:** its own manifest `id` and `start_url`, so it gets
  its own icon.
- Manifest **`shortcuts`** for common pages. Layouts sync via the gateway.
- Bench test: several installs from one origin on Chrome Android and the Dudu7.

### 8. Warnings, themes and performance (in brief)

- **Warnings:** colour is used only for state, in plain words.
  - **Caution (amber):** rings the tile the problem is about (if it is on screen), lights the
    strip and chimes; it never takes over a tile.
  - **Warning (red):** takes over one tile until ACK, with big type, one instruction and one
    ACK button. It takes the passenger-side tile that is not an instrument page and never
    covers an instrument page; if that tile is only a chip, it opens as a band across the
    bottom or side. The WARNING label stays in the strip until the problem clears, even after
    ACK. Which tile wins when none fits cleanly is open (hand-off review, decision 9).
- **Themes** (rules from the designer's `Ostler Themes v2`; the set itself is open, hand-off
  review decision 11):
  - a theme changes structure as well as colour: frame, labels, numbers, gauges, controls,
    strip and divider;
  - each theme ships a **day and a night version**; the choice is Auto, Day or Night, and Auto
    follows the headlights signal when the gateway has it, then the light sensor, then sunset
    at the car's position;
  - themes never change layout and tile sizes, touch targets, the drag handles between tiles,
    warning and caution colours or safety icons, and never the protected surfaces, required
    parts or the render check of the theme engine (decisions 5–7);
  - steering-wheel controls and soft keys are not part of a theme (§4a).
- **Theme import:** custom CSS imports pass a sanitiser (variables and allowed properties only; no
  remote `url()` or `@import`); the user's photo stays on the device; contrast is verified
  by the existing render check, not by reading the CSS; warning and caution colours and
  safety icons are locked.
- **Performance:** Chip and Compact pages update less often; only the main tile runs a live
  map.

### 9. Decisions for the owner

1. **Moving text floor: 22 or 24 px?** The brief says 22. The
   [driver distraction research](../references/research/driver_distraction_rules.md) sets no
   general text floor (its `tiles` template asks ≥ 56 px digits, §7.2); the 24 px floor
   comes from the visual spec §4 and the
   [head-unit research](../references/research/ui/head_unit_ui.md) (Android for Cars: text
   ≥ 24 sp, secondary 24 dp). Nothing found supports 22. **Recommend 24 px**; open: whether
   dp on a given head unit equals CSS px.
2. **Module or iframe boundary.** Recommend: page modules for every app we publish from
   `ostler.app` or the Brain; iframes for anything else, including third-party apps on
   another origin.
3. **Where shared preferences live.** Recommend the gateway (synced), with each app's
   Shared section as a view, not a copy.
4. **Gateway app repo name.** Recommend keeping `ostler-app-hub` for now, since it already
   holds the front door; a rename is cosmetic.
5. **Automatic layout switching triggers.** Recommend car started, low range and parked
   only at first.
6. **The designer's hand-off drift.** The designer's docs say 22 px and four size classes
   (Chip, Compact, Standard, Expanded) and limit tiles by screen inches; this ADR keeps 24 px,
   five classes and pixel limits until the owner decides. The full list, with the theme set,
   theme wording and state colours, is the
   [hand-off review](../references/design/2026-10/mfd/REVIEW.md) "Decisions for the owner".

7. **Should the Gateway Android app host the shell full screen?** It is the only way to get
   native widgets as tiles and Open beside for native apps, and it brings back part of the
   parked launcher idea (ADR-0048) as an app, not a home screen. **Recommend yes, as an option
   inside the Gateway app**, not as the default launcher.
   **Decided 2026-10-12 (owner): yes, as an option inside the Gateway app.**
8. **The layout carousel while moving.** **Recommend the wheel and automatic triggers only**;
   swiping only when parked. Alternative: allow swiping on the strip while moving.
   **Decided 2026-10-12 (owner): the wheel and triggers only.** The wheel is a D-pad; moving
   the cursor off the screen edge pages to the next layout (§4a).
9. **Frameless widgets: a page option or a tile setting?** **Recommend a tile setting** in edit
   mode ("Show frame"), allowed at Chip and Compact only; pages need not opt in.
   **Decided 2026-10-12 (owner): a tile setting.**
10. **A locked primary region?** Cockpits always keep the primary flight display. **Recommend
    no fixed tile,** but warnings always have a place (takeover or band) whatever the layout.
    **Decided 2026-10-12 (owner): no fixed tile.**

## Confirmation

- A size-class test: the pure function gives the research §8 checks (800 × 480 full tile is
  Expanded; half is Standard; a third of 1024 × 600 is Compact) and does not flicker across
  the exit margins while a divider is dragged.
- A contract test: the shell never mounts a page at an unsupported class, and an
  unrenderable page shows as a chip.
- A moving test: with speed above zero, every `not-while-moving` action is refused and
  layout editing is locked, while saved-layout switching still works.
- Bench: four live tiles with one map on the Dudu7; several installs from one origin.
- Edit mode (v0.6): press and hold enters it only when parked; every edit has a non-drag path;
  a snap shows the result and its class; the carousel switches layouts by the wheel while
  moving and never by a swipe on a tile.

## Consequences

- `ostler-app-drive` is not created; instrument pages ship with the gateway app.
- The front door's Home becomes the gateway's Car page; its connect, garage, devices and
  permissions pages are the gateway app's.
- Every app gains a dependency on `ostler-shell`, versioned with the layout format.
- `layoutClass.ts` is renamed and limited to chrome; pages move to `data-size`.
- The drive-modes spec's mode switcher and presets become saved layouts.

## Alternatives considered

- **A shell or launcher app hosting the others.** Rejected by the owner: one more thing to
  install; the shell as a library needs none.
- **Iframes for every page.** Rejected: a renderer process each; too heavy for head units.
- **Size from the device type.** Rejected: tiles on one screen differ in size.
- **Drive modes.** Rejected by the owner: a mode duplicates layouts; safety follows actions.
- **Settings per app with no shared store.** Rejected: car, units and theme would drift.

## Relation to other ADRs

- **ADR-0049:** amends v1.3 (front door and Drive PWA); separate PWAs on one gateway stand.
- **ADR-0051:** data requirements are VSS paths; the gateway serves them over VISS.
- **ADR-0053:** the gateway's hardware detection feeds Car-page suggestions.
- **ADR-0033, ADR-0044:** per-action moving safety maps to their categories and rules.
- **ADR-0029:** the garage and connected car.
- **ADR-0047:** style stays a default; the locked items are the safety ones.
- **ADR-0048:** stays parked as a launcher; v0.6 decision 7 asks whether the Gateway app may
  host the shell full screen, which is not a home-screen role.
- **ADR-0050:** the Android template wraps the same pages and bundles `ostler-shell`.

## Changelog

- 2026-10-11 — v0.1, proposed: from the owner and designer's MFD brief with the owner's
  corrections of 2026-10-11.
- 2026-10-11 — v0.2, proposed: §6 adds the gateway's three levels of settings and car profiles
  (gateway settings spec).
- 2026-10-11 — v0.3, proposed: §6 adds "everything lives in the gateway" and Ostler-wide web
  permissions.
- 2026-10-11 — v0.4, proposed: soft keys in the page contract; §4a input: the soft-key row,
  steering-wheel buttons on `ShellInput`, Select as acknowledge only while a warning shows, and
  the optional Ostler Controls app (steering-wheel capture, overlays, floating gauge) sending
  commands through the gateway.
- 2026-10-11 — v0.5, proposed: from the designer's MFD hand-off
  (`references/design/2026-10/mfd/`): §2 shell elements (top strip order with no clock,
  connection chip from the gateway, tile label menu, app navigation only at Standard and
  Expanded, shared cursor); §8 warning takeover details and the theme rules (structure,
  day and night with Auto, the never-change list); §9 item 6 points to the hand-off review.
  Five classes, 24 px and pixel tile limits unchanged.
- 2026-10-12 — v0.6, proposed: §2a editing and switching layouts, from the owner and
  designer's review of the playground and the
  [touch tiling research](../references/research/touch_tiling_edit_mode.md): no permanent
  divider bars; a parked-only, press-and-hold edit mode (grabbable edges, page tray, live snap
  preview with class labels and haptics, non-drag path, Done) that also holds layout
  management; the dwindle split; frameless Chip and Compact pages as widgets; a layout carousel
  with dots replacing the strip's dropdown; native Android extras only where the Gateway app
  hosts the shell. §9 adds decisions 7 to 10.
- 2026-10-12 — v0.7: the owner decided §9 items 7 to 10 as recommended, so §2a is approved;
  §4a adds the D-pad cursor (spatial focus; moving off the screen edge pages to the adjacent
  layout, no wrap-round) and makes the soft-key row optional (a shared setting).
