---
title: "Designer brief 40-b — driving states: locked view, Passenger view, phone Moving banner, Park to edit, the driving page, service mode and Brain wake"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-visual-design-system-design.md, references/research/driver_distraction_rules.md]
summary: >
  Second shell brief file. It covers how the shell shows the driving state: the locked view
  ("Available when parked" with Open on phone and, only for vehicle-state content, Passenger
  view), the Passenger view prompt, badge, frame and exits, the phone's Moving banner and its
  once-per-trip "I'm a passenger" question, the new "Park to edit" toast and the "Finish
  editing when parked" prompt, the "Using Ostler while driving" page, the service-mode frame
  and badge, and the Brain wake sheet with queued buttons and the "Needs the Brain" card. Each
  block gives labels, states and the UK regulation 109 limits that shape them. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 40-b — Driving states, service mode and Brain wake

Back to [40-a](40-drive-a.md) for the conventions and the file list.

### shell-locked-view — Locked view ("Available when parked")  [Existing]
- **Purpose:** what any page that is not allowed while Moving shows on a driver-facing
  display, instead of its content.
- **Owner:** os
- **Opens from → goes to:** any locked route while Moving (the app drawer, the Trips app's
  analysis, Diagnostics detail, editors, pinned apps without a Moving template). **Open on phone** sends the view to a paired phone;
  **Passenger view** (only where allowed) → `shell-passenger-view`; **Back to Drive** →
  Drive mode.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night-dim Moving
  (with and without the Passenger view button); hu5 Night-dim Moving; phone Day Moving.
- **Content:** 1. Material icon `lock` and the page name ("Trips"). 2. Line "Available when
  parked" (24 px). 3. **Open on phone** (primary). 4. **Passenger view** (secondary; only
  when every item on the page is vehicle state, own location or route, or a driving camera).
  5. **Back to Drive**. Nothing of the page's content shows behind it, not even blurred.
- **States:** Moving: as above. Idling without Park evidence: the same card for text entry,
  Maintenance actions and editors. Parked: never shown. No paired phone: Open on phone reads
  "Pair a phone in Settings → Network" and is disabled. Offline phone: "Phone not reachable".
- **Safety and driving rules:** unknown speed counts as Moving on HU; a view with no `moving`
  rule is fully locked (fail closed); at most 3 screens deep ([UI §12.1][ui-12.1]).
- **Components:** Card, Button. Tokens `type-body` (≥ 24 px), no glow (default look).
- **Spec refs:** [UI §3.5][ui-3.5] · [UI §12.1][ui-12.1].
- **Open questions:** none.

### shell-passenger-view — Passenger prompt, badge and frame  [Existing]
- **Purpose:** let a passenger see driving-related content on the head unit while Moving,
  per trip, with the driver warned.
- **Owner:** os
- **Opens from → goes to:** **Passenger view** on a locked view → the prompt → the page in a
  frame; **Back to Drive** or any exit → Drive mode.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Moving prompt;
  hu7 Night-dim Passenger frame over the Dashboard Parked grid.
- **Content:**
  1. **Prompt** (sheet, Cancel focused): "Are you a passenger? The driver must not use this
     while driving." Buttons **I'm a passenger** and **Cancel**. No "always", no checkbox.
  2. **Frame:** a persistent border round the viewport and a **Passenger view** badge in the
     strip; a one-tap **Back to Drive** in the badge.
  3. **Inside:** only vehicle state, own location and route, driving cameras; for example a
     Drive home page's full Parked grid with Td5 boost, coolant, battery and SLABS ride heights,
     without animation.
- **States:** ends (back to Drive mode, prompt again next time) on Parked, ignition off, a new
  trip, unknown speed, reverse, service mode, any red telltale or after 15 minutes; a short
  line says why ("Passenger view ended: red warning"). Refused for a page with messages,
  social content, other vehicles, video other than driving cameras, Docs or text entry; that
  page shows only **Open on phone**.
- **Safety and driving rules:** view-only: no action, no text entry; each grant is logged in
  the trip's local log and never shared. Released only after the U2 legal opinion; without it
  the button is absent ([UI §12.1][ui-12.1], [reg 109 research][r-dd-4.2]).
- **Components:** Sheet, Button, Chip (badge). Tokens `accent-soft`, `line-strong` (frame).
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §4.3][dm-4.3] ·
  [Drive modes §8.1][dm-8.1] R3.
- **Open questions:** none.

### shell-phone-moving-banner — Phone Moving banner and "I'm a passenger"  [Existing]
- **Purpose:** remind a phone user that the car is moving, and ask once per trip before
  non-driving views.
- **Owner:** os
- **Opens from → goes to:** shown at the top of the phone while Moving; opening Trips
  analysis, Social, Vehicles & Map or Docs asks the question; **I'm a passenger** opens the
  view read-only; **Not now** returns.
- **Layout classes:** phone. **Draw first:** phone Night Moving with banner; phone Day Moving
  with the question sheet; phone Night Passenger (view-only badge).
- **Content:** 1. Banner (tone card): `directions_car` "Moving · for passengers only" and a
  link "Using Ostler while driving". 2. Question sheet: "Are you a passenger?" with **I'm a
  passenger** and **Not now**. 3. After yes: a "Passenger · view only" badge; car actions keep
  the gate's "vehicle stationary" checks.
- **States:** asks again after a stop or a new trip; no "always". Parked: no banner. Idling:
  banner hidden 3 s after the stop.
- **Safety and driving rules:** guidelines plus review, not a lockout: reading stays open, car
  actions still need the stationary check ([UI §12.1][ui-12.1]).
- **Components:** Card (tone), Button, Sheet. Tokens `info`, `surface-2`.
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §3.5][ui-3.5].
- **Open questions:** none.

### shell-park-to-edit — "Park to edit" toast and "Finish editing when parked"  [New]
- **Purpose:** the only answer to an edit gesture on a driver-facing display while Moving,
  and the way back to a kept draft.
- **Owner:** os
- **Opens from → goes to:** long-press (or long `ok`) on the strip, an empty area, a widget or
  a dock item while Moving; Reset layout or Edit layout tapped while Moving; entering Moving
  while editing. The prompt **Finish editing** reopens the editor at the next Parked.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Moving toast
  over the Dashboard cluster; hu7 Night Parked prompt.
- **Content:**
  1. **Toast** (3 s, no button): `local_parking` "Park to edit". Bottom of the content area,
     never over the strip, the telltale or an `alert_card`.
  2. **Editor closes to the Drive home page** when the car starts moving mid-edit; the draft is kept.
  3. **Prompt at the next Parked** (a small card): "Finish editing when parked" with
     **Finish editing** and **Discard draft** (Cancel focused).
- **States:** Moving: toast only. Idling without Park evidence: toast. Parked: prompt. Phone,
  desktop, passenger-only display: never shown, editing is allowed.
- **Safety and driving rules:** the server refuses layout writes from a Moving display (R1);
  no edit bar ever appears while Moving ([Drive modes §8.1][dm-8.1]).
- **Components:** Toast (new component: one line, icon + word, no actions, 3 s), Card,
  Button.
- **Spec refs:** [Drive modes §7.1][dm-7.1] · [Drive modes §8.1][dm-8.1] ·
  [shell input §14][si-14] · [UI §15.2][ui-15.2].
- **Open questions:** none.

### shell-driving-page — "Using Ostler while driving"  [Existing]
- **Purpose:** the plain statement of what is safe while driving (ESoP principle IV).
- **Owner:** os
- **Opens from → goes to:** Settings → About, the passenger prompt's link, the phone banner's
  link, the docs.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day, hu7 Night Parked, hu7 Night-dim Moving (locked).
- **Content:**
  1. Title "Using Ostler while driving".
  2. Lead paragraph: "Ostler's driver-safe screens are Drive mode, telltales, Mark, the
     own-car map, media controls, climate setpoints, arming and the reverse camera.
     Everything else is for use when parked, or by a passenger on their own phone."
  3. "Passenger view on the car screen is for a passenger only; using it while driving may be
     an offence (in the UK, Construction and Use regulation 109) and is your responsibility."
  4. Sections: **While moving** (the template list in words: up to 6 tiles, one alert at a
     time, lists of up to 6 rows); **Messages** (sender and app only, Play and Reply);
     **Calls** (audio only); **Phones and messenger calls** (what rings in the car, from
     the Phone & Comms bench matrix); **Editing** ("Park to edit").
- **States:** Parked: full. Moving: `shell-locked-view`. Offline: works (shipped text).
- **Safety and driving rules:** read Parked only on a driver-facing display.
- **Components:** Card. Tokens `type-body`, `type-title`.
- **Spec refs:** [UI §12.1][ui-12.1] · [research §8.3][r-dd-8.3] · [Phone & Comms §6.4][pc-6.4].
- **Open questions:** none.

### shell-service-mode — Service mode frame and strip badge  [Existing]
- **Purpose:** show that admin and Experimental items are on.
- **Owner:** os
- **Opens from → goes to:** long-press on the version line in Settings → About plus the server
  password; **Exit service mode** in the badge's sheet; Diagnose is the landing page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night on Diagnose with the frame; phone Day.
- **Content:** 1. A thick frame round the viewport in `warn` with its word. 2. Strip badge
  `build` "Service" (shell-drawn, not a chip). 3. Experimental items marked "Experimental";
  the Decode lab app opens from the app drawer. 4. Badge sheet: "Service mode is on", **Exit service
  mode**.
- **States:** Parked, Idling: on. Moving: refused and exits; a toast "Service mode ended:
  moving". Passenger view also ends it.
- **Safety and driving rules:** never on while Moving ([UI §3.5][ui-3.5]); the frame and badge
  are outside any layout and cannot be covered ([Drive modes §8.1][dm-8.1] R3).
- **Components:** Chip (badge), frame (new component: viewport frame shared with Passenger
  view). Tokens `warn`, `warn-ink`, `line-strong`.
- **Spec refs:** [UI §3.5][ui-3.5] · [Drive modes §8.1][dm-8.1].
- **Open questions:** Passenger view and service mode both draw a viewport frame; give them
  distinct colours and words (service: `warn`; passenger: `info`).

### shell-brain-wake — Brain wake sheet, queued button, "Needs the Brain"  [Existing]
- **Purpose:** wake the Brain for something that needs it, honestly, with its cost.
- **Owner:** os
- **Opens from → goes to:** a Brain-only view (full Trips, replay, clips) or action; **Wake
  and run** → the action; **Cancel** → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Day remote sheet; hu7 Night "Needs the Brain" card; hu7 Night queued button.
- **Content:**
  1. **Remote wake sheet** (cannot be skipped): "This needs the Brain. Wake it? About 30 s ·
     uses about 30 mAh (today: 180 mAh left) · battery 12.5 V", quota "2 of 6 remote wakes
     left today", **Wake and run** and **Cancel** (Cancel focused).
  2. **Local wake:** no sheet; the button reads "Waking Brain…"; optional "Don't ask again"
     (local links only).
  3. **Queued button:** "Queued · runs when the Brain is ready · expires 14:35 · Cancel";
     check-in targets: "Runs when Relay box next checks in (≤ 10 min)".
  4. **Outcomes:** Done · Expired · Cancelled · Refused by *device* · State changed.
  5. **Needs the Brain card:** `memory` "Needs the Brain" with **Wake**, in place of the view.
  6. **Refusals:** "Brain not woken: battery 11.9 V", "Limit reached: 6 wakes this hour".
  7. **Phone, node in deep sleep:** "Node asleep (deep) · wakes on ignition, door or motion ·
     last seen 3 h", nothing else offered.
- **States:** no Brain fitted: the card and sheet are absent. Parked: full. Moving: no wake
  prompt in Drive mode (the ignition holds the Brain awake). Offline: refusal reason shown.
- **Safety and driving rules:** Tier 2–3 wake first, then the normal approval; approvals never
  queue ([UI §3.8][ui-3.8]).
- **Components:** Sheet, Button (Wake and run, Cancel), Card. Status tokens.
- **Spec refs:** [UI §3.8][ui-3.8] · [shell input §7][si-7].
- **Open questions:** none.

[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[pc-6.4]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#64-messenger-calls-whatsapp-signal-telegram-messenger
[r-dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[r-dd-8.3]: ../../../research/driver_distraction_rules.md#83-using-ostler-while-driving-page-esop-iv-first-lines
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-3.8]: ../../../../specs/2026-10-06-ui-architecture-design.md#38-asleep-waking-and-queued-actions-accepted-2026-10-06
