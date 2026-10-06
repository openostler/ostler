# Node message fixtures (NodeSource)

JSON Lines, one MQTT message per line: `{"topic", "qos", "retain", "payload"}`; a binary
payload (a raw-tap batch) carries `payload_b64` instead of `payload`. Used by the
NodeSource tests (`tests/test_node_*.py`, through `tests/fake_node.py`) and by
`tests/e2e_server.py --node`.

## From the firmware

| File | What it holds |
|---|---|
| `td5-vectors.jsonl`, `slabs-vectors.jsonl` | One vector run each: the node app replays the shared Discovery 2 vectors through fake ECUs and the host-test sink dumps every message it publishes: `power` (`awake`, then `shutting_down`), the capability `manifest` (K-line item `unverified`, then `ok` after the first init), the gate claim `role/gate/kline-diag` and its release (empty payload) at shutdown, `vss/…`, the tap header and batches (`tap/<session>/meta|data`, with `time` events). |
| `lifecycle.jsonl` | `status` `online`, start, both modules, a reconnect's re-announce (manifest and claim again), then a clean sleep: claim released, `power` `asleep` (with `next_checkin`), `status` `asleep`. |

Source: `openostler/ostler-firmware` (github.com/openostler/ostler-firmware),
`firmware/node/host/fixtures/`, commit **`0426ea5`** (2026-10-06). Copied unchanged.
Shapes as built (firmware `README.md`, sensor-detection spec amendment, raw-tap spec
amendment of 2026-10-06): the manifest is canonical JSON with the `etag` (SHA-256 of the
canonical JSON without it) added last; `board` is `host-sim`, `memory.psram_kb` 0, `roles`
`[]`, `links` `[{"kind":"wifi"}]`, `power` `{class, wake_paths}`, the K-line item carries
`"bus":"kline-diag"`; `priority` is absent from the manifest and `null` in the claim when
no owner priority is set (these runs set 10); the shutdown releases the claim without
changing `status`. The wall clock starts at 2026-10-06T10:00:00Z and advances with the
fake bus, so `ts`, `since` and the tap `time` events move; tests never pin them.

Regenerate in the firmware repo (`cmake --build build/host --target node-fixtures`), copy
the three files here and update the commit above.

## Hand-written here

Only for what the firmware cannot produce yet:

| File | What it holds, and why |
|---|---|
| `status-power.jsonl` | Lines tagged with a `case`: `offline` (the broker publishes the will; no host-test dump has it) and the ADR-0040 `power` states the node does not publish: `held`, `waking`, `off` (from a power owner; no `since_us`). `online`, `awake`, `asleep` and `shutting_down` come from the firmware files (`tests/fake_node.py` `case`). |
| `cluster.jsonl` | The devices around the node (P3), tagged with a `case`: `cluster` (a guardian, a brain, an always-on relay module and a `check_in` sensor node: retained manifests in the firmware's canonical form, `status`, `power` and ADR-0037 §3 claims, including the brain's `uplink` and the sensor node's void `pbroker`); `node_roles` (the node declaring the parked broker, time and PLCA roles and holding the first two, which this firmware does not); `node_roles_released` (their release before a sleep); `gate_conflict` (a second node claiming the K-line gate); `guardian_takes_pbroker`. The node's own manifest, gate claim, power and sleep come from `lifecycle.jsonl` (`tests/fake_node.py` `cluster_messages`). |

The files are synthetic: fake ECUs, the identity scrub on, no VIN, `vid` `d2-bench`. Real
car captures are never committed (Constitution). The tap header and batches drive the P2
tests (`tests/test_node_tap.py`, `tests/test_node_recording.py`): the codec, the `.otap`
writer, the `time` events to UTC and the pcapng round trip.

Licence: CC BY-SA 4.0 (vehicle data, `LICENSE-DATA`; `REUSE.toml`).
