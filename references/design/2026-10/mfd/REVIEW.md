---
title: "MFD hand-off review (2026-10-11) — each design against ADR-0052, the gateway settings spec and the theme specs: matches, drift and decisions for the owner"
area: references
status: draft
version: 0.1
updated: 2026-10-11
depends_on: [references/design/2026-10/mfd/README.md, decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md, decisions/adr-0053-automatic-hardware-detection-in-the-gateway.md, decisions/adr-0049-open-vehicle-data-standard-and-app-suite.md, decisions/adr-0050-kotlin-for-the-android-app-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0044-adapters-on-the-brain-without-a-node.md, specs/2026-10-11-gateway-settings-design.md, specs/2026-10-07-theme-engine-design.md, specs/2026-10-07-visual-design-system-design.md, references/research/responsive_tile_sizes.md, references/design/2026-10/brief/00-direction-mfd.md]
summary: >
  Review of the designer's MFD hand-off of 2026-10-11 (the owner: "some drift here but you get the idea"). For each design (MFD v2, Tiling v2, Core, Core Sizes, Gateway, Themes v2, v1 MFD and Tiling) it records what it shows, what matches the recorded decisions and the drift, each with a recommended resolution. Main drift: 22 vs 24 px moving floor; tile limits by screen inches; four size classes vs five; the shell's Settings sheet and built-in Car page vs the gateway owning both; a clock in the MFD strip; the Themes v2 set (twelve, drawn only as HTML) vs the 22 in ostler-themes.js; themes relabelling status words and using red or green for normal values; a moving-safe theme variant vs visual §13.3; structural theme CSS vs the parked skin engine. What was clearly agreed went into ADR-0052 v0.5, a theme engine amendment and a gateway spec note. Ends with eighteen decisions for the owner.
---

# MFD hand-off review (2026-10-11)

Reviewed against [ADR-0052](../../../../decisions/adr-0052-mfd-pages-sizes-and-the-shell-library.md)
v0.4, the [gateway settings spec](../../../../specs/2026-10-11-gateway-settings-design.md) v0.3,
the [theme engine spec](../../../../specs/2026-10-07-theme-engine-design.md) and
[visual §13](../../../../specs/2026-10-07-visual-design-system-design.md), and the
[responsive tiles research](../../../research/responsive_tile_sizes.md). Renders are in `png/`;
the folder is described in the [README](README.md).

**Taken in now** (clearly agreed, no decision changed): ADR-0052 v0.5 (top strip order,
connection chip, tile label menu, app navigation by size, shared cursor, warning takeover
details, theme rules), a dated note in the theme engine spec, and a dated note in the
gateway settings spec. Everything that is drift is in the owner's list at the end.

## 1. MFD v2 (`mfd-v2-*.png`)

**Shows:** the interactive MFD. Saved layouts Trail, Convoy, Commute, Workshop, Bench; the six
layouts, locked while moving; toggles for moving, caution, master warning and right-hand
drive. Strip: layout name, connection ("Brain · live"), "Layout locked", the caution or
warning pill, a clock. Each tile label: page name, a menu chevron, "App · Size".

**Matches:**
- No drive modes; instruments are pages; "Off-road" style sets are saved layouts.
- Layout editing locked while moving; saved layouts still one tap.
- Size from the tile (Bench: Diagnose Expanded with freeze frame and live values).
- Caution as a strip pill; warning takes a tile until ACK, with one instruction.
- Right-hand drive mirrors the whole screen, strip included.

**Drift:**
- **A clock in the strip** (10:14). The direction brief, the designer's ADR and the Core
  design all say no clock. *Resolution:* no clock; the design is out of date.
- **No shared-settings button in the strip.** The designer's ADR lists it fourth.
  *Resolution:* follow the ADR (Core shows the gear).
- **The warning took the driver-side map tile** (Trail, bottom left on a left-hand-drive
  car), because it was the only page that is not a car instrument. *Resolution:* order the
  choice: passenger side first, then not an instrument, then not a map with guidance; if
  nothing fits, use the band (decision 9).
- **Chip text "Brain · live"** differs from the Gateway design's states ("Connected · via
  Brain"). *Resolution:* use the Gateway design's list everywhere.

## 2. Tiling v2 (`tiling-v2-*.png`)

**Shows:** the same shell in squeezed windows: 7″ whole screen; Android split half (tiles drop
to one number) and third (main page plus a chip row); 10″ split top and bottom (one row of
columns); a master warning as a band under Speed; 5″ main + two; phone Workshop (Diagnose over
Logs) and Convoy.

**Matches:** window rules in order (shape, size, overflow); one row under about 320 px; chips
swap in on tap; the warning band never covers a Drive page; Android split screen is just a
smaller window.

**Drift:**
- **Class labels disagree with the recorded thresholds.** A tile about 310 px wide is
  labelled Standard (ADR-0052: Standard needs 360 × 260); phone tiles about 370 × 330 are
  labelled Compact (ADR-0052 would say Standard). *Resolution:* keep the research §8 numbers;
  the designer's labels are illustrative.
- **The overflow chips** (icon and value, no name: 289°, 1.8, LOW) are what ADR-0052 calls
  **Badge**. *Resolution:* keep five classes; map them (decision 3).

## 3. Core (`core-*.png`)

**Shows:** the bare shell before any apps. State 1 "Connect your car" (gateway found nearby,
other ways); state 2 the Car page (health, pinned gauges, "Pin a signal", up to three
dismissable suggestions); state 3 Diagnose opens beside Car; moving shows "Layout locked";
the gear opens a full-screen Settings sheet (Vehicles, Connections, Apps, Layouts, Themes,
Alerts, Display, Brain, Account and sync, About) with a theme grid.

**Matches:** never an empty grid; suggestions from what the car can do; first app opens beside
with Undo; no clock; Settings browse-only while moving.

**Drift:**
- **The Car page is "built in" to the shell, and the shell has a ten-section Settings
  sheet.** ADR-0052 §1 puts the Car page in the gateway app; the designer's own update says
  the shell holds no settings screens. *Resolution:* read Core as the **gateway app** on first
  run: Welcome and Car are gateway pages; the gear opens the gateway's shared settings
  (Display, Layouts) and links to the rest of the gateway's sections. The shell holds only the
  button (ADR-0052 v0.5 §2).
- **The theme grid is the old 22-theme set** (`ostler-themes.js`: Glass, Minimal, Deep night,
  High contrast, Air…), not Themes v2. *Resolution:* see §6 and decision 11.
- **"Brain" and "Vehicles" as shell sections** match the gateway spec's This gateway and Cars.

## 4. Core Sizes (`core-sizes-*.png`)

**Shows:** the four states at phone 393×852, 5″ 800×480, 7″ 1024×600, 10″ 1280×720 and tablet
1180×820. Settings is two panes on head units and tablets, list then detail on the phone.

**Matches:** tall windows split top and bottom; the same pages at every size; Settings layout
per screen.

**Drift:**
- **Only Compact, Standard and Expanded appear.** No Chip or Badge state is drawn.
  *Resolution:* ask for Badge and Chip of the Car page (decision 3).
- **A full 800 × 480 tile is labelled Standard.** The research §8 check says it is Expanded
  if chrome is about 48 px; the designer's strip and margins take about 90 px, so the box is
  under 420 px high. *Resolution:* keep the strip at 48 px or less on 480 px screens, or lower
  Expanded's height to 400 (decision 4).
- **On the phone the connection chip is a dot with no words.** Colour alone carries the
  state. *Resolution:* keep a short word or a shaped icon.

## 5. Gateway (`gateway-*.png`)

**Shows:** g1 first-run connect (car → gateway → apps; Brain recommended, this phone, this
browser for now); g2 Status (health, this gateway's role, sources, apps using this car); g3 New
car found (masked VIN, "Set up a profile", "Just look, don't save", "Pick a car myself"); g4 per-app
car permissions (see, change as a request, access log); g6 car profile settings; g5 This device
(Ostler-wide web permissions; role, power, updates); g7 This gateway (client of the car's
Brain or standalone; network, storage, power, updates); g8 an app that cannot reach the
gateway; the connection chip's five states; three action states.

**Matches** (gateway settings spec): one gateway owns hardware and stores everything (§1–§2);
three levels (§3); automatic car choice, unknown car prompt, manual switch (§4); one server
per car, phone as client (§4); car permissions per app and per car with an access log, changes
always a request (§2, §5.1); web permissions Ostler-wide, location from the gateway (§2);
offline cache marked stale with no actions (§2); "one tester per bus" notice and the actuator
opt-in (§5.1); masked VIN only in the garage (ADR-0018 Q7, ADR-0036).

**Drift and gaps:**
- **The design adds a Status tab** and a bottom navigation Status · Cars · Apps · This device.
  The spec has no Status section. *Resolution:* add Status to the spec as the gateway's home
  (done as a note; decision 14 to confirm the navigation).
- **The car profile sidebar lacks Display and About** (spec §5.3, §5.5); Account sits under
  "Gateway". *Resolution:* keep Display and About; place Display with shared settings.
- **Devices bound to one car: Brain, Guardian node and a K-line dongle, all live**, with
  K-line "in use by Ostler". ADR-0044 allows an adapter on the Brain only with no node.
  *Resolution:* confirm whether a Guardian counts as a node here; otherwise show the dongle as
  passive (decision 15).
- **"Apps" in the gateway also holds per-app permissions**, while the spec keeps them in the
  car profile. Same data, two doors; fine.

## 6. Themes v2 (`themes-v2-*.png`)

**Shows:** twelve themes, each drawn day and night on the same Diagnose + Engine screen:
Night, Heritage, Expedition, Blueprint, Race, Adventure, Knight Rider, Paper, and "mission
themes" Military, Naval, Jet fighter, Spy. Each lists what it changes: frame, labels, numbers,
gauges, controls, strip, divider. Rules: Auto, Day or Night (Auto follows headlights, then the
light sensor, then sunset); a safe version while moving; one CSS file with a day and a night
block, checked for contrast and minimum sizes; never changes layout, tile sizes, touch targets,
drag handles, warning and caution colours, safety icons; steering-wheel and soft-key controls
are not themes.

**Matches:** structure, not just colour (visual §13, theme engine); warning and caution colours
and safety icons locked (ADR-0052 §8); contrast and size checks on import; fonts are all open
licences (DM Serif Display, IBM Plex, Barlow, B612, Share Tech Mono, Black Ops One, Special
Elite).

**Drift:**
- **The set.** `ostler-themes.js` holds 22 themes (the brief says 22); Themes v2 shows twelve,
  drawn only as HTML with no token file. Six are shared (Night, Heritage, Expedition,
  Blueprint, Race, Paper), six are new (Adventure, Knight Rider, Military, Naval, Jet fighter,
  Spy), sixteen are dropped, including **High contrast** and **Deep night**.
  *Resolution:* Themes v2 is the current look for the twelve; keep High contrast and Deep
  night as built-ins; values for the new six must be written as tokens (decision 11).
- **Moving.** Themes v2, the brief and ADR-0052 §5 switch to a safe version while moving (no
  blur, glow or texture). Visual §13.3, approved 2026-10-07, says themes look the same while
  moving, with no safe variant. *Resolution:* owner to choose (decision 10); recommend the
  safe version, since ADR-0052 already says so.
- **Themes change words.** "LINK", "NET · UP", "UPLINK SECURE", "Contact established",
  "ANOMALY", "IAT CIRCUIT", "ENGI", "WKSP", "MENU". The brief says plain words, no cryptic
  codes; the chip's states are a fixed list. *Resolution:* themes may change case, font and
  spacing, never the words of status, the connection chip, fault text or actions (decision 12).
- **Colour for state.** Knight Rider shows normal values in red; Naval at night is all red;
  Jet fighter is green on black (the brief: "no green-on-black text"); Race's shift lights
  use green, amber and red. *Resolution:* red and amber only for warning and caution; Naval
  night keeps warnings distinct by shape, word and inversion; the render check tests it
  (decision 13).
- **Controls change meaning.** Naval puts "ALERT … ACK" on a stored fault; ACK is only for
  warnings (ADR-0052 §4a). *Resolution:* themes restyle controls, never relabel or add them.
- **Divider label "58 : 42"** (Blueprint) while dividers snap to ⅓, ½, ⅔. Minor; the label
  should show a snap value.
- **Theme engine scope.** Structural CSS per theme needs the free-CSS layer, which the
  2026-10-08 re-scope parked with the skin engine. *Resolution:* un-park the CSS layer only
  (no OSML layouts), with protected surfaces, required parts and the render check (decision
  16).
- **Day and night.** Each theme ships both, drawn separately; visual §13.3 keeps Day, Night
  and Night dim modes and an Auto that pairs two themes. *Resolution:* each theme ships day
  and night; users may still pair two themes; Night dim stays (decision 17).
- **Name "Knight Rider"** is a television show's name. *Resolution:* rename (for example
  "Scanner") before shipping (decision 18).

## 7. v1 MFD and Tiling (`v1-*.png`)

Earlier explorations. A left layout rail (Commute, Workshop, Parked), soft keys along tile
edges, a Drive page, a fixed tile limit "2 on 5″, 3 on 7″, 4 on a tablet", and on the phone the
layout's tiles as a tab bar. v2 replaces the rail with the strip switcher and stacks tiles on
the phone. *Resolution:* reference only; v2 wins.

## 8. The designer's docs against the repo

| Point | Designer | Repo | Recommendation |
|---|---|---|---|
| Moving text floor | 22 px | 24 px (ADR-0052 §5, §9.1) | Keep 24 (decision 1) |
| Tile limits | 2 on 5″, 3 on 7″, 4 on a tablet | Pixels: every tile at least Compact | Pixels (decision 2) |
| Size classes | Four: Chip, Compact, Standard, Expanded | Five, with Badge, and thresholds | Five (decision 3) |
| Expanded entry | ≥ 640 × 440 (760 wide for Diagnose, Logs) | 640 × 420, no per-app override | Keep; per-page minimums go in the page contract (decision 5) |
| Shell and settings | Shell holds no settings screens, but the strip has a Shared settings button and Shared Settings exists | Shared preferences live once in the gateway | Button in the shell opens the gateway's shared settings (decision 6) |
| Only app that talks to the car | Gateway | Gateway (ADR-0052 §1, spec §1) | Matches |
| Native apps | Only the gateway's Android wrapper | ADR-0050 template for Android apps; optional Ostler Controls (§4a) | Gateway wrapper is the only required native app (decision 7) |
| Soft keys | Later, as a separate overlay app | Shell draws the in-app row; Ostler Controls draws over other apps | Keep ADR-0052 §4a (decision 8) |
| Connection chip | In every app, from the gateway; tap opens the Gateway | Vehicle chip only | Both chips (taken in, v0.5) |
| App navigation | Shows at Standard and Expanded, hides at Compact and Chip | Not stated | Taken in (v0.5) |
| Warning takeover | Passenger-side tile, not a car gauge, never a Drive page, band if a chip | Same in brief | Taken in (v0.5); the tie-break order is decision 9 |
| Theme Auto | Headlights → light sensor → sunset | Auto pairs two themes (§13.3) | Taken in as a note; see decision 17 |
| What themes change | Frame, labels, numbers, gauges, controls, strip, divider | Visual §13: anything, by CSS hooks; engine re-scoped to tokens | Decision 16 |
| What themes never change | Layout and sizes, touch targets, drag handles, warning and caution colours, safety icons | Protected surfaces, required parts, render check (engine 5–7) | Use the union (taken in as a note) |
| Theme set | Twelve (Themes v2); 22 in the brief | 22 (visual §13.3, engine §9) | Decision 11 |
| Shared Settings list | Theme, units, text size, alert levels, layouts, account, apps menu, permissions | Display shared; alerts, permissions, layouts in the car profile | Same data in the gateway; fine |

## Decisions for the owner

1. **Moving text floor:** recommend **24 px** (ADR-0052 §9.1); the designer's 22 has no source.
2. **Tile limits:** recommend **pixels**, not screen inches; the inch counts become examples.
3. **Size classes:** recommend **five**. Map the designer's Chip to Chip and the overflow and
   rail items (icon and value) to Badge; ask the designer for Badge and Chip of each page.
4. **800 × 480 full tile:** recommend a strip of 48 px or less on 480 px-high screens so a
   full tile stays Expanded; the alternative is Expanded at 640 × 400.
5. **Per-page Expanded minimum** (the designer's 760 px for Diagnose and Logs): recommend a
   page-contract field, not a different class threshold.
6. **Shared settings button:** recommend the shell draws the button only and it opens the
   gateway's shared settings; the shell has no settings screens.
7. **Native apps:** recommend "the gateway's Android wrapper is the only **required** native
   app"; Ostler Controls stays optional; other apps are PWAs, wrapped only where ADR-0050
   pays.
8. **Soft keys:** recommend keeping ADR-0052 §4a: the shell draws the in-app soft-key row;
   Ostler Controls handles steering-wheel keys and overlays outside Ostler.
9. **Warning tile order:** recommend passenger side, then not an instrument page, then not a
   map with guidance; otherwise a band.
10. **Moving theme variant:** recommend the safe version while moving (opaque, no blur, glow
    or texture, plain wallpaper behind driver tiles), which amends visual §13.3's "same while
    moving".
11. **Theme set:** recommend Themes v2's twelve plus High contrast and Deep night as the
    built-ins, with token values written for the six new themes; the other 20 of the old set
    move to a gallery or are dropped.
12. **Theme wording:** recommend themes never change the words of status, the connection
    chip, fault text or actions; case, font and spacing are free.
13. **State colours in themes:** recommend red and amber only for warning and caution; no
    normal values in red; green on black only for state, not body text; the render check
    tests it on the night variant.
14. **Gateway navigation:** recommend the design's Status · Cars · Apps · This device, with
    Status as the gateway's home and Display, Account and About under This device.
15. **Guardian with a dongle:** confirm whether a Guardian counts as a node for ADR-0044; if
    it does, a K-line dongle on the same car is passive only.
16. **Theme engine scope:** recommend un-parking the free-CSS layer only (structure per theme
    through documented hooks), keeping OSML layouts parked.
17. **Day and night:** recommend each theme ships a day and a night version with Auto by
    headlights, light sensor, then sunset; users may still pair two themes; keep Night dim.
18. **Theme names:** recommend renaming "Knight Rider" before it ships.
