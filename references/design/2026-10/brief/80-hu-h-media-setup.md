---
title: "Designer brief 80-h — Media app: first-run setup, network shares, streaming integrations, settings and widgets"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-phone-comms-addon-design.md]
summary: >
  The Media app's first-run setup and settings (app:media) and how streaming services plug
  in. Setup picks the music sources: storage on the Brain, USB sticks, network shares and
  Bluetooth phones. Adding a network share is its own page. Streaming services are separate
  integrations from the Store, each with its own setup page, in the Home Assistant style;
  Media lists them. Settings cover library folders, USB auto-play, resume, artwork, video,
  and indexing. The end lists the widgets Media adds to the widget picker gallery (now
  playing, recent, source shortcut) with their setup options and Moving behaviour.
---

# 80-h — Media setup, integrations, settings and widgets

Proposed for the reason in [80-g](80-hu-g-media.md). All pages are Parked only on
driver-facing displays and can run from a phone linked to the car.

## Setup flow (first run)

| Step | Screen | What the user does | What can fail, and the recovery |
|---|---|---|---|
| 1 | `audio-setup-shape` | Confirms "Ostler is the head unit" (shared with Audio) | Beside a head unit: Media offers Bluetooth and shares only |
| 2 | `media-setup` | Ticks the sources to use | No source available: "Add one later" |
| 3 | `media-share-add` | Adds a network share (optional) | Share unreachable or wrong password: error with retry |
| 4 | `media-setup` (indexing) | Waits for the first scan or skips | Slow USB: indexing continues in the background |
| 5 | `media-now-playing` | Lands on now playing, nothing playing | — |

### media-setup — Media: choose sources  [Proposed]
- **Why the app needs it:** the player is empty until the owner says where music lives.
- **Purpose:** choose and check every music source in one page.
- **Owner:** app:media
- **Opens from → goes to:** first open of Media; `media-settings` → Sources; the empty
  library card. Goes to `media-share-add`, `phone-pairing` (by name), `media-integrations`,
  `media-now-playing`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. StepProgress "Sources".
  2. ListRows with Toggles and a status word:
     - **Music on the Brain** — "Ostler storage · 12 GB free" with **Choose folder**.
     - **USB sticks and SD cards** — "Play when plugged in" option.
     - **Network shares** — "None yet" with **Add a share**.
     - **Bluetooth phones** — "Pixel 8 · media audio on" or **Pair a phone** (Phone app).
     - **Streaming services** — "Add from the Store" → `media-integrations`.
  3. **Index now** with a ProgressRow "Indexing · 640 of 1,204 tracks"; **Skip**.
  4. **Done** (primary).
- **States:** Brain asleep: "Needs the Brain" Card with **Wake**. No storage free: `warn`.
  Moving: locked view.
- **Safety and driving rules:** Parked only; no typing while Moving.
- **Components:** StepProgress (new component), ListRow, Toggle (new component),
  ProgressRow (new component), Button.
- **Spec refs:** [UI §3.5][ui-3.5] · [App model §14][am-14].
- **Open questions:** none.

### media-share-add — Add a network share  [Proposed]
- **Why the app needs it:** many owners keep music on a home server; the car is on home
  Wi-Fi when parked at home.
- **Purpose:** add an SMB or NFS share, or a DLNA server.
- **Owner:** app:media
- **Opens from → goes to:** `media-setup` → Add a share; `media-settings` → Sources. Back to
  where it came from.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone
  Day; hu7 Night.
- **Content (top to bottom):** 1. "Found on this network" ListRows (DLNA servers and SMB
  hosts). 2. **Address** TextField ("smb://nas.local/music"). 3. **User** and **Password**
  fields (stored on the Brain only). 4. **Sync** Segmented: Stream when at home · Copy to the
  Brain for the road (with a size estimate "8.4 GB"). 5. **Test** and **Add**.
- **States:** unreachable: "Can't reach nas.local"; wrong password; copy in progress
  "Copying · 3.1 of 8.4 GB · on home Wi-Fi only". Moving: locked view.
- **Safety and driving rules:** Parked only; credentials never leave the Brain.
- **Components:** ListRow, TextField (new component), Segmented, Button.
- **Spec refs:** [UI §3.5][ui-3.5].
- **Open questions:** copying over the uplink costs data; limit it to home Wi-Fi by
  default? Recommend yes.

### media-integrations — Streaming integrations  [Proposed]
- **Why the app needs it:** streaming services are separate integrations (one repo each);
  Media must show which are installed and how to add one.
- **Purpose:** list streaming integrations that feed Media, and add more from the Store.
- **Owner:** app:media
- **Opens from → goes to:** `media-setup` → Streaming; `media-settings`. Goes to
  `media-integration-setup`, the Store (70-store files) filtered to "Media integrations".
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with two installed; phone Day empty.
- **Content (top to bottom):** 1. Installed: ListRows with the integration's icon, name,
  account state ("Signed in on the phone", "Needs setup"), and a status chip. 2. **Add a
  streaming service** (Store, filtered). 3. A note: "Each service is its own app with its own
  terms. Some need the internet; offline playback depends on the service."
- **States:** none installed: empty Card with **Browse the Store**. Offline: chips read
  "Offline · downloaded only". Moving: locked view.
- **Safety and driving rules:** Parked only. Integrations fill the `media` template; they
  cannot draw their own Moving UI ([App model §4.4][am-4.4]).
- **Components:** ListRow, Chip (status), Button, Card.
- **Spec refs:** [App model §4.4][am-4.4] · [App model §14][am-14] · [Drive modes §5.6][dm-5.6].
- **Open questions:** which bridges come first: a Spotify Connect receiver and an MPRIS
  bridge are named in [Drive modes §5.6][dm-5.6]; others need each service's terms checked.

### media-integration-setup — Streaming integration setup  [Proposed]
- **Why the app needs it:** each integration needs a sign-in or link step; this is the
  shape they all follow.
- **Purpose:** link one streaming integration to Media.
- **Owner:** os (integration setup frame, 90-appframe files); the integration fills it
- **Opens from → goes to:** `media-integrations` → a row; the Store after install. Back to
  `media-integrations`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu7
  Night with "Continue on your phone"; phone Day sign-in.
- **Content (top to bottom):** 1. Integration name and icon. 2. What it can do (Chips:
  "Play", "Browse", "Offline downloads", "Needs internet"). 3. Data it uses (permissions):
  "Account name", "What you play", never location. 4. **Sign in**: on a head unit a QR code
  and a short code, "Continue on your phone"; on a phone the service's own page. 5. Result
  "Linked as *account name*". 6. **Done**.
- **States:** sign-in pending; expired code (**New code**); offline ("Connect to the
  internet to sign in"). Moving: locked view.
- **Safety and driving rules:** Parked only; no typing on the head unit, a QR code instead.
- **Components:** Chip, ListRow, QR code (new component), Button.
- **Spec refs:** [App model §14][am-14].
- **Open questions:** none.

### media-settings — Media settings  [Proposed]
- **Why the app needs it:** the app's own choices need one home outside system Settings.
- **Purpose:** the Media app's options.
- **Owner:** app:media
- **Opens from → goes to:** `media-now-playing` → Settings; App info → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. **Sources** (as `media-setup`). 2. **Playback**: Toggle
  "Resume where I left off when the car starts" (on); Toggle "Play when a USB stick is
  plugged in" (off); Segmented "Gap between tracks: Normal · Gapless · Crossfade 3 s".
  3. **Artwork**: Toggle "Look up missing artwork online" (off; "sends album names").
  4. **Video**: Toggle "Allow video when parked" (on), with the fixed line "Video always stops
  while driving". 5. **While driving the browse list shows**: Segmented Recent · Playlists ·
  Favourites. 6. **Rebuild the library** (secondary).
- **States:** not owner: Sources read only. Moving: locked view.
- **Safety and driving rules:** Park to edit; no setting can allow video while Moving.
- **Components:** ListRow, Toggle (new component), Segmented, Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

## Media widgets (in the widget picker gallery)

- **Now playing** (the approved "now playing" widget from a media source, [Drive modes
  §9][dm-9]) — artwork, title, artist, controls; for whatever source is active (Radio,
  Media, Bluetooth, streaming). Sizes: small (artwork and play), medium (title, artist,
  controls), wide (adds source and progress), hero (large artwork, Parked home pages). Setup
  options: which source (Follow the active source, or a fixed one), show artwork, show
  progress (Parked only), controls (skip, seek, like). **Moving:** the OS draws the `media`
  template (`media-moving`).
- **Recent and playlists** — up to 6 rows to start playing. Sizes: medium, wide. Setup
  options: Recent, a playlist, or Favourites; number of rows (3 or 6). **Moving:** a
  `short_list` of ≤ 6 rows, ≤ 30 characters each.
- **Source shortcut** — one tap to play a chosen source ("USB stick", "Bluetooth"). Size:
  small. Setup options: which source. **Moving:** allowed (source switch).
- **Shortcuts:** "Media" app shortcut; Drive menu rows "Play or pause" and "Next track".

[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[am-14]: ../../../../specs/2026-10-06-app-model-design.md#14-amendment-2026-10-07-approved-ecosystem-add-ons-trips-and-templates
[dm-5.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
