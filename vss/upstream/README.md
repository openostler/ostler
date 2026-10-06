# vss/upstream — COVESA VSS 6.1 (vendored, MPL-2.0)

Unmodified release artefacts of the COVESA Vehicle Signal Specification, pinned by
[`../VERSION`](../VERSION) (ADR-0016). They are under the Mozilla Public License 2.0
([`LICENSE`](LICENSE), copied from the tag), not under this repository's licences.

- **Source:** <https://github.com/COVESA/vehicle_signal_specification>, tag **`v6.1`**
  (commit `2817646d1808fc7c470c0432fc7f4ed685e5c9e3`), release
  <https://github.com/COVESA/vehicle_signal_specification/releases/tag/v6.1>.
- **Fetched:** 2026-10-06.

| File | Release asset | Why it is here |
|---|---|---|
| `vss.json` | `vss.json` (370 KB) | The release JSON export of the standard tree. `tools/build_metrics.py` derives `src/openostler/vss_leaves.json` (every leaf path and unit) from it |
| `model.vspec` | `model.vspec` inside `vss_compose.tar.gz` | The whole standard tree composed into one `.vspec`. vss-tools reads `.vspec`, not JSON, so the overlay is applied to this file; `build_metrics.py` checks that it still exports to exactly the tree in `vss.json` |
| `units.yaml` | `units.yaml` | The unit keys. Every `unit` in `metrics.json` is a verbatim key of this file (`Celsius`, `km/h`, `kPa`, …) |
| `quantities.yaml` | `quantities.yaml` | The quantities the units refer to; vss-tools needs it |
| `LICENSE` | the tag's `LICENSE` | MPL-2.0 text |

Together they are about 0.6 MB, so the release JSON is vendored whole rather than a
subset of `.vspec` branches. sha256 of the downloaded assets: `vss.json`
`bef9ad501b38edd60e7b903cb39ba5b8f0864a984595b3e901d6efa3f06bdb70`, `vss_compose.tar.gz`
`c4edf6a6212fd91091a5c9826b685be9afe7daf37a69103cafa82d06621e85ed`.

Do not edit these files. Moving the pin is its own PR: replace all five files from the new
tag, update `../VERSION`, run `python tools/build_metrics.py`, and add a `vspec diff` note
for any renamed or removed path a pack uses (ADR-0016).
