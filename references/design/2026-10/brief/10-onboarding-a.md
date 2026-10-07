---
title: "Designer brief 10-a — onboarding: the setup flows on every surface, welcome and first-run preferences"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-source-adapters-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-vehicle-packs-generic-obd2-bmw-e-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-02-hardware-platform-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md]
summary: >
  First of the onboarding brief files (10-a to 10-e). It maps every first-run and setup
  flow as a step table: a new Brain with its own head-unit screen, a phone or tablet
  browser, a desktop (with or without a Brain), the companion phone app, Ostler Diagnostics
  alone (node plus phone), joining a household by invite, adding a vehicle or a display
  later, and moving to a new Brain. Each step names its screen ID, what the user does, what
  can fail and how to recover. It then gives the blocks for the welcome screen (setup code,
  set up here or from a phone, restore) and the first-run language and units step. The
  owner of every screen here is the OS; apps, the dashboard builder and the theme wizard are
  installed or called as steps. The rest of the steps are in 10-b to 10-e.
---

# 10-a — Onboarding flows, welcome and first-run preferences

Setup is one **wizard** that any signed-in owner can resume on any surface. Its progress
lives on the Brain (or, on Ostler Diagnostics alone, in the phone app). Only owner creation
is required, because a device has no default password ([Accounts §2.1][acc-2.1]); every
other step has **Skip for now**, and a skipped step becomes a row in the setup checklist
card on the first home page (`setup-checklist`, [10-d](10-onboarding-d.md)).

**Owner: os.** First-run setup is part of the operating system's own UI, so every screen
in these files is owned by the OS unless its block says otherwise. On a bare OS no app is
installed yet: setup installs them (`setup-apps`), then each app runs its own setup flow
(the `90-appframe-*` files). The dashboard builder and the theme wizard are launcher screens
(the `45-launcher-*` files); setup only calls them as steps.

**Files.** 10-a flows, welcome, preferences · [10-b](10-onboarding-b.md) trust, companion
app, sign-in, invites, device codes · [10-c](10-onboarding-c.md) vehicle, source, node,
adapter, first contact · [10-d](10-onboarding-d.md) choose your apps, display, people, Car
profile, app permissions, phone, summary, checklist · [10-e](10-onboarding-e.md) backup, restore, add a Brain, move to
a new Brain. Fitting the node and wiring the Brain are in the `20-hardware-*` files.

**Wizard frame (all steps).** A **SetupStepper** (new component) heads each step: Back,
the step title, "Step 3 of 9" with a thin progress track, and **Skip for now** on the
trailing side where allowed. The primary Button sits at the bottom (phone) or on the
passenger side (head units). A step never scrolls on a head unit; long content splits into
two steps. Every head-unit step is Parked only (see "The unknown-speed problem" below).

## Flows

### F1. New Brain, set up on its own head-unit screen

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `setup-welcome` | reads the 8-digit setup code; picks **Set up on this screen** or **Set up from my phone** (QR) | code expires (15 min) → **New code**; speed unknown → only the code and QR show (below) |
| 2 | `setup-prefs` | picks language, units and clock | — (defaults kept) |
| 3 | `accounts-s1` | enters the code, a name, a passkey or password | wrong code → "That code doesn't match" (ask for **New code**); weak password → inline reason |
| 4 | `setup-apps` | picks a flavour (Diagnostics, Guardian, Ostler Brain or Custom); its apps install from the bundled Store catalogue | an app fails to install → row "Not installed · Retry"; setup goes on |
| 5 | `setup-vehicle-add` | picks **Land Rover Discovery 2 · Td5**, or **Detect from the car** | pack not installed → "My car isn't listed" |
| 6 | `setup-vehicle-name` | names the car, confirms right-hand drive | — |
| 7 | `setup-source` | picks **Ostler Diagnostics node**, **An adapter I already have** or **Not now** | a node is already on the car → adapter row disabled (ADR-0044) |
| 8a | `setup-node-pair` | presses the node's button when asked | no node found → "Is it plugged in and in setup mode?"; press timed out → **Try again** |
| 8b | `adapter-connect` → `adapter-verdict` | picks transport, pairs, waits for detection | clone → "Clone: read-only"; not Parked → detection waits |
| 9 | `setup-first-contact` | parks, ignition on, engine off; watches the checks | bus busy, ECU refused, no ECU → each with its own fix (10-c) |
| 10 | `setup-display` | names this screen, confirms it is driver-facing | — |
| 11 | dashboard builder (the `45-launcher-*` files) | picks presets for this car and this display; they become its home pages | — (the flavour's default pages are kept) |
| 12 | theme wizard (the `45-launcher-*` files) | picks colours and wallpaper | — (the default theme is kept) |
| 13 | `setup-people` → `setup-car-profile` | adds family drivers, sets the Car profile | invite expires (48 h) → resend |
| 14 | each app's setup flow (the `90-appframe-*` files) | runs the setup flow of every app just installed, one after another; for the Phone app this is `phone-pairing` | an app's flow skipped → checklist row |
| 15 | `setup-summary` | checks the list and goes to the home pages | any red row → its **Fix** button reopens that step |

### F2. Phone or tablet browser (same Brain)

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | (camera app) | scans the QR on the head unit, or types `ostler-xxxx.local` | name not found → type the address the welcome screen shows |
| 2 | `setup-trust` | installs this Ostler's certificate, compares the fingerprint | fingerprint differs → **Stop** (wrong device) |
| 3 | `setup-welcome` (phone) or `accounts-s2` | not set up yet: as F1 from step 2; set up: signs in | — |
| 4 | F1 steps 2–15 | as F1; detection steps still need the car Parked | the server refuses detection while not Parked |

### F3. Desktop

- **With a Brain:** as F2 at desktop size. The trust step names the desktop browser.
- **Laptop as the host (no Brain):** the installer opens `http://localhost`. `setup-welcome`
  shows the code from the console; F1 runs with the laptop as host. On `setup-source` the
  node row reads "Needs a Brain or the phone app"; adapters (USB K-line cable, ELM327,
  OBDLink, SocketCAN) are offered ([Adapters §3][sa-3]). No display step (not a head unit).

### F4. Companion phone app

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `setup-app-connect` | picks **Find my Ostler** (Brain on this Wi-Fi), **Scan the car screen**, **Set up an Ostler Diagnostics node** or **Enter an address** | nothing found → check Wi-Fi; Local network permission off → Settings |
| 2 | `setup-app-permissions` | allows Bluetooth, Local network, Notifications, Location (each optional) | denied → feature row greys with "Turn on in Settings" |
| 3 | `accounts-s2` or `setup-welcome` | signs in, or sets up a new Brain as F2 | — |

### F5. Ostler Diagnostics alone (node plus phone app, no Brain)

The node's setup helper order: pair and set the owner → uplink → pack → first scan
([ADR-0039 §7][adr-39]).

| # | Screen | The user… | Can fail → recovery |
|---|---|---|---|
| 1 | `setup-app-connect` | taps **Set up an Ostler Diagnostics node** | Bluetooth off → turn on |
| 2 | `setup-node-pair` (phone) | presses the node's button, or scans the label QR; becomes the owner | press timed out → hold the button again |
| 3 | `setup-node-uplink` | picks the car or phone hotspot, or the node's 4G | Wi-Fi password wrong → retry |
| 3b | `setup-apps` | picks the Diagnostics or Guardian flavour (from the catalogue bundled in the phone app) | — |
| 4 | `setup-vehicle-add` → `setup-vehicle-name` | chooses or detects the pack, names the car | detection needs Parked |
| 5 | `setup-first-contact` | runs the first scan | as F1 step 8 |
| 6 | `setup-summary` | finishes | — |

### F6. Joining a household (person invite)

`setup-invite-accept` (from a link or QR the owner sends) → `setup-trust` if this browser
does not trust the Brain yet → own passkey or password → the home pages. Fails: expired, used,
revoked, or a certificate that does not match the invite → stop, ask for a new invite.

### F7. Later setups (from the app drawer and Settings)

- **Add a vehicle:** Settings → Vehicles → **Add vehicle** runs F1 steps 5–9.
- **Add a display:** a new screen that opens the Brain shows `setup-display` once.
- **Link a TV, script or second screen:** `setup-device-code` ([10-b](10-onboarding-b.md)).
- **Add apps:** the Store app; each new app runs its setup flow (`90-appframe-*`).
- **Rebuild dashboards or change the theme:** the dashboard builder and theme wizard (`45-launcher-*`).
- **Add a Brain to my node, restore, move to a new Brain:** [10-e](10-onboarding-e.md).

### The unknown-speed problem (owner decision needed)

A brand-new Brain has no node and no adapter yet, so its speed is **unknown**, and unknown
speed counts as Moving on every head-unit class ([UI §3.5][ui-3.5]). Taken literally, the
head unit would show only the locked view during first run. This brief keeps the rule and
draws the head unit's first-run in that state as the **locked view plus the setup code**:
large digits, the QR "Set up from my phone", no text entry. Typing then happens on a phone
(a passenger device, [UI §12.1][ui-12.1]). Once a node or adapter reports speed 0 for
more than 5 s, the head unit offers **Set up on this screen**. Draw both frames.

---

### setup-welcome — Set up this Ostler  [New]
- **Owner:** os
- **Purpose:** the first page of a device with no owner, on every surface; also the start
  of restore.
- **Opens from → goes to:** any page of a Brain or laptop host with no owner ("every page
  shows 'Set up this Ostler'", [Accounts §2.1][acc-2.1]); the phone browser after
  `setup-trust`; `setup-app-connect` → **Set up on this screen** → `setup-prefs`;
  **Set up from my phone** → QR (stays here); **Restore from a backup** → `setup-restore`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (Parked); hu7 Night-dim unknown speed (locked view + code); phone Day; hu5 Night.
- **Content (top to bottom):**
  1. Language row: `language` "English" (opens the list, `setup-prefs` §1). Head units
     only; phones follow the OS and offer it in step 2.
  2. Wordmark and title "Set up this Ostler"; one line "This Ostler has no owner yet."
  3. **Setup code** card (only on the device's own screen and console, never on a phone):
     kicker "Setup code", eight digits in `type-num-xl` as "4 digits · 4 digits", caption
     "Single use · expires in 14 min" with a countdown, Button **New code** (ghost).
  4. **QR panel** (new component): QR to `https://<device-name>/setup`, the address in
     text under it ("ostler-xxxx.local"), caption "Scan with your phone's camera".
  5. Buttons: **Set up on this screen** (primary; hidden while speed is unknown or
     Moving), **Restore from a backup** (secondary), and on phones **I have the code**
     (primary) which opens `accounts-s1`.
  6. Footer: "Ostler never asks for your car's VIN, and no account with us is needed."
     Link "What is the setup code?" opens a sheet: the code proves you are at the device;
     a lost owner runs `ostler auth reset-owner` on the console.
- **States:** loading: skeleton card. Error (server unreachable): Card `warn` "Can't reach
  this Ostler" + **Retry**. Offline: works (local). No vehicle: normal, this is first run.
  Parked: all of §5. Idling: as Parked but **Set up on this screen** needs Park evidence.
  Moving / unknown: the locked view (`shell-locked-view`) with §3 and §4 only.
  Passenger: n/a. Locked: owner exists → this page never shows; the device opens sign-in.
- **Safety and driving rules:** no text entry on a driver-facing head unit unless Parked
  ([UI §12.1][ui-12.1]); the code never travels to another screen; the QR holds no secret.
- **Components:** SetupStepper (new, hidden on this first page), Card, QR panel (new),
  Button, ListRow (language), Sheet.
- **Spec refs:** [Accounts §2.1][acc-2.1] · [Accounts §14.7 S1][acc-14.7] ·
  [UI §3.5][ui-3.5] · [UI §12.1][ui-12.1] · [ADR-0021][adr-21].
- **Open questions:** (1) The unknown-speed frame above (the setup code shown on the
  locked view) needs the owner's yes. (2) May the QR carry the setup code so the phone
  skips typing it? This brief says no: seeing the screen is the physical step.

### setup-prefs — Language and units  [Proposed]
- **Owner:** os
- **Why the app needs it:** the first values the owner sees (coolant, boost, ride
  heights) must already be in their units and language.
- **Purpose:** set the device defaults once; each user can change their own later in
  `preferences`.
- **Opens from → goes to:** `setup-welcome` → **Continue** → `accounts-s1`. Back →
  `setup-welcome`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day; hu5 Night (tightest).
- **Content (top to bottom):**
  1. **Language**: ListRow "Language · English (United Kingdom)" → a `short_list`-style
     sheet of the shipped languages. Phones preselect the OS language.
  2. **Units**: Segmented "Metric · Imperial (UK) · US"; a preview line beneath, using real
     pack signals in the chosen units: "Coolant °C · Boost kPa · Speed km/h · Ride height
     mm" (Imperial UK: "°C · psi · mph · in"; the exact sets come from the unit registry).
     A ListRow **Customise** opens per-quantity choices (temperature, pressure, speed,
     distance, volume, fuel economy).
  3. No theme row: setup runs in Night (the default, [visual §1][vds-1]); colours and
     wallpaper come later in the theme wizard step (the `45-launcher-*` files).
  4. **Clock**: Segmented "24-hour · 12-hour".
  5. Button **Continue** (primary).
- **States:** loading: the language list shows a spinner row. Offline: works. Parked: full.
  Idling: full (no text entry here). Moving / unknown: locked view. Passenger: n/a.
- **Safety and driving rules:** Parked on driver-facing displays; setup screens never glow on
  head units ([visual §1][vds-1] principle 6).
- **Components:** SetupStepper (new), ListRow, Segmented, Sheet, Button.
- **Spec refs:** [visual §1][vds-1] · [visual §3.1][vds-3.1] ·
  [UI §10.1 (Intl units)][ui-10.1] · [App model §4.2 (i18n)][am-4.2].
- **Open questions:** (1) Which languages ship first? Until decided, draw English (United
  Kingdom) selected and two greyed rows "More languages later". (2) **Decided (item 63):**
  units are a device default set here, with a per-user override in `preferences`; the
  garage's per-vehicle units do not override them.

[acc-2.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[sa-3]: ../../../../specs/2026-10-07-source-adapters-design.md#3-where-adapters-sit-with-the-node-first-rules
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-10.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#101-standards-per-phase
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[vds-1]: ../../../../specs/2026-10-07-visual-design-system-design.md#1-principles
[vds-3.1]: ../../../../specs/2026-10-07-visual-design-system-design.md#31-surfaces-text-accent-and-status-per-theme
[am-4.2]: ../../../../specs/2026-10-06-app-model-design.md#42-field-rules
[adr-21]: ../../../../decisions/adr-0021-local-https-on-the-device.md#decision
[adr-39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
