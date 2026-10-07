---
title: "Home Assistant integrations and dashboards — the model Ostler follows, mapped onto packs, data sources, add-ons, layouts, faces and widgets"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-source-adapters-design.md, references/research/ui/app_model.md, references/research/ui/generated_ui.md, references/research/ui/obd_apps.md, references/research/ui/vehicle_data_model.md, references/research/cluster_view.md, references/research/obd_telematics_apps.md, references/research/ovms.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Live research (2026-10-07) behind the owner's "we are building the automotive version of Home Assistant" and the approved direction that dashboards follow HA's model (views, sections, cards, badges, stored as data, edited in place, a card picker fed by core and add-ons) and HA's split of integrations (packs and data sources) from add-ons (feature apps). Covers HA integrations (manifest, integration types, config flows, discovery, entities, devices, areas, the entity registry, the quality scale, the catalogue UX, custom integrations and HACS, the 2026.2 rename of add-ons to apps), HA dashboards (Lovelace to sections, the 12-column grid, tiles, badges, card picker, edit mode, YAML versus storage, strategies and "take control", custom cards, per-user defaults, wall-tablet kiosks, themes, the 2025–2026 Home dashboard) and the vehicle integrations HA already has (Tesla Fleet, OVMS, WiCAN and OBD adapters, the companion app's car sensors). Maps entities to VSS paths, devices to vehicles and systems, areas to vehicle zones, and HA's dashboard vocabulary to ostler.layout/1 (a rename-or-keep table), strategies to presets and generated defaults, custom cards to iframe-only community widgets, and lists what the Moving templates forbid. Ends with Copy / Avoid / Decide, with concrete proposals for the drive-modes spec and the app-model widget contract.
---

# Home Assistant integrations and dashboards, mapped onto Ostler

**Question (owner, 2026-10-07):** "We are building the automotive version of Home Assistant."
The owner approved the same day that Ostler's dashboards follow HA's model (views, sections,
cards and badges, stored as data, edited in place, with a card picker fed by core and add-ons) and
that Ostler keeps HA's split between **integrations** (here: vehicle packs and data sources) and
**add-ons** (feature apps). This note checks what HA actually does today and maps it, term by term,
onto the [drive-modes spec](../../specs/2026-10-07-drive-modes-and-editing-design.md) (draft v0.2),
the [app-model spec](../../specs/2026-10-06-app-model-design.md) §14–§15, the
[UI spec](../../specs/2026-10-06-ui-architecture-design.md) §12–§15 and
[ADR-0042](../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md). Earlier notes
already cover parts of HA: manifests, custom cards and HACS ([app model §2.1](ui/app_model.md)),
the entity model and strategies ([generated UI §1.1](ui/generated_ui.md)), device pages
([cluster view §2](cluster_view.md)) and diagnostics redaction
([trip and log sharing](trip_and_log_sharing.md)). This note does not repeat them; it adds what is
new and does the mapping. All web sources were checked on 2026-10-07 and are paraphrased.

## 1. HA integrations, as of October 2026

**Manifest.** Every integration has a `manifest.json`: `domain` (unique, the folder name), `name`,
`version` (required for custom integrations), `codeowners`, `dependencies` and
`after_dependencies`, `requirements` (pip), `config_flow`, `single_config_entry`,
`quality_scale`, documentation and issue-tracker URLs, and two classifiers [H1]:

- **`integration_type`**: `device` (one device, ESPHome), `hub` (a gateway to many devices, Hue),
  `service` (one online service), `entity` (a basic platform such as `sensor`), `helper`
  (computed entities: groups, derivatives), `hardware` (the board HA runs on), `system`,
  `virtual` (a brand that points at another integration or standard).
- **`iot_class`**: `local_push`, `local_polling`, `cloud_push`, `cloud_polling`,
  `assumed_state`, `calculated`. Users see it on the integration's page.
- **Discovery keys**: `bluetooth`, `zeroconf`, `ssdp`, `homekit`, `mqtt`, `dhcp`, `usb`, each a
  matcher. A match starts the integration's config flow.

**Config flows** [H2]. Setup is a UI flow of steps (`user`, plus one step per discovery source).
A discovered device must **always be confirmed by the user**; nothing auto-completes. Each entry
has a **`unique_id`** that is stable and not user-changeable (serial number or MAC address; never
an IP address, hostname or URL), which stops duplicates. **Reauth** repairs expired credentials
in place, **reconfigure** changes required setup data, and an **options flow** changes optional
settings later.

**Entities, devices, areas** [H3][H4][H5]. An integration creates **entities** on **platforms**
(`sensor`, `binary_sensor`, `switch`, `button`, `number`, `select`, `climate`, `lock`, `cover`,
`device_tracker`, `media_player`, `update` …). An entity declares `device_class`, a native unit,
`state_class`, an optional **`entity_category`** (`config` or `diagnostic`, kept off the default
dashboard), `translation_key` and `has_entity_name` (the entity name is only the data point,
"Power usage", and the UI prefixes the device name), `available`, and
**`entity_registry_enabled_default`** (fast-changing diagnostics ship disabled). Entities hang off
a **device** (identifiers, connections, manufacturer, model, versions, serial, `via_device` for
the hub it is reached through, `configuration_url`, `suggested_area`, `name_by_user`). One device
belongs to one config entry. Devices and entities sit in **areas**; areas sit on **floors**;
**labels** cut across everything; an entity inherits its device's area unless overridden.
Automations and dashboards target areas, floors and labels.

**Entity registry** [H6]. Every entity with a `unique_id` is registered, so its `entity_id` is
stable and its **user overrides** (name, and in the UI also icon, area, hidden and disabled) live
in the registry, not in the integration, and survive updates.

**Quality scale** [H7]. Bronze (UI setup, tests, basic docs), Silver (error handling, reconnects,
an active owner), Gold (discovery, firmware updates, full tests, translations, extensive docs),
Platinum (typed, async, efficient). Special labels: No score, Internal, Legacy (YAML-only) and
Custom (community code, unsupported by the project).

**Catalogue UX** [H8]. Settings → Devices & services shows **Discovered** cards at the top, then
the installed integrations; **Add integration** searches over a thousand brands; the flow ends
by assigning an **area**.

**Custom integrations and HACS** [H9]. HACS is itself a custom integration that installs
community repositories in six categories: integrations, dashboard plugins (cards), themes,
templates, python scripts and AppDaemon apps. It has a default list and user-added custom
repositories; review is light (the earlier note found no signing and no sandbox).

**Add-ons are now "apps"** [H10]. In 2026.2 HA renamed add-ons (separate programs running beside
HA on HA OS) to **apps**, because newcomers confused them with integrations and everyone knows
what an app store is. The split is unchanged: **integrations connect devices and services;
apps are software you install beside HA.** The same release launched an opt-in, anonymised
**device database** (over 10,000 devices from 260+ integrations).

## 2. HA dashboards, as of October 2026

**History.** Lovelace arrived as an experimental UI in 0.72 (June 2018) [H11]; multiple dashboards
came in 0.107 (March 2020), including admin-only and wall-tablet ones [H12]; the name Lovelace left
the UI in 2022.4 (it survives as the `lovelace:` config key) [H13]. The **sections view** shipped
as experimental in 2024.3 with drag and drop [H14][H15], **badges** were redesigned in 2024.8
[H16], and sections became the **default view** in 2024.11 (old views import into one "Imported
cards" section) [H17]. An experimental **Areas** dashboard came in 2025.4 [H18], an experimental
**Home** dashboard (summaries, favourites, areas, weather and energy) and many new **tile
features** (trend graph, media controls, bar gauge) in 2025.9 [H19]; in 2025.12 the Home
dashboard graduated, admins got a **system-wide default dashboard** with per-user override, and
the editor gained **undo/redo (75 steps)** [H20]; 2026.1 made Home the default for new users and
put summary cards first on mobile [H21]; 2026.2 made it the default for all new installs [H10].
HA now ships purpose dashboards (Home, Activity, Energy, History, Map, To-do, Lights, Security,
Climate, Maintenance) [H22].

**Model** [H22][H23][H24]. A **dashboard** holds **views** (tabs; `sections` default, `masonry`,
`panel` for one full-width card such as a map, `sidebar`). A view may be hidden per user (the URL
still works) or be a **subview** (off the tab bar, reached by navigation, with a back button), and
may have its own background and theme. A sections view holds **sections** (a heading and cards),
a configurable maximum number of sections across, optional dense placement, and a header with
title and **badges** (top or bottom). A section is a **12-column grid of 56 px rows with 8 px
gaps**; a card declares default, minimum and maximum `columns` and `rows`, ideally in multiples of
3 [H25]. The **tile card** (icon, name, state, optional **features** such as controls and graphs)
is the suggested default [H26]. **Badges** are small entity chips above the cards, with
show/hide of icon, name and state and their own conditions [H16][H27]. Every card and badge may
carry **visibility conditions**: state, numeric state, screen size, user, and/or [H23].

**Card picker and edit mode** [H15][H23]. Add card offers **By card** (types, with live previews;
tile pinned first) or **By entity** (pick entities, HA suggests cards). Editing is in place: an
edit mode, long-press to drag sections and cards, a size picker for columns and rows ("precise
mode" for finer steps), a visual editor per card with a code editor beside it, and undo/redo.

**Storage, YAML and strategies** [H22][H28]. Dashboards are stored as data either by the UI
(**storage mode**) or in YAML files (**YAML mode**); the two do not mix per dashboard. The default
dashboard is produced by a **strategy**: a frontend class whose `generate(config, hass)` returns
an ordinary dashboard or view config, so generated and hand-made dashboards share one renderer;
custom strategies load as modules. **Take control** freezes the generated output into an editable
copy, after which the dashboard **no longer updates** when new devices or features appear [H22].

**Custom cards** [H25]. A card is a web component registered as `custom:<name>` and listed in
`window.customCards` (name, description, preview, documentation link) so it appears in the
picker. It implements `setConfig`, a `hass` setter, `getCardSize` (masonry), `getGridOptions`
(sections), `getStubConfig` (the default config the picker inserts) and either `getConfigElement`
(its own editor) or `getConfigForm` (a schema HA draws). Resources load from `/local/`; there is
no sandbox: a card runs with the signed-in user's full rights.

**Per user, per device, kiosk** [H22][H29]. The default dashboard is set system-wide by an admin
and per user; HA's answer for a wall tablet that should differ is **a separate user for that
tablet**. Core has no kiosk mode: wall tablets run the companion app or **Fully Kiosk Browser**
(full screen, motion wake, with an integration that exposes brightness, screen and battery), and
the community **kiosk-mode** plugin hides the header and sidebar [H30].

**Themes** [H31]. YAML maps of CSS variables with optional light and dark `modes`, chosen per user
or per view; community **card-mod** restyles any card with raw CSS.

## 3. Vehicles in HA today

| Integration | How | What it shows | Note |
|---|---|---|---|
| **Tesla Fleet** (core) [H32] | `cloud_polling` through Tesla's Fleet API; polls every 10 min while awake, stops after 15 min idle so the car can sleep; newer cars need signed commands | sensors (charge, range, odometer), binary sensors, climate, locks, covers (windows, boot), device tracker, buttons (honk, flash), switches, numbers, selects, media, update | the car as one **device** with ~100 entities |
| **OVMS** (HACS) [H33] | the OVMS module publishes metrics to MQTT; the integration subscribes | auto-creates sensors, binary sensors, a device tracker, switches and buttons from every metric, grouped by function; commands as services | the closest in spirit: a canonical metric namespace turned into entities |
| **WiCAN** and BLE OBD adapters [H34] | ESP32 OBD/CAN adapters publish over MQTT or webhooks; community BLE integrations | PIDs as sensors (SoC, coolant, speed) | data arrives when the car is on and in range of the house |
| **Torque** (core) [H35] | the Torque app uploads to an HA URL | each PID as a sensor | covered in [telematics research](obd_telematics_apps.md) |
| **Companion app** on Android Auto / AAOS [H36][H37] | the phone or car app | an entity list and favourites, limited by the car's own list cap; settings only when parked; car sensors `car_battery`, `car_fuel`, `car_odometer`, `car_range_remaining`, `car_speed`, charging and connector | the HA app must be opened on the car screen each drive |

**What they share.** All treat the vehicle as **a device in a house**: slow polled state, location,
locks and charging, reached when parked; commands sit on the dashboard as buttons and switches with
no notion of driving state. None renders anything for the driver while moving except the
companion's projected entity list, whose limits the car platform imposes. This is the gap
Ostler fills: the same entity-and-dashboard model, but with live data at speed, a driving state,
and a gate on every effect.

## 4. Mapping HA onto Ostler

### 4.1 Entities, devices and areas

| HA | Ostler | Keep / change |
|---|---|---|
| entity (`sensor.car_speed`) | **signal**, named by a **VSS path** (`Vehicle.Speed`, ADR-0016) | Keep VSS. HA's `entity_id` is per install; a VSS path means the same thing on every car, so layouts travel (drive-modes §4.2) |
| `unique_id` | pack signal id (`td5.coolant_temp`) within a `vid` | Keep; already stable, never user-editable |
| platform (`sensor`, `binary_sensor`, `button`) | VSS node type and datatype (sensor, actuator, attribute; boolean draws a chip) | Keep; actuators are **actions** (ADR-0033), never entities a card toggles |
| `device_class`, unit | `class`, `unit` (a VSS `units.yaml` key) | Keep (UI spec §5.1) |
| `state_class` | none yet | Add only if Trips needs it (odometer and engine hours are `total_increasing`) |
| `entity_category` | `ha_category` (`primary`, `config`, `diagnostic`) | Keep (UI spec §5.1) |
| `entity_registry_enabled_default: false` | signals not subscribed unless visible | Keep, stronger: K-line bandwidth makes "visible = polled" a rule |
| unavailable / unknown | "Not available on this car", "Not in this session", stale, plus `proven` / `candidate` | Ours is richer; HA has no confidence word |
| entity registry overrides (name, icon, hidden) | per-item overrides in layouts (drive-modes §4.5) | Gap: no per-signal override (Decide 4) |
| device | **vehicle** (`vid`) and its **systems** (ECUs), plus hardware **devices** (node, cameras) | Keep both levels; a system is reached `via` the node or an adapter, as HA's `via_device` |
| config entry | a **pack bound to a vehicle through a data source** (node, adapter, replay) | Same idea; Ostler picks the best source per role (UI spec §5.4), which HA does not |
| area / floor | **vehicle zone**: VSS instances (`Row1.DriverSide`, `Front`, `Rear`) for body items; **system category** (powertrain, body, chassis) for grouping | Use system category where HA uses areas when generating; zones only inside a system page |
| label | none | Not needed in v1 |
| `iot_class` | `source_kind` (node, adapter, replay) and push versus poll | Show it on the integration page |
| discovery + "always confirm" | a device suggests an add-on (ADR-0042 §5); adapter detection (source-adapters §5) | Keep "always confirm" as a rule |

### 4.2 Integrations versus add-ons

HA's split, applied: **integrations** connect Ostler to cars and the outside world (vehicle packs,
`generic_obd2`, source adapters, the RealDash CAN stream, the LubeLogger bridge, MQTT out); **add-ons**
are feature apps in the app model (Social, Vehicles & Map, Maintenance & Garage, Cameras,
Navigation, Community, Decode lab). ADR-0042 today files the bridges as an "Integrations" add-on
family inside the Add-ons catalogue; the UI spec's More list already has a separate
**Integrations** entry (§12.4). HA's 2026.2 rename shows the cost of a muddled pair of nouns
(Decide 1–2).

### 4.3 Dashboard vocabulary and schema

| HA term | HA schema | Ostler today | Proposal |
|---|---|---|---|
| dashboard | a stored config with views | **Home** and each **Drive mode** (`kind: home`, `drive_mode`) | Keep our names; a "dashboard" in Ostler is a layout document |
| view (tab) | `views[]` | **face** (1–3 per mode, swiped; drive-modes §3) | Keep "face" in Drive (a face has a Moving section, a tab does not); Home has one view |
| subview | `subview: true` | a **page** (More → Pages) | Keep "page" |
| panel view | one full-width card | a face holding one **pane** (`map`) | Keep "pane" |
| section | heading + grid | none | **Add** to Home on phone, tablet, desktop (Decide 5); not in Drive |
| card | `type: tile` … | **widget** (core or add-on) | Keep "widget": the kit already has a `Card` component, and the owner asked for Android-style widgets |
| tile card | entity tile with features | **signal tile** (`ostler.tile`, styles number, arc, bar, chip) | Keep; tile "features" become widget `style` |
| badge | header chip per view | **strip chip** (global, shell-owned) | Keep chips; no per-view badge row (Decide 9) |
| `grid_options` columns × rows | 12 columns × 56 px rows | `size` small / medium / wide / hero over a per-class grid | Keep named sizes; HA's "multiples of 3" is the same discipline |
| visibility conditions | state, numeric, screen, user | `requires`, layout class, profile | Narrow version, Parked only (Decide 6) |
| card picker by card / by entity | `customCards`, entity suggestion | widget picker by group | **Add** "By signal" (Decide 8) |
| `getStubConfig` | picker default config | none | **Add** `default_config` to `contributes.widgets` |
| `getConfigForm` / `getConfigElement` | schema or own editor | `settings` JSON Schema subset, shell-drawn | Keep schema-only; no add-on editors |
| strategy | `generate()` → config | tier 1 generated default, tier 2 pack layout, presets | Same idea (§4.4) |
| take control | fork, stops updates | `base` reference + Update from preset | Ours is better; keep |
| storage / YAML mode | two stores | one store, files for import/export | Keep one store; add a code view (Decide 10) |
| custom card | `custom:<name>` JS | community widget, iframe only | §4.5 |
| theme | CSS variables per user or view | tokens only; Night, Dim, Day; `theme_hint: night_dim` | Keep tokens; no user CSS |
| per-user default, separate tablet user | profile setting | profile × vehicle × layout class; **Car** kiosk profile | Ours already matches HA's tablet advice |
| undo/redo 75 | editor | 50 steps (drive-modes §7.1) | Keep |

### 4.4 Strategies versus presets

HA's strategy is a pure function from the registry to the same config a person could write; this
is UI spec §5.3 tier 1 already. The difference is what happens after the user edits: HA forks
("take control") and stops following new devices; the drive-modes spec stores a full copy with a
`base` reference and an "Update from preset" view. Two HA ideas are worth taking: the generator
should **name itself and its version** in `base` (`{ "generator": "ostler.home.roles", "version":
2 }`), and HA's new Home dashboard shows that a good generated default (summaries by purpose, then
favourites, then areas) is what most users keep. For Ostler that is Home by roles, then the
user's pinned signals, then systems. Add-ons should contribute **presets as data**, never code
strategies (Decide 7).

### 4.5 Custom cards versus community widgets

HA runs custom cards in the page with the user's rights and loads them from an unauthenticated
path. App-model §15.6 already says Ostler's community widgets are **sandboxed iframes on web hosts
only, Parked only, with Moving data through `widgets.publish`**, and never in the native phone app.
HA's experience supports that: its iframe option for panels exists because shared-realm code
clashes, not only for safety. What HA gets right and Ostler should copy is the **registration
data** (`window.customCards`: name, description, preview, docs link) so the picker can list a
widget before its code runs; app-model §15.1 already has `title`, `description` and `icon`, and
needs `default_config` and a docs link.

### 4.6 What the driving templates take away

HA-style freedom stops at the Moving section of a driver-facing display. These HA features have no
Moving equivalent in Ostler, by the UI spec §12.1 templates and drive-modes §4.3 and §8.1:

- **free card sizes and counts**: ≤ 6 tiles and ≤ 2–3 panes, fixed minimum sizes per class;
- **any card type**: only `tiles`, `value`, `map`, `media`, `call`, `setpoint`, `short_list`;
  an add-on widget's own view never renders while Moving;
- **tap actions on cards** (toggle, call a service): layouts are Read only; only template
  buttons, routed through the shell and the gate;
- **conditional cards** that appear or vanish: nothing changes under the driver (R7);
- **trend graphs and animated features**: no sparkline, no animation, ≤ 4 Hz with hysteresis;
- **themes and card-mod**: tokens only, no glow in Drive mode, safety colours fixed;
- **scrolling views and masonry**: no scroll, fixed grid per class;
- **editing**: Park to edit on head units, enforced by the server (R1).

Everything else (Parked Home, Parked Drive grids, phone, tablet, desktop) may follow HA closely.

## 5. Copy / Avoid / Decide for Ostler

### Copy

| # | Pattern | From | Maps to |
|---|---|---|---|
| C1 | Integrations connect, apps add features: two nouns, two catalogue pages | HA 2026.2 [H10] | ADR-0042 §5; UI spec §12.4 More → Integrations |
| C2 | A **Discovered** row at the top of the catalogue; a discovered thing is **always confirmed** by the user | config flows [H2][H8] | ADR-0042 "device-suggested"; source-adapters §5 |
| C3 | Stable, non-user-editable ids, never an address | `unique_id` [H2][H6] | pack signal ids, node and adapter serials |
| C4 | Per-signal user overrides held in a registry, applied everywhere | entity registry [H6] | Decide 4 |
| C5 | Diagnostics and config entities off the default dashboard and **disabled by default** | `entity_category`, enabled default [H3] | `ha_category`; K-line poll budget |
| C6 | Generation is a pure function emitting the stored format, one renderer | strategies [H28] | UI spec §5.3; presets |
| C7 | **By signal** in the picker: pick a signal, get suggested widgets | card picker [H23] | drive-modes §7.2, §7.4; Decide 8 |
| C8 | A picker default config per widget | `getStubConfig` [H25] | `contributes.widgets[].default_config` |
| C9 | Settings drawn by the host from a schema | `getConfigForm` [H25] | app-model §15.2 `settings` (already) |
| C10 | Sections with headings on Home where the screen is large | sections view [H14] | Decide 5 |
| C11 | A separate profile for a fixed screen (wall tablet → head unit) | default dashboards [H29] | the Car kiosk profile (already) |
| C12 | A code view of the stored layout next to the visual editor | card editor [H23] | Decide 10 |
| C13 | A good generated Home most people never edit: purpose summaries, favourites, areas | Home dashboard [H19][H21] | UI spec §5.4 roles; pinned signals |
| C14 | `iot_class` shown on the integration page (local push versus cloud poll) | manifest [H1] | `source_kind`, push or poll, on the pack and adapter pages |

### Avoid

| # | Anti-pattern | Seen in | Our rule |
|---|---|---|---|
| A1 | Third-party UI code in the page with the user's full rights, served unauthenticated | custom cards, `/local/` [H25] | iframe only, web hosts only (app-model §5, §15.6) |
| A2 | "Take control" forks the default and stops it updating | dashboards [H22] | `base` + Update from preset (drive-modes §8.3) |
| A3 | Two stores for one thing (storage versus YAML) | Lovelace modes [H22] | one store; files only for import and export |
| A4 | Height-driven auto-placement where cards jump columns | masonry [H14] | fixed grid per class, swap on drop |
| A5 | Raw CSS restyling by users | card-mod, themes [H31] | tokens only (visual spec §9) |
| A6 | Car as a slowly polled cloud device that can stop it sleeping | Tesla Fleet [H32] | local push from the node; power states (ADR-0040) |
| A7 | Car commands as dashboard buttons with no driving state | Tesla, OVMS [H32][H33] | layouts are Read only; actions only through the gate (ADR-0033) |
| A8 | Widgets that appear and vanish on conditions while driving | visibility conditions [H23] | Moving composition fixed (R7) |
| A9 | Light-curation community stores as the default path | HACS [H9] | no remote catalogue yet (ADR-0042 §5) |
| A10 | Renaming core nouns after launch | Lovelace → dashboards, add-ons → apps [H13][H10] | settle the vocabulary now (Decide 1) |

### Decide (recommendations for the owner)

1. **User-facing vocabulary.** Recommend: follow HA's *structure* and keep Ostler's nouns where
   they carry a safety meaning: **Home** and **Drive mode** (HA's dashboards), **face** (a view
   with a Moving section), **page** (subview), **widget** (card), **signal tile** (tile card),
   **pane** (panel), **strip chip** (badge), **section** (new, Home only); keep **add-on** for
   feature apps rather than HA's 2026.2 "app", because on a phone and head unit "app" already
   means the host and Android Auto apps; adopt **integration** for packs, data sources and
   bridges. Alternative: HA's words exactly (dashboard, view, card, badge, app), easier for HA
   users, but "card" collides with the kit's `Card` and "app" with the store app.
2. **Integrations get their own catalogue page.** Recommend: More → **Integrations** lists vehicle
   packs, `generic_obd2`, source adapters and bridges (RealDash CAN out, LubeLogger, MQTT), with
   a **Discovered** row on top, each page showing source, push or poll, and signal counts; More →
   **Add-ons** keeps feature apps only. This amends ADR-0042 decision 4–5 (the "Integrations"
   add-on family moves). Alternative: keep everything in More → Add-ons with an Integration label.
3. **Maturity label for integrations.** Recommend: no medals; show counts in the existing
   vocabulary ("Engine: 24 proven, 9 candidate signals; 3 verified actions") plus Core,
   First party or Community. Alternative: an HA-style Bronze-to-Platinum scale for code quality.
4. **Signal registry overrides.** Recommend: a per vehicle × profile **signal override** (name ≤ 30,
   icon from the catalogue, hidden) applied everywhere the signal appears (tiles, picker, Trips
   charts, system pages), with widget overrides on top; layouts keep only the VSS binding.
   Alternative: overrides per widget only, as the drive-modes spec drafts.
5. **Sections on Home.** Recommend: the `home` layout gains optional `sections` (a heading ≤ 30
   characters and its widgets) on phone, tablet and desktop; head-unit Home stays one flat grid;
   Drive faces never have sections. Alternative: a flat grid on every class.
6. **Visibility conditions.** Recommend: an optional `show_when` on Home widgets and Parked Drive
   cells only, limited to vehicle in session, add-on enabled, signal level (warning or
   critical) and layout class; never in a Moving section, where composition is fixed on entering
   Moving. Alternative: no conditions in v1.
7. **Strategies, presets and add-ons.** Recommend: presets and generated defaults are generators
   in the shell that emit `ostler.layout/1` and record `{generator, version}` in `base`; add-ons
   contribute presets **as data files** (`contributes.layouts`, validated like imports), never
   code strategies. Alternative: bundled add-ons may ship generator code, as HA custom strategies.
8. **Widget picker "By signal".** Recommend: the picker has **By widget** and **By signal** tabs;
   app-model §15.1 gains `suggest` (VSS classes, units or path prefixes a widget suits),
   `default_config` and `docs`, so an add-on widget is offered for a matching signal.
   Alternative: By widget only.
9. **Badges.** Recommend: no per-view badge row; the strip is Ostler's badge row (global,
   shell-owned, safety chips inside), and small widgets do the rest on Home. Alternative: an
   optional Home header row of small status widgets, Parked and non-head-unit classes only.
10. **Code view of layouts.** Recommend: a JSON view of the current `ostler.layout/1` on tablet
    and desktop, Parked, editable through the same validator (drive-modes §8.2), for power users
    and pack authors. Alternative: file import and export only.

## Sources (all checked 2026-10-07)

- [H1] Integration manifest: <https://developers.home-assistant.io/docs/creating_integration_manifest/>
- [H2] Config flow handler: <https://developers.home-assistant.io/docs/config_entries_config_flow_handler/>
- [H3] Entity: <https://developers.home-assistant.io/docs/core/entity/>
- [H4] Device registry: <https://developers.home-assistant.io/docs/device_registry_index/>
- [H5] Organising (areas, floors, labels): <https://www.home-assistant.io/docs/organizing/>
- [H6] Entity registry: <https://developers.home-assistant.io/docs/entity_registry_index/>
- [H7] Integration quality scale: <https://developers.home-assistant.io/docs/core/integration-quality-scale/>
- [H8] Adding integrations: <https://www.home-assistant.io/getting-started/integration/>
- [H9] HACS: <https://hacs.xyz/docs/use/>
- [H10] 2026.2 release notes (apps, Home default, device database): <https://www.home-assistant.io/blog/2026/02/04/release-20262/>
- [H11] 0.72 release notes: <https://www.home-assistant.io/blog/2018/06/22/release-72/>
- [H12] 0.107 release notes: <https://www.home-assistant.io/blog/2020/03/18/release-107/>
- [H13] 2022.4 rename: <https://home-assistant-guide.com/changelog/home-assistant/core-2022-4/lovelace-is-no-more-say-hello-to-the-dashboard/>
- [H14] Dashboard chapter 1: <https://www.home-assistant.io/blog/2024/03/04/dashboard-chapter-1/>
- [H15] 2024.3 release notes: <https://home-assistant.io/blog/2024/03/06/release-20243/>
- [H16] 2024.8 release notes: <https://www.home-assistant.io/blog/2024/08/07/release-20248/>
- [H17] Sections becomes default (2024.11): <https://peyanski.com/sections-view-is-the-new-default-in-home-assistant/>
- [H18] 2025.4 release notes: <https://www.home-assistant.io/blog/2025/04/02/release-20254/>
- [H19] 2025.9 release notes: <https://www.home-assistant.io/blog/2025/09/03/release-20259/>
- [H20] 2025.12 release notes: <https://www.home-assistant.io/blog/2025/12/03/release-202512/>
- [H21] 2026.1 release notes: <https://www.home-assistant.io/blog/2026/01/07/release-20261/>
- [H22] Multiple dashboards, modes, take control: <https://www.home-assistant.io/dashboards/dashboards/>
- [H23] Cards, picker, visibility: <https://www.home-assistant.io/dashboards/cards/> · views: <https://www.home-assistant.io/dashboards/views/> · sections: <https://www.home-assistant.io/dashboards/sections/>
- [H24] Dashboards overview: <https://www.home-assistant.io/dashboards/>
- [H25] Custom card API: <https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/>
- [H26] Tile card: <https://www.home-assistant.io/dashboards/tile/>
- [H27] Badges: <https://www.home-assistant.io/dashboards/badges/>
- [H28] Custom strategies: <https://developers.home-assistant.io/docs/frontend/custom-ui/custom-strategy/>
- [H29] Default dashboard per user: <https://www.home-assistant.io/dashboards/dashboards/#set-a-default-dashboard>
- [H30] Wall tablets, Fully Kiosk, kiosk-mode: <https://evezone.evetech.co.za/deep-dives/best-wall-tablets-for-running-a-home-assistant-lovelace-dashboard> · <https://www.home-assistant.io/integrations/fully_kiosk/>
- [H31] Frontend themes: <https://www.home-assistant.io/integrations/frontend/>
- [H32] Tesla Fleet: <https://www.home-assistant.io/integrations/tesla_fleet/>
- [H33] OVMS integration: <https://docs.openvehicles.com/en/latest/userguide/homeassistant.html>
- [H34] WiCAN: <https://www.crowdsupply.com/meatpi-electronics/wican-pro> · <https://community.home-assistant.io/t/wican-esp32-based-open-source-obd2-obd-ii-vehicle-car-or-truck-can-bus-diagnostics-to-wifi-ble-usb-adapter-for-home-assistant-integration/456098/>
- [H35] Torque: <https://www.home-assistant.io/integrations/torque/>
- [H36] Companion on Android Auto: <https://companion.home-assistant.io/docs/android-auto/>
- [H37] Companion car sensors: <https://companion.home-assistant.io/docs/core/sensors/>
