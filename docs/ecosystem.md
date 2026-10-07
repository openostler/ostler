---
title: "The Ostler ecosystem — core, add-ons, how add-ons get car data, and the safety boundaries"
area: docs
status: stable
version: 1.0
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, references/research/addons_catalogue.md]
summary: >
  Map of the Ostler ecosystem, approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted), whose main goal is getting the car's data into apps. A table of core (shell, Diagnose, Trips, Network, Security) and add-ons (Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations one per integration, Decode lab as a developer add-on) enabled at More → Add-ons, with repo, where each appears, what car data it reads and what it adds. How add-ons get car data: the VSS signal stream, events, faults, trips (summary index and recordings, odometer and engine hours) and the data-class registry with audiences and ghost by default, all through the shell SDK, plus opt-in MQTT/Home Assistant outside the shell. The safety boundaries: the node gate, ADR-0033 remote paths (mesh included) read and alerts only, shell templates only on a driver-facing display while Moving, and ghost by default.
---

# The Ostler ecosystem

**Approved by the owner on 2026-10-07 ("approve all").** Ostler is an ecosystem whose main goal is **getting the car's data
into apps**: a small core reads and interprets the car and hands its data to **add-ons**, which
are the product people choose, in the way Home Assistant's core serves its add-ons. Decision:
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) (accepted);
mechanics: [app-model spec](../specs/2026-10-06-app-model-design.md) §14 (approved); add-on
specs: [Social](../specs/2026-10-07-social-addon-design.md),
[Vehicles & Map](../specs/2026-10-07-vehicles-and-map-addon-design.md),
[Maintenance & Garage](../specs/2026-10-07-maintenance-garage-addon-design.md); hardware
add-on ideas: [add-ons catalogue](../references/research/addons_catalogue.md).

## 1. Core and add-ons

Every row is an app in the one shell. Core is always present; add-ons are off by default and
enabled in **More → Add-ons** (Installed / Available, each card labelled Core, Add-on or
Developer; no remote catalogue yet). Hardware add-ons share the same catalogue. No add-on adds a destination (five, UI spec §3.4).

| App | Kind | Repo | Appears in | Reads | Adds |
|---|---|---|---|---|---|
| **Shell** | core | `ostler` | strip, rail, Home, Drive mode, sign-in, invites, More → Add-ons | everything it serves | the VSS stream, gate client, registry, templates |
| **Diagnose** | core | `ostler` | Diagnose | systems, live signals, faults | scans, fault snapshots, gated tests |
| **Trips** (was Logs) | core | `ostler` | Trips (Statistics and Records inside) | recordings, GPS, signals | trip summary index, replay, Export all, odometer/engine-hours history |
| **Network** | core | `ostler` | More → Network | cluster, devices, links | pairing, uplinks, device pages |
| **Security** | core, once a node exists | `ostler` | Security | alarm, tracker, geofences | arming, alarm events |
| **Social** | add-on | `ostler-app-social` | More → Social (`more:social`), Home card, ride/call strip chip, alerts | own location, trips (as shared) | messages, push-to-talk, calls, later cameras |
| **Vehicles & Map** | add-on | `ostler-app-vehicles` | More → Vehicles (`more:vehicles`), Home card (`home:card`) | own and shared vehicle location | the map of your and others' vehicles, by audience |
| **Maintenance & Garage** | add-on | `ostler-app-maintenance` | More → Garage, Home card, strip chip when very urgent, trip-start/end alert card | odometer, engine hours, faults, trips | services, reminders, fuel, costs, CSV import/export |
| **Cameras** | add-on | `ostler-app-cameras` | Security → Clips, live chip, `camera_live` | speed, events | clips, live view |
| **Integrations** | add-on, one per integration | own repos (e.g. `ostler-app-lubelogger`) | More → Integrations | signals, trips, maintenance | RealDash CAN out (read-only), LubeLogger bridge, social integrations |
| **Decode lab** | developer add-on | `ostler` | More → Developer, service mode only | raw frames, signals | decode evidence for packs |

Hardware add-ons (sensor nodes, cameras, displays, mesh radios) join through the module
contract and usually arrive with a declarative app the catalogue offers when the device
appears ([catalogue](../references/research/addons_catalogue.md); app-model §7).

## 2. How add-ons get car data

An add-on never talks to the car, the node or the broker directly. It declares what it needs in
its manifest (`requires.signals`, `requires.api`, `permissions.data`) and receives it through
the shell SDK (`@ostler/app-sdk`), whose types are generated from OpenAPI and AsyncAPI.

| Channel | What it carries | SDK | Notes |
|---|---|---|---|
| **VSS stream** | live values `{value, ts, confidence, stale}` on VSS paths (ADR-0016) | `signals.subscribe(paths)` | only declared paths; stale looks stale; `candidate` stays `candidate` |
| **Events** | driving-state changes, trip start/end, Mark, alarm events, device appearing | `driving`, `trips`, `power` | AsyncAPI events; read-only |
| **Faults** | per-system fault list and new-fault events, with snapshots | `faults` | read-only; clearing stays a Diagnose action through the gate |
| **Trips** | trip summary index (route, distance, durations, stops, max/avg, time at speed, faults) and the recording behind it; odometer and engine-hours history, estimated when the car does not report it | `trips` (was `logs`) | Export all is core's, not the add-on's |
| **Data-class registry** | which data classes exist (location, precise location, trips, video, audio, plus add-on classes such as maintenance costs) and each one's audience: me / person / group / household / public later | `sharing` | defined in core accounts and sharing; add-ons register classes and read audiences, never set another user's |
| **Actions** | requests for gated actions listed in the manifest | `actions.request` | the shell runs confirms and approvals; the gate decides |

Outside the shell, the same data reaches other apps through opt-in integrations: MQTT with
Home Assistant discovery, OVMS topics, OwnTracks and Traccar (GOALS §4), and the MCP server
(ADR-0030). They follow the same registry and are off by default.

## 3. Safety boundaries

1. **The gate.** The node's transmit gate is the only path to the car (ADR-0032). Add-ons
   list existing actions with their category and tier; they never define one, draw an
   approval or call an action route except through `actions.request` (app-model §8, ADR-0033).
2. **Remote paths are read and alerts only** (ADR-0033 §6): Ostler Cloud, remote access and
   every mesh (Wi-Fi mesh, HaLow, LoRa; ADR-0038) unless the install-level
   `OSTLER_ALLOW_REMOTE_CONTROL` override is set. Social and Vehicles & Map inherit this.
3. **Driving templates.** On a driver-facing display while Moving the shell draws only
   templates (`tiles`, `map`, `media`, `alert_card`, `short_list`, `call`, and the existing
   five), task depth ≤ 3, no message content, no video other than driving cameras. Passenger
   view covers driving-related content only; everything else offers **Open on phone**. The
   authority is UI spec §3.5 as amended by §12.1 (approved); limits are in
   [driver_distraction_rules §7.2](../references/research/driver_distraction_rules.md#72-template-limits-recommended).
4. **Ghost by default.** Every new user and every add-on starts with every data class shared
   with no one. One master toggle returns to ghost; precise location is always time-limited
   (≤ 24 h); no one can raise another's precision. The only exception is a user's own SOS or
   crash alert to their safety contacts.
5. **Exit guarantee.** Export all lives in core; nothing in core depends on an Ostler-run
   server; an add-on that keeps data exports it in an open format.

## Changelog

- 2026-10-07: v0.1, proposed map (ecosystem drafts).
- 2026-10-07: v1.0, approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted):
  the catalogue at More → Add-ons, Integrations one add-on per integration, the add-on specs
  linked, the new slots named.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **Is this the map to publish?** Recommend: accept with ADR-0042 and link it from GOALS and
   the README. Alternative: keep the map only inside the app-model spec.
2. **Hardware add-ons in the same catalogue as app add-ons?** Recommend: yes, one More →
   Add-ons page, with device-suggested declarative apps under Available. Alternative: devices
   stay in Network only.
3. **Integrations: one add-on or one per integration?** Recommend: one per integration
   (separate enable, separate data classes). Alternative: one Integrations add-on with toggles.
