# src/d2diag/

The Python package: comms core → interpretation → web consumer. The map is in
`docs/architecture.md`.

## Files

- `transport/`, `kline/`, `kwp2000/`, `session.py`, `ports.py` — the comms core.
- `td5/`, `slabs/`, `bcu/`, `airbag/`, `ace/`, `autobox/` — module layers and menus.
- `signals/*.json` — single source of truth for LID mappings (use `upsert_field`). A record may
  carry `length` to apply only to replies of that many data bytes (variants share a name).
- `sniff/` — capture parsing, module detection (`modules.py`), the protocol library,
  automap, calibration, the NanoCom capture importer (`importer.py`) and the fault-screen
  importer (`fault_import.py`, T-30).
- `faultscan.py`, `modscan.py`, `menus.py`, `community/` — cross-module helpers
  (`modscan.py` = the read-only address scan) and opt-in upload.
- `web/` — consumer: stdlib HTTP + SSE server, data sources. `web/static/` is the built
  UI from `ui/` (generated — rebuild, never edit); `dashboard*.html` are legacy references.

## Editing rules

- Core modules never import `web` (`tests/test_layering.py`).
- Obey the protocol rules in `CONSTITUTION.md` (release(), SLABS polling, tolerant).
- Every change comes with a hardware-free test using `tests/fakes.py`.
