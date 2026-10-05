# tools/

Platform CLI entry points. Run them with `PYTHONPATH=src` (or an editable install). Vehicle
tools (verify_ecu, bcu_scan, diffmap, lid_sweep, map_inputs, nanocom_import, the
generators, …) live in the vehicle pack's repo (ADR-0015).

## Files

- `dashboard.py` — web dashboard, always live (`--serial`, `--module`, `--replay FILE|pack`,
  `--geocoder`; no demo mode, ADR-0011 — a simulated car is `tests/e2e_server.py`).
  `--replay pack` loops the active pack's demo sniff log.
- `deploy.sh` — Pi deploy (mirrors the platform and a pack checkout, `PACK_DIR`).
- `module_scan.py` — read-only K-line address scan (logic in `src/openostler/modscan.py`,
  addresses from the pack's `SniffSpec`).
- `esp32_read.py` — ESP32 sniffer reader with live markers.
- `make_demo_session.py` — regenerates the pack's demo sessions (`pack.demo.generate`).
- `build_places.py` — builds `src/openostler/geo/places.tsv.gz` from GeoNames.

## Editing rules

- Keep logic in `src/openostler/`. Tools are thin wrappers so the logic stays testable.
- Tools name no vehicle module unless it is a CLI default the user can override.
