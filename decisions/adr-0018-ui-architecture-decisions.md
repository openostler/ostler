---
title: "ADR-0018 — UI architecture decisions"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/ovms_ui.md, references/research/ui/head_unit_ui.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md]
summary: >
  Records the owner's answers to UI spec §11 Q2–Q11 (Q1 is ADR-0016): canonical function areas with pack labels, a driver-side rail, a comfort class only for our own add-ons that never write to a vehicle ECU, unknown speed counts as Moving on head units, three rendering tiers with user-arranged dashboards deferred, an HMAC fingerprint and masked VIN only, service mode by long-press plus password, reverse pre-emption only after the fast path, guardian before generic_obd2, and a non-runnable write tier. Also the OVMS lessons (capabilities as data, no vehicle-type checks) and 360 cameras as a future item.
---

# ADR-0018 — UI architecture decisions

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06: "yes" to every recommended answer in UI spec
  §11). It approves [the UI architecture spec](../specs/2026-10-06-ui-architecture-design.md)
  v0.2, which holds the detail. Each migration phase still gets its own spec.

## Context

The UI spec drafted one head-unit-first UI generated from a per-vehicle capability
manifest, and left eleven questions for the owner. Q1 (the signal namespace) is
[ADR-0016](adr-0016-covesa-vss-canonical-signal-namespace.md). This ADR locks Q2–Q11 so
later phase specs do not reopen them.

## Decision drivers

- One UI for every vehicle, with no vehicle-type checks in screens.
- Driver safety on head units: the server gates, the UI only adds friction.
- Data honesty and VIN privacy.
- The rule of two: no abstraction before a second user of it.

## Decision

| # | Decision | Spec |
|---|---|---|
| Q2 | **Canonical function areas** (Overview · Faults · Live · Tests · Procedures · Settings) with **pack labels**; the D2 still reads Inputs / Outputs / Utilities | §3.4, §4.2 |
| Q3 | Landscape classes use a **rail on the driver's side**, from the vehicle's `driver_side` (right for the D2); the kiosk flag overrides; portrait uses a bottom bar | §3.3 |
| Q4 | A **`comfort` class** exists **only for our own add-on devices whose actions never write to a vehicle ECU** (HEVAC setpoints, camera switching). It is allowed while Moving, not remote by default, and still passes the server gate. Any action that reaches a vehicle bus or ECU keeps the five tiers | §6, §7 |
| Q5 | **Unknown speed counts as Moving** on head-unit classes. On phones reading stays open and actions keep the "vehicle stationary" precondition | §3.5 |
| Q6 | **Three rendering tiers** (generated, pack-declared, custom). User-arranged dashboards are **deferred**, and may come only as a per-vehicle diff over the tiers. No remote layout server, no runtime- or model-composed screens | §5.3 |
| Q7 | The garage stores an **HMAC fingerprint** (device-local secret) and a **masked VIN** only, never the full VIN, even locally | §4.1, §4.4 |
| Q8 | **Service mode** is entered by a long-press on the version line (More → About) plus the server password, with a frame and strip badge; it is refused and exits when Moving. `/admin` stays on **desktop for one release**, then goes | §3.5 |
| Q9 | **Reverse-camera pre-emption only after the fast path exists** (direction spec); assist-only until then | §6 |
| Q10 | **The guardian (U5) comes before `generic_obd2` (U4)**; `generateViews()` is built only together with `generic_obd2` | §10 |
| Q11 | **Tier 4 (write/coding/security) is listed for honesty and never runnable**; any write path needs its own ADR | §7 |

**Cameras, future.** The owner added: "in future we'll think about 360 cameras etc".
360° surround view is recorded as a **future camera kind**, not a commitment. When it
comes it registers as a camera device in the same slots and keeps the same rules (live
below 10 km/h, no playback unless Parked, pre-emption only after the fast path), and it
needs its own spec.

**OVMS lessons, adopted** ([OVMS UI §6](../references/research/ui/ovms_ui.md)):
- **Capabilities reach the UI as data**: a versioned manifest (`schema`, `etag`) built by
  the platform. OVMS never sent capabilities, and its app branches on `car_type`.
- **Screens never test a vehicle type**, pack, module or device id. The literal guard
  (`ui/src/vehicles/literalGuard.test.ts`) extends to "no pack, module or device ids
  outside `ui/src/vehicles/`".
- Destinations and pages **register** into the shell (`slot`, `order`, `requires`,
  `trust`), as OVMS pages do; opt-in shared page templates and named hook slots are copied
  as designs.

## Confirmation

- The literal guard and view snapshot tests (no vehicle-type branches).
- Playwright at 1024×600, 1280×720, 1920×720 and 393×852, with target-size asserts (U1).
- Server tests: Tiers 1–3 refused while Moving or with unknown speed on a head unit; Tier
  4 always refused; comfort actions refused if they target a vehicle bus (U2).
- A test that no full VIN reaches the garage, logs or fixtures (U4, U6).

## Consequences

- The spec moves to approved (v0.2). U0 can start; U1–U7 each need a phase spec.
- The comfort class needs a field on device actions in the manifest schema (U5).
- Removing `/admin` is scheduled one release after U2 ships service mode.

## Alternatives considered

- **NanoCom names everywhere (Q2).** Rejected: they mean nothing on other vehicles.
- **Comfort for vehicle actions (Q4).** Rejected: anything touching an ECU keeps the tiers.
- **User-arranged dashboards now (Q6).** Rejected: they fork per user before the
  generated tier exists.
