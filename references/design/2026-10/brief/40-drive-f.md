---
title: "Designer brief 40-f — Drive home pages, part 2: Convoy / Ride, Off-road (D2) and Split / Media"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-visual-design-system-design.md]
summary: >
  Second Drive home-page brief file. It covers the pages that the app and vehicle-specific presets add to the flat
  carousel: Convoy (Map and talk, and Ride, shown only while a ride is active and the Social app is on),
  Off-road for the Discovery 2 (Tilt with pitch, roll, low range, altitude, heading and speed,
  and Trail map) with its honest gaps (no node tilt yet, low range only in a SLABS session),
  the new one-time "Open SLABS" prompt on reaching Tilt while Parked, and
  Split / Media (map plus now playing, hidden until a media app exists). Each block lists
  widgets and bindings per class from the shipped presets, the Moving grid and the strip.
---

# 40-f — Drive home pages, part 2

Back to [40-a](40-drive-a.md) for the file list. The shared frame, Drive strip, Moving
template, honest states, **Draw first** list and the D2 signal table are in
[40-e](40-drive-e.md#what-every-drive-home-page-shares).

### drive-convoy-map-ptt — Convoy / Ride · Map + PTT  [Existing]
- **Purpose:** ride with friends: the map, a big push-to-talk button, the ride line.
- **Owner:** app:social
- **Opens from → goes to:** the page "Map and talk" (icon `groups`), which the Convoy
  preset adds with "Ride"; both show in the carousel only while a ride is
  active; the comms chip shows "Ride: Peak · PTT".
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** shared list,
  plus hu7 Night-dim Moving while someone is talking.
- **Content (page "Map and talk", added by preset `ostler.convoy`):** 1. **Map** pane (own position,
  trail; convoy members as plain markers, at most six, no names). 2. **Speed** overlay tile.
  3. **Talk** pane (`call` template): a large **Hold to talk** button (`mic`), "who's
  talking" as one name ≤ 30 characters (no photo), **Mute** and **End**: ≤ 3 buttons ≥ 76 px.
  HU-wide adds a **Leader** distance tile ("Leader 1.2 km") in a left column.
- **Moving placement:** HU-5, HU-7, HU-9/10 2 × 2: map left (speed overlaid top-left), Talk
  right. HU-wide 3 × 2: Speed / Leader, map, Talk. Phone 1 × 2: map top, Talk bottom.
- **States:** no ride: both Convoy pages are skipped in the carousel and the page list, never shown broken. Without
  the Map app: no markers, no leader distance. A phone or Social call pauses PTT: the Talk
  pane reads "Ride: on hold" and a press does nothing. Social disabled: "Needs the Social
  app".
- **Safety and driving rules:** audio only; no video, photos or message text; convoy markers
  only for a ride the driver opted into ([UI §12.1][ui-12.1], [Social §13][soc-13]).
- **Components:** map template, call template, StatTile.
- **Spec refs:** [Drive modes §5.4][dm-5.4] · [Social §5][soc-5] · [Vehicles & Map §7][vm-7].
- **Open questions:** none.

### drive-convoy-ride — Convoy / Ride · Ride  [Existing]
- **Purpose:** the ride at a glance: members, leader and sweep distance.
- **Owner:** app:social
- **Opens from → goes to:** the second page the Convoy preset adds.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** shared list.
- **Content (page "Ride"):** four tiles: **Ride** (Social ride status: ride name and member
  count, for example "Peak · 5"), **Leader** (Map app convoy distance, "1.2 km"),
  **Sweep** ("0.4 km"), **Speed** (km/h).
- **Moving placement:** 2 × 2 on every class (phone too). Four tiles.
- **States:** no ride: hidden. Without the Map app: Leader and Sweep read "Needs the Map app". A member stopped: an `alert_card` "Convoy: a member stopped" (see `alert-other`).
- **Safety and driving rules:** members as a count, never a list of names while Moving.
- **Components:** StatTile.
- **Spec refs:** [Drive modes §5.4][dm-5.4] · [Drive modes §5.8][dm-5.8] ·
  [Vehicles & Map §7][vm-7].
- **Open questions:** none.

### drive-offroad-tilt — Off-road (D2) · Tilt  [Existing]
- **Purpose:** green-lane driving in the D2: angles, low range, height and heading.
- **Owner:** os
- **Opens from → goes to:** the page "Tilt" (icon `landscape`), which the Off-road preset
  adds with "Trail" for a vehicle it hints (the D2); the next page is Trail map.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** shared list,
  plus hu7 Night-dim Moving with a critical roll and with every honest gap showing.
- **Content (page "Tilt", added by preset `ostler.offroad`):** 1. **Pitch** inclinometer (side view
  silhouette, for example 4°). 2. **Roll** inclinometer (rear view, for example 12°). 3.
  **Low range** chip (`IsLowRangeEngaged` ← SLABS `transfer_low`). 4. **Altitude** (GPS,
  "312 m"). 5. **Heading** compass ("214° SW"). 6. **Speed**.
- **Moving placement:** HU-5, HU-7, phone: the six tiles (3 × 2, phone 2 × 3). HU-9/10 4 × 2:
  Pitch, Roll, map pane (2 × 2) / Low range, Heading. HU-wide 6 × 2: Pitch, Roll, map, Low
  range (wide) / Altitude, Heading, Speed (wide). ≤ 6 tiles + 1 map.
- **Honest gaps on the D2:** Pitch and Roll read "Needs the node's IMU" until the node's tilt
  derivation ships (then `candidate`, valid only below 0.1 g). Low range shows only in a
  SLABS session; then rpm and coolant elsewhere read "Not in this session" and speed is GPS.
  Heading freezes below about 3 km/h and says "stale". Altitude is GPS (tens of metres).
- **States:** critical roll (user threshold, for example ≥ 30°): tile `alarm` + "Roll". The
  silhouette is static and steps ≤ 4 Hz; it never swings.
- **Safety and driving rules:** as every page ([Drive modes §4.3][dm-4.3]).
- **Components:** inclinometer tile (new component: static silhouette rotated by the value),
  binary chip tile, StatTile, compass tile, map template.
- **Spec refs:** [Drive modes §5.5][dm-5.5] · [Drive modes §5.8][dm-5.8].
- **Open questions:** the spec draws Low range and **Centre diff lock** as one two-state
  tile; the preset has Low range only because the diff-lock overlay leaf is not in the D2
  pack yet (SLABS `diff_lock` is proven but unmapped). Draw the pair as a variant.

### drive-offroad-trail — Off-road (D2) · Trail map  [Existing]
- **Purpose:** the breadcrumb trail of this trip, with heading and altitude.
- **Owner:** os
- **Opens from → goes to:** the second page the Off-road preset adds.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** shared list.
- **Content (page "Trail"):** 1. **Map** pane (own trail, heading up). 2. **Heading**. 3.
  **Altitude**. HU-9/10 swaps Heading for **Speed**.
- **Moving placement:** HU-5 and HU-7 3 × 2: map 2 × 2 left, Heading / Altitude right (the
  dock side). HU-9/10 4 × 2: map 3 × 2, Speed / Altitude. HU-wide 6 × 2: map 4 × 2, Heading /
  Altitude. Phone 2 × 3: map 2 × 2 top, Heading · Altitude below. `map` + 2 tiles.
- **States:** back-tracking along the trail needs the Navigation app ("Needs
  Navigation"). Offline basemap: trail and puck on `bg`.
- **Safety and driving rules:** own position and route only.
- **Components:** map template, compass tile, StatTile.
- **Spec refs:** [Drive modes §5.5][dm-5.5] · [visual §7][vds-7].
- **Open questions:** none.

### drive-offroad-open-slabs — Off-road "Open SLABS" prompt  [New]
- **Purpose:** K-line holds one session, so the Off-road tiles need SLABS; offer the switch
  once.
- **Owner:** app:diagnostics
- **Opens from → goes to:** swiping to the Tilt page while Parked with no SLABS session. **Open
  SLABS** releases the Td5 session and opens SLABS; **Not now** keeps the Td5 session.
- **Layout classes:** hu5 · hu7 · hu9 · huwide · phone. **Draw first:** hu7 Night Parked.
- **Content:** a small card over the page: `swap_horiz` "Low range is read by SLABS. Open
  SLABS? Engine values will pause." with **Open SLABS** and **Not now** (Not now focused).
- **States:** Parked: offered once per entry. Moving: never offered (a system switch is
  locked while Moving). Switching: "Opening SLABS…"; failure: "SLABS didn't answer. Engine
  session kept."
- **Safety and driving rules:** a system switch, refused while Moving ([UI §3.5][ui-3.5]);
  read-only (no gate action).
- **Components:** Card, Button.
- **Spec refs:** [Drive modes §5.5][dm-5.5] · [UI §3.5][ui-3.5].
- **Open questions:** should the prompt also offer "Back to Engine" when leaving Off-road
  Parked, so rpm and coolant return to Dashboard?

### drive-split-split — Split / Media · Split  [Existing]
- **Purpose:** map beside what is playing (AutoZen-style), three columns on HU-wide.
- **Owner:** app:media
- **Opens from → goes to:** the page "Split" (icon `music_note`), which the Split / Media
  preset adds; shown only when a media app is installed; HU-wide's default
  page when one exists.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** shared list,
  huwide first.
- **Content (this page, added by preset `ostler.split`):** 1. **Map** pane with a **Speed** overlay. 2. **Now
  playing** pane (`media`): static artwork, title ≤ 30 and artist ≤ 30 characters, controls
  `skip_previous`, `play_pause`, `skip_next`, `volume_up`. HU-wide adds a left column:
  **Speed** and **Coolant**; with Navigation the spec allows "Next · 300 m" there.
- **Moving placement:** HU-5, HU-7, HU-9/10 2 × 2: map left (speed overlaid), media right.
  HU-wide 3 × 2: Speed / Coolant, map, media. Phone 1 × 2: map top, media bottom.
- **States:** no media app: the page is skipped in the carousel and the list; the picker says "Needs a
  media app". Nothing playing: "Nothing playing" with play. Browsing: only a `short_list`.
- **Safety and driving rules:** no lyrics, no video, no browsing beyond a `short_list`
  ([UI §12.1][ui-12.1]).
- **Components:** map template, media template, StatTile.
- **Spec refs:** [Drive modes §5.6][dm-5.6] · [Drive modes §5.9][dm-5.9].
- **Open questions:** none.

[dm-4.3]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#43-the-moving-section-and-the-template-mapping
[dm-5.4]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#54-convoy--ride
[dm-5.5]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#55-off-road-d2
[dm-5.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-5.8]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#58-faces-per-preset
[dm-5.9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#59-defaults-and-rotation-per-class
[soc-13]: ../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap
[soc-5]: ../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[vds-7]: ../../../../specs/2026-10-07-visual-design-system-design.md#7-maps
[vm-7]: ../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving
