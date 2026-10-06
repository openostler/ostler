---
title: "App model — one shell, apps by manifest: how car platforms, dashboards and editors host plugins, and what Ostler should copy"
area: references
status: stable
version: 1.1
updated: 2026-10-06
depends_on: [references/research/ui/ovms_ui.md, references/research/ui/head_unit_ui.md, references/research/ui/generated_ui.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md]
summary: >
  How comparable systems run features as apps inside one host: Android for Cars and CarPlay (categories, host-drawn templates, task limits, distraction-optimised tags), Home Assistant (integration manifests, custom panels and cards, HACS), Grafana (plugin.json, signed manifests, frontend sandbox), VS Code (contributes, activation events, capabilities), Backstage (extension tree, module-federation remotes) and OVMS web plugins. Compares four loading models for a Vite/React PWA (bundled at build time, runtime ES modules, sandboxed iframes, declarative-only) on trust, offline, Capacitor and safety. Recommends one shell that owns every safety surface, apps declared by a manifest, bundled-at-build plus declarative apps first, signed runtime modules and sandboxed iframes only later behind an ADR, and the shell drawing every while-Moving view from templates.
---

# App model — one shell, apps by manifest

**Question (owner, 2026-10-06):** can the UI become one shell (launcher, status strip, driving
states, auth, data stream, registry, safety) with features as apps declared by a manifest, core
apps in the platform repo and optional apps (Social, Cameras, Decode lab, add-on module apps) in
their own repos, without separate PWAs? This note gathers the prior art; the design is the
[app-model spec](../../../specs/2026-10-06-app-model-design.md). Web sources were checked on
2026-10-06 and are paraphrased, never copied.

## 0. Where Ostler is today

- `ui/src/screens/registry.ts` is a static array of eight public and three admin tabs; adding a
  tab is one row. `ui/src/vehicles/registry.ts` lets a pack register custom views by kind, and
  `main.tsx` is the composition root that imports each pack's views at build time.
- `ui/src/state/app.tsx` holds one `AppContext` that every screen reads (snapshot, catalog,
  fields, prefs, `goTo`, toast, fault sheet). Actions go through `useAction` and
  `components/confirm.ts`. Map code is already a lazy chunk (`import()`), guarded by a test.
- The UI spec (v0.4) already says destinations **register** with `slot`, `order`, `requires`
  and `trust` (§3.4, from OVMS), devices contribute to **slots** (§6), and the server and node
  gates enforce safety while the UI only adds friction (§7). So the app model is a
  generalisation of seams that are already decided, not a new direction.

## 1. Car platforms: the host draws the screen

### 1.1 Android for Cars (Android Auto, AAOS)

- **Categories gate entry.** The Car App Library supports a short list of app categories
  (navigation, points of interest, IoT, weather, plus media and messaging through their own
  APIs). The category is declared on the app's car service in the Android manifest, and store
  review checks that the app fits it. ([Car apps overview](https://developer.android.com/training/cars/apps),
  checked 2026-10-06.)
- **Templates, not views.** Apps hand the host a template (list, grid, pane, message, map,
  sign-in) filled with data; the host renders it with its own sizes, fonts and day/night theme.
  An app never draws free-form pixels on the car screen.
- **The host enforces the task budget.** At most five templates per task; the last must be one
  of a few terminal types; refreshes of the same template with the same main content do not
  count; popping the back stack restores quota; when the budget is spent the host shows an
  error and closes the app. List lengths are capped by the host per vehicle.
  ([Template restrictions](https://developer.android.com/training/cars/apps/library/template-restrictions).)
- **AAOS full apps.** Activities run while driving only if tagged
  `distractionOptimized` in the manifest; the platform checks the tag, not the behaviour, and
  pushes `CarUxRestrictions` (no keyboard, limited lists, no video) to apps that opt in.
  ([Driver distraction guidelines](https://source.android.com/docs/automotive/driver_distraction/guidelines).)

**Lesson.** Two layers: a **declared** capability (category, distraction-optimised tag) that the
host can check cheaply, and a **host-drawn** template set for anything shown while driving,
because a tag cannot prove behaviour. Our UI spec's Moving lockouts (§3.5) are the
`CarUxRestrictions` analogue; the missing piece is templates.

### 1.2 Apple CarPlay

- **Entitlement per category** (audio, video parked-only, messaging, navigation, a utility
  group covering EV charging, fuelling, parking and driving-task apps), granted by Apple on
  request. **Apple draws the UI**: apps fill templates; widgets and Live Activities appear on
  the dashboard with little extra code; CarPlay Ultra lets carmakers add vehicle features.
  ([CarPlay for developers](https://developer.apple.com/carplay/), checked 2026-10-06.)

**Lesson.** Same pattern, stricter: no custom driving UI at all, a category gate before any
code runs, and the host owns the dashboard where small app surfaces (widgets) appear. Our
status strip and Home cards play that role.

## 2. Dashboards and editors: manifests, contributions, trust

### 2.1 Home Assistant

- **Integration manifest** (`manifest.json`): `domain` (matches the folder), `name`,
  `version` (required for custom integrations, SemVer or CalVer), `integration_type`,
  `iot_class` (local or cloud, push or poll), `dependencies` and `after_dependencies`,
  `requirements` (pip pins), `codeowners`, `config_flow`, `quality_scale`, documentation and
  issue-tracker URLs. ([Integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/).)
- **Frontend extensions.** Custom cards and panels are JavaScript modules loaded by URL and
  registered as custom elements (`type: custom:<name>`). Resources under `/local` are served
  without authentication; there is **no signing and no sandbox** for cards.
  ([Registering resources](https://developers.home-assistant.io/docs/frontend/custom-ui/registering-resources/).)
  A custom **panel** may be a module or be **embedded in an iframe** (needed for React or
  clashing web components); by default the user must confirm before an external script loads,
  and a panel can be admin-only. ([panel_custom](https://www.home-assistant.io/integrations/panel_custom/).)
- **HACS** distributes community code from public GitHub repos with a `hacs.json` at the root;
  a frontend plugin is a `.js` file named after the repo (in `dist/` or the root); installs
  pick from the last five releases or the default branch. Curation is light: a repo
  description, topics and a README. ([HACS publishing](https://hacs.xyz/docs/publish/start),
  [plugins](https://hacs.xyz/docs/publish/plugin/).)

**Lesson.** HA shows the cost of trusting by default: a card runs with the full privileges of
the signed-in user, and the only gate is "the user added it". It works because HA's
dangerous effects sit behind server services, which matches our "the gate is on the node". The
iframe option exists because shared-realm code clashes (two React copies, custom-element name
collisions), not only for security.

### 2.2 Grafana

- **`plugin.json`**: `id`, `type` (app, panel, datasource, …), `dependencies.grafanaDependency`
  (a SemVer range on the host), `dependencies.plugins` (other plugins by type), `includes`
  (pages and dashboards an app plugin adds to navigation).
  ([plugin.json](https://grafana.com/developers/plugin-tools/reference/plugin-json).)
- **Signing.** A `MANIFEST.txt` lists SHA-256 hashes of every file and is signed; Grafana
  verifies it with a built-in public key and by default **refuses unsigned plugins** outside
  development mode; levels are private (bound to listed root URLs), community and commercial.
  ([Sign a plugin](https://grafana.com/developers/plugin-tools/publish-a-plugin/sign-a-plugin).)
- **Frontend sandbox** (public preview since 11.4): plugin frontend code runs in a separate
  JavaScript context so it cannot change UI outside its area or interfere with other plugins;
  per-plugin opt-in; Grafana's own signed plugins are excluded.
  ([Plugin frontend sandbox](https://grafana.com/docs/grafana/latest/administration/plugin-management/plugin-frontend-sandbox/).)

**Lesson.** The closest match to our needs: a host-version range, a signed file manifest, and
the experience that sandboxing in-page code is hard (still a preview after years). Signing
answers "who wrote this"; it does not answer "what can it do".

### 2.3 VS Code

- **Manifest** (`package.json`): `engines.vscode` (a host range, `*` not allowed),
  `contributes` (commands, views, menus, settings: static declarations the host renders before
  any code runs), `activationEvents` (lazy loading on a view, command or file type),
  `capabilities` (whether it works in **untrusted** or virtual workspaces) and `extensionKind`
  (run on the UI side or the workspace side).
  ([Extension manifest](https://code.visualstudio.com/api/references/extension-manifest).)

**Lesson.** Separate **contributions** (data the shell renders without loading the app) from
**activation** (code loaded only when needed), and let the app declare where it can run
(`extensionKind` ≈ our `hosts`) and in which trust mode (≈ our driving states).

### 2.4 Backstage

- The new frontend system: an app is an **extension tree**; plugins attach extensions to
  parent inputs; **route refs** let plugins link to each other without hard-coded URLs;
  **utility APIs** are typed interfaces the host provides.
  ([Architecture](https://backstage.io/docs/frontend-system/architecture/index).)
- Plugins are npm packages built into the app; **dynamic frontend plugins** are built as
  **module-federation remotes** and loaded at runtime by a feature loader, served by the
  backend's dynamic feature service.
  ([Module federation](https://backstage.io/docs/frontend-system/building-apps/module-federation).)

**Lesson.** Build-time plugins came first and stayed the default; runtime loading arrived
years later as an opt-in for installers who cannot rebuild. Typed host APIs and route refs are
worth copying now.

### 2.5 OVMS web plugins (reused from [OVMS UI §1.5](ovms_ui.md))

Page plugins and hook plugins are HTML fragments stored on the module, registered with a
menu, a label and an auth flag, installed by copy-paste or `plugin repo install`; there is no
signing or isolation, and missing hook points are fixed by asking upstream. The lessons we
already took: register pages, give every page named slots, and make capabilities data.

## 3. Loading models for a Vite/React PWA

| | **A. Bundled at build time** | **B. Runtime ES modules** | **C. Sandboxed iframe** | **D. Declarative-only** |
|---|---|---|---|---|
| What | App repos publish npm packages; the platform build pins and includes them, each as a lazy chunk | Shell `import()`s a URL (import map, or module federation via `@module-federation/vite`) | App runs in `<iframe sandbox="allow-scripts">` at an opaque origin; RPC over `postMessage` | Manifest + views as JSON, rendered by the shell's tiers (UI spec §5.3) |
| Trust | Code review and the pin; same realm, full user privilege | Signature + hash; same realm, full user privilege | Isolated: no cookies, no DOM access to the shell; only the bridge | Nothing executes; schema-validated data |
| Offline / SW | Precached with the shell | Must be precached; versions per install | Precachable, but a second document per app | Trivial |
| Capacitor (iOS) | Fine: shipped in the reviewed binary | Downloaded JS allowed only if it does not change the app's purpose (Apple DPLA 3.3.2, guideline 2.5.2); review risk | Same as B for remote content; local bundles fine | Fine |
| React / deps | One copy, shared | Needs shared singletons (federation) or each app ships its own | Each app ships its own runtime | None |
| Safety surfaces | Shell-owned only if enforced by lint and review | Same as A, enforced only by trust | Enforced by construction | Enforced by construction |
| Cost to build | Lowest | Medium (loader, signing, SW, versioning) | High (bridge, sizing, theming, focus, a11y) | Low once the generated tier exists (U4) |

Notes:
- **Integrity for runtime modules.** Import maps can carry an `integrity` map so a statically
  or dynamically imported module is checked against a hash before it runs; shipped in Chromium
  and WebKit in 2024 ([Shopify engineering](https://shopify.engineering/shipping-support-for-module-script-integrity-in-chrome-safari)).
  Module Federation 2.0 runs without webpack and has an official Vite plugin
  ([@module-federation/vite](https://cdn.jsdelivr.net/npm/@module-federation/vite@1.16.12/README.md)).
- **Iframe sandbox.** `allow-scripts` together with `allow-same-origin` lets the framed
  document remove its own sandbox, so never combine them; the `allow` attribute narrows
  camera, microphone and geolocation per frame
  ([MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe)).
- **Same-origin code is the user.** Our sessions are `__Host-` cookies (ADR-0029): any script in
  the shell's origin sends them. A bundled or runtime module can therefore call any route the
  user may call, and draw a fake confirm. That is acceptable for reviewed code, never for
  unknown code. An iframe at an opaque origin gets no cookie; the shell can hand it a
  **scoped, revocable token** (ADR-0029 tokens) narrowed to the categories its manifest
  declares.
- **The Web App Manifest** (W3C Working Draft, revised through 2026) describes one installable
  app with a `scope`; it has no notion of sub-apps or permissions, so it stays the shell's
  manifest only. Several PWAs would mean several scopes, several service workers and
  independent windows that cannot share one status strip or one lockout.

## 4. Driver safety: who enforces what

- **The gate is not in the UI.** Car-touching actions are checked on the node gate and add-on
  actions on the brain gate (ADR-0032, ADR-0033 §3), whatever the client. No app model choice
  weakens that; the risk an app adds is **UX safety** (distraction) and **approval spoofing**.
- **Distraction.** Android and CarPlay solved it the same way: the host draws driving UI from
  templates; a declared tag only admits an app to the restricted state. For us: an app may
  declare a view **moving-allowed only by naming a shell template** (tiles, telltale list,
  single value, setpoint, camera live), and the shell renders the template from the app's
  data. Custom components are hidden when Moving (and when speed is unknown on a head unit),
  replaced by "Available when parked".
- **Approval spoofing.** Confirms, checklists, wizards, the ActiveTestBanner with Stop and the
  phone-approval card must be **shell-owned layers** that apps cannot draw or cover; an app
  only asks for an action by id and receives its outcome.
- **The strip and Drive mode are shell-only.** Apps contribute chip **data**, never chip
  components, so a crashed or slow app cannot hide a red telltale.

## 5. Signing and distribution options

| Option | Seen in | Fit |
|---|---|---|
| Pinned npm package + code review | Backstage default, our build | Now: core and first-party apps |
| Signed file manifest (hashes + signature), host refuses unsigned | Grafana | Later: runtime modules; key list held on the device, owner-editable locally only |
| Public repo + release scan, no signing | HACS, OVMS | Rejected for code; acceptable for declarative JSON |
| Store entitlement per category | CarPlay, Android for Cars | Our analogue: `trust` levels and categories checked at install |

Verification of an ed25519 signature is available in WebCrypto in current engines and in the
`cryptography` package already used by `openostler[passkeys]`; choosing where to verify (the
brain at install, or the shell before `import()`) is an open question for the spec.

## 6. Recommendation

1. **One shell, never separate PWAs.** The shell owns the launcher, status strip, Drive mode
   and landing by driving state, auth and session, the data stream, the app registry, the
   safety-gate client and every approval surface. Separate PWAs cannot share a lockout.
2. **Apps declare, the shell enforces.** A manifest (id, version, host range, source, entry,
   requires, contributes to slots, actions used with category and tier, per-view driving
   rule, hosts, permissions, i18n, icons) is checked before any code loads; contributions
   render without activation.
3. **Loading, in order.** (a) **Bundled at build time** for core and first-party apps,
   including optional apps from their own repos as pinned npm packages, each a lazy chunk;
   (b) **declarative-only** apps for add-on modules, generated or JSON-declared; (c) later and
   behind an ADR, **sandboxed iframes** for third-party code with a scoped token; (d) signed
   **runtime ES modules** only for first-party updates without a rebuild, if ever needed.
4. **Moving views come only from shell templates**; custom views are Parked/Idling only.
5. **Not before U1**, but U1 leaves the seams (destination registry shaped as manifests, a
   typed shell context, one action path, per-destination lazy chunks and error boundaries,
   strip chips as data, route names, CSP `script-src 'self'`).

## 7. Store policy check

Checked live on 2026-10-06 for the phone build (app-model spec §7.1); paraphrased.

- **Apple 2.5.2** still says an app must be self-contained and may not download or run code
  that adds or changes its features (a narrow exception covers coding-education apps).
  **4.2** still asks for features beyond a repackaged website, and 4.2.2 rules out apps that
  are mostly web clippings or links. **4.7** now admits HTML5/JavaScript mini apps and
  plug-ins not in the binary, but the host answers for them, and **4.7.2** forbids exposing
  native APIs to that software without Apple's permission. No last-updated date was shown.
- **Google Play, Device and Network Abuse:** no downloading executable native code (dex,
  JAR, `.so`) from outside Play; JavaScript in a webview is outside that ban, but code loaded
  at run time must not allow policy breaches, and a webview with an added JavaScript
  interface must not load untrusted or unverified URLs.
- **Home Assistant Companion:** listed on the App Store as a client for the user's own Home
  Assistant server; it shows that server's frontend in a webview and adds native sensors,
  location, notifications, widgets, Watch and CarPlay surfaces (version 2026.9.3 current).
  Its July 2026 change of OS minimums was about Apple's tools, not review.
- **Capacitor:** `server.url` and `allowNavigation` are documented as **not for production**
  (live-reload use); the deploying-updates guide calls web-layer updates store-compatible.
- **Live updates:** Capgo says it ships only the web layer and advises a store release for
  native changes or anything that alters the reviewed purpose, and it promises no review
  outcome. Ionic stopped selling Appflow in February 2025, with a sunset reported for
  2027-12-31 (third-party and Ionic support pages; not re-read on ionic.io).

**Fit with the owner's plan:** no contradiction. Risks to carry: a production way to load the
server shell (not `server.url`); the native bridge only for the paired HTTPS origin (4.7.2,
Play's JavaScript-interface rule); reviewer judgment on 2.5.2; no dependence on Appflow.

## Sources

All checked 2026-10-06; content paraphrased.
- Android for Cars: [car apps overview](https://developer.android.com/training/cars/apps) ·
  [template restrictions](https://developer.android.com/training/cars/apps/library/template-restrictions) ·
  [AAOS driver distraction](https://source.android.com/docs/automotive/driver_distraction/guidelines)
- Apple: [CarPlay for developers](https://developer.apple.com/carplay/) ·
  [forum thread on dynamic JS loading and guideline 2.5.2](https://developer.apple.com/forums/thread/760364)
- Home Assistant: [integration manifest](https://developers.home-assistant.io/docs/creating_integration_manifest/) ·
  [registering resources](https://developers.home-assistant.io/docs/frontend/custom-ui/registering-resources/) ·
  [panel_custom](https://www.home-assistant.io/integrations/panel_custom/) ·
  [HACS publish](https://hacs.xyz/docs/publish/start) · [HACS plugin](https://hacs.xyz/docs/publish/plugin/)
- Grafana: [plugin.json](https://grafana.com/developers/plugin-tools/reference/plugin-json) ·
  [signing](https://grafana.com/developers/plugin-tools/publish-a-plugin/sign-a-plugin) ·
  [frontend sandbox](https://grafana.com/docs/grafana/latest/administration/plugin-management/plugin-frontend-sandbox/)
- VS Code: [extension manifest](https://code.visualstudio.com/api/references/extension-manifest)
- Backstage: [frontend architecture](https://backstage.io/docs/frontend-system/architecture/index) ·
  [module federation](https://backstage.io/docs/frontend-system/building-apps/module-federation)
- Web platform: [MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe) ·
  [module script integrity](https://shopify.engineering/shipping-support-for-module-script-integrity-in-chrome-safari) ·
  [@module-federation/vite](https://cdn.jsdelivr.net/npm/@module-federation/vite@1.16.12/README.md) ·
  [Web Application Manifest](https://www.w3.org/TR/appmanifest/)
- OVMS: [OVMS UI note](ovms_ui.md) (sources there).
- Store policy (§7): [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) ·
  [Play Device and Network Abuse](https://support.google.com/googleplay/android-developer/answer/9888379) ·
  [HA Companion docs](https://companion.home-assistant.io/docs/core/) ·
  [HA app listing](https://apps.apple.com/us/app/home-assistant/id1099568401) ·
  [HA Apple platform support, 2026-07-07](https://www.home-assistant.io/blog/2026/07/07/companion-app-changing-support-for-apple-platforms/) ·
  [Capacitor config](https://capacitorjs.com/docs/config) ·
  [Capacitor deploying updates](https://capacitorjs.com/docs/guides/deploying-updates) ·
  [Capgo FAQ](https://capgo.app/docs/faq/) · [Appflow live updates](https://ionic.io/docs/appflow/deploy/intro) ·
  [Capawesome on Appflow's sunset](https://capawesome.io/docs/blog/migrating-from-ionic-appflow-to-capawesome-cloud/)
