---
title: "The Ostler ecosystem — core, add-ons, how add-ons get car data, and the safety boundaries"
area: docs
status: stable
version: 1.5
updated: 2026-10-07
depends_on: [docs/feature_map_dmd.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-trip-sharing-design.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, references/research/addons_catalogue.md]
summary: >
  Map of the Ostler ecosystem, approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted), whose main goal is getting the car's data into apps. A table of core (shell, Diagnose, Trips, Network, Security) and add-ons (Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations one per integration, Decode lab as a developer add-on) enabled at More → Add-ons, with repo, where each appears, what car data it reads and what it adds. How add-ons get car data: the VSS signal stream, events, faults, trips (summary index and recordings, odometer and engine hours) and the data-class registry with audiences and ghost by default, all through the shell SDK, plus opt-in MQTT/Home Assistant outside the shell. The safety boundaries: the node gate, ADR-0033 remote paths (mesh included) read and alerts only, shell templates only on a driver-facing display while Moving, and ghost by default. The amendment of 2026-10-07 (DMD round), approved by the owner on 2026-10-07 ("approve all", DMD round), adds rows for Ostler Community (the open `ostler-app-hub` add-on and the closed, Ostler-run `ostler-hub` service: publishing, forum, vehicle development, wiki), Navigation, Phone & Comms and, later, Alerts; core ShellInput, per-trip sharing, third-party adapters (the Brain only for a vehicle with no node, ADR-0044) and later Crash SOS; and points to the Home Assistant direction in ADR-0042. Amended 2026-10-07 (OS round): the core/add-on table is superseded by ADR-0046 (the empty OS; every feature an app).
---

# The Ostler ecosystem

> **Amended 2026-10-07 (OS round), approved by the owner on 2026-10-07 ("approve all", OS
> round):** the core and add-on split below is superseded by
> [ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md): the platform is an empty
> OS (system services and system UI); Diagnose, Trips, Security and every add-on are apps in
> their own repos, found in the drawer and the Store. This map is re-drawn when next revised.

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
| **Ostler Community** *(DMD round)* | add-on + closed service | `ostler-app-hub` (open, AGPL), `ostler-hub` (private, closed, run only by Ostler; not self-hostable) | More → Community (`more:hub`), hub audiences in the Trips share sheet, Diagnose → Get help, Decode lab → Ask for help, Home card (never while Moving) | trips and faults only as granted or handed over | publish L0–L2, help threads with L3/L4 hand-overs, the project forum, vehicle development (decode cards, pack PRs through a GitHub bridge), the wiki (vehicle pages from pack releases), clubs, events, Discover, Following |
| **Navigation** *(DMD round)* | add-on | `ostler-app-navigation` | Drive `map` template's next manoeuvre, Drive-menu rows, More → Navigation (`more:navigation`), Home card | own position, speed, installed map regions | routing on the Brain, turn-by-turn, voice, GPX library and follow, planner, roadbook |
| **Alerts** *(DMD round, later; named only)* | add-on | `ostler-app-alerts` | `alert_card`, Drive tile | own coarse position, route | UK official weather, flood and closure alerts, free, opt-in |
| **Phone** (Phone & Comms) *(DMD round)* | add-on; needs a Brain for calls | `ostler-app-phone` (created at PH0) | More → Phone (`more:phone`), the `call` template via the shell's call session, the message `alert_card`, the favourites `short_list` widget and Drive-menu rows while Moving; keypad and lists Parked only | the user's own paired phone over the Brain's Bluetooth (HFP, PBAP, MAP) and the companion bridge; phone contacts and call history audience `me` only, in memory | phone mirroring (notifications), dialer, contacts (Ostler and phone, badged), recents, messages ([spec](../specs/2026-10-07-phone-comms-addon-design.md), approved) |

Rows marked *DMD round* were approved by the owner on 2026-10-07 ("approve all", DMD round);
see [Amendment (2026-10-07, DMD round), approved](#amendment-2026-10-07-dmd-round-approved).

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

## Amendment (2026-10-07, DMD round), approved

**Status: approved by the owner on 2026-10-07 ("approve all", DMD round)**, with the matching
amendments to
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md#amendment-2026-10-07-dmd-round-approved)
and [ADR-0034](../decisions/adr-0034-repo-boundaries.md#amendment-2026-10-07-dmd-round-approved).
Every DMD2 and DMD Hub feature, with its home, phase and spec status, is in
[feature_map_dmd.md](feature_map_dmd.md) (approved as the DMD checklist).

- **Four add-on rows** in §1, marked *DMD round*: Ostler Community
  ([spec](../specs/2026-10-07-community-hub-design.md), approved), Navigation
  ([spec](../specs/2026-10-07-navigation-addon-design.md), approved), Phone (Phone & Comms:
  mirroring, dialer, contacts, recents, messages; needs a Brain for calls;
  [spec](../specs/2026-10-07-phone-comms-addon-design.md), approved) and Alerts (later, named
  only, no spec yet). The community hub is a closed service run by Ostler (one instance, not
  self-hostable, its own private repo separate from `ostler-cloud`), reached through the open
  `ostler-app-hub`; it is also the forum, the vehicle-development workspace and the wiki. It sits
  outside core: nothing in core needs it, and everything on it can be exported (ADR-0042
  decision 7).
- **Core gains, no new destination:** `ShellInput` in the shell (D-pad input, focus zones, the
  Drive menu as a `short_list` of ≤ 6 driver-safe actions while Moving, ships with U2;
  [spec](../specs/2026-10-07-shell-input-design.md), approved); per-trip sharing (scrubber,
  `ostler.share/1`, `ostler share verify` in the platform, the share sheet in Trips, "get help
  with this fault" in Diagnose, help-decode in Decode lab, privacy zones in More → Places;
  [spec](../specs/2026-10-07-trip-sharing-design.md), approved;
  [ADR-0043](../decisions/adr-0043-gps-and-logs-in-shared-trips.md)); third-party adapters
  (ELM327 and others) in `openostler/adapters/`, with the Brain hosting one only for a vehicle
  with no node, through the soft gate
  ([spec](../specs/2026-10-07-source-adapters-design.md), approved;
  [ADR-0044](../decisions/adr-0044-adapters-on-the-brain-without-a-node.md)); later, Crash SOS
  and the unplug alarm in Security.
- **§2 gains two registry pieces** (accounts spec §15, approved): a `route` detail on the
  `location` ladder and a `link` audience, with `public` brought forward for explicit publishing.
  Full logs (L3) and diagnostics bundles (L4) are hand-overs, never grants.
- **§3 is unchanged and applies to all four:** none declares a car action; guidance renders only
  through the `map` template while Moving; the speed-limit tint is off by default and never
  logged or scored; Phone shows only shell templates while Moving (`call`, the message
  `alert_card`, a favourites `short_list` of ≤ 6), its keypad, contacts and recents Parked
  only; every class starts in ghost. §3's node-gate line gains ADR-0044's one exception: for a
  vehicle with no node, an adapter driven through the soft gate under the adapter rules.
- **Home Assistant direction** (ADR-0042's DMD-round amendment, items 5–9): dashboards follow
  Home Assistant's views, sections, cards and badges; vehicle packs and data sources are
  **integrations** and feature apps are **add-ons**, listed on one page. Container add-ons on
  the Brain, install flavours (OS image, container, VM later, Python for developers) and Home
  Assistant compatibility (investigated, not promised) wait for a Home Assistant research
  round and their own ADRs.

## Changelog

- 2026-10-07: v0.1, proposed map (ecosystem drafts).
- 2026-10-07: v1.0, approved by the owner on 2026-10-07 ("approve all"; ADR-0042 accepted):
  the catalogue at More → Add-ons, Integrations one add-on per integration, the add-on specs
  linked, the new slots named.
- 2026-10-07: v1.1, Proposed amendment (2026-10-07, DMD round) for owner approval: proposed rows
  for Ostler Community, Navigation, Alerts and Phone; core ShellInput, per-trip sharing and later
  Crash SOS; link to the DMD feature map. The approved text is unchanged.
- 2026-10-07: v1.2, the Ostler Community row and bullet revised in place for the owner's
  direction: a closed, Ostler-run hub (not self-hostable) that is also the forum, the
  vehicle-development workspace and the wiki, with the open `ostler-app-hub`. The approved text
  is unchanged.
- 2026-10-07: v1.3, the Phone row and bullets revised in place (cross-spec reconcile): Phone
  & Comms (mirroring, dialer, contacts, recents, messages; needs a Brain for calls), linked to
  its draft spec, still not created. The approved text is unchanged.
- 2026-10-07: v1.4, the DMD-round amendment is approved by the owner on 2026-10-07 ("approve
  all", DMD round) and renamed "Amendment (2026-10-07, DMD round), approved"; the rows lose
  "proposed" (Alerts stays later, named only); adapters (ADR-0044) and the Home Assistant
  direction added; DMD-round decision 4 answered as recommended.
- 2026-10-07: v1.5, amended (OS round, approved by the owner on 2026-10-07, "approve all"):
  the core and add-on split superseded by ADR-0046.

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
4. **(DMD round) Add the four rows and the core gains?** Recommend: yes, as the ADR-0042
   DMD-round amendment says (Ostler Community as a closed, Ostler-run service with an open
   add-on); the rows lose "proposed" when it is approved (done 2026-10-07).
   Alternative: keep only Ostler Community and Navigation in the map until Alerts and Phone have
   approved specs. (Reconcile note: Phone now has an approved spec, Phone & Comms; Alerts has none.)
   *Answered 2026-10-07: approved as recommended ("approve all", DMD round); the alternative
   was not chosen.*
