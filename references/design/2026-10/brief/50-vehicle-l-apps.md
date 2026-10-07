---
title: "Designer brief: vehicle and diagnostics (L) — the four apps: setup flows, settings pages and widgets"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-05-replay-notes-capture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md]
summary: >
  Twelfth file of the vehicle and diagnostics brief, written for the owner's new direction
  of 2026-10-07: Ostler is an Android-style OS and Diagnostics, Trips, Maintenance and
  Decode lab are separate apps, each with its own drawer icon. For each app it gives the
  first-run setup flow, the app's own settings page and the widgets it contributes to the
  launcher's home pages (name, what it shows, setup options). Examples: fault count, live
  gauge from a signal, last trip, service due. Vehicle packs are integrations set up in the
  app framework pages. The setup and settings pages are New: the approved app UI model
  spec covers setup flows and options flows.
---

# Vehicle and diagnostics brief (L): apps, setup, settings and widgets

**Spec:** the owner's direction of 2026-10-07 makes every feature an app with its own setup
flow and settings page; the approved app UI model spec covers both: a setup flow drawn by
the OS from the app's schemas ([app UI model §4][ua-4]) and an options flow or the app's
own settings page ([app UI model §5][ua-5]). The system "App info" page per app, the widget picker and the widget setup
page belong to the app framework and launcher areas (`90-appframe-*`, `45-launcher-*`); this
file only lists what each app puts into them. **Vehicle packs are integrations**: the D2 pack
(`lr_d2`) is installed and set up on its integration setup page in the app framework area;
these apps read it and link there by name. Safety stays with the OS: confirm sheets, the
fault telltale, Moving templates and Park to edit are never an app's to change
([Drive modes §8.1][dm-8.1]).

### diagnose-app-setup — Diagnostics: first-run setup  [New]
- **Purpose:** get from "installed" to a first honest module list.
- **Owner:** app:diagnostics
- **Opens from → goes to:** first open from the app drawer; App info → "Run setup again" → diagnose-systems.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night.
- **Content (top to bottom):** 1. Step "1 of 3 · Vehicle": active vehicle from the Garage; "Vehicle pack: Land Rover Discovery 2 (lr_d2) · set up" or **Set up the vehicle pack** (opens the pack's integration setup page). 2. Step "2 of 3 · Link": the Connection ladder result ("ECU session: TD5") or **Use an adapter** (adapter-connect, only when no node is fitted). 3. Step "3 of 3 · First scan": **Scan all** with per-module progress, or **Skip**. 4. **Done** → diagnose-systems.
- **States:** no pack match: "Unknown vehicle — help decode it" path. Not connected: setup can finish with "Scan later". Moving: locked (Parked only).
- **Safety and driving rules:** the scan is read only; nothing writes to the car.
- **Components:** StepProgress (new component), Card, Button.
- **Spec refs:** [UI §4.4][ui-4.4] · [UI §4.5][ui-4.5] · [App model §14][am-14] · [app UI model §4][ua-4].

### diagnose-app-settings — Diagnostics: settings  [New]
- **Purpose:** the Diagnostics app's options.
- **Owner:** app:diagnostics
- **Opens from → goes to:** Diagnostics overflow menu; App info → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. **Area names**: "Use the pack's words (Inputs, Outputs, Utilities)" or the plain words (Live, Tests, Procedures). 2. **Fault watch by default** toggle. 3. **Scan report**: export format (HTML, JSON), "Mark scans before a repair". 4. **Hidden modules** (marked Not fitted) with Show. 5. **Show candidate values** toggle (on; candidate is always marked). 6. Links by name: the vehicle pack's integration page; Adapter actions (owner only, adapter-soft-gate).
- **States:** not owner: owner-only rows hidden. Moving: locked.
- **Safety and driving rules:** no setting can skip a confirm, the clear-codes snapshot or a Parked rule.
- **Components:** ListRow, Toggle (new component), Segmented.
- **Spec refs:** [UI §3.4][ui-3.4] · [UI §4.3][ui-4.3] · [app UI model §5][ua-5].

**Diagnostics widgets** (read only; each has a widget setup page in the launcher's style):
- **Fault count** — worst status and count for the vehicle or one module ("2 faults · SLABS"); options: all modules or one, show Logged or Current only. Its tap opens diagnose-faults. (The OS fault telltale is separate and cannot be removed.)
- **Live gauge** — one signal as a calm Gauge or number with unit (e.g. Coolant, Turbo pressure); options: signal (from the pack's list, proven or candidate marked), style (gauge, number, sparkline), normal band override. Allowed on a Drive home page only through the `tiles` template while Moving.
- **Module status** — the module list chips in a 2×2 or 4×1 grid; options: which modules.
- **Vehicle view** (Proposed with D) — the SLABS silhouette with ride heights; options: module.
- **Scan all** shortcut — one button that runs a read-only scan (Parked).

### trips-app-setup — Trips: first-run setup  [New]
- **Purpose:** set up recording and privacy once.
- **Owner:** app:trips
- **Opens from → goes to:** first open; App info → Run setup again → trips-list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. "Trips records automatically while the car is connected. Nothing leaves this device unless you share it." 2. **Sources**: GPS, phone audio, accelerometer rate (as trips-recording-options). 3. **Units** (km/h or mph speed bands). 4. **Private places**: "Add Home to hide it in every share" → Places. 5. **Done**.
- **States:** no GPS: "Trips will have no maps until a GPS is connected". Moving: locked.
- **Safety and driving rules:** location stays on the device unless shared (ADR-0009).
- **Components:** StepProgress (new component), ListRow, Toggle (new component), Button.
- **Spec refs:** [Replay §3][rn-3] · [UI §13.4][ui-13.4] · [app UI model §4][ua-4].

### trips-app-settings — Trips: settings  [New]
- **Purpose:** the Trips app's options.
- **Owner:** app:trips
- **Opens from → goes to:** Trips overflow menu; App info → Settings → trips-recording-options, Places, trips-export-all.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. **Recording & flags** → trips-recording-options. 2. **Place names**: online refinement on or off ("© OpenStreetMap contributors · GeoNames"). 3. **Speed bands** unit. 4. **Sharing defaults**: default level L0, default expiry. 5. **Export all** → trips-export-all. 6. **Storage**: space used and the oldest-first rotation note.
- **States:** Brain asleep: "Needs the Brain" for storage figures. Moving: locked.
- **Safety and driving rules:** no setting pauses recording (recording is always on while connected).
- **Components:** ListRow, Toggle (new component), Segmented.
- **Spec refs:** [UI §12.2][ui-12.2] · [Logs at scale §1][ls-1] · [app UI model §5][ua-5].

**Trips widgets:**
- **Last trip** — mini dark map, place, distance, duration; options: vehicle, show max speed (off by default). Hidden while Moving on head units.
- **Recording** — "Recording · 14 min" or "Paused — no connection", with Mark; options: none. Mark stays usable at any speed through the OS Mark chip.
- **This month** — distance and trips this month (neutral facts, no score); options: period.
- **Rewind** shortcut — opens the newest trip at its end.

### maint-app-setup — Maintenance: first-run setup  [New]
- **Purpose:** set up per-vehicle tracking.
- **Owner:** app:maintenance
- **Opens from → goes to:** first open; App info → Run setup again → maint-home.
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Vehicle (from the Garage). 2. **Odometer now** (the Td5 reports none, so this anchors the estimate) → maint-odometer. 3. Currency and economy unit. 4. **Schedule**: the pack's templates or "No Td5 schedule yet · add your own" → maint-templates. 5. **Import** existing records (optional) → maint-import-upload. 6. **Done**.
- **States:** skipped odometer: distances read "—" until a reading exists. Moving: locked.
- **Safety and driving rules:** typing Parked only.
- **Components:** StepProgress (new component), TextField (new component), Button.
- **Spec refs:** [Maintenance §4][mg-4] · [Maintenance §6][mg-6] · [Maintenance §9][mg-9] · [app UI model §4][ua-4].

### maint-app-settings — Maintenance: settings  [New]
- **Purpose:** the Maintenance app's options.
- **Owner:** app:maintenance
- **Opens from → goes to:** Maintenance overflow; App info → Settings → maint-import-upload, maint-export, maint-buyer-share, maint-templates.
- **Layout classes:** phone · tablet · desktop · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. **Urgency leads**: urgent 30 d / 1 500 km / 20 h, very urgent 7 d / 500 km / 5 h (editable). 2. **Reminders**: push, node notifier (ntfy, Telegram, SMS), in-car card at trip start or end. 3. **Clean drives to close a fault task**: 3. 4. **Import**, **Export bundle**, **Share with a buyer**. 5. **Templates**.
- **States:** Moving: locked.
- **Safety and driving rules:** no setting allows a mid-drive alert ([Maintenance §8][mg-8]).
- **Components:** ListRow, TextField (new component), Toggle (new component).
- **Spec refs:** [Maintenance §3][mg-3] · [Maintenance §8][mg-8] · [app UI model §5][ua-5].

**Maintenance widgets:**
- **Service due** — next due task with band pill and remainder ("Oil and filter · in 300 km est."); options: vehicle, how many tasks (1–3).
- **Cost this month** — total and donut; options: vehicle, categories.
- **Documents expiring** — next document expiry; options: kinds.
- **Add fill-up** shortcut — opens maint-add-record on Fuel (Parked).

### decode-app-setup — Decode lab: first-run setup  [New]
- **Purpose:** prepare the lab for a first capture.
- **Owner:** app:decode-lab
- **Opens from → goes to:** first open (service mode on) → decode-lab.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. "Decode lab is read only. It never writes to the car." 2. **Sniff source**: the node's tap, a sniffer, or "None yet" (Sniff will say "No sniff source"). 3. **Contribution consent** default: off; the CC BY-SA 4.0 sentence. 4. **Community account** link (if the Community app is installed). 5. **Done**.
- **States:** service mode off: the app is hidden. Moving: refused.
- **Safety and driving rules:** service mode only; refused while Moving ([UI §8.4][ui-8.4]).
- **Components:** StepProgress (new component), ListRow, Checkbox (new component), Button.
- **Spec refs:** [UI §8.4][ui-8.4] · [UI §13.3][ui-13.3] · [app UI model §4][ua-4].

### decode-app-settings — Decode lab: settings  [New]
- **Purpose:** the Decode lab app's options.
- **Owner:** app:decode-lab
- **Opens from → goes to:** Decode lab overflow; App info → Settings.
- **Layout classes:** tablet · desktop · hu9 · huwide · phone. **Draw first:** desktop Night.
- **Content (top to bottom):** 1. **Credit name** for contributions. 2. **Contribution consent** default. 3. **Keep identity replies in raw recordings on this device** (off; ADR-0036 opt-in for security decoding work, never shared). 4. **Sniff source**. 5. Read-only list of the services a sweep may send.
- **States:** Moving: refused.
- **Safety and driving rules:** no option enables a write service.
- **Components:** ListRow, Toggle (new component), TextField (new component).
- **Spec refs:** [UI §8.1][ui-8.1] · [UI §8.3][ui-8.3] · [app UI model §5][ua-5].

**Decode lab widgets:** none on Drive home pages; one **Decode progress** widget for Parked home pages (coverage per module, e.g. "TD5 · 31 of 45 proven"), options: module.

[ui-3.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#34-five-destinations
[ui-4.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#43-scan-all-and-its-honest-states
[ui-4.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#44-identification-and-fallbacks
[ui-4.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#45-the-connection-ladder
[ui-8.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#81-stages
[ui-8.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#83-data-evidence-fixtures-and-scrub
[ui-8.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#84-decode-mode-in-the-ui
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[ui-13.3]: ../../../../specs/2026-10-06-ui-architecture-design.md#133-ask-for-help-decoding-decode-lab-changes-84
[ui-13.4]: ../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[mg-3]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#3-reminder-engine
[mg-4]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#4-odometer-and-engine-hours-ladder
[mg-6]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#6-faults-and-manufacturer-schedules
[mg-8]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#8-reminder-delivery
[mg-9]: ../../../../specs/2026-10-07-maintenance-garage-addon-design.md#9-import-and-export
[rn-3]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#3-audio-and-accelerometer-capture
[ls-1]: ../../../../specs/2026-10-06-logs-at-scale-design.md#1-record-only-while-connected
[ua-4]: ../../../../specs/2026-10-07-app-ui-model-design.md#4-the-setup-flow
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
