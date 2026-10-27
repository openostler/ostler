---
title: "AAOS vehicle data — what a third-party Android Automotive app can read"
area: references
status: draft
version: 0.1
updated: 2026-10-27
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, references/research/head_unit_experiments.md]
summary: >
  A Play-distributed app on Android Automotive OS can read battery level, charge rate,
  range, speed, gear, outside temperature and plug state through CarPropertyManager with
  normal or user-granted (dangerous) permissions, but not climate, diagnostics or raw bus
  data, and only what the OEM's VHAL implements. The calculator fits the templated POI
  category at best, with a templates-only UI while driving. Keep the Ostler bridge for
  depth and history; add an AAOS app as an optional extra source that publishes to the
  gateway over VISS.
  Written for the trip calculator (openostler/ostler-trip-calc) and ADR-0054.
---

# AAOS vehicle data: what a third-party app can read

Question: on a car with Google built-in (test car: 2021 Volvo XC40 Recharge P8), can the
trip calculator get its car data straight from Android Automotive OS (AAOS)? Is the Ostler
bridge still needed?

Short answer: yes for a useful core set, no for depth. AAOS gives a clean, permissioned,
read-mostly view of a few dozen standard properties. It never gives raw CAN, diagnostics or
per-cell data to a third-party app. The bridge stays.

Status key: **[doc]** checked against an official page on 2026-10-27; **[src]** checked
against AOSP source; **[unverified]** from memory or secondary reports, needs a check on
the car.

## 1. What a third-party app can read

### 1.1 Protection levels decide everything

A Play app is not platform-signed, so it can only hold `normal` permissions (granted at
install) and `dangerous` ones (the user grants them at runtime). Anything
`signature|privileged` is out of reach. Levels below are from the AOSP car service
manifest **[src]** and the `VehiclePropertyIds` reference **[doc]** (page dated
2025-10-09).

| Permission | Level | Third-party? |
|---|---|---|
| `android.car.permission.CAR_INFO` | normal | yes |
| `android.car.permission.CAR_ENERGY_PORTS` | normal | yes |
| `android.car.permission.CAR_EXTERIOR_ENVIRONMENT` | normal | yes |
| `android.car.permission.READ_CAR_DISPLAY_UNITS` | normal | yes |
| `android.car.permission.CAR_POWERTRAIN` | normal | yes |
| `android.car.permission.CAR_ENERGY` | dangerous | yes, user grant |
| `android.car.permission.CAR_SPEED` | dangerous | yes, user grant |
| `android.car.permission.CAR_MILEAGE_3P` | dangerous | yes, user grant (new; see below) |
| `android.car.permission.CAR_MILEAGE` | signature/privileged | no |
| `android.car.permission.CONTROL_CAR_CLIMATE` | signature/privileged | no |
| `android.car.permission.CONTROL_CAR_ENERGY` | signature/privileged | no |
| `android.car.permission.CAR_DIAGNOSTICS` | signature/privileged | no |
| `android.car.permission.CAR_VENDOR_EXTENSION` | signature/privileged | no |

### 1.2 Properties the calculator wants

| `VehiclePropertyIds` | Read permission | Third-party? | Use in calculator |
|---|---|---|---|
| `EV_BATTERY_LEVEL` (Wh) | `CAR_ENERGY` | yes | energy now |
| `INFO_EV_BATTERY_CAPACITY` (Wh, nominal) | `CAR_INFO` | yes | pack size |
| `EV_CURRENT_BATTERY_CAPACITY` (Wh, usable now) | `CAR_ENERGY` | yes, but newer **[unverified: Android 15+]** | SoC % |
| `EV_BATTERY_INSTANTANEOUS_CHARGE_RATE` (mW) | `CAR_ENERGY` | yes | live charge power |
| `EV_CHARGE_STATE`, `EV_CHARGE_TIME_REMAINING` | `CAR_ENERGY` | yes | charge session |
| `EV_CHARGE_PERCENT_LIMIT` | `CAR_ENERGY` (write needs `CONTROL_CAR_ENERGY`) | read only | target SoC |
| `EV_BATTERY_AVERAGE_TEMPERATURE` | `CAR_ENERGY` | yes, but newer **[unverified: Android 15+]** | charge-speed hint |
| `EV_CHARGE_PORT_CONNECTED`, `EV_CHARGE_PORT_OPEN` | `CAR_ENERGY_PORTS` | yes | plugged in |
| `RANGE_REMAINING` (m) | `CAR_ENERGY` (write is privileged) | yes | car's own range |
| `PERF_VEHICLE_SPEED`, `PERF_VEHICLE_SPEED_DISPLAY` | `CAR_SPEED` | yes | cruise speed |
| `PERF_ODOMETER` | `CAR_MILEAGE_3P` or `CAR_MILEAGE` | only where `_3P` exists | trip distance |
| `GEAR_SELECTION`, `PARKING_BRAKE_ON` | `CAR_POWERTRAIN` | yes | parked/driving |
| `ENV_OUTSIDE_TEMPERATURE` | `CAR_EXTERIOR_ENVIRONMENT` | yes | consumption model |
| `DISTANCE_DISPLAY_UNITS`, `EV_BATTERY_DISPLAY_UNITS` | `READ_CAR_DISPLAY_UNITS` | yes | units |
| `INFO_MAKE`, `INFO_MODEL`, `INFO_MODEL_YEAR` | `CAR_INFO` | yes | car profile |
| `HVAC_POWER_ON`, `HVAC_AC_ON`, `HVAC_TEMPERATURE_SET` | `CONTROL_CAR_CLIMATE` (read and write) | **no** | climate load |

Notes:

- A property is only there if the OEM's VHAL implements it. Use
  `CarPropertyManager.getPropertyList()` and treat every value as possibly unavailable.
- `CAR_MILEAGE_3P` is recent. The Car Hardware page still says mileage is "not available
  to AAOS apps installed from Google Play" **[doc, 2026-09-08]**. On the XC40, expect no
  odometer **[unverified]**; integrate speed instead, or use the cloud API.
- The XC40 Recharge got AAOS 13 support in Volvo software 4.2.13 **[doc: Volvo release
  notes]**. AAOS 13 is API 33, so properties added in API 34 or later will not exist there.
- No HVAC read means the climate load must be inferred from consumption or temperature.

### 1.3 Car App Library: `CarHardwareManager` / `CarInfo`

The Car App Library wraps a subset in `androidx.car.app.hardware` (car API level 3+)
**[doc, Car Hardware APIs, 2026-09-08]**:

| `CarInfo` call | Data | AAOS permission |
|---|---|---|
| `fetchModel` | make, model, year | `CAR_INFO` |
| `fetchEnergyProfile` | EV connector types, fuel types | `CAR_INFO` |
| `addEnergyLevelListener` (`EnergyLevel`) | battery %, fuel %, range remaining | `CAR_ENERGY`, `CAR_ENERGY_PORTS`, `READ_CAR_DISPLAY_UNITS` |
| `addSpeedListener` (`Speed`) | raw and display speed | `CAR_SPEED`, `READ_CAR_DISPLAY_UNITS` |
| `addMileageListener` (`Mileage`) | odometer | not available to Play apps on AAOS |
| `addEvStatusListener` (`EvStatus`) | charge port open/connected | `@ExperimentalCarApi`, library 1.2.0 **[doc]**; permission likely `CAR_ENERGY_PORTS` **[unverified]** |
| `fetchExteriorDimensions` | dimensions | `CAR_INFO`, API 30+, some cars |

`CarSensors` returns `STATUS_UNIMPLEMENTED` on AAOS; use `SensorManager` and
`LocationManager` instead **[doc]**. `CarInfo` is the same code on Android Auto and AAOS,
but it has no charge rate, no charge state and no capacity. A templated app can still call
`CarPropertyManager` directly for those **[unverified: allowed in Play review]**. Any
category of templated app can use `CarInfo`; no category gate is documented.

## 2. App types, distribution and distraction rules

| Type | AAOS on Play? | UI while driving | Fit for calculator |
|---|---|---|---|
| Templated: Navigation | yes | templates + own map surface | only if it does routing; heavy |
| Templated: POI (CHARGING and PARKING folded in, library 1.3) | yes | list/map/pane templates | **best fit**: chargers as places, with time and cost per stop |
| Templated: IoT, Weather | yes | templates | no |
| Media, Messaging, VoIP | media yes; messaging/calling Android Auto only | system UI | no |
| Parked: Video, Games, Browsers | yes (browsers "labs") | blocked while driving (DD-2, DD-3) | no; not a calculator category |

Key rules from the car app quality guidelines **[doc, 2026-09-14]**:

- PC-1: "The app must not include features outside the app types intended for cars."
  A bare calculator is not a category. It must be framed as a POI charging-planner.
- PE-1 (Media, Navigation, POI, IoT on AAOS): apart from setup, settings and sign-in
  while parked, the app must not offer functions through its own activities. So the
  driving UI is templates only: no custom views, no WebView.
- Car apps get manual review. If an update fails it is blocked until approved.
- Templates carry Google's driver-distraction limits (step counts, list lengths, text
  length) **[doc, Car App Library overview]**.

Fallback with no review: a sideloaded or internal-testing build. That is fine for the
owner's car, but not for distribution **[unverified: Volvo may block sideloading in
production builds]**.

## 3. Volvo specifics

- **Allow-lists.** OEMs choose which VHAL properties to implement and can add vendor
  properties behind privileged permissions. Volvo publishes no public list of the
  standard properties it exposes to Play apps **[unverified]**. Volvo's developer portal
  offers an AAOS emulator image, which is not proof of what the real car returns. Plan a
  property census on the car first (dump `getPropertyList()` with the permission and
  status of each).
- **Browser.** Chrome reached select Volvo and Polestar cars as a beta at CES 2024
  (reports list all XC40 Recharge versions); it is parked-only **[src: press, January
  2024]**. Vivaldi was first on Polestar 2 (December 2021), then went on Google Play
  (September 2023), but Volvo-branded cars are not confirmed. The PWA could run in the
  browser when parked. It gets **no car data**: there is no web API for vehicle
  properties. PWA install and offline service workers in in-car Chrome are
  **[unverified]**.
- **Cloud APIs** (developer.volvocars.com; Volvo ID OAuth, owner consent, VCC API key):
  - Energy API v2: `GET /energy/v2/vehicles/{vin}/state` gives battery %, electric range,
    charging status and more, each field OK or ERROR; `/capabilities` lists the fields
    each car supports **[src: portal search snippets; the portal blocked direct fetch]**.
  - Connected Vehicle API v2: odometer, statistics, lock, windows, vehicle details.
  - Extended Vehicle API: deprecated, shut down on 31 December 2025.
  - Rate limits of about 100 per minute and 10,000 per day are from a third-party listing
    **[unverified]**.
  - Use: pre-trip SoC and odometer away from the car. Not for live speed: it is polled,
    needs a network and depends on Volvo terms.

## 4. What AAOS will not give, so the bridge stays

| Need | AAOS to a third-party app | Ostler node/bridge |
|---|---|---|
| Raw CAN frames, other buses | never; the VHAL abstracts the bus | yes |
| Per-cell voltages and temperatures, pack current/voltage | no standard property (vendor-only if at all) | yes, via ECU requests (pack-dependent) |
| DTCs, freeze frames, live UDS/KWP data | `CarDiagnosticManager` is privileged (`CAR_DIAGNOSTICS`) | yes (the platform's core job) |
| Fine charging curve (kW at 1 Hz, limits, BMS reasons) | `INSTANTANEOUS_CHARGE_RATE` only, if implemented; rate not guaranteed | yes, at bus rate |
| Climate state and power | privileged | yes, if on the bus |
| Odometer on Play builds | only with `CAR_MILEAGE_3P` (new) | yes |
| History while the head unit sleeps | the app is not running | gateway records |
| Older and non-AAOS cars (the D2 pack) | none | yes |
| MQTT, Home Assistant, RealDash outputs | not an AAOS feature | gateway's External MQTT (ADR-0051) |

## 5. Stack implications

Constraint: on AAOS the driving UI must be Car App Library templates built in Kotlin. A
WebView is allowed only in parked setup or settings screens (PE-1).

| Option | How | For | Against |
|---|---|---|---|
| A. Web core + Kotlin port, shared JSON test vectors | TS core for the PWA; small Kotlin re-implementation of the maths; both pass the same `vectors/*.json` | idiomatic on each side; no runtime cost; vectors keep them honest | two codebases for the model; drift between test cases |
| B. Headless JS engine in the AAOS app | run the TS core in QuickJS or a hidden WebView, then render templates in Kotlin | one model codebase | JS bridge, start-up cost and memory on the head unit; Play review of embedded engines **[unverified]**; awkward debugging |
| C. Kotlin Multiplatform core | write the core in Kotlin, compile to JS/Wasm for the PWA and JVM for AAOS | one typed codebase and one test suite | the PWA team writes Kotlin; JS output size and tooling; breaks the "React/TS for screens" line (ADR-0050 v1.1) |

Suggested: **A**. The core is small (energy per km against speed and temperature, charge
time from a curve table, cost per stop), so a port is days, not weeks. The JSON vectors
become the specification. B is the fallback if the model grows large. C is worth
revisiting only if more Ostler apps need AAOS-native logic.

Whatever the choice: keep the core pure (inputs in, plan out), make the data source a
port (`VehicleDataSource`: manual, VISS, AAOS, cloud), and name inputs in VSS paths
(`Vehicle.Powertrain.TractionBattery.StateOfCharge.Current`,
`Vehicle.Speed`, `Vehicle.Exterior.AirTemperature`). Then AAOS and VISS map onto one
model.

## 6. Recommendation for a proposed ADR: "AAOS as a direct vehicle-data source"

Options:

1. **AAOS-direct only.** The app reads `CarPropertyManager` and nothing else. Simplest,
   no hardware, works for any owner of a Google built-in car. But it is capped at about 20
   standard properties, depends on the OEM's VHAL, has no history while the car sleeps,
   cannot help older cars and gives Ostler nothing.
2. **Bridge only.** Everything comes through the node and gateway over VISS. Full depth,
   one data model, consistent with ADR-0049 and ADR-0051 ("the node stays the only path
   to the car"). But each car needs hardware and a vehicle pack. The XC40 has no pack yet,
   so the calculator would wait on reverse engineering.
3. **Both: an AAOS adapter publishing to the gateway.** A small Kotlin "AAOS source" reads
   the permitted properties and serves them as a read-only VISS source (or feeds a local
   gateway), mapped to VSS. Apps keep talking only to the gateway. A node adds depth when
   fitted. External MQTT stays the gateway's job.

**Recommendation: option 3, staged.** First, the calculator works with manual inputs and
an optional AAOS source, which needs no node. Second, the AAOS source is treated as a
**read-only, non-gate source** in the gateway, like an adapter (ADR-0044). It never
writes, and it never stands in for the node gate. It is labelled with its origin and
rate, so data honesty holds. Third, where a node is fitted, node values win and AAOS
values become a cross-check. This needs ADR-0049's "the node stays the only path to the
car" to be amended to "the only *write* path; read-only platform sources such as AAOS and
OEM clouds may feed the gateway". Trade-offs: one more source to map and test; Play review
risk on the AAOS app (POI framing); per-OEM property gaps found only on real cars. In
return the calculator ships on the XC40 without hardware, and Ostler gains a
zero-hardware entry point. Raw CAN, diagnostics, cell data and fine charging curves keep
the bridge clearly relevant.

## Open checks on the car

1. Census of `getPropertyList()` on the XC40 (software version, API level, each property's
   status and update rate).
2. Is `EV_BATTERY_INSTANTANEOUS_CHARGE_RATE` live while DC charging, and how often?
3. Does Chrome on the XC40 install a PWA and keep it offline?
4. Is sideloading or Play internal testing possible on a production Volvo?
5. Energy API v2 `capabilities` for the test VIN.

## Sources

- [VehiclePropertyIds reference](https://developer.android.com/reference/android/car/VehiclePropertyIds), Android Developers, updated 2025-10-09.
- [Car service AndroidManifest.xml](https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/service/AndroidManifest.xml), AOSP main, read 2026-10-27 (protection levels).
- [VHAL system properties](https://source.android.com/docs/automotive/vhal/system-properties), AOSP, updated 2026-09-24.
- [Car Hardware APIs](https://developer.android.com/training/cars/apps/library/car-hardware-api), updated 2026-09-08; [CarInfo reference](https://developer.android.com/reference/androidx/car/app/hardware/info/CarInfo).
- [Android for Cars App Library](https://developer.android.com/training/cars/apps); [POI apps](https://developer.android.com/training/cars/apps/poi), updated 2026-09-08.
- [Parked apps](https://developer.android.com/training/cars/parked), updated 2026-10-23.
- [Car app quality guidelines](https://developer.android.com/docs/quality-guidelines/car-app-quality), updated 2026-09-14.
- [What's new with Android for Cars](https://android-developers.googleblog.com/2022/05/whats-new-with-android-for-cars.html), Android Developers Blog, May 2022.
- [XC40 Recharge software release notes](https://www.volvocars.com/za/support/car/xc40-recharge-pure-electric/software-release-notes/), Volvo Cars (AAOS 13 in 4.2.13).
- Volvo developer portal: [Energy API v2](https://developer.volvocars.com/apis/energy/v2/overview), [energy state](https://developer.volvocars.com/apis/energy/v2/endpoints/energy-state), [Connected Vehicle API v2](https://developer.volvocars.com/apis/connected-vehicle/v2/overview), [Extended Vehicle API news](https://developer.volvocars.com/news/extended-api-news).
- [Vivaldi on Android Automotive on Google Play](https://vivaldi.com/?p=596457), Vivaldi, 13 September 2023; [Vivaldi on Polestar 2](https://androidcentral.com/android-automotive-adds-its-first-browser-vivaldi-polestar-cars), Android Central, December 2021.
- [Chrome added to select Volvo and Polestar models](https://www.caradvice.com.au/news/google-chrome-added-to-select-volvo-polestar/), CarAdvice, January 2024.
- [Android vehicle data requirements](https://wiki.covesa.global/x/04DbBw), COVESA wiki.
- [Volvo Cars provider profile](https://providers.apievangelist.com/providers/volvo-cars/), API Evangelist (third-party; rate limits).
