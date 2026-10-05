---
title: "In-car and head-unit UI — industry patterns, distraction rules and gaps in our PWA (Oct 2026)"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-platform-direction-design.md]
summary: >
  Surveys how production in-car UIs (EV makers, AAOS, iDrive, MBUX, CarPlay/CarPlay Ultra, Android Auto) lay out persistent vehicle status, app panes, climate, security, cameras and hidden service menus, and distils the hard numbers (NHTSA 2 s / 12 s, 76 dp targets, 32/24 dp text, 5-step tasks, night polarity). Compares them with the current Ostler PWA and recommends a head-unit rail layout, a portrait phone layout, a persistent status strip, a speed-driven driving lockout and five top-level destinations.
---

# In-car and head-unit UI (October 2026)

Scope: what the Ostler PWA must become to sit on an Android head unit in kiosk mode (then
an Ostler launcher) while still working on phones, tablets and desktops. Brands below are
cited only as evidence; none of their marks, names or visual signatures belong in our UI.

## 1. Hard numbers (the rules we should design to)

| Rule | Value | Source |
|---|---|---|
| Single glance off road | ≤ 2.0 s (≤ 15 % of glances > 2 s, for 21 of 24 test drivers) | NHTSA Phase 1 guidelines [N1][N2] |
| Total eyes-off-road per task | ≤ 12 s | NHTSA [N1] |
| Per se lockouts while driving | video and non-driving images, auto-scrolling text, manual text entry, reading > 30 characters (a number plus unit counts as one) | NHTSA [N1][N2] |
| "Driving" | transmission not in Park (a manual car has no Park, so we need speed) | NHTSA [N1]; AAOS states [A3] |
| Portable/aftermarket devices | proposed Phase 2 guidelines: pair with the car, or offer a simplified **Driver Mode** | NHTSA Phase 2 (draft, 2016) [N3] |
| Touch target | ≥ 76 × 76 dp; ≥ 23 dp between targets; no overlap | Android for Cars [G1][G2] |
| Touch target (parked-class apps) | ≥ 64 dp, 24 dp apart and from screen edges, text ≥ 24 sp | Car app quality UX-1..3 [G3] |
| Text | primary 32 dp, secondary 24 dp; ≤ 120 Roman characters per string | Android for Cars [G1] |
| Contrast | ≥ 4.5:1 for anything conveying information | Android for Cars [G1] |
| Night | content at night **must** be negative polarity (light on dark) | Android for Cars [G1] |
| Task depth | ≤ 5 templates (screens) per task; toggles refresh in place without using a step | Car App Library [G4] |
| Motion | no auto-scrolling text, no animated graphics (canvas animation only when parked and relevant) | Car app quality ST-1, SA-1 [G3] |
| Notifications | no heads-up notifications from apps; show only what the driver needs | Car app quality IN-1/IN-2 [G3] |
| Tabs | max 5 tabs (4 for audio apps) in the CarPlay tab bar template | CarPlay framework [C2] |
| Screen sizes | 800×480, 960×540, 1280×720, 1920×720 (8:3); landscape and portrait | CarPlay HIG [C1] |
| Placement | most important content and controls in the upper half; never send the driver to the phone | CarPlay HIG [C1] |
| Telltale colours | red = danger, amber = caution/malfunction, green = on/normal, blue = main beam | ISO 2575 [I1] |
| Physical controls | indicators, hazards, horn, wipers and SOS must not live on a touchscreen (5-star rating from 2026) | Euro NCAP [E1] |

Driving states worth copying verbatim from AAOS [A3]: **Parked** (unrestricted), **Idling**
(not in Park, speed 0: no video, no setup screens), **Moving** (fully restricted: no keyboard,
limited string length, limited list items and depth, no video, no setup).

## 2. What the production systems do

### EV-maker touchscreen (large landscape, single screen)
- **Layout:** a persistent car-status column on the driver side (drive mode, range, a top-down
  car visualisation with tappable trunk/charge-port controls), the map filling the rest, and a
  persistent **bottom bar** holding the car-controls launcher, the cabin temperature, apps and
  volume [T1][T2].
- **Cards:** swipeable cards under the car visualisation (media, tyre pressures, trip) [T1].
- **Tyres:** pressures drawn on the car visualisation with "last measured" time; underinflation
  raises an alert in the car-status area and an icon by the tyre [T3].
- **Climate:** a temperature target always on the bottom bar; tap for the full climate pane,
  `<`/`>` for a quick popup [T2].
- **Security:** the surveillance-recording state is a status-bar icon; the recorded-clip viewer
  opens only **in Park**, lists events by date/location with per-camera thumbnails [T4].
- **Service mode:** hidden behind a long-press on the model name in Software plus an access
  code; once on, the **whole screen gets a red border** and a red wrench icon sits in the dock;
  the owner is told not to drive in it [T5].

### Android Automotive OS (AAOS) reference UI, as shipped by a Swedish EV maker
- **System UI layer above the app layer:** a status bar on top (connectivity, notifications,
  profile, quick controls) and a navigation bar that can be bottom, left or right, holding
  facet buttons (app shortcuts), notifications and **vehicle controls such as HVAC** [A1][A2].
- **Small landscape reference:** home cards stacked on the left, the main app (navigation) on
  the right; when an app opens, the cards collapse and the app widens [A2].
- **Home:** four large tiles (navigation, media, phone, a vehicle card) instead of an app wall [P1].
- **Climate bar:** a persistent strip at the bottom of the centre display with driver and
  passenger temperatures, seat heating/ventilation and heated wheel [P2].
- **Restrictions:** CarUxRestrictions maps gear and speed to Parked / Idling / Moving and exposes
  limits such as max content items, max depth and max string length [A3][A4].

### US adventure-EV maker
- A **vertical status bar** with key vehicle information and quick access to frequent controls and
  settings; quick controls and the media player can dock on **either side** for reach [R1].
- Lock/unlock sits beside closures and the **alarm (camera-backed guard mode)**; release-note
  summaries describe its video as viewable from the centre display while parked (not verified
  against a manual) [R2].

### German premium A (iDrive 8 / 8.5 / 9)
- **Zero-layer "QuickSelect":** live widgets stacked vertically on the **driver's side**, all major
  functions one level deep, a home icon at the bottom always one tap away [B1].
- **Climate row is fixed** at the bottom regardless of menu; seat and wheel heating toggle without
  opening the climate menu [B1][B2].

### German premium B (MBUX)
- **Zero layer:** the top level shows situational, context-aware cards instead of menus [M1].
- Warnings appear in the driver display in red text; a service view lists warnings and days to
  next service [M2].

### CarPlay and CarPlay Ultra
- CarPlay is template-driven: the system renders lists/grids/tabs, so every app inherits sizes,
  contrast and lockouts; it supports light/dark switching by ambient light [C1].
- **Ultra** takes over the cluster and centre screen: live speed/rev/fuel/temperature gauges,
  radio and **climate**, a **tyre-pressure app** with high/low/puncture warnings, widgets on the
  cluster, maker-specific themes; video only when parked [C3][C4].

### Android Auto "Coolwalk"
- A **split-screen dashboard**: the largest card is the map, then a media card and a contextual
  suggestions card; a **rail** (time, signal, battery, app grid, notifications, assistant) docks
  **bottom on standard screens and left on wide ones**; on portrait screens the map goes on top [AA1][AA2].
- The map card sits nearest the driver and can be enlarged to full screen [AA1].

### Aftermarket Android head units (our real target)
- Typical panels: 7" 1024×600, 9" 1280×720, 10.1" 1280×720 or 1920×1080; ultra-wide 1920×720
  bars exist too [H1][C1].
- Their own "Factory settings" menu is hidden behind a 7-tap on the version line and a numeric
  code [H2] — the same "hidden + code + obvious once on" pattern.

## 3. Patterns that recur everywhere

1. **A persistent vehicle/status strip** that never scrolls away: clock, link state, the highest
   active warning, security state, and the one or two controls used most (climate).
2. **Driver-side placement.** Status and quick controls sit nearest the driver; the "big pane"
   (map/app) takes the rest. Wide screens get a vertical rail; narrow screens a bottom bar.
3. **Zero/one layer home.** 4–6 large cards with live data, each one tap from detail; no app wall.
4. **Car visualisation as the status index.** Doors, tyres, warnings and closures are drawn on a
   top-down car; tapping a part opens that system.
5. **Warnings are telltales, not dialogs.** ISO colours, an icon in the status area, a card with
   detail on demand. Modal popups are rare and reserved for red conditions.
6. **Security is a status-bar icon plus a parked-only viewer.**
7. **Service/diagnostic menus are hidden twice** (gesture plus code), and once active the whole
   screen is visibly different (red frame) and driving is discouraged.
8. **Driving state gates the UI**, not the user's discipline: Parked / Idling / Moving.
9. **Night = dark, automatically**, keyed to light level or headlights, with a manual override.
10. **Cameras pre-empt everything on reverse** and are otherwise a parked or low-speed tool.

## 4. Our current UI (read from `ui/src`, Oct 2026)

| Aspect | Today | File |
|---|---|---|
| Shell | One column, `max-width: 900px`, header 56 px, content, optional replay transport, **bottom tab bar** | `App.tsx`, `styles.css` |
| Destinations | **8 public tabs** (Drive, Faults, Inputs, Outputs, Settings, Utilities, Logs, Analysis) + 3 admin; bar scrolls below 8 × 48 px | `screens/registry.ts` |
| Header | module select, clock, Mark, battery V, Rewind, connection pill, ⚙ — up to 7 controls | `App.tsx` |
| Touch targets | header chips 36 px, pill 32 px, buttons 48 px, options 56 px, tabs 56 px tall × ≥ 48 px | `styles.css` |
| Type | body 14 px, labels 11–13 px, Drive values `clamp(34px, 12vw, 64px)` | `styles.css` |
| Breakpoints | width only (600/480/460/400/360 px); **no landscape or height-aware layout**; e2e viewports are phones (360–412 wide) | `styles.css`, `e2e/smoke.spec.ts` |
| Theme | follows `prefers-color-scheme`, `data-theme` override; no automatic night switch from car signals | `styles.css` |
| Faults | `FaultSheet` **auto-pops as a modal** on connect with unacknowledged faults | `App.tsx` |
| Drive | per-module tiles in a 2-column grid, health strip, REC badge; is a tab, not a mode | `screens/Drive.tsx` |
| Safety | actions gated by registry safety + user-ticked preconditions; **nothing reads speed/gear** | `components/ActionButton.tsx` |
| Service | `/admin` path (server password), Experimental mode with a yellow banner | `lib/admin`, `App.tsx` |
| Motion | blinking dots (`@keyframes blink`), pulsing replay pill (reduced-motion respected) | `styles.css` |

Signals already in the pack fixtures that a lockout can use (status per the protocol handoff;
treat as candidate until proven in the car): `speed`, `wheel_speed_*`, `reverse_gear`,
`neutral_gear`, `reverse_light`, `side_lights`. GPS speed arrives with the guardian/u-blox.

## 5. Gaps

1. **No head-unit layout.** On 1024×600 the header + tab bar take 112 px (19 % of height), the
   900 px cap leaves dead bands on 1280/1920-wide panels, and a bottom bar wastes the short axis.
2. **Too many destinations.** 8 tabs (11 with admin) vs the 5-tab ceiling every car platform uses.
3. **Targets and type are phone-sized.** 32–48 px targets and 11–14 px text are under half the
   76 dp / 24–32 dp car minimums; spacing between header chips is ~8–12 px, not 23.
4. **No driving state.** Nothing distinguishes Parked / Idling / Moving; outputs, settings writes,
   free-text notes, Docs, Analysis and replay/video are all reachable at speed.
5. **Modal fault popup** is a heads-up interruption; it should be a telltale in the strip while moving.
6. **Status is spread across the header** with no severity ordering; no security slot, no climate
   slot, no camera entry; the module picker (a technician control) sits in the most valuable spot.
7. **Night mode depends on the OS**; kiosk browsers on head units rarely flip `prefers-color-scheme`
   with the illumination wire.
8. **Animations** (blink, pulse) run in normal states; car rules reserve motion for alarms.
9. **Service mode isn't visually distinct** beyond a small banner; Experimental can stay on while driving.
10. **No car visualisation**: tyres, doors, SLABS wheel speeds and faults have no spatial index.
11. **Tests cover phones only**; no 1024×600, 1280×720 or 1920×720 screenshots.

## 6. Recommendations

### 6.1 Five destinations, Drive as a mode (confirms the platform spec)
`Home · Diagnose · Logs · Security (Map when no guardian) · More`, cap 5, matching the CarPlay
tab ceiling [C2] and the five-step task limit [G4]. Mapping from today:
- **Home** — zero-layer cards: vehicle visualisation, warnings, battery/charging, last trip, a big
  **Drive** button. The current Drive tiles become Drive mode.
- **Diagnose** — module picker (moved out of the header), Faults, Inputs, Outputs, Settings,
  Utilities as segments inside one destination (≤ 5 segments).
- **Logs** — sessions, recording, replay; Analysis is the session detail view.
- **Security / Map** — alarm state, events, tracker map; clip viewer parked-only.
- **More** — preferences, add-ons (climate controller, cameras), packs, about; the hidden service
  entry lives here (6.6).

### 6.2 Layout classes (chosen by aspect and height, not width alone)

| Class | Trigger | Shell |
|---|---|---|
| **Phone portrait** | portrait, width < 600 | top status strip 48 px · content · bottom bar 5 × ≥ 72 px |
| **Tablet/desktop** | width ≥ 900, height > 800 | left rail 88 px · status strip · two-pane content (list + detail) |
| **Head unit** | landscape and height ≤ 800, or `?display=headunit` | **left (driver-side) rail** · top status strip · cards |
| **Ultra-wide** | aspect ≥ 2.4 (1920×720) | rail · vehicle pane (fixed) · main pane · secondary pane |

Provide a kiosk URL flag (`?display=headunit&side=left|right`) because head-unit browsers often
report odd DPIs; RHD/LHD decides which side the rail docks (driver side, as [B1][R1][AA1]).
Drop the 900 px `max-width` for head-unit and ultra-wide classes.

**1024×600 (7")** — rail 96 px (5 targets of ~96 × 100 px), status strip 56 px, content 928 × 544:
home = 2 × 2 cards; Drive mode = 3 × 2 tiles, value text ≥ 56 px, label ≥ 24 px.

**1280×720 (9–10")** — rail 112 px, strip 64 px; home = vehicle card (40 %) + 2 × 2 cards; Diagnose
= list (380 px) + detail.

**1920×720 (8:3)** — rail 112 px, strip 64 px, three panes like the dashboard split [AA1]: vehicle
pane 520 px always visible (car visualisation + telltales), main pane, and a secondary pane
(camera, or Logs mini-timeline). Opening an app widens the main pane over the secondary [A2].

**Phone portrait (360–430 × 780–930)** — 5-item bottom bar fits at 72–86 px each (a 393 px phone
gives 78 px, ≈ the 76 dp target); strip shows clock, link dot, worst telltale, REC, security;
everything else moves to Home cards or More. Drive mode = 2 × 3 tiles full height.

### 6.3 What is persistent (the status strip)
Always visible, left to right in severity order, each item ≥ 48 px tall in the strip and opening a
sheet on tap: **worst active telltale** (ISO colours, count), **link/connection** (icon + word,
not colour alone), **REC** (when logging), **security state** (disarmed/armed/alerting; Map slot
shows tracker fix), **12 V battery**, **clock**, **Mark** (one-tap flag — the one action safe at
speed). Optional add-on slot: when the climate controller is present, a compact temperature +
fan chip (on ultra-wide, a full bottom climate strip as in [P2][B2]). Not persistent: module
picker, Rewind, preferences cog (move to Diagnose / Logs / More).

### 6.4 Driving-mode lockout
- **State machine:** Parked (engine off or speed 0 for > 5 s with handbrake/neutral where known),
  Idling (engine running, speed 0), Moving (speed > 5 km/h from ECU or GPS for > 2 s; leave Moving
  only after < 2 km/h for 3 s). Unknown speed = **assume Moving** on the head-unit display.
- **On Moving:** auto-enter Drive mode on the head unit; keep the strip; allow Drive tiles,
  telltale sheet (≤ 30 characters per line, codes + short names), Mark, reverse/low-speed camera.
- **Locked while Moving:** all Outputs/actuator tests and settings writes (also server-side —
  safety travels with the action), text entry (notes, search), Docs, Analysis, replay scrubbing,
  dashcam/clip playback, module switching, Experimental/service mode (auto-exit), lists longer
  than ~6 items or deeper than 2 levels. Locked items show a lock and "Available when parked".
- **Idling:** allow reading and logs, still no actuations that the registry marks engine-off,
  no video other than cameras.
- Keep every remaining task ≤ 5 screens and plausibly ≤ 12 s; no auto-scroll, no animation except
  red alarms; replace the modal `FaultSheet` with a strip telltale while Moving.
- A phone is a passenger device we cannot verify: show the same Moving banner and lock actuations,
  but allow reading.

### 6.5 Sizes, type, theme
- Head-unit/Drive tokens: target 76 px min (rail items larger), gap ≥ 24 px, edge inset ≥ 24 px;
  text primary 32 px, secondary 24 px, never < 20 px in Moving; tile values 56–96 px tabular.
- Night: negative polarity, dimmer accent, no large white surfaces. Auto-switch from `side_lights`
  (once proven) else sunrise/sunset from GPS + clock, else `prefers-color-scheme`; manual override in
  More. Test colours in sun (contrast ≥ 4.5:1) [C1][G1].
- Colour semantics locked to ISO 2575; never use red/amber for brand or interactive accents.

### 6.6 Service and diagnostic depth
Treat Experimental + admin as **service mode**: entered from More by a long-press on the version
line plus the server password (no separate URL needed on the head unit), shown by a thick
coloured frame round the whole viewport and a strip badge, unavailable and auto-exited when
Moving [T5][H2].

### 6.7 Status, warnings, security, cameras, tyres
- **Vehicle visualisation** (our own generic top-down silhouette, pack-supplied geometry):
  wheels coloured from SLABS wheel speeds/faults, doors/closures when the BCU is decoded, tyres
  when a TPMS add-on exists — show "not fitted" vs "no data" honestly.
- **Warnings:** strip telltale → sheet → Diagnose detail (3 steps).
- **Security:** strip icon; Security destination for state and event list; clips parked-only.
- **Cameras:** reverse pre-empts the screen (needs the fast path the platform spec flags);
  underbody/front only below a low speed; dashcam review parked-only (NHTSA video lockout [N1]).

### 6.8 Tests
Add Playwright viewports 1024×600, 1280×720, 1920×720 (landscape) and a Moving-state fixture
asserting that actuations, text inputs and video are locked and targets measure ≥ 76 px.

## Sources
- [N1] NHTSA Visual-Manual Driver Distraction Guidelines (2013): https://www.nhtsa.gov/sites/nhtsa.gov/files/distracted_driving_guidelines_for_in-vehicle_electronic_devices.pdf ; summary https://www.transportation.gov/briefing-room/us-dot-releases-guidelines-minimize-vehicle-distractions
- [N2] Glance criteria and 30-character rule as published: https://www.govinfo.gov/content/pkg/FR-2014-09-16/pdf/2014-22028.pdf ; https://ohsonline.com/Articles/2012/02/26/New-Guidance-Lists-Unsafe-Driver-Distractions.aspx
- [N3] NHTSA Phase 2 (portable/aftermarket, Driver Mode), proposed 2016: https://www.govinfo.gov/content/pkg/FR-2016-12-05/html/2016-29051.htm
- [G1] Android for Cars visual principles: https://developers.google.com/cars/design/design-foundations/visual-principles
- [G2] Android Auto sizing: https://developers.google.com/cars/design/android-auto/design-system/sizing
- [G3] Car app quality guidelines: https://developer.android.com/docs/quality-guidelines/car-app-quality
- [G4] Car App Library template restrictions: https://developer.android.com/training/cars/apps/library/template-restrictions
- [A1] AAOS System UI: https://source.android.com/docs/automotive/hmi/system_ui
- [A2] AAOS small landscape reference: https://developers.google.com/cars/design/automotive-os/product-experience/system-ui/small-landscape
- [A3] Car UX Restrictions: https://source.android.com/docs/automotive/driver_distraction/car_uxr
- [A4] CarUxRestrictions API: https://developer.android.com/reference/android/car/drivingstate/CarUxRestrictions
- [C1] CarPlay HIG: https://developer.apple.com/design/human-interface-guidelines/carplay
- [C2] CPTabBarTemplate: https://developer.apple.com/documentation/carplay/cptabbartemplate
- [C3] CarPlay Ultra overview: https://www.igeeksblog.com/apple-carplay-ultra-features ; https://www.androidauthority.com/apple-carplay-ultra-3558074/
- [C4] CarPlay Ultra hands-on: https://www.techradar.com/vehicle-tech/hybrid-electric-vehicles/ive-tried-apple-carplay-ultra-it-fixes-everything-thats-irritating-about-carplay-but-theres-a-catch
- [AA1] Dashboard redesign: https://9to5google.com/2022/05/12/android-auto-redesign/
- [AA2] Rollout and rail position: https://www.xda-developers.com/android-auto-coolwalk-rollout/ ; https://www.notebookcheck.net/Google-I-O-2022-Android-Auto-Coolwalk-refresh-introduced-for-small-and-large-in-car-displays.619937.0.html
- [T1] Car status and cards (owner's manual): https://www.tesla.cn/ownersmanual/model3/en_hk/GUID-80B80D48-E3A9-4857-864B-F4CC9B56FD7E.html
- [T2] Climate controls (owner's manual): https://www.tesla.com/ownersmanual/model3/en_hk/GUID-4F3599A1-20D9-4A49-B4A0-5261F957C096.html
- [T3] Tyre care and pressures: https://www.tesla.cn/ownersmanual/modely/en_gb/GUID-94F63B13-EA2C-45D9-83AB-5DCA6295D587.html
- [T4] In-car clip viewer: https://electrek.co/2020/04/03/tesla-update-teslacam-sentry-mode-video-viewer/
- [T5] Service mode: https://www.notateslaapp.com/news/2046/tesla-service-mode-how-to-access-it-and-what-it-does
- [P1] AAOS home tiles: https://newatlas.com/polestar-2-ui-android/58212/ ; https://www.gearbrain.com/amp/review-android-automotive-polestar-2-2646843862
- [P2] Climate bar (owner's manual): https://www.polestar.com/us/manual/polestar-2/2022/article/525e288f53b183ccc0a80151593cbdb3/
- [R1] Vertical status bar, quick controls either side: https://rivianroamer.com/software-updates/2026-31
- [R2] Guard-mode controls and video (release-note aggregators): https://riviantrackr.com/2026-31/ ; https://rivianroamer.com/software-updates/2024-19
- [B1] QuickSelect zero layer: https://paultan.org/2023/03/09/bmw-idrive-9-and-idrive-8-5-revealed/
- [B2] Fixed climate row: https://www.whichcar.com.au/news/bmw-idrive-8-revealed
- [M1] Zero layer: https://media.mercedes-benz.ca/releases/mercedes-benz-unveils-the-new-mbux-hyperscreen-which-will-debut-in-the-eqs
- [M2] Warnings and service view: https://www.autoguide.com/auto/manufacturers/mercedes-benz/2023-mercedes-benz-glc-300-exploring-the-mbux-driver-displays-44607835
- [I1] ISO 2575 telltales: https://www.iso.org/standard/68409.html
- [E1] Physical controls: https://whichcar.com.au/news/euro-ncap-wants-more-physical-controls-and-less-touchscreens-to-achieve-five-star-rating
- [H1] Head-unit panel sizes: https://www.ebay.com/itm/316472511559 (typical listing; treat as indicative)
- [H2] Hidden factory menu: https://android-headunits.com/pin-codes-for-android-headunit/
