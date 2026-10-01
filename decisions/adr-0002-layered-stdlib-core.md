---
title: "ADR-0002 — Layered Python core with a stdlib-only server"
area: decisions
status: locked
version: 1.0
updated: 2026-09-30
summary: >
  The protocol stack stays Python, strictly layered (transport → K-line → KWP2000 → session → modules), with pyserial as the only runtime dependency and a stdlib HTTP+SSE server.
---

# ADR-0002 — Layered Python core with a stdlib-only server

- **Date:** 2026-09-30
- **Status:** accepted

## Context

The core value of the project is the K-line/KWP2000 protocol stack and its
hardware-free test suite (300+ tests). The installs that matter are Mac testers and a
Raspberry Pi in the car. The review asked whether a TypeScript rewrite would be better.

## Decision

Keep the core and the HTTP/SSE server in Python. Keep pyserial as the only runtime
dependency. Keep the layering enforced by `tests/test_layering.py`. Record this decision,
which was made before the fork, so it is not reopened by accident.

## Consequences

- The protocol stack, fakes and tests are preserved.
- The UI is swappable, because it talks only to the snapshot/SSE/command contract.
- Anything web-heavy must live in the UI (ADR-0004), not in new server dependencies.

## Alternatives considered

- Rewrite in Node/TypeScript. Rejected: it throws away a proven, tested protocol stack,
  and serial timing on Node is no better.
- FastAPI or another server framework. Rejected: it adds dependencies to a Pi and tester
  install for no protocol gain.
