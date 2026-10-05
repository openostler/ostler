---
title: "ADR-0019 — Reuse from OVMS and OBDb"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/ovms_reuse.md, references/research/ovms.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0018-ui-architecture-decisions.md]
summary: >
  Import every OVMS vehicle (EVs included) and every command the licence and legal position allow; the only exclusions are licence or legal ones (dealer-database lineage such as the BMW i3/Mini SGBD tables and DDT4all writes; non-open files such as the Roadster _ctp files; GPL-3-only material such as CanZE-derived Zoe PIDs, which may live in a separately licensed GPL-3 pack). Imported commands keep their safety tier and ship disabled behind Experimental, service mode, Parked, the server gate and per-action confirmation; Tier 4 writes stay non-runnable until their own ADR. OBDb stays the primary source for polled data; the MIT notice travels; tools/import_ovms.py has a human review gate; the OVMS gauge geometry is ported to DOM SVG.
---

# ADR-0019 — Reuse from OVMS and OBDb

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06: "reuse what we can from OVMS, especially
  already-decoded vehicles"; then: import **all** OVMS vehicles, EVs included, and make
  **all** functionality available, gated in the app like Experimental mode)

## Context

- The [OVMS reuse audit](../references/research/ovms_reuse.md) read all 48 OVMS v3
  vehicle modules at `7c87784`: almost all EV, all CAN, no K-line, nothing for the D2.
  About 3,200 poll entries and 490 passive CAN IDs, almost no tests, and several scaling
  bugs on a light read. Many modules carry commands that write or actuate (lock, climate,
  charge control, wake, the Volt's engine on/off, SEVCON reconfiguration).
- OBDb publishes per-model signalsets in our schema, CC BY-SA 4.0 like our data, with
  YAML tests. It overlaps about 20 OVMS modules.
- OVMS is MIT "for the majority", with licence exceptions inside vehicle directories.

## Decision drivers

- As many vehicles and functions as possible, as soon as possible.
- Licence-clean data and code that fit both the AGPL build and the commercial licence.
- No write reaches a car by default; the safety tiers and the constitution are unchanged.

## Decision

**Import everything the licence and legal position allow.**
- **All MIT modules' decodes**, EVs included: poll tables, passive-CAN decodes, state
  semantics and the models OBDb lacks.
- **All commands**, including writes and actuations (climate, charge control,
  lock/unlock, wake, headlights, valet, the Volt engine on/off), each imported with its
  safety tier (ADR-0018, UI spec §7).

**The only exclusions are licence and legal ones, never functional:**

| | Material | Rule |
|---|---|---|
| a | **Dealer-database lineage:** `vehicle_bmwi3` / `vehicle_minise` `ecu_definitions/` and `dev/*.json` (GPL-3, from BMW SGBD via Ediabaslib); the DDT4all-derived smart EQ and Zoe Ph2 write sets | **Excluded, never shipped** (ADR-0012, the DMCA lesson). Use OBDb's BMW-i3 / MINI repos; read-only DIDs may be cross-checked |
| b | **Non-open files:** Roadster `vehicle_teslaroadster_ctp.*` ("licence granted for inclusion on OVMS") | Excluded, or imported only if upstream relicenses |
| c | **GPL-3-only material:** the Zoe Ph1 PID list "extracted from CanZE" | Compatible with AGPL but would break the commercial dual licence, so **kept out of core and our CC BY-SA packs**. It **may** live in a separately licensed GPL-3 pack if a contributor wants that |

Firmware third-party code (wolfSSL, wolfSSH, mongoose, Highcharts) is never copied.

**How imported commands are gated.** Nothing imported is runnable by default.
- Every imported action is `status: experimental` and `remote: false`. It is visible and
  runnable only in **service mode with Experimental items on**, **Parked**, through the
  **server gate**, with a **per-action confirmation** that names the action and its source.
- **Tier 2 (actuate) and Tier 3 (procedure)** imports run under those gates plus their
  tier's own friction (preconditions, Stop, timeout, wizard).
- **Tier 4 (code: writes, security access, coding, controller reconfiguration)** imports
  ship **listed and disabled**. The constitution and ADR-0018 (Q11) require an ADR for any
  write path, so enabling a Tier 4 class (for example "OVMS-imported charge-limit writes
  for module X") needs its own ADR; once accepted it runs under all the gates above.
- The importer assigns **Tier 4 to any command it cannot classify**; a reviewer may lower
  it only with a reason recorded in the action's evidence.

**Source order for data.** OBDb is the primary source for polled data where it has the
model (`generic_obd2` imports OBDb SAEJ1979; OVMS `vehicle_obdii` is not used). OVMS is
the source for passive CAN, state semantics and models OBDb lacks, and cross-check
evidence elsewhere. Imported fields are `candidate` and never rise higher by import; a
conflict with OBDb blocks promotion until a car reading settles it.

**Attribution.** The OVMS MIT notice and each source file's `(C)` lines travel with any
ported code and imported table (`NOTICE`, `THIRD_PARTY_LICENSES.md`). Every imported
signal and action carries `x-ostler.evidence.source` (repo, SHA, file, line).

**The importer, `tools/import_ovms.py`**, is planned (audit §4; its own spec before code).
It parses a pinned OVMS checkout (tree-sitter-cpp, dev-only), maps names through the
ADR-0016 alias table (ICE modules by PID meaning, never fuel as `v.b.soc`), and writes to
`build/ovms_import/<module>/`, never committed directly. **A human review gate** promotes
output into a pack repo: units and signedness against a fixture, metric semantics, wheel
order, provenance (a/b/c above), and every action's tier and gating.

**Order of work** (all modules are in scope; this is sequence, not a shortlist):
`jaguaripace`, `voltampera`, the GM ICE trio, `nissanleaf`, `maxus_edeliver3`, then the
rest; `vwegolf.dbc` through cantools (dev-only) as a quick win.

**Gauges.** The react-native-vehicle-gauges (MIT) geometry is ported to DOM SVG in our
`Gauge` components, with the notice kept and colours from our tokens. No OVMS C++ is
ported; poller ideas are reimplemented in Python with a citation.

## Confirmation

- Importer tests: every action has a tier, `experimental`, `remote: false`, and a source;
  unclassified commands are Tier 4; nothing from list a/b/c appears in output.
- Server tests: an imported action is refused outside service mode, Experimental, Parked
  or without confirmation; a Tier 4 import is always refused until enabled by an ADR.

## Consequences

- Imported data lands in pack repos (CC BY-SA); a GPL-3 pack, if any, is a separate repo.
- The Experimental surface grows a lot; the review gate is the bottleneck by design.

## Alternatives considered

- **A shortlist, commands left out** (the first draft of this ADR). Rejected by the owner.
- **Vendor OVMS C++.** Rejected: ESP-IDF bound; Python libraries already exist.
