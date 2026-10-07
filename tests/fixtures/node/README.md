# Node message fixtures (NodeSource)

JSON Lines, one MQTT message per line: `{"topic", "qos", "retain", "payload"}`; a binary
payload (a raw-tap batch) carries `payload_b64` instead of `payload`, and a message with
MQTT 5 publish properties carries them as `"properties"` (a tap batch:
`{"content_type":"application/vnd.ostler.tap.v1","user_property":[["first_seq","N"]]}`,
module-bus spec §8; an event: `{"message_expiry_interval":3600}`, §6.1); `tests/fake_node.py` sends them with the message. Used by the
NodeSource tests (`tests/test_node_*.py`, through `tests/fake_node.py`) and by
`tests/e2e_server.py --node`.

## From the firmware

| File | What it holds |
|---|---|
| `td5-vectors.jsonl`, `slabs-vectors.jsonl` | One vector run each: the node app replays the shared Discovery 2 vectors through fake ECUs and the host-test sink dumps every message it publishes: `power` (`awake`, then `shutting_down`), the capability `manifest` (K-line item `unverified`, then `ok` after the first init), the gate claim `role/gate/kline-diag` and its release (empty payload) at shutdown, `vss/…`, the tap header and batches (`tap/<session>/meta|data`, with `time` events). A bench build: power class `always`, no wake path. |
| `slabs-vectors-no-priority.jsonl` | The Slabs run without `node.priority`: no `priority` in the manifest, `"priority":null` in the claim. |
| `lifecycle.jsonl` | `status` `online`, start, both modules, a reconnect's re-announce (manifest and claim again), then a clean sleep: claim released, `power` `asleep` (with `next_checkin`), `status` `asleep`. A build that sleeps: power class `check_in` with `["timer"]` in the manifest and every `power` record. |
| `gate-conflict.jsonl` | A second device (`node2`, a claim only: no manifest or status) claims the K-line gate; the node goes listen-only, its manifest gains `problems` `[{"item":"kline","code":"gate_conflict"}]` and it publishes `event/gate.conflict` (`cause: "claims"`, QoS 1, Message Expiry 3600 s); `node2` releases and the manifest returns to its earlier `etag`; then shutdown. |
| `wire-conflict.jsonl` | A conflict seen on the wire (module-bus spec v1.3 §7.2): foreign traffic on the K-line before an init; the manifest's `problems` gains `{"by":"bus","code":"gate_conflict","item":"kline"}` and the node publishes `event/gate.conflict` with `cause: "bus"`; after the quiet period the problem clears; then shutdown. |
| `off.jsonl` | A supply cut (spec v1.3 §4, §5): claim released, `power` `off` (`reason: "supply cut"`), `status` `asleep`, then a clean disconnect; the node comes back `online`. |

Since firmware a65c44d (093e0ea) the Slabs runs publish the battery voltage only on its pack leaf
`vss/lr_d2.slabs.battery` (the pack marks the Td5 field primary for
`Vehicle.LowVoltageBattery.CurrentVoltage`, spec v1.3 §6); the Td5 run keeps the VSS leaf.

Source: `openostler/ostler-firmware` (github.com/openostler/ostler-firmware),
`firmware/node/host/fixtures/`, commit **`a65c44d`** (2026-10-07; the merge of the module-bus v1.3 follow-ups, whose
fixtures are those of `093e0ea`). Copied unchanged
(`td5-vectors.jsonl` and `lifecycle.jsonl` did not change since `5971323`).
Shapes as built (firmware `README.md`, sensor-detection spec amendments, raw-tap spec
amendments of 2026-10-06): the manifest is canonical JSON with the `etag` (SHA-256 of the
canonical JSON without it) added last; `board` is `host-sim`, `memory.psram_kb` 0, `roles`
`[]`, `links` `[{"kind":"wifi"}]`, `power` `{class, wake_paths}` (the parked class, the
same in every `power` record), the K-line item carries `"bus":"kline-diag"`, `problems` is
absent unless there is one; `priority` is absent from the manifest and `null` in the claim
when no owner priority is set (the other runs set 10); the shutdown releases the claim
without changing `status`. The tap header's `records` is `["kline_msg","time"]`, and every
batch carries the content type `application/vnd.ostler.tap.v1` and the user property
`first_seq` (the `seq` of its first record). The wall clock starts at 2026-10-06T10:00:00Z
and advances with the fake bus, so `ts`, `since` and the tap `time` events move; tests
never pin them.

Regenerate in the firmware repo (`cmake --build build/host --target node-fixtures`), copy
the seven files here and update the commit above.

## Hand-written here

Only for what the firmware cannot produce yet:

| File | What it holds, and why |
|---|---|
| `status-power.jsonl` | Lines tagged with a `case`: `offline` (the broker publishes the will; no host-test dump has it) and the ADR-0040 `power` states the node does not publish: `held`, `waking`, `off` (hand-written before the firmware published it; `off.jsonl` now has the node's own). Each carries the lifecycle node's parked class, `check_in` with `["timer"]`, as every power record now does. `online`, `awake`, `asleep` (with `next_checkin`) and `shutting_down` come from the firmware files (`tests/fake_node.py` `case`). |
| `cluster.jsonl` | The devices around the node (P3), tagged with a `case`: `cluster` (a guardian, a brain, an always-on relay module and a `check_in` sensor node: retained manifests in the firmware's canonical form, `status`, `power` and ADR-0037 §3 claims, including the brain's `uplink` and the sensor node's void `pbroker`); `node_roles` (the node declaring the parked broker, time and PLCA roles and holding the first two, which this firmware does not); `node_roles_released` (their release before a sleep); `gate_conflict` (a second node, with its own manifest and status, claiming the K-line gate: two live claims, the claim-based alert; the firmware's `gate-conflict.jsonl` has the node's own report instead, from a claim-only device); `guardian_takes_pbroker`. The node's own manifest, gate claim, power and sleep come from `lifecycle.jsonl` (`tests/fake_node.py` `cluster_messages`). |

The files are synthetic: fake ECUs, the identity scrub on, no VIN, `vid` `d2-bench`. Real
car captures are never committed (Constitution). The tap header and batches drive the P2
tests (`tests/test_node_tap.py`, `tests/test_node_recording.py`): the codec, the header's
`records`, the batch properties, the `.otap` writer, the `time` events to UTC and the
pcapng round trip.

Licence: CC BY-SA 4.0 (vehicle data, `LICENSE-DATA`; `REUSE.toml`).
