---
title: "ADR-0042 — Ecosystem: small core, add-ons are the product"
area: decisions
status: locked
version: 1.2
updated: 2026-10-07
depends_on: [docs/feature_map_dmd.md, specs/2026-10-07-community-hub-design.md, specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-trip-sharing-design.md, references/research/dmd2_features.md, references/research/dmd_hub_features.md, GOALS.md, SCOPE.md, CONSTITUTION.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, references/research/ui/app_model.md, references/research/app_teardown_speedometer.md, references/research/obd_telematics_apps.md, references/research/driver_distraction_rules.md, references/research/addons_catalogue.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all"). Ostler is an ecosystem whose main goal is getting the car's data into apps: a small core and installable add-ons, Home Assistant style. One core product (one app per store, one shell), no separate Android apps; thin Android Auto, CarPlay and watch companions only later, each specced against that platform's category first (CarPlay Driving Task allows no live gauges and no maintenance). The phone app's background location, push and pairing are native and fixed; add-ons on the phone are bundled into a shell build or declarative, never fetched code. Core is the shell (layouts, strip, rail, Drive mode, login/users/invites, the VSS stream, the gate client, the app registry, the Add-ons catalogue), Diagnose, Trips (was Logs), Network and Security (once a node exists). Add-ons in their own repos: Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations (RealDash CAN out, LubeLogger bridge, social integrations) and Decode lab as a developer add-on. More → Add-ons lists Installed and Available with Core / Add-on / Developer labels, no remote catalogue yet; an empty Home suggests add-ons. One add-on per integration. Exit guarantee: Export all, and nothing in core depends on an Ostler-run server. No driving score in core. A Proposed amendment (2026-10-07, DMD round), awaiting the owner, adds four add-ons from the DMD2 and DMD Hub research: `ostler-app-hub` (open) with its closed, Ostler-run `ostler-hub` service (Ostler Community: publishing, forum, vehicle development, wiki), `ostler-app-navigation`, `ostler-app-alerts` and `ostler-app-phone`; puts the `ShellInput` D-pad model and per-trip sharing in core, and Crash SOS in core Security later.
---

# ADR-0042 — Ecosystem: small core, add-ons are the product

> **Proposed amendment (2026-10-07, DMD round), awaiting the owner:** four new add-ons
> (Ostler Community, Navigation, Alerts, Phone), `ShellInput` and per-trip sharing in core,
> Crash SOS in core Security later. See
> [Proposed amendment](#proposed-amendment-2026-10-07-dmd-round). The accepted text is unchanged.

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07 ("approve all"), drafted from
  the owner's ecosystem direction of the same day. Specs it changes carry a dated
  "Amendment (2026-10-07), approved":
  [app-model spec §14](../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates),
  the UI spec §12 (lockouts, templates, Trips, Drive), the accounts spec §14 (data-class
  registry).
  Map of the result: [docs/ecosystem.md](../docs/ecosystem.md).

## Context

- The owner: "Ostler is an ecosystem; its main goal is getting the car's data into apps.
  Small core, add-ons are the product", in the Home Assistant style: one core product with
  installable add-ons, no separate Android apps, maybe thin Android Auto, CarPlay or watch
  companions later.
- The app model ([spec](../specs/2026-10-06-app-model-design.md), draft v0.5) already gives
  one shell, apps by manifest, optional apps in `ostler-app-<x>` repos (ADR-0034 amendment)
  and a phone build on the Companion model (§7.1). It never says which features are core,
  how a user finds and enables an add-on, or what core promises if Ostler the project goes.
- Telematics history: Automatic and Dash died with their servers and took every integration
  with them; Dash's road to revenue ran through insurers and scores
  ([obd_telematics_apps](../references/research/obd_telematics_apps.md#automatic-and-dash-what-they-did-and-why-they-died)).
  The owner's reference app (Speedometer, now Odo) is a strong single app, but its garage,
  friends and convoy features are exactly the parts that suit add-ons
  ([teardown §5](../references/research/app_teardown_speedometer.md#5-mapping-every-feature-onto-ostler)).
- CarPlay's Driving Task category refreshes data no faster than every 10 s and bars
  maintenance features; Android Auto has no gauge template
  ([driver_distraction_rules §2](../references/research/driver_distraction_rules.md#2-android-for-cars-and-carplay-checked-2026-10-07)).

## Decision drivers

- Core only shrinks (GOALS §2.6); the five-destination cap stands (UI spec §3.4).
- One shell owns every safety surface; no add-on can weaken a lockout or reach the car
  except through the gate (app-model §8, ADR-0033).
- Store rules: no downloaded code that changes features (Apple 2.5.2, Play), native value
  in the binary (Apple 4.2) (app-model §7.1).
- Local-first and survivable: the product must outlive any Ostler-run server.

## Decision

1. **One core product, add-ons on top.** Ostler ships as one app (one shell, ADR-0018,
   app-model) per host. Features beyond the core are **add-ons**: apps in the app model,
   off by default, that a user installs or enables. There are **no separate Android or iOS
   apps** per feature.
2. **Companions later, thin, category first.** Android Auto, CarPlay and watch surfaces are
   later companions inside the same phone binary, each specced against that platform's
   category before any code: CarPlay as Driving Task with **no live gauges** (≥ 10 s refresh)
   and **no maintenance**; Android Auto as IoT. They show the shell's `alert_card`, a
   `short_list` of values and trip status. Live gauges stay in Ostler's own head-unit UI.
3. **The phone-app boundary.** Background location, push notifications and pairing (BLE and
   local Wi-Fi to the node, Tier 2–3 approval over local links, ADR-0033 §6) are **native
   features fixed in the binary**. Add-ons on the phone are **bundled** into a shell build
   (the phone's own, or the user's Brain's served per app-model §7.1) or **declarative**;
   never fetched or runtime-loaded code. Add-ons reach native features only through the
   shell SDK, under the data-class registry.
4. **Core and add-ons.**

   | Core (platform repo `ostler`) | Add-ons (own repos, ADR-0034) |
   |---|---|
   | **Shell:** layouts, status strip, rail, Drive mode, login/users/invites, the VSS stream, the safety-gate client, the app registry, the **Add-ons catalogue** | **Social** (`ostler-app-social`): messaging, push-to-talk, calls, cameras later |
   | **Diagnose** | **Vehicles & Map** (`ostler-app-vehicles`) |
   | **Trips** (was Logs; Speedometer/Odo features folded in) | **Maintenance & Garage** (`ostler-app-maintenance`): services, reminders, fuel, costs |
   | **Network** | **Cameras** (`ostler-app-cameras`) |
   | **Security**, shown once a node exists | **Integrations**, one add-on per integration: RealDash CAN out, LubeLogger bridge (`ostler-app-lubelogger`), social integrations |
   | | **Decode lab**, a **developer** add-on, shown only in service mode |

   Decode lab moves from "core app" (app-model Q5) to developer add-on: off by default,
   labelled Developer; its code stays in `ostler` until ADR-0034's split rule applies.
   No add-on adds a destination.
5. **The Add-ons catalogue.** **More → Add-ons** (replacing More → Apps; UI spec §12.4) has two tabs,
   **Installed** and **Available**; every card shows a **Core** or **Add-on** label
   (Developer for Decode lab), what it needs ("Needs a camera", "Needs the Brain") and the
   data classes it reads. Core cards cannot be removed. **Available** lists add-ons bundled
   in the build and declarative add-ons a device suggests; a remote catalogue is a new
   outbound path and waits for its own ADR (app-model Q7). Enabling is an owner-role
   operation; nothing auto-installs.
6. **Empty-state Home.** With no add-on enabled, Home shows its core cards plus one
   dismissible card of suggestions, such as **"Track maintenance"** (Maintenance & Garage)
   and **"Share drives with friends"** (Social), each opening that add-on's catalogue page.
   Never on a head unit while Moving.
7. **Exit guarantee.** Trips offers **Export all** (CSV, GPX, VBO; ADR-0009) on one screen,
   and every add-on that keeps user data exports it in an open format. **Nothing in core
   depends on an Ostler-run server**; add-ons that use one degrade to local function.
8. **No driving score in core.** Trips shows neutral facts privately. Any score or
   leaderboard lives only in the Social add-on, opt-in per friend or group, speed never
   ranked, never exportable to insurers.
9. **Unchanged hard lines.** The node gate is the only path to the car (ADR-0032, ADR-0033);
   remote paths, mesh included, are read and alerts only; while Moving on a driver-facing
   display only shell templates render; every data class starts in ghost (nothing shared).

## Confirmation

- Registry tests: an add-on is disabled on a fresh install; disabling it removes every
  contribution; a core card cannot be removed; Available never lists an incompatible add-on.
- An import test: core (shell, Diagnose, Trips, Network, Security) builds and its tests pass
  with no add-on package installed.
- A network test: with every Ostler-run host unreachable, core starts, records, replays and
  exports; Export all produces CSV, GPX and VBO.
- The phone build's CI fails on any runtime `import()` of a URL outside the bundle.
- A lint forbids a score or ranking field in core's Trips schema.

## Consequences

- App-model spec §3, §7 and §8 change (amendment §14, approved); UI spec §3.4 renames Logs
  to Trips and §3.5 gains the new templates and passenger rules (UI spec §12, approved).
- Social, Vehicles & Map and Maintenance & Garage each need a spec before code.
- SCOPE.md and GOALS.md re-state the mission (approved wording).
- The catalogue UI and empty Home land in phase UA with the registry.

## Alternatives considered

The owner's alternatives in the decision list below were not chosen.

- **A big single app** (the Odo model). Rejected: everything becomes core and grows, and
  every feature shares one release cadence.
- **Separate store apps per feature.** Rejected: separate apps cannot share one lockout,
  one gate client or one sign-in, and the stores see repackaged clones.
- **A runtime add-on store in the phone app.** Rejected by Apple 2.5.2 and app-model §7.1.
- **Live-gauge CarPlay companion.** Rejected: against the Driving Task rules.

## Relation to other ADRs

- **ADR-0034:** applied; add-on repos are `ostler-app-<x>`.
- **ADR-0018 / UI spec:** five destinations kept; Logs reads Trips.
- **ADR-0029:** the data-class registry with audiences extends its token data classes.
- **ADR-0009, ADR-0033, ADR-0038:** unchanged and relied on.

## Decisions for the owner

Answered 2026-10-07: approved as recommended. Each recommendation below is the decision;
each alternative was not chosen.

1. **Accept the small-core model?** Recommend: accept this ADR. Alternative: keep the
   app-model spec as is and decide core/add-on per feature.
2. **Decode lab: developer add-on or core?** Recommend: developer add-on, code in `ostler`
   for now. Alternative: keep Q5's answer (core app shown in service mode).
3. **Phone add-ons: bundled or declarative only, including from the Brain?** Recommend: yes;
   "bundled" means built into the phone's or the Brain's shell build. Alternative: phone's
   own bundle only, no Brain-served add-ons in the native app.
4. **Security in core only once a node exists?** Recommend: yes (hidden with no node).
   Alternative: always shown, with a "needs a node" card.
5. **Companions: when?** Recommend: none before Trips and Drive mode ship on the head unit;
   then CarPlay Driving Task (alerts, trip status, ≤ 10 s refresh). Alternative: an Android
   Auto IoT companion first.
6. **Remote catalogue?** Recommend: not now; Available lists bundled and device-suggested
   add-ons only. Alternative: a signed catalogue repo, with its own outbound-path ADR.

## Proposed amendment (2026-10-07, DMD round)

**Status: proposed, for the owner's approval.** The accepted decision above is unchanged until
the owner approves this section. Source: the owner's direction of 2026-10-07 to "pull all the
features over" from DMD2 and DMD Hub, "many as add-ons, and separate repos", with the Hub as the
social side and per-trip sharing at chosen data levels. The feature-by-feature mapping is
[docs/feature_map_dmd.md](../docs/feature_map_dmd.md) (draft); the research is
[DMD2 features](../references/research/dmd2_features.md),
[DMD2 UI teardown](../references/research/dmd2_ui_teardown.md),
[DMD Hub features](../references/research/dmd_hub_features.md),
[DMD Hub UI teardown](../references/research/dmd_hub_ui_teardown.md),
[trip and log sharing](../references/research/trip_and_log_sharing.md) and
[community hub architecture](../references/research/community_hub_architecture.md).

1. **Four new add-ons** join decision 4's right-hand column, each off by default, each in its
   own repo under ADR-0034's rule (proposed amendment there), none created yet:

   | Add-on | Repo(s) | What it is | Spec |
   |---|---|---|---|
   | **Ostler Community** | `ostler-app-hub` (open AGPL shell add-on, holding the public API contract) and `ostler-hub` (a **closed service run by Ostler**, one official instance, not self-hostable, in its own private repo separate from `ostler-cloud`: Python ASGI, PostgreSQL + PostGIS, S3-compatible storage, PMTiles; web in TS/React on the shell's kit and tokens) | Publish trips and routes, help threads for decoding and diagnosis, the project **forum** (categories per make and model, Q&A, solved, search, notifications), the **vehicle-development workspace** (decode cards, vehicle projects, data-only PRs to pack repos through a GitHub App), the **wiki** (vehicle pages generated from pack releases plus community pages), clubs, events, Discover; no federation | [community hub](../specs/2026-10-07-community-hub-design.md) (draft) |
   | **Navigation** | `ostler-app-navigation` | Routing on the Brain with an open engine (licence to verify), turn-by-turn and voice, GPX library, import/export and follow, planner, roadbook, curated routes, route sharing to the hub. It absorbs the "routes" and "roadbook" ideas. Guidance renders through the `map` template's next manoeuvre while Moving; the speed-limit tint is off by default, never logged or scored; no speed cameras in v1 | [navigation](../specs/2026-10-07-navigation-addon-design.md) (draft) |
   | **Alerts** | `ostler-app-alerts` | UK official weather, flood and closure alerts, free and opt-in; later | needs spec |
   | **Phone** | `ostler-app-phone` | Phone mirroring (notifications, calls), Parked-only content; later | needs spec |

   **Ostler Community is a closed add-on service, outside core.** It sits outside the small core
   on the add-on side, like Ostler Cloud: an Ostler-run server reached only through its open
   add-on, under ADR-0013's cloud boundary (ADR-0034 proposed amendment). Decision 7 holds as a
   hard rule and, because the hub is closed and single-operator, gains these lines:
   - **inside core, nothing:** no core app, contract or test needs `ostler-app-hub` or the hub;
     the add-on degrades to local function (shares stay on the device; help falls back to file,
     relay link or the pack repo's issue form);
   - **outside, the hub only:** the forum, the wiki, vehicle projects and public pages;
   - **export everything** from the hub in open formats (posts, wiki edits, decode cards, items,
     club data for club owners), plus a monthly public CC BY-SA dump of public knowledge and a
     90-day shutdown promise;
   - **pack contributions never need the hub:** the pack repos on GitHub stay the source of
     truth and accept issues and PRs directly;
   - **the client stays open:** encryption of help attachments and what leaves the device are
     checkable in `ostler-app-hub`.

   Safety, sharing and decode help are never charged for (only extra hosted storage). The hub has
   no points, ranks or votes, no direct messages, no public feed for strangers (Discover instead;
   an opt-in Following chip in `ostler-app-hub` only), and shares out through Web Share, copy
   link, QR and embed, never social-network buttons. Its H1 accepts track, trip and log files
   only (no images; photos at H4 with on-device blur). Minimum age 16; live follow and public
   profiles 18.
2. **Core gains, it does not grow a destination.** These stay in `ostler`:
   - **`ShellInput`** in the shell: a D-pad input model (keyboard arrows, Enter and Escape, HID
     remotes, the Gamepad API, and read-only steering-wheel button events from packs) with focus
     zones, spatial navigation, long-press to the rail, a **Drive menu** that is a `short_list`
     of ≤ 6 driver-safe actions while Moving, confirm sheets that open with Cancel focused, a
     3 px focus-ring token, bindings owned by the display, a key test screen, and a map theme
     independent of the app theme. It ships with U2 ([ShellInput](../specs/2026-10-07-shell-input-design.md),
     draft). Hardware remotes are hardware add-ons that only supply key events; input is never
     paywalled.
   - **Per-trip sharing**: the scrubber, the `ostler.share/1` bundle writer and
     `ostler share verify` in the platform; the share sheet in Trips; "get help with this fault"
     in Diagnose; the help-decode flow in Decode lab; privacy zones in the shell (More → Places)
     ([trip sharing](../specs/2026-10-07-trip-sharing-design.md), draft;
     [ADR-0043](adr-0043-gps-and-logs-in-shared-trips.md), proposed).
   - **Crash SOS and the unplug/theft alarm** in core **Security**, later, each with its own
     spec; Crash SOS is the existing ghost exception (accounts spec §14.5).
3. **The Add-ons catalogue** (decision 5) lists the four when bundled: Ostler Community card
   "Needs a hub account", Navigation "Needs the Brain", Alerts "Needs internet", Phone "Needs a
   paired phone". No remote catalogue is added.
4. **Unchanged hard lines** (decision 9) apply to all four: none declares a car action (send to
   device is the add-on's own data between the user's devices); nothing from them renders on a
   driver-facing display while Moving except through shell templates; every class they read
   starts in ghost.

**Confirmation (deltas).** The import test of the Confirmation section also passes with
`ostler-app-hub`, `ostler-app-navigation`, `ostler-app-alerts` and `ostler-app-phone` absent; the
network test also passes with every hub unreachable; a ShellInput test drives every destination
and Drive mode by keyboard only and asserts that gated confirms open with Cancel focused.

### Decisions for the owner (DMD round)

1. **Add the four add-ons?** Recommend: yes, Ostler Community (`ostler-app-hub` + `ostler-hub`)
   and Navigation now as specs, Alerts and Phone named for later. Alternative: Community and
   Navigation only; decide Alerts and Phone when they are specced.
2. **Community hub: closed, Ostler-run, outside core and separate from `ostler-cloud`?**
   Recommend: yes (owner's direction): a closed service in its own private repo, one official
   instance, not self-hostable, reached through the open `ostler-app-hub`; decision 7 holds with
   the lines above (nothing in core needs it, export everything, pack contributions never need
   it). Alternative: the previous draft, an open, self-hostable AGPL hub with one official
   instance; or the hub inside the closed `ostler-cloud`.
3. **One navigation add-on that absorbs routes and roadbook?** Recommend: yes. Alternative:
   separate `ostler-app-routes` and `ostler-app-roadbook` repos.
4. **ShellInput in core with U2?** Recommend: yes. Alternative: a later phase, or an
   input add-on.
5. **Crash SOS in core Security (later) rather than an add-on?** Recommend: core, because it is
   the one safety exception to ghost and must never be optional or paid. Alternative: a separate
   `ostler-app-sos` add-on.

## Changelog

- 2026-10-07 — v0.1, proposed: drafted from the owner's ecosystem direction.
- 2026-10-07 — v1.0, accepted: approved by the owner ("approve all"). The catalogue sits at
  More → Add-ons (UI spec §12.4); Integrations is one add-on per integration; every
  "Decisions for the owner" item answered as recommended.
- 2026-10-07 — v1.1, adds the Proposed amendment (2026-10-07, DMD round) for owner approval:
  `ostler-app-hub` + `ostler-hub`, `ostler-app-navigation`, `ostler-app-alerts`,
  `ostler-app-phone`; ShellInput and per-trip sharing in core; Crash SOS in core Security later.
  The accepted text above is unchanged.
- 2026-10-07 — v1.2, the Proposed amendment (DMD round) revised in place for the owner's
  direction: Ostler Community becomes a closed, Ostler-run service (not self-hostable, its own
  private repo separate from `ostler-cloud`) that is also the forum, the vehicle-development
  workspace and the wiki; the open `ostler-app-hub` stays; decision 7's exit guarantee gains
  explicit inside/outside lines for the hub; DMD-round decision 2 revised. The accepted text
  above is unchanged.
