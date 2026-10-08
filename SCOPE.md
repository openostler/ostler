---
title: "Scope & architecture"
area: root
status: stable
version: 1.8
updated: 2026-10-08
summary: >
  Approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted): Ostler is an ecosystem whose main goal is getting the car's data into apps; small core, add-ons are the product; the core's own job stays comms and interpretation. Then the core mission (communication with the car and interpretation of its data) and the layering boundary that keeps storage and UI as consumers. Out of scope: HEVAC control, and the owner's own Discovery 2 fault and maintenance records (the sister project); maintenance as a feature is the Maintenance & Garage add-on. Amended 2026-10-07 (OS round): small core reads as the empty OS of ADR-0046. Amended 2026-10-07 (openness round, ADR-0047): add-ons are off by default unless a flavour preinstalls them on. Amended 2026-10-08 (direction round, ADR-0049): Ostler is an open diagnostic and logging platform with an open vehicle-data feed (VISS); the empty OS is replaced by a gateway app and separate apps; the contract is the VISS v3 feed (ADR-0051).
---

# Scope & architecture

> **Amended 2026-10-08 (direction round,
> [ADR-0049](decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md)), approved by
> the owner on 2026-10-08 ("I agree with everything"):** Ostler is **an open diagnostic and
> logging platform with an open vehicle-data feed (VISS)**, not an OS. The empty OS of the
> note below is replaced by a required gateway app and separate apps, and the one contract
> is the VISS v3 feed ([ADR-0051](decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)).
> The core mission (comms and interpretation) is unchanged.

> **Amended 2026-10-07 (OS round), approved by the owner on 2026-10-07 ("approve all", OS
> round):** "small core" now reads as the **empty OS** of
> [ADR-0046](decisions/adr-0046-empty-os-every-app-an-add-on.md): system services and system
> UI only; Diagnose, Trips, Security and every other feature are apps. The core mission (comms
> and interpretation) is unchanged.

## Mission

Per [ADR-0049](decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md) (accepted
2026-10-08):

**Ostler is an open diagnostic and logging platform with an open vehicle-data feed (VISS).**
The core's own job does not widen: it is still **communication with the car and
interpretation of its data**, delivered through one contract, the VISS v3 feed over VSS
([ADR-0051](decisions/adr-0051-viss-v3-is-the-core-vehicle-data-protocol.md)). The gateway
app serves that feed on each Android device, behind its permissions controller; the apps
(Diagnostics with Decode lab, Trips, Security, Maintenance and add-ons) and third-party apps
read it the same way. Output bridges (RealDash, ELM327 and CAN-box emulation, Home Assistant
and OVMS through External MQTT) are read-only views of it.
Map: [docs/ecosystem.md](docs/ecosystem.md).

**The core mission of this project is communication with the car and interpretation of
its data.** Storage and presentation (dashboards, logging, InfluxDB/Grafana) are useful,
but they are *consumers* built on top of the core — not the point of it. This file states
that boundary so the extras don't quietly become the product.

## Three layers, one contract

```
COMMS  — talk to the ECUs over K-line (and CAN)
  Python:  transport/ · kline/ · kwp2000/ · session.py · ports.py   (this repo; lab/reference)
  Node:    C link layer on the ESP32 (ostler-firmware; the D2 kline_node moves there, ADR-0034)
        │  raw LID bytes
        ▼
INTERPRETATION  — turn raw bytes into named, scaled, confidence-tagged signals
  pack.py = the VehiclePack contract; signals/ and dtc/ = the store loaders
  each pack's signals/*.json = the SINGLE SOURCE OF TRUTH (offset / scale / unit / confidence)
  the pack's module decoders (D2: td5/ slabs/ airbag/ bcu/ ace/ autobox/) read it
  one portable C decoder reads the pack JSON on the node and, via ctypes, on PC/Linux;
  the Python reference decoder is the lab path and the fallback (ADR-0035)
        │  normalized snapshot: {status, signals:{name:{v,u,s,c}}, faults:[…]}  (see DataSource.poll)
        ▼ ───────────────── the defined API (the contract) ─────────────────
CONSUMERS  — storage & presentation (optional, swappable)
  web/ dashboard + SSE · file logging · InfluxDB/Grafana · raw-log collector · community upload
```

**Core = COMMS + INTERPRETATION** (the top two layers). Everything below the snapshot
contract is optional and replaceable.

## The one hard rule

**Core never imports from the consumer layer.** `transport`, `kline`, `kwp2000`,
`session`, `ports`, `signals` and the packs' module decoders must not import from `web` (or any
future storage/presentation package). Data flows one way: comms → interpretation →
snapshot → consumers. `web/sources.py` is the boundary — it consumes the core and adapts
it for the UI.

## Two platforms, one interpretation

The ESP32 node owns the car ([ADR-0032](decisions/adr-0032-one-node-optional-brain.md)); a computer with a KKL cable becomes a dev-only
path. **Decoding is one implementation, not two:** a portable C decoder in
`ostler-firmware` builds for the ESP32 and as a native library for PC/Linux, which Python
loads through stdlib `ctypes` ([ADR-0035](decisions/adr-0035-languages-by-tier.md)). The Python decoder stays the lab and reference
implementation while decoding is ongoing, and is used whenever the native library is
missing. Shared test vectors (bytes in → VSS out, plus init and gate cases) run in CI
against both, so they cannot drift.

**Interpretation is not duplicated either:** each pack's `signals/*.json` is the one
contract, and the node reads that pack JSON directly — no generated header, nothing
hand-copied. Hand-copying is exactly what caused the MAF mis-map (the store and the ESP
drifted apart). The link and decode layers port to C once a pack's facts are stable;
until then they keep being built in Python.

## What lives where

This repo is the **platform** (ADR-0013, ADR-0015):

- `src/openostler/` — the core library (comms + interpretation + the `VehiclePack`
  contract) plus, under `web/`, the reference consumer (dashboard/SSE/logging).
- `ui/` — the React/TS dashboard, built into `src/openostler/web/static/`.
- `tools/` — the platform CLIs (`dashboard`, `deploy.sh`, `module_scan`,
  `esp32_read` (a lab client of the node), `build_places`, `make_demo_session`).
- `docs/`, `specs/`, `decisions/`, `references/research/` — platform docs and decisions.

Elsewhere:

- **Vehicle packs**, e.g. the Discovery 2 pack
  ([ostler-pack-lr-d2](https://github.com/openostler/ostler-pack-lr-d2), distribution
  `d2diag`): decoders, keygens, `signals/*.json` (written only via `upsert_field`),
  `dtc/*.json`, menus, actions, demo data, D2 tools, and the protocol knowledge with its
  car-test backlog (`references/test_plan.md`). Its ESP32 `kline_node` moves to
  `ostler-firmware` when that repo is created (ADR-0034).
- **Node firmware** (`ostler-firmware`): the C decoder, the link layer, every node variant
  and the per-pack keygen C plugins (ADR-0034).
- The cloud seed (`server/`) goes to the private `ostler-cloud` repo.
- InfluxDB / Grafana / the raw-log collector live on a separate server, not in this repo.

## Direction: core · vehicle packs · integrations (2026-10-06, draft)

The project is growing into an open vehicle platform, covering diagnostics, logging,
telemetry, tracking and an alarm. See
[specs/2026-10-06-platform-direction-design.md](specs/2026-10-06-platform-direction-design.md)
(draft) and [references/research/](references/research/platform.md).

The layering stays as above. Two names are added:

- **Vehicle packs** are declarative per-vehicle data plus small code hooks. They sit inside
  INTERPRETATION. The D2 Td5 is the reference pack, the separate distribution `d2diag`,
  reached only through `openostler.pack` (Phase 0 done; repo split done, ADR-0015).
- **Integrations** are opt-in consumers and add-ons, such as MQTT/Home Assistant, the
  tracker and the alarm. Every one of them is off by default.

The hard rule doesn't change: core never imports from vehicle packs or integrations.

## Deliberately out of scope (for now)

- **HEVAC (climate) control** lives in a separate ESP32 project. This repo only talks to
  it, for example over the add-on CAN bus.

- The owner's own Discovery 2 fault and maintenance records belong in the sister project
  `../Discovery 2/`, not here. Maintenance as a feature (services, reminders, fuel, costs)
  is the [Maintenance & Garage add-on](specs/2026-10-07-maintenance-garage-addon-design.md),
  in its own repo.

See [docs/architecture.md](docs/architecture.md) for the layer-by-layer stack and [CONSTITUTION.md](CONSTITUTION.md) for the hard rules.

## Changelog

- 2026-10-08: v1.8, amended (direction round, approved by the owner on 2026-10-08,
  ADR-0049): the mission is an open diagnostic and logging platform with an open
  vehicle-data feed (VISS); the gateway app and separate apps replace the empty OS; the
  contract is the VISS v3 feed.
- 2026-10-07: v1.7, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", ADR-0047): add-ons are off by default unless a flavour preinstalls them on.
- 2026-10-07: v1.6, amended (OS round, approved by the owner on 2026-10-07, "approve all"):
  small core reads as the empty OS (ADR-0046).
- 2026-10-07: v1.5, approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted):
  the restatement is the mission text at the top; the out-of-scope line narrows "maintenance
  history" to the owner's own Discovery 2 records, maintenance as a feature being the
  Maintenance & Garage add-on.
- 2026-10-07: v1.4, proposed restatement at the top (awaiting the owner; ADR-0042 proposed);
  the rest unchanged.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **Adopt the restatement?** Recommend: yes; it keeps the layering and the hard rule and
   names add-ons as the product. Alternative: leave SCOPE as is and state the ecosystem goal
   only in GOALS.
2. **"Maintenance history belongs in the sister project" (out of scope list)?** Recommend:
   narrow it to the owner's own Discovery 2 records; maintenance as a feature now lives in the
   Maintenance & Garage add-on. Alternative: keep the line as written.
