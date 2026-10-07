---
title: "Designer brief 80-j — Camera app: first-run setup (cameras, reverse trigger, guidelines), settings and widgets"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, references/research/canbus_headunit.md]
summary: >
  The Camera app's first-run setup and settings (app:camera). Setup checks that cameras exist
  and have roles (devices are added in the hardware pages), chooses the reverse trigger (a
  node input on the reverse lamp wire, the head unit's own reverse wire, or manual only) and
  calibrates static guidelines against marks on the ground behind the Discovery 2. Settings
  cover mirror and crop, guideline style, the close delay, the low-speed limit display,
  recording and storage. The end lists the widgets Camera adds to the widget picker gallery
  (camera live, rear-camera button, dashcam status) with their setup options.
---

# 80-j — Camera setup, settings and widgets

Proposed for the reason in [80-i](80-hu-i-camera.md). Setup is Parked only. The ground marks
step needs the car parked with space behind it and a tape measure.

## Setup flow (first run)

| Step | Screen | What the user does | What can fail, and the recovery |
|---|---|---|---|
| 1 | `camera-setup` | Checks the cameras and their roles | No camera: "Add a camera" (hardware page by name) |
| 2 | `camera-setup-trigger` | Picks how reverse opens the camera, then tests it | Trigger not seen: wiring hint, "Manual only" |
| 3 | `camera-setup-guidelines` | Lines up guidelines with marks on the ground | Image too dark: "Try in daylight", skip |
| 4 | `camera-home` | Lands on Cameras | — |

### camera-setup — Setup 1: cameras and roles  [Proposed]
- **Why the app needs it:** the app's rules depend on each camera's role.
- **Purpose:** confirm which cameras the app will use and for what.
- **Owner:** app:camera
- **Opens from → goes to:** first open of Camera; `camera-settings` → Cameras. Goes to
  `hw-camera-add` and `hw-camera` (by name), `camera-setup-trigger`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):** 1. StepProgress "1 of 3 · Cameras". 2. ListRows: still frame,
  name, role chip ("Rear · Reverse", "Front", "Underbody"), and **Change role** (opens the
  device page). 3. **Add a camera**. 4. A plain note per role: "Reverse: an aid when
  reversing", "Front and underbody: below 10 km/h", "Cabin and dash: parked only".
  5. **Next**.
- **States:** none: empty Card with **Add a camera**; no Reverse role: step 2 is skipped
  with a note. Brain asleep: "Needs the Brain". Moving: locked view.
- **Safety and driving rules:** Parked only.
- **Components:** StepProgress (new component), ListRow, Chip, Button, Card.
- **Spec refs:** [UI §6][ui-6].
- **Open questions:** none.

### camera-setup-trigger — Setup 2: reverse trigger  [Proposed]
- **Why the app needs it:** the camera must open on reverse; the D2 has no fast reverse
  signal on the K-line, so the owner must pick a wired source.
- **Purpose:** choose and test what opens the reverse camera.
- **Owner:** app:camera
- **Opens from → goes to:** `camera-setup`; `camera-settings` → Reverse trigger. Goes to
  `camera-setup-guidelines`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with the test waiting; hu7 Night test passed.
- **Content (top to bottom):**
  1. StepProgress "2 of 3 · Reverse".
  2. Choice list (ListRows with one line each):
     - **Node input · reverse lamp wire** (recommended) — "Fast. Needs one wire to the
       node's input."
     - **Head unit's reverse wire** — "Your head unit switches to its own camera input."
     - **Vehicle pack signal** — "Not available on Discovery 2 (no fast reverse signal)."
       greyed.
     - **Manual only** — "Open the rear camera with a button."
  3. **Test:** "Put the car in reverse with the engine off and the handbrake on" →
     "Reverse seen · 120 ms" in `ok`, or "Not seen yet".
  4. **Close delay** Segmented: 0 · 3 · 5 · 10 s after reverse ends.
  5. **Next**.
- **States:** input not wired: "No signal on input 2 · check the wire" with a link to the
  hardware install guide (20-hardware-b by name); manual only: test step hidden. Moving:
  locked view.
- **Safety and driving rules:** Parked only; read only; the test never moves the car and
  says so. Pre-emption still waits for the fast path approval ([UI §6][ui-6]).
- **Components:** StepProgress (new component), ListRow, Segmented, Chip (status), Button.
- **Spec refs:** [UI §6][ui-6] · [head-unit research B4][ch-b4].
- **Open questions:** does the node's opto input count as the "fast path" that lets reverse
  pre-empt the screen? Needs the owner's call and a latency test.

### camera-setup-guidelines — Setup 3: static guidelines  [Proposed]
- **Why the app needs it:** guidelines are only useful if they match this car and this
  camera's mounting.
- **Purpose:** line up the distance bands and width lines with real marks on the ground.
- **Owner:** app:camera
- **Opens from → goes to:** `camera-setup-trigger`; `camera-settings` → Guidelines. Goes to
  `camera-home`.
- **Layout classes:** tablet · hu7 · hu9 · huwide · phone. **Draw first:** hu9 Night Parked
  with handles.
- **Content (top to bottom):**
  1. StepProgress "3 of 3 · Guidelines".
  2. Instruction Card: "Put marks on the ground 0.5 m, 1 m and 2 m behind the bumper,
     in line with the sides of the car."
  3. Live image with the GuidelineOverlay (new component) in edit mode: drag handles on each
     band's ends; a width Slider; Mirror Toggle.
  4. **Style** Segmented: Lines · Bands · Off. **Dynamic lines** row greyed: "Needs a
     steering-angle signal (not on the Discovery 2)".
  5. **Reset**, **Save**.
- **States:** image too dark: "Too dark to line up · try in daylight" with **Skip** (default
  lines used). Moving: locked view.
- **Safety and driving rules:** Parked only; the "Assist only" chip cannot be turned off.
- **Components:** StepProgress (new component), GuidelineOverlay (new component), Slider
  (new component), Toggle (new component), Segmented, Button.
- **Spec refs:** [UI §6][ui-6].
- **Open questions:** none.

### camera-settings — Camera settings  [Proposed]
- **Why the app needs it:** the app's own choices need one home outside system Settings.
- **Purpose:** the Camera app's options.
- **Owner:** app:camera
- **Opens from → goes to:** `camera-home` → Settings; App info → Settings. Goes to the setup
  steps, Security → Clips (by name).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. **Cameras** (as `camera-setup`). 2. **Reverse:** trigger,
  close delay, chime on reverse Toggle, guidelines style. 3. **Low-speed cameras:** "Hide
  above 10 km/h" shown as a fixed line, not a control. 4. **Recording:** Toggle per camera,
  loop length Segmented (1 · 4 · 12 h), "Save clip also marks the trip" Toggle, storage
  limit. 5. **Parking sensors** source row: "None found" or an add-on device.
- **States:** not owner: recording rows read only. Moving: locked view.
- **Safety and driving rules:** Park to edit; no setting raises the 10 km/h limit, adds a
  second live stream while Moving or allows playback while Moving.
- **Components:** ListRow, Toggle (new component), Segmented, Button.
- **Spec refs:** [UI §6][ui-6] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

## Camera widgets (in the widget picker gallery)

- **Camera live** (the approved "camera live" add-on widget, [Drive modes §9][dm-9]) — one
  camera's live image. Sizes: medium, wide, hero (Parked home pages). Setup options: which
  camera (driving cameras only on Drive home pages), mirror, show guidelines. **Moving:**
  `camera_live` within the camera's role rule; Cabin and Dash cameras are refused on Drive
  home pages.
- **Rear camera button** — one button that opens `camera-reverse`. Size: small. Setup
  options: icon and name only. **Moving:** allowed below 10 km/h.
- **Dashcam status** — "REC" state and **Save clip**. Size: small. Setup options: which
  cameras to show. **Moving:** allowed (Save clip is like Mark).
- **Shortcuts:** "Camera" app shortcut; Drive menu rows "Rear camera" and "Save clip".

[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[ch-b4]: ../../../research/canbus_headunit.md#b4-steering-wheel-reverse-cameras-amplifier
