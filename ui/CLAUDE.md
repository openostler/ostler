# ui/

The dashboard: Vite + React + TypeScript. `npm run build` writes to
`src/d2diag/web/static/`, which is committed so the Pi needs no Node (ADR-0004).

## Files

- `src/api/` — `schemas.ts` (Zod contract), `client.ts`, `useSnapshot`/`useSniff`, `fixtures/`.
- `src/screens/` — one component per tab; `registry.ts` lists them (`admin` ones only on /admin).
- `src/components/` — shared pieces (Value, Gauge, Readout, Sheet, Settings, …).
- `src/layout.ts` — the only place that names signals/commands (Drive tiles, outputs).
- `src/styles.css` — the calm-instrument tokens (auto day/night) and all styles.
- `e2e/` — Playwright smoke test against `tools/dashboard.py --mock`.

## Editing rules

- Dev: `PYTHONPATH=src python3 tools/dashboard.py --mock` in the repo root, then `npm run dev`.
- Never hard-code signal labels, groups or units — they come from `/fields` (the signal store).
- A server response change → `UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`, then
  update `schemas.ts`.
- Before committing: `npm run check` (lint, typecheck, test, build) and commit `web/static`.
- Anything that writes to an ECU goes through `components/confirm.ts`.

## Design rules (calm instrument — ISA-101 + automotive HMI)

- Neutral when healthy. Colour (warn/alarm) only for abnormal values, always with an icon
  and a word (`StatusChip`); OK values show no badge at all.
- Every number in context: `RangeBar` (span + `normal` band from the signal store) and a
  60 s `Sparkline`. Bands live in `signals/*.json` (`span`, `normal`), never in components.
- `HealthStrip` leads Drive and Inputs with the one-line answer and links to the cause.
- Status hues are validated with the dataviz `validate_palette.js` in both modes — re-run it
  if you change `--ok/--warn/--alarm/--accent`.
- Screens scroll: never let flex shrink a block (`main > *` is `flex-shrink: 0`).
