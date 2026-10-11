---
title: "ADR-0052 — The MFD: pages at five size classes from their own tile, and the ostler-shell library every app bundles"
area: decisions
status: draft
version: 0.2
updated: 2026-10-11
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0047-openness-round.md, decisions/adr-0048-ostler-as-an-android-launcher.md, references/research/responsive_tile_sizes.md, references/research/driver_distraction_rules.md, references/research/ui/head_unit_ui.md, references/design/2026-10/brief/00-direction-mfd.md, references/design/2026-10/brief/00-structure.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-theme-engine-design.md]
summary: >
  Proposed (draft for the owner, 2026-10-11), from the owner and designer's MFD brief and the owner's corrections. The screen is an aircraft-style multi-function display: a layout of tiles, each showing one page from any installed app. Each app has its own home and settings; the gateway is an app of its own (connections, devices, hardware, permissions, garage). Every app bundles a separate library repo, ostler-shell (tiling engine, window rules, size classes and snapping, page contract, moving rules, theme resolver, apps menu, layout format, vehicle chip); there is no launcher and no shell app, whichever app is open hosts the tiles. Own apps' pages are same-origin page modules; iframes only for third-party pages; tiles talk over BroadcastChannel; layouts are versioned and synced through the gateway; an unrenderable page shows as a chip. Five size classes (Badge, Chip, Compact, Standard, Expanded) picked from the tile's own box with enter and exit thresholds; JS writes data-size; layoutClass becomes deviceClass. A page contract (sizes, summary value, ranked parts, per-action moving safety, VSS data requirements, links). No drive modes: moving is a set of shell rules on actions, with a 24 px text floor kept. Shared preferences and the vehicle switcher live in the gateway. Save to phone per app, layout or screen. Warnings, theme import safety and performance in brief. Amends ADR-0049 v1.3: the MFD and the gateway's Car page replace the front-door Home and the Drive PWA.
---

# ADR-0052 — The MFD: pages at five size classes, and the ostler-shell library

- **Date:** 2026-10-11
- **Status:** **proposed** (draft for the owner). Written from the owner and designer's
  brief ([direction brief](../references/design/2026-10/brief/00-direction-mfd.md)) and the
  owner's corrections of 2026-10-11, which this text follows where they differ.
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
- **Layout format:** versioned (successor to `ostler.layout/1` in the drive-modes spec §4),
  stored in the gateway and synced. Saved layouts switch in one tap and may switch
  automatically (car started, low range, parked).

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
- **links** to other pages (open beside, shared cursor).

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

### 7. Save to phone

- **Whole app:** a normal PWA install.
- **A saved layout or a single screen:** its own manifest `id` and `start_url`, so it gets
  its own icon.
- Manifest **`shortcuts`** for common pages. Layouts sync via the gateway.
- Bench test: several installs from one origin on Chrome Android and the Dudu7.

### 8. Warnings, themes and performance (in brief)

- **Warnings:** a caution rings its tile, lights the strip and chimes. A warning takes the
  passenger-side tile that is not an instrument page until ACK, and never covers a Drive or
  instrument page (as a band if that tile is a chip); the strip label stays until the
  problem clears.
- **Themes:** custom CSS imports pass a sanitiser (variables and allowed properties only; no
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

## Confirmation

- A size-class test: the pure function gives the research §8 checks (800 × 480 full tile is
  Expanded; half is Standard; a third of 1024 × 600 is Compact) and does not flicker across
  the exit margins while a divider is dragged.
- A contract test: the shell never mounts a page at an unsupported class, and an
  unrenderable page shows as a chip.
- A moving test: with speed above zero, every `not-while-moving` action is refused and
  layout editing is locked, while saved-layout switching still works.
- Bench: four live tiles with one map on the Dudu7; several installs from one origin.

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
- **ADR-0048:** stays parked; no launcher.
- **ADR-0050:** the Android template wraps the same pages and bundles `ostler-shell`.

## Changelog

- 2026-10-11 — v0.1, proposed: from the owner and designer's MFD brief with the owner's
  corrections of 2026-10-11.
- 2026-10-11 — v0.2, proposed: §6 adds the gateway's three levels of settings and car profiles
  (gateway settings spec).
