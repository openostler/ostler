# src/d2diag/

The Python package: comms core → interpretation → web consumer. The map is in
`docs/architecture.md`.

## Files

- `transport/`, `kline/`, `kwp2000/`, `session.py`, `ports.py` — the comms core.
- `td5/`, `slabs/`, `bcu/`, `airbag/`, `ace/`, `autobox/` — module layers and menus.
- `signals/*.json` — single source of truth for LID mappings (use `upsert_field`).
- `sniff/` — capture parsing, the protocol library, automap and calibration.
- `faultscan.py`, `menus.py`, `community/` — cross-module helpers and opt-in upload.
- `web/` — consumer: stdlib HTTP + SSE server, data sources, the dashboard.

## Editing rules

- Core modules never import `web` (`tests/test_layering.py`).
- Obey the protocol rules in `CONSTITUTION.md` (release(), SLABS polling, tolerant).
- Every change comes with a hardware-free test using `tests/fakes.py`.
