---
title: "ADR-0037 — Role holders and handover (transmit gate, parked broker, time source, PLCA coordinator, uplink manager)"
area: decisions
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [references/research/cluster_view.md, decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md]
summary: >
  Proposed, pending owner answers. Data in an Ostler car is decentralised (every device publishes its own manifest, status and readings), but a few roles must have exactly one holder at a time. The transmit gate (one per car bus) belongs to the node wired to that bus and never hands over: no holder means no transmit. The parked broker (node → guardian), the time source (brain → node → guardian, best clock first), the PLCA coordinator (per T1S segment: node → guardian, never the brain) and the uplink manager (brain → node) move by a static priority the owner sets at pairing, with timeouts, a term number and hysteresis; no voting. Holders announce with a retained claim on their own MQTT topic, an online status with an offline will, and a roles hint in the mDNS TXT record. Split brain is made harmless rather than voted away. Holding a role never grants authority: every approval is checked by the gate that executes it, whichever UI asked. Confirmation by a simulated role harness and bench pulls.
---

# ADR-0037 — Role holders and handover

- **Date:** 2026-10-06
- **Status:** proposed (draft for the owner; nothing here is accepted until the open
  questions are answered). Builds on [ADR-0026](adr-0026-module-bus-10base-t1s.md),
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
| **Time source** | one per vehicle | brain (GNSS + PPS) → node (GNSS) → guardian (GNSS); a phone may seed time on Lite | yes, best clock first | each device free-runs on its RTC; readings carry `time: unsynced`; the logbook marks the gap |
| **PLCA coordinator** | one per T1S segment | node → guardian (only if wired to that segment); **never the brain** | yes, standby only | the segment runs CSMA/CD (degraded, still works); alert |
| **Uplink manager** (proposed) | one per vehicle LAN | brain → node | yes | no shared default route; each device uses its own SIM, if any; local-first is unaffected |

- **Where brain → node → guardian applies:** the time source in full; the uplink manager as
  brain → node only (the guardian's SIM stays its own, for the alarm path). **Where it does
  not:** the transmit gate (no order; wiring decides); the
  parked broker and PLCA coordinator (the brain is not a candidate, because it sleeps).
- **Always-on mode** (ADR-0028 §2) does not move the parked broker: the brain's broker serves
  everything and stays bridged to the node's, which keeps the role.
- **Not roles:** the cluster view and the merge (any full-app host builds one; ADR-0032 §11);
  the phone and the cloud hold no in-car role. The local CA and pairing authority stay where
  ADR-0027 §8 and ADR-0032 §12 put them and **never move automatically** (open question 5).

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
| Time source | the holder's status is `offline`, or its claim reports no GNSS fix and its root distance passes 1 s (chrony orphan-style) | 60 s | when a higher-priority source with a fix has been stable for 120 s |
| PLCA coordinator | PLCA status FAIL (about 1 s after the BEACON stops) on the standby's PHY | 5 s of FAIL, then the standby reconfigures as ID 0 | the standby returns to its own ID as soon as its PHY reports an unexpected BEACON, or the node's status is `online` for 10 s |
| Uplink manager | the brain's status is `offline` (it slept) | at once (the node's own uplink was already its fallback) | when the brain is awake and its uplink profile is up |

Timeouts are proposals for the bench to tune; the bench values become the module-bus
message spec's numbers.

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
why. A view whose inputs are stale is read-only and shows its age (the Proxmox lesson).
Detail: the proposed amendments to the
[UI spec](../specs/2026-10-06-ui-architecture-design.md) and the
[app-model spec](../specs/2026-10-06-app-model-design.md).

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
- unplug the GNSS antenna on the brain: the node becomes the time source within 60 s and
  module clocks stay within ADR-0027's 10 ms; sleep the brain: the same;
- on T1S hardware only (ADR-0026 bench plan): remove the coordinator, the segment keeps
  passing MQTT in CSMA/CD; with a standby, PLCA returns within 5 s + 1 s; restoring the node
  causes no lasting duplicate BEACON;
- remove the node wired to K-line: every transmit request is refused with "No gate for this
  bus", and no other device offers to transmit.

## Consequences

- The module-bus message spec gains the `status` and `role/#` topics, the claim payload, the
  TXT keys and the timeouts; `asyncapi.yaml` gains the channels at U5.
- The capability manifest (UI spec §5.1, ADR-0032 §6) gains `roles` (roles a device can
  hold, with scope) and `transmit` per `bus_id`.
- The guardian, when alongside a node, gains standby duties (broker, PLCA if wired, time),
  which cost parked current; its power budget must allow it (open question 3).
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
  alongside on the same segment (an amendment if accepted).
- **ADR-0027:** §3 and §7 put NTP on the Pi; this ADR makes the time source a role with the
  node and guardian as fallbacks (an amendment if accepted). §4's PLCA ID assignment at
  pairing stands; the ID table is part of each device's install configuration so a standby
  can coordinate.
- **ADR-0028:** answers §1's open point (hand-over when a guardian is fitted) and formalises
  §5's fallback "the guardian hosts the parked broker".
- **ADR-0032:** §2 (gate and parked broker on the node) and §4 ("with the brain off, the node
  is the hub again") stand unchanged.
- **ADR-0033:** unchanged. §3's "the brain's gate does so for add-on actions" is read as "the
  executing gate"; see open question 4.

## Open questions for the owner

1. **Handover order.** Keep brain → node → guardian for the time source, and node →
   guardian (no brain) for the parked broker and PLCA? Or prefer the always-powered devices
   first everywhere?
2. **Uplink manager.** Is it a single-holder role (brain → node, the guardian keeping its SIM
   to itself), or does every device just manage its own uplink?
3. **Guardian standby.** May a guardian alongside a node act as standby broker, PLCA
   coordinator and time source, at the cost of parked current?
4. **Add-on actions with the brain off.** ADR-0033 §3 has the brain's gate check add-on
   actions. When the brain sleeps, are add-on actions refused, checked by the add-on's own
   gate, or checked by the node?
5. **CA and pairing authority.** Confirm that the local CA (brain) and pairing (node on Lite)
   never move automatically, and that losing the brain only blocks new pairings.
6. **Timeouts.** Accept the proposed 30/60/5 s values as bench starting points?
