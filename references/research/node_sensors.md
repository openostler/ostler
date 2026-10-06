---
title: "Node sensors — detection, budgets, timing, parked current and placement"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, references/research/hardware.md, references/research/addons_catalogue.md]
summary: >
  Research for the owner's item 3 (2026-10-06): one node firmware whose capability manifest comes from the hardware. Auto-detect what can be detected (I²C chips by address plus ID register, u-blox by UBX poll, declared SPI parts by plausibility), declare what cannot (tacho pulses, analog senders, taps, outputs) in a node config file or a harness ID resistor, and merge both into one manifest. Holds a live-checked chip ID table with address collisions and heuristics (MAX31855 has no ID), ESP32-S3 budgets (45 GPIOs, ADC2 unusable with Wi-Fi, 4 PCNT units, 4+4 RMT channels, 2 MCPWM with capture, 3 UARTs, octal-PSRAM parts rated to 65 °C), fast tacho vs K-line timing across both cores, memory headroom, a parked-current table per sensor, placement (hidden guardian, diag-port node, engine bay) and driver libraries with licences under ADR-0025.
---

# Node sensors: detection, budgets, timing, parked current and placement

Research for the owner's item 3 of 2026-10-06: **one firmware, manifest from hardware.** It
backs the proposed amendment at the end of
[ADR-0032](../../decisions/adr-0032-one-node-optional-brain.md#proposed-amendment-2026-10-06-pending-owner-answers)
and the draft firmware spec for sensor detection (to live in `ostler-firmware` as
`docs/specs/sensor-detection.md`, ADR-0034). GPS receivers are covered in
[hardware research §GPS split](hardware.md#gps-split-two-receivers-two-jobs-2026-10-06).
Facts were checked live on **2026-10-06**; **(U)** means unverified, so measure or confirm
before relying on it.

## 1. The model in one paragraph

Every node (diagnostic-port node, guardian variant, sensor node) runs the same firmware.
At boot it learns its **board** (compiled-in board profile: pin map, on-board chips, whether
outputs are allowed), reads an optional **harness ID resistor**, loads an optional **node
config file**, then **probes** the buses the board and config name. Detected items and
declared items are merged into **one capability manifest** (ADR-0032 §6, UI spec §5), with
each item marked `detected`, `declared` or `board`, and a status (`ok`, `absent`, `fault`,
`no_signal`). Readings carry source tags (ADR-0032 §13). Sensors are Read, Tier 0; any
output declares its category and tier (ADR-0033 §1) and only exists on a board whose profile
allows outputs, never on the guardian.

## 2. What can and cannot be detected

| Kind | Detectable? | How |
|---|---|---|
| I²C chips with an ID register (IMUs, pressure, thermocouple amps like MCP9600, power monitors) | **Yes** | ACK at a known address, then read the ID register; only then configure |
| I²C chips without an ID (ADS1115, DS3231, SHT4x) | **Weakly** | ACK plus reset-default register values; treat as "probable" unless declared |
| u-blox GNSS on I²C (0x42) or UART | **Yes** | I²C: bytes-available registers 0xFD/0xFE answer; UART: NMEA/UBX seen at a known baud; then poll UBX-MON-VER for the model and firmware |
| SPI chips (MAX31855, MAX31856, MAX6675) | **Only when declared** | SPI has no addresses, so firmware never toggles an undeclared chip select. A declared part is then checked for plausibility (§3.2) |
| Tacho pulses (crank, cam, coil, injector), speed pulses | **No** | Declared: pin, conditioner type, wheel pattern. Status becomes `ok` once plausible pulses arrive |
| Analog senders (oil pressure, temperature, fuel) | **No** | Declared: pin (ADC1 only), divider, curve |
| Read-only taps (lamp, switch, door lines) | **No** | Declared: pin, opto or high-impedance input, active level |
| Relay or switched outputs | **No, and never probed** | Declared on an I/O board only, with category and tier; each car-switching function needs its own ADR first |

## 3. Chip ID table (live-checked 2026-10-06)

### 3.1 I²C

| Chip | Type | 7-bit address | ID register → value | Collides with | Notes |
|---|---|---|---|---|---|
| BMI270 | 6-axis IMU | 0x68 / 0x69 | 0x00 → **0x24** | ICM-42688-P, MPU-6050, DS3231 (0x68) | Needs a config blob upload after reset (Bosch API does it) |
| ICM-42688-P | 6-axis IMU | 0x68 / 0x69 | 0x75 → **0x47** | BMI270, MPU-6050, DS3231 | Register bank 0 must be selected (reset default) |
| MPU-6050 (legacy) | 6-axis IMU | 0x68 / 0x69 | 0x75 → 0x68 | as above | Recognised only to report "unsupported" |
| LSM6DSO / LSM6DSOX | 6-axis IMU | 0x6A / 0x6B | 0x0F → **0x6C** | QMI8658 (0x6A/0x6B) | Same ID for DSO and DSOX (U); treat as one driver |
| QMI8658 | 6-axis IMU | 0x6A / 0x6B | 0x00 → **0x05** | LSM6DSO | On LilyGO T-Beam Supreme |
| LIS3DH | accelerometer | 0x18 / 0x19 | 0x0F → 0x33 | — | Cheap wake-on-motion option |
| BMP390 | pressure | 0x76 / 0x77 | 0x00 → **0x60** | BME280 (same value, other register) | BMP388 reads 0x50 at 0x00 |
| BME280 | pressure, humidity | 0x76 / 0x77 | 0xD0 → **0x60** | BMP390 | BMP280 reads 0x58, BME680 0x61 (U) at 0xD0 |
| MCP9600 / MCP9601 | thermocouple amp | 0x60–0x67 | 0x20 → **0x40** / 0x41 | — | An I²C alternative to the MAX31855 for EGT |
| INA226 | current, voltage | 0x40–0x4F | 0xFE → 0x5449, 0xFF → 0x2260 (U) | other 0x40 parts | For 12 V and parked-current self-measurement |
| ADS1115 | 16-bit ADC | 0x48–0x4B | none | — | Config register resets to 0x8583 (U); "probable" only |
| u-blox M8/M9/M10 | GNSS | 0x42 | 0xFD/0xFE (bytes waiting) | — | Confirm with UBX-MON-VER; then UBX-NAV-PVT at 10 Hz |

**Rule for collisions:** probe in a fixed order per address, reading only ID registers
(reads never change state on these parts), and accept the first match. 0x68 is tried as
BMI270 (0x00), then ICM-42688 (0x75); 0x6A/0x6B as LSM6DSO (0x0F), then QMI8658 (0x00);
0x76/0x77 as BMP390 (0x00), then the BME/BMP 0xD0 family. An ACK with no ID match is
reported as `unknown_i2c@0xNN`, never guessed. The DS3231 RTC at 0x68 has no ID register,
so a board profile that carries one marks 0x68 as taken.

### 3.2 SPI thermocouple amplifiers (declared only)

- **MAX31855** has no ID and is read-only: one 32-bit frame. Plausibility checks on a
  declared chip select: the frame is neither all zeros nor all ones (a pull-up on MISO makes
  "absent" read as all ones); the two reserved bits (D17 and D3) are zero; the cold-junction
  temperature (D15–D4) is within −40…+125 °C and within about 15 °C of the board's own
  temperature sensor (U); fault bits (D2–D0) map to `fault` (open, short to GND, short to
  VCC), which still proves the chip is there. Three good frames in a row set `ok`.
- **MAX6675** (older, 16-bit) is told apart by frame length and its always-zero device-ID
  bit (D1) (U).
- **MAX31856** has readable registers with known reset defaults, so a declared one can be
  confirmed by reading them (U).

### 3.3 UART devices

- **u-blox on UART:** listen at the configured baud (then 9600, 38400, 115200) for a valid
  NMEA checksum or UBX sync bytes (0xB5 0x62), then poll UBX-MON-VER. Configure with
  UBX-CFG-VALSET (M9/M10 configuration keys).
- **Wideband AFR controllers** speak their own serial protocols; declared only, with the
  protocol named in the config (U per controller).
- **The SIM7670G GNSS** is reached through modem AT commands and its NMEA port, known from
  the board profile.

## 4. ESP32-S3 budgets

From the ESP32-S3 datasheet v2.2 and ESP-IDF stable docs (checked 2026-10-06).

| Resource | ESP32-S3 has | Node use (diagnostic-port node) | Left for sensors |
|---|---|---|---|
| GPIOs | 45 (GPIO0–21, 26–48); 26–32 for flash/PSRAM; 33–37 also lost with octal PSRAM; 19/20 are USB-JTAG; 0, 3, 45, 46 are strapping pins | K-line TX/RX + L-line (U), CAN TX/RX, ignition and opto inputs (3–4), brain power, T1S SPI (4–5) + IRQ, GNSS UART + PPS, I²C (2) | About 8–12 on a custom node board (U); **only I²C (GPIO2/3) and the unused camera pins** on the LilyGO T-SIM7670G-S3 Standard |
| ADC | Two 12-bit SARs, 20 channels: ADC1 on GPIO1–10, ADC2 on GPIO11–20. **ADC2 cannot be used while Wi-Fi is on**. Calibrated error from ±5 mV (0–850 mV range) to ±50 mV (0–2900 mV range) | 12 V sense, battery sense | **ADC1 only** for senders and the harness ID; an external ADS1115 when more or better channels are needed |
| PCNT | 4 units × 2 channels, 16-bit counters, glitch filter | — | 4 pulse inputs (tacho, road speed, flow) |
| RMT | 4 TX + 4 RX channels sharing 384 × 32-bit words | — | Snapshot capture of pulse trains (lab "scope" mode) |
| MCPWM | 2 units, each with a capture module (3 capture channels per unit (U), timestamps on the APB clock) | — | Per-tooth timing on up to 6 inputs |
| UART | 3 (UART0–2), up to 5 Mbit/s, 1 KB FIFO RAM shared | K-line, GNSS, console (or a modem on the guardian) | Usually none: a wideband controller needs a node without console or a second GNSS |
| I²C | 2 controllers | On-board IMU/GNSS bus | Second bus for an external harness |
| SPI (general) | 2 (SPI2, SPI3) | T1S MAC-PHY (LAN8651) | Shared bus with chip selects for MAX31855s or an SD card |
| TWAI (CAN) | 1 | Vehicle CAN where present | A second CAN needs an MCP2515/MCP251863 on SPI |
| LEDC PWM | 8 channels | Status LED | Gauge outputs on add-ons only |

### 4.1 Memory and temperature

- **SRAM 512 KB** internal, 16 KB RTC SRAM. Wi-Fi, BLE, lwIP, TLS and the MQTT broker
  together take a large share (U, measure on the bench). ADR-0032 already says PSRAM is
  required. Rule: pack JSON trees, the logbook ring buffer and web assets go to PSRAM; ISR
  and DMA buffers stay in internal RAM.
- **Octal-PSRAM parts are rated only to 65 °C ambient** (ESP32-S3R8, R16V), or 85 °C with
  PSRAM ECC on (losing 1/16 of PSRAM). Quad-PSRAM parts are rated to 85 °C (FH4R2) or 105 °C
  (RH2, 2 MB). Cabin heat reaches 60–80 °C ([hardware risks](hardware.md#risks)), so a node
  board uses a quad-PSRAM part or turns on PSRAM ECC; this matters more than PSRAM size.
- **LilyGO T-SIM7670G-S3:** the wiki and product page list 8 MB PSRAM; the GitHub README
  for the Standard edition lists ESP32-S3-WROOM-1 with **2 MB quad PSRAM**. Two editions
  are sold (H707 and Standard H802), so check which one arrives (U).
- **Flash writes stall the caches.** While the internal flash is written (NVS, a LittleFS
  logbook), code and ISRs that are not in IRAM wait. The UART, PCNT and MCPWM ISRs must be
  built IRAM-safe (ESP-IDF Kconfig options exist for each), and the logbook should go to an
  SD card or PSRAM ring, flushed in batches.

## 5. Fast tacho vs K-line timing (both cores)

**Pulse rates.** Crank wheel with N tooth positions: f = rpm / 60 × N.

| Source | Example | At 4,500 rpm | Tooth period |
|---|---|---|---|
| Crank wheel 60-2 (owner's example) | 58 teeth seen per rev | 4,350 Hz | about 230 µs |
| Crank wheel 36-1 | 35 teeth | 2,625 Hz | about 380 µs |
| Td5 crank wheel | pattern (U), scope it first | — | — |
| Injector pulses, 5-cyl four-stroke | 2.5 events per rev | 188 Hz | 5.3 ms |

**Peripheral choice.**
- **PCNT** counts edges with no CPU per edge; read every 20–50 ms for a smooth rpm. Cheapest,
  no per-tooth detail. Default for "fast tacho" on any node.
- **MCPWM capture** stamps every edge in hardware at APB resolution (12.5 ns at 80 MHz) and
  raises one interrupt per edge. Gives per-tooth periods, gap detection on a missing-tooth
  wheel and crank acceleration. At about 4.4 kHz with a 1–3 µs IRAM ISR this costs roughly
  0.5–1.5 % of one core (U, measure).
- **RMT RX** records a burst of pulse widths into its RAM without per-edge interrupts: good
  for a lab snapshot, not for continuous running.

**K-line needs.** 10,400 baud is about 0.96 ms per byte. KWP2000 windows are milliseconds
(ECU inter-byte P1 up to 20 ms, response P2 25–50 ms, request spacing P3 from 55 ms, tester
inter-byte P4 0–20 ms; the ADR-0022 profiles carry the exact values). Fast init needs a
25 ms low and 25 ms high, held to about a millisecond. The UART FIFO and its RX-timeout
interrupt absorb bytes; only fast init and P4 spacing need timers (esp_timer or a GPIO
matrix switch for the wake-up pattern).

**Core plan.**

| Core | Runs |
|---|---|
| Core 0 | Wi-Fi, BLE, lwIP, TLS, MQTT broker and client, web server, OTA (ESP-IDF pins the Wi-Fi task to core 0 by default) |
| Core 1 | Link layer (K-line UART, TWAI), the transmit gate, the C decoder, GNSS parsing, sensor sampling; tacho ISRs allocated here, at a higher priority than the UART ISR |

**Verdict.** The two loads are on different time scales (µs edges vs ms windows), so a
diagnostic node can run PCNT tacho alongside K-line safely. A per-tooth MCPWM ISR at crank
rates is also within budget on paper, but jitter on a fast-init edge or a missed P2 reply
would hurt diagnostics, so **per-tooth crank timing is recommended on an engine-bay sensor
node**, and PCNT tacho is allowed on any node. Bench check: run fast init plus polling while
a signal generator feeds 6 kHz into MCPWM capture, and log P2 misses and init failures.

## 6. Parked current per sensor

The node and guardian sleep with the radio off between check-ins (ADR-0032 §4). Draw at the
part (3.3 V), before regulator losses.

| Item | Parked state | Draw | Source |
|---|---|---|---|
| ESP32-S3 | Deep sleep, RTC memory on | 7–8 µA | Datasheet v2.2 Table 5-10 |
| ESP32-S3 | Deep sleep with ULP polling a sensor | 170–190 µA | Same |
| ESP32-S3 | Light sleep (+ PSRAM: 40 µA for 2 MB quad, 140 µA for 8 MB octal) | 240 µA + PSRAM | Same |
| LSM6DSO | Accelerometer only, 1.6 Hz, wake-up interrupt armed | 4.4 µA | ST product data |
| BMI270 | Suspend; any-motion low-power mode | 3.5 µA suspend; any-motion (U) | Search summary of Bosch data (U) |
| ICM-42688-P | Low-noise accelerometer only | 280 µA (low-power mode lower, U) | TDK product page |
| BMP390 | 1 Hz sampling | 3.2 µA | Bosch flyer |
| MAX31855 | Always converting, no shutdown pin | 900 µA typ | ADI datasheet; **switch its supply off** when parked |
| u-blox MAX-M10S | Tracking | about 8 mA (25 mW) | u-blox datasheet; switched off parked, hot start from the backup cell |
| u-blox NEO-M9N | Tracking | about 31 mA | SparkFun product page; switched off parked |
| Active GNSS antenna LNA | Powered | 5–15 mA (U) | Switch with the receiver (the LilyGO switches it through modem GPIO1) |
| SIM7670G modem + GNSS | Sleep or PSM | (U) — vendor lists "TBD" | Measure |
| LilyGO T-SIM7670G-S3 board | Deep sleep, modem off | 147 µA (earlier listing) vs 497 µA average (2026 reseller listing) (U) | Measure both editions |
| VR crank conditioner (MAX9926 class) | Powered | mA class (U) | Switch off when parked |
| Opto tap input | Input low | 0 | Only draws when the car drives the line |
| Harness ID divider | Measuring for 1 ms at boot | 0 parked | Switched pull-up |

Budget rule: the guardian keeps only the IMU wake (µA class) and the ESP32-S3 deep sleep on
its own cell; everything else is power-switched. The node draws from the car battery, so the
hardware research's 20–50 mA parasitic allowance applies to the whole car, not to us.

## 7. Placement

| Device | Where | Why | Sensors |
|---|---|---|---|
| **Hidden guardian** | Behind trim, away from the diagnostic port: high on the dash behind the A-pillar or under the roof lining (U on the D2) | Survives the node being ripped out; antennas under plastic, not metal | IMU (screwed down, not foam tape, so tilt is real), GNSS with a hidden active antenna, LTE, tamper switch, own cell |
| **Diagnostic-port node** | Under the dash by the diagnostic connector (U on the D2) | Short K-line and CAN stubs; ignition and opto inputs nearby | u-blox (antenna cable to the top of the dash or the windscreen edge), 12 V sense, optional IMU |
| **Engine-bay sensor node** | Cabin side of the bulkhead, or a shaded inner wing in a sealed box; never near the turbo or exhaust | ESP32-S3 parts top out at 65–105 °C ambient (§4.1) | Thermocouple amps with K-type extension wire to the probe; boost and oil senders; crank pulses through a VR conditioner or opto |

## 8. Rules (carried from ADR-0032 and ADR-0033)

- **Taps are read-only and isolated.** A declared tap pin is configured as an input only;
  the config schema cannot turn a tap into an output. VR or opto conditioning presents a
  high impedance to the ECU's sensor circuit and never loads it (tap on a crank sensor shared
  with the ECU needs a conditioner with high input impedance; bench check on the scope that
  the ECU's waveform is unchanged).
- **Probing is read-only.** Detection reads ID registers only; a chip is written (reset,
  configured) only after its ID matched. Undeclared SPI chip selects and GPIOs are never
  driven.
- **Every output declares category and tier** in the manifest (ADR-0033 §1); a board
  profile with `outputs_allowed: false` (the guardian, every diagnostic node) refuses any
  declared output, and the manifest lists it under `problems`.
- **Sensors are Read, Tier 0.** Their readings are VSS signals with source tags (device,
  sensor) and shared time (ADR-0032 §13), recorded in the logbook beside bus data.

## 9. Driver libraries usable under ADR-0025 (licences checked 2026-10-06)

| Part | Library | Licence | Note |
|---|---|---|---|
| BMI270 | Bosch Sensortec BMI270_SensorAPI | BSD-3-Clause | Plain C with bus callbacks; ports to ESP-IDF directly |
| BMP390 / BMP388 | Bosch Sensortec BMP3_SensorAPI | BSD-3-Clause | Same style |
| BME280 | Bosch Sensortec BME280_SensorAPI | BSD-3-Clause | Same style |
| LSM6DSO / LSM6DSOX | STMicroelectronics lsm6dso-pid / lsm6dsox-pid | BSD-3-Clause | Platform-independent C register drivers |
| ICM-42688-P | Zephyr driver as a reference (Apache-2.0) (U); TDK's own driver licence (U) | — | Or write ours from the register map |
| QMI8658 and others on LilyGO boards | lewisxhe SensorLib | MIT | Arduino-style C++; usable as reference |
| u-blox GNSS | u-blox ubxlib | Apache-2.0 | Official; heavy. Alternative: SparkFun u-blox GNSS v3 (MIT), or our own UBX-NAV-PVT parser (small) |
| MAX31855, MCP960x, ADS111x, INA219/INA260 | esp-idf-lib components | BSD-3-Clause | ESP-IDF native; esp-idf-lib's `i2cdev` helper is MIT, its `bmp280` is MIT |
| MAX31855, MCP9600 | Adafruit libraries | BSD | Reference only (Arduino) |
| Bus drivers | ESP-IDF (I²C master, SPI master, PCNT, MCPWM, RMT, UART, ADC oneshot) | Apache-2.0 | The base layer |

All are permissive and compatible with the firmware's AGPL-3.0-or-later (ADR-0034); keep
their notices in `THIRD_PARTY_LICENSES.md`. ESPHome stays an idea source only (ADR-0032).

## 10. Open questions

1. Config file format: JSON (recommended: one parser on the node, already used for packs,
   JSON Schema in CI) or TOML (nicer by hand)?
2. Harness ID: a resistor (cheap, 16 codes per pin) now, with an I²C EEPROM in the harness
   as a later option?
3. Per-tooth crank timing: only on an engine-bay sensor node, or allowed on the diagnostic
   node too once the bench test passes?
4. The Td5 crank wheel pattern and whether its sensor can take a high-impedance tap without
   upsetting the ECU (scope test needed).
5. EGT needs a VSS overlay path (no upstream signal); boost maps to the overlay's
   `CombustionEngine.MAP`, oil pressure to `CombustionEngine.EOP`.

## Sources

[ESP32-S3 datasheet v2.2](https://documentation.espressif.com/esp32-s3_datasheet_en.pdf) (peripherals,
ADC2 and Wi-Fi, low-power currents, ambient temperature per part),
[ESP-IDF GPIO](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/gpio.html),
[ESP-IDF ADC oneshot](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/adc/adc_oneshot.html),
[ESP-IDF PCNT](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/pcnt.html),
[ESP-IDF MCPWM](https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/peripherals/mcpwm.html),
[LilyGO T-SIM7670G-S3 Standard README](https://github.com/Xinyuan-LILYGO/LilyGo-Modem-Series/blob/main/docs/en/esp32s3/sim7670g-s3-standard/README.MD),
[Linux BMI270 patch notes (chip ID)](https://lkml.iu.edu/hypermail/linux/kernel/2603.2/02057.html),
[ESPHome BMP3xx constants](https://api-docs.esphome.io/bmp3xx__base_8h_source),
[NuttX MCP9600 docs](https://nuttx.apache.org/docs/latest/components/drivers/special/sensors/mcp9600.html),
[RIOT QMI8658 constants](https://api.riot-os.org/qmi8658__constants_8h.html),
[MAX31855 datasheet](https://wcm-cce.cldnet.analog.com/media/en/technical-documentation/data-sheets/MAX31855.pdf),
[ST LSM6DSO](https://www.st.com/en/mems-and-sensors/lsm6dso.html),
[Bosch BMP390](https://bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp390),
[TDK ICM-42688-P](https://adm.invensense.tdk.com/icm-42688-p),
[esp-idf-lib component list](https://github.com/UncleRus/esp-idf-lib),
[Bosch BMI270 API](https://github.com/boschsensortec/BMI270_SensorAPI),
[ST lsm6dso-pid](https://github.com/STMicroelectronics/lsm6dso-pid),
[u-blox ubxlib](https://github.com/u-blox/ubxlib),
[SparkFun u-blox GNSS v3](https://github.com/sparkfun/SparkFun_u-blox_GNSS_v3),
[SensorLib](https://github.com/lewisxhe/SensorLib).

## Changelog

- 2026-10-06: v0.1, first draft for the owner's item 3 (sensor detection on nodes).
