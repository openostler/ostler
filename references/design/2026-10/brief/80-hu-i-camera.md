---
title: "Designer brief 80-i — Camera app: cameras home, reverse camera, front and underbody, multi-camera, dashcam"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-platform-direction-design.md, references/research/canbus_headunit.md, references/research/driver_distraction_rules.md]
summary: >
  The Camera app's viewing pages (app:camera). The cameras home lists every camera with a
  still or live tile. The reverse camera opens on the reverse signal or a manual button and
  draws static guidelines and, where a sensor exists, the parking sensor overlay; on the
  Discovery 2 dynamic guidelines are not available (no steering-angle signal). Front and
  underbody views are for off-road use below 10 km/h. The multi-camera grid is Parked only.
  Dashcam shows recording state and clips, which live in Security → Clips. The `camera_live`
  template and its speed rules are approved; the app pages around them are New (the
  head-unit apps spec).
---

# 80-i — Camera app pages

Camera devices are added and given a role in the hardware brief (`hw-camera-add`,
`hw-camera` in 20-hardware-d); this app is where the driver **views** them. Cameras stream
through go2rtc on the Brain ([platform direction][pd]). **Approved rules** ([UI §6][ui-6],
[App model §4.4][am-4.4]): `camera_live` shows one stream; reverse pre-empts the screen only
once a fast path exists and is assist-only until then; front and underbody show live below
10 km/h; no playback unless Parked. The approved head-unit apps spec covers the
Camera app ([head-unit apps §6][hu-6]): the reverse view, its trigger, guidelines and other
views Parked only (multi-view and dashcam later), so these pages are New.

### camera-home — Cameras  [New]
- **Purpose:** list cameras and open one.
- **Owner:** app:camera
- **Opens from → goes to:** app drawer → Camera. Goes to `camera-reverse`,
  `camera-offroad`, `camera-multi`, `camera-dashcam`, `camera-settings`, `hw-camera` (by
  name, for device settings).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked with three cameras; hu7 Night-dim Moving.
- **Content (top to bottom):** 1. Camera Cards in a grid: still frame with age ("12 s ago")
  or live when Parked, name, role chip (Reverse, Front, Underbody, Cabin, Dash), status
  ("Recording", "Off"). 2. Buttons: `grid_view` "All cameras" (Parked), `videocam`
  "Dashcam", `settings` "Settings". 3. **Add a camera** → `hw-camera-add` (by name).
- **States:** no cameras: "No cameras yet · Add a camera". Brain asleep: "Needs the Brain"
  with **Wake**. Stream lost: grey still and the age. Moving: a `short_list` of driving
  cameras only (Reverse, Front, Underbody), each opening `camera_live` within its speed
  rule; Cabin and Dash are absent.
- **Safety and driving rules:** non-driving cameras are Parked only on driver-facing
  displays and never in Passenger view ([UI §12.1][ui-12.1]).
- **Components:** Card, Chip (status), Button, `short_list` template.
- **Spec refs:** [UI §6][ui-6] · [UI §12.1][ui-12.1] · [head-unit apps §6][hu-6].
- **Open questions:** none.

### camera-reverse — Reverse camera with guidelines  [New]
- **Purpose:** show the rear camera when reversing, with guidelines and parking distances.
- **Owner:** app:camera (view); os (`camera_live` template and pre-emption)
- **Opens from → goes to:** the reverse signal (see the trigger in `camera-setup-trigger`);
  a manual `videocam` "Rear camera" button (widget, Drive menu row or a wheel key). Closes
  when reverse ends plus a delay (default 5 s) or on Back; returns to where the driver was.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  reversing with static guidelines; hu7 Night-dim with "Parking sensors not available";
  huwide Night-dim (camera in the main area, strip still visible); hu5 Night.
- **Content (top to bottom):**
  1. Strip stays visible above (telltale and Security chips never covered).
  2. Live image, mirrored as set, full main area, no rounded corners on HU.
  3. **Guidelines (static):** three distance bands (0.5 m, 1 m, 2 m) in `alarm`, `warn`
     and `ok` line colours at 60 % opacity, plus the car's width lines; no animation.
  4. **Dynamic guidelines:** not drawn on the D2; a small caption "Dynamic lines need a
     steering-angle signal" in Parked frames only.
  5. **Parking sensor overlay** (only when a sensor source exists): four rear zones as arcs,
     each with distance "0.6 m" and a word; with none: nothing drawn.
  6. Corner chip "Assist only · check around you" (`info`), and **Back**.
- **States:** camera not ready (Brain booting, 15–20 s): "Rear camera starting…" then the
  image; the car's own mirrors are the fallback. Stream lost: "Rear camera lost" on `bg`,
  never a frozen frame. Moving forward above 10 km/h with the manual button: refused with
  the toast "Rear camera available below 10 km/h". Red telltale during reverse: the OS
  draws its `alert_card` at the top edge, not over the guidelines.
- **Safety and driving rules:** `camera_live`, one stream, no playback; pre-emption only
  once a fast reverse path exists, until then it opens when placed on a home page or by the
  button ([UI §6][ui-6]); a reverse camera is a driving camera under reg 109 (c)
  ([research §4.2][dd-4.2]); message cards wait until reverse ends ([UI §12.1][ui-12.1]).
- **Components:** `camera_live` template, GuidelineOverlay (new component), SensorArcs (new
  component), Chip (status), Button (Back).
- **Spec refs:** [UI §6][ui-6] · [App model §4.4][am-4.4] · [UI §12.1][ui-12.1] ·
  [head-unit research B4][ch-b4].
- **Open questions:** (1) **Decided ([head-unit apps §6][hu-6]):** the trigger is a pack
  signal or a 12 V reverse wire into a node or I/O-module input; on the D2 that is the
  reverse lamp wire, a first car check (item 65); where the head unit has its own camera
  input (setup B) that stays the fast path. Latency is measured on the bench. (2) Many D2s
  have a rear parking aid; its module is not on the pack today, so the overlay needs an
  add-on sensor device.

### camera-offroad — Front and underbody views  [New]
- **Purpose:** see the ground ahead and under the car on rough tracks.
- **Owner:** app:camera (view); os (`camera_live` template)
- **Opens from → goes to:** the Off-road (D2) Drive home page's camera cell; the camera
  widget; a Drive menu row "Front camera". Back to the Drive home page.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim
  Moving at 6 km/h with the front view; huwide Night-dim beside the Tilt tiles.
- **Content (top to bottom):** 1. Live image (one stream). 2. **Switch** Segmented: Front ·
  Underbody (one at a time). 3. Static wheel-track lines on the underbody view. 4. Optional
  small tiles beside it on HU-wide: Pitch and Roll from the Off-road page (≤ 6 tiles total),
  "Low range" and "Centre diff locked" chips when a SLABS session is open.
- **States:** above 10 km/h: the stream is replaced by "Camera hidden above 10 km/h" and a
  still icon, and returns below 8 km/h (hysteresis). Stream lost: grey with age. No front
  camera: Segmented hides the option.
- **Safety and driving rules:** `camera_live` below 10 km/h only; one stream; no recording
  playback ([UI §6][ui-6], [App model §4.4][am-4.4]).
- **Components:** `camera_live` template, Segmented, StatTile, Chip (status).
- **Spec refs:** [UI §6][ui-6] · [App model §4.4][am-4.4] · [Drive modes §5.5][dm-5.5].
- **Open questions:** the hysteresis numbers (10 off, 8 on) are a proposal.

### camera-multi — All cameras (multi-view)  [New]
- **Purpose:** see up to four cameras at once.
- **Owner:** app:camera
- **Opens from → goes to:** `camera-home` → All cameras. A tile opens that camera full
  screen (Parked). Back.
- **Layout classes:** tablet · desktop · hu7 · hu9 · huwide · phone. **Draw first:** hu9
  Night Parked 2×2; huwide Night 4×1.
- **Content (top to bottom):** CameraGrid (new component): 2×2 (or 4×1 on HU-wide), each
  with the name and a "Live" word; tap enlarges; **Snapshot all** button.
- **States:** Brain load too high: "Showing 2 of 4 to keep recording smooth". Moving: closes
  to the Drive home page; only the `camera_live` driving cameras remain.
- **Safety and driving rules:** Parked only on driver-facing displays (one stream while
  Moving, [App model §4.4][am-4.4]); a true stitched 360° view is a future camera kind with
  its own spec ([UI §6][ui-6]).
- **Components:** CameraGrid (new component), Button.
- **Spec refs:** [UI §6][ui-6] · [App model §4.4][am-4.4] · [head-unit apps §6][hu-6].
- **Open questions:** none.

### camera-dashcam — Dashcam and recording  [New]
- **Purpose:** see recording state, save a clip, and open clips.
- **Owner:** app:camera; clips are shown in Security → Clips (app:security)
- **Opens from → goes to:** `camera-home` → Dashcam; the REC strip chip. Goes to
  Security → Clips (by name), `camera-settings` → Recording.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; hu7 Night-dim Moving (save-clip only).
- **Content (top to bottom):** 1. Status: "Recording · Front, Rear · loop 4 h" with a red
  dot and "REC". 2. **Save last 60 s** (primary) → a toast "Clip saved · linked to this
  trip". 3. Storage: "Clips use 18 of 64 GB · oldest from 2 Oct". 4. Recent clips list
  (Parked) with time, camera, trip; **Open in Clips**. 5. **Pause recording** (Parked).
- **States:** storage full: `warn` "Oldest loop clips are being replaced". Brain asleep:
  "Recording starts when the Brain wakes (about 20 s)". Moving: a single **Save clip**
  button (like Mark) and the REC state; no playback, no list.
- **Safety and driving rules:** no playback unless Parked ([UI §6][ui-6]); **Save clip** is
  safe at any speed, like Mark; Cabin recording follows Security's consent rules.
- **Components:** Chip (status), Button, ListRow, ProgressRow (new component), Toast.
- **Spec refs:** [UI §6][ui-6] · [platform direction][pd] · [head-unit apps §6][hu-6].
- **Open questions:** whether Save clip also drops a Mark flag in the trip. Recommend yes.

[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-5.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[pd]: ../../../../specs/2026-10-06-platform-direction-design.md#displays-are-thin-clients-cameras-live-on-our-infrastructure
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[ch-b4]: ../../../research/canbus_headunit.md#b4-steering-wheel-reverse-cameras-amplifier
[hu-6]: ../../../../specs/2026-10-07-head-unit-apps-design.md#6-camera
