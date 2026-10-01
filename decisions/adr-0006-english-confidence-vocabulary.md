---
title: "ADR-0006 — English confidence vocabulary (proven/candidate)"
area: decisions
status: locked
version: 1.0
updated: 2026-10-01
depends_on: [decisions/adr-0003-signal-store-source-of-truth.md]
summary: >
  The confidence values in the signal store, snapshot and UI are renamed from Swedish
  belagt/kandidat to proven/candidate; the loader still accepts the old values.
---

# ADR-0006 — English confidence vocabulary (proven/candidate)

- **Date:** 2026-10-01
- **Status:** accepted (amends the vocabulary of ADR-0003; its decision is unchanged)

## Context

The repo is public and English-only for new content. The confidence tag was still
Swedish (`belagt`/`kandidat`) in the signal-store JSON, the snapshot (`c`), the
dashboard and the tools. Contributors and agents had to learn two foreign words to read
the most important field in the data model.

## Decision

The confidence values are now `proven` and `candidate`.
- `signals.normalize_confidence()` maps the legacy values (`belagt`, `kandidat`) to them.
- The signal store loader and `upsert_field` call it, so old files, captures and
  community payloads keep working.
- Every writer emits the new values.

## Consequences

- The JSON store, tools, sources, dashboards and tests change in one commit.
- Consumers outside this repo that compare `c` against `"kandidat"` must update. Only
  the two bundled dashboards do this, and both accept either value until the React UI
  replaces them.

## Alternatives considered

- Keep the Swedish values as fixed project vocabulary. Rejected: it contradicts the
  English-only rule, and it is the one term every contributor meets.
