---
title: "ADR-0004 — React + TypeScript dashboard, shipped as static assets"
area: decisions
status: locked
version: 1.0
updated: 2026-09-30
summary: >
  The dashboard moves from two single-file vanilla-JS pages to one Vite + React + TypeScript app, built ahead of time and served as static files by the existing Python server.
---

# ADR-0004 — React + TypeScript dashboard, shipped as static assets

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
