# CLAUDE.md — Entry Point

**Ostler — the open vehicle platform** (OpenOstler; ADR-0013, ADR-0014, ADR-0015). This
repo is the vehicle-agnostic platform: the K-line/KWP2000 comms core, the `VehiclePack`
contract, the session logbook and the dashboard. Vehicle specifics live in separate
vehicle packs; the reference pack is the Land Rover Discovery 2 pack `d2diag`
([ostler-pack-lr-d2](https://github.com/openostler/ostler-pack-lr-d2)). This repo
follows the [Vibes as Code](https://github.com/JamesWrightDavid/Vibes-as-Code) method:
orient cheaply, then load on demand.

## Read first, every session

1. **[INDEX.md](INDEX.md)** is the manifest: every doc's path, area, status and
   ~100-token summary, plus reading paths.
2. **[CONSTITUTION.md](CONSTITUTION.md)** holds the hard invariants (layering, protocol,
   safety, data honesty). Load it in full and never summarize it. It is shared with the
   packs. Process guidelines are in [CONTRIBUTING.md](CONTRIBUTING.md) (ADR-0047).

## Then load on demand

- The code map, commands and key seams: [docs/architecture.md](docs/architecture.md).
- The HTTP and event API contracts (OpenAPI, AsyncAPI) and how to keep them current:
  [api/README.md](api/README.md).
- What the project is for and where it is going: [GOALS.md](GOALS.md).
- Mission and layering boundary: [SCOPE.md](SCOPE.md).
- What moved where at the split: [ADR-0015](decisions/adr-0015-repo-split-executed.md).
- Why a choice was made: [decisions/](decisions/CLAUDE.md).
- Designs in progress: [specs/](specs/CLAUDE.md).
- Notable changes and the versioning policy: [CHANGELOG.md](CHANGELOG.md); reporting
  vulnerabilities: [SECURITY.md](SECURITY.md).
- Vehicle knowledge and the car-test backlog: the pack's repo (for the D2,
  `references/protocol_state_handoff.md` and `references/test_plan.md` there).

## Working rules

These apply to work in this repo and the `openostler` organisation's repos. Community and
third-party authors are exempt from the process rules (UX first, spec first); the
constitution's invariants bind everyone (openness round,
[ADR-0047](decisions/adr-0047-openness-round.md)).

- UX first (ADR-0045, as amended): for anything a user sees in the core repo, write the UX
  brief in `references/design/briefs/` and get it approved; then build the UI against
  recorded fixtures (labelled synthetic fixtures are fine for states, previews and mocks);
  only then wire it to real services. Backend-only integrations need only a setup-page
  brief. The owner reviews built screens only for core safety surfaces.
- Design before code for core and safety paths: write a spec in `specs/` and get it
  approved before implementing. Experiments may land behind an off-by-default flag.
- Style rules are defaults, not laws: themes, add-ons and users may restyle anything within
  [visual §13](specs/2026-10-07-visual-design-system-design.md) and the
  [theme engine](specs/2026-10-07-theme-engine-design.md) (render check, protected surfaces,
  required parts). Do not reintroduce hard caps or bans on taste; make them defaults.
- Run `pytest -q` before committing code. It needs no hardware. Install the D2 pack
  (`pip install --no-deps -e <pack checkout>`) so the `needs_pack` tests run too.
- The platform never imports a pack (`tests/test_layering.py`).
- Run `ruff check .` and `reuse lint` too (or `pre-commit install` once). New source
  files need an SPDX header (`reuse annotate`); add notable changes to `CHANGELOG.md`.
- After editing docs, run `python3 skill/scripts/validate_frontmatter.py`, then
  `python3 skill/scripts/build_index.py` (pre-commit and CI also run them). `INDEX.md` is
  generated, so never hand-edit it.
