---
title: Vibes as Code adoption — Design
area: specs
status: stable
version: 1.0
updated: 2026-09-30
depends_on: [decisions/adr-0001-adopt-vibes-as-code.md]
summary: >
  Design for bringing the fork onto Vibes as Code, docs layer only: what is added, how
  existing docs are tagged, what is deferred, and how it is verified.
---

# Vibes as Code adoption — Design

## Goal

Make the repo agent-navigable without changing protocol code. It is done when:
- the validator passes,
- INDEX.md is generated,
- the test suite is still green,
- CI enforces all three.

## Decisions (locked this session)

| Decision | Choice |
| -------- | ------ |
| Scope of first pass | Docs layer only: no dedupe, no translation, no file splits |
| Tooling | Vendor upstream `skill/scripts/` with a project area enum |
| Areas | `root, docs, references, hardware, decisions, specs` |
| Front end | React + TypeScript, Python backend kept (ADR-0004), separate spec |
| NanoCom | Passive ESP32 sniff, candidate-only import (ADR-0005), separate spec |

## Architecture

- **Root:**
  - `CLAUDE.md`: a slim entry point.
  - `CONSTITUTION.md`: hard rules lifted from the old CLAUDE.md and SCOPE.md.
  - `INDEX.md`: generated.
  - `SCOPE.md`: unchanged boundary document.
- **`docs/architecture.md`:** the code map and seams moved out of the old CLAUDE.md.
- **`decisions/`:** ADR-0001 to ADR-0005.
- **`specs/`:** this design, and the ones that follow it.
- **`skill/scripts/`:**
  - Vendored validator and index builder.
  - Excludes vendored code (`muki01`), raw data (`logs/`, `captures/`) and
    `THIRD_PARTY_LICENSES.md`.
  - Warns when a file is over 300 lines.
- **Every directory with docs or code gets a ≤25-line `CLAUDE.md`.**
- **`web/docs.py` strips frontmatter** before rendering, so the dashboard's Documents tab
  is unchanged for readers.

## Testing

- `python3 skill/scripts/validate_frontmatter.py` exits 0.
- `python3 skill/scripts/build_index.py` writes INDEX.md.
- `pytest -q` passes, including a new docs test for frontmatter stripping.
- A GitHub Actions workflow runs all three and fails if INDEX.md is stale.

## Non-goals (follow-ups)

- **Split over-length docs along their seams:** `reference_tool_master_menu.md`,
  `slabs_protocol.md`, `kline-protocol.md`, the capability inventory, `slabs.md`,
  `test_plan.md`.
- **Dedupe `docs/` against `references/`.** Make `docs/` the public canonical source and
  `references/` the working notes that link to it.
- **Translate Swedish filenames and text** (`full_taeckning_och_maf.md`,
  `portabilitet_andra_bilar.md`, `td5_externa_fynd.md`, `biltest_plan_slabs_bcu.md`).
- **Replace hard-coded test counts** in README and TODO with a pointer to CI.

## Changelog

- 2026-09-30 — Initial design and adoption.
