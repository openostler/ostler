---
title: "Scope & architecture"
area: root
status: stable
version: 1.3
updated: 2026-10-06
summary: >
  States the project's core mission (communication with the car and interpretation of its data) and the layering boundary that keeps storage and UI as consumers.
---

# Scope & architecture

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
  ([discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag), distribution
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

- The car's own faults and maintenance history — those belong in the sister project
  `../Discovery 2/`, not here.

See [docs/architecture.md](docs/architecture.md) for the layer-by-layer stack and [CONSTITUTION.md](CONSTITUTION.md) for the hard rules.
