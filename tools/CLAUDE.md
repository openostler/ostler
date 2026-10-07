# tools/

Platform CLI entry points. Run them with `PYTHONPATH=src` (or an editable install). Vehicle
tools (verify_ecu, bcu_scan, diffmap, lid_sweep, map_inputs, nanocom_import, the
generators, …) live in the vehicle pack's repo (ADR-0015).

## Files

- `dashboard.py` — web dashboard, always live (`--serial`, `--module`, `--sniff PORT`,
  `--geocoder`; no demo mode, ADR-0011 — a simulated car is `tests/e2e_server.py`). The
  admin Decode tab's sniff feed comes only from a live ESP32 sniffer (`--sniff`); there is
  no replayed sniff log in the product (the test server's `--replay` loops one).
- `deploy.sh` — Pi deploy (mirrors the platform and a pack checkout, `PACK_DIR`).
- `module_scan.py` — read-only K-line address scan (logic in `src/openostler/modscan.py`,
  addresses from the pack's `SniffSpec`). A sweep is probing, so it is Parked-only: it
  refuses to start without `--confirm-parked` or a "yes" at its prompt.
- `esp32_read.py` — ESP32 sniffer reader with live markers.
- `make_demo_session.py` — regenerates the pack's demo sessions (`pack.demo.generate`).
- `build_meta.py` — stamps `BUILD_COMMIT`/`BUILD_TIME` into the Docker build (Settings → Version).
- `build_places.py` — builds `src/openostler/geo/places.tsv.gz` from GeoNames.
- `build_metrics.py` — dev-only (vss-tools from `[dev]`, Python >= 3.11): applies
  `vss/ostler.vspec` to the pinned VSS release and writes `src/openostler/metrics.json` and
  `vss_leaves.json` (ADR-0016). `--check` exits 1 when either is stale (CI). The build
  logic lives here rather than in `src/` because it needs vss-tools and PyYAML.

## Editing rules

- Keep logic in `src/openostler/`. Tools are thin wrappers so the logic stays testable.
- Tools name no vehicle module unless it is a CLI default the user can override.
