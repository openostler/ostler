---
title: "Navigation add-on — offline routing on the Brain, turn-by-turn and voice, GPX library and follow, planner and roadbook — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/dmd2_features.md, references/research/dmd2_ui_teardown.md, references/research/dmd_hub_features.md, references/research/community_hub_architecture.md, references/research/trip_and_log_sharing.md, references/research/driver_distraction_rules.md, docs/ecosystem.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-07-community-hub-design.md]
summary: >
  Draft for the owner (DMD round, 2026-10-07). One new optional add-on, `ostler-app-navigation`, for cars and
  motorcycles on and off road; it absorbs the earlier "routes" and "roadbook" add-on ideas. Routing runs on the
  Brain with Valhalla (MIT, checked live; per-request costing for car, motorcycle and off-road options, map
  matching, spoken-instruction text) behind an engine adapter, BRouter (MIT) as an optional second engine for
  scripted off-road profiles; OSRM and GraphHopper not chosen. One region download carries the visual spec's
  PMTiles, the routing graph and a search index. Guidance renders through the shell's `map` template
  next-manoeuvre while Moving (turn card, then-preview, lane arrows, ETA toggle), computed on the display from a
  route the Brain sends whole; an off-route card may auto-confirm because routing choices are not car actions.
  Voice uses the browser's speech first, Piper (GPL-3.0) later. A GPX library with import, export, follow and
  track-to-turns; a Parked planner; a roadbook view; saved places; curated routes and share to `ostler-app-hub`;
  a speed-limit sign and `warn` tint, off by default, never logged or scored; no speed cameras in v1; rider
  reports later over Social's transport. Privacy, offline behaviour, phases N0–N4, tests and decisions.
---

# Navigation add-on — design (draft)

**Status:** draft for the owner's approval (DMD round, 2026-10-07); nothing is built before U2 and
V1c (visual spec §11). Evidence: [DMD2 features](../references/research/dmd2_features.md) §4–§8
and §12, [DMD2 UI teardown](../references/research/dmd2_ui_teardown.md) §2, §8, [DMD Hub
features](../references/research/dmd_hub_features.md) §2.5, §2.9, §4,
[community hub architecture](../references/research/community_hub_architecture.md) and
[trip and log sharing](../references/research/trip_and_log_sharing.md). Framing:
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) (small core,
add-ons are the product). Input on head units: [ShellInput](2026-10-07-shell-input-design.md)
(draft, this round). Facts checked live on 2026-10-07; (U) marks what was not.

## 1. Scope and boundaries

For **cars and motorcycles, on road and off road** (green lanes, tracks, overland). One add-on,
**`ostler-app-navigation`** (own repo, ADR-0034; `trust: first_party`, off by default): a Python
service on the Brain plus a React UI bundled into the shell (app model §3, §7), like Maintenance
& Garage. It replaces the separate `ostler-app-routes` and `ostler-app-roadbook` ideas in the
DMD research.

| Owns | Does not own (reads from or hands to) |
|---|---|
| Routing on the Brain, profiles, destination search, guidance state, voice prompts | **Map rendering, styles, tokens, PMTiles serving:** the shell and the [visual spec](2026-10-07-visual-design-system-design.md) §7 |
| The **region manager**'s routing and search parts (§3) | **Recording, trip stats, Export all:** core **Trips** (recording stays Trips') |
| The GPX **library** (plans, imported files, curated routes), follow-track, planner, roadbook view | **Saved privacy zones and home/work Places:** core shell (More → Places, [trip-sharing spec](2026-10-07-trip-sharing-design.md) §5.2) |
| Speed-limit sign (optional), rider-report layer (later) | **Who may see a route:** the core data-class registry ([accounts §14](2026-10-06-accounts-sharing-design.md)) |
| Navigation rows in the Drive menu (§5.6) | **Others' vehicles on the map, convoys:** [Vehicles & Map](2026-10-07-vehicles-and-map-addon-design.md); talk and ride channels: [Social](2026-10-07-social-addon-design.md); publishing: `ostler-app-hub` |

It declares **no car actions** (ADR-0033): nothing in it touches any car. "Send this route to the
head unit" is the add-on's own data moving between the user's own devices, not an action.

## 2. Routing engine (on the Brain)

Licences read from each project's licence file on 2026-10-07; other facts from each README and
API reference the same day.

| Engine | Licence | Profiles | Turn text and voice | Map matching | Fit for a Pi 5-class Brain |
|---|---|---|---|---|---|
| **Valhalla** | **MIT** (`COPYING`) | **per request** ("dynamic, runtime costing"): `auto`, `motorcycle` (beta) with `use_trails` 0–1 ("adventure"), `use_highways`, `use_tolls`; auto `use_tracks`, `exclude_unpaved`; `truck`, `motor_scooter` | manoeuvres with `verbal_pre_transition_instruction` etc., locales in-repo | yes (`trace_route`, `trace_attributes`) | C++, tiled graph "for memory constrained devices … regional extracts"; Python bindings; build cost on a Pi unmeasured (U) |
| **BRouter** | **MIT** (`LICENSE`, 2019) | **scriptable profile files** per request; strong for off-road and elevation | "voice hints" exported in GPX flavours; no lanes | no | Java, low memory; segments built weekly by brouter.de or self-built |
| GraphHopper | Apache-2.0 | custom models per request | instructions, many languages; `/navigate` endpoint | yes | Java; offline/Android "no longer officially supported" (server use fine) |
| OSRM | BSD-2-Clause | Lua profile **baked at extract time**: one dataset per profile | instructions, lanes | yes | fast but one graph per profile; RAM-heavy on a Pi (U) |

**Recommendation: Valhalla** behind a small `RouteEngine` adapter (route, reroute, match,
attributes). It gives car, motorcycle and off-road preferences per request from **one** graph,
spoken-instruction text in many locales, map matching for track-to-turns (§6.3), elevation
(its `skadi` module) and an MIT licence that sits under our AGPL with a notice (ADR-0025).
**BRouter** is the optional second engine for N3–N4 off-road scripting if Valhalla's trail
weights prove too coarse on real green lanes. Not chosen: OSRM (a graph per profile), GraphHopper
(equal licence, but a second Java runtime for less off-road control than BRouter).

**Graph data.** Built from the same OSM extract (ODbL; a Produced Work, attribution as visual
spec §12) as the region's PMTiles, **on the Brain** by default, or imported as a prebuilt file.
No Ostler-run server is needed (exit guarantee, app model §14.6); a hosted prebuilt download may
come later as an optional paid-hosting convenience, never required and never for safety data.

## 3. Offline map regions

One **region** is one install unit, managed at **Settings → Maps** (the place the visual spec §7
already picks the region): the **PMTiles extract** (visual spec V1c), the **routing graph**, a
**search index** and optional **elevation** tiles, all cut from **one OSM extract date** so map,
router and search agree. The region list shows size, data date, an update badge and **Update**;
removing a region removes all four parts. Sizes are unmeasured (U); the Brain shows free space
before a download. The navigation add-on extends the region manager; without it, regions carry
PMTiles only, as today.

**Search** is our own **SQLite FTS5** index of named places, addresses (`addr:*`) and POI
categories built with the region (stdlib, no service). Coordinates, Plus Codes and pasted map
links (Google, Apple, OSM, OsmAnd) parse locally. Not chosen: Nominatim (GPL-2.0, a PostgreSQL
database), Photon or Pelias (an extra search server; licences not re-checked, U).

When the vehicle leaves every installed region the map shows one card, **"Off your maps: install
Wales"**, and guidance continues on the cached route (§8).

## 4. Profiles

A profile is a named set of engine options plus the garage vehicle's kind and size (car, 4x4,
van, motorcycle; height, width, weight and a trailer flag for `truck` costing later).

| Profile | Car / 4x4 | Motorcycle | Notes |
|---|---|---|---|
| **Fast** | `auto` | `motorcycle`, `use_highways` 1 | default |
| **Scenic** | `auto`, motorways and tolls low | `motorcycle`, `use_highways` 0.2 | "curvy" weighting does not exist in the engine; we do not claim it (U) |
| **Unpaved friendly** | `use_tracks` 0.5 | `use_trails` 0.5 | gravel and tracks allowed, not sought |
| **Off-road / 4x4** | `use_tracks` 1 | `use_trails` 1 | N3; BRouter scripted profiles as the option |
| **Avoid** toggles | motorways, tolls, ferries, unpaved (`exclude_unpaved`) | same | per route, remembered per vehicle |

**Legality first.** No profile routes on `access=no|private`, `motor_vehicle=no` or
`highway=footway|bridleway|cycleway|path` unless the user ticks a per-route "I have permission"
override, shown on the route with a warning. Off-road profiles prefer ways tagged as open to
vehicles (in England and Wales `designation=byway_open_to_all_traffic`), soft-avoid fords and
gates, and every route card says **"Check local access rules. Map data may be incomplete."**
Traffic Regulation Orders are not in OSM in general (U).

## 5. Guidance

### 5.1 Who computes what

The Brain computes routes; the **display computes guidance**. The Brain sends the whole route
(geometry, manoeuvres, spoken texts, speed limits per edge, lanes where tagged) to every display
showing it; each display tracks progress from the shared VSS position stream
(`Vehicle.CurrentLocation.*`, node GPS) with the same deterministic code, so two displays agree
and guidance survives a Brain drop (§8). Only one display, the **audio display** named in the
install configuration, speaks.

### 5.2 While Moving: the `map` template's next manoeuvre

Rendered by the shell, not the add-on, inside the `map` template's limits (UI spec §12.1: own
position, route, next manoeuvre; no free panning or search). The add-on fills one
`next_manoeuvre` payload; the shell draws it. The map style follows the map theme setting
([UI spec §13.5](2026-10-06-ui-architecture-design.md#135-map-theme-independent-of-the-app-theme-changes-123s-map-style-sentence),
proposed this round). Styling: `text-1` on `surface-glass`, arrow large,
no red card, no glow, gradient or animation (teardown §6; visual spec §1).

| Element | Rule |
|---|---|
| **Turn card** | Material Symbols arrow (`turn_left`, `roundabout_*`, `fork_*`, `merge`, `u_turn_*`, `straight`); distance in `type-num-xl`, stepped (500 m, then 50 m steps, then 10 m under 100 m); road or exit name ≤ 30 characters |
| **Then-preview** | one small arrow and distance, shown only when the following manoeuvre is ≤ 300 m after this one |
| **Lane arrows** | only where OSM has `turn:lanes`; ≤ 6 lanes; usable lanes `text-1`, others `text-3`; never colour alone |
| **ETA toggle** | one value: arrival time or time remaining; `ok` or a tap flips it (display state, not an action) |
| **Distance to go** | one `tiles` value beside the map, counted in the ≤ 6 budget |
| **Badge** | `NAV` (routed) or `TRACK` (following a line, §6.3), word plus icon |

Map camera follows the puck (the motion any moving map needs); zoom steps by speed and
flattens before a manoeuvre, in steps, never animated. Then-preview, lanes and the ETA toggle
read as parts of "next manoeuvre"; if the UI spec owner reads them as more, they come by
platform proposal (Decision 4).

### 5.3 Off route and reroute

Off route = > 30 m from the route for 3 fixes, or > 15 m and diverging for 2 (DMD's 20 m / 15 m,
widened for 1 Hz GPS). The shell shows one `alert_card`: **"Off route · rerouting in 8 s"**
with **Reroute** (focused) and **Keep route**; the seconds count down as text at 1 Hz, no bar.
On zero the focused choice applies. **This auto-confirm is allowed only because rerouting is
a navigation choice, not a car action**; ShellInput forbids it for anything that reaches the gate.
"Skip to next point" lives in the Drive menu (§5.6). If the engine fails, guidance keeps the
old route, retries every 30 s or 500 m, and says "No new route, keeping the old one" once.

### 5.4 Voice

Prompt text comes from the engine's localised spoken instructions; the add-on adds only fixed
phrases ("Off route", "You have arrived"). Voice reads manoeuvres, road names and warnings,
never people's names or messages (UI spec §12.1).

| TTS option | Licence (checked 2026-10-07) | Offline | Where |
|---|---|---|---|
| **Web Speech API** (`speechSynthesis`) | browser and OS voices, nothing shipped | when the OS has the voice installed (U per head unit) | the audio display |
| **Piper** | **GPL-3.0** (`OHF-Voice/piper1-gpl`; the old MIT `rhasspy/piper` says "development has moved"); embeds eSpeak NG; **each voice carries its own licence** | yes | the Brain, as a separate process |
| eSpeak NG | GPL-3.0 | yes, tiny, robotic | fallback |
| sherpa-onnx | Apache-2.0 runtime, runs Piper voices (still needs eSpeak NG data) | yes | alternative runtime |

**Recommend:** Web Speech in N1; Piper as an optional Brain component in N2 (GPL-3.0 combines
with our AGPL-3.0 distribution; run as its own process; ship only voices whose licence allows
redistribution, listed in third-party notices). Volume, mute and "voice off" are display
settings; mute is also a Drive-menu row.

### 5.5 Speed limit (off by default)

A setting, **Show speed limit**, off by default. When on: a limit roundel in the `map`
template corner from OSM `maxspeed` on the current edge (tagged values only; hidden when
untagged or the edge match is older than 2 s), and the speed tile takes the `warn` tint above
limit + a user tolerance (default + 10 %, ≥ 2 km/h). No sound, no `alarm`, no red. Speed-limit
state is **never logged, scored, recorded in Trips, shared or exported** (UI spec §12.2 "no
score"). Speed source honesty stands (GPS or ECU, labelled). **No speed cameras in v1**
(DMD2 research Decide 6).

### 5.6 Drive menu rows

The add-on contributes rows to the ShellInput Drive menu (`short_list`, ≤ 6 rows in total,
shell-chosen): **Mute voice**, **Skip to next point**, **End navigation** (Moving-safe, no
confirm; navigation only). Everything else (search, planner, library, profiles) is Parked.

## 6. GPX library, tracks and planner

### 6.1 Library

Stored on the Brain in `navigation.db` (SQLite, WAL) plus the original files, per user and
vehicle. Folders, tags, colour, show/hide on the map, draw order; per-file distance, ascent,
surface split and % ridden (computed on the device from Trips traces). A virtual **My trips**
folder lists Trips recordings read through the SDK `trips` service; **Use as route** copies a
trace into the library (recording stays Trips').

### 6.2 Import and export

**Import:** GPX 1.0/1.1, KML/KMZ, GeoJSON, TCX; FIT later (parser licence to check, U); the DMD
GPX extension read where present; OpenRally in N4 (format licence U). Content-sniffed, size-capped,
parsed in a worker, rejected unless it parses; batch import. Opening a shared map link or a file
on the phone hands it to the library. **Export:** plain GPX 1.1 per file and **Export library**
(a zip of GPX), offline; an optional `ostler:` GPX extension for profile and instructions
(Decision 6).

### 6.3 Follow a track

Three modes, chosen per file: **Turns** (map-match the track with the engine and guide by its
manoeuvres, for road tracks), **Line** (distance to the line, bearing and distance to the next
point, next-curve warning, for off-road), **Hybrid** (route to the nearest point, then Line).
Start from the nearest point; reverse direction; off-track alert > 30 m for 3 fixes, wrong
direction after 2. Line mode shows the `TRACK` badge and no lanes.

### 6.4 Waypoints, places and POIs

Destinations: search, a long-press on the map (Parked), core **Places** (home, work; read-only
here), **saved places** owned by this add-on (name, category, note), library waypoints, and
**priority waypoints** (≤ 3 starred, on an amber line in the `map` template's route only).
**Along the route** (N2): up to four POI categories (fuel, food, toilets, campsites) from the
region index, nearest ahead first, in a Parked list; while Moving only the next fuel distance as
a `tiles` value if chosen. Recent destinations: local, ≤ 20, clearable, can be turned off.

### 6.5 Planner (Parked)

In the add-on on phone, tablet and desktop, and on a head unit when Parked (task depth rules do
not apply Parked). Routes by stops and tracks by anchors (snap to road or free), drag to reorder,
cut, merge, reduce points, route ↔ track, profile per section, undo/redo, route info (distance,
ascent, surface split, off-road %). Saved plans land in the library and show on every display;
**Start on head unit** makes a plan the active route there.

### 6.6 Roadbook view (N4)

A roadbook generated from a route's manoeuvres (tulip, partial and total distance, CAP and
heading, waypoint n/N, trip meter nudge), and an OpenRally reader. While Moving it renders only
through templates: CAP and partials as `tiles` values and the tulip as the `map` template's next
manoeuvre; a dedicated `roadbook` template needs a platform proposal (Decision 9).

## 7. Curated routes, sharing and reports

- **Curated routes:** a library file with title, description, warnings, season, vehicle kinds,
  difficulty, off-road %, surface split. Publishing goes through **`ostler-app-hub`**
  ([community hub spec](2026-10-07-community-hub-design.md); H1 accepts track and trip files); the hub, not this add-on, holds moderation, licence choice
  (CC BY-SA 4.0 opt-in default for public routes, hub research §10) and completions. A
  completion (≥ 80 % coverage) is computed on the device; only the fact goes up, by choice.
- **Sharing levels:** a route **derived from a trip** follows the
  [trip-sharing spec](2026-10-07-trip-sharing-design.md) levels (L1 Route: ends trimmed 500 m, never < 200 m, privacy zones, simplified, no point times,
  public only by an explicit publish act ≥ 24 h after the trip). A **planned** route is clipped
  at core privacy zones by default and carries no times. Both share as the registry's `route`
  detail on `location` (proposed this round) to a person, group, ride, `link` or (by explicit
  publish) `public` audience.
- **Rides:** a ride leader may share the active route with the ride's group audience; it shows
  on members' maps (Vehicles & Map convoy layer); reroutes are not pushed.
- **Rider reports (later, N4):** one-tap closures and hazards (Drive-menu row while Moving, no
  text), sent over Social's link router, kept until "Gone" or expiry, with the reporter's id
  dropped and sending delayed until the reporter is ≥ 2 km away. Police and speed-camera reports
  never exist.

## 8. Data, privacy and offline behaviour

- **Routes are location data** (ADR-0009): the library, recent destinations, the active route and
  ETA stay on the user's devices and leave only through a registry grant or a hand-over. Sharing
  an ETA with a ride is a `location` grant at that ride's window; the destination is never sent
  unless shared.
- **No navigation history** beyond recent destinations; guidance state is not written to
  Trips; speed-limit state never stored (§5.5). Exit guarantee: Export library (§6.2).
- **No identity:** no VIN, `vid` or plate in any exported or published route (ADR-0036).
- **Offline:** with a region installed, search, routing, guidance and voice (Web Speech where the
  OS voice is local, or Piper) work with no internet. **Brain unreachable:** displays keep the
  cached route and keep guiding while a position source remains (the node's stream, or the
  display's own GPS on a phone; how a head unit reaches the node without the Brain is U);
  rerouting and search show "Needs the Brain". **No region:** the
  map uses the online fallback and routing shows an install card. **Node-only or phone-only**
  (Ostler Diagnostics alone): the add-on is unavailable in v1 (`needs_brain`; Decision 8).

## 9. Manifest sketch

```jsonc
{ "id": "ostler.navigation", "name": "Navigation", "trust": "first_party", "kind": "addon",
  "source": { "repo": "https://github.com/openostler/ostler-app-navigation",
              "license": "AGPL-3.0-or-later", "publisher": "openostler" },
  "hosts": ["head_unit", "phone", "desktop"],
  "requires": { "api": ["garage.read", "trips.read", "places.read"],
                "signals": ["Vehicle.CurrentLocation.Latitude", "Vehicle.CurrentLocation.Longitude",
                            "Vehicle.CurrentLocation.Heading", "Vehicle.Speed"] },
  "contributes": { "slots": [ { "slot": "more:navigation", "view": "library" } ],
                   "drive_menu": ["mute_voice", "skip_point", "end_nav"] },
  "actions": [],
  "views": [
    { "id": "guide",   "needs_brain": false,
      "driving": { "parked": "full", "idling": "full",
                   "moving": { "template": "map", "layer": "next_manoeuvre" } } },
    { "id": "library", "needs_brain": true, "driving": { "parked": "full", "idling": "full", "moving": false } },
    { "id": "planner", "needs_brain": true, "driving": { "parked": "full", "idling": false, "moving": false } } ],
  "permissions": { "data": ["location", "trips"], "storage": "server" } }
```

`more:navigation` and `contributes.drive_menu` are new platform names (Decision 10), added the
way app model §14.7 added `more:vehicles`. A Home card (`home:card`) offers "Navigate home".

## 10. Phases

| Phase | Ships | Depends on |
|---|---|---|
| **N0 Seams** | `next_manoeuvre` payload in the `map` template; region manager hooks; `drive_menu` contributions; Valhalla build and route timing on the Pi 5 bench (measured, recorded in `references/`) | U2 templates, V1c regions, ShellInput (U2) |
| **N1 Route and guide** | search, Fast/Scenic/Unpaved profiles, turn card, ETA, off-route card, Web Speech voice, recent destinations, GPX import/export, Drive-menu rows | N0 |
| **N2 Tracks and planner** | library, follow track (Turns/Line/Hybrid), planner, saved places, along-route POIs, lanes, Piper voice, speed-limit option | N1 |
| **N3 Off-road and sharing** | Off-road/4x4 profile, legality overrides, optional BRouter adapter, curated routes, share to `ostler-app-hub`, ride routes | hub H1, registry `route` detail and `link` audience, Social rides |
| **N4 Roadbook and reports** | roadbook view and generator, OpenRally reader, rider reports over Social's transport | N3; Social router |

## 11. Tests

- The Moving `map` template carries only the `next_manoeuvre` fields above; no search field, list,
  pan or text entry exists in the DOM while Moving (Playwright, each head-unit class).
- Two displays given the same route and position fixture show the same manoeuvre and distance.
- Off-route fixture: the card appears after 3 fixes, Reroute is focused, the countdown applies it;
  a gate action fixture never shows a countdown (shared ShellInput test).
- Brain killed mid-route with a position fixture still flowing: guidance continues to the
  destination on the cached route.
- Speed-limit off: no roundel, no tint. On: tint above tolerance; nothing written to the
  recording, the summary index, exports or shares (file and index diff).
- No route outside the user's devices without a grant (fake registry); a shared planned route is
  clipped at privacy zones and has no `<time>` elements.
- Import: malformed, oversized and zip-bomb files are refused; each format round-trips to GPX.
- Profiles never route over `access=private` without the override (graph fixture).
- Licence notices list Valhalla, any BRouter build, Piper and each shipped voice.

## Changelog

- 2026-10-07: v0.1, draft (DMD round): one `ostler-app-navigation` add-on, Valhalla on the Brain,
  regions shared with the visual spec, guidance through the `map` template, voice, library,
  planner, roadbook, sharing hooks, phases N0–N4.

## Decisions for the owner

1. **One navigation add-on?** Recommend: yes, `ostler-app-navigation`, absorbing routes and
   roadbook. Alternative: separate `ostler-app-routes` (library, planner) and navigation.
2. **Engine?** Recommend: Valhalla (MIT, per-request profiles, map matching, spoken texts) behind
   an adapter, BRouter optional for off-road. Alternative: BRouter only (lighter, best off-road,
   no lanes, weaker turn text).
3. **Where guidance runs?** Recommend: routes on the Brain, guidance on each display from the
   whole route. Alternative: guidance on the Brain streamed to displays (one source, dies with
   the Brain).
4. **Turn card contents while Moving?** Recommend: arrow, stepped distance, name, then-preview,
   lanes, one ETA value, read as "next manoeuvre" in the `map` template. Alternative: arrow and
   distance only until a platform proposal widens the template.
5. **Voice?** Recommend: Web Speech in N1, optional Piper (GPL-3.0) on the Brain in N2.
   Alternative: Piper from N1 for consistent offline voices.
6. **Our own GPX extension?** Recommend: write plain GPX 1.1, an `ostler:` extension only for
   profile and instructions, documented. Alternative: plain GPX only.
7. **Search?** Recommend: own SQLite FTS5 index per region. Alternative: Photon or Nominatim on
   the Brain (better ranking, a heavy extra service).
8. **Navigation without a Brain?** Recommend: not in v1. Alternative: GPX follow (Line mode) on
   the phone with Ostler Diagnostics alone.
9. **Roadbook while Moving?** Recommend: through `map` and `tiles` until a `roadbook` template is
   proposed with cited limits. Alternative: Parked and phone only.
10. **New platform names?** Recommend: slot `more:navigation` and manifest
    `contributes.drive_menu`. Alternative: Navigation under More → Vehicles and no Drive-menu rows.
11. **Speed limit?** Recommend: sign and `warn` tint, off by default, never logged or scored; no
    cameras. Alternative: leave speed limits out entirely.
12. **Off-road legality?** Recommend: never route on private or non-vehicle ways without a
    per-route override and the warning. Alternative: no override at all.
