---
title: "Designer brief: Store (part A): rules, item kinds, Store home, categories and search"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, references/research/ha_architecture_addons.md, references/research/ha_integrations_dashboards.md, references/research/ha_companion_community.md]
summary: >
  Part A of the Store brief. The Store is a system app of the Ostler OS, modelled on a phone
  app store but adapted to a car and to Ostler's open values: it hosts apps, integrations
  (vehicle packs, data sources, bridges), widget packs, themes, icon packs, wallpapers,
  dashboard presets, gauge styles and sound and EQ presets. This part gives the shared rules
  (Parked-only browsing on head units, no installs while Moving, owner-only installs on local
  links, what the native phone app may install, the bundled catalogue, no ratings), the item kinds table, the main install flow as a step list, and the blocks for the
  Store home, a category page and search with filters (vehicle, kind, works offline, open source).
---

# Store brief, part A: rules, item kinds, home, categories, search

Parts: **A** (this file) · [B: item detail and install](70-store-b-item-install.md) ·
[C: updates and My library](70-store-c-updates-library.md) ·
[D: publisher, report, offline, sideload, open questions](70-store-d-publisher-sideload.md).
Process and the constraints checklist: [design hand-off README][readme].

## 1. What the Store is

- **A system app.** The Store is part of the OS, like Settings: always in the app drawer,
  never hidden, never removed, in every flavour. Owner: **os** (the Store *client*; the
  online catalogue behind it is a service, see part D).
- **Like a phone app store, with three differences.** It knows your car (it offers what fits
  the installed vehicle pack), it is honest about data (every item says, in plain words,
  which data classes it reads and where it runs), and it works with no internet (a catalogue
  is bundled with the OS, and items can be installed from a file).
- **What exists today.** The approved catalogue is More → Add-ons with tabs Installed and
  Available, listing bundled add-ons and add-ons a device suggests, with no remote catalogue
  ([app model §14.2][am-14], [ADR-0042 §5][adr-42]). That screen, `addons-catalogue`, becomes
  **My library** (part C). The **online catalogue** is opt-in and off by default, with one
  switch at first run, and comes only after its own ADR (decided, item 32;
  [app model §11 Q7][am-11]). The Store is a system app: never uninstalled, Parked only on
  driver-facing displays (decided, item 28; [Store §3][st-3]).

## 2. Item kinds

| Kind (label on cards) | What it is | Code? | Where it runs | Examples from the specs | Setup |
|---|---|---|---|---|---|
| **App** | a feature app with pages, widgets, settings | yes | Brain-served UI; phone only if bundled or declarative | Diagnostics, Trips, Security, Maintenance & Garage, Social, Navigation, Phone & Comms, Cameras | its own setup flow (`90-appframe-*`) |
| **Integration** | connects Ostler to a car or a service; backend only, setup page only | data, or a service | node and Brain (pack data); Brain (bridges) | Ostler pack for Land Rover Discovery 2, Generic OBD-II, RealDash CAN out, LubeLogger bridge, MQTT out | one setup page |
| **Widget pack** | widgets for the picker | declarative, or sandboxed | where the widget is placed | Starter widgets | none, or per-widget setup |
| **Theme** | a token set (colours for Night, Night dim, Deep night, Day) | no | every display | Default theme | the theme wizard (`45-launcher-*`) |
| **Icon pack** | a glyph set mapped to Material Symbols names (item 49) | no | every display | (none in the specs yet) | the theme wizard |
| **Wallpaper** | still images for home pages | no | every display | (none in the specs yet) | the theme wizard |
| **Dashboard** | a preset home page as layout data | no | every display | Diagnostic, Dashboard, Map, Convoy / Ride, Off-road (D2), Split / Media, Minimal / Night | the dashboard builder wizard |
| **Gauge style** | how gauge widgets draw | no | every display | (styles of the one gauge spec) | the theme wizard |
| **Sound and EQ** | presets for the Audio app | no | Brain | (none in the specs yet) | the Audio app (`80-hu-*`) |

- **Runs on the Brain.** Items that run a container service on the Brain (HA's "apps") wear
  a "Runs on the Brain" label, for example Navigation's routing service
  ([HA research §8, Decide 1][ha-arch-8]).
- **Developer** label: items shown only in service mode, such as Decode lab
  ([app model §14.1][am-14]).
- Never shown: an item the registry finds incompatible (shell range, `requires`, host),
  except in search with "Show items that don't fit" ([ADR-0042 Confirmation][adr-42]).

## 3. Rules every Store screen follows

1. **Moving.** On a driver-facing head unit the Store is **Parked only**: while Moving it
   shows the locked view, "Available when parked", with **Open on phone**
   ([UI §12.1][ui-12.1], [§12.4][ui-12.4]). It has no Passenger view (store content is not
   vehicle state). On a phone the Store stays usable with the Moving banner.
2. **Installs never happen while Moving.** Not started, not finished, not updated. An
   install asked for on a phone while the car moves reads **Install when parked** and waits
   in a queue shown on the Store home. A running install pauses if the car starts moving and
   resumes when Parked.
3. **Owner only, local links only.** Installing, updating, rolling back and removing are
   owner operations on a local link ([UI §12.4][ui-12.4], [§7.2][ui-7.2]). Other users can
   browse and press **Ask the owner**; remote paths (Ostler Link) can browse only.
4. **The native phone app** installs only bundled or declarative items; it never fetches
   code ([app model §7.1][am-7.1], [ADR-0042 §3][adr-42]). On the phone, an app with code
   installs on the Brain and is served from there; its card says "Installs on your Brain".
5. **Nothing passes the gate.** An item's actions are only requests that the node's gate
   still decides ([ADR-0033][adr-33]); the Store never shows an item as able to "control"
   the car, only "may ask to" with the action's category.
6. **Safety stays with the OS.** No item can remove the fault telltale, alarm alerts, the
   Moving templates or Park to edit ([Drive modes §8.1][dm-8.1]). Themes must pass the
   contrast checks and have no glow on head units at night ([visual §3][vds-3]); wallpapers
   are still images only (no video or animation on driver-facing displays); icon packs map
   to Material Symbols names and never change safety icons (item 49; [visual §6][vds-6]).
7. **Honest data.** Every item lists its data classes in words from the registry
   ([Accounts §14.1][acc-14.1]); a new class it adds starts "only me" and in ghost.
8. **No votes.** No star ratings, reviews or download leaderboards (decided, items 33 and
   62; [Store §11][st-11]); the Community hub has a no-votes rule ([hub §1][hub-1]). Items
   show facts instead: review level, badges, publisher, verified key, vehicles tested, last
   update, known issues, the issue tracker, open source.
9. **Updates never on a metered link over quota** and never while Moving
   ([ADR-0028][adr-28], [HA research §8][ha-arch-8]).
10. **Exit guarantee.** Everything works with the bundled catalogue and from files; nothing
    in the OS depends on an Ostler-run server ([ADR-0042 §7][adr-42]).

## 4. The main flow: find, install, set up

| # | Screen | The user | What can fail → recovery |
|---|---|---|---|
| 1 | `store-home` | opens the Store from the app drawer or Settings → Apps → **Get more apps** | offline → the bundled catalogue, banner "Offline · showing items on this Brain" |
| 2 | `store-category` or `store-search` | browses a kind or searches | no results → "No items match. Clear filters" |
| 3 | `store-item` | reads the detail, presses **Install** | doesn't fit → button disabled with the reason ("Needs a camera") |
| 4 | `store-install-sheet` | reviews access and where it runs, presses **Install** | not owner → **Ask the owner**; Moving → locked view |
| 5 | `store-installing` | waits; sees progress | download or check fails → **Retry**; car moves → paused |
| 6 | `store-installing` (done) | presses **Set up now** | the app's own setup flow (`90-appframe-*`); **Later** leaves a "Finish setup" row in My library |

### store-home — Store home  [New]
- **Owner:** os
- **Purpose:** the landing page of the Store: featured items, what fits your car, what is
  new and updated, and every kind.
- **Opens from → goes to:** the app drawer (Store icon `storefront`); Settings → Apps →
  **Get more apps**; the empty-Home suggestion card; the widget picker's **Get more
  widgets**; the theme and dashboard wizards' **More in the Store**. Goes to
  `store-category`, `store-search`, `store-item`, `store-updates`, `addons-catalogue`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day and Night, hu7 Night, hu7 Night dim Moving (the locked view), desktop Night.
- **Content (top to bottom):**
  1. Top bar: title "Store", search field "Search apps, packs and themes" (→ `store-search`;
     a button on head units, since typing is Parked only), **My library** icon button
     (`apps`), **Updates** icon button with a count badge (`update`, "3").
  2. **Queue** card (only when something waits): "1 install waits until you park ·
     Maintenance & Garage" with **Cancel**.
  3. **Picks** (curated by the project, each with a written reason): one wide Card per item, swipeable (phone) or two side by side (tablet,
     hu9, huwide): image from the item's screenshots, name, one line, kind Chip. Example:
     "Maintenance & Garage · Service reminders, fuel and costs · App".
  4. **For your car** (header shows the active vehicle: "For your Discovery 2 Td5"): items
     that declare support for the installed pack, for example "Off-road (D2) · Dashboard ·
     SLABS ride heights, pitch and roll", "Ostler pack for Land Rover Discovery 2 · Update
     available". With no vehicle: a Card "Add a car to see what fits" → `setup-vehicle-add`.
  5. **New and updated**: a horizontal row of StoreItemCards (icon, name, kind, "Updated
     ‹date›").
  6. **Browse by kind**: a grid of nine tiles with icon and word: Apps (`apps`),
     Integrations (`hub`), Widgets (`widgets`), Themes (`palette`), Icon packs
     (`interests`), Wallpapers (`wallpaper`), Dashboards (`dashboard`), Gauge styles
     (`speed`), Sound and EQ (`equalizer`).
  7. Footer line: "Every item here is open source or says it isn't. Nothing here can
     control your car without the car's own checks." Link **How the Store works**.
- **States:** loading: skeleton cards. Empty: never (the bundled catalogue always has the
  first-party items). Error (catalogue unreachable): banner "Can't reach the Store · showing
  items on this Brain · Retry". Offline: the same banner wording "Offline"; rows show only
  bundled items; online-only items are absent. No vehicle: "For your car" becomes the add-a-car
  card. Parked: full. Idling: full with Park evidence, else as Moving. Moving (head unit):
  locked view, "The Store is available when parked" + **Open on phone**. Moving (phone):
  Moving banner; **Install** buttons read **Install when parked**. Passenger: not offered on
  head units. Locked (not owner): browsing works; install buttons read **Ask the owner**.
- **Safety and driving rules:** Parked only on head units; installs never while Moving
  ([UI §12.1][ui-12.1], [§12.4][ui-12.4]); no autoplay video anywhere in the Store.
- **Components:** search field, Card (featured), new component **StoreItemCard** (rows),
  Chip (kind, status), ListRow, Button.
- **Spec refs:** [UI §12.4][ui-12.4], [app model §14.2][am-14], [ADR-0042][adr-42],
  [HA integrations research §5][ha-int-5] (Discovered on top, C2) · [Store §3][st-3].
- **Open questions:** **Decided ([Store §3][st-3]):** the project curates **Picks**, each
  with a written reason; a "Set up your car" row (items that match the vehicle, its
  integrations and devices found) leads the page, as Home Assistant's Discovered row does.

### store-category — Category page  [New]
- **Owner:** os
- **Purpose:** list every item of one kind, with subgroups and sorting.
- **Opens from → goes to:** `store-home` → Browse by kind; the widget picker, theme wizard
  and dashboard wizard (`45-launcher-*`) open the matching kind. Goes to `store-item`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night (Integrations), hu7 Night (Dashboards), desktop Night (Themes).
- **Content (top to bottom):**
  1. Title (the kind, for example "Integrations"), back arrow, search icon.
  2. **Subgroup** Chips (filter chips, one selected):
     - Apps: All · Car · Drive and travel · Media and calls · Tools · Developer.
     - Integrations: All · Vehicle packs · Data sources and adapters · Bridges.
     - Widgets: All · Gauges · Maps · Media · Status.
     - Themes, Icon packs, Wallpapers, Gauge styles: All · Dark · Light · High contrast.
     - Dashboards: All · For your car · Driving · Off-road · Media.
     - Sound and EQ: All · EQ · Chimes.
  3. **Sort** Segmented: "Fits your car" (default) · "Recently updated" · "A to Z".
  4. List or grid: Apps and Integrations as ListRows (icon, name, publisher, one line,
     Chips "Installed", "Update", "Runs on the Brain", "Open source"); Themes, Wallpapers,
     Icon packs, Gauge styles and Dashboards as a grid of preview tiles (preview drawn for
     the current layout class and theme). Integration example rows: "Ostler pack for Land
     Rover Discovery 2 · openostler · Td5 engine, SLABS, BCU, airbag"; "RealDash CAN out ·
     Bridge"; "LubeLogger bridge · Bridge".
- **States:** loading: skeleton rows or tiles. Empty kind: "Nothing here yet" with
  **Install from a file** (Developer mode only). Offline: bundled items only, banner as on
  home. No vehicle: sort "Fits your car" is hidden. Moving and locked: as `store-home`.
- **Safety and driving rules:** as `store-home`. Previews of wallpapers and gauge styles are
  still images; no animated previews on head units.
- **Components:** Chip (filter), Segmented, ListRow, StoreItemCard (new), preview tile (new
  component **PreviewTile**).
- **Spec refs:** [UI §12.4][ui-12.4], [Drive modes §5][dm-5] (the seven presets),
  [HA integrations research §4.2][ha-int-42] (integrations versus add-ons) · [Store §3][st-3].
- **Open questions:** **Decided ([Store §3][st-3]):** Integrations stay one category, with
  vehicles, data sources, bridges and devices as its sub-categories; "Set up your car" on
  the Store home puts the vehicle pack first.

### store-search — Search and filters  [New]
- **Owner:** os
- **Purpose:** text search over the catalogue with filters for vehicle, kind, works offline
  and open source.
- **Opens from → goes to:** the search field on `store-home` and `store-category`. Goes to
  `store-item`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night with the keyboard, hu7 Night with the on-screen keyboard, desktop Day.
- **Content (top to bottom):**
  1. Search field (focused), placeholder "Search apps, packs and themes"; recent searches
     as Chips under it before typing ("SLABS", "boost gauge").
  2. **Filters** row of Chips, each opening a small sheet:
     - **Vehicle**: "Discovery 2 Td5" (the active vehicle, default on) · "Any vehicle" ·
       other vehicles in the garage.
     - **Kind**: the nine kinds, multi-select.
     - **Works offline** (toggle): items that need no internet once installed.
     - **Open source** (toggle): items with a source link and an open licence.
     - **More**: "Runs on the Brain", "Show items that don't fit".
  3. Results: count line "12 results", then ListRows as on `store-category`, the matched
     words in `text-1` bold. Items that don't fit (only with that filter) are dimmed with
     the reason: "Needs a camera".
- **States:** before typing: recents and "Try 'boost', 'SLABS', 'dark theme'". No results:
  "No items match. Clear filters" (Button). Offline: searches the bundled catalogue, banner
  as on home. Moving (head unit): locked view; typing is Parked only. Moving (phone): works,
  Moving banner. Locked: as `store-home`.
- **Safety and driving rules:** typing and the keyboard are Parked only on head units
  ([UI §12.1][ui-12.1]).
- **Components:** search field, Chip (filter), Sheet (filter), toggle (as Segmented "On ·
  Off"), ListRow, StoreItemCard (new).
- **Spec refs:** [UI §12.1][ui-12.1], [app model §4.2][am-4.2] (`requires`, hosts),
  [HA companion research §9][ha-comm-9] · [Store §3][st-3].
- **Open questions:** does "Works offline" come from a manifest field (new) or from the
  catalogue's own check?

<!-- refs -->
[readme]: ../README.md
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[adr-28]: ../../../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md
[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[adr-42]: ../../../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[am-11]: ../../../../specs/2026-10-06-app-model-design.md#11-open-questions-for-the-owner
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#5-the-seven-presets
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ha-arch-8]: ../../../research/ha_architecture_addons.md#8-copy--avoid--decide-for-ostler
[ha-comm-9]: ../../../research/ha_companion_community.md#9-copy--avoid--decide-for-ostler
[ha-int-42]: ../../../research/ha_integrations_dashboards.md#42-integrations-versus-add-ons
[ha-int-5]: ../../../research/ha_integrations_dashboards.md#5-copy--avoid--decide-for-ostler
[hub-1]: ../../../../specs/2026-10-07-community-hub-design.md#1-purpose-and-non-goals
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[vds-3]: ../../../../specs/2026-10-07-visual-design-system-design.md#3-colour
[vds-6]: ../../../../specs/2026-10-07-visual-design-system-design.md#6-icons-and-fonts
[st-3]: ../../../../specs/2026-10-07-store-design.md#3-the-store-app
[st-11]: ../../../../specs/2026-10-07-store-design.md#11-ratings-and-paid-items-owner-decisions
