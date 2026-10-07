---
title: "Driver-distraction rules — Android for Cars, CarPlay, NHTSA, ESoP, UK law, passenger modes and liability (Oct 2026)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, references/research/ui/head_unit_ui.md, references/research/ui/app_model.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md]
summary: >
  Live research (2026-10-07) on the rules a driver-facing Ostler screen must follow: Android Auto and Automotive (categories, five-step tasks, list limit 6, pane 4, AAOS 120-character strings, 21 items, depth 3, per-display passenger restrictions), CarPlay (categories, depth 3 for Driving Task, no data refresh faster than every 10 s, no maintenance features), NHTSA (voluntary, original equipment only, 2 s / 12 s, purpose-based lockouts; the 30-character rule was dropped in the final text; "driving" includes idling in gear), the European Statement of Principles, UK Construction and Use regs 109 and 110 and Highway Code rule 149, passenger modes (Waze, Google Maps, Tesla Passenger Play) and liability. Evaluates the owner's lockout model, separates what is required from what is advised, and gives wording for UI spec §3.5 and app-model §4.4.
---

# Driver-distraction rules and the "I'm a passenger" override

**Question (owner, 2026-10-07):** strict driver-safe templates only on the driver-facing head
unit while Moving; guidelines plus review elsewhere; a Waze-style per-trip "I'm a passenger"
override (re-prompts, no "always", logged, view-only); a template set of map, media, gauge/tile
grid, alert card and short list that add-on authors extend by proposal. What is required, what
is advised, what is missing, and how should the spec say it?

Builds on [head-unit UI research](ui/head_unit_ui.md) (hard numbers, production patterns) and
[app-model research](ui/app_model.md) §1.1–1.2 (categories and host-drawn templates); this note
does not repeat them. It corrects one row there (§3.3). Not legal advice: §7 lists what a
lawyer should confirm.

## 1. The rules at a glance

| Source | Binding? | Covers Ostler? | What it asks |
|---|---|---|---|
| Android for Cars (Auto and AAOS) | only for Play distribution | only a future Android Auto companion | categories, host templates, ≤ 5 steps, list limits (§2) |
| CarPlay | only for an Apple entitlement | only a future CarPlay companion | categories, templates, depth, refresh caps (§2.2) |
| NHTSA Phase 1 (2013) | **no**: voluntary, no force of law | written for original equipment; aftermarket "encouraged" | 2 s / 12 s glances, purpose-based per se lockouts (§3) |
| NHTSA Phase 2 (proposed 2016) | no; **never finalised** (none found) | aimed squarely at aftermarket and phones | pair with the car, or a **Driver Mode** (§3.4) |
| European Statement of Principles (2008/653/EC) | **no**: a Commission recommendation | yes: OE, aftermarket and nomadic devices by name | non-driving visuals off or unseen while moving; non-driving functions "impossible" for the driver (§4.1) |
| UK Construction and Use reg 109 | **yes**: an offence for the driver (and whoever causes or permits) | yes, any screen the driver can see | a driver-visible screen shows only vehicle state, location/road, view of the road, or navigation (§4.2) |
| UK reg 110 and Highway Code rule 149 (2022 law) | **yes** for hand-held use | the phone, when held | no hand-held use while driving, even stopped in traffic (§4.3) |
| Vienna Convention 1968 art. 8(6); EU GSR ADDW | treaty / type approval | indirectly | drivers minimise other activity; new EU cars warn after eyes-off-road (§4.4) |

**Reading:** almost nothing forces a design on Ostler as a *product*; UK law forces it on the
*driver*, and liability (§6) makes the platform's design choices evidence either way. The
practical bar is therefore "what a court, a regulator or a store reviewer would expect of a
competent aftermarket screen", which is NHTSA plus ESoP plus the platform store rules.

## 2. Android for Cars and CarPlay (checked 2026-10-07)

### 2.1 Android Auto and Android Automotive

- **Categories.** Car App Library apps that run while driving: navigation, point of interest,
  IoT, weather (media and messaging have their own APIs). **Parked-only:** video, games,
  browsers and "adaptive" apps, which must not launch or play audio while driving
  (quality criteria DD-2/DD-3) [G1][G2].
- **Task budget.** ≤ 5 templates per task; the last must be a terminal type (navigation, pane,
  message, media playback, sign-in, long message); same-template refreshes are free; going back
  restores quota; exhausting it makes the host show an error and **close the app** [G3].
- **Content limits** are set by the host per car and read at runtime; the library's fallback
  minimums are **list 6, grid 6, place list 6, route list 3, pane 4 rows** [G4][G5].
- **Quality rules for driving categories:** no animated elements (canvas animation only when
  parked and relevant), no auto-scrolling text, notifications only when relevant to driving
  (SA-1, ST-1, IN-1) [G2]. Parked-category apps: targets ≥ 64 dp, 24 dp apart, text ≥ 24 sp.
- **AAOS restrictions engine.** Default map: Parked unrestricted; **Idling = no video only**;
  Moving = no dialpad, no filtering, limited strings, no keyboard, no video, limited content,
  no setup, no text messages. Defaults: **strings ≤ 120 characters, ≤ 21 cumulative items,
  depth ≤ 3**. Missing or malformed config falls back to **fully restricted** [A1].
- **Passengers in AAOS are a display property, not a button.** Restrictions can be set per
  physical display or per occupant zone, and a "passenger" mode string exists for OEMs; a
  passenger screen gets its own map [A1]. Apps opt in per activity with
  `distractionOptimized`; the platform trusts the tag and Play review checks behaviour [A2].

### 2.2 CarPlay (Developer Guide, June 2026)

- **Categories** (entitlements): audio, communication, driving task, EV charging, fueling,
  navigation, parking, public safety, quick food ordering, video (new, iOS 27, parked use) and
  voice-based conversational; plus widgets and Live Activities [C1][C2].
- **All apps:** built for their category's purpose; never tell people to pick up the phone;
  every flow possible without the phone; **no features unrelated to the primary task
  ("unrelated settings, maintenance features")**; no gaming or social networking; never show
  message content; templates only for their intended purpose [C2].
- **Driving Task apps:** must help with the drive, not merely happen during it; templates only
  (no custom maps, no real-time video); no account setup or detailed settings; **no data item
  refreshed more often than every 10 s ("no real-time engine data")**; POIs at most every 60 s;
  not a location finder; no use outside the vehicle [C2].
- **Templates and limits:** Driving Task may use action sheet, alert, grid (≤ 8 items), list,
  tab bar (≤ 5 tabs), information, point of interest and voice control; **depth 3 including the
  root** (2 before iOS 26.4); some cars cap lists at **12 items** while driving [C2].

**Implication for a thin CarPlay companion:** live gauges are explicitly out of the Driving
Task category, and maintenance screens are out of every category. A CarPlay companion can
carry alerts, a Mark button, climate/arm controls and a trip summary refreshed ≥ 10 s apart;
a live-gauge CarPlay screen like the one the owner admires is a policy risk, not a template
gap (see [app teardown](app_teardown_speedometer.md)). Android Auto's IoT category
fits car controls better and has no 10 s cap, but has no gauge template either.

## 3. NHTSA (US)

### 3.1 Status
Phase 1 (78 FR 24818, 26 April 2013) says outright it has no force of law and is not a
regulation; it covers original-equipment interfaces the driver can see or reach, "even if
intended for use solely by front seat passengers", and nothing located only behind the front
seats [N1]. Aftermarket and portable makers were asked to adopt what is "feasible", pending
Phase 2 [N1].

### 3.2 Numbers and lockouts
- **Acceptance (eye glance):** for ≥ 21 of 24 drivers, mean glance ≤ 2.0 s, ≤ 15 % of glances
  over 2.0 s, total eyes-off-road ≤ 12 s; or occlusion: 1.5 s views, ≤ 12 s total shutter-open
  time. Baseline task: manual radio tuning [N1].
- **Per se lockouts (final):** non-driving video; non-driving graphical or photographic images
  (maps, rear-camera and short-lived task-selection images excepted); auto-scrolling text;
  manual text entry for messaging, communication or browsing; reading text from books,
  publications, web pages, social media or messages [N1].

### 3.3 Two corrections for our docs
1. **The 30-character limit is not in the final guidelines.** The 2012 proposal locked out
   reading > 30 characters and text entry > 6 presses; the final text replaced both with the
   purpose-based lockouts above [N1]. [head_unit_ui.md §1](ui/head_unit_ui.md#1-hard-numbers-the-rules-we-should-design-to)
   lists it as an NHTSA lockout. Our "≤ 30 characters a line" in UI spec §3.5 is still a
   good design limit; cite it as ours (and the AAOS 120-character string cap as the platform
   ceiling), not as NHTSA's.
2. **NHTSA's "driving" includes Idling.** Driving means propulsion is on unless the
   transmission is in Park; for a car with no Park position (the Td5 manual), only when the
   parking brake is on **and** the box is in neutral (sensed, or inferred from engine speed ÷
   driven-wheel speed matching no gear ratio) **and** speed < 5 mph [N1]. Our Idling (engine
   running, speed 0) allows text entry and Maintenance, which NHTSA would call driving when
   the car is merely stopped in traffic. ESoP also asks for a few seconds' delay after a stop
   before non-driving visuals return [E1]. The D2 has engine speed and SLABS wheel speeds, so
   the ratio inference NHTSA accepts is available to us once both are proven.

### 3.4 Phase 2 (portable and aftermarket, proposed Dec 2016)
Proposed pairing with the car's interface, or a **Driver Mode** on the device, ideally
automatic when the device can tell a driver is driving and **not** active for a passenger;
because driver-passenger distinction was immature, NHTSA allowed **manual activation as a
temporary option** and admitted its "inherent limitations" [N2]. No final version was found
(searched 2026-10-07; treat as unverified absence).

## 4. Europe and the UK

### 4.1 European Statement of Principles on HMI (Recommendation 2008/653/EC)
Scope names OE, aftermarket and **nomadic** devices and their app/service providers [E1]. The
principles that bear on the override (read from the Official Journal text, Spanish edition;
the English PDF could not be fetched):
- **System behaviour I:** while moving, non-driving visual information likely to distract
  noticeably (video, auto-scrolling images and text; web pages judged against these) must be
  switched off automatically or shown only where the driver cannot see it. Driver-paced
  scrolling lists are fine. The "bad" example is **passenger entertainment the driver can see
  while moving**; recommended: a few seconds' delay after stopping [E1].
- **System behaviour III:** functions not meant for the driver while driving must be
  **impossible** to use while moving, including under **reasonably foreseeable misuse**; the
  "less preferable" fallback is a clear warning, ideally acknowledged by a button press. The
  bad example is a TV lockout tied to a handbrake sensor that a partly pulled handbrake
  defeats [E1].
- **Interaction:** short sequences may be uninterruptible; long ones must survive
  interruption and resume where they stopped [E1].
- **Information IV:** instructions must say plainly which functions are meant for the driver
  while driving and which are not [E1].

A driver tapping "I'm a passenger" is the textbook foreseeable misuse (§5.2), so on a
driver-visible screen the override is at best ESoP's "less preferable" warning route, and it
can never lawfully cover Principle I content.

### 4.2 UK: regulation 109 (screens visible to the driver)
No one may drive, or cause or permit driving, where the driver can see (directly or by
reflection) a "television receiving apparatus or other cinematographic apparatus" displaying
anything other than information about **(a) the state of the vehicle or its equipment, (b) its
location and the road, (c) the road adjacent to the vehicle, or (d) reaching the destination**
[U1]. The definition still says "cathode ray tube" showing images from broadcast, recording,
camera or computer; whether a court reads that onto an LCD head unit is untested as far as we
found (unverified; assume it applies). Consequence: in the UK a passenger override cannot make
social feeds, other people's vehicles, messages, video, clip playback, Docs or Analysis
lawful on the head unit while it is visible to the driver. Diagnose live data and telltales
fit (a); the own-car map fits (b) and (d); reverse and low-speed cameras fit (c).

### 4.3 UK: regulation 110 and Highway Code rule 149 (the 2022 phone law)
Since 25 March 2022 "using" a hand-held phone or other interactive device covers almost any
use (screen, notifications, apps, photos, browsing), while driving and while stopped in
traffic; exemptions: 999/112 when stopping is unsafe, contactless payment while stationary,
remote parking within 6 m [U2][U3]. A device in a cradle is not "hand-held", but rule 149
says hands-free use is still distracting and drivers **MUST** keep proper control; rule 150
says the same of in-vehicle systems [U3]. For Ostler: the phone is lawful for a **passenger**
in any state; for the driver only cradled, and then reg 109 applies to what it shows.

### 4.4 Treaty and type approval
Vienna Convention art. 8(6): drivers minimise activity other than driving; parties must ban
hand-held phone use in motion [V1]. UNECE has no binding regulation on infotainment HMI that
we found (unverified). The EU General Safety Regulation's Advanced Driver Distraction Warning
(camera driver monitoring) is mandatory on new EU cars from 7 July 2026 [V2]; it does not
reach a 2003 Discovery, but it shows where expectations are heading.

## 5. Passenger modes in practice

| Product | Where the override lives | What it unlocks | Outcome |
|---|---|---|---|
| **Waze (phone)** | phone, on the keyboard lockout | typing (search, reports) | widely used; users and press describe drivers "lying" to it [W1] |
| **Waze / Google Maps on Android Auto** | **none on the car screen** | — | typing needs Park and handbrake; the phone app now stays usable during projection so a **passenger uses the phone** (Maps 2023, Waze 2025) [W2][W3] |
| **Android Auto / CarPlay hosts** | none | — | keyboard and list limits are absolute; cars may tighten them [G4][C2] |
| **AAOS** | a passenger **display** or occupant zone | that display's own restriction map | the OEM decides by geometry, not by asking [A1] |
| **Tesla Passenger Play (2020–21)** | centre screen | games while moving | NHTSA opened PE21-024 (≈ 580 000 cars); Tesla locked games to Park by OTA within a month; closed May 2023 without recall, citing **apparent driver use on about a third of trips** with it in use [T1][T2] |

**The lesson:** every major platform keeps the driver-visible car screen locked and moves the
passenger to their own device or their own display. The one shipped centre-screen passenger
unlock for non-driving content (Tesla) was used by drivers often enough to draw a federal
investigation and was withdrawn.

## 6. Liability exposure for an open-source project

- **Licence disclaimers bind licensees, not victims.** AGPL-3.0 §§15–16 limit warranty and
  liability toward users; an injured third party never agreed to them (ADR-0012).
- **Design-defect claims survive "it's just software".** *Lemmon v. Snap* (9th Cir. 2021):
  Section 230 did not bar a negligent-design claim over a feature that rewarded speeding
  while driving [L1]. Contrast *Modisette v. Apple* (Cal. Ct. App. 2018): dismissed for no
  duty and no proximate cause over FaceTime while driving [L2]. Courts have gone both ways;
  a feature that *invites* in-motion use is the riskier shape.
- **EU Product Liability Directive (EU) 2024/2853** treats software as a product for items
  placed on the market after **9 December 2026**; free open-source software supplied outside
  a commercial activity is excluded, but a charged service or data-for-service revives it
  [L3]. Ostler funds itself by hardware sales, a cloud subscription and commercial licences
  (ADR-0012), so the shipped product is in scope. The UK's 1987 Act is under review on
  software (unverified).
- **What helps:** a documented, platform-standard design (templates, server enforcement);
  following ESoP III's order (impossible first, warning only as fallback); instructions that
  say which functions are for the driver (ESoP IV); tests that prove the lockouts. **What
  hurts:** an override the platform knew drivers misuse, a persisted "always", or a log that
  shows misuse the project ignored.
- **The override log cuts both ways.** It is evidence the user affirmed being a passenger, and
  a record of possible driver misuse. It is personal data (GDPR): keep it local, minimal,
  owner-visible, never shared or uploaded by default (ADR-0029, ADR-0036 spirit).

## 7. Evaluation of the owner's model

| Element | Verdict | Basis |
|---|---|---|
| Templates only on the driver-facing head unit while Moving | **Required** in substance (UK reg 109 for content; ESoP I/III; every platform) | §2, §4 |
| "Driver-facing" | **Gap:** must mean any screen the driver can see or reach (NHTSA, reg 109 wording), not the screen labelled "driver". Every head-unit class is driver-facing; only an install-level declaration of a screen out of the driver's sight (rear seat) can opt out | §3.1, §4.2 |
| Moving rule for Idling-in-traffic | **Gap:** NHTSA and ESoP treat stopped-in-gear as driving; our Idling unlocks text entry | §3.3 |
| Guidelines plus review elsewhere (phone, desktop, cloud) | **Advised; fine.** A held phone is the driver's legal problem (reg 110), not a product rule; keep phone Moving banner and the gate's stationary checks | §4.3, UI spec §3.5 |
| Per-trip "I'm a passenger" on the head unit | **Advised against for non-driving content; acceptable for driving-related content.** UK law and ESoP I forbid non-driving visuals the driver can see, whoever asked; Tesla shows the misuse rate | §4, §5 |
| Re-prompt after stop or new trip, no "always" | **Required if the override exists** (ESoP III warning route; Phase 2's "inherent limitations") | §3.4, §4.1 |
| Logged | **Advised**, local only, minimal | §6 |
| View-only | **Required:** no text entry, no actions, no tier change; the server gate is unchanged | NHTSA text entry; ADR-0033 |
| Template set map, media, tiles, alert card, short list | **Advised**, with limits below; extend only by platform proposal | §2, app-model §4.4 |

### 7.1 Gaps the model does not cover
1. **Display geometry.** Head units are driver-facing by default; no user-level toggle.
2. **Idling-in-traffic.** Text entry and Maintenance need proven Park evidence.
3. **Override scope by content class,** not by view: reg 109 classes (a)–(d) only, on a
   driver-visible screen.
4. **Hand-off to a phone** as the preferred passenger path (Waze/Maps pattern).
5. **Exit and fail-safe:** the override ends on Parked, ignition off, new trip, unknown speed
   on a head unit, service-mode entry, reverse, any red telltale, and on a timeout.
6. **Server-side state.** The override is a server state keyed to trip and display; an app
   cannot set or read it as "unlocked", only render what the shell allows.
7. **Instructions (ESoP IV):** a "Using Ostler while driving" page listing driver-safe and
   parked-only functions.
8. **Companion apps** inherit the platform rules (§2) on top of ours: no live gauges or
   maintenance on CarPlay; a 5-step budget on Android Auto.
9. **Other people's data on the map** (Vehicles & Map, Social): reg 109 (b) covers *your*
   vehicle; names, avatars and photos are non-driving images (NHTSA). Show no other vehicles
   while Moving on a head unit, or at most convoy members as plain markers (decide below).
10. **Alerts from add-ons** (Social messages, calls) must not show message content on the
    head unit while Moving (CarPlay rule, NHTSA lockout); a message alert reads "New message
    from a friend" with no text, or audio only.

### 7.2 Template limits (recommended)

| Template | Limit while Moving | Notes |
|---|---|---|
| `map` | own position, route, next manoeuvre; no other vehicles' names, avatars or photos; no free panning or search | reg 109 (b)(d); NHTSA map exception |
| `media` | title/artist ≤ 30 characters each, static artwork, play/pause/skip/volume; no lyrics, no video, no browsing beyond a `short_list` | CarPlay audio rule; reg 109 (a) as equipment state (our reading) |
| `tiles` (gauge/tile grid) | ≤ 6 tiles, ≥ 56 px digits, display refresh ≤ 4 Hz with hysteresis, no animated needles except red alarms | Android grid 6; SA-1 |
| `alert_card` | one card, icon + ≤ 2 lines ≤ 30 characters, ≤ 2 buttons; never message content | CarPlay alert; NHTSA |
| `short_list` | ≤ 6 rows, one level, ≤ 30 characters a row, driver-paced scroll only | Android list 6; ESoP I |
| existing `telltale_list`, `value`, `setpoint`, `camera_live`, `arm` | as app-model §4.4 | — |

Every task ≤ 3 screens on a head unit while Moving (CarPlay Driving Task depth; tighter than
Android's 5 because our Drive mode is the root), and the last screen returns to Drive mode.

## 8. Recommended wording

### 8.1 UI spec §3.5, replace the Idling rule and add a paragraph after "Unknown speed"

> **Idling** — engine running, speed 0. Reading, Logs, cameras and Security arming are
> allowed. **Text entry, Maintenance and Tier 2 `engine_running_ok` actions also need Park
> evidence:** handbrake on, or neutral (sensed, or inferred from engine speed ÷ wheel speed),
> for > 3 s. Without it, Idling uses the Moving rules for those items. Non-driving visuals
> return 3 s after entering Idling or Parked.

> **Driver-facing displays.** Every head-unit layout class is driver-facing. A display counts
> as passenger-only only when an owner declares it in the install configuration as out of the
> driver's sight and reach (for example a rear-seat tablet); no user setting, app or API can
> change this while Moving. The phone stays a passenger device (above).

> **Passenger view (per trip).** On a driver-facing display, while Moving, a locked view may
> offer **Passenger view** only if every item in it is vehicle state, own location and route,
> or a driving camera (UK reg 109 classes). It never unlocks video other than driving cameras,
> clip playback, replay or animation, Docs, other people's vehicles, messages or social
> content, text entry, or any action; tiers and the gate are unchanged. Opening it asks once,
> "Are you a passenger? The driver must not use this while driving", with **I'm a passenger**
> and **Cancel**; there is no "always" and no setting to skip the question. Passenger view
> shows a persistent "Passenger view" badge and frame and a one-tap **Back to Drive**. It ends
> on Parked, ignition off, a new trip, unknown speed, reverse, service mode, any red telltale
> or 15 minutes, whichever comes first, and asks again next time. The server holds the state
> per trip and display and records each grant (time, trip, display, user if signed in) in the
> trip's local log; the record is shown to the owner, kept with the trip and never shared or
> uploaded. Every locked view also offers **Open on phone**, which sends the view to a paired
> phone; this is the preferred passenger path.

### 8.2 App-model §4.4, replace the last two sentences

> Templates have no text entry, no scrolling beyond the limit, no typed confirm, no animation
> other than red alarms, and no message content. Every task on a driver-facing display while
> Moving is ≤ 3 screens and ends back in Drive mode. Unknown speed counts as Moving on head
> units (ADR-0018 Q5). An app may declare `"moving": {"template": …}` only for a shell
> template; it may declare `"passenger_view": true` for a view whose data is vehicle state,
> own location or route, or a driving camera, which the registry checks against the view's
> declared signals and data classes. **New templates are added only by a platform proposal**
> (spec, owner approval, limits, tests) and must cite the rule each limit comes from.

### 8.3 "Using Ostler while driving" page (ESoP IV), first lines

> Ostler's driver-safe screens are Drive mode, telltales, Mark, the own-car map, media
> controls, climate setpoints, arming and the reverse camera. Everything else is for use when
> parked, or by a passenger on their own phone. Passenger view on the car screen is for a
> passenger only; using it while driving may be an offence (in the UK, Construction and Use
> regulation 109) and is your responsibility.

## 9. Copy / Avoid / Decide for Ostler

### Copy
- **AAOS fail-closed default** (missing config = fully restricted) for the driving state and
  for a view with no `driving` rule → UI spec §3.5, app-model §4.2 (already "missing = false";
  keep it).
- **Android's limits as our template limits**: list/grid 6, pane 4, ≤ 120-character strings,
  21 items, depth 3 → app-model §4.4 table (§7.2).
- **NHTSA's neutral inference** from engine ÷ wheel speed for Park evidence on manual cars →
  UI spec §3.5 Idling; protocol state handoff for `engine_rpm` and SLABS wheel speeds.
- **Waze/Maps hand-off**: the car screen stays locked; the passenger uses a phone → UI spec
  §3.5 (Open on phone), app-model §4.3 hosts.
- **ESoP IV instructions page** → U2 deliverable in UI spec §10.
- **CarPlay's "no message content"** for every alert card → app-model §4.4, Social add-on.

### Avoid
- A head-unit passenger unlock for **non-driving content** (Tesla Passenger Play; reg 109;
  ESoP I) → UI spec §3.5.
- An "always" switch, a remembered choice, or a per-user exemption (ESoP III foreseeable
  misuse) → UI spec §3.5.
- Citing the **30-character rule as NHTSA's** → fix [head_unit_ui.md §1](ui/head_unit_ui.md)
  and UI spec §10.1 U2 wording ("NHTSA numbers as normative" should name 2 s / 12 s and the
  per se list, not 30 characters).
- **Live engine gauges in a CarPlay Driving Task companion** (10 s refresh rule) → future
  companion spec; app-model §4.3.
- Uploading or sharing the override log → ADR-0029 data classes, ADR-0036.

### Decide (recommendations for the owner)
1. **D1 — Passenger view on the head unit.** Recommend: allow it only for driving-related
   content (vehicle state, own location/route, driving cameras), per trip, with the wording in
   §8.1; everything else via **Open on phone**. Alternative: no head-unit override at all
   (what Android Auto and CarPlay do). Maps to UI spec §3.5, app-model §4.4.
2. **D2 — Idling needs Park evidence for text entry and Maintenance.** Recommend yes
   (handbrake, or neutral inferred from engine ÷ wheel speed, > 3 s); without it those items
   use Moving rules. Maps to UI spec §3.5, ADR-0033 (Maintenance "Parked or Idling").
3. **D3 — Passenger view timeout.** Recommend 15 minutes plus the stop/new-trip/red-telltale
   exits in §8.1. Maps to UI spec §3.5.
4. **D4 — Override log.** Recommend local only, owner-visible, kept with the trip, never
   synced unless the owner exports the trip. Maps to UI spec §3.5, ADR-0029.
5. **D5 — Other vehicles on the head-unit map while Moving** (Vehicles & Map, Social).
   Recommend: none by default; convoy members of an active group drive as plain markers with
   no names or photos, an owner opt-in. Maps to the add-on's spec and app-model §4.4 `map`.
6. **D6 — Template set and process.** Recommend adopting `map`, `media`, `tiles`,
   `alert_card`, `short_list` with the limits in §7.2 alongside the existing five, task depth
   ≤ 3 on head units, and "added only by platform proposal citing the source of each limit".
   Maps to app-model §4.4.
7. **D7 — Companion apps.** Recommend that any CarPlay or Android Auto companion is specced
   against that platform's category first (CarPlay: Driving Task without live gauges or
   maintenance; Android Auto: IoT), and that live gauges stay in Ostler's own head-unit UI.
   Maps to app-model §4.3 hosts.
8. **D8 — Legal check before U2 ships.** Recommend a short opinion from a UK road-traffic
   lawyer on reg 109's application to LCD head units and on the passenger view, and from a
   product-liability lawyer on the PLD once hardware sales start. Maps to UI spec §10 U2.

## Sources (all checked 2026-10-07)

- [G1] Android for Cars app categories: https://developer.android.com/training/cars/apps
- [G2] Car app quality guidelines (updated 2026-09-14): https://developer.android.com/docs/quality-guidelines/car-app-quality
- [G3] Template restrictions: https://developer.android.com/training/cars/apps/library/template-restrictions
- [G4] Constraints API: https://developer.android.google.cn/training/cars/apps/library/constraints-api?hl=en
- [G5] Car App Library fallback limits (`integers.xml`): https://android.googlesource.com/platform/frameworks/support/+/androidx-main/car/app/app/src/main/res/values/integers.xml
- [A1] AAOS default UX restrictions map: https://android.googlesource.com/platform/packages/services/Car/+/refs/heads/main/service/res/xml/car_ux_restrictions_map.xml
- [A2] AAOS driver distraction guidelines: https://source.android.com/docs/automotive/driver_distraction/guidelines
- [C1] CarPlay for developers: https://developer.apple.com/carplay/
- [C2] CarPlay Developer Guide (June 2026): https://developer.apple.com/download/files/CarPlay-Developer-Guide.pdf
- [N1] NHTSA Phase 1 guidelines, 78 FR 24818 (2013): https://www.govinfo.gov/content/pkg/FR-2013-04-26/html/2013-09883.htm
- [N2] NHTSA Phase 2 proposal, 81 FR 87656 (2016): https://www.govinfo.gov/content/pkg/FR-2016-12-05/html/2016-29051.htm
- [E1] European Statement of Principles on HMI, Recommendation 2008/653/EC, OJ L 216 (Spanish edition read): https://www.boe.es/doue/2008/216/L00001-00042.pdf ; https://eur-lex.europa.eu/eli/reco/2008/653/oj
- [U1] Road Vehicles (Construction and Use) Regulations 1986, reg 109: https://www.legislation.gov.uk/uksi/1986/1078/regulation/109
- [U2] Reg 110 as amended 2022: https://www.legislation.gov.uk/uksi/1986/1078/regulation/110
- [U3] Highway Code rules 148–150: https://www.gov.uk/guidance/the-highway-code/general-rules-techniques-and-advice-for-all-drivers-and-riders-103-to-158
- [V1] Vienna Convention art. 8(6) (as amended): https://assets.publishing.service.gov.uk/media/5a7b1fca40f0b66eab99f277/EM_9570_Conv_Road_Traffic.pdf
- [V2] EU ADDW from July 2026 (press summary): https://english.news18a.com/news/english_273212.html
- [W1] Waze passenger typing (press and user reports): https://www.vice.com/en/article/wazevoice-notes-report-road-conditions ; https://support.google.com/androidauto/answer/7441088
- [W2] Waze phone use during Android Auto (2025): https://www.autoindustriya.com/auto-industry-news/waze-now-accessible-on-android-auto-in-latest-update.html
- [W3] Google Maps phone use during Android Auto (2023): https://www.journaldugeek.com/2023/03/04/google-va-supprimer-cette-limitation-frustrante-de-google-maps-avec-android-auto/
- [T1] NHTSA opens Passenger Play probe: https://www.fortune.com/2021/12/23/highway-safety-regulators-open-probe-into-teslas-controversial-in-car-video-game-feature
- [T2] Probe closed May 2023: https://driveteslacanada.ca/?p=73548 ; https://mobilesyrup.com/2023/05/30/tesla-escapes-recalls-for-allowing-in-motion-gaming-in-its-vehicles/
- [L1] Lemmon v. Snap (9th Cir. 2021): https://www.insideprivacy.com/data/ninth-circuit-denies-section-230-defense-in-products-liability-case/
- [L2] Modisette v. Apple (2018): https://productsliabilityopinions.justia.com/2018/12/14/modisette-v-apple-inc
- [L3] Product Liability Directive (EU) 2024/2853 and open source: https://www.ibanet.org/European-Product-Liability-Directive-liability-for-software
