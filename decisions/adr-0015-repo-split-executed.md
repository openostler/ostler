---
title: "ADR-0015 — Repo split executed: the openostler platform repo and the d2diag pack"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
depends_on: [decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0014-ostler-handles.md, specs/2026-10-06-phase0-vehiclepack-decoupling-design.md]
summary: >
  Records ADR-0013 step 2 as done: this repo (history kept with git filter-repo) is the platform, Python distribution and import "openostler"; the Discovery 2 code is the separate distribution "d2diag" (PACK at d2diag:PACK, entry point openostler.vehicle) in the discovery2-diag repo; the built-in fallback and import shim are gone; D2 integration tests are marked needs_pack and CI installs the pack; Docker installs platform + pack and replays the pack's demo log.
---

# ADR-0015 — Repo split executed

> **Amended by [ADR-0034](adr-0034-repo-boundaries.md), 2026-10-06:** `esp32/` moves to `ostler-firmware`, `hardware/` to `ostler-hardware` at PCB time; `tools/esp32_read.py` becomes a lab client of the node.

- **Date:** 2026-10-06
- **Status:** accepted. It carries out step 2 of ADR-0013, with the names fixed in
  ADR-0014.

## Context

- Phase 0 ([spec](../specs/2026-10-06-phase0-vehiclepack-decoupling-design.md)) moved every
  Discovery 2 specific under `src/d2diag/vehicles/lr_d2/`, behind the `VehiclePack`
  contract. It kept two Phase-0-only crutches: a built-in fallback
  (`d2diag.vehicles.lr_d2:PACK`) and an import-alias shim (`_compat.py`).
- ADR-0013 requires the split to keep history and to make the Dockerfile install the
  platform plus the D2 pack.

## Decision

**This repo is the platform.** It was cut from the monorepo with `git filter-repo`, so the
history of every kept path is preserved (`git log --follow` works). Two passes:

1. **Keep** (`--paths-from-file`):
   - `src/d2diag/`, `ui/`, `tests/`, `skill/`, `docs/`, `decisions/`,
     `references/research/`, `mac/`, `.github/`;
   - the root files;
   - the platform tools: `dashboard.py`, `deploy.sh`, `build_places.py`, `esp32_read.py`,
     `make_demo_session.py` and `module_scan.py` (`raw_analyze.py` is Td5-specific and stays
     in the pack);
   - the platform specs.
2. **Drop** (`--invert-paths`):
   - `src/d2diag/vehicles/` and `_compat.py`;
   - the pre-Phase-0 D2 paths (`td5/`, `slabs/`, `bcu/`, `airbag/`, `ace/`, `autobox/`,
     the four D2 sniff importers, `logbook/synth.py`, the demo sessions, the demo sniff
     log, `signals/*.json` and `dtc/*.json`);
   - `docs/discovery-2-td5/`, `docs/capability-inventory/` and `docs/rover-v8/`;
   - ADR-0005 and ADR-0007.

**Names (ADR-0014):**

| Thing | Name |
|---|---|
| Platform distribution and import | `openostler` (`src/openostler/`, renamed from `src/d2diag`) |
| Pack distribution and import | `d2diag`. Its modules are the former `vehicles/lr_d2/*` moved up: `d2diag.td5`, `d2diag.sources`, `d2diag.synth`, `d2diag.sniff.*`, … |
| Pack object | `d2diag:PACK`, registered as `[project.entry-points."openostler.vehicle"] lr_d2` |
| Pack repo | [JamesWrightDavid/discovery2-diag](https://github.com/openostler/ostler-pack-lr-d2) (branch `split-pack` until merged). It depends on `openostler`. |

**What moved where:**

| Stays in the platform | Moves to the D2 pack repo |
|---|---|
| comms core, `pack.py`, signals/dtc loaders, catalog, commands, menus, faultscan, modscan, generic sniff, gps, geo (+ GeoNames data), imu, logbook, web, community client | module layers, keygens, `signals/*.json`, `dtc/*.json`, menus/actions/sources/sniff spec, demo sessions and sniff log, NanoCom/fault-screen importers, `layout.json` |
| `ui/` (incl. `ui/src/vehicles/lr_d2/` views, a known coupling) and the committed `web/static` build | D2 tools (`verify_ecu`, `bcu_scan`, `diffmap`, `lid_sweep`, `map_*`, `nanocom_import`, the generators, …), `esp32/`, `hardware/` |
| platform docs, specs, ADRs (all but 0005/0007), `references/research/`, Vibes tooling | `docs/discovery-2-td5/`, `docs/capability-inventory/`, `docs/rover-v8/`, `references/` (D2), D2 specs, ADR-0005/0007 |
| Dockerfile, compose, `deploy.sh`, `mac/install.sh` | — |
| — | `server/` (the cloud seed) is in neither: it goes to the private `ostler-cloud` repo |

**Loader.**

- `_BUILTIN_FALLBACK` is removed. With no pack installed, `active_pack()` raises
  `NoVehiclePackError`. The error names the `openostler.vehicle` group and how to install
  a pack.
- The `_compat` shim is removed.
- The layering guard now forbids any `d2diag` import or reference in `src/openostler/`.

**Tests.**

- **Platform tests** run on `tests/fake_pack.py`. Modules marked `fake_pack` activate
  `FAKE_PACK` automatically.
- **Integration tests** that exercise the D2 pack stay here and are marked `needs_pack`:
  web, UI contract, e2e server, sessions and replay, logbook and index, catalog drift
  guards, and some others. Without the pack they skip, with a reason.
- **CI** installs the pack (`pip install --no-deps "d2diag @ git+…@${PACK_REF}"`) and sets
  `OSTLER_REQUIRE_PACK=1`, so a missing pack fails instead of skipping.
- **Pure D2 unit tests** moved to the pack: td5, slabs, bcu*, airbag, identifiers, keygen,
  faults, generators, importers, dtc data and the Phase 0 golden.

**Deploy.**

- The Dockerfile installs the platform, then the pack at `PACK_REF` (build arg, default
  `main`).
- The dashboard's `--replay pack` replays `active_pack().demo.sniff_log`, so no
  site-packages path is hard-coded. The healthcheck is unchanged.

## Consequences

- A pack is now a hard runtime requirement for the dashboard and the e2e suite, and an
  optional one for `pytest`.
- The platform's UI still bundles the D2 views (`ui/src/vehicles/lr_d2/`, imported from
  `main.tsx`). Shipping pack UI separately is an open item (TODO.md).
- CI tracks the pack's `split-pack` branch until it is merged; then `PACK_REF` becomes
  `main`.
- The repo moves to `openostler/ostler` once the org exists (ADR-0014 checklist).
- The shared constitution is owned here (ADR-0013). The pack's CLAUDE.md links to it.

## Alternatives considered

- **Vendor the pack as a git submodule or subtree.** Rejected: it recouples the repos and
  defeats the entry-point contract.
- **Keep the built-in fallback for convenience.** Rejected: it is an import of a pack by
  name, which ADR-0013 forbids; the explicit error is clearer.

## Amendments (2026-10-06)

Amended by [ADR-0034](adr-0034-repo-boundaries.md) (repo boundaries). The split as
executed above stands; the D2 pack column changes as follows.
1. **`esp32/`** leaves the D2 pack for `ostler-firmware` when that repo is created
   (history kept with `git filter-repo`); its D2-specific parts become the pack's JSON and
   its keygen C plugin.
2. **`hardware/`** leaves the D2 pack for `ostler-hardware` (CERN-OHL-S) when PCB work
   starts.
3. **`tools/esp32_read.py`** stays in the platform as a lab client of the node, not as
   part of the firmware.
