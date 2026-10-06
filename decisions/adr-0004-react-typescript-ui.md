---
title: "ADR-0004 — React + TypeScript dashboard, shipped as static assets"
area: decisions
status: locked
version: 1.1
updated: 2026-10-06
summary: >
  The dashboard moves from two single-file vanilla-JS pages to one Vite + React + TypeScript app, built ahead of time and served as static files by the existing Python server.
---

# ADR-0004 — React + TypeScript dashboard, shipped as static assets

> **Amended by [ADR-0035](adr-0035-languages-by-tier.md), 2026-10-06:** UI types are generated from OpenAPI/AsyncAPI; the phone app is the same build packaged with Capacitor.

- **Date:** 2026-09-30
- **Status:** accepted

## Context

The UI is two divergent single-file pages. `dashboard.html` is about 1,260 lines and
`dashboard_v2.html` about 1,130, each with about 750 lines of untyped inline JS. They have
duplicated signal metadata, no JS tests and some Swedish identifiers. The maintainer's
projects are meant to be worked on easily by AI agents, and they favour TypeScript
because the compiler rejects hallucinated properties. The UI will grow: a mapping
console, NanoCom import review and charts.

## Decision

Build a single `web/ui/` app with Vite, React and TypeScript (strict), tested with
Vitest and Testing Library.
- The TS types mirror the Python snapshot contract (`{status, signals, faults}`,
  `/snapshot`, `/events`, command routes). A test fails when the types drift from the
  contract.
- The build output is committed under `src/d2diag/web/static/` and shipped as
  package-data. Python users and the Pi never need Node.
- The Python backend is unchanged (ADR-0002).
- The old pages are removed only when the new app reaches feature parity.
- Implementation is specified in its own spec before any code is written.

## Consequences

- Easier: typed, componentised UI that agents can edit safely, and UI tests.
- Harder: contributors editing the UI need Node. Built assets must be rebuilt and
  committed (checked in CI).
- The zero-dependency rule applies to the Python package only.

## Alternatives considered

- Consolidate into one vanilla-JS file with ES modules. Rejected: cheaper, but still
  untyped and hard for agents to change safely.
- Rewrite the whole stack in TypeScript. Rejected: see ADR-0002.

## Amendments (2026-10-06)

Amended by [ADR-0035](adr-0035-languages-by-tier.md) (languages by tier). The decision to
build the UI with Vite, React and strict TypeScript and ship it as static files stands.
1. **Generated types.** The TS types are generated from the platform's OpenAPI and
   AsyncAPI contracts instead of hand-mirroring the snapshot contract; CI fails when the
   committed types differ from a fresh generation. The drift test above becomes that check.
2. **One app in three places.** The same build serves the cloud, the brain and the phone.
   On the phone it runs as a PWA inside a native wrapper such as Capacitor, which gives it
   Bluetooth and local Wi-Fi access (needed for the phone-to-node link, especially on iOS).
   The Pi install stays Node-free; the native wrapper is built separately.
3. **Path.** The build output now lives under `src/openostler/web/static/` (ADR-0015).
