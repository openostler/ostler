---
title: "App model — one shell, features as apps declared by a manifest — design"
area: specs
status: draft
version: 0.10
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/app_model.md, references/research/ui/ovms_ui.md, references/research/ui/head_unit_ui.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, references/research/obd_telematics_apps.md, references/research/app_teardown_speedometer.md, references/research/driver_distraction_rules.md, CONSTITUTION.md]
summary: >
  Draft for owner review; not built before U1. One shell (launcher, status strip, driving states and landing, auth and session, the VSS data stream, the app registry, the safety-gate client, approval surfaces, theming and layout classes) hosts features as apps declared by a JSON manifest: id, version, shell API range, source repo, entry, requirements (VSS signals, capability-manifest devices and node variants, product tier), slot contributions, actions used with category and tier, a driving rule per view (moving views only as shell templates), hosts, permissions, i18n and icons. Core apps (Diagnose, Logs, Security, Network, and Decode lab shown only in service mode) stay in the platform repo and fill the five destinations; optional apps (Cameras, Social, add-on module apps) live in their own repos now (ADR-0034 amendment) and ship as pinned npm packages bundled at build time, or as declarative-only apps that a device's capability manifest can suggest. Community code may later run only in sandboxed iframes on web hosts (brain, cloud, browser), never in the native phone app; signed runtime modules stay a later option behind an ADR. v0.2 adds the phone build: the Capacitor app follows Home Assistant's Companion model with a server reachable and ships a bundled shell, core and declarative apps for Ostler Diagnostics alone and offline, with fixed native features and no runtime third-party code, plus a dated store-policy check and its risks. Not separate PWAs; apps never bypass the gate and never touch the car except through the shell's action API. Defines the U1 seams, a later phase UA, tests and open questions. v0.3 (owner answers, 2026-10-06): Network is a core app that absorbs More → Devices (the whole cluster page, device pages inside it, slots `more:network`, `sheet:link` and `network:device:<id>`); each device's firmware-served page stays outside the app model with a read-only peer view; pairing, revoking and uplink changes are owner-role API operations, not a new action category. v0.4 (owner answers, 2026-10-06; ADR-0039, ADR-0040): §13 is accepted (action fields `runs_on`, `needs_brain`, `queueable`, `expires_max_s`; `needs_brain` views with a "Needs the Brain" placeholder; `permissions.wake`; power records in the cluster model; SDK wake and expiry options and a read-only `power` service with leases; apps wake only through action requests and held views, with no `wake()` call; "Don't ask again" per user and device, local links only); the `product` value `lite` becomes `diagnostics`. v0.6–v0.7 (amendment §14, approved by the owner on 2026-10-07 ("approve all"); ADR-0042 accepted): small core (shell, Diagnose, Trips (was Logs), Network, Security once a node exists) and add-ons (Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations, Decode lab as a developer add-on); More → Add-ons catalogue (no remote catalogue yet, Q7) and an empty-state Home; phone add-ons bundled or declarative only; SDK `trips`, `faults`, `sharing` and the data-class registry; templates incl. the new `call` (UI spec §3.5, §12.1); new slots `more:social`, `more:vehicles` and `home:card`; exit guarantee; no driving score in core. v0.8–v0.9 (amendment §15, DMD round, approved by the owner on 2026-10-07 ("approve all", DMD round)): widgets that add-ons register for Home and Drive (`contributes.widgets`, user-placed, Moving only through a shell template), Drive menu rows (`contributes.drive_menu`), slots `home:widget`, `drive:widget`, `more:hub` (the one official Community hub), `more:navigation` and `more:phone`, pinnable `more:*` pages, `short_list` as a widget Moving template, SDK `widgets`, `input`, `drive_menu` and `calls` (the one shell-owned call session). Amended 2026-10-07 (OS round): amended by the app UI model spec (§3, §4, §14.1 and §14.2; ADR-0046).
---

# App model — design (draft)

> **Amended 2026-10-07 (OS round), approved by the owner on 2026-10-07 ("approve all", OS
> round):** amended by the [app UI model spec](2026-10-07-app-ui-model-design.md): §3 (app
> kinds) and §14.1 (the core list) give way to the empty OS
> ([ADR-0046](../decisions/adr-0046-empty-os-every-app-an-add-on.md)); §4's manifest goes to
> schema 2; §14.2's More → Add-ons gives way to the drawer, Settings → Apps and the Store.

**Status:** draft v0.9 for owner review; §14 is an amendment approved by the owner on
2026-10-07 ("approve all"), and §15 an amendment approved by the owner on 2026-10-07
("approve all", DMD round) (Q1, Q2, Q6 and Q9–Q14 answered 2026-10-06; Q5 reopened and Q7
answered 2026-10-07; §11). Q3, Q4 and Q8 are open. **Do not build before U1** (UI spec §10): U1 only
leaves the seams in §9. Evidence: [app model research](../references/research/ui/app_model.md).
It refines the [UI architecture spec](2026-10-06-ui-architecture-design.md) (approved), which
stays the authority for layout classes, the strip, destinations, driving states, the
capability manifest and the tiers; this spec changes none of them.

## 1. Context and goals

The owner asked for **one shell** with features as **apps declared by a manifest**: core apps
(Diagnose, Logs, Security, Network) in the platform repo, optional apps (Social, Cameras,
Decode lab, add-on module apps) possibly in their own repos, and **not separate PWAs**, because
safety and lockouts need one shell.

Goals: (1) the nav, Home cards, strip chips and device pages are built from declarations, not
hard-coded (UI spec §3.4 already requires `slot`, `order`, `requires`, `trust`); (2) an app
can be developed and released outside the platform repo; (3) no app can weaken a lockout,
draw an approval or reach the car other than through the gate; (4) the same build runs on the
head unit, phone (Capacitor), desktop and cloud (ADR-0032 §11), offline.

**Non-goals.** Separate PWAs or windows per app. A public app store. Third-party code loaded
at runtime in v1, and inside the native phone app ever (§7.1). Apps that define new car actions (actions come from packs and device
manifests). User-arranged dashboards (deferred by ADR-0018 Q6).

## 2. The shell's responsibilities

The shell is the platform UI minus every feature screen; Home stays a shell surface built from
roles (UI spec §5.4) plus app contributions. The shell alone owns:

| Area | The shell owns | Apps may |
|---|---|---|
| **Launcher and nav** | the five destinations (rail or bottom bar, UI spec §3.3–3.4), More → Apps grid, deep links, route names | contribute to a destination or the Apps grid via the manifest |
| **Status strip** | every chip, its order by severity, the sheet it opens (§3.2) | supply data for the one device-slot chip their device claims |
| **Driving states and landing** | Parked / Idling / Moving from the server, landing by state, Drive mode, service mode (§3.4–3.5) | read the state; declare per-view rules (§4.4) |
| **Auth and session** | sign-in, the kiosk session, roles and categories, service-mode entry (ADR-0029, ADR-0033) | read the effective categories |
| **Data stream** | one SSE stream now, MQTT/VSS later (AsyncAPI); the visible-signals subscription (U3 polling rule) | subscribe to declared VSS paths |
| **App registry** | discovery, compatibility check, install/enable, activation, error boundaries | — |
| **Safety-gate client** | the action API, confirms, precondition checklists, wizards, the ActiveTestBanner with Stop, phone-approval cards, refusals | request an action by id and read its outcome |
| **Theming and layout** | design tokens, layout class, night mode, target sizes, `Intl` formatting | use tokens and the layout class |
| **Replay** | whole-app read-only replay (ADR-0010); every action refused | render the replayed snapshot as live data |

## 3. App kinds and where they live

| App | Kind | Repo | Fills |
|---|---|---|---|
| **Diagnose** | core | `ostler` | Diagnose destination: systems, areas, Scan all (UI spec §4.2–4.3) |
| **Logs** | core | `ostler` | Logs destination: timeline, Analysis, replay, Rewind |
| **Security** | core | `ostler` | Security destination: alarm, events, tracker map, geofences |
| **Network** | core | `ostler` | More → Network: the whole cluster (UI spec §3.7): devices and every device page, transports and link health, role holders, uplinks and metering, remote access, certificates and pairing, node AP (ADR-0028, ADR-0032, ADR-0037, ADR-0038; §12) |
| **Cameras** | optional, first-party | `ostler-app-cameras` | Security → Clips, live-camera chip, HU-wide secondary pane, reverse template |
| **Social** | optional, first-party | `ostler-app-social` | More → Apps; groups and rides (ADR-0029 P4) |
| **Decode lab** | core, enabled only in service mode | `ostler` (Q5, answered) | More → Developer (UI spec §8.4); hidden unless service mode (the experimental/dev mode, UI spec §3.5) is on |
| **Add-on module apps** | optional; declarative first | the module's repo | More → Network → *device* (slot `network:device:<id>`), Home card, strip device slot (UI spec §6) |

Core apps are ordinary apps with `trust: core`, so the registry is exercised by five users from
day one (rule of two). Decode lab's manifest adds a `requires.mode: "service"` rule, so the
registry hides it unless service mode is on, and it leaves with service mode when Moving.
Optional apps live in their own `ostler-app-<x>` repos now (Q1; ADR-0034 amendment). Garage, Integrations, Preferences, Privacy and About stay shell
pages under More; Devices is part of the Network app (§12).

## 4. The app manifest

`ostler-app.json` at the root of the app package, validated by
`schemas/app-manifest.schema.json` (JSON Schema 2020-12, ADR-0017; described here, created in
phase UA).

### 4.1 Shape

```jsonc
{ "$schema": "https://ostler.tech/schemas/app-manifest.schema.json",
  "schema": 1,
  "id": "ostler.cameras",                  // reverse-DNS-like; "ostler." reserved for first party
  "name": "Cameras", "version": "1.3.0",   // SemVer
  "shell": "^1.0",                         // shell API range (cf. engines.vscode, grafanaDependency)
  "source": { "repo": "https://github.com/openostler/ostler-app-cameras",
              "license": "AGPL-3.0-or-later", "publisher": "openostler" },
  "trust": "first_party",                  // core | first_party | community
  "entry": { "kind": "bundled", "module": "@ostler/app-cameras" },  // bundled | declarative | iframe | module
  "hosts": ["head_unit", "phone", "desktop", "cloud"],
  "requires": {
    "product": ["ostler"],                 // ostler (with a Brain) | diagnostics (node alone)
    "devices": [{ "kind": "camera" }],     // matched against capabilities.devices
    "node_variants": [],                   // e.g. ["guardian"]
    "signals": ["Vehicle.Speed"],          // VSS paths (ADR-0016) it subscribes to
    "api": ["sessions.read", "clips.read"] // OpenAPI operation tags it may call
  },
  "activation": ["onDestination:security", "onDevice:camera"],
  "contributes": {
    "slots": [ { "slot": "destination:security", "view": "clips", "order": 40 },
               { "slot": "strip:device", "chip": "camera_live" },
               { "slot": "pane:secondary", "view": "live" } ],
    "suggest": { "device_kind": "camera" }
  },
  "actions": [ { "id": "camera.record", "category": "accessories", "tier": 1 } ],
  "views": [
    { "id": "clips", "driving": { "parked": "full", "idling": "full", "moving": false } },
    { "id": "live",  "driving": { "parked": "full", "idling": "full",
                                  "moving": { "template": "camera_live", "below_kmh": 10 } } } ],
  "permissions": { "data": ["video"], "notifications": false, "storage": "app" },
  "i18n": { "default": "en", "messages": "i18n/{locale}.json" },
  "icons": [ { "symbol": "videocam" }, { "src": "icon.svg", "purpose": "monochrome" } ] }
```

### 4.2 Field rules

- **`id`** is unique and stable; `ostler.*` is reserved for apps published by the project.
  **`version`** is SemVer; **`shell`** is a SemVer range the registry checks before loading.
- **`trust`** is assigned by the registry from the signer, never self-declared to gain power:
  `core` only for apps built from the platform repo.
- **`requires`** decides visibility, as UI spec §6 decides device chrome: no camera, no Cameras
  app chrome. Signals and devices are matched against the capability manifest (§5 there);
  `product: ["ostler"]` hides an app on Ostler Diagnostics alone (no Brain; the value
  `diagnostics`, formerly `lite`, ADR-0039). `mode: "service"` shows an app only in service mode
  (Decode lab).
- **`actions`** lists capability-manifest action ids (or `<device>.*` patterns) the app may
  request, each with its **category and tier copied from that manifest**. The registry refuses
  a manifest whose pair differs from the capability manifest or breaks ADR-0033's caps. The
  list only narrows: the gate still decides on role, share, token, transport and state.
- **`views[].driving`**: `full`, `false` (locked, "Available when parked") or a **shell
  template** (§4.4). `moving` may only name a template. A missing rule means `false` for
  Moving and Idling.
- **`permissions.data`** uses the token data classes of ADR-0029 (`location`, `video`,
  `audio`); `identity` does not exist, because the VIN never reaches the UI (ADR-0036).
- **`i18n`** keys are namespaced by app id; units format through `Intl` in the shell.
- **`icons`** prefer a Material Symbols name (U1 icon set) with an SVG fallback.
- **Slot names** are `destination:<id>` (for example `destination:security`), `strip:device`,
  `pane:secondary`, `more:network` (the Network page under More), `sheet:link` (a row in the
  Link chip's sheet, UI spec §3.2) and `network:device:<id>` (a device's page inside Network,
  where add-on module apps contribute), plus, by the approved §14.7 platform change,
  `more:social` (the Social add-on's page under More), `more:vehicles` (the Vehicles & Map
  add-on's page under More) and `home:card` (a card on Home). New slots are added only by a
  platform change.

### 4.3 Hosts

`head_unit` (HU-7, HU-9/10, HU-wide), `phone` (Capacitor and browser), `desktop`, `cloud`
(Ostler Cloud serving the app remotely: every action is a remote path, read-only unless the
install override is set, ADR-0033 §6). An app absent from a host is not offered there. The
native phone app is a host with fixed limits (§7.1): it never offers third-party code
(`iframe` or community `module` apps); first-party apps served by a brain or the cloud are fine.

### 4.4 Driver-safe templates

While Moving, the shell renders **only templates**, filled with the app's data and drawn by
the shell at the layout class's sizes (the Android for Cars and CarPlay model; research §1):

| Template | Content limit | Example |
|---|---|---|
| `tiles` | up to 6 values, ≥ 56 px digits | a sensor-node app's EGT and boost |
| `telltale_list` | ≤ 6 rows, ≤ 30 characters a line, one level | a module's warnings |
| `value` | one value with unit and state | oil pressure |
| `setpoint` | one setpoint, ± buttons, a toggle | HEVAC temperature (Comfort) |
| `camera_live` | one stream, speed-limited | reverse, underbody below 10 km/h |
| `arm` | arm button and state (never disarm) | Security arming |

Templates have no text entry, no scrolling list beyond the limit and no typed confirm.
Unknown speed counts as Moving on head units (ADR-0018 Q5). Templates are added to the shell
only by a platform change.

## 5. Lifecycle and isolation

**States:** available (in the build or a signed bundle) → **compatible** (shell range,
`requires`, host) → **enabled** (by an owner, per install; per vehicle is Q8) → **activated**
on an activation event → suspended (view locked by the driving rule, or replay) → disabled.
Contributions render from the manifest without activating the app.

**Isolation by kind:**

| Kind | Code runs | Isolation | When |
|---|---|---|---|
| `bundled` | in the shell's realm, lazy chunk | review + pin; lint forbids direct `fetch` to action routes and imports of shell internals | UA |
| `declarative` | no app code; shell tiers 1–2 (UI spec §5.3) | by construction | with U4/U5 |
| `iframe` | `sandbox="allow-scripts"`, opaque origin, `postMessage` RPC, a scoped token per app | by construction; no cookies, no DOM access | later, ADR first; the only kind for community code (Q2), web hosts only (brain, cloud, browser), never in the native phone app or the shell's origin |
| `module` | runtime `import()` with hash-pinned import map, signed | signature only | later, ADR first, maybe never |

Every app view sits in an **error boundary**; a crash shows "App stopped" and the shell keeps
running. Apps never render inside the strip, Drive mode or an approval layer.

## 6. The shell ↔ app API

One TypeScript package, `@ostler/app-sdk` (npm scope per ADR-0014), versioned with SemVer as
the `shell` range. Data types are **generated from `api/openapi.yaml` and
`api/asyncapi.yaml`** (ADR-0035); the SDK adds only shell services. Bundled apps call it
directly; iframe apps get the same interface over `postMessage`.

| Service | Surface |
|---|---|
| `vehicle` | active `vid`, the capability manifest filtered to the app's `requires`, its `etag` |
| `signals` | `subscribe(paths)` → `{value, ts, confidence, stale}` (VISS-shaped, U3); feeds the visible-signals subscription |
| `driving` | current state and changes (read-only) |
| `actions` | `request(id, params)` → a handle with status events; the shell runs the confirm, checklist, wizard or phone approval; the app never sees a grant |
| `session` | user, effective categories, kiosk flag, service mode (read-only) |
| `nav` | `open(route, params)` by route name; never raw paths |
| `logs` | query sessions and events (Logs API), `mark()` |
| `ui` | toast, sheet (non-approval), layout class, tokens, `t()` |
| `storage` | a per-app key-value namespace (server-side for state that must persist) |

Car-touching or gated effects exist **only** in `actions.request`, which posts to the API's
action route, which the brain gate and the node gate re-check (ADR-0032, ADR-0033 §3). Apps
send `X-Ostler-App: <id>` so the audit log names them.

## 7. Optional apps from their own repos

- **Packaging.** An app repo publishes an npm package `@ostler/app-<name>` holding
  `ostler-app.json`, an ESM build (React as a peer dependency), types and `i18n/`. Releases are
  GitHub releases with SBOM and provenance (ADR-0017). Licence: AGPL-3.0-or-later for apps
  bundled into the shell (ADR-0012); third-party licences are Q4.
- **Repo rule (Q1, answered 2026-10-06).** Optional UI apps (Cameras, Social, add-on module
  apps, community apps) may live in their own `ostler-app-<x>` repos now, on the grounds of
  release cadence and contributors ([ADR-0034](../decisions/adr-0034-repo-boundaries.md),
  amendment of 2026-10-06). The shell and the core apps, Decode lab included, stay in
  `ostler`.
- **Bundling (UA).** The platform's `ui/package.json` pins each enabled optional app exactly;
  Dependabot proposes bumps; CI validates every manifest, checks the `shell` range and runs
  the app's contract tests. The build emits one lazy chunk per app; disabled apps cost only
  their manifest. The Pi stays Node-free (ADR-0004).
- **Versioning.** The shell API follows SemVer; a breaking SDK change bumps the major, and the
  registry refuses an app outside its range with "Needs Ostler x.y".
- **Signing.** Bundled apps are trusted through the pin and review. For later kinds a release
  carries a file manifest of SHA-256 hashes and a detached ed25519 signature (the Grafana
  pattern); the device keeps the publisher keys, editable only locally by an owner (Q3).
- **Install and enable.** In UA, "install" means enabling a bundled app (owner role, More →
  Apps), applying `requires` and `hosts`. Fetching apps from a catalog is a new outbound path
  and needs an ADR (ADR-0017).
- **Suggested by a device.** A node or add-on capability manifest (ADR-0027 §9, ADR-0032 §6) may
  carry `app: {id, min_version}`. When such a device appears, the shell offers "Use the
  Climate app" if that app is bundled and compatible; otherwise the generated device view
  (UI spec §5.3 tier 1) is used. A device works with **no app**; nothing auto-installs.
- **Community apps (Q2, answered 2026-10-06).** Community code may load, but only as
  `iframe` apps: an opaque origin, a scoped revocable token narrowed to its manifest, never
  the shell's origin. That kind is a web-host feature (brain, cloud, a browser); the native
  phone app never offers it (§7.1). It still waits for its own ADR (§9).

### 7.1 Amendment (2026-10-06): the phone build

Owner decision of 2026-10-06 (Q9), refining ADR-0032 §11 ("one app in three places").

1. **Companion model with a server.** With a brain (Ostler Brain) or Ostler Cloud reachable, the
   Capacitor app loads the shell and every app (core, optional and runtime-loaded first-party
   apps) from that server, as a browser would, in the way Home Assistant's Companion app shows
   the user's own server frontend. New apps need no store update; the native app never changes
   its own features at runtime (App Store 2.5.2, Play policy).
2. **Bundled fallback for Ostler Diagnostics alone and offline.** With no brain and no internet the phone talks
   straight to the node, which serves only its small manifest-generated page. The app
   therefore ships a bundled shell, the core apps (Diagnose, Logs, Security, Network) and the
   declarative add-on apps (manifest plus generated views). **Ostler Diagnostics works fully
   offline with only the node.**
3. **Native features, fixed in the binary:** BLE and local Wi-Fi to the node, notifications,
   location, background tasks and approval of Tier 2–3 actions over local links within
   ADR-0033 §6. They give the app real native value (App Store 4.2).
4. **No runtime third-party code in the native app.** `iframe` community apps stay a
   web-host feature (brain, cloud, browser); when the shell runs inside the native app the
   registry does not offer them, even when the server serves them. Live updates to the
   bundled web code are for bug fixes only, never new features.
5. **Versions.** The bundled and the server-served shells must both satisfy each app
   manifest's `shell` range. With a server reachable the phone prefers the server's newer
   shell; offline it falls back to the bundled one.
6. **Store policy check (live, 2026-10-06; detail in the
   [research note §7](../references/research/ui/app_model.md#7-store-policy-check)).** Apple
   2.5.2 still bars downloaded code that adds or changes features; 4.2 still asks for more than
   a repackaged website; Play bans downloaded native code but exempts JavaScript in a webview,
   provided runtime-loaded code cannot cause policy breaches; Home Assistant's app is listed as
   a client for the user's own server, with native sensors, location, notifications and
   widgets; Capgo and Capacitor present web-layer updates as allowed but within the reviewed
   purpose, with no guarantee. Nothing found contradicts the plan. **Risks:**
   - **Capacitor `server.url` is documented as development-only** (and `allowNavigation`
     likewise). Loading a server shell needs a production design: a native webview navigation
     the wrapper controls, or the bundled shell fetching server-served app chunks. Phase UA
     must pick one before the phone build.
   - **Native bridge exposure.** Apple 4.7.2 forbids exposing native APIs to downloaded HTML5
     mini apps without permission, and Play forbids a JavaScript interface on untrusted or
     unverified URLs. The bridge must answer only the paired brain or cloud origin over HTTPS
     (ADR-0021), and server-loaded apps reach native features only through the shell's SDK.
   - **Reviewer judgment.** "Changes features" (2.5.2) is decided per review; the Home
     Assistant precedent helps but is not a ruling. The store listing should say the app is a
     client for the user's own Ostler.
   - **Ionic Appflow live updates** are being wound down (sunset reported for 2027-12-31);
     do not depend on it. Capgo or a self-hosted updater fits the bug-fix-only rule.

## 8. Explicit non-goals and hard lines

- **Not separate PWAs.** One Web App Manifest, one service worker, one origin, one strip.
- **Apps never bypass the gate.** No app action reaches the car except through
  `actions.request` → the API → the node gate; MQTT, HA and raw-frame routes are not in the SDK.
- **Apps never draw approvals** or cover the strip, Drive mode or the ActiveTestBanner.
- **No app defines a car action, safety tier or category**; it only lists existing ones.
- **No custom view while Moving**; only shell templates (§4.4).
- **No AI path.** An MCP client is not an app; ADR-0030 keeps its own surface.

## 9. Migration: not before U1; the seams U1 leaves

U1 builds the shell (UI spec §10) with today's screens in the five destinations. To let apps
slot in later at no extra cost, U1 should leave these seams and nothing more:

1. **Destination registry shaped like `contributes.slots`**: a typed array of entries
   (`id`, `slot`, `order`, `requires`, `trust`, lazy `component`), replacing `SCREENS`.
2. **A typed shell context** (`useShell()`: driving, layout class, vehicle, signals, actions,
   nav, session, toast) split from screen state, so screens stop reading App internals.
3. **One action path**: every action through `useAction` and `confirm.ts`; a lint rule forbids
   other calls to action routes.
4. **A lazy chunk and an error boundary per destination**, as the map chunk does today.
5. **Strip chips as data descriptors**, rendered by the shell.
6. **Route names** for `goTo`, not tab ids or paths.
7. **CSP `script-src 'self'`** and no inline scripts, so the shell can later refuse unknown
   code.
8. **Namespaced i18n keys and design tokens** only (U1 brings tokens).

**Phase placement.** U2 adds per-view `driving` rules and the first templates with the
lockouts. U3's capability manifest feeds `requires`. U5 brings declarative device apps and
device suggestions. A new phase **UA (apps)**, after U3 and before or with U5's camera work,
ships the manifest schema, `@ostler/app-sdk`, the registry, core apps moved behind manifests
and the first optional app (Cameras) from its own repo, bundled. Iframe and runtime-module
kinds wait for a real third-party app and an ADR.

## 10. Tests

- **Schema:** every manifest validates; a missing category, a tier below its category cap or a
  pair that differs from the capability manifest is refused (ADR-0033 manifest test).
- **Registry:** an app outside its `shell` range, host or `requires` is not offered; disabling
  an app removes all its contributions; "no device, no chrome" for device apps.
- **Driving:** with a Moving fixture (and unknown speed on a head-unit class) only template
  views render; a custom view shows "Available when parked"; templates hold their limits.
- **Gate:** an app calling an action route directly fails lint; `actions.request` for an
  action not in the app's list is refused by the shell, and the server refuses it regardless.
- **Approval surfaces:** no app can mount inside the strip, Drive mode or approval layers
  (DOM test); a throwing app view leaves the strip and nav working.
- **Replay:** apps render replayed data; every action is refused (ADR-0010).
- **Layout:** Playwright and axe per layout class with a test app enabled (U1 sizes).
- **Contract:** SDK types regenerate from OpenAPI/AsyncAPI with no diff (ADR-0035).
- **Literal guard:** no app or core screen names a pack, module or device id (ADR-0018).

## 11. Open questions for the owner

1. ~~**Repo split.**~~ **Answered 2026-10-06:** own `ostler-app-<x>` repos now for optional
   apps (cadence, contributors); the shell and core apps stay in `ostler`. ADR-0034 amended (§7).
2. ~~**Third-party code.**~~ **Answered 2026-10-06:** yes, in sandboxed iframes only (opaque
   origin, scoped token, never the shell's origin), on web hosts only, never in the native
   phone app (§5, §7, §7.1). Signed runtime modules are not adopted for community code.
3. **Signing keys.** Only the project key, or may an owner add a publisher key locally?
4. **Licences.** Must bundled apps be AGPL-compatible (yes by ADR-0012), and may a closed app
   run as an iframe under the commercial licence?
5. ~~**Decode lab.**~~ **Answered 2026-10-06:** a core app in `ostler`, enabled only in
   service mode, the experimental/dev mode (§3; UI spec §8.4). **Reopened and answered
   2026-10-07:** a developer add-on (off by default, service mode only), code staying in
   `ostler` (§14.1, ADR-0042).
6. ~~**Network** as a core app under More, covering uplinks, remote access and pairing.~~
   **Answered 2026-10-06:** yes, widened to the whole cluster and absorbing Devices (Q10, §12).
7. ~~**Catalog.** A future app catalog is a new outbound path: wanted, and from where?~~
   **Answered 2026-10-07:** not now; Available lists bundled and device-suggested add-ons
   only, and a remote catalogue waits for its own ADR (§14.2, ADR-0042 §5).
8. **Enablement scope.** Per install (recommended) or per vehicle?
9. ~~**Phone app.**~~ **Answered 2026-10-06:** Companion model with a server; a bundled
   shell, core and declarative apps for Ostler Diagnostics alone and offline; fixed native features; no runtime
   third-party code (§7.1, which records the store-policy check and its risks).
10. ~~**Network as a core app** that absorbs Devices, rather than two pages?~~ **Answered
    2026-10-06:** yes; Network is a core app that absorbs More → Devices (§12.1).
11. ~~**Device pages** outside the app model?~~ **Answered 2026-10-06:** yes; the
    firmware-served device page stays outside the app model (§12.2).
12. ~~**Owner operations** (pairing, revoking, uplinks): API calls or a new category?~~
    **Answered 2026-10-06:** owner-role API operations (ADR-0029 §5), not a new ADR-0033
    category (§12.1).
13. ~~**Wake by apps.**~~ **Answered 2026-10-06:** only through action requests and held
    views; no `wake()` call (§13.3).
14. ~~**"Don't ask again"** for brain wakes.~~ **Answered 2026-10-06:** stored per user and
    device, honoured on local links only (§13.3).

## 12. The Network app and device pages (accepted 2026-10-06)

*Accepted by the owner on 2026-10-06 (Q6, Q10–Q12). Context: UI spec §3.7,
[ADR-0037](../decisions/adr-0037-role-holders-and-handover.md), [cluster view
research](../references/research/cluster_view.md).*

**12.1 Network as a core app that absorbs Devices.** The Network row of §3 grows from
"uplinks, remote access, pairing, node AP" to the whole cluster page of UI spec §3.7:
devices (variant, firmware, addresses, reached via, health), transports and link health,
role holders, uplinks and metering, remote access, certificates and pairing. **Devices stops
being a shell page** (§3's last paragraph): the device list and each device page live inside
Network, and add-on module apps contribute to `network:device:<id>` instead of More → Devices.
It stays core because every product tier needs it and it renders the pairing flow, which
only the platform may ship.

```jsonc
{ "schema": 1, "id": "ostler.network", "name": "Network", "version": "1.0.0",
  "shell": "^1.0", "trust": "core",                   // assigned by the registry (§4.2)
  "source": { "repo": "https://github.com/openostler/ostler", "license": "AGPL-3.0-or-later",
              "publisher": "openostler" },
  "entry": { "kind": "bundled", "module": "@ostler/app-network" },
  "hosts": ["head_unit", "phone", "desktop", "cloud"],
  "requires": { "product": ["ostler", "diagnostics"], "devices": [], "node_variants": [],
                "signals": [],
                "api": ["cluster.read", "uplinks.read", "uplinks.write", "pairing.write",
                        "certs.read"] },
  "activation": ["onDestination:more"],
  "contributes": { "slots": [ { "slot": "more:network", "view": "cluster", "order": 10 },
                              { "slot": "sheet:link", "view": "roles_row" } ] },
  "actions": [],                                       // no car or device actions
  "views": [ { "id": "cluster", "driving": { "parked": "full", "idling": "full", "moving": false } },
             { "id": "roles_row", "driving": { "parked": "full", "idling": "full",
                                               "moving": { "template": "telltale_list" } } } ],
  "permissions": { "data": [], "notifications": true, "storage": "app" },
  "i18n": { "default": "en", "messages": "i18n/{locale}.json" },
  "icons": [ { "symbol": "lan" } ] }
```

- **No actions.** Pairing, revoking a certificate and changing an uplink are **owner-role API
  operations** (ADR-0029 §5), not ADR-0033 action categories; they are refused on remote
  paths (ADR-0033 §6) and checked by the device that holds them, never by the page. They
  are not a new action category (Q12).
- **`hosts: cloud`** renders read-only (§4.3).
- `cluster.read` returns the view each host builds from retained manifests, `status` and role
  claims (ADR-0037 §3); its schema lives with the module contract (ADR-0034).
- The `more:network`, `sheet:link` and `network:device:<id>` slot names are in the slot
  list (§4.2).

**12.2 The device's own page is a shell-less device page.** Each device's local web page
(ADR-0028 §7, ADR-0032 §6) is **not an app and not the shell**: it is served by the firmware
(`ostler-firmware`, ADR-0034), works with no brain and no phone app, and is generated from
the device's own capability manifest. It follows the shell's rules where they apply:
controls declare category and tier, every action is checked by that device's gate, nothing
is drawn for absent hardware. It gains a read-only **peer view**: the peers it sees by mDNS
and on its broker, their variant, firmware, health and role claims, each with a link to that
peer's own page. It never acts on a peer. When a full-app host is reachable, the page offers
"Open in Ostler" (a deep link to Network → *this device*). The peer view and the Network
page's Devices rows share one JSON shape so one test can check both.

**12.3 Changes made (v0.3):** §3's Network row and its "Garage, Devices, Integrations…"
sentence read as above; §3's add-on module apps row reads "More → Network → *device*"; the
slot names join §4.2; Q6 and Q10–Q12 are answered (§11). U5 carries the peer view and UA the
Network app.

## 13. Power states, wake and queued actions (accepted 2026-10-06)

*Accepted by the owner on 2026-10-06 (Q13, Q14; v0.4). Decision:
[ADR-0040](../decisions/adr-0040-power-states-and-wake.md); UI: UI spec §3.8 (accepted);
evidence: [power states research](../references/research/power_states.md).*

**13.1 Manifest additions.** Additive; old manifests stay valid.
- **Capability manifest actions** (UI spec §5.1) gain `runs_on`, `needs_brain`, `queueable`
  and `expires_max_s`. An app's `actions` list copies them as it copies category and tier
  (§4.2); the registry refuses a manifest whose copy differs, or that marks a Tier 2+ action
  `queueable`.
- **App views** gain `needs_brain: true` where the view needs a brain service (full Logs,
  replay, clips). With the brain asleep the shell renders a "Needs the Brain" card with **Wake**
  in the view's slot and does not activate the app; on Ostler Diagnostics alone the view is
  hidden by `requires.product` as today.
- **`permissions.wake`**: `["interactive"]` lets the app ask the shell to wake a device for a
  person's tap; `["background"]` (OTA, sync) is first-party only and subject to the budget. No
  permission means the app can never cause a wake.

```jsonc
"actions": [ { "id": "relay1.ch3", "category": "accessories", "tier": 1,
               "runs_on": "relay1", "needs_brain": false, "queueable": true, "expires_max_s": 300 } ],
"views":   [ { "id": "clips", "needs_brain": true,
               "driving": { "parked": "full", "idling": "full", "moving": false } } ],
"permissions": { "data": ["video"], "wake": ["interactive"] }
```

**13.2 Cluster model.** The `cluster.read` device rows and the device page's peer view
(§12.1–12.2) gain the device's retained `power` record: `state` (off, asleep, waking, awake,
held, shutting_down, offline), `class` (always, wakeable, check_in, none), `wake_paths`,
`next_checkin`, `leases` and `est_ma`, plus the arbiter's ledger (today's mAh against the
budget, the floor in force). One JSON shape for both, as §12.2 requires.

**13.3 SDK.**

| Service | Addition |
|---|---|
| `actions` | `request(id, params, { wake: "ask" \| "auto" \| "never", expires_in_s })`. The handle reports `waking`, `queued {expires_at}`, `running`, `done`, `expired`, `cancelled`, `refused {by, reason}`, `state_changed`; `handle.cancel()` |
| `power` (new) | `state(deviceId)` and `subscribe(deviceIds)` (read-only records above); `hold(deviceId, { until, reason })` returns a lease handle that the shell renews while the view is visible and releases on unmount or at the maximum (ADR-0040 §4.5) |

- **`wake: "ask"`** (default) lets the shell show the brain-wake sheet where one applies (UI
  spec §3.8: remote requests always; local requests wake without a sheet); `"auto"` is
  honoured only for module wakes (`needs_brain: false`) or after the user chose "Don't ask
  again", which is stored per user and device and honoured on local links only, so it never
  skips the remote sheet; `"never"` fails fast with `refused {reason: "asleep"}`.
- **There is no `wake()` call for apps.** A wake is always the side effect of an action
  request, a held view or a shell Wake button, so its purpose is known and checked.
- **The shell owns** the wake sheet, the queued list in the Link chip's sheet and every
  refusal; apps never draw them (§2, §8).

**13.4 Tests (added to §10).** A `needs_brain: false` request never wakes the brain (fake
arbiter); a queued request reports `expired` after its expiry and `state_changed` after a
driving-state change; a Tier 2 action marked `queueable` is refused by the registry; an app
without `permissions.wake` cannot cause a wake; leases are released on unmount; a
`needs_brain` view shows the placeholder, not the app, while the brain is asleep.

**Open questions added by this amendment** (answered 2026-10-06, §11):

13. ~~**Wake by apps:** only through action requests and held views (no `wake()`)?~~
    **Answered:** yes (§13.3).
14. ~~**"Don't ask again"** for brain wakes: per user and device, local links only?~~
    **Answered:** yes (§13.3; UI spec §3.8).

## 14. Amendment (2026-10-07), approved: ecosystem, add-ons, Trips and templates

*Approved by the owner on 2026-10-07 ("approve all"); where it differs, §14 overrides
§1–§13. Decision:
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md) (accepted);
map: [docs/ecosystem.md](../docs/ecosystem.md); evidence:
[OBD and telematics apps](../references/research/obd_telematics_apps.md),
[Speedometer/Odo teardown](../references/research/app_teardown_speedometer.md),
[driver-distraction rules](../references/research/driver_distraction_rules.md).*

**14.1 Core and add-ons (replaces §3's table).** Core (`trust: core`, repo
`ostler`): the shell, **Diagnose**, **Trips** (Logs renamed; id `ostler.trips`, slot
`destination:trips`), **Network**, and **Security** with `requires.devices: [{kind: "node"}]`.
Add-ons (`trust: first_party`, off by default, own repos): **Social** (`ostler-app-social`),
**Vehicles & Map** (`ostler-app-vehicles`), **Maintenance & Garage**
(`ostler-app-maintenance`), **Cameras** (`ostler-app-cameras`), **Integrations** (one
add-on per integration: RealDash CAN out, `ostler-app-lubelogger`, social integrations) and **Decode lab**, now a developer
add-on (`requires.mode: "service"`, label Developer; code stays in `ostler`), which reopens
Q5. The manifest gains `"kind": "core" | "addon" | "developer"`, assigned by the registry
like `trust`. No add-on contributes a `destination:*` slot of its own.

**14.2 Add-ons catalogue and empty Home (replaces "More → Apps" in §7).** More → Add-ons
(the top entry of More, UI spec §12.4), tabs **Installed** and **Available**, each card labelled Core, Add-on or Developer, with its
`requires` in words and the data classes it reads; core cannot be removed; enabling is an
owner-role operation. Available = bundled add-ons plus declarative add-ons a device suggests
(§7); no remote catalogue yet (Q7, answered). With no add-on enabled, Home shows one dismissible card
of suggestions ("Track maintenance", "Share drives with friends"); never on a head unit
while Moving.

**14.3 Phone boundary (narrows §7.1).** Background location, push and pairing are native and
fixed. Add-ons on the phone are bundled into a shell build (the phone's, or the Brain's
under §7.1) or declarative; no fetched code. Add-ons ask the shell for push and location
through the SDK, and the data-class registry decides who sees the result. One store app per
platform; Android Auto, CarPlay and watch companions are later surfaces of that binary,
each specced against its platform category first (CarPlay Driving Task: no live gauges, no
maintenance; Android Auto: IoT). `hosts` gains `carplay`, `android_auto` and `watch` only
with that spec.

**14.4 SDK (additive).** `logs` becomes **`trips`** (trip summary index, recordings, events,
`mark()`; odometer and engine-hours history, estimated when the car does not report them);
new read-only **`faults`** (per-system faults and new-fault events, for "fault code seen"
reminders); new read-only **`sharing`** (`audience(dataClass)` from the data-class registry;
the app never sets precision or audience for another user); `notify` (push through the
native feature, rate-limited, never message content on a head unit while Moving).
`permissions.data` names classes from the **data-class registry** (accounts spec §14, approved),
and an add-on may register new classes in `contributes.data_classes` (accounts spec §14.1); each
starts in ghost. This also supersedes §4.2's "token data classes of ADR-0029" wording.

**14.5 Templates and lockouts (summary; authority: UI spec §3.5 as amended by §12.1, approved).** The
template set becomes `telltale_list`, `value`, `setpoint`, `camera_live`, `arm`, plus `map`,
`media`, `tiles` (the Drive-layout grid: VSS paths with normal/warning/critical levels),
`alert_card`, `short_list` and **`call`**, with limits per
[driver_distraction_rules §7.2](../references/research/driver_distraction_rules.md#72-template-limits-recommended);
task depth ≤ 3 on head units; new templates only by platform proposal citing each limit's
source. Views may declare `"passenger_view": true` only for vehicle state, own
location/route or a driving camera (UK reg 109); everything else offers **Open on phone**.
**`call`**: one active audio call or push-to-talk channel; a name ≤ 30 characters (no photo),
state and timer, ≤ 3 buttons (answer/decline, mute/end, or hold to talk); never video,
never message text; group calls show a count, not a list.

**14.6 Hard lines added to §8.** **Exit guarantee:** Trips has Export all (CSV, GPX, VBO),
every add-on that keeps user data exports it in an open format, and nothing in core depends
on an Ostler-run server. **No driving score in core;** scores and leaderboards only in the
Social add-on, opt-in, speed never ranked, never exportable to insurers.

**14.7 New slots (platform change).** §4.2's slot names gain **`more:social`** (the Social
add-on's page under More; [Social spec](2026-10-07-social-addon-design.md)),
**`more:vehicles`** (the Vehicles & Map add-on's page under More) and **`home:card`** (a
dismissible card on Home, never on a head unit while Moving;
[Vehicles & Map spec](2026-10-07-vehicles-and-map-addon-design.md)). As with every slot, a
contribution needs the add-on enabled and passes the registry's `requires` check.

**Decisions for the owner (this amendment).** Answered 2026-10-07: approved as recommended.
Each recommendation is the decision; each alternative was not chosen.

1. **Accept §14?** Recommend: yes, with ADR-0042. Alternative: keep §3 and decide per feature.
2. **Decode lab (reopens Q5): developer add-on?** Recommend: yes, code in `ostler`.
   Alternative: keep it a core app shown in service mode.
3. **`call` template now or with Social?** Recommend: define it now, build with Social.
   Alternative: add it by platform proposal when Social is specced.
4. **Manifest `kind` field?** Recommend: registry-assigned like `trust`. Alternative: derive
   it from `trust` and `requires.mode` with no new field.
5. **Companion hosts?** Recommend: no `carplay`/`android_auto`/`watch` host until each has a
   spec. Alternative: reserve the names now.

## 15. Amendment (2026-10-07, DMD round), approved: widgets, Drive menu rows, input and new slots

*Approved by the owner on 2026-10-07 ("approve all", DMD round), v0.9; added in v0.8. §15 adds to §4.1–§4.2 (manifest and slot names), §5 (isolation) and §6 (SDK) and
changes nothing else. Designs it serves:
[Drive modes and editing](2026-10-07-drive-modes-and-editing-design.md) (approved; the widget
picker, Home and Drive editing, rail pinning),
[shell input](2026-10-07-shell-input-design.md) (approved; `ShellInput`, the Drive menu),
[navigation add-on](2026-10-07-navigation-addon-design.md) (approved) and
[Ostler Community](2026-10-07-community-hub-design.md) (approved) and the
[Phone & Comms add-on](2026-10-07-phone-comms-addon-design.md) (approved). Templates and their limits are
unchanged (§14.5; UI spec §12.1). Revised the same day (DMD round) for the owner's "the entire
UI is editable, with no fixed icons": apps supply only default icons and names, users may
re-icon, rename, hide or replace any app widget or page, and core pages may be displaced from
the rail but stay reachable (15.1, 15.4, 15.7, 15.8; decision 3 revised, 6–7 added). Revised
again the same day (DMD round, cross-spec reconcile): `short_list` joins the widget `moving`
set (Phone & Comms decision 12), a `more:phone` slot, a `calls` SDK service for the one
shell-owned call session (Social §13 C1), and `more:hub` follows the closed, single-instance
hub of the community hub spec v0.2 (15.1, 15.2, 15.4, 15.5, 15.7; decision 4 revised, 8–10
added).*

**15.1 `contributes.widgets` (the widget contract).** An app declares the widgets a user may
place on Home or in a Drive mode. Placement is always the user's (or a preset's); an app never
places itself.

```jsonc
"contributes": {
  "widgets": [
    { "id": "ptt",                               // unique within the app; full id "ostler.social/ptt"
      "title": "Push to talk",                   // default name, ≤ 30 characters (i18n key allowed); the user may rename
      "icon": "record_voice_over",               // default icon: a Material Symbols catalogue name; the user may re-icon
      "description": "Hold to talk to your ride", // ≤ 60 characters, shown in the picker
      "surfaces": ["drive", "home"],             // where it may be placed
      "sizes": ["medium", "wide"],               // small | medium | wide | hero
      "view": "ptt_widget",                      // the Parked view (a views[] id)
      "data": ["audio"],                         // data classes read; ⊆ permissions.data
      "signals": [],                             // VSS paths read; ⊆ requires.signals
      "settings": { "type": "object", "properties": {} },   // JSON Schema subset for the settings sheet
      "refresh_hz": 1,                           // ≤ 4 while Moving whatever is declared
      "moving": { "template": "call" },          // false | { template: tiles|value|map|media|call|setpoint|short_list }
      "passenger_view": false,                   // §14.5 rule
      "requires": { "ride": true } } ] }         // extra visibility conditions, as top-level requires
```

**15.2 Field rules.**
- **`moving`** is `false` (the widget shows "Available when parked" in a Moving section and
  the layout validator refuses it there) or names **one existing template**; the shell draws
  the template from data the app publishes (15.5), never the app's own view. A widget whose
  template is `tiles` or `value` counts against the ≤ 6 tile budget; `map`, `media`, `call` and
  `short_list` count as panes (Drive-modes spec §4.3). **`short_list`** (added in the
  reconcile revision, Phone & Comms decision 12) keeps its UI spec §12.1 limits: ≤ 6 rows, one
  level, ≤ 30 characters a row, a glyph badge at most; a row tap routes through the shell like
  any template button (a favourite starts a call through the `calls` service, 15.5), never into
  the app's own view.
- **`data` and `signals` only narrow** `permissions.data` and `requires.signals`; the
  registry refuses a widget that asks for more than its app. What a widget receives is
  filtered by the data-class registry (§14.4) like any other read.
- **`settings`** is a JSON Schema subset (string with `maxLength` ≤ 30, number with bounds,
  boolean, enum, and the shell's `x-ostler-signal` picker for a VSS path); the shell draws the
  settings sheet; apps draw no settings UI for widgets.
- **`sizes`** are the shell's (Drive-modes spec §4.2); the shell picks the type steps and
  enforces the class minimums. Text in a widget is plain, ≤ 30 characters a line in templates.
- A widget never renders in the strip, an approval layer or a confirm sheet (§5 rule), and
  widgets carry **no actions** of their own: template buttons (`media`, `call`, `setpoint`)
  route through the shell, and anything that reaches the gate goes through `actions.request`
  in a Parked view.

**15.3 `contributes.drive_menu` (Drive menu rows).** An app may offer rows for ShellInput's
Drive menu (a `short_list`: ≤ 6 rows, one level, ≤ 30 characters a row, driver-safe only;
shell input spec §6). The field is an array; an entry is a row id string (label from the i18n
key `drive_menu.<id>`, a navigation or display choice handled by the app through the SDK) or
an object `{ "id", "label", "action": "<capability-manifest action id>" }` naming an existing
Moving-allowed action, with its category and tier copied from `actions[]` as §4.2 requires.
Example (navigation add-on): `"drive_menu": ["mute_voice", "skip_point", "end_nav"]`. Rows that
would need a confirm sheet while Moving are not offered; which six show, and in what order, is
the display's setting, changed Parked only.

**15.4 Slot names (adds to §4.2 and §14.7; platform change).**

| Slot | Meaning | From |
|---|---|---|
| `home:widget` | a user-placed widget on Home | Drive-modes spec §7.2 |
| `drive:widget` | a user-placed widget in a Drive mode face | Drive-modes spec §7.4 |
| `more:hub` | More → Community (`ostler-app-hub`): tabs Discover · Forum · Help · Mine, plus Wiki links (vehicle pages open in the hub's wiki); the add-on's hub URL is fixed to the one official, Ostler-run hub (no linking several hubs; a developer build may set a staging URL) | [community hub spec v0.2](2026-10-07-community-hub-design.md#152-in-shell-add-on-ostler-app-hub) §4, §15.2 |
| `more:navigation` | the Navigation page under More (`ostler-app-navigation`) | navigation add-on spec |
| `more:phone` | More → Phone (`ostler-app-phone`, Phone & Comms): Favourites, Recents, Contacts, Keypad (Parked only), Messages, Settings | [Phone & Comms spec](2026-10-07-phone-comms-addon-design.md#10-ui-per-layout-class-and-driving-state) §10, §12 |

`home:widget` and `drive:widget` are filled only through `contributes.widgets` (an entry in
`contributes.slots` naming them is refused). **Every `more:*` page is pinnable** by the user
to any rail slot (Drive-modes spec §7.3; More always keeps one of the five): a pin is a user
shortcut, not an app contribution, so §14.1's "no add-on contributes a `destination:*` slot"
stands; a pinned page keeps its own driving rule. A `more:*` page declares its default `title`
(i18n key) and `icon` (catalogue name) in its `contributes.slots` entry; both are defaults
only (15.8). `home:card` (§14.7) stays for app-suggested, dismissible cards.

**15.5 SDK additions (§6).**

| Service | Surface |
|---|---|
| `widgets` | `publish(widgetId, instanceId, data)` → the template data for Moving (shape per template, validated by the shell; ≤ the widget's `refresh_hz`, capped at 4 Hz Moving); `config(instanceId)` → the user's settings; `onPlaced`/`onRemoved` events; a widget's Parked view receives `{ size, layoutClass, config, driving }` as props |
| `input` | read-only, as the shell input spec (§11) describes it: `requestFocus(elementId)` within the app's own zone, and intent events (`up`, `down`, `left`, `right`, `ok`, `back`, `zoom_in`, `zoom_out`, `ptt`) delivered only to a view the user has **engaged**; no raw key codes, no binding changes, no events while another zone or a sheet holds focus |
| `drive_menu` | `onSelect(rowId)` and `setState(rowId, text ≤ 12 characters)` for the app's own rows ("On", "Muted") |
| `calls` | the one **call session**, owned by the shell (Social §13 C1): `request({ source, label, kind: "phone" \| "ostler" \| "ptt" })` → a session handle or "busy" (a second ringing call is offered as call waiting, never a second `call` template); `state` (subscribe: ringing, active, held, waiting, ended); `end(handle)`; `onAction(handle, "answer" \| "decline" \| "mute" \| "hold_answer" \| "swap" \| "audio")`. The shell draws the `call` template, holds the one audio focus, pauses PTT during a call, writes the one local call log (Social §13 C4) and drives the comms chip; an app supplies the label (≤ 30 characters) and the media, never the UI. Needs `permissions.calls`; first-party apps only until a review path exists |

**15.6 Isolation (adds to §5).** Bundled widgets render in the shell's realm inside their own
error boundary ("Widget stopped"; the rest of the grid keeps running); a widget that throws
three times in a drive is replaced by its placeholder until Parked. Community widgets exist
only as `iframe` apps on web hosts (Q2): one sandboxed frame per placed widget, Parked only,
with `publish` over `postMessage` for Moving. Declarative apps may declare widgets whose
`view` is a shell tier-1 view (a signal tile or gauge over their `signals`). The shell, not
the app, measures and caps refresh, size and text.

**15.7 Tests (adds to §10).** Registry: refuses a widget whose `data`/`signals` exceed its
app's, a `moving` template outside the set, a `contributes.slots` entry naming
`home:widget`/`drive:widget`, a `drive_menu` action whose category or tier differs from the
capability manifest. Shell: a published payload over the template limits is truncated and
reported, never drawn; `publish` faster than 4 Hz is coalesced while Moving; the `input`
service delivers nothing to an unengaged view; a crashing widget leaves the other widgets and
Drive mode running. User overrides (15.8): the registry refuses an app `icon` outside the
Material Symbols catalogue and any app field that tries to set `locked`, `pinned`,
`required` or a rail position; the SDK exposes no read or write of the user's overrides;
pinning an add-on page in place of a core destination leaves that destination opening from
More → Pages, by its deep link and by its landing rule; disabling the add-on frees the slot and
keeps the user's overrides for it; no app widget or page can hide, cover or replace a safety
surface. Reconcile additions: a `short_list` widget payload over 6 rows or 30 characters is
truncated and reported; two `calls.request` sessions never render two `call` templates (the
second is call waiting); a `calls` request from an app without `permissions.calls` is refused;
`ostler-app-hub` exposes no setting that changes its hub URL outside a developer build.

**15.8 User overrides, replacing core destinations and safety surfaces (revised, DMD
round).**

- **Apps supply defaults only.** An app's widgets and pages carry a default `title` (i18n key
  or text, ≤ 30 characters) and a default `icon` (a name from the shell's curated Material
  Symbols catalogue; no images, URLs or emoji). The **user** may re-icon, rename (Drive-modes
  spec §7.6 limits), hide or replace any app widget or page; the override is stored in the
  user's layout, not in the app, survives app updates and is dropped only by Reset layout or
  **Use defaults**. An app cannot lock its placement, name or icon, cannot read or change the
  user's overrides, and is told only `onPlaced`/`onRemoved` (15.5).
- **Hiding an app page** moves it from More → Pages to More → Hidden pages; the app stays
  enabled and its deep links still open. Turning an app off stays at More → Add-ons (§14.2).
- **"Replace" for core destinations.** The rail's five slots are the user's (More always one of
  them). Putting an add-on page in a slot a core destination held **displaces** that
  destination; it does not replace it. A displaced core destination (Home, Diagnose, Trips,
  Security; Network and the rest of More are unaffected): stays registered with its
  `destination:*` slot and routes; is listed under More → Pages with its icon and name; keeps
  its deep links and its landing rule (Drive when Moving, Security when Parked and armed,
  Diagnose in service mode); and, for Home, stays the default landing page and the root of
  `back` (Drive-modes spec §7.3). No app page can take a core destination's route, id, landing
  rule or data, and a pinned app page gains no driving permission it did not have. Core pages
  cannot be uninstalled (§14.2), so "replaced" always means "one tap away in More".
- **Safety surfaces are not removable.** The fault telltale (strip chip, fault sheet, Home
  warnings card), alarm alerts (Security chip while a node is present, Security alert card,
  `alert_card`) and the Moving templates with their limits belong to the shell. A user may move
  them; no app, widget, page, pin or layout file can remove, hide, cover, rename or re-icon them
  (Drive-modes spec §8.1 R3). App widgets never render in the strip (15.2), and no app
  contributes strip chips.

**Decisions for the owner (this amendment).**

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen.

1. **Accept `contributes.widgets` with user-only placement?** Recommend: yes. Alternative:
   let an app propose a default placement on Home (like `home:card`), which the user can remove.
2. **Moving data path for widgets?** Recommend: `widgets.publish` to a shell template only.
   Alternative: let first-party (`trust: first_party`) widgets render their own view while
   Moving after review (faster to build, weaker guarantee).
3. **Pinnable `more:*` pages instead of add-on destinations? (revised)** Recommend: yes, user
   pins in any rail slot within the five-slot cap (More always one of the five); a displaced
   core destination stays one tap away under More → Pages with its routes and landing rule
   (15.8). Alternative: pins only in the middle slots, Home and More locked (the first draft).
4. **New slot and manifest names? (revised)** Recommend: `home:widget`, `drive:widget`,
   `more:hub`, `more:navigation`, `more:phone`, `contributes.widgets`,
   `contributes.drive_menu`, SDK `widgets`, `input`, `drive_menu` and `calls`, all in this
   platform change. Alternative: add each with its own add-on spec when that add-on is built.
5. **Community widgets.** Recommend: iframe only, web hosts only, Parked only, Moving through
   `publish`. Alternative: no community widgets until the iframe kind has its own ADR (Q2).
6. **App icons and names as defaults only?** Recommend: yes; the user may re-icon (catalogue
   only), rename, hide or replace any app widget or page, and apps cannot lock or read those
   overrides. Alternative: apps may mark a widget's icon as fixed (brand recognition), still
   renamable and hideable.
7. **What does "replace" mean for a core destination?** Recommend: displacement only: the core
   page leaves the rail, stays registered, under More → Pages, with its deep links and landing
   rule, and Home stays the landing page and `back` root. Alternative: an add-on page may also
   take Home's role as landing page when the user chooses it (a "Start on" preference).
8. **`short_list` as a widget Moving template? (new, reconcile)** Recommend: yes, add it to the
   `moving` set with its UI §12.1 limits (≤ 6 rows, ≤ 30 characters), counted as a pane, row
   taps routed through the shell; it lets the Phone favourites widget work while Moving (Phone &
   Comms decision 12). Alternative: keep the set as drafted; favourites reach Moving only
   through a Drive menu row.
9. **One shell-owned call session as an SDK `calls` service? (new, reconcile)** Recommend: yes,
   `calls.request`/`state`/`end`/`onAction`, the shell drawing the one `call` template, owning
   audio focus, PTT pause, the call log and the comms chip (Social §13 C1); first-party apps
   only at first. Alternative: each add-on raises its own `call` template through `widgets` and
   the shell shows the newest (no call waiting, no shared log).
10. **`more:hub` bound to the official hub only? (new, reconcile)** Recommend: yes, the add-on's
    hub URL is fixed to the one Ostler-run hub (community hub spec v0.2, decision B 7); More →
    Community shows Discover · Forum · Help · Mine with Wiki links; a developer build may point
    at staging. Alternative: v0.1's model, a device may link several hubs and the user picks
    one per publish.

## Changelog

- 2026-10-07: v0.10, amended (OS round, approved by the owner on 2026-10-07, "approve
  all"): §3, §4, §14.1 and §14.2 amended by the app UI model spec (ADR-0046).
- 2026-10-07: v0.9, **§15 approved by the owner on 2026-10-07 ("approve all", DMD round)**:
  renamed "Amendment (2026-10-07, DMD round), approved"; its decisions 1–10 answered as
  recommended (alternatives not chosen); the Drive-modes, ShellInput, navigation, Community
  and Phone & Comms specs cited as approved. Stays draft: Q3, Q4 and Q8 are open.
- 2026-10-07: v0.8 revised in place (DMD round, cross-spec reconcile), still pending the
  owner: `short_list` added to the widget `moving` set (Phone & Comms decision 12); slot
  `more:phone`; SDK `calls` for the one shell-owned call session (Social §13 C1); `more:hub`
  reads More → Community (Discover · Forum · Help · Mine, plus Wiki links) on the one official
  hub (community hub spec v0.2); tests added; decision 4 revised, decisions 8–10 added.
- 2026-10-07: v0.8, **proposed amendment §15 (DMD round)**, pending the owner: the widget
  contract `contributes.widgets` (surfaces, sizes, data classes and signals, settings schema,
  `moving` template), Drive menu rows `contributes.drive_menu`, slots `home:widget`,
  `drive:widget`, `more:hub` and `more:navigation`, pinnable `more:*` pages, SDK `widgets`,
  `input` and `drive_menu`, isolation and tests; decisions 1–5 of §15.
- 2026-10-07: v0.7, **§14 approved by the owner on 2026-10-07 ("approve all")**, with
  ADR-0042 accepted: §14 renamed "Amendment (2026-10-07), approved"; its decisions answered
  as recommended; the catalogue at More → Add-ons; one add-on per integration; new slots
  `more:social`, `more:vehicles` and `home:card` (§14.7, §4.2); Q5 reopened and answered
  (developer add-on), Q7 answered (no remote catalogue yet). Stays draft: Q3, Q4 and Q8 are
  open.
- 2026-10-07: v0.6, **proposed amendment §14**, pending the owner (ADR-0042, proposed): core
  is the shell, Diagnose, Trips (Logs renamed), Network and Security once a node exists;
  add-ons (Social, Vehicles & Map, Maintenance & Garage, Cameras, Integrations, Decode lab as
  a developer add-on, reopening Q5); Settings → Add-ons catalogue and an empty-state Home;
  the phone boundary; SDK `trips`, `faults`, `sharing`, `notify` and the data-class
  registry; the template set with `call`, summarised from UI spec §3.5; exit guarantee and no
  driving score in core.

- 2026-10-06: v0.1, first draft from the [app model research](../references/research/ui/app_model.md):
  shell responsibilities, the app manifest, driver-safe templates, lifecycle and isolation
  kinds, the shell ↔ app API, optional apps from their own repos, U1 seams and phase UA.
- 2026-10-06: v0.2, owner answers. Q1: optional apps in their own repos now (ADR-0034
  amended). Q2: community code only in sandboxed iframes, web hosts only. Q5: Decode lab is a
  core app shown only in service mode. Q9: §7.1 adds the phone build (Companion model with a
  server, bundled fallback for Lite and offline, fixed native features, no runtime third-party
  code, shell version rule) and a live store-policy check with its risks. Stays draft: Q3, Q4,
  Q6, Q7 and Q8 are open.
- 2026-10-06: proposed amendment §12, pending owner answers (no version change): Network as a
  core app that absorbs More → Devices, its manifest, the firmware-served device page with a
  read-only peer view, and open questions 10–12.
- 2026-10-06: v0.3, owner answers on networking. §12 is accepted: Network is a core app
  that absorbs More → Devices (its §3 row widened to the whole cluster page of UI spec §3.7;
  add-on module apps contribute to `network:device:<id>`); the firmware-served device page
  stays outside the app model, with a read-only peer view; pairing, revoking and uplink
  changes are owner-role API operations, not a new category. §4.2 lists the slot names,
  `more:network`, `sheet:link` and `network:device:<id>` included. Q6 and Q10–Q12 answered.
  Stays draft: Q3, Q4, Q7 and Q8 are open.
- 2026-10-06: proposed amendment §13, pending owner answers (no version change): action
  fields `runs_on`, `needs_brain`, `queueable`, `expires_max_s`; `needs_brain` views with a
  "Needs the hub" placeholder; `permissions.wake`; per-device power records in the cluster
  model; SDK wake and expiry options on `actions.request`, a read-only `power` service with
  leases; tests and open questions 13–14 (ADR-0040, proposed).
- 2026-10-06: v0.4, owner answers on power states and the product family (ADR-0039,
  ADR-0040). §13 is accepted: action fields `runs_on`, `needs_brain`, `queueable` and
  `expires_max_s`; `needs_brain` views with a "Needs the hub" placeholder;
  `permissions.wake`; per-device power records in the cluster model; SDK wake and expiry
  options on `actions.request` and a read-only `power` service with leases. Q13 (apps wake
  only through action requests and held views; no `wake()`) and Q14 ("Don't ask again" per
  user and device, local links only) answered; the brain-wake sheet shows for remote
  requests only. The `product` value `lite` becomes `diagnostics`, and "Lite" reads Ostler
  Diagnostics. Stays draft: Q3, Q4, Q7 and Q8 are open.
- 2026-10-06: v0.5, product name per the ADR-0039 amendment: "Ostler Hub" is now **Ostler Brain**; "hub" (our compute box) reads "Brain"; the "Needs the hub" placeholder reads "Needs the Brain"; the `product` value `ostler` is unchanged and means a Brain is present.
