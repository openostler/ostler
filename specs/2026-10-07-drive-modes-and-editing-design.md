---
title: "Drive modes and the editable UI — mode switcher, seven presets, Android-style editing of Home, rail and Drive — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-community-hub-design.md, references/research/obd_telematics_apps.md, references/research/dmd2_ui_teardown.md, references/research/dmd2_features.md, references/research/driver_distraction_rules.md, references/research/node_sensors.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, ui/src/screens/Drive.tsx, ui/src/shell/strip.ts, ui/src/shell/layoutClass.ts, ui/src/shell/destinations.ts, ui/tokens/size.tokens.json, schemas/layout.schema.json]
summary: >
  DRAFT for the owner (DMD round, 2026-10-07), answering "the current Drive mode is too diagnostic" and the ask for an Android-style editable UI. Drive mode gains several modes, each a Drive layout as data (UI spec §12.3) in a versioned JSON format, `ostler.layout/1`, authored per layout class, with tiles bound to VSS paths (range, normal/warning/critical levels, units, gauge style) and map, media and push-to-talk panes, plus an explicit, strictly validated Moving section that maps onto the shell templates. Seven presets: Diagnostic (today's six tiles), Dashboard (speed hero, rpm sweep, side gauges), Map, Convoy / Ride, Off-road (D2), Split / Media and Minimal / Night, each with per-class wireframes and its data and add-on needs (D2 gaps marked: IMU tilt not published yet, low range and diff lock only in a SLABS session, no VSS leaf for the centre diff lock, no media source yet). A Drive-mode chip in the strip switches with one tap while Moving (tap cycles a rotation of up to four modes, long-press lists up to six); editing needs Parked on head units ("Park to edit"), enforced by the server. Home gets long-press edit mode (drag, small/medium/wide, remove, a widget picker from core and add-ons, undo, Reset to default); the rail gets reorder and pinning of add-on pages inside the five-slot cap with Home and More locked; the Drive editor binds any VSS signal, gauge style, units and thresholds with a live Moving preview. Safety items (fault telltale, alarm alerts, core strip chips) cannot be removed. Layouts are stored per vehicle, layout class and user profile on the Brain (on the device without one), exported and imported as files that are rejected when their Moving section breaks the template limits. Add-ons register widgets through a `contributes.widgets` contract proposed for the app-model spec. Tests, phases DM1–DM5 and decisions.
---

# Drive modes and the editable UI — design

**Status:** draft for the owner, DMD round (2026-10-07). Nothing here is built before U1, and
the Moving parts land no earlier than U2's lockouts. It **refines, and where marked amends,**
UI spec [§12.3 Drive layouts as data](2026-10-06-ui-architecture-design.md#123-drive-mode-changes-31-35-53-54-10-u1-and-its-test)
and §3.2–§3.4, and proposes a widget and slot contract for the
[app-model spec](2026-10-06-app-model-design.md) (its proposed §15). Tiers, the gate, action
categories, the templates and their limits (UI spec §12.1) are unchanged.

**Owner's ask (2026-10-07, in brief).** (1) Several Drive modes with a switcher, because "the
current Drive mode is too diagnostic": a chip in the status strip, one tap while Moving,
editing and adding only when Parked; presets Diagnostic, Dashboard, Map, Convoy / Ride,
Off-road (D2), Split / Media and Minimal / Night, each a layout as data rendered through the
templates while Moving; a default per layout class; modes shareable as files. (2) An editable
UI, Android style: Home edit mode with drag, resize, remove, a widget picker and Reset; rail
reorder and pinning within the five-slot cap; Drive tiles bound to any VSS signal with style,
units, thresholds and live preview; Park to edit on head units; safety items locked; layouts per
layout class and user profile, importable and exportable; a widget contract for add-ons.

**Evidence** (linked, not repeated): [OBD and telematics apps](../references/research/obd_telematics_apps.md)
(RealDash model, AutoZen, community layouts, Decide 1 and 3);
[DMD2 UI teardown](../references/research/dmd2_ui_teardown.md) (§2 Home rows and cluster view,
§3 layout editors, §4 Drive versus the cluster, §5 remote model, Copy 4–6, Avoid 1);
[DMD2 features](../references/research/dmd2_features.md) (§3, Decide 2 "no rider profiles");
[driver-distraction rules](../references/research/driver_distraction_rules.md) (§7.2 limits).
Sibling draft in this round: the D-pad input model `ShellInput`,
[shell input spec](2026-10-07-shell-input-design.md) (drafted in parallel; this spec uses its
intents `up`/`down`/`left`/`right`/`ok`/`back`/`menu` and its 600 ms long press by name).

## 1. Where we are, plainly

- `ui/src/screens/Drive.tsx` renders the pack's `layout.drive[<module>]` (`schemas/layout.schema.json`
  `driveView`): for the D2's Td5 that is **Boost, Coolant, Battery, Intake air, Fuel now, Trip**
  (economy). No speed, no rpm, no map. SLABS and BCU sessions show pack-registered car views.
  That is the "too diagnostic" screen: it follows the module in session, not the driver.
- The strip (`ui/src/shell/strip.ts`) leads with **Back** in Drive mode; chip ids are
  `back · admin · telltale · link · rec · battery · clock · mark`. HU-5 and phone keep subsets.
- Layout classes (`ui/src/shell/layoutClass.ts`): `hu5 · hu7 · hu9 · huwide · phone · tablet ·
  desktop`; `size.tokens.json` holds rail width, strip height, `target` (76 px on head units),
  `gap` and the type scale per class (`type-num-xl` 64 px on HU-5/7, 72 px on HU-9/10 and HU-wide).
- The destination registry (`ui/src/shell/destinations.ts`) already has `slot`, `order`,
  `requires`, `trust` and the hard cap `MAX_DESTINATIONS = 5`.
- Nothing is user-editable today; §12.3 approved a Parked-only grid editor over a per-vehicle
  diff, with no pixel editor in v1.

## 2. Goals and non-goals

**Goals.** Drive mode that serves the driver first (speed, a map, media, the ride) and keeps
diagnostics one tap away; several modes and a switcher that is safe at speed; one data format
for every mode, shipped presets and user layouts alike; Android-style editing of Home, rail and
Drive that can never produce an unsafe Moving screen; layouts that follow the person and the
car and travel as files; add-ons that contribute widgets without new shell code per add-on.

**Non-goals.** A pixel or free-drag editor (§12.3; DMD's own docs concede dragged positions do
not travel, teardown Avoid 1); RealDash-style triggers or actions in layouts (layouts are Read
only, ADR-0033); animated needles, glow or video while Moving; a second "profile" concept
beside users and vehicles (DMD2 features Decide 2); editing the strip's core chips; a
seventh template.

## 3. Terms

| Term | Meaning |
|---|---|
| **Drive mode** | One named Drive layout the driver can switch to with the strip chip (Dashboard, Map …); replaces §12.3's single layout |
| **Face** | One screen inside a mode (for example the cluster and a map); a mode has 1–3 faces per class, switched by D-pad `left`/`right` or a swipe ([ShellInput](2026-10-07-shell-input-design.md) §6); each face has its own Moving section |
| **Layout** | A document in the `ostler.layout/1` format (§4): kind `drive_mode`, `home` or `rail` |
| **Grid** | Per layout class: columns × rows of cells, rows sized by remaining height (`grid-auto-rows: 1fr`, §12.3) |
| **Widget** | A placed item: a core widget (signal tile, gauge, hero, map …) or one an add-on registers (§9) |
| **Pane** | A large widget that maps to a non-tile template: `map`, `media` or `ptt` (the `call` template) |
| **Moving section** | The part of a Drive layout shown while Moving on a driver-facing display; validated strictly (§4.3) |
| **Profile** | The signed-in user on that display (accounts spec §14.7 S4), or **Car** (the head unit's kiosk session) |
| **Rotation** | The ordered modes the switcher chip cycles through with one tap (≤ 4) |

## 4. The layout format, `ostler.layout/1`

### 4.1 Shape

One JSON document per layout, validated by `schemas/ostler-layout.schema.json` (JSON Schema
2020-12, ADR-0017; created in DM1). Media type `application/vnd.ostler.layout+json`, file
extension `.ostler-layout.json`.

```jsonc
{ "format": "ostler.layout/1",                 // format and major version; minor additions are additive
  "kind": "drive_mode",                        // drive_mode | home | rail
  "id": "community.d2-greenlane",              // preset ids are "ostler.<name>"; user ids are minted locally
  "name": "Green lane", "icon": "terrain",     // name ≤ 30 characters, Material Symbols name
  "description": "Low range, tilt and the breadcrumb trail",   // ≤ 120 characters
  "base": { "preset": "ostler.offroad", "version": 3 },        // what it was made from (Reset target)
  "license": "CC-BY-SA-4.0", "author": "optional display name",
  "vehicle_hint": { "pack": "lr_d2" },         // optional discovery hint; never a vid, VIN or plate
  "requires": { "addons": [], "signals_any": ["Vehicle.Speed"] },
  "theme_hint": null,                          // null | "night_dim": may darken, never brighten
  "classes": {
    "hu7": [ {                                 // authored per class, never scaled (§12.3); 1–3 faces
      "face": "cluster", "name": "Cluster",    // the first face is the default
      "grid": { "cols": 6, "rows": 4 },
      "widgets": [
        { "slot": "a", "widget": "ostler.hero", "at": [0, 0], "size": "hero",
          "bind": { "path": "Vehicle.Speed" }, "style": "arc",
          "unit": "km/h", "range": [0, 160],
          "levels": { "warning": [null, null], "critical": [null, null] } },
        { "slot": "b", "widget": "ostler.gauge", "at": [4, 0], "size": "small",
          "bind": { "path": "Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature" },
          "style": "bar", "unit": "Celsius", "label": "Coolant",
          "levels": { "warning": [100, 110], "critical": [110, 130] } },
        { "slot": "m", "widget": "ostler.map", "at": [0, 2], "size": "wide",
          "config": { "follow": "heading_up", "trail": "trip", "layers": [] } } ],
      "moving": {                              // REQUIRED for head-unit classes; strict (§4.3)
        "show": ["a", "b", "m"],               // slot ids, in reading order; ≤ 6 tiles + panes
        "grid": { "cols": 3, "rows": 2 },
        "place": { "a": [0, 0, 2, 2], "b": [2, 0, 1, 1], "m": [2, 1, 1, 1] } } },
      { "face": "map", "name": "Map", "grid": { "...": "..." }, "widgets": [], "moving": { "...": "..." } } ],
    "phone": [ { "...": "..." } ] } }
```

### 4.2 Field rules

- **`format`** is checked first; an unknown major version is refused with "Made for a newer
  Ostler". Unknown fields in a known major version are ignored and kept on export.
- **Faces.** Each class holds an array of **1–3 faces** (`face` id, `name` ≤ 30 characters,
  `grid`, `widgets`, `moving`); the first is the default. A face is validated like a whole
  layout, so every face is drivable. Home and rail layouts have one face.
- **`classes`** holds any of `hu5`, `hu7`, `hu9`, `huwide`, `phone`, `tablet`, `desktop`. A
  missing class falls back in a fixed order (`hu5` ← `hu7` ← `hu9`; `tablet` ← `desktop`;
  `huwide` and `phone` have no fallback and use the generated default, §5.4 of the UI spec),
  never by scaling.
- **Bindings are VSS paths** (ADR-0016, VSS 6.1 plus the `Vehicle.Ostler.*` overlay), never
  pack signal names, so a mode travels between vehicles. A path the active vehicle does not
  provide renders "Not available on this car"; a path provided but not in session renders
  "Not in this session" (the D2's one-session K-line, UI spec §3.5); never zero.
- **`range`, `levels`, `unit`, `dec`** default from the signal's `span`, `normal`, `limits`,
  `unit` and `dec` in the capability manifest (§5.1) and may be overridden per widget. Levels
  are `[min, max]` pairs as in RealDash; the tile changes colour only when its level changes
  (§12.3) and wears the word ("High") with the colour (visual spec §8). `unit` is a VSS
  `units.yaml` key; the display converts through `Intl` per the user's preference unless the
  widget fixes one.
- **`style`** per widget kind: `number`, `arc` (the 240° gauge of visual spec §8), `bar`,
  `chip` (binary), `text` (enum), `sparkline` (Parked only), `inclinometer`, `compass`.
- **`size`**: `small` (1 × 1 Moving cell), `medium` (2 × 1), `wide` (full row on phone, 3 × 1
  on HU), `hero` (2 × 2). The Parked `grid` uses finer cells; each class's minimums are in §4.4.
- **No code, no URLs, no images** in v1: labels are plain text ≤ 30 characters with control
  and bidi-override characters stripped; `config` values are validated against the widget's
  declared settings schema (§9). Size ≤ 256 KB.
- **Nothing identifying**: no `vid`, VIN, plate, user id or place. Export strips them (§8).

### 4.3 The Moving section and the template mapping

While Moving on a driver-facing display (UI spec §12.1) the shell renders **only** the current
face's Moving section, and each element through one template:

| Layout element | Template while Moving | Counted against |
|---|---|---|
| Signal tile, gauge, hero, chip, inclinometer, compass, trip figure | `tiles` | ≤ 6 tiles (a hero counts as one) |
| Overlay tile on the map pane (speed, two stats) | `tiles` | the same ≤ 6 |
| Map pane | `map` (own position, route, next manoeuvre, opted-in convoy markers only) | ≤ 1 pane of each kind |
| Media pane | `media` | ≤ 1 |
| PTT / ride pane | `call` | ≤ 1 |
| One status line | `value` (≤ 2 values, one line ≤ 30 characters) | counts as 2 tiles |
| Fault telltale, alarm alerts | shell-drawn (strip chip, `alert_card`) | never in the layout; always on |

**Strict rules** (an import or save that breaks any of them is refused, §8.2): at most 6
tiles; at most two panes on HU-5, HU-7 and phone, three on HU-9/10 and HU-wide; no widget
whose manifest says `moving: false` (§9); digits ≥ the class's `type-num-xl` floor of 56 px,
labels ≥ 24 px (visual spec §4); no `sparkline`, no animation, refresh ≤ 4 Hz with
hysteresis and no tweening (an rpm "sweep" steps, it does not glide); every element inside the
viewport with no scroll (§12.3 test). Parked and Idling (with Park evidence) render the full
grid; Passenger view (§12.1) may render the full grid **only** when every widget in it is
vehicle state, own location or a driving camera, and still without animation.

### 4.4 Grids and minimum sizes per class

Content area per class from §3.1 and §12.3 (Drive mode is full-screen: strip on top, rail on
the driver's side). Proposed values, tuned in DM1 by the no-scroll tests.

| Class | Drive content (px) | Moving grid | Parked grid | Min Moving tile | Min pane |
|---|---|---|---|---|---|
| HU-5 800×480 | 720 × 432 | 3 × 2 | 6 × 4 | 208 × 176 | 340 × 300 |
| HU-7 1024×600 | 928 × 544 | 3 × 2 | 6 × 4 | 280 × 240 | 440 × 360 |
| HU-9/10 1280×720 | 1168 × 656 | 4 × 2 | 8 × 4 | 260 × 290 | 540 × 420 |
| HU-wide 1920×720 | 1808 × 656 | 6 × 2 (three columns) | 12 × 4 | 280 × 290 | 560 × 560 |
| Phone ~393×852 | ~393 × 730 | 2 × 3 | 4 × 6 | 170 × 200 | 361 × 300 |
| Tablet, desktop | per page | 3 × 2 | 8 × 6 | — (not driver-facing unless declared) | — |

## 5. The seven presets

Presets ship in the platform as `ostler.layout/1` files (`ui/src/drive/presets/*.json`,
CC BY-SA 4.0), each with every class above. Legend for data: ✔ have, ◐ compute or partial, ✘
new. In every wireframe the strip (with the Drive-mode chip, §6) is on top and the rail on
the driver's side, drawn here on the right for the right-hand-drive D2. `[T]` = a tile.

### 5.1 Diagnostic (today's six tiles)

The pack's `layout.drive` for the module in session, converted to a mode (tier 2 of UI spec
§5.3); generated from roles when the pack declares none. Exactly today's screen, now one mode
among several.

```
HU-5 / HU-7 (3×2)            HU-9/10 (4×2; 7th+ Parked)    HU-wide (6×2)
┌────────┬────────┬────────┐ ┌──────┬──────┬──────┬──────┐ ┌────┬────┬────┬────┬────┬────┐
│ Boost  │Coolant │Battery │ │Boost │Cool. │Batt. │Intake│ │Bst │Cool│Batt│Int │Fuel│Trip│
├────────┼────────┼────────┤ ├──────┼──────┼──────┴──────┤ ├────┴────┴────┴────┴────┴────┤
│ Intake │Fuel now│ Trip   │ │Fuel  │ Trip │ (Parked: +) │ │ Parked: system view, wide    │
└────────┴────────┴────────┘ └──────┴──────┴─────────────┘ └──────────────────────────────┘
Phone (2×3): Boost Coolant / Battery Intake / Fuel now Trip
```

**Data:** ✔ D2 Td5 tiles (`manifold_press`, `coolant_temp`, `battery`, `air_temp`, `economy`,
`trip_economy`); the economy figures are `candidate` and drawn as such. **Add-on:** none.
**Change:** bindings move from pack signal names to VSS paths where the pack maps them
(`Vehicle.Powertrain.CombustionEngine.MAP` …); unmapped ones (`air_temp`, `economy`) keep a pack
binding `{"pack": "lr_d2", "signal": "td5.air_temp"}` allowed only in pack-shipped and
vehicle-hinted layouts.

### 5.2 Dashboard (RealDash-style cluster)

A speed hero in the middle, an rpm sweep, side gauges; DMD's full-screen cluster and the
RealDash two-page pattern ([telematics research](../references/research/obd_telematics_apps.md#editor-and-screens),
teardown §4). **Proposed default on head units.**

```
HU-5 / HU-7 Moving                  HU-9/10 Moving                     HU-wide Moving
┌────────┬─────────────┬────────┐   ┌───────┬───────────────┬───────┐ ┌──────┬──────┬───────────┬──────┬──────┐
│Coolant │   ╭─────╮   │ Boost  │   │Coolant│  ╭─────────╮  │ Boost │ │Cool. │Boost │  ╭─────╮  │Batt. │ Fuel │
│  88 °C │   │ 64  │   │ 1.2bar │   │ 88 °C │  │   64    │  │1.2 bar│ │      │      │  │ 64  │  │      │      │
├────────┤   │km/h │   ├────────┤   ├───────┤  │  km/h   │  ├───────┤ ├──────┴──────┤  │km/h │  ├──────┴──────┤
│Battery │   ╰─────╯   │  rpm   │   │Battery│  ╰─────────╯  │  rpm  │ │ (Parked: g, │  ╰─────╯  │ (Parked:    │
│ 13.9 V │  (hero arc) │ ▮▮▮▯▯  │   │13.9 V │  hero 2×2     │ ▮▮▮▯▯ │ │  trip, map) │   hero    │  sparklines)│
└────────┴─────────────┴────────┘   └───────┴───────────────┴───────┘ └─────────────┴───────────┴─────────────┘
Phone Moving (2×3): hero speed (2 wide) / rpm Coolant / Boost Battery
Parked or Passenger view: free-form 6×4 (HU-7): adds g-meter, trip figures, fuel or economy, ride height; no animation
```

**Moving:** hero speed + rpm + 4 side gauges = 6 tiles. **Data:** ◐ speed: `Vehicle.Speed`
from the Td5 when it holds K-line, else GPS (`Vehicle.Speed` from the node's GNSS, labelled
by source, §12.2); ✔ rpm, coolant, MAP (boost), battery in a Td5 session; ✘ fuel level (the D2
has none decoded; the economy figure is `candidate`, UI spec §5.4); ◐ g-meter from the node
IMU (`motion.py`, Parked/Passenger only). **Add-on:** none.

### 5.3 Map

Full-screen dark map (Ostler Night, visual spec §7), speed and two stat overlays, buddies as
plain markers for opted-in ride members only (§12.1 rule, Vehicles & Map spec §6).

```
HU-5 / HU-7                          HU-9/10                              HU-wide
┌──────────────────────────────┐   ┌──────────────────────────────────┐ ┌──────────────────────────────────────────┐
│ ┌──────┐                     │   │ ┌──────┐                ┌──────┐ │ │┌──────┐                         ┌──────┐│
│ │ 64   │      ▲ (puck)       │   │ │ 64   │     ▲          │Next ↱│ │ ││ 64   │          ▲               │Next ↱││
│ │ km/h │   ·  ·  ·  (trail)  │   │ │ km/h │   · · ·        │300 m │ │ ││ km/h │      · · ·  ●(convoy)    │300 m ││
│ └──────┘          ●(convoy)  │   │ └──────┘                └──────┘ │ │└──────┘                          └──────┘│
│ [Alt 312 m]  [ETA / trip km] │   │ [Alt 312 m]   [Trip 42 km]       │ │[Alt 312 m] [Trip 42 km]  [Heading 214°]  │
└──────────────────────────────┘   └──────────────────────────────────┘ └──────────────────────────────────────────┘
Phone: map full, speed overlay top-left, two stats at the bottom
```

**Moving:** `map` + 3 overlay tiles (+ next manoeuvre only from the navigation add-on). No
free panning, no search; D-pad `up`/`down` zoom (ShellInput). **Data:** ✔ own position and
trail (Trips' live track); ✔ altitude (`Vehicle.CurrentLocation.Altitude`, GPS); ◐ trip
distance (Trips' "Recording now" figures exposed as `Vehicle.Ostler.Trip.*` signals, ✘ new, as
teardown Copy 9); ◐ basemap: PMTiles on the Brain, else the online fallback, else the offline
fallback (`bg`, trace and puck). **Add-ons:** optional `ostler-app-navigation` (route, next
manoeuvre, ETA); optional Vehicles & Map (convoy markers, only for an active ride the driver
opted into).

### 5.4 Convoy / Ride

Map, a big push-to-talk button, ride status (Social spec "PTT first").

```
HU-5 / HU-7                                HU-9/10                              HU-wide
┌──────────────────────┬───────────────┐ ┌──────────────────────┬────────────┐ ┌──────────┬─────────────────────┬────────────┐
│  map (convoy markers │  ╭─────────╮  │ │ map                  │ ╭────────╮ │ │ Speed 64 │ map, convoy markers │ ╭────────╮ │
│  plain, ≤ 6)         │  │  HOLD   │  │ │                      │ │  HOLD  │ │ │ km/h     │ (plain, ≤ 6)        │ │  HOLD  │ │
│  ┌──────┐            │  │ TO TALK │  │ │ ┌──────┐             │ │TO TALK │ │ ├──────────┤                     │ │TO TALK │ │
│  │ 64   │            │  ╰─────────╯  │ │ │ 64   │             │ ╰────────╯ │ │ Leader   │                     │ ╰────────╯ │
│  └──────┘            │ Ride: Peak ·5 │ │ └──────┘             │ Ride: Peak │ │ 1.2 km   │                     │ Mute · End │
│                      │ Leader 1.2 km │ │ [Sweep 0.4 km]       │ Leader 1.2 │ │          │                     │ Ride: Peak │
└──────────────────────┴───────────────┘ └──────────────────────┴────────────┘ └──────────┴─────────────────────┴────────────┘
Phone: map top half, PTT button bottom half, one ride line
```

**Moving:** `map` + `call` (hold to talk, mute, end: ≤ 3 buttons; "who's talking" as one name
≤ 30 characters, no photo) + speed and leader distance tiles. Offered in the switcher only while
a ride is active; it never appears by itself (Decision 6). **Data:** ✘ ride state, PTT and
"who's talking" (Social S1/S2); ✘ convoy markers and distance to leader/sweep (Vehicles &
Map V2). **Add-ons:** **Social required**, Vehicles & Map optional (without it: PTT and ride
line, map shows only own position). A hardware PTT button is an input source (ShellInput
`ptt` intent), not a car action.

### 5.5 Off-road (D2)

Inclinometer (pitch and roll), altitude, compass, low range and centre diff lock, breadcrumb
map. Shipped with `vehicle_hint: {pack: "lr_d2"}` but bound to VSS so other 4×4s can use it.

```
HU-5 / HU-7                                HU-9/10                              HU-wide
┌─────────────┬────────────┬───────────┐ ┌────────────┬───────────┬─────────┐ ┌───────────┬───────────┬─────────────┬──────────┐
│  PITCH  4°  │ ROLL  12°  │ LOW RANGE │ │ ╭──╮ pitch │ ╭──╮ roll │ LOW     │ │ Pitch 4°  │ Roll 12°  │ breadcrumb  │ LOW      │
│   ◢■◣ side  │  ◢■◣ rear  │ DIFF LOCK │ │ ╰──╯  4°   │ ╰──╯ 12°  │ DIFF LK │ │ (side)    │ (rear)    │ map, trail  │ DIFF LOCK│
├─────────────┼────────────┴───────────┤ ├────────────┼───────────┴─────────┤ ├───────────┼───────────┤ back-track  ├──────────┤
│ Alt 312 m   │  breadcrumb map        │ │ Alt 312 m  │ breadcrumb map      │ │ Alt 312 m │ ↑ 214° SW │             │ Speed 8  │
│ ↑ 214° SW   │  (trail, own position) │ │ ↑ 214° SW  │                     │ │           │           │             │ km/h     │
└─────────────┴────────────────────────┘ └────────────┴─────────────────────┘ └───────────┴───────────┴─────────────┴──────────┘
Phone (2×3): Pitch Roll / Low range+Diff lock (one chip pair) Altitude / map (wide)
```

**Moving:** 5 tiles + `map` (low range and diff lock as one two-state tile; the inclinometer
draws a static vehicle silhouette rotated by the value, stepped ≤ 4 Hz, critical level from
the user's threshold, for example roll ≥ 30°). **Data on the D2, honestly:**

| Item | VSS path | State on the D2 | Gap |
|---|---|---|---|
| Pitch, roll | `Vehicle.Orientation.Pitch`, `.Roll` (VSS leaves exist) | ✘ **not published.** The node IMU (`imu/reader.py`) gives specific force only; `motion.py` levels it (`level_matrix`) but computes no tilt | New node or Brain derivation: static tilt from the low-passed gravity vector after levelling, `candidate`, valid only at low acceleration (≤ 0.1 g) or with gyro fusion later; the IMU must be screwed down (node sensors note §placement). Without a node IMU the tiles read "Needs the node's IMU" |
| Altitude | `Vehicle.CurrentLocation.Altitude` | ✔ GPS (`GPS_Altitude`) | GNSS altitude error is tens of metres; label "GPS" |
| Compass | `Vehicle.CurrentLocation.Heading` | ◐ GPS course over ground; frozen below about 3 km/h | No magnetometer on the node; a parked or crawling heading shows the last course with "stale" |
| Low range | `Vehicle.Powertrain.Transmission.IsLowRangeEngaged` | ✔ `slabs.transfer_low`, proven (T-29) | **Only in a SLABS session** (`21 42`): the Td5 is then not in session, so rpm and coolant read "Not in this session" and speed comes from GPS (UI spec §3.5) |
| Centre diff lock | none in VSS (VSS has `DiffLockFront/RearEngagement` only) | ✔ `slabs.diff_lock`, proven, but unmapped | Needs an overlay leaf, proposed `Vehicle.Ostler.Powertrain.Transmission.IsCentreDiffLocked`, a D2 pack change (`metric` on the store record and `test_metrics_d2.py`), same SLABS-session limit |
| Breadcrumb map | own track | ✔ Trips' live track | Back-track along the trail needs the navigation add-on |

**Add-on:** none for the tiles; navigation optional. Because K-line holds one session, the
preset's switcher entry offers "Open SLABS" once when entered Parked with no SLABS session
(a system switch, which is locked while Moving, §3.5).

### 5.6 Split / Media

AutoZen-style "Coolwalk": map plus a now-playing side panel; three columns on HU-wide
(research: the most-installed drive screen wins on media and navigation, not gauges).

```
HU-5 / HU-7                                HU-9/10                              HU-wide (three columns)
┌──────────────────────┬───────────────┐ ┌──────────────────────┬────────────┐ ┌──────────┬───────────────────┬─────────────┐
│ map                  │ ┌───────────┐ │ │ map                  │ ┌────────┐ │ │ Speed 64 │ map               │ ┌─────────┐ │
│ ┌──────┐             │ │ artwork   │ │ │ ┌──────┐             │ │artwork │ │ ├──────────┤                   │ │ artwork │ │
│ │ 64   │             │ └───────────┘ │ │ │ 64   │             │ └────────┘ │ │ Coolant  │                   │ └─────────┘ │
│ └──────┘             │ Title ≤ 30    │ │ └──────┘             │ Title      │ ├──────────┤                   │ Title       │
│                      │ Artist ≤ 30   │ │                      │ Artist     │ │ Next ↱   │                   │ Artist      │
│                      │ ⏮  ⏯  ⏭  🔊  │ │ [Trip 42 km]         │ ⏮ ⏯ ⏭      │ │ 300 m    │                   │ ⏮  ⏯  ⏭     │
└──────────────────────┴───────────────┘ └──────────────────────┴────────────┘ └──────────┴───────────────────┴─────────────┘
Phone: map top 55 %, now-playing card below (title, artist, ⏮ ⏯ ⏭)
```

(Controls are drawn as Material Symbols `skip_previous`, `play_pause`, `skip_next`,
`volume_up`, never as text glyphs; the wireframe uses glyphs only for brevity.)

**Moving:** `map` + `media` (title and artist ≤ 30 characters, static artwork,
play/pause/skip/volume; browsing only as a `short_list`) + ≤ 3 tiles. **Data:** ✘ **no media
source exists today.** A browser page cannot read the head unit's or phone's now-playing state
(the Media Session API covers only the page's own playback). **Add-on:** a media source
widget (§9) is required, for example an Integrations add-on bridging MPRIS or Spotify Connect on
the Brain, or the phone app's native media session over the local link; until one is enabled
the preset is hidden from the switcher and the picker says "Needs a media add-on" (Decision 7).

### 5.7 Minimal / Night

Huge speed, one status line. For night driving, fatigue and passengers who want a calm screen.

```
HU-5 / HU-7                     HU-9/10                          HU-wide
┌──────────────────────────┐  ┌──────────────────────────────┐ ┌────────────────────────────────────────┐
│                          │  │                              │ │                                        │
│           64             │  │             64               │ │                  64                    │
│          km/h            │  │            km/h              │ │                 km/h                   │
│                          │  │                              │ │                                        │
│  Coolant 88 °C · 13.9 V  │  │   Coolant 88 °C · 13.9 V     │ │        Coolant 88 °C · 13.9 V          │
└──────────────────────────┘  └──────────────────────────────┘ └────────────────────────────────────────┘
Phone: the same, hero 64 px → scaled up to the `type-hero` token of the class, never beyond it
```

**Moving:** one hero tile + one `value` status line (two values) = 3 tiles' budget.
`theme_hint: "night_dim"` darkens to Night dim (visual spec §3) when the theme is Auto and it
is dark; it never brightens. **Data:** ✔ speed (Td5 or GPS), coolant, battery. **Add-on:**
none.

### 5.8 Faces per preset

| Preset | Faces (`left`/`right`) |
|---|---|
| Diagnostic | Tiles · (Parked) system view of the module in session |
| Dashboard | Cluster · Map (speed overlay) |
| Map | Map (one face) |
| Convoy / Ride | Map + PTT · Ride (members as a count, leader and sweep distance) |
| Off-road (D2) | Tilt · Trail map |
| Split / Media | Split (one face) |
| Minimal / Night | Minimal (one face) |

### 5.9 Defaults and rotation per class

| Class | Default mode | Default rotation (one-tap cycle) |
|---|---|---|
| HU-5, HU-7, HU-9/10 | Dashboard | Dashboard → Map → Diagnostic → Minimal |
| HU-wide | Split / Media if a media source exists, else Dashboard | Dashboard → Split / Media → Diagnostic → Minimal |
| Phone (passenger device, §3.5) | Dashboard | Dashboard → Map → Diagnostic |
| Tablet, desktop | Diagnostic | — (switch from the list) |

Off-road joins the rotation automatically for a vehicle whose pack hints it (the D2) once the
user picks it the first time; Convoy joins while a ride is active (§5.4). A pack may ship a
default mode (tier 2) that replaces Dashboard for its vehicles; the user's choice always wins.

## 6. The switcher

**Chip.** A new strip chip `drive_mode`, shown **only in Drive mode**, right after Back:
icon + the mode's name ("Dashboard"), ≥ 48 px tall, hit target `--target` (76 px on head
units). It joins the phone and HU-5 chip sets (`strip.ts` `PHONE`, `HU5`). It is a core strip
chip (safety rule R4 applies: it cannot be removed).

**One tap while Moving.** *Tap* cycles to the next mode in the rotation (≤ 4 modes); the chip
word changes and the new layout appears; no toast, no animation. *Long-press* (600 ms,
ShellInput) or a long `ok` on the focused chip opens the **mode list** as a `short_list`: up to
six modes, one level, names ≤ 30 characters, the current one ticked; one tap picks; a short
`ok` on the focused chip cycles like a tap.

**Modes and faces are two levels, as ShellInput defines them:** the chip switches **modes**;
D-pad `left`/`right` and a horizontal swipe switch the **faces** of the current mode, wrapping
(DMD's corner swap of ring and map, RealDash's tap-to-cycle centre views;
[ShellInput](2026-10-07-shell-input-design.md) §6); `ok` and `menu` in Drive mode with focus in
`main` open ShellInput's **Drive menu**, not the mode list. The active face is remembered with
the mode. The mode list shows **Edit modes…** only when Parked; while Moving the
row is absent, not greyed (no dead targets).

**Order and visibility.** The rotation is the user's ordered list; the mode list shows the
rotation first, then other available modes. A mode whose `requires` fails (Convoy without an
active ride, Split / Media without a media source) is hidden from both, never shown broken.

**Remembered** per display × profile × vehicle: the active mode survives a restart, a wake
and a profile switch back. On entering Moving the display opens the last mode used on it;
nothing switches by itself while Moving (no auto-switch at night or on a ride start: the
driver decides; Decision 6). A switch is not a car action and is not logged in the trip.

**Server.** The active mode is a display setting the server stores (§8.3); a switch is a
`PUT` allowed in any driving state; adding, editing, deleting or re-ordering modes is refused
while that display is Moving (rule R1).

## 7. Editing

### 7.1 Common states and gestures

```
Viewing ──long-press 600 ms (Parked)──▶ Editing ──Done──▶ Saving ──▶ Viewing
   ▲                                       │  ▲ Undo / Redo (session stack, 50 steps)
   │                                       │  └─ Preview (Moving preview, §7.4)
   └────────────── Cancel / back ◀─────────┘   (discards since entering)
Moving on a driver-facing display: long-press shows "Park to edit" for 3 s; nothing else.
Entering Moving while Editing: the draft is kept, the editor closes to Drive mode, and
"Finish editing when parked" is offered at the next Parked.
```

- **Touch.** Long-press on empty space or any widget enters edit mode (Android launcher
  model); widgets jiggle-free (no motion), each shows a frame, a drag handle, a **size**
  button that cycles small → medium → wide (→ hero where allowed) and a remove button (×).
  Drag snaps to the class grid; dropping on an occupied cell **swaps** (DMD's "duplicate picks
  swap", so a layout is never invalid and needs no gaps-repair step). A **+** button opens the
  widget picker. Resizing by buttons, not corner drags, keeps it glove-friendly (76 px targets).
- **D-pad** (ShellInput): `menu` long-press on Home or Drive enters edit mode when Parked;
  arrows move focus between widgets; `ok` picks a widget up (focus ring doubles), arrows move
  it cell by cell, `ok` drops (swap on occupied), `back` cancels the move; `menu` on a focused
  widget opens its options sheet (size, settings, remove); `back` with nothing picked asks
  "Discard changes?" with **Cancel** focused.
- **Undo and Redo** in the edit bar; **Reset to default** asks once, Cancel focused, and
  restores the `base` (preset, pack or generated default) for this class only, with "All
  screen sizes" as an option.
- **Edit bar** (top of the content area, never in the strip): Done, Cancel, Undo, Redo,
  Preview, Reset, and a class picker ("Editing for: this screen ▾") on phone and desktop.
- **Autosave of the draft** to the server every change, so a dropped connection or a wake loses
  nothing; the live layout changes only on **Done**.
- **Editing another screen's layout.** From a phone or desktop, any class can be edited at
  any time (they are not driver-facing for this purpose) with a preview at that class's size;
  if the target display is Moving, the change is held and applies at its next Parked ("Applies
  when the car is parked"), so nothing changes under a driver's eyes.

### 7.2 Home

Home's grid comes from roles today (§5.4); edit mode turns it into a widget grid per class
(HU-7 2 × 2 cards becomes a 4 × 4 cell grid where a card is medium or wide; phone 4 columns).
The **widget picker** is a sheet (bottom on phone, passenger side on head units): search,
then groups **Vehicle** (vehicle card, any signal tile, gauge, health, last trip), **Trips**,
**Security**, **Network**, then one group per enabled add-on (its `contributes.widgets` with
`surfaces` containing `home`), each row an icon, a bold name, a one-line description and the
sizes it supports (DMD Home editor, teardown §3). An add-on that is installed but not enabled
appears greyed with "Enable in Add-ons". Locked items: the **warnings card** (fault telltale)
and the **Security alert card** may be moved and resized, never removed; the vehicle card may
be resized, not removed, while the garage holds one vehicle. The empty-state Add-ons card
(§12.4) stays dismissible as today and is not a widget.

### 7.3 Rail

**Shape.** Five slots, a hard cap (§3.4): **Home first and More last are locked**; the three
middle slots hold, in the user's order, any of the core destinations (Diagnose, Trips,
Security) and **pinned add-on pages** (any `more:*` page, for example Social, Vehicles & Map,
Community). Whatever is not in the rail appears at the top of More under **Pages**, so nothing
is ever unreachable. The head-unit Drive-mode button stays fixed beside the rail (§3.3) and is
not a slot.

**Editing.** More → Preferences → **Rail**, or long-press on the rail (Parked): a list of the
five slots with drag handles and a "Pages you can pin" list below; D-pad: `ok` picks, `up`/`down`
moves, `ok` drops. Pinning a page when three middle slots are full asks which one to move to
More. A pinned page keeps its own driving rule (locked while Moving like the rest of More, its
`moving` template if it has one), so pinning unlocks nothing.

**Safety.** Alarm alerts reach the driver through the strip's Security chip and `alert_card`
whatever the rail holds (R3), so Security may move to More like any other destination; the
landing rule (Security when Parked and armed, §3.4) opens it wherever it sits. Default rail:
Home · Diagnose · Trips · Security · More (today's).

This **amends** UI spec §3.4 ("five destinations") and app-model §14.1 ("no add-on contributes
a `destination:*` slot"): the cap and the slot rule hold, but the user may swap a core
destination for a shortcut to an add-on page (Decision 4).

### 7.4 Drive modes

Slot-first editing (teardown Copy 4): pick a cell, then pick what goes in it.

1. **Modes list** (Parked): rotation order (drag), add (from preset, duplicate, import),
   rename, delete (presets cannot be deleted, only hidden), share (§8).
2. **Mode editor**: tabs for the mode's faces (add up to three, rename, reorder, delete), then
   for each face the class's Parked grid with the edit gestures of §7.1, plus a **Moving
   strip** below it showing which widgets are in the Moving section and their order (drag to
   reorder, a pin icon to add or remove from Moving; the counter reads "Moving: 5 of 6 tiles,
   1 of 2 panes").
3. **Widget settings sheet**: **Signal** (a VSS picker grouped by system and VSS branch,
   filtered by "Available on this car" by default, each row with its confidence word and
   "Not in this session" where relevant; any VSS path may be typed on desktop); **Style**
   (§4.2, only those valid for the signal's type); **Units** (follow Preferences, or fixed per
   tile); **Decimals**; **Label** (≤ 30 characters); **Range**; **Thresholds**: normal,
   warning and critical as min/max pairs with a live band drawn on the gauge, defaulting from
   the signal's `normal` and `limits`, validated ordered and inside the range.
4. **Live preview**: the widget shows live values while editing; **Preview** renders the mode
   at the target class's size in two panes, **Parked** and **Moving**, the latter exactly what
   the template renderer will draw (same code path), with failed rules listed in words ("Tile
   7 shows only when parked", "Map pane too small on HU-5: 300 px, needs 340").
5. **Save** runs the validator (§8.2) for every class the mode holds; a mode whose Moving
   section is invalid for a head-unit class cannot be saved ("Fix for driving first"), so a
   saved mode is always drivable.

## 8. Safety rules, storage and files

### 8.1 Safety rules

- **R1 Park to edit.** On a driver-facing display (§12.1), entering edit mode, adding,
  deleting, reordering modes and changing the rail need **Parked** (or Idling with Park
  evidence). The server refuses the write for that display otherwise (`409` with
  `driving_state` in the error envelope); the UI shows "Park to edit". Switching modes is
  allowed in any state.
- **R2 Moving obeys the templates.** Whatever a user, pack, add-on or file says, the Moving
  render passes only through §4.3's mapping and limits; the validator and the renderer share
  one implementation; fail closed (an unknown widget in a Moving section renders as an empty
  cell and is reported, never as its Parked view).
- **R3 Safety items are shell-owned and not removable.** The fault telltale (strip chip and,
  while Moving, its sheet), alarm and Security alerts (`alert_card`), the Passenger-view badge
  and frame, the service-mode frame and Mark are drawn by the shell outside any layout; a layout
  file cannot contain, hide or cover them. Home's warnings and Security alert cards are
  movable, not removable (§7.2).
- **R4 Core strip chips are fixed.** Back, Drive mode, Worst telltale, Link, REC, Security,
  12 V, Clock and Mark keep their order and presence rules (§3.2); only the device slot's
  choice (climate or camera) is a preference.
- **R5 Size minimums.** Moving tiles and panes keep §4.4's minimums and the type floors; a
  widget that cannot fit drops one type step, then refuses (clipping is a test failure, visual
  spec §4).
- **R6 No actions in layouts.** Widgets read; the only controls in a Moving layout are those
  the templates already allow (media play/pause/skip/volume, PTT hold/mute/end, a `setpoint`
  ±), routed through the shell; anything that reaches the gate keeps its confirm sheet with
  Cancel focused (ADR-0033, ShellInput).
- **R7 Nothing changes under the driver.** A layout change made elsewhere for a display that
  is Moving applies at its next Parked (§7.1).
- **R8 Other people's data.** No layout can show other vehicles while Moving except the `map`
  template's opted-in convoy markers; no names, avatars or photos; the data-class registry
  decides what a widget can read at all.

### 8.2 Validation

One validator (TypeScript in the shell, the same rules mirrored in a Python check on the
server for writes and imports), run on save, import and preset build:

1. JSON Schema (`ostler-layout.schema.json`), size ≤ 256 KB, known `format` major.
2. Text hygiene: labels and names ≤ 30 characters (description ≤ 120), control and bidi
   overrides stripped, no URLs.
3. Bindings: each path exists in VSS 6.1 or the overlay (`vss_leaves.json`, `metrics.json`);
   unknown paths are **warnings** (the tile reads "Not available on this car").
4. Widgets: each id is a core widget or one declared by an enabled add-on; a missing add-on is
   a **warning** (placeholder "Needs *add-on*" with a link to More → Add-ons).
5. Levels ordered and inside the range; units are VSS unit keys compatible with the signal.
6. **Moving section, per head-unit and phone class it holds: strict** (§4.3): tile and pane
   counts, `moving: false` widgets absent, minimum sizes, type floors, no sparkline or
   animation, at most one of each pane kind. Any failure **rejects** the file or the save,
   naming the class and the rule.
7. Identity scrub on export: `vid`, VIN-pattern strings (ADR-0036 block), user ids, places and
   free text that looks like a plate are removed; `author` is kept only if the user typed it.

### 8.3 Storage

**Key:** vehicle (`vid`) × profile (user id, or `car`) × layout class, holding the Home
layout, the rail order, the user's Drive modes and the rotation; plus, per display id, the
active mode per profile and vehicle. Resolution for what a display shows: the profile's layout
for this vehicle and class → the `car` profile's (the owner's default for this car) → the
pack's (tier 2) → the generated default (tier 1). Profiles follow the accounts spec: the
head unit starts in the kiosk session as **Car**; a signed-in user's layouts apply after a
Parked profile switch (S4) and revert to Car at sign-out (ignition off).

| Setup | Where layouts live | Notes |
|---|---|---|
| With a Brain | the Brain, a `ui_layouts` table in its settings store (not `auth.db`), served by `/ui/layouts/{vid}/{profile}/{class}` with ETags | Every display and phone sees the same layouts; the server enforces R1 and R7 |
| Ostler Diagnostics alone (node + phone) | the phone app's local store (Capacitor Preferences); a head unit browser's `localStorage` when it talks to the node directly | The node stores none (flash and wear); export to a file is the backup |
| Ostler Cloud | never stores layouts in v1; a file or the Community hub carries them | Exit guarantee: everything exports |

**Edits are stored as a full copy with a `base` reference** (preset id and version), not as a
patch: grids patch badly, and §5.3's "per-vehicle diff, never a fork" is kept by the `base`
reference, **Reset to default** and an "Update from preset" view that shows the preset's
changes since `base.version` and applies them per slot (Decision 3). Kiosk-session (Car)
layouts are editable Parked from the head unit unless the owner sets **Lock car layouts**
(More → Preferences), after which only an owner signed in may change them.

### 8.4 Import and export

- **Export:** from the modes list, Home or Rail editor: **Save as file** (`.ostler-layout.json`),
  **Copy link** and **QR** (a link carries the file inline when ≤ 2 KB compressed, else a
  relay or hub link), and **Share** through Web Share. No social-network buttons. Licence
  CC BY-SA 4.0 by default (ADR-0012), author optional.
- **Import:** open a file, paste a link or scan a QR, on any host; a preview shows the mode at
  the current class (Parked and Moving), its warnings and the add-ons it wants; **Add** puts it
  in the modes list, not in the rotation. On a head unit, import needs Parked (R1).
- **Community layouts** ([research Decide 3](../references/research/obd_telematics_apps.md#decide-recommendations-for-the-owner)):
  plain files first, an optional catalogue repo later; in this round's
  [Ostler Community](2026-10-07-community-hub-design.md) a layout could become a hub item type
  (publish Private → Pending review → Public), files only, no images (Decision 8).

## 9. The widget and slot contract (summary)

The contract is proposed as **app-model §15** (Proposed amendment (2026-10-07, DMD round));
in short:

- An add-on declares widgets in its manifest under **`contributes.widgets`**: `id`, `title`,
  `description`, `surfaces` (`home`, `drive`), `sizes` (`small`, `medium`, `wide`, `hero`),
  `data` (data classes it reads, a subset of `permissions.data`) and `signals` (VSS paths),
  a `settings` schema for the settings sheet, `refresh_hz`, and **`moving`**: `false` or
  `{ "template": "tiles" | "value" | "map" | "media" | "call" | "setpoint" }` with the data
  the template needs.
- Add-ons also contribute Drive menu rows through **`contributes.drive_menu`** (ShellInput §6;
  a `short_list` of ≤ 6 driver-safe rows while Moving); the Drive menu is separate from the
  mode switcher.
- The user places widgets; there is no add-on-chosen placement. New slot names
  **`home:widget`** and **`drive:widget`** mark where widgets may be placed; `more:*` pages
  become pinnable to the rail (§7.3).
- While Moving the shell draws the widget's template from data the add-on provides through the
  SDK; the add-on's own component renders only Parked (or in Passenger view if it declares
  `passenger_view: true` and qualifies). Widgets get only their declared signals and data
  classes, filtered by the registry; widgets crash into a "Widget stopped" placeholder;
  community widgets run only as sandboxed iframes on web hosts (app-model §5).

**Core widgets** (in the platform): signal tile, gauge, hero, binary chip, enum text,
sparkline, inclinometer, compass, altitude, trip figures (Trips), map (Trips' map), clock,
health/warnings card, vehicle card. **Add-on widgets expected:** PTT and ride status (Social),
convoy distance (Vehicles & Map), next manoeuvre and ETA (navigation), now playing (a media
source), service due (Maintenance & Garage), camera live (Cameras, `camera_live`).

## 10. Tests

- **Unit** (Vitest, no React): the schema; the validator on good and bad fixtures (7 tiles,
  sparkline in Moving, pane too small on HU-5, unknown widget, unknown path, levels out of
  order, VIN-pattern label); the Moving reduction per class; the resolution order (user → Car
  → pack → generated); export scrub; preset files validate for every class.
- **Server** (pytest): `PUT` of layouts and rail refused while the display is Moving (R1);
  held changes apply at Parked (R7); a mode switch accepted while Moving; import refusal
  envelopes name the class and rule.
- **Playwright**, at 800×480, 1024×600, 1280×720, 1280×480, 1920×720 and 393×852:
  - **Switcher:** the `drive_mode` chip is present only in Drive mode, after Back, ≥ 48 px;
    a tap cycles the rotation and the chip word follows; long-press opens a list of ≤ 6 rows;
    the choice survives a reload per display and profile; hidden modes (Convoy with no ride,
    Split / Media with no source) are absent; `ArrowLeft`/`ArrowRight` switch faces within the
    mode and never change the mode.
  - **Park-to-edit gate:** with the Moving fixture, long-press on Home and Drive shows "Park
    to edit" and no edit bar; no "Edit modes…" row in the list; the rail editor route is
    refused; switching Parked → Moving while editing closes the editor and keeps the draft.
  - **No scroll per face per mode per class:** for each face of each of the seven presets (with fixtures for ride,
    media source and SLABS session), `main` does not scroll, every Moving element is inside the
    viewport, ≤ 6 tiles render, digits ≥ 56 px, no element carries `data-glow`, and no
    animation runs (computed `animation-name: none`).
  - **Safety items:** no remove control exists for the warnings and Security alert cards; a
    file that tries to hide the telltale changes nothing; the strip chips are unchanged after
    any edit.
  - **Editing:** drag swap, size cycling, undo/redo, Reset to default; the same by keyboard
    only (ShellInput) with focus always visible and Cancel focused in discard and reset sheets.
  - **Import/export round trip** keeps the layout byte-equal except scrubbed fields; a file
    with an invalid Moving section is refused with the class and rule named.

## 11. Phases

| Phase | Ships | Needs |
|---|---|---|
| **DM1** (with U2) | `ostler.layout/1` schema and validator; Moving reduction through the templates; presets Diagnostic, Dashboard, Minimal / Night; the `drive_mode` chip, rotation and list; server storage and R1; the no-scroll tests per mode | U2 lockouts; visual V1–V2 (tokens, gauge) |
| **DM2** | Drive mode editor (slot-first, settings sheet, live and Moving preview); file import/export, link and QR | DM1 |
| **DM3** | Home edit mode and widget picker with core widgets; the rail editor and pinning | DM1; U4/U5 Home cards |
| **DM4** | `contributes.widgets` in the registry (phase UA); Map preset (dark basemap V1c); Convoy (Social S1/S2, Vehicles & Map V2); Split / Media (a media source add-on); Off-road (IMU tilt derivation, `IsCentreDiffLocked` overlay leaf in the D2 pack) | app-model UA; add-ons |
| **DM5** | Layouts on Ostler Community (if Decision 8) | hub H1+ |

## Changelog

- 2026-10-07: v0.1, first draft (DMD round): layout format `ostler.layout/1` with a strict
  Moving section; seven presets with per-class wireframes and D2 data gaps; the `drive_mode`
  chip and rotation; editing for Home, rail and Drive with Park to edit; safety rules R1–R8;
  storage per vehicle × profile × class; import/export and validation; the widget contract
  summary (app-model §15, proposed); tests; phases DM1–DM5; decisions 1–10.

## Decisions for the owner

1. **Modes and faces as two levels?** Recommend: yes, as ShellInput defines them: the strip
   chip switches modes; D-pad `left`/`right` or a swipe switches 1–3 faces inside a mode (for
   example Dashboard's cluster and map); each face validated on its own. Alternative: one level
   only, each mode a single screen and `left`/`right` cycling modes (simpler, but more modes in
   the rotation).
2. **What does "one tap" mean on the chip?** Recommend: tap cycles a rotation of ≤ 4 modes;
   long-press (or D-pad `ok`) opens a list of ≤ 6. Alternative: tap opens the list (two taps to
   switch, but no blind cycling).
3. **How are user edits stored?** Recommend: a full copy with a `base` reference, Reset and an
   "Update from preset" view (amends §12.3's "per-vehicle diff" wording, keeps "never a fork").
   Alternative: a JSON Merge Patch (RFC 7396) over the base, as §12.3 literally says.
4. **May the rail hold add-on pages?** Recommend: yes, Home and More locked, three middle slots
   from core destinations and pinned `more:*` pages, the rest under More → Pages (amends §3.4
   and app-model §14.1's wording, not the cap). Alternative: core destinations fixed; add-on
   pages may take only a slot left empty (Security with no node).
5. **Default mode on head units?** Recommend: Dashboard (Split / Media on HU-wide when a media
   source exists); Diagnostic stays one tap away. Alternative: keep Diagnostic as the default
   and let users switch.
6. **Automatic switching?** Recommend: none while Moving; Convoy joins the rotation during a
   ride and Minimal / Night is suggested once at dusk, never applied by itself. Alternative:
   auto-switch to Convoy on ride start and to Minimal at night, with an undo chip.
7. **Media source for Split / Media.** Recommend: a widget from an add-on (Brain MPRIS or
   Spotify Connect bridge, or the phone app's native media session), preset hidden until one is
   enabled. Alternative: a core `media` source in the shell for the phone app only.
8. **Community layouts on Ostler Community?** Recommend: yes, as a file-only hub item type after
   H1, CC BY-SA 4.0, pre-moderated like other items. Alternative: files and a catalogue repo
   only, no hub item.
9. **Off-road tilt on the D2.** Recommend: derive static pitch and roll from the node IMU's
   levelled gravity vector as `candidate`, shown only below 0.1 g, and add the overlay leaf
   `Vehicle.Ostler.Powertrain.Transmission.IsCentreDiffLocked` in the D2 pack. Alternative: wait
   for gyro fusion on the node and leave the Off-road tilt tiles "Needs the node's IMU".
10. **Who may edit the Car profile's layouts on the head unit?** Recommend: anyone in the
    kiosk session when Parked, unless the owner turns on **Lock car layouts**. Alternative:
    owner only, always.
