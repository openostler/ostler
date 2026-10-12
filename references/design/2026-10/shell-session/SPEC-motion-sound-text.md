---
title: "Shell motion, haptics, sound, text, icons and app rules — the designer's exact values (13 October 2026)"
area: references
status: stable
version: 1.0
updated: 2026-10-13
depends_on: [references/design/2026-10/shell-session/IMPLEMENTATION.md, references/design/2026-10/shell-session/README.md]
summary: >
  The designer's answers to the builder's request, saved as delivered with frontmatter added: motion durations and easing per transition, haptics per event, the caution chime and warning tone spec, rules for apps (per-module stale data, focus inside pages), the full shell text table (toasts, refusals, buttons, announcements, spoken alert format), Material Symbols icon names, and answers to the open points (default instrument pages, transparent instruments while moving, the tab and card on 12 inches and up).
---

# Ostler shell: motion, haptics, sound, text, icons and app rules

This answers sections 2, 3, 5, 6 and 7 of the builder's request. Token values are in `ostler-shell-tokens.json`.

## 2. Motion

Easing uses the Material 3 curves: **standard** `cubic-bezier(.2,0,0,1)`, **decelerate** `cubic-bezier(.05,.7,.1,1)` and **accelerate** `cubic-bezier(.3,0,.8,.15)`.

| Event | Duration | Easing / notes |
|---|---|---|
| Zoom out (enter edit mode) | 280 ms | decelerate; scale 1 → 0.84, panels fade in over 150 ms |
| Zoom in (Done) | 240 ms | accelerate |
| Slide-swap | starts 300 ms after hovering, then animates in 220 ms | standard; tiles move as one |
| Stack-forming highlight | appears at 800 ms of hover | 120 ms fade |
| Carousel paging, parked | follows the finger; settles in 300 ms | standard; commits past ⅓ of the page or on a fling over 1000 dp/s; 120 ms rubber-band at the ends |
| Carousel, moving (wheel/trigger) | 0 ms (straight cut) | no slide |
| Resize preview reflow | live while dragging; 150 ms settle on release | standard |
| Resize snap | 80 ms | decelerate to the anchor |
| Heads-up card in | 220 ms | decelerate; from y −16 and opacity 0 |
| Card to tab | after 4000 ms; 300 ms morph | standard; size, position and radius together |
| Card or tab out (cleared) | 200 ms | accelerate; fade |
| Page dots | in 150 ms, hold 1500 ms after idle, out 300 ms | linear fade |
| Edge-paging hold | glow builds over 600 ms, then the page turns in 300 ms; repeats every 800 ms while held | linear glow, standard turn |
| Full screen in / out | 260 ms | standard; other tiles shrink into the badge rail |
| Sheets (picker, style, save) | 250 ms in / 200 ms out | decelerate / accelerate |
| Toast | in 150 ms, shown 4 s (10 s with Undo), out 150 ms | |
| Reduced motion | all movement 0 ms; fades 100 ms | follow the OS setting |

While moving, nothing moves except fades of 150 ms or less; page changes are cuts.

## 2b. Haptics

Android `HapticFeedbackConstants`, falling back to `navigator.vibrate` on the web.

| Event | Android | Web fallback |
|---|---|---|
| Hold to edit, or lift a tile | `LONG_PRESS` | 20 ms |
| Snap to an anchor | `SEGMENT_TICK` (API 34), else `CLOCK_TICK` | 8 ms |
| Size limit reached (edge stops) | `GESTURE_THRESHOLD_DEACTIVATE`, else `REJECT` | 30 ms |
| Drop placed | `CONFIRM` | 12 ms |
| Over the delete circle | `GESTURE_THRESHOLD_ACTIVATE` | 15 ms |
| Delete released | `CONFIRM` | 12 ms |
| Page edge bump (D-pad, carousel end) | `REJECT` | 25 ms |
| Edge-paging turn | `CLOCK_TICK` | 8 ms |
| ACK | `CONFIRM` | 12 ms |

## 3. Sound

These are specs to synthesise, in mono, 48 kHz.

**Caution chime**
- Two notes, 880 Hz then 660 Hz, each 120 ms with a 40 ms gap.
- Sine wave with a little 2nd harmonic (−18 dB). Envelope: 8 ms attack, 140 ms release.
- Loudness −18 LUFS integrated, peak −3 dBFS.
- Plays once.

**Warning tone**
- Three pulses at 1000 Hz, each 150 ms on and 100 ms off.
- Triangle wave, low-passed at 4 kHz. Envelope: 5 ms attack, 40 ms release.
- Loudness −12 LUFS, peak −1 dBFS.
- After the first time it repeats every **10 s**, 6 dB quieter, until ACK.

**Spoken line**
- Starts 300 ms after the tone ends. Android `TextToSpeech`, rate 1.0, the system voice.
- Format: `"{Caution|Warning}: {app speak text}"`. For example "Caution: coolant one-oh-eight".
- The app supplies the words; numbers are spoken by the app's own speech text.

**Audio focus**
- Request `AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK`. Duck media to −14 dB (about 20%) for the tone and speech.
- Use the `USAGE_ALARM` stream for warnings and `USAGE_NOTIFICATION_EVENT` for cautions.
- Warnings can't be muted below 50% of the alert volume.

## 5. Rules for apps

**Stale data per module** (every app should do it the same way)
- Mark staleness at the smallest unit that's actually stale: a row, a gauge or a section. Never the whole page unless everything in it is stale.
- How to mark it:
  - dim the value to 50%;
  - add a `schedule` icon (16 dp, or 22 while moving) and `{Module} asleep · last {time}` in `text2`, 13/600 (24 while moving).
  - Examples: "ABS asleep · last 10:42", "Guardian asleep · last 2 h ago".
- Time format: `HH:MM` today, `Yesterday HH:MM`, otherwise `D Mon HH:MM`. Never "3 h ago" for times older than 1 hour.
- **Unavailable** (never seen this drive): show "—" and "Not available". **Estimated:** add an `est.` pill.
- When the whole tile is stale, the tile label shows the schedule icon and the time (the shell handles this through `page.summary()`).

**Focus inside a page**
- When OK enters a page, the shell draws a 2 dp `focus` outline at 50% opacity around the tile.
- The app then draws the standard ring (3 dp wide, 3 dp gap, `focus` colour) around the control that has focus. Its radius is the control's own radius plus 6.
- At the edge of the page, play the edge bump and don't move the focus.
- Restore the last inner focus when the page is re-entered.

## 6a. Shell text

| Key | Text (parked) | Moving variant |
|---|---|---|
| edit.refused | — | Park to edit the layout |
| edit.title | Editing {layout} | — |
| edit.done | Done | — |
| edit.undo | Undo · {n} | — |
| edit.layout | Layout | — |
| edit.settings | Settings (a11y label) | — |
| edit.kept | — | Layout edits kept. Park to save. |
| edit.save.title | Save your changes? | — |
| edit.save.over | Save over “{layout}” | — |
| edit.save.new | Save as new… | — |
| edit.save.discard | Discard edits | — |
| edit.save.keep | Keep editing | — |
| edit.removed | {page} removed · Undo | — |
| edit.limitMax | {page}: largest size | — |
| edit.splitRefused | Too small to split · {page} needs {class} | — |
| edit.lastTile | A layout needs one tile | — |
| edit.newPage | New page | — |
| picker.title | Add to the {class} slot | — |
| picker.change | Change {page} to… | — |
| picker.suggested | Suggested for {car} | — |
| picker.all | All pages | — |
| picker.empty | No pages match | — |
| picker.noFit | Needs a bigger slot | — |
| style.title | {page} · window style | — |
| style.normal / transparent / none | Normal / Transparent / None · widget | — |
| style.note | While moving, Transparent shows solid on instruments. | — |
| style.appSettings | Page settings | — |
| stack.release | Release to stack | — |
| alert.header | {CAUTION/WARNING} · {app} | same, 24 dp |
| alert.diagnose / ack | Diagnose / ACK · Select | same |
| alert.after | Trail opens after ACK | same |
| viewing | Viewing {car} | same |
| gateway.lost | Can’t reach the gateway · data from {time} | Gateway lost · data from {time} (toast) |
| gateway.open | Open Gateway | — |
| fullscreen.restore | Restore layout (a11y) | — |
| pages.only | {layout} · only layout | same |
| pages.last | {layout} · last layout | same |
| trigger.switched | Switched to {layout}: {reason} | same, text only |
| a11y.resize | {page}: {fraction} wide, {class} | — |
| a11y.moved | {page}, {position} of {n} | — |
| a11y.alert | {level}. {title}. From {app}. | — |
| speak.alert | {Caution/Warning}: {speak} | — |

## 6b. Icons (Material Symbols Rounded)

| Use | Icon |
|---|---|
| Edit layout / layout name | edit |
| Done | check |
| Undo | undo |
| Layout (shapes) | grid_view |
| Settings | settings |
| More shapes | tune |
| Delete circle | delete |
| Stack (zone centre) | layers |
| Zone arrows | north / south / west / east |
| Add slot | add |
| All pages | apps |
| Pinned | push_pin |
| Full screen restore | close_fullscreen |
| Caution | error (FILL 1) |
| Warning | warning (FILL 1) |
| Spoken line | volume_up |
| Diagnose | stethoscope |
| ACK | check |
| Stale | schedule |
| Viewing another car | visibility |
| Gateway lost | cloud_off |
| Refused / blocked | block |
| Swap target | swap_horiz |
| Split | vertical_split |
| Android widgets | widgets |
| Back hint | keyboard_return |

## 7. Answers to the open points

1. **Instruments by default:** Speed, Attitude, Heading, Transfer, Engine (the gauge page), and Route **while turn-by-turn guidance is active**.
   - Trail, Logs, Diagnose, Convoy, Security and widgets are not instruments.
   - An app sets this through `instrument: true`.
2. **Transparent instrument tiles while moving: confirmed, they turn solid.** Non-instrument tiles keep their transparency, but blur is off.
   - The background behind transparent tiles is the theme's wallpaper.
   - While moving, instrument tiles show their solid `surface1` instead of the wallpaper.
   - See frame X-07 in `shell-X-builder-frames.dc.html`.
3. **12″ and up:**
   - The **card** is centred over the two visible pages, so its centre lines up with the seam, never over the pinned column.
   - The **tab** sits top centre, straddling the seam, 6 dp from the top. If an instrument tile's label row is under it, it may cover only the label row.
   - With a pinned column, the centre is worked out across the pages only.
