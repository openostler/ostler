---
title: "Add-ons catalogue — module ideas with transport, standards and phase"
area: references
status: draft
version: 1.0
updated: 2026-10-06
depends_on: [references/vision.md, references/research/ecosystem_architecture.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, references/research/features_backlog.md]
summary: >
  A catalogue of add-on module ideas for the Ostler ecosystem (guardian alarm and gateway, cameras and dashcam, 360 view, relay box, sensor pods, buttons, displays and head unit, gauges, TPMS, LoRa/Meshtastic convoy messaging, Wi-Fi HaLow link to home, B.A.T.M.A.N.-adv/802.11s convoy mesh, GNSS/RTK, cellular and Starlink gateway, CAN/T1S bridges, leisure battery and solar via Victron VE.Direct, EV charger via OCPP/ISO 15118, camper and overland kit, tracker, OBD dongle, winch and lights, weather station, trailer, motorcycle modules and more), each with what it does, its transport, the open standards it should use and a phase (now / next / later / idea), plus rules every add-on follows and live-checked facts (October 2026) with sources.
---

# Add-ons catalogue

Ideas for add-on modules, the long-term half of [vision §5](../vision.md#5-add-ons-anything-you-can-think-of).
This is a parking lot, not a commitment: each module needs a spec, and the
[feature backlog](features_backlog.md) tags still apply (add-ons are off by default). Facts
were checked live in **October 2026**; **(U)** means unverified.

## Rules every add-on follows

- **One module contract** ([ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md),
  [ecosystem research §3.2](ecosystem_architecture.md#32-the-module-contract-a-device-side-twin-of-the-vehicle-pack-contract)):
  an IP host, found by mDNS/DNS-SD, speaking VSS-named MQTT 5, with a manifest of signals
  and safety-tiered actions. Devices that cannot describe themselves get a DevicePack
  adapter.
- **Stands on its own.** Each module hosts a small web page with its basic controls (like
  an IP camera or an ESP32 project) and keeps working without the base pack. No default
  passwords.
- **The one server gate.** Every action passes it; remote paths stay read-only (plus arming
  the software alarm). No module writes to a vehicle ECU or bus except through the
  platform's gates; MQTT is never bridged to vehicle CAN
  ([ADR-0020](../../decisions/adr-0020-can-links-listen-only-by-default.md)).
- **Alarm-critical links are wired** (T1S or CAN), never Wi-Fi
  ([ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md)). Alarms are notify-only.
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
| **Guardian: alarm and gateway** | Always-on ESP32 with its own cell, IoT SIM and GNSS: tracker, geofences, **notify-only** alarm (strong/weak triggers, tamper), notification escalation, an LTE uplink and gateway, may host the parked broker (the base's buddy keeps the PLCA coordinator role, [ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)) | T1S; CAN or wake wire as fallback; LTE uplink | MQTT 5 + HA discovery, OwnTracks, Traccar OsmAnd, ntfy | next (Phase 2) |
| **Relay box** | Switched outputs for accessories; each channel declares a tier (default Tier 2, Parked-only, never remote) | T1S; CAN fallback | MQTT + HA discovery (`switch`) | next (Phase 4) |
| **Sensor pods** | Temperature, humidity, tilt/inclinometer, door/bonnet/tailgate contacts, PIR, cabin CO and air quality (advisory only, not a certified detector) | T1S; BLE for battery pods | MQTT + HA discovery; BTHome for BLE pods | next |
| **Dash buttons and keypads** | Panel buttons, rotary encoders, a PIN keypad for the notify alarm; events, not direct actions | T1S; CAN fallback | MQTT events, HA device triggers | next |
| **Gauge display** | A small round or bar display for chosen signals | T1S | VSS paths via MQTT | next |
| **Displays / head unit** | The PWA on any screen, head-unit first; later an Ostler Android launcher | Wi-Fi, USB (NCM/RNDIS) | PWA, the documented head-unit CAN-box protocol | now |
| **Head-unit CAN/OBD emulator** | Feeds an aftermarket head unit the CAN messages it expects | CAN (its own, never the car's) | Head-unit CAN-box protocols | next (Phase 4) |
| **Cameras** | Dashcam, parking and alarm clips, reversing, underbody in one timeline | Eth / PoE (never T1S) | ONVIF, RTSP, go2rtc; optional Frigate | now (off the shelf) |
| **360° surround view** | Stitched view from four cameras | Eth; our own 100BASE-T1 cameras later | ONVIF/RTSP | later (ADR-0018) |
| **HEVAC controller** | The owner's separate climate project, joined as a device | T1S or Wi-Fi | Module contract, `comfort` actions | external |

## 2. Connectivity and range

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **Cellular / Starlink gateway** | The base has no SIM by default; uplinks: car/head-unit Wi-Fi, phone hotspot, home Wi-Fi, any 3G/4G USB dongle, an OpenWrt high-speed gateway, Starlink, the guardian's LTE; Auto failover or a pinned source, metered with data-cap alerts. Remote access: LAN default, then Tailscale, Ostler Cloud, HA Cloud | USB, Eth, Wi-Fi | USB NCM/RNDIS/QMI, ModemManager, OpenWrt; Tailscale (WireGuard) | next ([ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md)) |
| **Wi-Fi HaLow link to home** | A long-range, low-rate link from the parked car to the house: alarm events, telemetry, a low-rate camera still | HaLow | IEEE 802.11ah; MQTT over it | later |
| **LoRa / Meshtastic convoy messaging** | Text and positions between vehicles and riders with no phone signal: overlanders, off-road groups, bikers | LoRa (868 MHz EU, 915 MHz US) | Meshtastic (its serial/protobuf or MQTT interface) | later |
| **Car-to-car convoy mesh** | An IP mesh between the base packs of vehicles in a convoy: shared positions, messages, a shared uplink | Wi-Fi (or HaLow) | batman-adv over 802.11s or ad-hoc | idea |
| **CAN / T1S bridges** | Joins a CAN-only node or a second T1S segment to the IP network | CAN, T1S | SocketCAN; listen-only to any vehicle bus by default | next |
| **Matter bridge** | Shows the car's sensors to Matter ecosystems, read-only | Wi-Fi/Eth (home side) | Matter bridge device type | later |

## 3. Vehicle extras

| Module | What it does | Transport | Standards | Phase |
|---|---|---|---|---|
| **TPMS receiver** | Reads aftermarket or OEM tyre sensors | 315/433 MHz receiver (SDR or a sub-GHz radio) on T1S or USB | rtl_433 decoders, MQTT | later |
| **GNSS / RTK** | 10 Hz logging and timing now; centimetre RTK for lap timing, surveying and trails later | T1S or USB | NMEA 0183, UBX, RTCM 3 over NTRIP | later |
| **Tracker** | A small hidden tracker on its own cell, separate from the guardian | LTE-M/NB-IoT or LoRa | OwnTracks, Traccar OsmAnd | later |
| **OBD dongle** | A Wi-Fi/BLE OBD front end for `generic_obd2` | Wi-Fi, BLE | ELM327 AT, slcan/SocketCAN (e.g. WiCAN Pro) | next ([ADR-0031](../../decisions/adr-0031-generic-obd2-pack-in-platform.md)) |
| **Winch and lights control** | Work lights, light bars, winch in/out with interlocks; physical controls stay primary | T1S via the relay box | MQTT + HA discovery; tiered actions, Parked-only, never remote | later |
| **Trailer / caravan module** | Lights check, hitch and tilt, tyre pressure, trailer battery | T1S over a trailer harness, or Wi-Fi/BLE | MQTT + HA discovery | idea |
| **Parking sensors** | Ultrasonic distance for retrofit parking aid | T1S | MQTT | idea |
| **Phone presence** | Notices the owner's phone to quiet the notify-only alarm; never unlocks the car | BLE | BLE advertising; HA presence | idea |

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
| **Bike base node** | A compact base pack for bikes: diagnostics where the bike allows it (many older bikes use K-line, (U) per make), lean angle and IMU logging, GNSS | BLE/Wi-Fi to the phone; no module bus | VSS, MQTT; the same `VehiclePack` contract | later |
| **Bike tracker and alarm** | Notify-only movement and tilt alarm with its own cell | LTE-M or LoRa | OwnTracks, Traccar OsmAnd | later |
| **Group rides** | Positions and messages within a riding group, with or without phone signal | LoRa (Meshtastic) and the phone | Meshtastic; the social layer of [vision §6](../vision.md#6-many-vehicles-many-people) | later |
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

- 2026-10-06: v1.0, first catalogue, from the owner's direction ("anything you can think
  of") and live checks.
