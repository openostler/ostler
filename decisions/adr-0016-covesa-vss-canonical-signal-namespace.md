---
title: "ADR-0016 — COVESA VSS as the canonical signal namespace"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/standards.md, references/research/ui/vehicle_data_model.md, references/research/ovms_reuse.md, decisions/adr-0002-layered-stdlib-core.md]
summary: >
  The canonical id of a vehicle meaning is a COVESA VSS path, pinned to VSS 6.1. One overlay, vss/ostler.vspec, is the single source: it adds the Vehicle.Ostler.* extension branch and carries the OVMS, Home Assistant and OBDb alias attributes. src/openostler/metrics.json is generated from it with vss-tools (dev-only) and checked in CI. Unit keys are copied verbatim from the pinned release and checked by a test; QUDT, not UCUM; the extension branch is Vehicle.Ostler.*. Supersedes the OVMS-canonical recommendation in references/research/platform.md (research, not an ADR).
---

# ADR-0016 — COVESA VSS as the canonical signal namespace

- **Date:** 2026-10-06
- **Status:** accepted (owner decision, 2026-10-06, UI spec §11 Q1)

## Context

- Nothing in the platform says that `td5.rpm` and OBD PID `0x0C` are the same meaning
  ([vehicle data model](../references/research/ui/vehicle_data_model.md)). Home roles,
  MQTT/Home Assistant export and the generated UI all need one shared name per meaning.
- [Platform research](../references/research/platform.md) recommended OVMS metric names.
  OVMS is EV-shaped: it has no names for fuel, oil or coolant, and its ICE modules store
  fuel level in `v.b.soc` ([OVMS reuse §6](../references/research/ovms_reuse.md)).
- COVESA VSS covers powertrain, body and cabin, is OEM-backed and MPL-2.0. In 6.0 it
  dropped the one-to-one OBD branch, which matches our "one meaning, many sources" model
  ([standards §1](../references/research/standards.md)).
- The owner: "yes Covesa, and on that try and use standard and open frameworks where
  possible" (see [ADR-0017](adr-0017-open-standards-first.md)).

## Decision drivers

- One name per meaning across every vehicle class, including ICE and pre-OBD cars.
- An open, maintained standard rather than a bespoke or EV-only tree.
- No new runtime dependency on the Pi ([ADR-0002](adr-0002-layered-stdlib-core.md)).
- One source file for every alias, so nothing is hand-kept twice.

## Decision

**The `metric` value on a signal is a COVESA VSS path.** It stays optional: a
pack-private field needs no metric, and adding one never blocks a field.

**VSS is pinned to release 6.1.**
- `vss/VERSION` holds `6.1`; the release JSON is vendored under `vss/upstream/` with its
  MPL-2.0 notice (marked MPL-2.0 in `REUSE.toml`).
- Moving the pin is its own PR, with a `vspec diff` and a migration note for any renamed
  or removed path a pack uses.

**`vss/ostler.vspec` is the single source** (CC BY-SA 4.0, like pack data).
- It adds the extension branch **`Vehicle.Ostler.*`** for meanings VSS lacks (MIL, DTC
  count, readiness, ride-height counts, guardian state).
- It annotates existing VSS nodes with our attributes: `ostler_role`, `ovms`,
  `ha_device_class`, `ha_state_class`, `obdb`.
- Packs do not ship overlays. A pack meaning that must be exported but has no VSS node
  gets a reviewed `Vehicle.Ostler.<Domain>.*` entry in this one file.

**`src/openostler/metrics.json` is generated, committed and checked.**
- CI runs `vspec export json` (vss-tools, MPL-2.0, Python ≥ 3.11) over the pinned release
  plus the overlay, then `tools/build_metrics.py` writes `metrics.json`.
- vss-tools is a **dev-only** dependency. The Pi reads only the committed JSON, so the
  runtime stays stdlib plus pyserial.

**OVMS, Home Assistant and OBDb names are generated aliases**, never canonical.
- The OVMS→VSS table is built from OVMS `main/metrics_standard.cpp` at a pinned OVMS
  SHA, mapped by hand ([OVMS reuse §6](../references/research/ovms_reuse.md)): about
  80–90 of 169 vehicle metrics have a direct VSS leaf; the rest become `Vehicle.Ostler.*`
  or stay unmapped.
- The reverse map (VSS→OVMS, for publishing the OVMS topic tree) is one-way and lossy. It
  never publishes fuel as `v.b.soc`, and `v.m.*` means the motor, not the engine.

**Units.**
- Unit keys are copied **verbatim** from the pinned release's `units.yaml`. In 6.1 the
  temperature key is `Celsius` (checked against the v6.1 tag on 2026-10-05).
- A pytest fails on any `unit` in the overlay, `metrics.json` or a pack field mapped to a
  metric that is not a key in the pinned file.
- Unit semantics and conversions follow **QUDT**, reached through the VSS unit references.
  **UCUM is not used**: its licence forbids derivative works.
- Store and send in the VSS unit; the UI formats with `Intl`; integration edges convert
  (knots for OsmAnd).

**Extension branch name: `Vehicle.Ostler.*`** (owner, 2026-10-06), not a neutral
`Vehicle.Private.*`. VSS sets no naming rule for private branches.

**Supersedes** the "use OVMS names" recommendation in `references/research/platform.md`
§1. That file is research, not an ADR, so no ADR changes status.

## Confirmation

- A CI job regenerates `metrics.json` and fails if the committed file differs.
- Pytest: every pack `metric` resolves in `metrics.json`; every unit is in the pinned
  `units.yaml`; every `ovms` alias is unique; no alias maps fuel to `v.b.soc`.

## Consequences

- U0 gains `vss/`, the overlay and `metrics.json` before any pack fills `metric`.
- Drivers never see the long paths: the UI keys on roles and labels.
- VISS, KUKSA and other VSS tools become possible interop later, without being needed.
- A VSS upgrade can rename paths; the pin and the diff step keep that deliberate.

## Alternatives considered

- **OVMS metric names as canonical.** Rejected: EV-shaped, no ICE or body names, and a
  de facto layout rather than a maintained spec. Kept as an alias.
- **Our own tree.** Rejected: bespoke, and every integration would need a mapping anyway.
- **Home Assistant device classes.** Rejected: classes, not meanings (two temperatures
  share one class).
- **Run vss-tools on the device.** Rejected: Python ≥ 3.11 and extra packages on the Pi.
