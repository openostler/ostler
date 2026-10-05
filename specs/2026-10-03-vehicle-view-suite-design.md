---
title: "Vehicle-view diagnostic suite — Design"
area: specs
status: draft
version: 1.1
updated: 2026-10-05
depends_on: [specs/2026-10-01-web-ui-design.md, references/menus/bcu-inputs.md, references/nanocom/feature_map.md]
summary: >
  Grow the dashboard into a diagnostic suite where each module has an elegant vehicle-view
  page drawn on one shared Discovery 2 silhouette (VehicleBase), overlaid with live status —
  starting with a Body/BCU page. Rendered on the Drive tab per module; honest when undecoded;
  lightly animated in mock.
---

# Vehicle-view diagnostic suite — Design

## Goal

Extend the loved SLABS Drive page (`SlabsCar.tsx` — a top-down Discovery with live per-wheel
overlays) into a **suite**: one shared **VehicleBase** silhouette that each module overlays
with its own live status — **Body (BCU)**, **Airbag**, **Auto gearbox**, with SLABS refactored
onto the same base. The suite should read as one calm, elegant system.

## Design language

Lean into the existing ISA-101 "calm instrument" rules (neutral when healthy, colour only for
abnormal, with an icon + word) — which already match the **Polestar/Scandinavian minimalism**
and **Tesla Service Mode** patterns surveyed: a vehicle schematic with live status overlaid,
glanceable, low cognitive load, one signature accent. No new palette; reuse the
`--ok/--warn/--alarm/--accent` tokens (light + dark), validated with the dataviz palette check.

## Decisions (locked)

| Decision | Choice |
|---|---|
| Navigation | Vehicle view on the **Drive tab per active module** (reuses the module picker; no new tabs) |
| Shared base | One `VehicleBase` SVG (top-down Discovery; optional side/front insets) with **named zones** |
| Bindings | Each module's **zone → signal** map lives in `ui/src/layout.ts` (the only place the UI names signals) |
| Honesty | A zone with no decoded signal shows **neutral "awaiting mapping"**; never a fabricated state |
| Mock | In mock mode only, a light generator animates a few states so the demo looks alive (clearly mock) |
| First page | **Body (BCU)** |

## Architecture

```
VehicleBase (SVG silhouette + named anchor zones: doors, bonnet, tailgate, 4 corners/lamps,
             windscreen, cabin, seats)  ── reused by ──▶ BodyCar / AirbagCar / GearboxCar / SlabsCar
Drive.tsx  ── by active module ──▶ renders the matching vehicle view
layout.ts  ── per module ──▶ ZONES: [{ id, label, signal, kind }]  (boolean | level | numeric)
snapshot.signals ── value + confidence (c) per signal ──▶ zone state: on/off/—, ok/warn/alarm, candidate
```

- **VehicleBase** draws the body and exposes zone slots; overlays position indicators/readouts
  at zone anchors, exactly as `SlabsCar` places wheel overlays today.
- A zone is **active/inactive/absent**: active (e.g. door open, lamp on) → accent/alarm per
  semantics; inactive → neutral; **absent** (signal not in the snapshot) → dashed "awaiting
  mapping" with the confidence dot. Numeric zones (voltages, temps) reuse `RangeBar`/`Value`.
- **Confidence** comes from the signal's `c` (proven/candidate); candidate/mock zones carry a
  small marker so the viewer never mistakes demo state for a proven reading.

## Body (BCU) page — the first slice

Zones driven by the BCU read-inputs ([menus/bcu-inputs.md](../references/menus/bcu-inputs.md)):
- **Doors/openings:** driver, passenger, (rear ×2 if present), bonnet, tailgate → open/closed.
- **Lamps:** side, main beam, dipped, front/rear fog, left/right indicator, hazard, brake,
  reverse → lit when on.
- **Windows:** front L/R up/down. **Wash/wipe:** front/rear wiper + wash. **Heated screen.**
- **Ignition/supply (readouts):** ignition position, battery/supply volts (numeric).

In **mock**, a generator gently toggles a few (a door opens, indicators blink, ignition on).
In **live with no decode**, all zones are neutral "awaiting mapping" until sniffed (run-sheet).

## Later slices (same base)
- **Airbag/SRS:** airbag + pretensioner zones (driver/passenger/side/curtain) with per-zone
  fault status (read-only, faults only).
- **EAT (auto gearbox):** PRND selector, oil-temp gauge, turbine/output speed, pressures.
- **SLABS:** refactor `SlabsCar` onto `VehicleBase` for a shared silhouette.
- **TD5:** keep Drive tiles; optional under-bonnet inset.

## Critical files
- New: `ui/src/components/VehicleBase.tsx`, `ui/src/components/BodyCar.tsx` (then
  `AirbagCar.tsx`, `GearboxCar.tsx`).
- Updated: `ui/src/screens/Drive.tsx` (dispatch by module), `ui/src/layout.ts` (zone maps),
  `ui/src/styles.css` (shared vehicle classes), `ui/src/components/SlabsCar.tsx` (later).
- Backend (mock only): `src/d2diag/web/sources.py` — `InfoDataSource` gains an optional mock
  signal generator; `tools/dashboard.py` wires the BCU mock to emit body states.
- Reuse: `SlabsCar.tsx` pattern, `RangeBar`/`StatTile`/`Value`, the feature map + bcu-inputs.

## Verification
- `npm run check` (lint/typecheck/vitest/build) + rebuild `web/static`; `pytest -q`.
- Mock: Drive → BCU shows the body diagram with a few animated states; Drive → a module with
  no vehicle view keeps its current screen; undecoded zones render neutral "awaiting mapping".
- Dataviz `validate_palette.js` if any status hue changes (none expected).

## Out of scope
No new decode/claims — the pages render what the store holds + mock demo. Actuation (output
tests from these pages) stays in the Outputs tab behind `confirm.ts`, unchanged.

## Changelog
- 2026-10-03 — Initial design drafted (research: Tesla Service Mode, Polestar HMI).
- 2026-10-05 — Module display names aligned with the catalog: "EAT (auto gearbox)" and "SRS (airbag)" (internal ids `autobox`, `airbag` unchanged).
