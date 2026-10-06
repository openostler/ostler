---
title: "Cluster view and role holders — Proxmox, Home Assistant, election patterns for a small in-car cluster"
area: references
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [decisions/adr-0026-module-bus-10base-t1s.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, references/research/connectivity_uplink.md, references/research/t1s_module_bus.md]
summary: >
  Short research note (live checks, 2026-10-06) behind ADR-0037 and the Network page amendments. How Proxmox VE shows a cluster (node list with votes, quorum, read-only when quorum is lost, one HA manager master chosen by a cluster-filesystem lock, watchdog fencing, about two minutes to fail over) and how Home Assistant shows devices (manufacturer, model, firmware, connections, via-device hub, a link to the device's own configuration page). Role-election patterns for a cluster of two or three always-on devices: voting quorum does not work with two members, so static priority set at pairing wins, with MQTT 5 retained claims plus the will message for liveness, mDNS TXT hints and goodbye packets, chrony orphan-style tie-breaks for time, and the T1S PHY's own duplicate-BEACON detection for the PLCA coordinator. Recommendation: static priority with hysteresis, non-voting, fail closed for the transmit gate, and authority always checked by the executing gate.
---

# Cluster view and role holders

Research for the owner's item "every node shows its peers; the full app shows the whole
cluster; some roles have exactly one holder". It feeds
[ADR-0037](../../decisions/adr-0037-role-holders-and-handover.md) (proposed) and the
proposed amendments to the [UI spec](../../specs/2026-10-06-ui-architecture-design.md) and
the [app-model spec](../../specs/2026-10-06-app-model-design.md). Sources were checked live
on 2026-10-06 and are paraphrased.

## 1. Proxmox VE: how a cluster is shown

- **Node list and quorum.** Each node has one vote by default; a change to the shared
  configuration needs a majority. The GUI lists members with ID, votes and name, marks the
  local node, and shows quorum under Datacenter → Cluster
  ([Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager), checked 2026-10-06).
- **Two nodes have no majority**, so Proxmox adds an external vote (QDevice) for small
  clusters (same page).
- **Losing quorum makes the shared configuration read-only** until quorum returns (same
  page). The lesson for us: when the cluster view cannot be confirmed, it becomes read-only
  and shows its age; it does not guess.
- **HA roles.** One cluster-wide manager is master at a time; the master is whichever node
  takes a lock in the cluster filesystem. Each node runs a local manager whose watchdog
  reboots ("fences") the node if it loses contact; detection plus failover is about two
  minutes, the watchdog about 60 s
  ([High Availability](https://pve.proxmox.com/wiki/High_Availability), checked 2026-10-06).
  Service placement follows node priorities, and a service moves back when a
  higher-priority node returns.

**Take:** a node list with health, the local node marked, a visible "who is master", and
read-only on doubt. **Do not take:** voting quorum (our cluster has two or three always-on
members, often two) and self-fencing by reboot (a node that reboots drops the alarm path).

## 2. Home Assistant: device and integration pages

- A device record carries identifiers, connections (for example MAC), manufacturer, model,
  hardware and firmware versions, a **via-device** link to the hub it is reached through,
  and a **configuration URL** that links to the device's own page
  ([device registry](https://developers.home-assistant.io/docs/device_registry_index/),
  checked 2026-10-06).
- Entities on a device are grouped, with diagnostic and configuration categories collapsed
  by default (already borrowed in UI spec §5.1).

**Take:** per device: variant, model, firmware, addresses, "reached via" (the T1S segment,
the brain, BLE through the phone), and an "Open device page" link to its own local page.
Integrations map to our uplinks and remote tiers, not to devices.

## 3. Role-election patterns for a small embedded cluster

| Pattern | Fits us? | Why |
|---|---|---|
| **Voting quorum** (Raft, corosync) | No | needs three voters; two always-on devices is common (node + guardian); the brain sleeps |
| **Lock in shared storage** (Proxmox CRM) | No | no shared filesystem, and the broker that would hold the lock is itself a role |
| **Bully / highest-ID election** | Partly | deterministic, but flaps on lossy links without hysteresis |
| **Static priority set at pairing, with hysteresis** | **Yes** | the owner's order is the policy; each device knows its rank offline; takeover only after a timeout, give-back only after a hold time |
| **Physical-layer arbitration** (T1S PLCA) | Yes, for PLCA | the PHY flags an unexpected BEACON and stops beaconing for two cycles; the node count and IDs are set by configuration |

Liveness and announcement building blocks:
- **MQTT 5 retained messages and the will message.** A new subscriber gets the last retained
  message on a topic; an empty retained payload clears it. The broker publishes a client's
  will after an abnormal disconnect, optionally after a will delay, and drops a client
  silent for 1.5× its keep-alive
  ([MQTT 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html), checked
  2026-10-06). So "online" retained status plus an "offline" will gives liveness on the
  broker; a role claim is a retained message on the claimant's own topic, which keeps
  ADR-0026's per-device ACLs (a device publishes only its own topics).
- **mDNS / DNS-SD TXT records** (RFC 6763 §6) carry small key=value hints; the RFC advises
  keeping a TXT record small (a couple of hundred bytes) so it fits one packet. A clean
  shutdown sends a goodbye (TTL 0). mDNS is a second, broker-independent liveness signal.
- **Time: chrony orphan mode.** Several servers configured alike agree that the one with
  the smallest reference ID serves local time, and the next takes over when the first's
  root distance passes a threshold
  ([chrony.conf](https://chrony-project.org/doc/4.6/chrony.conf.html), checked 2026-10-06).
  That is static priority with a built-in tie-break; a GNSS-disciplined source always
  outranks a free-running one.
- **T1S PLCA.** Node ID 0 is the coordinator and sends the BEACON that starts each cycle; if
  nodes are not all PLCA-enabled the segment behaves as CSMA/CD; PLCA status goes to FAIL
  about a second after PLCA stops being active; a coordinator that hears another BEACON
  stops transmitting for two cycles (IEEE 802.3cg material and the LAN865x data sheet,
  found 2026-10-06:
  [IEEE 802.3cg PLCA mixing](https://www.ieee802.org/3/cg/public/adhoc/beruto_3cg_mixing_PLCA_with_non_PLCA_enabled_nodes.pdf),
  [Intrepid on PLCA](https://intrepidcs.com/multi-drop-physical-layer-collision-avoidance-plca/),
  [netdev PLCA netlink patches](https://lkml.iu.edu/hypermail/linux/kernel/2212.1/00596.html)).
  So a missing coordinator degrades the segment to CSMA/CD rather than killing it, and a
  duplicate coordinator is detected in hardware.

## 4. Split brain

- With two candidates and no quorum, split brain cannot be prevented by voting; it is made
  **harmless**. The rules that do that: a **term number** in every claim (higher term wins,
  then higher priority); **two independent signals** (MQTT will and mDNS, or PLCA beacon
  loss) before taking over; a **hold time** before giving back; and roles whose duplication
  is unsafe (the transmit gate) **never move**.
- Authority does not come from holding a role. A broker or hub relays; it never authorises.
  Every approval is verified by the gate that executes it (ADR-0032 §2, ADR-0033 §3), so two
  brokers, two time sources or two cluster views can never cause an unapproved write.

## 5. Recommendation

1. **Static priority, owner-set at pairing, with hysteresis; no voting.** Default order
   brain → node → guardian where a role can move, and stated per role where it cannot.
2. **The transmit gate never hands over**; no holder means no transmit on that bus (fail
   closed).
3. **Announce three ways:** retained claim on the holder's own MQTT topic, status with an
   "offline" will, and a `roles=` hint in the `_ostler-mod._tcp` TXT record.
4. **Show it like Proxmox and Home Assistant:** one Network page with devices (variant,
   firmware, addresses, reached via, link to own page), transports and link health, role
   holders with "since" and candidates, uplinks and metering, certificates and pairing; and
   a small read-only peer list on every device's own page. A stale or unconfirmed view is
   read-only and shows its age.
