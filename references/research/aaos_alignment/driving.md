---
title: "Driving state and driver distraction: Android Automotive compared with Ostler"
area: references
status: draft
version: 0.1
updated: 2026-10-15
summary: >
  AAOS UX restrictions: the OEM config per driving state, speed band, mode and display; apps see restriction flags and limits (120 chars, 21 items, depth 3); unknown state is fully restricted, boot is not. Ostler matches or is stricter on most rules, differs on purpose on hysteresis, the passenger view and boot, and has gaps: no single rules file, no keyboard/video block in the shell, 60 dp vs 76 dp targets, idling state drift. How to feed Ostler’s verdict to an AAOS head unit through a VISS-fed VHAL.
---

# Driving state and driver distraction: Android Automotive OS compared with Ostler

Researched 2026-10-15. Part 1 comes from the AOSP and developer.android.com pages and from the
AOSP car service source (`packages/services/Car`, `main`), read directly. Part 2 comes from the
Ostler docs repo (`openostler/ostler`) and the shell code
(`openostler/ostler-shell`, commit `824dd1a`). Part 3 compares them. Every source is listed
at the end. Nothing in any repo was changed.

---

## Part 1: how AAOS does it

### 1.1 The pipeline

```
VHAL properties ──▶ CarDrivingStateService ──▶ CarUxRestrictionsManagerService ──▶ apps
PERF_VEHICLE_SPEED    infers PARKED / IDLING /     maps state (+ speed range,         listen to CarUxRestrictions
GEAR_SELECTION        MOVING / UNKNOWN             + mode, + display) to a            (a bit mask + limits);
PARKING_BRAKE_ON                                   restriction set from the OEM XML   SystemUI blocks activities
IGNITION_STATE (opt.)                                                                 not tagged distractionOptimized
```

There are two layers, and apps are pointed at the second one.

- **`CarDrivingStateManager`** gives the raw state (`DRIVING_STATE_PARKED`, `IDLING`,
  `MOVING`, `UNKNOWN`). It is a `@SystemApi` that needs `android.car.permission.CAR_DRIVING_STATE`,
  so only platform parts, bundled apps and privileged apps can read it.
- **`CarUxRestrictionsManager`** is the public API. The docs tell apps to "monitor restrictions
  rather than the absolute driving state for anything related to UI/UX", because the manager
  maps state to restrictions, so apps "don't need to handle different market safety
  requirements". An app registers `OnUxRestrictionsChangedListener`, reads
  `getCurrentCarUxRestrictions()` once at start, and then checks `isRequiresDistractionOptimization()`
  and the `getActiveRestrictions()` bit mask.

### 1.2 How the driving state is inferred (VHAL to state)

`CarDrivingStateService.inferDrivingStateLocked()` uses these rules:

1. `GEAR_SELECTION == GEAR_PARK` gives **PARKED**.
2. Otherwise, on a **manual** car, `PARKING_BRAKE_ON` true gives **PARKED**. A car counts as
   manual when its supported-gears list has no `GEAR_PARK`. On an automatic car the brake is ignored.
3. Otherwise the state comes from `PERF_VEHICLE_SPEED` in m/s: exactly 0 gives **IDLING**,
   and any other value gives **MOVING**.
4. If speed is unavailable, `IGNITION_STATE` of LOCK, OFF or ACC gives **PARKED**. Otherwise
   the state is **UNKNOWN**.

`CURRENT_GEAR` is not used. The only speed boundary in the state machine is "zero or not",
with no hysteresis. Speed bands belong to the restriction config (§1.4). To test it, inject
values with `cmd car_service inject-vhal-event 0x11600207 <m/s>` (speed) and
`0x11400400 <gear>` (gear: 4 = Park, 8 = Drive).

### 1.3 Unknown, missing and malformed inputs

AAOS mixes failing open at boot with failing closed everywhere else, on purpose:

| Situation | Behaviour (source) |
|---|---|
| Boot, before any state arrives | **Unrestricted.** `CarUxRestrictionsManagerService.init()`: "Unrestricted until driving state information is received. During boot up, we don't want everything to be blocked … If we start driving and still don't get speed or gear information, we have bigger problems." `initializeUxRestrictions` leaves `UNKNOWN` unchanged. The `car_uxr` page says it "behaves as if the state is Parked". |
| State becomes `UNKNOWN` later | Mapped through the config. The hard-coded default config maps `DRIVING_STATE_UNKNOWN` to **fully restricted** with `requiresDistractionOptimization=true`. |
| `MOVING` with no speed value | Treated as the **highest speed range** (`MAX_SPEED`). The code comment calls it "the safest route". |
| Config missing or unreadable | Falls back to `createDefaultConfig()`: parked and idling baseline/unrestricted, moving and unknown **fully restricted**. |
| A state or attribute missing from the XML | The XML's own header says "the platform takes a fully restricted approach when there is no information or if the information is malformed". `requiresDistractionOptimization` defaults to true and `uxr` to `fully_restricted`. Any `uxr` other than baseline forces `requiresDistractionOptimization=true`. |
| A display not in the config | **Fully restricted.** |
| New config pushed | Saved as "staged" and promoted only when the car service restarts **while parked**. |

### 1.4 The per-state restriction config (`car_ux_restrictions_map.xml`)

The OEM writes an overlay XML (`<UxRestrictions>`):

- `<RestrictionMapping>`, either for the driver's main display by default or for a display
  picked by `physicalPort` or by `occupantZoneId` + `displayType`.
- Inside it, `<DrivingState state="parked|idling|moving" minSpeed=".." maxSpeed="..">`. Speed
  is in **m/s**, ranges are half-open `[min, max)` and must not overlap, and the top range
  has no `maxSpeed`.
- Inside that, `<Restrictions requiresDistractionOptimization="true|false"
  uxr="no_video|no_keyboard|…" mode="baseline|passenger|…">`.
- `<RestrictionParameters>`, global or per mapping:
  `<StringRestrictions maxLength>` and `<ContentRestrictions maxCumulativeItems maxDepth>`.

AOSP's shipped reference values:

| State | requiresDO | uxr |
|---|---|---|
| parked | false | baseline |
| idling | true | `no_video` (the `car_uxr` doc example adds `no_config`/`no_setup`) |
| moving, [0, 5 m/s) | true | no_dialpad, no_filtering, limit_string_length, no_keyboard, no_video, limit_content, no_setup, no_text_message |
| moving, ≥ 5 m/s | true | the same set (it is there to show two speed bands) |
| Parameters | | **maxLength 120**, **maxCumulativeItems 21**, **maxDepth 3** |

The restriction flags in `CarUxRestrictions` are: `NO_DIALPAD` 1, `NO_FILTERING` 2 (no typing
to filter a list), `LIMIT_STRING_LENGTH` 4, `NO_KEYBOARD` 8, `NO_VIDEO` 16 ("no animated frames
above 1 fps"), `LIMIT_CONTENT` 32 (cumulative items and depth "along any one path in a single
task"), `NO_SETUP` 64, `NO_TEXT_MESSAGE` 128, `NO_VOICE_TRANSCRIPTION` 256, and
`FULLY_RESTRICTED` 511, which is all of them.

### 1.5 "Baseline" compared with "fully restricted"

- **`requiresDistractionOptimization=false` + `baseline`** means no restrictions. Any activity
  may run. This is the parked case.
- **`requiresDistractionOptimization=true` + `baseline` (0)** means no specific flags are set,
  but only activities tagged `distractionOptimized` may run, and they must follow Google's
  general distraction guidelines. This is the floor whenever the car isn't parked.
- **`fully_restricted` (511)** means every flag is on. It is the fail-closed value.

### 1.6 Who decides, and who enforces

| Role | Decides | Enforced by |
|---|---|---|
| Google | Baseline guidelines and the flag vocabulary; car-app quality criteria (DD-2/DD-3: video, games and browsers are not launchable while driving; SA-1 no animation; ST-1 no auto-scrolling text; AC-1 five-screen tasks; IT-1 limits on IoT controls while driving) | Google Play review. The platform "can't detect or enforce an app's actual adherence". |
| OEM | The XML: what each state, speed band, mode and display restricts, plus the string and content limits. This is where market rules (NHTSA, JAMA, ESoP) are encoded. | `CarUxRestrictionsManagerService` |
| Platform | Blocks any activity not tagged `<meta-data android:name="distractionOptimized" android:value="true"/>` while `requiresDO` is true, using SystemUI's blocking activity. | The car service and SystemUI |
| App | Declares DO activities, listens to restrictions, and adapts its own UI: truncates strings, caps lists, hides the keyboard, stops video. | Itself, checked by Play review |
| Car Settings (a bundled app) | Most preferences are greyed out while driving. Tapping one shows the `restricted_while_driving` toast (an overlay of 60 characters or fewer). OEMs whitelist preference keys with `config_ignore_ux_restrictions`. | The app |

Design guidance for apps (Design for Driving, developers.google.com/cars, moving to
docs.partner.android.com/drivingux): the driver should be able to read content in **2 s**;
touch targets **76 × 76 dp** with **23 dp** gaps; primary text 32 dp and secondary 24 dp; text
**≤ 120 characters**; contrast at least 4.5:1; no video or auto-scrolling text; sequences that
can be interrupted and resumed; parked-only features hidden or clearly marked. Partner video
guidance for parked apps gives 64 dp targets 24 dp apart.

### 1.7 Passengers

AAOS has no "I'm a passenger" button. A passenger is handled in two ways:

1. **By geometry.** A `RestrictionMapping` per physical port or occupant zone gives a passenger
   or rear display its own map, often baseline at every speed. The XML notes that passenger
   mode "can be generically supported by specifying UxR for passenger displays".
2. **By mode.** `setRestrictionMode(String)` switches the whole map to a named set such as
   `"passenger"`. The default is `UX_RESTRICTION_MODE_BASELINE`. The call needs
   `PERMISSION_CAR_UX_RESTRICTIONS_CONFIGURATION`, so only the OEM's system UI can do it,
   never a third-party app. AOSP does not say how the OEM verifies the passenger.

### 1.8 Policies AAOS relies on

The public AOSP and developer pages fetched for this note **do not name NHTSA, JAMA or ESoP**.
They speak of "different market safety requirements" that the OEM's map absorbs. The links in
practice, mostly from Ostler's own research note:

- **NHTSA Visual-Manual Guidelines, Phase 1 (2013).** Voluntary. Glances of 2 s or less each
  and 12 s total. Lockouts by purpose: video, non-driving images, auto-scrolling text, manual
  text entry for messaging or browsing, and reading long text. "Driving" means not in Park, so
  idling in gear counts as driving. A manual car counts as parked only with the brake on, in
  neutral and below 5 mph. Phase 2 (2016) proposed a "Driver Mode" and was never finalised.
- **JAMA Guideline** (Japan, first 1990, v3 2004). It measures glance time and bans video and
  heavy text while moving. One threshold often quoted is 5 km/h, which this note did not check
  against the text. AAOS's Japanese text limit (31 characters) fits a JAMA-style market.
- **ESoP, Recommendation 2008/653/EC.** Non-driving visuals must be off or out of the driver's
  sight while moving. Functions not meant for the driver must be impossible to use, even under
  "reasonably foreseeable misuse", with a warning only as the weaker fallback. Long sequences
  must survive interruption.

The 120-character, 21-item, depth-3 and 0/5 m/s defaults are Google's reference values. They
are not quotations from any regulation.

### 1.9 The AAOS philosophy in five lines

1. **The OEM decides** what is allowed; the platform enforces activity blocking; apps declare
   and adapt; Google's store reviews.
2. **Apps learn restrictions, not driving state**: a bit mask plus three numbers, pushed by
   listener.
3. **Baseline** means "only distraction-optimized UI, guidelines apply". **Fully restricted**
   means every flag. Parked has no restrictions at all.
4. **The passenger is a display or a system-set mode**, never an app's claim or a tap.
5. **Unknown fails closed** (fully restricted, highest speed band) **except at boot**, which is
   left open deliberately until the first reading.

---

## Part 2: what Ostler does

The rules sit in three layers, and the layers have drifted apart (see §2.4).

### 2.1 The platform: UI spec §3.5 and §12.1, ADR-0033

- **States and thresholds** (`specs/2026-10-06-ui-architecture-design.md` §3.5). The platform
  (the server) computes the state from vehicle speed, then GPS speed, then proven gear and
  handbrake signals:
  - **Parked:** speed 0 for more than 5 s and engine off, or handbrake/neutral where known.
  - **Idling:** engine running and speed 0. Since §12.1 (U2), text entry, Maintenance and
    `engine_running_ok` Tier 2 actions also need **Park evidence**: handbrake on, or neutral
    (sensed, or inferred from engine speed ÷ wheel speed) for more than 3 s. This follows
    NHTSA's "idling in gear is driving".
  - **Moving:** **> 5 km/h for > 2 s; leave below 2 km/h for 3 s** (hysteresis).
  - **Unknown speed counts as Moving on head units.** A phone is a passenger device that
    can't be verified, so reading stays open and actions keep the stationary check.
- **Enforcement on the server.** "The server re-checks the state from the node on every
  action, whichever device asked." Layout writes are refused with `409` and `driving_state`
  in the error (drive-modes spec §8). Apps "can neither set nor read 'unlocked'".
- **Rules per category** (ADR-0033): Read allowed; Comfort allowed with driver-safe UI;
  Security arming allowed, disarming Parked only; Maintenance Parked or Idling; Actuator tests
  and Procedures Parked only; Coding disabled. An action that transmits on a vehicle bus is
  Parked-only.
- **Fail closed:** a view with no `moving` rule, or a missing restriction config, is fully
  locked. This was copied from AAOS (§12.1).
- **Templates and limits while Moving** (§12.1): `map`, `media`, `tiles` (≤ 6, digits ≥ 56 px,
  refresh ≤ 4 Hz), `alert_card` (≤ 2 lines of ≤ 30 characters, ≤ 2 buttons, no message text),
  `short_list` (≤ 6 rows, one level, ≤ 30 characters), `call` (audio only), plus
  `telltale_list`, `value`, `setpoint`, `camera_live` (≤ 10 km/h by default) and `arm`. A task
  is **≤ 3 screens** (the owner may raise this to 5). The 30-character limit is Ostler's own
  default, and the owner may raise it up to the AAOS cap of **120**. Rate limits for message
  cards. **No voice transcript** while Moving, citing AAOS `NO_VOICE_TRANSCRIPTION`.
- **Driver-facing displays.** Every head-unit display counts as driver-facing. Only an owner
  install setting marks a screen passenger-only.
- **Passenger view** (per trip, on a head unit). It covers only UK reg 109 content: vehicle
  state, own location and route, driving cameras. It asks once, has no "always", shows a
  badge and frame, and is view-only. It ends on Parked, ignition off, a new trip, unknown
  speed, reverse, service mode, a red telltale or a timeout (15 min by default, up to 60).
  The server holds it, and each grant is logged locally. **Open on phone** is the preferred
  route. A phone may be marked as a passenger device. The release waits for a UK legal opinion.
- **"Using Ostler while driving" page** (ESoP IV).

### 2.2 ADR-0052 §5 and the shell spec (`specs/2026-10-11-ostler-shell-design.md`)

- **No drive modes.** "While moving, the floor is about actions, not pages; owners choose
  pages". No typing or editing, no layout editing (switching saved layouts stays one tap), no
  clearing faults, no actuator tests, no video. Blur, glow and texture are off, text is at
  least 24 px, and settings can be browsed but not changed ("Park to change").
- **Shell spec §9:** states moving/idling/parked/unknown, with **unknown counted as moving**.
  `actionGate(action, state)` uses each page action's `MovingSafety` (`safe`, `confirm`,
  `not-while-moving`). The kinds `typing`, `edit`, `layout-edit`, `clear-faults`,
  `actuator-test` and `video` are always `not-while-moving`. `layoutEditAllowed` and
  `effectsAllowed` allow parked or idling. Parts marked `hideWhileMoving` drop first.
- **§18:** "Motion unknown" shows as an outlined status. A wheel action refused off screen gets
  a text-only toast for 4 s ("Clear faults: not while moving"). Open beside is allowed while
  moving only if it replaces a tile. "Show sizes" is never shown while moving.
- **§21 owner rulings** (after a safety review that found 29 gaps): **every touch target is at
  least 60 dp while moving** (`space.touchMinMoving`, the alert tab included, ACK buttons
  raised from 56 dp to 60 dp). **All text is at least 24 dp while moving**, labels included.
  **Unknown motion** means a missing or stale value, an unreachable Gateway, a new host, or a
  value the shell doesn't know such as `idling`, and it counts as moving. Alerts stay above
  edit mode.
- **Drive-modes spec** (`specs/2026-10-07-drive-modes-and-editing-design.md`, partly
  superseded): long-pressing while Moving shows "Park to edit". If the car starts Moving
  mid-edit, the draft is kept and "Finish editing when parked" appears. Mode switching stays
  one tap.

### 2.3 Shell code (`openostler/ostler-shell`src/motion/`)

- `rules.ts`: `MotionState = "moving" | "parked" | "unknown"`, and `isMoving(s)` is
  `s !== "parked"`. `toMotionState` maps **anything else, `idling` included, to unknown**, so
  idling is treated as moving.
- `canDo(action, state)` uses a fixed list of shell actions. Allowed while moving: change page
  or layout by wheel or trigger, stack badge, full screen, focus, ACK, Diagnose, alerts list,
  browse settings. Blocked: swipe page (silently), edit layout, hold, resize, save layout,
  change settings, open a parked-only page. Each refusal has a one-line toast ("Park to edit
  the layout", "Park to change settings", "Park to open {page}").
- Each page sets a `moving` field: `"safe" | "reduced" | "parkedOnly"`. `pageMode()` returns
  `full`, `reduced` (the page gets `ctx.moving = true` and draws its reduced form) or
  `blocked` (summary plus "Park to open").
- `motionEffects`: no effects, solid instrument tiles, text-only toasts, page changes **cut**
  rather than slide, fades ≤ 150 ms. `textSize` sets text to at least 24 dp and `targetSize`
  sets targets to at least 60 dp (48 dp parked), from the generated tokens.
- `onMotionChange`: when moving starts, edit mode closes with its edits kept as "Edited", any
  drag is cancelled, and one toast shows.
- `effective.ts`: the Gateway sends a heartbeat every **1 s**. A report is **stale at 3 s**,
  and stale, unreachable, no report yet, or a new host all give **unknown**. No speed is used
  in the shell; the Gateway decides the state.
- `ThemeProvider` refuses theme changes while moving. With no motion supplied, it defaults
  to moving.
- **Not in the code:** the spec's `actionGate` with per-action `MovingSafety` and `confirm`,
  the forced kinds (`typing`, `clear-faults`, `actuator-test`, `video`), `hideWhileMoving`,
  `minTextPx` and `canChangeSettings`. Those were replaced by the guide's simpler model
  (ADR-0052 v0.8, shell spec §20). The per-action rules live on the server gate and in each
  app.

### 2.4 Drift inside Ostler that matters for this comparison

1. The **UI spec has four states** with an Idling + Park-evidence tier. The **shell code has
   three**, and treats idling as moving. The shell is therefore stricter than the platform
   while stopped in traffic. That is safe, but layout edits are refused at red lights even
   when there is Park evidence, and the spec's "parked or idling" for `layoutEditAllowed` no
   longer holds.
2. **Touch-target sizes:** the platform templates use px (digits ≥ 56 px), the shell's §21
   uses 60 dp, AAOS design guidance uses 76 dp and the parked video guidance 64 dp. Ostler's
   moving target is below Google's driving recommendation.
3. **Thresholds** (5 km/h / 2 km/h / 2 s / 3 s / 5 s) appear only in the UI spec. Shell spec
   §20 delegates the state to the Gateway, and no Gateway-side spec was found that restates
   the thresholds for the v2 three-state feed.

---

## Part 3: comparison

| AAOS mechanism | Ostler equivalent | Status | Recommendation |
|---|---|---|---|
| **Driving state inferred from VHAL** (gear Park, else handbrake on a manual, else speed 0 or not, else ignition) | Server state from vehicle speed, then GPS, then proven gear/handbrake (UI spec §3.5). The shell only receives `moving/parked/unknown` from the Gateway. | aligned | Keep. Write the v2 Gateway's derivation down in one place (thresholds, sources, Park evidence) so the shell's three states trace back to it. |
| **Four states: PARKED / IDLING / MOVING / UNKNOWN** | Platform: Parked / Idling (+ Park evidence) / Moving / unknown. Shell code: moving / parked / unknown, with idling counted as unknown and therefore moving. | different on purpose (shell), with a gap between platform and shell | Either add `idling` with an `evidence` flag back into the shell feed, or record in the UI spec that the shell treats Idling as Moving and that Gateway "parked" already requires Park evidence. Today the two documents disagree. |
| **Speed thresholds per state** (`minSpeed`/`maxSpeed` in m/s, half-open bands; reference 0 and 5 m/s) | One fixed band: Moving above 5 km/h for 2 s, leaving below 2 km/h for 3 s, with hysteresis that AAOS lacks. `camera_live` has its own limit (10 km/h). | different on purpose | Keep the hysteresis; it is better than AAOS's raw "speed ≠ 0". Only add speed bands if a real feature needs them, for example cameras allowed below 10 km/h. Units: VHAL is m/s, VSS `Vehicle.Speed` is km/h. |
| **Per-state restriction config XML** (OEM overlay; staged and applied only when parked) | No data-driven map. Rules are code (`rules.ts` lists), the ADR-0033 category table and spec prose. The owner may tune some numbers within platform caps (openness round, ADR-0047). | gap (deliberate in part) | Consider a small versioned `ostler.motion-rules/1` document on the Gateway: state → allowed categories and actions, plus limits. Load it fail-closed, and apply changes only when parked, as AAOS stages them. That gives one source for server, shell and apps and lets owner tuning stay within caps the platform checks. |
| **Apps learn restrictions, not state** (`CarUxRestrictions` bit mask + 3 limits, by listener) | Pages get `ctx.moving: boolean` and `motion`. Page `moving: safe/reduced/parkedOnly`. The server gate refuses actions. | different on purpose | Consider giving pages a restrictions object (`{noKeyboard, noVideo, maxString, maxItems, maxDepth}`) as well as `moving`, so third-party iframe pages get the numbers from one place instead of reading the spec. |
| **Baseline** (requiresDO, no flags: only DO activities, follow guidelines) | `reduced` pages, plus the templates on the platform side. | aligned | None. |
| **Fully restricted** (all 9 flags; the fail-closed default) | "Fail closed: a view with no `moving` rule, or a missing restriction config, is fully locked". `parkedOnly` → blocked. | aligned | None. |
| **`distractionOptimized` manifest tag**, trusted by the platform and checked by store review | Page contract `moving`, declared by the app and trusted by the shell. Ostler has no store review, but experimental templates go through a measurable validator. | aligned (same trust model) | Add a CI or registry check: a page declaring `safe`/`reduced` is rendered from fixtures at moving size and checked for the 24 dp text floor, the 60 dp targets and no video. This is the nearest thing Ostler can have to Play review. |
| **Unknown state → fully restricted; moving with no speed → highest band** | Unknown counts as moving everywhere. Stale after 3 s with a 1 s heartbeat; Gateway unreachable, a new host or an unknown value all give unknown. The theme defaults to moving. | aligned, and Ostler is stricter | Keep. Ostler adds staleness and heartbeat rules that AAOS lacks. |
| **Boot leaves restrictions open until the first state** | Ostler starts unknown, so a new host is locked. | different on purpose | Keep Ostler's choice. It is safer, and the cost is a second of "Motion unknown" at start-up. |
| **Passenger via per-display maps or a system-set `mode`** | Head units are all driver-facing; an owner install setting marks a screen passenger-only (the same idea as AAOS geometry). Per-trip **Passenger view** on head units is limited to reg 109 content, re-prompted and timed out. Phones can be marked as passenger devices. **Not in the shell code yet.** | different on purpose (stricter on content; per-trip prompt AAOS doesn't have) and gap (not built) | Keep geometry first. When built, model Passenger view as a server-held **mode** like `setRestrictionMode`, never an app flag. On the AAOS head unit, use AAOS's own occupant-zone maps for any rear screens rather than Ostler's prompt. |
| **`LIMIT_STRING_LENGTH`** (120 characters by default) | Templates: 30 characters a line by default, raisable up to 120. Alert cards ≤ 2 lines. The shell has no general string cap. | aligned (stricter) | Keep. Expose the cap to pages (see the restrictions-object row). |
| **`LIMIT_CONTENT`** (21 cumulative items, depth 3) | `short_list` ≤ 6 rows, one level; `tiles` ≤ 6; task ≤ 3 screens. Nothing measures cumulative items across a task. | aligned on depth; gap on cumulative counting | 6 rows × 3 levels is at most 18, which already sits under 21. Note this in the spec so the numbers trace to AAOS. No new mechanism is needed. |
| **`NO_KEYBOARD` / `NO_FILTERING`** | No typing while moving (ADR-0052 §5). Text entry needs Park evidence while Idling. The keypad is Parked only. No search on the `map`. The shell code has **no typing action** to refuse; it is left to apps and the server. | aligned in policy; gap in the shell | Add `typing` (or `keyboard`) to the shell's blocked list, or provide a shell input wrapper that refuses focus while moving, so third-party pages can't show a keyboard. |
| **`NO_DIALPAD`** | Keypad Parked, or Idling with Park evidence; voice dial and favourites list while Moving. | aligned | None. |
| **`NO_VIDEO`** (no animated frames above 1 fps); DD-2/DD-3 video, games and browsers not launchable | No video while moving except driving cameras (reverse and low-speed `camera_live`; front and side road cameras off pending the legal opinion). Effects off, page changes cut, fades ≤ 150 ms, `tiles` refresh ≤ 4 Hz, no animated needles except red alarms. The shell code has **no video gate**; a `reduced` page could play video. | aligned in policy; gap in the shell | Borrow AAOS's measurable definition ("no animated frames above 1 fps, except driving cameras") and have the shell enforce it, for example by blocking `<video>` in reduced pages and in iframes while moving, unless the page is a declared camera. |
| **`NO_SETUP` / Car Settings DO** (most preferences greyed out, "not available while driving" toast) | "Park to change settings". Browsing is allowed, changes are refused with a toast. Theme changes are refused. | aligned | Consider AAOS's whitelist (`config_ignore_ux_restrictions`) for the few settings that are safe at speed, such as brightness and day/night. |
| **`NO_TEXT_MESSAGE`** | Message alert cards show sender and app only, no text; Play and Reply by voice; canned replies; rate limits. | aligned (more detailed) | None. |
| **`NO_VOICE_TRANSCRIPTION`** | No transcript text while Moving (§12.1 and §14). | aligned | None. |
| **Activity blocking by the system** (non-DO activity replaced by a blocking screen) | `parkedOnly` page → summary plus "Park to open {page}". Opening one is refused with a toast. | aligned | None. |
| **Edit mode / launcher editing** (AAOS launchers aren't editable while driving under DO) | Edit mode, hold, resize and save are refused while moving. When moving starts mid-edit, edit mode closes with the edits kept and the drag cancelled. Layout switching by wheel or trigger is allowed. | aligned | None. |
| **Touch targets 76 × 76 dp, 23 dp gaps; text 32/24 dp** (Design for Driving) | 60 dp targets and 24 dp text while moving, 48 dp parked. | gap (smaller than Google's driving guidance) | Record why 60 dp is enough on 5–10″ head units, or raise the moving targets toward 76 dp on HU classes. Cite the AAOS figure in shell spec §21. |
| **2 s glance; interruptible tasks** | NHTSA 2 s / 12 s cited as normative for U2. When moving starts, the edit draft is kept ("Finish editing when parked"). | aligned | Add a glance test (occlusion-style) to the U2 acceptance list if feasible. |
| **Per-display restrictions** (`physicalPort`, occupant zones) | An owner install setting for a passenger-only display. A **cluster** or second screen run by the shell gets the same rules as the head unit. | aligned in concept | None. |
| **Category rules for actions** (no AAOS equivalent: AAOS restricts UI, not car writes) | ADR-0033 categories, with every action re-checked on the server. Bus writes are Parked-only. | Ostler-only (beyond AAOS) | Keep. AAOS has nothing comparable for car-control actions. |

### 3.1 Could Ostler drive AAOS's driving state on the owner's head unit?

**Yes, and it fits the planned Ostler-fed VHAL** in
`openostler/ostler-android-automotive`lineage/vendor/headunit/vhal/README.md`: "a
vendor VHAL that subscribes to the Ostler Brain's VISS v3 server … and maps VSS signals to VHAL
properties". `scripts/vhal-inject.sh` already sets `GEAR_SELECTION` and `PERF_VEHICLE_SPEED`
(0x11600207) through `cmd car_service inject-vhal-event`, which proves the path into
`CarDrivingStateService`. The proposed mapping:

| VHAL property | Fed from (VSS over VISS) | D2 notes |
|---|---|---|
| `PERF_VEHICLE_SPEED` (m/s) | `Vehicle.Speed` ÷ 3.6 | Td5 speed while the Td5 holds K-line, else GNSS. **Missing in a SLABS session**, so GPS must cover it. |
| `GEAR_SELECTION` / `CURRENT_GEAR` | `Vehicle.Powertrain.Transmission.SelectedGear` | Manual R380: there is no Park, so declare supported gears **without `GEAR_PARK`** so AAOS treats the car as manual. On a 4HP22 auto, map P. Gear and park/neutral are BCU/SK-bus signals, not yet proven. |
| `PARKING_BRAKE_ON` | `Vehicle.Chassis.ParkingBrake.IsEngaged` | The handbrake switch drives the pack's brake lamp (shared with fluid level and SLABS). It is **not yet a proven Ostler signal**. Until it is, AAOS can only reach PARKED from ignition. |
| `IGNITION_STATE` | `Vehicle.LowVoltageSystemState` | Lets AAOS reach PARKED when speed is unavailable. |

There are two ways to map it. The second is preferred.

1. **Feed raw signals and let AAOS infer.** This is simple, but AAOS has **no hysteresis** (any
   non-zero speed means MOVING, so GPS jitter at standstill flickers the restrictions). It
   ignores Ostler's Park evidence and stale-data rules, and it has the open-at-boot hole.
2. **Feed Ostler's verdict.** The VHAL synthesises properties from the Gateway's motion state:
   - `moving`: the real speed (clamped to ≥ 0.5 m/s so it never reads 0) and a non-park gear;
   - `parked`: speed 0 and `PARKING_BRAKE_ON = true`, with gears declared manual;
   - `unknown` or stale (no VISS update for 3 s): mark `PERF_VEHICLE_SPEED` and the brake
     `UNAVAILABLE` and leave `IGNITION_STATE` unset. AAOS then infers **UNKNOWN**, which the
     default config maps to fully restricted.

   Both layers then agree. AAOS has no state for "moving, speed known only as stale", so the
   unavailable route is the honest way to signal it.

Also needed:

- **Close the boot gap.** AAOS starts unrestricted until a state arrives. Have the VHAL
  publish UNAVAILABLE speed at once (giving UNKNOWN, then fully restricted under the default
  config), or ship an XML that leaves out `requiresDistractionOptimization=false` for anything
  but parked.
- **Ship our own `car_ux_restrictions_map.xml` overlay** (in `lineage/vendor/headunit/`) that
  states Ostler's choices: parked baseline; idling the same as moving (matching the shell);
  moving with every flag except perhaps `no_voice_transcription`, and add that one too, since
  §12.1 forbids transcripts; `maxLength` 120 (the AAOS ceiling; Ostler's own 30 applies inside
  Ostler pages); `maxCumulativeItems` 18; `maxDepth` 3.
- **Car Maps and Waze** follow `CarUxRestrictions`, so their keyboard and search lockouts will
  then follow Ostler's state. That is the main safety benefit for the stated goal ("car Maps
  and Waze fed by Ostler").
- **The Ostler shell inside AAOS** (the Gateway Android app or a WebView). It should keep
  taking motion from the Gateway, not from `CarUxRestrictionsManager`, so there is one source.
  It must also be tagged `distractionOptimized`, or AAOS will block it while moving. Optionally,
  check the two agree and show "Motion unknown" when they don't.
- **Rear or passenger screens** (docs/ideas.md "Passenger screens") should use AAOS occupant-
  zone `RestrictionMapping` rather than Ostler's per-trip prompt.
- **Where it lives:** the VHAL README says the VSS-to-VHAL table "belongs in the ostler repo".
  The motion-state-to-VHAL synthesis rules above should go with it, as a spec in
  `ostler-shellspec/specs/` before any code (repo working rule).

---

## Sources

### AAOS and Android (fetched 2026-10-15)
- Driver distraction guidelines: https://source.android.com/docs/automotive/driver_distraction/guidelines
- Car UX Restrictions rules: https://source.android.com/docs/automotive/driver_distraction/car_uxr
- Consume driving state and UX restrictions: https://source.android.com/docs/automotive/driver_distraction/consume
- Distraction optimization in Car Settings: https://source.android.com/docs/automotive/hmi/car_settings/do_car_settings
- `CarUxRestrictions` reference: https://developer.android.com/reference/android/car/drivingstate/CarUxRestrictions
- `CarUxRestrictions.Builder` reference: https://developer.android.com/reference/android/car/drivingstate/CarUxRestrictions.Builder
- Car app quality guidelines: https://developer.android.com/docs/quality-guidelines/car-app-quality
- Design for Driving foundations: https://developers.google.com/cars/design/design-foundations/about-design-foundations
- Visual principles (76 dp, 120 characters): https://developers.google.com/cars/design/design-foundations/visual-principles
- Interaction principles (2 s, discourage distraction): https://developers.google.com/cars/design/design-foundations/interaction-principles
- Define user tasks: https://developer.android.com/design/ui/cars/guides/foundations/define-user-tasks
- Design for driving (new home): https://docs.partner.android.com/drivingux
- Video apps (64 dp / 24 dp): https://docs.partner.android.com/drivingux/automotive-os/app-experience/video
- AOSP source, default restriction map: https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/service/res/xml/car_ux_restrictions_map.xml
- AOSP source, `CarDrivingStateService.java`: https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/service/src/com/android/car/CarDrivingStateService.java
- AOSP source, `CarUxRestrictionsManagerService.java`: https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/service/src/com/android/car/CarUxRestrictionsManagerService.java
- Policy background: NHTSA Phase 1, 78 FR 24818: https://www.govinfo.gov/content/pkg/FR-2013-04-26/html/2013-09883.htm ; NHTSA Phase 2 proposal: https://www.govinfo.gov/content/pkg/FR-2016-12-05/html/2016-29051.htm ; ESoP 2008/653/EC: https://eur-lex.europa.eu/eli/reco/2008/653/oj ; ESoP, AAM and JAMA overview: https://wbldb.lievers.net/10094513.html ; NHTSA compared with ESoP and AAM: https://wbldb.lievers.net/10138789.html ; NHTSA Phase 2 coverage: https://techcrunch.com/2016/11/23/nhtsa-spells-out-what-your-phone-shouldnt-be-able-to-do-while-driving/
- Third-party explainer (secondary): https://appning.com/newsroom/incorporating-driver-distraction-guidelines-into-aaos-apps/

### Ostler files
- `openostler/ostler`references/research/driver_distraction_rules.md`
- `openostler/ostler`specs/2026-10-06-ui-architecture-design.md` (§3.5, §12.1)
- `openostler/ostler`specs/2026-10-11-ostler-shell-design.md` (§7, §9, §18, §19, §20, §21)
- `openostler/ostler`specs/2026-10-07-drive-modes-and-editing-design.md` (§4.3, §6, §7, §8)
- `openostler/ostler`decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md` (§5, §9)
- `openostler/ostler`decisions/adr-0033-action-categories-and-approvals.md` (§1)
- `openostler/ostler`references/design/2026-10/shell-session/IMPLEMENTATION.md` (§6, §10)
- `openostler/ostler`specs/2026-10-07-phone-comms-addon-design.md`, `2026-10-07-social-addon-design.md`, `2026-10-06-app-model-design.md` (Park evidence, `camera_live`)
- `openostler/ostler-shell`src/motion/rules.ts`, `effective.ts`, `react.ts`, `rules.test.ts`, `effective.test.ts`
- `openostler/ostler-shell`src/contract/page.ts`, `src/contract/host.ts`, `src/strings/table.ts`, `src/surfaces/refusal.ts`, `src/theme/ThemeProvider.tsx`, `src/theme/kitTokens.generated.ts`
- `openostler/ostler-android-automotive`README.md`, `lineage/vendor/headunit/vhal/README.md`, `scripts/vhal-inject.sh`, `docs/experiments.md`, `docs/ideas.md`
- `openostler/ostler-pack-lr-d2`references/research/instrument-pack/wiring.md`, `references/menus/bcu-inputs.md` (handbrake and park/neutral signal status)
