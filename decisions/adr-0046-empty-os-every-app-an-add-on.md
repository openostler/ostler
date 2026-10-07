---
title: "ADR-0046 — The empty OS: the platform is an operating system with no apps; every feature is an app in its own repo"
area: decisions
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0045-ux-first.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, GOALS.md, CONSTITUTION.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-store-design.md, specs/2026-10-07-head-unit-apps-design.md, references/research/ha_architecture_addons.md, references/research/ha_integrations_dashboards.md, references/research/ha_companion_community.md]
summary: >
  Proposed (2026-10-07), awaiting the owner. The platform repo `ostler` becomes an empty operating system, like an Android phone with no apps. The OS holds system services (the gate client and node link, the module bus, the VSS stream, the integration loader where vehicle packs become integrations, the app runtime, permissions and data classes, users, accounts and roles, driving state and the Moving lockouts, the alert and notification pipeline, audio focus and the call session, input, recording and export, backups, updates, network) and the system UI (launcher with home pages, dock, drawer, widget host and edit mode; status strip; Connection sheet; system Settings; the Store client; the theme engine; first-run setup). Safety is never an app. Everything else is an app in its own repo: Diagnostics, Trips, Security, Maintenance, Social, Map, Navigation, Phone, Radio, Audio, Media, Camera, Decode lab, Community, the starter widgets and the default theme. Product flavours become preinstalled sets (amends ADR-0039); any non-system app can be uninstalled (on the phone, bundled apps are disabled, not deleted). Code in core today moves only after each app's UX brief is approved (ADR-0045); the ADR maps today's modules to target repos and gives the repo list (amends ADR-0034). Supersedes ADR-0042 §4's core list and §5's catalogue placement; reverses GOALS' "rebuilding media" non-goal. Risks: a bare OS shows nothing, so flavours, the bundled catalogue and first run matter; safety stays in the OS.
---

# ADR-0046 — The empty OS: every app is an add-on

- **Date:** 2026-10-07
- **Status:** proposed (drafted from the owner's direction of 2026-10-07; not accepted).
  If accepted it **supersedes in part**
  [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (decision 4's core list
  and decision 5's catalogue at More → Add-ons) and **amends**
  [ADR-0034](adr-0034-repo-boundaries.md) (the repo list),
  [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (product flavours as
  preinstalled sets) and the [app-model spec](../specs/2026-10-06-app-model-design.md) §3 and
  §14.1. The notes on those files are added only on acceptance; until then this text is the
  record. Work follows [ADR-0045](adr-0045-ux-first.md) (UX first).
- **Designs (drafts of the same day):**
  [launcher and widgets](../specs/2026-10-07-launcher-and-widgets-design.md),
  [app UI model](../specs/2026-10-07-app-ui-model-design.md),
  [Store](../specs/2026-10-07-store-design.md),
  [head-unit apps](../specs/2026-10-07-head-unit-apps-design.md).

## Context

- The owner (2026-10-07): "The main repo is an empty operating system, like an Android phone
  with no apps installed. Everything else is an add-on in its own repo, even Diagnostics. A
  Guardian owner may install only the Security app and its widgets." And: "the most open,
  modular system possible, Home Assistant style", with an Android launcher, a Store and the
  standard head-unit apps.
- [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (accepted) chose a small
  core: the shell, Diagnose, Trips, Network and Security in `ostler`, add-ons outside. The new
  direction moves Diagnose, Trips and Security out too, and adds Radio, Audio, Media and
  Camera.
- Home Assistant splits Core, the Supervisor and the OS; integrations connect things, apps
  (formerly add-ons) are installed beside it
  ([HA architecture](../references/research/ha_architecture_addons.md),
  [HA integrations and dashboards](../references/research/ha_integrations_dashboards.md)).
  Android splits system services and system UI from apps, and lets apps add widgets,
  shortcuts and settings.
- [GOALS](../GOALS.md) §3 lists "Rebuilding media: CarPlay/Android Auto, radio, amplifier and
  wheel controls stay on a media head unit" as a non-goal. The owner now wants radio, audio
  and every standard head-unit page.
- The phone app may not download code that changes features (app-model §7.1, ADR-0042
  decision 3). That limit still holds.

## Decision drivers

- Safety is never optional: the lockouts, the gate, alarm paths and telltales must work with
  no app installed (CONSTITUTION, ADR-0032, ADR-0033).
- Open and modular: anyone can replace any app, Diagnostics included.
- A device shows only what its owner wants: a Guardian owner installs Security alone.
- One contract for first-party and community apps.
- Local-first: the OS and its bundled catalogue work offline.
- Store rules on the phone are unchanged.

## Decision

### 1. The OS boundary

The OS is the platform repo `ostler`. It has two halves, in the Android sense.

**System services** (no UI of their own, or only system UI):

| Service | What it does | Today |
|---|---|---|
| **Gate client and node link** | the action API, grants, the node gate client, the soft gate for adapters (ADR-0044), confirmations and approvals | `web/`, `can/`, `node/`, `signing.py` |
| **Module bus** | the Brain's MQTT 5 broker and topics, the cluster and role holders | `mqtt/`, `node/` |
| **VSS stream** | one data stream of VSS signals with confidence and staleness | `signals/`, `metrics.py`, `web/sources.py` |
| **Integration loader** | loads vehicle packs, the node source, source adapters and bridges as **integrations** (§4); the `openostler.vehicle` entry point stays | `pack.py`, `transport/`, `kline/`, `kwp2000/`, `obd/`, `dtc/`, `session.py`, `catalog.py`, `menus.py`, `commands.py`, `faultscan.py`, `modscan.py` |
| **App runtime** | the registry, install, enable, update, isolation, the SDK `@ostler/app-sdk`, app backends | `ui/src/shell/destinations.ts` (seed) |
| **Permissions and data classes** | the data-class registry, ghost by default, per-app grants, outbound-path consent | accounts spec §14 |
| **Users, accounts and roles** | sign-in, kiosk session, roles and categories, invites | accounts spec |
| **Driving state and Moving lockouts** | Parked, Idling, Moving, Park evidence, driver-facing displays, Passenger view, the Moving templates | UI spec §3.5, §12.1 |
| **Alerts and notifications** | the alert pipeline, `alert_card`, notification channels, the alarm path to the phone, Crash SOS later | ADR-0033, UI spec §12.1 |
| **Audio focus and the call session** | one audio focus, the one call session (app-model §15.5), the system voice that reads alerts aloud | added to the owner's list: Radio, Media and Phone must share one owner of the speaker |
| **Input** | ShellInput, bindings, steering-wheel button learning, the key test | `ui/src/shell/input.ts`, `focus.ts` |
| **Recording and export** | the always-on recorder and store, Mark, whole-app replay, Export all, the share scrubber and bundle (ADR-0043) | `logbook/`, `gps/`, `imu/`, `geo/` |
| **Backups, updates, network** | backups of OS and app data, OS and app updates, uplinks, remote access, pairing, certificates | `web/`, ADR-0028 |

**System UI:**

| Surface | What it is | Spec |
|---|---|---|
| **Launcher** | home pages in a carousel (Drive mode is the carousel while Moving), the dock, the app drawer, the widget host and edit mode | [launcher and widgets](../specs/2026-10-07-launcher-and-widgets-design.md) |
| **Status strip** | the chips, including the worst telltale and the Security chip | UI spec §3.2, §15 |
| **Connection sheet** | link state, the always-reachable Reset layout | UI spec §3.2 |
| **System Settings** | network and devices, vehicles and integrations, apps, home screen, display and theme, sound, notifications, driving and safety, privacy and places, users, input, backups, updates, developer, about | [app UI model §8](../specs/2026-10-07-app-ui-model-design.md) |
| **Store client** | browse, install, update, the bundled offline catalogue | [Store](../specs/2026-10-07-store-design.md) |
| **Theme engine** | tokens, theme packs, wallpaper, icon packs; safety colours fixed | [visual design system](../specs/2026-10-07-visual-design-system-design.md) |
| **First-run setup** | owner, vehicle, integrations, flavour apps, dashboard builder | launcher spec §9 |

### 2. Safety is never an app

These stay in the OS, work with no app installed and cannot be uninstalled, disabled or
covered by any app: the gate client and the soft gate; driving state and every Moving
lockout; the Moving templates and their limits; the **worst-telltale chip, the fault sheet
and the Home warnings widget**; **alarm alerts** (the Security chip while a node is present,
the Security alert widget, `alert_card`) and the alarm path to the phone; confirm sheets,
approvals and the ActiveTestBanner with Stop; Passenger view; Crash SOS (moved here from
"core Security later", ADR-0042 DMD-round decision 2); the data-class registry, privacy zones
(Places) and the share scrubber. With Diagnostics uninstalled, a red telltale still shows,
with its code and system name, and the fault sheet still opens.

### 3. Everything else is an app in its own repo

| App | Repo | What it holds | From today |
|---|---|---|---|
| **Diagnostics** | `ostler-app-diagnostics` | systems, Scan all, faults, live data, tests, procedures, settings, pack car views, docs | `ui/src/destinations/Diagnose.tsx`; `ui/src/screens/` Faults, Inputs, Outputs, Utilities, ModuleSettings, Docs; `ui/src/components/` ModuleSelect, ProcedureSheet, ItemCard, CoverageBar; `ui/src/vehicles/`; `web/docs.py`, `web/markdown.py` |
| **Trips** | `ostler-app-trips` | timeline, trip detail, analysis, replay controls, share sheet | `ui/src/destinations/LogsDestination.tsx`; `ui/src/screens/` Logs, Analysis; `ui/src/components/replay/` (map engine files stay in the OS); RecordingCard, RecordingOptions, RewindButton, NoteSheet |
| **Security** | `ostler-app-security` | alarm, arming, events, tracker map, geofences, clips | `ui/src/destinations/Security.tsx` |
| **Maintenance** | `ostler-app-maintenance` | as its approved spec | — |
| **Social** | `ostler-app-social` | as its approved spec | — |
| **Map** | `ostler-app-map` (replaces the uncreated `ostler-app-vehicles`) | the full map page, places, offline regions; friends' vehicles as a layer from the Vehicles & Map spec | — |
| **Navigation** | `ostler-app-navigation` | as its approved spec | — |
| **Phone** | `ostler-app-phone` | Phone & Comms, as its approved spec | — |
| **Radio**, **Audio**, **Media**, **Camera** | `ostler-app-radio`, `-audio`, `-media`, `-cameras` | [head-unit apps](../specs/2026-10-07-head-unit-apps-design.md) | — |
| **Decode lab** | `ostler-app-decodelab` | capture, auto-mapping, labelling, coverage | `ui/src/screens/` Capture, CoverageMap; `sniff/`; `web/sniffer.py` (the reference decoder and shared vectors stay in the OS) |
| **Community** | `ostler-app-hub` | as its approved spec | `community/` (empty package) |
| **Starter widgets** | `ostler-starter` | the starter widget pack and the preset dashboards | the presets of the Drive-modes spec |
| **Default theme** | `ostler-theme-default` | Ostler Night, Day, Dim and Deep night as a theme pack | `ui/tokens/` values (the token names and safety colours stay in the OS) |

The OS keeps the component kit (`ui/src/components/` Gauge, StatTile, Sparkline, Trend,
Readout, Value, RangeBar and the V2 kit), exported to apps through the SDK. The launcher
(`ui/src/destinations/Home.tsx`, `ui/src/drive/`, `ui/src/screens/Drive.tsx`) and the drawer
and Settings (`ui/src/destinations/More.tsx`) stay in the OS. The MCP server stays an optional
system service (`[mcp]`, ADR-0030).

### 4. Integrations and object kinds

Vehicle packs, the node source, source adapters and bridges (MQTT and Home Assistant
discovery, OwnTracks, Traccar, ntfy, RealDash CAN out, LubeLogger) are **integrations**:
backend apps with a setup page and no pages of their own. Packs keep their repos
(`ostler-pack-<x>`) and their contract (ADR-0013); they gain an `ostler-app.json` with `kind:
integration`. The `generic_obd2` pack (ADR-0031) stays bundled with the OS as the default
integration. Every installable thing has an **object kind**: app, integration, widget pack,
theme pack, icon pack, wallpaper pack, dashboard preset, sound or EQ preset
([app UI model §5](../specs/2026-10-07-app-ui-model-design.md)).

### 5. Product flavours are preinstalled sets (amends ADR-0039)

The product names stay. A flavour is the set of apps preinstalled on first run:

| Flavour | Preinstalled apps |
|---|---|
| **Ostler Diagnostics** (node and phone) | Diagnostics, Trips, Security, starter widgets, default theme |
| **Ostler Guardian** | Security and its widgets, default theme |
| **Ostler Brain** (head unit) | Diagnostics, Trips, Security, Map, Media, Audio, starter widgets, default theme; Camera when a camera is found; Radio when a tuner is found |
| **Developer** (any flavour, service mode) | adds Decode lab |

- **Any non-system app can be uninstalled**, including Diagnostics. System services and system
  UI cannot (§1, §2).
- **On the phone**, code apps are bundled in the binary or served by the user's own Brain
  (app-model §7.1). "Uninstall" there disables the app and deletes its data; the code stays in
  the binary until the next build drops it. Data-only objects (themes, wallpapers, icon
  packs, presets) install and delete for real.
- Uninstalling asks to **export the app's data first** (the exit guarantee, ADR-0042
  decision 7).

### 6. Code in core today moves later

Nothing moves now. Each app's code leaves `ostler` only after **its UX brief is approved**
(ADR-0045) and its repo is created (§7). Until then it stays where it is, behind the app
registry as a bundled app with `trust: first_party`, so the boundary is tested before the
move. Server routes that read the car (menus, catalogue, faults, Scan all, actions) stay in
the OS as the vehicle service API that apps call through the SDK; only the UI and
app-specific backends move.

### 7. The repo list (amends ADR-0034)

| Kind | Repo pattern | Repos |
|---|---|---|
| **OS** | `ostler` | the OS, the SDK, the contracts, `generic_obd2` |
| **Firmware, hardware, contract** | unchanged | `ostler-firmware`, `ostler-hardware` (at PCB time), the module contract repo (at v1) |
| **Private services** | unchanged | `ostler-cloud`, `ostler-hub` |
| **Vehicle integrations** | `ostler-pack-<x>` | unchanged |
| **Other integrations** | `ostler-integration-<x>` | `-mqtt` (Home Assistant discovery, OVMS topics), `-owntracks`, `-traccar`, `-ntfy`, `-realdash`, `-lubelogger` (was `ostler-app-lubelogger`) |
| **Apps** | `ostler-app-<x>` | `-diagnostics`, `-trips`, `-security`, `-maintenance`, `-social`, `-map`, `-navigation`, `-phone`, `-radio`, `-audio`, `-media`, `-cameras`, `-decodelab`, `-hub`, `-alerts`, `-weather`, `-car`; later `-climate`, `-voice` |
| **Widget, theme and data packs** | `ostler-starter`, `ostler-theme-<x>`, `ostler-icons-<x>`, `ostler-wallpapers-<x>` | `ostler-starter`, `ostler-theme-default` |
| **Store catalogue** | `ostler-catalogue` | the signed catalogue data (Store spec), when its ADR is accepted |

A repo is created only when its app's work starts, with the owner asked first (ADR-0034's
DMD-round rule). ADR-0034's split grounds (toolchain, licence, cadence, contributors) are
replaced for apps by this rule: every app has its own repo.

### 8. Words

- **App** is the user's word for anything in the drawer (the owner's Android model).
  **Integration** is a backend app with a setup page. **Store** is where both are found.
  ADR-0042's "add-on" stays as the developer's umbrella word in specs.
- **More → Add-ons** is replaced: the drawer lists apps; **Settings → Apps** lists everything
  installed with its App info page; the **Store** browses and installs.

### 9. Unchanged hard lines

The node gate is the only path to the car, with ADR-0044's one exception; remote paths are
read and alerts only; while Moving on a driver-facing display only system templates render;
every data class starts in ghost; nothing in the OS needs an Ostler-run server; no driving
score in the OS. Apps never define car actions, tiers or categories.

### 10. GOALS changes (proposed text)

In GOALS §3 Non-goals, remove "Rebuilding media: CarPlay/Android Auto, radio, amplifier and
wheel controls stay on a media head unit" and add: "**Projection receivers** (Android Auto,
CarPlay) are not built by the project: they need certification and licences an open project
cannot hold ([head-unit apps](../specs/2026-10-07-head-unit-apps-design.md) §11)." In §1,
"Small core" reads "**Empty OS:** system services and system UI only; every feature is an app
(ADR-0046)". In §2 principle 6, "Five destinations is a hard cap" reads "The dock holds at
most its layout class's slots ([launcher](../specs/2026-10-07-launcher-and-widgets-design.md)
§5.1); every app stays reachable from the drawer". The non-goal "user-arranged dashboards"
is already replaced by the Drive-modes spec and goes.

## Risks

1. **A bare OS shows nothing.** Mitigations: flavours preinstall apps (§5); the Store ships a
   **bundled offline catalogue** with every first-party app; first-run setup runs the
   **dashboard builder** with basic templates; the system widgets (warnings, vehicle state,
   alarm) show with no app; an empty home page shows one **Get apps** card.
2. **Safety drifting into apps.** Mitigations: §2's list is a hard boundary; a test
   uninstalls every app and checks that telltales, alarm alerts, lockouts and Reset layout
   still work.
3. **Many repos.** Release, CI and SDK version skew grow. Mitigations: repos created only
   when needed; one CI template; SemVer on the SDK with a compatibility matrix in the Store.
4. **Phone store rules.** Code apps cannot be fetched on the phone. Mitigation: §5's phone
   rule; the Store on the phone installs data objects and enables bundled apps.
5. **Pi resources.** Many app backends on a 2 GB Brain. Mitigation: backends declare limits;
   the Store warns before install (app UI model §4.4).
6. **Third-party trust.** Mitigation: review levels, signed packages and a plain permissions
   sheet (Store spec).

## Confirmation

- An import test: the OS builds and its tests pass with **no** app package installed; the
  launcher shows the system widgets and the Get apps card.
- A safety test: with every app uninstalled, a red telltale fixture shows the chip and the
  fault sheet; an alarm fixture raises `alert_card` and the phone notification; Moving locks
  as today; Reset layout is reachable.
- A layering test: `openostler` imports no `ostler-app-*` or `ostler-integration-*` package.
- A flavour test: each flavour's first run installs exactly its set and nothing else.
- A registry test: a system service or system UI entry cannot be uninstalled or disabled.

## Consequences

- ADR-0042 decision 4's core list and decision 5's catalogue are superseded; its exit
  guarantee, phone boundary and companions stand.
- The app-model spec §3 and §14.1 change through the
  [app UI model spec](../specs/2026-10-07-app-ui-model-design.md).
- The Drive-modes spec's rail, switcher and editing sections change through the
  [launcher spec](../specs/2026-10-07-launcher-and-widgets-design.md).
- GOALS, SCOPE, README and docs/ecosystem.md are re-worded on acceptance.
- A remote Store catalogue is a new outbound path and needs its own ADR (ADR-0042 decision
  5); the [Store spec](../specs/2026-10-07-store-design.md) prepares it.

## Alternatives considered

- **Keep ADR-0042's small core** (Diagnose, Trips, Security in core). Not chosen: the owner
  wants Diagnostics replaceable and a Security-only Guardian install.
- **One monorepo for all first-party apps.** Not chosen by the owner's direction; it stays an
  owner decision (below).
- **Safety in a "Safety app" that cannot be removed.** Not chosen: an app that cannot be
  removed is a system service with extra steps.

## Relation to other ADRs

- **ADR-0042:** decisions 4–5 superseded in part; decisions 1–3 and 6–9 stand.
- **ADR-0034:** the repo list amended (§7).
- **ADR-0039:** flavours as preinstalled sets (§5); names unchanged.
- **ADR-0013, ADR-0031:** packs keep their contract and become integrations; `generic_obd2`
  stays bundled.
- **ADR-0018, ADR-0033, ADR-0044:** unchanged and relied on.
- **ADR-0045:** every move in §6 waits on an approved brief.

## Decisions for the owner

The full numbered list for this round is kept with the manager. The items here are this
ADR's own.

1. **Accept the empty OS?** Recommend: yes, as §1–§3. Alternative: keep ADR-0042's core.
2. **Recording, replay and Export all in the OS?** Recommend: yes (other apps read trips, and
   Export all is the exit guarantee). Alternative: they move with the Trips app.
3. **Crash SOS a system service?** Recommend: yes. Alternative: part of the Security app.
4. **Audio focus and the call session in the OS?** Recommend: yes. Alternative: owned by the
   Media app.
5. **One repo per app?** Recommend: yes, created only when work starts. Alternative: one
   `ostler-apps` monorepo for first-party apps.
6. **Map replaces Vehicles & Map?** Recommend: one Map app with friends' vehicles as a layer.
   Alternative: keep two apps.
7. **"App" as the user word?** Recommend: yes; "add-on" only for developers. Alternative: keep
   "add-on" in the UI.

## Changelog

- 2026-10-07 — v0.1, proposed: drafted from the owner's direction of 2026-10-07.
