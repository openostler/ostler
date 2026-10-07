---
title: "Designer brief 80-f — Audio app: first-run setup (install shape, output device, channels, speaker test), settings and widgets"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, specs/2026-10-07-phone-comms-addon-design.md, references/research/hardware.md, references/research/canbus_headunit.md]
summary: >
  The Audio app's first-run setup and settings (app:audio). Setup asks whether Ostler is the
  head unit or sits beside one, picks the output device (the CarPiHAT PRO 5 DAC, an I²S DAC
  HAT, a USB DAC, or an external DSP over USB or Bluetooth), maps channels to the car's
  speakers (front, rear, subwoofer, tweeters) and runs a speaker test with levels. Settings
  hold the device, the channel map, per-profile sound, and reset. The end lists the widgets
  Audio adds to the widget picker gallery (volume, sound profile, source) with their setup
  options and Moving behaviour.
---

# 80-f — Audio setup, settings and widgets

The approved head-unit apps spec covers the two setups and the output hardware
([head-unit apps §1][hu-1], [§4][hu-4]), so these pages are New. Setup is Parked only on driver-facing
displays and can run from a phone linked to the car. Each step has **Back**, **Next** and
**Set up later**.

## Setup flow (first run)

| Step | Screen | What the user does | What can fail, and the recovery |
|---|---|---|---|
| 1 | `audio-setup-shape` | Chooses "Ostler is the head unit" or "beside my head unit" | — (changeable later) |
| 2 | `audio-setup-output` | Picks the output device the Brain found | None found: wiring help; DSP not paired: pair again |
| 3 | `audio-setup-channels` | Maps each output to a speaker | Fewer outputs than speakers: suggests a 2- or 4-channel map |
| 4 | `audio-setup-test` | Plays a tone on each speaker, sets levels | A speaker is silent: "Check wiring" with the channel named |
| 5 | `audio-sound` | Lands on Sound with the Flat preset | — |

"Beside my head unit" skips steps 2–4: the old unit keeps sound; Audio shows only
`audio-system-sounds` routing and a note that EQ lives on the old unit.

### audio-setup-shape — Setup 1: install shape  [New]
- **Purpose:** decide who makes the sound in this car.
- **Owner:** app:audio
- **Opens from → goes to:** first open of Audio, Radio or Media; `audio-settings` → Install
  shape. Goes to `audio-setup-output` or ends.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):** 1. StepProgress "1 of 4 · Install". 2. Two large choice
  Cards: **"Ostler sits beside my head unit"** (preselected: "Your head unit keeps radio
  and music; Ostler shows car data and cameras") and **"Ostler is the head unit"**
  (offered, never the default, item 55: "Ostler plays radio, media and calls through your
  amplifier"). 3. A small line: "Calls follow the Phone app's
  hands-free choice" linking to Phone settings by name. 4. **Next**.
- **States:** a phone set as hands-free elsewhere: the note names it. Moving: locked view.
- **Safety and driving rules:** Parked only.
- **Components:** StepProgress (new component), Card (choice), Button.
- **Spec refs:** [Phone §3][pc-3] · [UI §1][ui-1] · [head-unit apps §1][hu-1].
- **Open questions:** **Decided (item 55):** "Ostler is the head unit" is offered, not the
  default; "Ostler sits beside my head unit" is preselected.

### audio-setup-output — Setup 2: output device (DAC or DSP)  [New]
- **Purpose:** choose and check the device that carries sound to the amplifier.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-setup-shape`; `audio-settings` → Output → Change. Goes to
  `audio-setup-channels`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. StepProgress "2 of 4 · Output".
  2. The audio path diagram card ([80-a](80-hu-a-overview.md#the-audio-path-draw-once-reuse-in-setup)),
     with the chosen device highlighted.
  3. "Found on the Brain" ListRows, each with channel count and what Ostler controls:
     - "CarPiHAT PRO 5 DAC · 2 channels · EQ on the Brain".
     - "I²S DAC HAT · 2 or 8 channels · EQ on the Brain".
     - "USB audio device · 2–8 channels · EQ on the Brain".
     - An external DSP is not supported in v1 (item 37): a found one shows "External DSP ·
       not supported yet · sound passes through flat".
  4. **Play a test sound** (secondary): 2 s at a safe level.
  5. **Next** (primary).
- **States:** none found: "No audio output found. Fit a DAC HAT or plug in a USB DAC." with
  **Show options** (the Store). DSP found but unsupported: "Ostler can't control this DSP;
  sound will pass through flat". DSP over Bluetooth drops: "DSP disconnected · reconnecting".
  Brain asleep: "Needs the Brain" with **Wake**. Moving: locked view.
- **Safety and driving rules:** Parked only; test sound capped (−20 dBFS).
- **Components:** StepProgress (new component), Card, ListRow, Button.
- **Spec refs:** [hardware research][hw] · [head-unit research B4][ch-b4] · [head-unit apps §4][hu-4].
- **Open questions:** **Decided (item 37):** v1 is a software DSP on the Brain; an external
  DSP board comes later as a `device` integration, so no external DSP is supported first.

### audio-setup-channels — Setup 3: channel map  [New]
- **Purpose:** map outputs to speakers and speaker types.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-setup-output`; `audio-settings` → Channels. Goes to
  `audio-setup-test`.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** hu7
  Night 4-channel; hu9 Night 6-channel.
- **Content (top to bottom):**
  1. StepProgress "3 of 4 · Speakers".
  2. **Layout** Segmented: 2 channels (front) · 4 (front and rear) · 4 + sub · 6 + sub
     (front tweeters and woofers).
  3. **SeatMap** (new component) with numbered speaker marks.
  4. Table: Output 1 → "Front right · Full range" (Segmented type: Full range · Woofer ·
     Tweeter · Subwoofer), Output 2 → "Front left", and so on.
  5. Suggested crossover note: "Tweeters get a 3.5 kHz high-pass by default".
  6. **Next**.
- **States:** fewer outputs than the layout: the extra rows say "Not connected". Moving:
  locked view.
- **Safety and driving rules:** Parked only; tweeter rows get a default high-pass that the
  owner must turn off on purpose.
- **Components:** StepProgress (new component), Segmented, SeatMap (new component),
  ListRow, Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### audio-setup-test — Setup 4: speaker test and levels  [New]
- **Purpose:** hear each speaker in turn and match levels.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-setup-channels`; `audio-settings` → Speaker test. Goes to
  `audio-sound`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night mid-test.
- **Content (top to bottom):** 1. StepProgress "4 of 4 · Test". 2. SeatMap with the playing
  speaker marked and the word "Playing: Front right". 3. Per speaker: **Heard it** and
  **Silent** Buttons, level trim ±6 dB. 4. **Measure levels with the phone** (optional,
  phone microphone at the driver's head). 5. **Finish**.
- **States:** "Silent" pressed: "Check the wire for Output 1 (Front right) and the amp
  channel", **Retry**. Moving: locked view.
- **Safety and driving rules:** Parked only; pink noise at a capped level.
- **Components:** StepProgress (new component), SeatMap (new component), Button, Slider
  (new component).
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4].
- **Open questions:** none.

### audio-settings — Audio settings  [New]
- **Purpose:** the Audio app's own options.
- **Owner:** app:audio
- **Opens from → goes to:** `audio-sound` → Settings; App info → Settings. Goes to the setup
  steps.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. **Install shape** row with Change. 2. **Output** device
  row ("CarPiHAT PRO 5 DAC · 2 channels") with Change and a status chip. 3. **Channels**
  and **Speaker test** rows. 4. **Sound per profile** Toggle ("Each driver has their own
  EQ and balance"). 5. **Export all sound settings** and **Import**. 6. **Reset audio to
  flat** (danger, confirm).
- **States:** device offline: status chip `warn` "Offline". Not owner: device rows read
  only. Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** ListRow, Chip (status), Toggle (new component), Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §4][hu-4] · [app UI model §5][ua-5].
- **Open questions:** none.

## Audio widgets (in the widget picker gallery)

- **Volume** — a large volume control with mute. Sizes: small, medium. Setup options:
  show the level number; step size 1 or 2. **Moving:** allowed (equipment state) as the
  volume control in the `media` template.
- **Sound profile** — the active EQ preset as a chip; tap opens the preset `short_list`.
  Size: small. Setup options: which presets to cycle (≤ 6). **Moving:** a `short_list`.
- **Source** — the active source icon and word; tap cycles or opens the source list. Size:
  small. Setup options: tap cycles, or tap opens the list. **Moving:** a `short_list`.
- **Shortcuts:** "Audio" app shortcut; Drive menu rows "Mute" and "Next source" (allowed
  while Moving; app-model §15.3).

[ui-1]: ../../../../specs/2026-10-06-ui-architecture-design.md#1-context-and-goals
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[hw]: ../../../research/hardware.md#development-kit-recommended-parts-250-plus-the-pi
[ch-b4]: ../../../research/canbus_headunit.md#b4-steering-wheel-reverse-cameras-amplifier
[hu-1]: ../../../../specs/2026-10-07-head-unit-apps-design.md#1-context-and-the-two-setups
[hu-4]: ../../../../specs/2026-10-07-head-unit-apps-design.md#4-audio
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
