---
title: "CAN emulation + fast RPM/speed signals — Design"
area: specs
status: draft
version: 1.0
updated: 2026-10-02
depends_on: [specs/2026-10-02-hardware-platform-design.md, docs/discovery-2-td5/system-map.md]
summary: >
  Two related additions: emulating a CAN message stream to drive an aftermarket head unit,
  and tapping the instrument-cluster tacho/speed pulse signals for fast RPM/road-speed
  without polling the K-line. Covers CAN controller/transceiver choice, bus termination,
  the opto-isolated pulse taps, and the phased plan.
---

# CAN emulation + fast RPM/speed signals — Design

## Goal

1. **CAN emulation** — generate the CAN messages an aftermarket head unit (or its CANbus
   interface box) expects for a chosen vehicle profile: road speed, reverse, illumination/
   dimmer, steering-wheel controls, handbrake.
2. **Fast RPM/speed** — obtain instantaneous engine RPM and road speed by tapping the
   cluster's pulse signals, far faster than polling `21 09` (RPM) over the shared K-line.

Both are new, physically separate from the diagnostic bus, and feed the existing snapshot/
dashboard as additional signals.

## Context from the car

- The D2 Td5 diagnostic path is K-line only; RPM is proven at `21 09` (0–4800) but
  **polled = slow**. Road speed is "measured by the instrument cluster via the BCU, not the
  ECM" (`docs/discovery-2-td5/engine-td5.md`). So fast, high-rate values want a **pulse
  tap**, not the bus.
- The Td5 feature config even lists a "CAN Bus" capability, but inter-module CAN is not the
  target here — the CAN we generate is a **dedicated bus to the head unit**, not the car's.

## CAN: controller + transceiver

A CAN transceiver is only the PHY; it needs a controller driving it.

| Platform | Controllers | Notes |
|----------|-------------|-------|
| ESP32/-S3 | 1× TWAI (classic CAN 2.0) | enough for one head-unit feed; already footprinted |
| RP2040 | can2040 via PIO (classic CAN) | one bus, software controller, needs only a PHY |
| Teensy 4.x | 3× FlexCAN incl. CAN-FD | if ≥2 buses / FD needed |
| Pi + HAT | MCP2515 / MCP2518FD → SocketCAN | easiest software (`python-can`) |

- **Transceiver:** SN65HVD230 (3.3 V classic) for a 500 k head-unit bus; TCAN1042 /
  MCP2558FD if CAN-FD headroom is wanted.
- **Termination gotcha:** this is a **bus we build** (emulator ↔ head unit = 2 nodes), so
  **terminate 120 Ω at each end** (enable the jumper left DNP in `hardware/README.md`).
  This is the opposite of the "don't terminate a live bus you only listen to" rule.
- **Message discipline:** emit at correct cycle times (speed every ~20–100 ms, etc.) for a
  chosen target-vehicle profile the head unit's CAN box supports.

Default: the ESP32-S3's single TWAI (or Pico can2040) is sufficient — one CAN bus. Step to
Teensy/STM32 only if isolating "car side" from "head-unit side" or needing CAN-FD.

## Fast RPM/speed: tap the pulses, count in hardware

Both signals are **frequency ∝ value** pulse trains:

- **Tacho** — the ECM drives an engine-speed square wave to the cluster. Tap → RPM.
- **Road speed** — the cluster/BCU speed feed (D2 derives it via ABS/transfer-box VSS).
  Tap → speed. (GPS speed, from the tracker spec, is a cross-check source.)

Measure with a **hardware pulse counter** — RP2040 PIO or ESP32 PCNT — not in Linux (Pi
scheduler jitter makes clean frequency measurement poor). This is a key reason an MCU sits
in the platform even when the Pi is the brain.

**Input protection (mandatory):** these wires swing 0–12 V. Never into a 3.3 V GPIO —
use a **fast optocoupler (6N137)** for isolation, or at minimum a divider + clamp.

## Integration

New signals (`rpm_fast`, `road_speed`) flow through the normal snapshot contract as
additional fields, with their own confidence tags, consumed by the dashboard like any
other signal. CAN emulation is an output subsystem — it does not feed interpretation.

## Planned development

- **B1 (read, low risk):** wire the opto-isolated tacho + speed taps to the Pico PIO;
  verify frequency→RPM/speed against the K-line `21 09` and the speedo. Add to the snapshot.
- **C1 (output, bench only):** bring up one CAN channel (SN65HVD230) on a **bench head
  unit**, terminated 120 Ω each end; emit a minimal profile (speed + illumination) and
  confirm the unit responds. No connection to any car bus.
- **C2:** expand the emulated profile (reverse, SWC, handbrake); document the target-
  vehicle message set.
- Decide whether CAN emit lives on the Pi (MCP2518FD HAT) or the MCU (TWAI/can2040).

## Open questions / confirm (RAVE / bench)

- Exact cluster-connector pins for the tacho drive and the road-speed feed, and their
  voltage swing.
- Which target-vehicle profile the chosen head-unit CAN box decodes.
- Classic CAN vs CAN-FD, and single vs dual bus.

## Changelog

- 2026-10-02 — Initial design drafted from the CAN/fast-signals conversation.
