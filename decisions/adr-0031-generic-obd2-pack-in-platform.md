---
title: "ADR-0031 — generic_obd2 pack ships in-platform under packs/"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0015-repo-split-executed.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, specs/2026-10-06-j1979-service-layer-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Amends the repo split of ADR-0013 and ADR-0015 for one pack only: generic_obd2, the OBD-II fallback, is a separate distribution (ostler-pack-generic-obd2, import ostler_generic_obd2) kept in the platform repo at packs/generic_obd2/ and installed by default by the Dockerfile, tools/deploy.sh and mac/install.sh. It is marked fallback, so the loader picks it only when no specific pack is installed; OSTLER_VEHICLE still wins. The platform package still never imports a pack, and the layering test still enforces that. Every other pack lives in its own repo named ostler-pack-<x>.
---

# ADR-0031 — generic_obd2 pack ships in-platform under packs/

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06; Q10 of the
  [packs spec](../specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md)).
  **Amends** the repo split of [ADR-0013](adr-0013-repo-split-and-vehicle-pack-contract.md)
  and [ADR-0015](adr-0015-repo-split-executed.md) for this one pack; does not supersede
  either.

## Context

- ADR-0013 puts vehicle packs in their own repos, and ADR-0015 removed the built-in
  fallback pack: with no pack installed, `active_pack()` raises `NoVehiclePackError`.
- The [UI architecture](../specs/2026-10-06-ui-architecture-design.md) §8.2 wants a car
  with no specific pack to still work, through a generic OBD-II fallback. ADR-0019 names
  `generic_obd2` as the OBDb SAEJ1979 importer.
- `generic_obd2` moves in lockstep with platform code: the
  [J1979 layer](../specs/2026-10-06-j1979-service-layer-design.md), K-line detection,
  CanLink and the connect-time capability builder. In its own repo every change there
  would be two PRs and a pinned ref.
- Vehicle data (PIDs, metrics, DTC text) still belongs in a pack, not in
  `src/openostler/` (owner, 2026-10-06).

## Decision

**`generic_obd2` lives in the platform repo, as its own distribution.**
- Path `packs/generic_obd2/` with its own `pyproject.toml`; distribution
  `ostler-pack-generic-obd2`, import `ostler_generic_obd2`, pack id `generic_obd2`, entry
  point `[project.entry-points."openostler.vehicle"] generic_obd2 =
  "ostler_generic_obd2:PACK"`. It depends on `openostler`.
- `src/openostler/` never imports it, by name or path; the platform's setuptools package
  discovery stays `src/` only, so the platform wheel does not contain it. The layering test
  forbids `ostler_generic_obd2` in `src/openostler/` as it forbids `d2diag`.

**It is installed by default and marked fallback.**
- The Dockerfile, `tools/deploy.sh` and `mac/install.sh` install it beside the platform. A
  pip-only platform install does not; the `NoVehiclePackError` hint says how.
- `VehiclePack` gains `fallback: bool = False` (defaulted, so `PACK_API_VERSION` stays 1);
  `generic_obd2` sets it. The loader: `OSTLER_VEHICLE` wins; otherwise exactly one
  non-fallback pack is used; with none, the single fallback pack; several non-fallback
  packs still raise and ask for `OSTLER_VEHICLE`. `NoVehiclePackError` remains for an
  install with no pack at all.

**This exception is for this one fallback pack only.** Every other pack, including any
later OBD-based or make-specific pack, lives in its own repo named `ostler-pack-<x>`
(import `ostler_<x>`); a make may appear in the name descriptively, never in our brand. The
Discovery 2 pack keeps `discovery2-diag` / `d2diag`.

## Confirmation

- Layering test: no `ostler_generic_obd2` (or `packs/`) import or path in `src/openostler/`.
- Loader tests: with `lr_d2` and `generic_obd2` installed, `lr_d2` is picked; with
  `generic_obd2` alone, it is picked; with two non-fallback packs, the loader raises;
  `OSTLER_VEHICLE` overrides each case.
- Platform CI installs `packs/generic_obd2[dev]` and runs its tests and contract test; the
  D2 job runs with both packs installed and still resolves `lr_d2`.
- The built platform wheel contains no file from `packs/`.

## Consequences

- One repo holds two distributions; the root `REUSE.toml` marks the pack's data
  CC-BY-SA-4.0 and its code AGPL-3.0-or-later.
- A J1979 or capability-builder change and its pack-side change land in one PR.
- Docker, Pi and Mac installs no longer hit the `NoVehiclePackError` dead end.
- If the pack later needs its own release cadence, `git filter-repo` moves it to its own
  repo with no name change; this ADR is then superseded.
- The packs spec's "ADR amending ADR-0015" item is this ADR.

## Alternatives considered

- **A built-in pack inside `src/openostler/`.** Rejected: it breaks "the platform never
  imports a vehicle pack" and ADR-0015, and puts vehicle data in the platform package.
- **Its own repo (`ostler-pack-generic-obd2`).** Rejected for now: lockstep changes become
  two PRs and a pinned ref, and a car with no pack works only if the installer remembers
  it. It stays the exit if the cadence diverges.
- **Bring back an unconditional built-in fallback.** Rejected: ADR-0015 removed it because
  it imported a pack by name.
