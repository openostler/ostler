---
title: "Designer brief — Social add-on: Chats, conversation, Calls, Rides and Cameras"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-social-addon-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md]
summary: >
  Page content for the Social add-on's own page, app drawer → Social, for a UX designer. Covers the
  four indexed tabs (Chats, Calls, Rides and Cameras) and the new conversation view behind a
  chat row: every row, field, button label and badge, what each driving state shows (the page
  is Parked or passenger only; while Moving it is replaced by the `alert_card` and `call`
  templates), ghost mode's effect (none on messaging), link badges for internet, Wi-Fi mesh,
  HaLow and LoRa, the hub link card and the components to use. Calls, video, the PTT sheet,
  ride creation and camera grants are in part b.
---

# Social add-on, part a: the page and its tabs

Example numbers and names in quotes are label formats, not data.

Social is an optional add-on (`ostler-app-social`), reached at **app drawer → Social** (slot
`more:social`), pinnable to the dock by the user. It is never a destination of its own.
The page has four tabs in a Segmented control: **Chats · Calls · Rides · Cameras** (Cameras
appears only once phase S4 ships and a camera exists). While Moving on a driver-facing head
unit the whole page is locked; people reach Social through the comms chip, the `call`
template and message `alert_card`s only ([Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell), [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)). Part b:
[60-apps-social-b.md](60-apps-social-b.md).

Shared rules for every block here:
- **Ghost costs nothing in Social**: messaging, PTT and calls keep working in ghost; only
  presence ("online", "in a ride") is hidden ([Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides), [Accounts §14.3](../../../../specs/2026-10-06-accounts-sharing-design.md#143-ghost-mode)).
- **Link badge** (Chip, status style, icon + word): "Internet", "Wi-Fi mesh · 2 hops",
  "HaLow", "LoRa · radio-encrypted". Never colour alone ([Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules)).
- **No message content on a driver screen while Moving**, no avatars, no video ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).

### social-chats — Social: Chats list  [Existing]
- **Owner:** app:social
- **Purpose:** every conversation I have: 1:1, groups and ride channels, newest first.
- **Opens from → goes to:** app drawer → Social (default tab), a dock pin, the Home Social
  card, a message `alert_card` (Parked) → social-conversation; "New chat" → contact picker
  (accounts-s7 contacts); Rides tab.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night and Day; hu7 Night and Night-dim Parked; hu7 Night-dim Moving (the locked frame).
- **Content (top to bottom):**
  1. Header: title "Social", the visibility chip read from the OS ("Ghost" or "Visible to Peak
     District ride · 1 h 20 m"), a "New chat" Button (icon `edit_square`).
  2. Tabs: Chats (selected) · Calls · Rides · Cameras.
  3. Pinned row when a ride is active: "Peak District ride · 5 riding" with a "Live" Chip and
     an "Open ride" chevron (to social-rides).
  4. Conversation rows (ListRow): avatar or initials disc (Parked only), name ("Sam", "Peak 4x4
     club", "Ride: Peak District"), last-message line (Parked only, one line, "Voice note",
     "Photo", "Location" for non-text), time ("14:05", "Yesterday"), unread count Chip,
     delivery tick icon (sent, delivered, read), link badge when not internet.
  5. Empty footer link: "Invite someone" (opens accounts-s7 → Add).
- **States:** empty: "No chats yet. Invite a friend to start." + Invite Button · loading:
  three skeleton rows · error: "Social stopped" card (app error boundary) · offline: rows stay,
  a banner "Offline · messages queue for 24 h", unsent messages show a clock icon · no vehicle:
  unchanged (Social is about people) · Parked: full · Idling: full read; "New chat" needs Park
  evidence · Moving (head unit): locked view "Available when parked" + Open on phone; the
  comms chip and alert cards carry Social · Passenger (phone "I'm a passenger"): full · locked
  (no Brain and no phone pairing): "Needs the Brain or a paired phone".
- **Safety and driving rules:** page locked while Moving on any driver-facing display
  ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)); no text entry while Idling without Park evidence; message previews never on a
  driver-facing display while Moving ([Social §12](../../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving)).
- **Components:** Segmented (tabs), ListRow, Chip (unread, link badge, visibility), Button,
  Card (error), Sheet (contact picker).
- **Spec refs:** [Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell) · [Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) · [Social §4](../../../../specs/2026-10-07-social-addon-design.md#4-messaging) · [Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) · [Social §12](../../../../specs/2026-10-07-social-addon-design.md#12-amendment-2026-10-07-dmd-round-approved-message-alerts-while-moving) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)
- **Open questions:** should ride channels sort above 1:1 chats while the ride is live, or
  only the pinned row?

### social-conversation — Social: conversation  [New]
- **Owner:** app:social
- **Purpose:** read and write one conversation (1:1, group or ride channel).
- **Opens from → goes to:** a social-chats row; a message `alert_card` when Parked; a ride
  card → back to Chats; header → contact or group detail (accounts-s7); Call icon →
  social-call-voice; Video icon → social-call-video (Parked only).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  phone Night and Day; hu7 Night Parked; tablet Night (list + conversation two panes).
- **Content (top to bottom):**
  1. Header: back, name ("Sam" or "Ride: Peak District · 5"), presence word when not ghosted
     ("Online", "In a ride"), Call (`call`) and Video (`videocam`) icon Buttons, "…" menu
     (Mute, Delete chat, Retention "90 days" or "30 days after ride end").
  2. Message list: bubbles with sender (groups), time, delivery ticks, link badge ("via LoRa ·
     radio-encrypted"); voice notes with play and length "0:12"; photo (S2+), location pin card
     at the precision shared ("Near Bakewell", coarse disc); **hub link card**: title ≤ 30
     characters, "Ostler Community", no preview until tapped ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C6).
  3. Day dividers ("Today", "Tue 6 Oct").
  4. Composer: text field "Message", attach (Photo, Location, Trip card), a hold-to-record
     voice-note Button (`mic`, "Hold to record"), Send.
  5. Queue notice when no link qualifies: "Waiting for a link · will try for 24 h".
- **States:** empty: "Say hello to Sam" · loading: skeleton bubbles · error: a failed bubble
  with "Not sent · Retry" · offline: composer stays, bubbles queue with a clock icon · Parked:
  full · Idling: read and play; composer needs Park evidence · Moving: locked view; incoming
  messages become `alert_card`s · Passenger (phone): full.
- **Safety and driving rules:** nothing here renders on a driver-facing display while Moving;
  a message shaped like a command runs nothing; no VIN, plate or vehicle id in any field
  ([Social §4](../../../../specs/2026-10-07-social-addon-design.md#4-messaging), [ADR-0036](../../../../decisions/adr-0036-vin-and-identity-data-in-recordings.md)).
- **Components:** ListRow, Card (link card, location card), Chip (link badge), Button,
  new component **MessageBubble**, new component **VoiceNotePlayer**.
- **Spec refs:** [Social §4](../../../../specs/2026-10-07-social-addon-design.md#4-messaging) · [Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)
- **Open questions:** do delivery ticks show "read" by default, or only when both sides allow
  it?

### social-calls — Social: Calls history  [Existing]
- **Owner:** app:social
- **Purpose:** the Ostler-source view of the one local call log (Social calls, PTT sessions).
- **Opens from → goes to:** Social tabs; a "Missed call" card at the next stop → call back
  (social-call-voice); a row → contact detail.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked; hu7 Night-dim Moving (locked frame).
- **Content (top to bottom):**
  1. Filter Segmented: All · Missed.
  2. Rows (ListRow): direction icon (`call_received`, `call_made`, `call_missed`), name, kind
     ("Voice", "Video", "Ride PTT"), duration "04:12", time, link badge ("Wi-Fi mesh"),
     trailing call-back icon Button.
  3. Footer caption: "Calls are never recorded. This log stays on this car for 90 days."
- **States:** empty: "No calls yet" · loading: skeleton rows · offline: log still shows (it is
  local) · Parked: full · Idling: read and call back · Moving: locked view; missed calls wait as
  one "Missed calls (2)" card at the next Parked · Passenger (phone): full.
- **Safety and driving rules:** list locked while Moving; calls themselves use the `call`
  template ([Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls)); the log is never uploaded ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C4, [ADR-0010](../../../../decisions/adr-0010-replay-notes-audio-motion.md)).
- **Components:** Segmented, ListRow, Button (call back), Chip (link badge).
- **Spec refs:** [Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell) · [Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [App model §15](../../../../specs/2026-10-06-app-model-design.md#15-amendment-2026-10-07-dmd-round-approved-widgets-drive-menu-rows-input-and-new-slots)

### social-rides — Social: Rides (live ride panel)  [Existing]
- **Owner:** app:social
- **Purpose:** the live ride: who is in it, who is talking, how each member is linked.
- **Opens from → goes to:** Social tabs; the comms chip "Ride: Peak · PTT" (Parked); the Home
  ride card → social-ptt-sheet (talk), vehicles-convoy (map), social-ride-new ("New ride").
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked; hu7 Night-dim Moving (Convoy / Ride home page, Drive modes §5.4).
- **Content (top to bottom):**
  1. Active ride Card: name "Peak District ride", time left "ends 18:00 · 2 h 10 m", members
     heard "5 of 6", leader and sweep names, "Open map" Button (vehicles-convoy).
  2. Big **Hold to talk** Button (HeroStat size, `record_voice_over`), "Who's talking" line
     ("Sam is talking"), Mute ride toggle.
  3. Member rows (ListRow): name, role chip (Leader, Sweep), presence word (hidden if that
     member is ghosted), distance to me when shared ("1.2 km"), link badge ("LoRa", "Wi-Fi
     mesh · 1 hop"), last heard "2 min ago".
  4. Ride actions: "Leave ride", "End ride" (leader only, confirm sheet, Cancel focused).
  5. Upcoming and past rides list: name, date, members count; past rides show "Ended" and no
     positions (deleted at ride end).
- **States:** empty: "No ride. Start one with friends or a group." + "New ride" Button ·
  loading: skeleton card · offline: "Talking over LoRa is not possible; text and positions
  still go" · Parked: full · Idling: full read; Hold to talk works · Moving (head unit): the
  page is locked; PTT lives in the comms chip and the Convoy / Ride home page (`call`
  template: Hold to talk, Mute, End) · Passenger (phone): full.
- **Safety and driving rules:** no member names, avatars or photos on the head-unit map while
  Moving, convoy markers only ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44), [Vehicles & Map §7](../../../../specs/2026-10-07-vehicles-and-map-addon-design.md#7-head-units-and-driving)); a phone or Social call pauses PTT and the
  chip reads "Ride: on hold" ([Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) C1).
- **Components:** Card, Button (Hold to talk), ListRow, Chip (role, link badge), Toggle (new
  component), Sheet (confirm).
- **Spec refs:** [Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell) · [Social §3](../../../../specs/2026-10-07-social-addon-design.md#3-contacts-friends-groups-and-rides) · [Social §5](../../../../specs/2026-10-07-social-addon-design.md#5-push-to-talk-voice-calls-and-video-calls) · [Social §6](../../../../specs/2026-10-07-social-addon-design.md#6-the-link-router-and-per-class-rules) · [Social §13](../../../../specs/2026-10-07-social-addon-design.md#13-amendment-2026-10-07-dmd-round-approved-comms-overlap) · [Drive modes §5.4](../../../../specs/2026-10-07-drive-modes-and-editing-design.md#54-convoy--ride)

### social-cameras — Social: Cameras (S4)  [Existing]
- **Owner:** app:social
- **Purpose:** cameras friends share with me, and the cameras I share, all live only.
- **Opens from → goes to:** Social tabs; a "Sam shared the front camera" card → 
  social-camera-viewer; "Share a camera" → social-camera-grant; "Being viewed" →
  social-being-viewed.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone
  Night; hu7 Night Parked; hu7 Night-dim Moving (locked frame).
- **Content (top to bottom):**
  1. "Shared with me" rows: friend name, camera name ("Front", "Rear"), time left chip "52 min",
     "Live" Chip, chevron to the viewer.
  2. "I'm sharing" rows: camera, audience ("Peak District ride"), time left, "Viewed by 2"
     Chip, "Stop" Button.
  3. "Share a camera" Button; caption "Viewers see live video only. They can still
     screen-record." ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)).
  4. My cameras off by default: rows "Interior · Off · asks occupants each trip".
- **States:** empty: "No cameras shared. Ghost by default: nothing is shared until you turn a
  camera on." · loading: skeleton · offline: shared-with-me rows read "Offline" · no camera:
  tab hidden (requires a camera device) · Parked: full · Idling: list readable, no video on a
  driver-facing display · Moving: locked · Passenger (phone): full.
- **Safety and driving rules:** another car's camera never on a driver-facing display while
  Idling or Moving ([Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4)); stopping a share is one tap at any time.
- **Components:** ListRow, Chip (time left, Live, Viewed by), Button, Card.
- **Spec refs:** [Social §2](../../../../specs/2026-10-07-social-addon-design.md#2-where-it-sits-in-the-shell) · [Social §7](../../../../specs/2026-10-07-social-addon-design.md#7-camera-sharing-s4) · [Accounts §14.1](../../../../specs/2026-10-06-accounts-sharing-design.md#141-the-data-class-registry) · [Calls research §8](../../../../references/research/calls_video_camera_sharing.md#8-camera-sharing)
