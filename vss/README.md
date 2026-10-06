# vss/ — the canonical signal namespace (ADR-0016)

- [`VERSION`](VERSION): the pinned COVESA VSS release, `6.1`.
- [`upstream/`](upstream/README.md): the unmodified 6.1 release artefacts (MPL-2.0): the
  release JSON export, the composed `.vspec` that vss-tools reads, `units.yaml` and
  `quantities.yaml`. About 0.6 MB, so the whole release JSON is vendored, not a subset.
- [`ostler.vspec`](ostler.vspec): our overlay (CC BY-SA 4.0). It annotates existing VSS
  nodes with the alias attributes `ostler_role`, `ovms`, `ha_device_class`,
  `ha_state_class` and `obdb`, and adds the `Vehicle.Ostler.*` branch. It is the single
  source of every alias; nothing else is hand-kept.

`python tools/build_metrics.py` (dev-only: vss-tools from the `[dev]` extra, Python
>= 3.11) runs `vspec export json` over `upstream/model.vspec` with the overlay and writes
`src/openostler/metrics.json` and `src/openostler/vss_leaves.json`, which ship in the
package. `--check` fails when either is stale; CI runs it. See
[docs/architecture.md](../docs/architecture.md) for how the runtime reads them.
