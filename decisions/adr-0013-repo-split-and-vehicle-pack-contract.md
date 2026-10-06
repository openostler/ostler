---
title: "ADR-0013 — Split into an Ostler platform, the D2 pack, firmware and a closed cloud; VehiclePack contract"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, specs/2026-10-06-platform-direction-design.md, SCOPE.md]
summary: >
  The project splits into a vehicle-agnostic platform repo (working brand "Ostler", public AGPL, holds the main UI), this repo as the Land Rover Discovery 2 vehicle pack, a public firmware repo and a private closed-source cloud repo; packs plug in through a VehiclePack entry-point contract, the cloud only speaks a documented protocol, and the split happens after the code is decoupled in place.
---

# ADR-0013 — Repo split and the VehiclePack contract

> **Amended by [ADR-0034](adr-0034-repo-boundaries.md), 2026-10-06:** `ostler-firmware` is first-class now and takes the D2 `esp32/kline_node`; packs are JSON data plus optional lab Python and C keygen plugins; hardware and contract repos come later.

- **Date:** 2026-10-06
- **Status:** accepted (owner decisions, 2026-10-06)

## Context

- The project has become an open vehicle platform: diagnostics, logging, telemetry, tracker and alarm. See the [direction spec](../specs/2026-10-06-platform-direction-design.md).
- Keeping everything in a repo named after one vehicle makes no sense any more.
- The owner wants a **closed-source cloud** as the revenue stream.
- A code survey (October 2026) found most layers already vehicle-neutral:
  - kline, kwp2000, transport, session, gps, imu, geo, community, the logbook, the server and the UI shell.
- D2 specifics leak in at about 15 places:
  - sources, server, dashboard, catalog, commands, menus, faultscan, modscan, sniff modules, logbook, `layout.ts`;
  - plus a `motor↔td5` alias used in 6+ places.

## Decision

**Working brand: Ostler.**

- Chosen by the owner from naming research: informal web, GitHub, PyPI, npm and DNS checks.
- An official UKIPO/EUIPO search (classes 9, 12, 38, 42) and an attorney's clearance come before announcing.
- Names to use:

  | Where | Name |
  |---|---|
  | Repos | `ostler`, `ostler-firmware`, `ostler-cloud` |
  | Python import | `ostler` |
  | PyPI distribution | `openostler` (because `ostler` is taken) |
  | npm scope | `@openostler` |
  | MQTT root / Home Assistant domain | `ostler` |

- JLR marks are never used in our brand. Say "Ostler pack *for* Land Rover Discovery 2".

**Repos:**

| Repo | Visibility, licence | Contents |
|---|---|---|
| `ostler` | public; AGPL + commercial | Platform: core comms, snapshot/event contract, **VehiclePack SDK and loader**, logbook/replay, geo/gps/imu, integrations, web server, **the main UI**, docs tooling, Docker/homelab deploy |
| `discovery2-diag` (this repo) | public; AGPL code + CC BY-SA data | **The Land Rover Discovery 2 pack**: decoders, keygens, signals/DTC data, menus and actions, D2 data sources, demo sessions, NanoCom/sniff importers, D2 tools, `esp32/kline_node`, the D2 research in `references/` and `docs/discovery-2-td5/` |
| `ostler-firmware` | public; AGPL | ESP32 guardian, add-on modules, shared HAL, private-CAN protocol |
| `ostler-cloud` | **private, closed** | Ostler Cloud |
| `ostler-hardware`, `ostler-android` | later | Hardware designs; Android launcher |

**The VehiclePack contract.** A pack exposes an entry point `ostler.vehicle` returning a pack object with:

- `modules`: id, name, address, init, keygen
- `sources(port)`
- `signals_dir`, `dtc_dir`
- `actions`, `menus`
- `faultscan` order
- `sniff` address map and importers
- `demo` sessions and sniff log
- `docs_dir`
- the UI `layout.json` manifest

Rules:

- The platform never imports a pack. The layering test enforces this.
- Packs pin a compatible platform version and run contract tests in CI.

**The cloud boundary.**

- `ostler-cloud` talks to devices only over a documented MQTT/HTTPS protocol.
- The open, device-side client lives in `ostler`.
- The cloud never imports platform code. This keeps the AGPL and closed code separate.
- `server/endpoint.py` seeds the cloud repo:
  - partly written by leijoma under MIT, which permits closed reuse with the notice kept;
  - the rest by the owner, who may relicense their own code.

**Sequence:**

1. **Decouple in place, behind `VehiclePack`** (Phase 0, which gets its own spec): move D2 code under `vehicles/lr_d2/`, cut the hotspots, drop the `motor↔td5` alias, add fake-pack platform tests.
2. **Split the repos with history preserved** (`git filter-repo`). Move the homelab deploy to `ostler`, and have the Dockerfile install the platform plus the D2 pack.
3. **Create the firmware and cloud repos** when that work starts.

**Contributors.** leijoma, who started this repo, is a past contributor; their MIT-licensed work stays credited.

## Consequences

- Phase 0 must land before the split, otherwise both repos break.
- The D2 pack becomes the reference pack and conformance fixture for the platform.
- One shared constitution, owned by `ostler`; the pack's CLAUDE.md links to it.
- The Mac installer and the Pi deploy script move to `ostler`.

## Alternatives considered

- **Keep a monorepo with packs as sub-packages.** Simpler for now, but it mixes the closed cloud's needs and per-vehicle data ownership into one repo. Kept only as the interim state during Phase 0.
- **Platform keeps this repo's identity.** Rejected by the owner: the D2 work keeps its name and history here.
- **Fork per vehicle.** Rejected: it duplicates the protocol core and the signal store.

## Amendments (2026-10-06)

Amended by [ADR-0034](adr-0034-repo-boundaries.md) (repo boundaries). The platform/pack
split, the VehiclePack contract and the cloud boundary above stand.
1. **Firmware is first-class now.** `ostler-firmware` holds the portable C decoder, the
   link layer, every node variant (diagnostic node, guardian, sensor nodes) and the
   per-pack keygen C plugins. It is created now, not "when that work starts".
2. **`esp32/kline_node` moves.** The D2 pack's `esp32/kline_node` moves to
   `ostler-firmware` when that repo is created; it no longer belongs in the pack row above.
3. **Packs are data first.** A pack (`ostler-pack-<x>`; the D2 pack keeps
   `discovery2-diag`) holds JSON data the C decoder reads, optional lab-only Python and
   optional C keygen plugin source.
4. **Later repos.** `ostler-hardware` (CERN-OHL-S) starts at PCB time; the module
   contract and conformance kit get their own repo at contract v1.
5. **The split rule.** A new repo only when toolchain, licence, release cadence or
   contributors differ.
