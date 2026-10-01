---
title: "ADR-0003 — Signal store is the single source of truth"
area: decisions
status: locked
version: 1.0
updated: 2026-09-30
summary: >
  LID field mappings live only in src/d2diag/signals/*.json with belagt/kandidat confidence, written via upsert_field; decoders, UI, automap and the ESP32 header all derive from it.
---

# ADR-0003 — Signal store is the single source of truth

- **Date:** 2026-09-30
- **Status:** accepted

## Context

A hand-copied decode table on the ESP32 drifted from the Python mapping and caused the
MAF mis-map. Confidence tags were the only defence against unverified mappings reaching
the UI.

## Decision

`src/d2diag/signals/*.json` is the only place a LID field mapping is defined.
- Code writes it via `upsert_field`.
- The ESP32 header is generated from it by `tools/gen_signal_header.py`.
- The UI reads metadata from it, not from a duplicated table.
- Every field is tagged `belagt` or `kandidat`.

## Consequences

- New sources, such as NanoCom captures, can only add `kandidat` entries.
- Promotion to `belagt` requires a car result logged in `references/test_plan.md`.
- The two dashboard HTML files currently duplicate a META table. The React UI
  (ADR-0004) removes this.

## Alternatives considered

- Mappings in Python code. Rejected: that was the original state, and it drifted.
