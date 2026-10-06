---
title: "Changelog"
area: root
status: stable
version: 1.0
updated: 2026-10-06
summary: >
  Notable changes to the Ostler platform in Keep a Changelog 1.1.0 form: the Unreleased U0 repo-hygiene work (REUSE, PEP 639, SECURITY.md, supply-chain CI, ruff/mypy/pre-commit) plus a brief history reconstructed from git, and the versioning policy (SemVer 0.y.z, integer PACK_API_VERSION, VSS pin in vss/VERSION).
---

# Changelog

All notable changes to the Ostler platform (`openostler`) are recorded here. The format
follows [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/). Vehicle packs keep
their own changelogs.

## Versioning

- **The platform follows [Semantic Versioning](https://semver.org/).** It stays on
  `0.y.z` until the pack API is frozen: until then a minor bump (`0.y`) may break packs or
  the HTTP API, and a patch bump (`0.y.z`) does not. The version lives in
  `pyproject.toml`; release tags are `v<version>` and must match it.
- **`PACK_API_VERSION`** (`src/openostler/pack.py`) is an integer major. It changes only
  when the `VehiclePack` contract breaks, and the platform refuses a pack built for
  another value.
- **The COVESA VSS pin** (ADR-0016) is recorded in `vss/VERSION`; changing it is listed
  here.
- Releases carry SBOMs and build provenance ([SECURITY.md](SECURITY.md)).

## [Unreleased]

### Added
- U0 repo hygiene (standards research §8.1 items 7–13, ADR-0017):
  - REUSE 3.3 compliance: `LICENSES/` with the canonical licence texts, `REUSE.toml`
    for docs, data, generated and binary files, and SPDX headers on source files;
    `reuse lint` in CI and pre-commit.
  - [SECURITY.md](SECURITY.md): private vulnerability reporting, scope, a 14-day
    acknowledgement target, supported versions, coordinated disclosure, CRA and PSTI
    readiness, and the hard safety lines for testing against vehicles.
  - Supply-chain CI: Dependabot (pip, npm, GitHub Actions, Docker; weekly), an OpenSSF
    Scorecard workflow, and a release workflow that builds the sdist and wheel, writes
    CycloneDX and SPDX SBOMs and attests build provenance.
  - Developer tooling: ruff (`[tool.ruff]`, CI step), mypy configuration (not enforced
    yet) and `.pre-commit-config.yaml`.
  - This changelog and the versioning policy above.
- THIRD_PARTY_LICENSES.md lists the UI libraries bundled in the committed build (React,
  zod, MapLibre GL JS).

### Changed
- `pyproject.toml` uses PEP 639 licence metadata (`license = "AGPL-3.0-or-later"`,
  `license-files`) and needs `setuptools>=77` to build.
- Every GitHub Action is pinned to a full commit SHA; workflows default to
  `permissions: contents: read`.

### Fixed
- Trivial lint findings (unused imports and variables, redundant arguments); no
  behaviour change.

## [0.0.1] - 2026-10-05

The only version so far; it was never tagged. In brief, from the git history:

### Added
- 2026-10-05: decisions ADR-0016 to ADR-0021 (COVESA VSS as the canonical signal
  namespace, open standards first, UI architecture, reuse from OVMS and OBDb, CAN links
  listen-only by default, local HTTPS on the device); UI architecture spec approved
  (v0.2); constitution 1.4 and GOALS 1.1.
- 2026-10-05: research notes on open standards, CAN interfaces and head units, OVMS
  reuse, and the head-unit-first UI architecture (7 notes and a draft spec).
- 2026-10-05: Settings → Version, which shows the platform and pack versions and
  commits (`GET /version`).
- 2026-10-05: Phase 0 (ADR-0013): the `VehiclePack` contract, canonical module ids,
  `/pack`, a data-driven UI, the fake pack and layering guards.
- 2026-10-05: Ostler handles (ADR-0014) and TRADEMARKS.md.
- 2026-09-30 to 2026-10-05: the Vibes as Code docs layer (ADR-0001), the Vite + React +
  TypeScript UI (ADR-0004), the always-on session logbook with GPS and map replay
  (ADR-0009), and replay notes, audio, motion and flags (ADR-0010).
- 2026-07-21 to 2026-09: the Discovery 2 Td5 diagnostics project this grew from: K-line
  transport, fast and slow init, KWP2000, Td5 and SLABS module layers, the live
  dashboard, sniffing and mapping tools, and the ESP32 K-line node.

### Changed
- 2026-10-05: repo split executed (ADR-0015). This repository became the
  vehicle-agnostic platform; the package was renamed `d2diag` → `openostler`, and the
  Discovery 2 specifics moved to the `d2diag` pack, which CI and Docker install from its
  repository.
- 2026-10-05: relicensed from MIT to AGPL-3.0-or-later for code and CC BY-SA 4.0 for
  vehicle data, with a CLA (ADR-0012). Earlier releases stay MIT; leijoma's MIT-licensed
  work stays credited.

[Unreleased]: https://github.com/openostler/ostler/commits/main
[0.0.1]: https://github.com/openostler/ostler/commits/93dc12d
