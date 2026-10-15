---
title: "How Android Automotive handles apps, compared with Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-15
summary: >
  AAOS app model: host-drawn templates (media, messaging, Car App Library), the distraction-optimized flag checked at runtime and by Play review, parked-only categories, OEM-owned windowing and theming. Compared row by row with Ostler PWAs, the page contract and the picker. Recommends shell-drawn templates and parked-only for third-party iframe pages while moving; lists code/doc drift in the page contract.
---

# How Android Automotive OS handles apps, and how Ostler compares

Research note, 2026-10-15. Read-only: no repo was changed. AAOS facts come from Google's docs,
fetched today (Sources, part A). Ostler facts come from the files listed in Sources, part B,
which were checked by reading them. Where the shell code and the docs disagree, this note says
so (§2.6).

---

## 1. Android Automotive OS: the app model

### 1.1 App categories, and how each one is built

Google lets a third-party app into the car only if it belongs to an approved **category**. Each
category comes with a fixed way of building the app, and that build method decides who draws the
UI. Source: [A1].

| Category | Built with | Who draws the UI | When it can run |
|---|---|---|---|
| **Media (audio)** | `MediaBrowserService` + `MediaSession`; templated media is in early access | **The system.** "Android Automotive OS takes care of laying out the media content… your app doesn't draw the UI" [A6]. The app ships no launcher activity; only settings and sign-in activities are allowed, and those are parked-only. | driving or parked |
| **Messaging** | `MessagingStyle` notifications plus a reply service; templated messaging is in labs | the system (notifications, read-aloud, voice reply) | driving or parked |
| **Calling** (labs) | Telecom Jetpack + Car App Library | host templates | driving or parked |
| **Navigation** | Car App Library (`NavigationTemplate`, `MapTemplate`…) | host templates; the app draws only the map surface (and a second map in the cluster) | driving or parked |
| **POI** (parking, charging, fuel) | Car App Library | host templates | driving or parked |
| **IoT** | Car App Library | host templates. While driving: device state, one-touch on/off, event notifications; no setup or fine control (IT-1) [A3] | driving or parked |
| **Weather** | Car App Library | host templates | driving or parked |
| **Video** | ordinary Views or Compose | the app | parked only (limited audio while driving on capable cars, DD-4) |
| **Games** | Views or Compose | the app | parked only (generally available since Sept 2026 [A3]) |
| **Browsers** (labs) | Views or Compose | the app | parked only; internal testing track only |

Long-form email apps are not permitted (MF rules) [A3]. AAOS also has OEM-side app surfaces:
**AppCards**, which are glanceable cards that an app supplies through an `AppCardContentProvider`
and that a system `AppCardHost` renders in the OEM's style, with a refresh period the host sets
[A11]. The **Control Center** reference app covers multi-display experiences [A14].

### 1.2 The Car App Library and its templates

- **Host and client.** The car (Android Auto or AAOS) is the *host* and renders everything. The
  app is a *client*: through a `CarAppService` → `Session` → `Screen` chain it sends **templates
  filled with data**. Examples are List, Grid, Pane, Message, Search, Map, Navigation, SignIn and
  LongMessage [A4][A5].
- **Who does what** [A7]:
  - The library handles input, screen sizing, transitions, light and dark, and driving-state
    restrictions. It makes the app "work in a driving-optimized way in all compatible cars".
  - The app handles voice input, flows, metadata and branding, plus map drawing if it is a
    navigation app.
  - On AAOS, the OEM handles vehicle-specific styling.
- **Hard limits** [A5]:
  - At most **five templates per task**, and the last one must be a terminal type.
  - A refresh with the same template type and the same main content is free.
  - Going back restores quota, and `NavigationTemplate` resets it.
  - Going over the limit makes the host show an error and **close the app**.
- **Why templates.** Google's reasons, from its own docs, plus the evidence in Ostler's research
  ([B14] §2.1):
  1. **Distraction compliance by construction.** The host enforces text limits, list lengths,
     no keyboard while driving and step counts, so no review has to trust the app.
  2. **Consistency.** "UI and interaction patterns are familiar and consistent across apps" [A7].
  3. **OEM fit.** One app looks native in every brand's car.
  4. **Every screen and input.** Touch, rotary, portrait, landscape and wide screens are covered
     without the app knowing which it is on.
- **How far an app can restyle a template** [A8]:
  - The app picks **up to 2 custom accent colours**, or picks from 4 standard ones, at 4.5:1
    contrast. It supplies its own icons and images.
  - It can **not** change fonts, template layout or default styling.
  - The OEM, on AAOS, sets fonts, shapes, button placement and width, and the primary-line colour.
    The OEM may recolour app-supplied colours "to blend with vehicle UIs".

### 1.3 Parked apps and the distraction-optimized (DO) flag

- **Driving states** [A10]:
  - **Parked:** gear in P; no restrictions.
  - **Idling:** not in P, speed 0; **no video, no config**.
  - **Moving:** fully restricted.
- **Restrictions are named types** (no_video, no_config, no_keyboard, fully_restricted, …). They
  come from `CarUxRestrictionsManager`, which also caps string length, cumulative content items
  and content depth [A10].
- **Who decides the rules.** The OEM, per display and per region [A12]. "By default, no
  restrictions are applied to additional displays." [A10]
- **The DO flag.** An activity runs under restriction only if its manifest carries
  `<meta-data android:name="distractionOptimized" android:value="true"/>`. Otherwise "activities
  cannot be run while UX restrictions are active" [A9][A12].
- **The platform trusts the declaration and Play enforces it.** "The platform can't detect or
  enforce an app's actual adherence… Adherence… is enforced during the Google Play review" [A9].
  For third parties, Google allows the flag **only on the Car App Library's `CarAppActivity`**:
  "No other activities should be marked as distraction optimized… your app will be rejected" [A12].
  Media settings and sign-in activities must *not* carry it [A6].
- **The upshot.** A third-party app may draw its own pixels while driving **only inside a host
  template**, apart from the map surface of a navigation app. Free-form UI means parked only.
- **Fail-safe behaviour** [A10]:
  - If the restriction config fails to load, AAOS uses a **hard-coded fully restricted mode**.
  - Before the first driving state arrives (at boot), AAOS behaves **as Parked**. This boot
    window fails open.

### 1.4 System apps and unbundled apps

- **System apps are the OEM's.**
  - **CarLauncher** is the HOME activity, built on `TaskView` so that a map sits inside the home
    screen [A15].
  - **Car Settings** (dual-pane, searchable), **SystemUI** (system bars that OEMs may lock so
    climate controls are always reachable [A12]), the Dialer, the Media centre and Car Messenger
    are also the OEM's. Several of them are **unbundled**, meaning they are shipped and updated
    separately from the platform [A2].
- **Windowing is the OEM's.**
  - **Scalable UI** is an XML-configured panel system. *TaskPanels* host app tasks and
    *DecorPanels* host views or widgets. It has variants (open, closed, minimised), events and
    transitions animated by WindowManager, and a restart policy for crashed panel apps [A16].
  - Apps do not choose their panel; the OEM's config does.
- **Some normal Android features are often missing.** App Widgets and picture-in-picture are "not
  available on many Android Automotive OS vehicles". TalkBack and Switch Access are absent. No
  back button is guaranteed, so apps must provide in-app navigation (AN-1) [A12].

### 1.5 Design for Driving and the quality tiers

- **Quality tiers** [A3]:
  - **Tier 3, Car ready.** Large-screen, parked use. Required for video, games and browsers.
  - **Tier 2, Car optimized.** Required for every driving-capable category.
  - **Tier 1, Car differentiated.** Adapts between driving and parked, and uses the cluster and
    other screens.
- **Rules that matter to Ostler** [A3]:
  - Text at least 24 sp (UX-3).
  - Touch targets at least 64 dp (UX-1), at least 24 dp apart and 24 dp from the edges (UX-2).
  - No animation (SA-1) and no auto-scrolling text (ST-1).
  - Images only where they help (IU-1).
  - At most five screens per task (AC-1).
  - Buttons respond within 2 s, and the app launches and loads within 10 s (DR-1 to DR-3).
  - The navigation audio channel is for navigation only (DD-1).
  - No heads-up notifications from parked apps (IN-2).
  - On AAOS, no functionality in the app's own activities except setup, settings and sign-in
    (PE-1).
  - Light and dark themes (TH-1), and maps in light or dark (MR-1).
- **The design hub.** Design for Driving has moved to `docs.partner.android.com/drivingux` (since
  11 March 2026) [A13].

### 1.6 Play Store review

- **Opt-in per form factor.** In the Play Console you add Android Auto and/or AAOS as form
  factors. AAOS needs two portrait and two landscape screenshots that name no OEM [A17].
- **Tracks.**
  - Media and templated apps use **AAOS-only tracks**.
  - Parked apps may share the mobile track.
  - Review blocks open testing and production, and does not block closed testing.
- **Manual review against the quality guidelines.**
  - It can take longer than usual.
  - Updates for other devices are **held until the car build is approved**.
  - Reviewers need test accounts, and a mock-GPS path for apps not available in the US [A3][A17].
- **Enforcement point.** The review is where the DO declaration is actually checked.

### 1.7 OEM customisation

- **RROs (runtime resource overlays)**, static or dynamic, recolour and resize resources app by
  app [A18].
- **Car UI library (`car-ui-lib`).**
  - A statically linked component library: toolbar, lists, preferences.
  - Its customisable resources are treated as **an API with backwards-compatible guarantees**
    [A18].
- **Car UI plugins** [A19]:
  - A plugin is a *preinstalled* APK on the system partition, found through a content provider.
  - It supplies whole component implementations (for example the toolbar's base layout) behind
    versioned `V#` factories. It must work with older and newer apps, and falls back to the
    static components.
  - Plugins exist because RROs change only XML resources, and only one app at a time.
- **OEM design tokens** feed the unbundled apps and the Car App Library host [A2].

### 1.8 Multiple displays

- **Occupant zones.**
  - `CarOccupantZoneManager` maps each zone (driver, front passenger, rear) to a set of displays.
  - Each zone has a main display and may have a cluster, HUD, auxiliary or IME display.
  - Each zone gets its own Android user: multi-user multi-display, with passengers as "visible
    background users" [A20][A21].
- **Restrictions per display.** These are set by the OEM; passenger and extra displays default to
  unrestricted [A10][A12].
- **The cluster.**
  - Navigation apps render a second map and turn cards into it through the Car App Library.
  - The AOSP sample cluster only fills the navigation panel for certified car Maps [B12].

### 1.9 AAOS's design philosophy in one paragraph

**The platform owns the frame, and the OEM owns the look. Apps own data, and own pixels only when
the car is parked.**

- **While driving**, a third-party app is a data source pouring into a template that the host
  draws: media trees, message notifications, templates and AppCards. The system therefore enforces
  distraction rules mechanically: text and list caps, a step quota, no keyboard, no video.
- **The few places an app draws itself** (a navigation map, parked categories) are justified by
  category and policed by a **manual store review**. The runtime DO flag is only a declaration.
- **What is forbidden:**
  - categories outside the list;
  - DO flags on anything but `CarAppActivity`;
  - video, keyboards and setup while moving;
  - animation, custom fonts and layouts in templates;
  - apps choosing their own window.
- **The reasons:**
  - Liability and regulation (NHTSA, ESoP) require that compliance can be checked without
    trusting each app.
  - OEMs require that every app looks like *their* car.
  - Developers get one build for every car, screen and input.

The cost is expressiveness. No third-party live gauge dashboard is possible while driving, which
Ostler's own research already noted ([B14] §2).

---

## 2. Ostler's equivalent

### 2.1 Direction

- **Ostler is "not an operating system"** [B3]. It is a diagnostic and logging platform with an
  open VISS feed.
- **Every screen is a separate PWA**, each in its own repo, served by `ostler.app` and the Brain,
  on one **gateway**. The gateway runs on the Brain, the Android Gateway app, a node, or the
  browser (ADR-0049 v1.3) [B3].
- **The screen line** is "Ostler arranges, Android runs" [B3]:
  - Ostler never builds its own media, radio, navigation or phone apps.
  - It never manages audio focus, never hosts other apps and never runs an app store.
- **Distribution** is Play, F-Droid and APK for native apps. The old Store becomes a
  "catalogue of packs and themes as data" (item 14) [B3].

### 2.2 The MFD and the ostler-shell library (ADR-0052, still marked *proposed*)

- **The MFD.** The screen is an aircraft-style MFD: a carousel of saved layouts of **tiles**, and
  each tile shows one **page** from any installed app [B4].
- **No launcher, no shell app.** **Every app bundles `ostler-shell`**, and whichever app is open
  hosts the tiles [B4][B6].
- **Hosting.**
  - Own apps (same origin) load as **page modules**.
  - **Third-party pages load as sandboxed iframes** that talk over `ostler.*` `postMessage`
    [B4][B9][B10].
  - A page the shell cannot render shows as a chip that opens its own app.
- **Five size classes** come from each tile's own box: Badge, Chip, Compact, Standard and
  Expanded. They have enter and exit hysteresis, and JavaScript writes the class [B4] (code:
  `src/layout/sizeClass.ts`, 16 dp hysteresis [B7]).
  - If a page lacks a class, the shell uses the largest smaller class it has.
  - At Chip or Badge the **shell** draws the page's `summary()` (icon, value, badge).
  - Otherwise it shows the "Needs a bigger tile" fallback (`resolveRender`) [B6].
- **The page contract as built** (`src/contract/page.ts`) [B6]. An `AppDef` is `{id, title,
  pages}`. Each `PageDef` declares:
  - `sizes`, `minExpandedW` and `instrument`;
  - **`moving: safe | reduced | parkedOnly`**;
  - `summary()`, `claimsGestures` and `render(el, ctx)`;
  - a `focus` tree for the D-pad and `deepLink`.

  "The shell owns the window, the tiles and attention; the app owns every pixel inside its page."
  The tile-navigation spec adds **starting points** (`{app, startingPoint, route}` per tile),
  app-owned history, `back()` and `navigate()`, and cross-app links gated on user activation for
  iframes [B10].
- **Instrument pages** (Speed, Attitude, Heading, Transfer, Engine) ship with the gateway. A
  warning never covers an instrument [B4][B6].
- **Moving rules belong to the shell, and apps cannot override them** (`src/motion/rules.ts`)
  [B8]:
  - `unknown` counts as moving.
  - While moving: text at least 24 dp, targets at least 60 dp, effects off.
  - Blocked while moving: edit, resize, saving, settings changes and `parkedOnly` pages, each
    with a toast such as "Park to edit the layout".
  - ADR-0052 §5 also bars typing, clearing faults, actuator tests and video while moving [B4].
  - Drive modes were **rejected**: "safety follows actions", and owners choose their pages [B4].
- **Alerts** run app → Gateway → shell. The **shell** draws them: a ring and tag, a card, or a
  passenger-side takeover. Warning and caution colours are locked [B4][B6].
- **Themes.**
  - A theme changes structure as well as colour, and comes in day and night versions [B4].
  - Locked tokens: warning and caution colours, sizes and safety icons.
  - Custom CSS imports pass a sanitiser that keeps known custom properties only, allows no
    `url()` except a `data:` wallpaper, and checks contrast.
  - Alert contrast is tested in every theme [B6][B11].
- **The picker.** In edit mode (parked only, Android-home-screen style), a slot picker lists
  "pages that fit the slot, at its real size, with suggestions first". It also lists Android
  widgets when the Gateway Android app hosts the shell (`src/edit/picker.ts`) [B6]. "Get more
  apps" shows when only the gateway is installed [B9].
- **Permissions.**
  - The Gateway's controller gives per-app toggles, issues a scoped VISS token, treats writes as
    requests only, starts with cautious defaults, and logs revokes [B3].
  - The node gate decides every write [B3].

### 2.3 The separate AAOS track

`openostler/ostler-android-automotive` is the owner's own head-unit build [B12][B13]:
- LineageOS Automotive, or Waydroid in the meantime, with car Maps and Waze, fed by Ostler over
  VISS. Car Maps and Waze already work on LineageOS 20 under Waydroid.
- The platform keeps the OS and the launcher as non-goals.
- Ideas file [B13]:
  - a gauge cluster built as an **Ostler module from VISS**, so it survives an Android crash;
  - AAOS's MUMD occupant zones noted as the way to do passenger screens;
  - rear headrest tablets running an Ostler app;
  - nothing on the D2's passenger airbag door.

### 2.4 Earlier Ostler designs that matter here

- **The old app-model spec had a `declarative` app kind** with "no app code; shell tiers 1–2",
  next to `iframe` for community code [B15].
- **The old Store spec had review levels**: System, First party, Verified publisher, Community
  and Sideloaded. Community code was iframes on web hosts only, and widgets had to declare
  `moving` [B16].
- **The driver-distraction research** recommended that driver-facing head units show **only
  templates** while moving: `map`, `media`, `tiles`, `alert_card` and `short_list`, with
  Android's limits, a task depth of 3, and new templates added only "by platform proposal" (D6)
  [B14].
- **ADR-0052 dropped templates and drive modes** in favour of page-declared moving behaviour and
  action rules [B4].

### 2.5 Ostler's design philosophy, in the same terms as §1.9

**The user owns the frame and the look, within locked safety tokens. The shell owns attention
(tiles, alerts, focus, moving rules). Apps own every pixel inside their page, at every speed,
by declaring `safe`, `reduced` or `parkedOnly`.**

- The gateway and the node own the car and its data, which reach apps through a VISS token.
- Android, not Ostler, owns media, navigation and the phone.

### 2.6 Drift found between the docs and the code (worth fixing either way)

1. **The page contract.**
   - ADR-0052 §4 and the shell spec §7 [B4][B9] describe priority-ranked `parts`, per-action
     moving safety (`safe/confirm/not-while-moving`), VSS `data.uses/requires`, `links`,
     `softKeys` and a `host: module | iframe` field.
   - The built `PageDef` [B6] follows the designer's guide §3 [B5] instead. It has **page-level**
     `moving: safe|reduced|parkedOnly` and none of those fields.
   - ADR-0052 v0.8 says the guide wins, but §4 and the shell spec were not updated.
   - Without `data.requires`, the picker cannot do "apps grow when data appears" or "Get more
     apps that work with this car" [B4].
2. **There is no iframe host in the code yet.**
   - `grep iframe src/` finds nothing outside the Android transport.
   - The tile-navigation spec lists it as "N7… when it is built" [B10].
   - So third-party apps have no working path today.
3. **Size-class exit thresholds.** The ADR table says 108×56 and 204×128, while the code uses
   16 dp hysteresis, giving 104×48 and 204×124 [B4][B7]. The units also changed from CSS px to dp.
4. **Widgets.**
   - ADR-0049 item 6 says "No widget apps" [B3].
   - ADR-0052 §2a makes a frameless Chip or Compact page a widget, and lets the Gateway host
     Android widgets [B4].
   - A one-line supersession note would settle it.

---

## 3. Comparison

Verdict key: **Aligned** = same idea. **Different on purpose** = a deliberate, defensible
divergence. **Gap** = something AAOS covers that Ostler does not yet.

| # | AAOS concept | Ostler equivalent | Verdict | Recommendation |
|---|---|---|---|---|
| 1 | **App categories** decide what an app may be (media, nav, POI, IoT, weather, messaging, parked video, games, browsers) | No categories. Any app offers any page; the page declares `moving` and `instrument` [B6] | Different on purpose (open ecosystem, ADR-0047) | Keep it open, but add an optional `category` hint (gauge, map, log, control, media-now-playing) for the picker's suggestions and for the moving defaults in row 3. |
| 2 | **Host-drawn templates** for third-party apps while driving (Car App Library, media centre, messaging notifications) | Pages draw their own pixels; the shell draws only chrome, the Chip and Badge summary, and alerts [B6] | **Gap for third-party apps**; different on purpose for first-party apps | **Yes, adopt template-like limits for third-party pages, not for own apps.** Revive the old `declarative` kind [B15] as a fourth host kind beside module and iframe. The page sends data and the shell draws it (`value`, `gauge`, `tiles` of 6 or fewer, `short_list` of 6 or fewer rows, `alert_card`, the limits from [B14] §7.2). Only declarative pages, and reviewed first-party modules, may be `safe` or `reduced` while moving. A **third-party iframe page is forced to `parkedOnly` while moving**, whatever it declares. This is AAOS's rule "DO only on `CarAppActivity`", in Ostler terms. |
| 3 | **The DO flag is trusted at runtime and enforced by Play review** | `moving: safe/reduced/parkedOnly` is self-declared; `validatePageDef` checks only that the value is valid [B6] | Gap (no review, no enforcement) | The shell cannot enforce 24 dp text or 60 dp targets *inside* an iframe it never draws into. So: (a) the row 2 rule; (b) the catalogue records a review level per app (bring back [B16]'s levels), and only First party or Verified may ship `safe` iframe pages; (c) default an undeclared or unknown `moving` value to `parkedOnly` (fail closed, like AAOS's restricted fallback). |
| 4 | **Parked-only categories** (video, games, browsers); Idling also bars video and config | `parkedOnly` pages; video, typing, edit, clear-faults and actuator tests blocked while moving; `unknown` = moving; the old `idling` → unknown [B4][B8] | Aligned (Ostler is stricter: AAOS behaves as Parked at boot) | Keep "unknown = moving". Write down why Ostler differs from AAOS's boot-as-parked default. |
| 5 | **Task quota**: 5 templates per task, then the app is closed; AC-1 caps tasks at 5 screens | Apps own history per tile instance; the shell sees `nav.report` [B10]. No depth limit | Gap (minor) | While moving, count pushes reported through `nav.report` per instance from the moment motion starts. At depth 3 (the CarPlay-style figure in [B14]), refuse further `navigate` pushes with "Park to go further". This is cheap because the shell already sees every route. |
| 6 | **Text 24 sp, targets 64 dp, 24 dp spacing; no animation; no auto-scroll** (UX-1..3, SA-1, ST-1) | While moving: 24 dp text, **60 dp** targets, blur, glow and texture off [B8] | Mostly aligned | Consider 64 dp to match UX-1. Add "no animation except red alarms" and "no auto-scrolling text" to the moving rules, so module pages get them through `ctx.moving`. |
| 7 | **The system draws media and messaging UI** from MediaBrowserService and MessagingStyle | "Never builds own media, radio, navigation or phone"; Spotify and Waze stay the real apps [B3] | Aligned / different on purpose (Ostler defers to the platform) | Keep. If a "now playing" tile is wanted, read Android `MediaSession` metadata in the Gateway-hosted shell and draw it as a declarative page. Do not build a player. |
| 8 | **AppCards**: the app supplies data, the OEM host renders cards at a host-set refresh | Chip and Badge `summary()` drawn by the shell; Chip and Compact update less often [B4][B6] | Aligned | The `summary()` path is already Ostler's AppCard. Extend it into the declarative kind (row 2) rather than inventing a second widget system. |
| 9 | **System apps vs unbundled apps**: OEM CarLauncher, Car Settings and SystemUI; Dialer, Media and Messenger unbundled | No launcher or shell app; the Gateway app owns connections, permissions, shared preferences and instrument pages; each app has its own home and settings with a Shared section [B4] | Different on purpose ("not an OS") | The Gateway is effectively Ostler's "Car Settings + SystemUI". Keep its protected surfaces (permission prompts, alerts) out of any app's reach, as now. |
| 10 | **Windowing is the OEM's**: Scalable UI panels in XML; apps never pick their window | The **user** composes layouts with the tiling engine and edit mode; layouts are synced by the Gateway [B4][B6] | Different on purpose (the user owns the layout) | Keep. Where Ostler runs *on* AAOS (row 15), the MFD is one app inside one panel, so do not count on freeform or open-beside there. |
| 11 | **OEM theming**: RROs, car-ui-lib resources as an API, plugins replacing whole components, OEM design tokens; apps get 2 accents | User themes change structure and colour; day and night; locked safety tokens; sanitised custom CSS; contrast tests [B4][B6][B11] | Aligned in mechanism (tokens as an API); different on purpose in who themes | Treat the `--os2-*` token set as a **versioned public API** with compatibility guarantees, as car-ui-lib does. **Gap:** iframe pages never receive the theme. Add an `ostler.theme` `postMessage` (token values plus day or night) so third-party pages can match, as OEM tokens reach Car App Library apps. Consider limiting third-party pages to accent colours, as AAOS does. |
| 12 | **Play review and quality tiers** (Car ready, optimized, differentiated), blocking review for production | Native apps go through Play, F-Droid and APK; PWAs come from `ostler.app` and the Brain; the catalogue is data; no review is defined for third-party pages [B3] | Gap | Bring back the review levels [B16] in the catalogue and tie them to rows 2–3. Publish an Ostler "page quality" checklist modelled on the AAOS IDs (moving behaviour, contrast, summary present, every size class tested at Chip through Expanded, no dead ends). It can be largely automated, because the playground already renders frames per class. |
| 13 | **Permissions**: car permissions on the Car API; the OEM configures UX restrictions | Gateway permission controller: per-app toggles mapped to data classes and action categories; scoped VISS token; writes only as requests; the node gate decides [B3] | Aligned (Ostler is finer-grained) | Keep. Add the page's declared VSS `data.requires` back to the built contract (§2.6 item 1), so the picker and permission prompts can explain what a page will read. |
| 14 | **Multiple displays**: occupant zones, a user per zone, per-display restrictions (passenger displays unrestricted by default), cluster display | Layouts stored per `car` and `screen` class [B6]; instrument pages; rear tablets and passenger screens only as ideas [B13]; the research says every head unit is driver-facing unless declared otherwise [B14] | **Gap** | Add a **screen role** in the Gateway (driver-visible, passenger, rear, cluster), set at install and never while moving, defaulting to driver-visible (fail closed, unlike AAOS's open default for extra displays). Motion rules apply by role. The cluster role allows instrument pages only, matching [B13]'s "cluster as an Ostler module from VISS". |
| 15 | **Running *on* AAOS**: browsers are labs and parked-only; only `CarAppActivity` may be DO; App Widgets and PiP are often missing; no TalkBack | The Kotlin template wraps the React pages in a WebView [B17]; the shell's Android extras (AppWidgetHost tiles, open beside) [B5] | Gap / risk for any Play-distributed AAOS build | On a Google-built-in car, an Ostler WebView app **cannot legally show live pages while driving** through Play. The only compliant Play route is a Car App Library app (the IoT or templated category) that sends the declarative pages from row 2 as templates. On the owner's own LineageOS build [B12], Ostler controls the `CarUxRestrictions` config and may mark its apps DO. In that case, take the shell's motion state from `CarUxRestrictionsManager` when present, and feed it from the VISS → VHAL bridge so the two always agree. |
| 16 | **Back**: no guaranteed back button; apps must have in-app navigation (AN-1); rotary input | Back order, wheel and D-pad focus engine, `FocusTree`, Android back callback [B6][B10] | Aligned | None. |
| 17 | **Fail-closed config**: a bad UX-restriction config gives fully restricted | Unknown or stale motion = moving; the motion heartbeat is 1 s and goes stale at 3 s [B6][B8] | Aligned | Also fail closed on a **page** that fails validation or declares nothing: show it as a chip, as already done for unrenderable pages. |

### 3.1 The concrete answer: should the third-party contract adopt template-like constraints?

**Yes, as a tier rather than a blanket rule:**

1. **Own apps (page modules, reviewed in their repos)** keep free-form pages with
   `safe/reduced/parkedOnly`. The shell can see their DOM, they are code-reviewed, and the
   instrument pages need the freedom. Car makers likewise exempt their own system apps.
2. **Third-party apps, while moving, get only shell-drawn declarative pages.**
   - The page supplies data; the shell draws it from a small, versioned template set.
   - The set is Chip and Badge summary, value, gauge, tiles, short list and alert card, with
     the limits from [B14] §7.2.
   - The set grows only by platform proposal.
   - Moving safety is then a property of the template, not something the third party claims.
3. **Third-party iframe pages are free-form, but `parkedOnly` while moving, always.**
   - The shell already shows a blocked page as its summary, so a declarative `summary()` still
     shows while moving.
4. **The catalogue records review levels** (row 12). A Verified publisher may apply for an
   exemption to row 3, which mirrors AAOS's manual review.

This keeps what makes Ostler different from AAOS: user-composed layouts, user themes, an open
ecosystem, and first-party gauges while driving. It closes the gap that the current contract
has. Today a third-party iframe can declare itself `safe` and draw 10 px scrolling text while
moving, and nothing stops it.

### 3.2 Where Ostler is deliberately ahead of AAOS, and should stay so

- Unknown motion counts as moving, whereas AAOS treats boot as Parked.
- Size classes come from each tile's own box, so one page works at five sizes. AAOS templates
  adapt per screen, not per user-sized tile.
- One alert pipeline is drawn by the shell, never covers an instrument, and has contrast-tested
  locked colours in every theme.
- Per-app VISS tokens, with writes only as requests to the node gate.

---

## Sources

### A. Android Automotive OS (fetched 2026-10-15)

- [A1] Android for Cars, app categories: https://developer.android.com/training/cars
- [A2] Unbundled apps (subpages: Car UI library, AppCards, Control Center, Media, Dialer, OEM design tokens): https://source.android.com/docs/automotive/unbundled_apps
- [A3] Car app quality guidelines: https://developer.android.com/docs/quality-guidelines/car-app-quality
- [A4] Android for Cars App Library: https://developer.android.com/training/cars/apps
- [A5] Template restrictions: https://developer.android.com/training/cars/apps/library/template-restrictions
- [A6] Media apps on AAOS: https://developer.android.com/training/cars/media/automotive-os
- [A7] Build apps with templates (Design for Driving): https://developers.google.com/cars/design/create-apps/apps-for-drivers/build-with-templates
- [A8] Customize your app (who controls what): https://developer.android.com/design/ui/cars/guides/foundations/customize-app
- [A9] Driver distraction guidelines (DO activities): https://source.android.com/docs/automotive/driver_distraction/guidelines
- [A10] Car UX restrictions: https://source.android.com/docs/automotive/driver_distraction/car_uxr
- [A11] AppCards: https://source.android.com/docs/automotive/unbundled_apps/appcards
- [A12] AAOS overview for developers: https://developer.android.com/training/cars/platforms/automotive-os
- [A13] Design for Driving hub (moved to docs.partner.android.com/drivingux): https://developers.google.com/cars/design
- [A14] Control Center reference app: https://source.android.com/docs/automotive/unbundled_apps/control-center
- [A15] CarLauncher on TaskView (CTS commit) and the AAOS system UI references: https://android.googlesource.com/platform/cts/+/6a6e7cc668a ; https://developer.google.com/cars/design/automotive-os/product-experience/system-ui/small-landscape ; https://docs.partner.android.com/drivingux/automotive-os/system-experience/overview
- [A16] Scalable UI: https://source.android.com/docs/automotive/scalableui ; 25Q4 notes: https://source.android.com/docs/automotive/start/releases/aaos-25q4
- [A17] Distribute car apps: https://developer.android.com/training/cars/distribute
- [A18] Car UI library: https://source.android.com/docs/automotive/hmi/car_ui
- [A19] Car UI plugins: https://source.android.com/docs/automotive/hmi/car_ui/plugins
- [A20] CarOccupantZoneManager: https://developer.android.com/reference/android/car/CarOccupantZoneManager
- [A21] Multi-Display Communications API: https://source.android.com/docs/automotive/displays/multi-display-comms-api
- IVI landing page: https://source.android.com/docs/automotive/ivi

### B. Ostler files cited

- [B1] `openostler/ostler`CLAUDE.md
- [B2] `openostler/ostler`GOALS.md (and INDEX.md)
- [B3] `openostler/ostler`decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md
- [B4] `openostler/ostler`decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md
- [B5] `openostler/ostler`references/design/2026-10/shell-session/IMPLEMENTATION.md (§3, §10, §12)
- [B6] `openostler/ostler-shell`README.md; `openostler/ostler-shell`src/contract/page.ts; `openostler/ostler-shell`src/contract/validate.ts; `openostler/ostler-shell`src/contract/host.ts; `openostler/ostler-shell`src/edit/picker.ts
- [B7] `openostler/ostler-shell`src/layout/sizeClass.test.ts
- [B8] `openostler/ostler-shell`src/motion/rules.ts
- [B9] `openostler/ostler`specs/2026-10-11-ostler-shell-design.md (§7, §8, §9)
- [B10] `openostler/ostler`specs/2026-10-13-tile-navigation-design.md (§2.2, §2.3)
- [B11] `openostler/ostler-shell`src/theme/customCss.ts
- [B12] `openostler/ostler-android-automotive`README.md
- [B13] `openostler/ostler-android-automotive`docs/ideas.md
- [B14] `openostler/ostler`references/research/driver_distraction_rules.md (§2.1, §7, §9 D6)
- [B15] `openostler/ostler`specs/2026-10-06-app-model-design.md (§5, isolation by kind)
- [B16] `openostler/ostler`specs/2026-10-07-store-design.md (§6.1 review levels)
- [B17] `openostler/ostler`decisions/adr-0050-kotlin-for-the-android-app-tier.md
- Also read: `openostler/ostler`decisions/adr-0034-repo-boundaries.md, `openostler/ostler`decisions/adr-0047-openness-round.md (community code only in sandboxed iframes on web hosts)
