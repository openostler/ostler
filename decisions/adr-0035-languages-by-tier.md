---
title: "ADR-0035 — Languages by tier: C/C++ on the node, Python on the brain and lab, TypeScript for the UI"
area: decisions
status: locked
version: 1.1
updated: 2026-10-08
depends_on: [decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0017-open-standards-first.md, SCOPE.md]
summary: >
  Supersedes in part ADR-0002 ("the production core stays Python") and amends ADR-0004. C/C++ on ESP-IDF for node firmware and the one shared decoder; Python for the lab, tools, brain services and MCP, with a core that stays stdlib + pyserial plus optional extras [passkeys], [mcp] and [can], and the native decoder loaded through stdlib ctypes with the Python reference decoder as the fallback when the library is missing; TypeScript for the UI, with types generated from OpenAPI/AsyncAPI and the phone app packaged with Capacitor. Rust only later, for a measured hot path. Revisit only when a measurement forces it. Amended 2026-10-08 (direction round, ADR-0050): Kotlin for the Android app tier, replacing the Capacitor wrapper.
---

# ADR-0035 — Languages by tier

> **Amended 2026-10-08 (direction round,
> [ADR-0050](adr-0050-kotlin-for-the-android-app-tier.md)), approved by the owner on
> 2026-10-08 ("I agree with everything"):** Kotlin joins the table for the Android app tier:
> one shared hybrid shell around the React pages, Jetpack, Glance for the feed widget,
> minimum SDK 29. It replaces the UI row's Capacitor wrapper. The other rows are unchanged.

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06). **Supersedes in part**
  [ADR-0002](adr-0002-layered-stdlib-core.md) (the production protocol core and decoding
  staying Python). **Amends** [ADR-0004](adr-0004-react-typescript-ui.md) (generated types,
  Capacitor packaging).

## Context

- ADR-0002 kept the whole protocol stack in Python, because the Pi with a KKL cable was the
  car-side device.
- The owner's direction of 2026-10-06 ([ADR-0032](adr-0032-one-node-optional-brain.md)) moves the car side to an ESP32 node:
  K-line and CAN I/O, decoding to VSS and the transmit gate run there, and the Pi becomes an
  optional brain. Decoding must be one implementation shared by the node and the PC, not
  two that drift (the MAF mis-map came from exactly that).
- Decoding is still active work (D2 MAF, wastegate, EGR and SLABS are open). Discovery,
  re-decoding old recordings, analysis and MCP are exploratory and need a fast language.
- ADR-0004 hand-mirrors the snapshot contract in TS types; the platform now has OpenAPI
  and AsyncAPI contracts (U0 seams) to generate from. The phone needs Bluetooth and local
  Wi-Fi access, which a plain PWA cannot get on iOS.
- Three repos (ADR-0034) give each language a natural home.

## Decision drivers

- One decoder, many targets: ESP32 and PC/Linux from the same source.
- Keep the fast Python lab while facts are still being found.
- Keep the Pi and tester install light (no compiler, no Node).
- Types that cannot drift from the contracts.
- No new language without a measured reason.

## Decision

| Tier | Language | Notes |
|---|---|---|
| Node firmware and the shared decoder | **C/C++ on ESP-IDF** | The decoder is portable C with no ESP-IDF dependency, so the same source builds a native library for PC/Linux. Link layer, gate and keygen plugins are C (ADR-0034). |
| Lab, tools, brain services, MCP | **Python** | The core stays stdlib + pyserial. Optional extras: `openostler[passkeys]` (`cryptography`), `openostler[mcp]` (the official Python MCP SDK), `openostler[can]`. |
| UI (cloud, brain, phone) | **TypeScript** | React as in ADR-0004; types generated from OpenAPI/AsyncAPI; the phone app is the same build in a native wrapper such as Capacitor. |
| A measured hot path, later | **Rust** | Only when a measurement shows C or Python is not good enough there. |

**Python and the native decoder.**

- Python loads the native decoder through stdlib **`ctypes`**: no build step on install and
  no new runtime dependency.
- When the native library is missing (an unsupported platform, a source checkout), the
  **Python reference decoder** is used. It stays the lab reference while decoding is
  ongoing.
- Shared test vectors (bytes in → VSS out, plus init and gate cases) run in CI against the
  C build and the Python reference; any difference fails.
- The link and decode layers port to C once a pack's facts are stable; until then the
  approved K-line, J1979 and CanLink specs keep being built in Python.

**Revisit** this table only if something measured forces it: a timing budget missed, a
memory limit hit, a profile showing a hot path.

## Confirmation

- The C decoder passes the shared vectors on ESP32 and PC/Linux, and the Python reference
  passes the same vectors.
- With the native library removed, the platform test suite still passes on the Python
  reference decoder.
- A plain `pip install openostler` pulls in only pyserial; each extra pulls in only its
  own dependency.
- CI regenerates the UI types from OpenAPI/AsyncAPI and fails when the committed types
  differ.

## Consequences

- The native library must be built per OS and architecture: at least Raspberry Pi
  (Linux arm64), macOS (arm64 and x86_64) and the CI runner (Linux x86_64). Wheels or a
  build step must ship it, and the ctypes fallback covers the gaps.
- Contributors to decoding need C as well as Python once a pack's decode moves to C; the
  native PC build keeps iteration fast without flashing.
- ADR-0002's layering, stdlib server and pyserial-only core stay; only "the production
  protocol core stays Python" is superseded.
- ADR-0004's hand-written mirror types give way to generated ones; the phone app adds a
  Capacitor project and a native build to the UI.

## Alternatives considered

- **Keep decoding in Python only.** Rejected: the node must decode on its own, and two
  hand-kept implementations drift.
- **MicroPython or CircuitPython on the node.** Rejected: weaker timing and memory control
  on the ESP32-S3, and no shared native build for the PC.
- **Rust everywhere now.** Rejected: no measured need, a smaller ESP-IDF ecosystem, and it
  would throw away the Python lab.
- **A compiled CPython extension instead of ctypes.** Rejected: it needs a compiler or
  per-version wheels on every install; ctypes needs neither.

## Changelog

- 2026-10-08 — v1.1, amended (direction round, approved by the owner on 2026-10-08,
  ADR-0050): Kotlin for Android apps.
