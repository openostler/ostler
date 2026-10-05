---
title: "Generated UI and multi-vehicle research: capability manifests, render tiers, garage model"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [references/research/platform.md]
summary: >
  Prior art for UIs generated from what a vehicle or device declares (Home Assistant, OVMS, Signal K/KIP, Android Automotive, COVESA VSS, Grafana, rjsf, server-driven UI, RealDash/Torque) and for multi-vehicle apps. Recommends a capability manifest (systems, signals with canonical paths, DTC sources, safety-classed actions, devices, views), a three-tier renderer (generated, then declared, then custom component), a hidden module level for single-ECU cars, slot-based add-on cards, and a per-vehicle session store behind a garage config.
---

# Generated UI and multi-vehicle research

## 0. Where Ostler is today

- `GET /pack` returns the manifest and the pack's `layout.json`. For the D2 the top-level keys are `group_order`, `drive`, `body`, `util_lids`, `notices` and `replay`.
- `ui/src/layout.ts` wraps it in accessors: `moduleNames()`, `groupOrder()`, `driveView(m)`, `bodyLayout()`, `moduleNotices(m)` and `defaultModule()`. `ui/src/pack/store.ts` holds the one pack (`getPack()`/`usePack()`).
- `ui/src/vehicles/registry.ts` already provides the escape hatch: `registerViews(packId, {kind: Component})`. The `"tiles"` kind is generic and the D2's `BodyCar`/`SlabsCar` are custom.
- `src/openostler/commands.py` already has a safety class (`read | actuator | service | gated`) and a confirm level (`none | preconditions | typed`).
- `src/openostler/pack.py`: `active_pack()` is a **process-wide singleton**. The server assumes one vehicle.

**The gap:** the layout is shaped as "what the D2 needs" (`drive.td5.tiles`, `body.signals`). It is not shaped as "what any vehicle declares". The second pack (generic OBD-II) is the right moment to fix that, under the rule of two.

## 1. Prior art: generated or schema-driven UIs

### 1.1 Home Assistant (Apache-2.0: core and frontend)

The closest analogue, and worth studying in detail.

- **Entity model.** An integration creates *entities* in a *domain* (`sensor`, `binary_sensor`, `switch`, `button`, `climate`, `lock`, `alarm_control_panel`, `camera`, ...). Each entity declares a `device_class` (semantic type such as `temperature`, `voltage`, `door`), a `native_unit_of_measurement` and a `state_class` (`measurement`, `total_increasing`). It may also declare an `entity_category` (`config`/`diagnostic`; such entities are hidden from the default dashboard), plus `icon`/`translation_key`. The frontend picks the icon, the unit conversion, the graph type and the card from these alone. <https://developers.home-assistant.io/docs/core/entity/>, <https://developers.home-assistant.io/docs/core/entity/sensor/>
- **Device registry.** Entities hang off a *device* (`identifiers`, `manufacturer`, `model`, `sw_version`, `via_device` for hubs). A device belongs to an *area*, and a *config entry* (one integration instance) owns devices. That gives a three-level tree: integration instance, then device, then entity. <https://developers.home-assistant.io/docs/device_registry_index/>
- **Auto-generated dashboard.** With no user config, the default dashboard is produced by a *strategy* (`original-states`). It groups entities by area, then by domain, and picks one card type per domain (an entities card for sensors, a thermostat card for `climate`, and so on). It hides `entity_category` entities and hidden or disabled entities.
- **Strategies.** A strategy is a JS class that takes `hass` and config and *returns* a Lovelace config (`views` → `sections`/`cards`). Dashboards, views and sections can each be strategies, and custom strategies load as frontend modules. Generation is a pure function from the entity registry to card config. It is not a separate rendering engine. <https://developers.home-assistant.io/docs/frontend/custom-ui/custom-strategy/>
- **"Take control".** The user can freeze the generated output into editable YAML. From then on, new entities are no longer auto-added. That is a known UX pain point, and it argues for keeping *declared overrides as a diff over generated defaults* rather than a fork.
- **Custom cards.** `customElements.define('my-card', ...)` and `type: custom:my-card`. This is the escape hatch, and it is the same idea as our `registerViews`.

**Lessons.** (a) The semantic class plus unit is enough to render 90% of signals well. (b) Generation is a function that emits the same config a human could write, so there is one renderer. (c) The device and area grouping maps directly onto our vehicle, system (ECU) and group levels. (d) Diagnostic entities stay hidden by default. That maps onto our "Inputs"/raw LIDs.

### 1.2 OVMS v3 (MIT): see `references/research/ovms.md` for depth

- There is one **standard metric namespace** (`v.b.soc`, `v.e.*`, `v.p.*`, `v.m.*`, `v.b.12v.voltage`). Vehicle modules fill it, and vehicle-specific metrics use `xxx.*` prefixes. The web UI and the apps render the standard metrics without knowing the car.
- **Web plugins**: HTML fragments stored on the module and registered as a page, or as a *hook* into an existing page (for example `body.pre`/`body.post` on the dashboard). Widgets bind to metrics with `data-metric="v.b.soc"` and update live from the websocket metric stream. <https://docs.openvehicles.com/en/latest/components/ovms_webserver/docs/index.html>
- **Lesson.** Canonical paths are the contract that makes generic pages possible. Hooks into named slots let add-ons extend a page without owning it.

### 1.3 Signal K (Apache-2.0 spec and server); KIP (MIT), Instrument Panel (Apache-2.0)

- **Data model**: one tree per *context* (`vessels.urn:mrn:...`, `self`), with dotted paths (`navigation.speedOverGround`, `propulsion.port.revolutions`, `electrical.batteries.house.voltage`). Values are SI throughout (K, Pa, rad, m/s). The **meta** (`units`, `displayName`, `zones` with `normal/warn/alarm` ranges, `displayScale`) lives next to the value, so a client can draw any path without a lookup table. <https://signalk.org/specification/latest/doc/data_model.html>
- **Multi-instance by path segment**: `propulsion.<id>.*` and `electrical.batteries.<id>.*`. This is the same shape as "N ECUs" or "N batteries".
- **KIP** (<https://github.com/mxtommy/Kip>) lets a user drop a widget (gauge, numeric, chart), pick *any* path from the live tree, and auto-fill the unit and zones from meta. **Instrument Panel** (<https://github.com/SignalK/instrumentpanel>) auto-creates a widget per incoming path and lets you hide or rearrange them. That is a near-pure generated UI.
- **Lesson.** Put SI units, display hints and zones on the signal, not in the view. Our `span`/`normal`/`limits` already play the role of SK `zones`.

### 1.4 Android Automotive: VehiclePropertyIds and the Car API (AOSP, Apache-2.0)

- There is a fixed catalogue of **VHAL properties** (`PERF_VEHICLE_SPEED`, `HVAC_TEMPERATURE_SET`, `ENGINE_COOLANT_TEMP`, `DOOR_LOCK`, ...). Each property has a type, an access mode (READ/WRITE) and a change mode (STATIC/ON_CHANGE/CONTINUOUS with a sample rate). **Area IDs** scope a property to a zone (seat rows, doors, windows, mirrors, or GLOBAL). <https://developer.android.com/reference/android/car/VehiclePropertyIds>, <https://source.android.com/docs/automotive/vhal/properties>
- **Binding.** System apps (the AOSP HVAC panel and Car Settings) call `CarPropertyManager.getPropertyList()`/`getCarPropertyConfig()` and *only render the controls whose property and areas the car reports*. The HVAC UI shows per-seat controls only if `HVAC_TEMPERATURE_SET` has several area IDs, and a single GLOBAL area collapses the zoning. Writes are gated by permissions (`CONTROL_CAR_CLIMATE` and so on), not by UI code.
- **Lesson.** Render only what is declared. Zones and areas collapse when there is one. Safety and permission live on the property or action, so the UI cannot bypass them. That is our `safety` plus server refusal.

### 1.5 COVESA VSS (spec MPL-2.0; KUKSA tooling Apache-2.0)

- A tree of branches, sensors, actuators and attributes, e.g. `Vehicle.Powertrain.CombustionEngine.ECT`, `Vehicle.Cabin.Door.Row1.DriverSide.IsOpen`, `Vehicle.OBD.*`. It carries `datatype`, `unit`, `min/max`, `allowed` and *instances* (`Row[1,2]`, `["DriverSide","PassengerSide"]`). Overlays add OEM branches. <https://covesa.github.io/vehicle_signal_specification/>
- UIs on it (KUKSA dashboards, Digital.Auto prototypes) bind widgets to VSS paths through VISS/gRPC. They are thin and path-bound, like OVMS and SK. <https://github.com/eclipse-kuksa>, <https://digital.auto/>
- **Lesson.** VSS is the most "official" vehicle path vocabulary. It is verbose, but its leaf names are good aliases. Keep OVMS names as the primary canonical form (as platform.md already decided) and record a `vss` alias per signal where one exists. That costs little and keeps a door open.

### 1.6 Grafana panel and field config (AGPLv3, licence-compatible with Ostler AGPLv3)

- A panel = visualization type + a query. **Field config** is separate: `defaults` (`unit`, `decimals`, `min`, `max`, `thresholds`, `mappings` for value→text/colour, `displayName`, `color`), plus **overrides** that match fields by name/regex/type. <https://grafana.com/docs/grafana/latest/panels-visualizations/configure-standard-options/>, <https://grafana.com/docs/grafana/latest/panels-visualizations/configure-overrides/>
- **Lesson.** Separate "how to show a value" (field config) from "where it goes" (panel layout). Defaults come from the data source and overrides are small diffs. Our `tileConv`/`dec`/`gauge` per tile in `layout.json` are field config hiding inside the layout, so they belong on the signal.

### 1.7 JSON-schema form generators: rjsf (Apache-2.0)

- `schema` (data shape and validation) + `uiSchema` (widget, order, `ui:help`, hidden) → a form. Custom widgets and fields are registered by name. <https://rjsf-team.github.io/react-jsonschema-form/docs/>
- **Fit.** Good for **settings and action parameters** (device config, adaptation values, alarm thresholds). It is not good for live dashboards. Treat it as a candidate for "action with inputs" and device config pages once a second device needs a config form (rule of two). It costs about 100 kB+ of bundle, so a small hand-rolled schema→form for 4 input types may be enough.

### 1.8 Server-driven UI

- **Airbnb Ghost Platform** (proprietary, described publicly). The server returns *screens* made of *sections* (typed components with data) and a *layout* placement. Clients ship a registry of section components, and unknown section types are skipped. <https://medium.com/airbnb-engineering/a-deep-dive-into-airbnbs-server-driven-ui-system-842244c5f5>
- **Microsoft Adaptive Cards** (MIT): JSON card schema with versioned host capabilities and `fallback` for unknown elements. <https://adaptivecards.io/>
- **Lesson.** Version the schema, make unknown component types degrade (skip or fall back to a generic tile), and keep the component registry on the client. We already have that shape. We do not need a remote layout server; the pack *is* the server.

### 1.9 RealDash and Torque (both proprietary apps)

- **RealDash**: dashboards are hand-designed `.rd` files from a visual editor. Data comes from *XML channel descriptions* (CAN frames → `<value targetId=... units= conversion=...>`), which map onto a fixed set of internal *target IDs* (RPM, speed, etc.) plus custom ones. <https://github.com/janimm/RealDash-extras> (format docs and examples; check the licence before reuse).
- **Torque Pro**: themes plus user-placed gauges. *Extended PIDs* are CSV (name, short name, mode+PID, equation, min, max, unit, header), and *vehicle profiles* hold per-car settings (fuel type, engine size, weight, ECU protocol, PID set). <https://torque-bhp.com/wiki/PIDs>
- **Lesson.** Both prove that drivers want to **arrange their own gauges** on top of a data model. That is a later "user override" tier and not needed for v1. Torque's per-profile PID set is a direct precedent for per-vehicle config in a garage.

## 2. Prior art: multi-vehicle apps

| App | Vehicle identity | Per-vehicle data | Switching |
|---|---|---|---|
| **Tesla app / Fleet API** | `GET /api/1/vehicles` lists vehicles, each with `id`/`vin` | `vehicle_data` per id; commands are per id; each car wakes independently | Picker at the top; the last-selected car is remembered; one active car on screen |
| **OVMS app (iOS/Android)** | Vehicle ID + server per entry, with a car image and colour per entry | Separate connection and metric cache per vehicle | Car list / swipe; one active connection |
| **Torque Pro** | Vehicle profile | PID set, units, fuel and engine params; logs tagged by profile | Profile chooser; the adapter is shared, so only one is live |
| **Home Assistant** | Device (via config entry) | Entities namespaced by device; history per entity | No "active" device; areas and dashboards group them |

Docs: <https://developer.tesla.com/docs/fleet-api>, <https://docs.openvehicles.com/en/latest/userguide/app.html>.

**Patterns.** (1) A stable vehicle id that is *not* the pack id (two Discoveries share a pack). (2) Per-vehicle config + cache + logs. (3) One *active* vehicle in the UI, remembered per client. (4) Inactive vehicles show a last-known summary (Tesla, OVMS). (5) A physical adapter is live for only one vehicle at a time (Torque). K-line makes that a hard constraint for us.

## 3. Recommendation: capability manifest

Evolve `GET /pack`'s `layout` into a `capabilities` document. **Generate it in Python** from data the pack already has (`ModuleSpec`, signal store JSON, `Command`s, `FaultReader`s). Packs then only hand-write the optional `views`. Sketch:

```jsonc
{
  "schema": 1,
  "vehicle": {"pack": "lr_d2", "name": "Discovery 2 Td5"},
  "systems": [                       // = ECUs / logical modules; one entry for OBD-II
    {"id": "td5", "name": "Engine (Td5)", "category": "powertrain",
     "live": true, "dtc": "td5", "notices": {"record_confirm": "..."}}
  ],
  "signals": [
    {"id": "td5.coolant_temp", "system": "td5", "group": "Temperatures",
     "metric": "v.m.temp",            // canonical (OVMS name where one exists, else x.<pack>.*)
     "vss": "Vehicle.Powertrain.CombustionEngine.ECT",   // optional alias
     "class": "temperature", "unit": "°C", "dec": 0,
     "span": [-40, 130], "normal": [80, 100],
     "confidence": "proven",          // proven | candidate (data honesty)
     "category": null}                // null | "diagnostic" (hidden by default)
  ],
  "dtc_sources": [{"id": "td5", "system": "td5", "label": "TD5", "clear": true}],
  "actions": [{"id": "td5.injector_test_1", "system": "td5", "label": "Injector 1",
               "safety": "actuator", "confirm": "preconditions", "status": "experimental"}],
  "devices": [                        // add-ons, attached to this vehicle
    {"id": "guardian", "kind": "alarm", "name": "ESP32 guardian",
     "signals": ["..."], "actions": ["..."], "views": ["guardian.home"]}
  ],
  "views": [                          // optional; the only hand-written part
    {"id": "td5.drive", "slot": "drive", "system": "td5", "type": "tiles",
     "signals": ["td5.manifold_press", "td5.coolant_temp", "td5.battery"]},
    {"id": "body", "slot": "drive", "system": "body", "type": "lr_d2/body"}  // custom component
  ]
}
```

Rules:

- **Field config lives on the signal** (Grafana/SK). Move `dec`, `gauge`, `conv` and ranges out of `layout.drive.*.tiles` onto signals, so views list only signal ids.
- **Canonical path** = `metric`. The UI keys generic behaviour (health strip, MQTT/HA export, cross-vehicle "battery voltage" cards) on `metric` and never on pack-local ids.
- **`class` borrows HA `device_class` names** (`temperature`, `pressure`, `voltage`, `speed`, `door`, `light`, ...). That gives icons and card choice for free and maps 1:1 onto HA discovery.
- **Actions keep `safety`/`confirm`.** The UI renders friction from them and the server still refuses. `gated` is listed (for honesty) but never rendered as runnable. Same as AAOS: the permission lives on the property, not in the view.
- **Version** with `schema`. The UI skips unknown view types and unknown classes fall back to a plain value tile (Ghost/Adaptive Cards).
- Keep the D2-only leftovers (`util_lids`, `replay.group_categories`) under `x` (pack extras) until OBD-II needs an equivalent. That is the rule of two.

## 4. Recommendation: rendering strategy (three tiers per slot)

The UI has named **slots**: `home`, `drive`, `system:<id>` (the module page), `security` and `more`. Each slot is filled by one pure function, as in HA strategies:

1. **Generated** (always available). `generateViews(capabilities, slot)` → `View[]`.
   - `system:<id>`: signals of that system, grouped by `group` in `group_order` order, with `category: diagnostic` collapsed. Card choice comes from `class`: number to tile (gauge if `span`), binary to chip, enum to text. Actions are filtered by system and sorted by safety, and DTCs come from `dtc_sources`.
   - `home`/`drive`: the first N signals with a well-known `metric` (rpm, speed, coolant, battery, boost), in a fixed priority list. That is the cross-vehicle "health strip".
2. **Declared** (`capabilities.views`). When a pack declares a view for a slot, it replaces the generated one for that slot (not merged: predictable, and easy to debug). This is today's `layout.drive`, generalised.
3. **Custom component** (`type: "<pack>/<kind>"`). Resolved through the existing `registry.ts` (`registerViews`). If no component is registered, fall back to tier 1 for that slot.

Notes:

- Write tier 1 *when the OBD-II pack lands*. It is the first pack with no hand-written layout, which is the second user of the renderer. Until then the D2 runs on tiers 2+3 as it does now.
- A view is plain data (`{type, signals[], title}`), so generated and declared views go through one renderer (HA's key insight). Tests can snapshot `generateViews()` output without React.
- User rearrangement (KIP/Torque/RealDash style) is a later tier 0 stored per vehicle on the server, as a *diff* over tiers 1–3 (avoid HA's "take control" fork). Do not build it yet.

## 5. Recommendation: single-ECU cars hide the module level

- The rule lives in one place: `const multiSystem = caps.systems.filter(s => s.live).length > 1`.
- When false: no `ModuleSelect`, no module breadcrumb in `ScreenHead`, the `system:<only>` slot *is* the Diagnose page, and fault scan shows one row without the system label.
- This matches the AAOS HVAC rule (a single GLOBAL area collapses zones) and HA's device page.
- Generic OBD-II = one system `obd` (`dtc_sources`: Mode 03 stored, 07 pending, 0A permanent, each as a separate source with `clear` only on stored). Its signal list is built *at connect time* from the Mode 01 support bitmap, so `capabilities` must be re-fetchable (`GET /vehicles/<vid>/capabilities` after connect, with an `etag`). That is the first real need for dynamic capabilities.
- Keep `system` on every signal and action even with one system, so data and URLs stay uniform. Only the chrome hides.

## 6. Recommendation: add-on devices register cards and pages

- A device is **an entry in `capabilities.devices` plus its own signals, actions and views**, with ids prefixed by the device id (`guardian.armed`, `hevac.set_temp`). It uses the same manifest vocabulary, so the same generator and renderer apply. Like an HA device with `via_device`.
- Devices contribute views to **slots** (`home`, `security`, `more`, or a page of their own `device:<id>`). The UI renders a slot as `[vehicle views..., device views...]` in `order`. This is the OVMS page-hook model, so no device edits a pack layout.
- Custom device UI registers through the same registry under the device kind: `registerViews("device:alarm", {...})`. A pack id and a device kind are both just namespaces.
- **Server side.** For now the alarm (the first device) is a module inside Ostler that appends its block to `capabilities`. **When the AC/HEVAC controller arrives (the second device)**, extract a `DevicePack` entry point (`openostler.device`) that mirrors `VehiclePack`'s `capabilities()`. That is the rule of two.
- Devices attach per vehicle (`garage.json`, §7). A camera or relay box may be vehicle-less later; model that as a vehicle-less device only when it actually happens.
- Safety: device actions carry the same `safety` classes. An alarm "disarm" or relay "cut fuel" is `service` with `typed` confirm at least, and the server enforces it.

## 7. Recommendation: multi-vehicle data model (server)

**Config: `garage.json`** (in the state dir; the user edits it via the UI):

```jsonc
{"active": "d2-green",
 "vehicles": [
   {"vid": "d2-green", "pack": "lr_d2", "name": "Green D2", "vin": "SALLT...", "transport": {"port": "/dev/ttyUSB0"},
    "devices": [{"id": "guardian", "kind": "alarm", "url": "mqtt://..."}],
    "prefs": {"units": "metric"}},
   {"vid": "golf", "pack": "obd2", "name": "Golf", "transport": {"port": "/dev/ttyUSB0"}}
 ]}
```

**Runtime: `VehicleSession` per vid** (a lazily created dict `sessions[vid]`) holds the `VehiclePack` instance, `sources`, the last-known signal cache (with timestamps), the dynamic capabilities (OBD-II bitmap), the command lock, and the logbook root `logs/<vid>/`.

- **Pack loading.** Replace the `active_pack()` singleton with `load_pack(pack_id)`, cached per id, and have `active_pack()` return `sessions[garage.active].pack` for back-compat. Two vehicles of the same pack share the pack object but not the session.
- **API.** Add `GET /vehicles` (list plus last-known summary) and `POST /vehicles/active`, then route everything vehicle-scoped under `/vehicles/<vid>/...` (`capabilities`, `signals`, `command`, `sessions`). Keep the current unprefixed endpoints as aliases of the active vid for one release.
- **One live link per port.** Connecting vehicle B on a port held by A stops A's sources first. Never interleave K-line traffic (constitution protocol rules). Inactive vehicles show their cached summary with an age, as the Tesla and OVMS apps do.
- **UI.** `pack/store.ts` becomes a store keyed by vid with `activeVid`. `getPack()` returns the active vehicle's capabilities so the `layout.ts` accessors keep working. The remembered selection goes in `localStorage` as a convenience only; the server's `garage.active` is the source of truth. A *Garage* page lists cards (name, pack, last seen, a health chip) and a header switcher appears only when more than one vehicle exists (the same collapse rule as §5).
- **Logbook.** Tag every session with `vid` now (cheap and forward-compatible) even before the garage exists. Existing logs migrate to the single configured vid.
- **Rule of two.** Building the garage is justified once a second vehicle is real (the OBD-II pack on a second car, or a second D2). Until then do only the cheap seams: `vid` in logs, and `load_pack(id)` beside `active_pack()`.

## 8. Licences at a glance

| Source | Licence | Reuse stance |
|---|---|---|
| Home Assistant core/frontend | Apache-2.0 | Borrow vocabulary (`device_class`, `state_class`, `entity_category`); code is compatible with AGPLv3 if copied |
| OVMS v3 | MIT | Borrow metric names; compatible |
| Signal K spec/server | Apache-2.0 | Borrow the meta/zones idea |
| KIP | MIT | Ideas only |
| Instrument Panel | Apache-2.0 | Ideas only |
| AOSP Car API / VHAL | Apache-2.0 | Borrow property names as aliases if useful |
| COVESA VSS | MPL-2.0 (spec) | Path aliases fine; keep file-level MPL if we vendor the spec |
| Grafana | AGPLv3 | Compatible, but we only need the concept |
| rjsf | Apache-2.0 | Candidate dependency for config forms |
| Adaptive Cards | MIT | Ideas only |
| Airbnb Ghost | Proprietary (blog only) | Ideas only |
| RealDash, Torque Pro | Proprietary apps | Formats as import/export targets only; check licences before reusing samples |

## 9. Suggested order (each step justified by a second user)

1. Move per-tile field config onto signals and emit `capabilities` from Python (D2 only; no UI change).
2. OBD-II pack: write `generateViews()`, the single-system collapse, and dynamic capabilities.
3. Alarm device: `capabilities.devices` plus slot contributions. AC/HEVAC: extract `DevicePack`.
4. Second real car: `garage.json`, `VehicleSession`, `/vehicles/<vid>/...`, the Garage page.
5. Later: per-vehicle user layout diffs (tier 0) and rjsf-style config forms.
