---
title: "UI architecture — one head-unit-first UI for every vehicle, many vehicles and add-on devices — design"
area: specs
status: stable
version: 0.2
updated: 2026-10-06
depends_on: [specs/2026-10-06-platform-direction-design.md, CONSTITUTION.md, references/research/platform.md, references/research/ui/obd_apps.md, references/research/ui/diag_tools.md, references/research/ui/vehicle_data_model.md, references/research/ui/head_unit_ui.md, references/research/ui/generated_ui.md, references/research/ui/ovms_ui.md, references/research/ui/decode_pipeline.md, references/research/standards.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, decisions/adr-0021-local-https-on-the-device.md]
summary: >
  Approved by the owner on 2026-10-06 (ADR-0016, ADR-0018). One UI generated from a per-vehicle capability manifest: head-unit-first layout classes with a driver-side rail and a persistent status strip, five destinations with Drive as a mode, Parked/Idling/Moving lockouts, a garage with an active-vehicle switcher, a vehicle → systems → function-areas tree that collapses for one-ECU cars, add-on devices (alarm, climate, cameras, tracker, relay box) that register into slots, five safety tiers plus a comfort class for our own add-ons, VSS canonical signal paths (VSS 6.1), an open-standards plan per phase, a read-only decode pipeline with a generic OBD-II fallback, and a phased migration that starts with cheap seams.
---

# UI architecture — design

**Status:** approved by the owner on 2026-10-06; the answers are in §11 and locked by
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) and
[ADR-0018](../decisions/adr-0018-ui-architecture-decisions.md). Each migration phase (§10) still
gets its own spec. It refines the IA row of the
[platform direction](2026-10-06-platform-direction-design.md) and changes none of its decisions.
The evidence is the seven notes in [`references/research/ui/`](../references/research/ui/), listed
in `depends_on`.

## 1. Context and goals

**Today.** `ui/src/App.tsx` is one 900 px column: a 56 px header with up to seven controls and a
bottom bar of eight public tabs (Drive, Faults, Inputs, Outputs, Settings, Utilities, Logs,
Analysis) plus three admin tabs (`ui/src/screens/registry.ts`). It knows one pack (`GET /pack`, a
process-wide `active_pack()`) shaped as the D2 `layout.json`, with custom views via
`ui/src/vehicles/registry.ts`. Nothing reads speed or gear, and faults pop up as a modal.

**Goals (the owner's brief).** (1) Every vehicle: generic OBD-II (one ECU), multi-ECU K-line cars
like the D2, modern CAN/UDS, pre-OBD, with no vehicle-type checks in screens. (2) More than one
vehicle, with a garage and a switcher. (3) The alarm/guardian (notify-only), the AC/HEVAC controller
(a separate ESP32 project we only talk to), cameras, the tracker and the relay box, without clutter.
(4) Head-unit first, still good on phone, tablet and desktop. (5) Generated UI evaluated, not
assumed (§5.3). (6) A dev pipeline for detecting and decoding cars (§8).

**Non-goals.** Media, CarPlay/Android Auto, radio and wheel controls stay on a media head unit
(direction spec). No new write path to any car. No cloud dependency.

## 2. Principles

1. **Generate from the manifest.** Render what the capability manifest (§5) declares, nothing else;
   screens never name a pack, module, device or vehicle type.
2. **Collapse a level with one member** (vehicle, system, camera). Data and URLs keep every level.
3. **Honest states.** A missing value is never zero, an unscanned system is never OK, `candidate`
   and stale look different, and nothing unsupported is greyed out as if it were for sale.
4. **Head-unit first.** Design at 1024×600 (76 px targets, 24 px gaps, 32/24 px text, the 2 s / 12 s
   glance rules), then relax for phone and desktop. Driving state gates the UI, not discipline.
5. **Safety travels with the action.** The server enforces tier, driving state and remote rules on
   every path; the UI only adds friction.
6. **The rule of two.** Generated tier with `generic_obd2`, `DevicePack` with the second device,
   garage with a second real vehicle; until then only cheap seams.
7. **Calm instrument.** ISO 2575 colours for telltales only, a word with every icon, motion only for
   red alarms, night dark automatically.

## 3. Information architecture

### 3.1 Layout classes

Chosen by aspect and height, not width alone; a kiosk flag (`?display=headunit&side=left|right`)
overrides detection because head-unit browsers report odd DPIs. The 900 px cap stays only on phone.

| Class | Trigger | Shell (px) | Content area |
|---|---|---|---|
| **HU-7** 1024×600 | landscape, height ≤ 640 | rail 96 · strip 56 | 928×544: Home 2×2 cards; Drive mode 3×2 tiles, values ≥ 56 px |
| **HU-9/10** 1280×720 | landscape, height ≤ 800 | rail 112 · strip 64 | 1168×656: Home = vehicle card 40 % + 2×2; Diagnose = list 380 + detail |
| **HU-wide** 1920×720 | aspect ≥ 2.4 | rail 112 · strip 64 | vehicle pane 520 (always on) · main 768 · secondary 520 (camera, mini-timeline); a page widens main over secondary |
| **Phone** 360–430 × 780–930 | portrait, width < 600 | strip 48 · bottom bar 72 + safe area | ~393×730, one column; Drive mode 2×3 tiles |
| **Tablet** | width ≥ 600, height > 800 | rail 88 · strip 56 | two panes (list 360 + detail) |
| **Desktop** | width ≥ 1200, fine pointer | rail 88 with labels · strip 56 | two or three panes; denser type when Parked |

### 3.2 The persistent status strip

One row, never scrolls. Each chip is ≥ 48 px tall, pairs icon and word, and opens a sheet. Left to
right by severity:

| # | Chip | Content |
|---|---|---|
| 1 | **Vehicle** | active vehicle name; only when the garage holds > 1 vehicle (§4.1) |
| 2 | **Worst telltale** | highest active warning, ISO colour, count; replaces the fault modal while Moving |
| 3 | **Link** | connection-ladder rung + the system holding the ECU session (§4.5) |
| 4 | **REC** | logging state; tap → Logs |
| 5 | **Security** | Disarmed / Armed / Alerting, or the tracker fix in Map mode (§6) |
| 6 | **Device slot** | climate setpoint + fan, or a live-camera chip; one on HU-7/phone, two on HU-wide |
| 7 | **12 V** | from the vehicle, else the guardian |
| 8 | **Clock** | |
| 9 | **Mark** | one-tap flag, the one action safe at any speed |

The phone keeps chips 2–5 and 9; the rest move to Home cards. Module select moves to Diagnose,
Rewind to Logs, the cog to More. Service mode and replay add a strip badge.

### 3.3 Driver-side rail versus bottom bar

Landscape classes use a **vertical rail on the driver's side**: wide-screen production systems keep
status and controls nearest the driver, and a bottom bar wastes the short axis of a 600 px screen.
The side comes from the vehicle's `driver_side` (the D2 is RHD), with the kiosk flag as override.
Portrait uses a **bottom bar** for thumb reach (five items at 72–86 px fit 393 px). The rail holds
only the five destinations, plus a Drive-mode button on head units, so it never scrolls.

### 3.4 Five destinations

`Home · Diagnose · Logs · Security (Map) · More`, a hard cap of five (direction spec). Destinations
register into the shell with `slot`, `order`, `requires` and `trust`, as OVMS pages do, so the nav
is built, not hard-coded.

| Destination | Contents | From today |
|---|---|---|
| **Home** | Zero-layer cards (§5.4): vehicle card (silhouette + health), role tiles, warnings, last trip, parked security/location, device cards, the "unknown vehicle" banner, a large **Drive** button | Drive's health strip |
| **Diagnose** | Identity bar · **Scan all** · system list (§4.2) · per system **Overview · Faults · Live · Tests · Procedures · Settings** · fault → related live data and tests | Faults, Inputs, Outputs, Settings, Utilities, ModuleSelect |
| **Logs** | One timeline: drives, parked periods, alarm events, faults, notes, scan reports. **Analysis** is the session detail; replay and Rewind live here | Logs, Analysis, Rewind |
| **Security** | Alarm state, events, tracker map, geofences, clips (Parked only). **Map** when no guardian | — |
| **More** | Garage, Devices, Integrations (MQTT/HA, OVMS, OwnTracks), Preferences, Privacy, **Developer** (Decode mode, Label, Coverage, Docs), About (service-mode entry) | cog, admin tabs |

The D2 keeps its NanoCom words as **pack labels** over the canonical areas (Live → Inputs, Tests →
Outputs, Procedures → Utilities). An area with no items disappears; one the pack declares but has
not mapped stays visible as `untranscribed`.

### 3.5 Drive mode, driving states and service mode

**Drive mode** is full-screen, not a tab: role tiles plus pack extras, the strip and a back target.
It opens from Home, and automatically on entering Moving on head-unit classes.

**Driving state** is computed by the platform, so the server can enforce it, from vehicle speed (any
system in session), then GPS speed (guardian or u-blox), then proven gear/handbrake signals.

| State | Rule | Allowed | Locked ("Available when parked") |
|---|---|---|---|
| **Parked** | speed 0 for > 5 s and engine off, or handbrake/neutral where known | everything its tier allows | — |
| **Idling** | engine running, speed 0 | reading, Logs, cameras, text entry; Tier 2 only if the action declares `engine_running_ok` | Tiers 1, 3, 4; video other than cameras |
| **Moving** | > 5 km/h for > 2 s; leave below 2 km/h for 3 s | Drive mode, telltale sheet (≤ 30 characters a line), Mark, reverse/low-speed camera, climate setpoints | Tiers 1–4, text entry, Docs, Analysis, replay scrubbing, clip playback, system switching, Decode and service mode (auto-exit), lists > 6 items or > 2 levels |

**Unknown speed** counts as Moving on head-unit classes. A phone is a passenger device we cannot
verify: reading stays open and actions keep today's "vehicle stationary" precondition. K-line
carries one session at a time, so in a SLABS session the Td5 speed is absent and GPS covers it.

**Service mode** merges admin and Experimental: a long-press on the version line in More → About
plus the server password; while on, a thick coloured frame round the viewport, a strip badge,
Experimental items and Decode mode. It is refused, and exits, when Moving.

## 4. The vehicle model in the UI

### 4.1 Garage and active-vehicle switcher

- **A vehicle id (`vid`) that is not the pack id**, since two D2s share one pack. `garage.json`
  (state dir) holds `active` and per vehicle: `vid`, `pack`, name, `driver_side`, transport,
  attached devices, units and a VIN **fingerprint** (§4.4).
- **One active vehicle** in the UI, remembered per client as a convenience; the server's
  `garage.active` is the truth. Inactive vehicles show a last-known summary with its age.
- **One live link per port.** Activating B on a port held by A stops A's sources first (released on
  K-line); K-line traffic is never interleaved.
- **Switcher:** the strip's Vehicle chip opens a sheet of vehicle cards; More → Garage edits them.
  With one vehicle neither appears. Every session carries `vid` from U0.

### 4.2 Vehicle → systems → function areas

Vehicle (garage) → Diagnose: identity bar · Scan all · Systems → *System* → Overview · Faults ·
Live · Tests · Procedures · Settings, plus fault → related live items and tests. Collapse rules:

| Live systems | Behaviour | Example |
|---|---|---|
| **1** | No system level: Diagnose opens on the function areas, the system name is a subtitle. Several OBD responders (7E8/7E9) are a **source tag** on each code or value | generic OBD-II, one-ECU pre-OBD |
| **2–12** | A flat list with a status chip and fault count per row; the list pane beside detail on head units, a list screen plus a compact "current system" switcher on phones | the D2 (6), most K-line cars |
| **> 12** | Grouped by domain (powertrain, chassis, body, comfort, safety), fault-free groups collapsed, search; topology only if the pack declares bus wiring | modern CAN/UDS |

The rule lives in one place: `multiSystem = systems.filter(s => s.live).length > 1`. On K-line there
is no gateway, so the pack lists plausible systems per variant and the user may mark a probed one
**Not fitted**.

### 4.3 Scan all and its honest states

One vocabulary across scan, system list and reports: `Not scanned` · `Scanning` · `OK` · `Faults n`
· `No response` · `Not fitted` · `Not supported yet`, each with its age; the last two separate
"absent from the car" from "absent from the tool". K-line scans run one system at a time (establish
→ read → release) with per-row progress and Stop. A scan saves a **report** to Logs (identity
masked, every row, codes with freeze frame, key values **with confidence**, every action), paired
before/after repair and exported as HTML and JSON; uploads are opt-in.

### 4.4 Identification and fallbacks

Tried in order, stopping at the first confident match:

1. **Read identity:** OBD Mode 09 VIN, CALID, ECU names; UDS `F187`/`F189`; KWP `1A`.
2. **Decode the VIN on the device,** in memory, against a bundled WMI/model-year table. Only `{make,
   model_year, region}` and a masked form (`SAL…****`) leave that function. The VIN is **never
   logged, recorded, captured, put in fixtures or uploaded**; the garage keeps an HMAC under a
   device-local secret to recognise the car again. Online lookups (e.g. NHTSA vPIC) are opt-in and
   masked.
3. **Match pack `detection`:** WMI + year, CALID/ECU-name or `F187` patterns, K-line probes.
4. **Ask only what changes the topology** (make → model → engine/gearbox/options), never a protocol
   list.
5. **Fall back** to `generic_obd2` on an OBD car, or "choose your vehicle / start a pack".

### 4.5 The connection ladder

`No adapter → Adapter (type, quality hint) → Bus (K-line init / CAN bitrate / ELM protocol) → ECU
session: <system> → Data flowing`, plus 12 V. The chip shows the highest rung and the session
holder; the sheet names the failed rung and what to try. Values go stale-grey when a rung drops.
Launch auto-connects with the active vehicle's adapter.

## 5. Capability manifest

### 5.1 Shape

Data the UI renders. `GET /pack` grows into it; later `GET /vehicles/<vid>/capabilities` (`etag`).

```jsonc
{ "schema": 1,
  "vehicle": { "vid": "d2-green", "pack": "lr_d2", "name": "Discovery 2 Td5", "variant": "D2a",
               "identity": { "source": "kwp_1a|obd_09|manual", "vin_masked": "SAL…****" } },
  "systems": [ { "id": "td5", "name": "Engine (Td5)", "category": "powertrain", "live": true,
                 "transport": { "bus": "kline", "init": "fast", "address": "0x13", "protocol": "kwp2000" },
                 "areas": { "live": "Inputs", "tests": "Outputs", "procedures": "Utilities" } } ],
  "signals": [ { "id": "td5.coolant_temp", "system": "td5", "group": "Temperatures",
                 "metric": "Vehicle.Powertrain.CombustionEngine.EngineCoolant.Temperature",
                 "class": "temperature", "unit": "Celsius", "dec": 0, "span": [-40, 130],
                 "normal": [80, 100], "confidence": "proven", "category": "primary",
                 "rate": { "parked": 0, "ignition": 1, "driving": 5 } } ],
  "dtc_sources": [ { "id": "td5", "system": "td5", "kind": "kwp_18", "clear_action": "td5.clear_faults" } ],
  "actions": [ { "id": "slabs.compressor", "system": "slabs", "safety": "actuator", "tier": 2,
                 "confirm": "preconditions", "status": "verified", "states": ["parked"], "remote": false } ],
  "devices": [ { "id": "guardian", "kind": "alarm", "transport": "mqtt", "signals": ["guardian.state"],
                 "actions": ["guardian.arm"], "slots": { "strip": "security", "destination": "security" } } ],
  "views": [ { "id": "body", "slot": "home", "type": "lr_d2/body" } ], "x": { "util_lids": [] } }
```

Rules: **field config lives on the signal** (`dec`, `class`, `span`, `normal`, `limits`), so views
list only ids. **`confidence` stays two-valued** (CONSTITUTION): a J1979 decode is `candidate` per
car until a car result exists. **`class`/`category` borrow Home Assistant's `device_class` and
entity categories** (`diagnostic` collapses by default). **Unknown types degrade** to a generated
tile; `schema` is versioned. **D2-only leftovers stay under `x`.** **`unit` is a key copied verbatim from
the pinned VSS 6.1 `units.yaml`** (`Celsius`, `km/h`, `kPa`), checked by a test (ADR-0016).

### 5.2 Generated by the platform from the pack

Packs do not hand-write the manifest. The platform builds it from `ModuleSpec` (systems), the signal
store (signals), `dtc/` and `FaultReader`s (DTC sources), `Command`s (actions), `layout.json`
(views) and a short `vehicle.json`. `generic_obd2` builds the same shape **at connect time** from
the support bitmaps and Mode 09: the first need for a re-fetchable manifest.

### 5.3 Three rendering tiers

Generated UI is adopted, bounded. Each **slot** (`home`, `drive`, `system:<id>`, `security`,
`device:<id>`, `more`) is filled by one pure function:

1. **Generated:** `generateViews(caps, slot)`. A system page is its signals by `group`, card by
   `class` (number → tile, gauge with `span`; binary → chip; enum → text), actions by tier, DTCs
   from `dtc_sources`. Home and Drive come from roles (§5.4).
2. **Pack-declared:** a `views` entry **replaces** the generated view for its slot (no merge, so it
   stays predictable). This generalises today's `layout.drive`.
3. **Custom component:** `type: "<pack>/<kind>"` via the existing `registerViews`; with nothing
   registered, the slot falls back to tier 1.

All three emit plain view data into one renderer, so `generateViews()` is snapshot-tested without
React. **Not adopted:** a remote layout server, runtime-composed or model-composed screens, and
user-arranged dashboards; the last may come later as a per-vehicle diff over tiers 1–3, never a
fork.

### 5.4 Home built from roles

Roles in fixed order: **speed, rpm, coolant, battery, fuel**, then **health** (MIL/DTC count,
readiness where it exists), then up to N pack extras (the D2 boost tile). Per role the best source
of that `metric` wins: vehicle over add-on, `proven` over `candidate`, fresh over stale, then
manifest order. Registry fallbacks: fuel → range → consumption; speed → wheel speeds → GPS. No
source shows "Not available on this car", never zero. The D2 has no decoded fuel level, so Home uses
the derived economy figure, marked `candidate`.

### 5.5 The OVMS lesson

OVMS solved generic-versus-specific inside the module (one metric tree, a page registry with a
vehicle menu) but never sent capabilities over the wire: its capabilities message is a stub and the
Android app branches on `car_type` dozens of times, so users meet "unsupported operation" ([OVMS UI
§6](../references/research/ui/ovms_ui.md)). Therefore **capabilities reach the UI as data, and
screens never test a vehicle type.** The literal guard (`ui/src/vehicles/literalGuard.test.ts`)
extends to "no pack, module or device ids outside `ui/src/vehicles/`". We also copy OVMS's opt-in
shared page templates (ECU list, live table, 12 V monitor, TPMS) and named hook slots (header, body,
footer on every page).

### 5.6 Canonical signal namespace (decided: ADR-0016)

[Vehicle data model](../references/research/ui/vehicle_data_model.md) makes VSS paths canonical;
[generated UI](../references/research/ui/generated_ui.md) and [platform
research](../references/research/platform.md) prefer OVMS names. **Decided: the `metric` value is a
COVESA VSS path, and OVMS, Home Assistant and OBDb names are generated aliases** in one platform
registry (`metrics.json`: VSS unit, display units, OVMS alias, HA `device_class`/`state_class`, OBDb
`suggestedMetric`, default span, Home role). Extensions live in a small overlay `Vehicle.Ostler.*`
(MIL, DTC count, readiness, ride-height counts); pack-private fields need no metric.

**Why:** the canonical tree must name every meaning on every vehicle class. OVMS is EV-shaped, with
no names for fuel level or much of the body, so ICE and pre-OBD cars would live in `x*` prefixes.
VSS covers powertrain, body and cabin, is maintained and OEM-backed, and its 6.0 removal of the
one-to-one OBD branch matches our "one meaning, many sources" model. **OVMS compatibility is kept:**
the OVMS topic tree is generated from the alias column. Drivers never see the long paths (the UI
keys on roles). Vendored `.vspec` files stay MPL-2.0. **Locked by
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md):** VSS pinned to 6.1; the
overlay `vss/ostler.vspec` is the single source; `src/openostler/metrics.json` is generated with
vss-tools (dev-only) and checked in CI; the OVMS alias table comes from OVMS `metrics_standard`
([OVMS reuse §6](../references/research/ovms_reuse.md)); QUDT, not UCUM; the extension branch is
`Vehicle.Ostler.*` (decided).

## 6. Add-on devices

A device is an entry in `capabilities.devices` with its own signals, actions and views, ids prefixed
by the device id (`guardian.armed`, `hevac.set_temp`). Devices contribute to **slots** and never
edit a pack layout; each kind may claim one strip slot and one destination or More → Devices page.
Device actions pass the same gate (§7). The guardian comes first, as a built-in module appending its
block; **the second device (HEVAC) triggers a `DevicePack` entry point** (`openostler.device`)
mirroring `VehiclePack`.

| Device | Strip | Home card | Page | Actions and gating |
|---|---|---|---|---|
| **Alarm / guardian** (notify-only) | Security: Disarmed / Armed / Alerting / Tamper | parked: state + last event | **Security**: state, events (filtered Logs), map | arm/disarm of the *software* alarm only; it never actuates the car. Remote: arm/disarm and reads only |
| **AC / HEVAC** (separate ESP32, its own API) | climate chip: setpoint + fan; HU-wide may add a bottom climate strip | cabin/ambient temps | More → Devices → Climate | setpoints are `comfort` actions on our own device, not car writes (ADR-0018); allowed while Moving; not remote by default |
| **Cameras** (go2rtc) | live-camera chip; REC shared | last clip (Parked) | Security → Clips (Parked); HU-wide secondary pane | reverse pre-empts the screen **only once a fast path exists**, assist-only until then; underbody/front live below 10 km/h; no playback unless Parked. **Future:** 360° surround view as another camera kind under the same rules (owner note, ADR-0018; own spec) |
| **Tracker** (in the guardian) | in the Security chip (fix age) | location when parked (opt-in) | Security / Map | read-only; location stays on the device unless opted in (ADR-0009) |
| **Relay box** (private CAN, Phase 4) | none by default | user-pinned channels | More → Devices → Relays | each channel declares its tier, default Tier 2, Parked only, never remote; interlocks on the device and the server |

With no device fitted nothing renders: no empty cards or greyed slots; Security shows Map.

**`comfort` class (ADR-0018).** A device action may declare `comfort` only if it never writes to
a vehicle ECU or bus (HEVAC setpoints, camera switching). Comfort actions are allowed while Moving,
are not remote by default, and still pass the server gate. Anything that reaches the vehicle keeps
the tiers in §7. CAN transmit rules are in
[ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md).

## 7. Safety gating tiers

The tier is derived by the platform from the existing `safety` vocabulary (`read | actuator |
service | gated`) and `confirm` levels in `commands.py`, never typed by a pack. One server gate
serves every path; the UI only renders friction.

| Tier | From | Examples | Gate | States |
|---|---|---|---|---|
| **0 Read** | `read` | codes, live data, ident, readiness | none; stale-grey on link loss | all |
| **1 Clear** | action flagged `clears` | clear DTCs (KWP `14`, OBD `04`) | one confirm naming system and consequence ("Clear 3 codes from SLABS? Freeze frames will be lost"); offer a report first; re-read to verify | Parked |
| **2 Actuate** | `actuator` | lamps, relays, compressor, injector test | precondition checklist from live data, else ticked; ActiveTestBanner with Stop; auto-timeout; leaving stops it | Parked (Idling if `engine_running_ok`) |
| **3 Procedure** | `service` | bleed, height calibration, adaptive reset | step wizard, preconditions re-checked each step, 12 V floor, abort anywhere; typed confirm | Parked |
| **4 Code** | `gated` | coding, security access, airbag or calibration writes | **listed for honesty, never runnable;** the server refuses | none |

**Constitution rules unchanged:** nothing writes to the car without these gates; Airbag/SRS is
read-only by construction; no SecurityAccess, coding or write is sent, and no sniffed write
replayed, without its own ADR; actuator tests are documented as stationary with ignition on. Also:
remote paths get Tier 0 only (plus software-alarm arm/disarm); Tiers 1–3 are refused while Moving or
below the "ECU session" rung; `candidate`/`experimental` status shows on the button and in the
confirm; buttons name the action; every Tier 1+ action is logged with before/after values. A write
tier with backup and diff would need its own ADR. **Imported actions** (OVMS, ADR-0019) keep their
tier, are `experimental` and `remote: false`, and run only in service mode, Parked, with a per-action
confirmation; imported Tier 4 writes stay disabled until their own ADR.

## 8. Decode pipeline and Decode mode

### 8.1 Stages

Detail: [decode pipeline §6](../references/research/ui/decode_pipeline.md). All read-only.

| # | Stage | Output |
|---|---|---|
| S0 | **Connect:** listen-only bitrate probe, ELM/OBD auto-detect, pack probes | `link.json` |
| S1 | **Identify:** local VIN decode, CALID/ECU names, KWP `1A`, pack `detection` | a pack, or `generic_obd2` + "unknown vehicle" |
| S2 | **Inventory:** read-only ECU sweep (modscan, UDS `3E`/`10 01`, passive CAN ID census) | `ecus.json`, identity redacted |
| S3 | **Baseline:** supported PIDs and DTCs | a working dashboard on day one |
| S4 | **Capture:** reference-tool sniff with markers, differential toggles, or drive-and-correlate against OBD/GPS/IMU | scrubbed `trace.json` |
| S5 | **Correlate:** `automap`, clean-room bit-flip segmentation, lagged correlation | proposals with R² and lag |
| S6 | **Label:** name, `metric`, unit, map via `upsert_field` | field, `candidate` |
| S7 | **Verify:** distinct readings, fixture, second car, review | `proven` with evidence |
| S8 | **Package:** `ostler pack new` skeleton → full pack; OBDb/DBC export | installable pack |
| S9 | **Contribute:** opt-in anonymous readings or a PR bundle | shared data |

Sweeps send only `3E`, `10 01`, `22`, `19`, `1A`, `21` and inits, never `27`, `2E`, `2F`, `30`,
`31`, `3B`, `11`, `14`, `28`/`85` or fuzzing; ignition on, engine off, Parked, rate-limited,
stopping on a burst of negative responses; K-line always releases.

### 8.2 `generic_obd2` and "unknown vehicle — help decode it"

`generic_obd2` is a real pack behind the same contract, selected when no pack's detection matches.
It imports the OBDb SAEJ1979 signalset as attributed data, speaks J1979 and J1979-2 (UDS), builds
its manifest at connect time, and ends today's `NoVehiclePackError` dead end. Home then shows a
dismissible banner, **"Unknown vehicle — help decode it"**, with the coarse identity and the number
of ECUs that answered without a definition; it offers a cached OBDb make/model overlay (all
`candidate`) and opens Decode mode at Scan. On a non-OBD car it leads to "choose your vehicle /
start a pack".

### 8.3 Data, evidence, fixtures and scrub

- **OBDb-compatible with an `x-ostler` block.** The store stays the source of truth (ADR-0003) but
  each field becomes OBDb-expressible (`hdr`/`rax`/`cmd`/`proto`/`freq`,
  `fmt{bix,len,mul,div,add,map,unit}`, `path`, `suggestedMetric`); `confidence`, `evidence`, ranges
  and safety sit in `x-ostler`, which OBDb tooling ignores. OBDb `freq` is in seconds (correcting
  platform.md). CC BY-SA 4.0 data can go upstream.
- **Evidence.** `evidence {source, readings, distinct, r2, cars, fixtures, reviewer}`. `candidate` =
  one solver or importer hit (imports never go higher). `proven` = ≥ 2 distinct readings at R² ≥
  0.999 against a reference, ≥ 1 committed fixture from a real capture, and a second person's
  review.
- **Fixtures.** Labelled captures become OBDb-style YAML (`response` → `expected_values`); `pytest`
  decodes every one, and a failure demotes the field.
- **Scrub** runs before any fixture commit, export or upload: it strips VIN (Mode 09 `02`, UDS
  `F190`, KWP `1A 87/90`), serials (`F18C`), EKA codes and seed/key pairs, and coarsens GPS, time
  and odometer. CI fails on a VIN pattern or identity DID under `tests/`.

### 8.4 Decode mode in the UI

In **More → Developer**, behind service mode, refused while Moving: **Detect → Scan → Sniff →
Correlate → Label → Verify → Contribute**, growing today's admin Decode and Label tabs. Sniff is a
byte grid with a bit-flip heat map; Verify shows the evidence checklist; Contribute previews the
exact JSON before anything leaves. `CoverageMap` stays the progress view.

## 9. Comparison

Production systems are evidence only ([head-unit UI §2](../references/research/ui/head_unit_ui.md)).

| Aspect | Ostler today | Proposed | Tesla | Polestar (AAOS) | OVMS | Dealer tools |
|---|---|---|---|---|---|---|
| Navigation | 8 bottom tabs + 3 admin | 5 destinations, rail or bar | car column + bottom dock | facet rail + 4 home tiles | Main · Tools · `<Vehicle>` · Config | vehicle → system → function |
| Persistent status | unordered header chips | severity-ordered strip | status column + top bar | status bar + climate bar | none | VCI/battery bar |
| Many ECUs | header module select | list pane; collapses at 1, groups > 12 | hidden | hidden | hidden (metrics) | system list / topology |
| Many vehicles | no | garage + switcher | app picker | profiles, one car | app spinner | VIN per session |
| Generated UI | no (D2 layout) | 3 tiers from a manifest | no (one fleet) | property-driven controls | metric widgets; apps hard-code | "only supported functions" |
| Driving lockout | none | Parked/Idling/Moving, server-enforced | yes | CarUxRestrictions | no | n/a |
| Service mode | `/admin` + banner | hidden entry + frame, exits on Moving | hidden + code + red frame | developer settings | per-page password | dealer login |
| Climate | none | device chip + page | bottom bar | climate bar | on/off + schedule | n/a |
| Security / cameras | none | Security; clips Parked only | sentry icon + parked viewer | OEM app | notifications | n/a |
| Data honesty | verified/candidate | + scan states + evidence | none shown | none shown | staleness | Not scanned / No response |
| Capabilities as data | `/pack` + `/catalog` | versioned manifest | closed | VHAL config | stubbed | closed DB |
| Local-first | yes | yes; VIN never leaves | cloud app | cloud services | own server | often cloud |

## 10. Phased migration

Each phase is small, testable and shippable, with its own spec. U0–U3 sit in the direction spec's
Phase 0, U5 in its Phase 2, U4 in its Phase 3.

| Phase | Ships | Test |
|---|---|---|
| **U0 Seams** | `vid` on every logbook session (old logs migrate to one vid); optional `metric` (VSS path) on store records via `upsert_field`; `metrics.json` common set; the D2 pack fills its set | unit tests; D2 coverage unchanged; no UI change |
| **U1 Shell** | layout classes, strip, rail / bottom bar, five destinations holding today's screens (§3.4), Drive mode, module select into Diagnose, fault modal → telltale | Playwright at 1024×600, 1280×720, 1920×720, 393×852; target-size asserts |
| **U2 Driving state** | platform driving state (vehicle → GPS), UI lockouts, server refusal of Tiers 1–3 while Moving, service mode with frame | Moving fixture locks actions, text and video; server tests |
| **U3 Manifest** | Python-generated capabilities (D2 on tiers 2+3), field config onto signals, derived tiers, Scan all with seven states and reports | golden manifests for D2 and the fake pack; scan-state tests |
| **U4 Second pack** | `generic_obd2`, `generateViews()` (tier 1), single-system collapse, connect-time manifest, local VIN decode, unknown-vehicle banner | view snapshots; ELM fake; a test that no VIN reaches logs |
| **U5 Devices** | guardian in `devices`, Security destination and chip; HEVAC then extracts `DevicePack`; cameras | device fake; "no device, no chrome" tests |
| **U6 Garage** | `garage.json`, `VehicleSession` per vid, `/vehicles/<vid>/…` (old routes alias the active vid), switcher, Garage page | two fake vehicles on one port, never interleaved |
| **U7 Decode** | evidence block, `fixtures`, `scrub` CI (D2 proven fields first), OBDb import/export, then Decode-mode screens | fixture and scrub CI |

U6 waits for a real second vehicle and `DevicePack` for the second device. U7's fixtures and scrub
may move earlier if the owner wants evidence before the second pack.

### 10.1 Standards per phase

Policy: [ADR-0017](../decisions/adr-0017-open-standards-first.md). The artefacts and verdicts live in
[standards §8](../references/research/standards.md#8-adoption-plan); each phase spec cites them.

| Phase | Standards that land with it |
|---|---|
| **U0** | `vss/` (VERSION 6.1, upstream, `ostler.vspec`) and the generated `metrics.json` (ADR-0016); `schemas/` in JSON Schema 2020-12 (store, layout, vehicle, capabilities); `api/openapi.yaml` 3.1 and `api/asyncapi.yaml` 3.0; RFC 3339 UTC timestamps; REUSE/SPDX, SBOM, SECURITY.md, Scorecard and Dependabot as the repo-wide items |
| **U1** | WCAG 2.2 AA with WAI-ARIA APG and an axe scan per layout class; W3C design tokens (`ui/tokens/*.tokens.json`); Material Symbols SVG subset; Web App Manifest; `Intl` (CLDR) for units |
| **U2** | NHTSA / Android for Cars numbers as normative; ASVS L1 on the gate; refusals in the OpenAPI error schema |
| **U3** | `capabilities.schema.json`, VISS-shaped datapoints `{value, ts}`, `etag`; golden manifests checked by pytest and vitest |
| **U4** | OBDb SAEJ1979 import (ADR-0019); J1979 / J1979-2 as references; local VIN decode under GDPR minimisation; SocketCAN `CanLink` if CAN is used (ADR-0020) |
| **U5** | **Needs the threat model first** (STRIDE + ASVS L2, `references/threat_model.md`); MQTT 3.1.1 with HA discovery, the OVMS alias tree, OwnTracks, Traccar OsmAnd, CloudEvents; AsyncAPI MQTT channels |
| **U6** | `garage.schema.json`; SOVD as a naming reference for `/vehicles/<vid>/…`; HMAC VIN fingerprint |
| **U7** | OBDb-compatible export; DBC import via cantools (dev-only); OVMS import behind the review gate (ADR-0019); REUSE on fixtures |

Triggered, not phased: service workers once the local-HTTPS trust setup ships (ADR-0021); ICU MessageFormat with a second
locale; MQTT 5 and OpenAPI 3.2 when tools support them.

## 11. Decisions (2026-10-06)

The owner answered every question; Q1 with "yes Covesa … try and use standard and open frameworks
where possible", Q2–Q11 with "yes" to each recommendation. Q1 is
[ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md) (with the policy in
[ADR-0017](../decisions/adr-0017-open-standards-first.md)); Q2–Q11 are
[ADR-0018](../decisions/adr-0018-ui-architecture-decisions.md).

| # | Question | Decision |
|---|---|---|
| 1 | Canonical namespace | COVESA VSS 6.1 paths; OVMS/HA/OBDb names are generated aliases (§5.6, ADR-0016) |
| 2 | Function-area names | Canonical areas with pack labels; the D2 still reads Inputs/Outputs/Utilities |
| 3 | Rail side | The vehicle's `driver_side` (right for the D2); the kiosk flag overrides |
| 4 | `comfort` class | Yes, only for our own add-ons that never write to a vehicle ECU (§6); car actions keep the five tiers |
| 5 | Unknown speed | Moving on head units; on phones reading stays open, actions keep the stationary precondition |
| 6 | Generated UI scope | The three tiers; user-arranged dashboards deferred; no remote layout server or composed screens |
| 7 | VIN in the garage | HMAC fingerprint and masked form only, never the full VIN |
| 8 | Service-mode entry | Long-press plus password; `/admin` kept on desktop for one release |
| 9 | Reverse pre-emption | Only after the fast path exists; assist-only until then. 360° cameras are a future item (§6) |
| 10 | U4 / U5 order | Guardian (U5) first; `generateViews()` only with `generic_obd2` |
| 11 | Write/coding tier | Tier 4 non-runnable; any write path needs its own ADR |

Related: reuse from OVMS and OBDb is [ADR-0019](../decisions/adr-0019-reuse-from-ovms-and-obdb.md);
CAN links are listen-only by default ([ADR-0020](../decisions/adr-0020-can-links-listen-only-by-default.md)).

**Also decided on 2026-10-06:** the extension branch is `Vehicle.Ostler.*` (ADR-0016); the Pi serves
local HTTPS so phones get service workers ([ADR-0021](../decisions/adr-0021-local-https-on-the-device.md));
all OVMS vehicles and commands are imported, with commands disabled behind the gates (ADR-0019);
EKA read/set stays in the D2 pack, gated and opt-in (GOALS §10).

**Still open:** whether `docs/` is CC BY-SA; CRA legal advice before the first sale.

## Notes on sources

- **python-OBD licence (conflict resolved).** Checked 2026-10-05: PyPI metadata says `GPL-2.0-only`
  and the README "GNU GPL v2", but the `obd/__init__.py` header says "version 2 … or (at your
  option) any later version". They disagree, so we take the conservative reading ADR-0012
  requires, GPL-2.0-only. Either way: ideas only, no code.
- **URLs from the generated-UI note** came from prior knowledge. Checked 2026-10-05: reachable are the
  HA strategy and entity docs, OVMS web-framework docs, Android `VehiclePropertyIds`, Grafana
  overrides, rjsf, Adaptive Cards, the Tesla Fleet API and VSS docs; **broken** are the Signal K
  `latest` data-model page (the 1.7.0 page works) and the OVMS app guide; **unverified** (GitHub
  unreachable here) are KIP, OBDb SAEJ1979/`.schemas` and the Signal K repo. No decision rests on
  them.

## Changelog

- 2026-10-06: v0.1, first draft from the seven UI research notes; resolves the namespace (VSS
  canonical) and python-OBD licence conflicts.
- 2026-10-06: v0.2, approved. §11 becomes the owner's decisions (ADR-0016, ADR-0018; also ADR-0017,
  ADR-0019, ADR-0020); §10.1 adds the standards plan per phase; §5.1 unit fixed to the VSS 6.1 key
  `Celsius`; §5.6 locked by ADR-0016; §6 adds the `comfort` class and 360° cameras as a future item; §7 adds imported actions (ADR-0019);
  local HTTPS decided (ADR-0021).
