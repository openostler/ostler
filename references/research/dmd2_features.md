---
title: "DMD2 (DMD Navigation) feature catalogue, mapped onto Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [docs/ecosystem.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, references/research/addons_catalogue.md, references/research/driver_distraction_rules.md, references/research/social_group_drive_apps.md]
summary: >
  Every DMD2 feature, from the official site, the full DMD2 manual (28 pages), the device manuals,
  companion-app pages, the FAQ, the public roadmap and the Play listing (checked 2026-10-07, v4.029).
  DMD2 is an Android-only offline navigation app and dashboard for adventure riders and 4x4s: on-device
  routing with six profiles, GPX done in depth, a rally roadbook, a configurable home dashboard, Bluetooth
  accessories (remotes, OBD2/CAN, TPMS, power box, action cameras, BMW CAN box), riding groups over
  internet and LoRa, trip sharing with privacy delay, rider hazard reports and OpenStreetMap editing.
  Each feature gets an Ostler home; navigation, roadbook, alerts and phone link become NEW add-ons.
  Ends with Styling, a by-home mapping table and Copy / Avoid / Decide.
---

# DMD2 feature catalogue, mapped onto Ostler

The owner calls DMD2 and the DMD HUB "very similar to our project" and wants their features in
Ostler, many as add-ons. This note is the app side (R1); the HUB website, planner and social layer
are covered from the app's point of view only. All facts checked live on 2026-10-07; (U) marks what
could not be confirmed.

**Sources (2026-10-07):** product page [dmdnavigation.com/dmd2-app](https://www.dmdnavigation.com/dmd2-app/);
the manual hub [docs.dmdnavigation.com/dmdnext](https://docs.dmdnavigation.com/dmdnext/) and all 27
pages under it (App Structure, Global Settings, Home, Map, Settings & Layers, Community Ways,
Navigation, GPX, GPX Manager, Loaded Files, Recording, Planner, Warnings, Improve the Map, Rider
Reports, Devices, Roadbook, Remote Controller Menu, HUB, Riding Groups, Locations, Discover, Trip
Sharing, Live Event, License Keys, Device Registration, Opening Files); the
[FAQ](https://docs.dmdnavigation.com/faq/); [device manuals](https://docs.dmdnavigation.com/devicemanuals/)
(T665, T865/T865X, Remote 2, Remote 4, OBD M1, TPMS, Power Box, BMW Sync Box); companion apps
([LoRa](https://docs.dmdnavigation.com/otherapps/lora/), [SOS & Alarm](https://docs.dmdnavigation.com/otherapps/sos/),
[Phone Link](https://docs.dmdnavigation.com/otherapps/phone-link/), Manage, Mini Launcher, Auto Off);
developer pages ([GPX extension](https://docs.dmdnavigation.com/dev/gpx-extension/),
[LoRa open API](https://docs.dmdnavigation.com/dev/lora-api/)); the firmware log and the public
[roadmap](https://docs.dmdnavigation.com/roadmap/); the
[Play listing](https://play.google.com/store/apps/details?id=com.thorkracing.dmd2launcher)
(DMD Navigation LDA, 4.1 stars from 1.32k reviews, 100k+ installs, updated 2 Oct 2026); the
[product lineup](https://www.dmdnavigation.com/lineup/); and the
[Oct 2025 "free for all" news post](https://www.dmdnavigation.com/news/68f0c5594fadb7fbd6030922/).

## 1. What DMD2 is

- **Product shape.** One Android app (package `com.thorkracing.dmd2launcher`, by Thork Racing, now
  DMD Navigation LDA, Portugal) rebuilt as v4 ("DMD2 Next") over the classic 3.x app, which ended at
  3.00290. Four sections: **Home, Map, Devices, Roadbook**, plus the HUB opened from Quick Actions. A
  persistent top status bar, up to three side-by-side panels in landscape (two in portrait), and a
  three-part bottom bar (section buttons, speedo, section controls).
- **Platforms.** Android only, "not planned to change" (FAQ): iOS is judged too hard and iPhones too
  fragile on a bike. No Android Auto or CarPlay, on purpose (streamed layouts would cripple it). An
  iPhone/iPad **DMD HUB** app is the companion (plan, share, groups, send a destination to the unit).
  Play build and sideloaded APK are signed differently and cannot update each other.
- **Business model.** Since Oct 2025 the app is free to install and ride: offline maps (three
  downloads), routing, GPX, roadbook, trips, profiles and every DMD device. A licence (6- or 12-month
  Play subscription, a DMD device's built-in licence, or legacy Thork Racing keys) adds online layers,
  weather, the worldwide fire layers, HUB sync, riding groups, trip sharing, Discover listings, online
  search, unlimited map downloads and generic (non-DMD) remotes. Subscription price not published
  (U). **"Safety features are free, on purpose"**: since 17 Aug 2026 the country hazard modules are
  outside the paid tier for good.
- **Hardware.** Rugged Android head units ship with the licence and companion system apps (Manage,
  SOS & Alarm, Auto Off, LoRa, Mini Launcher, eSIM).

Ostler homes below use: **Core** (Shell, Drive mode, Trips, Diagnose, Network, Security;
[ecosystem](../../docs/ecosystem.md)); approved add-ons **Social**, **V&M** (Vehicles & Map),
**M&G** (Maintenance & Garage), **Cameras**, **Integrations**; hardware add-ons from the
[catalogue](addons_catalogue.md); and NEW add-ons proposed here: **`ostler-app-navigation`** (Nav),
**`ostler-app-roadbook`** (Roadbook), **`ostler-app-alerts`** (Alerts), **`ostler-app-phone`** (Phone).
"—" means not needed, with the reason.

## 2. App structure and global settings

| Feature | What it does | Ostler home |
|---|---|---|
| Top status bar | Battery, GPS precision in metres (colour by fix quality), weather, online, clock | Core Shell strip (add GPS-fix chip) |
| Panel cascade | Settings and details open to the right of the main view, up to 3 panels | Core Shell (head-unit layout classes) |
| Bottom bar speedo | Centre slot shows speed + limit sign + alert slot; per-section choice of speed, trip, altitude, bearing, RPM, coolant, TPMS | Core Drive mode (strip hero value) |
| Speed colour ramp | Speed digits orange within 10 km/h of limit, red over | Nav (needs limit) + Core Drive |
| Trip view | Tap speedo: trip distance, total/moving/stopped time, avg speed, reset with confirm | Core Trips |
| Quick Menu | Profile, Settings, Keep Background, Shutdown from any section | Core Shell |
| Rider profiles (6) | Whole independent setups (layout, devices, map, units, menus, trip meters), synced to HUB; active profile per device | Core Shell: per-vehicle settings in the garage (UI spec active-vehicle switcher) |
| Profile copy / force sync | Duplicate a profile; compare device vs HUB copy, upload/download, manual-sync switch | Core Shell (settings export/import) |
| Theme | Light, Dark, Auto (system), Auto (ambient light sensor); map theme separate or follows app | Core Shell (visual design system) |
| Units | Independent distance, altitude, speed, temperature, pressure (bar/PSI/kPa), 12/24 h; speed can differ from distance (UK) | Core Shell |
| App language and voice | App language reloads UI and voice together; map label language separate | Core Shell / Nav |
| Background activity | Per-feature keep-alive (trip computer, groups, recorder, voice), PiP auto/always/never, activity recognition pauses GPS when stopped | — on Brain-served web UI; Core power states (ADR-0040) where relevant |
| Display scale, font, orientation lock | Size the whole UI, pick typeface, lock orientation (holds unit auto-rotate) | Core Shell |
| App sections on/off | Hide Home/Devices/Roadbook buttons; Map always stays | Core Shell (add-ons choose destinations, not new ones) |
| Notification filter | Per-app allow list for notifications shown in DMD | Phone |
| Report Issue | Sends description with logs attached | Core Shell (support bundle) |
| First-run tour | 13 steps: units, tour, download a map, sign in | Core Shell onboarding |
| Map data credits | OSM ODbL credit and link | Core (ADR-0009 basemap) |
| Shutdown | Ends nav cleanly, auto-saves a running recording, stops services; no confirm | — (Brain stays up; power states own this) |

## 3. Home dashboard and widgets

| Feature | What it does | Ostler home |
|---|---|---|
| Home 1 / Home 2 | Two independent three-row layouts, swap in one tap or show both | Core Drive layouts as data (UI spec §12.3) |
| Draggable dividers | Snap stops share screen between rows and map (1/2/3 rows, strip over map); handles dim after 10 s | Core Drive (`map` pane share) |
| Full-screen minimal mode | Car-cluster view: speed ring to 200 km/h, altitude, heading, trip, weather, now playing, one card per live device; self-balancing | Core Drive mode (default layout) |
| Row: App Shortcuts | Grid of app launchers | — (Ostler is not a launcher) |
| Row: Favorite Locations | Distance tiles to saved places; tap to navigate | Nav |
| Row: Media Player | Mirrors the active Android media session | Core Drive `media` template |
| Row: Useful Indicators | Weather, altitude, trip distance, notification count | Core Drive tiles |
| Row: GPS Dashboard | Compass, pitch/roll gauges, altitude, GPS time, accuracy; expands | Core Drive tiles (IMU pitch/roll, `motion.py`) |
| Row: Trip Info | Distance, total, moving, stopped time; ticks without fix | Core Trips |
| Row: Odometer | Total plus Trip A / Trip B, each reset/pause/switch | Core Trips (odometer history) |
| Row: Profile Switcher | Avatar strip of profiles | Core Shell garage switcher |
| Row: OBD2 Sensors | Three tap-to-reassign gauge cells | Core Drive tiles (VSS paths) |
| Row: TPMS | Pressure, temperature, sensor battery per tyre; low alarm | HW TPMS add-on → Core Drive tile |
| Row: Power Box | Switch six aux outputs | HW relay add-on via gate (ADR-0033) |
| Row: Fuel Level | Range left from tank settings | M&G (fuel) + Core Drive tile |
| Row: Action Cameras | Record start/stop, battery | Cameras |
| Row: Last Notifications | Three latest phone notifications | Phone (Parked only, distraction rules) |
| Row: Weather Details | Conditions, high/low | Alerts |
| Row: Speedometer | Big digits, limit roundel, camera countdown, road-name band that becomes a speed-vs-limit bar | Core Drive + Nav |
| Overlays: Notifications / Weather / All Apps | Pop over the active home | Phone / Alerts / — |
| Remote cycle on Home | One button walks Home → Trip → Notifications → Weather | Core Shell input map |
| Trip A/B settings | Reset after inactivity (6 h–5 d), scheduled daily/weekly/monthly, reset both, single-meter mode | Core Trips |

## 4. Map, layers and offline maps

| Feature | What it does | Ostler home |
|---|---|---|
| Offline vector maps | 300+ regions by continent/country, update badges, Update All, Download All for a region, SD card storage | Core basemap (ADR-0009: Brain PMTiles); region manager in Nav |
| Free map limit | Three downloads free | — (no gating) |
| Un-downloaded area card | Warns when you ride off your maps and names the map to fetch | Nav |
| Follow modes | Bearing-up, 3D, north-up, free; rotation lock | V&M map / Nav |
| Map Scale | Map 1–4x, labels 0.5–1.3x, symbols 1–2.3x, live | Core visual tokens / Nav |
| Map Setup | Per road type, POI category and label a "show from" scale; contour toggle | Nav (style builder) |
| Auto Zoom | Zoom and tilt by speed (steps at 35/50 km/h, glide to top speed), pause after manual zoom, Turn Preview flattens/zooms before turns | Nav |
| Snap to Road Hybrid | Dead-reckons the icon along route/road between fixes and through tunnels | Nav |
| Online layers | ESRI satellite, national topo rasters (US, SE, AU, NO, CZ, FR IGN), hillshading, public GPS traces, custom rasters, opacity each | Nav (layers; UK: OS Open data (U)) |
| Weather overlays | Precipitation, wind, refreshed every 10 min | Alerts |
| Offline caching | Auto-cache viewed tiles; download a drawn rectangle or a 1–20 km corridor along a GPX | Nav (+ Brain tile cache) |
| Online Layers button | Count badge, quick layer dialog | Nav |
| Map overlays + placement mode | Floating cards (speed, altitude, heading, clock, road name, progress) dragged and sized per orientation, Auto Arrange, hide-all switch | Core Drive (layout editor, Parked only) |
| Round map buttons | Follow, zoom, group, trip sharing, direct lines, layers, HUB, planner shortcuts | Nav / V&M |
| Quick Actions panel | One-tap map actions and toggles (themes, layers, recorder, save location, reports) | Core Shell action menu |
| Shortcut button | Rider-assignable slot for a view, action or toggle, shows toggle state | Core Shell |
| Direct Lines | Up to 10 coloured crow-flies lines with live distance to a waypoint, place or map point | Nav |
| Auto POI | Four category slots searched along the line or around you, radius 0.5–10 km, extend to 100 km if empty, on-line/detour dots | Nav |
| My Locations pins | Photo or category pins, name tooltips, size | Nav |
| Community Ways | Roads ridden by ≥3 riders, learned anonymously from indexed GPX; solid paved, dashed unpaved, dotted not in OSM | Nav (needs a shared server; later) |
| Location Info (long-press) | What the map knows about a road; Navigate, Save, Share, Open With | Nav |

## 5. Navigation and routing

| Feature | What it does | Ostler home |
|---|---|---|
| On-board router | "DMD Router", fully offline on installed maps | Nav (engine on the Brain) |
| Routing profiles | Road Fast, Road Fun, Match Any Road, Offroad Easy/Medium/Hard, Advanced Adventure | Nav |
| Road options | No tolls, no motorways, avoid classes; Adventure prefers forests/rivers/unpaved, avoids cities/ferries/private | Nav |
| Terrain and legality | Soft-avoid gates and fords; legality overrides for private/permission roads | Nav |
| Community routing | Pull routes onto Community Ways (auto/prefer/strong) | Nav (later) |
| Destinations | Search (address, POI, coordinates, own and HUB places), long-press, favourites, GPX, shared from apps | Nav |
| Offline search | Address and POI search on device; online adds HUB places | Nav |
| Turn card | Big arrow, distance, "then" preview, distance and ETA (tap flips arrival/remaining), progress bar, NAV/GPX badge | Nav → Core Drive `map` template |
| On-road detail | Lane guidance, roundabout exits, road names, motorway exits | Nav |
| Voice | TTS prompts in 7 languages, falls back to English | Nav |
| Navigation Options | Route colour, profile, via-points, route info (ascent, surface split), measure along route, save as GPX | Nav |
| Off-route choices | Reroute to line / to next point / don't, with countdown and remote focus | Nav |
| Route failure handling | Keeps guiding on old route, retries as you move, auto-dismiss 60 s | Nav |
| Next / priority waypoints | Next waypoint line, starred objectives on an amber line (up to 3 in landscape), stored in the GPX | Nav |
| Share navigation with group | Leader's route becomes group GPX; reroutes deliberately not pushed; keep until all arrive | Nav + Social |
| Weather / Warnings On Route | Per-stop forecast, fires, country warnings, rider reports; "Warnings Where You Are" with no route | Alerts (free) + Nav |

## 6. GPX tracks, routes, waypoints, planner

| Feature | What it does | Ostler home |
|---|---|---|
| Multiple loaded files | Show/hide, reorder draw order, filter by name, colour all; capacity measured in points | Nav |
| Track/route/waypoint detail | Colour (12), invert, centre, navigate, ascent/descent, point info, measure two-point | Nav |
| Line appearance | Width, opacity, arrows, unpaved dashes, colour by surface or slope, distance pins | Nav (Trips replay already colours by speed) |
| Track Navigation | Turn-by-turn from a plain track, next-curve geometry by difficulty, or hybrid; curve alerts by flash or voice | Nav |
| Off-track / wrong direction | >20 m for a few fixes, or 15 m and diverging | Nav |
| Route Repair | Fix automatically, show failed points, change profile | Nav |
| Route points editor | Add from map/search, drag to reorder | Nav |
| Planner (on device) | Multi-section files: routes by stops, tracks by anchors (snap/connect/free), finger draw, cut, merge, reduce points, convert route↔track, undo/redo | Nav (touch only, Parked) |
| GPX Manager | Library with folders, special folders (My Recordings, My Trips, Shared With Me, Community), filters (colour, vehicle, difficulty, tags), sort by distance | Nav library; recordings stay Core Trips |
| Ridden progress | Per-file % ridden, time invested, personal best | Nav + Trips |
| File details | Title, description, warnings, tags, country, season, vehicle and difficulty, off-road %, two photos, YouTube link | Nav |
| Share file | Send the .gpx through any app | Core Trips export (exists) |
| Share link: Locked | Lands in recipient's Shared With Me, stays in sync, revocable; available-from, link expiry, access-until (deleted from device), collection limit | Social + accounts grants (`trips` class) |
| Share link: Download | Their own copy; expiry, per-user download limit | Social |
| Make public | Reviewed publication to Discover with a checklist | Social (public audience reserved, later) |
| Help the planner learn | Opt-in anonymous indexing of files for Community Ways | Nav (later, opt-in) |
| Import formats | GPX, KML, KMZ, GeoJSON, TCX, FIT, ITN, waypoint CSV; content-sniffed; batch | Core Trips import + Nav |
| Shared places | Google/Apple Maps, Waze, OSM, HERE, OsmAnd links, coordinates, Plus Codes, MGRS, UTM, photo EXIF, contacts | Nav |
| Open With out | Send a point to any installed map app (show or navigate) | Nav |
| DMD GPX extension | Namespaced GPX 1.1 with pre-rendered route, instructions, surface, timing, regulations, nav card and integrity hash | Nav (read it; consider own extension) |

## 7. Ride recording and statistics

| Feature | What it does | Ostler home |
|---|---|---|
| GPX recorder | Idle/recording/paused; live distance, tracks, moving and stop time, avg/max speed, climb, waypoints | Core Trips (sessions already record GPS) |
| Under 5 km/h is not travel | No distance, climb or points below 5 km/h | Core Trips (copy the rule) |
| Auto-record | Starts on movement, jitter threshold | Core Trips (sessions start on connect) |
| New track / add waypoint | Split days; quick-pick waypoint types learned by use; movable pin | Core Trips (Mark, ADR-0010) |
| Survives shutdown, crash recovery | Resumes or asks on next launch | Core Trips |
| My Recordings sync | Auto-named, monthly folders, local/remote states, download all | Core Trips (+ Social for sync) |
| Save questions | What did you ride, and more, on finish | Core Trips (vehicle known already) |
| Lean angle recording | Roadmap request (U, not shipped) | Core Trips (IMU exists) |

## 8. Roadbook and rally

| Feature | What it does | Ostler home |
|---|---|---|
| Readers | PDF, GPX roadbooks and OpenRally (FIA format) | Roadbook |
| Generate roadbook | Tulips from an active navigation, route or track | Roadbook |
| Tulip strip | Partial/total distance, heading, CAP with L/R degrees, next WP, ON COURSE | Roadbook |
| Trip meter adjust | Adjust total/partial to the top row in one press | Roadbook |
| Notes mode | Annotate tulips; notes travel with the roadbook | Roadbook |
| Waypoint validation | Validated/missed, penalties, results view to share | Roadbook |
| Chrono, speed zones | Stage stopwatch; zone limit and distance to end | Roadbook |
| Map split, locked maps | Map beside roadbook unless event rules forbid it | Roadbook |
| Own remote mapping | Buttons page the roadbook in this section | Roadbook + Core input map |
| Three instrument panels, session resume | Configurable values; resume stage | Roadbook |
| DMD Events | Event feed, file prefetch 24 h before and unlock at start, auto-open roadbook, navigate to start | Social (events, later) + Roadbook |
| Live Event | States (active, break, need a hand), SOS to crew and nearest riders, board, crew messages, roles (sweep, lead), finish safe, public live page | Social (later) |

## 9. Devices and sensors

| Feature | What it does | Ostler home |
|---|---|---|
| Devices section | Paired accessories as live cards, saved per profile, auto-reconnect, user ordering | Core Network (device pages) |
| OBD2 dongle | Bluetooth ELM327: voltage, RPM, coolant, intake temp and more; "show unsupported" | Core Diagnose / generic OBD2 pack (ADR-0031) |
| CAN cable | Wired CAN feed through the Manage app (firmware added the driver Apr 2026) | Core (CAN links, ADR-0020) |
| DTC read/clear | MIL button turns red with stored codes; read stored and pending, clear | Core Diagnose (clear through the gate) |
| OBD Scanner M1 | DMD's sealed waterproof ELM-style dongle, sleeps when parked | — (Ostler node is the reader) |
| DMD TPMS | BLE valve caps: pressure, temperature, battery; low and fast-deflation alarms; 2 or 4 wheels | HW TPMS add-on (catalogue: BLE or 433 MHz) |
| Power Box | BT 6-channel switch, 9–28 V, 80 A per channel; C1 ignition, C2 input switches profile or rules | HW relay add-on; actions gated (ADR-0033) |
| BMW Sync Box | CAN module on BMW bikes: Wonder Wheel drives the app; RPM, gear, coolant, ambient, throttle, TPMS | Vehicle packs (bike) + Core input map from passive CAN (ADR-0024) |
| Action cameras | DJI, Insta360 (X4, X3, ONE RS, ONE X2), GoPro (HERO 9–13, MAX); record all | Cameras |
| Fuel Level Simulator | Virtual tank: range counts down by GPS distance, low warning, reset to full | M&G fuel + Core Drive tile (real fuel signal preferred) |
| iPhone notifications | ANCS mirroring of notifications and calls, no app on the phone | Phone |
| GPS dashboard sensors | Compass (magnetic optional), pitch/roll, altitude | Core Drive tiles |

## 10. Handlebar and steering-wheel remotes

| Feature | What it does | Ostler home |
|---|---|---|
| DMD remotes | Remote 1 (legacy), Remote 2 (360° joystick, 2-way zoom switch, A/B; wired M9 or BT), Remote 2 Bracket Edition, Remote 3 (rally: longer switch, 3 big buttons), Remote 4 (steering wheel, BT, rechargeable) | HW "Dash buttons and keypads" add-on |
| Generic remote | Any BT keyboard/HID mapped to actions (licensed); third-party SilverFox arrives this way; no long-press menu | Core Shell input map (keyboard events) |
| Default mapping | Joystick pans map / moves in menus; switch zooms; Button 1 = follow toggle / confirm; Button 2 = back / cancel; long-press 2 = menu | Core Shell input map |
| Remote Controller Menu | Eight colour-coded families (Safety, Navigation, Devices, Save, Map, Media, Trip, System); rows appear only when relevant; reorder, hide per profile; first tap selects, second fires | Core Shell action menu (Moving-safe `short_list`) |
| Double-tap bindings | Any menu entry bound to a double tap; toast confirms | Core Shell input map |
| Unit buttons | Head unit's P1–P3 / colour buttons: press, long-press, double-tap each | Core Shell input map |
| Test Remote Keys | A falling-blocks game driven by your mapping that ticks off each key | Core Network device page (button test) |
| Dialog remote focus | Off-route and confirm dialogs driven by the remote, countdown default | Core Shell |

## 11. Groups, sharing, community

| Feature | What it does | Ostler home |
|---|---|---|
| Riding groups | Create, roles (owner/admin/moderator), active group, share location switch | Social (groups) + V&M (map) |
| Invites | Email, link (expiry and use limit, revoke), "Nearby" pick with no typing | Social (accounts §14.6 invites) |
| One device shares at a time | Second device asks to take over | Social |
| Live buddy tracking | Internet (NET badge) and LoRa at once; newest wins; Online/Offline/Timed out | V&M + LoRa HW add-on (ADR-0038) |
| Group tabs | Members (navigate to, mute), chat, files, events, locations, map drawings | Social |
| Group GPX | One active route on every member's map | Nav + Social |
| Help Me / I'm OK | Group beacon over LoRa and internet | Social (safety exception, ecosystem §3.4) |
| LoRa | 10–15 km, mesh relay, positions, speed, status flags, chat (100 msgs, not persisted), region auto-band; open AIDL API | Meshtastic-compatible LoRa add-on |
| Trip Sharing | Live link anyone opens without account; red map button with watcher count | Social + accounts registry |
| Trip privacy | Trail window none/1–24 h/all; delay live or 1–6 h (covers pins); show speed; show trip values | accounts registry grant options (Decide 3) |
| Listing on HUB | Findable on a Live map only if switched on per trip, with a one-time warning; drops after 2 h idle | Social (public reserved) |
| Viewer chat | Signed-in followers write 200-char messages; delete, block | Social |
| Moments | Quick messages, photos (EXIF location), video links, places, each pinned; edit, hide, delete | Social |
| Phone companion | Phone adds posts to the unit's trip | Social |
| Trip Journal | Keep or discard; map, timeline, Relive fly-through with chat replay, GPX in My Trips; auto-end after 24 h idle, kept 14 days | Core Trips + Social |
| Location Manager | Saved places with category, ground, vehicle, crowding, best time, warnings, photos | Nav |
| Discover | Community GPX, Signature Tracks (curated), locations, services, events, live riders, videos | Social (later) |
| HUB feed | Posts, likes, comments, follow, rider pages | Social |
| Rider Reports | One-tap closures and hazards; pins from zoom 10; on-route warning with Reroute to Avoid; Still There / Gone; offline queue; police/camera hidden where illegal | Nav (layer) + Social (transport) |
| Improve the Map | One-tap OSM tags (surface, smoothness, track type, width, signs), missing-track recording, gates/fords as nodes, 12 h undo, own OSM account | Nav (later; Integrations-style OSM sign-in) |

## 12. Alerts and hazards

| Feature | What it does | Ostler home |
|---|---|---|
| Speed limit | Sign in speedo when the map has a confirmed limit | Nav (OSM `maxspeed`) |
| User speed | Two personal thresholds | Core Drive (tile limits) |
| Speed cameras | Map/database cameras with countdown; off by law in DE, CH, FR unless the rider overrides | — v1 (Decide 6) |
| Waypoint proximity, off-track, wrong direction | Line alerts | Nav |
| Weather along route | Per-stop forecast | Alerts |
| Fire alerts | Worldwide active fires and fire danger (paid) | Alerts |
| Country modules (free) | Portugal Avisos (no-ride zones, IPMA fire and weather, ANEPC incidents), Catalunya Pla Alfa, France Vigilance and ZFE (motorcycle Crit'Air rules), NSW and Victoria fire | Alerts (UK equivalents to find) |
| Warnings Where You Are | Position check every 30 s, no refresh button | Alerts |
| TPMS alarm | Priority alert in speedo | HW TPMS → Core alert card |
| Outputs | Speedo slot, screen/LED flash in warning colour, voice | Core Drive `alert_card` |

## 13. Safety, power and companion apps (DMD units)

| Feature | What it does | Ostler home |
|---|---|---|
| Crash SOS | IMU + GPS speed; motorcycle and car models; road/adventure/enduro sensitivity; arms only when docked, screen on, calibrated and moving ≥15 m (50 m car); 60 s countdown; SMS with map link to 1–2 contacts; group Help Me | Core Security (later; safety exception) |
| Calibration | Upright zero on the bike, self-refines above 20 km/h | Core Security |
| Theft alarm | Arms when docked and screen off; unplugging triggers; siren, SMS, chirp; PIN to stop; silence from phone; report stolen and lock the unit | Core Security (exists in concept) |
| Auto Off | Shutdown/suspend by dock, ignition wire, inactivity | Core power states (ADR-0040) |
| Manage app | Remote setup, unit buttons, holder actions, walkie-talkie | Core Network + Social (push-to-talk) |
| Phone Link (Android) | Calls, messages, notifications, send files, share internet from pocket phone | Phone |
| Mini Launcher | Car-themed Android home with dialer and cards | — (Ostler shell is the dashboard) |
| eSIM, OTA firmware | Unit firmware log, security patches | — (head unit vendor's job) |

## 14. Hardware (DMD units)

| Unit | Notes | Ostler home |
|---|---|---|
| T665 | 5.7" Android 14 "navigation phone", IP68, 64 GB, 800 nit, dual SIM/SD; no theft alarm (no motion sensors) | — reference head unit class HU-phone |
| T865 / T865X | 8" Android 14, 8000 mAh, IP67, 60 °C, M9 connector; X: 128 GB, 1300 nit; T865 discontinued | — reference for HU-8 |
| T880X | 8", external GPS antenna, Android 16 firmware Aug 2026 (U for full specs) | — |
| NOR7E | 7", brightest; four coloured buttons; CAN cable driver | — |
| Holders | Motorcycle road, off-road (charging pins), 4x4 USB holder | — |
| 2-year warranty, CE/FCC/UKCA | Per manuals | — |

Reading: DMD's hardware is a phone-class Android tablet; Ostler's head-unit display is a browser on
whatever screen exists, with the car's own node doing the sensing. Their accessory list is the
shopping list for our hardware add-ons, not a design to copy.

## 15. Styling

Seen in the manual's screenshots (1280×800 captures saved in the scratchpad; not committed).

- **Dark chrome, light map by default.** Near-black top bar and bottom bar, dark rounded cards
  floating on a light OSM-style map; the map has its own dark theme.
- **Display face for numbers.** Wide, squared, heavy digits (speed, distances, times) with small grey
  units; labels in spaced uppercase small caps (TRIP, DISTANCE, ALTITUDE). Docs use Saira Semi
  Condensed; the app's digit face is unidentified (U).
- **Colour carries meaning.** Cyan `#00b4ff` for active state and selected rows; red for recording,
  over-limit and turn cards close to the manoeuvre; amber for paused, near-limit and priority
  waypoints; green for good GPS and online. Remote menu families each own a colour (orange
  navigation, red safety, magenta save, cyan map, violet media, grey system, green devices, teal trip)
  shown as a left rail and a row edge.
- **Selected row grows.** In the remote menu the focused row enlarges, fills with its family colour
  and shows its value large: a strong, glanceable focus state for gloved, remote-only use.
- **Turn card top-right**, dark red when close, with "then" preview and a flag line for distance/ETA.
- **Full-screen cluster**: a thin arc speed ring, three card columns, nothing configurable.
- **Rings on round buttons** encode state (red recording, yellow paused, white idle).

Ostler fit: our visual system already chose dark, calm, tabular numerals and level-only colour
changes ([UI spec §12.3](../../specs/2026-10-06-ui-architecture-design.md)). Take the focus-row
treatment and family colour rail for the action menu; avoid their light map as a default at night.

## 16. Feature → Ostler mapping (by home)

| Ostler home | DMD2 features it takes | Why there |
|---|---|---|
| Core Shell | Status bar GPS chip, panel cascade, Quick Menu, themes incl. light sensor, independent units, display scale, sections on/off, first-run tour, report issue, Quick Actions, shortcut slot, **input map and action menu** (remote families, double tap, unit buttons, dialog focus) | Every app needs the same input and settings; add-ons register actions, the shell draws them |
| Core Drive mode | Home 1/2 as Drive layouts, dividers, full-screen cluster, speedo slot and colour ramp, overlay placement, GPS dashboard, OBD tiles, user speed, alert outputs, media pane | Already "layouts as data" with `tiles`/`map`/`media` (UI §12.3) |
| Core Trips | Trip A/B and odometer, trip view, reset rules, recorder stats, 5 km/h rule, auto-record, Mark/waypoints, crash recovery, import formats, export, trip journal storage, lean angle | Trips owns recordings and stats (ecosystem table) |
| Core Diagnose | OBD2 live data, CAN feed, DTC read, clear via gate | Faults and scans are core |
| Core Network | Devices list, pairing, auto-reconnect, ordering, key test game | Device pages live here |
| Core Security | Crash SOS (later), theft alarm, report stolen | Alarm and tracker are Security |
| Social | Groups, invites, chat, Help Me, trip sharing link and privacy, viewer chat, moments, journals online, share links (locked/download), feed, Discover, events, Live Event | Social reads groups and grants from core |
| V&M | Live buddy map, member status, group pins | The map of others' vehicles |
| M&G | Fuel level and range | Fuel records live there |
| Cameras | Action camera control, record all | Camera control |
| Integrations | OSM account for Improve the Map (as `ostler-app-osm` if split) | Third-party account |
| NEW `ostler-app-navigation` | Offline routing, profiles, turn-by-turn, voice, GPX library and follow, track navigation, planner, route repair, Auto POI, direct lines, locations, search, layers and caching, auto zoom, snap to road, speed limits, rider-report layer, Community Ways, map region manager | Ostler has a map but no routing; large, optional, its own release cycle |
| NEW `ostler-app-roadbook` | PDF/OpenRally reader, generator, tulips, CAP, validation, chrono, speed zones, notes | Niche rally use; depends on Nav |
| NEW `ostler-app-alerts` | Weather, route weather, fires, country official warnings, warnings where you are | Hazard feeds are per-country and online; free always |
| NEW `ostler-app-phone` | Notification mirror, calls, phone link | Distraction-sensitive; separate grant and limits |
| HW add-ons | Remotes (dash buttons), TPMS, relay box, LoRa | Already in the catalogue |
| Not needed | App shortcuts, Mini Launcher, PiP/background keep-alive, shutdown, OBD M1 dongle, eSIM/firmware, free-map limit, licence keys | Platform-specific or business-model artefacts |

## 17. Copy / Avoid / Decide for Ostler

**Copy**

1. **Safety is never paywalled.** Their 2026 rule matches ecosystem §3.4; write it into GOALS.
2. **One action registry, two ways in.** Menu families, rows that only appear when relevant,
   first-tap-selects/second-fires, double-tap bindings: a Moving-safe `short_list` (ADR-0033 actions).
3. **Remote-first dialogs with a countdown** that applies the safest default (off-route choice).
4. **Trip sharing privacy knobs** (trail window, delay, speed, values, findable vs link-only, one-time
   warning before listing, auto-end after 24 h idle) for the owner's per-trip sharing.
5. **Share links with three dates** (available from, link expiry, access until) and revoke that
   removes the file from devices: the right shape for "share a full log for decoding help".
6. **Under 5 km/h is not travel**, and Relive-style replay with moments (Trips already replays).
7. **Key test game** as the button-mapping check on a device page.
8. **Free vs paid stated per feature** and "At a Glance" boxes in docs; a public, votable roadmap.
9. **Wheel buttons from the bike's CAN** (BMW Sync Box) as a passive input source.

**Avoid**

1. Android-only and launcher behaviour; Ostler stays a web UI on any screen.
2. A subscription gating groups and sync; any hosted relay we run must be optional (exit guarantee).
3. Speed-camera warnings with a "you are responsible" override.
4. Per-device licence binding, key moving and lockouts.
5. Shutdown with no confirmation; one monolithic app with sixteen map-settings categories.
6. Findable live position by default; their listing is off by default, ours stays ghost (§14.3).

**Decide**

1. **Build navigation?** Recommend: yes, NEW `ostler-app-navigation`, routing on the Brain with an
   open engine (BRouter for its scriptable offroad profiles, or Valhalla; licences to verify (U)),
   reading the same PMTiles regions; phase after Trips and V&M.
2. **Rider profiles?** Recommend: no separate concept; profile = vehicle in the garage plus the
   user's own preferences.
3. **Trip-sharing privacy as grant options?** Recommend: add `trail_window`, `delay` (0–6 h),
   `show_speed`, `show_values` to `location`/`trips` grants in the registry; delay 1 h suggested for
   any link audience.
4. **What may cost money?** Recommend: nothing in core or add-ons; only optional hosted services
   (relay, tile hosting), and never safety alerts.
5. **Remote menu in core?** Recommend: yes, Shell input map and action menu; hardware remotes are a
   hardware add-on that only supplies key events.
6. **Speed cameras?** Recommend: not in v1; speed limits from OSM only.
7. **Rider Reports and Community Ways need a shared server.** Recommend: later, over Social's
   transport with expiry by confirmation; no Ostler-run server required for core.
8. **Alerts add-on scope?** Recommend: NEW `ostler-app-alerts`, UK first (official weather and
   flood warnings; feed licences to check (U)), free and opt-in.
9. **Crash SOS?** Recommend: yes in Core Security later, copying their arming conditions,
   calibration and countdown; SMS through the guardian's modem.
10. **Phone mirroring?** Recommend: NEW `ostler-app-phone`, later, Parked-only content per the
    distraction rules ([driver_distraction_rules](driver_distraction_rules.md)).

See also [social group-drive apps](social_group_drive_apps.md), the
[Social spec](../../specs/2026-10-07-social-addon-design.md), the
[V&M spec](../../specs/2026-10-07-vehicles-and-map-addon-design.md), the
[M&G spec](../../specs/2026-10-07-maintenance-garage-addon-design.md),
[accounts §14](../../specs/2026-10-06-accounts-sharing-design.md),
[ADR-0009](../../decisions/adr-0009-session-logbook-and-location.md),
[ADR-0033](../../decisions/adr-0033-action-categories-and-approvals.md),
[ADR-0038](../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) and
[ADR-0042](../../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md).
