---
title: "NodeSource — the Brain ingests node data over MQTT — design"
area: specs
status: stable
version: 0.7
updated: 2026-10-06
depends_on: [decisions/adr-0002-layered-stdlib-core.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0010-replay-notes-audio-motion.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-api-consistency-design.md, docs/architecture.md, CONSTITUTION.md]
summary: >
  Approved by the owner on 2026-10-06 (answers in §15); phase P1 (read-only ingest) built in v0.3, phase P2 (recording and raw tap) in v0.4, the P3 backend (manifest and role claims, GET /cluster, the serial source's refusal beside a gate-holding node) in v0.5; the Network page UI waits for U1. v0.6 records the owner's second-round answers (§15): the manifest topic and claim payload as drafted, now in the module-bus message spec; every kline* bus is a K-line gate bus; the node will emit tap time events. v0.7 aligns with the node firmware's real output (ostler-firmware 0426ea5): its fixtures replace the hand-written node lines, the pcapng export stamps UTC from the tap's time events, power off is accepted, and the as-built payload shapes are corrected (§16). A new DataSource, NodeSource, lets the Brain consume what the node publishes over MQTT 5 (retained VSS values, power, status with an offline will, raw-tap batches) instead of driving a KKL cable: the read-only subscription set and QoS; the connection to the Brain's broker (bridged to the node's parked broker) with an mTLS client certificate and a per-device ACL that never subscribes to request topics it does not own; mapping node messages into the snapshot (pack field names, VSS paths and metrics, units passed through until U3, confidence never raised, per-signal staleness from t_us and ts, source tags, ADR-0032 selection for composite readings); recorder integration (decoded values and raw tap side by side, identity scrub re-checked, sessions driven by the node's power and status); additive snapshot, SSE, OpenAPI and AsyncAPI changes; Network page data; requests to the node gate (requester-owned topics, request id, category, tier, MQTT 5 expiry, Tier 0-1 queueable only), the Brain never transmitting on a car bus; offline, asleep and stale states; replay; the KKL and serial sources kept as selectable lab and dev sources. Recommends a minimal stdlib MQTT 5 client (no new dependency, no ADR) over the optional paho-mqtt extra (2.1.0, EPL-2.0 or EDL-1.0, checked 2026-10-06), with an adapter seam. Phases P1 read-only ingest, P2 recording and raw tap, P3 Network page, P4 requests; tests on a fake broker with fixtures from the firmware host tests.
---

# NodeSource — the Brain ingests node data over MQTT — design

**Status:** approved v0.2 (owner, 2026-10-06; answers in §15); v0.3: P1 built, v0.4: P2
built, v0.5: the P3 backend built, its UI after U1 (§16); v0.6: the owner's second-round
answers (§15). Build in phases P1–P4. It applies
[ADR-0032](../decisions/adr-0032-one-node-optional-brain.md) §3 ("the brain consumes the
node's VSS messages over IP") to the platform's server, and changes no ADR. Where it needs a
decision it lists it in §15.

## 1. Context

- The platform's server reads the car through `DataSource`s (`web/sources.py`): `poll()`
  returns `{status, source, signals: {name: {v, u, s, c}}, faults}`, the poll loop in
  `web/server.py` decorates it (`_decorate`), pushes it over `/events` every 0.5 s and feeds
  it to `SessionRecorder.feed()` (`logbook/recorder.py`). Today every live source drives a
  K-line through a KKL cable or serial port on the same host.
- ADR-0032 moves the car to the node: bus I/O, decoding, the transmit gate. The Constitution
  makes it a hard rule that the brain never touches the car and that the KKL path is the
  dev path.
- The node app v0 (`ostler-firmware` `firmware/node/`, commit f59ac00, 2026-10-06) already
  publishes, over MQTT 5 with mTLS, keep-alive 10 s:

| Topic under `ostler/v1/<vid>/<device>/` | Retained | QoS | Payload |
|---|---|---|---|
| `status` | yes | 1 | `online`; will `offline` (plain text, not JSON) |
| `power` | yes | 1 | ADR-0040 record `{state, since, since_us, class, wake_paths, next_checkin, leases, est_ma, reason}` |
| `vss/<VSS path>` or `vss/<pack>.<module>.<field>` | yes | 0 | `{value, unit, ts, t_us, source, name, c, raw, state?}`; `ts` null until SNTP; `source` like `kline-diag/td5/21 10` |
| `tap/<ULID>/meta` | yes | 1 | raw-tap session header (`ostler-firmware` `docs/specs/raw-tap.md` §2.1) |
| `tap/<ULID>/data` | no | 1 | binary record batches, 100 ms or 8 kB (raw-tap §2.2) |

  It reads Tier 0 only, scrubs identity replies in the tap (ADR-0036 Amendments) and has no
  request topics yet.

## 2. Goals and non-goals

**Goals.**
1. A `NodeSource(DataSource)` that turns the node's MQTT messages into the snapshot the UI,
   SSE and recorder already use, so a Brain runs the whole app with no cable.
2. Honest state: asleep is not offline, stale values keep their age, confidence is never
   raised, and nothing is fabricated when the node is silent.
3. Recording of decoded values and the raw tap side by side, identity data scrubbed.
4. The data the Network page needs (devices, power, last seen, role holders).
5. Requests from the Brain to the node gate, with the gate deciding.
6. No new runtime dependency on the Brain unless the owner chooses one (§12).

**Non-goals.** The Brain transmitting on any car bus (never; ADR-0032). Grant format and
pairing ([module-bus message spec](2026-10-06-module-bus-messages-design.md) §10 and the U5 threat model). Home Assistant discovery, the OVMS
tree and other outbound MQTT exports (U5 integrations). Running the broker (Mosquitto is an
OS service, ADR-0027 §3). The phone's own node client (TypeScript). Garage and several
vehicles at once (U6): one NodeSource serves one `vid`.

## 3. Where the code goes (for the implementation spec to confirm)

- `openostler/mqtt/` (new, core layer, stdlib only): the MQTT 5 packet codec and a small
  client (§12). It imports nothing from `web` (`tests/test_layering.py`).
- `openostler/node/` (new, core layer): the device table, payload validation, staleness,
  the selection rules of §6.5, the raw-tap codec. Pure and clock-injected, so it is tested
  without sockets.
- `web/node_source.py`: `NodeSource(DataSource)`, the boundary adapter.
- `logbook/tap.py` and an exporter in `logbook/export.py` for the raw tap (§7).
- Platform code names no pack, module or field: module ids come from source tags and the
  active pack's data (`active_pack()`), as today.

## 4. Subscription set and QoS

`<vid>` is the active vehicle's id (never a VIN; a VIN-shaped `vid` is refused, as the node
does). `+` is the device level.

| Filter | Max QoS | Phase | Why |
|---|---|---|---|
| `ostler/v1/<vid>/+/status` | 1 | P1 | liveness, will (ADR-0037 §3) |
| `ostler/v1/<vid>/+/power` | 1 | P1 | power state (ADR-0040 §1) |
| `ostler/v1/<vid>/+/vss/+` | 0 | P1 | readings; the VSS path is one dotted level |
| `ostler/v1/<vid>/+/manifest` | 1 | P3 | capability manifest ([module-bus message spec](2026-10-06-module-bus-messages-design.md) §7) |
| `ostler/v1/<vid>/+/role/#` | 1 | P3 | role claims (ADR-0037 §3) |
| `ostler/v1/<vid>/+/tap/+/meta` | 1 | P2 | tap session headers |
| `ostler/v1/<vid>/+/tap/+/data` | 1 | P2 | tap batches; only while recording or the lab asks |
| `ostler/v1/<vid>/<arbiter>/wake/+` | 1 | P4 | the arbiter's wake outcomes (ADR-0040 §4.1) |
| `ostler/v1/<vid>/<node>/act/+`, `…/<node>/lab/resp` | 1 | P4 | the node's answers to the Brain's requests (§9) |

- **MQTT 5 subscription options:** No Local on (the Brain never needs its own publishes
  back); Retain As Published off, so a message carrying the retain flag is known to be a
  stored value delivered at subscribe time, not a live one (§6.4); Retain Handling 0.
- **Clean start with a session expiry of 0** for the read subscriptions: on reconnect the
  retained topics rebuild the state, so no broker-side queue is needed. QoS 1 tap data is
  the exception: its subscription uses a session expiry of 60 s so a short Brain hiccup
  does not lose batches (the node's PSRAM ring covers the rest, raw-tap §3).
- **Never subscribed:** `…/lab/req`, `…/tap/ctl`, other requesters' `wake/<id>` and `act/<id>`
  topics, `…/#` on the whole vehicle. The Brain listens only to state and to answers
  addressed to it. The broker ACL enforces the same (§5).

## 5. Broker connection

- **Where.** On a Brain, NodeSource connects to the Brain's own Mosquitto, which bridges to
  the node's parked broker while the Brain is awake (ADR-0027 Amendments, ADR-0032 §4) and
  which the node also uses directly for the tap (raw-tap §3). The bridge patterns must carry
  `status`, `power`, `vss/+`, `manifest`, `role/#` and `wake/#` inbound and the Brain's
  request topics outbound (ADR-0037 §3.4). With no Brain broker (lab: a laptop and a
  Diagnostics node), NodeSource connects to the node's broker directly; same topics.
- **Found by** mDNS (`_ostler-mod._tcp` and the broker service, ADR-0027 §6) or a configured
  URL (`--mqtt mqtts://host:8883`). Never a hard-coded address.
- **Identity.** TLS 1.2+ via stdlib `ssl` with a client certificate issued by the Brain's
  local CA (ADR-0027 §8, ADR-0021); one certificate per Brain service, client id
  `<brain>-nodesource`. No passwords, no default credentials. On a loopback-only listener the
  same mTLS applies (owner question, §15).
- **Per-device ACL** (ADR-0026). Read: the filters of §4 for its own `vid` only. Write: only
  the Brain's own topics (`ostler/v1/<vid>/<brain>/act/+`, `…/<brain>/wake/+`) plus the two
  node-owned request topics ADR-0039 and raw-tap §3 define (`…/<node>/lab/req`,
  `…/<node>/tap/ctl`), granted explicitly to the paired Brain. Nothing else; in particular no
  write to any `vss`, `status`, `power` or `role` topic.
- **Reconnect** with jittered back-off (1 s doubling to 30 s). While the broker is
  unreachable the snapshot says so (§10) and retained values keep their age.

## 6. Mapping into the snapshot

### 6.1 One device table

NodeSource keeps a table keyed by `(device, topic)`; each entry holds the parsed payload,
the receive time on the Brain's monotonic clock, the retain flag and the device's last
`status` and `power`. `poll()` builds a snapshot from it under a lock and never blocks: the
MQTT reader thread fills the table, the poll thread only reads it.

### 6.2 Names, paths and metrics

- **Pack-decoded values** (payload with `name` and a `source` of the form
  `<bus_id>/<module>/<request>`) appear in `signals` under the pack field name, exactly as a
  cable source would publish them, so `/fields`, the UI and the recorder need no change. The
  module comes from the source tag's middle segment; `poll()` returns the active module's
  fields (the `module` the UI selected). Selecting a module only filters the view: the node
  keeps its own rotation (raising a module's priority is a P4 request, after U3's
  visible-signals rule).
- **The VSS path** comes from the topic. When it is a `Vehicle.*` path it is checked with
  `metrics.is_known()` and added to the signal as `m`; an unknown path is kept, marked
  `m_unknown: true` and reported once in the connection log. A `<pack>.<module>.<field>` leaf
  carries no metric.
- **Readings with no pack field** (a guardian's IMU, a sensor node's EGT, any GNSS fix) go to
  a new snapshot field `vss`: `{<VSS path>: {sel, value, unit, ts_utc, age_s, stale, c,
  sources: {<device>/<source>: {...}}}}`, built by §6.5.
- **The pack id in leaves.** The node publishes the platform's pack id, `lr_d2`
  (`vss/lr_d2.<module>.<field>`; `ostler-firmware` ceb4cc7, owner answer 3), so no alias or
  mapping exists anywhere. A leaf naming another pack is kept and reported once in the
  connection log.

### 6.3 Values, units, confidence, labels

| Node payload | Snapshot signal | Rule |
|---|---|---|
| `value` | `v` | numbers only; a non-numeric value is dropped with a log line |
| `unit` | `u` | passed through. Today the node sends the store's display unit (`°C`, `kg/hr`, `raw`), like a cable source; the conversion to the VSS unit of `metrics.json` happens at U3's mapping step for both paths at once (ADR-0016) |
| `c` | `c` | `proven` or `candidate`; anything else, or a value the Brain's installed pack store marks `candidate`, becomes `candidate`. **Never raised:** the lower of node and store wins, and a mismatch is flagged once (node and Brain on different pack versions) |
| `state` | `label` (new) | the field's enumeration label; `s` keeps its meaning (range status) |
| — | `s` | computed from the Brain's signal store with the same rule the pack's sources use; null where the store has none |
| `raw` | `raw` (new, optional) | kept for Decode work; never shown to drivers |
| `ts`, `t_us`, `source` | `ts_utc`, `age_s`, `stale`, `src` (new) | §6.4 |

Snapshot `faults` stays empty with `faults_note: "not read by the node yet"` until the node
publishes fault reads (its gate allows only `21 <lid>` today); a later `faults/<module>`
topic is for the [module-bus message spec](2026-10-06-module-bus-messages-design.md) (its §17).

### 6.4 Staleness per signal

- **Age on the node's own clock.** Each device's latest message gives its monotonic `t_us`
  at a known Brain receive time. A value's age is `node_now − t_us`, where `node_now` is
  that latest `t_us` plus the Brain time since it arrived. This needs no clock sync and
  holds across modules of one device. A `power.since_us` or `t_us` going backwards marks a
  node reboot: older entries from that device lose their `t_us` age.
- **Wall time** (`ts`, RFC 3339 UTC) is shown as `ts_utc` and used across devices only when
  both are synced (`ts` non-null and the device's clock synced); unsynced readings are
  merged by receive order only, never across devices by timestamp (ADR-0032 A3).
- **Stale** when the age passes `max(3 × the field's observed interval, 2 s)`; the interval
  is an EMA of the field's own arrivals (the node's pace differs per module) until the
  manifest's `rate` exists (UI spec §5.1).
- **Retained on subscribe** (the retain flag set): shown as the last known value, stale, with
  its `ts_utc` age when `ts` exists and "age unknown" otherwise, until a live message
  arrives. Never zero, never "Unavailable" (UI spec §3.8).

### 6.5 Several devices and composite readings

- Every reading keeps its source tag `<device>/<source>` (ADR-0032 §13). Two devices
  publishing one VSS path never overwrite each other.
- **Selection, not fusion, in v1.** GNSS follows ADR-0032 A4 exactly (usability, the table,
  hysteresis, disagreement events) through one documented algorithm with shared vectors run
  by the C firmware and the Python server. Other paths: the pack-decoded bus value first,
  then the device the manifest marks primary, then the freshest usable reading, ties to the
  owner's priority and then the lowest device id. `sel` names the chosen source.
- A selected value is for display and recording only: no gate on the Brain uses it, and the
  node gate never trusts a speed or state from another device (ADR-0032 A5, ADR-0037 §5).
- Driving state keeps the UI spec order (vehicle speed, then GNSS speed with the u-blox
  before the guardian, then gear and handbrake; UI spec §3.5).
- `battery_v` (`_decorate`) reads the selected `Vehicle.LowVoltageBattery.CurrentVoltage`
  when no `battery` field is present.

## 7. Recorder integration

- **Decoded values** reach `SessionRecorder.feed()` unchanged: one snapshot per poll. Pack
  fields keep their column names; `vss` paths add a merged column `<path>` and one column
  per source `<path>@<device>` (ADR-0032 A4 records every receiver and the merged stream).
  `Utc` uses the node's `ts` when synced, else the Brain's clock with `time_unsynced` noted
  in `events.jsonl`.
- **Raw tap side by side.** While a session records, the recorder writes each tap batch as
  received to `<session>/tap/<tap-ULID>.otap` (append, fsync once a second like `data.csv`)
  and lists it in `meta.json` `tap: [{session, device, boot_id, scrub, seq_first, seq_last,
  gaps, overflow}]`. Decoded rows and tap records are linked by the node's `t_us` and the
  tap's `time` events (raw-tap §2.4). `seq` gaps are logged as events, never filled.
- **Identity scrub, checked again (ADR-0036).** The node scrubs first; the Brain re-checks:
  - signal names and VSS paths matching the recorder's identity pattern are never written;
  - a tap header with `scrub: off` is accepted only when the Brain's own install option is on
    too; otherwise the Brain replaces framed identity replies (`5A`, `49`) with the
    placeholder and drops unframed runs that contain those service bytes, the node's rule;
  - every export, share and contribution scrubs and drops `unframed` records whatever the
    setting (ADR-0039 owner answer 3); the `scrubbed` flag is never cleared.
- **Sessions follow the node.** A session opens when the node's `status` is `online`, its
  `power.state` is `awake` or `held`, and live values arrive (the existing "connected"
  rule). The node going `asleep` (a clean sleep) ends the session at once with
  `end_reason: node_asleep`; `offline` (the will) or a lost broker pauses it, and the 300 s
  idle rule ends it (ADR-0011). Parked periods and alarm events still go to the logbook per
  ADR-0010's amendment, from the node's own `power` and alarm topics, in a later spec.
- **Meta** gains `source: "node"`, the device ids seen, each device's firmware and manifest
  `etag` once published, and the pack id and version (ADR-0010 amendment).

## 8. SSE and API changes

All snapshot changes are additive (the object is open; old clients ignore them).

- **`Snapshot`** gains `source_kind` (`node` | `serial` | `kline`), `node` (`{device,
  status, power, last_seen_utc, broker: {connected, host}, tap: {session, state} | null}`),
  `vss` (§6.2), `faults_note`, and `status` values `asleep` and `broker-down`.
- **`SignalValue`** gains optional `m`, `label`, `raw`, `ts_utc`, `age_s`, `stale`, `src`.
- **`/events`** keeps one unnamed snapshot message; no new SSE event in P1–P3. P4 adds
  request outcomes to the snapshot (`requests: [{id, action, state, expires_utc, reason}]`).
- **New routes:** `GET /cluster` (P3, the app-model `cluster.read` shape, §11) and
  `fmt=pcapng` on `GET /sessions/<id>/export` (P2; `_EXPORT_FORMATS` gains it).
- **`/command` errors** gain codes `gate_refused` (403, the node's gate refused, its reason
  in `error`), `no_gate` (409, ADR-0037 "No gate for this bus"), `node_asleep` (409, with the
  wake path), `expired` (504) and `state_changed` (409), in the error envelope of the API
  consistency spec.
- **`api/openapi.yaml`** documents all of the above; `tests/test_api_contracts.py` and the UI
  fixtures follow (`ui/src/api/schemas.ts`, a node-sourced fixture).
- **`api/asyncapi.yaml`** gains a second server, `brain-broker` (protocol `mqtt`, MQTT 5,
  mTLS), and the channels of §4 with payload schemas (VSS value, power, status, tap meta,
  tap batch as `application/vnd.ostler.tap.v1`), marked as consumed by the Brain. This is
  the first slice of ADR-0026's "asyncapi gains the MQTT channels at U5"; the
  [module-bus message spec](2026-10-06-module-bus-messages-design.md) is their owner, and the schemas move there.

## 9. Requests to the node (P4)

The Brain asks; the node's gate decides (ADR-0032 §2, ADR-0033 §3). NodeSource never
writes a byte to a car bus and has no code path that could.

- **Topic shape** (requester-owned, like ADR-0040's wake requests, so ACLs stay "own
  topics only"): the Brain publishes `ostler/v1/<vid>/<brain>/act/<id>`, QoS 1, not retained:
  `{id, target, action, params, category, tier, user, role, transport, origin, grant?,
  queued_at, expires_at, needs_brain: false}`. `id` is a ULID; `transport` is `local` or
  `remote` (ADR-0033 §6); `grant` is minted by the Brain or a paired phone for Tier 1+ and
  verified by the node (format: [module-bus message spec](2026-10-06-module-bus-messages-design.md) §10).
- **MQTT 5 properties:** Message Expiry Interval set to `expires_at − now` (ADR-0040 §5),
  Correlation Data = `id`, Response Topic `ostler/v1/<vid>/<node>/act/<id>`; the node answers
  there with `{id, state: accepted | refused | running | done | expired | state_changed |
  failed, reason?, t_us}` and never the payload of a refused write.
- **Rules carried, not decided, by the Brain:** only Tier 0–1 is ever queued (default expiry
  2 min, max 10 min); Tier 2–3 need a live approval on a local link, sent at once, never
  queued; an expired or state-changed request is dropped by the node; a remote-origin grant
  runs only if the node's own install configuration has `OSTLER_ALLOW_REMOTE_CONTROL`; an AI
  client's accept never becomes an approval. Asleep node: the request becomes an ADR-0040
  wake request first (no grant inside the wake).
- **Lab requests** keep ADR-0039's `…/<node>/lab/req` and `lab/resp` shape for the decode
  lab, in service mode only (raw-tap §4); whether to move them to the requester-owned shape
  is §15 Q6.
- **Server threading.** Node requests touch no local bus, so they run on the HTTP thread as
  a third command path beside `_INLINE_COMMANDS` and the poll queue; the reply waits up to
  the command timeout and maps the node's outcome to the codes of §8.
- **Audit and events.** `events.jsonl` records `{action, ok, state, reason}` only, never
  params (ADR-0010).

## 10. Offline, asleep and stale states

| Situation | Snapshot `status` / `conn` | UI (UI spec §3.8) |
|---|---|---|
| Broker unreachable | `broker-down` / `lost` | "Brain cannot reach the broker"; last values stale grey with age |
| No `status` ever seen | `connecting` / `connecting` | "Waiting for the node" |
| `status: online`, `power: awake/held`, live values | `connected` / `connected` | live |
| `online`, no live value for the active module | `connected`, signals stale | values grey with age; "Node not reading <module>" |
| `power: asleep` (clean sleep) | `asleep` / `disconnected` | "Node asleep · wakes on … · last seen …"; Wake where the role allows |
| `power: waking` | `connecting` | "Waking…" with elapsed seconds |
| `status: offline` (the will) | `error` / `lost` | "Node offline" (amber), last seen |
| Device reboot detected (§6.4) | unchanged | old values marked "before restart" |

Values are never zeroed or invented in any row (Constitution, data honesty).

## 11. Network page data (P3)

`GET /cluster` returns one row per device seen under the `vid`, the same JSON shape as a
device page's peer view (app-model spec §12.2, §13.2): `id`, kind and variant, model,
board, firmware and manifest `etag` (from the manifest), "reached via" (from the manifest's
`links`), `status`, the whole `power` record (state, class, wake paths, next check-in,
leases, est. current), **last seen** (the Brain receive time of that device's latest
message on any topic, plus `power.since`), and its role claims. A `roles` list gives each
single-holder role's holder, `term`, `since`, candidates and the last handover (ADR-0037
§2–§4); a claim from a device that is `asleep` or `offline`, or not in the owner's order, is
shown void and flagged. Over a remote path the page is read-only (ADR-0033 §6). The view is
built, never authoritative (ADR-0037 §1).

## 12. MQTT client choice

| | Stdlib MQTT 5 client in `openostler/mqtt/` | `paho-mqtt` as `openostler[mqtt]` |
|---|---|---|
| Dependency rule (ADR-0035) | none added; no ADR | a new extra: needs an ADR amending ADR-0035's list |
| Licence | AGPL-3.0-or-later, ours | dual EPL-2.0 / EDL-1.0 (BSD-3-Clause text; PyPI lists `EPL-2.0 OR BSD-3-Clause`); AGPL-compatible via EDL (checked 2026-10-06) |
| Maturity | new code: CONNECT with will and properties, SUBSCRIBE with options, PUBLISH receive and send at QoS 0/1 with properties (expiry, correlation, response topic, user properties, content type), PUBACK, PINGREQ, DISCONNECT with reason, reconnect, stdlib `ssl`; no QoS 2, no server-side features; roughly 600–800 lines with tests | MQTT 5.0, 3.1.1 and 3.1, TLS client certificates; 2.1.0 (released 2024-04-29) is still the latest release, while master had commits in September 2026; Debian trixie ships 2.1.0, bookworm 1.6.1 (checked 2026-10-06) |
| Fit | exactly the subset §4–§9 use; the same codec drives the test fake broker | broad API; the 2.0 callback break shows its API moves |
| Pi install | nothing to install | an OS package or pip on the Brain |

**Recommendation: the stdlib client**, behind a small `MqttClient` interface (connect,
subscribe, publish, on_message) so a paho adapter can be added later without touching
NodeSource. Reasons: the core stays stdlib + pyserial with no ADR (ADR-0035); the subset is
small and fully specified by MQTT 5.0 (OASIS, 2019); one codec serves the client and the
fake broker; paho's release cadence (none since April 2024) is a risk for a security-facing
dependency. **Fallback:** if the client fails the conformance tests against Mosquitto
(§13), or TLS edge cases cost more than they save, propose `openostler[mqtt]` with paho
under its own ADR. MQTT 3.1.1 is not enough: the node relies on MQTT 5 wills and expiry
(ADR-0037, ADR-0040).

## 13. Testing

- **Unit (no sockets):** the codec round-trips every packet type and property used; the
  device table, staleness (reboot, retained-on-subscribe, EMA intervals), confidence never
  raised, unknown metric flagged, VIN-shaped `vid` refused, §6.5 selection and the GNSS
  vectors of ADR-0032 A4 shared with the firmware.
- **Fake broker** (`tests/fake_broker.py`): in-process, our codec, retained messages, wills,
  keep-alive and session and message expiry on a controllable clock, and an ACL table; it is
  the same fake the ADR-0037 role harness and ADR-0040 wake harness need.
- **Fixtures from the firmware.** The firmware host test's in-memory sink (`t_sink`) gains a
  dump of every message (topic, QoS, retain, payload) to JSONL; the run that replays the 115
  shared vectors through fake ECUs is committed here as `tests/fixtures/node/*.jsonl`. They
  are synthetic (fake ECUs, scrubbed placeholders, no VIN), so they may be committed; real
  car captures never are. A firmware change (that repo) comes first.
- **Contract tests:** the fixtures validate against the node message schemas; NodeSource fed
  a fixture yields signals equal to the Python reference decoder's for the same vectors; its
  snapshot validates against the OpenAPI `Snapshot`; the recorder writes the same columns as
  a cable source for the same values; a tap fixture with a `1A` reply exports with only the
  placeholder.
- **Safety tests:** no NodeSource code path opens a serial port or calls a transport; with
  the ACL fake, subscribing to `lab/req` or `act/+` of another device is refused; a Tier 2
  request marked queued is refused before it is published; an approval inside a wake request
  is never sent.
- **Optional conformance:** `needs_broker` tests against a real Mosquitto (CI service
  container) for TLS, wills and retained handling; skipped locally without one.
- `tests/test_layering.py` covers `openostler.mqtt` and `openostler.node` (no `web` import).

## 14. Phases

| Phase | Ships | Done when |
|---|---|---|
| **P1 Read-only ingest** | `openostler.mqtt`, the device table, `NodeSource` with status, power and `vss` subscriptions, snapshot and SSE fields, `--source node`, OpenAPI and AsyncAPI updates | the UI runs from the fixtures through the fake broker; contract tests pass; on the bench, values match the node's log |
| **P2 Recording and raw tap** | sessions driven by power and status, `vss` columns, tap files and meta, the Brain-side scrub check, pcapng export | the recorder tests of §13; a tap fixture round-trips to pcapng with `seq` gaps reported |
| **P3 Network page data** | manifest and `role/#` subscriptions, `GET /cluster`, last seen, role table | the cluster shape validates for the peer view and the page; void claims are flagged |
| **P4 Requests** | `act/<id>`, wake requests, lab requests, outcomes in the snapshot, `/command` codes | the gate fake refuses and expires as §9 and ADR-0040 Confirmation say; nothing reaches a bus from the Brain |

**The dev path stays.** The KKL and serial sources (the pack's sources, `KLineLinkSource`)
remain the lab and dev sources, chosen with `--serial` as today; `--source node` (or a
Brain's install default) selects NodeSource. They are never combined for one bus: when
NodeSource sees a node holding the transmit gate for `kline-diag` (its claim, P3) a serial
source on that vehicle refuses to start, since a second tester on a shared K-line collides
and bypasses the gate (Constitution; §15 Q7). Replay works for node sessions as for any
other (§7 files, ADR-0010): read-only, the active link untouched, no request published
while a replay is open; re-decoding a session's tap with the Python reference decoder is a
decode-lab feature for a later spec.

## 15. Owner answers (2026-10-06)

The owner took the recommendations on every question.

1. **Client:** a stdlib MQTT 5 client in `openostler/mqtt/` behind a client interface (§12).
   No new dependency and no ADR. A paho adapter under an `openostler[mqtt]` extra, with its
   own ADR, is the fallback only if the stdlib client fails conformance against Mosquitto.
2. **Units on the wire:** the node keeps publishing its display units; the Brain converts to
   the VSS unit at U3, for both the node and the serial path.
3. **Pack id in topics:** the node aligns to the platform's id, `lr_d2`. No alias. The
   firmware node plan and its defaults change to match.
4. **Boot id:** VSS payloads gain `boot` (as the tap header has), so reboots are exact.
   Inference from `t_us` stays as the fallback for nodes without it (§6.4).
5. **Loopback listener:** mTLS stays on the Brain's loopback listener. No Unix socket.
6. **Request topics:** the split stays: actions on the requester-owned `<brain>/act/<id>`,
   with `lab/req` and `tap/ctl` node-owned per ADR-0039.
7. **KKL beside a node:** a serial source refuses to start on a vehicle whose node holds the
   K-line gate.
8. **Session end on sleep:** the session ends at once on `asleep`; the 300 s idle rule stays
   for other disconnects.
9. **Tap retention:** tap batches are recorded only during a recorded session. No rolling
   buffer.

### Owner answers (2026-10-06, second round)

The owner answered the questions left by P2 and P3 the same day, taking the
recommendations.

- **P2 Q1, identity install option:** stays the environment variable
  `OSTLER_RECORD_IDENTITY`, off by default (no change).
- **P2 Q2, `end_reason`:** stays node-only; cable sessions and the D2 demo logs stay
  byte-stable.
- **P2 Q3, tap time:** yes, the node emits the tap's `time` events (raw-tap §2.3–§2.4) so
  tap timestamps can map to UTC. This is firmware work; the Brain maps them when present.
- **P3 Q1, manifest and claims:** the manifest topic and the claim payload are confirmed as
  drafted (§4, §16 P3, `tests/fixtures/node/cluster.jsonl`) and are now specified in the
  [module-bus message spec](2026-10-06-module-bus-messages-design.md) (§7).
- **P3 Q2, serial refusal:** stays a start-time check when `--mqtt` is given (no change
  now).
- **P3 Q3, K-line buses:** every bus whose id begins `kline` is a K-line gate bus
  (confirmed; module-bus message spec §2).

## 16. As built

### P1 (v0.3)

- `openostler.mqtt` (codec, `MqttClient`, `StdlibMqttClient`), `openostler.node`
  (`messages`, `table`, `select`), `web/node_source.py` (`NodeFeed`, `NodeSource`),
  `--source node` in `tools/dashboard.py`, `tests/e2e_server.py --node`.
- Judgement calls: the device table is keyed by `(device, leaf, source)`, not
  `(device, topic)`, because the node publishes two modules' readings of one VSS path on one
  topic (the D2 battery voltage from the Td5 and SLABS); `vss` lists every `Vehicle.*`
  reading, pack-decoded ones included, so §6.5 can prefer the bus value; a field with no
  observed interval yet is stale after 15 s (3 × an assumed 5 s); `last_seen_utc` counts
  live messages only; a reconnect forgets each device's `status` and `power` until the
  retained copies return; the boot id is compared as a growing counter, so retained copies
  from an older boot are marked "before restart" in any arrival order; a node source
  records no sessions until P2; `devices` is an extra snapshot field.
- Not in P1, in `TODO.md`: the serial source's refusal beside a gate-holding node needs the
  role claims (P3; today `--serial` with `--source node` is refused), GNSS selection by
  ADR-0032 A4, mDNS discovery, the §10 wording in the UI (the UI already never draws a
  stale value as live), and a Mosquitto service in CI for the `needs_broker` tests.

### P2 (v0.4)

- **Code.** `logbook/node.py` (the recorder's node rules), `node/tap.py` (the raw-tap codec
  and the identity scrub), `logbook/tap.py` (`TapRecorder`, the `.otap` files),
  `logbook/pcapng.py` (the export), `SessionRecorder.tap_message`, `NodeFeed.start_tap` /
  `stop_tap` / `tap_state`, `DiagServer._sync_tap`; `fmt=pcapng` on the export route. The
  dashboard and `tests/e2e_server.py --node` now record; the CI `broker` job runs the
  `needs_broker` tests with `OSTLER_REQUIRE_BROKER=1`.
- **§7 sessions.** A node session opens on the node's `status: online`, `power.state`
  `awake` or `held` and at least one live (not stale) value, signal or `vss`; `status:
  asleep` ends it at once with `end_reason: node_asleep`; `offline` (`status: error`) and
  `broker-down` pause it and the 300 s idle rule ends it (`end_reason: idle`). `close` and
  `split` record `closed` and `split`. A poll with nothing live writes no row.
- **§7 columns and time.** Stale values (per-signal `stale`) are never written. `vss`
  adds `<path>` from the selected reading and `<path>@<device>` from that device's
  freshest live source; their channel group is `vss` and their confidence `candidate`
  (the store has no record for a path; never raised). `Utc`: a GPS fix first (unchanged),
  then the node's wall clock (a live reading's `ts_utc` plus its age), then the Brain's,
  with `time_unsynced` (and `time_synced` on recovery) in `events.jsonl`.
- **§7 identity.** Signal names keep the recorder's rule; VSS paths are checked per
  segment with camel case split (`SerialNumber`), and the `VehicleIdentification` branch
  is never written. The tap: a header with `scrub: on` is re-checked with the node's rule
  and a miss is logged (`tap_scrub`, `missed: true`); `scrub: off` or no header is kept
  unscrubbed only when the Brain's own install option is on, otherwise the Brain scrubs
  (`scrub: "brain"` in the meta). **The Brain's option is the environment variable
  `OSTLER_RECORD_IDENTITY`** (read only from the process environment, like
  `OSTLER_ALLOW_REMOTE_CONTROL`; off by default).
- **§7 tap files.** One `<session>/tap/<tap session>.otap` per tap session and device: the
  v1 records after the Brain's check, appended per batch, fsynced at most once a second.
  `meta.json` `tap` entries carry `session, device, file, boot_id, scrub, buses, clock,
  started, seq_first, seq_last, records, bytes, gaps, lost, overflow, brain_scrubbed,
  brain_dropped`. A tap session spans recorded sessions (one per node boot), so
  `seq_first` is wherever this session's subscription began.
- **§4 tap subscription.** Its own connection, client id `<id>-tap`, session expiry 60 s:
  clean start for each new run (no batch from an earlier session), no clean start on its
  reconnects (queued QoS 1 batches arrive); subscribed while a session is open (recording
  or paused), unsubscribed then disconnected when it ends (owner answer 9). The snapshot's
  `node.tap` is `{session, state: connecting | waiting | receiving, batches}` while
  subscribed.
- **§8 pcapng.** One interface per tap session and bus, K-line as `LINKTYPE_USER0` (no
  registered K-line link type), CAN as `LINKTYPE_CAN_SOCKETCAN`, events as
  `LINKTYPE_USER1` (CBOR payload); timestamps are the node's `t_us`, not UTC (stated in
  the section comment); `seq` gaps as packet comments and `isb_ifdrop`. *(2026-10-06,
  v0.7: a tap with `time` events is now stamped in UTC; see "Firmware alignment" below.)* A session without
  a tap answers 400 (`bad_request`).
- **Judgement calls.** `end_reason`, `devices`, `pack` and `tap` are written for node
  sessions only, so cable sessions and the pack's byte-stable demo logs are unchanged;
  per-byte K-line records and unknown protocols are dropped when the Brain must scrub (they
  cannot be framed alone; the node's v0 emits none); duplicates by `seq` are skipped as
  QoS 1 redeliveries; a non-ULID tap session id never names a file; a second device
  reusing a tap session id gets `<session>-<device>.otap`; the `pack.version` is the
  pack distribution's version (null for a pack without one).
- **Not in P2, in `TODO.md`:** UTC for tap timestamps from `time` events, parked periods
  and alarm events from the node, and the firmware and manifest `etag` in the meta (P3).

### P3 (v0.5): backend only

- **Code.** `node/cluster.py` (pure: device classes, declaration and eligibility, void
  claims, holders, candidates, alerts, `kline_gate_holders`, `serial_refusal`);
  `node/messages.py` gains `parse_manifest`, `parse_role_rest`, `parse_claim`, the
  `asleep` status and the `manifest` and `role/#` subscriptions (QoS 1, same connection
  and options as P1); `DeviceTable` keeps each device's manifest and claims,
  `DeviceTable.cluster()` and `device_info()`; `NodeFeed.cluster()`, `probe_cluster`,
  `check_serial_beside_node`; `GET /cluster` (`DiagServer.cluster`); `tools/dashboard.py
  --serial … --mqtt URL`; `tests/fixtures/node/cluster.jsonl` (hand-written);
  `tests/e2e_server.py --node` serves a cluster around the simulated node.
- **§11 the view.** Devices: `id, kind, variant, class, model, board, fw, etag,
  manifest_utc, links, status, power` (the whole record), `last_seen_utc, since` (=
  `power.since`), `roles_declared, transmit, memory, items, claims`; the same row is the
  peer view's (app-model §12.2). Roles: one row per `(role, scope)` for the vehicle roles
  (`pbroker`, `time`, `uplink`, always listed once a device is seen), every declared or
  claimed scope, and a gate row for every bus a reading came from (a source tag's
  `bus_id`), so a bus read without a gate reads "No gate for this bus". Each row:
  `holder, term, since, reason, conflict, no_holder, hands_over, candidates, claims,
  last_handover`. `stale` while the broker is not connected (last known, never emptied);
  `as_of_utc` is the last message's arrival. With a cable source the lists are empty and
  `note` says why. Refused in public mode (403).
- **Void claims and holders.** Void, with every reason in `flags`: `offline`, `asleep`
  (status, or a power state `asleep`, `off` or `shutting_down`), `no_manifest`,
  `not_declared` (the role is not in the manifest's `roles`, or a gate's bus not in its
  `transmit`), `not_eligible` (ADR-0037 §2 orders: the brain is never a parked-broker or
  PLCA candidate, a guardian or module never the uplink manager, a module never PLCA; an
  add-on module holds the parked broker only with `power.class: always`, `memory.psram_kb`
  ≥ 2048 and `max_clients` 1–5, Amendment 14), `mismatch` (the payload names another role
  or scope). The holder is the live claim with the higher term, then the higher priority,
  then the lowest device id; the others are `superseded`. Two live gate claims on one bus:
  both `conflict`, no holder, a `gate_conflict` alert. Candidates: devices declaring the
  role and eligible, in the role's order (parked broker node → guardian → module; PLCA
  node → guardian; uplink brain → node), then the owner's priority (the role entry's, else
  the manifest's `priority`), then the id.
- **§15 answer 7.** `kline_gate_holders`: a device that claims a gate on a bus whose id
  starts with `kline` (void or not: a claim says it is wired there), or whose manifest
  declares `transmit` on one (the gate is the wiring and never hands over, so a node that
  slept and released its claims still counts). `--source serial` with `--mqtt` reads the
  vehicle's retained messages once (client id `<id>-check`, so a running NodeSource is
  never taken over; it waits for the SUBACK and 0.3 s of quiet, at most 2 s) and refuses
  to start when any is found; it also refuses when it cannot check (fails closed).
  Without `--mqtt` there is nothing to check; P1's refusal of `--serial` with `--source
  node` stays.
- **§7 meta.** `meta.json` `device_info: {device: {fw, etag}}` (latest seen) for node
  sessions; each first sight and change is a `node_manifest` event. The snapshot gains
  `device_info` and `node.fw`, `node.etag`.
- **§8.** No new SSE event (P1–P3). OpenAPI: `/cluster`, `Cluster`, `ClusterDevice`,
  `ClusterRole`, `ClusterClaim`, `NodeManifest`, `RoleClaim`, `DeviceInfo`; AsyncAPI:
  `nodeManifest`, `nodeRole` (`role/{role}`) and `nodeRoleScoped` (`role/{role}/{scope}`),
  `nodeStatus` gains `asleep`. The UI fixture `snapshot-node.json` carries a manifest;
  no UI code changed (Zod strips the new fields until the Network page, after U1).
- **Judgement calls.** The owner's order (ADR-0037 §3) is read as the manifest's role
  list, since the install configuration publishes only the roles the owner ordered; a
  claim with no manifest yet is void (`no_manifest`) because it cannot be checked. A
  handover is any change of holder a live `status`, `power`, `manifest` or claim message
  causes (a stored copy never records one, so a reconnect invents none); for a gate it
  only says the bus lost or regained its gate. A reconnect forgets manifests and claims
  until the retained copies return (a claim released meanwhile must not linger). The
  device class comes from `kind` and `variant` (`node` with `diag-port` or no variant is
  the Diagnostics node; a guardian is `guardian` by kind or variant; a sensor node and
  any other device are add-on modules; `brain`). `last_seen_utc` stays live messages only
  (as P1); `manifest_utc` is the manifest's arrival. With several devices, the snapshot's
  `node` is the device serving the module, else the Diagnostics node by its manifest (P1
  took the lowest id, which became the brain). The node's own `status: asleep` makes the
  snapshot `asleep`, which ends a recorded session as `power.state: asleep` does.
- **Not in P3, in `TODO.md`:** the Network page UI (after U1); the firmware publishing the
  manifest, claims and `asleep` (the fixture is hand-written; done in v0.7, below); a
  running check after the serial source has started; the manifest's `primary`, priority
  and `rate` in the §6.5 selection; the energy ledger and floors (P4 and firmware).

### Firmware alignment (v0.7, 2026-10-06; `ostler-firmware` 0426ea5)

The node now publishes what P1–P3 read, and its host-test fixtures (`td5-vectors.jsonl`,
`slabs-vectors.jsonl` and the new `lifecycle.jsonl`) replace the hand-written node lines in
`tests/fixtures/node/`. Where the real output differs from what P1–P3 assumed:

- **Manifest.** `board` may be `host-sim`; `memory.psram_kb` may be `0`; `roles` is `[]`
  (the gate is declared by `transmit` and claimed on `role/gate/<bus_id>`); `links` is
  `[{"kind":"wifi"}]` with no `via`; `power` is `{class, wake_paths}` with no `parked_ma`;
  `priority` is absent when the owner set none (the claim then carries `priority: null`);
  the K-line item carries `"bus":"kline-diag"` and starts `unverified`, then `ok` after the
  first init (a new `etag`). The cluster code needed no change: it reads these fields
  optionally and keeps items as published. OpenAPI `NodeManifest` gains the `unverified`
  status and the item `bus`, and documents the rest; the drafted `via` and `parked_ma`
  stay optional for other devices. The `etag` is the SHA-256 of the canonical JSON
  (sensor-detection amendment); a test checks it on every fixture manifest.
- **Sleep and shutdown.** A clean sleep publishes the claim release, then `power`
  `asleep`, then `status` `asleep` (P3 had assumed `status` first), so the gate row's
  last handover reads "node released" rather than "node asleep"; the node still counts as
  wired to the K-line by its manifest. A shutdown releases the claim and publishes
  `shutting_down` without changing `status`.
- **Timestamps advance** with the fake bus from 2026-10-06T10:00:00Z (`ts`, `since`, the
  tap marks); no test pins them.
- **`power.state: off`** (ADR-0040 §1) is accepted; its claims are void (as before) and the
  snapshot reads `asleep` (not running, no unexpected loss). The UI's power badge has no
  word for it yet (`TODO.md`).
- **Tap time to UTC.** The node writes `time` events (raw-tap amendment of 2026-10-06:
  event code 6, bus 0xFF, a CBOR map `{t_us, utc_ns, source, err_us}`) before the first
  synced record of a session and at least once a second while records flow.
  `node/tap.py` decodes them (`parse_time_event`, a stdlib subset of CBOR: unsigned and
  negative integers, text, null and booleans in a definite-length map) and `TimeMap` maps
  `t_us` to UTC linearly between marks, with the nearest mark's offset outside them; a
  mark whose CBOR `t_us` differs from its record's is not used. The `.otap` files keep the
  events with the other records; `meta.json` `tap` entries count them (`time_marks`). The
  pcapng export stamps a tap with marks in UTC (µs since the epoch), comments each mark
  and every record the node flagged unsynced ("UTC extrapolated"), and says per interface
  which clock it uses; a tap without marks keeps `t_us` as before. Decoded rows and tap
  records stay linked by `t_us`.
- **Hand-written fixtures kept** for what the node cannot publish yet: the devices around
  it, a second gate claim, the node holding vehicle roles (`node_roles`), the will
  (`offline`) and the `held`, `waking` and `off` power states.

## Notes on sources

- v0.7: `ostler-firmware` `origin/main` 0426ea5 (2026-10-06): `firmware/README.md`,
  `firmware/node/host/fixtures/*.jsonl`, `docs/specs/raw-tap.md` and
  `docs/specs/sensor-detection.md` (their amendments of 2026-10-06), `CHANGELOG.md`.
- `ostler-firmware` at f59ac00 (2026-10-06): `firmware/README.md` (topics and payloads),
  `components/poll` (`poll.c` payload building, `sink.h`), `main/net.c` (MQTT 5, keep-alive
  10 s, retained will), `docs/specs/raw-tap.md` (accepted 2026-10-06).
- paho-mqtt: PyPI metadata (2.1.0, uploaded 2024-04-29, `EPL-2.0 OR BSD-3-Clause`), the
  project's `LICENSE.txt` (dual EPL-2.0 and EDL-1.0), its GitHub commit history (commits in
  September 2026) and Debian package search (bookworm 1.6.1, trixie 2.1.0); all checked
  2026-10-06.
- Platform code read on main 6b2cba7: `web/sources.py`, `web/server.py` (`_decorate`, `_sse`,
  `_poll_loop`, `record_poll`), `logbook/recorder.py`, `logbook/store.py`, `api/openapi.yaml`,
  `api/asyncapi.yaml`.

## Changelog

- 2026-10-06 — v0.1: first draft for owner review.
- 2026-10-06 — v0.2: approved by the owner with the recommended answers (§15): stdlib
  MQTT 5 client, Brain converts units at U3, node pack id aligns to `lr_d2`, `boot` id in
  VSS payloads, mTLS on loopback, request-topic split kept, serial source refuses beside a
  gate-holding node, session ends on `asleep`, tap recorded only in sessions.
- 2026-10-06 — v0.3: P1 built (§16). §6.2: the node publishes `lr_d2` directly (firmware
  ceb4cc7), no alias; VSS payloads carry `boot`; fixtures from the firmware host tests.
- 2026-10-06 — v0.4: P2 built (§16 P2): sessions driven by the node's status and power,
  live values and `vss` columns only, the raw tap on its own 60 s-session connection while
  a session is open, `.otap` files and `meta.json` `tap`, the Brain-side scrub with the
  install option `OSTLER_RECORD_IDENTITY`, `fmt=pcapng`, read-only replay, the CI
  `broker` job.
- 2026-10-06 — v0.5: the P3 backend built (§16 P3): `manifest` and `role/#`, the cluster
  view with void claims, gate conflicts and live handovers, `GET /cluster`, the serial
  source's refusal beside a node holding the K-line gate (fails closed), `device_info` in
  node session meta and the snapshot, the `asleep` status; the Network page UI waits for
  U1 (UI spec §10).
- 2026-10-06 — v0.6: the owner's second-round answers (§15): `OSTLER_RECORD_IDENTITY` and
  node-only `end_reason` unchanged; the node emits tap `time` events (firmware); the
  manifest topic and claim payload confirmed and moved to the
  [module-bus message spec](2026-10-06-module-bus-messages-design.md), which this spec's
  references now link; the serial refusal stays a start-time check; every `kline*` bus is a
  K-line gate bus.
- 2026-10-06 — v0.7: aligned with the node firmware (0426ea5, §16 "Firmware alignment"):
  its fixtures replace the hand-written node lines; the manifest, sleep and shutdown as
  built; tap `time` events map `t_us` to UTC in the pcapng export (`time_marks` in the
  meta); `power.state: off` accepted.
