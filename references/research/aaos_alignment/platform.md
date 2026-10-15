---
title: "Android Automotive platform architecture compared with Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-15
summary: >
  AAOS layering (apps, Car API, CarService, VHAL, vehicle networks), feature control, VHAL properties and permissions, SDV, multi-display and the cluster, Scalable UI, power, users and the QM/safety split, compared with Ostler’s node gate, gateway, VSS/VISS, packs, shell layout and power ADRs. Mostly aligned; gaps listed. Plan for the owner’s head unit: a gRPC VHAL served from the host as a VISS client, a first VSS-to-VHAL table, Ostler owning the cluster.
---

# Android Automotive OS platform architecture vs Ostler

Research note, 2026-10-15. Read-only research: no repo was modified. Facts about AAOS come
from source.android.com and the Android Developers Blog, as read on 2026-10-15. Where a
detail could not be confirmed in an official page it is marked **(U)** (unverified).

---

## Part 1. AAOS: what the platform is

### 1.1 The layer cake

```
Apps (Maps, media, OEM apps)               distractionOptimized activities, car permissions
  │  Car API: CarPropertyManager, CarPowerManager, CarOccupantZoneManager,
  │           CarUxRestrictionsManager, CarAppFocusManager, ClusterHome…
  ▼
CarService (com.android.car, runs as user 0, the ONLY Java client of the VHAL)
  │  checks every Car API permission; hosts CarFeatureController, CarPowerManagementService,
  │  CarDrivingStateService, CarUxRestrictionsService, occupant zones, cluster services
  ▼  AIDL IVehicle (Android 13+, HIDL before)
Vehicle HAL (VHAL)  DefaultVehicleHal (generic) + IVehicleHardware (vendor/bus-specific)
  │  the only component connected to the in-vehicle network; filters and rate-limits
  ▼
Vehicle networks (CAN, LIN, SOME/IP…) via a VMCU, or a host/VM over gRPC-over-vsock
```

- **Access path.** Java apps reach vehicle properties only through `CarPropertyManager`;
  direct VHAL access is blocked by SELinux. CarService is the only Java VHAL client, and all
  Car API permission checks happen there. Native code uses `libvhalclient` (`IVhalClient.h`).
- **Vehicle system isolation** (security guide): apps need permission to reach car
  subsystems; generic APIs "do not accept arbitrary data blobs"; CarService is updated only
  by OTA/USB with verified boot; the VHAL is the only component on the vehicle network and
  can rate-limit messages so an app cannot flood the CAN bus. SELinux filters driver calls.

### 1.2 The VHAL property model

- **Property ID** is a bit-OR of four fields: group (`SYSTEM` 0x10000000 or `VENDOR`
  0x20000000), area type (4 bits), value type (8 bits) and a 16-bit unique ID. Example:
  `INFO_VIN` = 0x11100100 (SYSTEM, STRING, GLOBAL, 0x0100).
- **Value types:** STRING, BOOLEAN, INT32(_VEC), INT64(_VEC), FLOAT(_VEC), BYTES, MIXED.
- **Area types:** GLOBAL, WINDOW, MIRROR, SEAT, DOOR, WHEEL. A zoned property is addressed by
  an area ID combining enum flags (`ROW_1_LEFT | ROW_1_RIGHT`).
- **Access:** READ, WRITE, READ_WRITE (per area; the config reports the most restrictive
  common subset). System properties must match `VehicleProperty.aidl`.
- **Change modes:** STATIC (fixed after boot), ON_CHANGE, CONTINUOUS (reported at a
  subscribed rate between `minSampleRate` and `maxSampleRate`; Android 15 adds
  `supportVariableUpdateRate` so subscribers get updates only on change).
- **Config:** `configArray`/`configString`, per-area min/max, `supportedEnumValues`
  (Android 14), dynamic supported values (Android 16, VHAL V4). **The property list must be
  static once the VHAL is initialised.**
- **Status:** an unavailable property is reported with an empty value and a status, not a
  fake value.
- **Interface (AIDL `IVehicle`):** `getAllPropConfigs`, `getValues`/`setValues` (batched,
  asynchronous), `subscribe`/`unsubscribe`, callbacks `onPropertyEvent`,
  `onPropertySetError`, `onSupportedValueChange`. Versions: V1 Android 13 … V4 Android 16.
- **Vendor properties** live in the VENDOR group. Default permission
  `android.car.Car.PERMISSION_VENDOR_EXTENSION`; finer control through the static
  `SUPPORT_CUSTOMIZE_VENDOR_PERMISSION` property (per-property read/write permission
  enums). A property can be made "not accessible" to Android apps entirely. Guidance: use a
  system property first; never duplicate one as a vendor property.

### 1.3 VHAL implementations, including virtualised

- **Reference VHAL:** `DefaultVehicleHal` (generic: input checks, subscriptions, permission
  checks, heartbeat, `checkHealth`) over an `IVehicleHardware` (bus-specific).
  `FakeVehicleHardware` keeps values in memory, reads JSON configs from
  `/vendor/etc/automotive/vhalconfig/`, and is for emulators only.
- **`GRPCVehicleHardware`** (Android 16): another `IVehicleHardware` that proxies every
  request to a **server on a remote machine or VM**. Virtualised AAOS (the deprecated
  `trout` reference and Cuttlefish) runs the VHAL server on the host and talks **gRPC over
  vsock** (`VehicleServer.proto`); OEMs may swap the transport.
- **SDV Gateway on IVI:** in the SDV architecture a reference **VHAL proxy** carries
  properties from remote SDV services through `ISdvGateway` and the SDV Data Tunnel, with
  VSIDL mapping (mapping details not published on the page).

### 1.4 Feature control (optional car services)

- Most car services are mandatory. Thirteen are optional (for example `car_evs_service`,
  `car_navigation_service`, `diagnostic`, `storage_monitoring`, `vehicle_map_service`,
  `experimental_car_keyguard_service`).
- **Allowlist by RRO:** `config_allowed_optional_car_features` lists what *may* be enabled.
- **Blocklist from the car:** the VHAL property `DISABLED_OPTIONAL_FEATURES` names features
  to turn off; if absent, every RRO-listed feature is on. Evaluated at boot; changes apply
  after reboot (`mPendingEnabledFeatures`). Debug builds can toggle with
  `cmd car_service enable-feature`.
- So the **build** (overlay) says what this product can do and the **car** (VHAL) says what
  this vehicle has. Apps then ask the Car API whether a feature is present.

### 1.5 Displays, occupant zones, cluster, Scalable UI

- **Occupant zones** (`CarOccupantZoneManager`): a zone maps an occupant (driver, front
  passenger, rear) to a set of displays (MAIN, INSTRUMENT_CLUSTER, HUD, INPUT, AUXILIARY)
  and an Android user. Zones are OEM-configured (the head-unit repo names the overlay keys
  `config_occupant_zones` and `config_occupant_display_mapping`; not found on a public
  docs page, **(U)**). A system can exist with no driver zone.
- **Driving restrictions per display:** UX restrictions apply by default to the driver's
  display; others are unrestricted unless a `RestrictionMapping` with a `physicalPort` says
  otherwise. Modes (`car:mode`, e.g. "passenger") select other rule sets.
- **Instrument cluster API:** CarService mediates; one navigation app at a time holds
  navigation focus (`CarAppFocusManager`) and launches an activity in category
  `android.car.cluster.NAVIGATION` into the OEM's `InstrumentClusterRenderingService`
  (needs `CAR_INSTRUMENT_CLUSTER_CONTROL`). A cluster can be graphics-based (a real or
  virtual display) or metadata-based (data sent to a cluster on its own system).
- **Cluster on another OS (ClusterHome / ClusterOS):** system properties `CLUSTER_SWITCH_UI`
  and `CLUSTER_REPORT_STATE` (Android 13, ON_CHANGE) let a cluster that runs elsewhere and
  the Android side coordinate through the VHAL. The ClusterHomeService itself has no public
  docs page; its role is inferred from the property docs and AOSP **(U)**.
- **Display Safety (SDV):** a **high availability renderer (HAR)** in Rust on a fast-boot
  "SDV Media" VM draws the elements that must appear quickly after cold boot (telltales,
  rear camera, chimes); **DriverUI**, an Android app in the IVI VM, draws the rest of the
  cluster. DriverUI sends heartbeats over gRPC; if they stop, HAR makes its areas opaque and
  shows placeholders. A Safety Monitor checks that what is shown matches vehicle state;
  Google's reference is "not ASIL certified"; the toolchain targets "ASIL-B safety goals".
- **Scalable UI** (strongly recommended; AAOS 16+ does not pass CTS with it disabled):
  system-level windowing in XML. **Panels** (each a root task: `TaskPanel` hosts apps,
  `DecorPanel` hosts views such as widgets) have **variants** (bounds, visibility, layer,
  corner radius: opened, closed, minimised), **transitions** between variants animated by
  WindowManager, and **events** (system ones like home, or custom ones from buttons) that
  trigger them. `<Action>` intents can tell cluster components about layout changes.
  Android 17 adds heads-up notification panels and system-bar customisation.

### 1.6 Power

- The **VMCU** sits between the vehicle network and the application processor (AP), owns
  AP power and is "the only valid wake source"; only it can start deep sleep.
- **`AP_POWER_STATE_REQ`** (VMCU → Android): ON, SHUTDOWN_PREPARE (with CAN_SLEEP,
  CAN_HIBERNATE, SHUTDOWN_ONLY, SLEEP_IMMEDIATELY, …), CANCEL_SHUTDOWN, FINISHED.
  **`AP_POWER_STATE_REPORT`** (Android → VMCU): WAIT_FOR_VHAL, DEEP_SLEEP_ENTRY/EXIT,
  HIBERNATION_ENTRY/EXIT, SHUTDOWN_POSTPONE, SHUTDOWN_PREPARE, SHUTDOWN_START, ON …
- **CarPowerManagementService** runs the state machine (Wait for VHAL → On → Pre Shutdown
  Prepare → Shutdown Prepare → Wait for VHAL Finish → suspend), notifies listeners, sends
  periodic **shutdown-postpone** reports, and suspends by writing `mem` (suspend-to-RAM) or
  `disk` (hibernation) to `/sys/power/state`. **Power policies** switch components
  (display, audio, voice) on and off.
- **Garage Mode:** at ignition off the display goes dark and JobScheduler idle jobs (OTA,
  app updates) run while the framework asks the VHAL to postpone shutdown, until jobs end or
  the limit passes; `SHUTDOWN_IMMEDIATELY` / `SLEEP_IMMEDIATELY` cut it short (low battery).

### 1.7 Users

- **Headless system user:** user 0 runs in the background (CarService lives there and serves
  every user); one foreground user is always required; at most three running users by
  default; guests are ephemeral. Background users stop when switched out; credential-
  encrypted storage needs unlock. Android 14+ adds concurrent users on passenger displays
  (per the owner's notes; zones each get a user).

### 1.8 Driving state

- `CarDrivingStateManager` derives **PARKED** (gear in Park), **IDLING** (not Park, speed 0)
  and **MOVING** from `PERF_VEHICLE_SPEED`, `GEAR_SELECTION` and `PARKING_BRAKE_ON`. An XML
  map turns each state into UX restriction flags (`no_video`, `no_config`, `no_keyboard`,
  `fully_restricted` …). Only activities tagged `distractionOptimized` may run when
  restricted (a manifest check; Google Play review enforces actual compliance).
- **Before the first data arrives (boot) the car is treated as parked and restrictions are
  not enforced.**

### 1.9 SDV and virtualisation

- **Virtualisation:** AAOS runs as a guest VM beside a cluster or ADAS OS on one SoC, on
  VirtIO (virtio-gpu, virtio-snd, virtio-scmi, virtio-video). Cuttlefish replaces `trout`
  (discontinued 2026-08-14).
- **AAOS SDV** ("Beyond Infotainment", Android Developers Blog, 24 March 2026; AOSP release
  later in 2026, Android 17 baseline): a headless Android stack for core compute, body
  control and cluster, in three execution profiles (SDV Core, a headless VM without a JVM;
  SDV Media, graphics and Display Safety; SDV IVI). Per-VM agents (Orchestrator, Service
  Discovery, Health Monitor, Update Manager, Vehicle Mode and Power Management) run
  independently updatable `.apex` service bundles; services are defined in **VSIDL** and
  protobuf and generated with `vsidlc`; inter-VM traffic runs over vsock or Ethernet,
  external ECUs over **SOME/IP**; VM attestation (DICE) and comms authorisation policies.
  The scope is QM: body, cluster, "QM ADAS integration", with safety display elements
  isolated in HAR and a Safety Monitor.

### 1.10 The design philosophy, distilled

1. **Layered abstraction with one choke point.** Apps → Car API → CarService → VHAL → bus.
   Each layer narrows what the one above can do; only the VHAL touches the network.
2. **Typed, enumerated data, not blobs.** Every vehicle fact is a declared property with
   type, area, access, change mode and permission. "Generic APIs do not accept arbitrary
   data blobs."
3. **Customise by overlay, not fork.** RROs (feature allowlist, occupant zones, UX
   restrictions XML, Scalable UI XML, CarSystemUI/launcher resources), JSON VHAL configs and
   vendor properties let an OEM ship one AOSP with its own config.
4. **Optional services, decided by build plus car.** Feature control: the overlay says what
   the product may run; the VHAL says what this vehicle lacks.
5. **Vehicle data behind permissions.** Per-property read/write permissions, enforced once
   in CarService; vendor properties default to a privileged permission.
6. **Safety lives elsewhere.** Android (IVI and now SDV) is QM. Telltales, chimes and rear
   camera that must survive Android failure go to an independent renderer and a monitor,
   often on a separate VM or OS; the Android cluster app is supplementary and watched by
   heartbeats.
7. **Power is owned by a small always-on controller.** The VMCU decides; Android requests
   postponement and reports.

---

## Part 2. Ostler's architecture in brief

- **Mission (ADR-0049, GOALS v2.9):** an open diagnostic and logging platform with an open
  vehicle-data feed; explicitly **not an OS or a launcher**.
- **Three layers (SCOPE):** COMMS → INTERPRETATION (packs: `signals/*.json` as the single
  source of truth) → normalized snapshot → CONSUMERS. Core never imports consumers; the
  platform never imports a pack.
- **Node / brain / gateway (ADR-0032, ADR-0049, ADR-0051):** the ESP32 **node** owns the
  car's buses, decoding to VSS, power switching and **the transmit gate, the only path to
  the car**. The optional **Brain** (Pi, Linux) owns compute and network and never touches
  the car. A **gateway** (on the Brain, else the native Ostler Gateway Android app, else a
  node, else the browser) serves the VISS feed, holds driving state and alerts, and runs the
  **permissions controller**, which issues VISS tokens scoped to per-app toggles (reads
  mapped to ADR-0029 data classes, writes to ADR-0033 categories and tiers). Writes are
  requests; the node gate decides; Tier 4 is impossible.
- **Signals:** COVESA VSS 6.1 is canonical (ADR-0016) with one overlay,
  `vss/ostler.vspec`, adding `Vehicle.Ostler.*` and OVMS/HA/OBDb aliases. **VISS v3**
  (WebSocket first) on every hop (ADR-0051); MQTT is external only.
- **Every field is `proven` or `candidate`**; a missing value is never zero; stale looks
  stale.
- **IP everywhere (ADR-0027):** every device an IP host, mDNS discovery, one module
  manifest of signals and safety-tiered actions, 10BASE-T1S for modules; the car's buses
  stay at the edge.
- **Capabilities:** one firmware; each device detects hardware and publishes a capability
  manifest (ADR-0032 §6, B1); the gateway finds, identifies and suggests hardware
  (ADR-0053, proposed); pages declare the VSS paths they `use` and `require`, so apps
  "grow when data appears".
- **Power (ADR-0040):** one power state per device (off, asleep, waking, awake, held,
  shutting_down, offline) and a reachability class; awake is a sum of leases; wake requests
  are messages arbitrated by the device wired to the wake path (the node); quotas, an
  energy ledger and battery floors; a brain that will not shut down is cut at the timeout.
- **Screens (ADR-0052 proposed v0.8, shell spec approved, tile navigation spec approved):**
  an aircraft-style MFD built by the `ostler-shell` library that every app bundles. Pages of
  at least 720 dp in a **carousel** of saved layouts (pinned driver column from 12″), tiles
  holding app instances with routes and history, stacks with badges, **five size classes**
  (Badge, Chip, Compact, Standard, Expanded) from the tile's own box with hysteresis, a
  page contract (sizes, summary, ranked parts, per-action moving safety, VSS data needs,
  links, `instrument`), **full screen with no shell chrome**, cross-app links (focus the
  tile if on screen, else open a full-screen visitor; Back returns), and a fixed Back order.
  **Moving rules** (unknown counts as moving): no editing, no clear-faults or actuator
  tests, 24 dp text floor, 60 dp targets. Warnings ring or take over a passenger-side
  non-instrument tile, never covering an instrument's value.
- **The owner's AAOS head unit (`ostler-android-automotive`):** LineageOS Automotive
  (`virtio_x86_64_car`) on an Intel N95, Android as a VM on a Linux host; car Maps and Waze
  are the goal. The VHAL and cluster folders are placeholders: a vendor VHAL fed from the
  Brain's VISS server (FakeVehicleHardware + VISS client, or the gRPC VHAL with Ostler as
  host), and a cluster drawn by an Ostler module from VISS, with Android only passing the
  navigation turn card. ADR-0049 already calls AAOS "the reference architecture" and parks a
  VISS→VHAL bridge.

---

## Part 3. Comparison

Verdicts: **Aligned** (same idea, compatible), **Different on purpose** (a deliberate
choice Ostler should keep), **Gap** (something Ostler lacks or has not decided).

| # | AAOS concept | Ostler equivalent | Verdict | Recommendation |
|---|---|---|---|---|
| 1 | **VHAL properties**: a fixed, typed catalogue (~200 system props) with area, access, change mode, status | **VSS paths over VISS v3**, with the `Vehicle.Ostler.*` overlay; confidence `proven`/`candidate`; stale and missing shown honestly | **Aligned** (both are typed, named, subscribable), **different on purpose** in scope: VSS is a tree for the whole car and the network, VHAL an in-device API | Keep VSS/VISS as the protocol (ADR-0051). Treat VHAL as an **output** like the ELM327 bridge. Learn three VHAL habits: (a) declare change mode and rate per path in VISS metadata (VHAL's STATIC / ON_CHANGE / CONTINUOUS plus min/max rate); (b) declare areas the VHAL way where VSS uses branches (`Row1.DriverSide`); (c) an explicit "unavailable" status on the wire rather than a missing key |
| 2 | **Property access mode** READ / WRITE / READ_WRITE per area | VSS `sensor` / `actuator` / `attribute`; writes become requests to the node gate, with ADR-0033 category and tier | **Aligned**, Ostler stricter: a VHAL write goes straight to the bus, an Ostler `set` is gated on a separate MCU | Keep. In the VHAL bridge, every car-touching property is READ unless it maps to an ADR-0033 category whose tier allows it |
| 3 | **Per-property permissions** enforced once in CarService; vendor props default to a privileged permission | **Permissions controller** in the gateway; VISS tokens scoped to data classes (reads) and categories/tiers (writes); cautious defaults; revoke and access log | **Aligned** | Publish a mapping from ADR-0029 data classes to Android car permissions (e.g. speed → `CAR_SPEED`, engine → `CAR_ENGINE_DETAILED`, diagnostics → `CAR_DIAGNOSTICS`, identity → `CAR_INFO`) so the bridge never exposes a class to a weaker Android permission than Ostler requires |
| 4 | **CarService**: the single Java client of the VHAL, the permission checkpoint, host of the car services (power, driving state, zones, features, cluster) | **Gateway** (Brain service or Gateway Android app): one server per node, permission set, driving state, alerts, outputs, hardware detection, shared preferences | **Aligned** in role. The Brain is the compute host (no AAOS equivalent beyond SDV Core) | Keep "one server per node" (≈ "CarService is the only VHAL client"). On AAOS, the Ostler VHAL is just **one more VISS client** of the gateway, with its own token, never a second server |
| 5 | **VHAL is the only thing on the vehicle network**, filters and rate-limits | **Node transmit gate is the only path to the car**; grants minted elsewhere, verified on the node; listen-only by default; no blind frames | **Aligned**, Ostler stronger (physical separation, own MCU, its own speed source for gate decisions) | Keep. Add an explicit **rate limit per client** to the gate rules if not already there (AAOS names it as a defence against a flooding app) |
| 6 | **Feature control**: RRO allowlist (`config_allowed_optional_car_features`) plus VHAL blocklist (`DISABLED_OPTIONAL_FEATURES`), applied at boot | **Packs** (entry point `openostler.vehicle`), **capability manifests** from detected hardware, page `data.requires`, ADR-0053 detection and suggestions, flavours that preinstall apps | **Aligned** in idea (build says what may run, car says what exists), **different on purpose** in timing: Ostler is dynamic at runtime, AAOS fixed at boot | Keep runtime. In the VHAL bridge, compute `DISABLED_OPTIONAL_FEATURES` from the capability manifest at boot (e.g. disable `car_evs_service` with no camera; keep `diagnostic` only if the pack exposes faults and freeze frames) |
| 7 | **OEM customisation by overlays, not forks** (RROs, JSON VHAL configs, XML for zones, UXR and Scalable UI) | Packs as **data** (`signals/*.json` single source; C decoder reads JSON, never a generated header), one VSS overlay file, theme token packs, layouts as versioned data, node config JSON | **Aligned**, strongly | Keep. On the head-unit build, follow the same rule: RROs for CarSystemUI, CarLauncher, zones and UXR; fork only what cannot be overlaid (the head-unit repo already does this) |
| 8 | **Static property list** after VHAL init; dynamic supported values only in V4 | Devices and signals appear and disappear at runtime | **Gap** at the boundary | The bridge declares the **superset** a pack can ever provide at boot and reports absent ones as UNAVAILABLE, never as zero (matches "a missing value is never zero") |
| 9 | **Occupant zones and multi-display**: zones map occupants to displays and users; UXR per display; Multi-Display Comms API | One gateway host per screen; driver side from the car profile; passenger side for Open beside and warning takeovers; rear tablets as separate Ostler devices | **Different on purpose** (Ostler does not own displays or users) with one **gap**: Ostler's moving rules do not know whether a screen is driver-visible | Add a **display role** (driver-visible / passenger / rear) to the shell's gateway client, defaulting to driver-visible. On AAOS read it from `CarOccupantZoneManager`. Passenger-only screens may relax moving rules, as AAOS does per display. Feed `INFO_DRIVER_SEAT` from the car profile's driver side |
| 10 | **Scalable UI**: system windowing, panels (Task/Decor), variants, transitions, events, all in XML | **ostler-shell**: tiles in pages, carousel of saved layouts, five size classes, stacks, full screen, edit mode, D-pad cursor, layouts as `ostler.layout/3` | **Aligned in model, different on purpose in level**: Scalable UI tiles *apps*; Ostler tiles *pages inside its own app*, because Android offers no public API to tile other apps (ADR-0052 §2a) | On the AAOS build use **Scalable UI for app panels** (Maps or Waze, media, Ostler) and let the Ostler shell tile **inside** its panel. Its pixel-based size classes already adapt. Map Ostler's automatic layout triggers (car started, low range, parked) to Scalable UI **events**, and avoid two tilers fighting: in a narrow panel default the shell to a single-page layout |
| 11 | **Instrument cluster**: Instrument Cluster API, navigation focus, cluster rendering service; ClusterHome / `CLUSTER_*` properties for a cluster on another OS | **Instrument pages** (attitude, heading, transfer, speed, engine) shipped by the gateway app; marked `instrument: true`, never covered by a warning; owner plans a separate cluster module drawn from VISS | **Aligned** with AAOS SDV's split (independent renderer, Android supplementary); **gap**: no cluster-module spec, no heartbeat or placeholder rule | **Ostler owns the cluster**, as a module on its own screen fed by VISS, working when Android sleeps or crashes. Copy Display Safety's pattern: the Android side sends **heartbeats**; when they stop the cluster greys or placeholders Android-sourced areas (the nav card) and keeps its own values. Android supplies only the turn card (see Part 4) |
| 12 | **Driving state**: PARKED / IDLING / MOVING from speed, gear and handbrake; UXR XML; `distractionOptimized` activities | Gateway driving state; moving / idling / parked / unknown; **unknown counts as moving**; per-action `moving` safety; 24 dp floor | **Aligned**, Ostler stricter at boot (AAOS treats no data as parked) | Keep Ostler's rule. On AAOS, also **tag Ostler activities `distractionOptimized`** where its own rules allow use while moving, or AAOS will block them. Feed driving state as in Part 4 |
| 13 | **Power state machine**: VMCU owns AP power; `AP_POWER_STATE_REQ/REPORT`; shutdown postpone; suspend-to-RAM; hibernation; power policies | ADR-0040: per-device power state and reachability; leases; wake requests arbitrated by the node; floors and energy ledger; a brain is cut at its timeout | **Aligned**: the **node is the VMCU** | Add a **head-unit device type** to ADR-0040 §2 (wake path ACC or the wake wire through the relay module; parked states suspend-to-RAM then off; power owner the node or relay). The VHAL bridge translates node power messages into `AP_POWER_STATE_REQ` and reports back with `AP_POWER_STATE_REPORT` |
| 14 | **Garage Mode**: idle jobs (OTA, updates) after ignition off, bounded by VHAL postponement | ADR-0040 leases: OTA lease max 30 min, ignition lease until off + 10 min; floors refuse background wakes | **Aligned** | Map Garage Mode to an **OTA lease** held by the head unit: the node grants postponement while the lease and the floors allow, then sends `SHUTDOWN_PREPARE` with `SLEEP_IMMEDIATELY` or `SHUTDOWN_IMMEDIATELY`. Never let Android postpone without a lease |
| 15 | **Multi-user, headless system user**: CarService in user 0 serves all users; foreground and guest users | Ostler roles (Owner, Driver, Viewer, Mechanic time-boxed); the head-unit **kiosk session** gets Read and Comfort only; accounts and garage | **Different on purpose**: Ostler roles are about car authority, Android users about profiles and data | Run the Ostler gateway or VHAL client as a **single-user, persistent system service** (like CarService in user 0) so the feed survives user switches. Do not bind Ostler roles to Android users at first; the head unit defaults to the kiosk role |
| 16 | **Safety vs QM split**: AAOS is QM; HAR, Safety Monitor and telltales sit apart; reference monitor not ASIL certified | Node gate as the only car path; tiers and categories; Tier 4 impossible; alarm independent of the brain; warnings never cover instrument values; "not Thatcham-rated" | **Aligned in spirit**, **gap in wording**: Ostler does not state its integrity level | Add one line to the Constitution or GOALS: **Ostler is QM / non-safety; it never replaces the vehicle's own telltales, warnings or cluster**, and its warnings are advisory. The D2's original instrument pack stays the legal display |
| 17 | **SDV**: service bundles, VSIDL/protobuf, SOME/IP to ECUs, orchestrator, health monitor, update manager, attestation | **IP everywhere**: devices as IP hosts, mDNS, VISS, one module manifest, T1S, role holders and heartbeats (ADR-0037), signed OTA as a risk item | **Aligned** in direction (service-oriented, IP, updatable), **different on purpose** in target: Ostler retrofits old cars and keeps legacy buses at the edge; it is not an ECU OS | Keep VISS; do not adopt VSIDL or SOME/IP. Borrow: a **health monitor** view (per-device liveness beyond `status`), **attestation** for nodes and modules (DICE-style device identity is close to ADR-0027's per-device certificates), and the **VHAL-proxy-through-a-gateway** pattern, which is exactly Ostler's VISS→VHAL bridge |
| 18 | **Virtualisation**: AAOS as a VM; gRPC VHAL on the host over vsock | Owner's lean: x86 Linux host with AAOS as a VM or container; the Brain is a Linux computer | **Aligned** | Make the **x86 host the Brain** and put the VHAL server there (Part 4). One box, one gateway, Android a guest |
| 19 | **Identity props** (`INFO_VIN`, make, model) readable by apps with the right permission | ADR-0036: VIN never recorded by default, never leaves the device | **Gap** (risk) | Report `INFO_VIN` as UNAVAILABLE unless the owner opts in for this head unit, with the same warning ADR-0036 uses |
| 20 | **Night mode** (`NIGHT_MODE` property) drives the system theme | Themes have Day and Night; Auto follows headlights, then a light sensor, then sunset | **Aligned** | Compute night once in the gateway and feed `NIGHT_MODE` from the same rule, so AAOS and Ostler switch together |

---

## Part 4. How Ostler should plug into AAOS on the owner's head unit

### 4.1 Topology

```
D2 buses ──K-line── Node (ESP32, gate, VMCU role, wake wire via relay module)
                       │ USB-NCM / T1S, VISS v3
                       ▼
x86 N95 Linux host = Ostler Brain (Python gateway: VISS server, permissions, logs)
   ├─ ostler-vhal-server (gRPC VehicleServer, a VISS client with its own token)
   │      │ gRPC over vsock
   │      ▼
   └─ AAOS guest VM (LineageOS virtio_x86_64_car)
          VHAL = DefaultVehicleHal + GRPCVehicleHardware (proxy, Android 16)
          CarService → CarPropertyManager → car Maps, Waze, Ostler apps
          Scalable UI panels: Maps | Ostler shell | media
   Cluster screen ← Ostler cluster module (VISS), Android passes only the turn card
```

- **Prefer the gRPC VHAL over a custom in-guest VHAL.** `GRPCVehicleHardware` exists for
  exactly this (a server on another VM or host). The server is outside Android, written in
  any language, and can be an Ostler add-on repo (the core's stdlib-only rule does not bind
  it). It keeps Android unmodified apart from the product makefile choosing the gRPC VHAL.
  Confirm that LineageOS 23.2 builds `GRPCVehicleHardware` for `virtio_x86_64_car` **(U)**.
- **Fallback:** extend `FakeVehicleHardware` with a VISS WebSocket client over the VM's
  virtual NIC. More Android code, but no host dependency.
- **Ostler Gateway app on AAOS:** not needed when the Brain is the server (ADR-0051 item 9:
  Android to a Brain is a client). Ostler apps in the guest reach the Brain's VISS directly,
  or through a thin client gateway. They should **not** read Ostler data back out of the
  VHAL: VHAL is a downgrade (fewer paths, no confidence, no `Vehicle.Ostler.*`).

### 4.2 VSS-to-VHAL property mapping (first cut)

The mapping table should live in the `ostler` repo as data beside `vss/ostler.vspec`
(e.g. `vss/vhal_map.json`, generated checks in CI), as the head-unit README asks, so it is a
single source. COVESA's AASIG has prior work (`vspec2aaproperties` in vss-tools'
`code_generation` branch, and an AOSP-VSS mapping sheet for Android 12, reported as probably
obsolete); reuse what still applies.

| VSS path (Ostler) | VHAL property | ID | Area / type / mode | Conversion and notes |
|---|---|---|---|---|
| `Vehicle.Speed` (km/h) | `PERF_VEHICLE_SPEED` | 0x11600207 | GLOBAL / FLOAT / CONTINUOUS | km/h ÷ 3.6 → m/s. Drives AAOS driving state |
| `Vehicle.Speed` | `PERF_VEHICLE_SPEED_DISPLAY` | from `VehicleProperty.aidl` | GLOBAL / FLOAT / CONTINUOUS | Same value; optional |
| `Vehicle.Powertrain.CombustionEngine.Speed` | `ENGINE_RPM` | 0x11600305 | GLOBAL / FLOAT / CONTINUOUS | rpm as is |
| `…CombustionEngine.EngineCoolant.Temperature` | `ENGINE_COOLANT_TEMP` | from aidl | GLOBAL / FLOAT / CONTINUOUS | °C as is |
| `…CombustionEngine.EngineOil.Temperature` | `ENGINE_OIL_TEMP` | from aidl | GLOBAL / FLOAT / CONTINUOUS | °C as is |
| `Vehicle.Powertrain.Transmission.CurrentGear` | `CURRENT_GEAR` | 0x11400401 | GLOBAL / INT32 / ON_CHANGE | VSS int (−1 R, 0 N, 1–n) → `VehicleGear` flags; declare `configArray` of supported gears |
| (selector position, autobox pack) | `GEAR_SELECTION` | 0x11400400 | GLOBAL / INT32 / ON_CHANGE | P/R/N/D from the Autobox signal. **Manual D2:** no selector; see 4.4 |
| `Vehicle.Chassis.ParkingBrake.IsEngaged` | `PARKING_BRAKE_ON` | from aidl | GLOBAL / BOOLEAN / ON_CHANGE | |
| `Vehicle.Powertrain.FuelSystem.RelativeLevel` (%) | `FUEL_LEVEL` | from aidl | GLOBAL / FLOAT / CONTINUOUS | % × `INFO_FUEL_CAPACITY` → ml; `INFO_FUEL_CAPACITY` from the pack (STATIC) |
| `Vehicle.Powertrain.FuelSystem.Range` (m) | `RANGE_REMAINING` | from aidl | GLOBAL / FLOAT / CONTINUOUS | Metres; expose READ only although AAOS allows write |
| `Vehicle.TraveledDistance` (km) | `PERF_ODOMETER` | from aidl | GLOBAL / FLOAT / CONTINUOUS | km as is |
| `Vehicle.Exterior.AirTemperature` | `ENV_OUTSIDE_TEMPERATURE` | from aidl | GLOBAL / FLOAT / CONTINUOUS | °C |
| `Vehicle.Body.Lights.Beam.Low.IsOn` | `HEADLIGHTS_STATE` | from aidl | GLOBAL / INT32 / ON_CHANGE | ON/OFF enum |
| (gateway's night rule) | `NIGHT_MODE` | from aidl | GLOBAL / BOOLEAN / ON_CHANGE | Same rule as the theme's Auto |
| (ignition from the node) | `IGNITION_STATE` | from aidl | GLOBAL / INT32 / ON_CHANGE | OFF / ACC / ON / START |
| `Vehicle.LowVoltageBattery.CurrentVoltage` | vendor property or none | VENDOR group | GLOBAL / FLOAT | AAOS has no 12 V voltage system property (to confirm **(U)**) |
| `Vehicle.Ostler.Diagnostics.MilOn`, `DtcCount` | `OBD2_LIVE_FRAME` / vendor | from aidl | MIXED | Only with the `diagnostic` optional feature on. **Never** implement `OBD2_FREEZE_FRAME_CLEAR`: clearing stays in Ostler, behind the node gate (ADR-0033) |
| `Vehicle.Ostler.Chassis.RideHeight.*` (SLABS) | vendor properties | VENDOR group | WHEEL area / FLOAT | `PERMISSION_VENDOR_EXTENSION` or a custom permission via `SUPPORT_CUSTOMIZE_VENDOR_PERMISSION` |
| `Vehicle.Ostler.Security.Alarm.State` | vendor, or not mapped | VENDOR | GLOBAL / INT32 | Prefer not mapping: alarm UX stays in Ostler |
| car profile driver side | `INFO_DRIVER_SEAT` | from aidl | SEAT / INT32 / STATIC | RHD for the owner's D2 |
| VIN | `INFO_VIN` | 0x11100100 | GLOBAL / STRING / STATIC | **UNAVAILABLE unless the owner opts in** (ADR-0036) |
| HVAC (owner's separate HEVAC ESP32) | `HVAC_TEMPERATURE_SET` etc. | 0x15600503 | SEAT / FLOAT / ON_CHANGE | Only through a HEVAC add-on device in the module manifest, Comfort tier 1, through the gate rules. Not in the first cut |

Rules for the bridge:

- **Read-only first.** Every property is `READ` in v1. Writes come later per ADR-0033
  category, each translated into a VISS `set` that the gateway confirms and the node gate
  decides; AAOS's `setValues` result reflects the gate's answer.
- **Honest status.** A VSS value that is missing or stale (age over two periods) is reported
  as `UNAVAILABLE`, never as zero or the last value re-dated. `candidate` signals may be
  bridged but only behind an owner switch, since VHAL has no confidence field.
- **One source per fact.** Unit conversions and enum maps live in the mapping file with
  shared test vectors (VSS in → VHAL out), as the C and Python decoders do.

### 4.3 Who owns the cluster

**Ostler owns it.** Recommended split:

- The **cluster screen** is driven by an Ostler cluster module (its own small renderer, fed
  by VISS from the node or Brain), so speed, rpm, coolant and Ostler warnings show within
  seconds of ignition and survive Android sleeping or crashing. This is AAOS SDV's HAR model
  without the certification.
- **Remove Android's cluster:** do not declare an `INSTRUMENT_CLUSTER` display in the
  occupant-zone overlay (or give the VM only one display) and leave out the sample cluster
  packages (the cluster README's three checks).
- **Android passes only the navigation turn card.** Options, in order: (a) implement the
  cluster navigation state property in the gRPC VHAL server (the ClusterHome / ClusterOS
  path: Android writes navigation state into the VHAL and the host forwards it as a
  `Vehicle.Ostler.Navigation.*` overlay branch) **(U: confirm the property name, payload
  and which navigation apps publish it)**; (b) a small privileged app holding navigation
  focus that reads `CarNavigationStatusManager` events; (c) Android notification listener as
  a last resort. The owner's note that only certified car Maps fills the cluster panel means
  (a) or (b) must be tested with Maps and Waze on the bench.
- **Heartbeats:** the Android side sends a heartbeat with the turn card; when it stops the
  cluster drops the card and shows a placeholder, never a stale arrow.

### 4.4 Feeding the driving state

AAOS derives driving state from three VHAL properties; Ostler's gateway already decides
moving / idling / parked / unknown (vehicle speed, then GNSS speed, then gear and handbrake).
To keep one decision:

- The bridge publishes `PERF_VEHICLE_SPEED` from the gateway's selected speed source (bus
  speed, else u-blox GNSS speed), and `PARKING_BRAKE_ON` from the bus.
- **Manual-gearbox D2:** there is no Park. Configure `GEAR_SELECTION` as unsupported (or not
  declared) and check how `CarDrivingStateService` behaves with only speed and handbrake
  **(U)**. If AAOS needs a gear, publish a gear only when it is a real signal; never invent
  "Park" from handbrake.
- **Boot gap:** AAOS treats "no data yet" as parked. Mitigate by (a) the gRPC server
  answering from the node's retained last values within the 1 s Read budget of ADR-0040;
  (b) the UXR XML restricting IDLING as well as MOVING; (c) Ostler's own apps still applying
  "unknown counts as moving" inside the shell, whatever AAOS says.
- **Do not feed back.** Ostler never reads AAOS's driving state; the node gate uses its own
  bus or receiver (ADR-0032 A5).

### 4.5 Power wiring

- The node (or relay module under its control) is the **VMCU**: ignition off → node sends
  `AP_POWER_STATE_REQ = SHUTDOWN_PREPARE, CAN_SLEEP` through the VHAL server; Android replies
  with postpone and finally `DEEP_SLEEP_ENTRY`; the host suspends to RAM (N95 S3 to be
  measured); after the parked budget (ADR-0040 floors, "a few days" in the owner's notes)
  the node asks for `SHUTDOWN_ONLY` and then cuts power.
- Postponement is a **lease** (Garage Mode ≈ OTA lease, max 30 min) and the battery floors
  end it. A head unit that does not report within the timeout is cut, like a hung Brain.

### 4.6 Summary of actions

1. Write the VSS→VHAL mapping as data with test vectors in the `ostler` repo.
2. Build `ostler-vhal-server` (gRPC `VehicleServer` on the Linux host, VISS client with a
   scoped token) and switch the head-unit build to the gRPC VHAL.
3. Remove Android's cluster; spec the Ostler cluster module with heartbeats and
   placeholders; test the turn-card path with Maps and Waze.
4. Add a head-unit device type to ADR-0040 and a display role to the shell.
5. Use Scalable UI panels for Maps, Ostler and media; Ostler's shell tiles inside its panel.
6. Tag Ostler activities `distractionOptimized` only where Ostler's moving rules allow.
7. State that Ostler is QM / non-safety and never replaces the car's own displays.

---

## Sources

### AAOS (official)

- Feature control: https://source.android.com/docs/automotive/feature-control
- VHAL overview: https://source.android.com/docs/automotive/vhal
- VHAL property configuration: https://source.android.com/docs/automotive/vhal/property-configuration
- VHAL interface (AIDL `IVehicle`): https://source.android.com/docs/automotive/vhal/vhal-interface
- VHAL reference implementation (`GRPCVehicleHardware`): https://source.android.com/docs/automotive/vhal/reference-implementation
- Vendor properties and permissions: https://source.android.com/docs/automotive/vhal/special-properties
- Supported system properties (CLUSTER_* listing): https://source.android.com/docs/automotive/vhal/system-properties
- Native client: https://source.android.com/docs/automotive/vhal/native-client
- What is Android Automotive: https://source.android.com/docs/automotive/start/what_automotive
- SDV overview: https://source.android.com/docs/automotive/sdv
- SDV gateway on IVI: https://source.android.com/docs/automotive/sdv/sdv-gateway-on-ivi
- Display Safety: https://source.android.com/docs/automotive/sdv/display-safety
- Scalable UI: https://source.android.com/docs/automotive/scalableui
- Displays overview: https://source.android.com/docs/automotive/displays
- Instrument Cluster API: https://source.android.com/docs/automotive/displays/cluster_api
- Multi-Display Communications API: https://source.android.com/docs/automotive/displays/multi-display-comms-api
- `CarOccupantZoneManager`: https://developer.android.com/reference/android/car/CarOccupantZoneManager
- Power overview: https://source.android.com/docs/automotive/power
- Power management: https://source.android.com/docs/automotive/power/power
- Garage Mode: https://source.android.com/docs/automotive/power/garage_mode
- Users (headless system user): https://source.android.com/docs/automotive/users_accounts/user_system
- Virtualization: https://source.android.com/docs/automotive/virtualization
- Virtualization architecture (gRPC over vsock): https://source.android.com/docs/automotive/virtualization/architecture
- Vehicle system isolation: https://source.android.com/docs/automotive/security/vehicle_system_isolation
- Security index: https://source.android.com/docs/automotive/security
- Driver distraction guidelines: https://source.android.com/docs/automotive/driver_distraction/guidelines
- Car UX restrictions: https://source.android.com/docs/automotive/driver_distraction/car_uxr
- "Beyond Infotainment: Extending Android Automotive OS for Software-defined Vehicles"
  (24 March 2026): https://developer.android.com/blog/posts/beyond-infotainment-extending-android-automotive-os-for-software-defined-vehicles
  and https://android-developers.googleblog.com/2026/03/Beyond-Infotainment-Extending-Android-Automotive-OS-for-Software-defined-Vehicles.html

### Other

- COVESA, Binding of VSS to Android properties: https://wiki.covesa.global/x/VAK5
- COVESA AASIG VHAL report: https://wiki.covesa.global/download/attachments/364375/AASIG%20VHAL%20Report.pdf?api=v2
- COVESA Data Workstream kickoff (vspec2aaproperties status): https://wiki.covesa.global/download/attachments/126386435/COVESA%20Data%20Workstream%20Kickoff.pdf?api=v2

### Ostler files read

- `openostler/ostler`CLAUDE.md`
- `openostler/ostler`CONSTITUTION.md`
- `openostler/ostler`GOALS.md`
- `openostler/ostler`SCOPE.md`
- `openostler/ostler`decisions/adr-0016-covesa-vss-canonical-signal-namespace.md`
- `openostler/ostler`decisions/adr-0027-ip-everywhere-ecosystem-architecture.md`
- `openostler/ostler`decisions/adr-0032-one-node-optional-brain.md`
- `openostler/ostler`decisions/adr-0033-action-categories-and-approvals.md`
- `openostler/ostler`decisions/adr-0034-repo-boundaries.md`
- `openostler/ostler`decisions/adr-0039-product-family-diagnostics-guardian-hub.md`
- `openostler/ostler`decisions/adr-0040-power-states-and-wake.md`
- `openostler/ostler`decisions/adr-0048-ostler-as-an-android-launcher.md`
- `openostler/ostler`decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md`
- `openostler/ostler`decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md`
- `openostler/ostler`decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md`
- `openostler/ostler`decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md`
- `openostler/ostler`vss/ostler.vspec`
- `openostler/ostler`specs/2026-10-11-ostler-shell-design.md`
- `openostler/ostler`specs/2026-10-13-tile-navigation-design.md`
- `openostler/ostler`references/research/direction_standard_not_os.md` (§3.3)
- `openostler/ostler-android-automotive`README.md`
- `openostler/ostler-android-automotive`docs/ideas.md`
- `openostler/ostler-android-automotive`lineage/vendor/headunit/vhal/README.md`
- `openostler/ostler-android-automotive`lineage/vendor/headunit/cluster/README.md`
- `openostler/ostler-android-automotive`lineage/vendor/headunit/systemui/README.md`
- `openostler/ostler-android-automotive`lineage/vendor/headunit/apps/ostler-gateway/README.md`
- `openostler/ostler-android-automotive`scripts/vhal-inject.sh`

Note: ADR-0016 (packs and VSS) was read through its summary; the pack contract ADR-0013 and
the VSS overlay rules were taken from the Constitution, SCOPE and `vss/ostler.vspec`.
