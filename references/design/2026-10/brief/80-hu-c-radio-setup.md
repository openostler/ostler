---
title: "Designer brief 80-c — Radio app: first-run setup (tuner, antenna, scan), settings and widgets"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, references/research/hardware.md, references/research/driver_distraction_rules.md]
summary: >
  The Radio app's first-run setup flow and its settings page (app:radio). Setup picks the
  tuner hardware (a USB DAB stick using software decoding, or a Si468x tuner HAT on the
  Brain), checks the antenna with a live signal reading on a known station, and runs the first
  band scan with the region. Settings cover RDS and DAB options (TA, AF, regional, DAB-to-FM
  link, PTY filter, logo lookups), presets per profile and the tuner device. The end lists
  the two widgets Radio adds to the widget picker gallery (now playing, presets) with their
  setup options and Moving behaviour.
---

# 80-c — Radio setup, settings and widgets

**Spec:** the approved head-unit apps spec covers the Radio app and its tuner
([head-unit apps §3][hu-3]); its setup is an OS-drawn setup flow ([app UI model §4][ua-4]).
A tuner is new hardware on the Brain and needs a guided setup.
The App info page and "Run setup again" belong to the app framework (90-appframe files).

## Setup flow (first run)

| Step | Screen | What the user does | What can fail, and the recovery |
|---|---|---|---|
| 1 | `radio-setup-tuner` | Picks or confirms the tuner the Brain found | None found: plug-in help, "Set up later" |
| 2 | `radio-setup-antenna` | Tunes a known strong station and reads the signal | Weak or none: antenna checklist, "Continue anyway" |
| 3 | `radio-setup-scan` | Picks the region and scans FM, AM and DAB | Scan finds nothing: back to step 2 |
| 4 | `radio-now-playing` | Lands on the strongest station; presets filled if chosen | — |

The flow is Parked only on driver-facing displays; it can run on a phone linked to the car.
Each step has **Back**, **Next** and **Set up later** (the app opens with a setup Card).

### radio-setup-tuner — Setup 1: pick the tuner  [New]
- **Purpose:** find the tuner and confirm which bands it can receive.
- **Owner:** app:radio
- **Opens from → goes to:** first open of Radio; `radio-settings` → Tuner → Change;
  `radio-now-playing` "Set up a tuner". Goes to `radio-setup-antenna`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. StepProgress "1 of 3 · Tuner".
  2. "Found on the Brain" ListRows, each with the bands as Chips:
     - "Si468x tuner HAT · I²C" — FM, DAB (AM only on chips that have it); listed first,
       the first tuner path (item 36).
     - "USB DAB stick · software decoding" — DAB, FM ("AM needs extra hardware").
  3. Help Card "No tuner? Ostler needs a USB DAB stick or a tuner HAT on the Brain. The car's
     old radio stays separate." with **Show options** (opens the Store, 70-store files).
  4. **Install shape** reminder: "Ostler is the head unit" (set in Audio setup) with
     **Change**.
  5. **Next** (primary).
- **States:** loading "Looking for a tuner…"; none found; driver missing "Tuner found but its
  driver is not installed · Update"; Brain asleep: "Needs the Brain" Card with **Wake**.
  Moving: locked view.
- **Safety and driving rules:** Parked only; touches no vehicle bus.
- **Components:** StepProgress (new component), ListRow, Chip, Card, Button.
- **Spec refs:** [UI §6][ui-6] · [hardware research][hw] · [head-unit apps §3][hu-3] · [app UI model §4][ua-4].
- **Open questions:** **Decided (item 36):** an Si468x-based HAT or module comes first (DAB+
  decoded in hardware); a USB SDR dongle is the second option.

### radio-setup-antenna — Setup 2: antenna check  [New]
- **Purpose:** prove the antenna works with a live signal reading.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-setup-tuner`; `radio-settings` → Antenna check;
  `radio-tune` "check the antenna". Goes to `radio-setup-scan`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night (good result), hu7 Night (weak result).
- **Content (top to bottom):**
  1. StepProgress "2 of 3 · Antenna".
  2. "Tuning a strong national station…" then the station: "BBC Radio 4 · 93.5 FM" or
     "BBC National DAB · 12B".
  3. **Signal** StatTiles: "Strength 52 dBµV", "Quality (SNR) 24 dB", and for DAB
     "Error rate 0.2 %"; each with a word: "Good", "Fair" or "Weak" (`ok`, `warn`).
  4. Result line: "Antenna OK" or "Weak signal".
  5. When weak, a checklist Card: "Is the antenna plugged in?", "Does an active antenna have
     its 12 V feed?", "Is a DAB antenna fitted? The car's FM aerial is poor for DAB.",
     "Park outside, away from buildings, and try again".
  6. **Test again** (secondary), **Next** (primary), **Continue anyway** (ghost).
- **States:** loading (live readings refresh twice a second, no animation); no station heard
  at all: "No signal on any band"; Moving: locked view.
- **Safety and driving rules:** Parked only; read only.
- **Components:** StepProgress (new component), StatTile, Card, Button.
- **Spec refs:** [hardware research][hw] · [head-unit apps §3][hu-3] · [app UI model §4][ua-4].
- **Open questions:** **Decided (item 65):** the D2's original aerial and its amplifier feed
  are first car checks; the checklist's D2 line is written only after the owner confirms
  them on the car.

### radio-setup-scan — Setup 3: region and first scan  [New]
- **Purpose:** set the region and fill the station list.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-setup-antenna`; `radio-stations` → Scan again. Goes to
  `radio-now-playing`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night scanning; hu7 Night done.
- **Content (top to bottom):**
  1. StepProgress "3 of 3 · Scan".
  2. **Region** list: "United Kingdom" (preselected from the system locale), "Europe",
     "Other"; it sets FM steps, AM steps (9 kHz) and DAB blocks (5A–13F).
  3. **Bands** Chips: DAB, FM, AM (only what the tuner supports).
  4. Progress: "DAB · block 11D · 31 services found", then "FM · 97.6 MHz · 18 found".
  5. Toggle "Fill presets with the six strongest stations" (on).
  6. Result "43 stations found" and **Done** (primary).
- **States:** nothing found: "No stations found" with **Check antenna**. Cancelled: keeps
  what was found. Moving: locked view (scan can finish in the background).
- **Safety and driving rules:** Parked only for the page; scanning itself mutes audio
  briefly and never runs while a call or navigation prompt is playing.
- **Components:** StepProgress (new component), ListRow, Chip, Toggle (new component),
  ProgressRow (new component), Button.
- **Spec refs:** [UI §3.5][ui-3.5] · [head-unit apps §3][hu-3] · [app UI model §4][ua-4].
- **Open questions:** none.

### radio-settings — Radio settings  [New]
- **Purpose:** the Radio app's own options.
- **Owner:** app:radio
- **Opens from → goes to:** `radio-now-playing` → Settings; App info → Settings. Goes to the
  setup steps, `audio-volume-rules` (TA volume).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):**
  1. **Traffic** section: Toggle "Traffic announcements (TA)" (off by default,
     [head-unit apps §3][hu-3]); "TA volume" link to
     `audio-volume-rules`; Toggle "Also news bulletins" (off).
  2. **Following:** Toggle "Follow the station on other frequencies (AF)" (on); Toggle
     "Stay on regional variant (REG)" (on); Toggle "Switch DAB to FM when DAB drops" (on).
  3. **Display:** Toggle "Show RadioText" (on, Parked only); Toggle "Show DAB slideshow"
     (on); Toggle "Look up station logos online" (off; says "Sends the station ID to a logo
     service").
  4. **Presets:** Segmented "Presets per: Car · Profile"; **Clear all presets** (danger,
     confirm).
  5. **Tuner:** device row ("Si468x tuner HAT · FM, DAB") with **Change**; **Antenna check**;
     **Scan again**; Region row.
  6. **Moving list:** Segmented "While driving, show: Favourites · Presets".
- **States:** no tuner: only the Tuner section, with "Set up a tuner". Not owner: Tuner and
  Region read only. Moving: locked view.
- **Safety and driving rules:** Park to edit ([Drive modes §8.1][dm-8.1]); no option can
  make RadioText scroll or show while Moving.
- **Components:** ListRow, Toggle (new component), Segmented, Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [Drive modes §8.1][dm-8.1] · [head-unit apps §3][hu-3] · [app UI model §5][ua-5].
- **Open questions:** none.

## Radio widgets (in the widget picker gallery)

Each has a widget setup page drawn in the launcher's style (45-launcher files); the OS rules
for widget setup are in `drive-widget-settings-addon`.

- **Radio · Now playing** — logo, station name, info line, seek and play or pause. Sizes:
  small (logo and name), medium (adds seek), wide (adds the preset strip). Setup options:
  show logo (on or off), show RadioText (Parked only), which buttons (seek, presets,
  favourite). **Moving:** drawn by the OS as the `media` template; never more than title,
  artist, static logo and the four controls.
- **Radio · Presets** — 3 or 6 preset buttons. Sizes: medium (3), wide (6). Setup options:
  which presets (P1–P6 or P7–P12), show logos or names only. **Moving:** a `short_list` of
  ≤ 6 rows, ≤ 30 characters each; tap recalls.
- **Shortcut:** "Radio" app shortcut, and "Traffic announcements on or off" as a Drive menu
  row (allowed while Moving; app-model §15.3).

[ui-3.5]: ../../../../specs/2026-10-06-ui-architecture-design.md#35-drive-mode-driving-states-and-service-mode
[ui-6]: ../../../../specs/2026-10-06-ui-architecture-design.md#6-add-on-devices
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[hw]: ../../../research/hardware.md#development-kit-recommended-parts-250-plus-the-pi
[hu-3]: ../../../../specs/2026-10-07-head-unit-apps-design.md#3-radio
[ua-4]: ../../../../specs/2026-10-07-app-ui-model-design.md#4-the-setup-flow
[ua-5]: ../../../../specs/2026-10-07-app-ui-model-design.md#5-the-options-flow
