---
title: "Module-bus messages — the MQTT topic tree, payloads, QoS, ACLs and versioning — design"
area: specs
status: stable
version: 1.3
updated: 2026-10-06
depends_on: [decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, decisions/adr-0041-brain-ed25519-signing.md, references/research/ecosystem_architecture.md, references/research/connectivity_uplink.md, references/research/mesh_networking.md, references/research/grant_flow.md, references/research/mqtt_topic_practice.md, references/research/power_and_roles_practice.md]
summary: >
  Approved by the owner on 2026-10-06 ("go with your recommendations"). The module-bus message spec that ADR-0026, ADR-0027, ADR-0028, ADR-0032, ADR-0037, ADR-0038, ADR-0039 and ADR-0040 require before firmware: it gathers, without new decisions, every topic and payload already decided under ostler/v1/<vid>/<device>/: vss/<path> readings with boot and source tags; power (the ADR-0040 record); status with an offline will and asleep; the retained capability manifest (board, roles, transmit, items with origin and status, problems, power, memory.psram_kb, links, tap, actions with runs_on, needs_brain, queueable and expires_max_s) exactly as the NodeSource spec and its cluster fixture drafted it; role/<role>[/<scope>] claims {role, scope, term, priority, since, reason} with release by empty payload and the ADR-0037 timeouts; tap/<ULID>/meta and data, tap/ctl and lab/req and lab/resp (firmware raw-tap spec); requester-owned act/<id> and wake/<id> requests with MQTT 5 expiry and their outcomes; the owner-approved transmit grant (a node-issued challenge and an Ed25519 JWS bound to it, keys enrolled only by pairing or adoption, refusal grant_invalid); every kline* bus is a K-line gate bus; the parked topic set and bridge patterns; per-device ACLs; mDNS TXT keys; mesh bridge topics and the mesh transport value; the CAN fallback rules; timeouts; versioning. Undecided items are listed as open questions. v1.1 (2026-10-06) records the payloads as the node firmware built them (ostler-firmware 0426ea5): manifest items with a bus and the unverified status, priority absent when unset (null in the claim), links without via, power without parked_ma, psram_kb 0, roles [] beside the gate claim; the sleep and shutdown sequences; the tap time event's CBOR keys; power off accepted by the Brain. v1.2 (2026-10-06) records firmware 5971323 as built: the tap batch content type and first_seq user property now set (and checked by the Brain), the tap header's records an array, power.class the same parked class in the manifest and every power record, gate_conflict as a manifest problems code; the firmware's stricter gate rule (any claim on its bus silences it, a void one included) is listed as a pending owner decision, not a spec change. v1.3 (2026-10-06) records the owner's answers to every open question (§17, now "Owner answers"): the grant challenge as a `challenge` outcome on the existing `act/<id>` topic, a pinned JWS header and `boot` and `rh` claims, `grant_locked`; queued requests carry no grant and are signed at delivery (the Brain may sign a Tier 1 request it relayed, ADR-0041); `tap/ctl` and `lab/req` at QoS 1 with hex bytes and de-duplication; wake expiry and the `act` outcome shape; `lab/resp` stays with the tap on the Brain's broker and `act` outcomes bridge inbound; the parked set adds `act`, `event` and `faults`; each device announces its own `off`, the power owner reports `feeds`, shutdown is an `act`; `event/<name>` and the `Vehicle.Ostler.Security.Alarm.State` enum; `faults/<pack>.<module>`; one primary module per VSS path; TXT `txtvers`, `md`, `etag`; the CAN fallback deferred to U5 with three risks; mesh bridge QoS, retain and ACL; gate claims never expire, cleared only by Remove device, and the firmware's any-claim rule plus K-line echo conflicts; the check-in ends when its work is done with a 60 s cap, a 15 s connect cap and back-off.
---

# Module-bus messages — design

**Status:** approved by the owner on 2026-10-06 (answer: "go with your recommendations"),
which settled three points this spec records: (a) the manifest topic and the role-claim
payload exactly as the [NodeSource spec](2026-10-06-node-source-design.md) drafted them
(§4–§6, §16 P3, and `tests/fixtures/node/cluster.jsonl`); (b) the transmit-grant format
proposed in the firmware draft `ostler-firmware` `docs/specs/node-can.md` §6; (c) every bus
id beginning `kline` is a K-line gate bus. Everything else here is consolidated from
accepted ADRs and approved specs, each section citing its source. What no source settled was
listed in §17; **the owner answered every item on 2026-10-06** (v1.3) by accepting the
recommendations of three research notes ([grant flow](../references/research/grant_flow.md),
[MQTT topic practice](../references/research/mqtt_topic_practice.md),
[power and roles practice](../references/research/power_and_roles_practice.md)). §17 now
records each answer and where its normative text sits; the Brain's signing library is
[ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md).

## 1. Scope and the obligations it meets

This is the "module-bus message spec" the ADRs name. It owns the MQTT 5 topic tree and its
payloads; the AsyncAPI document (`api/asyncapi.yaml`) describes the same channels and
follows this spec (NodeSource §8). It does not cover the vehicle buses (ADR-0027 §10), the
UI's capability manifest for a vehicle (UI spec §5), people's accounts (ADR-0029) or the U5
threat model.

| Source | Asked this spec for | Here |
|---|---|---|
| ADR-0026 Consequences | topic tree, CAN mapping, certificates and ACLs, CAN-fallback authentication | §2, §13, §14, §16 |
| ADR-0027 Consequences, Confirmation | topic tree, manifest schema, certificates, ACLs, CAN-fallback auth, CAN mapping, parked topic set and bridge patterns; manifests validated in CI once this lands | §2–§7, §12–§14, §16 |
| ADR-0028 Consequences | parked topic set, bridge patterns, the parked broker's compiled ACL, the wake-and-republish fallback | §12, §13, §16 |
| ADR-0032 Consequences, Amendments B3 | the node's capability manifest (`origin`, `status`, `problems`), brain bridge patterns, wake and shutdown messages, source tags | §5, §6, §11, §12 |
| ADR-0037 Consequences, §4 | `status` and `role/#`, the claim payload, TXT keys, timeouts | §4, §7, §14, §15 |
| ADR-0038 §4, Consequences | mesh bridge topics, rate limits, the mesh transport value | §9, §16 |
| ADR-0039 Consequences | `tap/` and `lab/`, the batch content type, the session header; manifest `tap` and `links` | §6, §8 |
| ADR-0040 Consequences | `power`, `wake/#`, `asleep`, lease and outcome payloads, timeouts | §4, §5, §11, §15 |
| NodeSource §2, §8, §9 | grant format; schemas move here; `faults/<module>` later | §6.2, §10, §17 |

## 2. Conventions (ADR-0027 §5, ADR-0016, ADR-0036)

- **Root:** `ostler/v1/<vid>/<device>/…`. `v1` is the tree version (§18).
- **`<vid>`** is the device-local vehicle handle, one topic level, **never the VIN**: a
  VIN-shaped `vid` (17 characters of ISO 3779) is refused by publishers and consumers alike.
- **`<device>`** is the device id from its install configuration (`node`, `guardian`,
  `brain`, `relay1`, `mesh-1`). Each device publishes **only under its own `<device>`**;
  requests are published on the requester's own topics (§9, §11) so ACLs stay "own topics
  only" (ADR-0026, ADR-0037 §3).
- **Payloads** are UTF-8 JSON objects, except `status` (plain text, §4), released role
  claims (empty, §7) and tap batches (binary, §8). Consumers ignore fields they do not know.
- **Time fields:** `ts` and `since` are RFC 3339 UTC, `null` until the device's clock is
  synced; `t_us` and `since_us` are the device's monotonic µs since boot; `boot` (and the
  tap header's `boot_id`) is a counter kept in NVS and incremented on every boot, so a
  consumer knows exactly when `t_us` restarted (NodeSource §6.4, owner answer 4).
- **Bus ids** (`bus_id`, e.g. `kline-diag`, `can-hs`, `can-body`) name one car bus per
  vehicle. **Every bus id beginning `kline` is a K-line gate bus** (owner, 2026-10-06):
  a serial or KKL source on that vehicle refuses to start beside a device that claims, or
  whose manifest declares `transmit` on, such a bus (NodeSource §15 answer 7, §16 P3).
- **Protocol:** MQTT 5.0 only; MQTT 3.1.1 lacks the wills, expiry and properties the
  sources rely on (NodeSource §12). QoS 2 is not used.

## 3. Topic summary

Publisher "own" means the device named in the topic. Expiry is the MQTT 5 Message Expiry
Interval.

| Topic under `ostler/v1/<vid>/<device>/` | Published by | QoS | Retained | Expiry | § |
|---|---|---|---|---|---|
| `status` | own; the broker for the will | 1 | yes | — | 4 |
| `power` | own | 1 | yes | — | 5 |
| `vss/<leaf>` | own | 0 (the alarm state 1, §6) | yes | — | 6 |
| `event/<name>` | own | 1 | no | 3600 s | 6.1 |
| `faults/<pack>.<module>` | own | 1 | yes | — | 6.2 |
| `manifest` | own | 1 | yes | — | 7 |
| `role/<role>[/<scope>]` | own | 1 | yes | — | 7 |
| `tap/<ULID>/meta` | node | 1 | yes | — | 8 |
| `tap/<ULID>/data` | node | 1 | no | — | 8 |
| `tap/ctl` | the paired Brain or an owner-role client, on the node's topic | 1 | no | — | 8 |
| `lab/req` | the paired Brain, on the node's topic | 1 | no | ≤ 10 s | 8 |
| `lab/resp` | node | 1 | no | — | 8 |
| `act/<id>` (request) | requester, on its own topic | 1 | no | `expires_at − now` | 9 |
| `act/<id>` (outcome) | the executing device, on its own topic | 1 | no | — (a `challenge` 10 s) | 9, 10 |
| `wake/<id>` (request) | requester, on its own topic | 1 | no | `deadline − now` | 11 |
| `wake/<id>` (outcome) | the arbiter, on its own topic | 1 | no | — | 11 |
| `in/text`, `in/alert` | a mesh bridge (`mesh-<n>`) | 1 | no | 86 400 s | 16 |
| `in/position/<peer>` | a mesh bridge | 0 | yes | 3600 s | 16 |
| `state/link` | a mesh bridge | 0 | yes | — | 16 |

## 4. `status` and the will (ADR-0037 §3, Amendment 8; ADR-0040 §1)

- Plain text, retained, QoS 1: `online`, `offline` or `asleep`.
- On connect a device sets an MQTT 5 will of `offline`, retained, **will delay 0 s**, and
  uses **keep-alive 10 s**; the broker publishes the will about 15 s (1.5 × keep-alive)
  after the device goes silent.
- **`asleep`** is a clean sleep: the device publishes a retained `asleep`, clears its role
  claims (§7) and disconnects cleanly, so no will fires. `offline` is kept for an
  unexpected loss. Consumers show asleep as asleep, never as offline (UI spec §3.8).
- A claim from a device whose status is `offline` or `asleep` is void (§7).
- **As built (2026-10-06, firmware 0426ea5).** The node's clean sleep publishes, in order:
  its claims released (empty payloads), `power` `asleep` (with `next_checkin` when a timer
  wake is set), `status` `asleep`, then a clean disconnect. `asleep` is published only
  before a sleep. A **shutdown** (the node stops without sleeping) releases its claims and
  publishes `power` `shutting_down` but does not change `status`. After every reconnect
  the node republishes `status` `online`, its manifest and its claims.
- **A device about to lose its supply** (owner answer 6, 2026-10-06; §5, §11) publishes
  its claims released, `power` `off`, `status` `asleep`, then disconnects with reason 0x00,
  so no will fires and `status` keeps its three values (an off device reads `asleep` here
  and `off` in `power`). The node's as-built shutdown above, which leaves `status`
  unchanged, gains these steps when it ends in a cut (a firmware follow-up). A device
  never disconnects with reason 0x04 on a clean exit: the will would then show `offline`.

## 5. `power` (ADR-0040 §1, §4.5; NodeSource §1)

Retained, QoS 1, one record per device:

```jsonc
{ "state": "awake",              // off | asleep | waking | awake | held | shutting_down
  "since": "2026-10-06T10:00:00.000Z", "since_us": 1000000,
  "class": "always",             // always | wakeable | check_in | none
  "wake_paths": ["ignition", "door", "imu", "timer"],
  "next_checkin": null,          // RFC 3339, for check_in devices
  "leases": [ { "holder": "brain-ui", "target": "brain", "until": "…", "reason": "view" } ],
  "est_ma": null, "reason": "polling",
  "feeds": [ { "target": "brain", "state": "on", "since": "…" } ] }  // feed owners only (below)
```

- `offline` is not published here: it is known from the will (§4) and shown as the power
  state "offline" by consumers (ADR-0040 §1 table).
- **`class` and `wake_paths` as built (v1.2, 2026-10-06; firmware 5971323,
  sensor-detection amendment of 2026-10-06):** they are the device's **parked**
  reachability class and wake paths, the same as the manifest's `power` (§7.1), in every
  record whatever its `state`; `state` says what the device is doing now. A node built to
  sleep on a timer publishes `check_in` with `["timer"]` while it polls too (the first
  firmware sent `always` in its awake records); a bench build that never sleeps publishes
  `always` with no wake path in both.
- `since_us` is an additive as-built field (firmware f59ac00 onwards, NodeSource §1) that
  lets a consumer detect a reboot without a synced clock.
- A **lease** is `{holder, target, until, reason}` (ADR-0040 §4.5); `held` means `leases`
  is non-empty. Lease maxima are in §15.
- **`off`** (owner answer 6). Each device announces its own `off`: a device whose supply
  is about to be cut publishes, in order, its claims released (§7.2), `power`
  `{state: "off", reason, …}` (retained), `status` `asleep` (§4), then an MQTT 5 DISCONNECT
  with reason 0x00. The will (§4) covers a crash or a cut with no warning. The Brain
  accepts `off` (2026-10-06): its claims are void and the snapshot reads it as `asleep`
  (not running, no unexpected loss).
- **`feeds`** (additive, owner answer 6). A device that owns a switched supply (the node
  for the Brain's power switch, a relay module for what it feeds) also reports it in its
  own record: `"feeds": [{"target": "brain", "state": "on" | "off", "since": "…"}]`. A
  consumer reads a device as **off** when its own record says `off` or its feed owner
  reports its feed `off`; an `offline` will that arrives after the feed was reported `off`
  is read as `off`, not as an unexpected loss. The feed owner never writes the target's own
  topics (§13).

## 6. `vss/<leaf>` readings (ADR-0027 §5, ADR-0032 §13; NodeSource §1, §6)

- **Leaf:** a VSS path (`Vehicle.…`, ADR-0016) as one topic level, or
  `<pack>.<module>.<field>` for a pack field with no VSS path, where `<pack>` is the
  platform's pack id (`lr_d2`), never a local alias (NodeSource §6.2).
- Retained, **QoS 0**. Payload:

```jsonc
{ "value": 13.9, "unit": "V", "ts": "2026-10-06T10:00:00.000Z", "t_us": 123456789,
  "boot": 2734, "source": "kline-diag/td5/21 10", "name": "battery",
  "c": "proven", "raw": 13900, "state": "On" }   // state only when the field has a label
```

- `value` is numeric; `unit` is the unit the device sends (today the store's display unit;
  the Brain converts to the VSS unit at U3, NodeSource §15 answer 2); `c` is `proven` or
  `candidate` and is **never raised** by a consumer (CONSTITUTION, NodeSource §6.3).
- **Source tags** (ADR-0032 §13): a reading is identified by `<device>/<source>`, where the
  device comes from the topic and `source` names the bus, module and request
  (`<bus_id>/<module>/<request>`; on CAN `can-hs/7E8/01 0C`, firmware node-can §8.2) or the
  sensor item. Two devices publishing one path never overwrite each other.
- **Identity** (ADR-0036): no identity reply and no `VehicleIdentification` path is
  published; the scrub applies before anything leaves the node.
- **One primary module per VSS path** (owner answer 9). When more than one module of one
  device decodes the same VSS path (the D2 battery voltage from the Td5 and SLABS), the
  pack's signal store marks one field **`primary`** for that path. The device publishes
  `vss/<VSS path>` only from the primary field and every other module's reading under its
  pack leaf `vss/<pack>.<module>.<field>`, both retained, each with its own `source`. A
  consumer that wants every source reads the pack leaves; selection across devices and
  sources stays with the Brain (NodeSource §6.5). There is no `@module` topic grammar and
  no selection on the node. When the primary module is not polled, its VSS leaf goes stale
  and shows its age.
- **Labelled enums.** A field with labels is published with `state` holding the label and
  `value` its index in the allowed list.
- **The alarm state** (owner answer 7) is a reading, not an event:
  `vss/Vehicle.Ostler.Security.Alarm.State`, retained and **QoS 1**, a written exception to
  the QoS 0 rule above. Its overlay node (ADR-0016 Amendments) is a `string` sensor with
  the allowed values `DISARMED`, `ARMING`, `ARMED`, `TRIGGERED`, aliased to OVMS
  `v.e.alarm` (true only when `TRIGGERED`) and to Home Assistant's alarm panel (`disarmed`,
  `arming`, `armed_away`, `triggered`). Every change to `TRIGGERED` also publishes
  `event/alarm.triggered` with its `cause` (§6.1).

### 6.1 `event/<name>` (owner answer 7)

Published by the device itself on `ostler/v1/<vid>/<device>/event/<name>`, **QoS 1, never
retained**, Message Expiry Interval 3600 s. `<name>` is one topic level, dotted and lower
case (`alarm.triggered`, `gate.conflict`, `fault.new`). Payload:
`{id (ULID), name, class, severity: "info" | "warning" | "alarm", ts, t_us, boot, source?,
cause?, text?}`. Consumers de-duplicate by `id`; the owner's allowlists (mesh,
notifications) filter on `class` and `severity`. State stays in retained readings (the
alarm state above); an event says only that something happened.

### 6.2 `faults/<pack>.<module>` (owner answer 8; NodeSource §6.3)

`ostler/v1/<vid>/<device>/faults/<pack>.<module>` (for example `faults/lr_d2.td5`; an OBD
node uses `faults/obd.<ecu>`), **retained, QoS 1**, always the **whole** current list after
every fault read, never a delta:
`{module, status: "ok" | "faults" | "error" | "unimplemented", faults: [{code, text?, state?,
c}], note?, ts, t_us, boot, source}`. **`faults: []` with `status: "ok"` means read, none; an
absent topic means not read.** A clear publishes the new read after the logbook snapshot
(ADR-0033). A code that appears also publishes `event/fault.new` (§6.1). Identity data is
scrubbed as for `vss` (ADR-0036). The Brain derives `Vehicle.Ostler.Diagnostics.DtcCount`
and does not publish `Vehicle.Diagnostics.DTCList`, whose OBD-only format does not fit pack
codes.

## 7. `manifest` and `role/#` (owner-approved as drafted; ADR-0037 §3; UI spec §3.7, §3.8, §5.1; app-model spec §12–§13; ADR-0032 Amendments B)

### 7.1 Capability manifest

`ostler/v1/<vid>/<device>/manifest`, **retained, QoS 1**, republished with a new `etag` on
every change (firmware sensor-detection §5 step 11–12). Fields as the NodeSource cluster
fixture and the UI spec's device entry drafted them:

| Field | Meaning | Source |
|---|---|---|
| `schema` | manifest schema version, `1` | UI spec §5.1 |
| `id`, `kind`, `variant` | device id; `node`, `brain` or `module`; `diag-port`, `guardian`, `sensor`, `relay`, … | fixture; ADR-0039 §1 |
| `model`, `board`, `fw` | human model name, compiled-in board profile, firmware version | UI spec §3.7, §5.1 |
| `etag` | SHA-256 (hex) of the manifest's canonical JSON | sensor-detection §5 |
| `priority` | the owner's priority set at pairing, for role ties; **absent** when none is set (the claim then carries `priority: null`) | ADR-0037 §3 |
| `memory.psram_kb` | PSRAM fitted, from the board profile; `0` when none | ADR-0037 Amendment 14 |
| `roles[]` | roles it may hold, the owner's order: `{role, scope?, max_clients?, priority?}`; the gate is not listed (it is declared by `transmit`), so the node publishes `[]` | ADR-0037 §2–§3, A14 |
| `transmit[]` | `{bus_id}` of the car buses whose transmit gate it holds | ADR-0037 Consequences |
| `links[]` | how it is reached: `{kind: wifi \| ethernet \| t1s \| usb \| ble, via?, segment?}`; `via` and `segment` are optional (the node sends `[{"kind":"wifi"}]`) | ADR-0039 Consequences |
| `power` | `{class, wake_paths, parked_ma?}`; `parked_ma` optional (the node sends none yet) | UI spec §3.8 |
| `items[]` | `{id, kind, origin: board \| detected \| harness \| config, status: ok \| absent \| fault \| no_signal \| unverified \| refused, bus?, reason?, part?, signals?}`; `bus` names the bus an interface item serves | ADR-0032 B1; sensor-detection §2, §7 |
| `problems[]` | `{item, code}`; absent when there is none; codes include `gate_conflict` (v1.2, below) | ADR-0032 B3; sensor-detection §7 and its amendment of 2026-10-06 |
| `signals[]`, `actions[]` | as the UI spec's device entry; each action declares `category`, `tier`, `states`, `remote`, `runs_on`, `needs_brain`, `queueable` (never for Tier 2+) and `expires_max_s` | UI spec §3.8, §5.1; app-model §13.1; ADR-0040 §5 |
| `tap` | raw-tap capability: buses, protocols, max rate | ADR-0039 Consequences |
| `wake.may_request` | the purposes for which it may ask for the Brain | ADR-0040 §4.3 |
| events, UI slots, OTA fields | as ADR-0027 §9 lists them | ADR-0027 §9 |

- Absent and refused items stay listed with their status; the UI draws nothing for them.
- `alarm_critical` requires a wired link; the mesh bridge declares no actions (ADR-0027
  §9, ADR-0038 §2).
- A consumer drops a field of the wrong type and keeps the rest (NodeSource §16 P3).
- **`unverified`** (sensor-detection §2): the item is there but not yet confirmed; the
  node's K-line item is `unverified` until an init on the bus succeeds, then `ok` (a new
  manifest and `etag`). Consumers show it as "Not verified yet", neither ok nor a fault,
  and keep reading the device.
- **`etag` as built** (sensor-detection amendment of 2026-10-06): the SHA-256 (lower-case
  hex) of the manifest without `etag` as canonical JSON (keys sorted at every level, no
  whitespace, UTF-8), and the published bytes are that JSON with `"etag"` added last.
- **As built (2026-10-06, firmware 0426ea5)** the node publishes `schema`, `id`, `kind`
  (`node`), `variant` (`diag-port`), `model`, `board` (`host-sim` in its host tests), `fw`,
  `priority` (when set), `memory`, `roles` (`[]`), `transmit`, `links`, `power` and one
  item, the K-line interface `{bus: "kline-diag", id: "kline", kind: "kline", origin:
  "board", status}`; the other fields come later. This corrects the drafted shapes above
  (which had `via`, `parked_ma` and roles on the node).
- **As built (v1.2, 2026-10-06, firmware 5971323; sensor-detection amendment of
  2026-10-06).** `power.class` is the parked class, the same as in every `power` record
  (§5). **`gate_conflict`** is a `problems` code on the item that holds the transmit gate
  (the node: `{"item": "kline", "code": "gate_conflict"}`): another device claims the gate
  of the same bus (ADR-0037 §5), so this device transmits nothing on it (listen-only; an
  open session is dropped without a frame) until every other claim is released; the
  member is left out again then, so the `etag` returns to its earlier value. The Brain's
  cluster view shows it beside the claim rules (§7.2).

### 7.2 Role claims

Topic `ostler/v1/<vid>/<device>/role/<role>[/<scope>]`, retained, QoS 1, payload
`{role, scope, term, priority, since, reason}`:

```json
{"role":"gate","scope":"kline-diag","term":1,"priority":10,"since":"2026-10-06T10:00:01.000Z","reason":"wired"}
```

| Role id | Scope | Candidates (ADR-0037 §2, A13) |
|---|---|---|
| `gate` | `bus_id` | only the device wired to that bus that declares `transmit` on it; never hands over |
| `pbroker` | none (`null`) | node → guardian → eligible always-on module (`pbroker` in `roles` with `max_clients` 1–5, `power.class` `always`, `psram_kb` ≥ 2048); never the brain |
| `time` | none | best clock first: GNSS with PPS, GNSS, holdover, phone seed; ties by priority |
| `plca` | T1S segment (`t1s0`) | node → guardian, if wired to that segment; never the brain, never a module |
| `uplink` | none | brain → node |

- **Release** clears the retained claim with an empty payload. A holder that sleeps
  releases its claims first (ADR-0037 A9); the gate claim is released too, but a device
  whose manifest declares `transmit` on a `kline*` bus still counts as wired there (§2).
- **Void claims** (every consumer's *view* ignores them; the Network page flags them):
  device `offline` or `asleep`; no manifest yet; role or bus not declared (the manifest's
  `roles` is read as the owner's order); not eligible; payload naming another role or scope.
  Void rules decide what views show as the holder; **they never let a gate transmit**
  (below).
- **Holder:** the live claim with the higher `term`, then the higher `priority`, then the
  lowest device id. A takeover increments `term`. Two live `gate` claims on one bus are a
  configuration fault: both refuse to transmit, no holder, an alert (ADR-0037 §5).
- `priority` may be `null` (no owner priority set); `scope` is `null` for vehicle roles.
- **A conflict the device reports (as built, v1.2).** A device whose manifest carries
  `gate_conflict` (§7.1) is shown by the Brain as in conflict on that bus, whatever the
  claims say: the gate row reads `conflict` with no holder, its claim is flagged
  `conflict`, and an alert `gate_conflict` with `by: "manifest"` names it and every other
  claimant (the two-live-claims alert has `by: "claims"`). A device that is offline or
  asleep transmits nothing anyway, so the Brain does not show its retained report.
- **The gate counts every claim** (owner answer 13, 2026-10-06; the firmware's rule,
  5971323, adopted). A gate holder treats **any** non-empty retained claim on
  `+/role/gate/<its bus>` from another device as live, whatever that device's status,
  manifest or eligibility. It goes listen-only and reports `gate_conflict` until the claim
  is released. Retained claims get 2 s after each subscription, and the node transmits
  nothing after boot until that first window has passed (as built). **Gate claims carry no
  Message Expiry and are never timed out**: silence never becomes permission on a bus with
  no arbitration (ADR-0037 Amendments).
- **Clearing a stale claim.** Only the owner, on a local link, by **Remove device** on that
  device's Network page (UI spec §3.7; one confirmation that names the bus that will become
  writable). Removal revokes the device's certificate and ACL entry, and every broker the
  cluster runs deletes its retained topics under `ostler/v1/<vid>/<device>/#`: a
  **broker-host operation** (on the node's parked broker the node does it itself, as a
  broker-local action, not a publish under another device's topic; §13). The gate holder
  then re-runs its claim window and resumes. A device that comes back after removal is
  unpaired and its claim is refused by the ACL. On Ostler Diagnostics alone the phone app
  offers Remove device over BLE or the node's AP.
- **Conflicts on the wire** (owner answer 13). A K-line echo that differs from what the
  node sent, or traffic seen during the idle wait before an init that the node did not
  send, is a `gate_conflict` with `by: "bus"` (a manifest `problems` entry and an
  `event/gate.conflict`): listen-only, the session abandoned without a frame, released only
  by the owner's acknowledgement or a quiet period with no foreign traffic (bench starting
  point 10 min, §15). It also catches testers that never claim (a NanoCom, a garage scan
  tool).

## 8. Raw tap and lab requests (ADR-0039 §3; firmware raw-tap §2–§4)

- **`tap/<session>/meta`** (retained, QoS 1): the session header
  `{v: 1, session (ULID), node, boot_id, buses: [{idx, bus_id, proto, baud | bitrate, mode?}],
  clock: {source, synced}, scrub: "on" | "off", filters, records?, started}`. **`records`**
  (as built, v1.2; raw-tap amendment of 2026-10-06) is an optional array of the record
  kinds the session's batches may contain (§2.2 `proto` names, §2.3 event names); the node
  sends `["kline_msg", "time"]`. It is a promise of what may appear; readers ignore kinds
  they do not know and never refuse a batch for an unlisted kind. The first firmware sent
  the string `"kline_msg"`; the Brain reads a string as a one-item list.
- **`tap/<session>/data`** (QoS 1, never retained): binary batches of v1 records (raw-tap
  §2.2: `t_us`, `seq`, `type`, `bus`, `dir`/`event`, `proto`, `flags`, `len`, payload; events
  `init`, `keepalive`, `gate`, `session`, `overflow`, `time`, `link`, `bus_state`), flushed
  every **100 ms or at 8 kB**, MQTT 5 content type **`application/vnd.ostler.tap.v1`** and
  user property **`first_seq`**, the decimal `seq` of the batch's first record (the same
  value that record carries), so a consumer sees a gap before it parses the batch. As
  built (v1.2, firmware 5971323, raw-tap amendment of 2026-10-06) every batch publish
  carries both. **The Brain** refuses a batch with any other content type (it is not a v1
  batch; its `seq` then reads as a gap), reads one without a content type or a readable
  `first_seq` as v1 by its records (a node from before the firmware set them; counted),
  and cross-checks `first_seq` with the first record: a disagreement is logged and
  counted and the records' own `seq` is kept. A batch with no whole record reports the gap
  up to its `first_seq`.
- **`time` events** map `t_us` to UTC between marks; consumers order unsynced records by
  `seq` only. `seq` gaps are reported, never filled. As built (raw-tap amendment of
  2026-10-06): an event record (type 1, bus 0xFF, code 6, proto 0, flags 0) whose payload
  is a CBOR map with the text keys `t_us` (unsigned, the header's instant), `utc_ns`
  (unsigned ns since the Unix epoch), `source` (`sntp`; later `ublox-pps`) and `err_us`
  (unsigned or null), written before the first synced record of a session and before any
  record a second or more after the last mark. The Brain maps linearly between marks and
  stamps its pcapng export in UTC (NodeSource §16).
- **`tap/ctl`** (Brain or an owner-role client → node; owner answer 3): QoS 1, not
  retained, `{op: "start" | "stop", session, buses?, filters?}`, where `session` is the ULID
  the requester chose (the tap header's name). A repeated `start` for a running session and
  a `stop` for an unknown one are no-ops.
- **`lab/req`** `{id, bus_id, service, grant?}` and **`lab/resp`** `{id, verdict, reply,
  t_us}` (owner answer 3): `lab/req` is QoS 1, not retained, with a Message Expiry Interval
  of **at most 10 s**; the node answers a repeated `id` with its first `lab/resp` without
  running it again (it remembers the last 16 ids), and a grant's single-use challenge
  already refuses a duplicate as `grant_used`. `service` and `reply` are **lower-case hex
  strings with no separators** (`"2110"`). Lab reads run only in service mode; the node
  gate decides and logs a `gate` event.
- Taps and the lab channel travel on the **Brain's broker**, to which the node connects
  directly; the node's parked broker is not used for them, and `tap/#`, `lab/req` and
  `lab/resp` are never bridged (owner answer 4; raw-tap §3; §12).
- **Scrub** (ADR-0036 Amendments): the node replaces framed identity replies with the
  placeholder unless its install option is on; unframed bytes are flagged and dropped from
  every export.

## 9. Action requests and outcomes (NodeSource §9; ADR-0033 §6; ADR-0040 §5)

- **Request** on the requester's own topic `ostler/v1/<vid>/<requester>/act/<id>`, QoS 1,
  not retained, `id` a ULID:
  `{id, target, action, params, category, tier, user, role, transport, origin, grant?,
  need?, queued_at, expires_at, needs_brain}`; `need: "challenge"` asks for a grant
  challenge (§10).
- **MQTT 5 properties:** Message Expiry Interval `expires_at − now`; Correlation Data
  `id`; Response Topic `ostler/v1/<vid>/<target>/act/<id>`.
- **Outcome** on the executing device's topic `ostler/v1/<vid>/<target>/act/<id>`:
  `{id, state, reason?, t_us}` with `state` one of `challenge` (§10, with its own fields),
  `accepted`, `refused`, `running`, `done`, `expired`, `state_changed`, `failed`; never the
  payload of a refused write. Outcomes reach the Brain over the bridge (§12), so consumers
  de-duplicate them by `(id, state)`.
- **`transport`** is `local` or `remote` (ADR-0033 §6); the gate matrix's transport axis
  also has **`mesh`** and **`matter`** (ADR-0033 Amendments), both remote paths. A mesh
  never carries an action (ADR-0038 §2).
- **Rules carried, decided by the executing gate:** only Tier 0–1 is queued (default expiry
  120 s, max 600 s); Tier 2–3 need a live approval on a local link and are never queued; a
  request is dropped as `expired` after `expires_at` and as `state_changed` when the
  driving state, the requester's role or the transport changed; a remote-origin grant runs
  only with `OSTLER_ALLOW_REMOTE_CONTROL` in the node's own install configuration; an AI
  client's accept is never an approval. A request for an asleep target becomes a wake
  request first (§11), with no grant inside the wake. The executing device also checks
  `expires_at` in the JSON, since MQTT 5 properties are not yet proven to survive a bridge
  (§12).
- **Queued requests and grants** (owner answer 2). A queued request (ADR-0040 §5) holds
  **no grant**; one that carries a `grant` has it dropped and logged, never verified later.
  At delivery the executing gate re-checks the request and, if it needs a grant, answers
  `challenge` (§10). The requester signs it if it is online; otherwise the **paired Brain
  may sign it for a Tier 1 request it relayed**, after re-checking the user's role, the
  category and `expires_at` at that moment, with `origin` the original request's; the audit
  names both. A phone that sent the request directly (BLE, AP) and left is not covered: the
  request expires. If no grant arrives within the challenge's `ttl_ms` the node issues one
  more challenge at most every 30 s until `expires_at`, then drops the request as
  `expired`. A client **offers to queue** a request for a `check_in` target only when the
  target's `power.next_checkin` is before the latest allowed `expires_at`; otherwise it
  says when the target next checks in (UI spec §3.8).
- **`shutdown`** (owner answer 6) is an `act` like any other; §11 gives its rules.

## 10. Transmit grants (owner-approved; firmware node-can §6; owner answers 1–2 of 2026-10-06)

`grant` in an `act` or `lab/req` request is required beyond Tier 0 for anything that
reaches a car bus, and is verified on the node gate before the first frame.

- **Minters:** the paired **Brain** and paired **phones**. Their Ed25519 public keys enter
  the node's trust store **only by pairing or adoption** (raw-tap §6 step 1; adoption with
  the node's button), stored in the signed install configuration in NVS, at most 8 keys,
  each with a role (`brain`, `phone`) and a maximum tier (3). No key is accepted over MQTT
  or from a remote path. The Brain signs with the optional extra `openostler[signing]`
  ([ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md)); without it the Brain mints
  nothing and a grant must come from a phone.
- **UI order** (owner answer 1). The phone or Brain shows the user's confirmation first,
  then asks for the challenge and signs at once, so the human is never inside the 10 s
  window (UI spec §7.2).
- **Challenge exchange** (owner answer 1). A requester that needs a grant publishes its
  `act/<id>` request (§9) without `grant` and with `"need": "challenge"`. The executing node
  runs **every gate step before the grant checks first** (node-can §5 steps 1–11, the
  driving state and origin included); if one fails it answers `refused` with that reason and
  issues nothing. Otherwise it answers on its existing outcome topic
  `ostler/v1/<vid>/<node>/act/<id>` with `{id, state: "challenge", challenge, boot, t_us,
  ttl_ms}`, QoS 1, Correlation Data `id`, Message Expiry 10 s. `challenge` is 16 bytes from
  the hardware RNG, **drawn only after the radio is up** (the ESP32-S3's RNG is true random
  only then), as unpadded base64url (22 characters); `boot` and `t_us` are the node's at
  issue; `ttl_ms` is the lifetime it will honour (≤ 10 000). The node records the challenge
  with the request id, action, tier and `rh`, keeps at most 16 outstanding (at most 4 per
  requester) and forgets each after 30 s. Freshness and single use rest on the **node's own
  monotonic clock** and boot counter, so they need no SNTP and survive clock skew.
- **Grant.** The requester then republishes the **same** `act/<id>` (same `id` and body)
  with `grant` set. A request whose `id` has no outstanding challenge is `grant_used` (a
  requester must wait for the `challenge` outcome before it republishes); one whose action,
  tier or `rh` differs from the recorded ones is `grant_mismatch`. A Tier 1+ request with
  neither `grant` nor `need` is `no_grant`. Over BLE or the node's AP the same JSON travels
  as the reply.
- **Token:** JWS compact serialisation (Ed25519), at most **640 bytes**. The header is
  **exactly** `{"alg":"EdDSA","kid":"<kid>"}`, `kid` naming the trust-store key; any other
  member (`jwk`, `jku`, `x5u`, `x5c`, `crit`, `b64`) or another `alg` is `grant_invalid`.
  Payload `{v: 1, node, vid, bus, action, tier, origin, challenge, ttl_ms, req, boot, rh}`,
  with `ttl_ms` ≤ 10 000, `req` the request id, `boot` the challenge's, and **`rh`** the
  unpadded base64url SHA-256 of the canonical JSON (the manifest `etag` rules, §7.1) of
  `{action, params, role, target, user}` from the request, so a relay cannot change the
  parameters under a valid grant. The signature is verified over the ASCII signing input
  (RFC 7515 §5.1) before the payload is parsed.
- **Node checks**, in gate order: `origin` is the stricter of the token's claim and the
  link the request came in on; header, signature and `kid` (bad header, bad signature or
  unknown key: **`grant_invalid`**); `node`, `vid` and `bus` are its own; `boot` is the
  node's (else `grant_expired`, before the challenge lookup); the challenge is outstanding
  for this `id` and unused (`grant_used`); node `t_us` ≤ challenge time + `ttl_ms`
  (`grant_expired`); action and tier equal the allowlist entry's and the recorded ones, and
  `rh` matches (`grant_mismatch`); then the challenge is spent, before the first frame. A
  missing grant is `no_grant`; Tier 4 never verifies.
- **Repeated failures** (owner answer 1): three `grant_invalid` refusals from one requester
  within 60 s make the node refuse that requester's challenges for 60 s with
  **`grant_locked`** (values to bench, §15).
- **Queued requests** carry no grant and are signed at delivery (§9).
- The node mints its own single-use **probe grant** for the Parked-only CAN bitrate probe
  (ADR-0023); it is never sent over MQTT.

## 11. Wake requests, check-ins and shutdown (ADR-0040 §4–§5, §9)

- **Request** on the requester's own `ostler/v1/<vid>/<requester>/wake/<id>`, QoS 1, not
  retained, or the same JSON to the node over BLE or its AP:
  `{id, target, purpose: {kind: action | view | schedule | alarm | ota, ref}, class, user,
  transport, hold_s, deadline, needs_brain}`. A wake carries **no grant and no approval**;
  one found inside is ignored.
- **MQTT 5 properties** (owner answer 3): Message Expiry Interval `deadline − now`,
  Correlation Data `id`, Response Topic `ostler/v1/<vid>/<arbiter>/wake/<id>`, as for `act`
  (§9).
- **Outcome** on the arbiter's `ostler/v1/<vid>/<arbiter>/wake/<id>`, in the `act` outcome
  shape `{id, state, reason?, t_us}` (owner answer 3), `state` one of `accepted`,
  `coalesced`, `refused` (with its reason, e.g. "Battery 11.9 V: Brain not woken"),
  `waking`, `awake`, `failed` or `expired`.
- **The arbiter is the device wired to the path** and never hands over: the node for the
  Brain's power switch and the wake wire, the device wired to a CAN for its wake frames,
  the parked-broker holder for check-in delivery (ADR-0040 §4.2).
- **Coalescing:** a request for a target already waking or awake joins it, and its hold
  becomes a lease (§5).
- **Check-in targets** (`class: check_in`): the request is queued for the next check-in
  with the same expiry, held by the parked-broker holder.
- **Check-in delivery** ends with the check-in: a check-in ends when its work is done, at
  most 60 s (§15, owner answer 14), so a queued request is offered only when it can still
  run (§9).
- **Shutdown** (owner answer 6; ADR-0032 §4). The power owner publishes on its own topic
  `ostler/v1/<vid>/<owner>/act/<id>` `{id, target, action: "shutdown", params: {timeout_s,
  reason}, category: "system", tier: 0, …}` with a Message Expiry Interval of `timeout_s`.
  `system` marks a device-to-device power order: it is not one of ADR-0033's user
  categories and no role grants it. The target **accepts it only from the device named as
  its feed owner** in its own install configuration, answers `accepted`, publishes
  `power` `shutting_down`, then the `off` sequence of §5 (claims released, `power` `off`,
  `status` `asleep`, DISCONNECT reason 0x00), then halts. The owner cuts at `off` plus a
  short grace or at `timeout_s`, whichever comes first (§15), and sets its `feeds[].state`
  to `off` (§5).

## 12. Brokers, the parked set and bridges (ADR-0027 Amendments; ADR-0028 §5; ADR-0032 §4; ADR-0037 §3, A14, A16; NodeSource §5)

- **Placement:** the node's parked broker (ESP-IDF Mosquitto port, one TLS listener, at
  most 5 mTLS clients until the bench proves more) serves while the Brain is off; the
  Brain's Mosquitto is the full broker while awake and bridges to the parked-broker holder.
  On Ostler Diagnostics alone the node's broker is the only one. Always-on (EV) mode keeps
  the Brain broker up, still bridged.
- **Parked topic set** (owner answer 5; the compiled-in allow-list of every parked-broker
  build, as patterns under `ostler/v1/<vid>/+/`): `status` (with its will), `power`,
  `manifest`, `role/#`, `vss/+`, `faults/+`, `event/+`, `act/+` and `wake/+`. **Excluded:
  `tap/#` and `lab/#`.** `act/+` is parked because a `needs_brain: false` action runs on
  its `runs_on` device with the Brain asleep (ADR-0040 §5); `event/+` and `faults/+`
  because Security and Home render from the node's retained data and alarm paths never
  depend on the Brain (UI spec §3.8, ADR-0033 §7). Retained state is not migrated on a
  handover (ADR-0037 A16): a device republishes its retained topics when it reconnects to a
  new holder. With a guardian or module holding the broker while the node is in
  parked-deep, the node's retained readings are absent until it wakes, so phones show "no
  reading", never zero.
- **Bridge patterns** (owner answer 4; the Brain's Mosquitto to the parked broker):
  **inbound** `+/status`, `+/power`, `+/vss/+`, `+/manifest`, `+/role/#`, `+/wake/+`,
  `+/act/+`, `+/event/+` and `+/faults/+`; **outbound** only `<brain>/act/+` and
  `<brain>/wake/+`. `act` outcomes bridge inbound because any device on the parked broker
  may execute an `act` (a relay module while the Brain sleeps); consumers de-duplicate
  `act` and `wake` outcomes by `(id, state)`. The tap and lab topics (`tap/#`, `lab/req`,
  `lab/resp`) are **never bridged**: the node publishes and subscribes to them on the
  Brain's broker over its own connection (§8). The bridge uses `bridge_protocol_version
  mqttv50` and `try_private true`, and the Brain ignores its own requests echoed back
  inbound. Both brokers then hold the same view of status, claims and outcomes.
- **Bench before relying on properties across a bridge** (owner answer 4): whether the
  Mosquitto bridge (the Brain's, and the ESP-IDF port's) passes MQTT 5 properties
  (expiry, Correlation Data, Response Topic, user properties) and applies expiry without
  SNTP is unproven; until the bench shows it, receivers also check the JSON's
  `expires_at` and `id` (§9).
- **Wake-and-republish fallback** (ADR-0028 §5): if a parked device cannot reach a parked
  broker, it signals the node by wake wire or CAN; the node wakes the Brain where needed
  and republishes. Alarms go direct to a paired phone or out the device's own uplink
  (ADR-0037 §2, ADR-0033 §7).
- **Clients** (NodeSource §4–§5, §16): TLS 1.2+ with a client certificate; client ids
  `<brain>-nodesource` (reads), `<id>-tap` (tap, session expiry 60 s, no clean start on its
  reconnects) and `<id>-check` (the serial source's one-shot check). Read subscriptions use
  clean start with session expiry 0, No Local on, Retain As Published off and Retain
  Handling 0; retained copies rebuild the state. Reconnect back-off 1 s doubling to 30 s.

## 13. Security and ACLs (ADR-0026 as amended; ADR-0027 §8; NodeSource §5)

- **mTLS for every device**, whatever the IP link: a key generated on the device and a
  certificate from the Brain's local CA, or trust from pairing on Ostler Diagnostics alone
  (ADR-0026 A4). No passwords by default, no trust from bus membership.
- **Per-device ACLs** on every broker (MQTT 5 authentication):

| Client | May publish | May subscribe |
|---|---|---|
| Any device | its own `status`, `power`, `manifest`, `role/#`, `vss/+`, `event/+`, `faults/+`; its own `act/+` and `wake/+` as a requester or as the executing device or arbiter | what its role needs; never another device's request topics |
| Node | the above plus its `tap/<ULID>/meta`, `tap/<ULID>/data` and `lab/resp` | requests addressed to it (`+/act/+`, `+/wake/+`) and its own `lab/req`, `tap/ctl` |
| Brain (NodeSource) | `<brain>/act/+`, `<brain>/wake/+`, and the node's `lab/req` and `tap/ctl`, granted explicitly to the paired Brain | the filters of NodeSource §4 for its own `vid`; never `lab/req`, `tap/ctl`, others' `act/` or `wake/`, nor `#` |
| Owner-role client | the node's `tap/ctl` (raw-tap §3) | as its role allows |
| Mesh bridge | its own `status` (with its will), `power`, `manifest`, `in/#` and `state/#` (owner answer 12); never `role/#`, `vss/+`, `act/+`, `wake/+`, `event/+`, nor an action, grant or command topic | the readings and events it forwards (§16) |

- No client may write any other device's `vss`, `status`, `power` or `role` topic. The
  power owner reports a cut in its own `feeds` (§5), never on the target's topics; a
  `shutdown` order is an `act` on the owner's own topic (§11).
- **Remove device is a broker-host operation** (owner answer 13). When the owner removes a
  device (§7.2), each broker's host revokes the device's certificate and ACL entry and
  deletes the retained messages under `ostler/v1/<vid>/<device>/#` itself (the Brain's
  host on its Mosquitto, the node on its parked broker). It is not an MQTT publish, so the
  "own topics only" rule still holds for every client.
- **CAN-fallback nodes** (µA wake, no TLS): their authentication is deferred to the U5
  threat model (owner answer 11), with the three risks of §16 recorded for it; until it is
  decided, no actuator command or alarm-arm change is accepted from a CAN-only node
  (ADR-0026).

## 14. Discovery and mDNS TXT keys (ADR-0027 §6; ADR-0037 §3.3; ADR-0039 §7)

- Devices advertise `_ostler-mod._tcp` (unregistered until module contract v1, ADR-0032
  §16); the Brain advertises its broker. Clean shutdown sends an mDNS goodbye. mDNS is the
  broker-independent liveness signal used by §15's two-signal rule.
- **TXT keys** (owner answer 10), in this order: `txtvers=1` (RFC 6763 §6.7; bumped only
  by an incompatible TXT change), `var=`, `md=` (the model, at most 24 bytes; shown in the
  Brain's adoption list before pairing, when the device has no manifest on the broker
  yet), `fw=`, `pr=` (`0` unpaired, so a Brain can offer adoption), `roles=` (e.g.
  `gate:kline-diag,pbroker,time,plca:t1s0`) and `etag=` (the manifest's full lower-case hex
  `etag`; absent while unpaired). **No `mf` and no `cv`**: the manifest topic follows from
  `vid` and the instance name (`ostler/v1/<vid>/<instance>/manifest`) and is not
  advertised. The whole record stays under 200 bytes (RFC 6763 §6); if a long `roles`
  would pass that, `etag` is cut to its first 16 hex characters (enough to see a change).
  Unknown keys are ignored.

## 15. Timeouts and limits (bench starting points)

| What | Value | Source |
|---|---|---|
| Keep-alive; will delay; will after silence | 10 s; 0 s; ≈ 15 s | ADR-0037 §3 |
| Parked broker takeover; give-back | 30 s of two signals; node healthy 60 s | ADR-0037 §4 |
| Time source takeover; give-back | 60 s; better clock stable 120 s | ADR-0037 §4 |
| PLCA standby; return | 5 s of FAIL; unexpected BEACON or node online 10 s | ADR-0037 §4 |
| Uplink manager | at once when the Brain is offline | ADR-0037 §4 |
| Add-on module pbroker hand-back | Diagnostics node or Guardian healthy 60 s | ADR-0037 A16 |
| Parked broker clients | ≤ 5 mTLS | ADR-0037 A14 |
| Queued action expiry | default 120 s, max 600 s; Tier 0–1 only | ADR-0040 §5 |
| Brain boot timeout | 60 s, retry once, then 1 h lockout | ADR-0040 §4.4 |
| Module online after a wire wake | 2 s, else `failed` | ADR-0040 §4.4 |
| Linger after the last lease | Brain 60 s, modules 5 s | ADR-0040 §4.5 |
| Lease maxima | interactive 15 min (renewed), remote 5 min, ignition off + 10 min, OTA 30 min | ADR-0040 §4.5 |
| Wake buckets | 6 Brain wakes an hour and 20 a day per requester; 30 a day global; alarms exempt | ADR-0040 §4.4 |
| Battery floors | 12.2 / 12.0 / 11.8 V | ADR-0040 §4.4 |
| Wake wire stuck | masked after 2 s, alerted | ADR-0040 §8 |
| Grant challenge | 16 outstanding (4 per requester), forgotten after 30 s; `ttl_ms` ≤ 10 000; the `challenge` outcome's expiry 10 s; a queued request re-challenged at most every 30 s | node-can §6; §9, §10 (owner answers 1–2) |
| Grant lock-out | 3 × `grant_invalid` from one requester in 60 s → `grant_locked` for 60 s | §10 (owner answer 1) |
| Grant token | ≤ 640 bytes | §10 (owner answer 1) |
| `lab/req` | expiry ≤ 10 s; the last 16 ids remembered for de-duplication | §8 (owner answer 3) |
| Events; mesh text and alerts; mesh peer positions | expiry 3600 s; 86 400 s; 3600 s | §6.1, §16 (owner answers 7, 12) |
| Shutdown order | `timeout_s` 60 s; cut at `off` plus ≈ 5 s grace or at `timeout_s` | §11 (owner answer 6) |
| Node quiet before sleep (car profile) | 10 min without a good read | firmware car profile; ADR-0040 §4.5 (owner answer 14) |
| Node check-in (car profile) | every 30 min; awake until the check-in's work is done, at most 60 s; back to sleep if Wi-Fi or the broker is not up within 15 s; each missed check-in in a row doubles the next interval, 30 → 60 → 120 → 240 min, reset by a check-in that connects or any other wake | firmware 6886716; ADR-0040 Amendments (owner answer 14) |
| Wire conflict release | owner acknowledgement, or 10 min with no foreign traffic | §7.2 (owner answer 13) |
| Tap batches; tap subscription | 100 ms or 8 kB; session expiry 60 s | raw-tap §3; NodeSource §4 |
| Staleness of a reading | max(3 × observed interval, 2 s) | NodeSource §6.4 |

Bench results replace these values here (ADR-0037 §4).

## 16. Mesh bridge and the CAN fallback

**Mesh bridge** (ADR-0038 §2, §4; mesh research §5). An add-on device `mesh-<n>` with a
manifest that declares Read outputs and data inputs and **no actions**.

| Direction | Topic | Content |
|---|---|---|
| Out (subscribes) | `ostler/v1/<vid>/+/vss/Vehicle.CurrentLocation.*` | position, heading, speed |
| Out (subscribes) | `ostler/v1/<vid>/+/vss/Vehicle.Ostler.Security.Alarm.State` | `DISARMED`, `ARMING`, `ARMED`, `TRIGGERED` (§6); the cause from `event/alarm.triggered` |
| Out (subscribes) | `ostler/v1/<vid>/+/event/+`, filtered by an owner-chosen allowlist of `class` and `severity` | class, severity, time (§6.1) |
| In | `ostler/v1/<vid>/mesh-<n>/in/text` | peer id, channel, text, time, SNR |
| In | `…/mesh-<n>/in/position/<peer>` | a peer's position as received |
| In | `…/mesh-<n>/in/alert` | a peer's alert, tagged untrusted |
| Health | `…/mesh-<n>/state/link` | radio, channel utilisation, airtime, peers heard |

- **QoS and retain** (owner answer 12). Over the radio nothing is retained and nothing is
  retried, except that alarm-state packets to paired Ostler peers set `want_ack`. In the
  car the bridge is an ordinary device: `in/text` and `in/alert` are QoS 1, not retained,
  Message Expiry 86 400 s; `in/position/<peer>` is QoS 0, **retained** with a Message
  Expiry of 3600 s, so a peer's last position fades; `state/link` is QoS 0, retained. The
  bridge also publishes its own `status` (with its will), `power` and `manifest` like any
  device, and never `role/#`, `vss/+`, `act/+`, `wake/+` or `event/+` (§13; ADR-0038
  Amendments).
- Inbound data is shown and recorded, never parsed as a request. **Transport value:**
  `mesh`, a remote path, Read and alerts only, whatever `OSTLER_ALLOW_REMOTE_CONTROL` says.
- **Rate limits:** position every 10 min parked and 2 min moving, never under 60 s, only on
  change; alarm state on change, at most one per 30 s; alerts debounced per class (one per
  5 min, ten an hour); hop limit 3; the radio's duty cycle obeyed, position dropped before
  alerts. **Privacy:** position sharing off until opted in per channel, coarse (≈ ±3 km) by
  default, never on the public default channel, no VIN, `<vid>`, plate or account name in
  any mesh field (ADR-0038 §5).

**CAN fallback** (ADR-0026, ADR-0027 §11). On CAN the module bus carries a compact,
generated mapping of the same topics; the bridge is mechanical and holds no meaning. CAN or
the separate wake wire carries µA-wake nodes until a bench proves T1S sleep and wake. The
mapping itself (identifiers, framing, which topics fit) and its authentication (§13) are
**deferred to the U5 threat model** (owner answer 11), which must cover three recorded
risks: (1) **freshness across deep sleep**: a SecOC-style counter must survive sleep and
power loss (RTC memory plus NVS, resynchronised at boot), or replays work after every wake;
(2) **wake frames stay unauthenticated** by nature (selective wake matches an id and mask
in the transceiver), which is acceptable only because a wake grants nothing (ADR-0040 §8),
so U5 does not try to sign them; (3) **alarm triggers from CAN-only sensors** are not
covered by §13's bar on actuator and alarm-arm changes: a spoofed trigger is a false alarm
needing physical bus access, and U5 decides whether such triggers show as untrusted.
Nothing on this bus reaches a vehicle bus.

## 17. Owner answers (2026-10-06)

The owner accepted every recommendation of the three research notes on 2026-10-06
([grant flow](../references/research/grant_flow.md),
[MQTT topic practice](../references/research/mqtt_topic_practice.md),
[power and roles practice](../references/research/power_and_roles_practice.md)), which
carry the evidence. Items keep the numbers the open questions had in v1.2.

1. **Challenge exchange.** `need: "challenge"` on the requester's `act/<id>`; the node runs
   gate steps 1–11 first, then answers `state: "challenge"` `{id, challenge, boot, t_us,
   ttl_ms}` on its existing `act/<id>` outcome topic (Correlation Data, 10 s expiry); the
   requester republishes the same `act/<id>` with the grant. The token stays the approved
   JWS, header exactly `{"alg":"EdDSA","kid":…}`, ≤ 640 bytes, plus the claims `boot` and
   `rh`; repeated failures → `grant_locked`; the UI confirms first, then requests the
   challenge and signs at once; the challenge is drawn only after the radio is up.
   → §9, §10, §15; UI spec §7.2.
2. **Queued actions and grants.** Queued requests carry no grant and are signed at
   delivery; with the requester offline the Brain may sign a Tier 1 action it relayed after
   re-checking the user's role; a grant inside a queued request is dropped and logged; the
   UI offers to queue only when `power.next_checkin` precedes the expiry. → §9, §10;
   UI spec §3.8.
3. **`tap/ctl`, `lab/`, wake details.** `tap/ctl` and `lab/req` QoS 1; `tap/ctl`
   `{op: start | stop, session}`; lab bytes hex; `lab/req` de-duplicated by `id` with an
   expiry ≤ 10 s; wake requests carry an MQTT 5 expiry from `deadline` plus Response Topic
   and Correlation Data; wake outcomes reuse the `act` outcome shape. → §3, §8, §11, §15.
4. **Bridges for answers.** `lab/resp` stays with the tap on the Brain's broker (not
   bridged); only `act` outcomes bridge inbound (`+/act/+`), and consumers de-duplicate; a
   bench test checks whether Mosquitto bridges pass MQTT 5 properties. → §8, §9, §12.
5. **Parked allow-list.** `vss`, `power`, `status`, `manifest`, plus `act`, `event` and
   `faults` (beside the claims and wake topics already named); `tap/#` and `lab/#`
   excluded. → §12.
6. **`off` and shutdown.** Each device publishes its own retained `off` before its supply
   is cut; the will covers crashes; the power owner also reports cuts in its own record as
   `feeds: [{target, state, since}]`; a clean shutdown is an `act` with action `shutdown`
   (`timeout_s`, MQTT 5 expiry), accepted only from the device's feed owner; sequence:
   release claims → `power` `off` → `status` `asleep` → disconnect with reason 0x00.
   → §4, §5, §11, §13, §15; ADR-0040 Amendments.
7. **Events and the alarm signal.** `event/<name>`, QoS 1, not retained, with a severity
   and an `id` for de-duplication. The alarm state is
   `Vehicle.Ostler.Security.Alarm.State`, an enum `DISARMED` / `ARMING` / `ARMED` /
   `TRIGGERED` mapped to OVMS `v.e.alarm` and Home Assistant's alarm-panel states, at QoS 1
   as a documented exception to `vss` QoS 0. → §3, §6, §6.1, §16; ADR-0016 Amendments.
8. **`faults/<pack>.<module>`**, retained, QoS 1, always the whole list; an empty list
   means read, none; an absent topic means not read. → §3, §6.2.
9. **One VSS path from two modules.** The pack marks one module primary per VSS path; the
   node publishes the VSS topic only from that module and the other under its
   `<pack>.<module>.<field>` topic; selection stays on the Brain; no `@module` syntax.
   → §6.
10. **TXT keys.** Keep `etag` and `md`, add `txtvers=1`, drop `mf` (and `cv`). → §14.
11. **CAN fallback** mapping and authentication deferred to the U5 threat model, with three
    risks recorded (freshness counters across deep sleep, unauthenticated wake frames grant
    nothing, CAN-only alarm triggers not covered). → §13, §16.
12. **Mesh bridge.** No retain or QoS over the radio; in the car `in/text` and `in/alert`
    QoS 1 not retained, `in/position/<peer>` retained with an expiry, `state/link` QoS 0
    retained; its ACL also covers its own `status`, `manifest` and `power`. → §3, §13, §16;
    ADR-0038 Amendments.
13. **Which claims silence a gate holder.** Gate claims never expire (no MQTT expiry); a
    stale one is cleared only by the owner's **Remove device** on a local link, which
    revokes the device and purges its retained `<vid>/<device>/#` on each broker (a
    broker-host operation); **any** claim on the node's gate bus silences it (the
    firmware's rule, adopted); a K-line echo mismatch or unexpected traffic before an init
    also counts as `gate_conflict`. The grant-flow note's alternative (self-expiring
    claims with a `boot` field) is not adopted. → §7.2, §13, §15; ADR-0037 Amendments;
    UI spec §3.7.
14. **Check-in timings.** A check-in ends when its work is done, capped at 60 s; a 15 s
    connect cap with exponential back-off 30 → 240 min (as built in firmware 6886716); the
    10 min quiet time and the 30 min timer stay. → §11, §15; ADR-0040 Amendments.

**Signing on the Brain.** Python's standard library cannot make Ed25519 signatures, so the
Brain signs grants with the `cryptography` package as the optional extra
`openostler[signing]`, reconciled with the `[passkeys]` extra the CONSTITUTION names
([ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md)). → §10.

**Not covered by the answers** (left for later, none blocking): how a `lab/req` that needs
a grant gets its challenge (the exchange above is defined on `act`; lab reads are Tier 0
today); whether a gate holder whose own broker connection is down should also go
listen-only (today it keeps the claims it last saw); the engine-running (12 V > 13.2 V)
wake before the 30 min timer is lengthened (ADR-0040 §3).

## 18. Versioning

- The topic tree carries `v1`; payloads carry their own versions: manifest `schema: 1`,
  tap header `v: 1` and content type `application/vnd.ostler.tap.v1`, grant payload `v: 1`.
  The grant payload's `boot` and `rh` and the pinned header (v1.3) are part of `v: 1`:
  no minter or verifier of the token existed before them.
- Changes within v1 are **additive**: new fields and topics may appear, consumers ignore
  what they do not know, and old manifests stay valid (app-model §13.1; UI spec §5.1).
- The conformance kit validates every manifest against the schema in CI (ADR-0027
  Confirmation); the module contract moves to its own repo at v1 (ADR-0034).

## Differences between sources, and how this spec reads them

- **Topic names:** the ecosystem research's proposal (§3.3) used `state/<VSS path>` and
  `cmd/<action>`; the firmware and NodeSource built `vss/<leaf>` and requester-owned
  `act/<id>`, which this spec follows. The mesh research's subscription to
  `state/Vehicle.CurrentLocation.*` reads `vss/…` here; the bridge's own `state/link`
  (ADR-0038) is a health topic, not a reading.
- **Source tags:** ADR-0032 A2 describes a fix's `source` as `{device id, receiver id}`;
  as built the device comes from the topic and `source` is a string (§6). ADR-0032 A3's
  `time: unsynced` is expressed as `ts: null`.
- **Grant nonce:** the CanLink spec §7.1 describes a minter's nonce and expiry; the
  owner-approved format binds the token to a node-issued challenge and the node's clock
  (§10). The Python reference reports a bad signature as `grant_used`; the approved code
  is `grant_invalid`.
- **Power states:** the Brain's parser (`node/messages.py`) accepts every ADR-0040 state,
  `off` included (2026-10-06; §5).
- **Gate conflicts (v1.2, settled in v1.3):** §7.2 counted only live claims and the
  firmware any claim on its bus; the owner adopted the firmware's rule for the gate (§17
  item 13), and the void rules now apply to views only.
- **Claim expiry (v1.3):** the grant-flow research proposed self-expiring claims (180 s,
  republished every 60 s, with a `boot` field); the power-and-roles research showed that
  expiry turns silence into permission on a bus with no arbitration. The owner chose never
  to expire gate claims (§7.2).
- **Shutdown category (v1.3):** the research's shutdown order carries `category: "system"`,
  which is not one of ADR-0033's categories; §11 reads it as a device-to-device power
  order that no role grants.
- **Power class (v1.2):** the first node firmware published `always` in its awake `power`
  records and `check_in` in its manifest; as built from 5971323 both carry the parked class
  (§5, sensor-detection amendment of 2026-10-06).
- **Manifest shapes:** the NodeSource cluster fixture drafted `links[].via`,
  `power.parked_ma` and roles on the node; the firmware (0426ea5) sends none of them and
  adds `items[].bus` and the `unverified` status. §7.1 records both: the drafted fields stay
  optional.

## Notes on sources

`ostler-firmware` at `origin/main` e5072b0 (2026-10-06): `docs/specs/raw-tap.md`
(accepted), `docs/specs/node-can.md` (draft; §6 grant format approved by the owner here),
`docs/specs/sensor-detection.md` (accepted), `firmware/README.md` (topics and payloads).
Platform: `src/openostler/node/messages.py`, `node/cluster.py`,
`tests/fixtures/node/cluster.jsonl` and `status-power.jsonl` at main 1a41e38.
v1.1: `ostler-firmware` `origin/main` 0426ea5 (2026-10-06): `firmware/README.md`,
`firmware/node/host/fixtures/` (`td5-vectors.jsonl`, `slabs-vectors.jsonl`,
`lifecycle.jsonl`), the raw-tap spec's and the sensor-detection spec's amendments of
2026-10-06, `CHANGELOG.md`.
v1.2: `ostler-firmware` `origin/main` 5971323 (2026-10-06): `CHANGELOG.md` (node
follow-ups and fixes), `firmware/README.md`, `docs/specs/raw-tap.md` (amendment "the
header's `records` list and the batch properties"), `docs/specs/sensor-detection.md`
(amendment "one power class, and the `gate_conflict` problem"),
`firmware/node/host/fixtures/` (now also `slabs-vectors-no-priority.jsonl` and
`gate-conflict.jsonl`).
v1.3: the owner's answers of 2026-10-06 to the research notes
`references/research/grant_flow.md`, `mqtt_topic_practice.md` and
`power_and_roles_practice.md`; `ostler-firmware` `origin/main` 6886716 (2026-10-06):
`CHANGELOG.md` (the check-in's connect cap, back-off and early sleep),
`firmware/node/sdkconfig.car`.

## Changelog

- 2026-10-06 — v1.0: first version, approved by the owner with the recommendations: the
  manifest and claim payload as NodeSource drafted them, the node-can grant format with
  `grant_invalid`, and `kline*` buses as K-line gate buses. Consolidates ADR-0026, -0027,
  -0028, -0032, -0033, -0037, -0038, -0039, -0040 and the approved specs; open questions
  in §17.
- 2026-10-06 — v1.1: as-built notes from the node firmware (0426ea5) and its fixtures:
  the sleep and shutdown sequences (§4); `off` accepted by the Brain (§5); manifest
  `priority` absent when unset, `psram_kb` 0, `roles` `[]`, `links` without `via`,
  `power` without `parked_ma`, items with `bus` and `unverified`, the `etag`'s canonical
  JSON (§7.1); the `time` event's CBOR keys and the Brain's UTC mapping (§8). No decision
  changed.
- 2026-10-06 — v1.2: as-built notes from the node firmware (5971323): the tap batch
  content type and `first_seq` are set by the firmware and checked by the Brain, and the
  header's `records` is an array (§8); `power.class` and `wake_paths` are the parked ones
  in the manifest and every power record (§5, §7.1); `gate_conflict` is a `problems` code
  and the Brain's cluster view shows it (§7.1, §7.2). The firmware's stricter rule (any
  claim on its gate bus silences it, one from an offline device included) is recorded as
  a pending owner decision (§17 item 13), not a spec change. No decision changed.
- 2026-10-06 — v1.3: the owner's answers to every open question (§17, now "Owner answers
  (2026-10-06)"), each written into the normative text: the grant challenge as a
  `challenge` outcome on `act/<id>` after the cheap gate steps, the pinned JWS header,
  `boot` and `rh` in the token, a 640-byte cap and `grant_locked` (§10); queued requests
  hold no grant and are signed at delivery, by the Brain for a Tier 1 request it relayed
  (§9); `tap/ctl` and `lab/req` QoS 1, `tap/ctl` JSON, hex bytes, `lab/req` de-duplication
  and expiry (§8); wake expiry, Response Topic, Correlation Data and the `act` outcome
  shape (§11); `lab/resp` not bridged, `act` outcomes (and `event`, `faults`) bridged
  inbound, a bench item for property pass-through (§12); the parked set (§12); the `off` sequence,
  `feeds` and the `shutdown` act (§4, §5, §11); `event/<name>` and the alarm-state enum at
  QoS 1 (§6, §6.1); `faults/<pack>.<module>` (§6.2); one primary module per VSS path (§6);
  ACL rows for events, faults and the mesh bridge, and Remove device as a broker-host
  operation (§13); TXT `txtvers`, `md`, `etag`, no `mf` or `cv` (§14); timeouts (§15);
  mesh QoS, retain and ACL, and the CAN fallback deferred to U5 with three risks (§16);
  gate claims never expire, Remove device, the any-claim rule and wire conflicts (§7.2).
  New: [ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md) (the Brain's signing
  extra). Amended: ADR-0016, ADR-0037, ADR-0038 and ADR-0040.
