---
title: "ADR-0025 — Reuse and licences: pragmatic"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0019-reuse-from-ovms-and-obdb.md, references/research/muki01/README.md, THIRD_PARTY_LICENSES.md]
summary: >
  Amends ADR-0019 (c). Reading any source and reimplementing its ideas, protocols, formulas and behaviour in our own words is fine whatever the licence. Descriptive text (fault-code descriptions, SAE J2012 wording) is never copied verbatim. GPL-3.0(-or-later) repos may be taken whole under their current licence, as a conscious per-use choice, into clearly marked GPL-3 modules or (preferably) packs with SPDX headers and REUSE annotations, so core stays commercially licensable (ADR-0012); our own and permissive code goes anywhere. GPL-2.0-only code and dealer-database material stay out; non-commercial and doubtful-grant sources are reimplement-only. No hunting licence dates.
---

# ADR-0025 — Reuse and licences: pragmatic

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06: "be less picky … the aim is pragmatic reuse").
  **Amends** [ADR-0019](adr-0019-reuse-from-ovms-and-obdb.md) exclusion (c); ADR-0019's
  exclusions (a) and (b), gating and attribution are unchanged.

## Context

- The [muki01 synthesis](../references/research/muki01/README.md) spent much effort on
  licence dates: the repos moved from MIT to GPL-3.0 plus a commercial licence on
  2026-10-03, and the KLine library carries non-commercial file headers under a GPL-3.0
  root. The draft rule ("port only from a pinned pre-relicence commit") made reuse slow and
  brittle for little gain.
- ADR-0012 already lists GPL-3 as compatible with our AGPL-3.0-or-later code. The catch is
  the commercial dual licence: third-party GPL-3 code cannot be sublicensed commercially.
- ADR-0019 (c) kept GPL-3 material out of core and our packs entirely.

## Decision drivers

- As much reuse as the law allows, with little ceremony.
- A core that stays commercially licensable (ADR-0012).
- No legal exposure: the DMCA lesson, and no copied creative text.

## Decision

**Ideas are free.** Reading any source, whatever its licence, and reimplementing its
ideas, protocols, formulas, timings and behaviour **in our own words** is fine.

**Descriptive text is never copied verbatim**: fault-code descriptions, SAE J2012 wording,
manual prose and similar creative text. We write our own, or use an openly licensed set.

**By licence, under the repo's current licence** (no hunting for older dates; a
permissive copy we already hold stays usable under its own terms):

| Source | What we may do |
|---|---|
| Our own code; MIT, BSD, Apache-2.0 and other permissive code | Copy anywhere, notice kept |
| **GPL-3.0 / GPL-3.0-or-later** | Take whole, as a **conscious per-use choice**, into a **clearly marked GPL-3 module or pack**: preferably a separate pack, else a module with an SPDX `GPL-3.0-or-later` header and a REUSE annotation that core never imports. Or reimplement |
| GPL-2.0-only | Reimplement only; it cannot be combined with AGPL-3 |
| Non-commercial terms, or file headers that impose them | Ideas and facts only: reimplement, never copy code |
| Doubtful grant (unclear upstream authorship, no licence file) | Reimplement only |
| Dealer-database-derived material (SGBD, ODX/DDT write sets, NavCoder, training PDFs) | **Excluded** (ADR-0019 (a), DMCA). Gating it in the app changes nothing |

**Keeping core commercially licensable.** GPL-3 modules are optional: core and our
CC BY-SA data packs never import or embed them, and the commercial build leaves them out.
Each use is recorded in `THIRD_PARTY_LICENSES.md` (repo, commit, files, licence) with the
notice kept.

**Evidence:** muki01 relicensed its repos to GPL-3.0 on 2026-10-03, so they may now be
taken whole into GPL-3 modules or packs; the `OBD2_KLine_Library` files still carry
non-commercial headers, so it stays reimplement-only; its `errorCodes.js` DTC text stays
out as descriptive text.

## Confirmation

- `reuse lint` passes; every GPL-3 file carries `GPL-3.0-or-later` and sits under a path
  annotated as such.
- `tests/test_layering.py` gains a rule: no core or data-pack module imports a GPL-3 one.
- The pack review gate (ADR-0019) checks provenance against the table above.

## Consequences

- ADR-0019 (c)'s Zoe Ph1 PID list may now sit in a marked GPL-3 pack or module.
- The muki01 reuse column becomes "GPL-3 module/pack, or reimplement".
- The commercial build needs a list of excluded GPL-3 modules.

## Alternatives considered

- **Facts-only for anything relicensed, ports from pinned commits only** (the first draft
  of this ADR). Rejected by the owner: too picky for the gain.
- **Allow GPL-3 into core.** Rejected: it would end the commercial licence (ADR-0012).
