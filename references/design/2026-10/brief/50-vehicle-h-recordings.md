---
title: "Designer brief: vehicle and diagnostics (H) — recording, marks and notes, flags, delete and whole-app replay"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-05-replay-notes-capture-design.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-06-logs-at-scale-design.md, specs/2026-10-06-ui-architecture-design.md]
summary: >
  Eighth file of the vehicle and diagnostics brief. It covers capturing and reviewing
  recordings in the Trips app, all new pages under the approved replay-notes, session-logbook
  and logs-at-scale specs: the live recording view (Analysis while recording, with Mark,
  Note, Options, Split and End trip now), the recording options sheet with sources and the
  flag manager, the Mark "What happened?" sheet, the notes and flags panel in playback, the
  flag sheet, the typed Delete confirm, and whole-app replay of Diagnose, read-only with
  "ran at" marks. Recording runs only while the car is connected; there is no demo mode.
---

# Vehicle and diagnostics brief (H): recordings, notes and replay

Recording is automatic and always on while the car is connected; with the car disconnected
the trip is **paused** (no rows, not even GPS) and ends after 5 minutes ([Logs at scale
§1][ls-1]). The VIN and identity reads are never recorded ([Session logbook][sl-rec]).

### trips-recording — Recording now (live analysis)  [New]
- **Purpose:** see the trip being recorded and mark moments while it records.
- **Owner:** app:trips
- **Opens from → goes to:** the trips-list "Recording now" card; the strip REC chip; live-chart "Open in Trips" → trips-mark-note, trips-recording-options, trips-playback (Rewind, follows the end).
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night (Parked), phone Day.
- **Content (top to bottom):**
  1. Status Card: "Recording · 14 min · TD5 · GPS · phone audio off", accent live dot; or "Paused — no connection" (no dot).
  2. Map at the live position with the growing trace (re-fetched every 5 s).
  3. Chart lanes (up to 3) with the cursor pinned to the newest sample; readouts from the live snapshot.
  4. Actions: **Mark** (primary), **Note…**, **Options**, **Split**, **End trip now**.
- **States:** GPS but not connected: map at the live position, hint "Recording starts when the car connects". Nothing at all: empty state with **Rewind** to the newest trip. Brain asleep: "Needs the Brain". Moving on a head unit: locked view, but the strip's **Mark** chip still works at any speed.
- **Safety and driving rules:** Mark is the one action safe at any speed ([UI §3.2][ui-3.2]); End trip now Parked or Idling only ([UI §12.2][ui-12.2]); Mark and Split refused while paused ([Logs at scale §1][ls-1]).
- **Components:** Card, Chart (Canvas lanes), Button, Sheet over map.
- **Spec refs:** [Replay §7][rn-7] · [Replay §5][rn-5] · [Logs at scale §1][ls-1] · [UI §12.2][ui-12.2].

### trips-recording-options — Recording options and flag manager  [New]
- **Purpose:** choose what a recording captures, and which automatic flags show.
- **Owner:** app:trips
- **Opens from → goes to:** trips-recording Options; Preferences → "Recording & flags" → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, desktop Night.
- **Content (top to bottom):**
  1. **Sources:** GPS ("USB · fix · 9 satellites" or "None"), Phone audio (asks for the microphone on Apply), Brain audio ("Unavailable: no microphone" with its reason), IMU on or off, Accelerometer rate Segmented **10 · 25 · 50 Hz**, **Calibrate** (motion permission on iOS).
  2. **Session name** TextField (optional).
  3. **Flags:** three switches with counts in the current trip: **Manual marks · 3**, **Sensor out of range · 2**, **Faults · 1**; **Muted sensors** list with Unmute.
  4. **Apply** (also requests permissions and the wake lock), **Cancel**.
- **States:** a source that cannot run: greyed with its reason ("Needs HTTPS — see the HTTPS guide"). Idling without Park evidence and Moving: locked view.
- **Safety and driving rules:** settings are per device and display only; Park to edit on head units.
- **Components:** Sheet, ListRow, Toggle (new component), Segmented, TextField (new component), Button.
- **Spec refs:** [Replay §3][rn-3] · [Replay §5][rn-5] · [Replay §8][rn-8].

### trips-mark-note — Mark: "What happened?"  [New]
- **Purpose:** add a reason to a Mark, or a note at a moment.
- **Owner:** app:trips
- **Opens from → goes to:** the strip Mark chip (Parked, or on a phone), trips-recording Mark or Note…, trips-playback ⚑ (retro mark at the cursor) → back.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night, hu9 Night (Parked).
- **Content (top to bottom):** 1. "Marked at 09:14:31" (the mark is already saved). 2. "What happened?" TextField. 3. Quick tag Chips: issue, fault, noise, driving, test. 4. **Save**, **Skip**.
- **States:** while Moving on a head unit: the mark is saved and no sheet opens; "Add details later in Trips". Paused: Mark is greyed, "Connect to the car to mark". Demo logs: hidden.
- **Safety and driving rules:** no text entry while Moving ([UI §12.1][ui-12.1]).
- **Components:** Sheet, TextField (new component), Chip, Button.
- **Spec refs:** [Replay §5][rn-5] · [Replay §8][rn-8] · [Replay §2][rn-2].

### trips-notes — Notes and flags panel  [New]
- **Purpose:** every note and automatic flag in a trip, to jump to and edit.
- **Owner:** app:trips
- **Opens from → goes to:** trips-detail (full sheet) and trips-playback → a row jumps the cursor; trips-flag-sheet.
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** desktop Night beside the chart, phone Night.
- **Content (top to bottom):** 1. Filter Segmented **All · Notes · Out of range · Faults**. 2. Rows by time: note text with tags and kind (mark, note, capture), range notes with their span ("02:55–03:50"); flags with severity icon and word ("Coolant out of range · peak", "10.4 shuttle valve switch · Current"); "6 more out of range" folded rows. 3. **Add note at cursor**; dragging on the chart makes a range note. 4. Inline edit and delete for notes (not on demo logs).
- **States:** empty: "No notes or flags". Demo log: read-only. Moving: locked.
- **Safety and driving rules:** flags are computed for display only, never stored ([Replay §8][rn-8]).
- **Components:** ListRow, Segmented, Chip, Button, TextField (new component).
- **Spec refs:** [Replay §2][rn-2] · [Replay §5][rn-5] · [Replay §8][rn-8].

### trips-flag-sheet — Flag sheet  [New]
- **Purpose:** explain one flag or note at the cursor.
- **Owner:** app:trips
- **Opens from → goes to:** the chip above the scrubber; a trips-notes row → diagnose-fault (a fault flag), Flag settings (trips-recording-options).
- **Layout classes:** phone · tablet · desktop · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. Title with severity ("Out of range", `warn` or `alarm`), time and duration. 2. Peak and normal band ("Coolant · peak and band") or the fault code, meaning and Current or Logged. 3. Buttons: **Jump to**, **Keep as note** (not on demo logs), **Mute this sensor**, **Flag settings**.
- **States:** flood fold: "6 more out of range" lists the folded flags. Moving: locked.
- **Safety and driving rules:** read only.
- **Components:** Sheet, StatTile, Button.
- **Spec refs:** [Replay §8][rn-8].

### trips-delete — Delete trip (typed confirm)  [New]
- **Purpose:** delete a recording for good, deliberately.
- **Owner:** app:trips
- **Opens from → goes to:** trips-detail Delete → trips-list.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** phone Night.
- **Content (top to bottom):** 1. "Delete this trip?" with name, date, size. 2. "Its notes and audio are deleted with it. This cannot be undone." 3. TextField "Type Delete to confirm" (case-sensitive). 4. **Cancel** (focused) · **Delete** (danger).
- **States:** hidden for demo logs and in public mode. Moving: locked.
- **Safety and driving rules:** typed confirm, Cancel focused ([Shell input §7][si-7]).
- **Components:** Sheet, TextField (new component), Button (danger).
- **Spec refs:** [Logs at scale §5][ls-5] · [Session logbook UI][sl-ui].
- **Open questions:** what happens to active grants of a deleted trip: revoked at once or kept until expiry? (The specs do not say.)

### trips-replay-diagnose — Whole-app replay of Diagnose  [New]
- **Purpose:** look at Diagnose as it was at a moment of a recorded trip.
- **Owner:** app:trips
- **Opens from → goes to:** trips-playback (any page while in replay) → diagnose-system areas in replay; **Exit to live**.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu9 Night (SLABS Outputs during the ABS pump test of Demo log 1), phone Night.
- **Content (top to bottom):** 1. Link chip as "Replay · Exit to live"; amber edge on `main`; global transport above the nav. 2. The module in view follows the recorded module. 3. Faults show the codes at the cursor; **Clear codes · replay** with a lock. 4. Outputs highlight the test running at the cursor; each row "ran at 09:22:40" with check or cross and word. 5. Settings shows only "Identity read at 09:14:03".
- **States:** a trip from another vehicle: the UI switches to that trip's pack and manifest and back on exit ([UI §4.1][ui-4.1]). Moving: locked.
- **Safety and driving rules:** every action refuses with "Replay — read only"; the live link is never touched ([Replay §4][rn-4]).
- **Components:** Scrubber (global transport), Chip, ListRow, Button.
- **Spec refs:** [Replay §4][rn-4] · [UI §4.1][ui-4.1].

[ui-3.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#32-the-persistent-status-strip
[ui-4.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#41-garage-and-active-vehicle-switcher
[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[ui-12.2]: ../../../../specs/2026-10-06-ui-architecture-design.md#122-logs--trips-changes-32-34-35-36-38-41-43-6-10
[si-7]: ../../../../specs/2026-10-07-shell-input-design.md#7-confirms-and-countdowns
[rn-2]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#2-notes
[rn-3]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#3-audio-and-accelerometer-capture
[rn-4]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#4-whole-app-replay-ui
[rn-5]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#5-recording-ui-notes-ui-and-the-replay-map
[rn-7]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#7-analysis-tab-and-rewind-v11
[rn-8]: ../../../../specs/2026-10-05-replay-notes-capture-design.md#8-rewind-to-the-end-automatic-flags-the-flag-manager-and--in-replay-v13
[sl-ui]: ../../../../specs/2026-10-05-session-logbook-design.md#ui
[sl-rec]: ../../../../specs/2026-10-05-session-logbook-design.md#recording-rules-sessionrecorder
[ls-1]: ../../../../specs/2026-10-06-logs-at-scale-design.md#1-record-only-while-connected
[ls-5]: ../../../../specs/2026-10-06-logs-at-scale-design.md#5-ui
