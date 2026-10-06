---
title: "Hardware research — development kit now, own hardware later"
area: references
status: stable
version: 1.5
updated: 2026-10-06
depends_on: [references/research/ovms.md, hardware/README.md]
summary: >
  Off-the-shelf development kit (Pi 5 + CarPiHAT PRO 5, an always-on ESP32-S3 LTE/GNSS node (ADR-0032; the guardian is its hidden battery-backed variant), 10 Hz u-blox for logging, KKL K-line, WiCAN Pro (a CAN-only board profile, ADR-0039), Waveshare/Autosport Labs ESP32 add-on modules) with prices and parked current; compute options compared; power, wake and buses; ready-made car products (AutoPi, Freematics, OVMS) as fallbacks; the path to our own boards (a node board with a guardian variant, a separate brain board); risks. Updated 2026-10-06 for ADR-0032/0033: one ESP32 node with an optional Pi brain, no buddy, the guardian as a hidden node variant with no outputs, KKL dev-only. v1.4 adds the GPS split (owner, 2026-10-06): the guardian's built-in SIM7670G GNSS at 1 Hz (fixed; GPS/GLONASS/Galileo/BeiDou) with a hidden active antenna for security, and a 10 Hz u-blox (MAX-M10S or NEO-M9N) on the diagnostic node for drive logging, with prices, antennas and the merge recommendation. v1.5 (ADR-0039, ADR-0040): the WiCAN Pro is a CAN-only board profile (K-line behind an interpreter IC); the u-blox placement on the diagnostic node is decided; the parked-current table gains the Diagnostics node (parked-ready ≤ 5 mA, parked-deep ≤ 0.5 mA) against a 10 mA budget.
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
| GPS for tracking and alarm | The guardian's **built-in SIM7670G GNSS**, plus an external active antenna | 8 | 1 Hz only (fixed), which is enough for check-ins, geofences and theft tracking ([GPS split](#gps-split-two-receivers-two-jobs-2026-10-06)). It passes its last fix to the Pi at boot, so the Pi knows where it is straight away. |
| GPS for drive logging | **A dedicated u-blox at 10 Hz**: keep the current USB GPS, or use a **[SparkFun MAX-M10S Qwiic](https://www.sparkfun.com/sparkfun-gnss-receiver-breakout-max-m10s-qwiic.html)**, plus an antenna | 0–55 | The logger needs 10 Hz (map, speed traces, G-G). The modem's GNSS is 1 Hz only. Production: on the diagnostic node ([GPS split](#gps-split-two-receivers-two-jobs-2026-10-06)). |
| Wake and alarm inputs | PC817 4-channel opto board (screw terminals) and **[Adafruit LSM6DSOX](https://adafruit.com/product/4438)** (STEMMA, plus one jumper wire for the interrupt pin) | 15 | Ignition, OEM alarm/siren and doors; wake on motion |
| Guardian → Pi link | One GPIO driving a CarPiHAT input through an opto/relay board, plus a UART link | 5 | Check the CarPiHAT's power-on logic first (U). Fallback: **[Witty Pi 5 HAT+](https://thepihut.com/products/witty-pi-5-hat-real-time-clock-and-power-management-for-raspberry-pi)**. |
| K-line (Td5) | **Keep the KKL USB cable** on the Pi for development only; production K-line runs on the node (ADR-0032) | 0 | Proven |
| OBD front end for later CAN cars (a **CAN-only board profile**: its K-line goes through an interpreter IC, so not for gated K-line or the raw tap; ADR-0039 §2) | **[MeatPi WiCAN Pro](https://www.crowdsupply.com/meatpi-electronics/wican-pro)** ($89; backordered until about December 2026) and an OBD Y-splitter (£17) | 85 | Fallback: [SparkFun OBD-II UART](https://www.sparkfun.com/sparkfun-obd-ii-uart.html) (STN1110, £53.50). It might pass the Td5 seed-key exchange, but its timing is unknown, so bench-test it first (U). |
| Add-on: I/O / relay module (later; ADR per car-switching function) | **[Waveshare ESP32-S3-ETH-8DI-8RO-C](https://thepihut.com/products/8-channel-esp32-s3-wi-fi-relay-module-with-can-interface)** | 43 | 7–36 V input; DIN rail; isolated CAN; 8 isolated inputs (5–36 V); 8 × 10 A relays; RTC. A more compact alternative is the [M5Stack StamPLC](https://docs.m5stack.com/en/products/sku/K141) (15 mA standby). |
| Add-on: CAN bridge / emulator | **[Autosport Labs ESP32-CAN-X2](https://wiki.autosportlabs.com/ESP32-CAN-X2)** ($54.95, in stock) | 42 | 2× CAN; automotive 6–20 V input; JST pigtails |
| Camera (later) | **[M5 Timer Camera X](https://thepihut.com/collections/new-products-maker/products/timer-camera-x-ov3660-esp32-psram)** (2 µA sleep, own battery), XIAO ESP32-S3 Sense, or Pi Camera 3 | 13–35 | Over Wi-Fi to go2rtc on the Pi |
| Mobile data | **1NCE** IoT SIM (about £11 for 10 years and 500 MB) | 11 | Enough for MQTT telemetry. Use giffgaff data-only if video is ever needed. 3G is switched off in the UK. |

**Parked current draw:**

| Part | Draw from the car battery |
|---|---|
| Guardian | About 0 (it runs from its 18650) |
| Diagnostics node (ADR-0040 §2; bench targets) | Parked-ready ≤ 5 mA (first 72 h); parked-deep ≤ 0.5 mA |
| CarPiHAT (hub's power board; the hub itself is cut) | Under 1 mA |
| WiCAN Pro, if fitted | About 1–3 mA |
| **Total** | **About 1.5–9 mA** (budget: ≤ 10 mA average including wakes, ADR-0040 §4.4) |

The usual parasitic allowance is 20–50 mA. 40 Ah at 4 mA is more than a year (U); at the
10 mA budget it is about five and a half months (U).

## GPS split: two receivers, two jobs (2026-10-06)

Owner direction (item 2, 2026-10-06): the **guardian's built-in GNSS** does security
tracking at about 1 Hz and saves battery while parked; a **10 Hz u-blox** does drive
logging, replay, Drive mode and the speed-vs-wheel-speed check. Merging picks the best fix:
the u-blox while driving, the guardian when parked or when the node is gone. Positions carry
source tags and shared time. The merge rules are in
[ADR-0032's Amendments](../../decisions/adr-0032-one-node-optional-brain.md#amendments-2026-10-06-gps-split-and-sensor-detection)
(accepted 2026-10-06; u-blox placement pending);
sensor detection is in [node sensors](node_sensors.md). Checked live on 2026-10-06.

### The guardian's receiver today (LilyGO T-SIM7670G-S3)

| Item | Finding |
|---|---|
| Update rate | **1 Hz only.** The SIM767XX AT manual's NMEA-rate command accepts a single value, 1 Hz |
| Constellations | GPS, GLONASS, Galileo, BeiDou, selectable (default all four); L1 band only |
| Accuracy, TTFF, GNSS current | **Not published:** SIMCom's SIM7672X hardware design v1.01 leaves its GNSS performance table empty, and LilyGO lists modem power as "TBD". Typical L1 modem GNSS is a few metres CEP open-sky, hot start in seconds and cold start around 30 s (U); measure |
| Antenna | IPEX socket; LilyGO requires an **active antenna** fed at 3.3 V (most take 2.5–5.5 V); antenna power is switched by the modem's GPIO1, so it can be off while parked |
| Timing | The Standard edition routes the modem's GNSS NMEA port and **PPS (GPIO17)** to the ESP32-S3, so the guardian can discipline its clock |
| Board editions | Two are sold: the original (H707, listed with 8 MB PSRAM, about $36) and the Standard (H802, about €52 in the EU; README says ESP32-S3-WROOM-1 with **2 MB quad PSRAM** and only GPIO2/3 free for I²C unless the camera pins are reused) (U: confirm which edition arrives) |
| Battery | Single-cell 4.2 V Li-ion/LiPo only; **LiFePO4 is explicitly not supported** by the on-board charger |
| Deep sleep | 147 µA (earlier listing, used in the kit table) vs 497 µA average (a 2026 reseller listing) (U: measure) |

Verdict: fine for check-ins, geofences and theft tracking. It cannot do 10 Hz logging, and
its accuracy is unknown until we measure it.

**Newer LilyGO boards.** The T-SIM/T-A Standard series (A7670E/G/SA, SIM7000G, SIM7080G,
SIM7600G, SIM7670G) all use the modem's own GNSS; none adds a u-blox (checked 2026-10-06).
The **T-Beam Supreme** (ESP32-S3, 8 MB PSRAM, QMI8658 IMU, SX1262 LoRa, about $60) ships
with an L76K or a **u-blox MAX-M10S**, but has no LTE: interesting for the off-grid / mesh
work and the bike product, not as the guardian. The Freematics ONE+ (SIM7670 + u-blox M9)
shows the "modem GNSS plus u-blox" pairing in one product. The guardian can also take a
u-blox on its QWIIC I²C connector if a single-box product ever needs 10 Hz.

### u-blox options for 10 Hz

| Module | Max rate | Notes | Board and price (2026-10-06) |
|---|---|---|---|
| **MAX-M10S** | 10 Hz with 3 constellations (5 Hz with all 4); 18 Hz single constellation, raised to 25 Hz by later M10 firmware (U) | About 25 mW tracking; external antenna; I²C 0x42 and UART | SparkFun Qwiic breakout, £44.20 at The Pi Hut (sold out on the day) |
| **NEO-M10S** | As MAX-M10S (same M10 engine) (U) | NEO footprint, drop-in for older NEO-M8 boards | Breakouts from smaller makers (U) |
| **SAM-M10Q** | 5 Hz with 4 constellations; up to 18 Hz single | Built-in patch antenna: no cable, but must sit under the windscreen or roof plastic | SparkFun breakout, £49.50 at The Pi Hut (sold out) |
| **NEO-M9N** | **25 Hz with 4 constellations** | About 31 mA tracking; the strongest pure-GNSS choice for logging | SparkFun SMA Qwiic breakout, $76.50 |
| **NEO-M9V** (option) | Up to 50 Hz | Untethered and automotive dead reckoning (built-in IMU; wheel-tick input); keeps a position in tunnels and multi-storey car parks | gnss.store module, €77.99 |
| **ZED-F9R** (option) | Multi-band RTK + dead reckoning | Centimetre class with corrections; the "GNSS/RTK later" add-on | About $470 as a Qwiic board |

**Recommendation:** the **MAX-M10S** (or the NEO-M9N for 25 Hz headroom) at 10 Hz with
GPS + Galileo + GLONASS, sending UBX-NAV-PVT (one message per epoch carries position,
velocity, accuracy estimates, fix type and UTC time). The NEO-M9V is the upgrade if the
owner wants positions to survive tunnels and wheel-speed fusion done inside the receiver.

### Antennas

| Use | Antenna | Price | Notes |
|---|---|---|---|
| Guardian (hidden) | Small adhesive active patch on a short lead, under the dash top, A-pillar trim or roof lining; never under metal | £8–15 (U) | 3.3 V active, IPEX/U.FL; its LNA is switched off parked |
| u-blox on the node | Active magnetic or adhesive puck, e.g. Taoglas AA.162 (GPS/GLONASS/Galileo, 3 m RG-174, SMA) | about £14–24 | On the dash top or the windscreen edge; check the D2's windscreen has no metallic coating (U) |
| Precision later | u-blox ANN-MB-00 multi-band (L1/L2) | about $35–65 | For the ZED-F9R / RTK add-on only |

Keep **two separate antennas**. A splitter would save one, but then pulling the node's
antenna lead would also blind the guardian, which defeats the point of a hidden tracker.

### Where the u-blox goes: node or brain

**Decided: on the diagnostic node** ([ADR-0039](../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md) §9; recommended here first) (UART with PPS to a node GPIO, or I²C on a dev
kit), with the brain receiving fixes over MQTT like every other reading.
- **Ostler Diagnostics works alone.** Ostler Diagnostics has no hub; the node records
  sessions itself (ADR-0032 §12), so 10 Hz logging and Drive mode on it alone need the
  receiver on the node.
- **The gate needs speed.** The driving state falls back to GPS speed, and the node gate
  re-checks it at execution (UI spec §3.5, ADR-0033 §3). During a SLABS session the Td5 speed
  is absent, so the gate's own receiver should be the fast one.
- **Time.** A u-blox time pulse on the node makes the node the best clock in the car, with
  or without a brain.
- **Load is small:** UBX-NAV-PVT is about 100 bytes, so 10 Hz is about 1 KB/s on a UART.
- **Against:** the Pi already reads a USB u-blox today (ADR-0009, pyserial NMEA). That stays
  as the **dev path**; a USB receiver on the brain remains a supported option for a node
  without spare pins.
- **When the guardian replaces the node** (ADR-0032 §5), the guardian is the only device, so
  it carries the u-blox too, on its QWIIC I²C port.

### Merge in brief

- Each fix carries its **source tag** (device, receiver), fix type, horizontal and speed
  accuracy, satellites used, GNSS time of fix and receive time on the shared clock.
- **Driving or ignition on:** the u-blox when its fix is valid and fresh; otherwise the
  guardian. **Parked:** the guardian; the u-blox is powered down. **Node gone** (offline
  will, heartbeat lost): the guardian, and a node-loss alert if armed.
- Hysteresis stops flapping; both raw streams are always logged, and the merged stream names
  the source it picked. Disagreement between the two beyond their stated accuracy is flagged
  (a possible fault, jamming or spoofing).
- Bus wheel speed vs GNSS speed (u-blox only, 10 Hz, steady straight segments) gives a
  speedometer or tyre-size error.

Sources: [SIM767XX AT manual v1.01](https://files.waveshare.com/wiki/SIM7670G-LTE-Cat-1-GNSS-HAT/SIM767XX_Series_AT_Command_Manual_V1.01.pdf),
[SIM7672X hardware design v1.01](https://files.waveshare.com/wiki/ESP32-S3-SIM7670G-4G/SIM7672X_Series_Hardware_Design_V1.01.pdf),
[LilyGO T-SIM7670G-S3 Standard README](https://github.com/Xinyuan-LILYGO/LilyGo-Modem-Series/blob/main/docs/en/esp32s3/sim7670g-s3-standard/README.MD),
[LilyGO product page](https://lilygo.cc/products/t-sim-7670g-s3),
[OpenELAB Standard series listing](https://openelab.io/products/lilygo-t-sim-t-a-standard-series-with-gps),
[T-Beam Supreme (Rokland)](https://store.rokland.com/collections/lilygo-boards/products/lilygo-t-beam-supreme-esp32-s3-lora-development-board-sx1262-915mhz-gps-l76k-or-u-blox),
[MAX-M10S datasheet](https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf),
[u-blox M10 rate PCN](https://shop.richardsonrfpd.com/docs/rfpd/u-blox_PCN_UBX-23006557.pdf),
[SparkFun MAX-M10S at The Pi Hut](https://thepihut.com/products/sparkfun-gnss-receiver-breakout-max-m10s-qwiic),
[SparkFun SAM-M10Q at The Pi Hut](https://thepihut.com/products/sparkfun-gps-breakout-chip-antenna-sam-m10q),
[SparkFun NEO-M9N SMA](https://www.sparkfun.com/sparkfun-gps-breakout-neo-m9n-sma-qwiic.html),
[NEO-M9V module (gnss.store)](https://gnss.store/products/elt0303),
[Taoglas AA.162](https://www.mouser.co.za/new/taoglas/taoglas-aa-162-antenna),
[ANN-MB-00 (Future Electronics)](https://futureelectronics.com/p/semiconductors--wireless-rf--antennas--gps-antennas/ann-mb-00-u-blox-6120194).

## Ready-made boards considered

| Board | Has | Sleep | Price | Role |
|---|---|---|---|---|
| WiCAN Pro | ESP32-S3; CAN + ISO 9141/14230 (fast/slow init) + J1850; IMU; RTC; microSD; MQTT/HA; GPL-3 firmware | 2.8 mA (claims <1 mA) | $89 | CAN-only board profile (ADR-0039 §2): K-line only through its interpreter IC, so generic K-line OBD reads at most, never our gated K-line core |
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
| K-line | On the node (ESP32-S3 with a K-line transceiver) in production; KKL on the Pi for development only. Not on the WiCAN Pro (CAN-only profile; its K-line sits behind an interpreter IC, ADR-0039 §2) or the STN1110 board, except for generic K-line OBD reads. L9637D breakouts aren't really sold (the chip is obsolete). |
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
