---
title: "App teardown — Speedometer: Driving Tracker (now Odo), screen by screen, mapped onto Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/ui/obd_apps.md, references/research/ui/head_unit_ui.md, references/research/addons_catalogue.md, references/research/features_backlog.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md]
summary: >
  The owner's main UI reference, torn down. Speedometer: Driving Tracker (App Store id6759611784, one
  developer, renamed Odo in v4.0.0 on 2026-10-06) is an iPhone/iPad/Mac/CarPlay trip tracker with OBD-II,
  route replay coloured by speed, trip stats, time-at-speed, all-time statistics, sprint records, a garage
  of costs, friends and convoys. This note lists every feature, breaks down each screenshot screen (layout,
  type, colour, map, controls), maps each feature onto Ostler (core Trips, Drive mode, Maintenance &
  Garage, Vehicles & Map, Social) with the data it needs and whether the repo already has it (it has more
  than the owner may think: 1/2/4/8x replay, speed-coloured traces, GPS altitude, IMU and GPS g), and
  ends with Styling and Copy / Avoid / Decide.
---

# App teardown: Speedometer: Driving Tracker (now "Odo")

The owner's favourite driving app, read from its App Store listing, its version history, the developer's
site and the two screenshots the owner supplied. Facts were checked live on **2026-10-07**; **(U)** marks
anything not verified. Related notes: OBD-app patterns in [ui/obd_apps.md](ui/obd_apps.md), head-unit rules
in [ui/head_unit_ui.md](ui/head_unit_ui.md), add-on ideas in [addons_catalogue.md](addons_catalogue.md),
the backlog in [features_backlog.md](features_backlog.md). This note does not repeat them.

## 1. The app in one paragraph

A one-person indie app (seller Taohidul Islam, who also makes step and sleep trackers), Navigation
category, 4.9 stars from 196 ratings, 103.9 MB, iOS/iPadOS 18.6+, macOS 15.6 (Apple silicon), visionOS,
CarPlay, Watch and Live Activities, 36 languages. Version **4.0.0 (2026-10-06) renamed it "Odo:
Speedometer, Drive & Ride"** and added turn-by-turn navigation and Convoy. The version history shows a
release every few days from May to October 2026 (3.5 → 4.0), each with long, plain-language notes. It
started as a GPS speedometer and trip logger and grew OBD-II (3.7, May 2026), a channel replay cockpit
(3.11), a friends board (3.19), trip photos and route history (3.25). Free core; Premium is **$7.99 a
month, $29.99 a year, $39.99 lifetime** (the brief's $19.99 a year is out of date).

## 2. Every feature (grouped as the listing groups them, plus the history)

| Group | Features |
|---|---|
| **Automatic trips** | Start/stop by motion detection, CarPlay connect or Bluetooth; Shortcuts automations (CarPlay, Bluetooth, NFC, Focus, Action Button, time); auto-pause, auto-end after a configurable idle, pause limit that rolls the end back to the start of the break; "Ignore early stops" up to 10 min for flaky links; auto-detect threshold 3–30 s (default 8); "Trip started" banner; pause auto-start for a passenger ride (30 min / 1 h / 2 h); auto vehicle match by CarPlay stereo, Bluetooth or VIN; tags, saved places (150 m radius), auto-tag rules incl. "pass through a saved place"; favourites; merge and split up to 10 trips; ignore or exclude a trip from stats |
| **Live speedometer** | Digital, analog, map and windshield HUD (mirrored) modes; 50+ gauge designs incl. an animated "Open Road" day/dusk; mph, km/h, knots, m/s; a 6-stat grid under the gauge (any order, incl. live OBD); stats text size S–XL; speed-limit alerts (haptic, audible, presets, 1 s threshold, repeat 1–5 s, mute 1 h, violations history); Picture in Picture speed window over other apps; Dynamic Island, Live Activity (16 presets, custom editor, refresh 1–30 s), Home and Lock Screen widgets; keep screen awake; GPS quality chip; video record button |
| **Trip detail** | Start/end places and times; distance, avg speed, max speed, duration, idle, moving, elevation gain, stops, avg moving speed; estimated fuel cost from the last fill-up price; turns left/right; peak g, acceleration and braking trends; Sustained Best (fastest 30 s average) instead of a GPS spike; time-at-speed donut (Time / Distance); speed over time, elevation profile and g-force charts, each full-screen with scrub, zoom and "moments that stood out"; distance by hour; segments; personal-record badges only when held; a "This Route" card ranking the drive among runs of the same route; on-device text summary with a "vs usual" chip; reorderable and hideable sections |
| **Replay** | Route Playback full-screen on the map, heading-up or north-up, speed-coloured trace, arrow or dot marker, time-of-day readout, copy coordinates, 1x/2x/4x/8x; elevation playback (route coloured by altitude); Max Speed Replay ("Max Speed Reel", jumps to the fastest stretch); Trip Reel (animated replay video to share); Channel Replay cockpit (speed and RPM arcs, signed g dial, throttle/load/boost bars, elevation strip with playhead, haptic peaks); follow a past route on the live map with ahead/behind score |
| **Statistics** | All-time max speed hero with place and date; totals (distance, trips, time, moving, idle, avg/max distance and duration, avg speed); speed distribution (trips by max speed band); Speed Records, Max Speed Records, sprint records; lifetime stats, top-speed medals, most-visited cities; daily/weekly/monthly maps of every route (pooled speed bands); activity clock (24 h ring); year heatmap; compare two trips head to head (crown on each winning stat); Monthly Recap share card |
| **Sprints** | 0–60 mph, 0–100 km/h and custom ranges (0→60/80/100 km/h in the screenshot); ranked list per band with gold/silver/bronze, delta to the best, peak speed, date; works in every unit; trace coloured by the same ramp as the map |
| **Garage** | Multiple vehicles (photo, plate, VIN editable, NHTSA year/make/model decode), last parked spot (not live tracking, says so); total vehicle cost hero; this-month donut fuel / maintenance / expenses with month-on-month change; spending tiles with + Add; Insights (vs year average, top spending, costliest month); fuel log with partial fills, This Tank card, pence-per-litre, pump/charger display scan by camera, station recognition and nearby stations; EV charging and efficiency; fuel level estimated from logs when the car does not report it (labelled estimate); maintenance with reminders by date or mileage counted from the last service; expenses with custom types; insurance/registration documents with expiry reminders; attachments; quick-log from the app icon; CSV import (incl. Spritmonitor) |
| **OBD-II** | ELM327 BLE/Wi-Fi with a setup wizard and per-vehicle protocol memory; live RPM, coolant, oil, fuel, battery, throttle, MAF, intake/ambient, boost, instant economy, O2/wideband AFR; gauges with the healthy range marked and a "what this means" sheet; DTCs stored/pending/permanent with freeze frame, plain-language text, web search, recurring-code highlight; readiness and Mode 06; Torque-style custom PIDs and presets; per-second OBD charts per trip (gaps over 15 s break the line, not smoothed); lifetime fuel, engine hours, cold starts; 12 V charging check; adapter diagnostics; PDF report for the mechanic; up to about 5 Hz on good adapters |
| **CarPlay** | Tabbed layout (Live, Map, Trips, Places, OBD, More), reorderable, choose the opening tab; a grid layout of rounded-square stat tiles; dashboard and instrument-cluster widgets; OBD and custom PIDs; speed alerts; map with 3D and Dark/Muted styles; convoys |
| **Navigation (4.0)** | Turn-by-turn from Apple Maps or OpenStreetMap; "your usual road" and own past routes offered; live ahead/behind vs your usual time; stops for fuel/food; avoid tolls/highways/ferries or a long-pressed spot |
| **Friends and Convoy** | Sign in with Apple only for this; daily totals only leave the phone, mutual accept, routes and places never uploaded; boards for today/week/custom period; **speed is never ranked**; Convoy live map with meeting point and arrival alerts, locations deleted when it ends, speed sharing optional; starting a convoy is Premium, joining is free |
| **Record and share** | Dashcam-style video with a live speed overlay up to 4K, reasons shown when a recording stops early; trip photos (up to 20, placed on the drive by capture time); share cards with or without the map; route privacy hides the start and end and place names; GPX/CSV/PDF import and export, automatic export on trip end (free); backup and restore; Mac review via iCloud |
| **Privacy claims** | No account to track trips; data in the user's own iCloud. The developer's site claims no ads and no advertising identifier, yet the App Store label lists a device ID "linked to you" for the developer's advertising and analytics. Treat the privacy story as good but not clean |

**Not verified in the current listing:** a true 3D *route playback* (the listing has a 3D *map* view in Map,
navigation and CarPlay; the brief's "3D playback" may be that) **(U)**; the exact Premium split. The
developer's earlier copy put route playback and max-speed playback behind Premium, but 3.21 made replay
video and Max Speed Replay in the share menu free, and automatic export is free. Only "starting a convoy
is Premium" is stated outright today.

## 3. Screen by screen (from the two screenshots)

Both images are App Store marketing frames: a short centred white caption on a deep navy gradient above a
phone, which helps read the screens but is not the app itself.

### 3.1 Bottom navigation (every screen)

Five tabs in a **floating pill bar** inset from the screen edges, dark translucent fill, thin icons over
tiny labels: **Garage** (crossed spanner and screwdriver), **Trips** (a road in perspective),
**Speedometer** (gauge), **Stats** (bar chart; "Statistics" on the sprint frame), **Settings** (cog). The
active tab gets a filled rounded-rectangle highlight in a darker teal-blue, with the icon tinted cyan.
Speedometer sits in the middle. Tab order is user-reorderable (3.23) and Statistics became a permanent tab
in 3.25.

### 3.2 Live speedometer ("See Your Drive Live & Accurate")

- **Top row:** a square video-record button on the left, a centred GPS quality chip (green signal bars and
  "Excellent"), a square settings cog on the right. Both buttons are dark rounded squares.
- **Hero:** an analog dial 0–300 km/h on a ~270° arc, ticks every 25 with small grey numerals. The arc
  is filled from zero to the current speed with a green → yellow-green gradient; a thin white needle; the
  digital value **90** in large bold white inside the dial with "km/h" small beneath. A compass chip
  ("NE") sits under the dial.
- **Stats block:** a centred two-column list of six small rows, each a tiny line icon, a grey label and a
  white value: Avg 72 km/h, Time 1:32:15, Dist 111 km, Max 108 km/h, Max G 0.42 G, Alt 245 m.
- **Controls:** two pill buttons near the bottom, **Pause** (orange fill) and **Stop** (red fill), with
  white icon and text.
- **Background:** a vertical navy gradient (near-black at the top to blue-navy), no cards. Most of the
  screen is empty dark space; the dial and its value are the only bright things.

### 3.3 Route playback ("Replay Your Route, Relive the Moment")

- **Map:** full-bleed, a dark-styled street map (navy water, slate land, muted grey labels, small white
  POI pins), the "Maps" attribution bottom left. The route is a thick line, **coloured by speed** (green
  slow → yellow → orange → red fast) with a dark casing; a red end marker and a bright heading marker.
- **Top bar:** floating translucent chrome: close (×) left, "Route Playback" title centred, map-type and
  recentre buttons right.
- **Bottom sheet:** a frosted dark card over the lower third. A big **52 km/h** readout (value bold, unit
  small), then one row of three small stats with icons: altitude 191 m, 0.02 g, distance 25.9 km. A thin
  cyan scrubber with a white thumb, elapsed time left and remaining time (negative) right in tiny grey
  digits. Then **1x 2x 4x 8x** chips (selected chip filled cyan), a large circular cyan **pause/play**
  button in the centre, and a restart icon on the right.

### 3.4 Trip detail ("Detailed Speed & Distance Insights")

- **Header:** back chevron left, date "Feb 19, 2026" centred, share and "…" round buttons right. Below,
  a two-stop itinerary: green dot + start place, red dot + end place, and a grey line with the date and
  "4:51 AM – 5:29 AM".
- **Stats grid card:** 3 × 3 cells, no dividers. Each cell: a tiny tinted icon and an **uppercase micro
  label** in grey (DISTANCE, AVG SPEED, MAX SPEED / DURATION, IDLE, MOVING / ELEVATION, STOPS, AVG MOVING),
  then a bold white value with a dim small unit (55.5 km, 88, 168 / 38m, 6m, 32m / 180 gain, 2, 103).
- **Time at Speed card:** title plus "km/h" subtitle, a **Time | Distance segmented toggle** top right. A
  thick donut on the left with "38m Total" in the centre, five arcs; a legend on the right, one row per
  band with a coloured dot, the band (0–40, 40–80, 80–120, 120–160, 160+), the time and the share (13%,
  29%, 38%, 18%, 2%). The band colours run blue, green, yellow, orange, red.
- **Speed Over Time card:** title with an expand icon; a line chart with a light grid, y-axis 50–200, the
  line coloured by speed with a soft gradient fill below it.
- Cards are dark navy rounded rectangles (~16 px radius) slightly lighter than the background, with no
  borders.

### 3.5 Statistics ("Explore Your Trip History")

- **Header:** "Statistics" centred, a filter button top right.
- **Hero card:** "ALL-TIME MAX SPEED" in spaced uppercase, **186 km/h** very large and bold, a sub-line
  with the road ("Highway A8") and date.
- **Totals grid:** 3 × 3 like the trip grid: total distance 8420 km, total trips 247, average distance
  34.1 km / average duration 38m, total time 156h 18m, average speed 54 / moving 141h 24m, idle 14h 54m,
  max distance 312.
- **Speed Distribution:** title and subtitle ("Number of trips by max speed reached"), a vertical bar
  chart with six bands 0–30 … 150+, each bar its own colour: green, cyan, blue, yellow, orange, red.
- **Browse:** a list row "Speed Records" with a lightning icon and a chevron (into the records and sprint
  screens).

### 3.6 Garage ("See Your Total Vehicle Cost")

- **Hero card:** "TOTAL VEHICLE COST", **15K $**, sub-line "This Year: 4.3K $".
- **This Month card:** a donut with "342 $" in the centre (fuel orange, maintenance blue, expenses green)
  and a legend with value and share (180 $ 53%, 120 $ 35%, 42 $ 12%); top right a green "↘ 10% vs last
  month" (down is good, so green).
- **Spending:** three tiles (Fuel 8.4K, Maintenance 3.8K, Expenses 2.5K), each with a coloured icon and a
  full-width **+ Add** button in its own colour (orange, blue, green), and a chevron to the log.
- **Insights:** list rows with icon, label, value and a right-aligned note: vs year average −5% (avg 361
  $/mo), top spending Fuel (52% of this month), costliest month Dec 2025 (892 $).

### 3.7 Sprint Records ("Acceleration & Sprint Records", second image)

- Back chevron and "Sprint Records" title. One card per band: a lightning badge, **"0 → 60 km/h"** bold,
  "4 sprints · Avg …" in grey. Ranked rows inside: a round rank badge (gold 1, silver 2, bronze 3, grey 4),
  the time large (**3.82 s**; others show a "+0.23s"-style delta to the best), date and time small, the
  peak speed right-aligned ("68 km/h Peak") and a chevron. Then 0 → 80 (5.41, 5.78, 6.12 s) and 0 → 100
  (6.91 s, peak 112).
- The tab bar on this frame shows the **Statistics** tab active and a red-tinted Garage icon (a badge, or
  a reminder due **(U)**).

### 3.8 Screens not in the screenshots (from the history; layout unverified)

CarPlay Live grid of rounded-square tiles; Channel Replay cockpit; full-screen chart pages; Compare Trips;
Route History; Friends boards; the OBD gauge pages with the healthy range drawn; the dashcam recorder with
a speed overlay; widgets and Live Activities. All **(U)** for exact layout.

## 4. What Ostler already has (checked in the repo, 2026-10-07)

The owner's sense that Ostler lacks this is half right: the *data and mechanics* are largely there; the
*presentation* is not.

| Capability | In Ostler today | Where |
|---|---|---|
| Trips as recorded sessions, auto start/end on connect or idle | Yes | [recorder.py](../../src/openostler/logbook/recorder.py) (ADR-0009, ADR-0011) |
| Per-trip duration, distance, max speed | Yes, in meta and the SQLite index | [index.py](../../src/openostler/logbook/index.py) |
| GPS lat/lon, speed, heading, **altitude**, sats, HDOP per row | Yes (`GPS_Altitude` etc.) | [channels.py](../../src/openostler/logbook/channels.py), [nmea.py](../../src/openostler/gps/nmea.py) |
| Longitudinal and lateral g | Yes: GPS-derived and Pi IMU / phone, levelled to the vehicle frame | [motion.py](../../src/openostler/logbook/motion.py), [imu/](../../src/openostler/imu) (ADR-0010) |
| Replay with play/pause, ±10 s, scrubber, **1×/2×/4×/8×** | Yes, the same four speeds | [playback.ts](../../ui/src/state/playback.ts), [Transport.tsx](../../ui/src/components/replay/Transport.tsx) |
| Map trace **coloured by any channel**, legend, two traces A/B, CVD-safe ramps and a "classic" blue → red | Yes | [trace.ts](../../ui/src/components/replay/trace.ts), [TraceMap.tsx](../../ui/src/components/replay/TraceMap.tsx) |
| g-g friction-circle panel, charts, notes, audio | Yes | [GGPanel.tsx](../../ui/src/components/replay/GGPanel.tsx), [Chart.tsx](../../ui/src/components/replay/Chart.tsx) |
| Session browser, filters, month scrubber, **year heatmap**, histogram API | Yes | [SessionBrowser.tsx](../../ui/src/components/replay/SessionBrowser.tsx), [YearHeatmap.tsx](../../ui/src/components/replay/YearHeatmap.tsx) |
| Start/end place names (offline, then OSM) | Yes | [geo/](../../src/openostler/geo), [places.py](../../src/openostler/logbook/places.py) |
| GPX / VBO / CSV export | Yes | [export.py](../../src/openostler/logbook/export.py) |
| Analog gauge with normal band | Yes (240° sweep) | [Gauge.tsx](../../ui/src/components/Gauge.tsx) |
| Dark theme | Yes, but neutral grey (`#0e1012` bg, `#4f8ce8` accent) | `ui/tokens/color.dark.tokens.json` |
| **Dark basemap** | **No**: OpenFreeMap "liberty" (light), streets/satellite/hybrid | [maplibre.ts](../../ui/src/components/replay/maplibre.ts), [basemap.ts](../../ui/src/components/replay/basemap.ts) |
| Avg/moving/idle time, stops, elevation gain, avg moving speed, time-at-speed, sustained best, turns | **No** (computable from rows) | — |
| All-time statistics, speed distribution, records, sprints | **No** (index has the columns to start) | — |
| Costs, fuel log, service reminders | **No** | Maintenance & Garage add-on |
| Video with overlay, share cards, route privacy on share | **No** | — |

Two data caveats specific to us: on the Td5, a K-line SLABS session holds one module at a time, so road
speed during most trips is **GPS speed** (UI spec §3.5); and the node's GPS today is a ~1 Hz NMEA receiver,
which is too coarse for honest sprint times (a 4 s sprint is four samples). The 10 Hz u-blox
([addons_catalogue.md](addons_catalogue.md), ADR-0039) plus the IMU fixes that. Fuel level and fuel used
from the Td5 ECU over diagnostics are unproven for this pack **(U)**, so cost-per-trip needs logs.

## 5. Mapping every feature onto Ostler

Homes: **Trips** (the core app, Logs renamed), **Drive** (the full-screen mode, UI spec §3.5),
**Maintenance & Garage** (add-on), **Vehicles & Map** (add-on), **Social** (add-on), **Diagnose** (core),
**Shell** (platform). Data: ✔ have, ◐ derivable from what we record, ✘ new.

| Feature | Home | Data needed | Have? |
|---|---|---|---|
| Live speed hero + 6-stat grid (avg, time, distance, max, max g, altitude) | Drive (`tiles` template) | speed, trip accumulators, g, alt | ✔ speed/alt/g; ◐ running avg/max |
| Analog/digital/HUD modes, gauge skins | Drive; skins as an add-on later | same | ✔ Gauge; ✘ HUD mirror, skins |
| GPS quality chip | Shell status strip | sats, HDOP, fix | ✔ |
| Pause / Stop a trip | Trips (control), Drive (one button) | recorder control | ◐ recorder is automatic; no manual pause |
| Speed-limit alerts | Drive (alert card template) | limit source (OSM maxspeed or user preset) | ✘ |
| Auto trip start/end, early-stop protection, ignore/exclude trip | Trips | connect/motion/idle | ✔ start/end; ✘ exclude-from-stats flag |
| Route playback, speed-coloured, 1–8x, heading-up | Trips (Analysis/replay) | track + speed | ✔ (needs dark map, heading-up, bottom-sheet layout) |
| Max-speed replay (jump to fastest stretch) | Trips | max speed index in rows | ◐ |
| Elevation-coloured playback | Trips | `GPS_Altitude` | ✔ (pick the channel; already works) |
| Channel Replay cockpit (RPM, speed, g, throttle, elevation strip) | Trips (replay "cockpit" view) | ECU channels + GPS + g | ✔ data when the engine was in session; ◐ view |
| Trip stats grid (distance, avg, max, duration, idle, moving, elevation gain, stops, avg moving) | Trips | rows | ✔ three; ◐ the other six |
| Time-at-speed donut (Time / Distance) | Trips | speed per row, dt, distance per row | ◐ |
| Speed over time, elevation, g charts with scrub | Trips | rows | ✔ Chart; ◐ full-screen pages |
| Sustained best (30 s), turns, accel/braking trends | Trips | speed, heading, g | ◐ |
| Start/end places, itinerary header | Trips | places | ✔ |
| Trip photos placed on the drive | Trips (later) | photo time → row | ✘ |
| This Route / route history / follow a past route | Trips; follow-route live in Drive | start/end clustering | ◐ |
| On-device trip summary text | Trips (optional, later) | stats | ◐ (keep numbers primary) |
| All-time max speed hero, totals grid | Trips → Statistics view | index columns | ◐ |
| Speed distribution, speed records | Trips → Statistics | max speed per trip | ✔ data; ◐ view |
| Year heatmap, activity clock, all routes on one map | Trips → Statistics | index, tracks | ✔ heatmap; ◐ others |
| Compare two trips | Trips | two sessions | ✔ two-trace A/B exists; ◐ stat-by-stat compare |
| Sprint records 0→60/80/100, custom bands, ranked | Trips → Statistics → Records | ≥ 10 Hz speed or IMU | ◐ 1 Hz GPS too coarse; ✘ until the u-blox |
| Garage list, photo, plate, VIN | Shell garage (UI spec §4.1) | identity (masked VIN, ADR-0036) | ✔ partly |
| Last parked spot | Security (parked) / Vehicles & Map | last fix | ✔ (better: the node is in the car, so it is real tracking, ADR-0009 rules) |
| Total cost hero, monthly donut, spending tiles, insights | Maintenance & Garage | user-entered costs | ✘ |
| Fuel log, partial fills, economy, estimated trip cost | Maintenance & Garage | fills + odometer; trip distance | ✘ fills; ✔ distance |
| Service reminders by date/distance (and engine hours) | Maintenance & Garage | odometer, engine hours | ◐ distance from trips; ✘ odometer read **(U)** |
| Documents with expiry reminders | Maintenance & Garage | user files | ✘ |
| OBD live gauges with healthy range, DTCs, freeze frame, readiness, PDF report | Diagnose (core) | pack + generic OBD-II (ADR-0031) | ✔ mostly; ◐ PDF report |
| Recurring-fault highlight, 12 V charging check | Diagnose / Maintenance | fault history, battery V | ◐ |
| CarPlay grid, cluster widgets | Drive templates; thin CarPlay/Android Auto companion later | same as Drive | ✘ companion |
| Live Activity / widgets / PiP | Phone build only (app-model spec §7.1) | live snapshot | ✘ |
| Turn-by-turn navigation | Not core; a Navigation add-on or hand off to an OSM app | routing | ✘ (avoid building) |
| Friends boards (totals only, speed never ranked) | Social | daily totals | ✘ |
| Convoy live map, meeting point, arrivals | Vehicles & Map (map) + Social (group) | live position, opt-in | ✘ |
| Dashcam video with speed overlay | Cameras add-on; overlay drawn from session rows | video + rows | ✘ video; ✔ rows |
| Share cards, Trip Reel, route privacy on share | Trips (share), Social | track, stats | ✘ |
| GPX/CSV import/export, auto-export on trip end | Trips | sessions | ✔ export; ✘ import, auto-export |
| Shortcuts automation | Ostler equivalent: automations over MQTT/HA (More → Integrations) | events | ◐ |

## 6. Styling

**What it looks like.** One dark, blue-tinted world: navy gradients (near-black to deep blue) instead of
neutral grey; cards a step lighter navy, ~16 px radius, no borders; white primary text, grey secondary,
spaced uppercase micro-labels above every number; huge bold hero numbers with a small dim unit; a cyan
accent for the active tab, the scrubber and the play button; one **semantic speed ramp** used everywhere
(green → cyan/blue → yellow → orange → red for slow → fast) on the trace, the donut, the distribution bars
and the chart, plus category colours in the garage (fuel orange, maintenance blue, expenses green); gold,
silver and bronze for ranks. Floating chrome over full-bleed maps; frosted bottom sheets; a floating pill
tab bar. Icons are thin line icons with small tinted squares behind them in stat cells. Density is
generous: one idea per card, at most a 3 × 3 grid.

**What to borrow.**
1. A navy-tinted dark palette as Ostler's dark theme (the tokens already split light/dark; only values
   change, `ui/tokens/color.dark.tokens.json`).
2. A **dark vector basemap** for replay and Drive (an OpenFreeMap or self-hosted dark style; offline PMTiles
   later), with the trace as the brightest thing on screen.
3. The **hero → grid → card** hierarchy for every summary screen: one big number, a 3 × 3 grid of
   label-over-value cells, then one chart per card.
4. **One speed ramp shared** by map, chart, donut and histogram, so a colour means the same speed
   everywhere. Ours is CVD-safe plasma by default; keep that, but offer the classic green → red as the
   owner's preferred look (the "classic colours" switch already exists).
5. Replay as **map + bottom sheet**: readout, scrubber, speed chips, big play button.
6. Uppercase micro-labels with the unit dimmed beside the value (our `.kicker` is close).

**Do not borrow.** Thin grey 9–10 px labels (fail our head-unit sizes, head_unit_ui §1); the floating
pill tab bar on a head unit (our driver-side rail stays, UI spec §3.3); colour as the only carrier of
meaning (pair the ramp with a legend and numbers, as we do).

## 7. Copy / Avoid / Decide for Ostler

### Copy

| # | Item | Maps to |
|---|---|---|
| C1 | Trip detail as hero itinerary + 3 × 3 stats grid (distance, avg, max, duration, idle, moving, elevation gain, stops, avg moving) + time-at-speed donut with a Time/Distance toggle + speed-over-time chart | Logs/Trips destination, UI spec §3.4; session-logbook spec |
| C2 | Replay layout: full-bleed dark map, speed-coloured trace, frosted bottom sheet with readout, scrubber and our existing 1/2/4/8× chips; heading-up option; "jump to max speed" | ADR-0010; replay spec |
| C3 | A Statistics view inside Trips: all-time max hero, totals grid, speed distribution by max-speed band, records list, our year heatmap | UI spec §3.4 (Logs); logs-at-scale spec |
| C4 | One speed ramp everywhere and a legend on every coloured thing | trace.ts; UI spec §2 principles |
| C5 | "Sustained best" (best 30 s average) shown beside the raw max, and gaps drawn as gaps, never smoothed | CONSTITUTION data honesty; ADR-0006 |
| C6 | Exclude a trip from stats (tow, test drive, passenger) without deleting it | session-logbook spec |
| C7 | Garage costs screen shape (total hero, monthly donut, + Add tiles, plain insights) for the Maintenance & Garage add-on; reminders counted from the last service, by distance, time and engine hours | addons_catalogue; app-model spec §3 |
| C8 | Friends boards show totals only and **never rank speed**; convoy locations deleted when the convoy ends | ADR-0029; accounts spec §6 |
| C9 | Route privacy on anything shared: trim start/end and hide place names by default | ADR-0009; accounts spec §5.3 |
| C10 | Estimates labelled as estimates (fuel level from logs, trip cost from last fill) | ADR-0006, ADR-0008 |

### Avoid

| # | Item | Why / maps to |
|---|---|---|
| A1 | Building turn-by-turn navigation | Huge scope, not our data; hand off to an OSM app. App-model spec §8 non-goals |
| A2 | A paywall on replay or history | Ostler is AGPL and local; the app itself walked replay back to free. ADR-0012 |
| A3 | Speed-limit "violations history" and any speed leaderboard | Liability and the wrong incentive; ADR-0029 social rules |
| A4 | Single-number peaks from 1 Hz GPS (sprints, max speed) presented as precise | Data honesty; wait for 10 Hz GNSS / IMU (ADR-0039) |
| A5 | Rich screens on the head unit while moving (charts, lists, scrubbing) | UI spec §3.5, app-model spec §4.4 templates |
| A6 | Privacy claims the data labels contradict | Our "location never leaves the device" (ADR-0009) must stay literally true |
| A7 | 50 gauge skins in core | Skins are an add-on concern; core ships one good gauge |

### Decide (recommendations for the owner)

| # | Question | Recommendation |
|---|---|---|
| D1 | Should Ostler's dark theme move from neutral grey to a navy-tinted palette like this app's? | **Yes**: change the dark token values only (same names), keep contrast tests; light theme unchanged. UI spec §10.1 tokens |
| D2 | Default basemap for replay and Drive | **A dark vector style by default in dark theme**, streets/satellite/hybrid still switchable; offline tiles later. ADR-0009/0010 basemap rules |
| D3 | Default speed ramp: our CVD-safe plasma, or the app's green → red? | **Keep plasma as default**, make "classic" green → yellow → red one tap in the legend, and use the chosen ramp for donut, histogram and chart too |
| D4 | Where Statistics and Records live | **Inside Trips** (a Statistics tab of the destination), not a sixth destination; the five-destination cap stands (UI spec §3.4) |
| D5 | Ship sprint records before the 10 Hz GNSS? | **No**: compute them only when ≥ 10 Hz speed or a calibrated IMU is in the session; otherwise show "needs fast GPS" |
| D6 | What runs in Drive while moving | **The `tiles` template with speed hero + 6 stats, and a map template** (the proposed richer set), nothing else; replay, stats and charts are parked-only on the head unit |
| D7 | Costs, fuel and reminders: core or add-on? | **Maintenance & Garage add-on**, with the core exposing trip distance and engine hours as data it can read |
| D8 | Video with speed overlay | **Cameras add-on**, overlay drawn from session rows at export time (no burn-in on record); after the dashcam spec |
| D9 | Manual Pause/Stop for a trip, as the app has | **Add "end trip now" and "exclude from stats"**, not pause: recording stays automatic and always-on (ADR-0011) |

## 8. Sources (checked 2026-10-07)

- App Store listing, description, version history 3.4–4.0.0, privacy labels, IAP prices:
  <https://apps.apple.com/us/app/speedometer-driving-tracker/id6759611784>
- Developer site (privacy claims, feature list): <https://speedometerproapp.com/>
- Product Hunt launch record via hunted.space (CarPlay-first pitch, tags):
  <https://hunted.space/product/speedometer-speed-distance>
- The owner's screenshots `1.webp` (App Store header and five frames) and `2.png` (Sprint Records).
- No developer Reddit post was found in this pass **(U)**; the brief's paraphrase of the developer's
  description (CarPlay driving-task entitlement, post-trip review over live gauges) is taken as given.
