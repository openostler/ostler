---
title: "Platform research — vehicle packs, plugins, MQTT/Home Assistant, alarm, mobile IA, phasing"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md, references/research/landscape.md, references/research/ovms.md]
summary: >
  How to grow the D2 tool into a universal platform without bloat: declarative per-vehicle packs (OBDb/OVD/Zigbee2MQTT-style, keeping our ranges/confidence/safety), a monorepo with core/vehicles/integrations layers and entry-point plugins, MQTT with HA discovery plus OVMS- and OwnTracks-compatible topics, a notify-only alarm owned by the ESP32 guardian, a Home/Diagnose/Logs/Security/More IA, and a phased roadmap with guardrails.
---

# Platform research

## 1. Vehicle packs: a declarative, per-vehicle definition that drives the UI

### How others define vehicles

| System | Unit of definition | Notes |
|---|---|---|
| **OBDb** | One repo per make and model. `signalsets/v3/default.json` holds `hdr`/`rax`/`cmd`/`freq`, and `signals[]` with `fmt` (`bix`, `len`, `mul`, `div`, `add`), `path` and `suggestedMetric`. Year overrides are allowed. | Organised by command; CAN-centric; CC BY-SA |
| **OpenVehicleDiag ECU JSON** | ECU → variants (matched by patterns) → errors, adjustments, actuations, functions, downloads | Closest to our actions-plus-signals model |
| **opendbc** | DBC files: `BO_` messages and `SG_` signals | Passive broadcast CAN only |
| **SAE J1979** | Mode 01 support bitmaps; Mode 09 VIN and ECU name | Lets us detect a vehicle procedurally |
| **UDS / ODX** | `0x22` DIDs, `0x19` DTCs; ODX/PDX XML (`odxtools`) | Import path only; too heavy for the core |
| **OVMS** | Per-vehicle C++ subclass, `poll_pid_t` with `polltime[state]`, a **standard metric namespace** | Per-state poll rates; canonical metrics |
| **Torque / Car Scanner** | CSV of custom PIDs | Export target |
| **Zigbee2MQTT / ESPHome** | Definition = decode + actions + `exposes`, with a code escape hatch | The best analogy |
| **Home Assistant entity model** | `device_class`, `unit`, `state_class`, `entity_category` | Vocabulary to borrow |

### Our store compared with OBDb

| Concept | OBDb | Ours today | Plan |
|---|---|---|---|
| Request | `hdr`/`rax`/`cmd` | `lid` (KWP `21` is implied) | Explicit `req` per ECU, so KWP `21`, UDS `22` and OBD `01` all fit |
| Bit position | `bix`/`len` (bits) | `offset` (bytes) + `kind` | Add bit-level positions and keep `kind` as shorthand |
| Scaling | `mul`/`div`/`add` | `scale`/`bias` | Equivalent; importer uses `scale = mul / div` |
| Ranges | `min`/`max` | `limits`, `span`, `normal` | **Keep ours (richer)** |
| Enums | `map` | ad hoc | Adopt `map` |
| Rate | `freq` | in code | Adopt, per vehicle state (parked / ignition / driving) |
| Canonical meaning | `suggestedMetric` | none | **Adopt `metric`**, using OVMS names where they exist (`v.b.12v.voltage`, `v.p.*`) |
| Provenance | none | `confidence`, `source` | **Ours is unique** (data honesty) |
| Actions | none | `commands.py` with a safety class | **Ours is unique** |
| Variants | year files | none | Adopt (D2 vs D2a, EAT vs manual) |

### Proposed layout

```
vehicles/lr_d2_td5/
  vehicle.json      # id, make, model, years, variants, detection, ecus[]
  ecus/td5.json     # transport (kline fast 10400 0x19) · protocol (kwp2000, session, security hook, keepalive)
                    # polls[] {req, rate{parked,ignition,driving}, signals[]} · actions[] {safety, confirm, preconditions}
                    # constraints {bus, max_rate_hz}
  ecus/slabs.json …
  dtc/*.json        # the existing dtc/ files move here
  hooks.py          # code escape hatch: keygen, odd decoders (named, referenced from the JSON)
```

**Rules:**
- `upsert_field` stays the only writer.
- The ESP32 header is generated from the pack.
- `catalog.py` still works out each item's status.
- The UI is generated from `group`, `metric`, `span`/`normal` and `actions.safety`.

**Detecting the vehicle:**
- **OBD-II cars:** Mode 09 VIN → manufacturer code (WMI) and model year → candidate packs, then Mode 01 bitmaps prune the list.
- **D2:** chosen manually, or found with a KWP `1A` ident probe.

**Interop:** import OBDb JSON and DBC files; export Torque CSV.

**Licence:** packs are vehicle data under CC BY-SA 4.0 (ADR-0012), the same licence as OBDb, so we can contribute a D2 pack back.

**Never ship converted dealer databases.** OpenVehicleDiag's SMR-D parser was taken down by DMCA.

## 2. Plugins and repo strategy

### Layers

The current SCOPE extends downwards and sideways:

```
Link drivers      serial-KKL | ESP32 bridge | SocketCAN | ELM327 | (J2534, low priority)
Network           K-line framing+init | ISO-TP (kernel CAN_ISOTP or own) | ELM-internal
Protocol          KWP2000 | UDS | OBD-II (J1979) | passive CAN (DBC)
Vehicle packs     lr_d2_td5 (reference) | generic_obd2 | …   → signals + actions + hooks
Sources           gps | imu | opto inputs | mic level | guardian link
──────── snapshot / event contract ────────
Integrations      web/UI | logbook | mqtt-ha | ovms-mqtt | owntracks | traccar | notifiers | community
```

### Plugins and dependencies

- **Plugin discovery** uses stdlib `importlib.metadata.entry_points`, in three groups:
  - `d2diag.transport`
  - `d2diag.vehicle`
  - `d2diag.integration`

  This is the same pattern python-can uses for its `can.interface` entry points.
- **CAN on the Pi:** stdlib `socket.AF_CAN` gives `CAN_RAW` and `CAN_ISOTP`, so no python-can is needed. python-can can be an optional driver for Mac and Windows dongles.

### Repo strategy: one monorepo, no fork

A fork would duplicate the protocol core and the signal store, which breaks constitution rule #3 (single source of truth).

1. **Restructure in place, with no behaviour change:**
   - split into `core/`, `vehicles/lr_d2_td5/` and `integrations/`;
   - extend `tests/test_layering.py` so that core imports neither vehicles nor integrations, and vehicles do not import integrations.
2. **Add `vehicles/generic_obd2/`** (ELM327 / SocketCAN with the OBDb SAEJ1979 data). This proves the platform is universal.
3. **Only then rename the distribution.** `d2diag` stays as the name of the D2 pack.
   - D2 remains the reference pack and the conformance fixture: CI fails if D2 coverage regresses.

## 3. MQTT and Home Assistant

### Topic layouts

All publishing is opt-in and off by default.

1. **Native Home Assistant device discovery** at `homeassistant/device/<id>/config` (`cmps`, `dev` and `o` blocks).
   - Re-publish when `homeassistant/status` goes online.
   - Two availability topics:
     - `brain`: the Pi, which runs only with the ignition on;
     - `tracker`: the ESP32 guardian, always on.
   - Set `expire_after` on live sensors, so "car off" never looks like valid but stale data.
2. **An OVMS v3-compatible tree**, so ovms-home-assistant and OVMS Connect work. See [ovms.md](ovms.md).
   - `ovms/<user>/<vid>/metric/<path>` (retained)
   - `event` and `notify/*`
   - `client/<cid>/command/<id>` → `response/<id>`
3. **OwnTracks JSON** for location, so Dawarich, Reitti and HA's OwnTracks integration work. Opt-in, because location stays on the device by default (ADR-0009).

### Entities

| Kind | Exposed |
|---|---|
| `sensor` / `binary_sensor` | Built from pack `metric`s |
| `device_tracker` | Location, opt-in only |
| `alarm_control_panel` | The software alarm |
| `event` | `alarm_triggered`, `fault_appeared`, `trip_ended` |
| `button` | **Read-only actions only.** Actuator, service and gated actions are never exposed remotely. |

### Delivery

- **Rate:** publish on change, with a deadband, at most about 1 Hz per entity.
- **Security:** TLS on port 8883, a broker ACL, and an allowlist of command topics.
- **Live state only.** MQTT does not backfill history. When coverage returns, history goes from the logbook to **Traccar OsmAnd** (stdlib `urllib`).

### Client

- A **stdlib MQTT 3.1.1 client** is feasible: about 300–400 lines covering QoS 0/1, LWT, reconnect and TLS. The precedent is MicroPython's `umqtt.simple`.
- `paho-mqtt` could be an optional extra, but that needs an ADR because the constitution keeps dependencies to the stdlib.
- The guardian uses ESP-IDF's `esp-mqtt`.

## 4. Alarm and tracker

**The software alarm watches and notifies; it never actuates.** Actuation (OEM disarm, immobiliser, remote start) stays gated, each with its own ADR (see the gps-tracker-alarm spec).

### States

Modelled on HA and [Alarmo](https://github.com/nielsfaber/alarmo):

```
DISARMED → ARMING (exit delay; baseline IMU/GPS captured) → ARMED_AWAY | ARMED_TRANSPORT (ferry/tow) | SERVICE
ARMED_* → ALERT_NOTICE (weak trigger; log + low-priority notify) | PENDING (entry delay) → TRIGGERED → ALERTING (escalation)
ALERTING → DISARMED (ack) | ARMED (timeout; retrigger cap per sensor)
TAMPER (guardian power loss, battery disconnect, GNSS jamming, bus silence) → always notify
```

### Triggers

| Trigger | Signal | Strength | Rule (starting values, to tune in the car via test_plan.md) |
|---|---|---|---|
| Ignition while armed | Ignition opto | Strong | Immediate |
| OEM siren / hazards | Opto | Strong | Immediate |
| Door / bonnet | Inputs | Strong | Entry delay if expected, else immediate |
| Tilt (jacking, towing) | Gravity vector compared with the armed baseline | Strong when sustained | More than about 3° for more than 10 s |
| GPS movement | Fix outside the geofence | Strong when corroborated | More than max(50 m, 3× accuracy) for 3 or more fixes, or above 5 km/h with the ignition off |
| Shock | IMU wake threshold | Weak | One shock gives a notice; several, or shock plus tilt, gives an alert |
| Cabin sound | Mic RMS above an adaptive baseline | Weak | Level only; **no audio recorded while armed** unless opted in |
| CAN anomaly (later) | Unknown IDs or timing | Weak | Research stage |

### How it behaves

- **Arming:** follows the OEM alarm through the opto input, so locking with the fob arms it. It can also be armed from the app or from HA.
- **Notification ladder:**
  1. HA / MQTT actionable notification
  2. **ntfy**
  3. Telegram
  4. **SMS through the modem** as the no-data fallback
- **The guardian owns all of this**, so an alert never waits for the Pi to boot.
- **Parked duty cycle** scales with battery voltage and days parked.
- **Alarm events and parked periods** land on the same logbook / flags timeline (ADR-0010).

## 5. Mobile information architecture

**Limits:**
- iOS HIG allows 3–5 tabs.
- Material 3 allows 3–5 in a navigation bar, or 3–7 in a navigation rail.
- Today we have 8 tabs, already scrolling at 393 px.

**Patterns we looked at:**
- DroneMobile: home widgets, plus separate map and alerts areas.
- Home Assistant 2025.9: an adaptive Home dashboard.
- Tesla: a status hero above rows of controls.
- Strava / TeslaMate: an activity feed leading to a detail map.
- Torque: dashboard first.

### Option A, recommended: `Home · Diagnose · Logs · Security · More`

| Destination | Content | Today's tabs |
|---|---|---|
| **Home** | Adaptive cards: live health when connected; security, location and last trip when parked. Add-on cards only when installed. Cards are generated from pack `metric`s. | Health strip |
| **Drive** | A full-screen live mode, opened from Home or automatically when connected and moving. A mini-bar returns to it. **Not a tab.** | Drive |
| **Diagnose** | Module list → per-module **Faults · Live · Tests · Settings · Utilities** | Faults, Inputs, Outputs, Settings, Utilities |
| **Logs** | One timeline: drives, parked periods, alarm events, faults, notes. Filter chips: Drives / Parked / Alerts / Faults. **Analysis** is the session detail. | Logs, Analysis |
| **Security** | Arm state, map, geofences, alerts (a filtered Logs view). Appears when a guardian is installed; otherwise the slot is "Map". | — |
| **More** | Add-ons (MQTT/HA, OVMS, OwnTracks, Traccar, notifiers), Settings, Privacy (location toggles), Developer (Decode / Label / Docs) | Admin tabs |

- **Wide screens** use a navigation rail with every destination.
- **`registry.ts`** gains `requires` (e.g. `"security"`) and `order`.

**Option B, rejected:** a mode switcher (Diagnose / Drive / Secure) changes the tab bar under the user and duplicates Logs and Map. It survives only as Home's adaptive card ordering.

## 6. Phasing and guardrails against bloat

| Phase | Scope |
|---|---|
| **0, now** | Extract the pack schema in place (no behaviour change); layering tests; the new IA |
| **1** | Opt-in, read-only MQTT/HA, OVMS-compatible topics, OwnTracks, Traccar OsmAnd, ntfy |
| **2** | ESP32 guardian (tracker + notify-only alarm); the Security tab appears |
| **3** | `generic_obd2` pack (proves the platform is universal) |
| **4** | CAN add-ons: relay box, head-unit/OBD emulator. **HEVAC is a separate ESP32 project** that we only talk to. |
| **Moonshot** | Remote OEM disarm, remote start, ODX/ARXML import, cloud fleet, other makes. **Each needs its own ADR and gate.** |

**Guardrails:**
1. **Rule of two:** no core abstraction until a second pack needs it. D2 and generic OBD-II are the two.
2. **D2 stays first-class:** it is the reference pack and conformance fixture, and ships as the default.
3. **The core only shrinks.** Everything else is a pack or an integration, and import tests enforce this.
4. **Safety travels with the action, not the transport.** Every path (UI, MQTT, HA, schedules) goes through the same gate. Remote paths get read-only actions only; arming the software alarm is its own low-risk class.
5. **A new top-level tab, a new outbound data path or a new runtime dependency each needs an ADR.** Five tabs is a hard cap.
6. **SCOPE.md names the layers:** core (comms + interpretation), packs (vehicles), integrations (consumers and add-ons).
