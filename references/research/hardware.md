---
title: "Hardware research — development kit now, own hardware later"
area: references
status: stable
version: 1.3
updated: 2026-10-06
depends_on: [references/research/ovms.md, hardware/README.md]
summary: >
  Off-the-shelf development kit (Pi 5 + CarPiHAT PRO 5, an always-on ESP32-S3 LTE/GNSS node (ADR-0032; the guardian is its hidden battery-backed variant), 10 Hz u-blox for logging, KKL K-line, WiCAN Pro, Waveshare/Autosport Labs ESP32 add-on modules) with prices and parked current; compute options compared; power, wake and buses; ready-made car products (AutoPi, Freematics, OVMS) as fallbacks; the path to our own boards (a node board with a guardian variant, a separate brain board); risks. Updated 2026-10-06 for ADR-0032/0033: one ESP32 node with an optional Pi brain, no buddy, the guardian as a hidden node variant with no outputs, KKL dev-only.
---

# Hardware research: a development kit now, our own hardware later

> **Update (2026-10-06, ADR-0032/0033):** one ESP32-S3 **node** owns the car and power
> (K-line/CAN I/O, decoding, the transmit gate, GPS, optional 4G, the parked broker, brain
> power); the Pi is the optional **brain** and never touches the car. There is no separate
> buddy: read "buddy" below as the node. The **guardian** is now a node hardware variant
> (same firmware, hidden, battery-backed, tamper and IMU, **no outputs**); its LilyGO
> T-SIM7670G-S3 + IMU breakout is the starting prototype. The KKL cable on the Pi is the
> dev path only. Alarm outputs (siren, native alarm, immobiliser) come later via a
> separate I/O / relay module, with an ADR per car-switching function. Lines that
> contradict this have been fixed; the architecture below is kept as history.

Prices are UK/US as of October 2026. **(U)** means unverified, so measure or confirm before relying on it.

## Strategy (owner, 2026-10-05)

- **Now:**
  - Build a development kit from boards and plug-in modules we can buy. No custom PCBs.
  - Pick boards that **match the eventual product**: the same ESP32-S3 family, a Pi-class Linux SoC, and the same CAN, K-line and modem chip families.
  - Prefer open, documented designs.
- **Later:** design our own board for hardware sales, once the software has settled.
- **How the software makes that switch cheap:**
  - Firmware and server code sit behind thin **hardware-abstraction layers**: power control, wake sources, K-line, CAN, modem, GNSS, IMU, I/O.
  - Changing boards then means writing new drivers, and nothing else.
- **Closed all-in-one products (AutoPi-class)** are a fallback only, not the plan.
- **The Pi Zero 2 W is ruled out**, because of availability.

> **Amended by [ADR-0028](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md) (2026-10-06):**
> the always-on ESP32 described below is now the **base "buddy"** (since ADR-0032: the node). It handles wake, the buses,
> Pi power and a small parked MQTT broker; the base has no SIM, and any USB dongle works.
> The **guardian** is an add-on: the always-on alarm and gateway, optionally with LTE
> (since ADR-0032: a node hardware variant with no outputs).
> The private CAN module bus is replaced by 10BASE-T1S, with CAN as fallback
> ([ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md)). The kit and prices below still apply.

## Architecture: "ESP32 guardian + Linux on demand"

- **The always-on part is an ESP32-S3 LTE/GNSS board (the guardian).** It runs from its own 18650 cell and owns:
  - the alarm;
  - the tracker;
  - wake decisions;
  - the 12 V watchdog;
  - power to the Pi.
- **The Linux computer is the Pi.** It runs the existing Python server and the PWA. It only powers up when:
  - the ignition is on;
  - the alarm triggers;
  - it is asked to remotely.
- **Why the Pi must be fully cut:** a Pi that has merely halted still draws about 50 mA.
- **Bus for add-on modules:** a private CAN bus. The guardian bridges it to MQTT.
- **Cameras use Wi-Fi.**

## Development kit: recommended parts (~£250 plus the Pi)

| Role | Part | £ | Notes |
|---|---|---|---|
| Linux computer | **Raspberry Pi 5, 2 GB** (£74.40), or the current Pi 4 | 0–74 | Production guaranteed to January 2038. The 1–2 GB models largely escaped the 2026 RAM price rises. A halted Pi 5 draws about 0.01 W (`POWER_OFF_ON_HALT`). |
| Car power for the Pi | **[CarPiHAT PRO 5](https://thepihut.com/products/carpihat-pro-5-car-interface-dac-for-raspberry-pi-5)** | 110 | 12 V → 5 V at 5 A; ignition sense with a safe-shutdown latch; draws <1 mA when off; RTC; 1× CAN (SocketCAN); opto-isolated inputs; 2× 12 V high-side outputs |
| Always-on guardian | **[LilyGO T-SIM7670G-S3](https://wiki.lilygo.cc/products/t-sim-series/t-sim7670g-s3/)** on its own 18650 (alternative: Waveshare ESP32-S3-SIM7670G, ~$49) | 28–40 | ESP32-S3; Cat-1 LTE (best UK coverage) and GNSS; 147 µA in deep sleep. It charges only while the ignition is on, so it takes about nothing from the car while parked. |
| GPS for tracking and alarm | The guardian's **built-in SIM7670G GNSS**, plus an external active antenna | 8 | About 1 Hz, which is enough for check-ins, geofences and theft tracking. It passes its last fix to the Pi at boot, so the Pi knows where it is straight away. |
| GPS for drive logging | **A dedicated u-blox at 10 Hz**: keep the current USB GPS, or use a **[SparkFun MAX-M10S Qwiic](https://www.sparkfun.com/sparkfun-gnss-receiver-breakout-max-m10s-qwiic.html)**, plus an antenna | 0–55 | The logger needs 10 Hz (map, speed traces, G-G). The modem's GNSS is about 1 Hz and may have to share time with LTE (U). |
| Wake and alarm inputs | PC817 4-channel opto board (screw terminals) and **[Adafruit LSM6DSOX](https://adafruit.com/product/4438)** (STEMMA, plus one jumper wire for the interrupt pin) | 15 | Ignition, OEM alarm/siren and doors; wake on motion |
| Guardian → Pi link | One GPIO driving a CarPiHAT input through an opto/relay board, plus a UART link | 5 | Check the CarPiHAT's power-on logic first (U). Fallback: **[Witty Pi 5 HAT+](https://thepihut.com/products/witty-pi-5-hat-real-time-clock-and-power-management-for-raspberry-pi)**. |
| K-line (Td5) | **Keep the KKL USB cable** on the Pi for development only; production K-line runs on the node (ADR-0032) | 0 | Proven |
| OBD front end for later cars and always-on K-line | **[MeatPi WiCAN Pro](https://www.crowdsupply.com/meatpi-electronics/wican-pro)** ($89; backordered until about December 2026) and an OBD Y-splitter (£17) | 85 | Fallback: [SparkFun OBD-II UART](https://www.sparkfun.com/sparkfun-obd-ii-uart.html) (STN1110, £53.50). It might pass the Td5 seed-key exchange, but its timing is unknown, so bench-test it first (U). |
| Add-on: I/O / relay module (later; ADR per car-switching function) | **[Waveshare ESP32-S3-ETH-8DI-8RO-C](https://thepihut.com/products/8-channel-esp32-s3-wi-fi-relay-module-with-can-interface)** | 43 | 7–36 V input; DIN rail; isolated CAN; 8 isolated inputs (5–36 V); 8 × 10 A relays; RTC. A more compact alternative is the [M5Stack StamPLC](https://docs.m5stack.com/en/products/sku/K141) (15 mA standby). |
| Add-on: CAN bridge / emulator | **[Autosport Labs ESP32-CAN-X2](https://wiki.autosportlabs.com/ESP32-CAN-X2)** ($54.95, in stock) | 42 | 2× CAN; automotive 6–20 V input; JST pigtails |
| Camera (later) | **[M5 Timer Camera X](https://thepihut.com/collections/new-products-maker/products/timer-camera-x-ov3660-esp32-psram)** (2 µA sleep, own battery), XIAO ESP32-S3 Sense, or Pi Camera 3 | 13–35 | Over Wi-Fi to go2rtc on the Pi |
| Mobile data | **1NCE** IoT SIM (about £11 for 10 years and 500 MB) | 11 | Enough for MQTT telemetry. Use giffgaff data-only if video is ever needed. 3G is switched off in the UK. |

**Parked current draw:**

| Part | Draw from the car battery |
|---|---|
| Guardian | About 0 (it runs from its 18650) |
| CarPiHAT | Under 1 mA |
| WiCAN Pro, if fitted | About 1–3 mA |
| **Total** | **About 1–4 mA** |

The usual parasitic allowance is 20–50 mA. 40 Ah at 4 mA is more than a year (U).

## Ready-made boards considered

| Board | Has | Sleep | Price | Role |
|---|---|---|---|---|
| WiCAN Pro | ESP32-S3; CAN + ISO 9141/14230 (fast/slow init) + J1850; IMU; RTC; microSD; MQTT/HA; GPL-3 firmware | 2.8 mA (claims <1 mA) | $89 | OBD front end; could run our K-line core |
| Freematics ONE+ B/H | ESP32 + OBD co-processor; KWP2000; SIM7670 + u-blox M9; IMU | About 10 mA | $135 / $175 | All-in-one alternative with no battery. Custom KWP headers (U). |
| OVMS v3.3 | 3× CAN; SIM7600; K-line board £25 | About 8–9 mA | £235 | Reference and interop rig ([ovms.md](ovms.md)) |
| Macchina M2 / A0 | M2: SAM3X with 2× K-line/LIN; A0: ESP32 CAN | U | $99 / $90 | Ready K-line platform, but not ESP32 |
| LilyGO T-SIM7080G-S3 | Cat-M/NB-IoT + GNSS, PMU | 128–250 µA | ~$35 | Lowest drain, but UK Cat-M coverage is patchy |
| LilyGO T-2CAN / T-CAN485 | ESP32-S3 2× isolated CAN, 12–24 V in / ESP32 CAN | U | $33 / $12 | Cheap CAN modules |
| M5 Unit CAN / CatM+GNSS / AtomS3 | Grove plug-ins | — | £12 / £45 / £9 | Plug-in CAN and LTE |
| Waveshare ESP32-S3-RS485-CAN | 7–36 V DIN | U | ~$29 | DIN CAN node |
| Kincony KC868 | ESP32-S3 I/O; **no CAN** | U | $50–80 | ESPHome I/O only |

## Ready-made car Pi / Linux + MCU products considered

| Product | Notes | Verdict |
|---|---|---|
| [AutoPi CAN-FD Pro](https://www.autopi.io/static/pdf/autopi_CAN_FD_Pro_datasheet.pdf) / TMU CM4 | CM4; LTE Cat-4; GPS; IMU; 2× CAN-FD; 12–35 V; 6 mA deep sleep / 35 mA sleep; €599 / €235+; autopi-core is Apache-licensed | Fallback "working box". It's a closed design; motion-wake is undocumented. |
| CarPiHAT PRO 5 | See the kit above | **Chosen** |
| Witty Pi 5 HAT+ | RP2350 power manager with open firmware; 6–30 V; RTC; 0.8–8 mA; £40.80 | Cheapest Pi power option, and the fallback |
| Sfera Strato Pi Max / CAN | CM4/CM5 + RP2040 power and boot control; up to 4× CAN; from €435 | Industrial DIN form, too big |
| PiCAN3 / PiCAN-FD (+SMPS), Waveshare 2-CH CAN FD HAT | CAN HATs | Extra CAN channels if needed |
| Arduino UNO Q | Qualcomm Linux + STM32U585; £57; 0.5 W idle; **can't power off its Linux side** | No |
| Portenta X8 + Max Carrier | i.MX8MM + STM32H7; CAN; Cat-M; ~€340 + module | Too expensive |
| Radxa X4 / LattePanda | N100/N150 + RP2040; 5–15 W idle | No |
| **NXP FRDM-IMX93** | 2× A55 + Cortex-M33 on one chip. While Linux is suspended the M33 watches CAN at ~122–132 mW at chip level ([AN13917](https://www.nxp.com/docs/en/application-note/AN13917.pdf)). ~$74 | **Candidate SoC for our own board** |
| STM32MP157 (Seeed Odyssey £55) | A7 + M4 | Same idea, older |
| BeagleY-AI, Milk-V Duo | Separate MCU domains, but immature software | No |

**Raspberry Pi availability (2026):**
- **Supply is fine; prices have risen.** Memory costs pushed up December 2025, February 2026 and April 2026 prices.
- **Pi Hut prices today:**

  | Model | Price |
  |---|---|
  | Pi 5 1 GB | £43.20 |
  | Pi 5 2 GB | £74.40 |
  | Pi 5 4 GB | £105.60 |
  | CM5 | from £64.80 |

- **Production guaranteed until:**

  | Model | Until |
  |---|---|
  | Pi 5 | January 2038 |
  | CM5 | January 2036 |
  | CM4 | January 2034 |

## Power, wake and buses (detail)

**Switching the Pi**
- The guardian controls the CarPiHAT (or Witty Pi), or alternatively the EN pin of a [Pololu D36V50F5](https://www.pololu.com/product/4091) buck regulator.
- Shutdown handshake:
  1. The Pi asserts `gpio-shutdown` and halts.
  2. The Pi asserts `gpio-poweroff` when it is down.
  3. The power is cut, with a 60 s hard timeout.

**Wake sources** (all off-the-shelf)

| Source | How |
|---|---|
| Ignition | PC817 opto input |
| OEM alarm / siren | PC817 opto input |
| Motion | LSM6DSOX/LIS3DH wake interrupt |
| CAN activity | SN65HVD230 in standby: its RXD pin toggles on bus traffic. Check that Rs is accessible. |
| LTE | Modem RI pin |
| Timer | RTC timer for GNSS check-ins |
| Engine running | 12 V ADC: alternator charging shows above 13.2 V (as OVMS does it) |

**Low-voltage cutoff in firmware**
- No Pi below about 12.0 V.
- Heartbeat only below about 11.8 V.
- OVMS-style staged power-down.
- Generic low-voltage-disconnect relay boards draw up to 10 mA themselves, so use them only as a backstop.

**Pi robustness**
- Read-only overlayfs root.
- Logs on a separate partition or USB drive.
- Optional supercap UPS HAT.

**Buses**

| Bus | Plan |
|---|---|
| K-line | On the node (ESP32-S3 with a K-line transceiver) in production; KKL on the Pi for development only. Other ESP32-side options: WiCAN Pro or the STN1110 board. L9637D breakouts aren't really sold (the chip is obsolete). |
| CAN on the Pi | CarPiHAT, or a Waveshare 2-CH CAN FD HAT |
| CAN on the ESP32 | TWAI + SN65HVD230 (~£3) or an M5 Unit CAN |
| Add-on bus | Private CAN at 250/500 kbit/s. 11-bit ID = 4-bit class + 7-bit node. Heartbeat / command / state messages, ISO-TP for config and OTA. Never share wires with vehicle CAN. |

## Path to our own hardware

> **Module bus decided (2026-10-06):** our own modules talk over 10BASE-T1S, not CAN alone; see
> [ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md) and the
> [T1S research](t1s_module_bus.md). CAN stays for µA-wake nodes.
>
> **Ecosystem network decided (2026-10-06):** every Ostler device speaks IP on an
> automotive-Ethernet backbone (T1S for modules, standard Ethernet or PoE for cameras, Wi-Fi/USB
> for displays, the Pi routing between them). The private-CAN "Add-on bus" row above is now the
> dev-kit and µA-wake fallback only. See
> [ADR-0027](../../decisions/adr-0027-ip-everywhere-ecosystem-architecture.md) and the
> [ecosystem research](ecosystem_architecture.md).

- **A node board** (ADR-0032) combining:
  - ESP32-S3 with PSRAM;
  - TJA1051 CAN;
  - an L9637-class K-line transceiver;
  - an ignition/opto front end and brain power switching;
  - GNSS and an optional SIM7670-class 4G modem.
- **A guardian variant** of the node board: backup 18650/LiFePO4 cell with a thermistor
  charger, IMU, tamper sensing, better antennas; no outputs.
- **A separate brain board:** CM5 (or i.MX93), a LAN8651 for T1S, the camera Ethernet port.
- **Firmware and drivers carry over** thanks to the hardware-abstraction-layer contract.

## Risks

| Risk | Mitigation |
|---|---|
| Cabin heat (60–80 °C) and Li-ion cells | Mount under a seat; use a cell rated to 60 °C; stop charging above 45 °C |
| SD card corruption | overlayfs and a clean shutdown handshake |
| Load dump, reverse polarity | 50 V-rated parts, a TVS diode (SMBJ24A), fuses |
| RF and EMC | Separate antennas, external GNSS antenna, twisted-pair CAN, ferrites |
| Battery-drain bugs | Firmware low-voltage cutoff, staged power-down, hard timeouts |
| Vehicle bus | Listen-only by default; our module bus is physically separate |
| UK insurance and law | A DIY alarm is not Thatcham-rated, so position it alongside the OEM alarm, not as a replacement; any outputs (siren, immobiliser) come only through a later I/O / relay module with its own ADR (ADR-0033). Declare any immobiliser. Sirens must stop within 5 minutes. Tracking other drivers raises GDPR consent issues. |
| Td5 | No CAN diagnostics; K-line with seed-key on the node (a C keygen plugin; the Python version stays the lab reference), KKL on the Pi for development |
