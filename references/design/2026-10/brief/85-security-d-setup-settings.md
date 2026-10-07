---
title: "Designer brief 85-d — Security app: setup flow, notification channels and settings"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-02-gps-tracker-alarm-design.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0039-product-family-diagnostics-guardian-hub.md, decisions/adr-0040-power-states-and-wake.md]
summary: >
  Fourth Security app file (app:security). The app's first-run setup flow as a step list:
  a welcome step, then the hardware pages already drawn in 20-hardware-f (alarm setup, walk
  test, tracker), then the notification channels and a done step. The channels page lists
  where alarm alerts go (paired phone, SMS from the Guardian, the owner's notify address,
  Home Assistant, a mesh radio) with tests and results, and states that alarm alerts are
  critical and can never be muted. The app's settings page holds arming defaults, sensors,
  tow and transport, retention and links to App info.
---

# 85-d — Security app: setup, channels and settings

Main page: [85-a](85-security-a-main.md). Every step is drawn in the OS's setup flow frame
(90-appframe files); this file gives only Security's content.

## Setup flow (first open, or "Run setup again")

| # | Screen | What the user does | What can fail → recovery |
|---|---|---|---|
| 1 | `security-setup-welcome` | reads what Security does, taps **Start** | no node or Guardian paired → **Pair a device** (OS pairing), or **Set up later** |
| 2 | `hw-alarm-setup` ([20-hardware-f](20-hardware-f-security-mesh-service.md)) | checks the sensor list, turns sensors on or off, picks how arming works | a sensor shows No signal → its help, or turn it off and go on |
| 3 | `hw-alarm-walk-test` ([20-hardware-f](20-hardware-f-security-mesh-service.md)) | walks round the car and triggers each sensor | "Not heard" → check the tap; **Skip test** (shown as "Not tested" on done) |
| 4 | `hw-tracker` ([20-hardware-f](20-hardware-f-security-mesh-service.md)) | picks the check-in interval and sees who can see the location | no fix yet → go on; the fix comes later |
| 5 | `security-channels` | turns on where alerts go and sends a test | test not delivered → fix or remove the channel; at least one must work to finish |
| 6 | `security-setup-done` | sees the summary, taps **Arm now** or **Done** | — |

Parked only on driver-facing displays; it runs best on the phone, at the car. Cancel at any
step leaves the app with a "Set-up not finished" Card on `security`.

### security-setup-welcome — Set up Security  [New]
- **Owner:** app:security
- **Purpose:** say what Security will and won't do, then start.
- **Opens from → goes to:** first open of Security; first run of the Guardian flavour
  (`setup-apps` in 10-onboarding-d); App info → Run setup again. Goes to `hw-alarm-setup`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; phone Day; hu7 Night.
- **Content (top to bottom):**
  1. Wizard frame header "1 of 6 · Security".
  2. Title "Guard your Discovery"; three rows with icons: `shield` "Alerts you if the car is
     opened, moved, towed or tampered with", `location_on` "Shows where it is parked. Only
     you can see it unless you share it.", `notifications_active` "Alerts reach your phone
     even with no internet, by SMS from the Guardian."
  3. Honest Card: "Ostler doesn't sound a siren, lock the car or stop the engine. The car's
     own alarm keeps working as before."
  4. **Found devices**: "Ostler Guardian · paired" or "Ostler Diagnostics · basic alarm and
     GPS"; none: **Pair a device**.
  5. Buttons **Set up later** and **Start**.
- **States:** no device (Start disabled, reason shown); loading; Moving: locked view.
- **Safety and driving rules:** setup is an owner operation, Parked ([UI §12.1][ui-121]).
- **Components:** Wizard frame, ListRow, Card, Button.
- **Spec refs:** [ADR-0033 §7][a33-7] · [ADR-0039 §1][a39] (Guardian) · [UI §6][ui-6] · [app UI model §4][ua-4].
- **Open questions:** none.

### security-setup-done — Security is ready  [New]
- **Owner:** app:security
- **Purpose:** summary and first arm.
- **Opens from → goes to:** step 5 → here. Goes to `security` or `security-arm-sheet`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night.
- **Content (top to bottom):**
  1. Tick and "Security is ready".
  2. Summary rows: "Sensors: Tilt, Shock, GPS movement, Tamper · tested 4 of 4", "Not fitted
     on this car yet: Doors, Bonnet, Car's alarm siren", "Alerts: phone, SMS · tested",
     "Tracker: Guardian GNSS · check-in about every 10 min".
  3. "Added to your home page: Alarm status" (the OS widget) with **Add more widgets**
     (opens the widget picker filtered to Security).
  4. Buttons **Done** and **Arm now** (primary).
- **States:** a step skipped shows `warn` rows ("Walk test skipped"); Moving: locked.
- **Safety and driving rules:** as the arm sheet when **Arm now** is chosen.
- **Components:** Wizard frame, ListRow, Chip (status), Button.
- **Spec refs:** [Drive modes §8.1][dm-81] (the alarm status widget is a safety item) · [app UI model §4][ua-4].
- **Open questions:** none.

### security-channels — Where alerts go  [New]
- **Owner:** app:security
- **Purpose:** choose and test the paths alarm alerts take, none of which need the Brain.
- **Opens from → goes to:** setup step 5; `security` → Alerts line; `security-settings`;
  `hw-alarm-setup` → Alerts reach you. Back. Links to Settings → Notifications
  (`settings-notifications`, 30-settings-b) for the phone's other alerts.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; phone Day; hu7 Night.
- **Content (top to bottom):**
  1. **Critical** Card (`alarm-bg`, no controls): "Alarm and tamper alerts are critical.
     They sound through quiet hours and can't be turned off. They work with the Brain off and
     no internet."
  2. **Channels** ListRows, each with a Toggle, its result of the last test, and **Test**:
     - "Paired phones · local Wi-Fi or Bluetooth" (per phone: "Owner's phone · last
       delivered 02:16");
     - "SMS from the Guardian · +44 7… (2 numbers)" with **Edit numbers** (Parked);
     - "Push over Ostler Cloud relay" (only if the relay is set up);
     - "Your notify address · https://…" (the owner's own endpoint);
     - "Home Assistant · alerts and state only" (if linked);
     - "Mesh radio · alarm state on change" (if a radio is fitted; [ADR-0038][a38]).
  3. **What to send**: rows with Toggles for non-critical kinds: Geofence, Battery low, Arm
     and disarm receipts, Shock (single knock). Alarm, Tamper, Movement and Tow are locked on.
  4. **Remote disarm notice**: "When anyone disarms remotely, you are always told." (locked)
- **States:** no channel works: banner "No alert path works · fix one before arming";
  test sent ("Test sent 14:02 · marked as a test"), delivered, failed with reason ("SMS: no
  signal", "Phone not reachable"); no Guardian: SMS row absent ("Needs a SIM: Guardian or
  the 4G module"); Moving: locked.
- **Safety and driving rules:** alarm alerts can't be removed or muted ([Drive modes §8.1
  R3][dm-81]); the alarm path never depends on the Brain or the internet
  ([ADR-0033 §7][a33-7]); a test never reaches a share's audience; phone numbers are typed
  Parked only.
- **Components:** Card (alarm tone), ListRow, Toggle, Button, Text field, Inline notice.
- **Spec refs:** [ADR-0033 §7][a33-7] · [ADR-0040 §6][a40-6] (≤ 5 s local) ·
  [ADR-0038][a38].
- **Open questions:** must at least one channel pass a test before arming is allowed, or is
  the banner enough?

### security-settings — Security settings  [New]
- **Owner:** app:security
- **Purpose:** the app's own options.
- **Opens from → goes to:** `security` overflow → Settings; App info → Options (90-appframe
  files). Goes to `hw-alarm-setup`, `hw-tracker`, `security-channels`, `security-geofences`,
  `security-tow-mode`, Users (system Settings).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night; hu7 Night; hu7 Night-dim Moving (locked).
- **Content (top to bottom):**
  1. **Arming**: Exit delay Segmented 0 s · 30 s · 60 s; Entry delay 0 s · 15 s · 30 s; Toggle
     "Remind me to arm when I park and lock" (needs the fob tap); "Arming follows the car's
     alarm" (read-only line from `hw-alarm-setup`).
  2. **Sensors and thresholds** → `hw-alarm-setup`; **Walk test** → `hw-alarm-walk-test`.
  3. **Alerts** → `security-channels`.
  4. **Tracker** → `hw-tracker`; **Geofences** → `security-geofences`; **Tow and theft mode**
     → `security-tow-mode`.
  5. **Who can arm and disarm**: read-only list from roles ("Owner, Driver: arm and disarm ·
     Viewer: see state"), link "Change in Users" (system Settings); a fixed line "Disarm
     works only when parked" (item 59).
  6. **Remote**: line "Remote arm and disarm: allowed for people with Security · logged ·
     disarm asks for a fresh passkey" (item 60);
     "Remote control override: off · set only in the install configuration" (read-only).
  7. **Keep events**: 30 days · 90 days · 1 year; **Clear event history** (danger, typed
     confirm, Parked).
  8. **Arm and disarm log** → `security-events` filtered to Arm and disarm.
- **States:** armed (sensor and threshold changes read-only until disarmed, as
  `hw-alarm-setup`); Viewer (all read-only); offline (changes wait to sync); Moving: locked.
- **Safety and driving rules:** Park to change; the override is never settable here
  ([ADR-0033 §6][a33-6]); clearing history is an owner operation with undo for 7 days.
- **Components:** ListRow, Segmented, Toggle, Button (danger), Text field (typed confirm).
- **Spec refs:** [ADR-0033 §2][a33-2] · [ADR-0033 §6][a33-6] · [UI §3.4][ui-34] · [app UI model §5][ua-5].
- **Open questions:** "Remind me to arm" needs a decoded lock signal; on the D2 the fob tap is
  not identified yet, so the row may be absent at first.

[a33-2]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#2-roles-grant-categories
[a33-6]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#6-local-links-phone-approval-and-the-install-override
[a33-7]: ../../../../decisions/adr-0033-action-categories-and-approvals.md#7-alarm-paths
[a38]: ../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md#decision
[a39]: ../../../../decisions/adr-0039-product-family-diagnostics-guardian-hub.md#decision
[a40-6]: ../../../../decisions/adr-0040-power-states-and-wake.md#6-latency-budgets
[dm-81]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[ui-34]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-121]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ua-4]: ../../../../specs/2026-10-07-app-ui-model-design.md#4-the-setup-flow
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
