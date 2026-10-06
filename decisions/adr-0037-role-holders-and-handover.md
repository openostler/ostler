---
title: "ADR-0037 — Role holders and handover (transmit gate, parked broker, time source, PLCA coordinator, uplink manager)"
area: decisions
status: locked
version: 1.2
updated: 2026-10-06
depends_on: [references/research/cluster_view.md, references/research/connectivity_uplink.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Accepted by the owner on 2026-10-06. Data in an Ostler car is decentralised (every device publishes its own manifest, status and readings), but a few roles must have exactly one holder at a time. The transmit gate (one per car bus) belongs to the node wired to that bus and never hands over: no holder means no transmit. The parked broker (node → guardian), the time source (best clock first, ranked by clock quality; u-blox placement pending product-family research), the PLCA coordinator (per T1S segment: node → guardian, never the brain) and the uplink manager (brain → node) move by a static priority the owner sets at pairing, with timeouts, a term number and hysteresis; no voting. A guardian fitted alongside a node is the standby for the parked broker, PLCA and time, at a parked-current cost. The cluster is shown on the Network core app, which absorbs More → Devices. An add-on action wakes the brain only if the brain is needed, otherwise the target module directly; the executing gate keeps the authority (detail: the power-state work, ADR-0040 draft, pending). Holders announce with a retained claim on their own MQTT topic, an online status with an offline will, and a roles hint in the mDNS TXT record. Split brain is made harmless rather than voted away. Holding a role never grants authority: every approval is checked by the gate that executes it, whichever UI asked. Confirmation by a simulated role harness and bench pulls. Amended 2026-10-06 by ADR-0039 and ADR-0040: `status` gains `asleep`; a holder that sleeps releases its claims; a guardian alongside takes the parked broker while the node is in parked-deep; the u-blox sits on the Diagnostics node and, with PPS, ranks first for time. Amended 2026-10-06 (owner): an always-on add-on module that declares the `pbroker` role and at least 2 MB of PSRAM in its manifest is the last parked-broker fallback (node → guardian → module), so a car with only add-on modules still coordinates; deep-sleeping modules (check-in or none) are never eligible; ties go to the owner's priority, then the lowest device id; the module hands the role back when a Diagnostics node or Guardian is healthy for 60 s.
---

# ADR-0037 — Role holders and handover

> **Amended 2026-10-06 (product family and power states, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), [ADR-0040](adr-0040-power-states-and-wake.md)):** `status` gains `asleep`; a holder that sleeps releases its claims; with the node in parked-deep a guardian fitted alongside takes the parked broker; the time-source order is confirmed, with the Diagnostics node's u-blox and PPS ranking first; "Lite" reads "Ostler Diagnostics". See [Amendments (product family and power states)](#amendments-2026-10-06-product-family-and-power-states).
> **Amended 2026-10-06 (owner, parked broker on add-on modules):** an eligible always-on add-on module (manifest `roles` lists `pbroker`, `power.class` `always`, `memory.psram_kb` ≥ 2048) is the **last** parked-broker fallback after the node and the guardian; deep-sleeping modules never are; ties by owner priority then lowest device id; it hands back when a Diagnostics node or Guardian is healthy for 60 s. See [Amendments (parked broker on add-on modules)](#amendments-2026-10-06-parked-broker-on-add-on-modules).

- **Date:** 2026-10-06
- **Status:** accepted (owner answers, 2026-10-06; see
  [Amendments](#amendments-2026-10-06-owner-answers)). Builds on [ADR-0026](adr-0026-module-bus-10base-t1s.md),
  [ADR-0027](adr-0027-ip-everywhere-ecosystem-architecture.md),
  [ADR-0028](adr-0028-base-hardware-connectivity-and-remote-access.md) and
  [ADR-0032](adr-0032-one-node-optional-brain.md); keeps
  [ADR-0033](adr-0033-action-categories-and-approvals.md) unchanged. Evidence:
  [cluster view research](../references/research/cluster_view.md).

## Context

- The owner (2026-10-06): every node shows its peers, the full app shows the whole cluster,
  and "some roles have exactly one holder": the transmit gate (one per car bus, on the node
  wired to it), the parked broker, the time source and the T1S PLCA coordinator. Define the
  handover order (for example brain → node → guardian) and the failure behaviour. "The data
  is decentralised; the authority is not: approvals are always checked by the gate that
  executes them, whatever UI asked."
- Today the holders are scattered: the gate and the parked broker on the node (ADR-0032 §2);
  NTP on the Pi (ADR-0027 §7); the PLCA coordinator on the node, or the guardian when it
  replaces the node (ADR-0026 Amendment 3); "hand-over when a guardian is fitted" is an open
  point (ADR-0028 §1); uplink selection on the Pi (ADR-0028 §4), with per-device SIMs
  (ADR-0032 §7).
- The brain sleeps when parked (ADR-0032 §4); the guardian may sit alongside the node as a
  hidden battery-backed tracker (ADR-0032 §5); the cluster often has only two always-on
  devices, so voting quorum is impossible (research §3).

## Decision drivers

- One transmitter per car bus, always; a failure must close the path, never open a second.
- The alarm path works with the brain off and no internet (ADR-0033 §7).
- Deterministic and explainable: the owner can read who holds what and why.
- Works offline, on ESP32 firmware, with standard parts (MQTT 5, mDNS, chrony, the T1S PHY).
- No new trust: a role claim is a message from an authenticated device under its own ACL.

## Decision

### 1. Two kinds of state

- **Decentralised data.** Each device publishes its own capability manifest (retained),
  status, readings with source tags and its role claims. Any full-app host (brain, cloud,
  phone) builds the cluster view from them; no device holds a master registry.
- **Single-holder roles.** The roles in §2 have at most one holder per scope at any time.
- **Authority is never a role.** Holding a role (broker, hub, time) gives no power to approve.
  Every grant is verified by **the gate that executes it** (ADR-0032 §2, ADR-0033 §3): the
  node's transmit gate for anything that reaches a car bus; the executing device's own gate
  and interlocks for add-on actions. A UI on any host only requests.

### 2. The roles

| Role | Scope | Candidates, in order | Hands over? | No holder means |
|---|---|---|---|---|
| **Transmit gate** | one per car bus (`bus_id`, e.g. `kline-diag`, `can-body`) | only the node wired to that bus whose manifest declares `transmit` on it | **Never** (tied to the wiring) | no transmit on that bus; reads continue if a listener is wired; actions show "No gate for this bus" |
| **Parked broker** | one per vehicle | node → guardian | yes | parked devices use the wake wire or CAN to the node (ADR-0028 §5 fallback); alarms go direct to a paired phone or out the device's own uplink (ADR-0033 §7) |
| **Time source** | one per vehicle | **best clock first**: ranked by clock quality (GNSS fix with PPS, then GNSS fix without PPS, then a disciplined clock in holdover, then a phone seed on Lite), ties broken by the owner's priority; which device carries the 10 Hz u-blox is **pending (product-family research)** | yes, best clock first | each device free-runs on its RTC; readings carry `time: unsynced`; the logbook marks the gap |
| **PLCA coordinator** | one per T1S segment | node → guardian (only if wired to that segment); **never the brain** | yes, standby only | the segment runs CSMA/CD (degraded, still works); alert |
| **Uplink manager** | one per vehicle LAN | brain → node | yes | no shared default route; each device uses its own SIM, if any; local-first is unaffected |

- **Where a device order applies:** the uplink manager as brain → node only (the
  guardian's SIM stays its own, for the alarm path); the parked broker and PLCA coordinator
  as node → guardian (the brain is not a candidate, because it sleeps). **Where it does
  not:** the transmit gate (no order; wiring decides) and the time source (best clock
  first, whichever device has it; the owner's priority only breaks ties).
- **Guardian standby.** A guardian fitted alongside a node is the standby parked broker,
  the standby PLCA coordinator (only if wired to that segment) and a time-source candidate.
  These duties cost parked current, which the guardian's power budget must carry.
- **Always-on mode** (ADR-0028 §2) does not move the parked broker: the brain's broker serves
  everything and stays bridged to the node's, which keeps the role.
- **Not roles:** the cluster view and the merge (any full-app host builds one; ADR-0032 §11);
  the phone and the cloud hold no in-car role. The local CA and pairing authority stay where
  ADR-0027 §8 and ADR-0032 §12 put them and **never move automatically**; losing the brain
  only blocks new pairings.

### 3. How holders announce

1. **Status with a will.** Every device keeps a retained
   `ostler/v1/<vid>/<device>/status` = `online` with an MQTT 5 will of `offline` (retained),
   keep-alive 10 s, will delay 0 s. The broker publishes the will 15 s (1.5 × keep-alive)
   after a device goes silent (MQTT 5).
2. **Retained claim on its own topic.** `ostler/v1/<vid>/<device>/role/<role>[/<scope>]`
   carries `{role, scope, term, priority, since, reason}`. Per-device ACLs (ADR-0026) already
   allow only that device to publish there, so no shared "role" topic is needed. A claim is
   void while its device's status is `offline`. Releasing a role clears the retained claim
   (empty payload).
3. **mDNS TXT hint.** The `_ostler-mod._tcp` record carries
   `roles=gate:kline-diag,pbroker,time,plca:t1s0` alongside `fw=`, `var=` and the manifest
   `etag`, kept small (RFC 6763 §6). A clean shutdown sends a goodbye. mDNS is the
   broker-independent liveness signal: it still works when the broker is the thing that
   failed.
4. **Bridges carry them.** The brain's bridge to the node's broker includes the `status`
   and `role/#` patterns, so both brokers hold the same view.

The candidate order and each device's priority are set by the owner at pairing, stored in
each device's signed install configuration, and published in its manifest. A device whose
manifest does not list a role, or which is not in the owner's order, may not claim it; every
consumer ignores such a claim and the Network page flags it.

### 4. Failure detection and handover

| Role | Holder is lost when | Standby takes over after | Gives back |
|---|---|---|---|
| Parked broker | the guardian cannot reach the node's broker **and** the node's mDNS record is gone or unanswered | 30 s of both | when the node has been healthy for 60 s; clients reconnect to the node by mDNS name |
| Time source | the holder's status is `offline`, or its claim reports no GNSS fix and its root distance passes 1 s (chrony orphan-style) | 60 s | when a better clock (higher quality class, or equal class and higher priority) has been stable for 120 s |
| PLCA coordinator | PLCA status FAIL (about 1 s after the BEACON stops) on the standby's PHY | 5 s of FAIL, then the standby reconfigures as ID 0 | the standby returns to its own ID as soon as its PHY reports an unexpected BEACON, or the node's status is `online` for 10 s |
| Uplink manager | the brain's status is `offline` (it slept) | at once (the node's own uplink was already its fallback) | when the brain is awake and its uplink profile is up |

Timeouts are bench starting points; the bench values become the module-bus message spec's
numbers.

### 5. Split-brain rules

- **Term numbers.** A takeover increments `term`. On seeing two live claims for one role and
  scope, every device and every view honours the higher term, then the higher priority; the
  loser releases at once.
- **Two signals before takeover.** No role moves on MQTT silence alone; it needs a second,
  independent signal (mDNS absence, PLCA FAIL, or loss of the wired link). A partitioned
  broker therefore does not create a second parked broker on its own.
- **Gate duplicates are a configuration fault.** Two devices claiming the transmit gate for
  one `bus_id` is never resolved by priority: **both refuse to transmit** on that bus,
  raise an alert, and stay listen-only until the owner removes one at pairing.
- **Harmless by construction.** A duplicate broker, time source or cluster view can confuse
  readings, never authorise a write: the executing gate re-checks every grant, its own
  driving state from its own bus or GNSS, and its own install configuration (ADR-0033 §6).
  A gate never trusts a time or state that came from a role holder for a safety decision.

### 6. What the UI shows

Every device's own page lists the peers it sees and the roles they claim (read-only, with
links to the peers' own pages); every full-app host shows the whole cluster on the Network
page, including who holds each role, since when, the candidates, and the last handover and
why. **Network is a core app that absorbs More → Devices**: the device list and every device
page live inside it. A view whose inputs are stale is read-only and shows its age (the
Proxmox lesson). Detail: [UI spec §3.7](../specs/2026-10-06-ui-architecture-design.md#37-network-page-peer-view-and-cluster-view-accepted-2026-10-06)
and [app-model spec §12](../specs/2026-10-06-app-model-design.md#12-the-network-app-and-device-pages-accepted-2026-10-06).

### 7. Add-on actions and wake

An add-on action **wakes the brain** if the brain is needed to carry it out, and otherwise
**wakes the target module directly** (wake wire, CAN or the node's broker). Either way the
authority stays with **the executing gate**: the target device's own gate and interlocks for
an add-on action, the node's transmit gate for anything that reaches a car bus (§1). A
sleeping brain therefore never blocks an add-on action that does not need it, and never
approves one by being awake. The detailed power-state and wake model is the power-state
work (ADR-0040 draft, pending).

## Confirmation

**Simulated (pytest, no hardware):** a role harness with fake devices, a fake broker
(retained messages, wills, keep-alive) and a fake mDNS responder, with a controllable clock:
- each takeover and give-back in §4 happens within its timeout ± one tick, and not earlier;
- MQTT silence alone moves no role; a broker partition yields one parked broker;
- two gate claims on one `bus_id` leave both devices refusing transmit, with an alert;
- a claim from a device not in the owner's order, or under another device's topic, is
  ignored (ACL test);
- the higher term wins on a duplicate claim, and the loser clears its retained claim;
- an approval minted on any host is refused by the executing gate when it fails the gate's
  own checks, whichever device holds the broker or time role.

**Bench (dev kit: node, guardian prototype, brain, one T1S or Ethernet module):**
- pull the node's power: the guardian claims the parked broker within 30 s + 5 s, a parked
  alarm event still reaches a paired phone; restore it: the node takes the role back after
  60 s and no event is duplicated;
- unplug the GNSS antenna on the time-source holder: the next-best clock becomes the time
  source within 60 s and module clocks stay within ADR-0027's 10 ms; power down the holder:
  the same;
- on T1S hardware only (ADR-0026 bench plan): remove the coordinator, the segment keeps
  passing MQTT in CSMA/CD; with a standby, PLCA returns within 5 s + 1 s; restoring the node
  causes no lasting duplicate BEACON;
- remove the node wired to K-line: every transmit request is refused with "No gate for this
  bus", and no other device offers to transmit.

## Consequences

- The module-bus message spec gains the `status` and `role/#` topics, the claim payload, the
  TXT keys and the timeouts; `asyncapi.yaml` gains the channels at U5.
  *Note (2026-10-06):* written as the [module-bus message spec](../specs/2026-10-06-module-bus-messages-design.md) (§4, §7, §14, §15).
- The capability manifest (UI spec §5.1, ADR-0032 §6) gains `roles` (roles a device can
  hold, with scope) and `transmit` per `bus_id`.
- The guardian, when alongside a node, gains standby duties (broker, PLCA if wired, time),
  which cost parked current; its power budget must allow it.
- The Network page and every device's own page render the role table.

## Alternatives considered

- **Voting quorum (Raft, corosync).** Rejected: needs three voters; often only two devices
  are always on, and the brain sleeps.
- **The brain as the single coordinator of everything.** Rejected: the brain sleeps, and the
  alarm path must not depend on it (ADR-0033 §7).
- **A shared retained "role" topic written by whoever holds it.** Rejected: breaks per-device
  ACLs (ADR-0026) and lets any device overwrite a claim.
- **Handing over the transmit gate** to the guardian or the brain. Rejected: the gate is the
  wiring; a second transmit path is exactly what the gate exists to prevent.
- **Self-fencing by reboot** (Proxmox HA). Rejected: a rebooting node drops the alarm path.

## Relation to other ADRs

- **ADR-0026:** Amendment 3 (the node is the PLCA coordinator, or the guardian when it
  replaces the node) stands; this ADR adds the guardian as a **standby** when it sits
  alongside on the same segment (recorded as ADR-0026 Amendment 8).
- **ADR-0027:** §3 and §7 put NTP on the Pi; this ADR makes the time source a role, and NTP
  runs on its holder (recorded in ADR-0027's Amendments of 2026-10-06). §4's PLCA ID
  assignment at pairing stands; the ID table is part of each device's install configuration
  so a standby can coordinate.
- **ADR-0028:** answers §1's open point (hand-over when a guardian is fitted) and formalises
  §5's fallback "the guardian hosts the parked broker".
- **ADR-0032:** §2 (gate and parked broker on the node) and §4 ("with the brain off, the node
  is the hub again") stand unchanged.
- **ADR-0033:** unchanged in substance. §3's "the brain's gate does so for add-on actions"
  reads "the executing gate" (§7 here; recorded in ADR-0033's Amendments of 2026-10-06).

## Amendments (2026-10-06, owner answers)

The owner answered the open questions on 2026-10-06 and accepted this ADR. The text above
already reads this way; the answers are kept here for the record. Question numbers in
brackets are the owner's numbering for the networking questions of that day.

1. **Handover order** (owner Q2: yes). The orders stand: node → guardian for the parked
   broker and the PLCA coordinator, never the brain; brain → node for the uplink manager.
   The **time source** is no longer a fixed device order: it is **best clock first** (§2),
   because which device carries the 10 Hz u-blox is **pending (product-family research)**:
   an "Ostler Diagnostics" OBD-port node is being designed, and the receiver's placement
   follows from that work (ADR-0032 Amendments).
2. **Uplink manager.** A single-holder role, brain → node; the guardian keeps its SIM for
   the alarm path (§2). ADR-0028 §4 is amended to match.
3. **Guardian standby** (owner Q2: yes). A guardian fitted alongside a node acts as standby
   parked broker, PLCA coordinator (if wired to that segment) and time-source candidate, at
   a parked-current cost (§2, Consequences).
4. **Add-on actions with the brain off** (owner Q8). An add-on action wakes the brain if the
   brain is needed, or wakes the target module directly when it is not; the authority stays
   with the executing gate (§7). The detailed power-state and wake model is being researched
   separately: the power-state work, ADR-0040 draft, pending.
5. **CA and pairing authority.** Not changed by the answers: the local CA and pairing never
   move automatically, and losing the brain only blocks new pairings (§2).
6. **Timeouts.** The values in §4 are bench starting points, tuned on the bench.
7. **The Network page** (owner Q1: yes). Network is a core app that absorbs More → Devices
   (§6; UI spec §3.7, app-model spec §12).

## Amendments (2026-10-06, product family and power states)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) and [ADR-0040](adr-0040-power-states-and-wake.md) (both accepted with the owner's answers of 2026-10-06). The decision
text and the Amendments above are unchanged; where these entries differ, they win.

8. **`asleep` status** (§3). `status` gains `asleep` beside `online` and `offline`: a device
   that goes to sleep publishes a retained `asleep` and disconnects cleanly (no will);
   `offline` stays for an unexpected loss (ADR-0040 §1). A claim is void while its device is
   `asleep`, as while it is `offline`.
9. **A holder that sleeps releases its claims** (§3, §4): it clears its retained claims
   before it sleeps, and the candidates follow §4. The transmit gate still never hands over
   (§2): while its node sleeps there is no transmit on that bus.
10. **Parked broker in parked-deep** (§2, §4; ADR-0040 §9). When the node enters parked-deep
    it runs no broker and releases the parked-broker claim; a **guardian fitted alongside
    takes it over**, at the cost of its own cell, and gives it back when the node is
    parked-ready or awake again.
11. **Time source confirmed** (§2; ADR-0039 §9). The 10 Hz u-blox sits on the **Diagnostics
    node**, which closes the pending placement above. Best clock first is confirmed: GNSS
    with PPS, then GNSS without PPS, then a clock in holdover, then a phone seed; the owner's
    priority breaks ties. The node's u-blox with PPS wired ranks first, so the node is
    normally the time source; readings after a wake from parked-deep are `unsynced` until
    GNSS or SNTP is back (ADR-0040 §9).
12. **Names.** Read "Lite" (§2's time-source row) as "Ostler Diagnostics" (ADR-0039).

## Amendments (2026-10-06, parked broker on add-on modules)

The owner amended this ADR on 2026-10-06 so that a car with only add-on modules (no
Diagnostics node, Guardian or Brain) still coordinates. The decision text and the Amendments
above are unchanged; where these entries differ, they win.

13. **Order** (§2). The parked broker's candidates become **node → guardian → eligible add-on
    module**. An add-on module is always the **last** fallback: it never outranks a node or a
    guardian, whatever priority the owner gives it. The brain is still never a candidate.
14. **Eligibility.** A module may claim the parked broker only if all of these hold; every
    consumer ignores a claim from any other module and the Network page flags it (§3):
    - its capability manifest lists `{"role": "pbroker"}` in `roles` (UI spec §5.1; the role
      id stays `pbroker`, so there is no second "eligible roles" field);
    - its `power.class` in its parked states is **`always`** (ADR-0040 §1). A module whose
      parked class is `wakeable`, `check_in` or `none` is never eligible, so deep-sleeping
      sensor nodes never hold the broker;
    - its manifest declares **PSRAM of at least 2 MB** (`"memory": {"psram_kb": 2048}` or
      more, from its board profile). Evidence: the ESP-IDF Mosquitto port needs about 2 kB
      of heap at start and 4 kB per plain client, but each mTLS client costs about 37 kB of
      heap with default buffers (25–30 kB for a handshake alone), so five mTLS clients peak
      at about 150–200 kB, which fits only with mbedTLS allocating in PSRAM
      ([connectivity research §2](../references/research/connectivity_uplink.md)). 2 MB
      leaves the module's own work and the TLS peaks room; the bench may raise the figure,
      never drop the PSRAM requirement;
    - its `pbroker` role entry declares **`max_clients`**, at most **5** mTLS clients (the
      port's tested figure) until the bench proves more. Parked devices beyond the limit use
      §2's "no holder" fallbacks (wake wire or CAN, alarms direct to a paired phone or out
      the device's own uplink); the guardian's and alarm-capable devices' sessions are
      admitted first;
    - it runs the same broker build as the node (ESP-IDF Mosquitto port, one TLS listener,
      client certificates from the local CA or the owner's pairing key, the compiled-in
      parked topic allow-list) and is in the owner's order set at pairing.
15. **Tie-break among modules.** Several eligible modules are ordered by the owner's
    priority set at pairing (§3), then by the **lowest device id** (byte-wise comparison of
    the id string). A higher-ranked module takes the role back from a lower one by §4's
    give-back rule (healthy for 60 s).
16. **Takeover and hand-back** (§4, §5). A module claims the role when no node or guardian is
    paired, or when the current holder is lost by §4's two signals for 30 s (no MQTT silence
    alone, §5). When a **Diagnostics node or Guardian** appears or recovers (status `online`
    and its mDNS record answered) and stays healthy for **60 s**, the module releases: it
    stops accepting new sessions, clears its retained claim, and its clients reconnect to
    the new holder by mDNS name; the new holder claims with a higher `term`. Retained state
    is not migrated: devices republish their manifest and status on reconnect (the
    research's relay-not-store rule). With a node in parked-deep and no guardian, an
    eligible module holds the role until the node is parked-ready or awake again (ADR-0040
    §9).
17. **No new authority.** A module holding the parked broker gains no gate, no approval
    power, no wake arbitration over the brain's power switch or the wake wire (ADR-0040
    §4.2: those stay with the node) and no PLCA or uplink-manager candidacy. It delivers
    check-in messages as the parked-broker holder (ADR-0040 §4.2). When the brain wakes, the
    brain's broker bridges to it as it would to the node.
18. **Confirmation (added).** *Simulated:* in the role harness, a car with only add-on
    modules (A: `always`, `psram_kb` 8192; B: `always`, `psram_kb` 2048; C: `check_in`
    sensor that lists `pbroker`; D: `always` with no PSRAM) elects exactly one parked broker:
    A or B by owner priority, else the lower device id; C's and D's claims are ignored and
    flagged; a sixth mTLS client is refused and falls back; adding a guardian (or a node)
    moves the role to it after 60 s ± one tick with a higher term, the module clears its
    claim, and no alarm event is lost or duplicated; removing it again returns the role to
    the module after 30 s of two signals. *Bench:* an ESP32-S3 module with 2 MB PSRAM runs
    the Mosquitto port with five mTLS clients for 24 h; peak internal heap and PSRAM use are
    recorded, and a parked alarm event from one module reaches a paired phone through it.
