---
title: "ADR-0042 — Ecosystem: small core, add-ons are the product"
area: decisions
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [GOALS.md, SCOPE.md, CONSTITUTION.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, references/research/ui/app_model.md, references/research/app_teardown_speedometer.md, references/research/obd_telematics_apps.md, references/research/driver_distraction_rules.md, references/research/addons_catalogue.md]
summary: >
  Proposed (2026-10-07), awaiting the owner. Ostler is an ecosystem whose main goal is getting the car's data into apps: a small core and installable add-ons, Home Assistant style. One core product (one app per store, one shell), no separate Android apps; thin Android Auto, CarPlay and watch companions only later, each specced against that platform's category first (CarPlay Driving Task allows no live gauges and no maintenance). The phone app's background location, push and pairing are native and fixed; add-ons on the phone are bundled into a shell build or declarative, never fetched code. Core is the shell (layouts, strip, rail, Drive mode, login/users/invites, the VSS stream, the gate client, the app registry, the Add-ons catalogue), Diagnose, Trips (was Logs), Network and Security (once a node exists). Add-ons in their own repos: Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations (RealDash CAN out, LubeLogger bridge, social integrations) and Decode lab as a developer add-on. Settings → Add-ons lists Installed and Available with Core / Add-on labels; an empty Home suggests add-ons. Exit guarantee: Export all, and nothing in core depends on an Ostler-run server. No driving score in core.
---

# ADR-0042 — Ecosystem: small core, add-ons are the product

- **Date:** 2026-10-07
- **Status:** proposed (drafted from the owner's ecosystem direction of 2026-10-07; not
  accepted). Specs it changes carry a dated "Proposed amendment (2026-10-07)":
  [app-model spec §14](../specs/2026-10-06-app-model-design.md#14-proposed-amendment-2026-10-07-ecosystem-add-ons-trips-and-templates),
  the UI spec §3.5 (lockouts and templates), the accounts spec (data-class registry).
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
   | **Security**, shown once a node exists | **Integrations**: RealDash CAN out, LubeLogger bridge (`ostler-app-lubelogger`), social integrations |
   | | **Decode lab**, a **developer** add-on, shown only in service mode |

   Decode lab moves from "core app" (app-model Q5) to developer add-on: off by default,
   labelled Developer; its code stays in `ostler` until ADR-0034's split rule applies.
   No add-on adds a destination.
5. **The Add-ons catalogue.** **Settings → Add-ons** (replacing More → Apps) has two tabs,
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

- App-model spec §3, §7 and §8 change (proposed amendment §14); UI spec §3.4 renames Logs to
  Trips and §3.5 gains the new templates and passenger rules.
- Social, Vehicles & Map and Maintenance & Garage each need a spec before code.
- SCOPE.md and GOALS.md re-state the mission (proposed wording).
- The catalogue UI and empty Home land in phase UA with the registry.

## Alternatives considered

- **A big single app** (the Odo model). Rejected: everything becomes core and grows, and
  every feature shares one release cadence.
- **Separate store apps per feature.** Rejected: separate apps cannot share one lockout,
  one gate client or one sign-in, and the stores see repackaged clones.
- **A runtime add-on store in the phone app.** Rejected by Apple 2.5.2 and app-model §7.1.
- **Live-gauge CarPlay companion.** Rejected: against the Driving Task rules.

## Relation to other ADRs

- **ADR-0034:** applied; add-on repos are `ostler-app-<x>`.
- **ADR-0018 / UI spec:** five destinations kept; Logs reads Trips (proposed).
- **ADR-0029:** the data-class registry with audiences extends its token data classes.
- **ADR-0009, ADR-0033, ADR-0038:** unchanged and relied on.

## Decisions for the owner

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
