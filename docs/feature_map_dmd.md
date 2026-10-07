---
title: "DMD2 and DMD Hub feature map — every feature, its Ostler home, phase and spec status"
area: docs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/dmd2_features.md, references/research/dmd2_ui_teardown.md, references/research/dmd_hub_features.md, references/research/dmd_hub_ui_teardown.md, references/research/trip_and_log_sharing.md, references/research/community_hub_architecture.md, docs/ecosystem.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  DRAFT for the owner (DMD round, 2026-10-07). One table per area mapping every DMD2 app feature and every DMD Hub feature onto Ostler: what DMD does in one line, the Ostler home (core app, approved add-on, new add-on repo, hardware add-on or not needed), the phase or dependency, and the spec status (specced, with a link to the section; needs spec; or out of scope with the reason). New homes: `ostler-app-navigation` (routing, guidance, GPX, planner, roadbook), `ostler-app-hub` with the `ostler-hub` server (Ostler Community), `ostler-app-alerts`, `ostler-app-phone`; `ShellInput`, per-trip sharing and Crash SOS stay core. Lists the deliberate leave-outs (Android-only, no CarPlay/Android Auto projection, speed cameras, gamification, social-network buttons, licence gating), a build order and Decisions for the owner.
---

# DMD2 and DMD Hub feature map

**Status: draft for the owner's approval (DMD round, 2026-10-07).** The owner asked to "pull all
the features over to Ostler", many as add-ons in separate repos, with the Hub as the social side
and per-trip sharing at chosen data levels. This page answers "where does each DMD feature go,
when, and is it specced?" in one place. The facts and sources are in the research notes; this
page does not repeat them:
[DMD2 features](../references/research/dmd2_features.md),
[DMD2 UI teardown](../references/research/dmd2_ui_teardown.md),
[DMD Hub features](../references/research/dmd_hub_features.md),
[DMD Hub UI teardown](../references/research/dmd_hub_ui_teardown.md),
[trip and log sharing](../references/research/trip_and_log_sharing.md) and
[community hub architecture](../references/research/community_hub_architecture.md).
The core/add-on map it extends is [ecosystem.md](ecosystem.md)
([ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)); the repo
rule is [ADR-0034](../decisions/adr-0034-repo-boundaries.md). All three carry a proposed
amendment from this round.

## How to read the tables

**Homes.** Core apps live in the platform repo `ostler`: **Shell** (layouts, strip, rail,
Preferences, Places, ShellInput, Settings → Sharing), **Drive** (Drive mode, part of the shell),
**Trips**, **Diagnose**, **Network**, **Security**, and **Platform** for core library pieces
(scrubber, bundle writer, verifier). **Decode lab** is the developer add-on (code in `ostler`).
Approved add-ons: **Social** (`ostler-app-social`), **V&M** (Vehicles & Map,
`ostler-app-vehicles`), **M&G** (Maintenance & Garage, `ostler-app-maintenance`), **Cameras**,
**Integrations** (one repo per integration). **New add-ons proposed in this round** (no repo
created): **Nav** (`ostler-app-navigation`), **Hub** (Ostler Community: the shell add-on
`ostler-app-hub` plus the server and web app `ostler-hub`), **Alerts** (`ostler-app-alerts`),
**Phone** (`ostler-app-phone`). **HW** is a hardware add-on from the
[catalogue](../references/research/addons_catalogue.md) that only supplies data or key events.
**—** means not needed, with the reason.

**Phases.** UI U1 shell, U2 driving state and lockouts, U5 devices, U6 garage
([UI §10](../specs/2026-10-06-ui-architecture-design.md#10-phased-migration)); UA registry and
catalogue ([app model §14](../specs/2026-10-06-app-model-design.md)); accounts P1–P5
([accounts §10](../specs/2026-10-06-accounts-sharing-design.md#10-phases)); Social S1–S4, V&M
V0–V5, M&G M0–M5 (their specs); sharing TS1–TS5
([trip sharing §15](../specs/2026-10-07-trip-sharing-design.md#15-phases)); Hub H0–H5
([community hub §13](../specs/2026-10-07-community-hub-design.md#13-phases)); Nav N0–N4
([navigation §10](../specs/2026-10-07-navigation-addon-design.md#10-phases)); ShellInput I1–I3
([ShellInput §12](../specs/2026-10-07-shell-input-design.md#12-where-it-lives-and-phases)); Drive modes DM1–DM5
([drive modes §11](../specs/2026-10-07-drive-modes-and-editing-design.md#11-phases)). **Alerts A1–A2 are
provisional labels used only here** until an alerts spec exists: A1 UK official warnings where
you are; A2 weather and warnings along a route (needs Nav N1).

**Spec status.** *Specced* links the section that covers it; "(draft)" marks a spec of this
round awaiting approval. *Needs spec* names the spec that should carry it. *Out* gives the
reason it is left out.

Short links used below: [UI](../specs/2026-10-06-ui-architecture-design.md),
[accounts](../specs/2026-10-06-accounts-sharing-design.md),
[visual](../specs/2026-10-07-visual-design-system-design.md),
[navigation](../specs/2026-10-07-navigation-addon-design.md),
[trip sharing](../specs/2026-10-07-trip-sharing-design.md),
[community hub](../specs/2026-10-07-community-hub-design.md),
[ShellInput](../specs/2026-10-07-shell-input-design.md),
[drive modes](../specs/2026-10-07-drive-modes-and-editing-design.md).

## 1. App structure and global settings (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Top status bar | Battery, GPS precision in metres, weather, online, clock | Shell strip; a conditional GPS-fix chip where speed comes from GPS | U2 | Specced: [UI §3.2](../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip); GPS chip needs a UI-spec line |
| Panel cascade | Settings open to the right, up to 3 panels | Shell layout classes | U1 | Specced: [UI §3.1](../specs/2026-10-06-ui-architecture-design.md#31-layout-classes) |
| Bottom-bar speedo slot | Speed, limit sign and alert slot in the nav bar | — in v1; Drive mode is one press away | — | Out: strip value slot declined for v1 (UI teardown Decide 4) |
| Speed colour ramp | Digits orange near the limit, red over | Nav only, off by default, never logged or scored | N2 | Specced (draft): [navigation §5.5](../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default) |
| Trip view | Tap speedo: distance, moving/stopped time, average | Trips; live trip figures as Drive tile signals | U2 | Specced: "Recording now" card [UI §12.2](../specs/2026-10-06-ui-architecture-design.md); tile signals need a Trips line |
| Quick Menu | Profile, Settings, keep background, Shutdown | Shell (More) | U1 | Specced: [UI §3.4](../specs/2026-10-06-ui-architecture-design.md#34-five-destinations) |
| Rider profiles (6) | Independent setups synced to the Hub | Shell: the vehicle in the garage plus the user's preferences | U6 | Specced: [UI §4.1](../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher); no second "profile" concept |
| Profile copy / force sync | Duplicate, compare device vs cloud | Shell Preferences export/import | later | Needs spec: Preferences export (small UI-spec item) |
| Theme incl. ambient light sensor | Light, Dark, Auto system, Auto sensor | Shell + visual tokens; light-sensor Auto with hysteresis where a sensor exists | U2 | Specced: [visual §1, §3.1](../specs/2026-10-07-visual-design-system-design.md); sensor input needs a visual-spec line |
| Map theme independent of app | Follow app, light, dark, high contrast | Shell Preferences: Map follow app / Day / Night / High contrast | U2 | Specced: the setting in [UI §13.5](../specs/2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence) (proposed); the High-contrast Day style still needs a visual §7 amendment |
| Units per quantity | Distance, speed, pressure, temperature, 12/24 h | Shell Preferences | U1 | Specced: Preferences (exists) |
| App and voice language | UI and voice language together; map labels separate | Shell (UI language); Nav (voice) | N1 | Specced (draft): [navigation §5.4](../specs/2026-10-07-navigation-addon-design.md#54-voice) |
| Background keep-alive, PiP | Per-feature keep-alive on Android | — | — | Out: the Brain serves the UI; power states own wake ([ADR-0040](../decisions/adr-0040-power-states-and-wake.md)) |
| Display scale, font, orientation lock | Size and typeface of the whole UI | Shell Preferences (scale only) | U2 | Needs spec: a scale token in the visual spec; no font picker |
| Sections on/off | Hide Home/Devices/Roadbook | Shell: an empty area disappears; add-ons never add destinations | U1 | Specced: [UI §3.4](../specs/2026-10-06-ui-architecture-design.md#34-five-destinations) |
| Notification filter | Per-app allow list | Phone | later | Needs spec: phone add-on |
| Report issue with logs | Description plus logs | Shell support bundle, scrubbed by Platform | TS1 | Needs spec: support bundle on `ostler.share/1` ([trip sharing §9](../specs/2026-10-07-trip-sharing-design.md#9-the-bundle-ostlershare1-and-the-verifier) covers the format) |
| First-run tour | Units, tour, map download, sign-in | Shell onboarding | U2 | Needs spec: onboarding (UI spec) |
| OSM credit | ODbL credit and link | Core basemap | done | Specced: [ADR-0009](../decisions/adr-0009-session-logbook-and-location.md) |
| Shutdown, no confirm | Ends nav, saves recording | — | — | Out: the Brain stays up; power states own it |

## 2. Home dashboard and widgets (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Home 1 / Home 2 | Two row layouts, one tap apart | Drive: modes, each with 1–3 **faces** switched by one press or D-pad left/right | DM1 | Specced (draft): [drive modes §5.8, §6](../specs/2026-10-07-drive-modes-and-editing-design.md#58-faces-per-preset), [ShellInput §6](../specs/2026-10-07-shell-input-design.md#6-drive-mode) |
| Draggable dividers | Snap stops between rows and map | Drive: the Split / Media preset on classes with room; fixed per class, no free dividers | DM4 | Specced (draft): [drive modes §5.6](../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media) |
| Full-screen cluster | Speed ring, trip, weather, altitude, cards self-balancing | Drive: the Dashboard preset with a hero widget | DM1 | Specced (draft): [drive modes §5.2](../specs/2026-10-07-drive-modes-and-editing-design.md#52-dashboard-realdash-style-cluster) |
| Row: App shortcuts | Android launcher grid | — | — | Out: Ostler is not a launcher |
| Row: Favourite locations | Distance tiles to saved places | Nav saved places | N2 | Specced (draft): [navigation §6.4](../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois) |
| Row: Media player | Active media session | Drive `media` template | U2 | Specced: [UI §12.1](../specs/2026-10-06-ui-architecture-design.md) templates |
| Row: Useful indicators | Weather, altitude, trip, notification count | Drive tiles (weather from Alerts) | U2 / A1 | Specced: tiles [UI §12.3](../specs/2026-10-06-ui-architecture-design.md) |
| Row: GPS dashboard | Compass, pitch/roll, altitude, accuracy | Drive tiles from GPS and IMU (`motion.py`) | U2 | Specced: tiles bound to VSS paths [UI §12.3](../specs/2026-10-06-ui-architecture-design.md) |
| Row: Trip info | Distance, total, moving, stopped | Trips live signals as Drive tiles | U2 | Needs spec: a UI §12.2 line |
| Row: Odometer, Trip A/B | Two resettable trip meters | Trips: Trip A/B over the odometer history | U2 | Needs spec: UI §12.2 amendment |
| Trip A/B rules | Reset after inactivity or on a schedule | Trips | U2 | Needs spec: with Trip A/B |
| Row: Profile switcher | Avatar strip | Shell garage switcher | U6 | Specced: [UI §4.1](../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher) |
| Row: OBD2 sensors | Three tap-to-reassign gauges | Drive tiles on VSS paths | U2 | Specced: [UI §12.3](../specs/2026-10-06-ui-architecture-design.md) |
| Row: TPMS | Pressure, temperature, battery, low alarm | HW TPMS add-on → Drive tile and `alert_card` | U5 | Needs spec: TPMS hardware add-on |
| Row: Power Box | Six aux switches | HW relay add-on, actions only through the gate | U5 | Specced: gate [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md); the device needs a spec |
| Row: Fuel level | Range from tank settings | M&G fuel + Drive tile; a real fuel signal first | M1 | Specced: [M&G §5](../specs/2026-10-07-maintenance-garage-addon-design.md#5-fuel-economy) |
| Row: Action cameras | Record start/stop, battery | Cameras | Cameras phase | Needs spec: Cameras add-on |
| Row: Last notifications | Three latest phone notifications | Phone, Parked only | later | Needs spec: phone add-on |
| Row: Weather | Conditions, high/low | Alerts | A1 | Needs spec: alerts add-on |
| Row: Speedometer with limit | Digits, limit roundel, camera countdown | Drive (speed) + Nav (limit sign, off by default) | U2 / N2 | Specced (draft): [navigation §5.5](../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default); cameras out |
| Overlays: notifications, weather, all apps | Pop over Home | Phone / Alerts / — | later | Needs spec in each; all-apps out |
| Remote cycle on Home | One button walks Home views | ShellInput: `left`/`right` switch faces | I1 | Specced (draft): [ShellInput §6](../specs/2026-10-07-shell-input-design.md#6-drive-mode) |

## 3. Map, layers and offline maps (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Offline vector maps by region | 300+ regions, update badges, SD storage | Core basemap (Brain PMTiles); routing and search parts of the region manager in Nav | N0–N1 | Specced: [visual §7](../specs/2026-10-07-visual-design-system-design.md#7-maps); (draft) [navigation §3](../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) |
| Free map limit | Three downloads free | — | — | Out: no gating of core function |
| Un-downloaded area card | Warns when you leave your maps | Nav: "Off your maps" card | N1 | Specced (draft): [navigation §3](../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) |
| Follow modes | Bearing-up, 3D, north-up, free | V&M map; Nav while guiding | V1 / N1 | Specced: [V&M §3](../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles); 3D out in v1 |
| Map scale, labels, symbols | Size multipliers | Visual tokens | U2 | Specced: [visual §7](../specs/2026-10-07-visual-design-system-design.md#7-maps) |
| Map setup per road type | "Show from" scale per class | — | — | Out: one Ostler Night/Day style, no style builder |
| Auto zoom, turn preview | Zoom and tilt by speed, flatten before turns | Nav, in steps, never animated | N1 | Specced (draft): [navigation §5.2](../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) |
| Snap to road hybrid | Dead reckoning through tunnels | Nav | N1 | Needs spec: a line in navigation §5 |
| Online layers (satellite, topo, hillshade) | Opacity per layer | Nav layers, imagery only where its licence allows | later | Needs spec: navigation spec (licence per source) |
| Weather overlays | Rain and wind, 10 min refresh | Alerts | A1 | Needs spec: alerts add-on |
| Offline caching, corridor download | Rectangle or 1–20 km along a GPX | Nav + Brain tile cache | N2 | Needs spec: a line in navigation §3 |
| Overlay cards + placement mode | Free drag per orientation, auto-arrange | Drive: overlay tiles on the map pane within the ≤ 6 budget; Map preset; Reset to default | DM1 / DM4 | Specced (draft): [drive modes §4.3, §5.3](../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping); free pixel drag out |
| Round map buttons | Follow, zoom, group, share, layers | V&M map chrome / Nav | V1 / N1 | Specced: [V&M §3](../specs/2026-10-07-vehicles-and-map-addon-design.md#3-the-map-built-into-vehicles) |
| Quick Actions panel | One-tap map actions and toggles | Shell action menu (Parked); Drive menu (Moving) | I1 | Specced (draft): [ShellInput §6](../specs/2026-10-07-shell-input-design.md#6-drive-mode) |
| Shortcut button | Rider-assigned slot | ShellInput bindings | I2 | Specced (draft): [ShellInput §8](../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test) |
| Direct lines | Crow-flies lines with live distance | Nav | N2 | Needs spec: a line in navigation §6.4 |
| Auto POI along route | Fuel etc. along route or around you | Nav | N2 | Specced (draft): [navigation §6.4](../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois) |
| My Locations pins | Photo or category pins | Nav saved places; privacy zones stay core Places | N2 / TS2 | Specced (draft): [navigation §6.4](../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois), [trip sharing §5.2](../specs/2026-10-07-trip-sharing-design.md#52-privacy-zones-saved-places-r5) |
| Community Ways | Roads ridden by ≥ 3 riders, learned anonymously | Nav layer fed by Hub aggregates, opt-in | after H4 | Needs spec: later (k-anonymity rules) |
| Location info (long-press) | What the map knows; navigate, save, share | Nav | N1 | Needs spec: a line in navigation §6.4 |

## 4. Navigation and routing (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| On-board router | Offline routing on installed maps | Nav: open engine on the Brain (Valhalla, BRouter optional; licences to verify) | N0–N1, after U2 and ShellInput | Specced (draft): [navigation §2](../specs/2026-10-07-navigation-addon-design.md#2-routing-engine-on-the-brain) |
| Routing profiles | Road fast/fun, offroad easy to hard, adventure | Nav: Fast, Scenic, Unpaved; Off-road/4x4 later | N1 / N3 | Specced (draft): [navigation §4](../specs/2026-10-07-navigation-addon-design.md#4-profiles) |
| Road options, terrain, legality | No tolls/motorways, avoid fords, legal overrides | Nav | N3 | Specced (draft): [navigation §4](../specs/2026-10-07-navigation-addon-design.md#4-profiles) |
| Community routing | Prefer Community Ways | Nav | after H4 | Needs spec: later |
| Destinations and offline search | Address, POI, coordinates, favourites, shared links | Nav | N1 | Specced (draft): [navigation §3](../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) |
| Turn card | Arrow, distance, then-preview, ETA, progress | Nav, drawn through the `map` template's next manoeuvre while Moving | N1, U2 | Specced (draft): [navigation §5.2](../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) |
| Lanes, roundabout exits, road names | On-road detail | Nav (lanes only where OSM tags them) | N2 | Specced (draft): [navigation §5.2](../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) |
| Voice prompts | TTS in 7 languages | Nav: Web Speech, then an optional Brain voice | N1 / N2 | Specced (draft): [navigation §5.4](../specs/2026-10-07-navigation-addon-design.md#54-voice) |
| Navigation options, route info | Via-points, ascent, surface split, save as GPX | Nav, Parked | N1 | Specced (draft): [navigation §5](../specs/2026-10-07-navigation-addon-design.md#5-guidance) |
| Off-route choices with countdown | Auto-confirms the highlighted reroute | Nav; countdown allowed for routing only, never for anything that reaches the gate | N1 | Specced (draft): [navigation §5.3](../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute), [ShellInput §7](../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns) |
| Route failure handling | Keeps the old route, retries | Nav | N1 | Specced (draft): [navigation §5.3](../specs/2026-10-07-navigation-addon-design.md#53-off-route-and-reroute) |
| Next / priority waypoints | Starred objectives on an amber line | Nav | N2 | Specced (draft): [navigation §6.4](../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois) |
| Drive menu navigation rows | Remote menu Navigation family | Nav rows in the ShellInput Drive menu (≤ 6 rows in total) | N1 | Specced (draft): [navigation §5.6](../specs/2026-10-07-navigation-addon-design.md#56-drive-menu-rows) |
| Share navigation with group | Leader's route becomes the group GPX; reroutes not pushed | Nav + Social ride + V&M convoy | N3, S1, V2 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports); rides [V&M §6.1](../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides) |
| Warnings on route / where you are | Forecast, fires, official warnings, reports | Alerts (free) + Nav | A1 / A2 | Needs spec: alerts add-on |
| Speed-limit sign and tint | From map data | Nav only, off by default, never logged or scored | N2 | Specced (draft): [navigation §5.5](../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default) |

## 5. GPX tracks, routes, planner and library (DMD2 and Hub)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| GPX Manager library, multiple loaded files | Folders, show/hide, order, colour, filters | Nav library; recordings stay in Trips | N2 | Specced (draft): [navigation §6.1](../specs/2026-10-07-navigation-addon-design.md#61-library) |
| Track detail and line appearance | Colour, invert, ascent, colour by surface or slope | Nav | N2 | Specced (draft): [navigation §6.1](../specs/2026-10-07-navigation-addon-design.md#61-library) |
| Track navigation, curve alerts | Turn-by-turn from a plain track | Nav: follow track (Turns / Line / Hybrid) | N2 | Specced (draft): [navigation §6.3](../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track) |
| Off-track, wrong direction | > 20 m for a few fixes | Nav (> 30 m for 3 fixes) | N2 | Specced (draft): [navigation §6.3](../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track) |
| Route repair, route points editor | Fix failures, drag stops | Nav, Parked | N2 | Specced (draft): [navigation §6.5](../specs/2026-10-07-navigation-addon-design.md#65-planner-parked) |
| Planner (device and web) | Sections, snap, draw, cut, merge, convert | Nav in the shell; a hub web planner later | N2 / after H2 | Specced (draft): [navigation §6.5](../specs/2026-10-07-navigation-addon-design.md#65-planner-parked); web planner needs spec |
| Ridden progress, verified completion ≥ 80 % | % ridden, personal best, badge | Nav computes on device; only the fact goes to the Hub, by choice | N3 / H2 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports); badge out (no gamification) |
| File details and ride tags | Description, vehicle, difficulty, off-road % | Nav curated routes; Hub publish checklist | N3 / H1 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports), [community hub §5](../specs/2026-10-07-community-hub-design.md#5-what-can-be-published) |
| Share file | Send the .gpx through any app | Trips export (exists); Nav export for plans | done / N1 | Specced: Export [UI §12.2](../specs/2026-10-06-ui-architecture-design.md); (draft) [navigation §6.2](../specs/2026-10-07-navigation-addon-design.md#62-import-and-export) |
| Import formats | GPX, KML, KMZ, GeoJSON, TCX, FIT, ITN, CSV | Nav (plans); FIT later | N1 | Specced (draft): [navigation §6.2](../specs/2026-10-07-navigation-addon-design.md#62-import-and-export) |
| Shared places | Map links, Plus Codes, MGRS, EXIF | Nav search | N1 | Specced (draft): [navigation §3](../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) |
| Open With out | Send a point to another map app | Nav | N1 | Needs spec: a line in navigation §6.2 |
| DMD GPX extension | Namespaced GPX with integrity hash | Nav reads it; writes plain GPX 1.1 | N1 | Specced (draft): [navigation §6.2](../specs/2026-10-07-navigation-addon-design.md#62-import-and-export) |
| Signature Tracks (curated, maintained) | Named maintainer, issue inbox, completions | Nav curated routes + Hub route pages and owner issue inbox | N3 / H1–H2 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports), [community hub §10](../specs/2026-10-07-community-hub-design.md#10-moderation-and-abuse) |
| Help the planner learn | Anonymous ways, k ≥ 3, ends cut | Hub aggregate, off by default | after H4 | Needs spec: later |
| Send to device | "Navigate to" on the web sets the unit's destination | Nav: the add-on's own data between the user's own devices, no car action | N1; hub button after H1 | Specced (draft): [navigation §1](../specs/2026-10-07-navigation-addon-design.md#1-scope-and-boundaries) |
| Group active GPX, map drawings | One route on every member's map | Nav ride routes + V&M convoy layer; drawings later | N3, V2 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports) |

## 6. Ride recording and statistics (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| GPX recorder with live stats | Idle/recording/paused, distance, times, climb | Trips: always-on recording, "Recording now" card | done / U2 | Specced: [UI §12.2](../specs/2026-10-06-ui-architecture-design.md), [ADR-0011](../decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md) |
| Pause | Stop points and clocks | — | — | Out: no pause (ADR-0011); End trip now and Exclude cover it |
| Under 5 km/h is not travel | No distance or climb when slow | Trips | U2 | Needs spec: a UI §12.2 line |
| Auto-record and minimum distance | Starts on movement, drops drift | Trips: trigger exists; add a minimum-distance rule | U2 | Needs spec: a UI §12.2 line |
| New track, add waypoint | Split days, quick waypoint types | Trips: End trip now, Mark | done | Specced: [ADR-0010](../decisions/adr-0010-replay-notes-audio-motion.md), [UI §12.2](../specs/2026-10-06-ui-architecture-design.md) |
| Crash recovery | Resume or ask | Trips | done | Specced: [session logbook](../specs/2026-10-05-session-logbook-design.md) |
| Recordings sync | Local/Remote states, monthly folders | Trips stays local; the Hub gets a trip only by a publish grant | TS5 / H1 | Specced (draft): [community hub §5](../specs/2026-10-07-community-hub-design.md#5-what-can-be-published) |
| Save questions | Vehicle, difficulty, off-road % | Trips free note; tags only in the Hub publish flow | H1 | Specced (draft): [community hub §5](../specs/2026-10-07-community-hub-design.md#5-what-can-be-published) |
| Trip journal and Relive replay | Map, timeline, fly-through with chat | Trips playback (exists); Hub shared trip page | done / H1 | Specced: [UI §12.2](../specs/2026-10-06-ui-architecture-design.md); (draft) [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Lean angle | Roadmap item | Trips (IMU exists) | later | Needs spec: Trips, with a motorcycle pack |
| Separate share recorder | Trip sharing apart from the GPX recorder | — | — | Out: one logbook (ADR-0009); sharing is a view of it |

## 7. Roadbook, rally and events (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Readers (PDF, GPX roadbook, OpenRally) | Show a rally roadbook | Nav roadbook view | N4 | Specced (draft): [navigation §6.6](../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4) |
| Generate roadbook | Tulips from a route or track | Nav | N4 | Specced (draft): [navigation §6.6](../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4) |
| Tulip strip, CAP, trip-meter nudge, notes | Distances, heading, cap to follow | Nav | N4 | Specced (draft): [navigation §6.6](../specs/2026-10-07-navigation-addon-design.md#66-roadbook-view-n4) |
| Waypoint validation, penalties, chrono, speed zones | Rally scoring tools | Nav, if events ask for them | after N4 | Needs spec: later (rally niche) |
| Locked maps, own remote mapping | Map hidden if rules forbid; roadbook keys | Nav + ShellInput bindings | N4 | Needs spec: navigation §6.6 line |
| DMD Events (time-locked files) | Files fetched ahead, unlocked at start | Hub events + Nav | H2 / N3 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Live Event | States, SOS to crew, board, roles, public live page | Social (board, threads) + V&M convoy + Hub live page; SOS stays core | S1, V2, H3 | Needs spec: later (Social and hub open questions) |

## 8. Devices, sensors and remotes (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Devices section | Live cards, auto-reconnect, ordering | Network device pages + Home cards | U5 | Specced: [UI §3.7](../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06), [app model §12](../specs/2026-10-06-app-model-design.md#12-the-network-app-and-device-pages-accepted-2026-10-06) |
| OBD2 dongle | ELM327 live data | Diagnose + `generic_obd2` pack | U4 | Specced: [ADR-0031](../decisions/adr-0031-generic-obd2-pack-in-platform.md) |
| CAN cable | Wired CAN feed | Core CAN links, listen-only | done | Specced: [ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md) |
| DTC read/clear, MIL button | Stored and pending codes, clear | Diagnose; clear through the gate | done | Specced: [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md) |
| OBD Scanner M1 | DMD's own dongle | — | — | Out: the Ostler node is the reader |
| TPMS sensors | BLE caps, deflation alarm | HW TPMS add-on | U5 | Needs spec: hardware add-on |
| Power Box | 6-channel switch, rules | HW relay add-on; actions gated | U5 | Needs spec: hardware add-on (the gate is specced) |
| BMW Sync Box (wheel drives the app) | CAN wheel and bike data | Vehicle packs + ShellInput (read-only button events) | I3 | Specced: [packs §3.5](../specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md); (draft) [ShellInput §3.1](../specs/2026-10-07-shell-input-design.md#31-input-events-from-packs-and-keypads) |
| Action cameras | DJI, Insta360, GoPro control | Cameras | Cameras phase | Needs spec: Cameras add-on |
| Fuel level simulator | Virtual tank by GPS distance | M&G fuel + Drive tile | M1 | Specced: [M&G §5](../specs/2026-10-07-maintenance-garage-addon-design.md#5-fuel-economy) |
| iPhone notifications (ANCS) | Mirrors calls and notifications | Phone, Parked only, no message content while Moving | later | Needs spec: phone add-on |
| DMD remotes 1–4, generic HID remote | Joystick, A/B, zoom rocker | HW "dash buttons and keypads" add-on that only supplies key events to ShellInput | I1 (HID) / I3 (keypad) | Specced (draft): [ShellInput §3](../specs/2026-10-07-shell-input-design.md#3-sources) |
| Default mapping, menu focus, dialog focus | Joystick pans, long-press to menu | ShellInput: intents, focus zones, spatial navigation, long-press to rail, confirm sheets open with Cancel focused | I1 | Specced (draft): [ShellInput §4, §7](../specs/2026-10-07-shell-input-design.md#4-focus-zones-and-spatial-navigation) |
| Remote Controller Menu (8 families) | Colour families, first tap selects | Drive menu = `short_list` ≤ 6 driver-safe actions while Moving; families Parked only | I1 | Specced (draft): [ShellInput §6](../specs/2026-10-07-shell-input-design.md#6-drive-mode) |
| Double-tap and unit buttons | Any action on a double tap | ShellInput bindings, owned by the display | I2 | Specced (draft): [ShellInput §8](../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test) |
| Test remote keys game | Ticks each key | Buttons page with a key test | I2 | Specced (draft): [ShellInput §8](../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test) |
| Touch lock | Disable touch in rain | Shell strip chip, D-pad still live | I2 | Specced (draft) as an open decision: [ShellInput](../specs/2026-10-07-shell-input-design.md) Decision 9 |

## 9. Safety, alerts, power and companions (DMD2)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Speed cameras | Database cameras with countdown | — v1 | — | Out: not in v1 (legal per country; an override puts the burden on the driver) |
| User speed thresholds | Two personal limits | Drive tile levels | U2 | Specced: [UI §12.3](../specs/2026-10-06-ui-architecture-design.md) |
| Waypoint proximity, off-track | Line alerts | Nav | N2 | Specced (draft): [navigation §6.3](../specs/2026-10-07-navigation-addon-design.md#63-follow-a-track) |
| Weather along route, fires | Forecast per stop; fire layers | Alerts | A2 | Needs spec: alerts add-on |
| Country official warnings (free) | PT, FR, ES, AU modules | Alerts: UK official weather, flood and closure alerts, free, opt-in | A1 | Needs spec: alerts add-on (feed licences to check) |
| Warnings where you are | Position check every 30 s | Alerts | A1 | Needs spec: alerts add-on |
| Alert outputs | Speedo slot, flash, voice | Shell `alert_card` | U2 | Specced: [UI §12.1](../specs/2026-10-06-ui-architecture-design.md) |
| Rider reports (hazards, closures) | One-tap reports, still there / gone | Nav layer over Social's transport, expiring; no police or camera reports | N4 | Specced (draft): [navigation §7](../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports) |
| Improve the Map (OSM edits) | One-tap tags under the rider's OSM account, review then send | Integrations (`ostler-app-osm` if split) | later | Needs spec: integration |
| Crash SOS | IMU detection, countdown, SMS to contacts | Core Security, later; the one ghost exception | after U5 | Needs spec: Crash SOS (allowed by [accounts §14.5](../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it)) |
| Theft / unplug alarm | Siren, SMS, report stolen | Core Security | U5 | Specced: [GPS tracker and alarm](../specs/2026-10-02-gps-tracker-alarm-design.md); the unplug trigger needs a line |
| Auto Off | Shutdown by dock, ignition, inactivity | Core power states | done | Specced: [ADR-0040](../decisions/adr-0040-power-states-and-wake.md) |
| Manage app, walkie-talkie | Remote setup, push-to-talk | Network + Social PTT | S1 | Specced: [Social §5](../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) |
| Phone Link (calls, messages, hotspot) | Pocket phone bridged to the unit | Phone, Parked only | later | Needs spec: phone add-on |
| Mini Launcher, eSIM, firmware OTA, own tablets | Android unit vendor features | — | — | Out: Ostler is a web UI on any screen |

## 10. Groups, live sharing and community (DMD2 app side)

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Riding groups, roles | Owner/admin/moderator, active group | Core groups + Social | P2, S1 | Specced: [accounts §14.6](../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites), [Social §3](../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) |
| Invites: email, link with expiry and limit, nearby code | Two-tap revoke | Core invites | P2 | Specced: [accounts §14.6](../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites); join limit and nearby code need a line |
| One device shares at a time | Handover prompt | Core sharing: one position source per user | P2 | Needs spec: an accounts §15 line |
| Live buddy tracking over LoRa and internet | Freshest wins, badges | V&M + LoRa HW add-on | V3 | Specced: [V&M §6.2](../specs/2026-10-07-vehicles-and-map-addon-design.md#62-routes-and-precision), [ADR-0038](../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) |
| Group tabs (members, chat, files, events, places) | One group home | Social + Hub clubs | S1 / H2 | Specced: Social; (draft) [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Help Me / I'm OK | Group beacon, not an emergency service | Social (safety exception) | S1 | Specced: [Social §6](../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) |
| Live trip link, no account to watch | Red button with watcher count | V&M §8 relay link + Hub live ride page | V5 / H3 | Specced: [V&M §8](../specs/2026-10-07-vehicles-and-map-addon-design.md#8-viewers-without-ostler-later); (draft) [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Trip privacy knobs | Trail window, delay 1–6 h, show speed, show values | Grant options `trail_window`, `delay` (0–6 h), `show_speed`, `show_values` | P2 / V5 | Specced (draft): [accounts §15.3](../specs/2026-10-06-accounts-sharing-design.md#153-live-trip-grant-options-changes-142-used-by-vehicles--map), [trip sharing §12](../specs/2026-10-07-trip-sharing-design.md#12-live-trips) |
| Listing on Live | Opt-in per trip, one-time warning, drops after 2 h | Hub "Live now", opt-in, 18+ | H3 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Viewer chat | 200-char messages from followers | — v1; members talk in the Social ride channel | — | Out v1: no viewer chat until moderation tools exist |
| Moments | Quick messages, photos, places pinned on the trip | Social ride channel + Trips Mark and notes; photos at H4 | S1 / H4 | Needs spec: a Social line; Hub photos at H4 |
| Phone adds posts to the unit's trip | Companion posting | Social | S1 | Specced: [Social §4](../specs/2026-10-07-social-addon-design.md#4-messaging) |
| Location Manager | Places with ground, vehicle, crowding | Nav (private); Hub community places | N2 / after H2 | Specced (draft): [navigation §6.4](../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois); hub places need spec |
| Discover | Community GPX, curated, places, events, live | Hub Discover | H1 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |

## 11. DMD Hub: accounts, profiles and content

| Feature | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Email + password account, all devices | No passkeys or 2FA | Core accounts (passkeys first) + a Hub account linked by device flow; a device may link several hubs | P1 / H1 | Specced: [accounts §2.2](../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always); (draft) [community hub §4](../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking) |
| Password change signs out everywhere | Sign out all devices | Core accounts | P1 | Specced: [accounts §2.3](../specs/2026-10-06-accounts-sharing-design.md#23-sessions) |
| One person, one account; age 16 | Parental consent under 18 | Hub: minimum 16; public profiles and live follow 18 | H1 | Specced (draft): [community hub §11](../specs/2026-10-07-community-hub-design.md#11-law-age-and-licences) |
| Public/private profile, rider page | Points, awards, map of places | Hub profile: garage cards, public items, counts; no map of places, no points | H2 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Deletion and GDPR export | Posts hard-deleted | Hub: export all, delete everywhere, tombstones in threads | H1 | Specced (draft): [community hub §11](../specs/2026-10-07-community-hub-design.md#11-law-age-and-licences) |
| Item visibility Private → Pending → Public | Checklist then staff review | Hub item states; `public` only by an explicit publish act | H1 | Specced (draft): [community hub §7](../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls) |
| Locked vs Download share links | Dates, limits, states, revoke | Core link controls on grants and relay links; Hub shows them | TS4 / H1 | Specced (draft): [accounts §15.4](../specs/2026-10-06-accounts-sharing-design.md#154-link-controls-changes-142-and-1412), [trip sharing §10](../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls) |
| Save to collection (live reference) | Follows the owner's edits | Hub: a Locked read that follows edits | H1 | Specced (draft): [community hub §7](../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls) |
| Community locations, favourites | Public POIs with exact coordinates | Hub places with a precision choice; V&M shows them | after H2 | Needs spec: hub places (later) |
| Services directory, ratings | Workshops, rentals, shops | M&G workshops + Hub reviews | M4 / H2 | Needs spec: an M&G "later" item |
| Feed: posts, likes, comments, bell | All / Following | Hub: an opt-in chronological Following feed in `ostler-app-hub` only; no public feed for strangers | H2 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Comments, ratings, owner replies | On tracks, places, events | Hub comments, off by default on new public items, tombstones | H2 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Points, badges, leaderboard, trust auto-publish | > 20 points ends pre-moderation | Hub trust threshold for moderation only; no points or ranks | H1 | Specced (draft): [community hub §10](../specs/2026-10-07-community-hub-design.md#10-moderation-and-abuse) |
| Events: registration, Going, ICS, capacity | The Hub never touches money | Hub events | H2 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Videos, News | YouTube links, articles | — | — | Out: link out from posts; no media portal |
| Communities (≥ 1,000 members) | Clubs need a large base | Hub clubs of any size, linkable to core groups | H2 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Moderation: report, block, review, code of conduct | Staff review, bans | Hub moderation, appeals, audit | H1 | Specced (draft): [community hub §10](../specs/2026-10-07-community-hub-design.md#10-moderation-and-abuse) |
| Licence gates sync and sharing | Paid tier | — | — | Out: never charge for safety, sharing or decode help; only hosted storage or relay |
| No public API, anti-scraping | Internal endpoints | Hub documented OpenAPI with scoped tokens | H1 | Specced (draft): [community hub §3](../specs/2026-10-07-community-hub-design.md#3-repos-and-stack) |
| Self-hosting | Not offered | `ostler-hub` self-hostable, one official instance, not in `ostler-cloud` | H1 | Specced (draft): [community hub §3](../specs/2026-10-07-community-hub-design.md#3-repos-and-stack) |
| Federation | None | Outbound-only, allowlist, not before H5 | H5 | Specced (draft): [community hub §13](../specs/2026-10-07-community-hub-design.md#13-phases) |
| Vehicle data on the Hub | Labels only; OBD data never shared | Ostler's edge: garage cards, telemetry and faults at chosen levels | H1–H2 | Specced (draft): [community hub §5](../specs/2026-10-07-community-hub-design.md#5-what-can-be-published) |

## 12. DMD Hub web screens

| Screen or element | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| Landing portal with counters and feed | Busy portal, volume counters | Hub Discover: one search, chips, make/model/engine filter | H1 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Track detail (3D satellite map, stat strip, elevation) | Pitched 3D by default | Hub route and trip page on flat Ostler Night, smoothed elevation | H1 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub); 3D out in v1 |
| Shared trip page with level tabs | (DMD has none for vehicle data) | Hub `/t/<id>`; tabs only for the level granted | H1 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Follower page (hero number, Moments sheet, trail badge) | Map-first, quiet stat stack | Hub live ride page; V&M relay link | H3 / V5 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Event live page | Full-screen map, one LIVE pill | Hub live ride page | H3 | Specced (draft): [community hub §9](../specs/2026-10-07-community-hub-design.md#9-discover-following-clubs-events-live-rides-comments) |
| Help thread | (none) | Hub help thread with an L3/L4 hand-over to named helpers, "solved" credit | H1 / TS5 | Specced (draft): [community hub §6](../specs/2026-10-07-community-hub-design.md#6-help-threads-and-l3l4-hand-overs) |
| Publish flow (choose, level, audience, preview) | Checklist only | Core Trips share sheet; the Hub uses the same steps | TS2 / H1 | Specced (draft): [trip sharing §11](../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit) |
| My shares list | Per-link states | Core Settings → Sharing + Hub rows | TS2 / H1 | Specced: [accounts §14.7](../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs); (draft) [trip sharing §11](../specs/2026-10-07-trip-sharing-design.md#11-preview-expiry-revoke-and-audit) |
| Visibility chip on every object | (none) | Core chip extended with `link` and `public` | TS2 / H1 | Specced (draft): [accounts §15.2](../specs/2026-10-06-accounts-sharing-design.md#152-audiences-link-added-public-brought-forward-changes-142), [community hub §8](../specs/2026-10-07-community-hub-design.md#8-screens) |
| In-shell More → Community (Discover, Following, Help, Mine) | iPhone app | `ostler-app-hub`, Parked or passenger only | H1 | Specced (draft): [community hub §8.2](../specs/2026-10-07-community-hub-design.md#82-in-shell-add-on-ostler-app-hub) |
| Share row (Facebook, X, LinkedIn, Instagram) | Brand buttons and scripts | Web Share, copy link, QR, embed card | H1 | Out: no social-network buttons or scripts |
| Embed card, report with pin, Add to calendar, copy coordinates | Small useful tools | Hub | H1–H2 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Units by viewer locale | Miles from the browser | Hub: viewer locale with a km/mi switch | H1 | Specced (draft): [community hub §8.1](../specs/2026-10-07-community-hub-design.md#81-web-app-ostler-hub) |
| Sign-in walls | Inconsistent | One rule: `public` readable signed out, `link` needs the link, members-only needs sign-in | H1 | Specced (draft): [community hub §7](../specs/2026-10-07-community-hub-design.md#7-item-states-links-and-their-controls) |
| Photos in posts and items | One photo per post | Hub photos at H4, with on-device face/plate blur and hash matching; H1 takes track, trip and log files only | H4 | Specced (draft): [community hub §13](../specs/2026-10-07-community-hub-design.md#13-phases) |

## 13. Per-trip sharing levels (the owner's ask)

DMD shares GPX files and live trips; it never shares vehicle data. Ostler's five levels
([trip sharing §3](../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels), draft;
[ADR-0043](../decisions/adr-0043-gps-and-logs-in-shared-trips.md), proposed):

| Level | What leaves | How it leaves | Home | Phase | Spec status |
|---|---|---|---|---|---|
| **L0 Card** | Stats only, no map; max speed hidden on public cards; date day-only | Grant (person, group, household, `link`, `public`) | Trips share sheet, Shell registry | TS2 / TS5 | Specced (draft): [trip sharing §3](../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels) |
| **L1 Route** | Ends trimmed 500 m (never < 200 m), privacy zones ≥ 500 m with a fixed random offset, simplified, no point timestamps, stats from the visible trace | Grant on the new `route` detail of `location`; `public` only by a publish act ≥ 24 h after the trip | Trips, Shell Places | TS2 / TS5 | Specced (draft): [trip sharing §5](../specs/2026-10-07-trip-sharing-design.md#5-trimming-privacy-zones-and-stats), [accounts §15.1](../specs/2026-10-06-accounts-sharing-design.md#151-a-route-detail-on-the-location-ladder-changes-141-and-145) |
| **L2 Telemetry** | Chosen VSS signals, relative time | Grant (person, group/club) | Trips | TS2 / TS5 | Specced (draft): [trip sharing §3](../specs/2026-10-07-trip-sharing-design.md#3-the-five-levels) |
| **L3 Full log** | Complete recording incl. raw tap, scrubbed | **Hand-over, never a grant**: file, relay link (key in the URL fragment) or hub help thread; passes `ostler share verify` first | Trips, Platform, Decode lab | TS1 file / TS4 relay / TS5 hub | Specced (draft): [trip sharing §10](../specs/2026-10-07-trip-sharing-design.md#10-delivery-paths-and-link-controls), [accounts §15.5](../specs/2026-10-06-accounts-sharing-design.md) |
| **L4 Diagnostics bundle** | Faults, freeze frames, module info, scrubbed | Hand-over, as L3; "get help with this fault" in Diagnose | Diagnose, Platform | TS1 / TS3 | Specced (draft): [trip sharing §13](../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose) |
| `ostler.share/1` bundle and verifier | Zip with `share.json`, hashes and a redaction record; pcapng, candump for CAN; ids re-minted; not signed with the Brain key | — | Platform | TS1 | Specced (draft): [trip sharing §9](../specs/2026-10-07-trip-sharing-design.md#9-the-bundle-ostlershare1-and-the-verifier) |
| Help me decode / diagnose | Helpers send recording recipes, never remote actions; only derived decodes and short fixture snippets flow back under CC BY-SA 4.0 | — | Decode lab, Diagnose, Hub | TS3 / H1 | Specced (draft): [trip sharing §13](../specs/2026-10-07-trip-sharing-design.md#13-help-me-decode-or-diagnose); rules from [ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md), [ADR-0012](../decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md), [ADR-0036](../decisions/adr-0036-vin-and-identity-data-in-recordings.md) |

## 14. DMD2 UI patterns (from the UI teardown)

| Pattern | DMD behaviour | Ostler home | Phase / dependency | Spec status |
|---|---|---|---|---|
| D-pad input model | Joystick, two buttons and zoom on every screen | **ShellInput** in core: keyboard arrows/Enter/Escape, HID remotes, Gamepad API, read-only steering-wheel button events from packs | I1–I3 (U2) | Specced (draft): [ShellInput §2–§3](../specs/2026-10-07-shell-input-design.md#3-sources) |
| Focus zones, spatial navigation | Base view, overlay, bottom menu | ShellInput zones (strip, rail, main, sheet) | I1 | Specced (draft): [ShellInput §4](../specs/2026-10-07-shell-input-design.md#4-focus-zones-and-spatial-navigation) |
| Focused row grows and fills | Glanceable but reflows | 3 px focus-ring token; the item never resizes | I1 | Specced (draft): [ShellInput §9](../specs/2026-10-07-shell-input-design.md#9-focus-visuals) |
| Bindings per context, key codes | Per-view tables | Bindings owned by the display, not synced, edited Parked only | I2 | Specced (draft): [ShellInput §8](../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test) |
| Slot editor with swap on duplicate | Accordion per slot | Drive layout editor, slot-first, swap on drop, Parked only | DM2 | Specced (draft): [drive modes §7.4](../specs/2026-10-07-drive-modes-and-editing-design.md#74-drive-modes) |
| Dark chrome, light map | Glare beats consistency | Night map by default; a High-contrast Day map | U2 | Needs spec: [visual §7](../specs/2026-10-07-visual-design-system-design.md#7-maps) amendment |
| Family colour rail in the menu | Eight colours | — | — | Out: one accent; families Parked only, words not colours |
| Large red turn card | Navigation emphasis | Nav manoeuvre in `text-1` on `surface-glass` | N1 | Specced (draft): [navigation §5.2](../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) |

## 15. Deliberate leave-outs

| Left out | DMD has it | Why not |
|---|---|---|
| Android-only, launcher, own tablets | Yes | Ostler is a web UI on any screen, one shell ([ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)) |
| CarPlay or Android Auto projection of the dashboard | No (on purpose) | Same answer as DMD for live gauges; ADR-0042 allows only thin, later companions (alerts, trip status) |
| Speed cameras | Yes | Not in v1: legal per country, and an override puts the burden on the driver |
| Speed-limit history or scoring | No | Never logged or scored; the tint is Nav-only and off by default |
| Points, badges, ranks, leaderboards | Yes | No gamification; trust thresholds for moderation only, plus counts and "solved" credits |
| Public feed for strangers | Yes | Discover instead; a Following feed, opt-in, in `ostler-app-hub` only, never in Social |
| Social-network share buttons | Yes | Web Share, copy link, QR and embed only; no third-party scripts |
| Licence gating sync, sharing, groups, remotes | Yes | Never charge for safety, sharing or decode help; only hosted storage or relay |
| Viewer chat on live pages (v1) | Yes | Needs moderation tools first; members use the Social ride channel |
| Pause recording, separate share recorder | Yes | One always-on logbook (ADR-0009, ADR-0011) |
| Notification and message mirroring while Moving | Yes | No message content on driver displays while Moving ([UI §12.1](../specs/2026-10-06-ui-architecture-design.md)); Phone is Parked-only |
| Free pixel drag of overlays | Yes | Per-class grids travel between screens; drag does not |
| Images on the hub before H4 | Yes | Online Safety Act hash-matching duty; photos only with on-device blur |
| Video portal, news | Yes | Link out; not core to a vehicle-data hub |
| Pitched 3D satellite maps by default | Yes | Flat Ostler Night first; imagery only where its licence allows |
| Rally scoring (penalties, results) | Yes | Niche; only if events ask for it, after N4 |

## 16. Build order

The order follows dependencies, not size. Core comes first, because every add-on reads it.

1. **Core in the U2 window:** lockouts, Drive modes DM1 (faces, the Dashboard hero),
   **ShellInput** I1–I2 and the Drive menu, the map theme setting, Trips live signals and Trip A/B, the minimum-distance and 5 km/h
   rules.
2. **Core sharing (TS1–TS3, with accounts P2 and the accounts §15 amendment):** scrubber,
   `ostler.share/1`, `ostler share verify`, More → Places, the Trips share sheet, Diagnose "get
   help with this fault", Decode lab help-decode. L3/L4 hand-overs work by file with no server.
3. **Approved add-ons as already phased:** Social S1, V&M V1–V2, M&G M1–M2.
4. **Navigation N0–N2:** routing on the Brain and guidance through the `map` template, then the
   library, follow track and planner; speed limit off by default.
5. **Ostler Community H1 with TS5:** `ostler-hub` + `ostler-app-hub`: device linking, Discover,
   publish L0/L1, L2 to clubs, help threads with L3/L4 hand-overs, moderation, export and
   delete; no images. Then **Nav N3** shares curated routes to it.
6. **Hub H2:** clubs, events, comments, the Following feed; TS4 relay links when Ostler Cloud's
   relay exists.
7. **Later, each with its own spec:** Alerts A1–A2, Hub H3 live rides (after V&M V5), Phone,
   Crash SOS and the unplug alarm in core Security, Hub H4 photos, Nav N4 roadbook and rider
   reports, Hub H5 federation only on measured demand.

## Changelog

- 2026-10-07: v0.1, draft for the owner (DMD round): every DMD2 and DMD Hub feature mapped to
  an Ostler home, phase and spec status; leave-outs; build order.

## Decisions for the owner

1. **Is this the map to work from?** Recommend: accept it as the DMD checklist; a "Needs spec"
   row closes only when an approved spec section covers it. Alternative: keep the mapping only
   inside the research notes.
2. **One navigation add-on that absorbs routes and roadbook?** Recommend: yes, one
   `ostler-app-navigation`, with the roadbook in its last phase (N4). Alternative: separate
   `ostler-app-routes` and `ostler-app-roadbook` repos (more repos sharing one map and library).
3. **Alerts phase labels (A1–A2) before an alerts spec exists?** Recommend: use them here as
   placeholders, replaced by the alerts spec's own phases. Alternative: no labels until the spec
   exists.
4. **ShellInput and the Drive menu in U2?** Recommend: yes, core, shipped with U2's lockouts;
   hardware remotes are hardware add-ons that only supply key events. Alternative: after U2,
   leaving head units touch-only at first.
5. **Crash SOS and the unplug alarm in core Security, later?** Recommend: yes, after U5 with
   their own spec, free, as the one ghost exception (accounts §14.5). Alternative: a separate
   `ostler-app-sos` add-on.
6. **Alerts and Phone as separate add-ons, both later?** Recommend: yes; Alerts UK-first, free
   and opt-in; Phone Parked-only. Alternative: fold Alerts into Navigation and leave phone
   mirroring out entirely.
7. **The leave-out list (§15)?** Recommend: accept it as the "not in v1" record, revisited only
   by an owner decision. Alternative: plan speed cameras and viewer chat as later add-ons now.
