---
title: "Vehicle integration roadmap — Design"
area: specs
status: draft
version: 1.1
updated: 2026-10-06
depends_on: [SCOPE.md, CONSTITUTION.md, hardware/README.md]
summary: >
  Umbrella plan for the next wave of Discovery 2 projects beyond diagnostics — CAN
  emulation for head units, fast RPM/speed signal taps, HEVAC control, GPS tracking,
  alarm integration, remote disarm and remote start. States the scope expansion, the
  shared hardware platform, the two power domains, and the phased development order,
  with the per-feature ADR + safety gate each one needs before implementation.
---

# Vehicle integration roadmap — Design

> **2026-10-06:** the wider direction now lives in
> [2026-10-06-platform-direction-design.md](2026-10-06-platform-direction-design.md) (draft).
> HEVAC control (spec #3) **moves to a separate ESP32 project**; this repo only talks to it.
> The hardware platform is revised in
> [references/research/hardware.md](../references/research/hardware.md): an ESP32 guardian
> with Linux on demand, built from an off-the-shelf development kit first.

## Why this exists

The diagnostics core (COMMS + INTERPRETATION over K-line) is established and the hosted
mock viewer is deployed. The owner wants to extend the Discovery 2 work into a set of
**control and integration** features. These are a new category for the project: most are
**actuation** or **security writes**, not read-only diagnostics, so each one must clear
the constitution's safety gate and carry its own ADR before any code or wiring.

This doc is the map: the feature set, the shared hardware, and the order to build in. It
does not implement anything — it points at the per-feature design specs, which are each
`status: draft` until approved.

## Scope expansion (needs an explicit decision)

`SCOPE.md` defines the core mission as *communication with the car and interpretation of
its data*, with storage/presentation as consumers. The features below add a third
category — **vehicle integration/actuation** — that `SCOPE.md` does not yet cover. Before
building, `SCOPE.md` should be amended (or an ADR raised) to admit this category and
restate the hard rules for it:

- The diagnostics **core never depends on these integration subsystems** (one-way data
  flow is preserved; they are consumers/peers, not imported by `transport/kline/kwp2000`).
- Every **write, coding, SecurityAccess or actuation** path stays behind an explicit gate
  and its own ADR (CONSTITUTION → Safety; ADR-0005 precedent).
- **Airbag/SRS remains read-only by construction** — untouched by any of this.

## The feature set and their specs

| # | Feature | Spec | Risk | Core relationship |
|---|---------|------|------|-------------------|
| 1 | Hardware platform (compute + power domains) | `2026-10-02-hardware-platform-design.md` | low | foundation |
| 2 | CAN emulation (head units) + fast RPM/speed taps | `2026-10-02-canbus-and-fast-signals-design.md` | med | new output + new read |
| 3 | HEVAC (climate) control | `2026-10-02-hevac-control-design.md` | med | actuation (panel) |
| 4 | GPS tracker + alarm integration + remote disarm | `2026-10-02-gps-tracker-alarm-design.md` | **high** | security write |
| 5 | Remote start | `2026-10-02-remote-start-design.md` | **highest** | security + safety-critical |

## Shared hardware platform (summary — detail in spec #1)

One system, **two power domains**, so the thirsty brain is off when parked while the lean
always-on subsystem protects the battery:

```
KL15 (ignition-switched)            CONSTANT 12V (+ low-voltage cutoff)
┌─────────────────────────┐        ┌───────────────────────────────┐
│ Pi (brain)              │        │ Tracker ESP32 (deep-sleep)    │
│  Python d2diag + React  │        │  GPS + LTE-M + accelerometer  │
│  CAN emit (optional)    │        │  alarm signal taps            │
│ RP2040/Pico (real-time) │        │  fob-emulation (disarm)       │
│  K-line timing, CAN,    │        │  remote-start relays + bypass │
│  I2C sniff, pulse count │        │  (behind auth + interlocks)   │
└─────────────────────────┘        └───────────────────────────────┘
```

Rationale: no single chip is best at both "Linux app/React/Python" and "hard-real-time
K-line/CAN/I2C/pulses/low-power tracking." The Pi runs the existing stack unchanged; the
MCUs do the deterministic I/O and the always-on jobs. GPS is shared (parked position +
a driving speed source).

## Planned development order

Build foundation-first, lowest-risk-first, and never wire a security/actuation feature
before its ADR is approved and its safety design reviewed.

- **Phase A — platform.** Spec #1. Bring up the Pi + Pico, power domains, and the proven
  L9637D K-line front-end on the new board. No new vehicle behaviour.
- **Phase B — read-only additions.** Fast RPM/speed pulse taps (spec #2, read half) and
  the HEVAC *display sniff* (spec #3, read half). Pure observation — low risk, high value,
  feeds the existing dashboard.
- **Phase C — benign output.** CAN emulation to a bench head unit (spec #2, write half),
  on an isolated bus. No effect on the car's own systems.
- **Phase D — HEVAC control.** Button-injection (spec #3, write half). Actuation of the
  climate panel only; the HEVAC controller still governs the system. ADR required.
- **Phase E — tracker + alarm (read) + remote disarm.** Spec #4. GPS/cellular + alarm
  signal taps first (read-only), then the authenticated, fail-secure fob-emulation disarm.
  ADR + threat model required before the disarm path is wired.
- **Phase F — remote start.** Spec #5. Only after D/E are proven. Transponder-present
  bypass + full safety-interlock + fail-secure design. ADR + safety review mandatory.

## Cross-cutting rules for every feature here

- **Design before code:** each spec is approved (and its ADR raised) before implementation.
- **Fail-secure:** on power loss, comms loss or any error, the vehicle defaults to the
  safe state — alarm armed, immobiliser intact, engine off, doors locked.
- **Authenticated commands:** disarm/start are never plain endpoints — authenticated TLS,
  signed commands, app behind real auth, and ideally a second factor for drive-relevant
  actions. Every arm/disarm/start event is logged (private, per the data-honesty rule).
- **Confirm on the car:** each spec lists the 🔴/🟡 items to verify against the real D2
  (wiring, BCU behaviour) before trusting them.

## Open questions

- Does the owner want the amended `SCOPE.md` category, or a standalone "integration"
  sub-project/repo? (Keeps the diagnostics core clean either way.)
- Manual vs automatic transmission on the target car — decisive for remote start (spec #5).
- Cellular carrier/plan and coverage for the tracker (spec #4).

## Changelog

- 2026-10-02 — Initial roadmap drafted from the hardware/architecture design conversation.
- 2026-10-06: v1.1, points at the platform direction spec; HEVAC moves out of scope.
