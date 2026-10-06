---
title: "App model — one shell, features as apps declared by a manifest — design"
area: specs
status: draft
version: 0.4
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/app_model.md, references/research/ui/ovms_ui.md, references/research/ui/head_unit_ui.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, CONSTITUTION.md]
summary: >
  Draft for owner review; not built before U1. One shell (launcher, status strip, driving states and landing, auth and session, the VSS data stream, the app registry, the safety-gate client, approval surfaces, theming and layout classes) hosts features as apps declared by a JSON manifest: id, version, shell API range, source repo, entry, requirements (VSS signals, capability-manifest devices and node variants, product tier), slot contributions, actions used with category and tier, a driving rule per view (moving views only as shell templates), hosts, permissions, i18n and icons. Core apps (Diagnose, Logs, Security, Network, and Decode lab shown only in service mode) stay in the platform repo and fill the five destinations; optional apps (Cameras, Social, add-on module apps) live in their own repos now (ADR-0034 amendment) and ship as pinned npm packages bundled at build time, or as declarative-only apps that a device's capability manifest can suggest. Community code may later run only in sandboxed iframes on web hosts (brain, cloud, browser), never in the native phone app; signed runtime modules stay a later option behind an ADR. v0.2 adds the phone build: the Capacitor app follows Home Assistant's Companion model with a server reachable and ships a bundled shell, core and declarative apps for Ostler Diagnostics alone and offline, with fixed native features and no runtime third-party code, plus a dated store-policy check and its risks. Not separate PWAs; apps never bypass the gate and never touch the car except through the shell's action API. Defines the U1 seams, a later phase UA, tests and open questions. v0.3 (owner answers, 2026-10-06): Network is a core app that absorbs More → Devices (the whole cluster page, device pages inside it, slots `more:network`, `sheet:link` and `network:device:<id>`); each device's firmware-served page stays outside the app model with a read-only peer view; pairing, revoking and uplink changes are owner-role API operations, not a new action category. v0.4 (owner answers, 2026-10-06; ADR-0039, ADR-0040): §13 is accepted (action fields `runs_on`, `needs_brain`, `queueable`, `expires_max_s`; `needs_brain` views with a "Needs the hub" placeholder; `permissions.wake`; power records in the cluster model; SDK wake and expiry options and a read-only `power` service with leases; apps wake only through action requests and held views, with no `wake()` call; "Don't ask again" per user and device, local links only); the `product` value `lite` becomes `diagnostics`.
---

# App model — design (draft)

**Status:** draft v0.4 for owner review (Q1, Q2, Q5, Q6 and Q9–Q14 answered 2026-10-06; §11).
Q3, Q4, Q7 and Q8 are open. **Do not build before U1** (UI spec §10): U1 only
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
    "product": ["ostler"],                 // ostler (with a hub) | diagnostics (node alone)
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
  `product: ["ostler"]` hides an app on Ostler Diagnostics alone (no hub; the value
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
  where add-on module apps contribute). New slots are added only by a platform change.

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

1. **Companion model with a server.** With a brain (Ostler Hub) or Ostler Cloud reachable, the
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
   service mode, the experimental/dev mode (§3; UI spec §8.4).
6. ~~**Network** as a core app under More, covering uplinks, remote access and pairing.~~
   **Answered 2026-10-06:** yes, widened to the whole cluster and absorbing Devices (Q10, §12).
7. **Catalog.** A future app catalog is a new outbound path: wanted, and from where?
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
  replay, clips). With the brain asleep the shell renders a "Needs the hub" card with **Wake**
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

## Changelog

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
