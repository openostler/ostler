---
title: "ADR-0034 — Repo boundaries: one platform repo, first-class firmware, packs as data, later hardware and contract repos"
area: decisions
status: locked
version: 1.4
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, docs/feature_map_dmd.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-navigation-addon-design.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0015-repo-split-executed.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, specs/2026-10-06-app-model-design.md, SCOPE.md]
summary: >
  Amends ADR-0013 and ADR-0015 (the precedent is ADR-0031). One platform repo `ostler` keeps the server, the Python lab, high-level features, the whole UI, the contracts and generic_obd2; the UI is not split out. `ostler-firmware` is first-class now: the portable C decoder, the link layer, every node variant and the per-pack C keygen plugins; the D2 pack's `esp32/kline_node` moves there when the repo is created. Each pack lives in `ostler-pack-<x>` and holds JSON data for the C decoder, optional lab-only Python and optional C keygen plugin source. `ostler-cloud` stays private; `ostler-hardware` (CERN-OHL-S) starts at PCB time; the module contract and conformance kit get their own repo at contract v1. A repo is split off only when toolchain, licence, release cadence or contributors differ. Licences follow ADR-0012. Amended 2026-10-06: optional UI apps (Cameras, Social, add-on module apps, community apps) may live in their own `ostler-app-<x>` repos now, on release cadence and contributors; the shell and core apps stay in `ostler`. Amended again 2026-10-06 (ADR-0038): a marked GPL-3 repo, `ostler-bridge-meshtastic` (GPL-3.0-or-later), holds the Meshtastic VSS bridge, outside the commercial build. Amended 2026-10-07 (ADR-0042, approved by the owner, "approve all"): the add-on repos `ostler-app-social`, `ostler-app-vehicles` and `ostler-app-maintenance`, and later `ostler-app-lubelogger` (none created yet); Trips replaces Logs among the core apps, and Decode lab is a developer add-on whose code stays in `ostler`. A Proposed amendment (2026-10-07, DMD round), awaiting the owner, names five more repos, none created: `ostler-hub` (the Ostler Community server and web app, AGPL plus commercial, outside the closed `ostler-cloud`), `ostler-app-hub`, `ostler-app-navigation`, and later `ostler-app-alerts` and `ostler-app-phone`.
---

# ADR-0034 — Repo boundaries

> **Amended 2026-10-06:** optional UI apps may live in their own `ostler-app-<x>` repos;
> the shell and core apps stay in `ostler`; the Meshtastic bridge lives in a marked GPL-3
> repo, `ostler-bridge-meshtastic` (ADR-0038). See [Amendments](#amendments-2026-10-06).
> **Amended 2026-10-07 (approved by the owner, "approve all"; ADR-0042):** the add-on repos
> `ostler-app-social`, `ostler-app-vehicles`, `ostler-app-maintenance` and later
> `ostler-app-lubelogger`. See [Amendment (2026-10-07)](#amendment-2026-10-07).
> **Proposed amendment (2026-10-07, DMD round), awaiting the owner:** `ostler-hub`,
> `ostler-app-hub`, `ostler-app-navigation`, later `ostler-app-alerts` and `ostler-app-phone`.
> See [Proposed amendment](#proposed-amendment-2026-10-07-dmd-round). The accepted text is unchanged.

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06). **Amends** the repo tables of
  [ADR-0013](adr-0013-repo-split-and-vehicle-pack-contract.md) and
  [ADR-0015](adr-0015-repo-split-executed.md); it supersedes neither. The precedent for
  amending rather than superseding is [ADR-0031](adr-0031-generic-obd2-pack-in-platform.md).

## Context

- ADR-0013 split the monorepo into the platform, the D2 pack, `ostler-firmware` and a
  private `ostler-cloud`, with firmware and hardware as "when that work starts". ADR-0015
  executed the platform/pack part and left `esp32/` and `hardware/` in the D2 pack repo.
- The owner's direction of 2026-10-06 ([ADR-0032](adr-0032-one-node-optional-brain.md), one node with an optional brain) makes the
  ESP32 node the device that owns the car: K-line and CAN I/O, decoding to VSS and the only
  transmit gate. Decoding moves into one portable C decoder that reads packs as JSON and
  builds for both the ESP32 and PC/Linux. Firmware is therefore no longer a side project
  of one pack; it is a product tier with its own toolchain (ESP-IDF, C/C++).
- Seed-key algorithms (keygens) for packs such as the Td5 must run on the node, so each
  pack may carry a small C plugin compiled into the firmware.
- The module contract and its conformance kit (ADR-0027 §9) are meant for third parties,
  and will be versioned on their own once v1 is published.
- Splitting too eagerly costs pinned refs and two-PR changes (the reason ADR-0031 kept
  `generic_obd2` in the platform repo); splitting too late mixes toolchains and licences.

## Decision drivers

- One place for everything that changes together in Python and TypeScript.
- A clean home for the C toolchain and the node's release cadence.
- Packs that every tier can consume: the node, the brain, the cloud and the lab.
- Licences that stay clear per repo (ADR-0012), with open hardware under a hardware licence.
- A simple, written rule for when a new repo is justified.

## Decision

**The rule.** A part gets its own repo only when its **toolchain, licence, release cadence
or contributors** differ from the repo it would otherwise live in. Otherwise it stays put.

**Repos:**

| Repo | Visibility, licence | Contents | When |
|---|---|---|---|
| `ostler` (platform) | public; AGPL-3.0-or-later + commercial | The server and brain services, the Python lab and reference decoder, tools, high-level features (logbook, replay, analysis, MCP), **the whole UI** (not split out), the contracts (OpenAPI, AsyncAPI, JSON Schemas, VSS overlay), `packs/generic_obd2` (ADR-0031), docs and ADRs | Now |
| `ostler-firmware` | public; AGPL-3.0-or-later + commercial | The portable **C decoder** (ESP32 and PC/Linux builds), the **link layer** (K-line, CAN), **every node variant** (the diagnostic node, the guardian, sensor nodes) as one firmware, the transmit gate, and the **per-pack keygen C plugins** build glue | **First-class now** |
| `ostler-pack-<x>` | public; AGPL-3.0-or-later code, CC BY-SA 4.0 data | Per vehicle: **JSON data for the C decoder** (signals, DTCs, profiles, menus, actions, manifest), **optional lab-only Python** (discovery, importers, re-decoding tools), **optional C keygen plugin source**, demo data, research | Now; the D2 pack keeps `discovery2-diag` / `d2diag` |
| `ostler-cloud` | **private, closed** | Ostler Cloud; talks to devices only over the documented protocols (ADR-0013) | Unchanged |
| `ostler-hardware` | public; **CERN-OHL-S-2.0** | Schematics, PCBs, enclosures, BOMs for nodes, the guardian and add-ons | When PCB work starts |
| module contract + conformance kit | public; AGPL-3.0-or-later code, CC BY-SA 4.0 schemas and docs | The module manifest schema, its spec and the conformance tests for "works with Ostler" | At contract v1; until then in `ostler` |

**What moves:**

- The D2 pack's `esp32/kline_node` moves to `ostler-firmware` when that repo is created,
  history kept with `git filter-repo` (as ADR-0015 did). Its D2-specific parts become the
  D2 pack's JSON and its keygen plugin.
- The D2 pack's `hardware/` moves to `ostler-hardware` when PCB work starts.
- The platform's `tools/esp32_read.py` stays in `ostler` as a **lab client of the node**,
  not as part of the firmware.

**Packs are data first.** The C decoder reads a pack's JSON directly; there is no generated
C header per pack. Lab-only Python in a pack never runs on the node. A keygen C plugin is
compiled into the firmware from the pack's source; the pack's Python keygen stays the lab
reference, and shared test vectors check both (ADR-0035).

**Licences** follow ADR-0012: code AGPL-3.0-or-later with the commercial licence and the
CLA; vehicle and contract data CC BY-SA 4.0; hardware CERN-OHL-S-2.0 (strongly reciprocal,
so the hardware stays open as the code does). GPL-3 reuse stays in marked modules or packs
(ADR-0025), including in firmware.

## Confirmation

- `ostler-firmware` CI builds the C decoder for ESP32 and for PC/Linux and runs the shared
  test vectors against both (ADR-0032, ADR-0035).
- The D2 node reads the D2 pack's JSON in a bench run with no generated header.
- Each repo carries `LICENSE` (and `LICENSE-DATA` where it holds data) and passes
  `reuse lint`; `ostler-hardware` carries CERN-OHL-S-2.0.
- A proposal for a new repo names which of the four differences (toolchain, licence,
  cadence, contributors) it rests on; with none, it is refused.

## Consequences

- ADR-0013's `ostler-firmware` row grows from "guardian, add-on modules, HAL" to the node,
  the decoder and the keygen plugins, and is created now rather than "when that work
  starts".
- Packs become the unit every tier shares; their JSON schema becomes a contract that both
  the C decoder and the Python reference must accept.
- Pack releases and firmware releases need a compatibility rule (pack schema version vs
  decoder version); signed pack updates without a reflash are a known risk (ADR-0032).
- Keygen plugins mean pack C code builds inside the firmware tree; the firmware defines the
  plugin interface.
- The UI stays in one repo with the server, so contract changes and UI changes land in one
  PR.

## Alternatives considered

- **Keep `esp32/` in each pack.** Rejected: the node firmware is shared by every vehicle,
  and a per-pack copy would drift as the MAF mis-map did.
- **Split the UI into its own repo.** Rejected: it shares the contracts and changes in
  lockstep with the server; the rule above finds no difference.
- **Generate a C header per pack.** Rejected: it needs a reflash per pack change; JSON
  read at run time allows signed pack updates.
- **Supersede ADR-0013 and ADR-0015.** Rejected: most of both still holds; ADR-0031 set the
  amend-in-place precedent.
- **Put hardware under AGPL or CC BY-SA.** Rejected: neither is designed for hardware;
  CERN-OHL-S is.

## Amendments (2026-10-06)

- **Optional UI apps in their own repos** (owner answer to the
  [app-model spec](../specs/2026-10-06-app-model-design.md) Q1, 2026-10-06). The decision's
  table keeps "the whole UI" in `ostler`; this narrows it. **Optional UI apps** (Cameras,
  Social, add-on module apps and community apps) may live in their own `ostler-app-<x>` repos
  **now**. The rule's grounds are **release cadence** (these apps ship on their own schedule,
  often tied to an add-on device) and **contributors** (module makers and community authors
  who need not work in the platform repo). **The shell and the core apps** (Diagnose, Logs,
  Security, Network and Decode lab) **stay in `ostler`**, because they change in lockstep with
  the contracts. An app repo publishes a pinned npm package `@ostler/app-<x>` that the
  platform build bundles; its licence follows ADR-0012 for apps bundled into the shell.
  Community apps load only as sandboxed iframes on web hosts (app-model spec §5, §7).
  Confirmation: CI in `ostler` validates every pinned app's manifest and `shell` range, and a
  proposal for an app repo still names cadence or contributors, as the rule requires.
- **A marked GPL-3 repo for the Meshtastic bridge** (owner answer of 2026-10-06 to the
  mesh questions, [ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md) §3). The rule's
  ground is **licence**: the bridge uses Meshtastic's GPL-3.0 protobufs, so it cannot live
  in an AGPL-plus-commercial repo (ADR-0025). The table gains one row:

  | Repo | Visibility, licence | Contents | When |
  |---|---|---|---|
  | `ostler-bridge-meshtastic` | public; **GPL-3.0-or-later**, marked GPL-3 | The thin VSS bridge between a Meshtastic-compatible radio (USB serial, BLE or TCP) and the Ostler broker: no actions, its own `in/` and `state/` topics only, rate limits and privacy defaults (ADR-0038 §2–§5); runs as a separate program on the brain or alongside the phone app | When the LoRa add-on work starts |

  Core, the C decoder and the node firmware never import or link it; it talks to Ostler only
  over MQTT under its own ACL. It is excluded from the commercial build, and its `reuse lint`
  shows GPL-3.0-or-later.

## Amendment (2026-10-07)

Approved by the owner on 2026-10-07 ("approve all") with
[ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (small core, add-ons are
the product). The grounds are the 2026-10-06 rule's: **release cadence** and
**contributors**. The core apps that stay in `ostler` are now Diagnose, **Trips** (was Logs),
Network and Security; Decode lab becomes a developer add-on whose code stays in `ostler`
until this ADR's split rule applies. The table gains these add-on repos, **none created
yet**; each starts from its approved spec:

| Repo | Visibility, licence | Contents | When |
|---|---|---|---|
| `ostler-app-social` | public; AGPL-3.0-or-later (ADR-0012) | The Social add-on: messaging, push-to-talk, calls, later camera sharing ([spec](../specs/2026-10-07-social-addon-design.md)) | When Social S1 starts |
| `ostler-app-vehicles` | public; AGPL-3.0-or-later | The Vehicles & Map add-on: shared vehicles and the built-in map ([spec](../specs/2026-10-07-vehicles-and-map-addon-design.md)) | When Vehicles & Map V1 starts |
| `ostler-app-maintenance` | public; AGPL-3.0-or-later (files translated from LubeLogger: `AGPL-3.0-or-later AND MIT`) | The Maintenance & Garage add-on ([spec](../specs/2026-10-07-maintenance-garage-addon-design.md)) | When Maintenance M1 starts |
| `ostler-app-lubelogger` | public; AGPL-3.0-or-later | The optional LubeLogger bridge, one integration add-on | Later, after Maintenance M2 |

The MeshCore bridge, `ostler-bridge-meshcore` (MIT), is named by
[ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md#amendment-2026-10-07-approved) item 1 and
is created after the Meshtastic bridge and the bench test.

## Proposed amendment (2026-10-07, DMD round)

**Status: proposed, for the owner's approval**, with the matching
[ADR-0042 proposed amendment](adr-0042-ecosystem-small-core-addons-are-the-product.md#proposed-amendment-2026-10-07-dmd-round)
(the DMD2 and DMD Hub features; map in [docs/feature_map_dmd.md](../docs/feature_map_dmd.md)).
The accepted text above is unchanged until it is approved. The table gains these repos,
**none created yet**; each starts from its approved spec, and each names its grounds as the rule
requires:

| Repo | Visibility, licence | Contents | Grounds | When |
|---|---|---|---|---|
| `ostler-hub` | public; AGPL-3.0-or-later + commercial (CLA, ADR-0012) | Ostler Community's server and web app: Python ASGI API, PostgreSQL + PostGIS, S3-compatible storage, PMTiles, TS/React web importing the shell's kit and tokens, migrations, the OpenAPI contract, moderation tools, a compose file for self-hosting clubs, policy templates ([community hub §3](../specs/2026-10-07-community-hub-design.md#3-repos-and-stack), draft) | **toolchain** (a deployed web service with Postgres), **release cadence**, **contributors** (web developers, club hosts) | When hub H1 starts |
| `ostler-app-hub` | public; AGPL-3.0-or-later | The shell add-on (npm `@ostler/app-hub`): link one or more hubs, publish from Trips, help threads, Discover, Following | cadence, contributors (the 2026-10-06 app-repo amendment) | With `ostler-hub`, at H1 |
| `ostler-app-navigation` | public; AGPL-3.0-or-later (MIT routing engines used under ADR-0025 with notices) | The Navigation add-on: a Python service on the Brain plus a React UI bundled into the shell; routing, guidance, voice, GPX library and follow, planner, roadbook ([navigation](../specs/2026-10-07-navigation-addon-design.md), draft). It replaces the `ostler-app-routes` and `ostler-app-roadbook` ideas of the research | **toolchain** (a routing engine and its data builds on the Brain), cadence | When Navigation N0 starts |
| `ostler-app-alerts` | public; AGPL-3.0-or-later; feed data under each feed's own licence | UK official weather, flood and closure alerts, free and opt-in | cadence (feed changes), contributors (per-country feeds) | Later, after its spec |
| `ostler-app-phone` | public; AGPL-3.0-or-later | Phone mirroring (notifications, calls), Parked-only content | cadence, contributors (per-platform phone links) | Later, after its spec |

**`ostler-hub` is not `ostler-cloud`.** The community hub is open and self-hostable; Ostler runs
one official instance of the same code. The closed `ostler-cloud` row is unchanged and may host
optional relay and storage services, never the only copy of the hub. Its OpenAPI contract lives
in `ostler-hub` and is pinned by `ostler-app-hub`; both generate TS types (ADR-0035).

**Stays in `ostler`:** `ShellInput` (the shell's D-pad input model), the per-trip sharing
pieces (scrubber, `ostler.share/1` bundle writer, `ostler share verify`, the Trips share sheet,
More → Places) and, later, Crash SOS in Security: they change in lockstep with the shell and
the contracts, so the rule finds no difference.

**Confirmation (delta).** `ostler`'s CI validates each pinned add-on's manifest and `shell`
range as before; `ostler-hub`'s CI runs its API tests against PostGIS and its web build against
the pinned kit package.

### Decisions for the owner (DMD round)

1. **Create these five repos when their phases start?** Recommend: yes, `ostler-hub` and
   `ostler-app-hub` at H1 and `ostler-app-navigation` at N0; Alerts and Phone only after their
   specs. Alternative: start Navigation and the hub add-on inside `ostler` and split later.
2. **`ostler-hub` licence: AGPL plus commercial, as `ostler`?** Recommend: yes, under the CLA
   (ADR-0012). Alternative: AGPL only, with no commercial licence for the hub.
3. **Keep the hub out of `ostler-cloud`?** Recommend: yes; the official instance runs the public
   code. Alternative: a closed hub in `ostler-cloud` (rejected by the exit guarantee).

## Changelog

- 2026-10-06: v1.0–v1.2, accepted and amended (optional app repos; the Meshtastic bridge repo).
- 2026-10-07: v1.3, Amendment (2026-10-07): the add-on repos `ostler-app-social`,
  `ostler-app-vehicles`, `ostler-app-maintenance` and later `ostler-app-lubelogger` (not yet
  created); Trips among the core apps; Decode lab a developer add-on (ADR-0042, approved by
  the owner, "approve all").
- 2026-10-07: v1.4, adds the Proposed amendment (2026-10-07, DMD round) for owner approval:
  `ostler-hub`, `ostler-app-hub`, `ostler-app-navigation`, later `ostler-app-alerts` and
  `ostler-app-phone` (none created); the hub stays outside `ostler-cloud`. The accepted text
  is unchanged.
