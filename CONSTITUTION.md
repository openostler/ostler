---
title: Constitution
area: root
status: stable
version: 1.3
updated: 2026-10-06
summary: >
  Hard rules for every agent and contributor: the five Vibes as Code operating
  principles plus this project's protocol, layering, safety and data-honesty invariants.
  Load in full; never summarize.
---

# Constitution

> Hard rules. Loaded by every agent. Never summarized away. Append-only in
> spirit: amend deliberately, record the amendment in the changelog.

## The five operating principles

1. **Progressive disclosure is the architecture.** ~100-token discovery; load
   bodies on demand; every directory has a small CLAUDE.md; every
   manifest-eligible file has frontmatter; the root stays minimal.
2. **One topic per file, ~300 lines max.** Split monoliths along their seams.
3. **Single source of truth, no duplication.** A fact lives in one file;
   everything else links.
4. **Decisions are immutable ADRs (append-only); specs are living documents**
   (versioned, with changelogs).
5. **Hard rules live in non-compressible places**, which means this file.

## Project invariants

### Layering and data
- **Core never imports from the consumer layer.** `transport`, `kline`, `kwp2000`,
  `session`, `ports`, module decoders and `signals` must not import `web` (enforced by
  `tests/test_layering.py`). `web/sources.py` is the boundary. See [SCOPE.md](SCOPE.md).
- **The platform never imports a vehicle pack** (ADR-0013, ADR-0015). Vehicle specifics
  live in separate pack distributions (the reference pack is `d2diag`, the Discovery 2
  repo) and reach the platform only through the `VehiclePack` contract
  (`openostler.pack.active_pack()`, entry-point group `openostler.vehicle`). Platform code
  names no pack, module id or alias. `tests/test_layering.py` enforces both rules.
- **A pack's `signals/*.json` is the single source of truth for its LID field mappings**
  (for the Discovery 2 pack, `src/d2diag/signals/` in its repo).
  Write it only via `upsert_field`; never hand-paste `Signal(...)` rows. The ESP32 decode
  header is generated from it, never hand-copied.
- **Confidence is honest.** Every field is `proven` (verified against the car) or
  `candidate` (derived or unverified). Nothing is promoted to `proven` without a car
  result recorded in the pack's car-test plan (for the D2 pack,
  [references/test_plan.md](https://github.com/JamesWrightDavid/discovery2-diag/blob/main/references/test_plan.md)).

### Protocol rules (violating these only shows up against the real car)
- **Always end a module with `EcuSession.release()`**, on module switch and error paths
  alike. Never use bare `close()`. `_establish` sends a best-effort `82` before every init.
- **SLABS is polled lightly:** ~1 Hz keepalive with a bare `3E` (never `3E 01`), heights
  each cycle, faults at most every 10th poll.
- **Keep `tolerant=True`** on KWP2000 for cheap KKL cables.
- **K-line is a shared bus:** one module at a time, establish → read → release.
- **K-line access is serialized on the poll thread.** Only server-state commands run
  inline on the HTTP thread.
- **macOS serial ports are `/dev/cu.*`**, never `/dev/tty.*`.

### Safety
- **Airbag/SRS is read-only by construction:** no clear, no outputs, no security writes.
- **Actuator tests and any write/coding/security service** stay behind an explicit
  confirmation, and are documented as stationary with ignition on.
- **Sniffed commands from a reference tool (e.g. NanoCom) are never replayed** to the car
  for a write, coding or SecurityAccess function without its own ADR (see ADR-0005).
- **Raw car captures (`logs/`, `captures/`) are never committed:** they may contain VIN
  or EKA data.

### Code and tests
- **Zero runtime dependencies above pyserial** for the Python package. The React/TS UI is
  built ahead of time and shipped as static files (ADR-0004), so a Pi install stays
  Node-free.
- **Tests run without hardware** against `tests/fakes.py::FakeKLineEcu`. Platform tests run
  against `tests/fake_pack.py`; tests that need the Discovery 2 pack are marked
  `needs_pack`, and CI installs the pack so they never skip there.
- **English everywhere** for new content: code, comments, docs and commits. When you
  touch Swedish text, translate it.

## Authoring rules

- Frontmatter is required on every manifest-eligible `.md` (not README.md, CLAUDE.md,
  INDEX.md). Areas: `root|docs|references|hardware|decisions|specs`.
- After editing docs, run `python3 skill/scripts/validate_frontmatter.py`, then
  `python3 skill/scripts/build_index.py`. `INDEX.md` is generated. Never hand-edit it.
- No code, scaffolding or implementation until a design is approved (a spec in
  `specs/`). Car findings route per the pack's
  [test plan](https://github.com/JamesWrightDavid/discovery2-diag/blob/main/references/test_plan.md).

## Changelog

- 2026-09-30 — Initial constitution: adopted Vibes as Code; invariants lifted from the
  former CLAUDE.md and SCOPE.md.
- 2026-10-01 — Confidence values renamed to `proven`/`candidate` (ADR-0006).
- 2026-10-06 — Vehicle specifics moved behind the `VehiclePack` contract; the signal store path is now `src/d2diag/vehicles/lr_d2/signals/` (ADR-0013, Phase 0).
- 2026-10-06 — Repo split executed (ADR-0015): this is the platform repo (`openostler`);
  vehicle packs are separate distributions; the signal store lives in each pack; the
  `needs_pack` test rule added.
