---
title: "ADR-0033 — Action categories, roles, phone approval, safe fault clearing and alarm paths"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0020-can-links-listen-only-by-default.md, decisions/adr-0024-body-bus-links-passive-by-default.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, decisions/adr-0032-one-node-optional-brain.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, CONSTITUTION.md]
summary: >
  Owner direction of 2026-10-06. Action categories (Read, Comfort, Security, Accessories, Maintenance, Actuator tests, Procedures, Coding) become a second axis beside the safety tiers: tiers keep setting friction and lockouts, each category has a tier cap and a while-moving rule, and roles grant categories. Default roles Owner, Driver, Viewer and Mechanic (time-boxed); the head-unit kiosk session gets Read and Comfort only. Every add-on and node variant declares category and tier per control in its manifest. ADR-0018's "comfort" render class is renamed "add-on device". Fault clearing is Maintenance: snapshot first, Parked or Idling, one confirmation, an extra warning for safety systems, audited, NRC 0x22 shown honestly; drivers may clear. A paired phone may approve Tier 2–3 over local links only, re-checked on the node gate, with Stop on the phone; an AI-client accept never counts. Remote paths stay read-only unless the install-level OSTLER_ALLOW_REMOTE_CONTROL override is set (off by default, never settable remotely). Alarm paths never depend on the brain or the internet; "notify-only" is dropped, and alarm outputs come later through an I/O or relay module, never the guardian.
---

# ADR-0033 — Action categories, roles, phone approval, safe fault clearing and alarm paths

- **Date:** 2026-10-06
- **Status:** accepted (owner direction, 2026-10-06, with the owner's answers on phone
  approval, the remote override and alarm outputs). It answers the role questions left open
  by [ADR-0029](adr-0029-accounts-multi-vehicle-sharing-and-social.md) and the phone question
  of [ADR-0030](adr-0030-ai-native-mcp-server-and-authoring-skill.md), and supersedes parts of
  ADR-0024, ADR-0020, ADR-0027, ADR-0028 and ADR-0018 (see
  [Supersedes in part](#supersedes-in-part)). Companion to
  [ADR-0032](adr-0032-one-node-optional-brain.md), which puts the transmit gate on the node.

## Context

- The safety tiers (UI spec §7, ADR-0018) say **how dangerous** an action is: Tier 0 read,
  1 clear, 2 actuate, 3 procedure, 4 code. They do not say **what kind of thing** it is. A
  family driver should be able to turn on the aux heater and clear a check-engine light but
  not run an injector test, and Tier 1 alone cannot express that.
- ADR-0029 (draft) made roles plain tier ceilings, with the driver role as "Tier 1 plus
  comfort and alarm arming", and left open whether a driver could run Tier 2. ADR-0030
  (draft) left open whether the owner's phone may approve Tier 2–3.
- The "remote paths get Tier 0" rule is written in several places (ADR-0020, ADR-0027
  Confirmation, ADR-0028 §6, ADR-0029, UI spec §7, GOALS). Developers need remote control on
  their own cars while the threat model matures, without opening it for everyone.
- ADR-0018 Q4 named a UI render class `comfort` (our own add-on devices that never write to
  a vehicle ECU). A "Comfort" action category about car functions would clash with it.
- Clearing fault codes is the most common write people make. Today it is Parked-only with
  "offer a report first"; freeze frames are lost when the report is skipped. Many ECUs refuse
  a clear while the engine runs (negative response `0x22`, conditions not correct).
- ADR-0024 kept the alarm "notify-only". The owner now wants real alarm outputs (siren, the
  car's native alarm, immobiliser) later, and ADR-0032 keeps the guardian output-free.

## Decision drivers

- The tier keeps setting safety friction; nothing in this ADR loosens a confirmation,
  precondition, lockout or the Constitution's safety rules.
- Permissions people understand: "can use the heater", "can clear codes", not tier numbers.
- One gate on the node (ADR-0032) checks every path the same way.
- Local-first: the car, the phone and the alarm work with no brain and no internet.
- Remote control only where the installer chose it, never switched on from afar.

## Decision

### 1. Categories beside tiers

Every action has a **category** and a **tier**. The tier sets the friction (confirmation,
checklist, wizard, banner with Stop, timeouts). The category sets who may run it and its
driving-state rule.

| Category | Examples | Tier | While moving |
|---|---|---|---|
| **Read** | live data, faults, logs, location | 0 | allowed |
| **Comfort** | AC and heater, seat heaters, lights, windows, aux heater | 1 | allowed, with driver-safe UI |
| **Security** | arm and disarm, locks, find my car | 1 | arming allowed; disarming Parked only |
| **Accessories** | relay outputs, spotlights, winch, camera recording | 1–2, set per add-on | set per add-on |
| **Maintenance** | clear codes, reset service interval | 1 | Parked or Idling only |
| **Actuator tests** | injector, wastegate, SLABS pump | 2 | Parked only |
| **Procedures** | bleeding, calibrations, adaptation resets | 3 | Parked only |
| **Coding** | ECU writes | 4 | disabled until each has its own ADR |

- **The category's tier is a cap.** An action may not declare a tier below its category's
  (an Accessories control declares 1 or 2). Tier 4 stays unrunnable (ADR-0018 Q11).
- **Driving state.** The category's while-moving rule replaces UI spec §3.5's per-tier lock
  only where the table allows more: Comfort and Security arming while Moving, and Maintenance
  while Idling. Everything else keeps §3.5. "Driver-safe UI" means no text entry, no typed
  confirm and Moving lockouts on lists and depth.
- **Bus rules still apply.** A category never loosens ADR-0020 or ADR-0024: an action that
  transmits on a vehicle bus still needs the pack allowlist, Parked and the gate, and window
  and sunroof jobs keep the occupant-present confirm. A Comfort or Security action that
  transmits on a vehicle bus is Parked-only until its own ADR allows more. In practice,
  "allowed while moving" today means our own add-on devices and the software alarm.
- **Manifests declare it.** Every pack action, add-on device control and node variant
  control declares `category` and `tier` in its capability manifest (UI spec §5,
  ADR-0027 module contract, ADR-0032 §6). The platform checks the pair against the table and
  refuses a manifest that breaks it. Pack actions keep their derived tier (UI spec §7); the
  pack adds the category.

### 2. Roles grant categories

| Role | Categories | Notes |
|---|---|---|
| **Owner** | all, up to Tier 3 | users, shares, tokens, service mode; at least one |
| **Driver** | Read, Comfort, Security, Maintenance; Accessories if granted | no Actuator tests or Procedures |
| **Viewer** | Read | location only if shared |
| **Mechanic** | Read, Maintenance, Actuator tests, Procedures | always time-boxed (ADR-0029) |

The owner can grant or remove categories per user (never Coding). Shares and tokens carry
categories too and only narrow.

**Kiosk session.** The head unit's session with no sign-in (accounts spec §2.3) gets **Read
and Comfort only**. Clearing codes, Security and anything above needs a signed-in user.

### 3. The one rule

```
allowed(action) =
      action.category in (role ∩ share ∩ token).categories
  and action.tier <= min(category_cap, role, share, token max tier)
  and transport allows it (§6)
  and the category's driving-state rule and the tier's lockouts allow it
  and every confirm, precondition, interlock and the 12 V floor passes
```

The node's transmit gate (ADR-0032) evaluates the car-touching part again at execution; the
brain's gate does so for add-on actions. The UI only hides and adds friction.

### 4. Name clash: render class renamed

ADR-0018 Q4's UI render class **`comfort` is renamed "add-on device"** (`addon_device` in
the manifest). Its rules are unchanged: only our own add-on devices that never write to a
vehicle ECU or bus, still through the gate. "Comfort" now means only the action category.

### 5. Clearing fault codes, made safe

Clearing is **Maintenance, Tier 1**. Drivers may clear.
- **Snapshot first, automatically.** Before the clear request, the server reads and writes
  to the logbook the codes, freeze frames (where the protocol has them) and readiness
  monitors of the target system, tagged with the user. No option to skip it.
- **Parked or Idling only.** **One confirmation** naming the system and the consequence.
- **Safety systems get an extra warning** (ABS, brakes, stability, steering): the warning
  says the fault may still be present and the system may be degraded. Airbag/SRS stays
  read-only by construction (Constitution): no clear is offered for it.
- **Audited:** who, which device and transport, which system, codes before and after.
- **Honest refusals.** While Idling many ECUs answer `7F 14 22` (conditions not correct). The
  UI says the ECU refused with the engine running and to switch the engine off with ignition
  on and try again. The snapshot is kept; there is no automatic retry loop. The re-read
  shows what really cleared.

### 6. Local links, phone approval and the install override

- **Local links:** the head unit, the in-car LAN, the node's Wi-Fi AP and BLE to the node.
  **Remote paths:** Tailscale, the Ostler Cloud relay, Home Assistant and MQTT from outside,
  and device-to-device shares. **Remote paths are read-only** (Read, plus arming, never
  disarming, the software alarm).
- **A phone may approve Tier 2–3** when all hold: it is a **paired device** (ADR-0029,
  ADR-0032 pairing) of a signed-in user whose role grants the category; it is on a **local
  link**; the node gate **re-checks Parked and the preconditions** at execution; the phone
  shows **Stop** for the whole action, and losing the phone link stops it as leaving the
  screen does.
- **An "accept" inside an AI client never counts** (ADR-0030): MCP elicitation, an agent's
  own confirm or a scripted tap through an AI client is never an approval.
- **Install-level override.** `OSTLER_ALLOW_REMOTE_CONTROL`, default off, lets remote paths
  run the same actions as local ones, for developers while the threat model matures.
  - It is read only from the environment or the install configuration on the device, at
    start. No API, UI setting, MQTT message, cloud command or share can set or change it.
  - The node gate honours a remote-origin grant only if the node's own install
    configuration has the override on too.
  - Everything else still applies: role, categories, tiers, driving state, Parked re-check
    on the node, confirmations. Tier 4 stays unrunnable. Home Assistant and MQTT never reach
    Tier 2+, and ADR-0024's body-bus rules (no remote transmit, no remote automation trigger)
    are not changed by the override.
  - While on, every UI shows a persistent "Remote control enabled" badge, and each start is
    logged in the audit log.

### 7. Alarm paths

- **Alarm paths never depend on the brain or the internet.** Node or guardian →
  notification works with the brain off and no Ostler Cloud: to a paired phone over a local
  link, and over the device's own uplink when it has one (for example SMS from its 4G
  modem, or the owner's own notify endpoint).
- **"Notify-only" is dropped.** Alarm outputs (a siren, triggering the car's native alarm,
  an immobiliser) are allowed, but only through a **future I/O or relay module** with its own
  design, and **each car-switching function needs its own ADR**. Outputs are **never on the
  guardian** (ADR-0032). An output design must show it cannot act on a moving vehicle (an
  immobiliser only blocks a start).

## Supersedes in part

- **ADR-0024, Alarm:** "the alarm stays notify-only" is replaced by §7. Body-bus alarm
  triggers stay read-only.
- **ADR-0020, "No remote path transmits on a vehicle bus":** replaced by §6 (local only,
  plus the install override). "Never bridge MQTT to vehicle CAN" stands.
- **ADR-0027 Confirmation, "a Tier ≥ 2 action is not reachable from MQTT, HA or any remote
  path":** replaced by §6. MQTT and Home Assistant stay below Tier 2; other remote paths are
  read-only unless the override is on.
- **ADR-0028 §6, "remote paths get read-only actions plus arming the software alarm … Tier ≥ 2
  stays unreachable remotely" and "no tier carries a write to the car":** replaced by §6.
- **ADR-0018 Q4, the name `comfort`:** renamed "add-on device" (§4); the rule stands.
- ADR-0029 and ADR-0030 were drafts and are amended in place to match.

## Confirmation

- **Gate matrix test** on the fake pack: role × category × tier × driving state (Parked,
  Idling, Moving, unknown speed) × transport (local; remote with the override off; remote
  with it on). Each cell matches §1–§3 and §6; Tier 4 refused everywhere; the kiosk session
  refused outside Read and Comfort.
- **Manifest test:** a control with a missing category, or a tier below its category's cap,
  is refused.
- **Phone approval:** a Tier 2 approval from a paired phone on a local link runs, re-checked
  at the node; the same approval over a remote path is refused with the override off and
  runs with it on; losing the phone link stops the test; an unpaired phone, or a user whose
  role lacks the category, is refused.
- **AI accept never honoured:** an MCP elicitation "accept" or an AI-client confirm executes
  nothing, with or without the override.
- **Override not remote-settable:** no route, message or share changes it; the node refuses
  a remote grant when only the brain has it on.
- **Alarm path:** with the brain powered off and no internet, a node or guardian trigger
  reaches a paired phone (bench test, ADR-0032 Confirmation).
- **Clear codes:** the snapshot (codes, freeze frames, readiness) is in the logbook before
  the clear request is sent; a fake ECU answering `7F 14 22` shows the honest refusal and
  keeps the snapshot; SRS offers no clear; the audit entry names the user.

## Consequences

- UI spec §3.5 and §7 gain the category column, Maintenance while Idling and the local-only
  remote rule; §6 renames the render class. The manifest schema gains `category` and
  `addon_device`.
- The accounts spec replaces role tier ceilings with categories; the MCP spec lets a paired
  phone approve Tier 2–3 locally.
- The threat model (U5) must cover phone pairing, the override and remote grants on the node.
- Add-on and relay-board work (ADR-0032 §15) declares categories from the start.

## Alternatives considered

- **Tiers only, with more roles.** Rejected: a tier cannot say "heater yes, injector test
  no".
- **Categories replace tiers.** Rejected: tiers carry the safety friction that already exists.
- **Phone approval over any path.** Rejected for now: remote control needs a mature threat
  model; the install override covers developers.
- **A UI toggle for remote control.** Rejected: anything settable remotely can be turned on
  by whoever takes over an account.
- **Keep the alarm notify-only.** Rejected by the owner; outputs come through a separate,
  separately decided module.
