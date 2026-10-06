---
title: "MQTT topic practice — prior art for the module-bus open questions 3, 4, 5, 7, 8, 9, 10 and 12"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-node-source-design.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0040-power-states-and-wake.md, references/research/ovms.md, references/research/mesh_networking.md]
summary: >
  Live research (2026-10-06) checking the manager's first-principles answers to module-bus spec §17 items 3, 4, 5, 7, 8, 9, 10 and 12 against MQTT 5.0, Sparkplug 3.0, Homie 5, Home Assistant MQTT, OVMS v3 (source), COVESA VSS 6.1 and master, J1939 DM1 practice, Mosquitto bridges, RFC 6763 TXT rules (with HAP, Matter and ESPHome keys) and the Meshtastic gateway source. Confirms QoS 1 for tap/ctl and lab/req (with id de-duplication and a short expiry on lab/req), hex bytes, wake expiry and the act outcome shape; changes the bridge answer (lab/resp stays on the Brain's broker with the tap, act outcomes bridge inbound), widens the parked allow-list (act, event, faults), moves the alarm signal to Vehicle.Ostler.Security.Alarm.State (an enum; VSS has no alarm node), adds a severity-carrying event/<name> at QoS 1, names faults/<pack>.<module>, replaces the "@module" topic with the pack leaf, keeps md and adds txtvers in TXT, and sets mesh-bridge QoS and retain per topic.
---

# MQTT topic practice for the module-bus open questions

Scope: [module-bus spec](../../specs/2026-10-06-module-bus-messages-design.md) §17 items 3,
4, 5, 7, 8, 9, 10 and 12. "Manager" is the manager's first-principles answer; quoted blocks
are proposed spec wording.

## Sources (checked 2026-10-06)

Facts are paraphrased in each question's "Prior art"; the links are here once.
- MQTT 5.0 (OASIS, os) §3.3.1.3, §3.3.2.3.3, §3.8.3.1, §4.10:
  [mqtt-v5.0-os](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html).
- Sparkplug 3.0.0 TCK assertions (data, birth and commands QoS 0 and not retained; NDEATH
  will QoS 1; host `STATE` QoS 1 and retained; `Node Control/Rebirth`):
  [spec PDF](https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf).
- Homie 5.0.0 (2025-05-11): [spec](https://homieiot.github.io/specification/).
- Home Assistant: [mqtt](https://www.home-assistant.io/integrations/mqtt/),
  [event.mqtt](https://www.home-assistant.io/integrations/event.mqtt),
  [alarm_control_panel.mqtt](https://www.home-assistant.io/integrations/alarm_control_panel.mqtt/).
- OVMS v3 source (master), read for QoS and retain flags:
  [ovms_server_v3.cpp](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/master/vehicle/OVMS.V3/components/ovms_server_v3/src/ovms_server_v3.cpp),
  [metrics_standard.h](https://github.com/openvehicles/Open-Vehicle-Monitoring-System-3/blob/master/vehicle/OVMS.V3/main/metrics_standard.h);
  topic table in [ovms.md](ovms.md).
- COVESA VSS: pinned 6.1 `vss/upstream/model.vspec`; upstream master
  [Body.vspec](https://github.com/COVESA/vehicle_signal_specification/blob/master/spec/Body/Body.vspec).
- J1939-73 DM1: general practice; the [CSS Electronics intro](https://www.csselectronics.com/pages/j1939-explained-simple-intro-tutorial)
  only names DM1 as a multi-packet DTC message (low weight).
- Mosquitto bridges: [mosquitto.conf(5)](https://mosquitto.org/man/mosquitto-conf-5.html).
- RFC 6763 §6: [RFC 6763](https://www.rfc-editor.org/rfc/rfc6763#section-6). TXT keys in
  practice: HAP ([go2rtc hap](https://pkg.go.dev/github.com/AlexxIT/go2rtc/pkg/hap)),
  Matter ([handbook](https://handbook.buildwithmatter.com/howitworks/discovery)), ESPHome
  ([mdns_component](https://api-docs.esphome.io/mdns__component_8cpp_source)).
- Meshtastic: [MQTT docs](https://meshtastic.org/docs/software/integrations/mqtt/),
  firmware [MQTT.cpp](https://github.com/meshtastic/firmware/blob/master/src/mqtt/MQTT.cpp)
  (master), payload limit ([forum](https://meshtastic.discourse.group/t/whats-the-text-limit/11440)).
- Traccar DTCs: [forum](https://www.traccar.org/forums/topic/how-to-view-fault-codes-dtc-coming-from-obd-device/).

## Q3. Wake and lab details (tap/ctl, lab/req QoS, encodings, wake expiry and outcome)

**Prior art**
- Sparkplug NCMD/DCMD and Homie `/set` commands are QoS 0 and rely on a state echo; OVMS
  answers commands at QoS 1; HA's command QoS is configurable (default 0).
- QoS 1 is at-least-once, so duplicates reach the receiver (MQTT 5 §4.3.2): dedup is the
  application's job.
- MQTT 5 expiry is a relative interval the broker counts down and forwards (§3.3.2.3.3);
  the requester turns an absolute deadline into it.
- Diagnostic tooling writes bytes as hex text (OVMS `obdii` commands, ELM327).

**Manager:** QoS 1 for both; `tap/ctl` `{op: start|stop, ulid}`; hex strings; wake expiry
from `deadline`; wake outcomes reuse the `act` outcome shape.

**Recommendation: confirm**, refined: the field is `session` (the tap header's name), not
`ulid`; `lab/req` is idempotent by `id` and short-lived; `wake` gets `act`'s Response Topic
and Correlation Data.

Proposed §8 and §11 wording:
> `tap/ctl` and `lab/req` are QoS 1, not retained. `tap/ctl` is
> `{op: "start" | "stop", session, buses?, filters?}`, where `session` is the ULID the
> Brain chose. A repeated `start` for a running session and a `stop` for an unknown one are
> no-ops. `lab/req` carries a Message Expiry Interval of at most 10 s, and the node
> answers a repeated `id` with its first `lab/resp` without running it again. A grant's
> single-use challenge already refuses a duplicate as `grant_used`. Service and reply bytes
> are lower-case hex strings with no separators (`"2110"`). A wake request carries a
> Message Expiry Interval of `deadline − now`, Correlation Data `id` and Response Topic
> `ostler/v1/<vid>/<arbiter>/wake/<id>`. Its outcome is the `act` outcome shape
> `{id, state, reason?, t_us}`, with `state` one of `accepted`, `coalesced`, `refused`,
> `waking`, `awake`, `failed` and `expired`.

**Confidence:** high. **Risks:** the ESP-IDF Mosquitto port's expiry must count without
SNTP (bench); the remembered-`id` table costs RAM (keep 16, like the challenges).

## Q4. Bridge patterns for answers (`<node>/act/+`, `<node>/lab/resp`)

**Prior art**
- MQTT 5 request/response (§4.10) assumes the reply comes back on the broker where the
  requester listens. Response Topic is a topic name, not a broker address.
- A Mosquitto bridge maps each pattern `in`, `out` or `both`. It has no "answer"
  semantics, and a pattern bridged in both directions risks echo loops. `try_private` and
  MQTT 5 No Local mitigate this between Mosquitto peers.
- Whether MQTT 5 properties (expiry, correlation data, user properties such as the tap's
  `first_seq`) survive a Mosquitto bridge is **not documented**. It must be bench-tested
  before anything relies on them across a bridge.

**Manager:** bridge `<node>/act/+` and `<node>/lab/resp` inbound, "as it does taps".

**Recommendation: change.** Taps are *not* bridged: the node publishes them on the Brain's
broker over its own connection (raw-tap §3). The lab channel belongs with the tap, so
`lab/resp` stays there too. `act` outcomes differ: any device on the parked broker may
execute an `act` (a relay module while the Brain sleeps), so outcomes bridge inbound.

Proposed §12 wording:
> **Bridge patterns.** Inbound: `+/status`, `+/power`, `+/vss/+`, `+/manifest`,
> `+/role/#`, `+/wake/+`, `+/act/+`, `+/event/+` and `+/faults/+`. Outbound: only
> `<brain>/act/+` and `<brain>/wake/+`. The tap and lab topics (`tap/#`, `lab/req`,
> `lab/resp`) are never bridged: the node publishes and subscribes to them on the Brain's
> broker over its own connection (raw-tap §3). Consumers de-duplicate `act` and `wake`
> outcomes by `(id, state)`. The bridge uses `bridge_protocol_version mqttv50` and
> `try_private true`, and the Brain ignores its own requests echoed back inbound.

**Confidence:** medium. **Risks:** inbound `+/act/+` also matches the Brain's own requests
(prove the echo guard on the bench); property forwarding across the bridge is unverified,
so the executing device also checks `expires_at` in the JSON (§9 carries it).

## Q5. The parked allow-list

**Prior art**
- Retained state lets an intermittent client rebuild its view (HA, Homie, OVMS metrics).
  Sparkplug avoids it only because it has rebirth and a primary host; a phone has neither.
- HA ages retained state out (`expire_after`, `message_expiry_interval`); Ostler shows the
  age instead (NodeSource §6.4).
- Size is small: ~100 `vss` leaves × ~300 B ≈ 30 kB, within the ≥ 2 MB PSRAM rule
  (ADR-0037 A14).

**Manager:** `vss/+`, `power`, `status` and `manifest` stay on the parked broker.

**Recommendation: confirm and widen.** ADR-0040 §5.1 has `needs_brain: false` actions run
on their `runs_on` device *with the Brain asleep*, so `act/+` must be parked. Alarm events
and faults must be parked too: Security and Home render from the node's retained data (UI
spec §3.8), and alarm paths never depend on the Brain (ADR-0033 §7).

Proposed §12 wording:
> **Parked topic set** (compiled into every parked-broker build, as patterns under
> `ostler/v1/<vid>/+/`): `status`, `power`, `manifest`, `role/#`, `vss/+`, `faults/+`,
> `event/+`, `act/+` and `wake/+`. Excluded: `tap/#` and `lab/#`.
> Retained state is not migrated on a handover (ADR-0037 A16). A device republishes its
> retained topics when it reconnects to a new holder.

**Confidence:** high. **Risks:** with a guardian or module holding the broker (node in
parked-deep) the node's retained `vss` are gone until it wakes, so phones show "no reading",
never zero; parked `act/+` widens what a phone reaches, so the ACL and gate (ADR-0033 §6)
stay the control.

## Q7. Events and the alarm-state signal

**Prior art**
- **State and event are separate everywhere.** The HA alarm panel holds a retained state
  enum, and HA events are non-retained (retained replays are discarded). OVMS has the
  `v.e.alarm` metric (retained) plus `event/<name>` and `notify/alert/<subtype>`
  (non-retained). Homie uses retained properties plus non-retained momentary properties.
- OVMS and Homie send events at QoS 0 with no payload; OVMS sends alerts at QoS 1. An
  alarm event that must reach a phone needs QoS 1.
- **VSS has no alarm node** in 6.1 or on master. A non-standard name under a standard
  branch (`Vehicle.Body.Alarm.*`) breaks ADR-0016, which reserves `Vehicle.Ostler.*` for
  meanings VSS lacks. A boolean cannot carry the spec's "armed, disarmed, triggered" (§16)
  or the UI's Disarmed / Armed / Alerting (UI spec §3.2).
- The mesh research already sketched `+/event/alert`, so one event family with a class
  and a severity is enough.

**Manager:** `event/<name>`; `Vehicle.Body.Alarm.IsActive` (or an `ostler.` prefix).

**Recommendation:** keep `event/<name>` (confirm). For the alarm signal, change both the
branch and the type.

Proposed §3 and §6 wording, plus a new §6a:
> **`event/<name>`**: published by the device itself, QoS 1, never retained, Message Expiry
> Interval 3600 s. `<name>` is one level, dotted, lower case (`alarm.triggered`,
> `gate.conflict`, `fault.new`). Payload: `{id (ULID), name, class, severity: "info" |
> "warning" | "alarm", ts, t_us, boot, source?, cause?, text?}`. Consumers de-duplicate
> by `id`. The owner's allowlists (mesh, notifications) filter on `class` and `severity`.
> The alarm state is a reading, not an event:
> `vss/Vehicle.Ostler.Security.Alarm.State`, retained, QoS 1. Its VSS overlay node is a
> `string` sensor with allowed values `DISARMED`, `ARMING`, `ARMED`, `TRIGGERED`, aliases
> `ovms: v.e.alarm` (true only when `TRIGGERED`) and HA `alarm_control_panel`.
> `ARMED` maps to `armed_away`, `ARMING` to `arming`, `TRIGGERED` to `triggered` and
> `DISARMED` to `disarmed`. On the wire it is published like any labelled field: `state`
> holds the label, and `value` holds its index in the allowed list. Every change to
> `TRIGGERED` also publishes `event/alarm.triggered` with its `cause`.

**Confidence:** high on the branch and the enum; medium on the expiry and the QoS 1
exception. **Risks:** §6 makes `vss` QoS 0, so this leaf is a written exception; the overlay
entry needs ADR-0016's review; a later upstream alarm node is aliased at a pin bump.

## Q8. `faults/<module>`

**Prior art**
- J1939 DM1 sends the **whole active list** plus lamp status, periodically and on change.
  A receiver never merges deltas.
- VSS 6.1 `Vehicle.Diagnostics.DTCList` is a string[] in OBD format, with a separate
  `DTCCount`, so the list is one value.
- OVMS has no standard DTC metric (vehicle modules use ad-hoc notifications). Traccar
  exposes DTCs per device protocol, as attributes and a "fault" event
  ([forum](https://www.traccar.org/forums/topic/how-to-view-fault-codes-dtc-coming-from-obd-device/)).
- A retained snapshot per source plus an event on change is the HA and OVMS state-plus-event
  pattern again (Q7).

**Manager:** `faults/<module>`, retained, today's fault-list shape.

**Recommendation: confirm**, but name the level like a pack leaf, so that two packs or an
OBD node cannot collide. Distinguish "read, none" from "never read".

Proposed §6b wording:
> **`faults/<pack>.<module>`** (for example `faults/lr_d2.td5`; an OBD node uses
> `faults/obd.<ecu>`), retained, QoS 1, the **whole** current list after every fault read
> (never a delta): `{module, status: "ok" | "faults" | "error" | "unimplemented", faults:
> [{code, text?, state?, c}], note?, ts, t_us, boot, source}`. This is today's
> `faultscan` row with time and a source tag. `faults: []` with `status: "ok"` means "read,
> none". An absent topic means "not read". A clear publishes the new read after the
> logbook snapshot (ADR-0033). A code that appears publishes `event/fault.new`. Identity
> data is scrubbed as for `vss` (ADR-0036). The Brain derives
> `Vehicle.Ostler.Diagnostics.DtcCount` and does not publish `Vehicle.Diagnostics.DTCList`,
> whose OBD-only format does not fit pack codes.

**Confidence:** high. **Risks:** freeze frames may need their own topic later (not v1);
keep `text` optional for the parked broker's RAM.

## Q9. One VSS path from two modules on one device

**Prior art**
- **No surveyed protocol merges in transport.** Sparkplug gives every device its own
  metric namespace. Homie puts a property under its node (`…/<device>/<node>/<prop>`), so
  two modules are two topics. HA keeps one entity per source and merges with helper
  entities. OVMS's single metric is last-writer-wins, which is the bug in our TODO.
- Selection already lives on the Brain (NodeSource §6.5: `sel`, sources by
  `<device>/<source>`). Selecting on the node as well would put the rule in two places,
  which goes against single source of truth.
- The leaf grammar already has a per-module name: `<pack>.<module>.<field>` (§6).

**Manager:** one retained topic per leaf (selected) plus `vss/<leaf>@<module>` per module.

**Recommendation: change.** Add no new `@` grammar and no selection on the node. The pack
data names one module as the **primary** for a VSS path. The node publishes the VSS leaf
only from that module, and every other module's reading of the same meaning under its
existing pack leaf.

Proposed §6 wording:
> When more than one module of one device decodes the same VSS path, the pack's signal store
> marks one field `primary` for that path. The device publishes `vss/<VSS path>` only from
> the primary field, and the others under their pack leaf `vss/<pack>.<module>.<field>`,
> both retained, each with its own `source`. A consumer that wants every source reads the
> pack leaves. Selection across devices stays with the consumer (NodeSource §6.5).

**Confidence:** medium. **Risks:** when the primary module is not polled (Td5 with the
ignition off) the VSS leaf goes stale while the other is fresh; the Brain still selects the
fresher pack leaf, but parked phones see the stale leaf with its age. It needs a `primary`
marker in the pack JSON (D2 battery: Td5).

## Q10. mDNS TXT keys

**Prior art**
- RFC 6763 §6: keys ≤ 9 characters, case-insensitive; the record ideally under 200 bytes;
  `txtvers` first.
- HAP announces change with a small counter (`c#`), a model (`md`) and a paired flag
  (`sf`). Matter announces vendor and product (`VP`) and a device name (`DN`) for the
  commissioning UI. ESPHome sends `version`, `board` and `friendly_name`. All three keep
  a model hint in TXT. An unpaired Ostler device has **no broker credentials**, so TXT is
  all the Brain sees before adoption.

**Manager:** `etag`; drop `cv`, `md`, `mf`.

**Recommendation: partly change.**
- Keep `etag` with the full 64-hex value. `etag=` plus 64 characters is 70 bytes, and the
  record stays about 170 bytes with `roles` (ADR-0037 §3).
- Drop `mf`: the manifest topic follows from `vid` and the instance name.
- Replace `cv` with RFC 6763's `txtvers=1`.
- Keep a short `md`, so the Brain's adoption list can name an unpaired device that has
  no manifest on the broker yet.

Proposed §14 wording:
> TXT keys, in this order: `txtvers=1` (RFC 6763 §6.7; bumped only by an incompatible TXT
> change), `var=`, `md=` (model, ≤ 24 bytes; shown in the adoption list before pairing),
> `fw=`, `pr=` (`0` unpaired), `roles=` and `etag=` (the manifest's full lower-case hex
> etag; absent while unpaired). The whole record stays under 200 bytes. Unknown keys are
> ignored. The manifest topic is `ostler/v1/<vid>/<instance>/manifest` and is not
> advertised.

**Confidence:** medium-high. **Risk:** a long `roles` could pass 200 bytes; then truncate
`etag` to 16 hex (enough for change detection).

## Q12. Mesh bridge QoS, retain and ACL

**Prior art**
- The Meshtastic gateway firmware publishes with retain off through PubSubClient (MQTT
  3.1.1, QoS 0 publishes) and subscribes at QoS 1. LoRa has no QoS or retain, only a
  per-packet `want_ack` and the optional Store & Forward module.
- The application payload is at most 233 bytes (`DATA_PAYLOAD_LEN`); JSON on its MQTT is
  ESP32-only. Anything crossing the mesh is a compact message, never MQTT semantics.
- On the in-car side the bridge is an ordinary device. Its readings and health follow the
  spec's state rules (retained), and received messages follow the event rules (Q7).

**Manager:** QoS 0, no retain over the mesh; ACL also covers its own `status`, `manifest`
and `power`.

**Recommendation:** confirm the ACL. Split the QoS answer: the radio side has no MQTT QoS,
and the bridge's in-car topics follow the spec's state and event rules.

Proposed §16 wording:
> Over the radio nothing is retained and nothing is retried, except that alarm-state
> packets to paired Ostler peers set `want_ack`. In the car: `in/text` and `in/alert`
> are QoS 1, not retained, Message Expiry Interval 86 400 s. `in/position/<peer>` is QoS 0,
> retained, Message Expiry Interval 3600 s, so a peer's last position fades. `state/link`
> is QoS 0, retained. The bridge also publishes its own `status` (with its will),
> `power` and `manifest` like any device. It never publishes `role/#`, `vss/+`, `act/+`,
> `wake/+` or `event/+`.

**Confidence:** high on the ACL and the radio side; medium on the expiry values.
**Risk:** retained peer positions are other people's data; the expiry and the per-channel
opt-in (ADR-0038 §5) must both hold.

## Conflicts with ADRs/specs

- **Module-bus spec §3:** add `event/<name>` and `faults/<pack>.<module>` rows; fill the
  `tap/ctl`, `lab/req` and wake-expiry cells; mark the alarm leaf's QoS 1; mesh rows per Q12.
- **§6:** the "`value` is numeric" rule gains the labelled-enum sentence (Q7) and the
  primary-module rule (Q9). **§12:** bridge list (Q4) and parked set (Q5).
- **§14 and connectivity research §6:** TXT keys become `txtvers`, `var`, `md`, `fw`, `pr`,
  `roles`, `etag`; the IANA draft's "Defined TXT keys" follows.
- **ADR-0016 / `vss/ostler.vspec`:** a reviewed `Vehicle.Ostler.Security.Alarm.State` entry
  (in scope: the ADR's examples name "guardian state").
- **ADR-0038 §2 and mesh research §5:** the ACL adds the bridge's own `status`, `power`,
  `manifest`; `event/alert` becomes `+/event/+` filtered by class and severity.
- **NodeSource §4–§5:** subscribe `…/+/event/+` and `…/+/faults/+` (QoS 1); bridge text per Q4.
- **D2 pack signal store:** a `primary` marker for a VSS path decoded by two modules (Q9).

## Open points for the owner

1. **Q9:** a pack-declared primary module (recommended) or the manager's selected-plus-`@`
   topics? The trade-off is a stale VSS leaf for phones against a second selection rule
   on the node.
2. **Q7:** should alarm state be the one QoS 1 reading, or should all of `vss` stay QoS 0
   with the alarm event carrying reliability?
3. **Q10:** keep `md` in TXT for the adoption list before pairing (recommended), or show
   only `var` until the device is adopted?
4. **Bench:** whether the Brain's and the ESP-IDF Mosquitto bridge forward MQTT 5
   properties and apply expiry without SNTP. Q3 and Q4 depend on it.
5. **Expiry values** for events (1 h), mesh text (24 h) and peer positions (1 h) are
   starting points. The owner may prefer them tied to the ADR-0038 rate limits.
