---
title: "ADR-0046 — The empty OS: the platform is an operating system with no apps; every feature is an app in its own repo"
area: decisions
status: locked
version: 1.2
updated: 2026-10-07
depends_on: [decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0045-ux-first.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0031-generic-obd2-pack-in-platform.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, GOALS.md, CONSTITUTION.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-store-design.md, specs/2026-10-07-head-unit-apps-design.md, references/research/ha_architecture_addons.md, references/research/ha_integrations_dashboards.md, references/research/ha_companion_community.md]
summary: >
  Accepted 2026-10-07 ("approve all", OS round; decision list items 4–13 and 41–43): approved by the owner on 2026-10-07, every item as recommended; the round's full decision list (items 1–65) is the Decisions appendix here. The platform repo `ostler` becomes an empty operating system, like an Android phone with no apps. The OS holds system services (the gate client and node link, the module bus, the VSS stream, the integration loader where vehicle packs become integrations, the app runtime, permissions and data classes, users, accounts and roles, driving state and the Moving lockouts, the alert and notification pipeline, audio focus and the call session, input, recording and export, backups, updates, network) and the system UI (launcher with home pages, dock, drawer, widget host and edit mode; status strip; Connection sheet; system Settings; the Store client; the theme engine; first-run setup). Safety is never an app. Everything else is an app in its own repo: Diagnostics, Trips, Security, Maintenance, Social, Map, Navigation, Phone, Radio, Audio, Media, Camera, Decode lab, Community, the starter widgets and the default theme. Product flavours become preinstalled sets (amends ADR-0039): Ostler Diagnostics, Ostler Guardian (Security only; dock Security · Settings · App drawer) and Ostler Brain, a third named flavour; any non-system app can be uninstalled (on the phone, bundled apps are disabled, not deleted). Code in core today moves only after each app's UX brief is approved (ADR-0045); the ADR maps today's modules to target repos and gives the repo list (amends ADR-0034). Supersedes ADR-0042 §4's core list and §5's catalogue placement; reverses GOALS' "rebuilding media" non-goal. Risks: a bare OS shows nothing, so flavours, the bundled catalogue and first run matter; safety stays in the OS. Amended 2026-10-07 (openness round, ADR-0047): dock size and side, page caps, anchors, wallpaper, hardware access, Store disabling, ratings and paid items, sideloaded projection and streaming clients, icon packs, image export and app strip chips become defaults or options; safety is still never an app.
---

# ADR-0046 — The empty OS: every app is an add-on

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings"; [ADR-0047](adr-0047-openness-round.md)):**
> several OS-round items become defaults the user, owner or author can change; §2 (safety is
> never an app) and §9's safety lines are unchanged. See
> [Amendment](#amendment-2026-10-07-openness-round).

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07 ("approve all", OS round;
  decision list items 4–13 and 41–43), drafted from the owner's direction of the same day.
  It **supersedes in part**
  [ADR-0042](adr-0042-ecosystem-small-core-addons-are-the-product.md) (decision 4's core list
  and decision 5's catalogue at More → Add-ons) and **amends**
  [ADR-0034](adr-0034-repo-boundaries.md) (the repo list),
  [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (product flavours as
  preinstalled sets) and the [app-model spec](../specs/2026-10-06-app-model-design.md) §3 and
  §14.1. Each of those files carries a dated amendment note. Work follows
  [ADR-0045](adr-0045-ux-first.md) (UX first).
- **Designs (approved the same day):**
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
| **Radio**, **Audio**, **Media**, **Camera** | `ostler-app-radio`, `-audio`, `-media`, `-camera` | [head-unit apps](../specs/2026-10-07-head-unit-apps-design.md) | — |
| **Decode lab** | `ostler-app-decode-lab` | capture, auto-mapping, labelling, coverage | `ui/src/screens/` Capture, CoverageMap; `sniff/`; `web/sniffer.py` (the reference decoder and shared vectors stay in the OS) |
| **Community** | `ostler-app-hub` | as its approved spec | `community/` (empty package) |
| **Starter widgets** | `ostler-widgets-starter` | the starter widget pack and the preset dashboards | the presets of the Drive-modes spec |
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

- **Ostler Guardian** installs Security alone (the owner's own set, item 41); its dock is
  **Security · Settings · App drawer** (item 42).
- **Ostler Brain** is a third named flavour, the full install (item 43), not "Diagnostics plus
  a Brain".

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
| **Apps** | `ostler-app-<x>` | `-diagnostics`, `-trips`, `-security`, `-maintenance`, `-social`, `-map`, `-navigation`, `-phone`, `-radio`, `-audio`, `-media`, `-camera`, `-decode-lab`, `-hub`, `-alerts`, `-weather`, `-car`; later `-climate`, `-voice` |
| **Widget, theme and data packs** | `ostler-widgets-starter`, `ostler-theme-<x>`, `ostler-icons-<x>`, `ostler-wallpapers-<x>` | `ostler-widgets-starter`, `ostler-theme-default` |
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

### 10. GOALS changes (applied)

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
- GOALS and README are re-worded on acceptance; SCOPE and docs/ecosystem.md carry an
  amendment note and are re-worded when next revised.
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

## Owner decisions

Approved by the owner on 2026-10-07 ("approve all", OS round). Every item takes its
recommendation; no alternative was chosen. The items this ADR covers (numbers from the
[Decisions (OS round)](#decisions-os-round) appendix):

- **4:** the empty OS (§1–§3).
- **5:** recording, replay and Export all stay in the OS.
- **6:** Crash SOS is a system service.
- **7:** audio focus and the call session are in the OS.
- **8:** one repo per app, created only when its work starts (§7).
- **9:** one Map app (`ostler-app-map`) with friends' vehicles as a layer.
- **10:** "app" is the user's word; "add-on" only in developer docs (§8).
- **11:** the flavour sets of §5; on the phone "uninstall" disables a bundled app and deletes
  its data.
- **12:** `generic_obd2` stays bundled in the OS as the default integration (§4).
- **13:** the GOALS changes of §10.
- **41:** flavour app sets: Guardian is Security only; Diagnostics and Brain as item 11.
- **42:** the Guardian dock is Security · Settings · App drawer.
- **43:** the full install is a third named flavour, **Ostler Brain**.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", OS round; decision list items
4–10). Each recommendation below is the decision; each alternative was not chosen.

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

## Decisions (OS round)

The owner's decision list for the Android-style OS round: ADR-0045, this ADR, and the specs
[launcher and widgets](../specs/2026-10-07-launcher-and-widgets-design.md),
[app UI model](../specs/2026-10-07-app-ui-model-design.md),
[Store](../specs/2026-10-07-store-design.md) and
[head-unit apps](../specs/2026-10-07-head-unit-apps-design.md).

Answered 2026-10-07: approved as recommended ("approve all", OS round). Each recommendation
is the decision; each alternative (*alt*) was not chosen. The approval also covers the two
ADRs and the four specs.

### UX first (ADR-0045)

1. **UX first as a hard rule:** put it in the CONSTITUTION (brief → approval → UI on recorded fixtures → wiring), with a short review of the built screens against the brief before wiring. *alt:* a CLAUDE.md working rule only, approving the brief alone.
2. **Where briefs live:** all in the platform's `references/design/briefs/`, one register. *alt:* each repo keeps its own briefs, linked from the register.
3. **Synthetic fixtures:** allowed only for states that cannot be recorded safely (a refusal, an error, a red telltale), labelled `synthetic`. *alt:* recorded fixtures only, no exceptions.

### The empty OS (ADR-0046)

4. **Accept the empty OS:** `ostler` holds only system services and system UI; Diagnostics, Trips, Security and every other feature become apps. *alt:* keep ADR-0042's small core (Diagnose, Trips, Network, Security in core).
5. **Recording, replay and Export all:** stay in the OS (other apps read trips; Export all is the exit guarantee). *alt:* move with the Trips app.
6. **Crash SOS:** a system service. *alt:* part of the Security app.
7. **Audio focus and the call session:** in the OS. *alt:* owned by the Media app.
8. **Repos:** one repo per app, created only when its work starts. *alt:* one `ostler-apps` monorepo for first-party apps.
9. **Map and Vehicles & Map:** one Map app (`ostler-app-map`) with friends' vehicles as a layer. *alt:* keep two apps.
10. **User word:** "app" in the UI (drawer, Store, App info); "add-on" only in developer docs. *alt:* keep "add-on" in the UI.
11. **Flavour sets:** Diagnostics = Diagnostics, Trips, Security, starter widgets, theme; Guardian = Security and its widgets, theme; Brain = those plus Map, Media, Audio (Camera and Radio when hardware is found); on the phone "uninstall" disables a bundled app and deletes its data. *alt:* smaller sets (Diagnostics only on Ostler Diagnostics).
12. **`generic_obd2`:** stays bundled in the OS as the default integration. *alt:* its own pack repo like the others.
13. **GOALS changes:** drop the "rebuilding media" non-goal, add "projection receivers" as a non-goal, and replace the five-destination cap with the dock's per-class cap. *alt:* keep media as a non-goal and ship Radio and Audio as community apps only.

### Launcher and widgets

14. **Pages:** one set of home pages replaces Home and Drive modes; Drive mode is their Moving view. *alt:* keep Home and Drive modes as two sets.
15. **Driving set and switching:** at most 6 driving pages; switch while Moving by a long swipe, the D-pad or the page chip. *alt:* no page limit; page chip and D-pad only, no swipe.
16. **Dock anchors:** Home and Apps (the drawer), both movable, never removable; the head-unit Drive button retired. *alt:* Apps only, with Home reached by the page chip; keep the Drive button as an optional dock item.
17. **Dock size:** phone 5, HU-5 and HU-7 5, HU-9/10 6, HU-wide 7, tablet and desktop 7. *alt:* 5 on every class.
18. **Drop on occupied cells:** reflow as Android does, swap when there is no room. *alt:* swap only (the Drive-modes rule).
19. **Wallpaper while Moving:** plain `bg` behind Moving sections on driver-facing displays. *alt:* the wallpaper dimmed to 20 %.
20. **Widget `moving` field:** required and explicit in every widget manifest. *alt:* defaults to `false` when absent.
21. **Dashboard builder:** adds pages by default; replacing keeps a 7-day snapshot. *alt:* replace by default, with Undo.

### App UI model

22. **Schema-rendered pages:** the OS draws list, detail, form, tiles, map and media pages from data. *alt:* custom pages only.
23. **Setup and options flows:** config-flow style, drawn by the OS from app schemas and handlers. *alt:* each app draws its own setup.
24. **Notification channels:** `alarm` and `critical` reserved for the OS. *alt:* reviewed first-party apps may use `critical`.
25. **Network hosts:** each declared host is an outbound path, off until the owner allows it. *alt:* one "Internet" switch per app.
26. **Hardware access:** only `device` integrations from first-party or verified publishers, never car buses. *alt:* no hardware access outside the OS.
27. **App backends:** Python services on the Brain now; containers after their own ADR. *alt:* wait for containers.

### Store

28. **Store as a system app:** not uninstallable, Parked only on driver-facing displays. *alt:* an uninstallable first-party app.
29. **Catalogue signing:** TUF-style roles with Ed25519 and a small verifier of our own. *alt:* adopt a TUF library (a new dependency, its own ADR).
30. **Review levels:** System, First party, Verified publisher, Community (data objects and declarative items anywhere; code only as iframes on web hosts), Sideloaded. *alt:* first party and verified only, no community items.
31. **Bundled offline catalogue:** in the OS image and the phone binary. *alt:* in the OS image only.
32. **Online catalogue:** opt-in, off by default, one switch at first run, after its own ADR. *alt:* on by default with a notice.
33. **Ratings:** none (keep the hub's no-votes rule); show review level, badges, last update, known issues and the issue tracker. *alt:* stars and short reviews from Community accounts.
34. **Paid items:** none in v1; donation links allowed. *alt:* paid data objects through an external checkout on web hosts.
35. **Works with Ostler:** free until the criteria tests and partners exist. *alt:* a yearly fee from the start.

### Head-unit apps

36. **First tuner path:** an Si468x-based HAT or module (DAB+ decoded in hardware). *alt:* a USB SDR dongle first.
37. **Audio processing:** a software DSP on the Brain in v1; crossover and time alignment later with multichannel hardware. *alt:* an external DSP board only, or crossover in v1 limited to stereo.
38. **Projection:** not built; owners keep a projection-capable head unit beside Ostler; no uncertified receivers in the Store. *alt:* allow an uncertified community receiver as a sideload-only developer item.
39. **Streaming:** internet radio, podcasts, AirPlay and UPnP only; no unofficial clients for commercial services. *alt:* list such clients as community items.
40. **Car and Climate apps:** later, once two packs declare settings (rule of two). *alt:* build the Car app on the D2 alone now.

### From the designer brief

41. **Flavour app sets:** Guardian = Security only (the owner's own set). Diagnostics and Head unit sets as in item 11. *alt:* the owner lists each set.
42. **Guardian dock:** Security · Settings · App drawer. *alt:* Home · Security · Settings · Store · App drawer.
43. **Brain full install:** a third named flavour ("Ostler Brain"). *alt:* "Diagnostics plus a Brain".
44. **Dock on HU-wide:** driver side. *alt:* bottom.
45. **Carousel limits:** one flat row of home pages; one-tap cycle capped at 4, page list at 6 while Moving. *alt:* no caps.
46. **Exit to Home while Moving:** hide the row. *alt:* show Home with safe content only.
47. **"By signal" widget picker tab:** yes. *alt:* "By widget" only.
48. **Accent colours:** allow validated colour sets beyond cyan. *alt:* keep the one-accent rule.
49. **Icon packs:** glyph sets mapped to Material Symbols names, safety icons never change. *alt:* Material Symbols styles only.
50. **Images (wallpaper, image widget):** stored on the device only, never exported in layouts. *alt:* export them with layouts.
51. **Widget setup pages:** the OS draws them from the widget's schema; an app may add one custom page behind "More settings". *alt:* schema only.
52. **Who ships data widgets:** each app ships its own (Now playing from Media, Radio from Radio). *alt:* all in the starter pack.
53. **Clock and Weather:** part of the starter pack. *alt:* their own apps.
54. **Voice control:** lift the input spec's non-goal; local-first assistant later. *alt:* keep voice out.
55. **Default install:** "Ostler is the head unit" (Radio, Audio, Media) is offered, not the default. *alt:* make it the default.
56. **One Apps list** in Settings with integrations labelled. *alt:* separate Apps and Integrations tabs.
57. **Settings app in the drawer:** yes (settings-root). *alt:* Settings under More only.
58. **Maintenance strip chip:** no; apps add no strip chips. *alt:* allow it.
59. **Disarm:** Parked only. *alt:* also Idling with Park evidence.
60. **Remote disarm:** needs a fresh passkey. *alt:* the session is enough.
61. **Toasts while Moving:** dropped. *alt:* held until Parked.
62. **Store ratings:** none (also item 33). **Uninstall Security while armed:** refused until disarmed.
63. **Units:** a device default with a per-user override. *alt:* per vehicle only.
64. **Backups:** encrypted with a passphrase; include app data; never the VIN or the Brain's keys. *alt:* unencrypted local backups.
65. **First car checks before the copy is final:** the D2's diagnostic socket location and fuse, the reverse lamp wire for the camera trigger, BCU wires for door, bonnet and siren, and the original aerial and amplifier feed.

## Amendment (2026-10-07, openness round)

Approved by the owner on 2026-10-07 ("the repo has too many rules that limit freedom and
flexibility, this should be an open system", then "apply the loosenings"); recorded in
[ADR-0047](adr-0047-openness-round.md). The decision above stands except:

- **§1, Theme engine row** ("safety colours fixed"): themes follow
  [visual §13](../specs/2026-10-07-visual-design-system-design.md) and the
  [theme engine](../specs/2026-10-07-theme-engine-design.md). Safety items may be restyled,
  guarded by the Drive-mode render check, protected surfaces and required parts; they are never
  removed or covered (§2 unchanged).
- **§7, repo creation:** "created only when its work starts, with the owner asked first"
  applies to repos under the `openostler` organisation. Community authors create their own app
  repos freely.
- **§9:** "every data class starts in ghost" stays the default; a user may choose visible to
  household by default at setup (accounts spec §14.3). "No driving score in the OS" stays;
  apps may offer scores, opt-in.
- **Decision items amended:**
  - 1–3 (UX first): scoped to the project's own repos; a contributor guideline in
    CONTRIBUTING.md, not the CONSTITUTION; labelled synthetic fixtures allowed (ADR-0045
    amendment).
  - 13, 16, 17, 44 (dock): the per-class slot counts and the driver side are defaults; the
    user may change the count (overflow scrolls) and the side; Home and Apps anchors may be
    hidden while the recovery path stays (launcher §6.6).
  - 15, 45 (caps): at most 6 driving pages, 4 in the one-tap cycle and 6 in the page list are
    defaults the user may raise; the `short_list` row limit still applies while Moving.
  - 19 (wallpaper while Moving): superseded; the theme decides (visual §13).
  - 26 (hardware access): any publisher's `device` integration with the owner's consent, never
    car buses, the node link or the module bus.
  - 28 (Store): still not uninstallable, but the owner may disable it.
  - 33, 34, 62 (ratings, paid items): opt-in ratings and paid data objects on web hosts are
    allowed (Store §11); safety, decoding and input are never sold.
  - 38, 39 (projection, streaming): not built or listed, but sideloadable as community items.
  - 48, 49 (accent, icon packs): any accent; icon packs may restyle safety glyphs under the
    render check.
  - 50 (images): an opt-in export of wallpaper and image widgets with layouts.
  - 58 (strip chips): apps may add status-only chips the shell draws.
- **Unchanged:** §2 in full; items 24 (reserved channels), 30 (code only as iframes for
  community items), 59–60 (disarm rules), 64 (backups never hold the VIN or the Brain's keys).

## Changelog

- 2026-10-07 — v0.1, proposed: drafted from the owner's direction of 2026-10-07.
- 2026-10-07 — v1.0, accepted: approved by the owner on 2026-10-07 ("approve all", OS round;
  decision list items 4–13 and 41–43); every decision answered as recommended; §5 records the
  Guardian set and dock and the Ostler Brain flavour; §10 applied to GOALS; the round's full
  decision list added as the Decisions (OS round) appendix.
- 2026-10-07 — v1.1: repo names match the repos the owner created (`ostler-app-camera`,
  `ostler-app-decode-lab`, `ostler-widgets-starter`).
- 2026-10-07 — v1.2, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", ADR-0047): theme engine row, §7 repo creation, §9 ghost default and decision
  items 1–3, 13, 15–17, 19, 26, 28, 33–34, 38–39, 44–45, 48–50, 58 and 62 become defaults or
  options; §2 unchanged.
