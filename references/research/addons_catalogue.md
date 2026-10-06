---
title: "Add-ons catalogue — module ideas with transport, standards and phase"
area: references
status: draft
version: 1.5
updated: 2026-10-06
depends_on: [references/vision.md, references/research/ecosystem_architecture.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, references/research/features_backlog.md]
summary: >
  A catalogue of add-on module ideas for the Ostler ecosystem (the guardian as a node hardware variant, cameras and dashcam, 360 view, own relay boards later, sensor nodes (fast tacho, EGT, boost/oil, wideband AFR, accelerometers) and sensor pods, buttons, displays and head unit, gauges, TPMS, a Meshtastic-compatible LoRa add-on first behind a thin GPL-3 VSS bridge (mesh is car-to-car, base or off-grid only, a remote path, ADR-0038), Wi-Fi HaLow link to home, a richer car-to-car mesh layer later (MeshCore, Reticulum/LXMF, Styrene, Ratspeak as references) and Babel if a Wi-Fi IP mesh is wanted, a 10 Hz u-blox GNSS (next; on the Diagnostics node, ADR-0039) and RTK later, cellular and Starlink gateway, CAN/T1S bridges, leisure battery and solar via Victron VE.Direct, EV charger via OCPP/ISO 15118, camper and overland kit, tracker, OBD dongle, winch and lights, weather station, trailer, motorcycles via an Ostler Diagnostics node with the phone or a guardian-variant node, and more), each with what it does, its transport, the open standards it should use and a phase (now / next / later / idea), plus rules every add-on follows and live-checked facts (October 2026) with sources.
---

# Add-ons catalogue

Ideas for add-on modules, the long-term half of [vision §5](../vision.md#5-add-ons-anything-you-can-think-of).
This is a parking lot, not a commitment: each module needs a spec, and the
[feature backlog](features_backlog.md) tags still apply (add-ons are off by default). Facts
were checked live in **October 2026**; **(U)** means unverified.

> **Update (2026-10-06, ADR-0032/0033):** the guardian is no longer an add-on but a
> **node hardware variant** (same firmware, hidden, battery-backed, no outputs); the base
> pack's "buddy" is replaced by the node, and add-ons work with **Ostler Diagnostics** (node
> alone) or **Ostler Diagnostics + Brain** (node + brain; names per ADR-0039). The node transmit gate is the only path to the car.
> The "alarms are notify-only" rule is dropped: alarm outputs come through a future I/O /
> relay module with an ADR per car-switching function. Sensor nodes are a new family (§1).

## Rules every add-on follows

- **One module contract** ([ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md),
  [ecosystem research §3.2](ecosystem_architecture.md#32-the-module-contract-a-device-side-twin-of-the-vehicle-pack-contract)):
  an IP host, found by mDNS/DNS-SD, speaking VSS-named MQTT 5, with a manifest of signals
  and safety-tiered actions. Devices that cannot describe themselves get a DevicePack
  adapter.
- **Stands on its own.** Each module hosts a small web page with its basic controls (like
  an IP camera or an ESP32 project) and keeps working without a brain. No default
  passwords.
- **The node gate is the only path to the car** (ADR-0032). Every control declares its
  action category and tier in the module manifest (ADR-0033); remote paths stay read-only
  unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set. No module writes
  to a vehicle ECU or bus except through the node gate; MQTT is never bridged to vehicle
  CAN ([ADR-0020](../../decisions/adr-0020-can-links-listen-only-by-default.md)).
- **Taps on car wiring are read-only and isolated** (optocouplers or high-impedance
  inputs); they never load or alter an ECU signal. Anything that switches a car function
  needs its own ADR before it ships.
- **Alarm-critical links are wired** (T1S or CAN), never Wi-Fi
  ([ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md)). Alarm paths never depend
  on the brain or the internet.
- **Radios use licence-exempt bands** for the region, and every outbound path is opt-in.
- **Licences:** GPL-3 projects (such as Meshtastic) are used as separate programs or in
  marked GPL-3 modules ([ADR-0025](../../decisions/adr-0025-reuse-and-licences-pragmatic.md)).

**Transport key:** **T1S** = 10BASE-T1S module bus; **Eth** = standard Ethernet (12 V or PoE),
100BASE-T1 for our own hardware later; **Wi-Fi** = 2.4/5 GHz; **HaLow** = Wi-Fi HaLow
(802.11ah, sub-GHz); **LoRa**; **BLE**; **CAN** = the dev-kit and µA-wake fallback;
**USB** = tethering or serial.

**Phase key:** **now** = possible with today's platform or dev kit; **next** = in the
near-term roadmap ([GOALS §5](../../GOALS.md#5-near-term-roadmap)); **later** = wanted,
not scheduled; **idea** = worth recording.

## 1. Core add-ons (the module families in ADR-0027)

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **Guardian (node hardware variant)** | Not an add-on any more: the node firmware on hidden hardware with its own backup cell, tamper sensing, IMU, better antennas, GNSS and optional 4G/IoT SIM; tracker, geofences, alarm triggers (strong/weak, tamper, IMU tow/theft), notification escalation; replaces the plain node or sits alongside it; **no outputs** ([ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md)) | T1S; CAN or wake wire as fallback; 4G uplink | MQTT 5 + HA discovery, OwnTracks, Traccar OsmAnd, ntfy | next (Phase 2 node firmware) |
| **I/O / relay boards** (our own, later) | Switched outputs and alarm outputs (siren, the car's native alarm, immobiliser); each control declares its category and tier (Accessories default Tier 2, Parked-only); an ADR per car-switching function before it ships | T1S; CAN fallback | MQTT + HA discovery (`switch`) | later (Phase 4) |
| **Fast tacho sensor node** | Engine speed from crank, coil or injector pulses at high rate | T1S | VSS signals with source tags; open-source driver libraries (ADR-0025), not ESPHome itself | next |
| **EGT sensor node** | Exhaust gas temperature from a thermocouple amplifier | T1S | VSS with source tags | next |
| **Boost and oil sensor node** | Boost pressure, oil pressure and oil temperature | T1S | VSS with source tags | next |
| **Wideband AFR node** | Air-fuel ratio read from a wideband controller over its serial output | T1S | Controller serial protocol → VSS | later |
| **Extra accelerometers** | More IMUs for body motion, tilt and theft detection; fused with the node's | T1S; BLE for battery pods | VSS with source tags | later |
| **Read-only isolated taps** | Reads car wiring (lamp, switch, sender lines) through optocouplers or high-impedance inputs; never loads or alters an ECU signal | T1S | VSS with source tags | next |
| **Sensor pods** | Temperature, humidity, tilt/inclinometer, door/bonnet/tailgate contacts, PIR, cabin CO and air quality (advisory only, not a certified detector) | T1S; BLE for battery pods | MQTT + HA discovery; BTHome for BLE pods | next |
| **Dash buttons and keypads** | Panel buttons, rotary encoders, a PIN keypad for the alarm; events, not direct actions | T1S; CAN fallback | MQTT events, HA device triggers | next |
| **Gauge display** | A small round or bar display for chosen signals | T1S | VSS paths via MQTT | next |
| **Displays / head unit** | The PWA on any screen, head-unit first; later an Ostler Android launcher | Wi-Fi, USB (NCM/RNDIS) | PWA, the documented head-unit CAN-box protocol | now |
| **Head-unit CAN/OBD emulator** | Feeds an aftermarket head unit the CAN messages it expects | CAN (its own, never the car's) | Head-unit CAN-box protocols | next (Phase 4) |
| **Cameras** | Dashcam, parking and alarm clips, reversing, underbody in one timeline | Eth / PoE (never T1S) | ONVIF, RTSP, go2rtc; optional Frigate | now (off the shelf) |
| **360° surround view** | Stitched view from four cameras | Eth; our own 100BASE-T1 cameras later | ONVIF/RTSP | later (ADR-0018) |
| **HEVAC controller** | The owner's separate climate project, joined as a device | T1S or Wi-Fi | Module contract, Comfort-category actions | external |

## 2. Connectivity and range

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **Cellular / Starlink gateway** | No SIM by default; uplinks: car/head-unit Wi-Fi, phone hotspot, home Wi-Fi, any 3G/4G USB dongle, an OpenWrt high-speed gateway, Starlink, the node's optional 4G (an official option, each device with its own IoT SIM); Auto failover or a pinned source, metered with data-cap alerts. Remote access: LAN default, then Tailscale, Ostler Cloud, HA Cloud | USB, Eth, Wi-Fi | USB NCM/RNDIS/QMI, ModemManager, OpenWrt; Tailscale (WireGuard) | next ([ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)) |
| **Wi-Fi HaLow link to home** | A long-range, low-rate link from the parked car to the house: alarm events, telemetry, a low-rate camera still | HaLow | IEEE 802.11ah; MQTT over it | later |
| **Meshtastic-compatible LoRa add-on** | Text, positions, alarm state and alerts between vehicles, riders and a camp with no phone signal. Step one: any Meshtastic radio the owner has (USB, BLE, TCP); step two: our own board on stock Meshtastic firmware over UART or T1S. A thin VSS bridge with **no actions** (Read and alerts out, data in); position off by default, coarse when on; a separate GPL-3 program (`ostler-bridge-meshtastic`, GPL-3.0-or-later, ADR-0034 Amendments), never in core or node firmware. The first mesh add-on, Meshtastic-compatible first (owner, 2026-10-06; [mesh research](mesh_networking.md), [ADR-0038](../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md)) | LoRa (868 MHz EU, 915 MHz US); its own non-IP network, bridged at the brain or a gateway | Meshtastic client API (serial/BLE/TCP protobufs) or its MQTT; "works with Meshtastic" naming | next (first mesh add-on) |
| **Richer car-to-car mesh** | Groups, rides and convoys for the social layer (ADR-0029 P4): store-and-forward messages, positions, shared media at low rate. A later goal or add-on: bench-test MeshCore (MIT), Reticulum/LXMF, Styrene and Ratspeak when it is taken up; until then all four, Reticulum included, are references only ([mesh research §3](mesh_networking.md#3-per-project-notes), ADR-0038 §7) | LoRa; any IP link for Reticulum | MeshCore companion protocol; RNS/LXMF | later |
| **Wi-Fi IP mesh (car-to-car, camp)** | A shared uplink or bulk sync between brains at camp; its own routed subnet, never bridged into a car | Wi-Fi (802.11s or ad-hoc), or HaLow | Babel (RFC 8966, babeld MIT) preferred; batman-adv only behind the routed edge (L2 floods mDNS, MTU cost) | idea |
| **CAN / T1S bridges** | Joins a CAN-only node or a second T1S segment to the IP network | CAN, T1S | SocketCAN; listen-only to any vehicle bus by default | next |
| **Matter bridge** | Shows the car to Matter ecosystems: Read entities plus alarm arming and disarming (disarm Parked only, audited); preheat and aux-heater switches only with the install override; never Tier 2+; every command through the node gate; a remote path; never for the module bus or a mesh. Via HA and Matterbridge until at scale; a certified Ostler bridge only then ([ADR-0027 Amendments](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md#amendments-2026-10-06-networking-answers)) | Wi-Fi/Eth (home side) | Matter bridge device type | later |

## 3. Vehicle extras

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **TPMS receiver** | Reads aftermarket or OEM tyre sensors | 315/433 MHz receiver (SDR or a sub-GHz radio) on T1S or USB | rtl_433 decoders, MQTT | later |
| **GNSS (10 Hz u-blox)** | Drive logging, replay, Drive mode, the driving-state fallback, the speed-vs-wheel-speed check and the best clock for the time role; the guardian's 1 Hz modem GNSS stays the security tracker ([ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md) Amendments A, [ADR-0037](../../decisions/adr-0037-role-holders-and-handover.md)). **On the Ostler Diagnostics node** ([ADR-0039](../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md) §9), where with PPS it ranks first for time; a USB u-blox on the Brain is the Brain-only and dev path | UART on a node (time pulse to a GPIO); USB as a dev path | NMEA 0183, UBX | next |
| **RTK** | Centimetre RTK for lap timing, surveying and trails | T1S or USB | UBX, RTCM 3 over NTRIP | later |
| **Tracker** | A small hidden tracker on its own cell; the guardian variant covers most of this | LTE-M/NB-IoT or LoRa | OwnTracks, Traccar OsmAnd | later |
| **OBD dongle** | A Wi-Fi/BLE OBD front end for `generic_obd2` | Wi-Fi, BLE | ELM327 AT, slcan/SocketCAN (e.g. WiCAN Pro) | next ([ADR-0031](../../decisions/adr-0031-generic-obd2-pack-in-platform.md)) |
| **Winch and lights control** | Work lights, light bars, winch in/out with interlocks; physical controls stay primary | T1S via an I/O / relay board | MQTT + HA discovery; Accessories category, Parked-only, remote per ADR-0033 | later |
| **Trailer / caravan module** | Lights check, hitch and tilt, tyre pressure, trailer battery | T1S over a trailer harness, or Wi-Fi/BLE | MQTT + HA discovery | idea |
| **Parking sensors** | Ultrasonic distance for retrofit parking aid | T1S | MQTT | idea |
| **Phone presence** | Notices the owner's phone to quiet alarm notifications; never unlocks the car | BLE | BLE advertising; HA presence | idea |

## 4. Power, camper and overland

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **Leisure battery and solar monitor** | Battery state, solar and charger data from the leisure system | T1S node with a serial port; BLE | Victron VE.Direct (text mode), Victron BLE advertising; BMS over BLE (U) | later |
| **EV charger integration** | Reads charging state and energy at home; any charge control is a gated action with its own ADR | Wi-Fi/Eth (home side) | OCPP 1.6/2.0.1 (charger to backend), ISO 15118 (car to charger), EVerest | idea |
| **Camper and overland kit** | Fridge temperature, water and fuel tank levels, diesel heater status, awning and step sensors | T1S; BLE for vendor devices | MQTT + HA discovery; vendor BLE through DevicePack adapters | idea |
| **Weather station** | Outside temperature, pressure, wind and rain at camp | T1S or 433 MHz | rtl_433 for off-the-shelf stations, MQTT | idea |

## 5. Motorcycles (bikers)

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **Bike: Diagnostics node + phone** | An Ostler Diagnostics node with the phone as the screen: diagnostics where the bike allows it (many older bikes use K-line, (U) per make), lean angle and IMU logging, GNSS | BLE/Wi-Fi to the phone; no module bus | VSS, MQTT; the same `VehiclePack` contract | later |
| **Bike: guardian-variant node** | Hidden, battery-backed tracker and movement/tilt alarm; probably the natural bike product | 4G (IoT SIM) or LoRa | OwnTracks, Traccar OsmAnd | later |
| **Group rides** | Positions and messages within a riding group, with or without phone signal; coarse positions unless a live ride is opted in | LoRa (Meshtastic-compatible add-on, ADR-0038) and the phone | Meshtastic; the social layer of [vision §6](../vision.md#6-many-vehicles-many-people) | later |
| **Bike TPMS** | Two-wheel tyre pressure | 433 MHz or BLE | rtl_433 or BLE | idea |

## 6. Live checks (October 2026)

- **Wi-Fi HaLow** is IEEE 802.11ah in the sub-GHz licence-exempt bands. Morse Micro's
  MM6108 is a certified HaLow SoC with rates up to 32.5 Mbit/s; the vendor demonstrated
  about 3 km, and a later line-of-sight field trial reported about 16 km. An ESP-IDF
  component wraps the Morse Micro IoT SDK and is tested on ESP32-C3, -C5, -C6, -S3 and -P4
  with MM6108 (MM8108 on -P4). Heltec makes a Pi HAT with a HaLow module. Range in a car,
  with a roof-level antenna and buildings in the way, is (U) until we test it.
- **Meshtastic** firmware and its protobuf definitions are GPL-3.0, and the firmware runs
  on ESP32, nRF52, RP2040/RP2350 and Linux. Ostler should talk to a Meshtastic node through
  its interfaces rather than link its code into core (ADR-0025).
- **B.A.T.M.A.N. advanced** (batman-adv) is a Linux kernel module that routes at layer 2,
  so the mesh looks like one switch; it runs over 802.11s, ad-hoc or wired links and is
  packaged for OpenWrt.
- **Mesh projects (2026-10-06):** MeshCore is MIT with learned routes; Reticulum and LXMF
  carry the "Reticulum License" (MIT plus use restrictions) and the author has stepped
  back; Styrene is an early solo Rust platform on Reticulum with remote exec and reboot;
  Ratspeak is an AGPL client on Reticulum, not a new protocol; Babel's babeld is MIT. See
  the [mesh research](mesh_networking.md).
- **Victron VE.Direct** has a documented text mode in which the device sends its run-time
  fields periodically without being asked; a HEX mode adds requests. Victron points to a
  list of open-source projects using it.
- **TPMS:** rtl_433 receives the 315, 433.92, 868 and 915 MHz bands and includes several
  TPMS decoders (Schrader, Toyota, Ford, Renault, Citroën among them).
- **EV charging:** EVerest (LF Energy, Apache-2.0) implements ISO 15118-2/-20, DIN 70121
  and OCPP 1.6 and 2.0.1, with 2.1 in progress. US NEVI rules require OCPP 2.0.1 on funded
  chargers.

Sources: [Morse Micro chips](https://morsemicro.com/chips),
[Morse Micro 3 km demo](https://www.everythingrf.com/news/details/17790-morse-micro-demonstrates-world-s-longest-range-wi-fi-halow-solution-reaching-3-kilometers),
[HaLow 16 km trial (TechRadar)](https://www.techradar.com/pro/groundbreaking-wireless-tech-that-can-run-on-coin-batteries-for-months-hits-new-milestone-halow-achieves-10-mile-range-in-latest-test),
[ESP-IDF HaLow component](https://components.espressif.com/components/morsemicro/halow),
[Heltec and Morse Micro](https://www.microwavejournal.com/articles/44273-heltec-automation-partners-with-morse-micro-to-advance-iot-connectivity-with-wifi-halow),
[Meshtastic component readme](https://components.espressif.com/components/espp/meshtastic/versions/1.3.5/readme),
[batman-adv kernel docs](https://kernel.org/doc/Documentation/networking/batman-adv.rst),
[OpenWrt batman-adv](https://openwrt.org/docs/guide-user/network/wifi/mesh/batman),
[VE.Direct protocol](https://www.victronenergy.nl/upload/documents/VE.Direct-Protocol-3.32.pdf),
[rtl_433](https://github.com/merbanan/rtl_433),
[EVerest](https://www.pionix.com/everest),
[LF Energy and NEVI](https://lfenergy.org/u-s-joint-office-of-energy-and-transportation-partners-with-linux-foundation-energy-to-improve-ev-charging-nationally/).

## Changelog

- 2026-10-06: v1.5, product name per the ADR-0039 amendment: "Ostler Hub" is now **Ostler Brain**; "hub" (our compute box) reads "Brain".
- 2026-10-06: v1.4, product names per ADR-0039: Ostler Diagnostics (was Ostler Lite) and
  Ostler Hub; the bike row reads a Diagnostics node + phone; the u-blox row's placement is
  decided (on the Diagnostics node).

- 2026-10-06: v1.3, owner's networking answers (ADR-0038 and ADR-0037 accepted, ADR-0027
  and ADR-0032 Amendments): the LoRa row is the first mesh add-on, Meshtastic-compatible
  first, phase next, with the bridge in `ostler-bridge-meshtastic` (GPL-3.0-or-later); the
  richer mesh row is a later goal with all four projects as references; the Matter row gains
  disarm and the "certified only at scale" rule; the GNSS / RTK row splits into a 10 Hz
  u-blox row (next, placement pending) and an RTK row (later).
- 2026-10-06: v1.2, mesh and Matter (ADR-0038 draft, ADR-0027 proposed amendment): the
  LoRa row becomes a Meshtastic-compatible LoRa add-on behind a thin VSS bridge (phase
  next); the batman-adv convoy row is replaced by a richer car-to-car mesh row and a
  Babel-first Wi-Fi IP mesh row; the Matter bridge row gains the entity set and the gate
  rule; a mesh live-check bullet links the new research.

- 2026-10-06: v1.1, node/brain direction (ADR-0032/0033): the guardian row becomes a node
  hardware variant; the relay box becomes our own I/O / relay boards later with an ADR per
  switching function; sensor-node rows added (fast tacho, EGT, boost/oil, wideband AFR,
  extra accelerometers, read-only isolated taps); bike rows become a Lite node + phone or
  a guardian-variant node; "alarms are notify-only" dropped.

- 2026-10-06: v1.0, first catalogue, from the owner's direction ("anything you can think
  of") and live checks.
