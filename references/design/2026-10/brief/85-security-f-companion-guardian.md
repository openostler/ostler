---
title: "Designer brief 85-f — Security app: companion phone view, Guardian home pages and crash SOS (later)"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md, decisions/adr-0009-session-logbook-and-location.md]
summary: >
  Last Security app file (app:security). The companion phone app's view of Security when
  away from the car: remote and read-only apart from arming and disarming the software
  alarm, with push alerts that reuse the companion alarm alert. Then the Ostler Guardian
  flavour's minimal home page set: what an owner who installed only Security sees, two home
  pages built from Security's widgets and the OS safety widgets, and a dock of Security,
  Settings and the app drawer. Ends with crash SOS, marked later: a proposed placeholder
  that follows the accounts spec's SOS exception for safety contacts.
---

# 85-f — Companion view, Guardian home pages, crash SOS

Main page: [85-a](85-security-a-main.md). The companion app's own screens
(`companion-car-status`, `companion-remote`, `companion-alarm-alert`,
`companion-notifications`) are in [60-apps-companion-a](60-apps-companion-a.md) and
[60-apps-companion-b](60-apps-companion-b.md); this file draws only Security's page inside it.

### security-companion-remote — Security on the phone, away from the car  [New]
- **Owner:** app:security (inside the companion phone app, which is os)
- **Purpose:** the Security page as the owner sees it on a remote link: state, events and
  the tracker, with arm and disarm the only actions.
- **Opens from → goes to:** the companion dock's Security item; `companion-alarm-alert` →
  **View**; a push. Goes to `security-remote-disarm`, `security-arm-sheet`,
  `security-tracker`, `security-event-detail`.
- **Layout classes:** phone. **Draw first:** phone Night remote (relay) armed; phone Night
  alerting from a push; phone Day remote disarmed.
- **Content (top to bottom):**
  1. Link Chip at the top: "Relay" or "Tailscale" with latency, or "Car Wi-Fi" when local.
  2. Banner (remote only): "Remote: view only. Arming and disarming the alarm work; other
     actions need you at the car."
  3. The `security` page's sections in phone layout: state hero with **Arm** or **Disarm**,
     recent events, the map with fix age, sensors (read only).
  4. Source line: "From the Guardian · checked in 4 min ago · via its own SIM".
  5. **Push alerts** row: "Alarm alerts: on (can't be turned off)", link to
     `companion-notifications`.
- **States:** remote with the Brain asleep: everything still shows (it comes from the node
  or Guardian, not the Brain); clips show "Needs the Brain · Wake" and the remote wake sheet
  with the quota ([UI §3.8][ui-38]); Guardian in a check-in sleep: actions queue with expiry;
  node in parked-deep and no Guardian: "Node asleep (deep) · last seen 3 h"; offline:
  cached with ages; no remote access set up: "Set up remote access in Settings → Network";
  Viewer: state and events only; Moving (phone in a moving car): Moving banner, view only.
- **Safety and driving rules:** remote paths are read-only plus arm and disarm of the
  software alarm, audited and notified ([ADR-0033 §6][a33-6]); everything else needs
  `OSTLER_ALLOW_REMOTE_CONTROL` on the node and is not offered here; a mesh link never arms
  or disarms; live location is the owner's unless shared ([ADR-0009][a09]); push alarm alerts
  can't be removed ([ADR-0033 §7][a33-7]).
- **Components:** Chip (link), Banner, Card (tone), ListRow, Map, Button.
- **Spec refs:** [ADR-0033 §6][a33-6] · [UI §7.2][ui-72] · [UI §3.8][ui-38] ·
  [App model §7.1][am-71].
- **Open questions:** none.

## The Guardian flavour

Guardian = the OS plus the Security app ([ADR-0039 §1][a39]; `setup-apps` in
10-onboarding-d). It usually has no head unit: the phone is the screen. The OS still gives
it the strip, the Connection sheet, Settings, the Store and the app drawer.

**Dock (Guardian):** **Security** `shield` · **Settings** `settings` · **App drawer** `apps`.
Home pages are reached by the home gesture or Back, as on Android. This differs from
01-sitemap-b (Home · Security · Settings · Store · App drawer) and 45-launcher-a (Home ·
Security · App drawer); see Open questions.

### security-guardian-home — Guardian home pages  [Proposed]
- **Owner:** os (the launcher's pages; preset contents from app:security)
- **Why the app needs it:** the Guardian owner has one app, so the generic first home page
  (vehicle widget, last trip, signal tiles) would be mostly empty; a preset page set built
  from Security's widgets makes the flavour feel complete.
- **Purpose:** what a Guardian-only owner sees on opening Ostler.
- **Opens from → goes to:** app launch; Home gesture; end of first run. Widgets go to their
  Security pages; the dock to Security, Settings and the app drawer.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night page 1 armed; phone Day page 1 disarmed; phone Night page 1 alerting; phone
  Night page 2; hu7 Night page 1.
- **Content (top to bottom):**
  1. Strip: Security chip ("Armed"), Link chip ("Guardian · SIM"), 12 V chip, Clock.
  2. **Page 1 "Guard"** (default):
     - Alarm status widget, wide (OS safety widget): "Armed · since 22:10 · last event none".
     - Arm button widget, medium.
     - Tracker mini-map widget, wide: "Home · 3 min ago".
     - Warnings widget (OS safety widget): with no Diagnostics app it shows device warnings
       only: "Guardian cell 84 % · 12 V 12.6 V · all OK".
  3. **Page 2 "Where"**: tracker mini-map hero size; last event widget (Card with 3 events).
  4. Page dots (2).
  5. Dock: Security · Settings · App drawer.
  6. A dismissible Card on page 1 for the first week: "Want fault codes and live data too?
     Get Diagnostics in the Store."
- **States:** first run before pairing: page 1 holds "Pair your Guardian" Card only; not
  set up: "Finish setting up Security" Card; node asleep: widgets stale with ages;
  offline: cached; empty after removing widgets: "Long-press to add widgets", but the two
  OS safety widgets stay; Moving (if fitted to a head unit): Guardian has no dashboards, so
  the head unit shows the strip, the `arm` template and alert cards only (10-onboarding-d);
  Passenger: phone Moving banner; Locked (layouts locked): "Only the owner can edit this
  screen".
- **Safety and driving rules:** the alarm status and warnings widgets move but never go
  ([Drive modes §8.1 R3][dm-81]); long-press opens edit mode, Park to edit on head units;
  the app drawer is always in the dock ([Drive modes §7.3][dm-73]).
- **Components:** Home page grid, Widget frame, Dock, Dock item, Page indicator dots, Strip
  chip, Card.
- **Spec refs:** [Drive modes §7.2][dm-72] · [Drive modes §8.1][dm-81] · [ADR-0039][a39] ·
  [UI §5.4][ui-54].
- **Open questions:** (1) Which dock is right for Guardian: Security · Settings · App drawer
  (this brief, from the owner's direction), or one of the two lists in 01-sitemap-b and
  45-launcher-a? (2) Should page 2 exist, or should one page be the whole preset?

### security-crash-sos — Crash SOS (later)  [Proposed]
- **Owner:** app:security
- **Why the app needs it:** the IMU that sees a tow can also see a crash, and the accounts
  spec already allows one exception to location privacy: my own SOS or crash alert to my
  safety contacts. **Marked later:** not for this round's build; draw the card only, for
  review.
- **Purpose:** after a hard impact, offer to send the owner's precise position to their
  safety contacts, with a countdown the driver can stop.
- **Opens from → goes to:** raised by the OS alert pipeline on a crash event; the Settings
  row "Crash SOS" in `security-settings` (later). Goes to the safety contacts page
  (Accounts, system Settings).
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving; phone Night.
- **Content (top to bottom):**
  1. `alert_card`: icon `car_crash`, line 1 "Crash detected", line 2 "SOS in 30 s · 2
     contacts".
  2. Buttons (≤ 2): **I'm OK** (cancels) and **Send now**.
  3. After sending: "SOS sent · live position until you mark safe (max 24 h)" with **I'm
     safe**.
- **States:** no safety contacts (feature off, setting says "Add safety contacts first");
  no uplink (SMS from the Guardian if fitted, else "Couldn't send"); false alarm cancelled
  (logged).
- **Safety and driving rules:** the card follows `alert_card` limits while Moving
  ([UI §12.1][ui-121]); position goes only to safety contacts, even in ghost, is audited and
  shown afterwards ([Accounts §14.5][acc-145]); never calls emergency services by itself.
- **Components:** `alert_card`, Button.
- **Spec refs:** [Accounts §14.5][acc-145] · [Accounts §14.7][acc-147] · [UI §12.1][ui-121].
- **Open questions:** crash thresholds from the IMU need their own spec and car tests; does
  this belong in Security or in a separate safety app?

[a09]: ../../../../decisions/adr-0009-session-logbook-and-location.md#decision
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[acc-145]: ../../../../specs/2026-10-06-accounts-sharing-design.md#145-precision-and-who-can-raise-it
[acc-147]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[am-71]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[dm-72]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-73]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#73-rail
[dm-81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-38]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
[ui-54]: ../../../../specs/2026-10-06-ui-architecture-design.md#54-home-built-from-roles
[ui-72]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
