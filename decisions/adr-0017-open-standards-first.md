---
title: "ADR-0017 — Open standards first"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/standards.md, decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md]
summary: >
  Policy: prefer an open standard, spec or format over a bespoke one, and adopt it as files and conventions rather than heavy frameworks, keeping the stdlib-plus-pyserial runtime of ADR-0002. Lists the adopted set with verdicts (JSON Schema 2020-12, OpenAPI 3.1 and AsyncAPI 3, RFC 3339, GeoJSON, GPX, MQTT with HA discovery, OVMS topics and OwnTracks, REUSE/SPDX, SBOMs, SECURITY.md and CRA readiness, OpenSSF Scorecard, Conventional Commits, MADR, WCAG 2.2 AA, W3C design tokens, ICU/CLDR), the rule for adding a dependency or standard, and the reference-only list (ODX, SOVD, ISO/SAE 21434, UN R155/R156, J2534, …).
---

# ADR-0017 — Open standards first

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06: "try and use standard and open
  frameworks where possible … keep our project as best practice as possible")

## Context

- [Standards research](../references/research/standards.md) surveyed every layer and gave
  each candidate a licence check and a verdict: ADOPT, ADOPT-LATER, REFERENCE-ONLY, AVOID.
- [ADR-0002](adr-0002-layered-stdlib-core.md) keeps the Python runtime to stdlib plus
  pyserial; [ADR-0012](adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md) sets which
  licences we may reuse. "Best practice" must not mean frameworks on a Pi.

## Decision drivers

- Interoperability with peers (Home Assistant, OVMS, OBDb, OwnTracks) without adapters.
- Fewer bespoke formats to document and defend.
- Machine-checkable compliance (licences, SBOMs, accessibility) for a project that will
  sell hardware.
- A small, Node-free, dependency-light install.

## Decision

**Policy.**
1. Prefer, in order: an **open standard** with open governance → an **open de facto
   convention** → a **bespoke format**, documented with a JSON Schema. A bespoke choice
   says in its spec why no standard fits.
2. Adopt standards as **files, schemas and conventions**, not runtimes. Validators,
   generators and linters are **dev-only** (CI and tests, never installed on a Pi).
3. Licences follow ADR-0012. Paywalled ISO/SAE texts give us facts; we never copy their
   tables. UCUM-style licences that forbid derivatives are out.
4. `references/research/standards.md` is the living register of verdicts. This ADR fixes
   the policy and the initial set; later changes go in the register and the phase specs.

**Adding a dependency or standard.**
- **A Python runtime dependency** needs its own ADR (ADR-0002).
- **A UI framework** shipped in the bundle (state, routing, i18n, component kit) needs an
  ADR; a small library needs a line in its phase spec.
- **A new outbound protocol or data path** needs an ADR (GOALS anti-bloat rule).
- **A dev-only tool or a file-format standard** needs a register row with its licence, a
  verdict and the phase, plus a line in the spec that introduces it.
- Dropping an ADOPT verdict that this ADR lists needs a superseding ADR.

**Adopted set** (phase per [UI spec §10](../specs/2026-10-06-ui-architecture-design.md#10-phased-migration)):

| Standard | Verdict | Where it lands |
|---|---|---|
| COVESA VSS 6.1 | ADOPT | [ADR-0016](adr-0016-covesa-vss-canonical-signal-namespace.md) |
| OBDb signalsets (CC BY-SA) | ADOPT (data) | [ADR-0019](adr-0019-reuse-from-ovms-and-obdb.md) |
| JSON Schema 2020-12 | ADOPT | `schemas/*.schema.json`, custom keys `x-…`; `jsonschema` dev-only |
| OpenAPI 3.1.1 · AsyncAPI 3.0 | ADOPT (3.2 later) | `api/openapi.yaml`, `api/asyncapi.yaml`; a test fails on an undocumented route |
| RFC 3339 (UTC `Z`) · GeoJSON (RFC 7946) · GPX 1.1 | ADOPT | every wire timestamp; trace export; GPX kept (ADR-0009) |
| MQTT 3.1.1 + Home Assistant discovery | ADOPT (Phase 1 / U5) | our stdlib client; discovery generated from `metrics.json` |
| OVMS v3 topic tree · OwnTracks JSON | ADOPT-LATER (U5) | opt-in alias tree; opt-in location (ADR-0009) |
| REUSE 3.3 / SPDX ids · PEP 639 | ADOPT | `LICENSES/`, `REUSE.toml`, SPDX headers, `reuse lint` in CI |
| SBOMs (SPDX + CycloneDX) · build provenance | ADOPT (first release) | attached to each release |
| SECURITY.md · CRA readiness · UK PSTI | ADOPT | vulnerability process, support period; CRA role needs legal advice (open) |
| OpenSSF Scorecard · Dependabot · Best Practices badge | ADOPT | workflows; actions pinned by SHA |
| STRIDE threat model + OWASP ASVS (L1 local, L2 remote) | ADOPT (before U5) | `references/threat_model.md` |
| SemVer + Keep a Changelog | ADOPT | `CHANGELOG.md` |
| Conventional Commits 1.0 | ADOPT-LATER | "Area: sentence" now; enforced when releases are automated |
| MADR 4.0 template | ADOPT | new ADRs (from this set on) add *Decision drivers* and *Confirmation* |
| WCAG 2.2 AA · WAI-ARIA APG · axe-core | ADOPT (U1) | axe scan per layout class in Playwright |
| W3C design tokens (DTCG 2025.10) | ADOPT (U1) | `ui/tokens/*.tokens.json` → CSS variables at build |
| Unicode CLDR via `Intl` · ICU MessageFormat | ADOPT · ADOPT-LATER | `Intl` formatting now; ICU messages with a second locale |
| Web App Manifest · service workers over local HTTPS | ADOPT (U1) · ADOPT-LATER | manifest now; service worker once the [ADR-0021](adr-0021-local-https-on-the-device.md) trust setup ships |
| Ruff · mypy · pre-commit | ADOPT (dev-only) | `pyproject.toml`, `.pre-commit-config.yaml` |

**Reference-only** (read, borrow ideas or vocabulary, never depend on or copy): ASAM ODX
and SOVD / ISO 17978, ISO/SAE 21434 (TARA terms), UN R155/R156 (signed updates), SAE
J2534 (last in the CAN interface order, [ADR-0020](adr-0020-can-links-listen-only-by-default.md)),
SAE J1979, ISO 14229 / 15765 / 14230, COVESA VISS (payload shape `{value, ts}` from U3),
KUKSA, NHTSA and Android for Cars guidance (normative numbers for us), ISO 2575, QUDT,
Zephyr.

**Avoid:** Velocitas, uProtocol, Sparkplug B, LwM2M, UCUM, heavy server frameworks
(FastAPI, pydantic, paho as a hard dependency).

## Confirmation

- CI runs `reuse lint`, the schema tests, the route-documentation test, Scorecard and
  the `metrics.json` freshness check; U1 adds the axe scans.

## Consequences

- Several small artefacts (`schemas/`, `api/`, `LICENSES/`, `SECURITY.md`, CI workflows)
  arrive with U0, each in a small PR; standards research §8.1 gives the order.
- Open owner questions that touch this set: the `docs/` licence (REUSE forces a statement)
  and CRA legal advice. Local HTTPS is decided in ADR-0021.

## Alternatives considered

- **Adopt case by case, no policy.** Rejected: the owner asked for best practice as a rule.
- **Adopt full stacks (KUKSA, FastAPI + pydantic).** Rejected: breaks ADR-0002 on a Pi.
