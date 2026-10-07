---
title: "Designer brief 80-l — Voice assistant and steering-wheel controls learning"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-shell-input-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, references/research/canbus_headunit.md]
summary: >
  Two input features of a head unit. The Voice app (app:voice) has the listening overlay
  (wake word or push-to-talk, no transcript while Moving), its setup flow (wake word,
  push-to-talk button, on-device speech download, privacy choices) and settings, with what
  voice may control: media, radio, volume, calls, navigation and Mark, never a car action.
  Steering-wheel controls learning (OS, input) is a wizard: pick the source (a resistor-ladder
  input on an I/O module, later, or a Bluetooth or USB wheel remote), learn each button
  by pressing it, then assign short and long presses to intents. It links to the Buttons
  pages in the hardware brief by name.
---

# 80-l — Voice and steering-wheel controls

**Spec:** the owner allowed voice on 2026-10-07 (decided, item 54): the shell input spec's
non-goal ([shell input §1][si-1]) is lifted, and the assistant is local-first and later. The
approved head-unit apps spec covers the Voice app ([head-unit apps §10][hu-10]) and
wheel-control learning in the OS ([head-unit apps §9][hu-9]), so these pages are New. The
D2 has no wheel buttons on its diagnostic K-line ([shell input §3.1][si-3.1]); its buttons
need a resistor-ladder input on an I/O module, later.

### voice-assistant — Voice assistant (listening)  [New]
- **Purpose:** listen for one request, confirm it aloud, and do it.
- **Owner:** app:voice (the listening overlay is drawn by the OS)
- **Opens from → goes to:** the wake word ("Hey Ostler", as chosen in setup); the
  push-to-talk wheel key or `mic` button on the Drive home page; the Drive menu row "Voice".
  Ends back where the driver was, ≤ 3 steps.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving listening; hu7 Night-dim Moving "Playing BBC Radio 2"; hu7 Night Parked
  with transcript.
- **Content (top to bottom):** a bottom card, `alert_card` size:
  1. `mic` icon with the word "Listening" (a static ring, no waveform animation while Moving).
  2. While Moving, no transcript; the answer is spoken and one line confirms the action
     ("Radio · BBC Radio 2", ≤ 30 characters).
  3. Buttons: **Cancel**; for anything that sends or calls, a read-back "Call Sam?" with
     **Yes** and **Cancel** (Cancel focused).
  4. Parked: the transcript and a "Try saying…" list: "Play Radio 4", "Next track",
     "Volume 15", "Call Sam", "Navigate home", "Mark this", "What faults are there?".
- **States:** not understood: "Didn't catch that" spoken and shown, one retry. Offline: local
  commands still work; "Needs the internet" only for an optional online service. Mic busy
  (in a call): voice refused with a tone. No app for the request: "Radio isn't installed".
- **Safety and driving rules:** no transcript while Moving (as AAOS
  `NO_VOICE_TRANSCRIPTION`, [UI §12.1][ui-12.1]); a spoken "yes" never counts as a
  confirmation for a gated action; voice never runs a car action, a Tier
  1–3 test or a disarm; reading faults aloud only reads (count and worst fault, "SLABS: right
  front wheel speed sensor, logged"). The card obeys `alert_card` limits.
- **Components:** `alert_card` template (voice variant, new component), Button, ListRow.
- **Spec refs:** [UI §12.1][ui-12.1] · [shell input §1][si-1] · [head-unit apps §10][hu-10].
- **Open questions:** a listening overlay is not one of the approved templates; it needs a
  platform proposal, or must fit `alert_card` exactly.

### voice-setup — Voice: first-run setup  [New]
- **Purpose:** turn on voice, local first, with clear privacy choices.
- **Owner:** app:voice
- **Opens from → goes to:** first open of Voice; `voice-settings` → Run setup again. Goes to
  `swc-assign` (by name, for the push-to-talk key) and `voice-assistant` (a test).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night step 2; phone Day.
- **Content (steps):**
  1. **Microphone**: pick the cabin mic (shared with the Phone app's hands-free mic) and a
     level test.
  2. **How to start listening**: Toggle "Wake word" (off by default) with a choice of
     phrases; Toggle "Push-to-talk button" (on) → binds a wheel key or button.
  3. **Speech on this device**: download the on-device model ("120 MB · English (UK)"),
     with a ProgressRow; **Use an online service instead** is a separate, off-by-default
     choice that names the provider and what is sent.
  4. **What voice may control**: Toggles for Media and Radio, Volume, Calls (needs Phone),
     Navigation (needs Navigation), Mark, Read faults aloud.
  5. **Test**: "Say: Play Radio 4".
- **States:** no mic: "Fit a cabin microphone" (hardware brief by name). Download fails:
  retry; Brain storage low. Moving: locked view.
- **Safety and driving rules:** Parked only; audio is never stored (ADR-0010 as used by the
  Phone app, [Phone §3][pc-3]); the wake word listens on the Brain only.
- **Components:** StepProgress (new component), Toggle (new component), ProgressRow (new
  component), ListRow, Button.
- **Spec refs:** [Phone §3][pc-3] · [shell input §8][si-8] · [head-unit apps §10][hu-10].
- **Open questions:** wake word default off or on? Recommend off (privacy, false wakes).

### voice-settings — Voice settings  [New]
- **Purpose:** the Voice app's options.
- **Owner:** app:voice
- **Opens from → goes to:** App info → Settings; `voice-assistant` (Parked) → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. Wake word Toggle and phrase. 2. Push-to-talk binding (opens
  `swc-assign`). 3. Speech engine: On this device · Online (provider named). 4. What voice
  may control (as setup). 5. Voice and speed of replies (shared with system sounds).
  6. **Privacy**: "Audio is never saved", "Recent requests: keep none · 24 h" Segmented,
  **Clear recent requests**.
- **States:** Moving: locked view.
- **Safety and driving rules:** Park to edit; no setting lets voice run a car action.
- **Components:** ListRow, Toggle (new component), Segmented, Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §10][hu-10] · [app UI model §5][ua-5].
- **Open questions:** none.

**Voice widgets:** **Voice button** (a `mic` button; size small; options: icon and name;
Moving: allowed) and a Drive menu row "Voice".

## Steering-wheel controls learning (wizard, OS input)

Bindings live in the display's **Buttons** page (`shell-buttons`) and are proved in **Key
test** (`hw-buttons-key-test`), both in the hardware brief (20-hardware-e). This wizard adds
wheel buttons as a source. Analogue wheel buttons are a resistor ladder on KEY1, KEY2 and
ground; an adapter turns each press into a button event ([head-unit research B4][ch-b4]).

| Step | Screen | What the user does | What can fail, and the recovery |
|---|---|---|---|
| 1 | `swc-adapter` | Picks the adapter and checks it is heard | Not heard: wiring card, retry |
| 2 | `swc-learn` | Presses each wheel button once, then holds it | Two buttons read the same: "Too close · re-learn" |
| 3 | `swc-assign` | Gives each button a short and long action | Conflict: swap or keep |
| 4 | `hw-buttons-key-test` | Proves every button | A miss: back to step 2 for that button |

### swc-adapter — Wheel controls 1: adapter  [New]
- **Purpose:** choose how the wheel buttons reach Ostler and check the link.
- **Owner:** os
- **Opens from → goes to:** the display's Buttons page → "Add wheel buttons"; first run of
  "Ostler is the head unit". Goes to `swc-learn`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. StepProgress "1 of 3 · Adapter". 2. Choice list:
  **Resistor-ladder input on an I/O module** (later: "Wire KEY1, KEY2 and ground to the
  module's analogue input"); **Bluetooth or USB wheel remote** (HID: "A clip-on remote; pair
  in this display's Bluetooth settings"); **Buttons from the vehicle pack** (read-only;
  "Not on Discovery 2", greyed). 3. A wiring card for the chosen kind. 4. Live check: "Adapter heard · idle
  4.7 kΩ" in `ok`, or "Nothing heard".
- **States:** no I/O module: "Add an I/O module" (hardware brief by name). Moving: locked
  view.
- **Safety and driving rules:** Parked only; button events never reach the gate
  ([shell input §3.1][si-3.1]).
- **Components:** StepProgress (new component), ListRow, Card, Chip (status), Button.
- **Spec refs:** [shell input §3.1][si-3.1] · [head-unit research B4][ch-b4] · [head-unit apps §9][hu-9].
- **Open questions:** **Decided ([head-unit apps §9][hu-9]):** resistor-ladder buttons are
  read by an I/O module's ADC (later), not by a separate button node; Ostler never sends
  button presses to the car.

### swc-learn — Wheel controls 2: learn buttons  [New]
- **Purpose:** capture each button's reading.
- **Owner:** os
- **Opens from → goes to:** `swc-adapter`; the Buttons page → Re-learn. Goes to
  `swc-assign`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night with 4 of 6 learnt.
- **Content (top to bottom):** 1. StepProgress "2 of 3 · Learn". 2. "Press the next button
  on the wheel" with a big live reading "1.20 kΩ · KEY1". 3. Learnt list: "Button 1 · 0.33
  kΩ", "Button 2 · 1.20 kΩ"… with **Rename** ("Vol +") and **Forget**. 4. "Hold the button
  for 1 s" check per button. 5. **Done learning** (≥ 1 button).
- **States:** two buttons too close: "Button 5 reads like Button 2 · press it again";
  noisy reading: "Unsteady · check the ground wire". Moving: locked view.
- **Safety and driving rules:** Parked only; a press while learning does nothing else.
- **Components:** StepProgress (new component), HeroStat, ListRow, TextField (new
  component), Button.
- **Spec refs:** [shell input §5][si-5] · [shell input §8][si-8] · [head-unit apps §9][hu-9].
- **Open questions:** none.

### swc-assign — Wheel controls 3: assign actions  [New]
- **Purpose:** map buttons to intents and app actions.
- **Owner:** os
- **Opens from → goes to:** `swc-learn`; the Buttons page; `voice-setup` (push-to-talk).
  Goes to `hw-buttons-key-test`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. StepProgress "3 of 3 · Assign". 2. One ListRow per
  button: name, **Short press** and **Long press** pickers. Choices: Volume up, Volume down,
  Mute, Next, Previous, Source, Play or pause, Answer or end call, Push to talk, Voice, Mark,
  Up, Down, Left, Right, OK, Back, Rear camera. 3. Suggested defaults from the wheel layout
  ("Vol +" → Volume up). 4. **Test buttons** → `hw-buttons-key-test`.
- **States:** conflict: "Already set on Button 3 · Swap?". Moving: locked view.
- **Safety and driving rules:** Parked only; no binding can open edit mode while Moving or
  run a car action; the long OK edit-mode binding stays fixed ([shell input §8][si-8]).
- **Components:** StepProgress (new component), ListRow, Sheet, Button.
- **Spec refs:** [shell input §2][si-2] · [shell input §8][si-8] · [head-unit apps §9][hu-9].
- **Open questions:** none.

[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[si-1]: ../../../../specs/2026-10-07-shell-input-design.md#1-goals-and-non-goals
[si-2]: ../../../../specs/2026-10-07-shell-input-design.md#2-intents
[si-3.1]: ../../../../specs/2026-10-07-shell-input-design.md#31-input-events-from-packs-and-keypads
[si-5]: ../../../../specs/2026-10-07-shell-input-design.md#5-repeat-and-long-press
[si-8]: ../../../../specs/2026-10-07-shell-input-design.md#8-bindings-and-the-key-test
[pc-3]: ../../../../specs/2026-10-07-phone-comms-addon-design.md#3-architecture
[ch-b4]: ../../../research/canbus_headunit.md#b4-steering-wheel-reverse-cameras-amplifier
[hu-10]: ../../../../specs/2026-10-07-head-unit-apps-design.md#10-clock-weather-and-voice
[hu-9]: ../../../../specs/2026-10-07-head-unit-apps-design.md#9-steering-wheel-control-learning-os
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
