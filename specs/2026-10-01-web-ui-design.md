---
title: Web UI (Vite + React + TypeScript) — Design
area: specs
status: stable
version: 1.1
updated: 2026-10-01
depends_on: [decisions/adr-0004-react-typescript-ui.md, decisions/adr-0003-signal-store-source-of-truth.md]
summary: >
  Design for replacing the two hand-written dashboard pages with one Vite + React +
  TypeScript app in ui/, built into src/d2diag/web/static and served by the unchanged
  Python server, with a fixture-checked API contract and signal metadata from the store.
---

# Web UI (Vite + React + TypeScript) — Design

## Goal

Replace `dashboard_v2.html` (the live UI) and `dashboard.html` (v1, the admin
reference) with one typed app that AI agents can change safely. The app must reach
feature parity with both pages. The Python core, the HTTP/SSE routes and the
Pi's Node-free install stay as they are.

## Decisions (locked this session)

| Decision | Choice |
| -------- | ------ |
| Tooling | Vite, React 18, TypeScript (strict), Zod, Vitest + Testing Library, Playwright smoke test, ESLint |
| Location | `ui/` (source) → `npm run build` → `src/d2diag/web/static/` (committed, package-data) |
| Routing | A screen registry (as in v2). `/admin` turns on the admin screens; no router library. |
| Styling | Plain CSS carrying v2's Astryx light/dark variables; no CSS framework |
| Signal metadata | `label`, `group` and `description` live in `signals/*.json`. Derived fields live in `web/sources.py::DERIVED_FIELDS`. `/fields` returns both. |
| Contract | `tests/test_ui_contract.py` compares real responses with `ui/src/api/fixtures/*.json` by shape. Vitest parses the same fixtures with the Zod schemas. |
| Legacy pages | Served at `/legacy/v2` and `/legacy/v1` behind admin until the app has been used in the car. `/` falls back to v2 when no build exists. |

## Architecture

```
ui/src/api        client (typed fetch, command()), Zod schemas, useSnapshot (SSE + /snapshot)
ui/src/state      prefs (localStorage "d2diag.v2", legacy keys kept), toast
ui/src/components Gauge, DataCard, Value, Flag, Sheet, FaultSheet, Settings, Consent, Trend, …
ui/src/screens    Drive, Connect, Faults, Inputs, Outputs, Utilities; admin: Map, Capture, Docs
ui/src/layout.ts  the few layout choices: Drive tiles, module list, output catalogue
```

The server serves `static/index.html` at `/`, `/v2` and `/admin`. It serves fingerprinted
`/assets/*` with an immutable cache header and other static files with `no-cache`.
Traversal outside `static/` is rejected.

## Data flow

The data flow is unchanged from v2:
- **Live values:** `EventSource("/events")` pushes the full snapshot every poll, and
  `/snapshot` primes it on load.
- **Actions:** every action goes through `POST /command {action, params}`. Admin tools
  use `/map`, `/sniff`, `/automap`, `/signal`, `/capture`, `/docs` and `/doc`.

## Error handling

- **Validation:** every response is validated with Zod. A shape mismatch is logged and
  shown as a toast; it never crashes the page.
- **Connection loss:** `EventSource` reconnects by itself, and the header pill shows
  "Connecting" until a snapshot arrives.
- **Destructive actions:** every actuator, clear-faults and shutdown action goes through
  one confirmation component.

## Testing

- Python: route, static, metadata and contract tests.
- UI: unit tests for value formatting, unit conversion, fault parsing and the schemas
  (against the fixtures), plus component tests for the screens.
- Playwright: a smoke test against `tools/dashboard.py --mock`.
- CI: a Node job runs lint, typecheck, tests and the build, and fails if the committed
  `static/` output differs from the build.

## Non-goals

- Changing the server's routes or command semantics.
- New features beyond the union of v1 and v2. The calibrate view (`/calib`) existed only
  as dead CSS in v1 and is not ported.
- Deleting the legacy pages. That follows a car session (`references/test_plan.md` T-24).

## Changelog

- 2026-10-01 — Initial design.
- 2026-10-01 — Implemented. Deviations from the design:
  - React 19, not 18 (the current release). TypeScript is pinned to 5.9, because
    typescript-eslint does not support 7 yet.
  - One global `styles.css`, not CSS modules: it is a direct port of v2's tokens and
    rules.
  - The all-module fault scan is on Faults for every user. It is read-only and was
    previously only in v1.
  - The markdown renderer now refuses non-http(s) link schemes, because the UI injects
    its HTML.
  - In admin mode the bottom nav scrolls sideways (9 tabs).
