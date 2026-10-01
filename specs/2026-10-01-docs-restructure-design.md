---
title: Docs restructure, translation and confidence vocabulary — Design
area: specs
status: stable
version: 1.1
updated: 2026-10-01
depends_on: [specs/2026-09-30-vibes-adoption-design.md, decisions/adr-0006-english-confidence-vocabulary.md]
summary: >
  Phase A2 of the Vibes as Code migration: split every doc over 300 lines, make docs/
  canonical and references/ evidence-only, translate the last Swedish names and rename the
  confidence values belagt/kandidat to proven/candidate.
---

# Docs restructure, translation and confidence vocabulary — Design

## Goal

When this is done:
- no doc is over 300 lines;
- every fact lives in one place;
- no Swedish identifiers remain outside compatibility shims;
- every moved path is still reachable, which a link checker in CI verifies.

## Decisions (locked this session)

| Decision | Choice |
| -------- | ------ |
| Confidence values | `proven` / `candidate` (ADR-0006). Old values are accepted on read. |
| Menu transcription | Converted to one table per module under `references/menus/` |
| Canonical home | `docs/` holds facts. `references/` holds evidence, captures, plans and the test backlog. |
| Renames | `git mv`, with all inbound links and code comments updated in the same commit |

## Path map

| Old | New |
| --- | --- |
| `references/reference_tool_master_menu.md` | `references/menus/{overview,bcu-inputs,bcu-settings,bcu-outputs-utilities,ace,autobox,airbag,td5}.md` |
| `docs/Discovery2_Diagnostic_Protocol_Capability_Inventory_MASTER.md` | `docs/capability-inventory/{overview,td5,slabs,bcu,ace,autobox,airbag,open-questions}.md` |
| `docs/discovery-2-td5/kline-protocol.md` | hub + `docs/discovery-2-td5/kline/{physical-and-init,frames-and-services,session-lifecycle}.md` |
| `docs/discovery-2-td5/slabs.md` | `slabs.md` + `slabs-actuators-faults.md` |
| `references/slabs_protocol.md` | `references/slabs/{overview,init-timing,services-and-lids}.md` |
| `references/test_plan.md` | `test_plan.md` (open) + `test-plan-resolved.md` |
| `docs/discovery-2-td5/verification-todo.md` | merged into `references/test_plan.md` |
| `references/fault_codes.md` | merged into `docs/discovery-2-td5/fault-codes.md` |
| `references/full_taeckning_och_maf.md` | `references/td5-full-coverage-and-maf.md` |
| `references/portabilitet_andra_bilar.md` | `references/portability-other-vehicles.md` |
| `references/td5_externa_fynd.md` | `references/td5-external-findings.md` |
| `references/biltest_plan_slabs_bcu.md` | `references/car-test-slabs-bcu.md` |

## Architecture

- **`GLOSSARY.md`** defines the domain vocabulary once.
- **`skill/scripts/check_links.py`** checks two kinds of reference:
  - every relative markdown link resolves;
  - every `docs/…md` or `references/…md` path mentioned in Python source exists.
  - CI runs it next to the frontmatter validator.
- **`signals.normalize_confidence()`** is the only place that knows the legacy values.
- **The dashboard's Documents tab** registers `docs/` as well as `references/`. It
  recurses into subdirectories, so moved pages stay visible.

## Testing

- `pytest -q`, including new tests for confidence normalisation and recursive doc
  registration.
- The validator reports zero length warnings.
- The link checker passes, and INDEX.md is current.

## Non-goals

- Rewriting doc content beyond moving it, de-duplicating it and translating identifiers.
- The React UI (ADR-0004) and the NanoCom tooling (ADR-0005), which get their own specs.

## Changelog

- 2026-10-01 — Initial design.
- 2026-10-01 — Implemented. Index pages are `overview.md`, not `README.md`, because
  READMEs are excluded from the manifest. BCU menus are split three ways to stay under
  300 lines. `verification-todo.md` items were mapped to test IDs (new T-23) and the
  file was removed. A pre-existing broken link in `hardware/README.md` was fixed.
