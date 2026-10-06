---
title: "muki01 OBD2-Diagnostic-UI — screens, protocol and what Ostler should take"
area: references
status: stable
version: 1.0
updated: 2026-10-06
depends_on: [specs/2026-10-06-ui-architecture-design.md]
summary: >
  muki01/OBD2-Diagnostic-UI is an MIT-licensed, vanilla HTML/CSS/JS single page (about 5k lines) served
  from an ESP32's SPIFFS. It is the web front end of muki01's GPL-3.0 K-line and CAN reader firmwares,
  linked by one WebSocket JSON push at 100 ms and a page-number downlink. It has six screens: live
  cards, DTCs, freeze frame, a 0–100 timer, vehicle info and settings. Ostler should take its
  screen-driven polling, no-faults success card, 12 V colour bands, gated 0–100 timer and contract
  test idea, and avoid its hero art, unconfirmed clear, OTA forms with no authentication and innerHTML
  rendering.
---

# muki01 OBD2-Diagnostic-UI

Read end to end on 2026-10-06: every file at `56e9153` (2026-08-30). The UI was run locally with a mock
WebSocket and screenshotted at 412×915 and 1280×720 in light and dark themes (the screenshots stayed in
the scratchpad). The firmware side was read in `muki01/OBD2_K-line_Reader/WebServer_Code` to check
the contract.

## 1. What it is

| Fact | Value |
|---|---|
| Repo | `github.com/muki01/OBD2-Diagnostic-UI`; 14 commits, one author (Muksin Muksin), 2026-02-24 → 2026-08-30. Bursty, with no issues or tests in the tree |
| Files | `index.html` (1,262 lines, about 65 KB of it one inline car SVG), `css/style.css` (1,811), `js/script.js` (666), `js/webSocket.js` (47), `js/errorCodes.js` (1,000), `fonts/Montserrat-Bold.woff2`, `build_spiffs.bat`, `LICENSE`, `README.md` |
| Stack | Vanilla ES modules, no build step and no framework. One CSS file with custom properties; dark mode swaps the variables under `body.dark-mode`. One font (Montserrat Bold) |
| Packaging | `build_spiffs.bat` (PowerShell inside batch, Windows only) gzips every text asset into `data/` for the ESP32 SPIFFS. The firmware serves `index.html.gz` with `Content-Encoding: gzip` |
| Branding | "OBD2 Master". The splash credits "MUKI01", and the footer reads "Designed by MUKI01" |

**Licence verdict.**
- The root `LICENSE` is **MIT**, © 2026 Muksin Muksin. No source file has a header or SPDX tag, so the
  root licence covers them all. **Code may be ported with the MIT notice kept**, for example in a
  `LICENSES/MIT.txt` plus an SPDX line on any file that carries ported code.
- **Excluded even under MIT:**
  1. **The 65 KB car illustration** in the home banner. It is a yellow coupé with a BMW kidney grille.
     Its source is not stated, it may be stock art, and it shows a real make, which our constitution
     would not allow anyway.
  2. **The "saved" tick icon.** It has an `Icons8`-style random gradient id (`c0yjGprCnv9Gl20e9Vf6Cb`),
     and Icons8's terms need attribution or a licence.
  3. **Montserrat.** It is OFL-1.1 and the repo ships no OFL text. We do not need it, since our UI uses
     Figtree.
  4. **`errorCodes.js`.** These are the 999 generic SAE J2012 P0000–P0999 titles. The table is under
     MIT here, but the wording derives from SAE J2012, which is copyrighted. Ostler already has its
     own DTC meaning path (`dtc/`, `faultMeaning`), so take nothing from it. If generic P-code text is
     needed, use OBDb or our own wording (ADR-0019).
- **The paired firmware is GPL-3.0.** That covers `OBD2_K-line_Reader` and `OBD2_CAN_Bus_Reader`, which
  hold `WEB_SERVER.ino`, `K_Line.ino` and the PID mappings. That code is **ideas only** for our
  AGPL-3.0-or-later platform. It is licence-compatible in principle, but our ESP32 firmwares may be
  licensed differently, so keep a clean room.

## 2. Screen-by-screen walkthrough

The look is the same everywhere: an iOS-style system palette (`#007aff` blue, `#ff3b30` red, `#34c759`
green, `#ff9500` orange, `#5856d6` indigo, `#8e8e93` grey). The light background is `#f2f4f7` with
white cards; the dark background is `#0c0c0e` with `#17171b` cards. Cards have 20 px radius, a soft
two-layer shadow and a 1 px border. Montserrat Bold is used throughout, with uppercase micro-labels
(11 px, 0.8 px tracking) above large tabular numbers (28 px, weight 800). Every colour, background and
shadow transitions over 0.3 s. Content is in a 90 % column, max 1140 px (540 px on home).

**Shell.**
- A sticky 64 px app bar: a 44 px round back arrow (hidden on home); a two-colour title (first
  word blue: "Live Data", "Error Codes"); and **two 24 px status glyphs**, a chip for the WebSocket
  and a car for the vehicle, each pure green `#00de00` or red, with no words.
- Navigation is hub and spoke: home → one screen → back. Switching cross-fades with an opacity
  transition (200 ms out, 200 ms in) and sends `pageN` to the hardware.
- A footer credit sits at the bottom of every page.
- **Not connected.** Each screen shows a status card ("Not Connected to the Vehicle.", "Waiting Live
  Data…") in place of its content.

**Splash (3 s, every load).** Near-black with a pulsing orange radial glow; "OBD2 MASTER" in 42 px
weight 900 ("OBD2" orange); "ADVANCED DIAGNOSTICS" in spaced caps over a fake "INITIALIZING
SYSTEMS…" bar; exits with `scale(1.1)` and a 10 px blur. Purely decorative: it **blocks the UI for
3 s on every load**.

**Home ("OBD2 Master").**
- A full-width banner with a blue gradient (`#007aff → #00d4ff`; darker navy in dark mode) and
  rounded bottom corners.
- The banner holds the car illustration (170 px tall), "OBD2 **Diagnostic**" (the second word in
  yellow `#FFCE49`) and the subtitle "Universal Car Monitoring System".
- Below them is a frosted **Battery Status pill**: an icon tile, the label "BATTERY STATUS" and the
  voltage. The voltage is coloured red below 12.0 V, yellow from 12.0 to 12.6 V and green above
  12.6 V (`script.js` `handleWebSocketMessage`).
- Below the banner, a **3×2 grid of 140 px tiles** (Live Data, Error Codes, Freeze Frame, Speed
  Test, Vehicle Info, Settings), each a 32 px stroke icon in a 56 px tinted squircle in its own hue
  (blue, red, indigo, orange, green, grey); pressing scales a tile to 0.96.
- At 1280×720 the banner takes about 430 px, so **the second tile row falls below the fold**: the hero
  wastes the short axis of a landscape screen.

**Live Data (page 1).**
- A two-column grid of `live-card`s. Each card has a 5 px blue left accent, an uppercase label, a
  28 px value and a blue unit.
- The list is whatever keys the firmware sends in `LiveData`, in object order. **The firmware adds
  "Battery Voltage" as its own card**.
- Rebuilt with `innerHTML` every 100 ms; no gauges, graphs, min/max, thresholds, staleness or
  sorting: the "one value per card" pattern the apps note flags.

**Error Codes (page 2).**
- A single-column list of `error-card`s. Each has a red warning triangle in a red-tinted 44 px tile,
  the code in 18 px red bold and the description in 14 px grey. An unknown code reads "Description
  not found for this error code."
- With no codes it shows a **green-tick "No DTC Found / No errors detected." success card**.
- A full-width blue **"Clear Error Codes"** button appears only when codes exist. **It sends
  `clear_dtc` at once, with no confirmation and no re-read**. The firmware sets a flag and clears on
  its next loop.
- The firmware also sends "Distance traveled with MIL on" on this page, but the UI ignores it.
- Stored codes only: pending (Mode 07) is read in firmware but never shown; no Mode 0A view.

**Freeze Frame (page 3).**
- The same cards as Live Data, with an indigo accent, from the `FreezeFrame` object.
- It shows only when `DTCs` is non-empty; otherwise it says "No errors detected."
- It has no link to *which* DTC stored the frame (the frame-to-DTC PID 02 is not shown).
- Below the cards is an **explainer card**, "What is Freeze Frame?", in one sentence. It is the
  repo's only in-context help.

**Speed Test (page 4).**
- A "CURRENT SPEED" card with an 80 px weight-900 number in an orange-to-yellow gradient.
- Below it, a stopwatch card reading `00 : 00 : 000` in 48 px tabular figures, with split
  **Start** (green) and **Reset** (red) buttons, and an orange-accent "Instructions" card in four
  steps.
- **Logic.** Start arms (disabled unless speed is 0); the timer starts when speed goes above 0 and
  stops at 100 or more; the device beeps on arm, start and stop.
- **Weaknesses.** A 10 ms browser `setInterval`, not ECU timestamps, so it drifts with about 100 ms
  (one message) quantisation at each end; no saved or interpolated result; km/h only; an
  **interactive screen used while driving**, with no lockout.

**Vehicle Info (page 5).**
- Six full-width `info-card`s (own accent colour, tinted icon tile, label left, value right): VIN,
  Calibration ID, Calibration Version, Supported PIDs, Freeze Frame Support, Vehicle Info Support.
- The last three are comma-joined hex lists from the firmware's support bitmaps.
- **The full VIN is shown unmasked.**

**Settings (page 6).**
- Five cards, each with a coloured left accent and a header icon:
  1. **Appearance**: a Dark Mode iOS switch, stored in `localStorage`, light by default with no
     automatic mode.
  2. **Communication Protocol**: a select of Automatic, ISO 9141-2, KWP fast and slow, and CAN
     11/29-bit at 250/500k, with "Apply Protocol". Read-only rows show the **Selected** and
     **Connected** protocol.
  3. **Monitor Parameters**: a two-column checkbox grid of the PIDs the ECU supports, pre-ticked with
     the current desired set, and "Update PID List".
  4. **Network Configuration**: SSID, password (at least 8), DHCP or Static, and a static block
     (IP, mask, gateway) with live 0–255 octet filtering.
  5. **System Maintenance**: file pickers for **firmware .bin ("Flash Firmware", red)** and **SPIFFS
     .bin ("Update Assets", yellow)**.
- Every form POSTs `FormData`; on 200 a zooming modal shows a green tick, "Settings Saved
  Successfully" and, for Wi-Fi and firmware, "Your device will reboot, please reconnect…". **No
  authentication, CSRF protection or flash confirm**; errors go only to `console.error`; no progress.

## 3. Hardware link and protocol

- **Topology.**
  - An ESP32, ESP32-S3/C3/C6 or ESP8266 runs muki01's firmware: `OBD2_K-line_Reader/WebServer_Code`
    (ISO 9141-2 / KWP2000 through his `OBD2_KLine_Library`) or `OBD2_CAN_Bus_Reader/
    WebServer_Code_CAN` (ISO 15765 through his CAN library).
  - The board starts its own Wi-Fi AP ("OBD2 Master") or joins a network as a station.
  - ESPAsyncWebServer serves this UI from SPIFFS.
  - **The phone browser is the head unit.** There is no Bluetooth LE, serial or ELM327 in the UI.
- **Uplink.** `ws://<host>/ws` (port 80, plain text). Every 100 ms the firmware sends a full JSON
  snapshot to all clients (`ws.textAll`).
  - The firmware decides **what to read on the bus from the page the UI is showing**: page 1 only
    the *desired* Mode 01 PIDs; 2 stored DTCs plus distance with MIL on; 3 all supported
    freeze-frame PIDs; 4 only speed (PID 0D); 5 VIN, CALID and CVN; 6 the supported and desired
    lists; pages 0, 2, 3, 5 and 6 also poll DTCs every 1 s.
  - Every message carries `vehicleStatus`, `Voltage` (from the ESP's own ADC divider, oversampled 16×),
    `selectedProtocol` and `connectedProtocol`.
- **Downlink.** Bare text frames: `page<N>`, `clear_dtc` and `beep` (a buzzer melody).
- **REST.**
  - Forms POST to `/wifiOptions`, `/protocolOptions`, `/pidSelect`, `/firmwareUpdate` and
    `/fileSystemUpdate`.
  - `GET /api/getData` returns one snapshot (it sets `page = -1`: live data plus DTCs).
  - `GET /api/clearDTCs` clears **through an unauthenticated GET**.
- **Contract drift.** The README contract and the firmware disagree on the vehicle-info support
  lists. The README says `SupportedLiveData`; the firmware sends `supportedLiveData`,
  `supportedFreezeFrame` and `supportedVehicleInfo`, which the UI reads. A README-faithful mock
  therefore renders **"undefined"** on Vehicle Info (seen in our run). `DesiredLiveData` is an int
  array, while the README shows hex strings.
- **Reconnect.** `onclose` calls `InitWebSocket()` at once, with no backoff. The status icons go red
  only when a message is falsy, so **a dead socket keeps the last green state**. There is no
  staleness timer.
- **Pairing with muki01's libraries.** The firmware links `OBD2_KLine_Library` or
  `OBD2_CAN_Bus_Library` at build time; the UI never sees them. The UI does not pair with
  `VAG_KW1281` or `I-K_Bus`; those projects have no web server.

## 4. Comparison with Ostler's spec and current UI

| Aspect | OBD2-Diagnostic-UI | Ostler spec (ADR-0018) | Ostler today (`ui/src`) |
|---|---|---|---|
| Navigation | Hub of 6 tiles → screen → back | 5 destinations on a driver-side rail or bottom bar; Drive is a mode | 8 public tabs + admin (`screens/registry.ts`) |
| Status | Two colour-only glyphs (socket, car) in the app bar; 12 V only on home | Severity-ordered strip: telltale, Link ladder, REC, Security, 12 V, Mark; icon plus word | `ConnectionPill` with a word and dot; replay pill |
| Layout | One responsive column; hero banner; no landscape class | HU-7 / HU-9/10 / HU-wide / phone classes at 76 px targets and ≥ 56 px values | 900 px column |
| Live data | Flat 2-column number cards from firmware keys | Generated from manifest `class`/`span`/`normal`; tiles, gauges, chips; `candidate` vs stale distinct | Inputs, `Gauge`, `StatTile`, `Sparkline`, `Readout`, `RangeBar` |
| Faults | List + unconfirmed Clear | Tier 1: one confirm naming system and consequence, report first, re-read | `Faults.tsx` with current/logged groups, `confirmAction`, export |
| Freeze frame | Cards plus an explainer | Part of scan report "codes with freeze frame" (§4.3) | **None in UI** |
| Readiness | None | Home health role "readiness where it exists" | None |
| Vehicle info | Unmasked VIN, CALID, CVN, support bitmaps | Masked VIN, HMAC fingerprint, identity bar (§4.4) | Module identity in Settings |
| Protocol | User picks from 8 protocols | "Never a protocol list"; detect, then ask only what changes topology | Pack-defined |
| PID selection | Checkbox grid of supported PIDs | Rates per state on the signal; user dashboards deferred | Channel picker in replay only |
| Theme | Manual light/dark toggle, light default | Night dark automatically | Auto/Day/Night in `Preferences.tsx` |
| Driving lockout | None; the 0–100 timer is meant for driving | Parked/Idling/Moving, server-enforced | None (U2) |
| Device admin | Wi-Fi, static IP, OTA firmware/assets, no auth | More → Devices; Tier gates; threat model before U5 | None |
| Safety | No tiers | Five tiers plus comfort | `confirm.ts` levels |

**Net.** Ostler's spec is well ahead on architecture, safety and honesty. This repo's value is in
**small interaction ideas and the ESP32 device contract**; its page-driven demand polling is a cheap,
concrete form of our per-signal `rate`, worth making explicit so K-line bandwidth follows the screen.
Its weak points are ones our spec already forbids: colour-only status, a protocol list, unconfirmed
clear, a full VIN, decorative splash and hero, and no lockouts.

## 5. Feature inventory

| Feature | Where in their code | Ostler has it? | Where it lands | Tier | Reuse | Effort |
|---|---|---|---|---|---|---|
| Hub grid of colour-coded function tiles | `index.html` `#mainMenu nav`, CSS `.menu nav` | partly (tabs) | Home zero-layer cards, U1 (as cards, not a launcher) | read | ideas-only | S |
| Two-colour screen title | `switchPage`, `#orangeText` | no | Not adopted (`ScreenHead` is enough) | read | — | — |
| Socket and vehicle link glyphs | `updateConnectionStatus` | yes (pill) | Strip Link chip, U1; split "adapter" and "ECU" rungs | read | ideas-only | S |
| 12 V pill with red, yellow and green bands | `handleWebSocketMessage` page 0 | partly | Strip 12 V chip plus Home card, U1; bands as `normal`/`limits` on `Vehicle.LowVoltageBattery` | read | ideas-only | S |
| Splash screen (3 s) | `#splash-screen`, CSS | no | **Avoid**; at most a < 300 ms PWA launch screen | — | — | — |
| Hero vehicle banner | `.banner` | partly (vehicle card spec) | Home vehicle card 40 % on HU-9/10, U1; pack silhouette, not stock art | read | no (art excluded) | M |
| Live data number cards (label, value, unit, accent) | `live-card` | yes | Generated tier tile, U4 | read | ideas-only | S |
| Accent colour per function area (blue live, indigo freeze, red faults) | CSS `#dataBoxLiveData`, `.freeze-dashboard` | no | Design tokens per function area, U1 (non-ISO colours only, telltales stay ISO) | read | ideas-only | S |
| Demand polling by open page (`pageN` downlink) | `switchPage` → firmware `K_Line.ino` | partly (`rate` per state) | Platform: a "visible signals" subscription from UI to poller, U3; K-line bandwidth follows the screen | read | ideas-only (firmware GPL-3.0) | M |
| DTC list with code, description and icon | `error-card` | yes | Diagnose → Faults, U1/U3 | read | ideas-only | S |
| "No DTC Found" green success card | page 2 else-branch | partly | Diagnose → Faults empty state, U3, with **scan age** ("OK · 2 min ago") per honest states | read | ideas-only | S |
| Clear DTCs (one tap) | `clearDTC_Btn` → `clear_dtc` | yes (confirmed) | Tier 1 already; **avoid** the no-confirm pattern | clear | — | — |
| Clear via unauthenticated GET | firmware `/api/clearDTCs` | no | **Avoid**; server gate for all paths (§7) | clear | — | — |
| Distance travelled with MIL on | firmware page 2 | no | `generic_obd2` fault detail, U4 | read | ideas-only | S |
| Pending DTCs (Mode 07) | firmware `readDTCs(read_pendingDTCs)` | partly (D2 logged) | `generic_obd2` "Pending" group, U4 | read | ideas-only | S |
| Freeze frame cards | page 3 | no | Diagnose → fault detail "Snapshot" section, U3 (D2 where KWP stores it) and U4 (OBD Mode 02) | read | ideas-only | M |
| Inline explainer card ("What is Freeze Frame?") | `#menu3 .info-card` | partly (`Glossary.tsx`) | Glossary "i" chips on Diagnose sections, U3; hidden while Moving | read | ideas-only | S |
| 0–100 km/h timer, auto-start and auto-stop | page 4, `startTimer` | no | Logs → session detail "Performance" (computed **after** the run from logged speed, GPS and IMU), U7 or a later phase; arm-only control Parked; result readable in Drive mode | read | ideas-only | M |
| Device beep on start and stop | `sendData("beep")` | no | Firmware or device action (`comfort`), U5 | comfort | ideas-only | S |
| Big gradient speed number | `.speed-value #Speed` | partly (Drive) | Drive mode hero tile, U1 (no gradient text; ≥ 56 px plain) | read | ideas-only | S |
| VIN, CALID and CVN cards | page 5 `info-card` | partly | Diagnose identity bar, U4; **masked VIN only** | read | ideas-only | S |
| Support bitmaps (PIDs, freeze frame, vehicle info) | page 5 | no | More → Developer → Coverage, U4 (as counts plus a list, not raw hex) | read | ideas-only | S |
| Protocol picker (8 options) | `protocolChange_Form` | no | **Avoid** as a first step; a Developer-only override under service mode, U7 | read | ideas-only | S |
| Selected and connected protocol display | `protocol-status` | partly | Link sheet "Bus" rung, U1 | read | ideas-only | S |
| PID checkbox grid ("Monitor Parameters") | `selectPID_Boxes` | partly (replay channel picker) | Live area: searchable signal picker that also sets poll set, U4; per-vehicle diff later (ADR-0018 Q6) | read | ideas-only | M |
| Dark mode switch in `localStorage` | `applyTheme` | yes (auto, day, night) | Already covered; keep auto | read | — | — |
| Wi-Fi SSID, password and static IP form with octet filter | `wifiChange_Form`, input filter | no | More → Devices → *device* network page, U5 (for our ESP32 add-ons); octet filter idea | comfort | port with notice (filter, ~20 lines) or clean-room | S |
| OTA firmware and SPIFFS upload | `firmwareUpdate_Form` | no | More → Devices → Update, U5; **needs auth, signed images, progress, Parked** | procedure | ideas-only | L |
| "Saved, device will reboot" modal | `#overlay` | partly (sheets) | Device settings result sheet, U5 | — | ideas-only | S |
| Gzip asset build for SPIFFS | `build_spiffs.bat` | n/a | Firmware tooling for our ESP32 devices (cross-platform script) | — | ideas-only | S |
| Not-connected placeholder per screen | `statusBox*` | yes (`ConnectionNotice`, `StatusGate`) | Keep ours (adds stale-grey) | read | — | — |
| Snapshot REST `GET /api/getData` | firmware | yes (`/snapshot`) | Already in platform | read | — | — |
| Embedded 999 P-code text table | `errorCodes.js` | partly | **Not taken** (SAE-derived); OBDb or own text, U4 | read | no | — |
| Page transition fade with a lock | `switchPage` | no | Not adopted (motion only for red alarms, §2.7) | — | — | — |

## 6. UI recommendations by phase

**U1 (shell).**
1. Give the strip's **12 V chip three bands** taken from the signal's `normal` and `limits`, not
   hard-coded: below 12.0 red, 12.0–12.6 amber, above 12.6 green when the engine is off. When the
   engine runs, the bands shift (13.2–14.8 green), because 12.4 V while running is a charging fault.
   Add a word: "12.3 V · Low".
2. On HU-7, **move the hero to a side**: a vehicle card at 40 % on HU-9/10, a small silhouette on
   HU-7, and none on the phone strip. Their 1280×720 home hides half its tiles below a 430 px banner,
   which is the failure to avoid. Playwright should assert all Home cards are above the fold at
   1024×600.
3. Add **per-area accent tokens** in `ui/tokens` (live, faults, snapshot, tests, procedures,
   device), kept clear of ISO telltale red, amber and green. The coloured left rule on cards is a
   cheap, readable cue.
4. Show the **Link chip as two rungs at a glance** (adapter, then ECU), with words, because their
   two colour-only glyphs fail WCAG 1.4.1. The chip must turn grey on silence (a staleness timer),
   not keep showing the last green.
5. **No splash screen.** The PWA should paint the shell straight away.

**U2 (driving state).**
6. Make **performance timing a Moving-safe pattern**. Arm it Parked with one big button. Then show
   nothing interactive while driving: Drive mode shows only the large speed figure and, after the
   stop, the result. Compute the time after the run from logged signals, interpolating the 0 and 100
   crossings, rather than with a browser stopwatch.

**U3 (manifest and scan).**
7. Add a **"visible signals" subscription**. The UI tells the platform which signal ids are on
   screen, and the poller narrows the K-line request set to them plus the strip roles. This is the
   per-screen version of `rate`, and it matters most on one-session K-line.
8. The Faults **empty state should be a positive card** with scan age and system, such as "No codes
   · Engine (Td5) · read 40 s ago". It should never appear for an unscanned system, which shows "Not
   scanned".
9. Add **freeze frame as a section of each fault's detail** (the snapshot values with their units
   and which code stored them), plus a one-line glossary chip, rather than as a separate destination.

**U4 (generic_obd2).**
10. Show **Mode 01 support, Mode 02 support and Mode 09 support as coverage counts** in the identity
    bar and Developer, add Pending and "distance with MIL on" to the fault detail, and give the Live
    area a **searchable signal picker** (their checkbox grid, with search and grouping).

**U5 (devices).**
11. Write a **device settings template** for our ESP32 add-ons (guardian, HEVAC): network (with the
    octet filter), protocol or bitrate, and update. Firmware update is a **Tier 3 procedure**:
    authenticated, Parked, signed image, progress and a reboot sheet. Never use an open POST or GET.

**U7 (decode and logs).**
12. Add **contract tests for device JSON**. Their README and firmware drifted (`SupportedLiveData`
    against `supportedLiveData`) and rendered "undefined". Our AsyncAPI and JSON Schema plan (U0/U5)
    should check every device payload in CI.

**Avoid:** rebuilding the DOM with `innerHTML` from bus data (an XSS vector on shared Wi-Fi),
unconfirmed clears, unmasked VINs, a protocol picker as the first step, reconnecting with no backoff,
decorative animation, and stock or brand art.
