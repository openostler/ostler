# tools/

CLI entry points and reverse-engineering utilities. Run them with `PYTHONPATH=src`.

## Files

- `dashboard.py` — web dashboard (`--mock` or `--serial`). `deploy.sh` — Pi deploy.
- `verify_ecu.py`, `esp32_read.py` — read-only live checks.
- `decode_session.py`, `analyze_capture.py`, `raw_analyze.py`, `diffmap.py`,
  `lid_sweep.py`, `map_inputs.py`, `map_gui.py` — capture analysis and mapping.
- `build_protocol_library.py`, `export_signals.py`, `gen_signal_header.py`,
  `gen_faultmap.py` — generators from the canonical stores.

## Editing rules

- Keep logic in `src/d2diag/`. Tools are thin wrappers so the logic stays testable.
- Generators read the canonical store. Never hand-edit their output.
