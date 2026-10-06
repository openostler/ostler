---
title: "ADR-0032 — One node, optional brain (Ostler Lite and Ostler)"
area: decisions
status: locked
version: 1.2
updated: 2026-10-06
depends_on: [decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0025-reuse-and-licences-pragmatic.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md]
summary: >
  Owner direction of 2026-10-06. Two tiers: Ostler Lite is an ESP32 diagnostic node alone (optional 4G, phone app or Ostler Cloud, fully offline with a phone); Ostler adds a Pi brain. The node replaces the buddy and owns the car and power: bus I/O, decoding to VSS, the transmit gate (the only path to the car), GPS, optional 4G, the parked broker and brain power. The brain owns compute and network, never touches the car, and is woken and shut down cleanly by the node. The guardian is a hidden, output-free hardware variant of the node; one firmware publishes a capability manifest that drives each device's UI. One portable C decoder reads packs as JSON on ESP32 and PC (ctypes), checked by shared vectors, with Python as the lab and reference fallback. One app runs in the cloud, on the brain and on the phone. Sensor nodes add tagged data through read-only isolated taps. Supersedes parts of ADR-0028, ADR-0002, ADR-0020 and ADR-0027. Amended 2026-10-06: GPS split (the guardian's 1 Hz modem GNSS for security, a 10 Hz u-blox for drive logging, every fix a tagged reading, best fix selected, GNSS time served by the time-role holder) with the u-blox placement pending product-family research; sensor detection (board profile, detected chips, declared config or harness ID, one manifest with origin and status per item, read-only probing).
---

# ADR-0032 — One node, optional brain

> **Amended 2026-10-06 (owner answers):** §5, §6, §13 and §14 gain the GPS split and sensor detection; the 10 Hz u-blox's placement is **pending (product-family research)**. See [Amendments](#amendments-2026-10-06-gps-split-and-sensor-detection).

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06). Supersedes parts of
  [ADR-0028](adr-0028-base-hardware-connectivity-and-remote-access.md),
  [ADR-0002](adr-0002-layered-stdlib-core.md),
  [ADR-0020](adr-0020-can-links-listen-only-by-default.md) and
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md) (see
  [Supersedes in part](#supersedes-in-part)). Companion decisions: ADR-0033 (action
  categories and approvals), ADR-0034 (repo boundaries), ADR-0035 (languages by tier) and
  ADR-0036 (VIN and identity data in recordings).

## Context

- ADR-0028 made the base a Pi plus an always-on ESP32 "buddy", with the guardian as an
  add-on. The Pi did the car work in Python; the buddy only listened while parked.
- The owner wants a cheaper entry product that works without a Pi, and a clean upgrade
  path to the full system with no change on the car side.
- The protocol logic exists twice today: in Python (the platform) and hand-ported in the
  D2 pack's ESP32 firmware. SCOPE.md treated that as unavoidable.
- Decoding is still open for several D2 areas (MAF, wastegate, EGR, SLABS), so the Python
  lab must keep moving fast.

## Decision drivers

- One path to the car, gated in one place, that stays up when everything else is off.
- A useful product with only a node and a phone, and never a cloud-only one.
- The upgrade is additive: plug in a brain, change nothing on the car side.
- One decoder and one set of pack data on every device, checked by the same vectors.
- The alarm path never depends on the brain or the internet.
- Low parked drain; a hung brain can never drain the battery.

## Decision

**1. Product line.** "Node" and "brain" are working names.

| Tier | Hardware | What it gives |
|---|---|---|
| **Ostler Lite** | ESP32 diagnostic node alone; 4G is an official option | Tracking, basic alarm, live data and faults through the phone app or Ostler Cloud. Works fully offline with a phone |
| **Ostler** | Node + Pi brain | The full local app, routing for add-ons, cameras, large logbooks, replay, analysis, the decode lab |

Add-ons work on either tier. Upgrading is plugging in a brain.

**2. The node owns the car and power.** It replaces the buddy; there is no separate buddy.
It owns K-line and CAN I/O, decoding to VSS, **the transmit gate (the only path to the
car)**, GPS, optional 4G, the parked MQTT broker and switching the brain's power. Grants
for gated actions may be minted by the brain or the phone; the node verifies every one
before anything reaches a bus (ADR-0033 sets the categories and approvals).

**3. The brain owns compute and network.** It never touches the car directly. It consumes
the node's VSS messages over IP, as the cloud, the phone and Home Assistant do. Link: 10BASE-T1S
(ADR-0026), or Ethernet, USB or UART on dev kits.

**4. Wake and shutdown.**
- The node wakes the brain on: ignition; a phone or cloud request; an alarm that needs
  cameras or recording; a schedule; or the EV always-on setting.
- While the brain is awake its broker bridges to the node's broker, and it serves the app,
  routing, logging and replay.
- The node orders a **clean shutdown with a timeout**; at the timeout it cuts power, so a
  hung brain cannot drain the battery.
- With the brain off, the node is the hub again.

**5. The guardian is a hardware variant of the node**, on the same firmware, built for
security: its own backup battery, tamper sensing, an IMU for tilt and motion, better
antennas, GPS, optional 4G with an IoT SIM.
- It is fitted hidden, away from the diagnostic port. It either **replaces** the plain node
  (wired behind the dash) or sits **alongside** it as a hidden battery-backed tracker that
  alerts if the node is ripped out.
- **It has no outputs**: no siren, native-alarm trigger or immobiliser I/O. It stays light
  and hidden. Alarm outputs come later through a separate I/O or relay module with its own
  design, and every car function it switches needs its own ADR.
- Starting hardware: LilyGO T-SIM7670G-S3 plus an IMU breakout. It is probably the natural
  motorbike product.

**6. One firmware; the UI follows the hardware.** Each variant detects its hardware at boot
and publishes a **capability manifest**. Its local web page is generated from that
manifest: a diagnostic-port node shows diagnostics and security; a hidden guardian shows
tracking, IMU, tamper and arm state and no diagnostics. Absent sensors never appear.

**7. Uplinks per device.** Each device may carry its own IoT SIM. Devices on the car LAN can
share uplinks under ADR-0028's selection, failover and metering.

**8. One decoder in portable C; packs are data.**
- The decoder is portable C and reads packs as JSON. The same source builds for the ESP32
  and for PC/Linux; Python calls the PC build through `ctypes`.
- **Shared test vectors** (bytes in, VSS out, plus init and gate cases) run in CI against
  both builds. They are seeded from the existing golden tests.
- If the native library is missing, the **Python reference decoder** is used.
- **Keygens** (seed-key, for example Td5) are a C firmware plugin per pack, compiled into the
  node. The Python version stays the lab reference; the shared vectors check both.

**9. Python stays the lab.** While decoding is ongoing, Python is the lab and the reference.
Discovery, re-decoding old recordings, analysis, the MCP server and high-level features stay
Python on the brain and the cloud. The link and decode layers are ported to C **once a
pack's facts are stable**. The KKL-cable path becomes **dev-only**. Recordings keep **raw
bytes alongside decoded values** (identity data per ADR-0036).

**10. Current work continues.** The approved K-line, J1979 and CanLink specs are built in
Python as planned. Their production link layer moves to the node later; the Python code
remains the reference and the lab path.

**11. Cloud merges; the car works without it.**
- Ostler Cloud merges every device and serves the whole app remotely. In the car, the brain
  (or the phone, on Lite) merges the same data over the local network, so the alarm path
  and the in-car app never depend on the internet.
- **One app codebase in three places:** the cloud; the brain; the phone as a PWA in a native
  wrapper such as Capacitor (needed for Bluetooth and local Wi-Fi, especially on iOS).
  Brain and cloud run the same containers (Dokploy-style).
  *Amended 2026-10-06 (owner):* with a brain or Ostler Cloud reachable, the phone app loads
  the shell and apps from that server (Home Assistant's Companion model); for Lite and
  offline it ships a bundled shell, the core apps and declarative add-on apps; its native
  features are fixed in the binary, and it runs no runtime third-party code. Detail:
  [app-model spec §7.1](../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build).
- The **phone-to-node link** (BLE through the wrapper, or the node's Wi-Fi AP) is **core
  now**. Web Bluetooth comes off the moonshot list.

**12. Lite without a brain.** Sign-in uses pairing keys held on the phone. The node records
sessions itself, in the ADR-0009 schema (which already anticipates the ESP32 writing it).
There is no Pi CA; trust comes from pairing.

**13. Composite sensor data.** Every device publishes VSS readings with **source tags**
(device, sensor) and shared time (NTP). The brain, the cloud or the node merges them: a
best or fused GPS fix; IMU motion with the ignition off as tow or theft, with fewer false
alarms; bus wheel speed against GPS speed.

**14. Sensor nodes** are new data sources: a fast tacho (crank, coil or injector pulses), an
EGT thermocouple, boost, oil pressure and oil temperature, wideband AFR through a
controller's serial port, extra accelerometers.
- They reuse open-source sensor driver libraries under ADR-0025, not ESPHome itself.
- **Taps on car wiring are read-only and isolated** (optocouplers or high impedance). They
  never load or alter an ECU signal.
- Readings are VSS signals tagged with their source and recorded in the same logbook.

**15. Our own BCUs and relay boards come later**, as add-ons whose controls declare category
and tier (ADR-0033). Anything that switches a car function needs its own ADR before it
ships. The `ostler-hardware` repo starts when PCB work starts (ADR-0034).

**16. Discovery registration timing.** `_ostler-mod._tcp` is used **unregistered during
development**; the drafted IANA request is submitted at **module contract v1**.

## Supersedes in part

- **ADR-0028 §1** (base = Pi + buddy; guardian as an add-on): replaced by §1–§2 and §5
  here. The node replaces the buddy; the guardian is a node variant.
- **ADR-0028 §2** (power states): replaced by §4 here (wake, clean shutdown with timeout).
- **ADR-0028, all "buddy" wording** (§3–§5, §7, Consequences, Confirmation): read "node".
- **ADR-0002**, "the production core stays Python": the production link and decode layers
  move to portable C on the node (§8–§9). Python stays the lab, the reference, the server and
  the high-level features. ADR-0035 sets languages by tier.
- **ADR-0020, link order and gate location:** the node's gate is the only transmit path;
  the brain or the phone mint grants and the node verifies them. SocketCAN and slcan on the
  Pi become lab and dev links. Listen-only by default and the allowlist rule stand.
- **ADR-0027, the Amendments' "Base and guardian" entry:** replaced by §1–§2 and §5 here.
  **ADR-0027 §9 "the one server gate"**, for car-touching actions: the gate is on the node.
  The gate wording for actions that do not touch the car is unchanged.

§16 also sets the timing of ADR-0028 §9: the registration stands, but the request is
submitted at module contract v1 rather than now.

## Risks

- **Phone-to-node connectivity** (BLE and AP behaviour, especially on iOS).
- **Node security:** secure boot, flash encryption, signed OTA, pairing, no default
  passwords, and the gate living on the node.
- **ESP32-S3 memory:** PSRAM is required.
- **Pack updates** must be signed and must not need a reflash.
- **Running a cloud service**, including GDPR duties for location data.
- **Supporting two tiers.**
- **Slower iteration in C.** Mitigation: build the firmware logic natively for CI and test it
  there.

## Confirmation

On the bench:
- An ESP32-S3 node initialises the D2 over K-line, decodes a few signals from pack JSON and
  publishes them as VSS over MQTT.
- The C decoder passes the shared vectors on the ESP32 and on PC.
- The node power-switches a Pi 5 (inrush included) and shuts it down cleanly; a brain that
  ignores the request is cut at the timeout.
- A node or guardian alert reaches a notification with the brain off.
- The LilyGO guardian prototype reports GPS, IMU and tamper.

**Fallback:** if the bench fails, the current Pi + Python path still works, and stays the
supported path until it passes.

## Consequences

- The firmware becomes first-class (ADR-0034); the D2 pack's `kline_node` moves there.
- SCOPE.md's statement that the protocol is necessarily implemented twice is reversed.
- The module-bus message spec gains the node's capability manifest, the brain bridge
  patterns, the wake and shutdown messages, and source tags on readings.
- The UI spec's Security destination applies to every tier, since every node has GPS and a
  basic alarm.
- GOALS, SCOPE and the hardware research are updated to the node/brain model by their owners.

## Alternatives considered

- **Keep the Pi as the only car path, with a buddy.** Rejected: no product without a Pi, and
  the gate would be off whenever the Pi sleeps.
- **The guardian as a separate add-on product.** Rejected: one firmware and one variant line
  are cheaper to build and support.
- **ESPHome as the node firmware.** Rejected: we reuse its ideas and open driver libraries,
  but a framework would own our gate and manifest.
- **Keep two hand-written protocol implementations.** Rejected: they drift; shared vectors
  over one C decoder do not.
- **Port everything to C now.** Rejected: decoding is still open; the Python lab stays until
  the facts are stable.
- **Cloud-only Lite.** Rejected: the car must work offline with a phone.

## Amendments (2026-10-06, GPS split and sensor detection)

*Accepted by the owner on 2026-10-06 (owner items 2, GPS split, and 3, sensor detection on
nodes), except the placement of the 10 Hz u-blox, which is **pending (product-family
research)**: an "Ostler Diagnostics" OBD-port node is being designed, and where the receiver
sits follows from that work. §5, §6, §13 and §14 above are unchanged; these entries add to
them. Research: [hardware research, GPS
split](../references/research/hardware.md#gps-split-two-receivers-two-jobs-2026-10-06) and
[node sensors](../references/research/node_sensors.md). Related:
[ADR-0037](adr-0037-role-holders-and-handover.md) (time source role, best clock first).*

### A. GPS split: two receivers, two jobs

**A1. Receivers.**
- **Guardian GNSS** (the LilyGO's built-in SIM7670G today): security tracking, geofences,
  check-ins and theft tracking. It is **1 Hz only** (the modem accepts no other rate), L1
  GPS/GLONASS/Galileo/BeiDou; its accuracy and TTFF are unpublished and must be measured. It
  gets its own **hidden active antenna**, separate from the node's, so removing the node
  leaves the guardian seeing the sky.
- **A 10 Hz u-blox** (MAX-M10S or NEO-M9N class; NEO-M9V with dead reckoning as an option):
  drive logging, replay, Drive mode, the driving-state fallback and the speed-vs-wheel-speed
  check. **Its placement is pending (product-family research).** The candidates are the
  diagnostic node or the "Ostler Diagnostics" OBD-port node being designed (UART, time
  pulse to a GPIO), which would work on Ostler Lite, give the node gate its own fast speed
  source and make that device the best clock; a USB u-blox on the brain stays a dev path
  and an option. Whichever device carries it publishes it in its manifest; nothing below
  depends on where it sits.

**A2. Every fix is a tagged reading.** Fixes publish as `Vehicle.CurrentLocation.*` (with
`GNSSReceiver.FixType`, `HorizontalAccuracy`) plus speed, each with:
`source` = {device id, receiver id}, the **GNSS time of fix** (UTC), the **receive time on
the shared clock**, horizontal and speed accuracy, satellites used, the receiver's rate, and
`dr: true` when a dead-reckoning receiver is coasting.

**A3. Shared time.** GNSS time is the reference. The device holding the time role (ADR-0037)
disciplines its clock from GNSS, with PPS where wired, and serves SNTP on the car LAN; the
role goes to the best clock first (ADR-0037 §2), normally the device carrying the u-blox,
wherever that ends up. Readings from a device with no synced clock carry `time: unsynced` and are merged
by receive order only, never across devices by timestamp.

**A4. Selection (best fix, not fusion, in v1).** A fix is **usable** when its fix type is 3D
(or 2D for the guardian while parked), its age is under two of its own periods (u-blox
about 200 ms at 10 Hz; guardian about 2 s), and its horizontal accuracy is under a set limit
(proposed 25 m, tuned on the car). Then:

| Situation | Selected source |
|---|---|
| Ignition on or Moving, u-blox usable | u-blox |
| Ignition on or Moving, u-blox not usable | guardian (marked `degraded_rate`) |
| Parked, ignition off | guardian; the u-blox and its antenna are powered down |
| Node offline (offline will or missed heartbeats) | guardian, with a node-loss alert when armed (§5) |
| Neither usable | no position; the last fix is kept with its age, never re-dated |

- **Hysteresis:** switch back to the u-blox only after it has been usable for 3 s; switch
  away after 1 s unusable. The merged stream names the source it picked.
- **Disagreement:** when both are usable and more than max(3 × the sum of their stated
  accuracies, 50 m) apart for over 10 s, publish a `position_disagreement` event (a fault,
  jamming or spoofing); while parked the guardian's fix wins.
- **Recording:** each receiver is logged as its own channel set, plus the merged stream;
  replay prefers the u-blox channels. Fused (filtered) positions are a later option.
- **Who merges:** whichever device holds the merge for the moment (§11, §13): the node when
  it sees both, the brain or the cloud otherwise. The rules live in one documented algorithm
  with shared test vectors, run by the C firmware and the Python server alike (as §8 does for
  decoding).

**A5. Speed checks.** On steady, straight segments above 30 km/h, bus wheel speed against
u-blox ground speed gives a speedometer or tyre-size ratio (Read only, logged). The driving
state keeps the UI spec order: vehicle speed, then GNSS speed (u-blox before guardian), then
gear and handbrake signals. A gate decision never trusts a speed that arrived from another
device's role; it uses its own bus or its own receiver.

### B. Sensor detection: one firmware, manifest from hardware

**B1. Two inputs, one manifest.**
- **Detected:** I²C chips by address and ID register (IMUs, pressure sensors, MCP9600-type
  thermocouple amps, power monitors), u-blox receivers by UBX poll, and the board's own
  parts from its compiled-in **board profile**.
- **Declared:** what cannot be detected (tacho and speed pulses with their wheel pattern,
  analog senders, read-only taps, SPI parts such as the MAX31855, and outputs on I/O boards)
  in a small **node config file** (JSON, validated by a JSON Schema) or by a **harness ID
  resistor** that selects a built-in harness profile (for example "pin 12 = crank pulse,
  60-2 wheel").
- Both feed one capability manifest. Each item says where it came from (`board`,
  `detected`, `harness`, `config`) and its status (`ok`, `absent`, `fault`, `no_signal`,
  `refused`). Declared SPI parts are confirmed by plausibility (the MAX31855 has no ID
  register); a declared pulse input becomes `ok` once plausible pulses arrive.

**B2. Rules.**
- **Probing is read-only:** only ID registers are read until a chip has matched; undeclared
  SPI chip selects and GPIOs are never driven.
- **Taps are read-only and isolated** (§14): the config cannot make a tap an output; inputs
  go through optocouplers or high-impedance conditioners.
- **Every output declares its category and tier** (ADR-0033 §1). A board profile with
  outputs disallowed (the guardian, every diagnostic node) refuses a declared output and lists
  it as `refused`; car-switching functions still need their own ADR.
- **Budgets are checked at boot:** a declaration that needs ADC2 while Wi-Fi is on, a pin the
  board reserves, more pulse inputs than PCNT and MCPWM capture provide, or a sensor that
  would break the parked-current budget is refused with a reason.
- **Sensors are Read, Tier 0,** with source tags and shared time (§13).
- **Per-tooth crank timing** runs on an engine-bay sensor node; a diagnostic node may count
  tacho pulses (PCNT) beside K-line. Both cores are planned: radio and network on one, link
  layer, gate, decoder and sensor interrupts on the other.

**B3. Where it is specified.** The boot sequence, the config schema and the harness ID
scheme go in the `ostler-firmware` spec `docs/specs/sensor-detection.md` (ADR-0034). The
manifest additions (`origin`, `status`, `problems`) go to the module-bus message spec and the
UI spec's §5 device entries.

**Pending and open:**
- **Pending (product-family research):** which device carries the 10 Hz u-blox (A1).
- **Open, settled with that research or on the bench:** MAX-M10S or NEO-M9N, and whether
  to pay for dead reckoning (NEO-M9V); the accuracy limit and hysteresis values of A4 (the
  values above are starting points); a resistor harness ID now with an EEPROM later;
  whether per-tooth timing may ever run on the diagnostic node. The node config is JSON
  (B1).
