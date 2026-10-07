---
title: "The Brain's Mosquitto — ACL, bridge and parked set templates"
area: docs
status: draft
version: 1.0
updated: 2026-10-07
depends_on: [specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-node-source-design.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0041-brain-ed25519-signing.md]
summary: >
  Configuration templates for the Brain's Mosquitto as module-bus spec v1.3 §12–§13 decided them: the per-identity ACL (the NodeSource read set with faults/+ and event/+, the tap connection, the broker-host identity Remove device uses), the bridge to the parked broker (inbound status, power, vss, manifest, role, wake, act, event and faults; outbound only the Brain's act and wake; tap and lab never bridged; MQTT 5, try_private), the parked broker's compiled-in allow-list for the firmware, and what Remove device does and does not purge.
---

# The Brain's Mosquitto: ACL, bridge and parked set

These are templates, not a shipped config: the Brain image writes the real files from its
install configuration. The rules come from the
[module-bus message spec](../specs/2026-10-06-module-bus-messages-design.md) v1.3
(§12 brokers and bridges, §13 ACLs, §7.2 Remove device) and the
[NodeSource spec](../specs/2026-10-06-node-source-design.md) §4–§5. `<vid>` is the vehicle
id, `<brain>` the Brain's device id; identities are certificate CNs
(`use_identity_as_username true`, mTLS, no passwords).

## ACL (`acl_file`)

```text
# NodeSource's read connection (<brain>-nodesource): the §4 read set, own vid only.
user <brain>-nodesource
topic read ostler/v1/<vid>/+/status
topic read ostler/v1/<vid>/+/power
topic read ostler/v1/<vid>/+/vss/+
topic read ostler/v1/<vid>/+/manifest
topic read ostler/v1/<vid>/+/role/#
topic read ostler/v1/<vid>/+/faults/+
topic read ostler/v1/<vid>/+/event/+
# the raw tap (a second connection, <brain>-nodesource-tap; same identity)
topic read ostler/v1/<vid>/+/tap/+/meta
topic read ostler/v1/<vid>/+/tap/+/data
# its own requests (NodeSource P4) and, granted explicitly, the node's lab/req and tap/ctl
topic write ostler/v1/<vid>/<brain>/act/+
topic write ostler/v1/<vid>/<brain>/wake/+
topic write ostler/v1/<vid>/node/lab/req
topic write ostler/v1/<vid>/node/tap/ctl

# The broker host (Remove device's purge, spec §13): a separate identity on loopback,
# never handed to a device. The Brain passes it with --mqtt-host-cert/--mqtt-host-key.
user <brain>-broker-host
topic readwrite ostler/v1/<vid>/#

# A device: its own topics only (status with its will, power, manifest, role/#, vss/+,
# event/+, faults/+, act/+, wake/+; the node also tap/<ULID>/meta|data and lab/resp).
user node
topic readwrite ostler/v1/<vid>/node/#
topic read ostler/v1/<vid>/+/act/+
topic read ostler/v1/<vid>/+/wake/+
```

The alarm state (`vss/Vehicle.Ostler.Security.Alarm.State`) is covered by `vss/+`; the
Brain subscribes to it a second time at QoS 1 (spec §6), which the same line allows.

## Bridge to the parked broker (spec §12, owner answer 4)

```text
connection parked
address <parked-broker-holder>:8883
bridge_protocol_version mqttv50
try_private true
cleansession false
bridge_cafile /etc/ostler/ca.pem
bridge_certfile /etc/ostler/<brain>-bridge.crt
bridge_keyfile /etc/ostler/<brain>-bridge.key
# inbound: every device's state, claims, readings, faults, events, wake and act outcomes
topic +/status in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/power in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/vss/+ in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/manifest in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/role/# in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/wake/+ in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/act/+ in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/event/+ in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic +/faults/+ in 1 ostler/v1/<vid>/ ostler/v1/<vid>/
# outbound: only the Brain's own requests
topic <brain>/act/+ out 1 ostler/v1/<vid>/ ostler/v1/<vid>/
topic <brain>/wake/+ out 1 ostler/v1/<vid>/ ostler/v1/<vid>/
# never: tap/#, lab/req, lab/resp (the node uses the Brain's broker directly for them)
```

- `+/vss/+` bridges at QoS 1 so the alarm state keeps its QoS 1 across the bridge; the
  other readings arrive at the QoS they were published with (0).
- `act` and `wake` outcomes come back inbound, and the Brain's own requests may echo:
  consumers de-duplicate outcomes by `(id, state)` and events by `id`, and the Brain
  ignores its own requests coming back (spec §12).
- Until the bench shows that the bridge passes MQTT 5 properties (expiry, Correlation
  Data, Response Topic, user properties such as `first_seq`), receivers also check the
  JSON's `expires_at` and `id` (TODO.md, Bench).

## The parked broker's allow-list (firmware, spec §12, owner answer 5)

Compiled into every parked-broker build, as patterns under `ostler/v1/<vid>/+/`:
`status` (with its will), `power`, `manifest`, `role/#`, `vss/+`, `faults/+`, `event/+`,
`act/+` and `wake/+`. Excluded: `tap/#` and `lab/#`. Retained state is not migrated on a
handover; each device republishes its retained topics when it reconnects to a new holder.

## Remove device (spec §7.2, §13)

`POST /cluster/remove {device, confirm: true}` (owner, local link only; OpenAPI) is the
Brain's broker-host operation on **its** broker:

1. it records the device in the Brain's revocation list (`removed_devices.json` in the
   state directory) and ignores the device's messages from then on;
2. it calls the install's revoke hook (`DiagServer(device_revoker=…)`) that removes the
   device's ACL entry and revokes its certificate on the broker host (`revoked.broker`
   reads `not configured` without one);
3. over the broker-host identity it subscribes to `ostler/v1/<vid>/<device>/#`, publishes
   an empty retained message to every retained topic found there or seen by NodeSource,
   then re-reads the tree and reports `purged`, `refused` and `remaining`.

Limits: only the Brain's broker (the node purges its parked broker itself, a firmware
item); Mosquitto has no wildcard delete, so a retained topic the broker-host identity may
not read and NodeSource never saw stays; a device still connected can republish until its
ACL entry is gone (step 2). The response answers 503 when the purge was refused or left
something; the revocation stays recorded either way.
