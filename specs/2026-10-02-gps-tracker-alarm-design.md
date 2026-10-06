---
title: "GPS tracker + alarm integration + remote disarm — Design"
area: specs
status: draft
version: 1.1
updated: 2026-10-06
depends_on: [specs/2026-10-02-hardware-platform-design.md, docs/discovery-2-td5/bcu.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0037-role-holders-and-handover.md]
summary: >
  An always-on, low-power subsystem that reports GPS position, detects alarm/security
  events by tapping the BCU's physical signals (car off), and performs an authenticated,
  fail-secure remote disarm by emulating a paired RF fob. Covers the car-off constraints,
  hardware, the security threat model, and the phased plan. Superseded in part (2026-10-06):
  the GNSS and modem hardware follow ADR-0032 and ADR-0037 (guardian SIM7670G GNSS for
  security tracking; a 10 Hz u-blox for drive logging, placement pending).
---

# GPS tracker + alarm integration + remote disarm — Design

> **Superseded in part (2026-10-06).** The GNSS and modem hardware below (u-blox NEO-M8N/M9N
> on the tracker, SIM7080G) is replaced by the GPS split of
> [ADR-0032](../decisions/adr-0032-one-node-optional-brain.md) (Amendments) and the time
> role of [ADR-0037](../decisions/adr-0037-role-holders-and-handover.md): the **guardian's
> SIM7670G** GNSS (1 Hz) and modem do security tracking, geofences and check-ins; a **10 Hz
> u-blox** on the node or the "Ostler Diagnostics" OBD-port node does drive logging and the
> speed cross-check, its **placement pending (product-family research)**; time is served by
> the time-role holder, best clock first. The remote-disarm and threat-model sections stand
> as a draft and still need their own ADR (ADR-0033 §7).

## Goal

Integrate the Discovery 2's security with a GPS tracking app: report position, raise alerts
when the alarm triggers or the car is moved, and allow an **authenticated remote disarm** —
all while the car is **off and parked**.

## Car-off constraints (decisive)

- The **alarm/BCU is always powered**, so the security system is alive when parked.
- But the **BCU will not attach over K-line with the ignition off** — it requires ignition
  cycling to attach (`docs/discovery-2-td5/kline/physical-and-init.md`). So **do not poll
  the diagnostic bus while parked** (🟡 — confirm on the car).
- Therefore alarm state is read by **tapping physical signals**, not the bus; and the whole
  subsystem must run on **constant 12 V** (not the KL15 brain domain), so it needs
  deliberate low-power design + a low-voltage cutoff (see platform spec).

## Read side — alarm/security via signal taps

Tap always-live BCU signals (level-shifted / opto-isolated):

- Door switches + bonnet switch (BCU inputs, `docs/discovery-2-td5/bcu.md`) → entry events.
- Siren drive and/or indicator-hazard flash output → "alarm triggered."
- Accelerometer (LIS3DH) wake-on-motion → "car moved/towed," and the power-saving wake.

These need no bus init and work car-off.

## GPS + reporting

- **GPS/GNSS:** u-blox NEO-M8N/M9N over UART + sky-view antenna (also a cross-check speed
  source for the CAN/fast-signals spec).
- **Remote link:** LTE-M/NB-IoT modem (SIM7080G) + SIM for reporting when away from home
  WiFi; WiFi-only is acceptable if "still on the drive" is all that's needed.
- **Power:** deep-sleep MCU (ESP32 ~10 µA) + wake-on-motion/timer + periodic check-in →
  weeks of parked life; low-voltage cutoff protects cranking voltage.

## Remote disarm — emulate a paired fob (no crypto RE)

The BCU already trusts the RF fob's rolling code, so the safe method is to **press a real,
paired fob**, not to reverse-engineer the code:

- Mount a **spare paired fob** (project already supports BCU key programming, ADR-0007) near
  the RF receiver, wired-powered, with an **opto across its "unlock" button**, driven by the
  tracker MCU. Arm = the "lock" button. Confirm via the alarm-output taps and report state.
- **Alarm ≠ immobiliser:** fob-unlock disarms/opens but the engine still needs the
  transponder key present (immobiliser), so remote disarm **cannot enable a drive-away**.
  Keep it that way — do not defeat the immobiliser here (see the remote-start spec for the
  controlled bypass).

### Rejected alternatives

- RF rolling-code cloning/replay — hard (KeeLoq-class), fragile, and the literal theft
  technique. The fob-press approach achieves disarm without it.
- Forcing raw door-unlock microswitches — may unlock without fully disarming; wrong channel.
- K-line diagnostic disarm — can't attach parked; not a remote path.

## Security threat model (this is a new unlock path)

Remote disarm is a security write — a weak design turns this project into the theft tool.
Non-negotiables (CONSTITUTION → Safety; requires its own ADR):

- **Strong auth** on the disarm command — authenticated TLS, signed commands, app behind
  real auth, ideally a second factor. Never a plain endpoint.
- **Fail-secure:** power/comms loss or any error → stays **armed**. Disarm only on explicit
  authenticated command.
- **Immobiliser untouched** (the fob method guarantees this).
- **Hide the spare fob** — anyone who finds it has a paired remote.
- **Log** every arm/disarm with who/when (private, per data-honesty rule).

## Hardware

Dedicated tracker **ESP32** (deep-sleep) on constant 12 V + LVC: GPS module, LTE-M modem +
SIM, LIS3DH, opto/level-shifted taps on door/bonnet/siren/indicator, and the fob-unlock opto.

## Planned development

- **E1 (read-only):** tracker ESP32 bring-up; GPS fix + cellular/WiFi check-in; alarm
  signal taps → events to the app; accelerometer motion alert. Verify parked current.
- **E2 (disarm, gated, after ADR + threat model):** spare fob + unlock opto; authenticated,
  fail-secure disarm; confirm via output taps; full event logging.

## Open questions / confirm (RAVE / car)

- That the BCU won't attach over K-line with ignition off (don't depend on it).
- Exact door/bonnet/siren/indicator wires at the BCU, and the RF receiver location.
- Cellular carrier/plan + coverage; privacy/retention of location data.

## Changelog

- 2026-10-02 — Initial design drafted from the GPS/alarm/remote-disarm conversation.
- 2026-10-06 — v1.1: superseded in part by ADR-0032 (GPS split) and ADR-0037 (time role);
  a note at the top records the new GNSS and modem split; u-blox placement pending.
