---
title: "ADR-0034 — Repo boundaries: one platform repo, first-class firmware, packs as data, later hardware and contract repos"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0015-repo-split-executed.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, specs/2026-10-06-app-model-design.md, SCOPE.md]
summary: >
  Amends ADR-0013 and ADR-0015 (the precedent is ADR-0031). One platform repo `ostler` keeps the server, the Python lab, high-level features, the whole UI, the contracts and generic_obd2; the UI is not split out. `ostler-firmware` is first-class now: the portable C decoder, the link layer, every node variant and the per-pack C keygen plugins; the D2 pack's `esp32/kline_node` moves there when the repo is created. Each pack lives in `ostler-pack-<x>` and holds JSON data for the C decoder, optional lab-only Python and optional C keygen plugin source. `ostler-cloud` stays private; `ostler-hardware` (CERN-OHL-S) starts at PCB time; the module contract and conformance kit get their own repo at contract v1. A repo is split off only when toolchain, licence, release cadence or contributors differ. Licences follow ADR-0012. Amended 2026-10-06: optional UI apps (Cameras, Social, add-on module apps, community apps) may live in their own `ostler-app-<x>` repos now, on release cadence and contributors; the shell and core apps stay in `ostler`.
---

# ADR-0034 — Repo boundaries

> **Amended 2026-10-06:** optional UI apps may live in their own `ostler-app-<x>` repos;
> the shell and core apps stay in `ostler`. See [Amendments](#amendments-2026-10-06).

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
