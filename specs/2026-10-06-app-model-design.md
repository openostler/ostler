---
title: "App model — one shell, features as apps declared by a manifest — design"
area: specs
status: draft
version: 0.2
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md, references/research/ui/app_model.md, references/research/ui/ovms_ui.md, references/research/ui/head_unit_ui.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0030-ai-native-mcp-server-and-authoring-skill.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, CONSTITUTION.md]
summary: >
  Draft for owner review; not built before U1. One shell (launcher, status strip, driving states and landing, auth and session, the VSS data stream, the app registry, the safety-gate client, approval surfaces, theming and layout classes) hosts features as apps declared by a JSON manifest: id, version, shell API range, source repo, entry, requirements (VSS signals, capability-manifest devices and node variants, product tier), slot contributions, actions used with category and tier, a driving rule per view (moving views only as shell templates), hosts, permissions, i18n and icons. Core apps (Diagnose, Logs, Security, Network, and Decode lab shown only in service mode) stay in the platform repo and fill the five destinations; optional apps (Cameras, Social, add-on module apps) live in their own repos now (ADR-0034 amendment) and ship as pinned npm packages bundled at build time, or as declarative-only apps that a device's capability manifest can suggest. Community code may later run only in sandboxed iframes on web hosts (brain, cloud, browser), never in the native phone app; signed runtime modules stay a later option behind an ADR. v0.2 adds the phone build: the Capacitor app follows Home Assistant's Companion model with a server reachable and ships a bundled shell, core and declarative apps for Lite and offline, with fixed native features and no runtime third-party code, plus a dated store-policy check and its risks. Not separate PWAs; apps never bypass the gate and never touch the car except through the shell's action API. Defines the U1 seams, a later phase UA, tests and open questions.
---

# App model — design (draft)

**Status:** draft v0.2 for owner review (Q1, Q2, Q5 and Q9 answered 2026-10-06; §11). **Do not build before U1** (UI spec §10): U1 only
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
| **Network** | core | `ostler` | More → Network: uplinks, remote access, pairing, node AP (ADR-0028, ADR-0032) |
| **Cameras** | optional, first-party | `ostler-app-cameras` | Security → Clips, live-camera chip, HU-wide secondary pane, reverse template |
| **Social** | optional, first-party | `ostler-app-social` | More → Apps; groups and rides (ADR-0029 P4) |
| **Decode lab** | core, enabled only in service mode | `ostler` (Q5, answered) | More → Developer (UI spec §8.4); hidden unless service mode (the experimental/dev mode, UI spec §3.5) is on |
| **Add-on module apps** | optional; declarative first | the module's repo | More → Devices → *device*, Home card, strip device slot (UI spec §6) |

Core apps are ordinary apps with `trust: core`, so the registry is exercised by five users from
day one (rule of two). Decode lab's manifest adds a `requires.mode: "service"` rule, so the
registry hides it unless service mode is on, and it leaves with service mode when Moving.
Optional apps live in their own `ostler-app-<x>` repos now (Q1; ADR-0034 amendment). Garage, Devices, Integrations, Preferences, Privacy and About stay shell
pages under More.

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
    "product": ["ostler"],                 // ostler (brain) | lite
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
  `product: ["ostler"]` hides an app on Ostler Lite. `mode: "service"` shows an app only in service mode
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

1. **Companion model with a server.** With a brain (Ostler) or Ostler Cloud reachable, the
   Capacitor app loads the shell and every app (core, optional and runtime-loaded first-party
   apps) from that server, as a browser would, in the way Home Assistant's Companion app shows
   the user's own server frontend. New apps need no store update; the native app never changes
   its own features at runtime (App Store 2.5.2, Play policy).
2. **Bundled fallback for Lite and offline.** With no brain and no internet the phone talks
   straight to the node, which serves only its small manifest-generated page. The app
   therefore ships a bundled shell, the core apps (Diagnose, Logs, Security, Network) and the
   declarative add-on apps (manifest plus generated views). **Lite works fully offline with
   only the node.**
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
6. **Network** as a core app under More, covering uplinks, remote access and pairing: agreed?
7. **Catalog.** A future app catalog is a new outbound path: wanted, and from where?
8. **Enablement scope.** Per install (recommended) or per vehicle?
9. ~~**Phone app.**~~ **Answered 2026-10-06:** Companion model with a server; a bundled
   shell, core and declarative apps for Lite and offline; fixed native features; no runtime
   third-party code (§7.1, which records the store-policy check and its risks).

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
