---
title: "Designer brief 80-k — Clock and alarms, Weather: pages, setup, settings and widgets"
area: references
status: draft
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-07-drive-modes-and-editing-design.md, references/research/driver_distraction_rules.md]
summary: >
  Clock and Weather, part of the starter widget pack (app:widgets-starter, owner decision
  item 53). Clock has the clock page with alarms, timers (a parking timer, a rest-break
  reminder) and a stopwatch; the alarm or timer ringing, which goes through the OS alert
  pipeline; and its setup and settings (time source from GPS or the Brain's clock, 12 or 24
  hours, time zone). Weather shows now, hourly and
  daily forecasts and road-relevant warnings, with a setup flow that asks where the location
  comes from and keeps it on the device unless the owner agrees to send a rounded position.
  Both list their widgets with setup options and Moving behaviour.
---

# 80-k — Clock and Weather

**Owner (decided, item 53):** Clock and Weather are part of the **starter widget pack**, so
every page here has the owner `app:widgets-starter`; they are not apps of their own. The
approved head-unit apps spec covers the OS time service, the Clock widget and Weather's
rules ([head-unit apps §10][hu-10]), so those pages are New. Alarms, timers and the
stopwatch are not in any approved spec, so `clock-page` and `clock-alarm-ring` stay
Proposed. The strip already shows the time.

### clock-page — Clock, alarms and timers  [Proposed]
- **Why the app needs it:** parking timers and rest-break reminders are useful in a car;
  every head unit has a clock page.
- **Purpose:** the time, alarms, timers and a stopwatch.
- **Owner:** app:widgets-starter
- **Opens from → goes to:** app drawer → Clock; the clock widget; the strip clock (long
  press is edit mode, so tap only). Goes to `clock-settings`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked Timers tab; phone Day Alarms.
- **Content (top to bottom):**
  1. Big time in `type-hero` "14:32" and the date "Wed 7 Oct".
  2. TabBar: **Alarms** · **Timers** · **Stopwatch**.
  3. Alarms: ListRows "06:45 · Weekdays" with a Toggle; **Add alarm** (Parked).
  4. Timers: preset Chips "Parking 1 h", "Parking 2 h", "15 min"; running timers as rows
     "Parking · 47:10 left" with **Stop**; **Rest break every 2 h of driving** Toggle.
  5. Stopwatch: big digits, **Start**, **Lap**, **Reset**.
- **States:** empty Alarms: "No alarms". Time not set yet (no GPS, no network): "Time not
  confirmed" chip in `warn`. Moving: a `value` template with the time and the next timer
  ("Parking · 47 min"); setting alarms is Parked only; preset timer Chips stay as a
  `short_list`.
- **Safety and driving rules:** no typing while Moving; starting a preset timer is allowed
  (one tap); the stopwatch's running digits update at ≤ 4 Hz ([UI §12.1][ui-12.1]).
- **Components:** HeroStat, TabBar, ListRow, Toggle (new component), Chip, Button, `value`
  template.
- **Spec refs:** [UI §12.1][ui-12.1] · [App model §4.4][am-4.4].
- **Open questions:** does the rest-break reminder belong with Trips (it knows driving
  time)? Recommend Clock asks Trips for driving time through the OS.

### clock-alarm-ring — Alarm or timer ringing  [Proposed]
- **Why the app needs it:** a ringing alarm or timer needs a safe, glanceable card.
- **Purpose:** tell the driver a timer or alarm went off, and stop or snooze it.
- **Owner:** os (alert pipeline draws it); app:widgets-starter raises it
- **Opens from → goes to:** a timer or alarm firing. Ends where the driver was.
- **Layout classes:** phone · tablet · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night-dim Moving ("Rest break" card); hu7 Night Parked ("Parking ends in 10 min").
- **Content (top to bottom):** an `alert_card`: icon `timer` or `alarm`, line 1 "Parking
  ends in 10 min" or "Time for a break", line 2 "Clock"; buttons **Stop** and **Snooze 10
  min**. One short tone (system sounds).
- **States:** a call, reverse or a red telltale is active: the card waits. Parked with the
  phone linked: also a phone notification.
- **Safety and driving rules:** one card, ≤ 2 lines of ≤ 30 characters, ≤ 2 buttons; never
  over a red telltale, the reverse camera, a call or a manoeuvre prompt
  ([UI §12.1][ui-12.1]).
- **Components:** `alert_card` template, Button.
- **Spec refs:** [UI §12.1][ui-12.1].
- **Open questions:** none.

### clock-settings — Clock setup and settings  [New]
- **Purpose:** first-run choices (shown once as setup) and later settings.
- **Owner:** app:widgets-starter
- **Opens from → goes to:** first open (as setup, with **Done**); `clock-page` → Settings;
  App info → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. **Time source** (read only, explained): "GPS time, then the
  Brain's clock, then the network". 2. **Format** Segmented 12 h · 24 h (24 h for the UK
  default). 3. **Time zone** Segmented Automatic · Choose. 4. **Alarm sound** and level.
  5. **Rest break** interval Segmented 1.5 · 2 · 3 h.
- **States:** no GPS fix: "Using the Brain's clock". Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** ListRow, Segmented, Slider (new component).
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §10][hu-10].
- **Open questions:** none.

**Clock widgets:** the **Clock** widget is the starter pack's ([launcher §9][lw-9]). The pack
also adds **Timer** (the next timer with Stop; sizes small, medium; options: which timer,
show seconds; Moving: a `value`) and **Alarm** (the next alarm; size small; options: show the
day; Moving: a `value`).

### weather-page — Weather  [New]
- **Purpose:** weather now, today and the next days, with warnings.
- **Owner:** app:widgets-starter
- **Opens from → goes to:** app drawer → Weather; the weather widget. Goes to
  `weather-settings`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night Parked; phone Day.
- **Content (top to bottom):**
  1. Place line: "Near your car" or a chosen place name (never coordinates).
  2. Now: icon (Material Symbols weather glyph), "7 °C", word "Rain", "Feels like 4 °C",
     wind "24 km/h SW".
  3. Warnings Card when present: "Yellow warning · wind · until 18:00" in `warn`.
  4. Hourly row (next 12 hours) and a daily list (7 days) with high, low and rain chance.
  5. Footer: provider and "Updated 14:10".
- **States:** offline: last forecast with "Offline · updated 3 h ago" in `text-3`. No location
  allowed: "Choose a place" button. Loading: placeholder rows. Moving: a `value` template
  "7 °C · Rain"; forecasts and lists are Parked only.
- **Safety and driving rules:** no scrolling lists while Moving; warnings may raise one
  `alert_card` per trip at most ("Wind warning ahead"), never animated radar.
- **Components:** HeroStat, Card, ListRow, Chip (status), `value` template.
- **Spec refs:** [UI §12.1][ui-12.1] · [App model §4.4][am-4.4] · [head-unit apps §10][hu-10].
- **Open questions:** is weather a driving item under reg 109? Treated as non-driving except
  the single `value` and the warning card ([research §4.2][dd-4.2]).

### weather-setup — Weather: first-run setup  [New]
- **Purpose:** choose where the forecast's place comes from, and agree to what is sent.
- **Owner:** app:widgets-starter
- **Opens from → goes to:** first open of Weather; `weather-settings` → Location. Goes to
  `weather-page`.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night; phone Day.
- **Content (top to bottom):** 1. StepProgress "Location". 2. Choice list: **Near the car,
  rounded to about 10 km** ("Your exact position never leaves the car") · **A place I
  choose** (search, Parked) · **Home place from Places** (by name). 3. What is sent: "A
  rounded position or a place name, to the weather service, every 30 minutes while the car
  is on". 4. **Provider** row. 5. **Done**.
- **States:** no internet: "Weather needs the internet to update". Moving: locked view.
- **Safety and driving rules:** Parked only; location sharing is opt-in and rounded
  ([ADR-0009][adr-9]).
- **Components:** StepProgress (new component), ListRow, TextField (new component), Button.
- **Spec refs:** [UI §12.1][ui-12.1] · [head-unit apps §10][hu-10].
- **Open questions:** which provider (one with no account and no key is preferred).

### weather-settings — Weather settings  [New]
- **Purpose:** the Weather app's options.
- **Owner:** app:widgets-starter
- **Opens from → goes to:** `weather-page` → Settings; App info → Settings.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  hu7 Night.
- **Content (top to bottom):** 1. **Location** (as setup). 2. **Units** follow system
  units, with an override. 3. **Refresh** Segmented 15 · 30 · 60 min · Only when I open it.
  4. **Warnings while driving** Toggle (on). 5. **Clear saved forecasts**.
- **States:** Moving: locked view.
- **Safety and driving rules:** Park to edit.
- **Components:** ListRow, Segmented, Toggle (new component), Button.
- **Spec refs:** [Drive modes §8.1][dm-8.1] · [head-unit apps §10][hu-10].
- **Open questions:** none.

**Weather widgets:** **Now** (icon, temperature, word; sizes small, medium; options: place
source, show feels-like; Moving: a `value`) and **Forecast** (hourly or daily; sizes wide,
hero; options: hours or days, how many; Parked home pages only).

[ui-12.1]: ../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44
[am-4.4]: ../../../../specs/2026-10-06-app-model-design.md#44-driver-safe-templates
[dm-8.1]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#81-safety-rules
[dm-9]: ../../../../specs/2026-10-07-drive-modes-and-editing-design.md#9-the-widget-and-slot-contract-summary
[dd-4.2]: ../../../research/driver_distraction_rules.md#42-uk-regulation-109-screens-visible-to-the-driver
[adr-9]: ../../../../decisions/adr-0009-session-logbook-and-location.md
[hu-10]: ../../../../specs/2026-10-07-head-unit-apps-design.md#10-clock-weather-and-voice
[lw-9]: ../../../../specs/2026-10-07-launcher-and-widgets-design.md#9-the-starter-catalogue
