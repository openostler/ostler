---
title: "Designer brief 80-g — Media app: the Moving media template, now playing, browse, queue, Bluetooth audio, video"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-phone-comms-addon-design.md, references/research/driver_distraction_rules.md]
summary: >
  The Media app's pages (app:media) and the OS's `media` Moving template that Radio, Media,
  Bluetooth and streaming all fill. The template frame and the Media pages are New (the
  head-unit apps spec). Now playing shows artwork, title, artist, album, progress and controls. Browse
  covers local storage, a USB stick and network shares by folder, artist, album and
  playlist (Parked only past six rows). The queue shows up next with shuffle and repeat.
  Bluetooth audio plays a phone over A2DP with AVRCP track data. Video plays only while
  Parked and stops on Moving. Setup, integrations, settings and widgets are in 80-h.
---

# 80-g — Media app pages and the Moving media template

Shared rules are in [80-a](80-hu-a-overview.md). **Spec:** the approved head-unit apps
spec covers the Media app ([head-unit apps §5][hu-5]): local and USB library, Bluetooth
audio, later streaming (internet radio, podcasts, AirPlay and UPnP only, decided item 39)
and later video, Parked or passenger-only. Its pages are New.

### media-moving — Media template while Moving (Radio, Media, Bluetooth, streaming)  [New]
- **Purpose:** the one driver-safe frame for anything that plays, drawn by the OS from the
  playing app's data.
- **Owner:** os (template); app:media, app:radio and streaming integrations fill it
- **Opens from → goes to:** any media page when the car starts Moving; the media pane on a
  Drive home page (`drive-split-split`); the now-playing widget. Tap on the browse button
  → one `short_list`; Back → the Drive home page.
- **Layout classes:** phone · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night-dim Moving
  media; hu5 Night-dim Moving; huwide Night-dim Moving as the third column; hu7 Night-dim
  Moving radio variant.
- **Content (top to bottom):**
  1. Static artwork (square, `radius-md`), or the station logo, or the source icon.
  2. Title ≤ 30 characters, `type-title` ≥ 24 px ("Wonderwall"); artist ≤ 30 characters
     ("Oasis"); radio shows station name as the title and RadioText Plus artist if present.
  3. Source word and icon: "Media · USB", "Bluetooth · Pixel 8", "Radio · DAB".
  4. Controls (76 px targets): `skip_previous`, `play_pause`, `skip_next`, `volume_up`;
     radio maps skip to Seek or to the next preset (setting in `radio-settings`).
  5. One `list` button "Browse" → a `short_list` of ≤ 6 rows: Recent, Favourites,
     Playlists (one level), or the radio presets.
  6. Progress: elapsed time as text only on Parked; while Moving no progress bar animation,
     only "2:31 / 4:18" updating at ≤ 1 Hz.
- **States:** nothing playing: "Nothing playing" with **Play** (resumes the last source).
  Source lost: "Bluetooth disconnected" with the source icon. Loading: artwork placeholder
  (`surface-3`). Passenger view: no change; not a driving item. Parked: the app's full page
  replaces the template.
- **Safety and driving rules:** title and artist ≤ 30 characters each, static artwork,
  play or pause, skip, volume; no lyrics, no video, no browsing beyond one `short_list`; no
  animation, glow or gradient ([UI §12.1][ui-12.1], [App model §4.4][am-4.4]). Artwork that
  changes more often than once per track is replaced by the source icon. Every task ≤ 3
  screens and back to the Drive home page.
- **Components:** `media` template, `short_list` template, Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §5.6][dm-5.6] · [Drive modes §9][dm-9]
  · [research: template limits][dd-7.2].
- **Open questions:** should artwork show at all on HU-5 while Moving, where it costs the
  title its width? Recommend: hide artwork below HU-7.

### media-now-playing — Media: now playing  [New]
- **Purpose:** what is playing, with full controls, when parked.
- **Owner:** app:media
- **Opens from → goes to:** app drawer → Media; the now-playing widget; `audio-sources`.
  Goes to `media-browse`, `media-queue`, `media-video` (a video file), `media-settings`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; hu9 Night Parked with the queue beside; phone Day.
- **Content (top to bottom):**
  1. Source chip ("USB stick", "Network share · NAS", "Bluetooth · Pixel 8").
  2. Artwork, large (left on head units, top on phone).
  3. Title, artist, album, year; format chip "FLAC 44.1 kHz" (Parked, `type-caption`).
  4. **Scrubber** with elapsed and remaining time.
  5. Controls: `shuffle`, `skip_previous`, `play_pause`, `skip_next`, `repeat`; `volume_up`;
     `favorite` "Like".
  6. Row: `queue_music` "Up next" (2 rows preview), `library_music` "Browse", `equalizer`
     "Sound" (opens `audio-sound`).
- **States:** empty library: "No music yet · add a USB stick or a network share" →
  `media-setup`. Loading: artwork placeholder. Error: "Can't read this file · skipped".
  Offline: network-share tracks greyed "Share not reachable". Moving: `media-moving`.
- **Safety and driving rules:** the full page is Parked only on driver-facing displays; the
  Scrubber is Parked only.
- **Components:** Chip, Scrubber, Button, ListRow, Card.
- **Spec refs:** [UI §12.1][ui-12.1] · [visual §8][vds-8] · [head-unit apps §5][hu-5].
- **Open questions:** none.

### media-browse — Browse (local, USB, network shares)  [New]
- **Purpose:** find and play music by folder, artist, album, genre or playlist.
- **Owner:** app:media
- **Opens from → goes to:** `media-now-playing` → Browse. A track plays and returns to now
  playing; a video opens `media-video`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked albums grid; hu7 Night-dim Moving `short_list`.
- **Content (top to bottom):**
  1. **Location** chips: This device · USB stick · SD card · Network share "NAS · Music"
     (each only when present).
  2. TabBar: Artists · Albums · Songs · Playlists · Folders · Genres.
  3. **Search** (Parked only) and an A–Z jump bar on the right edge.
  4. List or grid: album Cards with artwork and title, or ListRows (title, artist, length).
  5. Actions on a row: Play, Play next, Add to queue, Add to playlist.
- **States:** USB stick indexing: "Reading USB stick · 640 of 1,204". USB removed: "USB stick
  removed" and its tracks leave the queue. Network share offline: "NAS not reachable · last
  seen 2 days ago". Moving: a `short_list` (≤ 6 rows, ≤ 30 characters, one level) of Recent
  and Playlists; no tabs, no search, no A–Z.
- **Safety and driving rules:** browsing beyond a `short_list` is Parked only
  ([UI §12.1][ui-12.1]); no typing while Moving.
- **Components:** Chip (filter), TabBar, TextField (new component), Card, ListRow,
  `short_list` template.
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §3.5][ui-3.5] · [head-unit apps §5][hu-5].
- **Open questions:** network shares need a password stored on the Brain; which store (the
  OS secrets store, by name)?

### media-queue — Queue  [New]
- **Purpose:** the play queue with shuffle and repeat.
- **Owner:** app:media
- **Opens from → goes to:** `media-now-playing` → Up next. Back.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu9
  Night as a side panel; phone Day.
- **Content (top to bottom):** 1. Now playing row (pinned). 2. "Up next" ListRows with a
  drag handle and remove. 3. **Clear queue**, **Save as playlist**. 4. Shuffle and repeat
  Segmented: Off · All · One.
- **States:** empty: "Queue is empty". Moving: locked; the template's skip is the only
  queue control.
- **Safety and driving rules:** Parked only on driver-facing displays.
- **Components:** ListRow, Segmented, Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [head-unit apps §5][hu-5].
- **Open questions:** none.

### media-bluetooth — Bluetooth audio  [New]
- **Purpose:** play and control a phone's audio (A2DP) with its track data (AVRCP).
- **Owner:** app:media
- **Opens from → goes to:** `audio-sources` → Bluetooth; `media-now-playing` source chip.
  Goes to the Phone app's pairing page by name (`phone-pairing`).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked playing; hu7 Night no phone.
- **Content (top to bottom):** 1. Phone name and battery chip ("Pixel 8 · 64 %").
  2. Artwork if the phone sends it (AVRCP cover art), else `bluetooth_audio`. 3. Title,
  artist, album, the app on the phone if sent. 4. Controls the phone allows (AVRCP):
  previous, play or pause, next; a Scrubber only if the phone reports position. 5. **Browse
  the phone** (AVRCP browsing, Parked) when supported. 6. **Switch phone** list of paired
  phones.
- **States:** no phone: "No phone connected · Connect" with the paired list and **Pair a
  phone**. Phone connected for calls only: "Pixel 8 is connected for calls. Turn on media
  audio on the phone." Metadata missing: "Bluetooth audio" as the title. Moving:
  `media-moving`.
- **Safety and driving rules:** pairing is the Phone app's, Parked only, numeric comparison
  ([Phone §13][pc-13]); A2DP sink is a role the owner enables there.
- **Components:** Chip (status), Button, ListRow, Scrubber.
- **Spec refs:** [Phone §3][pc-3] · [Phone §13][pc-13] · [UI §12.1][ui-12.1] · [head-unit apps §5][hu-5].
- **Open questions:** **Decided ([head-unit apps §5][hu-5]):** one pairing covers calls and
  media; it lives on the Phone app's pairing page, with a "Media audio" switch per phone.

### media-video — Video player (Parked only)  [New]
- **Purpose:** play a local or shared video file.
- **Owner:** app:media
- **Opens from → goes to:** `media-browse` → a video file. Back to browse.
- **Layout classes:** tablet · desktop · hu7 · hu9 · huwide · phone. **Draw first:** hu9
  Night Parked playing; hu9 Night-dim the moment Moving starts.
- **Content (top to bottom):** full-bleed video; controls on tap: Scrubber, play or pause,
  10 s back and forward, subtitles, audio track, **Exit**.
- **States:** Moving starts: video stops within one frame, the screen shows "Video stops
  while driving" with the sound paused, then returns to the Drive home page; resumes
  only on Parked by tapping **Resume**. Unsupported file: "Can't play this format".
- **Safety and driving rules:** no video on any driver-facing display while Idling without
  Park evidence or Moving, Passenger view included ([UI §12.1][ui-12.1],
  [reg 109][dd-4.2]); the OS, not the app, stops it. A passenger-only display declared in
  the install configuration may keep playing.
- **Components:** Scrubber, Button, locked view.
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §3.5][ui-3.5] · [research reg 109][dd-4.2] · [head-unit apps §5][hu-5].
- **Open questions:** keep the audio of a video playing while Moving? Recommend no.

[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-5.6]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#56-split--media
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[pc-13]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#13-security
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[dd-7.2]: ../../../research/driver_distraction_rules.md#72-template-limits-recommended
[hu-5]: ../../../../specs/2026-10-07-head-unit-apps-design.md#5-media
