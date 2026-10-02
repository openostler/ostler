---
title: "Hardware platform (compute + power domains) — Design"
area: specs
status: draft
version: 1.0
updated: 2026-10-02
depends_on: [hardware/README.md, SCOPE.md, docs/discovery-2-td5/kline/physical-and-init.md]
summary: >
  The shared hardware for the vehicle-integration features: a Pi brain + RP2040 real-time
  co-processor on ignition-switched power, plus an always-on low-power tracker ESP32 on
  constant 12V. Covers why no single chip suffices, the two power domains, the K-line
  front-end reuse, bus-architecture options, and the starter parts list.
---

# Hardware platform (compute + power domains) — Design

## Goal

Pick one coherent hardware base that serves every planned feature (diagnostics, CAN
emulation, fast signals, HEVAC, GPS/alarm, remote start) without the battery drain,
real-time, or SD-corruption pitfalls — and without rewriting the existing Python stack.

## Why not one chip

The jobs pull in two directions:

- **App / React / Python / WiFi UI** → wants a Linux brain (a Pi).
- **Hard real-time** (K-line 25 ms init timing, CAN bit-timing, I2C sniffing, pulse
  counting) and **always-on low-power tracking** → wants a microcontroller.

No single part tops both. So the platform is a **brain + MCU** pairing, split across two
power domains.

## Decision: Pi + RP2040 (+ tracker ESP32)

| Role | Part | Power domain | Runs when |
|------|------|--------------|-----------|
| Brain: Python `d2diag` + React UI + (optional) CAN emit | **Pi Zero 2 W** (or CM4 for eMMC/no-SD) | KL15 (ignition-switched) | key on |
| Real-time I/O: K-line timing, CAN, I2C sniff, pulse count | **RP2040 / Pico** (PIO) | KL15 | key on |
| Always-on: GPS, cellular, accelerometer, alarm taps, fob/relay actuation | **ESP32** (deep-sleep) | **constant 12V + low-voltage cutoff** | car off, parked |

- The **Pi runs the existing stack unchanged** — this maps onto the "WiFi bridge" option
  already noted in `hardware/README.md` (MCU relays bytes; Python stays on the host).
- The **RP2040's PIO** is the universal low-level tool: deterministic K-line pulses,
  I2C sniffing, CAN (can2040), and pulse capture, in parallel.
- The **tracker ESP32** deep-sleeps at ~10 µA and wakes on motion/timer, so it can live on
  the battery for weeks without flattening it; a Pi cannot (idles at ~0.5 W+).

### Single-chip fallback

If starting smaller, an **ESP32-S3 (N16R8, 16 MB flash / 8 MB PSRAM)** is the only single
MCU with WiFi + native CAN (TWAI) + pulse counters (PCNT) + room to serve the ~120 KB
React bundle. Caveats: one CAN bus, and I2C sniffing is its weak area (no PIO) — add a £4
Pico as an I2C/second-CAN sidecar when HEVAC arrives, converging on the pairing above.

## Two power domains (the battery rule)

```
OBD16 / battery +12V ─ PTC ─ reverse P-FET ─ load-dump TVS ─┬─ [constant] buck → tracker ESP32 (+ LVC)
                                                            └─ KL15 fuse → buck → Pi + Pico + K-line/CAN front-ends
```

- **KL15 (ignition-switched)** for the brain + real-time MCU → dead when parked → zero
  parasitic drain. Decided for the ESP32 board in `hardware/README.md`; applies here too.
- **Constant 12V** only for the lean tracker, behind a **low-voltage cutoff** so it can
  never discharge the battery below cranking voltage.
- Automotive power throughout: ≥40 V-input buck (load-dump margin), PTC fuse, reverse-
  polarity P-FET, load-dump TVS (per `hardware/README.md`).

## K-line front-end (reused, proven)

ST **L9637D** transceiver on a UART, **510 Ω–1 kΩ pull-up** to 12 V (critical for bit
timing at 10400 baud), 1N4148 on VS, non-inverting. Verified against the car 2026-08-23
(fast init → `03 C1 57 8F AA`). No change — the Pico/ESP32 drives it exactly as the
existing ESP32 board does.

## Bus architecture note (for reference)

The D2 diagnostic K-line is a single shared half-duplex wire (pin 7) — see
`docs/discovery-2-td5/system-map.md`. Options considered for multi-module live data:

- **Shared-bus TDM (recommended):** keep one bus; hold multiple KWP2000 sessions open with
  `TesterPresent` and interleave addressed polls. No loom surgery. Natural next step from
  today's establish→read→release.
- **Star / active gateway:** split each module onto its own channel for true parallelism —
  only worth the invasive wiring + per-channel transceivers if high-rate simultaneous
  multi-module logging becomes a hard requirement. Deferred.

## Starter parts list

- Brain: Pi Zero 2 W (or CM4 + carrier). Real-time: Raspberry Pi Pico.
- K-line: L9637D (+ SO8→DIP breakout), 510 Ω–1 kΩ 0.5 W pull-up, 1N4148, decoupling.
- CAN: SN65HVD230 (classic) or MCP2518FD (FD/2nd bus) + 120 Ω termination jumper.
- Fast signals: 2× 6N137 optocouplers (tacho + speed) + resistors.
- Tracker: ESP32, u-blox NEO-M8N + antenna, SIM7080G LTE-M + SIM, LIS3DH accelerometer,
  low-voltage-cutoff module.
- HEVAC: 8-ch logic analyzer (FX2/sigrok) for RE; photoMOS relays (AQY21x) / CD4066.
- Power: ≥40 V buck (LMR14030) ×2 domains, PTC, reverse P-FET, load-dump TVS.
- Bench: current-limited 12 V supply (~200 mA) for safe bring-up.

## Planned development

- **A1** Breadboard Pi + Pico, both power domains from a bench supply; verify rails,
  boot, and the Pico↔Pi link.
- **A2** Move the proven L9637D K-line front-end onto the Pico; reproduce fast init and a
  `21 xx` read; cross-check vs the USB-KKL + `d2diag`.
- **A3** Tracker ESP32 bring-up on constant-12V + LVC; confirm deep-sleep current.
- **A4** Decide WiFi-bridge vs standalone firmware split (hardware identical).

## Open questions / confirm

- Pi Zero 2 W (micro-USB OTG for the KKL) vs CM4 (no SD, needs carrier) for the brain.
- Read-only/overlay rootfs vs UPS/supercap for clean shutdown on KL15 power-off.
- Where to physically tap KL15 + constant 12V + ground (fusebox vs OBD breakout).

## Changelog

- 2026-10-02 — Initial platform design drafted from the hardware conversation.
