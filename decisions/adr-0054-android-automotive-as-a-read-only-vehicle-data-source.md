---
title: "ADR-0054 — Android Automotive as a read-only vehicle-data source beside the node"
area: decisions
status: draft
version: 0.1
updated: 2026-10-27
depends_on: [decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, references/research/aaos_vehicle_data.md, references/research/head_unit_experiments.md, CONSTITUTION.md]
summary: >
  Proposed (draft for the owner, 2026-10-27). On cars with Android Automotive OS (Google built-in), an app installed from Play can read a useful standard set through CarPropertyManager: battery level, nominal capacity, charge rate and state, plug state, range, speed, gear, parking brake, outside temperature and display units. It cannot read climate, diagnostics, raw bus frames, per-cell data or anything the maker's VHAL leaves out. Proposal: keep the node and the gateway; add an AAOS source as a read-only adapter that maps properties to VSS paths and publishes to the gateway over VISS, never writes, and never bypasses the node gate. Where a node is fitted its values win and AAOS values become a cross-check. Apps may also read AAOS directly when no gateway is present (the trip calculator first). ADR-0049's "the node stays the only path to the car" would be read as "the only write path", with read-only platform sources allowed. Staged: S1 the trip calculator reads AAOS directly; S2 an AAOS source in the gateway app; S3 node and AAOS side by side. First step: a property census on the owner's 2021 XC40.
---

# ADR-0054 — Android Automotive as a read-only vehicle-data source beside the node

- **Date:** 2026-10-27
- **Status:** **proposed** (draft for the owner). Nothing changes until the owner approves.
- **With:** [ADR-0049](adr-0049-open-vehicle-data-standard-and-app-suite.md) (the node stays
  the only path to the car; Android Automotive as reference and a parked track),
  [ADR-0051](adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md) (VISS v3 on every
  hop), [ADR-0044](adr-0044-adapters-on-the-brain-without-a-node.md) (third-party adapters,
  read-only by default), [ADR-0050](adr-0050-kotlin-for-the-android-app-tier.md) (Kotlin
  for Android apps).
- **Research:** [AAOS vehicle data](../references/research/aaos_vehicle_data.md).

## Context

- The owner's second car, a 2021 Volvo XC40 Recharge P8, runs Android Automotive OS with
  Google built-in. The owner is building a trip calculator (cruise speed against charging
  time and cost) that would be better with live battery and charging data, and asked
  whether AAOS can supply it directly, whether the Ostler bridge is then needed, or
  whether it stays to publish data to MQTT and other outputs.
- Ostler's model today: the **node** is the only path to the car's buses and its gate
  decides every write (ADR-0049 §3, CONSTITUTION). The gateway serves VISS; MQTT is an
  output only.
- The research found that a Play-distributed AAOS app can read, with install-time or
  user-granted permissions: `EV_BATTERY_LEVEL`, `INFO_EV_BATTERY_CAPACITY`,
  `EV_BATTERY_INSTANTANEOUS_CHARGE_RATE`, charge state and time remaining, charge-port
  connected, `RANGE_REMAINING`, `PERF_VEHICLE_SPEED`, gear, parking brake,
  `ENV_OUTSIDE_TEMPERATURE` and display units. Climate needs a privileged permission;
  diagnostics (DTCs, UDS) are privileged; raw CAN and per-cell data are not exposed at all;
  odometer needs a newer permission that may not reach the XC40's AAOS 13. What a given
  car really offers depends on the maker's VHAL and is not published.
- A templated car app (POI category) is the only Play route for the calculator's driving
  UI; custom screens are allowed only when parked.

## Decision drivers

- Work on a car with no Ostler hardware fitted, using what the car already shares.
- Keep the safety model whole: one write path, through the node gate.
- One vocabulary: VSS paths, whatever the source.
- Do not depend on one maker's goodwill for anything Ostler cannot do without.

## Options

1. **AAOS only.** Apps read the car through AAOS; no node on AAOS cars. Cheap, but shallow
   (no diagnostics, no raw bus, no history while the head unit sleeps), per-maker gaps,
   and nothing for older cars.
2. **Node only (today).** Full depth and one model, but the XC40 needs hardware to show
   even its battery level.
3. **Both, AAOS as a read-only source (proposed).** An AAOS source maps properties to VSS
   and feeds the gateway over VISS; the node stays the only write path and the deeper
   source where fitted.

## Decision (proposed)

1. **AAOS is a read-only vehicle-data source.** It never writes to the car, never asks
   for climate or other control permissions, and never stands in for the node gate.
2. **VSS paths throughout.** The AAOS source maps each property to its VSS path (for
   example `EV_BATTERY_LEVEL` → `Vehicle.Powertrain.TractionBattery.StateOfCharge.Displayed`,
   `PERF_VEHICLE_SPEED` → `Vehicle.Speed`) with units converted to VSS units, and tags
   each value with its source.
3. **Where both exist, the node wins.** AAOS values are kept as a cross-check and shown as
   such; a disagreement is logged, not hidden.
4. **Staged:**
   - **S1:** the trip calculator reads AAOS directly when it runs on the car, with manual
     entry as the fallback. No gateway needed.
   - **S2:** the Ostler gateway app on AAOS gains an AAOS source that publishes to the
     gateway over VISS, so every Ostler app and the output bridges (MQTT, Home Assistant)
     get the data.
   - **S3:** on a car with both, the node and AAOS run side by side under rule 3.
5. **ADR-0049 wording.** ADR-0049 says the node "stays the only path to the car's buses,
   and its gate decides every write"; the decisions index already summarises it as "the
   only write path". This ADR makes that reading explicit: the node stays the only
   **write** path, and read-only platform sources (AAOS; maker clouds later, by their own
   ADR) may feed the gateway. The constitution's line changes only if the owner approves
   this ADR.
6. **First step:** a property census on the owner's XC40: a small app lists every
   property the VHAL offers, its access and its update rate. The result goes into the
   research note before S1 is built.

## Consequences

- An AAOS car gets Ostler's basic live data without hardware; the node keeps its value
  for diagnostics, the raw bus, recording while parked and non-AAOS cars.
- One more source to map and test, per maker; gaps only show up on real cars.
- Play review risk for the car app; a sideloaded or self-built route may be needed
  ([head-unit experiments](../references/research/head_unit_experiments.md)).
- The calculator's core stays pure so a Kotlin port can run on the car against the same
  test vectors.

## Confirmation

- The XC40 census lists each property and whether it read.
- S2: the gateway shows AAOS values with their source tag, the layering and gate tests
  still pass, and no AAOS code path can send a write.
- The owner approves the ADR-0049 wording change before any S2 work.
