---
title: "Designer brief 80-b — Radio app: now playing, stations, tuning, presets, DAB slideshow, traffic interrupt"
area: references
status: draft
version: 0.3
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, references/research/driver_distraction_rules.md]
summary: >
  The Radio app's main pages (app:radio). Now playing for FM, AM and DAB+ with RDS (station
  name, RadioText, programme type, traffic and alternative-frequency flags) and the DAB DLS
  line; the station list with logos and the DAB service list; tune, seek and scan with a
  frequency scale; presets with recall and save; the DAB slideshow (Parked only); and the
  traffic announcement interrupt, which goes through the OS alert pipeline. Each block says
  what the Moving `media` template keeps and what becomes Parked only. Setup, settings and
  widgets are in 80-c. Amended 2026-10-07 (openness round, ADR-0047): style notes are the default look and stale rules (fixed safety looks, unremovable anchors, no app chips, no emoji icons, calls never recorded) follow the amended specs; safety rules unchanged.
---

# 80-b — Radio app pages

Shared rules (Moving template, Parked-only long lists, no video) are in
[80-a](80-hu-a-overview.md). **Spec:** the approved head-unit apps spec covers the Radio
app ([head-unit apps §3][hu-3]), so these pages are New, except the traffic announcement
card, which differs from the spec (see its block). Examples use
UK broadcasts the D2 owner can receive. Every page is driver-facing on head units.

### radio-now-playing — Radio: now playing  [New]
- **Purpose:** show the station on air and give band, preset, seek and volume in one place.
- **Owner:** app:radio
- **Opens from → goes to:** app drawer → Radio; the now-playing widget; `audio-sources` →
  Radio; the Drive home page's media pane (Parked). Goes to `radio-stations`, `radio-tune`,
  `radio-presets`, `radio-dab-slideshow`, `radio-settings`.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked DAB; hu7 Night-dim Moving (the `media-moving` frame); hu5 Night FM; phone Day as a
  remote.
- **Content (top to bottom):**
  1. **Band** Segmented: FM · AM · DAB (only bands the tuner supports).
  2. **Station block:** logo (static, 1:1, `radius-md`) or a band icon (`radio`) if none;
     station name in `type-title` ("BBC Radio 2"); second line: frequency "89.1 FM" or the
     DAB ensemble and block "BBC National DAB · 12B".
  3. **Info line:** RadioText or DAB DLS as one static line, ≤ 2 lines Parked; when RadioText
     Plus tags exist it splits into title and artist ("Wonderwall · Oasis").
  4. **Chips (status):** PTY ("Pop music"), **TA** (on or off), **AF** (following), signal
     bars with a word ("Strong", "Weak"), "Stereo" or "Mono", DAB bitrate "128 kbit/s"
     (Parked).
  5. **Transport row:** `skip_previous` "Seek down", `play_pause` (mute or stop), `skip_next`
     "Seek up", `volume_up` volume, `star` "Save preset".
  6. **Preset strip:** six preset buttons P1–P6 with logo and short name; long-press saves.
  7. **Secondary row:** `list` "Stations", `tune` "Tune", `image` "Slideshow" (DAB, Parked),
     `settings` "Settings".
- **States:** loading: "Tuning…" with the target frequency. No tuner: Card "No radio
  tuner found · Set up a tuner" → `radio-setup-tuner`. Weak signal: "Weak signal" chip in
  `warn`, audio may mute; DAB drop-out: "Signal lost · trying FM" when the same station has
  an FM link. Offline: no change (radio needs no internet); logos missing show the band icon.
  No vehicle: works the same. Parked and Idling: full page. Moving: the `media-moving`
  frame; presets as a `short_list`. Passenger: no extra content (not a driving item). Locked:
  n/a.
- **Safety and driving rules:** RadioText and DLS never scroll or animate (auto-scrolling
  text is a per se lockout, [NHTSA lockouts][dd-3.2]); while Moving the info line shows only
  RadioText Plus title and artist, ≤ 30 characters each, or nothing ([UI §12.1][ui-12.1]).
  Seek, preset recall and volume are allowed while Moving.
- **Components:** Segmented, HeroStat (station name variant), Chip (status), Button,
  PresetButton (new component), Card.
- **Spec refs:** [UI §12.1][ui-12.1] · [App model §4.4][am-4.4] · [visual §4][vds-4] · [head-unit apps §3][hu-3].
- **Open questions:** whether to show the PTY chip while Moving (it is equipment state, but
  it is a third line).

### radio-stations — Station list and DAB service list  [New]
- **Purpose:** pick a station from what the tuner can hear now, with logos.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-now-playing` → Stations. A row tunes and returns to
  now playing. Goes to `radio-presets` (long-press → Save as preset).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked DAB list; hu7 Night-dim Moving (`short_list`); hu5 Night.
- **Content (top to bottom):**
  1. Tabs (TabBar): **All** · **DAB** · **FM** · **AM** · **Favourites**.
  2. Filter chips (Parked): PTY ("News", "Pop music", "Classical"), **Local** (strong only).
  3. **Search** field (Parked only): "Search stations".
  4. List of ListRows: logo, station name, meta ("BBC National DAB · 12B" or "93.5 FM"),
     signal word, trailing `star` for Favourites. DAB rows group by ensemble on HU-9 and
     HU-wide (Parked).
  5. Footer: "Last scan 14:02 · 43 stations" and **Scan again** (Parked).
- **States:** empty: "No stations yet · Scan" (button → `radio-setup-scan`). Loading: "Scanning
  DAB · block 11D of 13F" with a progress bar. Error: "The tuner stopped responding · Restart
  tuner". Moving: only Favourites (≤ 6 rows, ≤ 30 characters) in a `short_list`, one level,
  no search, no filters. Offline: logos fall back to the band icon.
- **Safety and driving rules:** the full list, search and filters are Parked only; the
  Moving list is the six Favourites or, if none, the six presets ([UI §12.1][ui-12.1]).
- **Components:** TabBar, Chip (filter), TextField (new component), ListRow, Button,
  `short_list` template.
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §3.5][ui-3.5] · [visual §8][vds-8] · [head-unit apps §3][hu-3].
- **Open questions:** logos come from broadcaster metadata (DAB SLS logos, RadioDNS lookups);
  the RadioDNS lookup needs internet and sends the station ID. Off by default?

### radio-tune — Tune, seek and scan  [New]
- **Purpose:** move across the band by step, seek or scan.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-now-playing` → Tune. Back to now playing.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked FM; hu5 Night.
- **Content (top to bottom):**
  1. Big frequency in `type-hero` "97.6" with unit "MHz" (AM "1089 kHz"; DAB "Block 12B").
  2. **FrequencyScale** (new component): a horizontal band 87.5–108.0 MHz with ticks; found
     stations as small markers; a draggable needle (Parked); no glow in the default look.
  3. Buttons: `chevron_left` "Step down", `chevron_right` "Step up" (0.1 MHz FM, 9 kHz AM,
     one block DAB), `fast_rewind` "Seek down", `fast_forward` "Seek up".
  4. **Scan** Button: plays 5 s of each found station; **Stop scan** while it runs.
  5. **Save to preset** Button.
- **States:** seeking: "Seeking up…"; no station found after a full sweep: "No stations
  found · check the antenna" → `radio-setup-antenna`. DAB: steps are blocks, not MHz.
  Moving: this page is locked; seek stays in the `media` template's skip buttons.
- **Safety and driving rules:** manual tuning is the NHTSA baseline task, not a driving
  task; the page is Parked only on driver-facing displays ([NHTSA][dd-3.2]); seek up or down
  is allowed while Moving through the template.
- **Components:** HeroStat, FrequencyScale (new component), Button, locked view.
- **Spec refs:** [UI §12.1][ui-12.1] · [UI §3.5][ui-3.5] · [head-unit apps §3][hu-3].
- **Open questions:** none.

### radio-presets — Presets  [New]
- **Purpose:** see, recall, save, reorder and clear presets across bands.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-now-playing` (preset strip, long-press); the presets
  widget; `radio-stations` (Save as preset). Back to now playing.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night-dim Moving `short_list`.
- **Content (top to bottom):**
  1. Title "Presets" and a **Mixed bands** note ("Presets can hold FM, AM and DAB").
  2. Grid of 12 PresetButtons (P1–P12): logo, short name ≤ 12 characters ("Radio 4",
     "Classic FM"), band word; an empty slot reads "Empty · Hold to save".
  3. Edit row (Parked): **Reorder** (drag), **Rename**, **Clear** (per preset).
  4. **Fill from strongest** Button (Parked): saves the six strongest stations.
- **States:** empty: all slots empty with one Card "Save your first station: hold a preset
  on the radio screen". A preset whose station is out of range: greyed "Not receivable
  here". Moving: P1–P6 as a `short_list` (≤ 6 rows); recall only.
- **Safety and driving rules:** recall is allowed while Moving; save, rename, reorder and
  clear are Park to edit ([Drive modes §8.1][dm-8.1]).
- **Components:** PresetButton (new component), ListRow, Button, `short_list` template.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] · [head-unit apps §3][hu-3].
- **Open questions:** presets per user profile or per car? Recommend per car and profile.

### radio-dab-slideshow — DAB slideshow and DLS  [New]
- **Purpose:** show the station's slideshow and full text when parked.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-now-playing` → Slideshow. Back to now playing.
- **Layout classes:** tablet · hu7 · hu9 · huwide · phone. **Draw first:** hu9 Night
  Parked; hu7 Night-dim Moving (locked view).
- **Content (top to bottom):** 1. Slide image, 4:3 or 16:9, letterboxed on `bg`. 2. DLS
  text in full, two lines, static. 3. Station name and time of the last slide ("Updated
  14:05"). 4. **Save image** (to the owner's device; Parked).
- **States:** no slideshow: "This station sends no pictures". Loading: still logo. Moving:
  locked view "Available when parked", with **Open on phone**; the `media` template shows
  the static logo only.
- **Safety and driving rules:** slides change on their own, so they are a non-driving
  moving image; Parked only on driver-facing displays; never in Passenger view
  ([UI §12.1][ui-12.1], [reg 109][dd-4.2]).
- **Components:** Card, Button, locked view.
- **Spec refs:** [UI §12.1][ui-12.1] · [driver-distraction research §4.2][dd-4.2] · [head-unit apps §3][hu-3].
- **Open questions:** none.

### radio-ta-alert — Traffic announcement interrupt  [Proposed]
- **Why the app needs it:** TA (RDS) and DAB announcements interrupt media with local
  traffic news. **Why still Proposed:** the approved spec turns TA off by default and shows
  a small chip, never a card with text ([head-unit apps §3][hu-3]); this card needs the
  owner's yes or a redraw as the chip.
- **Purpose:** tell the driver a traffic bulletin is playing and let them skip it.
- **Owner:** os (the alert pipeline draws it); app:radio raises it
- **Opens from → goes to:** raised by the tuner when TA is on and a bulletin starts, from any
  source or app. Ends back where the driver was.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving over the Dashboard home page; hu5 Night.
- **Content (top to bottom):** an `alert_card`: icon `traffic`, line 1 "Traffic news"
  (≤ 30 characters), line 2 the station "BBC Radio Derby"; buttons **Skip** and **Turn off
  TA**. The bulletin plays at the TA volume set in `audio-volume-rules`; media pauses.
- **States:** bulletin ends: the card leaves and the source resumes. A call, navigation
  voice or a red alarm is active: TA waits (rule 7 in [80-a](80-hu-a-overview.md)); a
  bulletin older than 2 minutes is dropped. TA on but no TA station: chip "No traffic
  station" on now playing.
- **Safety and driving rules:** one card, two buttons, ≤ 2 lines of ≤ 30 characters; never
  covers a red telltale, the reverse camera, a call or a navigation manoeuvre prompt
  ([UI §12.1][ui-12.1]). The card is OS-drawn; the app cannot style it.
- **Components:** `alert_card` template, Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [App model §4.4][am-4.4].
- **Open questions:** does TA count toward the alert rate limits that message cards use?
  Recommend no; it is audio-led and rare.

[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[vds-4]: ../../../../specs/2026-10-07-visual-design-system-design.md#4-type
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[dd-3.2]: ../../../research/driver_distraction_rules.md#32-numbers-and-lockouts
[hu-3]: ../../../../specs/2026-10-07-head-unit-apps-design.md#3-radio
