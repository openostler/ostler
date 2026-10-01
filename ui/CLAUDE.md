# ui/

The dashboard: Vite + React + TypeScript. `npm run build` writes to
`src/d2diag/web/static/`, which is committed so the Pi needs no Node (ADR-0004).

## Files

- `src/api/` — `schemas.ts` (Zod contract), `client.ts`, `useSnapshot`/`useSniff`, `fixtures/`.
- `src/screens/` — one component per tab; `registry.ts` lists them (`admin` ones only on /admin).
- `src/components/` — shared pieces (Value, Gauge, Readout, Sheet, Settings, …).
- `src/layout.ts` — the only place that names signals/commands (Drive tiles, outputs).
- `src/styles.css` — the Astryx light/dark tokens and all styles.
- `e2e/` — Playwright smoke test against `tools/dashboard.py --mock`.

## Editing rules

- Dev: `PYTHONPATH=src python3 tools/dashboard.py --mock` in the repo root, then `npm run dev`.
- Never hard-code signal labels, groups or units — they come from `/fields` (the signal store).
- A server response change → `UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`, then
  update `schemas.ts`.
- Before committing: `npm run check` (lint, typecheck, test, build) and commit `web/static`.
- Anything that writes to an ECU goes through `components/confirm.ts`.
