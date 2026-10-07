---
title: "Designer brief 10-d — onboarding: choose your apps, this display, people and the Car profile, app access, phone, the summary and the checklist"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-phone-comms-addon-design.md]
summary: >
  Fourth onboarding brief file. Choose your apps (a product flavour: Diagnostics, Guardian,
  Ostler Brain or Custom, installed from the bundled Store catalogue), the access sheet each
  app shows before install (needs, data classes, permissions), registering a head unit or
  other display (name, layout class, driver side, whether the driver can see it, buttons),
  the people who use the car and the Car kiosk profile, the Phone app's pairing as its own
  setup flow, the "everything connected" summary that ends the wizard, and the setup
  checklist card on the first home page. All owned by the OS except phone pairing.
---

# 10-d — Apps, display, people, Car profile, phone, summary and checklist

### setup-display — This screen  [New]
- **Owner:** os
- **Purpose:** register this display once: name, size class, driver side, who can see it.
- **Opens from → goes to:** F1 step 9; a new display opening the Brain for the first time
  (shown once, Parked); Settings → Network → the display's page → **Display settings**. →
  the dashboard builder step (`45-launcher-*`), or back to where it came from.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · tablet. **Draw first:** hu7 Night; hu5
  Night; huwide Night; tablet Night (rear-seat case).
- **Content (top to bottom):**
  1. **Name** field, prefilled "Dash screen" (rear tablet: "Rear screen").
  2. **Screen size** row: the detected class and size ("HU-7 · 1024 × 600") with
     **Change** (a Sheet of the classes; the same choice as the kiosk flag, [UI §3.1][ui-3.1]).
  3. **Driver side** Segmented "Right · Left" (from the vehicle; [UI §3.3][ui-3.3]).
  4. **Who can see this screen?** Segmented "The driver can see it" (selected, default) ·
     "Passengers only". Choosing "Passengers only" opens a confirm Sheet (Cancel focused):
     "Only for a screen out of the driver's sight and reach, such as a rear-seat tablet.
     Head units are always driver-facing." Owner only; every head-unit class stays
     driver-facing ([UI §12.1][ui-12.1]).
  5. **Starts as** row: "Car (no sign-in)" with a link to `setup-car-profile`.
  6. **Home pages** row: "Built in the next step" (the dashboard builder in the
     `45-launcher-*` files picks presets for this car and this class; Drive swipes between
     the pages, [Drive modes §5.9][dm-5.9] gives the old per-class defaults).
  7. **Buttons** row: "Steering-wheel and remote buttons" → `shell-buttons` (**Test
     buttons** there).
  8. Button **Save**.
- **States:** loading: rows skeleton. Error: save refused while Moving (`409`) → "Park to
  save". Offline from the Brain: "Can't reach the Brain" + Retry. Moving / unknown: locked
  view. Passenger-only display: rows 4–5 read-only.
- **Safety and driving rules:** Parked only; nothing here can mark a display passenger-only
  while Moving; changes made elsewhere for a Moving display wait for Parked
  ([Drive modes §8.1 R7][dm-8.1]).
- **Components:** SetupStepper (new), text field, Segmented, ListRow, Sheet, Button.
- **Spec refs:** [UI §3.1][ui-3.1] · [UI §12.1][ui-12.1] · [Shell input §8][si-8] ·
  [Drive modes §8.3][dm-8.3] · [Drive modes §5.9][dm-5.9] · [launcher §10.2][lw-10.2].
- **Open questions:** (1) The Car kiosk session is bound to `localhost`, never an IP range
  ([Accounts §14.7 S4][acc-14.7]). A head unit that browses the Brain over Wi-Fi (an Android
  head unit) is not `localhost`: how does it get the Car session? (2) Is "Passengers only"
  set here or only in the install configuration file?

### setup-people — Who uses this car?  [New]
- **Owner:** os
- **Purpose:** add the household and anyone who drives, so trips record who drove and the
  right people can sign in at the car.
- **Opens from → goes to:** F1 step 10 (S1's optional "Invite someone"); → `setup-car-profile`
  → next step. The full editor is `accounts-s5`.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; phone Day.
- **Content (top to bottom):**
  1. **You** ListRow: name, role Chip "Owner".
  2. **Add a person** Button → Sheet: Name; Role Segmented "Driver · Mechanic · Viewer"
     with the role's line from [Accounts §3.1][acc-3.1]; Expiry (Mechanic always: "24 h"
     default, up to 14 days); **Show on the car screen** toggle; **Create invite** → QR
     panel (new), **Copy link**, **Share**; "Expires in 48 h".
  3. **Add a name only** Button: "For someone who drives but won't sign in. Trips can say
     they drove; they get no rights."
  4. **Pending invites** list with countdowns and **Revoke**.
  5. Line "Each person sets their own passkey or password. A head-unit PIN is set after
     their first sign-in."
- **States:** empty (owner only): the list shows "Just you so far." Invite expired → row
  `warn` "Expired" + **Resend**. Offline: invites still made; they redeem on the car's
  network. Moving (phone): open.
- **Safety and driving rules:** owner operations; on a head unit Parked only.
- **Components:** ListRow, Chip (role), Sheet, Segmented, QR panel (new), Button.
- **Spec refs:** [Accounts §5.1][acc-5.1] · [Accounts §3.1][acc-3.1] · [Accounts §14.7 S1,
  S4, S5][acc-14.7].
- **Open questions:** none.

### setup-car-profile — The Car profile  [New]
- **Owner:** os
- **Purpose:** explain and set what the head unit does with nobody signed in.
- **Opens from → goes to:** `setup-people`; `setup-display` "Starts as"; Settings → Users
  → **Car profile**. → next step.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Night.
- **Content (top to bottom):**
  1. Title "Car"; line "The car screen starts as Car. Anyone in the car can use it without
     signing in."
  2. **Car can**: Chips "Read" and "Comfort" (fixed). Line "Clearing codes, Security and
     more need a person signed in."
  3. **Switching person**: "Parked only, with a 6-digit PIN or approval from their phone.
     Everyone signs out when the ignition goes off."
  4. **Who appears on the car screen**: the people with **Show on the car screen** on, each
     a tile preview (name only).
  5. **Lock car layouts** toggle: "Only an owner signed in can change the car screen's
     layouts" ([Drive modes §8.3][dm-8.3]).
  6. **Trips without a person** record "Car" as the driver.
- **States:** no people yet: §4 reads "Only Car for now". Moving: locked view on head units.
- **Safety and driving rules:** the kiosk session is Read and Comfort only; Tier 2–3 still
  need a phone approval ([Accounts §2.3][acc-2.3], [§14.7 S4][acc-14.7]).
- **Components:** Card, Chip (status), ListRow, toggle (as Segmented "On · Off"), Button.
- **Spec refs:** [Accounts §2.3][acc-2.3] · [Accounts §3.1][acc-3.1] · [Accounts §14.7 S4][acc-14.7]
  · [Drive modes §8.3][dm-8.3].
- **Open questions:** none.

### setup-apps — Choose your apps  [New]
- **Owner:** os
- **Purpose:** pick a product flavour, which preinstalls its apps from the Store catalogue
  bundled with the OS (no internet needed); Custom picks app by app.
- **Opens from → goes to:** F1 step 4 (after owner creation); → `setup-app-access` for each
  app that asks for access → `setup-vehicle-add`. Later: the Store app (`70-store-*`).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day; hu5 Night.
- **Content (top to bottom):**
  1. Title "Choose your apps"; line "You can add or remove apps later in the Store."
  2. Four flavour Cards (one selected, `accent-soft`), each with an icon, name, one line and
     its app list in Chips:
     - `build` **Diagnostics** "Read and clear faults, live data, trips." Apps: Diagnostics,
       Trips, Security, Starter widgets, Default theme.
     - `shield` **Guardian** "Alarm and tracking only." Apps: Security (with its widgets),
       Default theme.
     - `dashboard` **Ostler Brain** "The car's screen: gauges, map, media." Apps:
       Diagnostics, Trips, Security, Map, Media, Audio, Starter widgets, Default theme;
       Camera when a camera is found, Radio when a tuner is found. One unticked option under
       it: "Ostler is the head unit (Radio, Audio and Media drive the speakers)"; offered,
       never the default (item 55).
     - `tune` **Custom** "Pick each app."
  3. Custom only: the bundled catalogue as ListRows with a check each (name, one line,
     size), grouped "Car", "Drive and travel", "Media and calls", "Look and feel".
  4. Line under the cards: "Each app brings its own setup, which runs after the car is
     connected."
  5. Button **Install** (primary) → progress rows per app ("Installing", "Installed",
     "Not installed · Retry").
- **States:** loading: the catalogue is local, so this is near-instant. Error: one app fails
  → its row `warn` with **Retry**; setup continues. Offline: works (bundled catalogue).
  Moving / unknown: locked view on head units. Guardian on a head unit: line "Guardian has no
  dashboards; this screen will show Security only."
- **Safety and driving rules:** installing is an owner operation on a local link, Parked on
  head units ([UI §12.4][ui-12.4]); safety items stay with the OS whatever is installed
  (the fault telltale and alarm alerts appear even with no app).
- **Components:** SetupStepper (new), Card (selectable), Chip, ListRow, progress rows, Button.
- **Spec refs:** [App model §14][am-14] · [UI §12.4][ui-12.4] · [ADR-0046 §5][adr-46-5] ·
  [Store §7][st-7].
- **Open questions:** **Decided (items 11, 41, 43):** Diagnostics = Diagnostics, Trips,
  Security, starter widgets, default theme; Guardian = Security and its widgets, default
  theme; Ostler Brain = those plus Map, Media and Audio, with Camera and Radio when their
  hardware is found. **Decided (item 55):** "Ostler is the head unit" is offered, not the
  default.

### setup-app-access — Review an app's access  [New]
- **Owner:** os
- **Purpose:** show, before an app is installed or turned on, what it needs, which data
  classes it reads and what it may ask for; this is an owner operation.
- **Opens from → goes to:** `setup-apps` **Install** (one sheet per app that reads a data
  class or asks a permission); the Store app's install. **Allow** → next app, then the
  flow continues; the app's own setup flow runs later (`90-appframe-*`); **Cancel** skips it.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night.
- **Content (top to bottom),** example Maintenance:
  1. Icon, name, label Chip "App", publisher "openostler", version.
  2. **Needs** (its `requires` in words): "A vehicle in the garage."
  3. **Reads** (data classes, [Accounts §14.1][acc-14.1]): `maintenance` "Service records,
     reminders and fuel; costs". New classes an app adds start visible to you only.
  4. **May ask for**: "Notifications" (and, for others, "Location", "Wake the Brain").
  5. **Works on**: Chips "Head unit", "Phone", "Desktop" (its hosts).
  6. **While driving**: "Its pages lock while moving" or the template it uses.
  7. Buttons **Allow** (primary), **Cancel** (focused on head units).
  Example Cameras: Reads `video` "Live view of each camera you grant"; Needs "A camera".
- **States:** requirement not met → **Allow** disabled with "Needs a camera". Not owner →
  "Ask the owner to install this". Remote path → "Local links only". Moving: locked view.
- **Safety and driving rules:** owner, local link, Parked on head units ([UI §12.4][ui-12.4]);
  no data class carries the VIN ([Accounts §14.1][acc-14.1]).
- **Components:** Sheet, Chip (label, host), ListRow, Button.
- **Spec refs:** [App model §14][am-14] · [App model §4.2][am-4.2] · [Accounts §14.1][acc-14.1].
- **Open questions:** none.

### phone-pairing — Pair a phone  [Existing]
- **Owner:** app:phone
- **Onboarding additions only.** It is the Phone app's own setup flow, so it runs in F1
  step 14 only when the Phone app was installed; the screen is unchanged ([Phone & Comms §13][pc-13]). **Skip for now** adds a
  checklist row.

### setup-summary — Everything connected  [Proposed]
- **Owner:** os
- **Why the app needs it:** after many optional steps the owner needs one honest page that
  says what works now and what is missing, with a fix for each.
- **Purpose:** close the wizard with a status list.
- **Opens from → goes to:** the last wizard step; Settings → System → **Setup summary**. →
  the home pages (with `setup-checklist` when anything was skipped), or any row's **Fix**.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):** title "You're set up" (or "Almost there"); one ListRow per
  item, each with a status Chip (`ok` "Done", `warn` "Not set up", `text-3` "Skipped"):
  1. **Owner** "Passkey added" or "Password only".
  2. **Vehicle** "Discovery 2 Td5 · Land Rover Discovery 2 · Td5 pack".
  3. **Connection** the Link rung, for example "Data flowing · TD5 (engine)", and the
     source ("Ostler Diagnostics node" or the adapter with its verdict chip).
  4. **First scan** "Report saved" with the per-system summary.
  5. **This screen** "Dash screen · HU-7 · driver-facing".
  6. **People** the count of people and of pending invites. 7. **Apps** the flavour and each app, with its setup flow "Done" or "Not set up".
  8. **Phone** "Paired" or "Not set up". 9. **This phone** "Trusted".
  10. Buttons **Go to my home pages** (primary).
- **States:** every row honest: a source that dropped reads its rung, never "Done".
  Moving: locked view.
- **Safety and driving rules:** Parked only on driver-facing displays.
- **Components:** ListRow, Chip (status), Button.
- **Spec refs:** [UI §4.5][ui-4.5] · [UI §4.3][ui-4.3] · [Accounts §14.7][acc-14.7].
- **Open questions:** none.

### setup-checklist — Finish setting up (home page card)  [Proposed]
- **Owner:** os
- **Why the app needs it:** skipped steps must stay findable without nagging.
- **Purpose:** one dismissible card on the first home page listing what is left.
- **Opens from → goes to:** the first home page after a wizard with skips. Each row → its setup step.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night first home page with the card; phone Day.
- **Content:** kicker "Finish setting up", "4 of 7 done" with a thin progress track; up to
  4 rows (`short_list` style, ≤ 30 characters): "Connect the car", "Add a passkey", "Set up the Phone app",
  "Invite someone"; **Dismiss** (ghost). Medium card size.
- **States:** all done → the card goes. Dismissed → it moves to Settings → System → Setup
  summary. Moving: never shown on a head unit; it never replaces a warning or vehicle card.
- **Safety and driving rules:** like the old add-ons empty-state card ([UI §12.4][ui-12.4]);
  not a safety item, so the user may remove it ([Drive modes §7.2][dm-7.2]).
- **Components:** Card, ListRow, Button.
- **Spec refs:** [UI §12.4][ui-12.4] · [Drive modes §7.2][dm-7.2] · [App model §14][am-14].
- **Open questions:** is it an OS card or a widget from the starter widget pack?

[acc-2.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#23-sessions
[acc-3.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#31-roles
[acc-5.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#51-two-kinds-of-invite
[acc-14.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[dm-7.2]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#72-home
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-8.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#83-storage
[si-8]: ../../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[pc-13]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security
[ui-3.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#31-layout-classes
[ui-3.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#33-driver-side-rail-versus-bottom-bar
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#124-add-ons-catalogue-placement-changes-34s-more-and-home-rows
[lw-10.2]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#102-the-wizard
[adr-46-5]: ../../../../decisions/adr-0046-empty-os-every-app-an-add-on.md#5-product-flavours-are-preinstalled-sets-amends-adr-0039
[st-7]: ../../../../specs/2026-10-07-store-design.md#7-the-bundled-offline-catalogue
