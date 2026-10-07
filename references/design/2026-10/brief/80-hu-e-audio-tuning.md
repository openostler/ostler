---
title: "Designer brief 80-e — Audio app: crossover, time alignment, subwoofer, volume rules and system sounds"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-phone-comms-addon-design.md]
summary: >
  The Audio app's expert tuning pages and the OS's system sound page. Crossover sets a
  high-pass and low-pass filter per channel with slope, drawn on one curve. Time alignment
  delays each speaker for a chosen listening position (driver, front, all) by measured
  distances on the Discovery 2 seat diagram. Subwoofer sets level, phase, low-pass and
  subsonic filter. Volume rules cover speed-dependent volume, start-up and maximum volume,
  per-source levels, ducking under navigation voice and calls, and the traffic announcement
  level. System sounds (OS) sets key beeps, chimes and alert sounds that no app can silence.
---

# 80-e — Audio tuning, volume rules and system sounds

The approved head-unit apps spec covers these pages ([head-unit apps §4][hu-4]), so they
are New, except System sounds. Crossover and time alignment come later, with multichannel
hardware (decided, item 37); v1 is a software DSP on the Brain. All tuning pages are **Parked only** on driver-facing displays.

### audio-crossover — Crossover  [New]
- **Purpose:** set high-pass and low-pass filters per output channel.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Crossover; `audio-setup-channels`. Back.
- **Layout classes:** tablet · desktop · hu7 · hu9 · huwide · phone. **Draw first:** hu9
  Night; phone Day.
- **Content (top to bottom):**
  1. **Channel** list on the left (HU) or a Segmented (phone): Front L · Front R · Rear L ·
     Rear R · Sub; **Link left and right** Toggle (on).
  2. **CurveEditor** (new component) in crossover mode: each channel's pass band as a
     filled shape in a `data` ramp colour, the selected one in `text-1`.
  3. **High-pass**: Toggle, Frequency Slider 20–500 Hz ("80 Hz"), Slope Segmented 12 · 18 ·
     24 dB/oct, Type Segmented Butterworth · Linkwitz-Riley.
  4. **Low-pass**: the same, 40 Hz–20 kHz.
  5. **Safety note** (warn token): "Tweeters need a high-pass. Running them full range can
     damage them." shown when a channel marked Tweeter has no high-pass.
- **States:** output with fixed crossovers: "Your amplifier sets the crossover" and read
  only. Moving: locked view.
- **Safety and driving rules:** Parked only; a change plays at −10 dB for 2 s, then ramps
  back, so a wrong filter cannot blast a speaker.
- **Components:** CurveEditor (new component), Slider (new component), Segmented, Toggle
  (new component), ListRow.
- **Spec refs:** [visual §8][vds-8] · [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### audio-time-alignment — Time alignment  [New]
- **Purpose:** delay each speaker so sound arrives together at one listening position.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Time alignment; `audio-balance-fade` → Tune
  for a seat. Back.
- **Layout classes:** tablet · desktop · hu7 · hu9 · huwide · phone. **Draw first:** hu9
  Night; hu7 Night.
- **Content (top to bottom):**
  1. **Listening position** Segmented: Driver · Front passenger · Front both · All seats ·
     Off.
  2. **SeatMap** (new component) with lines from each speaker to the chosen head position,
     each labelled with its distance.
  3. Table (ListRows): speaker, **Distance** "Front R 0.62 m", computed **Delay** "1.9 ms";
     edit by distance or by delay (Segmented: cm · ms).
  4. **Measure with the phone** Button: plays a click per speaker and times it with the
     phone's microphone at the head position (Parked; phone only).
  5. **Test** Button: plays pink noise through each speaker in turn.
- **States:** Off: delays 0, Front both uses a compromise. Measurement fails: "Too noisy
  · turn the engine off and try again". Moving: locked view; the position may be switched
  only through a saved preset.
- **Safety and driving rules:** Parked only; test sounds at a capped level (−20 dBFS).
- **Components:** Segmented, SeatMap (new component), ListRow, TextField (new component),
  Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** should Ostler hold measured speaker distances per vehicle in the
  pack's profile (D2 doors) as a starting point? Only with real measurements.

### audio-subwoofer — Subwoofer  [New]
- **Purpose:** blend the subwoofer with the main speakers.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Subwoofer. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. Toggle **Subwoofer** (only if a Sub channel is set up).
  2. **Level** Slider −15 to +15 dB. 3. **Phase** Segmented 0° · 180° (and a 0–180°
  Slider on DSPs that allow it). 4. **Low-pass** "80 Hz" (shared with `audio-crossover`).
  5. **Subsonic filter** "25 Hz" Toggle and Slider. 6. **Bass boost follows sub** Toggle.
- **States:** no sub channel: "No subwoofer set up · Set up channels". Moving: locked view;
  sub level is not a Moving control.
- **Safety and driving rules:** Parked only.
- **Components:** Toggle (new component), Slider (new component), Segmented.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### audio-volume-rules — Volume rules  [New]
- **Purpose:** set how volume behaves on its own.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Volume rules; `radio-settings` → TA volume.
  Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. **Speed-dependent volume:** Segmented Off · Low · Mid · High; a small line chart of
     "+ dB against speed" (0 to 110 km/h); source line "Speed from GPS" (or the pack's road
     speed when proven).
  2. **Start-up volume:** Toggle "Limit volume at start-up" with a Slider (level 12 of 40).
  3. **Maximum volume** Slider.
  4. **Per-source levels:** Radio, Media, Bluetooth, AUX, each ±6 dB, so a
     switch does not jump.
  5. **Ducking:** "Navigation voice lowers media by" Segmented 6 · 12 · 20 dB · Pause;
     "Calls" Segmented Pause · Lower 20 dB; "Message read-out" Segmented Pause · Lower.
  6. **Announcement levels:** Navigation voice, Traffic (TA), Calls, Message read-out, each
     with its own Slider and a **Test** Button.
- **States:** no speed source: speed volume greyed "Needs GPS or vehicle speed". Moving:
  locked view.
- **Safety and driving rules:** Park to edit. The priority order (alarm and reverse chime >
  calls > navigation > TA > read-out > media) is the OS's and is shown read only, not
  editable ([80-a rule 7](80-hu-a-overview.md)). Navigation voice and calls cannot be set
  below an audible floor.
- **Components:** Segmented, Slider (new component), Toggle (new component), area line chart
  (visual §8), Button.
- **Spec refs:** [visual §8][vds-8] · [Phone §3][pc-3] · [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### audio-system-sounds — System sounds  [Proposed]
- **Why the app needs it:** key beeps, chimes and alert tones need one owner, and safety
  tones must never be silenced by an app.
- **Purpose:** set the OS's own sounds.
- **Owner:** os (system Settings → Sound); the Audio app only routes them
- **Opens from → goes to:** system Settings → Sound (30-settings files); `audio-sound` →
  "System sounds". Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. **Key beeps** Toggle (off on head units by default) and level.
  2. **Mark chime** (when a Mark flag is taken) Toggle.
  3. **Message chime** (one short chime per alert card at most) Toggle and level.
  4. **Safety tones** (read only rows, with a lock icon and the word "Always on"): red fault
     telltale, alarm alert, reverse-camera chime, "Park to edit" refusal tone. Level Slider
     with a floor.
  5. **Voice** for read-outs: Segmented voice, speed, and **Test**.
  6. **Sound output for system sounds**: "Same as media" or "Driver's front speaker only".
- **States:** Audio app not installed: system sounds play through the default output; this
  page still works. Moving: locked view.
- **Safety and driving rules:** safety tones cannot be turned off; their level cannot go
  below the floor ([Drive modes §8.1][dm-8.1] "safety items move, never go").
- **Components:** ListRow, Toggle (new component), Slider (new component), Segmented,
  Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [UI §12.1][ui-12.1].
- **Open questions:** should the 30-settings brief own this page instead? It is drawn here
  because it shares the Audio app's components.

[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[hu-4]: ../../../../specs/2026-10-07-head-unit-apps-design.md#4-audio
