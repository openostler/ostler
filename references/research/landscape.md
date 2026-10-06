---
title: "Open-source landscape — automotive diagnostics, telemetry, racing, tracking, security (Oct 2026)"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md]
summary: >
  About 340 open-source projects relevant to growing the D2 tool into an open vehicle platform, grouped by area, each with its licence and AGPL-3.0 compatibility, activity and why it matters to us; plus top picks, the best vehicle-data sources, licence red flags and the gaps nobody owns.
---

# Open-source landscape (October 2026)

## How this was made, and how to read it

**Sources.** Six research passes on 2026-10-05:

- **First pass:** a broad sweep.
- **Deeper passes:**
  - OVMS;
  - open diagnostics;
  - racing, security and tracking;
  - two ready-made hardware surveys.

**Verification.**

- GitHub URLs were checked against GitHub search.
- Licences come from the LICENSE/COPYING file, or from source headers where it mattered.
- **(U)** means unverified.
- Stars and activity are as of October 2026.

**Licence key, read against our AGPL-3.0-or-later code (ADR-0012):**

| Mark | Meaning | What we may do |
|---|---|---|
| 🟢 | Permissive (MIT, BSD, Apache, ISC, CC0, Unlicense) | Reuse with attribution |
| 🟡 | LGPL, MPL, EPL, CC BY-SA | Use as a dependency or data package. **EPL is GPL-incompatible.** |
| 🔴✓ | GPL-3, GPL-2-or-later, AGPL | Compatible since our move to AGPL; reuse with the notice |
| 🔴✗ | GPL-2-only, non-commercial, source-available | **Do not copy** |
| ⚠️ | No licence (all rights reserved) | Facts only; ask the author for a licence |

**Relevance codes:**

| Code | Meaning |
|---|---|
| **L** | Library to reuse |
| **P** | Protocol reference |
| **D** | Vehicle data |
| **U** | UX inspiration |
| **C** | Competitor or peer |
| **I** | Integrate with |
| **F** | File format |

## Top picks

| # | Project | Licence | Why |
|---|---|---|---|
| 1 | [OBDb](https://github.com/OBDb) (745+ per-model repos, [SAEJ1979](https://github.com/OBDb/SAEJ1979), [.schemas](https://github.com/OBDb/.schemas)) | 🟡 CC BY-SA | Universal OBD-II / mode-22 signal database with a clean JSON schema and test cases. It has no D2/Td5 repo, so we can contribute one. |
| 2 | [OpenVehicleDiag](https://github.com/rnd-ash/OpenVehicleDiag) + [ecu_diagnostics](https://github.com/rnd-ash/ecu_diagnostics) | 🔴✓ GPL-3 | Its ECU JSON schema (ECU → variants → errors, adjustments, actuations, functions) is the closest existing design to our vehicle packs. Its DMCA lesson is in [Licence red flags](#licence-red-flags). |
| 3 | [OVMS v3](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3) | 🟢 MIT (mostly) | The closest open telematics system: metric namespace, per-state polling, events, staged power-down, MQTT. See [ovms.md](ovms.md). |
| 4 | python-can · [python-can-isotp](https://github.com/pylessard/python-can-isotp) · [python-udsoncan](https://github.com/pylessard/python-udsoncan) · [mdabrowski1990/uds](https://github.com/mdabrowski1990/uds) | 🟡 LGPL / 🟢 MIT | CAN, ISO-TP and UDS stack. `uds` also covers **K-line**. |
| 5 | [opendbc](https://github.com/commaai/opendbc) + [cantools](https://github.com/cantools/cantools) | 🟢 MIT | DBC data for broadcast CAN, plus a decoder |
| 6 | Td5: [td5keygen](https://github.com/pajacobson/td5keygen), [TD5Tester](https://github.com/hairyone/TD5Tester), [Td5OpenDiag](https://github.com/Td5OpenDiag/Td5OpenDiag-android), [SimonRafferty Td5 apps](https://github.com/SimonRafferty/Td5-Diagnostic-App) | 🟢 BSD-2 / Apache / MIT | The permissively licensed Td5 references (seed→key, PIDs) |
| 7 | [Oleg-mk/jlr-scanner](https://github.com/Oleg-mk/jlr-scanner) | 🔴✓ AGPL | Rust + Tauri + React, read-only SDD-era JLR. **Closest peer for Discovery 3/4; collaborate.** |
| 8 | [zigbee-herdsman-converters](https://github.com/Koenkk/zigbee-herdsman-converters) | 🟢 MIT | Proven pattern for a device-definition database (fingerprint → exposes → converters) |
| 9 | [Traccar](https://github.com/traccar/traccar) + [OwnTracks](https://github.com/owntracks/recorder) protocol | 🟢 Apache / 🔴✓ GPL-2+ | Tracking backends we don't have to build |
| 10 | [go2rtc](https://github.com/AlexxIT/go2rtc) | 🟢 MIT | Camera streams into the PWA (WebRTC/MSE) |
| 11 | [rtl_433](https://github.com/merbanan/rtl_433) + [rtl_433_ESP](https://github.com/NorthernMan54/rtl_433_ESP) | 🔴✓ | TPMS (tyre-pressure) reading |
| 12 | [Meshtastic](https://github.com/meshtastic/firmware) ([python](https://github.com/meshtastic/python)) | 🔴✓ GPL-3 | Off-grid LoRa convoy tracking for overlanding |
| 13 | [racer-coder/TrackDataAnalysis](https://github.com/racer-coder/TrackDataAnalysis) | 🟢 MIT | Readers for AiM, MoTeC and RaceCapture logs: import competitors' data |
| 14 | [ddt4all](https://github.com/cedricp/ddt4all) | 🔴✓ GPL-3 | UX benchmark for ECU screens and plugin procedures (1.9k★) |
| 15 | [WiCAN](https://github.com/meatpiHQ/wican-fw) | 🔴✓ GPL-3 | Nearest product peer; the ESP32-S3 dongle does CAN and **K-line**. See [hardware.md](hardware.md). |

## 1. Vehicle telematics platforms and firmware

| Project | What | Lang | Licence | ★ / active | Rel |
|---|---|---|---|---|---|
| [OVMS v3](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3) | ESP32 vehicle module: per-vehicle components, metrics, MQTT, web UI | C++ | 🟢 MIT (the binary links GPL-2 mongoose/wolfSSL) | 863 / 2026 | C, U, D |
| [OVMS v2](https://github.com/openvehicles/Open-Vehicle-Monitoring-System) · [Server](https://github.com/openvehicles/Open-Vehicle-Server) · [Android](https://github.com/openvehicles/Open-Vehicle-Android) | Legacy PIC module; Perl server; apps | C/Perl/Kotlin | 🟢 MIT (server licence U) | dormant / 2026 / 2026 | P |
| [Traccar](https://github.com/traccar/traccar) · [web](https://github.com/traccar/traccar-web) · [client](https://github.com/traccar/traccar-client) · [manager](https://github.com/traccar/traccar-manager) | GPS tracking server (200+ protocols) and apps | Java/JS/Dart | 🟢 Apache | 7.8k / 2026 | I |
| [comma panda](https://github.com/commaai/panda) · [openpilot](https://github.com/commaai/openpilot) | CAN interface with a safety model; driver-assistance OS with log/replay tooling | C/Py | 🟢 MIT | 1.7k / 63.8k | U, L |
| [TeslaMate](https://github.com/teslamate-org/teslamate) | Self-hosted Tesla logger | Elixir | 🔴✓ AGPL | 9.1k / 2026 | U |
| [TeslaLogger](https://github.com/bassmaster187/TeslaLogger) | TeslaMate alternative | C# | 🔴✓ GPL-3 | 639 / 2026 | U |
| [evcc](https://github.com/evcc-io/evcc) | EV charging, with a vehicle adapter registry | Go | 🟢 MIT | 7.3k / 2026 | U |
| [Tesla fleet-telemetry](https://github.com/teslamotors/fleet-telemetry) · [vehicle-command](https://github.com/teslamotors/vehicle-command) | Tesla's own streaming telemetry server; signed commands | Go | 🟢 Apache | 892 / 710 | P (architecture) |
| [Freematics](https://github.com/stanleyhuangyc/Freematics) | ONE+ ESP32 OBD/GNSS/LTE firmware and Hub | C++ | ⚠️ | 501 / 2025 | P, C |
| [OpenXC vi-firmware](https://github.com/openxc/vi-firmware) · [openxc-python](https://github.com/openxc/openxc-python) | Ford CAN translator with a JSON signal map | C++/Py | 🟢 BSD-3 | 211 / dormant | P |
| [Carloop](https://github.com/carloop/carloop-library) | CAN library for Particle cellular boards | C++ | 🟢 MIT | 132 / dormant | P |
| [Macchina M2 hardware](https://github.com/macchina/m2-hardware) | Open OBD hardware with 2× K-line | HW | U | 111 / 2026 | P |
| [autopi-core](https://github.com/autopi-io/autopi-core) | Software for the AutoPi Pi-CM4 car dongle | Py | 🟢 Apache | 188 / 2026 | L, U |
| [CarConnectivity](https://github.com/tillsteinbach/CarConnectivity) | Multi-brand car API with MQTT | Py | 🟢 MIT | 215 / 2026 | U (schema) |
| [SignalK server](https://github.com/SignalK/signalk-server) | Open **marine** data model and plugin server | TS | 🟢 Apache | 437 / 2026 | U (data model): the closest analogue to what we're building |
| [fleetbase](https://github.com/fleetbase/fleetbase) · [openremote](https://github.com/openremote/openremote) | Fleet and IoT platforms | JS/Java | 🔴✓ AGPL | 4.2k / 1.9k | C |
| [ThingsBoard](https://github.com/thingsboard/thingsboard) | IoT platform | Java | 🔴✗ BSL from v4.4 | 22.5k | avoid |
| [smartcar SDK](https://github.com/smartcar/python-sdk) | Closed cloud API | Py | 🟢 MIT SDK | 48 | C |

## 2. Diagnostics: OpenVehicleDiag and its author

**OpenVehicleDiag** ([repo](https://github.com/rnd-ash/OpenVehicleDiag)):

- **Basics:** Rust, GPL-3, about 1k★, release v1.0.5 (2021), last push July 2025.
- **GUI:** built with iced.
- **Hardware access:**
  - J2534 (any adapter on Windows);
  - SocketCAN on Linux (work in progress);
  - Macchina M2 through his own J2534 driver.
- **Tools:** CAN tracer, OBD toolbox, UDS/KWP scanner.
- **`CBFParser`:** turns Mercedes CBF files into **OVD ECU JSON** (SCHEMA v1.0), a simpler stand-in for ODX/CBF/SMR-D.
- **DMCA takedown:** the SMR-D parser was removed after one.

**The same author's other repos:**

| Repo | What | Licence | Rel |
|---|---|---|---|
| [ecu_diagnostics](https://github.com/rnd-ash/ecu_diagnostics) | UDS/KWP2000/OBD2 diagnostic server crate with a pass-through API and C FFI | 🔴✓ GPL-3 (was MIT) | L, P |
| [oxibus/automotive_diag](https://github.com/oxibus/automotive_diag) | Fork of the last MIT version: UDS/KWP/OBD/DoIP definitions | 🟢 MIT/Apache | L |
| [Macchina-J2534](https://github.com/rnd-ash/Macchina-J2534) | J2534 driver for M2/A0 | ⚠️ | P |
| [J2534-Rust](https://github.com/rnd-ash/J2534-Rust) · [dpdu-rust](https://github.com/rnd-ash/dpdu-rust) | J2534 and D-PDU definitions | 🟢 MIT | L |
| [m2-utd-dpdu](https://github.com/rnd-ash/m2-utd-dpdu) | D-PDU driver for M2 | 🔴✓ GPL-3 | P |
| [openStar](https://github.com/rnd-ash/openStar) | Xentry/DAS-style tool | ⚠️ | U |
| [mercedes-hacking-docs](https://github.com/rnd-ash/mercedes-hacking-docs) | Reverse-engineering write-ups | ⚠️ | P |
| [ultimate_nag52](https://github.com/rnd-ash/ultimate_nag52) · [fw](https://github.com/rnd-ash/ultimate-nag52-fw) · [config-app](https://github.com/rnd-ash/ultimate-nag52-config-app) | Open 722.6 transmission controller (KWP/UDS) | ⚠️ / 🔴✓ / 🔴✓ | P, U |
| [EGS52_emu](https://github.com/rnd-ash/EGS52_emu) | Transmission ECU emulator | 🔴✓ | P |
| [MBUX-Port](https://github.com/rnd-ash/MBUX-Port) · [W203-canbus](https://github.com/rnd-ash/W203-canbus) · [mb-w211-pc](https://github.com/rnd-ash/mb-w211-pc) | Mercedes infotainment builds | ⚠️ / 🟢 / 🔴✓ | U |
| [canviewer-rs](https://github.com/rnd-ash/canviewer-rs) | Live CAN viewer with DBC | 🔴✓ | U |

## 3. Diagnostics: J2534 / pass-thru, ODX / CBF / SOVD

| Project | What | Licence | Rel |
|---|---|---|---|
| [NikolaKozina/j2534](https://github.com/NikolaKozina/j2534) | Linux J2534 for Tactrix OpenPort 2.0 | 🟢 BSD-3 | L |
| [keenanlaws/Python-J2534-Interface](https://github.com/keenanlaws/Python-J2534-Interface) | Python J2534 | 🟢 MIT | L |
| [jcmnn/j2534-rs](https://github.com/jcmnn/j2534-rs) | Rust J2534 | 🟢 MIT | L |
| [diamondman/J2534-PassThru-Logger](https://github.com/diamondman/J2534-PassThru-Logger) | Logs J2534 API calls (shim DLL) | 🟢 MIT | P |
| [Xplatforms/J2534_OIP_Wrapper](https://github.com/Xplatforms/J2534_OIP_Wrapper) | J2534 over IP | 🔴✓ | L |
| [fenugrec/J2534tool](https://github.com/fenugrec/J2534tool) · [joeFischetti/python-j2534](https://github.com/joeFischetti/python-j2534) · [J2534DotNet](https://github.com/beyerch/J2534DotNet) | Testers and wrappers | ⚠️ | P |
| [mercedes-benz/odxtools](https://github.com/mercedes-benz/odxtools) | ODX/PDX (ISO 22901) parse, encode and decode | 🟢 MIT | **L, D**: import path |
| [jglim/CaesarSuite](https://github.com/jglim/CaesarSuite) · [UnlockECU](https://github.com/jglim/UnlockECU) | Daimler CBF library; pluggable seed-key | 🟢 MIT | P, **L** |
| [eclipse-opensovd](https://github.com/eclipse-opensovd/opensovd) · [classic-diagnostic-adapter](https://github.com/eclipse-opensovd/classic-diagnostic-adapter) · [odx-converter](https://github.com/eclipse-opensovd/odx-converter) | SOVD (REST) server and gateway; ODX → MDD | 🟢 Apache | **P**: template for a future UDS/DoIP/REST layer |
| [bri3d/mcd-diag-rs](https://github.com/bri3d/mcd-diag-rs) | VW MCD-driven diagnostics | 🟢 BSD | P |

## 4. Diagnostics by make

| Make | Projects (licence) | Rel |
|---|---|---|
| Renault / PSA | [ddt4all](https://github.com/cedricp/ddt4all) (🔴✓; ECU databases are user-supplied, **not shippable**); [pyren](https://gitlab.com/py_ren/pyren) (U); [CanZE](https://github.com/fesch/CanZE) + [iOS](https://github.com/fesch/CanZE4iOS) (🔴✓; frame/field CSVs in the repo); [arduino-psa-diag](https://github.com/ludwig-v/arduino-psa-diag) and [psa-seedkey](https://github.com/ludwig-v/psa-seedkey-algorithm) (🔴✓) | U, P, **D** |
| VAG | [VW_Flash](https://github.com/bri3d/VW_Flash) (🟢 BSD-2); [sa2_seed_key](https://github.com/bri3d/sa2_seed_key) (🟢); [esp32-isotp-ble-bridge](https://github.com/bri3d/esp32-isotp-ble-bridge) (🟢: PWA ↔ Web Bluetooth ↔ ISO-TP); [pq-flasher](https://github.com/I-CAN-hack/pq-flasher) (🟢: clean TP2.0 + KWP2000); [KLineKWP1281Lib](https://github.com/domnulvlad/KLineKWP1281Lib) (🔴✓); [kw1281test](https://github.com/gmenounos/kw1281test) (🟢); [vwradio](https://github.com/mnaberez/vwradio) (🟢); [vagtuner](https://github.com/michaeldove/vagtuner) / [vag-diag-sim](https://github.com/michaeldove/vag-diag-sim) (🟢); [jared52005/Monitor](https://github.com/jared52005/Monitor) (🟢: CAN/K-line into Wireshark with UDS/KWP dissection) | L, P |
| BMW | [EdiabasLib / Deep OBD](https://github.com/uholeschak/ediabaslib) (🔴✓); [pydiabas](https://github.com/BembelBytes/pydiabas) (🟢); [klartext](https://github.com/HadiCherkaoui/klartext) (🔴✓ AGPL, ENET/UDS in Rust); [bmw-f](https://github.com/packetpilot/bmw-f) (🔴✓); [BimmerDis](https://github.com/radelbro/BimmerDis) (⚠️); [ediabasx](https://github.com/emdzej/ediabasx) (🔴✗ PolyForm NC) | P, D |
| Saab / Volvo | [TuningSuites T5/T7/T8](https://github.com/mattiasclaesson/TuningSuites) (🟢 Apache); [Trionic](https://github.com/mattiasclaesson/Trionic) (⚠️); [Volvo-CAN-Gauge](https://github.com/Alfaa123/Volvo-CAN-Gauge) (⚠️); [Volvo-VIDA](https://github.com/Tigo2000/Volvo-VIDA) (🔴✓) | D |
| Subaru / Nissan / Honda / Mitsubishi | [RomRaider](https://github.com/RomRaider/RomRaider) (🔴✓ GPL-2+; XML definitions); [LibSSM2](https://github.com/src0x/LibSSM2) (🔴✓); [openconsult](https://github.com/jonsim/openconsult) / [K11Consult](https://github.com/fridlington/K11Consult) (🔴✓); [nisprog](https://github.com/fenugrec/nisprog) (🔴✓); [ArduinoHondaOBD](https://github.com/kerpz/ArduinoHondaOBD) (⚠️); [libmut](https://github.com/harshadura/libmut) (⚠️); [KWP2000 for bikes](https://github.com/aster94/Keyword-Protocol-2000) (🔴✓) | D, P |
| Ford / Toyota / GM / Fiat | [ford-eec-iv-diagnostic](https://github.com/babroval/ford-eec-iv-diagnostic) (🟢); [eec-iv-reader](https://github.com/flxkrmr/eec-iv-reader-arduino) (🔴✓); [toyota-obd-1](https://github.com/hyperion11/toyota-obd-1) (🔴✓); [GM-ECU-Simulator](https://github.com/hjtrbo/GM-ECU-Simulator) (🔴✓ AGPL dual); [arduino-gmlan](https://github.com/Afterglow/arduino-gmlan) (⚠️); [iaw-scan-3](https://github.com/intilinux-eng/iaw-scan-3) (🟢/🟡) | P |
| EVs | [EVNotify](https://github.com/EVNotify/EVNotify) (⚠️); EVNotiPi (🔴✗ NC); [evDash](https://github.com/nickn17/evDash) (🟢); [OBD-PIDs-for-HKMC-EVs](https://github.com/JejuSoul/OBD-PIDs-for-HKMC-EVs) (⚠️ data); [Battery-Emulator](https://github.com/dalathegreat/Battery-Emulator) (🔴✓); [model3dbc](https://github.com/joshwardell/model3dbc) (🟢); [LeafCAN](https://github.com/lincomatic/LeafCAN) (🔴✓); [niro-spy](https://github.com/Tuoris/niro-spy) (U: Web Bluetooth PWA, same stack as ours) | D, U |

## 5. Land Rover / Rover / MG (home turf)

| Project | What | Licence | Rel |
|---|---|---|---|
| [rovergauge](https://github.com/colinbourassa/rovergauge) · [libcomm14cux](https://github.com/colinbourassa/libcomm14cux) · [librosco](https://github.com/colinbourassa/librosco) | 14CUX and MEMS display, diagnostics and libraries | 🔴✓ GPL-3 | **L, P**: ready-made packs |
| [memsfcr](https://github.com/andrewdjackson/memsfcr) · [webmemsfcr](https://github.com/andrewdjackson/webmemsfcr) | MEMS fault-code reader, also a web version | 🔴✓ / U | U |
| [openEAS-tool](https://github.com/jdselby24/openEAS-tool) | Range Rover Classic / P38 air-suspension ECU tool | 🔴✓ | **P** |
| [jlr-scanner](https://github.com/Oleg-mk/jlr-scanner) | Read-only SDD-era JLR diagnostics, every module | 🔴✓ AGPL | **C, L** |
| [Ekaitza_Itzali](https://github.com/EA2EGA/Ekaitza_Itzali) | Td5 diagnostic tool (our existing protocol reference) | ⚠️ | P |
| [td5keygen](https://github.com/pajacobson/td5keygen) | Td5 seed→key (ported in `td5/keygen.py`) | 🟢 BSD-2 | L |
| [TD5Tester](https://github.com/hairyone/TD5Tester) · [Td5OpenDiag](https://github.com/Td5OpenDiag/Td5OpenDiag-android) | Td5 tools | 🟢 Apache | P, D |
| [SimonRafferty Td5 app](https://github.com/SimonRafferty/Td5-Diagnostic-App) · [Arduino](https://github.com/SimonRafferty/Land-Rover-Td5-Arduino-Diagnostics) | Td5 over ELM327; Defender live data | 🟢 MIT | C, P |
| [LRDuinoTD5](https://github.com/BennehBoy/LRDuinoTD5) | STM32 multi-gauge using an L9637D | 🟢 Beerware | P |
| [TD5EcuEmulatorMM](https://github.com/BennehBoy/TD5EcuEmulatorMM) · [TD5EcuEmulator](https://github.com/BennehBoy/TD5EcuEmulator) · [td5opencomstm32](https://github.com/BennehBoy/td5opencomstm32) | Td5 ECU emulators (bench rig) | ⚠️ | L (bench), P |
| [Td5MapEditor](https://github.com/Luca72/Td5MapEditor) · [td5utils](https://github.com/pajacobson/td5utils) | Td5 maps | 🔴✓ | D |
| [BinOwl_Td5Gauge](https://github.com/k0sci3j/BinOwl_Td5Gauge) | ESP32 Td5 gauge | 🔴✓ | P |
| [td5-storm](https://github.com/adriannovegil/td5-storm) · [TD5_Touchscreen](https://github.com/LoetLuemmel/TD5_Touchscreen) | Td5 dashboards | ⚠️ / U | U |
| [lr-hudiy-rpi-hat](https://github.com/sedlons/lr-hudiy-rpi-hat) | Discovery II dash Pi HAT | 🔴✓ | U |
| [DeCANder](https://github.com/posmanet/DeCANder) · [OBD2_Interface_v2](https://github.com/bionicbone/OBD2_Interface_v2) · [LR rotary gear change](https://github.com/SomersetEV/LandRover-rotary-gear-change) | Defender / Freelander 2 / LR CAN | ⚠️ / U | D |
| [OBDb Landrover](https://github.com/OBDb/Landrover) · [LR4](https://github.com/OBDb/Land-Rover-LR4) · [Range Rover](https://github.com/OBDb/Land-Rover-Range-Rover) · [Velar](https://github.com/OBDb/Land-Rover-Range-Rover-Velar) | Signal sets | 🟡 CC BY-SA | D |
| [LandRoverErrorCodes](https://github.com/tslothorst/LandRoverErrorCodes) · [JLR_config_editor](https://github.com/mntsss/JLR_config_editor) | DTC list; VBF config | ⚠️ | D, P |
| [Leijoma/discovery2-diag](https://github.com/Leijoma/discovery2-diag) | This project's Swedish origin repo | — | — |

**Searched for, but found nothing open:** Nanocom, GAP IIDTool, Allisport, RRSport, Td5 EZ, rovercom, lr-diag, P38 BeCM, Freelander 1, Discovery 3 air suspension.

## 6. General scan tools, K-line, UDS and CAN

| Project | What | Licence | Rel |
|---|---|---|---|
| [python-OBD](https://github.com/brendan-w/python-OBD) | ELM327 OBD-II | 🔴 **GPL-2-only vs -or-later is reported both ways; check the headers before any use** | P |
| [pyobd (barracuda)](https://github.com/barracuda-fsh/pyobd) | Scan tool | 🔴✓ GPL-2+ | U, C |
| [OBDII (PaulMarisOUMary)](https://github.com/PaulMarisOUMary/OBDII) | Modern ELM327 library | 🟢 MIT | L |
| [ELMduino](https://github.com/PowerBroker2/ELMduino) · [arduino-OBD2](https://github.com/sandeepmistry/arduino-OBD2) | Arduino OBD | 🟢 MIT | L |
| [iwanders/OBD9141](https://github.com/iwanders/OBD9141) | ISO 9141/14230 K-line, with good timing notes | 🟢 MIT | **P, L** |
| [muki01 OBD2_K-line_Reader](https://github.com/muki01/OBD2_K-line_Reader) · [KLine lib](https://github.com/muki01/OBD2_KLine_Library) | ISO 9141, 14230, KW1281, DS2 | 🟢 reader MIT until `91ae045` (2026-10-01), 🔴✓ GPL-3.0 since 2026-10-03 / 🔴✗ lib (non-commercial headers; facts only) | P |
| [freediag](https://github.com/fenugrec/freediag) | ISO 9141/14230/J1850 scan tool | 🔴✓ GPL-3 | P |
| [AndrOBD](https://github.com/fr3ts0n/AndrOBD) | Android OBD with plugins and MQTT | 🔴✓ | U |
| [obdium](https://github.com/provrb/obdium) | Rust OBD app | 🔴✓ | U, C |
| [obd-java-api](https://github.com/pires/obd-java-api) · [kotlin-obd-api](https://github.com/eltonvs/kotlin-obd-api) · [node-bluetooth-obd](https://github.com/EricSmekens/node-bluetooth-obd) · [SwiftOBD2](https://github.com/kkonteh97/SwiftOBD2) | OBD APIs | 🟢 | P |
| [ArduinoOBD](https://github.com/stanleyhuangyc/ArduinoOBD) | Freematics OBD library | ⚠️ | P |
| [obd2-mqtt](https://github.com/adlerre/obd2-mqtt) | ESP32 OBD → MQTT/HA | 🔴✓ | U |
| [EQM_OBDWEB](https://github.com/EQMOD/EQM_OBDWEB) · [PiOBDII](https://github.com/BirchJD/PiOBDII) | Web or Pi OBD | U | U |
| [ESP32-Bluetooth-OBD2-Gauge](https://github.com/VaAndCob/ESP32-Bluetooth-OBD2-Gauge) | Gauge | 🔴✗ MIT-NoCommercial | U |
| [dtc-database](https://github.com/Wal33D/dtc-database) | 28k DTCs | 🟢 MIT (check where the data came from) | D |
| [CaringCaribou](https://github.com/CaringCaribou/caringcaribou) | UDS/XCP discovery and fuzzing | 🔴✓ | **L**: discovery on undocumented LR ECUs |
| [CANalyzat0r](https://github.com/schutzwerk/CANalyzat0r) · [UDSim](https://github.com/zombieCraig/UDSim) · [ICSim](https://github.com/zombieCraig/ICSim) | CAN security and simulators | 🔴✓ | test |
| [can-isotp](https://github.com/hartkopp/can-isotp) · [can-utils](https://github.com/linux-can/can-utils) | Kernel ISO-TP; SocketCAN tools | 🟢 BSD option | L |
| [EcuBus-Pro](https://github.com/ecubus/EcuBus-Pro) | UDS/DoIP/LIN tool scripted in TypeScript | 🟢 Apache | U, L |
| [iso14229](https://github.com/driftregion/iso14229) | Embedded UDS | 🟢 MIT | L |
| [cangaroo](https://github.com/HubertD/cangaroo) · [BUSMASTER](https://github.com/rbei-etas/busmaster) · [SavvyCAN](https://github.com/collin80/SavvyCAN) · [CANdevStudio](https://github.com/GENIVI/CANdevStudio) · [cabana](https://github.com/commaai/cabana) | CAN analysers | 🔴✓ / 🔴✓ / 🟢 / 🟡 MPL / 🟢 (archived) | U |
| [esp32_can](https://github.com/collin80/esp32_can) · [ESP32RET](https://github.com/collin80/ESP32RET) · [candleLight_fw](https://github.com/candle-usb/candleLight_fw) | ESP32 TWAI; USB-CAN firmware | 🟢 / U | L |
| [scapy](https://github.com/secdev/scapy) | Automotive layers | 🔴 GPL-2 (check only vs or-later) | P |
| [awesome-canbus](https://github.com/iDoka/awesome-canbus) · [awesome-automotive-can-id](https://github.com/iDoka/awesome-automotive-can-id) | Indexes | U / 🟢 CC0 | D |
| [ELM327-emulator](https://github.com/Ircama/ELM327-emulator) | Multi-ECU emulator | 🔴✗ CC BY-NC-SA | local testing only |
| [ecu-simulator (lbenthins)](https://github.com/lbenthins/ecu-simulator) · [(shchers)](https://github.com/shchers/ecu-simulator) · [esp32-obd2-emulator](https://github.com/limiter121/esp32-obd2-emulator) | Test fixtures | 🟢 MIT / 🟢 Apache / 🟡 MPL | test |

## 7. Data logging and motorsport

| Project | What | Licence | Rel |
|---|---|---|---|
| [TrackDataAnalysis](https://github.com/racer-coder/TrackDataAnalysis) | Python readers for AiM, MoTeC and RaceCapture | 🟢 MIT | **L, F** |
| [motec-i2](https://github.com/afonso360/motec-i2) · [ldparser](https://github.com/gotzl/ldparser) · [MotecLogGenerator](https://github.com/stevendaniluk/MotecLogGenerator) · [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) | MoTeC .ld read and write | 🟢 / 🔴✓ / U / ⚠️ | F |
| [libxrk](https://github.com/m3rlin45/libxrk) · [xdrk](https://github.com/bmc-labs/xdrk) · [Aim_2_MoTeC](https://github.com/ludovicb1239/Aim_2_MoTeC) | AiM XRK files | U / U / 🟢 | F |
| [DovesDataViewer](https://github.com/TheAngryRaven/DovesDataViewer) · [DovesLapTimer](https://github.com/TheAngryRaven/DovesLapTimer) | Web viewer; GPS lap timing | 🔴✓ GPL-3 (usable since ADR-0012) | U, L |
| [bonogps](https://github.com/renatobo/bonogps) | ESP32 10 Hz GPS → RaceChrono/Harry's over BLE | 🟢 MIT | L |
| [racechrono-ble-diy-device](https://github.com/aollin/racechrono-ble-diy-device) · [RealDash-extras](https://github.com/janimm/RealDash-extras) | RaceChrono BLE / RealDash CAN specs | ⚠️ / 🟢 Unlicense | **F**: export targets |
| [OpenLapTimer](https://github.com/tongo/OpenLapTimer) · [hyperdrag](https://github.com/hyper-tuner/hyperdrag) · [kart-data-logger](https://github.com/nGoline/kart-data-logger) | Lap and drag timers | 🟢 | U |
| [lap-timer (superbrobenji)](https://github.com/superbrobenji/lap-timer) | ESP32 lap timer | 🔴✗ PolyForm Strict | avoid |
| [RaceCapture-Pro firmware](https://github.com/autosportlabs/RaceCapture-Pro_firmware) · [OBD2CAN](https://github.com/autosportlabs/OBD2CAN) · [CAN integrations](https://github.com/autosportlabs/RaceCapture_CAN_Bus_Integrations) · [ESP32-CAN-X2](https://github.com/autosportlabs/ESP32-CAN-X2) | Autosport Labs (RaceCapture app and Podium repos are gone) | 🔴✓ archived / 🔴✓ / U / ⚠️ | P |
| [gpmf-parser](https://github.com/gopro/gpmf-parser) · [gopro-telemetry](https://github.com/JuanIrache/gopro-telemetry) · [gpmf-extract](https://github.com/JuanIrache/gpmf-extract) · [telemetry-parser](https://github.com/AdrianEddy/telemetry-parser) · [OpenGoPro](https://github.com/gopro/OpenGoPro) | Action-camera telemetry and control | 🟢 | **L, I** |
| [gopro-dashboard-overlay](https://github.com/time4tea/gopro-dashboard-overlay) · [gpx2video](https://github.com/progweb/gpx2video) · [OpenLap](https://github.com/LaurensVR3/OpenLap) · [GPStitch](https://github.com/Romancha/GPStitch) · [OVRLEY](https://github.com/spirokai/OVRLEY) | Video telemetry overlays | ⚠️ / 🔴✓ ×4 | U |
| [hypertuner](https://github.com/hyper-tuner/hypertuner) · [hypertuner-cloud](https://github.com/hyper-tuner/hypertuner-cloud) · [mlg-cli](https://github.com/hyper-tuner/mlg-cli) · [mlg-converter](https://github.com/karniv00l/mlg-converter) · [ini](https://github.com/hyper-tuner/ini) | Open TunerStudio-style tools; .mlg log parsers | 🔴✓ / 🟢 ×4 | **F** (Speeduino/rusEFI logs in the PWA) |
| [rusEFI](https://github.com/rusefi/rusefi) · [FOME](https://github.com/FOME-Tech/fome-fw) · [Speeduino](https://github.com/speeduino/speeduino) · [MegaTunix](https://github.com/djandruczyk/MegaTunix) · [megasquirt_node_logger](https://github.com/boxidau/megasquirt_node_logger) | Open ECUs and loggers | 🔴 GPL-3 + extra terms (rusEFI/FOME) / 🔴 GPL-2 (Speeduino, MegaTunix: check) / 🟢 | I |
| [Fast-F1](https://github.com/theOehrly/Fast-F1) · [RaceIQ](https://github.com/SpeedHQ/RaceIQ) · [CrewChiefV4](https://github.com/mrbelowski/CrewChiefV4) | F1 analysis; React lap analysis; spoken callouts | 🟢 / 🔴✓ AGPL / 🟢 | **U** |
| [simetry](https://github.com/adnanademovic/simetry) · [simapi](https://github.com/Spacefreak18/simapi) · [pyirsdk](https://github.com/kutu/pyirsdk) · [ibt-telemetry](https://github.com/SkippyZA/ibt-telemetry) | Sim-racing telemetry (test data) | 🟢 / 🟡 / 🟢 / 🟢 | test |
| [racetrack-database](https://github.com/TUMFTM/racetrack-database) | Track centre lines | 🟡 LGPL | D |
| [Formula-Student-Telemetry](https://github.com/GKPr0/Formula-Student-Telemetry) · [UBC Consolidated-Firmware](https://github.com/UBCFormulaElectric/Consolidated-Firmware) · [Telematic-Control-Unit](https://github.com/CapibaribeR/Telematic-Control-Unit) | Formula Student stacks | U / 🟢 / 🔴✓ | U |
| [OpenLog](https://github.com/sparkfun/OpenLog) · [gps-tracker (lap timer)](https://github.com/gotzl/gps-tracker) · [gogi](https://github.com/MarinX/gogi) | Loggers | U / U / 🟢 | P |

## 8. Security, alarm and cameras

| Project | What | Licence | Rel |
|---|---|---|---|
| [go2rtc](https://github.com/AlexxIT/go2rtc) · [MediaMTX](https://github.com/bluenviron/mediamtx) · [WebRTC card](https://github.com/AlexxIT/WebRTC) | Camera streaming gateways | 🟢 MIT | **I** |
| [Frigate](https://github.com/blakeblackshear/frigate) · [Viseron](https://github.com/roflcoopter/viseron) · [kerberos agent](https://github.com/kerberos-io/agent) | NVR with object detection | 🟢 MIT | I |
| [motionEye](https://github.com/motioneye-project/motioneye) · [ZoneMinder](https://github.com/ZoneMinder/zoneminder) · [moonfire-nvr](https://github.com/scottlamb/moonfire-nvr) | Classic NVR | 🔴✓ | C |
| [ESP32-CAM_MJPEG2SD](https://github.com/s60sc/ESP32-CAM_MJPEG2SD) · [ESP32-CAM-Video-Recorder](https://github.com/jameszah/ESP32-CAM-Video-Recorder) · [esp32-cam-webserver](https://github.com/easytarget/esp32-cam-webserver) | ESP32-CAM recording | 🔴✓ AGPL (directly reusable) / 🔴✓ / U | **L** |
| [Alarmo](https://github.com/nielsfaber/alarmo) · [alarmo-card](https://github.com/nielsfaber/alarmo-card) · [hass-pandora-cas](https://github.com/alryaz/hass-pandora-cas) · [pandora-cas](https://github.com/turbulator/pandora-cas) | HA alarm model; car-alarm entity model | 🟢 | **U, I** |
| [rtl_433](https://github.com/merbanan/rtl_433) · [rtl_433_ESP](https://github.com/NorthernMan54/rtl_433_ESP) · [OpenMQTTGateway](https://github.com/1technophile/OpenMQTTGateway) · [rtl_433-hass-addons](https://github.com/pbkhrv/rtl_433-hass-addons) | Radio sensors including **TPMS** | 🔴✓ / 🔴✓ / 🔴✓ / ⚠️ | **I** |
| [jboone/tpms](https://github.com/jboone/tpms) · [flipperzero-tpms](https://github.com/wosk/flipperzero-tpms) | TPMS research | 🔴 GPL-2 (check) / ⚠️ | P |
| [canids](https://github.com/cjholoday/canids) · [CAN-MIRGU](https://github.com/sampathrajapaksha/CAN-MIRGU) | CAN intrusion detection; attack dataset | ⚠️ | idea, test |
| [teslausb](https://github.com/cimryan/teslausb) · [tesla_dashcam](https://github.com/ehendrix23/tesla_dashcam) · [tesla_dashcam_manager](https://github.com/SimonKagstrom/tesla_dashcam_manager) · [teslacam-browser](https://github.com/BobStrogg/teslacam-browser) · [teslacam](https://github.com/milesburton/teslacam) | Sentry-style clip handling | 🟢 | L, U |
| [dashcamigo](https://github.com/amkulikov/dashcamigo) · [blackclue](https://github.com/gandy92/blackclue) · [a119_join](https://github.com/miahi/a119_join) · [dride-core-pi](https://github.com/dride/dride-core-pi) · [dashcam-transporter](https://github.com/steve192/dashcam-transporter) · [dashcam-pi](https://github.com/notchum/dashcam-pi) · [Dash-USB](https://github.com/Sentry-Six/Dash-USB) | Dashcam viewers and ingest | 🔴✓ AGPL / 🟢 / 🔴✓ / 🟢 / 🔴✓ / 🔴✓ / U | **U, F** |
| [CarWatch](https://github.com/ThinkOffApp/CarWatch) | Pi 5 + dashcam + local AI "car agent" | 🔴✓ AGPL | **C** |

No notable open car alarm or immobiliser project exists. That gap is ours.

## 9. Tracking, location and off-grid

| Project | What | Licence | Rel |
|---|---|---|---|
| [OwnTracks recorder](https://github.com/owntracks/recorder) · [iOS](https://github.com/owntracks/ios) · [frontend](https://github.com/owntracks/frontend) · [Android](https://github.com/owntracks/android) | The de facto MQTT location JSON | 🔴✓ GPL-2+ / 🟢 / 🟢 / 🟡 **EPL (GPL-incompatible)** | **F, I** |
| [Dawarich](https://github.com/Freika/dawarich) · [Reitti](https://github.com/dedicatedcode/reitti) · [PhoneTrack](https://github.com/julien-nc/phonetrack) | Self-hosted location history | 🔴✓ AGPL | **I** |
| [Hauk](https://github.com/bilde2910/Hauk) · [GPSLogger](https://github.com/mendhak/gpslogger) · [Overland-iOS](https://github.com/aaronpk/Overland-iOS) · [ulogger-server](https://github.com/bfabiszewski/ulogger-server) | Share links and loggers | 🟢 / 🔴✓ / 🟢 / 🔴✓ | U |
| [Meshtastic firmware](https://github.com/meshtastic/firmware) · [python](https://github.com/meshtastic/python) · [web](https://github.com/meshtastic/web) · [Android](https://github.com/meshtastic/Meshtastic-Android) · [Apple](https://github.com/meshtastic/Meshtastic-Apple) · [MeshCore](https://github.com/meshcore-dev/MeshCore) | Off-grid LoRa mesh | 🔴✓ ×5 / 🟢 | **I** |
| [Akita CarNode](https://github.com/AkitaEngineering/Akita-CarNode-for-Reticulum) · [SoftRF](https://github.com/lyusupov/SoftRF) | Reticulum car node; FLARM-like proximity | U / 🔴✓ | idea |
| [LoRa_APRS_Tracker (richonguzman)](https://github.com/richonguzman/LoRa_APRS_Tracker) · [(lora-aprs)](https://github.com/lora-aprs/LoRa_APRS_Tracker) · [aprsdroid](https://github.com/ge0rg/aprsdroid) | APRS | 🔴✓ / 🟢 / 🔴 GPL-2 (check) | I |
| [TTGO-T-Beam-Car-Tracker](https://github.com/tekk/TTGO-T-Beam-Car-Tracker) · [gnss_lorawan_tracker](https://github.com/phfbertoleti/gnss_lorawan_tracker) · [T-SIM7000G Traccar tracker](https://github.com/onlinegill/LILYGO-TTGO-T-SIM7000G-ESP32-Traccar-GPS-tracker) · [Car-Assistant](https://github.com/ShonP40/Car-Assistant) | ESP32 trackers | 🔴✓ / 🟢 / ⚠️ / U | **P** (guardian reference) |
| [TinyGSM](https://github.com/vshymanskyy/TinyGSM) · [TinyGPSPlus](https://github.com/mikalhart/TinyGPSPlus) · [SparkFun u-blox GNSS v3](https://github.com/sparkfun/SparkFun_u-blox_GNSS_v3) · [LilyGo-Modem-Series](https://github.com/Xinyuan-LilyGO/LilyGo-Modem-Series) | Guardian firmware libraries | 🟡 LGPL / 🟡 / 🟢 / 🟢 | **L** |
| [Turf.js](https://github.com/Turfjs/turf) | Geofences and geometry in JS | 🟢 MIT | **L** |
| [Organic Maps](https://github.com/organicmaps/organicmaps) · [OsmAnd](https://github.com/osmandapp/OsmAnd) · [Trail-Sense](https://github.com/kylecorry31/Trail-Sense) · [OpenTrailMap](https://github.com/mikeskaug/OpenTrailMap) | Offline maps and overland apps | 🟢 / 🔴 GPL-3 + NC-ND artwork / 🟢 / 🟢 | U |
| [Navit](https://github.com/navit-gps/navit) | Navigation | 🔴✗ **GPL-2-only** | avoid |

## 10. Home Assistant / MQTT integration

| Project | What | Licence | Rel |
|---|---|---|---|
| [Home Assistant core](https://github.com/home-assistant/core) | MQTT discovery conventions; Traccar integrations | 🟢 Apache | I |
| [ESPHome](https://github.com/esphome/esphome) | Config-driven ESP firmware | Mixed (C++ MIT, Python GPL-3) | **L** (add-on modules) |
| [ovms-home-assistant](https://github.com/enoch85/ovms-home-assistant) | OVMS MQTT → HA entities | 🟢 MIT | **I**: works with us if we speak the OVMS topics |
| [ha-wican](https://github.com/jay-oswald/ha-wican) · [ha-addon-teslamate](https://github.com/lildude/ha-addon-teslamate) · [teslamate-discovery](https://github.com/nebhale/teslamate-discovery) · [leapmotor-mate](https://github.com/ProtossBlaster/leapmotor-mate) | Device → HA patterns | U | U |
| [Zigbee2MQTT](https://github.com/Koenkk/zigbee2mqtt) | Bridge architecture | 🔴✓ GPL-3 | U |
| [kia_uvo](https://github.com/Hyundai-Kia-Connect/kia_uvo) · [volkswagencarnet](https://github.com/robinostlund/homeassistant-volkswagencarnet) · [mbapi2020](https://github.com/ReneNulschDE/mbapi2020) · [renault-api](https://github.com/hacf-fr/renault-api) · [fordpass-ha](https://github.com/itchannel/fordpass-ha) · [alandtse/tesla](https://github.com/alandtse/tesla) · [tesla_ble_mqtt](https://github.com/tesla-local-control/tesla_ble_mqtt_docker) · [bimmer_connected](https://github.com/bimmerconnected/bimmer_connected) (archived) | HA car integrations, mostly cloud | 🟢 / 🔴✓ / … | U. Lesson: **cloud APIs die, so stay local-first** |

## 11. Head-unit / CAN-box emulation

| Project | What | Licence | Rel |
|---|---|---|---|
| [smartgauges/canbox](https://github.com/smartgauges/canbox) | STM32 canbox emulating Raise, Oudi and HiWorld protocols | ⚠️ | P |
| [VwRaiseCanbox](https://github.com/icarome/VwRaiseCanbox) | Raise VW protocol | 🔴✓ | P |
| [esp32-canbox-nissan](https://github.com/aerodomigue/esp32-canbox-nissan) | Nissan CAN → Toyota head-unit protocol on ESP32-C3 | 🟢 MIT | **L** |
| [GTTurboEcu](https://github.com/TheBigBadWolfClub/GTTurboEcu) | Arduino ELM327 emulator | U | P |

## 12. Car UI and dashboards

| Project | What | Licence | Rel |
|---|---|---|---|
| [OpenAuto](https://github.com/f1xpl/openauto) · [Crankshaft](https://github.com/opencardev/crankshaft) · [OpenDsh dash](https://github.com/openDsh/dash) | Pi head units and dashboards (Qt) | 🔴✓ GPL-3 | U |
| [CarVitals](https://github.com/sm0keyyy/CarVitals) | OBD+GPS dashboard PWA | U | C (the only other PWA found) |
| [react-native-vehicle-gauges](https://github.com/openvehicles/react-native-vehicle-gauges) · [ovms-client-nodejs](https://github.com/openvehicles/ovms-client-nodejs) | OVMS front-end pieces | 🟢 MIT | U |

## Best sources of vehicle data for future packs

| Source | What | Shippable? |
|---|---|---|
| OBDb (incl. SAEJ1979, Land Rover sets) | Per-model JSON signal sets | ✓ CC BY-SA, same as our data licence |
| OVMS3 vehicle modules | ~48 vehicles, mostly EVs | ✓ MIT |
| CanZE | ZOE/Twizy frames and fields CSV | ✓ GPL-3+ |
| RomRaider + definition repos | Logger parameters | App ✓; definition repos are often ⚠️ |
| Saab TuningSuites | T5/T7/T8 | ✓ Apache |
| model3dbc · Leaf CAN DB · Battery-Emulator · awesome-automotive-can-id | CAN databases | ✓ |
| Rover 14CUX/MEMS libraries · td5utils · openEAS-tool | Home turf | ✓ GPL-3 |
| JejuSoul HKMC PIDs · EVNotify · LandRoverErrorCodes | PIDs and DTCs | ⚠️ re-derive the facts; ask before copying |
| ddt4all / pyren databases · Mercedes CBF/SMR-D · dealer ODX | Dealer data | ✗ **never ship** (DMCA precedent) |

## Licence red flags

- **GPL-2.0-only (✗):**
  - Navit.
  - Treat as GPL-2.0-only until checked: jboone/tpms, aprsdroid, MegaTunix, scapy, python-OBD.
- **Non-commercial or source-available (✗):**
  - Ircama ELM327-emulator, EVNotiPi, ediabasx, VaAndCob gauge.
  - superbrobenji lap-timer (PolyForm Strict).
  - ThingsBoard ≥ v4.4 (BSL).
  - txlogger (custom licence); taskmanager-j2534 (proprietary).
- **GPL-incompatible:** OwnTracks Android (EPL-1.0). Use the protocol only.
- **GPL-3 with extra terms:** rusEFI/FOME. Read the terms before reuse.
- **No licence:** Ekaitza_Itzali, Macchina-J2534, openStar, Trionic, ArduinoOBD, canbox, Freematics, most small Land Rover repos. Facts only, or ask the author.
- **DMCA:** OpenVehicleDiag's SMR-D parser was taken down. Converted dealer databases are off-limits.
- **Avoid:** `audi-vcds/vcds-audi-diagnostic-suite`, which looks like spam or malware bait.

## Gaps nobody owns, and that suit us

1. **K-line-first open vehicle definitions:** KWP2000, ISO 9141, Td5, DS2 and KW1281, with init sequences, seed-key handling and test vectors. OBDb, opendbc and WiCAN all assume CAN.
2. **Land Rover pre-CAN body systems:** SLABS, BeCM, EAT and HEVAC for the D2 and P38. Nanocom-class tools are all closed. jlr-scanner covers D3/D4, and openEAS-tool covers only the P38 air suspension.
3. **An open ICE / K-line telematics node:** tracker, alarm, logger and diagnostics in one box. OVMS covers EVs on CAN only.
4. **An open car alarm / security module** with HA alerts and camera triggers.
5. **A PWA-first car UI** with live data, replay and maps. Everything else is Qt or Android.
6. **One log format and exporter** for MoTeC .ld, RaceChrono, VBO and RealDash, with synced audio and IMU.
7. **A documented, permissively licensed head-unit CAN-box protocol** (Raise / Hiworld / Simple-Soft).
