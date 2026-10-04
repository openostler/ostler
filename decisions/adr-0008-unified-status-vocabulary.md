---
title: "ADR-0008 — One derived status vocabulary for every UI item"
area: decisions
status: locked
version: 1.0
updated: 2026-10-05
depends_on: [decisions/adr-0003-signal-store-source-of-truth.md, decisions/adr-0006-english-confidence-vocabulary.md, decisions/adr-0007-bcu-security-access.md]
summary: >
  Every dashboard item (input, output, setting, utility, fault page) has exactly one status — verified, candidate, sniff or untranscribed — derived from the signal store or the new command registry (src/d2diag/commands.py), never hand-copied, plus an orthogonal safety class read/actuator/service/gated that the server enforces.
---

# ADR-0008 — One derived status vocabulary for every UI item

- **Date:** 2026-10-05
- **Status:** accepted (extends ADR-0003 and ADR-0006; the signal-store vocabulary
  `proven`/`candidate` is unchanged)

## Context

The dashboard used six status vocabularies at once:
- menu `ok/maybe/todo`;
- store `proven/candidate`;
- fault-meaning confidence;
- output tags `verified/experimental`;
- module tags `verified/experimental/partial`;
- the docs' `ESTABLISHED/OPEN`.

The menu statuses were copied by hand and drifted. For example, the proven Td5 switches
showed as `todo`. Which outputs could run was decided only in the browser, so the server
would run any `output_*` it received.

## Decision

**Status.** Every UI item has exactly one:

| status | meaning | replaces |
|---|---|---|
| `verified` | proven on a car | ok, proven, verified, ESTABLISHED |
| `candidate` | mapped or implemented, unproven | maybe, candidate, experimental, partial |
| `sniff` | transcribed from the NanoCom, not mapped | todo, OPEN |
| `untranscribed` | a NanoCom page known to exist, fields not transcribed | (new placeholder) |

**Safety class**, independent of status: `read | actuator | service | gated`. `gated`
means never sent by this project. That covers:
- SecurityAccess unlock, EKA and key programming (ADR-0007);
- Td5 learn security code;
- airbag outputs;
- calibration writes (SLABS store heights, ACE calibrate/set calibrated).

**Derived, never copied.** `src/d2diag/catalog.py` derives an item's status from what it
links to:
- `sig`: the signal-store confidence (`proven` → verified).
- `actions`: the command registry `src/d2diag/commands.py`, which records per action
  `verified | experimental | planned` and its safety class.

A hand-written status is allowed only for items with no link (NanoCom fields not yet
mapped, untranscribed pages, and the session and fault functions).

**Server-enforced.** `POST /command` checks `commands.refusal()`:
- gated and planned actions are always refused;
- experimental actions are refused unless the client says it is in Experimental mode;
- the public server refuses every actuator and service action.

**Stable mode** shows only `verified` items and hides the status chips and coverage bars.

## Consequences

- One `StatusTag` and one `CoverageBar` in the UI. The Capabilities page goes; coverage
  is shown in place on every page.
- The admin `/map` keeps `ok/maybe/todo` through `catalog.legacy_status()`.
- A new action needs a registry entry, and `tests/test_commands.py` fails until it has
  one.
- The Td5 security-status read (`31 C0`/`33 C0`, sniffed from the NanoCom) ships as
  Experimental, read-only, behind a confirm. Learn security code stays gated.

## Alternatives considered

- **Keep `ok/maybe/todo` and fix the drift by hand.** Rejected: it drifted twice already.
- **Status on each component.** Rejected: the server could not enforce it.
