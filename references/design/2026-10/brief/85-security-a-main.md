---
title: "Designer brief 85-a — Security app: main page, arming and disarming"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-02-gps-tracker-alarm-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0009-session-logbook-and-location.md]
summary: >
  First file of the Security app brief (app:security, the whole Ostler Guardian flavour). It
  maps the app's pages across files 85-a to 85-f, then draws the main page (Existing
  `security`): the armed state with Arm and Disarm, recent events, the tracker map and sensor
  states, with every state from no node to Alerting. Then the arm flow and its confirm sheet
  (allowed while Moving through the `arm` template), the disarm flow and its confirm sheet
  (Parked only), and the remote disarm sheet: Security role, audited, owner told, never over
  a mesh, and nothing beyond the software alarm unless the node's install override is set.
---

# 85-a — Security app: main page, arming and disarming

## The app in one paragraph

Security is an app (owner `app:security`) in its own repo. It is the whole **Ostler
Guardian** flavour: an owner who buys a Guardian installs the OS plus this app only. It reads
the node's or Guardian's alarm inputs, IMU and GNSS, arms and disarms Ostler's **software
alarm**, shows events, and tracks the parked car. It has **no outputs**: no siren, no door
locks and no immobiliser ([ADR-0033 §7][a33-7]). The OS keeps the safety parts: the Security
strip chip, the alarm status widget and every alarm `alert_card` are drawn by the OS and
cannot be removed while a node is fitted, even if this app is uninstalled
([Drive modes §8.1 R3][dm-81]). Uninstalling Security is refused while the car is armed
(decided, item 62); disarm is Parked only (item 59) and a remote disarm needs a fresh
passkey (item 60). It is also preinstalled in Ostler Diagnostics and Ostler Brain (item
11).

## Page map (where each page is drawn)

| File | Screens |
|---|---|
| 85-a (this) | `security` (Existing), `security-arm-sheet`, `security-disarm-sheet`, `security-remote-disarm` |
| [85-b](85-security-b-events.md) | `security-events`, `security-event-detail`, `security-clip`, `security-alert-card` |
| [85-c](85-security-c-tracker.md) | `security-tracker`, `security-trail`, `security-geofences`, `security-geofence-edit`, `security-tow-mode` |
| [85-d](85-security-d-setup-settings.md) | setup flow, `security-setup-welcome`, `security-setup-done`, `security-channels`, `security-settings` |
| [85-e](85-security-e-widgets.md) | widgets: alarm status (drawn in 45-launcher-f), `security-widget-arm`, `security-widget-last-event`, `security-widget-tracker-map`; shortcuts and Drive menu row |
| [85-f](85-security-f-companion-guardian.md) | `security-companion-remote`, `security-guardian-home`, `security-crash-sos` (later; an OS system service, item 6) |

Hardware setup pages belong to this app but are drawn in
[20-hardware-f](20-hardware-f-security-mesh-service.md): `hw-alarm-setup`,
`hw-alarm-walk-test`, `hw-tracker`. They are not repeated here.

**Words used on every page.** States: **Disarmed** (`lock_open`, neutral), **Armed**
(`shield`, `ok`), **Alerting** (`e911_emergency`, `alarm`, the only pulse), **Tamper**
(`warning`, `alarm`), **Testing** (`science`, `warn`). Always icon plus word, never colour
alone. "Arm" means Ostler's software alarm watches the sensors; it does not lock the car.

### security — Security main page  [Existing]
- **Owner:** app:security
- **Purpose:** one look at whether the car is guarded, what happened, and where it is.
- **Opens from → goes to:** the dock's Security item; the Security strip chip; the alarm
  status widget; an alarm `alert_card` or phone push; the app drawer. Landing page when
  Parked and armed ([UI §3.4][ui-34]). Goes to `security-arm-sheet`, `security-disarm-sheet`,
  `security-events`, `security-event-detail`, `security-tracker`, `security-settings`,
  `hw-alarm-setup`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night armed; phone Day disarmed; phone Night Alerting; hu7 Night armed; hu7
  Night-dim Moving (the `arm` template); huwide Night (map pane beside the list).
- **Content (top to bottom):**
  1. **State hero** (Card, tone by state): icon and word "Armed", line "since 22:10 · armed by
     you on the head unit"; or "Disarmed · since 07:42"; or "Alerting · Driver's door opened
     02:14". Under it, a source line: "Watching: Tilt, Shock, GPS movement, Tamper" (only the
     sensors that are on).
  2. **Primary button**: **Arm** when disarmed, **Disarm** when armed or alerting (opens the
     sheet; never acts on one tap). When alerting, a second button **I've checked it**
     (silences the repeat on this screen; the event stays open until disarmed).
  3. **Recent events** (up to 5 ListRows, newest first): icon, title, time and source, for
     example "Tilt > 3° for 10 s · 02:14 · Guardian IMU", "Moved 120 m with ignition off ·
     02:16 · GPS", "12 V low · 12.1 V · 18:03", "Armed · 22:10 · you (head unit)",
     "Disarmed remotely · 07:42 · you (phone, relay)". Link **All events** →
     `security-events`.
  4. **Where it is** (Map, Ostler Night or Day style): the car's puck with fix age
     "Last fix 3 min ago · ±8 m · Guardian GNSS", geofence outlines, the trail since armed if
     it moved. Tap → `security-tracker`. Below: "Only you can see this" (or who it is shared
     with, from Accounts sharing).
  5. **Sensors** (compact ListRows, only hardware present): name, status Chip (OK, No signal,
     Fault, Off), last event age. Ignition · Tilt (IMU) · Shock (IMU) · GPS movement · Tamper
     (Guardian) · 12 V battery "12.6 V" · Guardian cell "84 %". On the Discovery 2, Doors,
     Bonnet and Car's alarm siren show only once their BCU taps are fitted (wires not yet
     identified; see `hw-alarm-setup`). Link **Alarm setup** → `hw-alarm-setup`.
  6. **Alerts reach you** line: "Phone · SMS · works with the Brain off and no internet",
     link → `security-channels`.
  7. Overflow menu: Settings, Tracker settings, Walk test, App info (90-appframe files).
- **States:**
  - **No node:** Empty state "No node reported yet · The alarm and tracker appear when a node
    or Guardian is paired." with **Pair a node** (today's text in `Security.tsx`).
  - **Loading:** hero and rows as Skeletons; the map draws `--bg` and the last puck.
  - **Offline / node asleep:** values in stale grey with their age, banner "Guardian asleep ·
    checks in about every 10 min · last seen 6 min ago" ([UI §3.8][ui-38]). Arm and Disarm
    stay enabled; they queue for the next check-in with expiry (see the sheets).
  - **Brain asleep:** the page renders from the node's retained data; clips show "Needs the
    Brain · Wake" ([UI §3.8][ui-38]). Without a Brain the clip rows are absent.
  - **Error:** "Can't reach the node · last state Armed, 14 min ago" banner; nothing pretends
    to be current.
  - **Parked:** full. **Idling:** full except Disarm, which is Parked only: the button is
    disabled with "Switch the engine off to disarm" (Parked only, decided item 59).
  - **Moving:** the page is replaced by the shell's `arm` template: state word and an **Arm**
    button only; never Disarm, events, map or sensors ([app model §4.4][am-44]). Alarm events
    reach the driver only as `alert_card`s (85-b).
  - **Passenger:** head-unit Passenger view may show state and own location (reg 109 classes),
    never Disarm. The phone shows the Moving banner; "I'm a passenger" unlocks reading only.
  - **Locked (kiosk session, no sign-in):** state and map read only; Arm and Disarm hidden
    with "Sign in to arm or disarm" (kiosk gets Read and Comfort only, [ADR-0033 §2][a33-2]).
  - **Viewer role:** state and events only; map only if location is shared with them.
  - **Remote control override on:** persistent "Remote control enabled" badge in the strip.
- **Safety and driving rules:** Security category, Tier 1: arming allowed while Moving,
  disarming Parked only ([ADR-0033 §1][a33-1], [UI §7.1][ui-71]). Clips Parked only
  ([UI §6][ui-6]). The alarm path never waits for the Brain or the internet
  ([ADR-0033 §7][a33-7], [ADR-0040 §8][a40-8]). Location stays on the device unless shared
  ([ADR-0009][a09]).
- **Components:** Card (tone), Button (primary, danger), ListRow, Chip (status), Map, Banner,
  Empty state, Skeleton, Strip chip (Security).
- **Spec refs:** [UI §3.4][ui-34] · [UI §6][ui-6] · [UI §3.8][ui-38] · [ADR-0033][a33-1] ·
  [tracker and alarm spec][ga-taps] (draft).
- **Open questions:** (1) **Decided (item 59):** disarm is Parked only, never while Idling,
  even with Park evidence. (2) Does "I've checked it" exist, or is Disarm the only way to
  quiet an alert?

## Arm flow

| # | Screen | What the user does | What can fail → recovery |
|---|---|---|---|
| 1 | `security` (or widget, shortcut, Drive menu row) | taps **Arm** | not signed in → "Sign in to arm" |
| 2 | `security-arm-sheet` | reads open sensors, taps **Arm now** | a door is open → arm anyway, or Cancel |
| 3 | `security` | sees "Arming · 30 s" countdown, then "Armed" | node does not answer in 2 s → "Not armed: Guardian didn't answer · Try again" |

Arming is ≤ 2 s on the node ([ADR-0040 §6][a40-6]); it needs no Brain (`needs_brain: false`).

### security-arm-sheet — Arm the alarm  [New]
- **Owner:** os (the shell's confirm sheet; the arm action is app:security's)
- **Purpose:** one clear confirm before Ostler starts watching the car.
- **Opens from → goes to:** **Arm** on `security`, the arm widget, the "Arm now" shortcut,
  the Drive menu row, the `arm` template while Moving. Goes back with the result.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night; hu7 Night-dim Moving (the template's short form).
- **Content (top to bottom):**
  1. Title "Arm the alarm?"; line "Ostler will alert you if the car is opened, moved or
     tampered with. This doesn't lock the car."
  2. **Open now** warn rows if any: "Driver's door open · it is watched once it closes".
  3. **Exit delay** Segmented: 0 s · 30 s · 60 s (default from settings).
  4. **Watching** summary: "Tilt, Shock, GPS movement, Tamper" with **Change** (Parked only,
     → `security-settings`).
  5. Buttons **Cancel** (focused) and **Arm now** (primary).
- **States:** sending ("Arming…"); done (Toast "Armed"); refused ("Not armed: you don't have
  Security rights"); node asleep: "Arms when the Guardian next checks in (≤ 10 min) · expires
  14:35 · Cancel" ([ADR-0040 §5][a40-5]); Moving: the `arm` template shows only "Arm the
  alarm?" with **Arm** and **Cancel**, no rows and no delay choice.
- **Safety and driving rules:** Tier 1 Security; arming allowed while Moving with driver-safe
  UI: no typing, ≤ 2 lines of ≤ 30 characters ([ADR-0033 §1][a33-1], [UI §12.1][ui-121]).
  Remote arming is allowed and audited ([ADR-0033 §6][a33-6]).
- **Components:** Sheet, Segmented, ListRow (warn), Button, Toast.
- **Spec refs:** [ADR-0033 §1][a33-1] · [app model §4.4][am-44] · [ADR-0040 §5][a40-5].
- **Open questions:** should arming while Moving exist at all for a software alarm (it
  arms as the car parks)? The ADR allows it; an "Arm when I park" choice may be clearer.

## Disarm flow

| # | Screen | What the user does | What can fail → recovery |
|---|---|---|---|
| 1 | `security`, alert card, phone push | taps **Disarm** | Moving or Idling → "Park to disarm" |
| 2 | `security-disarm-sheet` (local) or `security-remote-disarm` (remote) | confirms | role lacks Security → refused with reason |
| 3 | `security` | sees "Disarmed · by you" and the audit row | node does not answer → stays **Armed** (fail-secure) with "Not disarmed · Try again" |

### security-disarm-sheet — Disarm (at the car)  [New]
- **Owner:** os (the shell's confirm sheet; the action is app:security's)
- **Purpose:** stop watching the car, deliberately, from a local link.
- **Opens from → goes to:** **Disarm** on `security`, the alarm `alert_card` (Parked), a
  phone push on a local link. Back to `security`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night.
- **Content (top to bottom):**
  1. Title "Disarm the alarm?"; line "Ostler stops watching the car. The car's own alarm is
     not changed."
  2. If alerting: "Open event: Driver's door opened 02:14 · it stays in the event list".
  3. Buttons **Cancel** (focused) and **Disarm** (secondary, not danger red).
- **States:** sending; done (Toast "Disarmed"); failed (stays Armed, "Not disarmed · Guardian
  didn't answer"); Idling or Moving: never opens, the button reads "Park to disarm".
- **Safety and driving rules:** Parked only ([ADR-0033 §1][a33-1]); fail-secure: any error
  leaves it armed ([tracker spec: threat model][ga-tm]); logged with who, when and which
  device.
- **Components:** Sheet, Button, Toast.
- **Spec refs:** [ADR-0033 §1][a33-1] · [UI §7.1][ui-71].
- **Open questions:** none.

### security-remote-disarm — Disarm remotely  [New]
- **Owner:** os (the shell's remote confirm; the action is app:security's)
- **Purpose:** disarm from away from the car, with the rules visible.
- **Opens from → goes to:** **Disarm** on the phone over Tailscale or the Ostler Cloud relay;
  the phone alarm push. Back to `security-companion-remote` (85-f) or `security`.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; phone Day.
- **Content (top to bottom):**
  1. Title "Disarm remotely?"; link line "Via relay · you are away from the car".
  2. Notice Card: "This disarms Ostler's alarm only. It can't unlock or start the car. The
     owner is told and it is logged."
  3. Re-check line: "The Guardian checks again that the car is parked."
  4. Buttons **Cancel** (focused) and **Disarm**. **Disarm** asks for a fresh passkey (the
     phone's own unlock) every time; a signed-in session alone is not enough (item 60).
- **States:** passkey check cancelled or failed: nothing is sent, "Not disarmed". Role lacks
  Security: "You can see the alarm but can't disarm it" (no button);
  over a mesh: never offered ("Not over a mesh radio", [ADR-0038][a38]); check-in target:
  queued with expiry and **Cancel**; Brain not needed (no wake sheet); a Viewer or a share
  without Security sees state only; done: "Disarmed · the owner has been told".
- **Safety and driving rules:** remote paths are read-only plus arming and disarming the
  software alarm, audited and notified ([ADR-0033 §6][a33-6]); Matter may disarm, a mesh
  never ([ADR-0033 amendments][a33-am]). Anything more over a remote path (for example a
  future fob-press disarm of the car's own alarm) needs `OSTLER_ALLOW_REMOTE_CONTROL` on the
  node, which no screen can set, and its own ADR first; it is **not drawn**. An AI client's
  "accept" never counts.
- **Components:** Sheet, Card (notice), Button, Strip badge ("Remote control enabled").
- **Spec refs:** [ADR-0033 §6][a33-6] · [UI §7.2][ui-72] · [tracker spec: threat model][ga-tm].
- **Open questions:** **Decided (item 60):** remote disarm needs a fresh passkey each time;
  the session is not enough.

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md#decision
[a33-1]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#1-categories-beside-tiers
[a33-2]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#2-roles-grant-categories
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a33-am]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#amendments-2026-10-06-networking-answers
[a38]: ../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md#decision
[a40-5]: ../../../../decisions/adr-0040-power-states-and-wake.md#5-the-owners-rule-for-actions
[a40-6]: ../../../../decisions/adr-0040-power-states-and-wake.md#6-latency-budgets
[a40-8]: ../../../../decisions/adr-0040-power-states-and-wake.md#8-safety
[am-44]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ga-taps]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#read-side--alarmsecurity-via-signal-taps
[ga-tm]: ../../../../specs/2026-10-02-gps-tracker-alarm-design.md#security-threat-model-this-is-a-new-unlock-path
[ui-34]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-71]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-72]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
