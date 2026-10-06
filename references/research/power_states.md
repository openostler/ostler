---
title: "Power states and wake — sleeping devices, wake paths, wake requests and parked current"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, references/research/hardware.md, references/research/connectivity_uplink.md, references/research/node_sensors.md, references/research/t1s_module_bus.md, references/research/cluster_view.md]
summary: >
  Live research (2026-10-06) behind ADR-0040 (draft) for the owner's request that add-on actions wake the brain only when they need it, and otherwise wake just the module they talk to, with "asleep" and "woken" shown honestly. Patterns: AUTOSAR network management (a bus stays awake while anyone requests it, then times out to sleep) and CAN partial networking (ISO 11898-2:2016 selective wake, TJA1145A under 64 µA); OPEN Alliance TC10 on 10BASE-T1S (in LAN865x/LAN867x silicon, wakes the whole segment, only a March 2026 LAN867x Rev D0 patch series in Linux; not confirmed for NCN26010); Wake-on-LAN (unauthenticated, so never a remote path); MQTT 5 session expiry, message expiry, retained state and will; ESP32-S3 sleep (deep sleep 7–8 µA chip, no radio; auto light sleep keeps Wi-Fi at about 1–2.5 mA; BLE needs light sleep); Matter ICDs (SIT up to 15 s polling, LIT with check-in) and Thread sleepy end devices; ESPHome and Home Assistant showing deep-sleep devices as unavailable unless set up for it; Pi 5 boot about 15–20 s, about 3 W idle, about 1.2 W halted unless POWER_OFF_ON_HALT=1 (0.01 W); car parasitic norms about 50 mA after 30 min. Proposes reachability classes, parked modes for the node, latency and energy figures for a budget, and the gaps to bench.
---

# Power states and wake

Research for the owner's request of 2026-10-06: "add-on actions wake the brain if necessary,
or they wake the module they're trying to talk to, where the brain isn't necessary. We should
probably try and convey this concept of 'asleep' and woken, perhaps build something more in
depth around it." The decision draft is
[ADR-0040](../../decisions/adr-0040-power-states-and-wake.md). Facts checked live on
2026-10-06 unless marked; **(U)** marks a figure that is unverified or needs the bench.
Concepts only: no specification text or code is reused.

## 1. What the existing decisions already fix

- **The node owns brain power** and wakes it on ignition, a phone or cloud request, an alarm
  that needs cameras or recording, a schedule or the EV always-on setting; it orders a clean
  shutdown with a timeout and then cuts power ([ADR-0032 §4](../../decisions/adr-0032-one-node-optional-brain.md)).
- **The alarm path never depends on the brain or the internet**
  ([ADR-0033 §7](../../decisions/adr-0033-action-categories-and-approvals.md)).
- **µA wake nodes stay on CAN or a separate wake wire** until T1S wake is proven; the wake
  wire to first MQTT message must be ≤ 500 ms on the bench
  ([ADR-0026](../../decisions/adr-0026-module-bus-10base-t1s.md)).
- **The parked broker is on the node**; the brain's broker bridges to it when awake
  ([ADR-0028 §5](../../decisions/adr-0028-base-hardware-connectivity-and-remote-access.md),
  [ADR-0037](../../decisions/adr-0037-role-holders-and-handover.md), draft).
- **Hardware notes:** a halted Pi must be cut (60 s hard shutdown timeout); no Pi below about
  12.0 V; heartbeat only below about 11.8 V; OVMS-style staged power-down
  ([hardware.md](hardware.md#power-wake-and-buses-detail)).

What is missing: a power state per device, wake paths to add-on modules, wake requests as
messages with limits, the "needs the brain?" rule per action, and what the UI shows.

## 2. Patterns from automotive networks

### 2.1 AUTOSAR network management (CAN NM)

AUTOSAR's CAN NM specification ([R24-11 SWS](https://autosar.org/fileadmin/standards/R24-11/CP/AUTOSAR_CP_SWS_CANNetworkManagement.pdf),
[R25-11](https://www.autosar.org/fileadmin/standards/R25-11/CP/AUTOSAR_CP_SWS_CANNetworkManagement.pdf))
is the pattern most OEM cars use (concepts paraphrased):
- **Decentralised keep-awake.** Every node that needs the bus sends periodic NM messages. A
  node that no longer needs the bus stops sending, and when **nobody** has sent one for an NM
  timeout the whole bus goes to a prepare-sleep phase and then to bus-sleep.
- **States:** bus-sleep → (wake) → network mode (a short *repeat message* phase so everyone
  learns who is awake, then *normal operation* while the node requests the network, then
  *ready sleep* while others still do) → prepare bus-sleep → bus-sleep.
- **Partial network clusters (PNC):** NM messages carry a bit vector of which function
  clusters are requested, so a transceiver with selective wake only wakes its ECU for the
  clusters it serves.

**Lesson for Ostler:** "awake" should be a **sum of requests with expiry** (a lease), not a
toggle. A device sleeps when its last lease ends plus a short linger. Wake requests name a
purpose, so only the device that serves it wakes.

### 2.2 CAN selective wake (ISO 11898-2:2016 partial networking)

- A partial-networking transceiver sleeps and wakes its node only on a configured **wake-up
  frame** (ID and data mask), ignoring other traffic.
- **NXP TJA1145A:** quiescent current below **64 µA** with the bus idle, under 1 mA with the bus
  active; local and remote wake; FD-passive variants ignore CAN FD frames while waiting
  ([NXP TJA1145A](https://www.nxp.com/products/TJA1145A),
  [datasheet](https://nxp.com/docs/en/data-sheet/TJA1145.pdf?pspll=1)).
- This is the only **selective, proven** µA wake on our list. ADR-0026 keeps CAN for µA wake
  nodes for that reason; ADR-0026's open CAN-fallback security (no actuator or alarm-arm
  command from a CAN-only node) still applies to anything carried after the wake.

### 2.3 TC10 on 10BASE-T1S

- The OPEN Alliance 10BASE-T1S sleep/wake specification 1.0 (2022) has a wake-up pulse that
  wakes **every node on the segment** (no selective wake); a local wake pin; an INH output to
  switch the node's own regulators; wake indication within about 17 ms
  ([t1s_module_bus.md §6](t1s_module_bus.md#6-wake-and-sleep)).
- **Silicon:** LAN8650/1 and LAN867x implement it (LAN8650/1 sleep typically under 140 µW,
  about 42 µA at 3.3 V); TI's DP83TD555J-Q1 claims it. For the **onsemi NCN26010** no TC10
  support was found in public material today (U: check the datasheet).
- **Software, live:** a patch series of **2026-03-30** adds generic TC10 suspend and resume
  helpers to the Linux Clause 45 PHY layer and TC10 sleep plus wake-on-PHY (exposed through
  ethtool WoL) to the **LAN867x Rev D0** driver, tested on the EVB-LAN8670-USB; it is a
  net-next proposal, not known to be merged ([LWN](https://lwn.net/Articles/1065451/)). Nothing
  for the LAN865x MAC-PHY or ESP-IDF.
- **Lesson:** TC10 is a *segment* wake (all modules wake, then the ones not addressed go back
  to sleep). Fine for a few modules; it costs every module a boot. Selectivity must come from
  the message after the wake, not the wake itself. The wake wire is the same: one shared
  open-drain line.

### 2.4 Wake-on-LAN

- A magic packet is six 0xFF bytes followed by sixteen copies of the target MAC (102 bytes),
  usually a UDP broadcast to port 9 or EtherType 0x0842
  ([Wikipedia](https://en.wikipedia.org/wiki/Wake-on-LAN)). The optional "SecureOn" password
  is a 6-byte plain-text value.
- **Lesson:** WoL carries no authentication and no purpose. Inside the car the node already
  switches the brain's power, so WoL adds nothing; it must **never** be a remote path. At most
  a lab convenience on a bench Ethernet.

## 3. Patterns from IoT and smart homes

### 3.1 MQTT 5 for sleeping clients

- **Session expiry interval:** with clean start off and a non-zero session expiry, the broker
  keeps a client's subscriptions and **queues QoS 1 and 2 messages** while it is away, up to
  the expiry ([HiveMQ, session and message expiry](https://www.hivemq.com/blog/mqtt5-session-message-expiry/),
  [EMQX](https://docs.emqx.com/en/emqx/v5.0/mqtt/mqtt-session-and-message-expiry.html)).
- **Message expiry interval:** per message; the countdown starts when the broker receives it,
  and an expired message is **dropped, even if the session still exists**
  ([EMQX](https://www.emqx.com/en/blog/mqtt-message-expiry-interval)). This is exactly the
  "queued action never runs after its expiry" rule, at the transport level.
- **Mosquitto** bounds the queue with `max_queued_messages` and `max_queued_bytes`, can expire
  idle sessions with `persistent_client_expiration`, and queues QoS 0 only if told to
  (examples: [mosquitto.conf](https://code.nicolabs.net/nicolabs/mosquitto/src/commit/c4e72331591334e75fb13a26acdd420986386c52/mosquitto.conf)).
  Whether Espressif's on-node Mosquitto port keeps persistent sessions in RAM, and how many,
  is unstated (U; [connectivity_uplink.md §2](connectivity_uplink.md#2-mqtt-broker-on-the-always-on-esp32-feasibility)).
- **Retained state and the will:** a clean MQTT 5 disconnect (reason 0x00) does **not**
  publish the will; an unclean loss does. So a device can publish a retained `asleep` status
  and disconnect cleanly, and "asleep" is never confused with "offline" (ADR-0037 §3 uses
  `online`/`offline` only today).
- **Lesson:** a queue is only safe with **two expiries**: the transport's (message expiry) and
  the gate's own (`expires_at` re-checked at execution). Never rely on the broker alone,
  because brokers reboot and lose RAM queues.

### 3.2 Matter ICDs and Thread sleepy end devices

- **Matter ICD** (Intermittently Connected Device): idle mode (asleep, polling slowly), active
  mode (reachable), and an active-mode threshold that keeps it awake briefly after traffic
  ([Silicon Labs ICD guide](https://docs.silabs.com/matter/2.3.0/matter-overview-guides/matter-icd)).
  - **SIT** (short idle time): polls at **≤ 15 s**, so a controller can reach it without
    coordination; example defaults are minutes of idle interval with 1 s threshold.
  - **LIT** (long idle time): sleeps minutes to an hour; the controller cannot reach it on
    demand. It sends a **Check-In** (a short, sessionless, keyed and counted message) to
    registered clients, which must act **during that window**; the active-mode threshold is at
    least 5 s. A **user active-mode trigger** (a button) makes it reachable for setup. LIT suits
    sensors and switches that report, not devices that must be commanded quickly
    ([Matter glossary](https://pigweed.googlesource.com/third_party/github/project-chip/connectedhomeip/+/HEAD/docs/GLOSSARY.md),
    [Nordic low-power Matter](https://nrfconnectdocs.nordicsemi.com/addons/ncs-matter/latest/matter/getting_started/low_power_configuration.html)).
- **Thread SED and SSED:** a sleepy end device polls its parent for queued data (latency = poll
  period); a synchronised one listens at agreed slots (CSL); the parent supervises the child so
  the child need not transmit to prove it is alive
  ([Nordic SED/SSED](https://nrfconnectdocs.nordicsemi.com/ncs/latest/nrf/protocols/thread/sed_ssed.html),
  [OpenThread child supervision](https://openthread.io/guides/build/features/child-supervision)).
- **Lesson:** classify each device by **reachability**, not by "battery or mains": always
  reachable, wakeable on demand (a wire), reachable only at check-in (a poll), or unreachable.
  The parent (for us, the node or the parked broker) holds messages for check-in devices.

### 3.3 How Home Assistant and ESPHome show sleeping devices

- ESPHome's deep sleep doc: a deep-sleeping node does no work and answers nothing, not even
  OTA; entities show **Unavailable** while it sleeps unless the device was registered with deep
  sleep configured (otherwise remove and re-add it). It offers *prevent* and *allow* actions to
  hold a node awake (for OTA), commonly driven by a **retained MQTT** "OTA mode" topic the node
  reads when it wakes; since ESPHome 2026.8.0 entering deep sleep marks new firmware good
  ([ESPHome deep_sleep](https://esphome.io/components/deep_sleep/)).
- Community practice is MQTT for sleepers, so the last state stays shown
  ([HA community notes](https://community.home-assistant.io/t/notes-on-esphome-deep-sleep/860987/9)).
- Matter controllers keep ICD state from their last report and deliver commands at check-in;
  how each controller labels it was not found in public docs (U).
- **Lesson:** "Unavailable" for a device that is supposed to be asleep is the classic smart-home
  wart. Ostler shows **Asleep · last seen 2 h · wakes on wire** and keeps last values (stale-
  grey, never zero; UI spec §2 honest states). "Offline" is only for an unexpected loss (the
  will). An "OTA hold" is a **stay-awake lease** with an expiry.

## 4. ESP32-S3 sleep modes

From the ESP-IDF sleep-mode and low-power guides (latest, read 2026-10-06:
[sleep modes](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-reference/system/sleep_modes.html),
[Wi-Fi low power](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s3/api-guides/low-power-mode/low-power-mode-wifi.html)):

| Mode | Wake sources | Radio | Chip current |
|---|---|---|---|
| Deep sleep | timer, touch, EXT0, EXT1, ULP, GPIO (RTC pads) | **off; connections dropped** | about 7 µA (6.9 µA in the Wi-Fi guide; 7–8 µA datasheet, [node_sensors.md §6](node_sensors.md#6-parked-current-per-sensor)); 170–190 µA with ULP polling |
| Light sleep (manual) | timer, touch, EXT0/1, ULP, GPIO, **UART**, Wi-Fi, BT | **connections not kept** unless power management is used | 240 µA datasheet; real boards 0.7–2.9 mA, mostly the flash rail ([esp32.com](https://esp32.com/viewtopic.php?p=150090)) |
| Auto light sleep + Wi-Fi (connected) | as light sleep, plus DTIM beacons | **kept**, wakes each DTIM | **2.45 mA DTIM1, 1.33 mA DTIM3, 0.93 mA DTIM10** (160 MHz) |
| Modem sleep + Wi-Fi | — | kept | about 20 mA |

- **UART wake** loses its first characters (the wake edge count is consumed); not a data path.
- **BLE** reachability needs light sleep with the controller running; advertising at a slow
  interval adds little on average but peaks at about 100–130 mA for 1–5 ms per event
  ([Hubble guide](https://hubble.com/community/guides/esp32-power-consumption-in-ble-mode-what-to-expect-from-advertising-scanning-and-connected-states/))
  (U: measure our board).
- **Consequence:** a node in deep sleep **cannot be reached by a phone** (no BLE, no AP) or
  by the module bus; only by its wires (ignition, door, IMU, wake wire, CAN transceiver wake),
  a timer, or a modem ring line. So the node needs **two parked modes** (§6).
- Board figures dwarf the chip's: the LilyGO guardian board is 147 µA or 497 µA in deep sleep
  (U), and regulators add their own ([hardware.md](hardware.md)).

## 5. Brain (Pi 5) figures

| Figure | Value | Source |
|---|---|---|
| Boot to a usable OS | about **15–20 s** (Pi OS, any storage); slower with cloud-init or network-wait units | [Elecrow review](https://www.elecrow.com/blog/unveiling-the-raspberry-pi-5-software-user-experience-the-most-in-depth-review.html), [HSTWB wiki](https://github.com/henrikstengaard/hstwb-installer/wiki/Boot-and-setup-Raspberry-Pi-OS-Lite) |
| Boot to Ostler served (OS + Mosquitto + server + bridge) | **not measured** (U); estimate 25–40 s | bench |
| Idle, headless, Wi-Fi | about **2.7–3.0 W** (≈ 0.25–0.3 A at 12.6 V after the buck) | [raspberry.tips 2026](https://raspberry.tips/en/raspberrypi-tutorials/raspberry-pi-power-consumption-update-2026-all-models-compared) |
| Halted, default EEPROM | about **1.2 W** (≈ 0.1 A at 12 V) | [Jeff Geerling](https://www.jeffgeerling.com/blog/2023/reducing-raspberry-pi-5s-power-consumption-140x/) |
| Halted, `POWER_OFF_ON_HALT=1` | about **0.01 W** | same |

The node still cuts the brain's supply after shutdown (ADR-0032 §4); `POWER_OFF_ON_HALT=1`
is belt and braces for the window between halt and cut.

**Energy per brain wake (estimate, U):** boot 30 s + 5 min held + 20 s shutdown at about
0.3 A ≈ **30 mAh** at 12 V. On a 70 Ah battery that is about 0.04%.

## 6. Parked current: norms and a budget

- **Car norms:** after 30 minutes, about **50 mA or less** for the whole car is the usual rule;
  newer cars 50–85 mA; full sleep can take up to two hours
  ([Vehicle Service Pros](https://www.vehicleservicepros.com/service-repair/battery-and-electrical/article/10775094/no-start-engine-and-how-to-test-for-parasitic-battery-drain),
  [ASE T6 guide](https://open-exam-prep.com/study-guides/ase-t6/circuit-faults-protection-relays/parasitic-drain-circuit-protection)).
  The 50 mA is the car's own allowance; an add-on should take a small slice of it.
- **The hardware note's table is stale** ([hardware.md](hardware.md), "Parked current draw"): it lists the
  guardian, CarPiHAT and WiCAN (about 1–4 mA) but not the diagnostic-port node, which now runs
  from the car battery (ADR-0032).

**Proposed node parked modes** (figures are at 12 V, board level, for the bench to confirm):

| Mode | What stays up | Reachable by | Target |
|---|---|---|---|
| **Parked, ready** | auto light sleep; BLE advertising slowly; Wi-Fi AP or client at a long DTIM; the parked broker; RTC; wake wires, IMU and ignition armed | phone (BLE, AP), modules, node 4G if fitted (U: modem PSM/eDRX latency) | **≤ 5 mA** |
| **Parked, deep** | deep sleep; ignition, door, IMU, wake wire and CAN-transceiver wake on RTC GPIOs; timer check-in | wires, timer, modem ring line only; **no phone, no broker** | **≤ 0.5 mA** |

- Staged like OVMS: ready for a set time (proposed 72 h) or until a budget or a floor is hit,
  then deep. A daily **energy ledger** (node parked current from an INA226-class monitor, plus
  every wake's estimated cost) drives it.
- **Proposed default budget:** Ostler averages **≤ 10 mA** parked (240 mAh a day), a fifth of
  the 50 mA norm: the node ready at 3–5 mA leaves room for about four to five brain wakes a day.
- **Floors** (resting 12 V, temperature compensation U): **12.2 V** soft (no background or
  scheduled wakes), **12.0 V** brain (no brain wakes; an awake brain is shut down), **11.8 V**
  deep (node to parked-deep, alarm inputs only). These extend the hardware note's 12.0/11.8 V.

## 7. Wake paths and their latency

| Path | From → to | Wake latency to first message | Selective? | Cost while waiting |
|---|---|---|---|---|
| Brain power switch | node → brain | boot 15–20 s OS; 25–40 s served (U) | yes | 0 (supply cut) |
| Wake wire (shared open drain) | any → all wired modules | ≤ 500 ms target (ADR-0026 bench) | **no**: all wake, then filter | µA (pull-up) |
| CAN selective wake | node → one CAN module | ms + MCU boot + reconnect | **yes** | < 64 µA transceiver |
| TC10 wake pulse | any → T1S segment | ≤ 17 ms PHY + boot + TLS reconnect | **no** | ≈ 42 µA PHY (U board) |
| Wi-Fi, module in auto light sleep | node → module | one DTIM (≈ 0.1–1 s) | yes | 1–2.5 mA chip |
| Wi-Fi or BLE module in deep sleep | none: waits for its check-in | up to the check-in period | n/a | µA |
| BLE to the node | phone → node (ready) | ≈ 1–2 s connect + auth (U) | yes | inside the ready budget |
| Cloud → node | uplink holder → node | 4G paging, PSM/eDRX dependent (U) | yes | modem sleep (U) |
| Wake-on-LAN | — | n/a | — | not used |

TLS reconnect after a wake costs a handshake (≈ 25–30 kB heap, about a second on an ESP32-S3,
U); session resumption would cut it (U: ESP-TLS support on the module side).

## 8. Gaps and what to bench

1. Node board current in parked-ready (BLE + Wi-Fi DTIM + broker) and parked-deep, at 12 V.
2. Pi 5 boot to "Ostler served" with the real image; shutdown time; the 60 s cut.
3. Wake wire to first MQTT message (ADR-0026), and CAN selective wake on a TJA1145A board.
4. Espressif Mosquitto port: persistent sessions, message expiry, queue bounds (U).
5. SIM7670G PSM/eDRX paging latency for a cloud wake; current in each.
6. TC10 on LAN8651 with the March 2026 helpers, if ported; NCN26010 TC10 status.
7. A stuck wake wire: detection time and masking.

## Changelog

- 2026-10-06: v0.1, first draft from live checks for the owner's wake request; feeds
  ADR-0040 (draft) and the proposed amendments to the UI and app-model specs.
