---
title: "Scope & architecture"
area: root
status: stable
version: 1.2
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
COMMS  — talk to the ECUs over K-line (platform-specific; same protocol, two impls)
  Python:  transport/ · kline/ · kwp2000/ · session.py · ports.py   (this repo)
  ESP32:   C firmware (ostler-firmware; the D2 kline_node lives in the D2 pack repo)
        │  raw LID bytes
        ▼
INTERPRETATION  — turn raw bytes into named, scaled, confidence-tagged signals
  pack.py = the VehiclePack contract; signals/ and dtc/ = the store loaders
  each pack's signals/*.json = the SINGLE SOURCE OF TRUTH (offset / scale / unit / confidence)
  the pack's module decoders (D2: td5/ slabs/ airbag/ bcu/ ace/ autobox/) read it
  Python decodes it at runtime; the ESP consumes a header generated from the same JSON
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

K-line comms are offered both from a computer (Mac/PC/Pi + a KKL cable, in Python) and
from an ESP32 (firmware). The protocol is necessarily implemented twice (C and Python
can't share code), **but interpretation is not duplicated**: `signals/*.json` is the one
contract. The ESP's decode table is *generated* from it, never hand-copied — hand-copying
is exactly what caused the MAF mis-map (the store and the ESP drifted apart).

## What lives where

This repo is the **platform** (ADR-0013, ADR-0015):

- `src/openostler/` — the core library (comms + interpretation + the `VehiclePack`
  contract) plus, under `web/`, the reference consumer (dashboard/SSE/logging).
- `ui/` — the React/TS dashboard, built into `src/openostler/web/static/`.
- `tools/` — the platform CLIs (`dashboard`, `deploy.sh`, `module_scan`, `raw_analyze`,
  `esp32_read`, `build_places`, `make_demo_session`).
- `docs/`, `specs/`, `decisions/`, `references/research/` — platform docs and decisions.

Elsewhere:

- **Vehicle packs**, e.g. the Discovery 2 pack
  ([discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag), distribution
  `d2diag`): decoders, keygens, `signals/*.json` (written only via `upsert_field`),
  `dtc/*.json`, menus, actions, demo data, D2 tools, the ESP32 `kline_node`, and the
  protocol knowledge with its car-test backlog (`references/test_plan.md`).
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
