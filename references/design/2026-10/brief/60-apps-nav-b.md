---
title: "Designer brief — Navigation add-on: search results, route preview, map regions and saved places"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-navigation-addon-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-trip-sharing-design.md]
summary: >
  Page content for four Navigation screens that the approved spec describes but the index does
  not hold: destination search results (local index, coordinates and pasted links), the route
  preview with profile and avoid choices, the legality warning and Start, the map region manager
  at Settings → Maps (map tiles, routing graph, search index and elevation cut from one data
  date) and saved places with priority waypoints. Each block gives content, states, driving rules
  and components.
---

# Navigation, part b: search, preview, regions and places

Example numbers and names in quotes are label formats, not data.

Part a: [60-apps-nav-a.md](60-apps-nav-a.md).

### nav-search — Destination search results  [New]
- **Owner:** app:navigation
- **Purpose:** find a place from the region's own index, with no internet.
- **Opens from → goes to:** the "Where to?" field on nav-page → a result → nav-route-preview.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night.
- **Content (top to bottom):**
  1. Field with the query ("Bakewell"); clear Button.
  2. Result rows: name, kind ("Town", "Fuel", "Campsite"), area ("Derbyshire"), distance.
  3. Parsed rows when the input is a coordinate, a Plus Code or a map link: "Coordinates
     53.2134, −1.6750".
  4. Footer: "Searching Wales and England · offline".
- **States:** empty query: recent destinations · no results: "Nothing found in your maps" ·
  no region: "Install a map region" · Parked: full · Idling: typing with Park evidence ·
  Moving: locked view.
- **Safety and driving rules:** no text entry while Moving ([UI §12.1](../../../../specs/2026-10-06-ui-architecture-design.md#121-u2-lockouts-changes-35-10-u2-101-u2-app-model-44)).
- **Components:** ListRow, Chip, Button.
- **Spec refs:** [Navigation §3](../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) · [Navigation §6.4](../../../../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois)

### nav-route-preview — Route preview  [New]
- **Owner:** app:navigation
- **Purpose:** show the route, its profile and warnings before starting.
- **Opens from → goes to:** a search result, a saved place, a library file → Start → nav-turn-card.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night and Day.
- **Content (top to bottom):**
  1. Map with the route; alternatives as grey lines.
  2. Sheet: distance "24 km", time "32 min", arrival "17:40", ascent, surface split, off-road %.
  3. Profile Chips and Avoid Toggles (as nav-page).
  4. Warning Card when used: "Uses a private or non-vehicle way: I have permission" Toggle
     (per route), plus "Check local access rules. Map data may be incomplete."
  5. Buttons **Start** (primary), "Save to library", "Share with ride" (leader of an active ride).
- **States:** loading: "Routing…" · error: "No route found" · Brain unreachable: "Needs the
  Brain" · Parked: full · Moving: locked view.
- **Safety and driving rules:** private ways never without the per-route override ([Navigation §4](../../../../specs/2026-10-07-navigation-addon-design.md#4-profiles)).
- **Components:** Sheet over map, Chip (profile), Toggle, Card, Button.
- **Spec refs:** [Navigation §4](../../../../specs/2026-10-07-navigation-addon-design.md#4-profiles) · [Navigation §7](../../../../specs/2026-10-07-navigation-addon-design.md#7-curated-routes-sharing-and-reports) · [Navigation §8](../../../../specs/2026-10-07-navigation-addon-design.md#8-data-privacy-and-offline-behaviour)

### nav-regions — Settings → Maps: regions  [New]
- **Owner:** app:navigation
- **Purpose:** install, update and remove offline map regions.
- **Opens from → goes to:** Settings → Maps; nav-page "Map regions"; the "Off your
  maps" card.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:**
  desktop Night; hu7 Night Parked; phone Night.
- **Content (top to bottom):**
  1. Free space line "Brain: 41 GB free".
  2. Region rows: name ("England", "Wales"), size, data date, parts (Map · Routing · Search ·
     Elevation), "Update available" Chip, Update Button, Remove.
  3. "Add a region" → a list of regions with sizes.
  4. Caption: "Map, routing and search come from one data date so they agree."
- **States:** downloading: progress "1.2 of 3.4 GB" · error: "Not enough space" · no Brain:
  "Needs the Brain; maps load online" · Parked: full · Moving: locked view.
- **Safety and driving rules:** owner operation; Parked ([Navigation §3](../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions)).
- **Components:** ListRow, Chip, Button.
- **Spec refs:** [Navigation §3](../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) · [Visual §7](../../../../specs/2026-10-07-visual-design-system-design.md#7-maps)

### nav-places — Saved places and waypoints  [New]
- **Owner:** app:navigation
- **Purpose:** places this add-on owns, plus the OS's Home and Work places, and priority waypoints.
- **Opens from → goes to:** nav-page → Saved places → a place → nav-route-preview.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night.
- **Content (top to bottom):** 1. Home and Work rows (read-only here; "Edit in Places").
  2. Saved place rows: name, category, note. 3. Priority waypoints (≤ 3, star icon). 4. "Along
  the route" categories: Fuel · Food · Toilets · Campsites. 5. "Recent destinations" Toggle
  and "Clear".
- **States:** empty: "Long-press the map to save a place" · Parked: full · Moving: locked view.
- **Safety and driving rules:** routes and places are location data and stay on my devices
  ([Navigation §8](../../../../specs/2026-10-07-navigation-addon-design.md#8-data-privacy-and-offline-behaviour), [ADR-0009](../../../../decisions/adr-0009-session-logbook-and-location.md)).
- **Components:** ListRow, Toggle, Button.
- **Spec refs:** [Navigation §6.4](../../../../specs/2026-10-07-navigation-addon-design.md#64-waypoints-places-and-pois) · [Navigation §8](../../../../specs/2026-10-07-navigation-addon-design.md#8-data-privacy-and-offline-behaviour) · [UI §13.4](../../../../specs/2026-10-06-ui-architecture-design.md#134-more--places-changes-34s-more-row-and-124s-order)

### nav-setup — Navigation: first setup  [New]
- **Owner:** app:navigation
- **Purpose:** the Navigation app's setup flow: install a region, pick a profile and voice.
- **Opens from → goes to:** the app framework's install step or first open → nav-regions →
  nav-page.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night.
- **Content (top to bottom):** 1. "Routing works offline on the Brain. Pick your map region."
  → region list with sizes and free space. 2. "Your vehicle": kind from the garage (car, 4x4,
  van, motorcycle) and default profile (Fast). 3. Voice: "Car screen speaks" (the audio
  display), Test voice. 4. "Show speed limit" (off by default; "never logged or scored").
  5. Home and Work: "Set in Places".
- **States:** no Brain: "Navigation needs the Brain" and nothing else · download in progress ·
  not enough space · Moving: locked view.
- **Safety and driving rules:** Parked only ([Navigation §8](../../../../specs/2026-10-07-navigation-addon-design.md#8-data-privacy-and-offline-behaviour)).
- **Components:** Sheet, ListRow, Segmented, Toggle, Button.
- **Spec refs:** [Navigation §3](../../../../specs/2026-10-07-navigation-addon-design.md#3-offline-map-regions) · [Navigation §4](../../../../specs/2026-10-07-navigation-addon-design.md#4-profiles) · [Navigation §5.4](../../../../specs/2026-10-07-navigation-addon-design.md#54-voice) · [Navigation §5.5](../../../../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default)

### nav-settings — Navigation: settings  [New]
- **Owner:** app:navigation
- **Purpose:** the Navigation app's own settings page.
- **Opens from → goes to:** nav-page "…" → Settings; App info.
- **Layout classes:** phone · tablet · desktop · hu5 · hu7 · hu9 · huwide. **Draw first:** hu7
  Night Parked; phone Night.
- **Content (top to bottom):** 1. Voice: on · off; volume; voice engine (system voice, or the
  Brain's offline voice when installed). 2. ETA shows: Arrival time · Time remaining. 3. Speed
  limit: Toggle (off), tolerance "+10 %". 4. Default profile and Avoid toggles. 5. Recent
  destinations: Toggle, Clear. 6. Map regions → nav-regions. 7. Export library.
- **States:** Parked: full · Moving: locked; mute voice is a Drive menu row instead.
- **Safety and driving rules:** speed-limit state never logged, scored or shared ([Navigation §5.5](../../../../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default)).
- **Components:** ListRow, Segmented, Toggle, Button.
- **Spec refs:** [Navigation §5.2](../../../../specs/2026-10-07-navigation-addon-design.md#52-while-moving-the-map-templates-next-manoeuvre) · [Navigation §5.4](../../../../specs/2026-10-07-navigation-addon-design.md#54-voice) · [Navigation §5.5](../../../../specs/2026-10-07-navigation-addon-design.md#55-speed-limit-off-by-default) · [Navigation §5.6](../../../../specs/2026-10-07-navigation-addon-design.md#56-drive-menu-rows) · [Navigation §6.2](../../../../specs/2026-10-07-navigation-addon-design.md#62-import-and-export)
