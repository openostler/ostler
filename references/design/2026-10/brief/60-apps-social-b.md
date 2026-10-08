---
title: "Designer brief — Social add-on: rides, push-to-talk, calls, video and camera sharing"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-07-social-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, references/research/calls_video_camera_sharing.md]
summary: >
  Page content for the Social add-on screens that are approved but not yet indexed: starting a
  ride (convoy) with its ask-at-start step, the push-to-talk sheet behind the comms chip, the
  Parked voice-call screen, video calls (Parked or passenger devices only, never a
  driver-facing screen), the camera grant sheet, the live camera viewer, the "being viewed"
  badge and sheet, the interior-camera occupant consent on the head unit, and Social settings
  (who may reach me, auto-reply scope, waking for calls, notify-via). Each block lists content,
  states, driving rules and components. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# Social add-on, part b: rides, talk, calls and cameras

Example numbers and names in quotes are label formats, not data.

Part a holds the page and its tabs: [60-apps-social-a.md](60-apps-social-a.md). The `call`
template itself (incoming, in call, waiting) is drawn by the shell and indexed as
`phone-incoming`; Social uses the same one call session ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C1, [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)).

**Start a ride (flow).**

| Step | Screen | The user does | Can fail · recovery |
|---|---|---|---|
| 1 | social-ride-new | names the ride, picks members or a group, a window and an optional route | no contacts: "Invite someone" opens accounts-s7 |
| 2 | vehicles-ride-ask | answers "Share live position with this ride until it ends?" | declines: the ride runs with talk only; can share later |
| 3 | social-rides | sees the live ride panel; members auto-join the channel and PTT room | no link: "Waiting for members" and queued invites |

### social-ride-new — Social: New ride  [New]
- **Owner:** app:social
- **Purpose:** create a ride (a OS group of kind ride) with members, a time window and a route.
- **Opens from → goes to:** social-rides "New ride"; a group's "…" menu → vehicles-ride-ask →
  social-rides. Cancel → social-rides.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. Title "New ride"; field "Ride name" (≤ 30 characters, e.g. "Peak District ride").
  2. "Who": a group picker row ("Peak 4x4 club") or contacts with check rows; "Leader" (me by
     default) and "Sweep" pickers.
  3. "When": Segmented "Now · Later"; start time; window ("ends 18:00"; the share window is at
     most 24 h, said in a caption).
  4. "Route" (optional): "Pick from Navigation library" row (only with Navigation enabled).
  5. "Safety contacts get start and end notices" Toggle (off by default; accounts-s10).
  6. Primary Button "Start ride" (or "Schedule ride").
- **States:** empty contacts: "Invite someone first" · loading: Button spinner · error: "Ride
  not created · Retry" · offline: rides can still start on LAN or a mesh; caption "Members
  join when a link appears" · Parked: full · Idling: needs Park evidence for typing · Moving:
  locked view "Available when parked" + Open on phone.
- **Safety and driving rules:** text entry Parked or Idling with Park evidence only
  ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)); a ride is the only unit for live precise position ([Vehicles & Map §6.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides)).
- **Components:** Sheet, ListRow (check), Segmented, Toggle, Button.
- **Spec refs:** [Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) · [Accounts §14.6](../../../../specs/2026-10-06-accounts-sharing-design.md#146-contacts-groups-and-invites) · [Vehicles & Map §6.1](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#61-rides) · [Navigation §7](../../../../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports)

### social-ptt-sheet — Social: PTT and ride call sheet  [New]
- **Owner:** app:social
- **Purpose:** the Parked sheet behind the comms chip for an active ride or call.
- **Opens from → goes to:** the comms chip "Ride: Peak · PTT" or "Call · 04:12" (while Moving
  the chip opens the `call` template instead) → social-rides, social-call-voice.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; phone Night; hu7 Night-dim Moving (the `call` template it becomes).
- **Content (top to bottom):**
  1. Ride line: "Ride: Peak District · 5 riding · ends 18:00".
  2. "Who's talking" line: "Sam is talking" or "Channel clear".
  3. **Hold to talk** Button (largest target on the sheet), roger beep note "Beep on release".
  4. Buttons: Mute ride · End (leave PTT for this trip).
  5. Link line: "Internet · Wi-Fi mesh 2 hops · LoRa (text only)" from the router.
  6. "On hold" banner when a phone call is active: "Ride on hold during your call".
- **States:** loading: "Joining ride…" · offline: "Talk needs internet or a Wi-Fi mesh; bursts
  queue on HaLow" · Parked: full sheet · Idling: full sheet · Moving: the `call` template:
  name ≤ 30 characters, Hold to talk, Mute, End (≤ 3 buttons), timer, link badge.
- **Safety and driving rules:** audio only; ≤ 3 buttons while Moving; a hardware PTT button
  arrives as the `ptt` intent, not a car action ([Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls), [Shell input §6](../../../../specs/2026-10-07-shell-input-design.md#6-drive-mode)); PTT pauses during any
  call ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap)).
- **Components:** Sheet, Button (Hold to talk), call template, Chip (link badge).
- **Spec refs:** [Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell) · [Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots) · [Drive modes §5.4](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#54-convoy--ride)

### social-call-voice — Social: voice call (Parked)  [New]
- **Owner:** app:social
- **Purpose:** a 1:1 or group voice call over the internet or a Wi-Fi mesh.
- **Opens from → goes to:** Call icon in social-conversation or social-calls; an answered
  incoming call → back to the previous page on End.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked; hu7 Night-dim Moving (`call` template).
- **Content (top to bottom):**
  1. Name ("Sam", or "Peak 4x4 club · 4 on call" as a count, never a list on the head unit).
  2. State and timer "04:12", link badge "Internet".
  3. Buttons: Mute · Speaker / Car audio route · Video (Parked, not on head units while
     Idling) · End (danger).
  4. Quality line when the link falls: "Weak link · switched to voice note".
- **States:** loading: "Calling…" · error: "Call failed · Try again" · offline: "No link for
  calls · Send a voice note instead" · Parked: full · Idling and Moving (head unit): `call`
  template (Mute, End, PTT) · Passenger (phone): full.
- **Safety and driving rules:** calls not recorded unless the user turns on recording, with an announced consent prompt ([Phone & Comms §9](../../../../specs/2026-10-07-phone-comms-addon-design.md#9-data-and-privacy)); audio only on driver-facing
  displays; only ride members and favourites ring while Moving ([Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls)).
- **Components:** call template, Button, Chip (link badge).
- **Spec refs:** [Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) · [Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)

### social-call-video — Social: video call (Parked, passenger devices)  [New]
- **Owner:** app:social
- **Purpose:** a video call when Parked, or on a phone or rear screen in passenger use.
- **Opens from → goes to:** Video icon in social-conversation or a voice call; falls back to
  social-call-voice when the link drops below 500 kbit/s.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night Parked; tablet Night (rear screen); hu9 Night Parked; hu7 Night-dim Moving (the
  locked frame showing the `call` template, no video).
- **Content (top to bottom):**
  1. Remote video full-bleed; my preview in a corner tile; names on the tiles (group).
  2. Controls bar: Mute · Camera off · Flip · End.
  3. Notice on start: "Video stops when the car moves. The call carries on as voice."
- **States:** loading: "Connecting video…" · error: "Video unavailable · voice only" ·
  offline: not offered · Parked: full · Idling (driver-facing): video replaced by the `call`
  template · Moving (driver-facing, Passenger view included): never video ·
  Passenger (phone with "I'm a passenger", or an owner-declared rear screen): full.
- **Safety and driving rules:** no video on any driver-facing display while Idling or
  Moving, override or not ([Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)); the switch to voice is automatic.
- **Components:** new component **VideoTile**, Button, call template.
- **Spec refs:** [Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) · [Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44) · [Calls research §7](../../../../references/research/calls_video_camera_sharing.md#7-calls-in-a-moving-car-what-is-allowed)

### social-camera-grant — Social: share a camera  [New]
- **Owner:** app:social
- **Purpose:** grant a live, time-boxed view of one camera to a contact, group or ride.
- **Opens from → goes to:** social-cameras "Share a camera"; a ride's "…" menu →
  social-interior-consent (interior only) → social-cameras.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. "Which camera": rows Front · Rear · Interior (each separate; Interior marked "asks
     occupants").
  2. "Who": contact, group or "This ride".
  3. "For how long": Segmented "This ride · 1 h · …up to 24 h"; interior never open-ended.
  4. Sound: "Camera audio: off" (Toggle off by default, explained).
  5. Plain lines: "Live only, no recording or rewind for viewers. They can still screen-record.
     You see who is watching."
  6. Button "Share camera".
- **States:** loading · error: "Camera asleep · Wake it locally" · no camera: the screen is not
  offered · Parked: full · Idling: with Park evidence · Moving: locked view.
- **Safety and driving rules:** ghost by default, no camera shared until turned on; recording,
  pan/tilt/zoom, IR and talk-back are not part of a grant and stay local ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)).
- **Components:** Sheet, ListRow, Segmented, Toggle, Button.
- **Spec refs:** [Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4) · [Accounts §14.1](../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry) · [ADR-0038](../../../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) · [Calls research §8](../../../../references/research/calls_video_camera_sharing.md#8-camera-sharing)

### social-camera-viewer — Social: live camera viewer  [New]
- **Owner:** app:social
- **Purpose:** watch a friend's shared camera, live only.
- **Opens from → goes to:** social-cameras row; a ride member's "…" → back to social-cameras.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Night Parked; hu9 Night Parked; hu7 Night-dim Moving (locked frame).
- **Content (top to bottom):** 1. VideoTile with "Live" Chip and "Sam · Front camera".
  2. Time left "Shared for 48 min". 3. Line "Sam can see that you are watching." 4. Close.
- **States:** loading: "Connecting…" · error: "Camera stopped sharing" · offline: "No link for
  video" · Parked: full · Idling and Moving (driver-facing): never shown · Passenger (phone):
  full.
- **Safety and driving rules:** no scrub-back, no recording controls; never on a driver-facing
  display while Idling or Moving ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)).
- **Components:** VideoTile, Chip, Button.
- **Spec refs:** [Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)

### social-being-viewed — Social: "Being viewed" badge and sheet  [New]
- **Owner:** app:social
- **Purpose:** tell the owner, on the car and the phone, that someone is watching a camera.
- **Opens from → goes to:** a badge on the head unit and the owner's phone → this sheet;
  "Stop all" → social-cameras.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Moving
  (badge only); hu7 Night Parked (sheet); phone Night.
- **Content (top to bottom):** 1. Badge "Viewed by 2" (`visibility` icon + words). 2. Sheet:
  rows per viewer, camera, since "14:02". 3. Buttons "Stop this camera", "Stop all".
- **States:** Parked: sheet · Moving: the badge stays, tapping it offers one "Stop all"
  (one tap, allowed while Moving, like going ghost) · offline: badge clears when no viewer.
- **Safety and driving rules:** stopping is always allowed; every view is audited ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)).
- **Components:** Chip (badge), Sheet, ListRow, Button.
- **Spec refs:** [Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4) · [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)

### social-interior-consent — Social: interior camera consent  [New]
- **Owner:** app:social
- **Purpose:** ask the people in the car each trip before an interior camera is shared.
- **Opens from → goes to:** a share or ride grant that includes Interior → back to the grant.
- **Layout classes:** hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night Parked.
- **Content (top to bottom):** 1. "Share the inside of this car with Peak District ride?"
  2. "Everyone in the car should agree. Audio is not shared." 3. Buttons "Allow for this
  trip" and "Don't share" (Don't share focused).
- **States:** Parked: full · Idling/Moving: waits for Parked; the share stays off.
- **Safety and driving rules:** asked each trip; never open-ended ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)).
- **Components:** Sheet, Button.
- **Spec refs:** [Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4) · [Accounts §14.1](../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry)

### social-settings — Social: settings  [New]
- **Owner:** app:social
- **Purpose:** who may reach me, auto-reply, waking for calls and notify-via.
- **Opens from → goes to:** Social "…" → Settings; Settings → Alerts → Social filter.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. "Who may message me": Contacts (default) · Ride members only.
  2. "Who may call me": Contacts and ride members (default) · Favourites only.
  3. "I'm driving" auto-reply: Toggle; scope Segmented "No one · Ride members · Favourites ·
     All contacts" (default favourites and ride members); text field ≤ 60 characters; caption
     "Ostler messages only. Once per chat per trip."
  4. "Canned replies" row → the shared list (five, ≤ 30 characters, edited Parked only).
  5. "Alert for group messages" Toggle (off).
  6. "Wake the car for calls from" group picker (off; uses the wake quota).
  7. "Notify via": rows for the owner's own webhook or bot (Discord, Telegram, ntfy, Home
     Assistant), per destination Toggle, "Test".
- **States:** loading · error · Parked: full · Idling: Park evidence for typing · Moving: locked.
- **Safety and driving rules:** auto-reply never goes into WhatsApp, SMS or other apps
  ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C5); canned replies edited Parked only ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Segmented, Toggle, Button, Sheet.
- **Spec refs:** [Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) · [Social §8](../../../../specs/2026-10-07-social-addon-design.md#8-driving-privacy-and-compliance) · [Social §9](../../../../specs/2026-10-07-social-addon-design.md#9-media-stack-and-integrations) · [Social §12](../../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap)

### social-setup — Social: first setup  [New]
- **Owner:** app:social
- **Purpose:** the Social app's own setup flow, run once after the app is installed.
- **Opens from → goes to:** the app framework's install step (90-appframe files) or the first
  open of Social → social-settings choices → social-chats.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night Parked.
- **Content (top to bottom):**
  1. Step 1 "Talk to the people you drive with": three lines (chats, push-to-talk on rides,
     calls when stopped); "No feed, no directory, no ads."
  2. Step 2 "You stay a ghost": "Messaging and calls work in ghost. Nobody sees where you are
     unless you choose." (links vehicles-visibility; nothing changes here).
  3. Step 3 "Who may reach you": the two choices from social-settings, defaults pre-set.
  4. Step 4 "Invite someone": QR, link or code (accounts-s7), or "Later".
  5. Done → Chats.
- **States:** no contacts: step 4 is the main action · offline: steps work; invites queue ·
  Parked: full · Moving: locked view "Available when parked" + Open on phone.
- **Safety and driving rules:** setup is Parked only on a driver-facing display ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** Sheet, ListRow, Segmented, Button, QRCode.
- **Spec refs:** [Social §1](../../../../specs/2026-10-07-social-addon-design.md#1-purpose-and-non-goals) · [Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) · [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)
