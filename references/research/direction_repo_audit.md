---
title: "Direction audit: what survives a standard-plus-native-apps Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-08
depends_on: [CONSTITUTION.md, GOALS.md, SCOPE.md, decisions/adr-0004-react-typescript-ui.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0016-covesa-vss-canonical-signal-namespace.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0045-ux-first.md, decisions/adr-0046-empty-os-every-app-an-add-on.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-app-ui-model-design.md, specs/2026-10-07-launcher-and-widgets-design.md, specs/2026-10-07-store-design.md, specs/2026-10-07-head-unit-apps-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-07-source-adapters-design.md, api/openapi.yaml, api/asyncapi.yaml, ui/src/shell/Boundary.tsx, references/design/2026-10/brief/00-start-here.md]
summary: >
  Recommendation: keep everything below the screen (node, firmware, transmit gate, C decoder,
  packs, VSS, module bus, Python services, recorder, accounts and sharing specs) and make it
  the standard; drop the web OS shell, the in-app Store as code distribution and the app
  runtime; defer the launcher. Build the first Android apps as option C (a native shell per
  app with AppWidgets, MediaSession and its own process, React pages in a WebView), then
  replace pages with native views only where it pays. Of eleven flaws checked in the current
  plan, four are fatal for an Android-first product: the third-party app wall, audio focus,
  an OS too big to maintain and, on Android, a Brain-only home for services. Rewrite cost:
  A is largest, B is not free (launcher, Store, runtime and theme engine are unbuilt), C is
  the cheapest path to native apps. Lists the ADRs and specs each option supersedes.
---

# Direction audit: what survives a standard-plus-native-apps Ostler

The question: if Ostler becomes **a vehicle-data standard, a reference service, SDKs and
native Android apps with their own widgets, launcher optional**, what in our repos survives,
what is re-targeted and what is dropped? And which flaws in the current plan
([ADR-0046](../../decisions/adr-0046-empty-os-every-app-an-add-on.md), the theme engine
spec, ADR-0047 and ADR-0048 on the open theme branch) are real?

## Recommendation

1. **Keep the bottom half, and call it the standard.** The node, the firmware, the transmit
   gate, the C decoder, the packs, VSS, the module-bus topics and the Python services are
   independent of how the screen is drawn. They already have a written contract
   ([openapi.yaml](../../api/openapi.yaml), 43 operations;
   [asyncapi.yaml](../../api/asyncapi.yaml), the node topics). That contract plus a Kotlin
   SDK is "every app gets its vehicle feed the same way".
2. **Drop the web OS shell, the Store as a code channel and the app runtime. Defer the
   launcher (withdraw ADR-0048 for now).** None of them is built beyond a seed
   (`ui/src/shell/destinations.ts`), so dropping them costs specs, not code.
3. **Build the first apps as option C (hybrid)**: each app is a real APK with its own
   process, AppWidgets, MediaSession or foreground service where it needs them, and its
   page bodies are our existing React pages, bundled in the APK and shown in a WebView.
   Move a page to native views only when a measurement or the owner asks. This keeps the
   15,000 lines of React, gets crash isolation and Android audio focus for free, and stays
   inside both stores' code rules (no downloaded code).
4. **Re-target, don't delete, the design work.** The theme's tokens and assets, the widget
   catalogue, the Moving templates and most of the 424 brief screens map onto per-app
   pages and AppWidgets. The launcher, Store and app-frame screens (108 of 424) go to a
   deferred folder.
5. **Add one ADR for Kotlin** (ADR-0035 says a new language needs one) and one ADR that
   supersedes ADR-0046 and ADR-0042 decisions 1–3.

## 1. What we have (evidence)

| Area | Size today | Built? |
|---|---|---|
| Python platform `src/openostler/` | about 27,700 lines: `logbook/` 7,041, `web/` 5,048, `can/` 2,419, `node/` 2,273, `kline/` 1,855, `obd/` 1,843, `mqtt/` 1,052, rest small | yes, tested (93 test files) |
| React UI `ui/src/` | about 15,100 lines TS/TSX, 1,300 CSS, 7,700 test lines; `components/` 5,593, `lib/` 1,813, `screens/` 1,523, `shell/` 1,485, `drive/` 1,307 | yes; launcher, Store and runtime not built |
| API contracts `api/` | OpenAPI 3,178 lines, AsyncAPI 781 lines | yes |
| Firmware `ostler-firmware` | C decoder, node app with `gate`, `kline`, `poll` components, shared vectors | v0 built |
| D2 pack `ostler-pack-lr-d2` | signals, menus, actions, faults, layout, sniff specs, `esp32/` | yes |
| Designer brief `references/design/2026-10/brief/` | 19,400 lines, 424 screens (launcher 50, store 16, app frame 42, head unit 63, vehicle 55, apps 56, settings 31, others) | design only |
| 17 repos `ostler-app-*`, `ostler-widgets-starter`, `ostler-theme-default`, `ostler-catalogue` | 5 files each, 2 commits, README says "Status: empty" | nothing |
| Theme engine spec (theme branch) | 758 lines, phases TE1–TE6 | design only |

The point: almost all of the OS that ADR-0046 describes is specification, not code. What is
built is the part that survives.

## 2. Classification

### 2.1 Platform repo: decisions

| Item | Mark | Reason |
|---|---|---|
| ADR-0013 pack contract | **KEEP** | Packs are data plus a lab; nothing about screens. |
| ADR-0016 VSS namespace | **KEEP** | This is the core of the standard. |
| ADR-0018 UI decisions | **RE-TARGET** | Tiers, Moving templates and kiosk rules stay; the rail and render classes become per-app rules. |
| ADR-0028 connectivity, remote access | **KEEP** | Uplinks, broker and Tailscale don't depend on the UI. |
| ADR-0032 node, optional Brain | **KEEP** | Matches the new shape better: the phone or head unit is the screen, the Brain is optional. |
| ADR-0033 action categories, approvals | **KEEP** | Enforced at the node gate; every app calls the same gate. |
| ADR-0034 repo boundaries | **RE-TARGET** | Add `ostler-sdk-android` and a link-service app; app repos become Android projects. |
| ADR-0035 languages | **RE-TARGET** | Needs Kotlin for Android apps and SDK; TS stays for pages and the Brain console. |
| ADR-0039 product family | **RE-TARGET** | Names stay; "flavour = preinstalled set" becomes "which APKs you install". |
| ADR-0042 small core, one app | **DROP (decisions 1–3, 5)** | "One app per store, no separate Android apps" is the opposite of the new direction; exit guarantee and no-Ostler-server rule stay. |
| ADR-0045 UX first | **KEEP** | Process rule; applies per app. |
| ADR-0046 empty OS | **DROP (most), KEEP §2 and §9** | The OS boundary goes; "safety is never an app" and the hard lines move to the node and the SDK. |
| ADR-0047 openness round (branch) | **KEEP, trim** | Loosenings stand; Store items (disable, paid objects, sideloaded clients) become moot. |
| ADR-0048 Android launcher (branch) | **DEFER** | Launcher is optional; reconsider once apps and widgets exist. |

### 2.2 Platform repo: specs

| Spec | Mark | Reason |
|---|---|---|
| UI architecture | **RE-TARGET** | Capability manifest, tiers, lockouts stay; destinations and rail go. |
| App model | **DROP §5–§7, KEEP §4 rules** | Registry, iframes and the Capacitor server-load plan go; manifest fields (signals, actions, driving rule) feed the SDK. |
| App UI model | **DROP or DEFER** | Schema-rendered pages, config flows and eight object kinds are an app runtime. |
| Launcher and widgets | **RE-TARGET (widgets), DEFER (launcher)** | The 24 starter widgets and the required Moving template become AppWidget specs; pages, dock, drawer wait. |
| Store | **DROP as code channel** | Android has Play, F-Droid and sideloading; keep a signed list of data packs and links. |
| Head-unit apps | **RE-TARGET** | Radio, Audio, Media, Camera become APKs; §13 audio focus becomes Android's. |
| Visual design system | **KEEP tokens, RE-TARGET kit** | DTCG tokens export to Android resources; the CSS kit stays for web pages. |
| Theme engine (branch) | **RE-TARGET** | Tokens, assets, icon and gauge packs survive; CSS layers, OSML and component templates only work in web pages. |
| Drive modes and editing | **RE-TARGET** | `ostler.layout` stays as data for a Drive app; launcher-wide editing goes. |
| Shell input | **RE-TARGET** | D-pad intents map to Android key events; the `event/input.button` topic stays. |
| Accounts and sharing | **KEEP** | Server-side; apps sign in through the SDK. |
| Trip sharing | **KEEP** | Server-side scrubbing and the share format don't care about the client. |
| Node source | **KEEP** | Brain ingest from the node. |
| Module bus messages | **KEEP** | The wire format of the standard. |
| Source adapters | **KEEP, port soft gate** | The phone host needs the soft gate; use the C gate through JNI. |

### 2.3 Platform repo: code

| Code | Mark | Reason |
|---|---|---|
| `can/gate.py`, `signing.py` | **KEEP** | Reference gate and grant signing; C gate is the portable twin. |
| `kline/`, `kwp2000/`, `obd/`, `transport/`, `dtc/` | **KEEP** | Protocol lab and reference. |
| `mqtt/`, `node/` | **KEEP** | The Brain side of the module bus. |
| `logbook/`, `gps/`, `imu/`, `geo/` | **KEEP on the Brain** | The recorder is the largest Python piece; phone-only owners need a smaller Kotlin or C recorder. |
| `web/server.py`, `web/sources.py` | **KEEP** | The reference service (HTTP, SSE) behind the OpenAPI contract. |
| `web/dashboard*.html`, `web/static/` | **RE-TARGET** | Becomes the Brain's browser console, not the OS. |
| `ui/src/components/` (Gauge, StatTile, Sparkline, sheets) | **KEEP (C) / RE-TARGET (A)** | Reusable inside app WebViews; rewritten under A. |
| `ui/src/screens/`, `destinations/`, `vehicles/` | **RE-TARGET** | Split into per-app bundles (Diagnostics, Trips). |
| `ui/src/shell/` (Shell, Nav, Strip, destinations) | **DROP** | The in-app OS frame; Android is the frame now. |
| `ui/src/shell/input.ts`, `focus.ts` | **RE-TARGET** | Still needed for D-pad inside a WebView page. |
| `ui/src/drive/` | **RE-TARGET** | Seeds a Drive app and the gauge widgets. |
| `ui/tokens/` | **KEEP** | Single source for web and Android colours. |
| MCP server (spec) | **KEEP** | Talks to the reference service, not the UI. |

### 2.4 Other repos

| Repo | Mark | Reason |
|---|---|---|
| `ostler-firmware` | **KEEP** | Node, gate and C decoder; the decoder and gate can also ship in the Android SDK. |
| `ostler-pack-lr-d2` | **KEEP** | Pure data and lab. |
| `ostler-app-diagnostics`, `-trips`, `-security` | **RE-TARGET** | First APKs; empty today, so nothing to undo. |
| `ostler-app-media`, `-radio`, `-audio`, `-camera` | **RE-TARGET** | Native APKs with MediaSession; on an Android head unit the unit's own radio and DSP may already exist, so these come later. |
| `ostler-app-map`, `-navigation`, `-phone` | **RE-TARGET, later** | Third-party apps (maps, dialler) already exist on Android; build only where Ostler adds car data. |
| `ostler-app-maintenance`, `-social`, `-hub` | **RE-TARGET** | Ordinary apps; could also be web pages on the Brain. |
| `ostler-app-decode-lab` | **RE-TARGET** | Developer tool; fits the Brain console better than a phone APK. |
| `ostler-widgets-starter` | **RE-TARGET** | Widgets now ship inside each APK; repo can hold shared widget layouts or be archived. |
| `ostler-theme-default` | **RE-TARGET** | Holds tokens and assets exported to Android and CSS. |
| `ostler-catalogue` | **DEFER** | A directory of apps and data packs, not an install channel. |

### 2.5 Designer brief

| Brief area | Mark | Reason |
|---|---|---|
| 00–03 foundation, components | **RE-TARGET** | Patterns and components stay; "OS chrome" parts go. |
| 10 onboarding | **RE-TARGET** | Becomes pairing and setup inside the link app. |
| 20 hardware | **KEEP** | Node install and setup don't change. |
| 30 settings | **RE-TARGET** | Split into per-app settings and Android settings. |
| 40 drive | **RE-TARGET** | A Drive app and gauge widgets. |
| 45 launcher (50 screens) | **DEFER** | Only if the launcher comes back. |
| 50 vehicle, 60 apps, 80 head unit, 85 security | **RE-TARGET** | Per-app pages and widgets. |
| 70 store (16 screens) | **DROP** | Play or F-Droid does this. |
| 90 app frame (42 screens) | **DROP** | Android's app frame. |

## 3. Fatal flaws in the current plan

Rated against the owner's answers: Android head units and phones first, native apps with
AppWidgets.

| # | Flaw | Rating | Evidence in the repo | Outside evidence |
|---|---|---|---|---|
| 1 | **Third-party app wall** | **fatal** | ADR-0046 §1 puts every feature inside one web shell; head-unit spec offers "the Brain as the head-unit computer", a Linux box that runs no APKs. ADR-0048 lets the web app host Android widgets, but it must lay native views over a WebView page. | Owner's chat, p. 9: a web container "cannot natively embed external Android APKs". |
| 2 | **Audio focus** | **fatal** | Head-unit spec §13: "Apps request focus through the SDK; the OS decides". On Android our whole OS is one app, so it cannot duck Spotify or a navigation app; Android decides. | Android: "Only one app can hold audio focus at a time"; from Android 12 "audio focus is managed by the system" ([audio focus](https://developer.android.com/media/optimize/audio-focus)). |
| 3 | **Crash isolation in one WebView** | **serious** | `ui/src/shell/Boundary.tsx` catches render errors per destination, but not a renderer crash, out-of-memory or a hung main thread. App-model §5 plans iframes only on web hosts. | Killing a renderer "may have an effect on multiple WebView instances", and if not handled "the application process will also be terminated" ([WebViewRenderProcess](https://developer.android.com/reference/androidx/webkit/WebViewRenderProcess)). |
| 4 | **Store downloading code into a phone app** | **serious** (product), minor (policy) | The plan already forbids it: app-model §7.1 item 4, ADR-0046 §5 ("uninstall disables"). So the Store on the phone can't install apps, only data. The risk is a Store that does little on the main platform. | Play: no downloaded dex, JAR or .so; JavaScript in a WebView is exempt ([Play policy](https://support.google.com/googleplay/android-developer/answer/9888379)). Apple 2.5.2 and 4.7.2 ([guidelines](https://developer.apple.com/app-store/review/guidelines/)). |
| 5 | **iOS** | **minor now** | Owner put iOS later. Capacitor would reach iOS cheaply; native Kotlin would not. | iOS has no launcher role; widgets get about 40–70 reloads a day ([WidgetKit](https://developer.apple.com/documentation/widgetkit/keeping-a-widget-up-to-date)). No live gauges on an iOS home screen in any option. |
| 6 | **The Brain as a required box** | **fatal on Android** | ADR-0032 calls the Brain optional, but the plan puts accounts, the recorder, app backends ("Python services on the Brain", app UI model decision 27) and the Store there. On a phone without a Brain the app falls back to a bundled subset (app-model §7.1 item 2). An Android head unit has the compute but no Python. | — |
| 7 | **Boot time** | **minor** | The plan doesn't own boot on Android; the head unit does. Reverse camera in the plan is an app (head-unit spec Camera). | Android head units cold-boot in about 20–60 s, faster with sleep mode ([boot times](https://android-headunits.com/android-headunit-boot-time/)); the owner's chat, p. 4, gives 30 s and more for Android. The reverse view should come from the head unit's own camera input, not an Ostler app. |
| 8 | **Size of an OS we can't maintain** | **fatal** | ADR-0046 lists 11 system services and 7 system-UI surfaces; 17 repos; 424 brief screens; specs with phases LW0–LW5, S0–S4, TE1–TE6, HU0–HU5 and UA; risks §3 of ADR-0046 already names "many repos" and SDK skew. Only the D2 diagnostics path is built. | The owner's chat, p. 8: "don't build an operating system inside an operating system". |
| 9 | **AppWidget update rate vs live gauges** | **serious** | Launcher spec: analogue gauge "≤ 4 Hz"; `refresh_hz: 4`. Gauges are custom drawing. | Periodic updates no faster than 30 minutes; faster needs a running app pushing `updateAppWidget` ([widget updates](https://developer.android.com/develop/ui/views/appwidgets/advanced)). RemoteViews takes a fixed set of views, no custom views ([RemoteViews](https://developer.android.com/reference/android/widget/RemoteViews)). So gauges are pushed bitmaps from a foreground service, 1–4 Hz, and smooth gauges live in the app. |
| 10 | **Theme engine depends on the web DOM** | **serious under A, minor under C** | Theme spec: CSS in cascade layers, `@scope`, container queries; OSML "rendered by the shell's React"; a Chromium 118 floor (§7, TE1). | AppWidgets can't run CSS (row 9), so under any native option widgets get tokens and assets only. |
| 11 | **Cost of rewriting the React UI natively** | **serious** | About 15,100 lines of UI plus 7,700 test lines. Most of the 424 screens are not built, so their cost is the same in any option. | — |

Fatal: 1, 2, 6, 8. Each is fatal only for the web-OS shape, and none touches the node,
gate, packs or services.

## 4. Rewrite cost of three options

Sizes are for one developer with tooling, rough, and count only work that differs between
options. Work common to all (node, packs, services, briefs for new screens) is left out.

### (A) Standard plus fully native apps

- **New:** Kotlin SDK (MQTT 5 client, VSS model with confidence and staleness, pairing,
  grant signing, BLE to the node); a link-service app holding the one node connection;
  AppWidgets for each app; the C decoder and gate through JNI for adapter hosts.
- **Rewrite:** all built UI (15k lines) and its tests in Compose; the theme engine cut to
  tokens and assets; a phone-side recorder (the Python one is 7k lines).
- **Size:** largest. Roughly 6–9 months before Diagnostics and Trips match today's web UI.
- **Gains:** the cleanest Android citizen; one tech per app. **Loses:** the shared web UI
  for the Brain console; iOS later is a second rewrite unless the SDK is written in Kotlin
  Multiplatform ([Kotlin Multiplatform](https://kotlinlang.org/docs/multiplatform.html)).

### (B) Keep the web OS

- **No rewrite**, but most of the plan is unbuilt: launcher, widget host, Store, app
  runtime, config flows, theme engine TE1–TE6, an audio-focus service, the Capacitor
  server-load design (app-model §7.1 says `server.url` is dev-only), and ADR-0048's native
  widget overlay.
- **Size:** also large, roughly 6–10 months, and flaws 1, 2, 3 and 8 remain.
- **Needs:** reversing the owner's 2026-10-08 answer (native apps with AppWidgets).

### (C) Hybrid: a native APK per app, React pages inside

- **New:** the Kotlin SDK and link service (as A); a thin Kotlin shell per app (activity,
  WebView, a bridge that serves only bundled pages, AppWidgets, MediaSession where needed);
  a Vite multi-entry build that splits `ui/` into per-app bundles.
- **Reused:** components, screens, `lib/`, `state/`, tokens, CSS and most tests; the theme
  engine works inside pages.
- **Size:** smallest path to native apps. Roughly 2–4 months for Diagnostics, Trips and
  Security with widgets.
- **Risks:** a WebView per app costs memory on 2 GB head units; old WebViews on cheap units
  (ADR-0048's own risk); pages and widgets look slightly different; two techs. Each page can
  move to native later, one at a time.

## 5. What each option supersedes

| Document | A | B | C |
|---|---|---|---|
| ADR-0046 empty OS | superseded (keep §2 safety list and §9 hard lines, re-homed to node and SDK) | stands | superseded, as A |
| ADR-0042 decisions 1–3, 5 | superseded | stands | superseded |
| ADR-0048 launcher | withdrawn, revisit later | accepted | withdrawn, revisit later |
| ADR-0035 languages | amended: Kotlin | stands | amended: Kotlin for shells and SDK |
| ADR-0004 React UI | amended: Brain console only | stands | amended: pages in app WebViews and the Brain console |
| ADR-0034, ADR-0039 | amended (repos, flavours as app sets) | stand | amended |
| ADR-0018 | amended (no rail or destinations) | stands | amended |
| ADR-0047 | Store items moot | stands | Store items moot |
| App model, app UI model, Store specs | superseded | stand | superseded |
| Launcher and widgets spec | widgets re-targeted, launcher deferred | stands | as A |
| Theme engine spec | cut to tokens, assets, packs | stands | kept for pages; widgets tokens only |
| Head-unit apps spec | §13 to Android focus; Brain-as-head-unit deferred | §13 amended anyway | as A |
| Visual design, drive modes, shell input | re-targeted | stand | lightly amended |
| UI architecture spec | amended | stands | amended |
| GOALS, SCOPE, CONSTITUTION (UI line, "safety is never an app") | amended | stand | amended |
| Node source, module bus, adapters, accounts, trip sharing | stand | stand | stand |

## 6. The standard, in one paragraph

The standard is what already sits under the screen: VSS paths with Ostler's overlay
(ADR-0016), the module-bus topics and payloads (module-bus spec, AsyncAPI), the action and
grant flow through the node gate (ADR-0033, OpenAPI), and the share format. COVESA's own
access protocol, VISS v3, carries the same tree over WebSocket, HTTP, MQTT and gRPC
([VISS v3 transport](https://raw.githack.com/COVESA/vehicle-information-service-specification/main/spec/VISSv3.0_Transport.html));
matching its read and subscribe shapes where cheap would let non-Ostler clients use our
feed. The Android SDK is a client of this standard, so third-party apps can use it too.

## Open questions for the owner

1. **Which option?** *Recommend:* C now, with pages moved to native one at a time where it
   pays; A is the long-run end state only if C's memory or look fails on real head units.
2. **One link app or each app connects to the node?** *Recommend:* one link-service app
   holds the node and Brain connection and the gate client; apps bind through the SDK;
   third parties can also read the MQTT feed directly.
3. **Where do recorder, accounts and sharing live with no Brain?** *Recommend:* a minimal
   recorder and the share scrubber in the link app (C core through JNI where possible); the
   full recorder and accounts stay on the Brain.
4. **Where does "safety is never an app" go?** *Recommend:* telltales and alarm alerts come
   from the node and the link service as Android high-priority notifications, so they work
   with every other app uninstalled.
5. **Launcher?** *Recommend:* defer; ADR-0048 withdrawn until three apps ship with widgets.
6. **Store?** *Recommend:* drop the Store client; publish APKs on Play, F-Droid and GitHub
   releases; keep `ostler-catalogue` as a plain directory page later.
7. **The 17 repos?** *Recommend:* keep and re-purpose the app repos as Android projects when
   each starts; archive `ostler-widgets-starter` and `ostler-catalogue` for now.
8. **Live gauges on the home screen?** *Recommend:* widgets update at 1 Hz from the link
   service, 4 Hz only while the app is visible; smooth gauges stay inside the Drive app.
9. **iOS?** *Recommend:* stay later; write the SDK so its logic can be shared (Kotlin
   Multiplatform or the C core) and accept that iOS widgets can't be live.
