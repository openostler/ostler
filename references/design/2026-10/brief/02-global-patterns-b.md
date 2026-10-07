---
title: "Designer brief — global patterns (b): toasts, confirms, permissions and the driving-state frames"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-phone-comms-addon-design.md, decisions/adr-0033-action-categories-and-approvals.md]
summary: >
  Patterns for telling and asking. Toasts and snackbars (one at a time, with Undo, and only
  "Park to edit" and "Sent" while Moving); the confirm sheets for every action that reaches
  the gate, with the ADR-0033 tiers (Tier 1 clear codes with snapshot and safety warning,
  Tier 2 checklist and Stop, Tier 3 wizard and typed confirm, Tier 4 listed only) and phone
  approval; browser and OS permission prompts with our own explanation first; the Moving
  lockout view; Open on phone; Park to edit; the head-unit Passenger view; and the phone's
  Moving banner. Discovery 2 Td5 examples throughout.
---

# Global patterns (b): toasts, confirms, permissions, driving-state frames

### ia-toast — Toasts and snackbars  [New]
- **Purpose:** a short note that something happened, with Undo when it can be undone.
- **Owner:** os
- **Opens from → goes to:** any finished action → nothing, or Undo.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** Night on phone and HU-7 for each variant; Night dim + Moving on HU-7 ("Park to edit", "Sent"); Day on phone.
- **Content:** one bar on `surface-2`, `radius-sm`: icon + one line ≤ 60 characters (≤ 30 on head units) + at most one text button. Variants: "Layout saved" · "Widget removed · **Undo**" · "Saved, will send later" (queued) · "Export ready · **Open**" · "Park to edit" (3 s) · "Sent" (2 s, after a canned reply).
- **States:** one at a time; a new one replaces the old; 4 s, or 8 s with a button · phone: above the bottom bar · head unit: bottom of main, passenger side · reduced motion: appears without a slide.
- **Safety and driving rules:** while Moving on a head unit only "Park to edit" and "Sent" show; any other toast raised while Moving is dropped, never held for Parked; never a toast when a Drive mode switches ([Drive modes §6][dm-6]); errors that need action are not toasts.
- **Components:** Toast (new), Button (ghost).
- **Spec refs:** [app model §6][am-6] (`ui.toast`), [shell input §14][si-14], [UI §12.1][ui-12.1].
- **Open questions:** **Decided (item 61):** other toasts raised while Moving are dropped, not held until Parked.

### Pattern: confirm sheets and the ADR-0033 tiers
- **Screen block:** `diagnose-confirm` in [50-vehicle-b-faults](50-vehicle-b-faults.md#diagnose-confirm--action-confirm-sheets-tier-13-clear-codes--existing); phone approval is `diagnose-phone-approve` in [50-vehicle-c-actions](50-vehicle-c-actions.md#diagnose-phone-approve--approve-on-phone--new). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** the one sheet that stands between a tap and anything that reaches the car's gate.
- **Opens from → goes to:** any action button in any app (Diagnostics, Security, an accessory app) or in Settings → Network → run, queue or cancel → result.
- **Content (top to bottom, by tier from [UI §7][ui-7] and [ADR-0033][adr-33]):**
  - **Tier 0 Read:** no sheet.
  - **Tier 1 (Maintenance, Comfort, Security):** title names action and system: "Clear 3 codes from SLABS?"; consequence: "Freeze frames will be lost."; note: "A snapshot of codes and freeze frames is saved to Trips first."; for brakes or ABS an extra `warn` line: "The fault may still be present. Braking may be degraded."; buttons **Cancel** (focused) and **Clear codes** (danger). Airbag offers no clear at all.
  - **Tier 2 Actuate:** precondition checklist ticked from live data where it can be ("Parked", "Ignition on", "Battery 12.4 V, above the floor"), else the user ticks it; **Cancel** / **Start test**; then the ActiveTestBanner with **Stop** on every screen and an auto-timeout.
  - **Tier 3 Procedure:** opens the procedure wizard (`diagnose-procedure-start` → `diagnose-procedure-step` → `diagnose-procedure-end`, drawn on the Wizard frame `ia-kit-wizard`) and starts with a typed confirm: "Type SLS height calibration to start".
  - **Tier 4 Code:** listed for honesty with "Not runnable in Ostler"; never a button.
  - `candidate` or `experimental` actions show the word on the button and in the sheet.
- **States:** waiting on phone approval: "Approve on your phone" with **Cancel** · phone side: "Run SLABS pump test? Requested from the head unit" **Approve** / **Cancel**, then **Stop** for the whole action · result: "2 of 3 codes cleared" from the re-read · honest refusal: "The ECU refused with the engine running. Switch the engine off, ignition on, and try again." · queued (Brain asleep, Tier 1 only): "Queued · runs when the Brain is ready · expires 14:35 · Cancel".
- **Safety and driving rules:** Cancel focused; `ok` within 500 ms ignored; no countdown auto-confirm; typed confirms Parked only; Tiers 1–3 refused while Moving except Comfort and arming ([shell input §7][si-7], [UI §7.2][ui-7.2]).
- **Components:** Sheet, Button (Cancel, danger), Checklist (new), Text field, ActiveTestBanner.
- **Spec refs:** [UI §7][ui-7], [§7.1][ui-7.1], [§7.2][ui-7.2], [shell input §7][si-7].

### ia-permission-prompt — Browser and OS permission prompts  [New]
- **Purpose:** ask for a phone or browser permission at the moment it is needed, after saying why.
- **Owner:** os
- **Opens from → goes to:** the feature that needs it → our sheet → the OS prompt → the feature, or a denied card.
- **Layout classes:** phone · tablet · desktop. **Draw first:** Night and Day on phone for Bluetooth, location and notifications.
- **Content (our sheet first):** 1. Icon and title: "Bluetooth to reach the node". 2. Why, in one line: "Ostler talks to the node over Bluetooth when there is no Brain." 3. What stays where: "Location stays on this phone unless you share it." 4. **Continue** (opens the OS prompt) and **Not now**. Permissions: Bluetooth, local network, location (and background location for trips), notifications (alarm and shares), microphone (push-to-talk, Speak a reply), camera (QR codes), contacts (Phone & Comms picker).
- **States:** denied: inline card "Notifications are off for Ostler · **Open settings**" · granted: no screen · browser (Web Bluetooth, geolocation): the same sheet, then the browser's own prompt.
- **Safety and driving rules:** never all at once on first launch; never while Moving on a head unit (head units are set up by the install); alarm notifications explain that alarms never wait for the phone.
- **Components:** Sheet, Button, Card (tone), Icon.
- **Spec refs:** [app model §7.1][am-7.1], [§14.3][am-14.3], [Phone & Comms §7.2][pc-7.2]. The companion app's first-run overview of all permissions is `setup-app-permissions` in [10-onboarding-b](10-onboarding-b.md#setup-app-permissions--companion-app-what-the-app-may-use--proposed); this block is the prompt at the moment of use.

### Pattern: the Moving lockout view
- **Screen block:** `shell-locked-view` in [40-drive-b](40-drive-b.md#shell-locked-view--locked-view-available-when-parked--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** stand in for any page the current driving state does not allow.
- **Opens from → goes to:** any locked route while Moving → Open on phone, Passenger view, Back to Drive.
- **Content:** 1. The page's icon and name ("Trips"). 2. "Available when parked" (≥ 24 px). 3. **Open on phone** (when a phone is paired). 4. **Passenger view** (only when every item on the page is vehicle state, own route or a driving camera). 5. **Back to Drive**.
- **States:** no phone paired: Open on phone absent, a line "Pair a phone to open pages there" · fail closed: a page with no Moving rule is locked.
- **Safety and driving rules:** ≤ 3 buttons, no text entry, no scrolling ([UI §12.1][ui-12.1]).
- **Components:** Card, Button.
- **Spec refs:** [UI §3.5][ui-3.5], [UI §12.1][ui-12.1].

### ia-open-on-phone — Open on phone  [New]
- **Purpose:** hand the locked page to a paired phone, the preferred passenger path.
- **Owner:** os
- **Opens from → goes to:** **Open on phone** on a locked view → the phone opens the same route.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** Night dim + Moving on HU-7 (sent); Night and Day on phone (received).
- **Content:** head unit: "Sent to your phone" (2 s), then back to Drive mode. Phone: notification "From the car: Trips" → opens Trips; if the car is Moving, the passenger question first.
- **States:** phone not reachable: "Phone not reachable" · two phones: a `short_list` of ≤ 6 names.
- **Safety and driving rules:** the phone stays view-only for car actions while Moving.
- **Components:** Toast, `short_list`, OS notification.
- **Spec refs:** [UI §12.1][ui-12.1].

### Pattern: Park to edit
- **Screen block:** `shell-park-to-edit` in [40-drive-b](40-drive-b.md#shell-park-to-edit--park-to-edit-toast-and-finish-editing-when-parked--new). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** the only answer a driver-facing display gives to an edit gesture while Moving.
- **Opens from → goes to:** long-press on the strip, an empty area, a widget or the launcher menu's Edit home pages while Moving → nothing.
- **Content:** 1. Toast with the `local_parking` icon and "Park to edit" for 3 s. 2. Entering Moving while editing: the editor closes to Drive mode; at the next Parked a card "Finish editing when parked" with **Resume** and **Discard**. 3. An edit made on a phone for a moving display: "Applies when the car is parked".
- **States:** Idling without Park evidence: as Moving.
- **Safety and driving rules:** R1 and R7 ([Drive modes §8.1][dm-8.1]); the server refuses the write.
- **Components:** Toast, Card, Button.
- **Spec refs:** [Drive modes §7.1][dm-7.1], [§8.1][dm-8.1], [UI §15.2][ui-15.2].

### Pattern: the Passenger view
- **Screen block:** `shell-passenger-view` in [40-drive-b](40-drive-b.md#shell-passenger-view--passenger-prompt-badge-and-frame--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** let a passenger see driving-related content on the car screen, per trip, with care.
- **Opens from → goes to:** **Passenger view** on a locked view → prompt → the page in a frame → **Back to Drive**.
- **Content:** 1. Prompt: "Are you a passenger? The driver must not use this while driving." **I'm a passenger** / **Cancel** (Cancel focused). 2. A frame round the viewport and a "Passenger view" badge in the strip. 3. **Back to Drive** always one tap.
- **States:** ends on Parked, ignition off, a new trip, unknown speed, reverse, service mode, a red telltale or 15 minutes; then asks again next time.
- **Safety and driving rules:** no "always", no setting to skip; no video, messages, other people, text entry or actions ([UI §12.1][ui-12.1]).
- **Components:** Sheet, Button, Chip (badge), Frame (new).
- **Spec refs:** [UI §12.1][ui-12.1].

### Pattern: the phone while Moving
- **Screen block:** `shell-phone-moving-banner` in [40-drive-b](40-drive-b.md#shell-phone-moving-banner--phone-moving-banner-and-im-a-passenger--existing). This section is the rule every page follows; draw the frames from the screen block.
- **Owner:** os (no app can change this rule).
- **Purpose:** on a phone, say the car is moving and ask once before non-driving views.
- **Opens from → goes to:** any page while Moving → "I'm a passenger" → the page, view-only.
- **Content:** 1. Banner under the strip in `warn` tone: "Car moving". 2. On non-driving views a card: "Are you a passenger?" **I'm a passenger** / **Not now**. 3. After yes: a small "Passenger" chip; car actions show "Needs the car stopped".
- **States:** asks again after a stop or a new trip; never "always".
- **Safety and driving rules:** [UI §12.1][ui-12.1]; logged locally like the head-unit grant.
- **Components:** Card (tone), Button, Chip.
- **Spec refs:** [UI §12.1][ui-12.1].

[adr-33]: ../../../../decisions/adr-0033-action-categories-and-approvals.md
[am-6]: ../../../../specs/2026-10-06-app-model-design.md#6-the-shell--app-api
[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[am-14.3]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#6-the-switcher
[dm-7.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#71-common-states-and-gestures
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[pc-7.2]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#72-android-notification-bridge-opt-in
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[si-14]: ../../../../specs/2026-10-07-shell-input-design.md#14-amendment-2026-10-07-dmd-round-approved-editing-and-the-movable-switcher
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-7]: ../../../../specs/2026-10-06-ui-architecture-design.md#7-safety-gating-tiers
[ui-7.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#71-action-categories-the-second-axis-adr-0033
[ui-7.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#72-phone-approval-and-remote-paths-adr-0033
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-15.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#152-editing-changes-34-and-53
