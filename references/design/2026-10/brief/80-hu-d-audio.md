---
title: "Designer brief 80-d — Audio app: sources, sound, graphic and parametric EQ, presets, balance and fade"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-phone-comms-addon-design.md]
summary: >
  The Audio app's everyday pages (app:audio). Sources lists every sound source (Radio, Media
  files, Bluetooth, Projection, AUX) and switches between them. Sound is the hub with
  loudness, bass boost and tone, and links to the tuning pages. The graphic EQ has 10, 15 or
  31 bands; the parametric EQ has bands with frequency, gain and Q on a curve; EQ presets save,
  load and share curves. Balance and fade use a top-down seat diagram of the right-hand-drive
  Discovery 2. While Moving, only source switch and volume are allowed; every tuning page is
  Park to edit.
---

# 80-d — Audio app: sources, sound, EQ, balance

**Why the Audio app needs these pages (all Proposed):** the owner's direction of 2026-10-07
makes Ostler the head unit, so it owns the sound: source switching, EQ and DSP. No approved
spec covers it. Processing runs on the Brain (PipeWire filter chains) or on an external DSP
the app controls; the pages are the same either way. The car is a right-hand-drive
Discovery 2, so the driver's seat is drawn on the **right**.

### audio-sources — Sources  [Proposed]
- **Why the app needs it:** the head unit's "Source" button; one place to switch what plays.
- **Purpose:** choose the active sound source.
- **Owner:** app:audio
- **Opens from → goes to:** app drawer → Audio → Sources; the Source button on the media
  widget; a steering-wheel "Source" key (cycles, no page). Goes to the source's app
  (`radio-now-playing`, `media-now-playing`, `media-bluetooth`, `projection-session`).
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7 Night
  Parked; hu7 Night-dim Moving (`short_list`).
- **Content (top to bottom):** a grid of source Cards (icon + word + one meta line), the
  active one with the `accent-soft` fill:
  1. `radio` **Radio** — "BBC Radio 2 · 89.1 FM".
  2. `library_music` **Media** — "USB stick · 1,204 tracks".
  3. `bluetooth_audio` **Bluetooth** — the phone's name, "Connected".
  4. `cast` **Projection** — "Android Auto" or "CarPlay" (only if set up).
  5. `settings_input_component` **AUX in** (only if the output device has an input).
  6. `podcasts` streaming integrations as their own Cards (one per integration).
- **States:** a source with no device: Card greyed with the reason ("No tuner", "No phone
  connected"). Only one source: the page shows it and a "Add a source" link to the Store.
  Moving: a `short_list` of available sources (≤ 6 rows, ≤ 30 characters), tap switches.
- **Safety and driving rules:** switching sources is allowed while Moving (equipment state);
  the page grid is Parked only ([UI §12.1][ui-12.1]).
- **Components:** Card, `short_list` template.
- **Spec refs:** [UI §12.1][ui-12.1].
- **Open questions:** none.

### audio-sound — Sound (loudness, bass, tone)  [Proposed]
- **Why the app needs it:** the quick sound page every unit has, above the expert pages.
- **Purpose:** the simple sound controls and the way into tuning.
- **Owner:** app:audio
- **Opens from → goes to:** app drawer → Audio (its home page). Goes to `audio-eq-graphic`,
  `audio-eq-parametric`, `audio-balance-fade`, `audio-crossover`, `audio-time-alignment`,
  `audio-subwoofer`, `audio-volume-rules`, `audio-settings`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; phone Day.
- **Content (top to bottom):**
  1. **Sound profile** chip row: the active EQ preset ("Flat", "Speech", "Off-road cabin",
     custom names) → `audio-eq-presets`.
  2. **Bass** and **Treble** Sliders (new component), −12 to +12 dB, 1 dB steps, centre
     detent, value shown "+3 dB".
  3. Toggle **Loudness** with a level Segmented: Low · Mid · High.
  4. Toggle **Bass boost** with a level Slider 0–10 and a centre frequency Segmented: 60 ·
     80 · 100 Hz.
  5. **Tuning** list (ListRows with chevrons): Equaliser · Balance and fade · Crossover ·
     Time alignment · Subwoofer · Volume rules.
  6. **Bypass all processing** Toggle (for comparing; off).
- **States:** no output device: Card "Set up audio output" → `audio-setup-output`. External
  DSP offline: "DSP not responding · settings will apply when it is back". Moving: locked
  view with only a **Volume** control and the active preset chip (switchable in a
  `short_list`).
- **Safety and driving rules:** Park to edit for every slider ([Drive modes §8.1][dm-8.1]);
  choosing an existing preset is allowed while Moving.
- **Components:** Chip, Slider (new component), Toggle (new component), Segmented, ListRow.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [visual §8][vds-8].
- **Open questions:** none.

### audio-eq-graphic — Graphic equaliser  [Proposed]
- **Why the app needs it:** a graphic EQ is standard on every aftermarket unit.
- **Purpose:** shape the sound with fixed bands.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Equaliser. Goes to `audio-eq-parametric`
  (Segmented switch), `audio-eq-presets`.
- **Layout classes:** tablet · desktop · hu7 · hu9 · huwide · phone. **Draw first:** hu9
  Night 31 bands; hu7 Night 10 bands; phone Day 10 bands (scrolls sideways).
- **Content (top to bottom):**
  1. Segmented **Graphic · Parametric**; Segmented **10 · 15 · 31 bands**.
  2. **Channel** Segmented: All · Front · Rear · Sub (per-channel EQ where the output allows).
  3. **EqBands** (new component): vertical faders at ISO centres (31 Hz to 16 kHz for 10
     bands), range ±12 dB, labels "31", "63" … "16k", the value above each fader on drag;
     a thin response line behind them in `text-2`, no glow.
  4. Row: **Preset** chip (name, "edited" mark), **Save as…**, **Reset to flat**, **Undo**.
  5. Note: "Cuts sound cleaner than boosts".
- **States:** clipping risk: a `warn` chip "Lower the boosts or the volume limit drops by
  4 dB" (the app lowers headroom automatically). DSP that has fewer bands: only its band
  counts are offered. Moving: locked view, "Available when parked".
- **Safety and driving rules:** Parked only on driver-facing displays.
- **Components:** Segmented, EqBands (new component), Chip, Button.
- **Spec refs:** [visual §8][vds-8] · [Drive modes §8.1][dm-8.1].
- **Open questions:** none.

### audio-eq-parametric — Parametric equaliser  [Proposed]
- **Why the app needs it:** for tuning a cabin properly (room modes, harsh peaks).
- **Purpose:** set each filter's frequency, gain, Q and type on a response curve.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-eq-graphic` (Segmented); `audio-setup-test` (measured
  correction). Back to `audio-sound`.
- **Layout classes:** tablet · desktop · hu9 · huwide · hu7. **Draw first:** hu9 Night;
  desktop Day.
- **Content (top to bottom):**
  1. **CurveEditor** (new component): log frequency axis 20 Hz–20 kHz, ±15 dB; the summed
     curve in `text-1`, each band a numbered handle (drag sets frequency and gain; pinch or
     the Q field sets width).
  2. Band table (ListRows, up to 10 bands per channel): number, Type Segmented (Peak · Low
     shelf · High shelf · High-pass · Low-pass), Frequency "120 Hz", Gain "−4.5 dB",
     Q "1.4", Toggle on or off.
  3. **Add band**, **Remove band**, **Channel** Segmented as in the graphic EQ.
  4. **Import filters** (a text file from a measurement tool; Parked).
- **States:** the output cannot do parametric bands: page hidden, the Segmented shows
  "Parametric needs the Brain or a DSP". Moving: locked view.
- **Safety and driving rules:** Parked only; number fields are text entry.
- **Components:** CurveEditor (new component), ListRow, Segmented, TextField (new
  component), Toggle (new component), Button.
- **Spec refs:** [visual §8][vds-8].
- **Open questions:** none.

### audio-eq-presets — EQ presets  [Proposed]
- **Why the app needs it:** drivers switch sound for speech, music or a loud gravel road.
- **Purpose:** pick, save, rename, share and delete sound profiles.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` profile chip; `audio-eq-graphic` → Preset. Back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; hu7 Night-dim Moving `short_list`.
- **Content (top to bottom):** 1. Built-in presets: Flat, Speech, Bass, Vocal, Loud cabin
  (diesel, road noise). 2. My presets with a small curve thumbnail, "Edited 3 Oct". 3.
  Per-source default rows: "Radio uses: Speech", "Media uses: Flat". 4. **Export** and
  **Import** as a file (Store "sound profiles" item later).
- **States:** empty My presets: "Save the current curve as a preset". Moving: a
  `short_list` of ≤ 6 presets; tap applies.
- **Safety and driving rules:** applying a preset is allowed while Moving; editing, rename
  and delete are Park to edit.
- **Components:** ListRow, Sheet, Button, `short_list` template.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1].
- **Open questions:** should sound profiles be a Store item type? Recommend yes, later.

### audio-balance-fade — Balance and fade  [Proposed]
- **Why the app needs it:** centre the sound on the driver or the whole cabin.
- **Purpose:** move the sound left, right, front and rear on a seat diagram.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Balance and fade. Goes to
  `audio-time-alignment` ("Tune for a seat").
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. **SeatMap** (new component): the D2 cabin from above in line art, driver on the right,
     two front seats, the rear bench, the two optional third-row seats greyed when not
     fitted; four speaker marks and a sub mark; a draggable point for the sound centre.
  2. Readouts: "Balance 2 R", "Fade 3 F"; step buttons `chevron_left`, `chevron_right`,
     `expand_less`, `expand_more` (D-pad friendly).
  3. Quick Chips: **Driver** · **Front** · **All seats** · **Centre**.
  4. **Rear speakers off when no rear passenger** Toggle (off).
- **States:** a channel not wired (set in setup): its speaker mark is hollow with "Not
  connected". Moving: locked view.
- **Safety and driving rules:** Park to edit; the quick Chips are not offered while Moving.
- **Components:** SeatMap (new component), Button, Chip, Toggle (new component).
- **Spec refs:** [Drive modes §8.1][dm-8.1].
- **Open questions:** draw a left-hand-drive variant now, or only when a LHD pack exists?

[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[vds-8]: ../../../../specs/2026-10-07-visual-design-system-design.md#8-charts-gauges-and-the-component-kit
