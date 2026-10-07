---
title: "Designer brief 10-b — onboarding: trust, the companion app, owner creation, sign-in, invites and device codes"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-community-hub-design.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0032-one-node-optional-brain.md]
summary: >
  Second onboarding brief file. It covers how a phone, tablet or desktop comes to trust a
  Brain (the guided certificate step with a fingerprint check), the companion phone app's
  first screens (find or scan an Ostler, or set up an Ostler Diagnostics node; then the
  native permissions with a reason for each), the onboarding additions to the Existing
  owner-creation and sign-in screens (accounts S1 and S2), accepting a person invite to
  join a household, and approving a device code for a TV, second screen, script or tool.
  There is no Ostler-run account: the owner lives on the device, and the head unit runs as
  Car with no sign-in.
---

# 10-b — Trust, companion app, sign-in, invites and device codes

**Accounts in one paragraph.** Users live on the Brain (or, with no Brain, as paired phones
on the node). There is no email, no central account and no social login in this round
([Accounts §14.8][acc-14.8]). "Using Ostler without an account" means two things: anyone in
the car uses the head unit as **Car** (the kiosk session: Read and Comfort only, no sign-in,
[Accounts §2.3][acc-2.3]); and a friend elsewhere uses their own Ostler, never a login on
yours. The owner is always created first. The screens S1–S10 are Existing; this file adds
only what onboarding needs.

### setup-trust — Trust this Ostler on this device  [New]
- **Owner:** os
- **Purpose:** let a phone, tablet or desktop browser reach the Brain over HTTPS, so
  sign-in, passkeys and the offline app work ([ADR-0021][adr-21]).
- **Opens from → goes to:** F2 step 2, F6, `setup-app-connect` (the app does it without the
  install steps); `accounts-s3` "Add a passkey" when no trusted name exists. Done →
  `setup-welcome` (no owner) or `accounts-s2` (owner exists).
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; phone Day;
  desktop Night.
- **Content (top to bottom):**
  1. Title "Trust this Ostler"; line "Your phone needs this Ostler's own certificate once.
     Nothing goes through the internet."
  2. **Fingerprint check** Card: kicker "Compare with the car screen", the certificate
     fingerprint as four groups of four characters in `type-num-l`; the head unit shows the
     same four groups on `setup-welcome`. Buttons **They match** (primary), **They don't
     match** (danger ghost).
  3. **Steps for this device** (auto-picked, with a Segmented "iPhone · Android · Computer"
     to change): numbered ListRows, for example on iPhone "1 Download the profile",
     "2 Open Settings → Profile Downloaded → Install", "3 Turn on full trust for it".
     Button **Download certificate**.
  4. **Other ways** (collapsed): "Use this Ostler's public name" (only when the optional
     per-device public name is on, [Accounts §14.7 S3][acc-14.7]); "Use my Tailscale name".
  5. Status line after install: `check_circle` "Trusted · ostler-xxxx.local" in `ok`.
- **States:** loading: the step list shows skeleton rows. Error: download failed → Card
  `warn` + **Retry**. Not trusted yet: §5 reads "Not trusted yet" in `text-2`. Mismatch:
  full-width `alarm` Card "Stop. This is not the Ostler in your car." with **Start again**;
  nothing else is offered. Offline: works on the local network. Moving (phone): reading
  open; the phone is a passenger device ([UI §3.5][ui-3.5]).
- **Safety and driving rules:** none beyond the phone rules; never on a head unit (it uses
  `http://localhost`, [Accounts §14.7 S3][acc-14.7]).
- **Components:** SetupStepper (new), Card, Segmented, ListRow, Button, Chip (status).
- **Spec refs:** [ADR-0021][adr-21] · [Accounts §2.2][acc-2.2] · [Accounts §14.7 S3][acc-14.7].
- **Open questions:** ADR-0021 leaves the trust approach to its own spec. How does the
  first page load before the certificate is trusted (a plain-HTTP page that only serves the
  certificate, or the browser's warning first)? The brief draws the page as if it loads.

### setup-app-connect — Companion app: connect to your Ostler  [New]
- **Owner:** os
- **Purpose:** the first screen of the companion phone app: find a Brain, or set up an
  Ostler Diagnostics node with no Brain.
- **Opens from → goes to:** first app launch; later Settings → Network → **Add an Ostler**.
  Found Brain → `setup-app-permissions` → `accounts-s2` or `setup-welcome`; node →
  `setup-node-pair` (phone).
- **Layout classes:** phone · tablet. **Draw first:** phone Night; phone Day.
- **Content (top to bottom):**
  1. Title "Connect to your Ostler"; line "Your Ostler lives in your car. This app talks to
     it directly."
  2. **Found on this network** (mDNS, live): ListRows `directions_car` with the name the
     owner advertises, its address and "Brain" or "Ostler Diagnostics". Empty: "No Ostler
     on this Wi-Fi" with a spinner row "Looking…".
  3. ListRow `qr_code_scanner` **Scan the car screen** (opens the camera for the QR on
     `setup-welcome` or Settings → Network).
  4. ListRow `bluetooth` **Set up an Ostler Diagnostics node** "A node with no Brain:
     the app becomes its screen".
  5. ListRow `edit` **Enter an address**.
  6. Footer: "No account with us needed. Ostler works with no internet."
- **States:** loading: "Looking…" row. Error: Local network permission denied → Card `warn`
  "Allow Local network to find your Ostler" + **Open Settings**. Offline (no Wi-Fi): only
  rows 3–5. Moving: phone, open.
- **Safety and driving rules:** phone rules only; nothing here touches the car.
- **Components:** ListRow, Button, Card, QR scanner frame (new component).
- **Spec refs:** [App model §7.1][am-7.1] · [ADR-0032 §11][adr-32] · [Accounts §4 (nearby
  devices)][acc-4] · [ADR-0039 §7][adr-39].
- **Open questions:** none.

### setup-app-permissions — Companion app: what the app may use  [Proposed]
- **Owner:** os
- **Why the app needs it:** the app's native features (Bluetooth to the node, local
  network, notifications, location) each need an OS prompt; app stores expect the reason
  first, and each refusal must leave the rest working.
- **Purpose:** explain each native permission before the OS asks.
- **Opens from → goes to:** `setup-app-connect` → here → the next step. Later: Settings →
  **App permissions**.
- **Layout classes:** phone · tablet. **Draw first:** phone Night; phone Day.
- **Content (top to bottom):** one Card per permission, each with icon, name, one reason
  and **Allow** (primary) / **Not now** (ghost), then a status Chip "Allowed" or "Off":
  1. `bluetooth` **Bluetooth** "To reach an Ostler Diagnostics node, and adapters later."
  2. `wifi` **Local network** "To find your Ostler on the car's Wi-Fi."
  3. `notifications` **Notifications** "Alarm alerts and faults. Never message text while
     you drive."
  4. `location_on` **Location** "Your trips, kept on your devices unless you share them."
     Second line: "Background location is separate. Ask me later."
  5. Button **Continue**.
- **States:** denied → the Card reads "Off · Turn on in Settings" with **Open Settings**;
  the features that need it show "Needs Bluetooth" where they appear. Offline: works.
- **Safety and driving rules:** none beyond phone rules.
- **Components:** Card, Button, Chip (status).
- **Spec refs:** [App model §7.1 item 3][am-7.1] · [App model §14.3][am-14] ·
  [ADR-0009 (location stays on the device)][adr-9].
- **Open questions:** should location be asked here or only when the Trips app first records?

### accounts-s1 — First run (owner creation)  [Existing]
- **Owner:** os
- **Onboarding additions only** (the screen is specified in [Accounts §14.7 S1][acc-14.7]).
- **Opens from → goes to:** `setup-prefs` → S1 → `setup-vehicle-add` (S1's optional "Name
  this car" and "Invite someone" become `setup-vehicle-name` and `setup-people`). On
  Ostler Diagnostics alone S1 is the same screen inside `setup-node-pair` (phone).
- **Content order in the wizard:** step header "Step 2 of 9 · You"; Setup code field
  (CodeInput, new component: 8 boxes, numeric keypad); "Your name"; **Add a passkey**
  (primary when this origin can hold one) or **Use a password** (12+ characters, a strength
  line); recovery line "Lost access? Run `ostler auth reset-owner` on the Brain's console."
  No email field anywhere.
- **States:** wrong or expired code → inline `alarm` line under the code "That code has
  expired. Get a new one on the car screen." Upgrade path: an existing admin password skips
  the code and shows the banner "Add a passkey or rename your account" ([Accounts §14.9][acc-14.9]).
- **Safety:** text entry Parked only on a driver-facing display; draw the hu7 frame with the
  on-screen keyboard on the passenger side.
- **Spec refs:** [Accounts §14.7][acc-14.7] · [Accounts §2.1][acc-2.1] · [Accounts §2.2][acc-2.2].

### accounts-s2 — Sign in  [Existing]
- **Owner:** os
- **Onboarding additions only:** reached from F2, F4 and `setup-trust` once an owner
  exists. Above the form: the Ostler's advertised name and "Trusted" Chip. **Sign in with a
  code** shows a code for another screen to approve on `setup-device-code` (RFC 8628).
  "This account works only in the car" for a local-only user on a remote path.
- **Spec refs:** [Accounts §14.7 S2][acc-14.7] · [Accounts §2.4][acc-2.4].

### setup-invite-accept — Join this Ostler  [New]
- **Owner:** os
- **Purpose:** turn a **person invite** into a local user on this device (a family driver,
  a mechanic at the car) ([Accounts §5.1][acc-5.1]).
- **Opens from → goes to:** an invite link or QR (`https://<device-name>/invite#…`) the
  owner made on `setup-people` or `accounts-s7`; → `setup-trust` first if needed → the home pages.
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; phone Day.
- **Content (top to bottom):**
  1. Title "Join the Ostler in *Discovery 2 Td5*" (the car's nickname); "Invited by" and
     the inviter's name; role Chip "Driver" (or "Mechanic · 24 h", "Viewer").
  2. What the role can do, in words, from [Accounts §3.1][acc-3.1]: for Driver "Read, Comfort,
     Security, Maintenance. Mark, notes, start and stop logs, clear codes." Mechanic adds
     "Ends in 24 h".
  3. Connection check: `verified_user` "Connection verified" in `ok` (the invite's pinned
     certificate fingerprint matched).
  4. "Your name"; **Add a passkey** or **Use a password**.
  5. Expiry line "Invite expires in 47 h"; Button **Join** (primary), **Not now** (ghost).
- **States:** expired, used or revoked → Card `warn` "This invite can't be used. Ask the
  owner for a new one." Fingerprint mismatch → Card `alarm` "Stop. This is not the Ostler
  that invited you." and no form. Offline (not on the car's network): "Connect to the car's
  Wi-Fi to join" (invites redeem over LAN, Tailscale or the relay, [Accounts §5.4][acc-5.4]).
- **Safety and driving rules:** phone rules; a Mechanic role is always time-boxed.
- **Components:** Card, Chip (role, status), ListRow, Button, CodeInput (new).
- **Spec refs:** [Accounts §5.1][acc-5.1] · [Accounts §5.2][acc-5.2] · [Accounts §3.1][acc-3.1].
- **Open questions:** none.

### setup-device-code — Approve a device code  [New]
- **Owner:** os
- **Purpose:** link a TV, second screen, script or tool by typing the short code it shows
  (OAuth device grant, RFC 8628), choosing exactly what it may do.
- **Opens from → goes to:** Settings → Network → **Link a device with a code**; `accounts-s6` →
  **Link with a code**. Approve → `accounts-s6` (the new token listed). The waiting side is
  `accounts-s2` "Sign in with a code".
- **Layout classes:** phone · tablet · desktop. **Draw first:** phone Night; desktop Night.
- **Content (top to bottom):**
  1. Title "Link a device"; CodeInput (new component) for the code as shown on the other
     screen (for example "WXYZ-1234"), Button **Next**.
  2. After a match: who asks: the client's name as it reported it, "Asked 1 min ago", the
     address it asked from.
  3. **What it may do** (defaults narrow, [Accounts §2.4][acc-2.4]): Vehicles (Segmented
     "This car · All"); Categories (Chips, "Read" on by default); Highest tier (Segmented
     "0 · 1", 0 selected); Data classes (Chips from the registry: `live`, `faults`, `trips`,
     `location`, `notes`; none on by default but `live`); Admin (off). Line: "Never more than
     your own role. It can never approve a car action."
  4. Expiry: Segmented "30 days · 90 days · 1 year" (90 selected).
  5. Buttons **Approve** (primary), **Deny** (ghost).
- **States:** wrong code → inline "No device is waiting with that code"; expired → "That
  code has expired. Get a new one on the other screen." Approved → `check_circle` "Linked"
  and the token row. Remote path: Admin and every category above Read are greyed, "Local
  links only".
- **Safety and driving rules:** Parked only on a head unit (text entry); MCP and AI clients
  use the same tokens, Read only unless widened, and never approve anything
  ([Accounts §2.4][acc-2.4]).
- **Components:** CodeInput (new), Segmented, Chip (choice), Card, Button.
- **Spec refs:** [Accounts §2.4][acc-2.4] · [Accounts §14.7 S2, S6][acc-14.7] ·
  [Community hub §4 (hub linking uses the same grant)][hub-4].
- **Open questions:** linking a device to the Ostler Community hub shows the hub's code on
  the head unit; that page belongs to the Community files, not here.

[acc-2.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#21-bootstrap
[acc-2.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#22-passkeys-first-passwords-always
[acc-2.3]: ../../../../specs/2026-10-06-accounts-sharing-design.md#23-sessions
[acc-2.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#24-tokens
[acc-3.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#31-roles
[acc-4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#4-multi-vehicle-garage
[acc-5.1]: ../../../../specs/2026-10-06-accounts-sharing-design.md#51-two-kinds-of-invite
[acc-5.2]: ../../../../specs/2026-10-06-accounts-sharing-design.md#52-invite-payload
[acc-5.4]: ../../../../specs/2026-10-06-accounts-sharing-design.md#54-transports
[acc-14.7]: ../../../../specs/2026-10-06-accounts-sharing-design.md#147-shell-screens-gap-list-and-short-specs
[acc-14.8]: ../../../../specs/2026-10-06-accounts-sharing-design.md#148-social-login
[acc-14.9]: ../../../../specs/2026-10-06-accounts-sharing-design.md#149-basic-auth-migration-replaces-the-overlap-line-in-21
[am-7.1]: ../../../../specs/2026-10-06-app-model-design.md#71-amendment-2026-10-06-the-phone-build
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[hub-4]: ../../../../specs/2026-10-07-community-hub-design.md#4-hub-accounts-and-device-linking
[adr-9]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[adr-21]: ../../../../decisions/adr-0021-local-https-on-the-device.md#decision
[adr-32]: ../../../../decisions/adr-0032-one-node-optional-brain.md#decision
[adr-39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
