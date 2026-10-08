---
title: "Launcher and widgets — the Android-model home screen: pages in a carousel, dock, drawer, widget host, widget setup, starter widgets, dashboard builder and theme wizard — design"
area: specs
status: stable
version: 0.5
updated: 2026-10-08
depends_on: [decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-store-design.md, specs/2026-10-07-head-unit-apps-design.md, references/research/ha_integrations_dashboards.md, references/research/driver_distraction_rules.md, references/research/obd_telematics_apps.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, schemas/ostler-layout.schema.json, src/openostler/layouts.py, ui/src/drive/DriveFace.tsx]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", OS round; decision list items 14–21 and 44–53), v0.2; every decision answered as recommended, under ADR-0045 (UX first) and ADR-0046 (the empty OS). The OS launcher follows Android. Home pages are dashboards in a carousel; on a head unit while Moving the carousel is Drive mode, showing each driving page's Moving section, switched by swipe, D-pad or the page chip. The rail becomes the dock (bottom on phones, driver's side on head units) with two anchors, Home and Apps; More becomes the app drawer, always reachable (a short list of driving apps while Moving). App shortcuts and folders go on pages and the dock. Each class has a cell grid; drag, drop with reflow, edge resize and page add, remove and reorder work as on Android, Parked only on driver-facing displays. A widget gallery (By app, By signal) and a widget setup page (a schema form drawn by the OS with live Parked and Moving previews, or an app's own Parked setup view) configure look and data source. The widget SDK contract: manifest, config schema, VSS data bindings, cell sizes, and a required, explicit Moving template. The starter pack lists 24 widgets with their options. Preset dashboards and a dashboard builder wizard run at first run and at any time; a theme wizard sets background, accent, icon pack and gauge style under visual §13. Safety mapping, migration from ostler.layout/1 to ostler.layout/2, phases LW0–LW5, tests and owner decisions. Supersedes the Drive-modes spec's rail (§4.5, §7.3), switcher (§6) and editing (§7) sections. Amended 2026-10-07 (openness round, ADR-0047): caps become defaults with ellipsis and warnings, the dock size is user-set and may hold widgets, anchors are hideable with one recovery path, synthetic widget previews are allowed, and theme rules defer to visual §13 and the theme engine (safety looks restylable under the render check). Parked 2026-10-08 (direction round, ADR-0049): no launcher until the bench test; one normal feed widget; no widget apps.
---

# Launcher and widgets — design

> **Parked 2026-10-08 (direction round,
> [ADR-0049](../decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md)), approved
> by the owner on 2026-10-08 ("I agree with everything"):** the launcher is optional and
> parked until the two-head-unit bench test (direction decision 23;
> [ADR-0048](../decisions/adr-0048-ostler-as-an-android-launcher.md) parked). There are no
> widget apps: the gateway app carries one normal feed widget at about 1 Hz, and live views
> stay inside the apps.

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings";
> [ADR-0047](../decisions/adr-0047-openness-round.md)):** counts and caps that were taste
> become defaults with ellipsis and warnings: pages per class (no cap), the driving set
> (default 6, user may raise), the Moving swipe distance, dynamic shortcuts (no cap), folder
> size and name length, widget description, text and image widget sizes, and the dock's slot
> count (a per-class default; overflow scrolls). The dock may hold widgets; anchors may be
> hidden while one recovery path stays (§6.6). User CSS and an optional free-form placement
> mode (Parked only) are no longer non-goals. Widget previews may use labelled synthetic
> fixtures. §11's theme rules point to [visual §13](2026-10-07-visual-design-system-design.md)
> and the [theme engine](2026-10-07-theme-engine-design.md); safety colours, icons and words
> may be restyled under the Drive-mode render check, and the wallpaper is no longer replaced
> while Moving. The Moving template limits, Park to edit, no car actions in layouts and
> safety widgets that never go are unchanged.

**Status:** approved by the owner on 2026-10-07 ("approve all", OS round; decision list
items 14–21 and 44–53), v0.2. Nothing here is built before its UX briefs are approved
([ADR-0045](../decisions/adr-0045-ux-first.md)). It **supersedes** the
[Drive-modes spec](2026-10-07-drive-modes-and-editing-design.md) §4.5 (rail), §6 (the
switcher) and §7 (editing), and **refines** its §4 (format, now `ostler.layout/2`), §5
(presets, now preset dashboards) and §8 (safety, validation, storage). It extends the widget
contract of [app-model §15](2026-10-06-app-model-design.md) through the
[app UI model spec](2026-10-07-app-ui-model-design.md). The templates and their limits
([UI spec §12.1](2026-10-06-ui-architecture-design.md)), the gate, tiers and categories are
unchanged. The launcher is system UI in the empty OS
([ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md) §1).

## 0. UX briefs first

These briefs come before any UI or wiring (ADR-0045 §1): home pages and the carousel (per
class, Parked and Moving); dock and drawer; edit mode (drag, reflow, resize, pages); widget
picker; widget setup page; dashboard builder; theme wizard; first-run setup. Each lists its
recorded fixtures: a D2 drive with a Td5 session, a SLABS session, a node stream with GPS and
IMU, and a parked alarm event.

## 1. The owner's ask (2026-10-07, condensed)

Dashboards are home-screen pages in a carousel that you swipe through in Drive mode. The
sidebar becomes the dock and "More" becomes the app drawer. Widgets have a setup page where
you pick how they look and where their data comes from. A starter pack brings a gallery of
widgets. App shortcuts go on the dashboard. Drag, drop, resize and adding pages work as on
Android. Extensions bring their own widgets; anyone can make any kind of widget. Preset
dashboards and a dashboard builder wizard, run at setup and at any time. A theme wizard
changes the background.

## 2. Goals and non-goals

**Goals.** One home screen model on every layout class; Drive mode that is simply the home
pages in their Moving form; an editor as familiar as Android's that can never produce an
unsafe Moving screen; widgets anyone can build, configured by one OS-drawn setup page; a
useful screen on first run with no editing.

**Non-goals.** Widgets that act on the car (layouts stay Read only, ADR-0033); animation or
video while Moving. *Amended 2026-10-07 (openness round): free pixel placement is an optional
free-form grid mode (Parked only, never in a Moving section); user CSS is allowed through
themes (visual §13); glow is a theme choice; new Moving templates follow UI spec §12.1.*

## 3. Terms

| Term | Meaning |
|---|---|
| **Page** | One home-screen page: a Parked grid of items and a Moving section. Was "Home" plus "Drive mode face" |
| **Default page** | The page the launcher opens on and Home returns to |
| **Carousel** | The ordered pages, switched by swipe, D-pad `left`/`right` or the page chip |
| **Driving set** | The pages shown while Moving, in order (default ≤ 6, user may raise); was the "rotation" |
| **Item** | A widget, an app icon, a shortcut or a folder on a page or the dock |
| **Dock** | The fixed row (phone) or column (head unit) of items; was the rail |
| **Drawer** | All installed apps; was More |
| **Anchor** | A default item: Home and Apps in the dock; Back and the page chip in the driving strip. It can move and, while the recovery path of §6.6 stays, be hidden |
| **Safety widget** | A system widget that can move but never go: Warnings, Security alert |
| **Widget host** | The OS part that draws widget frames, isolates them and caps refresh |

## 4. Home pages and the carousel

### 4.1 Pages

- Pages belong to a **display × profile × vehicle**, as layouts do today (Drive-modes §8.3).
- A display has **one or more pages** per layout class (no upper cap; *amended 2026-10-07,
  openness round*, was 1–12). One is the **default page** (a house glyph on
  its page dot).
- Each page has a **Parked grid** (§6.1) and a **Moving section** (the Drive-modes §4.3
  mapping, unchanged). The OS fills the Moving section from the page's widgets in reading
  order, using each widget's Moving template; the user can reorder it or drop items from it
  (the Moving strip of Drive-modes §7.4, kept).
- A page whose Moving section is empty or invalid is a **Parked-only page**. It is skipped
  while Moving.

### 4.2 Parked

The carousel works as on Android: a horizontal swipe moves one page; page dots sit above the
dock; D-pad `left`/`right` in `main` move pages (ShellInput §6). The last page used is
remembered per display.

### 4.3 Drive mode is the carousel while Moving

- On a driver-facing display, entering Moving shows the **driving set**: the pages marked
  **Show while driving**, in the user's order, by default at most six (the user may raise
  this in Settings → Home screen). Each shows only its Moving
  section. The display opens the last driving page used, else the first.
- **Switching while Moving** is allowed and has three ways: a **swipe** (a long travel: by default
  at least 30 % of the width, user-tunable, or a fling), D-pad `left`/`right`, or the **page chip** in the
  strip. Page dots are not targets.
- The **page chip** replaces the `drive_mode` chip (Drive-modes §6): icon plus the page name;
  a tap moves to the next driving page; a long press opens a `short_list` of the driving
  pages; it is an anchor in the driving strip. ShellInput's rule that `back` focuses the
  switcher while Moving now focuses the page chip.
- Nothing moves by itself: no auto-advance, no switch at night or on a ride start (Drive-modes
  Decision 6, kept). Pages are not added, removed or reordered while Moving.
- **Back** stays an anchor in the driving strip. On the carousel it focuses the page chip;
  inside an app's Moving view it returns to the carousel.

### 4.4 Always one drivable page

A head-unit class must have at least one valid driving page. The validator refuses a write
that leaves none. If an old file or an uninstalled app leaves none, the OS shows a generated
**Essentials** page while Moving (speed, the worst telltale summary, clock) and offers the
dashboard builder at the next Parked.

### 4.5 Faces and modes retired

A Drive mode's faces become pages (§13). "Drive mode" stays as the name of the head unit's
Moving view of the carousel.

## 5. The dock, the drawer, shortcuts and folders

### 5.1 The dock

Slot counts are **defaults** (*amended 2026-10-07, openness round*); the user may add slots,
and a dock with more items than fit scrolls or opens an overflow.

| Class | Where | Default slots (anchors included) |
|---|---|---|
| Phone | bottom bar, 72 px plus safe area | 5 |
| HU-5, HU-7 | driver's side, 80–96 px | 5 |
| HU-9/10 | driver's side, 112 px | 6 |
| HU-wide | driver's side, 112 px | 7 |
| Tablet, desktop | side, 88 px (labels on desktop) | 7 |

- Two **anchors** by default: **Home** (opens the default page; on the default page it does
  nothing) and **Apps** (opens the drawer). They can move, be renamed, re-iconed and hidden;
  the drawer stays reachable by the recovery path of §6.6 (long press, the Connection sheet,
  holding Back).
- The other slots hold **app icons, shortcuts, folders or widgets** (a widget in the dock uses
  its smallest size).
- The head-unit Drive button of UI spec §3.3 is retired: Moving shows Drive mode by itself,
  and Parked the pages are already the dashboards.
- **While Moving**, a dock item whose target has no Moving view is not drawn and its slot stays
  empty, so nothing shifts. Home and Apps stay.

### 5.2 The drawer

- **Search** at the top (on head units Parked only, since it is text entry), then all apps
  A–Z in a grid of 76 px targets (48 px on phone), then **System**: Settings and Store.
- Long press on an app: **Add to home**, its **shortcuts**, **App info**, **Uninstall** or
  **Disable** (owner role), **Hide**. Hidden apps sit in Settings → Apps → Hidden.
- **While Moving** the drawer stays reachable and opens as a `short_list`: up to six **driving
  apps** (apps with a Moving view, user-ordered in Settings → Home screen; default Media,
  Radio, Phone, Navigation, Map, Diagnostics). Each opens its Moving view. Nothing else is
  listed; no greyed rows.

### 5.3 App shortcuts

- An app declares **static shortcuts** in its manifest (`contributes.shortcuts`: id, label
  ≤ 30 characters by default, icon, route, driving rule) and may publish **dynamic shortcuts**
  (no cap; the launcher shows the most recent first)
  through the SDK ("Call Sam", "Resume route"). The user places them; an app never does.
- A shortcut is a 1 × 1 item on a page or in the dock. In a Moving section it counts as one
  tile and opens its target's Moving view; a shortcut whose target has none cannot be put in
  a Moving section.

### 5.4 Folders

Drop an icon or shortcut on another to make a **folder** (no cap on name length or items; a
long name is ellipsised). A folder opens as a sheet. Folders are never in a Moving section; in the dock while
Moving a folder opens as a `short_list` of its driving items, or is hidden if it has none.

## 6. The grid, drag, drop, resize and pages

### 6.1 Grids per class

Content areas and Moving minimums are those of Drive-modes §4.4; the dock takes the rail's
place.

| Class | Parked grid (cells) | Moving grid | Notes |
|---|---|---|---|
| HU-5 800×480 | 6 × 4 | 3 × 2 | a widget's min size is checked in px, not cells |
| HU-7 1024×600 | 6 × 4 | 3 × 2 | |
| HU-9/10 1280×720 | 8 × 4 | 4 × 2 | |
| HU-wide 1920×720 | 12 × 4 | 6 × 2 | |
| Phone ~393×852 | 4 × 6 | 2 × 3 | |
| Tablet, desktop | 8 × 6 | 3 × 2 | not driver-facing unless declared |

### 6.2 Edit mode

- **Enter:** long press (600 ms) on an empty area, the strip or an item; Settings → Home
  screen → **Edit home screen**; or a long `ok` on a focused item (ShellInput). On a
  driver-facing display while Moving: "Park to edit" for 3 s and nothing else (R1).
- **Edit bar** (top of the content area): Done, Cancel, Undo, Redo, **Widgets**, **Pages**,
  **Wallpaper and theme**, **Preview while driving**, Reset.
- Items show a frame and resize handles; the page shrinks a little so its neighbours peek in
  at the edges (Android). Autosave of the draft as today; the live layout changes on Done.

### 6.3 Drag and drop

- Drag snaps to the grid. **Dropping on occupied cells reflows** the other items to the
  nearest free cells, as Android does; if there is no room the drop **swaps** (Drive-modes'
  rule, kept as the fallback), so a page is never invalid.
- Hold an item at the screen edge for 600 ms to move it to the next page; past the last page
  this **adds a page**.
- Drop on an icon to make a folder (§5.4); drop on the dock to add (icons, shortcuts and
  folders only).
- **D-pad:** `ok` picks up, arrows move cell by cell, `ok` drops (reflow), `back` cancels;
  `menu` opens the item sheet (Size, Settings, Move to page, Remove).

### 6.4 Resize

Edge and corner handles as on Android, each with a 48 px hit area on phone and 76 px on head
units; the widget's `sizes` give min and max. The item sheet keeps a **Size** row that steps
through the allowed sizes, for gloves and the D-pad.

### 6.5 Pages

- **Pages overview** (edit bar → Pages, or pinch in): thumbnails to drag into order, **+**
  to add a page (blank or from a preset), and per page: Rename (long names ellipsised), Set as
  default, **Show while driving** on or off (with the Moving check), Delete.
- An empty page is removed when edit mode closes. Deleting a page with items asks once, with
  Cancel focused; safety widgets on it move to the default page.

### 6.6 Undo, Reset and reachability

Undo and Redo (50 steps), Reset layout (in Settings, the Connection sheet and the edit bar,
with a 7-day Undo reset) and the rule that every app stays reachable from the drawer are kept
from Drive-modes §7.1, §7.7 and §7.8. **One recovery path always works** (*amended
2026-10-07, openness round*): whatever the user hides, a long press on the strip or an empty
area opens edit mode, the Connection sheet keeps Reset layout, and holding Back for 10 s (the
[theme engine](2026-10-07-theme-engine-design.md) §4 safe-mode trigger) offers Reset.

## 7. The widget picker and the widget setup page

### 7.1 The picker (gallery)

- A sheet (bottom on phone, passenger side on head units) with search and two tabs:
  **By app** (installed apps' widgets, grouped, with the starter pack first) and **By signal**
  (pick a VSS signal, get the widgets that suit it, from each widget's `suggest`; HA research
  Decide 8).
- Each entry shows its **preview** (rendered live from the current data if connected, else
  from the widget's recorded preview fixture), its name, a one-line description and its size
  chips. A **More widgets in the Store** row ends the list.
- **Tap** places the widget in the first free spot at its default size; **drag** places it
  where dropped. If the widget's setup is required, the setup page opens at once.

### 7.2 The widget setup page

The Android widget configure screen, drawn by the OS from the widget's `settings` schema:

| Section | What the user picks |
|---|---|
| **Data** | each binding: a VSS signal from the picker (grouped by system, "Available on this car" by default, confidence word shown) or an app's data feed |
| **Look** | style (for a gauge: analogue arc, digital, bar), gauge options, label and icon |
| **Range and levels** | range, normal, warning and critical bands, defaulting from the signal |
| **Units** | follow Preferences or fixed; decimals |
| **Size** | the allowed sizes |

- A **live preview** shows the widget at its size in two panes, **Parked** and **Moving**
  (exactly what the template renderer draws), with any rule it breaks in words.
- **Done** validates against the schema; errors sit under their fields. **Cancel** removes a
  just-placed widget. Long press → **Settings** reopens the page later.
- The page is text entry, so on a driver-facing display it is Parked only.

### 7.3 A custom setup page

A widget may name its own **setup view** (`setup.view`). The OS opens it in the setup sheet,
Parked only, in the widget's error boundary (an iframe for community widgets on web hosts).
It returns a config through `widgets.completeSetup(config)`; the OS validates it against the
schema before saving. The OS still draws the Moving preview and the Size section.

## 8. The widget SDK contract

### 8.1 Manifest entry

It extends app-model §15.1 (all its fields and rules stand unless changed here).

```jsonc
"contributes": { "widgets": [ {
  "id": "gauge.analogue",                       // full id "ostler.starter/gauge.analogue"
  "title": "Analogue gauge", "icon": "speed",
  "description": "One signal on a calm arc",    // ≤ 60 characters recommended; longer is ellipsised
  "category": "gauges",                          // gauges | vehicle | media | navigation | people | time | tools | other
  "preview": { "fixture": "previews/gauge.json" },   // a recorded or labelled synthetic fixture the OS renders in the picker
  "surfaces": ["home"],                          // pages; "home" covers every page
  "sizes": { "min": [1, 1], "max": [3, 3], "default": [2, 2], "resize": "both" },   // cells; none | horizontal | vertical | both
  "bindings": { "value": { "kind": "signal", "datatype": "number",
                           "suggest": ["Vehicle.Speed", "Vehicle.Powertrain.*"] } },
  "settings": { "type": "object", "properties": { "style": { "enum": ["arc240", "arc270"] } } },
  "default_config": { "style": "arc240" },
  "setup": { "required": true, "view": null },   // view: a Parked views[] id for a custom setup page
  "data": [], "signals": [],                     // ⊆ the app's permissions; filled from bindings at place time
  "refresh_hz": 4,
  "moving": { "template": "tiles" },             // REQUIRED: false or one template
  "passenger_view": false,
  "docs": "docs/widgets/gauge.md" } ] }
```

### 8.2 Field rules

- **`moving` is required** and has no default. It is `false` (Parked only; the validator keeps
  the widget out of every Moving section) or names one template: `tiles`, `value`,
  `telltale_list`, `map`, `media`, `call`, `short_list`, `setpoint` or `arm`. `camera_live`
  is the system's (the reverse view) and is not offered to widgets.
- **Bindings** are what the user connects on the setup page. Kinds: `signal` (a VSS path,
  filtered by `datatype`, unit class or path patterns, with `suggest` for the By signal tab),
  `feed` (data the app publishes through `widgets.publish`), `system` (clock, own location,
  driving state; read-only). A widget receives only its bound values, each with confidence and
  staleness, filtered by the data-class registry.
- **Sizes** are cells in the Parked grid. The Moving size comes from the template and the
  class's Moving grid, never from the widget.
- **`settings`** keeps app-model §15.2's JSON Schema subset and adds `x-ostler-gauge-style`
  and `x-ostler-levels` (the band editor), both drawn by the OS.
- **`preview.fixture`** is a recorded fixture or an author-supplied synthetic one; a synthetic
  preview carries `"synthetic": true` and the picker labels it "Sample data" (*amended
  2026-10-07, openness round*; ADR-0045 §6 as amended).
- Widgets carry **no car actions**; template buttons route through the OS; anything that
  reaches the gate goes through `actions.request` in a Parked view.

### 8.3 Who can make a widget

| Kind | What it is | Where it runs |
|---|---|---|
| **Declarative** | data only: an OS view (tile, gauge, bar, text) over bindings, with settings | every host, the phone included; the Store can install it there |
| **Bundled** | the app's own Parked view, in the OS realm, in an error boundary | as the app (app-model §5) |
| **Iframe** | community code, sandboxed, Parked only, Moving through `widgets.publish` | web hosts only (app-model §15.6) |

Anyone can publish a declarative widget pack in the Store. Code widgets follow their app's
review level (Store spec).

## 9. The starter catalogue

The starter pack (`ostler.starter`, repo `ostler-widgets-starter`, ADR-0046) holds these 24 widgets.
Every one has its Moving template fixed below; options are set on the setup page.

| Widget | Sizes (cells) | Data | Options | Moving |
|---|---|---|---|---|
| **Analogue gauge** | 1×1–3×3 | one signal | 240° or 270° arc, needle or fill, ticks, range, bands, unit, decimals, label, icon | `tiles` (static arc, stepped, ≤ 4 Hz) |
| **Digital gauge** | 1×1–3×2 | one signal | type step, label, unit, decimals, bands (colour and word), min/max memory (Parked) | `tiles` |
| **Bar gauge** | 1×1–4×1, 1×2–1×4 | one signal | horizontal or vertical, range, bands, segmented or solid | `tiles` |
| **Graph** | 2×1–6×3 | 1–3 signals | window 30 s–24 h from the recorder, y range auto or fixed, line or area, Mark flags | `value` (latest value of the first signal) |
| **Multi-value** | 2×1–4×3 | 2–6 signals | list or grid, label, unit, decimals and bands per row | `tiles` (each value is a tile) |
| **Warning lights** | 2×1–6×2 | the pack's telltales and active faults | systems shown, active only or all, compact or named | `telltale_list` |
| **Map** | 2×2–full page | own position, trip trace, layers from apps | north up, heading up or free; zoom; trail none, trip or 1 h; layers | `map` (pane) |
| **Compass and incline** | 1×1–2×2 | heading (GPS or IMU), roll and pitch (IMU) | compass, incline or both; warning angles; pack silhouette | `tiles` (inclinometer) |
| **G-meter** | 1×1–2×2 | IMU longitudinal and lateral | scale 0.5, 1 or 1.5 g; peak hold and trail (Parked) | `tiles` (two numbers; no dot plot) |
| **Ride height** | 2×1–3×2 | the pack's ride-height signals | corners shown, units, target band, mode word | `tiles` (≤ 4 values) |
| **Clock** | 1×1–4×2 | system time | digital or analogue, 12 or 24 h, date, seconds (Parked), second zone | `value` |
| **Weather** | 1×1–4×2 | the Weather app's feed | place (current, home, chosen), units, forecast (Parked) | `value` (temperature and one word) |
| **Media** | 2×1–4×2 | the active audio source (Media, Radio) | follow active or fixed source, artwork, controls | `media` (pane) |
| **Radio** | 1×1–4×2 | the Radio app | band, preset row (≤ 6), RDS or DLS text and slideshow (Parked) | `media` (pane); presets as `short_list` |
| **Phone favourites** | 1×1–4×2 | the Phone app | up to 6 contacts, order, photos (Parked) | `short_list` (names only) |
| **Next turn** | 2×1–3×2 | the Navigation app | units, lane hint, ETA | `map` (manoeuvre only; counts as the map pane) |
| **Trip computer** | 1×1–4×2 | the recorder | trip (current, A, B, today), up to 4 figures, reset (Parked, not a car action) | `tiles` |
| **Fuel** | 1×1–2×2 | fuel level, range, economy (pack or estimated) | figures, low-fuel level, units | `tiles` |
| **Service due** | 1×1–3×1 | the Maintenance app | next reminder or all, distance or time | `value` |
| **Alarm status** | 1×1–2×2 | the Security app | arm button, last event (Parked) | `arm` (arm only, never disarm) |
| **Camera** | 2×2–full | the Camera app | camera, grid overlay | `false` (Parked only; the reverse view is the system's) |
| **App shortcut** | 1×1 | any app or app shortcut | target, label, icon | one tile; only if the target has a Moving view |
| **Text** | 1×1–6×2 | user text | text (default ≤ 120 characters, the user may raise it), type step, alignment | `false` |
| **Image** | 1×1–full page | a local image | file (EXIF stripped; default ≤ 2 MB, the user may raise it), fit or fill | `false` |

**System widgets** (in the OS, not the starter pack): **Warnings** and **Security alert**
(safety widgets, §12), **Vehicle** (state and health card) and **Get apps** (the empty-state
card, dismissible, never while Moving). A widget whose app is not installed shows "Needs
*app*" with a Store link, never a broken view.

## 10. Preset dashboards and the dashboard builder

### 10.1 Presets

Preset dashboards are data (`ostler.layout/2` pages) in the starter pack: the seven of
Drive-modes §5 (Diagnostic, Dashboard, Map, Convoy / Ride, Off-road, Split / Media, Minimal /
Night, one page per former face) plus **Everyday** (vehicle, warnings, trip, clock, media),
**Head unit** (media, radio, map, phone favourites), **Security only** (alarm, map, 12 V) and
**Developer** (signals, coverage, session). Apps add presets as data
(`contributes.dashboards`, validated like an import; never code).

### 10.2 The wizard

1. **This screen** (first run only, pre-filled): head unit, phone or tablet; driver's side.
2. **While driving, show me**: up to six chips (Speed and revs, Map and directions, Music and
   radio, Calls, Off-road, Engine health, Ride with friends, Keep it minimal). A chip whose app
   is missing says "Gets the *app* app" and installs it from the bundled catalogue.
3. **Home page**: Everyday, Head unit, Security only or Developer.
4. **Look**: Night, Day or Auto, and an accent (the theme wizard has the rest).
5. **Preview**: the new pages in a carousel, Parked and Moving side by side.
6. **Apply**: **Add these pages** (default) or **Replace my pages** (a 7-day Before snapshot).

### 10.3 When it runs

At first run, automatically, as the last step of setup. At any time from Settings → Home
screen → **Dashboard builder** and from the edit bar. After an app with widgets is installed,
one dismissible card offers "Add *app* to your home screen?" (never while Moving). It never
changes pages silently. The generator is a pure function that writes `ostler.layout/2` and
records `{generator, version}` in `base` (HA research §4.4).

## 11. The theme wizard

> **Amended 2026-10-07, approved by the owner:** themes follow
> [visual spec §13](2026-10-07-visual-design-system-design.md). Theme packs may carry any
> custom CSS against the documented hooks, images and fonts. Nothing is locked, and a theme
> looks the same while Moving. The rules below about "tokens only, no user CSS", fixed status
> colours, and glow and wallpaper while Moving are superseded for theme packs. The
> content rules of the Moving templates still apply.
>
> **Amended 2026-10-07 (openness round):** the rules paragraph at the end of this section is
> rewritten to point to [visual §13](2026-10-07-visual-design-system-design.md) §13.9 and the
> [theme engine](2026-10-07-theme-engine-design.md) instead of restating theme rules.

1. **Mode:** Night, Day, Auto (sun or headlights on head units); Night dim and Deep night
   (visual spec §3).
2. **Background:** a wallpaper from a wallpaper pack, the user's own photo (chosen Parked,
   stored on the device, EXIF stripped), a solid surface colour, or none; a dim level for
   night.
3. **Accent:** one of a set of accents that pass contrast in every theme (visual spec §3.2).
4. **Icons:** an icon pack (Material Symbols outlined by default; rounded, sharp, a pack
   that maps the catalogue names, emoji or SVG). Telltale and safety icons may be restyled,
   guarded by the Drive-mode render check.
5. **Gauges:** default gauge style (240° arc, 270° arc, bar, digital), needle or fill, tick
   density.
6. **Preview and apply**, with Undo.

Rules: what a theme may change and the guards that stay (the Drive-mode render check,
protected surfaces, required parts, safety items that move but never go) are in
[visual §13](2026-10-07-visual-design-system-design.md) and the
[theme engine spec](2026-10-07-theme-engine-design.md) §11; they are not restated here. The
wallpaper shows while Moving as the theme draws it (Decision 7 is superseded). Theme,
wallpaper and icon packs are data objects (app UI model §5).

## 12. Safety mapping

| Owner's line or hard rule | How the launcher keeps it |
|---|---|
| Swiping pages while Moving is allowed | the driving set only; long swipe, D-pad or page chip; 76 px targets; dots are not targets |
| …with Moving templates | each driving page shows only its Moving section, validated strictly (Drive-modes §4.3) |
| Editing is Parked only | R1 kept: the server refuses layout writes for a Moving display; "Park to edit" |
| Safety widgets can't be removed | Warnings and Security alert: move, resize and restyle, never remove or cover; the worst-telltale chip, the Security chip and `alert_card` stay system-drawn |
| More (the drawer) is always reachable | Apps is a dock anchor by default; if hidden, the recovery path of §6.6 opens it; while Moving it opens a `short_list` of driving apps |
| Nothing changes under the driver | no auto-advance; edits made elsewhere apply at the next Parked (R7); installed apps add nothing while Moving |
| No dead targets | dock items with no Moving view are not drawn while Moving; their slots stay empty |
| Layouts never act on the car | no actions in layouts; template buttons only (R6) |

## 13. The format, `ostler.layout/2`, and migration

### 13.1 Shape

Kinds `home` (all pages of a class), `dock`, `strip` and `drawer`. Item overrides (`icon`,
`label`, `hidden`) and the text and icon rules of Drive-modes §4.5 and §7.6 stand.

```jsonc
{ "format": "ostler.layout/2", "kind": "home", "id": "user.home", "name": "My home",
  "base": { "preset": "ostler.everyday", "version": 1, "generator": "ostler.builder", "generator_version": 1 },
  "classes": { "hu7": {
    "default_page": "p1",
    "driving": ["p2", "p1"],                      // the driving set, in order (default ≤ 6)
    "pages": [
      { "id": "p1", "name": "Home", "grid": { "cols": 6, "rows": 4 },
        "items": [
          { "id": "w1", "type": "widget", "widget": "ostler.starter/gauge.analogue",
            "at": [0, 0], "span": [2, 2], "bind": { "value": "Vehicle.Speed" },
            "config": { "style": "arc240", "range": [0, 160] } },
          { "id": "w2", "type": "widget", "widget": "system/warnings", "at": [2, 0], "span": [2, 2] },
          { "id": "s1", "type": "shortcut", "app": "ostler.radio", "shortcut": "presets", "at": [4, 3] },
          { "id": "f1", "type": "folder", "name": "Tools", "items": ["app:ostler.trips", "app:ostler.diagnostics"], "at": [5, 3] } ],
        "moving": { "show": ["w1", "w2"], "grid": { "cols": 3, "rows": 2 },
                    "place": { "w1": [0, 0, 2, 2], "w2": [2, 0, 1, 2] } } } ] } } }
```

### 13.2 Migration from `ostler.layout/1`

| v1 | v2 |
|---|---|
| `kind: drive_mode`, each face | one page per face, named "*mode* · *face*", Moving section kept |
| the rotation | the driving set, same order |
| `kind: home` | the default page, widgets kept; the Drive button widget dropped |
| `kind: rail` | `kind: dock`: `destination:home` → Home anchor; `destination:more` → Apps anchor; `destination:diagnose`, `trips`, `security` → the matching app icons; `more:*` pins → app icons; the Drive button dropped |
| `kind: strip` | unchanged, with `drive_mode` → `page` |
| core widget ids (`ostler.gauge`, `ostler.hero`, `ostler.map` …) | starter or system widget ids by a fixed table |

- The server migrates each stored layout once, keeps the v1 copy as the Before snapshot for
  30 days, and logs the migration once.
- Import of a v1 file is accepted forever and converted on import; export writes v2.
- The DM1 code (`src/openostler/layouts.py`, `ui/src/drive/`) gains the v2 shape; the
  validator's Moving rules are shared unchanged.

## 14. Phases

| Phase | Ships | Needs |
|---|---|---|
| **LW0** | UX briefs (§0), owner approval | ADR-0045 |
| **LW1** | On recorded fixtures: pages and the carousel, Moving sections, the page chip, the dock with anchors, the drawer (incl. Moving list), edit mode (drag with reflow, resize, pages overview), `ostler.layout/2` schema and validator, v1 migration | LW0 |
| **LW2** | The widget host, picker and setup page; the widget contract (app UI model UA2); starter set A (gauges, graph, multi-value, warning lights, clock, trip computer, fuel, compass and incline, G-meter, shortcut, text, image) | LW1 |
| **LW3** | Shortcuts and folders; presets and the dashboard builder; the theme wizard and theme packs | LW2 |
| **LW4** | Wiring: server storage and R1 for v2, stored-layout migration; starter set B as each app lands (map, ride height, weather, media, radio, phone favourites, next turn, service due, alarm, camera) | the apps |
| **LW5** | Widget packs from the Store; iframe community widgets on web hosts | Store, the iframe ADR |

## 15. Tests

- **Unit** (Vitest and pytest, shared fixtures): the v2 schema; every v1 fixture migrates and
  validates; the driving set holds only valid pages (≤ the user's limit, default 6); a write leaving no driving page is
  refused; a safety widget cannot be removed or hidden; a `moving`-less widget manifest is
  refused; a shortcut to a target with no Moving view is refused in a Moving section; folders
  are refused in Moving sections; reflow never produces overlap; the builder is deterministic
  (same input, same file).
- **Server:** layout writes refused while the display is Moving; held writes apply at Parked;
  migration keeps the Before snapshot.
- **Playwright** at 800×480, 1024×600, 1280×720, 1280×480, 1920×720 and 393×852, on recorded
  fixtures: the carousel swipes and D-pad moves pages Parked; with the Moving fixture only the
  driving set shows, each page's Moving section does not scroll, ≤ 6 tiles render, digits
  ≥ 56 px, nothing animates beyond the alarm pulse; a short swipe does not change page; the page chip
  cycles and lists; dock items with no Moving view vanish while their slots hold; Apps opens
  a ≤ 6-row list while Moving; long press shows "Park to edit"; uninstalling every app leaves
  the Warnings widget, the strip and the Essentials page working; the setup page's Moving
  preview matches the live Moving render pixel for pixel.

## 16. Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", OS round; decision list items
14–21 and 44–53). Each recommendation below is the decision; each alternative was not chosen.

1. **Pages replace Home plus Drive modes?** Recommend: yes, one set of pages; Drive mode is
   their Moving view. Alternative: keep Home and Drive modes as two sets.
2. **Driving set size?** Recommend: ≤ 6 pages. Alternative: no limit.
3. **Switch pages while Moving by swipe?** Recommend: yes, a long swipe, plus D-pad and the
   page chip. Alternative: page chip and D-pad only.
4. **Dock anchors Home and Apps?** Recommend: both. Alternative: Apps only, Home by the page
   chip.
5. **Dock size per class?** Recommend: 5, 5, 6, 7 and 7 (§5.1). Alternative: 5 everywhere.
6. **Drop on occupied cells?** Recommend: reflow as on Android, swap when there is no room.
   Alternative: swap only (Drive-modes' rule).
7. **Wallpaper while Moving?** Recommend: plain `bg` behind Moving sections on driver-facing
   displays. Alternative: the wallpaper dimmed to 20 %.
8. **Required `moving` field?** Recommend: required and explicit. Alternative: default
   `false`.
9. **Builder default action?** Recommend: add pages. Alternative: replace with Undo.
10. **Drive button?** Recommend: retired. Alternative: keep it as an optional dock item.

## Changelog

- 2026-10-07: v0.1, first draft from the owner's direction of 2026-10-07 (Android launcher
  model), for ADR-0046.
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all", OS round; decision
  list items 14–21 and 44–53): every decision answered as recommended (alternatives not chosen).
- 2026-10-07: v0.3, amended (approved by the owner on 2026-10-07): §11 defers to visual
  spec §13. Themes may use custom CSS and change anything, and look the same while Moving.
- 2026-10-07: v0.4, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", [ADR-0047](../decisions/adr-0047-openness-round.md)): caps become defaults
  (pages, driving set, swipe distance, dynamic shortcuts, folders, names, descriptions, text
  and image widgets, dock slots with overflow); widgets allowed in the dock; anchors hideable
  with one recovery path (§6.6); free-form placement and user CSS no longer non-goals;
  synthetic widget previews allowed, labelled; §11's rules point to visual §13 and the theme
  engine; safety looks restylable under the render check; the wallpaper shows while Moving.
  The decision list stays as history.
- 2026-10-08: v0.5, parked (direction round, approved by the owner on 2026-10-08, ADR-0049).
