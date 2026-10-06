---
title: "ADR-0040 — Power states and wake (asleep, waking, awake; wake requests, leases, queued actions with expiry)"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [references/research/power_states.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0037-role-holders-and-handover.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Accepted by the owner on 2026-10-06 (all recommendations). Every Ostler device publishes one power state (off, asleep, waking, awake, held, shutting down; offline only for an unexpected loss) and a reachability class (always, wakeable, check-in, none) with its wake paths. Awake is a sum of leases with expiry, as in AUTOSAR network management. Wake requests are first-class messages with a purpose, a requester, a deadline and a hold; the device wired to the wake path (the node for the brain and the wake wire) arbitrates them with role-based permission, per-requester and global rate limits, coalescing, an energy ledger, battery floors that refuse wakes, and timeouts. The owner's rule: an action declares whether it needs the brain; if yes the brain is woken and the action queued with an expiry; if no only the target module is woken through its own path; queued actions carry no authority, are re-checked by the executing gate, and never run after expiry or a driving-state change; Tier 2+ is never queued (default expiry 2 min, max 10 min). The alarm path never waits for a wake. The node gets two parked modes (ready for 72 h, then deep); budget 10 mA average, floors 12.2/12.0/11.8 V (bench-tuned). Owner and Driver may wake the Hub locally and remotely within quota, a Viewer's Read only within the remote quota; a brain wake asks for confirmation only on remote requests; a guardian alongside may take the parked broker while the node is in parked-deep; Wi-Fi modules with actions stay wakeable; apps wake only through action requests and held views. Confirmation by a simulated wake harness and bench measurements.
---

# ADR-0040 — Power states and wake

- **Date:** 2026-10-06
- **Status:** accepted (owner answers, 2026-10-06; see
  [Owner answers](#owner-answers-2026-10-06)). Builds on
  [ADR-0026](adr-0026-module-bus-10base-t1s.md),
  [ADR-0028](adr-0028-base-hardware-connectivity-and-remote-access.md),
  [ADR-0032](adr-0032-one-node-optional-brain.md) and
  [ADR-0033](adr-0033-action-categories-and-approvals.md); works with
  [ADR-0037](adr-0037-role-holders-and-handover.md) and
  [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md); amends ADR-0028, ADR-0032,
  ADR-0033 and ADR-0037 (recorded in their Amendments). Evidence:
  [power states research](../references/research/power_states.md).

## Context

- **The owner (2026-10-06):** "add-on actions wake the brain if necessary, or they wake the
  module they're trying to talk to, where the brain isn't necessary. We should probably try
  and convey this concept of 'asleep' and woken, perhaps build something more in depth around
  it."
- ADR-0032 §4 lists the brain's wake causes and the clean shutdown with a timeout, but says
  nothing about add-on modules, limits, cost or what a person sees. ADR-0033 §3 said the
  brain's gate checks add-on actions, which fails when the brain sleeps (ADR-0037 §7 and
  ADR-0033 Amendments moved it to the executing gate and left the detail to this ADR).
- The product family ([ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md):
  Diagnostics node, Guardian, Hub/brain, add-on modules on T1S,
  Ethernet, Wi-Fi or CAN) mixes devices that are always reachable, wakeable by a wire, or
  reachable only when they check in. Smart homes show the last kind as "Unavailable"
  (research §3.3); we want honest "Asleep".
- A node in deep sleep cannot be reached by a phone at all (no BLE, no AP; research §4).

## Decision drivers

- The alarm path never waits for, or depends on, a wake of the brain or the internet.
- A wake never grants authority; the executing gate decides (ADR-0037 §1).
- A hung or abused wake can never flatten the battery.
- Honest states: asleep is not offline, waking is visible, a queued action shows its expiry.
- Standard parts: MQTT 5 retained state, will, session and message expiry; wires for wakes.

## Decision

### 1. Vocabulary: one power state, one reachability class

Every device publishes a retained `ostler/v1/<vid>/<device>/power`:
`{state, since, class, wake_paths, next_checkin, leases, est_ma, reason}`.

| State | Meaning | How it is known |
|---|---|---|
| **off** | no supply (cut by its power owner, or not powered) | the power owner's report |
| **asleep** | announced sleep; reachable only through its wake paths or at check-in | retained `asleep`, then a clean MQTT 5 disconnect (no will) |
| **waking** | a wake was sent; not yet online | the arbiter's wake status |
| **awake** | online, no lease beyond its own needs | `status` online |
| **held** | awake because of one or more leases (§4.5) | `leases` non-empty |
| **shutting_down** | ordered to sleep or off; finishing | the device, then the power owner |
| **offline** | expected awake but silent | the will (ADR-0037 §3) |

`status` (ADR-0037 §3) gains the value `asleep` beside `online` and `offline`.

| Class | Reachable | Examples |
|---|---|---|
| **always** | on demand, no wake | node in parked-ready; brain in EV always-on |
| **wakeable** | on demand through a wake path, < 1 s plus boot | brain (power switch), wired modules (wake wire, CAN selective wake, TC10 once proven) |
| **check_in** | only when it next checks in; messages wait | deep-sleeping Wi-Fi or BLE modules, guardian modem in PSM (Matter LIT pattern) |
| **none** | not remotely | node in parked-deep for a phone; any device that is off and has no power owner |

### 2. States per device type

| Device | Driving | Parked states and targets (12 V, bench to confirm) | Wake paths |
|---|---|---|---|
| **Node** (Diagnostics) | awake | **parked-ready** ≤ 5 mA: auto light sleep, BLE, AP or Wi-Fi client, parked broker; **parked-deep** ≤ 0.5 mA: deep sleep, wires and timer only | ignition, door/alarm inputs, IMU, wake wire, CAN-transceiver wake, timer, modem ring; BLE and Wi-Fi in ready only |
| **Guardian** | awake | own cell; deep sleep with IMU wake, timed check-ins; modem PSM | IMU, tamper, timer, modem ring, wake wire if wired |
| **Brain** (Hub) | awake (ignition lease) | **off** (cut, < 1 mA for the switch); EV always-on: held | node power switch only |
| **Wired module** (T1S/Ethernet) | awake | asleep (µA class with a switched PHY) | wake wire; TC10 after its bench; Ethernet modules stay on the node's switched feed |
| **CAN module** | awake | asleep (< 64 µA transceiver) | CAN selective wake frame |
| **Wi-Fi module** | awake | auto light sleep (wakeable, 1–2.5 mA), **required for any module with actions**; deep sleep (check-in) only for sensor-only modules | DTIM, or its own timer check-in |
| **Camera** | awake if powered | off (feed switched by the node or an I/O module) | the switched feed; boot time per model |

The node starts parked-ready and stages to parked-deep after 72 h, on the energy budget, or
at the deep floor (§4.4). The phone and the cloud hold no power state;
they are requesters.

### 3. Wake sources

| Source | Wakes | Class of request |
|---|---|---|
| Ignition, engine running (12 V > 13.2 V) | node; then brain (ignition lease) | system |
| Door, OEM alarm, IMU, tamper | node or guardian; alarm handling first, then optionally the brain for cameras | alarm |
| Wake wire, CAN wake frame, TC10 | node and/or modules | module |
| Timer or schedule | any device with an RTC | scheduled |
| Phone over BLE or the node AP | node (ready only); then targets | interactive, local |
| Head unit or in-car LAN | as the phone | interactive, local |
| Cloud or Tailscale through the uplink holder | node (if its modem is reachable); then targets | interactive, remote |
| Software (OTA, upload, sync) | brain or module | background |

### 4. Wake requests

**4.1 The message.** A requester publishes on its own topic (per-device ACLs, ADR-0026)
`ostler/v1/<vid>/<requester>/wake/<id>`, or sends the same JSON to the node over BLE or the
AP: `{id, target, purpose: {kind: action|view|schedule|alarm|ota, ref}, class, user,
transport, hold_s, deadline, needs_brain}`. The **arbiter** answers on
`ostler/v1/<vid>/<arbiter>/wake/<id>`: `accepted | coalesced | refused(reason) | waking |
awake | failed | expired`. A wake carries **no grant and no approval**.

**4.2 The arbiter is whoever is wired to the path.** The brain's power switch and the wake
wire belong to the node (ADR-0032 §2); CAN wake frames to the device wired to that CAN;
check-in delivery to the parked broker holder. Like the transmit gate, the arbiter is tied
to wiring and **never hands over** (ADR-0037 §2): no arbiter means no wake on that path.

**4.3 Who may wake whom.**
- Only an authenticated, paired device or signed-in user; the purpose's **category** must be
  in the requester's role (ADR-0033 §2). The **Owner and the Driver** may wake the brain,
  locally and remotely. A **Viewer's Read** request may wake it only within the remote wake
  quota.
- **Remote** requests need the owner's "remote wake" setting (on by default for the Owner and
  Driver roles) and count against a daily quota. A remote wake is not remote *control*: the
  action that follows is still bound by ADR-0033 §6.
- Modules may wake the node (wire) and request the brain only for their declared purposes
  (manifest `wake.may_request`).
- Mesh and Home Assistant never wake the brain (ADR-0038: a mesh never commands).

**4.4 Limits and cost.**
- **Rate limits:** a token bucket per requester (starting values, tuned on the bench: 6 brain wakes an hour, 20 a day)
  and a global cap (30 brain wakes a day); alarm-class requests are exempt from the
  buckets but not from the hard floor.
- **Energy ledger:** the arbiter keeps a daily ledger of parked current and the estimated
  cost of each wake (brain ≈ 30 mAh per 5 min, research §5). Default budget ≤ 10 mA average
  (240 mAh a day), owner-settable and tuned on the bench; over budget, scheduled and background wakes are refused
  and interactive ones need confirmation. Cellular data per wake is counted against the
  uplink's meter (ADR-0028 §4).
- **Floors** (resting 12 V): **12.2 V** refuses scheduled and background wakes; **12.0 V**
  refuses brain wakes and shuts an awake brain down; **11.8 V** puts the node into
  parked-deep with alarm inputs only. The floor values are tuned on the bench. A refused wake
  says why ("Battery 11.9 V: hub not woken").
- **Coalescing:** a request for a target already waking or awake joins it; its hold becomes a
  lease. Ten requests make one wake.
- **Timeouts:** a brain that is not online by the boot timeout (60 s, bench-tuned) is cut, retried
  once, then locked out for an hour with an alert; a module not online in 2 s after a wire wake
  is reported `failed`. After two failed boots in a day, brain wakes need a local request.

**4.5 Stay-awake leases.** `{holder, target, until, reason}`; the device sleeps when its last
lease ends plus a linger (brain 60 s, modules 5 s). Maximums: interactive 15 min, renewed
while a screen that needs it is open; remote 5 min; ignition until ignition off plus 10 min;
OTA 30 min; schedule as set. No lease is unbounded except EV always-on, which the floors
still end. The Network page lists holders (§7).

### 5. The owner's rule for actions

Every action in a capability manifest declares **`runs_on`** (the device whose gate executes
it) and **`needs_brain`** (true when it needs a brain service: cameras' recorder, the large
logbook, replay, analysis). Then:

1. **`needs_brain: false`** (relay channel, aux heater on an add-on, arm the software alarm):
   wake **only `runs_on`** through its path (node relays a wire, CAN or Wi-Fi wake); send the
   request when it is online; **that device's gate** checks authority, category, tier, driving
   state from its own inputs, interlocks and the floor (ADR-0037 §1). The brain stays asleep.
2. **`needs_brain: true`:** wake the brain and **queue** the request on the arbiter with an
   `expires_at` (default 2 min, max 10 min), delivered when the brain is online; also as an
   MQTT 5 message expiry where it travels through a broker.
3. **Car-touching** actions run on the node gate; they never need the brain (ADR-0032 §2).
4. **Queued actions carry no authority** and are re-checked at execution. They are dropped
   with `expired` after `expires_at`, and with `state_changed` if the driving state, the
   requester's role or the transport differs from when they were queued.
5. **Only Tier 0–1 may be queued.** Tier 2–3 need a live confirmation: the UI wakes the
   target, then asks; an approval never waits in a queue (ADR-0033 §6).
6. A target that cannot be woken (class `check_in`) gets the request queued for its check-in
   with the same expiry, and the UI says "Runs when Relay box next checks in (≤ 10 min)".

### 6. Latency budgets

| Category (ADR-0033) | Needs the brain? | Acceptable | Budget |
|---|---|---|---|
| Alarm notification | never | immediate | ≤ 5 s local, without any wake |
| Security arming | no | interactive | ≤ 2 s (node) |
| Comfort, Accessories on a wired module | no | interactive | ≤ 2 s wire or CAN wake + action |
| Read, live or last values | no (node's retained data) | instant | ≤ 1 s |
| Read, logs, replay, clips | yes | with progress | ≤ 45 s to served (Pi boot 15–20 s + services, U) |
| Maintenance, Actuator tests, Procedures | runs on the node; ignition on | as today | brain usually awake already |

Phone to node over BLE adds ≈ 1–2 s (U); a cloud request adds the uplink's paging latency (U).

### 7. What people see

Asleep badges with last seen and wake path, a "Waking…" progress, queued actions with expiry
and Cancel, a confirmation when a **remote** request wakes the brain ("Wakes the hub, ≈ 30 s, uses
battery"; local wakes do not ask, and a "Don't ask again" choice is stored per user and device
and honoured on local links only),
a power column on the Network page, and the Link chip (no new strip chip) for the brain's
state. Apps cause a wake only through action requests and held views (no `wake()` call).
Detail: [UI spec §3.8](../specs/2026-10-06-ui-architecture-design.md) and
[app-model spec §13](../specs/2026-10-06-app-model-design.md).

### 8. Safety

- **A wake never bypasses a gate,** never carries a grant, and never changes the driving state.
- **The alarm path is independent:** node or guardian alarm handling and notification run
  first; a brain wake for cameras is best effort after the notification has gone.
- **Wake storms and DoS:** coalescing, buckets, the global cap, boot lockout, remote quota;
  refusals cost the arbiter nothing beyond the reply. A wake wire held asserted longer than
  2 s is masked and alerted ("wake wire stuck"); a module that wakes the segment more than a
  set rate is named from the first message after each wake and its wake permission dropped.
- **Parked drain:** the brain is always cut after shutdown (and set to power off on halt); the
  ledger and floors stage the node down; a device whose measured current says it did not
  sleep is switched off where its feed is switched, and alerted.
- **Wake-on-LAN is never used** on a remote path (no authentication; research §2.4).

### 9. Role holders while asleep (ADR-0037)

- **Parked broker:** the node in parked-ready. In parked-deep the node runs no broker and
  clears its claim when it sleeps; a **guardian fitted alongside takes over** the parked
  broker then, at the cost of its own cell (ADR-0037 §2, §4), and gives it back when the node
  is parked-ready or awake again.
- **Time source:** the node's RTC carries time through deep sleep; readings after a wake are
  `unsynced` until GNSS or SNTP is back.
- **Uplink manager:** the node while the brain is off (ADR-0037 §4); a cloud wake is only
  possible if the node or guardian has its own uplink.
- **PLCA coordinator:** a sleeping T1S segment needs none; the node coordinates when awake.
- **Wake arbiter:** not a handover role (§4.2).

## Confirmation

**Simulated (pytest, no hardware):** a wake harness with fake devices, a fake broker
(retained, will, session and message expiry), a fake power switch and wake wire, a 12 V
model and a controllable clock:
- a `needs_brain: false` action wakes only its target; the brain's switch never closes;
- a `needs_brain: true` action wakes the brain and runs once it is online; delivered after
  `expires_at`, it is dropped as `expired`; after a driving-state change, as `state_changed`;
- a Tier 2 action is refused for queuing;
- coalescing: ten requests in 5 s produce one wake and ten outcomes;
- buckets, the global cap and the remote quota refuse with their reasons; alarm requests pass
  the buckets; nothing passes the 12.0 V floor for the brain;
- a brain that never comes online is cut at the boot timeout, retried once, then locked out;
- a lease ends at its expiry; with no leases the brain is shut down after the linger;
- an approval or grant inside a wake request is ignored; the executing gate refuses an action
  that fails its own checks, whoever woke it;
- a clean sleep shows `asleep`, an unclean loss shows `offline`.

**Bench (dev kit: node, guardian prototype, Pi 5 brain, one wired and one Wi-Fi module):**
- **Parked current:** node parked-ready ≤ 5 mA and parked-deep ≤ 0.5 mA at 12 V over 24 h;
  brain off < 1 mA including the switch; each module's asleep figure recorded.
- **Wake latency:** phone (BLE) → node → relay module action ≤ 3 s, 50/50; phone → brain
  served ≤ 45 s, 20/20; wake wire → first MQTT ≤ 500 ms (ADR-0026).
- **Expiry:** a queued action with a 30 s expiry and a brain held from booting is never
  executed, and the phone shows "Expired".
- **Battery floor:** on a bench supply lowered to 11.95 V a brain wake is refused with the
  reason; at 11.75 V the node enters parked-deep and an alarm input still notifies.
- **Alarm with the brain off:** brain cut, no internet: a door or IMU trigger reaches a paired
  phone (ADR-0033 Confirmation), and no brain wake is needed for it.
- **Stuck wake wire:** held low, it is masked within 2 s + 1 s and alerted; parked current
  returns to target.

## Consequences

- The module-bus message spec gains the `power` and `wake/#` topics, the `asleep` status, the
  lease and outcome payloads, and the timeouts; `asyncapi.yaml` gains the channels at U5.
- The capability manifest gains `power` per device and `runs_on`, `needs_brain` and
  `queueable` per action (UI spec §5.1 amendment).
- The app SDK's `actions.request` gains wake and expiry options and the new outcomes
  (app-model spec amendment).
- Node firmware gains the arbiter, the ledger, two parked modes and an INA226-class current
  monitor (node sensors research).
- The hardware note's parked-current table needs the node's own line (research §6).

## Alternatives considered

- **Always wake the brain for any action.** Rejected: 30 s and battery for a relay click.
- **Keep the brain always on.** Kept only as the EV setting (ADR-0028 §2).
- **Let the broker queue alone enforce expiry.** Rejected: RAM queues vanish on reboot and a
  broker cannot see driving state; the gate re-checks.
- **Queue approvals for Tier 2+.** Rejected: an approval must be live (ADR-0033 §6).
- **Wake-on-LAN or Wi-Fi wake for alarm-critical modules.** Rejected (ADR-0026: wired).
- **Voting on who wakes the brain.** Rejected: the wiring decides (as for the gate).

## Relation to other ADRs

- **ADR-0032 §4:** stands; this ADR adds module wakes, limits, floors, leases and states
  (recorded in ADR-0032's Amendments).
- **ADR-0033 §3:** "the brain's gate does so for add-on actions" reads "the gate of the
  device the action runs on" (§5; as ADR-0037 §7 set out).
- **ADR-0033 §6:** a remote *wake* is permitted under quota; the action it serves stays
  read-only on remote paths unless the install override is set.
- **ADR-0037 §3:** `status` gains `asleep`; a holder that sleeps releases its claims.
- **ADR-0026, ADR-0027 §11:** the wake wire stays; a stuck-wire rule is added.
- **ADR-0028 §2** (superseded by ADR-0032 §4): its state words map to §1 here.

## Owner answers (2026-10-06)

The owner accepted every recommendation on 2026-10-06; the decision text above already reads
this way. Questions 1–7 are this ADR's draft numbering; 8 and 9 were open questions 13 and 14
of the app-model spec's §13.

1. **Node parked modes:** parked-ready for 72 h, then parked-deep (§2).
2. **Budget and floors:** 10 mA average; floors 12.2 / 12.0 / 11.8 V; all tuned on the bench
   (§4.4).
3. **Who may wake the Hub:** the Owner and the Driver, locally and remotely within the remote
   quota; a Viewer's Read request may wake it only within the remote quota (§4.3).
4. **Queued actions:** default expiry 2 min, maximum 10 min, Tier 0–1 only (§5).
5. **Guardian standby:** a guardian fitted alongside may take over the parked broker while the
   node is in parked-deep (§9; ADR-0037 Amendments).
6. **Brain-wake confirmation** only for remote requests (§7).
7. **Wi-Fi modules:** a module with actions stays wakeable (auto light sleep); deep sleep with
   check-in only for sensor-only modules (§2).
8. **Apps wake only** through action requests and held views; there is no `wake()` call
   (app-model spec §13.3).
9. **"Don't ask again"** is stored per user and device, and honoured on local links only
   (§7).
