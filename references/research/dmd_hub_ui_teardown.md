---
title: "DMD Hub web UI teardown — screen by screen, and the screens an Ostler community hub should have"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/dmd_hub_features.md, references/research/dmd2_ui_teardown.md, references/research/social_group_drive_apps.md, references/research/app_teardown_speedometer.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Screen-by-screen teardown (2026-10-07) of the public, signed-out side of DMD Hub
  (hub.dmdnavigation.com), captured with Playwright at 1440×900 and 390×844 with WebGL maps
  rendering: shell and navigation, landing feed, Signature Track and GPX detail pages (3D
  satellite map, elevation, stat strip, sidebar facts, comments, report, share row, embed
  dialog), listings and filters, location, profile and leaderboard, communities, events with
  calendar and embed, the public full-screen event live map, the live-trip follower page,
  sign-in walls, and map styles. Measures the styling, compares it with the Social, Vehicles &
  Map and visual design specs, and proposes the screens of an Ostler community hub web app
  and in-shell add-on (ASCII layouts on our tokens and Ostler Night maps), ending with Copy /
  Avoid / Decide items.
---

# DMD Hub web UI teardown

The owner calls DMD Hub "exactly" the social side he wants, including sharing trips there.
The feature inventory is in the sibling note [DMD Hub feature catalogue](dmd_hub_features.md)
(link controls, visibility states, share levels, server needs); DMD2's own app UI is in
[DMD2 UI teardown](dmd2_ui_teardown.md). **This note is about screens**: what each page looks
like, how it is laid out on desktop and phone, and what Ostler's hub screens should be. It
does not repeat the catalogue's feature lists or its Decide items; it adds UI decisions.

**Method.** Playwright (Chromium, WebGL via SwiftShader) captured 30 public pages at desktop
1440×900 and phone 390×844, full page plus a map-in-view shot, and an interaction pass
(elevation toggle, embed dialog, report, calendar menu, satellite switch). All captures were
read; they live in the session scratchpad, not the repo. No account was created and nothing
was signed into. Signed-in screens (planner, GPX list, Live Adventures, upload, edit,
visibility, group pages) were **not reachable**; where they are described, it is from the
public DMD docs and the Hub's own marketing renders, marked **(U)**. All checked 2026-10-07.

## 1. Coverage: what is public and what is walled

| Signed out | Pages (all captured at d and m) |
|---|---|
| **Public** | landing feed; Signature Tracks list and detail; **GPX file detail** (by URL); locations list and detail; services, videos, news; events list, detail and **event live map**; profiles and Top Contributors; communities (empty); marketing pages (organisers, live trip, OSM, mission); sign in and register |
| **Sign-in wall** | GPX Files list ("registered users only"); Live Adventures; planner (redirects to sign-in) |
| **Not seen** (link-only or signed in) | live-trip follower page and journals, Riding Groups, upload and edit, visibility switches: docs and marketing renders only (U) |

The walls are inconsistent: the GPX list is walled but every GPX detail is public by URL, and
Live is walled while an event's live map is public. Ostler should pick one rule (Decide 8).

## 2. Shell and navigation

- **Desktop top bar** (`#0b0f1a`, 68 px): logo; menus *GPX Files ▾ · Locations ▾ · Live● ·
  Videos · Events · Planner · Activity ▾ · About ▾*; one cyan **Sign In** pill. The red dot on
  Live is permanent, not a signal that anyone is live.
- **Phone**: logo and hamburger only (a full-height drawer of the same tree); no bottom bar and
  no header search; search exists only per list.
- **List pattern** everywhere: an icon + "<Thing> HUB" title card with one sentence and one or
  two buttons, a filter bar, a count ("Showing 1–50 of 1357"), cards, numbered pagination;
  breadcrumbs on details. Footer link columns; a cookie bar with *Essential Only* and *Accept
  All* of equal weight; an iOS app banner.

## 3. Screen by screen

### 3.1 Landing and feed

Desktop: a hero (two-colour "DMD HUB" wordmark, one sentence, *Plan Your Ride* in indigo,
*Find Events*, *Watch Videos*); **four counter tiles** (users 25,567, GPX 589, locations 1,357,
Signature Tracks 15) with coloured top edges; **Latest & Upcoming** image cards with date
badges plus a **LIVE NOW** card that, signed out, offers *Sign in to follow*. Then two columns:
a **post feed** (avatar, name, age, text, one big photo, like and comment counts) and a right
rail with **Monthly Highlights** (top contributors, most favourited locations, most collected
GPX) and a filterable **Activity** stream of video, route and location cards with coloured
type badges. Phone: the same blocks stacked; the feed lazy-loads behind a spinner. A busy
portal that sells volume, but there is always something new on it.

### 3.2 Track detail (Signature Track): the best screen

```
┌ hero: cover photo darkened ─────────────────────────────────────────────┐
│ [Signature Track] [Europe] [Portugal]                                   │
│ GET BEER26 BEER TRACK            (Apotek 48/800)                         │
│ one-line description                                                    │
│ ◯ Maintained by <user> · 520 views     Created … · Updated …   [+ Sign in to collect] │
└─────────────────────────────────────────────────────────────────────────┘
┌ 22 collected · ☆ — 0 ratings ┐ ┌ 86.5 KM │ 1 TRACKS │ 18 WAYPOINTS │ 90% OFF-ROAD ┐
┌ MAP: MapLibre, satellite + 3D terrain, pitched; red trace; POI pins ─────┐
│ (+ − ↑ controls top-left; attribution strip bottom-right)                │
├ ELEVATION PROFILE                         ↑ +560 m  ↓ −501 m   ›        ┤  (collapsed)
└──────────────────────────────────────────────────────────────────────────┘
┌ About this ride (2/3) ──────────────┐ ┌ Ridden by riders: all-time · year · month · 24 h ┐
│ Videos (embedded YouTube)           │ │ Time required: 6 hours                         │
│ Rate this track (sign in)           │ │ Surface: 10 % paved ▬▬▬ 90 % unpaved            │
│ Spotted a problem? [Sign in to report]│ │ Expertise needed                              │
│ Comments (2)                        │ │ Best time to ride: [Spring][Summer][Autumn]     │
│                                     │ │ Suited vehicle types: [Enduro][Adventure]       │
│ #tags                               │ │ Warnings & safety notes (amber card)            │
│                                     │ │ Share this track: in f X ig [</>]               │
└─────────────────────────────────────┘ └────────────────────────────────────────────────┘
```

- **Map**: pitched 3D on satellite imagery with terrain from public elevation tiles, a red (or
  blue) trace, coloured teardrop pins by category. Pitched by default looks great and reads
  poorly: the far half of the route is foreshortened.
- **Stat strip**: four indigo numbers (distance, tracks, waypoints, off-road %); elevation sits
  in a collapsed bar under the map with gain and loss. **Sidebar**: facts as a stack of cards,
  each with its own tinted gradient and border.
- **Report a problem**: reason list, text and an optional pin (*Use my location*); goes to the
  owner's inbox. **Embed dialog**: iframe snippet, *Copy code*, a live preview of the card
  (cover, title, chips, blurb, "View on DMD HUB"), *Open embed page*; events have one too.
- **Phone**: hero, full-width collect button, stats wrap 3 + 1, map ~600 px, then the sidebar
  cards stacked; hero chips and button touch the screen edge.

### 3.3 GPX file detail

A plainer sibling: title card with dates and chips (region, **"282.5 mi" in the viewer's
locale units**, difficulty, off-road %), *All GPX*, **Download GPX** (works signed out),
*Login to Add to Collection*. The map is **Leaflet** on OSM raster with *Roads | Satellite*;
the **elevation profile** is open (gain, loss, max, min, area chart). One route showed
**+34,677 ft gain over 282 mi of road**: raw GPS noise presented as fact. Two map engines and
two layouts for one object type show a Hub grown page by page.

### 3.4 Listings, search and discovery

| List | Filters | Sort and views | Card |
|---|---|---|---|
| Signature Tracks | *Filters* drawer, a row of #tag chips | newest; 15 items, 2 pages | cover, SIGNATURE badge, title, country chip, km, % off-road, blurb, collected / completions / rating |
| Locations | search box, *Filters* (continent, country, state, 19 categories, season, ground type, vehicle type, crowding, rating), **Map** toggle | newest, oldest, A–Z, Z–A; list / compact / grid | photo, favourite count or rating badge, title, country and category chips, surface, vehicle chips, author |
| Services | search, community, category, region, rating | paged (40) | title, chips, blurb, author, *View Details*, *Website* |
| Videos | search, community, category, duration | paged (357) | YouTube thumbnail, chips, author |
| Events | search, community, category, region; **Live now** strip on top | date order | date badge, title, dates, place, type, blurb, organiser, "16 going", *View Event* |
| News | search, filters | paged (44) | title, chips, excerpt, author |

There is **no global search** and no "near me" on the web (the app has *Closest first*).

### 3.5 Location detail

Chips, About, Photos, Reviews and a sidebar: **coordinates with *Copy***, ground type,
crowding, *Navigate (Phone)*, *Google Maps*, vehicles, season, share row; a small Leaflet map.
Coordinates are always exact: a public place has no precision choice.

### 3.6 Profile and leaderboard

A dark hero with a contour-line texture, name, @handle, quoted bio, big avatar and social
icons; three cards: **points** ("134 Points rating"), an explainer, and a **Follow User**
toggle ("Followed by 238"); **Awards** chips (Spot Expert, Spot Master, Author of 2 Signature
Tracks), completed-track cards, a **clustered map of the user's locations and GPX files**,
latest videos and posts. **Top Contributors** ranks users with medal discs, badges and "291
pts". The profile map shows where one person goes, clustered over their home region; Ostler's
must not (§7.2 P7).

### 3.7 Groups and clubs

**Communities** (web) is a filter bar, search, *Create* and an empty state; a request needs an
existing community of **at least 1,000 members**. **Riding Groups** exist only in the apps (U):
an active-group card with a *Share my location* switch that pulses red when off, tabs for
members, chat, files, events and locations, invites by email, expiring link or a "nearby"
six-digit code. So there is **no small-club page on the web**: the gap P4 fills.

### 3.8 Events

- **List**: a *Live now* strip ("Tunesien Rallye · LIVE · 2 riding"), then upcoming events with
  date badges (rendered as stray purple slivers in our capture: a layout bug).
- **Detail**: hero, a registration banner, map card, photo, **Attendance & calendar** (*I'm
  going*, *Add to Calendar ▾* Google or Apple ICS, *Register*, "0 going"), comments; sidebar
  **When & where** (dates, address, phone, coordinates with *Copy*, *Navigate*), types, links,
  share and embed.
- **Event live page** (public): a **full-screen map**, one floating title pill (name + LIVE
  outline badge), zoom and compass, a toast "Riders appear here as they set off". Nothing else:
  the cleanest screen on the site and the shape for Ostler's ride page (P5).

### 3.9 Live trip follower page (marketing renders, U)

Not reachable without a link; the `/live-trip/` page shows it in high-fidelity renders:

```
┌ (AV) <trip name>             ●LIVE ┐          [← HUB][KM/MI][MAP|SAT][RELIEF][3D]
│ <rider> · updated 20 s ago · 15 watching   │   ┌ MOMENTS | CHAT ───────────┐
└────────────────────────────────────┘          │ 12:21 Lunch break · msg    │
   full-bleed map: blue trail, rider puck,       │ 11:16 Miradouro · place    │
   photo / message / place pins                  │ 10:44 Quick stop · photo   │
┌ SPEED NOW 57 km/h ∿∿∿ ┐                        │ 09:29 Fuel stop · msg      │
│ ALTITUDE 745 m │ CLIMB 3641 m │                │ …                          │
│ DISTANCE 146.9 │ MOVING 3:03  │                └────────────────────────────┘
│ TRAIL · WHOLE TRIP ▁▂▃▅▃▂ │
└───────────────────────────┘
```

Phone: the map takes the top half with two small stat chips over it, and *Moments | Chat*
tabs fill the bottom half. Followers may recolour the trail by speed, altitude or slope; a
badge says how much trail is shown ("Trail · last 3 h"). Chat is signed-in only, 200
characters, and never pops up on the rider's unit. This is DMD's Ostler-like screen: dark,
map-first, a hero number with a sparkline, a quiet stat grid, and a sheet. It is close to our
trip detail spec (UI spec §12.2) and should be our shared-trip page.

### 3.10 Planner, upload, visibility, share and sign-in

- **Signed in only (U, docs):** the planner (browser routing on OSM data, send to bike); items
  move **Private → Pending Review → Public**, *Make Public* unlocks after a checklist
  (description ≥ 50 characters, region, best time …) with separate *Allow Download* and *Allow
  HUB Indexing*; a live trip stays private to its link until *List on the HUB*, off for every
  new trip, with a one-time "listed means findable" warning (dmd_hub_features §5).
- **Share row** on every detail: LinkedIn, Facebook, X, Instagram in brand colours, and `</>`
  embed. No copy-link, QR or native share sheet.
- **Sign in**: split screen (form left, a DMD unit on a handlebar right), email, password,
  remember me, a Cloudflare Turnstile check. **Register**: name, email, password (≥ 10 with
  classes), terms. No passkeys, no social login.

### 3.11 Map styles

| Where | Engine | Base | Extras |
|---|---|---|---|
| Signature Track detail | MapLibre GL 4.7 | Esri World Imagery + Esri place labels | 3D terrain from public Terrarium elevation tiles; pitched by default |
| GPX detail, profile, location | Leaflet | OpenStreetMap standard raster ("Roads") | *Satellite* switch |
| Event live | MapLibre | OSM raster | full screen |
| Follower page (U) | MapLibre | planner map, satellite, relief | 3D; trail by speed (yellow → red), altitude, slope (blue → green → red) |
| Planner (U) | MapLibre | OpenFreeMap vector | — |

No dark basemap anywhere: the dark UI frames a bright map, which is the exact problem our
visual spec fixed (§7 there). Attribution is a collapsed info control on MapLibre pages and a
plain strip on Leaflet pages.

## 4. Phone (390 × 844) findings

Everything stacks and nothing is re-thought: a track page is ~5,000 px tall with the map below
a full screen of hero and stat cards; maps inside the scroll take the thumb (no cooperative
gestures: our P2 scroll trap); track heroes have no side gutter; the hamburger is the only
navigation. The two exceptions, the **event live page** and the **follower page**, are
full-bleed map with floating chrome and content in a bottom area: copy those.

## 5. Styling (measured from computed styles)

| Role | DMD Hub | Ostler token (visual spec) |
|---|---|---|
| Page | `#2a2d35` body under a `#0b0f1a` header and footer | `bg` `#0b0d10` |
| Cards | darker grey cards, 1 px border, coloured gradient tints and borders per card | `surface-1` `#14181d`, no border |
| Body text | white at 70 % (`#bfc0c2` effective, ~7.5:1) | `text-1` / `text-2` |
| Primary button | cyan `#00a0f2`, 8 px radius, drop shadow | `accent` `#22a6e0`, `radius-sm` 10 |
| Numbers | indigo `#6366f1`, 22 px bold | `text-1`, `type-num-l` 24/28 |
| Second accent | indigo `#6366f1` for the hero CTA and stats | none: one accent only |
| Display type | "Apotek" (custom, heavy, wide), 48/800 for H1 | Figtree 700, `type-title` |
| Body type | Saira Semi Condensed 17 px (Videos pages use Manrope) | Figtree 15/22 |
| Icons | Boxicons + emoji in user content | Material Symbols, no emoji glyphs in UI |
| Status | red live dot, amber warning card, green/red gain/loss | `alarm`, `warn-bg`, `ok` |
| Stack | server-rendered pages, jQuery, Bootstrap-based theme, Swiper, lightGallery, Leaflet and MapLibre, Google Fonts, Cloudflare | React shell, kit, self-hosted fonts, MapLibre only |

**Verdict.** The palette family (near-black, cyan action, dark cards) is ours already; the
differences are the ones Avoid lists (§9): two accents, rainbow card tints, three typefaces,
brand-coloured share icons, bright maps in a dark UI, pitched 3D by default.

## 6. Against Ostler's specs

| DMD Hub screen | Ostler spec today | Gap or conflict |
|---|---|---|
| Track and GPX detail | Trips trip detail: full-bleed Ostler Night map, sheet with 3×3 grid, donut, speed chart (UI spec §12.2) | Ostler has no **public or link** version of a trip page; one is needed in the hub (§7.2 P2) |
| Follower page | Vehicles & Map §8 relay link (later, ≤ 24 h, no vehicle data) | Same idea; DMD adds delay, trail window, Moments. Fold into §8 |
| Riding Groups, event live | Vehicles & Map §6.1 rides, convoy layer; Social ride channel | Covered in-app; no **web** ride page. Add one, ride-scoped and expiring |
| Feed, likes, follows, leaderboard | Social §1 non-goals: no feed, likes, followers, directory | Conflict by design: these belong to the opt-in hub add-on, never to Social (Decide 6) |
| Profile with a map of places | accounts §14.5 precision ladder, privacy zones | DMD leaks a home region; ours shows vehicles and trips only at granted detail |
| Share row (Facebook, X …) | Social §9: no scraping, no contact upload | Use Web Share, copy link, QR, embed; no third-party scripts (Decide 7) |
| Visibility (Private / Pending / Public, listing switch) | registry audiences me · person · group · household · public-later | Needs `link` and `public` audiences (dmd_hub_features Decide 3) and a UI for them (§7.4) |
| Sign-in walls | none yet (no hub) | Decide 8 |
| Satellite, 3D terrain | Ostler Night/Day on PMTiles, OpenFreeMap fallback; imagery per ADR-0010 | Keep flat Ostler Night default; imagery optional (Decide 3) |
| Speed-coloured trail for followers | Vehicles & Map §3: no speed traces of other people | Only when the owner grants speed (Decide 2) |

## 7. Proposed screens

Two surfaces, one design system. **`ostler-hub-server`'s web app** (public and link pages,
works in any browser, no Ostler install; named in dmd_hub_features §6) and the in-shell add-on
**`ostler-app-hub`** (More → Hub, plus contributions to Trips and Home). Both use the visual
spec's tokens, kit (Card, StatTile, HeroStat, Chip, Segmented, Sheet over map, ListRow) and
**Ostler Night** maps; the web app ships the kit as a package and server-renders public pages
so a link opens fast with JavaScript only for the map.

### 7.1 Rules for every hub screen

1. **Map-first where there is a place** (visual spec §1.2): full-bleed Ostler Night map,
   floating chrome on `surface-glass`, content in a sheet (phone: bottom sheet peek / half /
   full; desktop: 420 px side sheet, `radius-lg`).
2. **One accent**: `accent` only for the primary action and anything live (puck, LIVE pill,
   live countdown). Categories use the three `series-*` slots; status uses ISO hues with words.
3. **Show the audience on every object**: a visibility chip (Only me · Person · Group · Link ·
   Public) in the header of every trip, place, route and post, and on every card the owner sees.
4. **Honest numbers**: smoothed elevation with its source; GPS 1 Hz labelled; "—" for missing.
5. **No points, ranks or speed boards**; counts of contributions and "verified completed" only.
6. **Driver screens get counts only** while Moving (UI spec §12.1); every page below is
   Parked or phone/desktop.

### 7.2 Web hub: sitemap and key layouts

`/` Discover · `/t/<id>` trip · `/r/<id>` route · `/p/<id>` place · `/g/<slug>` group or club ·
`/e/<id>` event · `/e/<id>/live` · `/ride/<token>` live ride (link, expiring) ·
`/help/<id>` help thread · `/u/<handle>` profile · `/v/<id>` vehicle card · `/search` · `/me/...`
(library, shares, inbox, settings).

**P1 Discover (signed out or in).** No people feed for strangers. Desktop: title card "Ostler
Hub" with one search field (vehicles, places, routes, help); a chip row (Routes · Places ·
Events · Help wanted · Clubs) and a **make / model / engine** filter (our differentiator);
then a 2/3 + 1/3 split: a grid of Cards (route and trip cards with a small static Ostler Night
thumbnail and trace, `type-num-l` distance, chips) and a side column "Help wanted on your
vehicles" and "Upcoming near you" (coarse region only). Signed in, a *Following* tab adds a
chronological feed of people and groups you follow; no ranking algorithm.

**P2 Shared trip page** (public or link; the owner's ask):

```
┌──────────────────────────── full-bleed Ostler Night map ─────────────────────────────┐
│ ┌ ← Hub  "Peak loop, Sat 4 Oct"  [Link · until 11 Oct] ┐        [Map|Imagery] [km|mi] ⓘ│
│ │ Disco 2 Td5 · 2003 · by @jd                           │                              │
│ └───────────────────────────────────────────────────────┘                              │
│      trace: series-1 indigo with casing (speed ramp only if the owner granted speed)  │
│      ends trimmed at privacy zones: dashed fade, no pin                               │
│                                         ┌ side sheet 420 (phone: bottom sheet) ──────┐│
│                                         │ HeroStat 142.6 km                           ││
│                                         │ 3:41 duration · 1:02 idle · +1,210 m        ││
│                                         │ ─ Elevation ▁▂▅▇▅▃▂ (smoothed, GPS)         ││
│                                         │ [Overview][Signals][Faults][Notes]  ← tabs  ││
│                                         │ Overview: 3×3 StatTiles per UI spec §12.2   ││
│                                         │ Signals (level "Stats"/"Full log" only):    ││
│                                         │   picker → area line per VSS signal, scrub  ││
│                                         │ Faults (level "Diagnostics"): code, word,   ││
│                                         │   freeze frame, when on the trace           ││
│                                         │ [Download GPX] (if allowed) [Ask for help]  ││
│                                         └─────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

Tabs appear only for the share level granted (catalogue §5 levels: Card, Route, Stats, Full
log, Diagnostics). A Card-level share has no map at all: a vehicle silhouette, the summary
numbers and a place name per end.

**P3 Help thread** ("help me decode this", the owner's other ask): left, the question with the
attached trip or capture at Full-log level, the vehicle chips (make, model, engine, year,
pack) and a **"time-boxed access: 30 days left"** chip; right, replies as ListRows with code
blocks and links to signals in the attached log ("see 00:12:31 on `Engine.Speed`"), and a
*Mark as solved* that can turn an answer into a decode contribution under CC BY-SA
(ADR-0012). No votes or points; "solved by" credit only.

**P4 Group or club page** (the gap in DMD): header with name, kind chip (friends · club ·
ride · safety; accounts §14.6), member count, *Join with code*; tabs **Rides · Routes ·
Events · Members · Files**; a map of the group's shared routes (never members' homes).
Membership-only content needs a signed-in member; a club may publish a public face (name,
about, events) once `public` opens.

**P5 Live ride page** (`/ride/<token>`, link or members): copy DMD's event live page exactly:

```
┌ ● LIVE  Peak District ride · 4 riding · ends 18:00 ┐                    ⓘ
   full-bleed Ostler Night, member pucks (accent for me, text-2 for others),
   leader / sweep badges, meeting point; owner-chosen delay shown as a badge
┌ bottom sheet peek: "Riders appear here as they set off" / list of members ┐
```

It ends at ride end or 24 h, whichever first (Vehicles & Map §6.1), and then shows "This ride
has ended" with no positions.

**P6 Event page**: DMD's layout minus the rainbow: title card, a When & where Card (dates in
the event's zone, place at the organiser's precision, *Add to calendar* ICS, *Navigate*),
Going (Segmented: Going · Maybe · Not going), files locked until the start, comments.

**P7 Profile** (`/u/<handle>`): avatar, name, bio; **Garage** row of vehicle cards (Vehicles &
Map §2.2, basic only unless granted); public routes and trips as cards; "helped with 12
decodes" and "completed 3 routes" counts. **No map of the person's places** and no points.

**P8 Publish flow** (web and in-shell, same steps):

```
1 Choose        2 Level              3 Audience & time          4 Preview → Publish
[trip ▾]   ( ) Card                 (•) Link   ( ) Group ▾       ┌ exactly what leaves ┐
           ( ) Route                ( ) Public (needs review)    │ map with trimmed ends│
           (•) Stats  [signals ▾]   Until: [1 day][7 d][30 d][∞] │ fields list, no VIN  │
           ( ) Full log             Download: [off]              └──────────────────────┘
           ( ) Diagnostics          Delay live trace: [none ▾]   [Publish] (primary)
```

Scrubbing runs on the device before upload (ADR-0036); the preview is rendered from the
scrubbed bundle, not the original; the checklist for Public (description, region, vehicle)
is shown inline, DMD-style.

**P9 My shares** (`/me/shares`, mirrored in the shell): one ListRow per link or publication
with level chip, audience chip, expiry countdown, views, *Revoke* (two taps) and *New link*.

### 7.3 In-shell add-on (`ostler-app-hub`)

| Slot | Screen | Driving rule |
|---|---|---|
| **More → Hub** (new `more:hub` slot) | tabs **Discover · Following · Help · Mine**; Discover as P1 in a phone column | Parked or passenger |
| **Trips → trip detail "…" → Share** | the P8 flow as a Sheet over the trip's own map; the trip page itself is core Trips | Parked or Idling with Park evidence |
| **Diagnose → fault sheet → Ask for help** | P8 preset to Diagnostics level with the fault and freeze frame attached | Parked |
| **Home card** | "2 replies on your help request", "Event tomorrow 09:00" | hidden while Moving; strip shows a count only |
| **Network / sharing (core)** | P9 list lives in core sharing (accounts §14.7), the hub adds rows | — |
| **Head unit** | none while Moving; Parked: Help replies and Events as ListRows ≤ 30 characters | UI spec §12.1 |

### 7.4 The visibility chip and sheet (shared component)

One chip, everywhere an object is shown to its owner: icon + word + time left, e.g.
`lock Only me`, `group Peak 4x4 club`, `link Link · 6 d`, `public Public`. Tapping opens a Sheet
with the same four steps as P8, the audit ("seen 14 times, last by @ali 2 h ago") and *Make
private now*. It is the core chip the accounts spec already defines, extended with `link`
and `public`.

## 8. Feature → Ostler home (UI)

| DMD Hub UI feature | Ostler home | Why |
|---|---|---|
| Track/GPX detail, elevation bar, stat strip | core **Trips** (own); **`ostler-app-hub`** P2 (shared) | Trips owns the record; the hub renders shared copies |
| Follower page, delay, trail window, event live map | **Vehicles & Map** §8 relay link and convoy layer; hub P5 web face | live position is a Vehicles & Map class |
| Riding Groups tabs and invites | core accounts §14.6 + **Social** | already designed |
| Feed, follows, comments, ratings, events, help threads, report, embed | **`ostler-app-hub`** + `ostler-hub-server` | Social excludes them by spec; they need public pages |
| Signature Tracks, planner, GPX library, places | NEW **`ostler-app-routes`** (catalogue Decide 7) | navigation-shaped, not core |
| Services directory | **Maintenance & Garage** (workshops) | feeds service records |
| Videos, News, points, badges, leaderboard | not needed | link out from posts; Avoid 8 |
| Sign in, register | core accounts (passkeys first, OIDC broker later, §14.8) | one identity |

## 9. Copy / Avoid / Decide for Ostler

**Copy**
1. The **event live page**: full-bleed map, one title pill with LIVE, an empty-state toast (P5).
2. The **follower page layout**: floating stat stack with a hero number and sparkline, a
   Moments sheet, a trail-window badge (P2, P5; visual spec §8 HeroStat, Sheet).
3. The **stat strip** and the **collapsed elevation bar** with gain and loss (Trips §12.2, P2).
4. **Facts as chips** and one list pattern: title card, filter bar, count, cards, pagination.
5. **Embed card with live preview**, **report with reason and pin**, **Add to calendar (ICS)**
   and **Copy coordinates**.

**Avoid**
1. **Two accents and per-card rainbow tints**: breaks visual spec §1.5 and §3.
2. **Bright raster or satellite maps in a dark UI** and **pitched 3D by default**.
3. **Two map engines** for one object type: MapLibre only (ADR-0009).
4. **Unsmoothed elevation as fact**; **scroll-trapping maps** and gutterless heroes on phones.
5. **Brand-coloured third-party share buttons** and their scripts.
6. **A profile map of a person's places** and **exact public coordinates** (accounts §14.5).
7. **Inconsistent sign-in walls**.
8. **Points, medals, leaderboards and volume counters** as the front door.

**Decide**
1. **Hub web front end.** Separate site or the shell? **Recommend** a separate server-rendered
   web app in `ostler-hub-server` that imports the shell's kit and tokens as a package (one
   look), with MapLibre lazy-loaded; the in-shell `ostler-app-hub` reuses the same components.
2. **Trace colour on shared trips.** **Recommend** `series-1` with casing by default; the violet
   speed ramp only when the owner's share level includes speed, labelled with its bands;
   never on live ride pages (Vehicles & Map §3).
3. **Imagery and terrain on hub maps.** **Recommend** Ostler Night/Day flat by default; an
   *Imagery* switch only where the imagery licence allows public web use (check per ADR-0010
   source before V-phase); no 3D terrain in v1.
4. **Elevation and signals on public pages.** **Recommend** a smoothed elevation profile at
   Route level and above; speed and other VSS signal charts only at Stats or Full log.
5. **Gamification.** **Recommend** none: no points or ranks; show contribution counts, "solved"
   credits on help threads and verified route completions only.
6. **Feed.** **Recommend** no public feed for signed-out visitors (Discover instead); a
   chronological *Following* feed in `ostler-app-hub` only, opt-in, never in Social.
7. **Sharing out.** **Recommend** Web Share API, copy link, QR code and the embed card; no
   Facebook/X/LinkedIn/Instagram buttons or scripts.
8. **Sign-in walls.** **Recommend** one rule: anything `public` is readable signed out; `link`
   pages need only the link; lists of live riders, help-thread attachments and group content
   need a signed-in member; nothing precise and live is ever `public`.
9. **Viewer chat on live pages.** **Recommend** none for link followers in v1 (read-only page);
   members talk in the Social ride channel; revisit with moderation tools.
10. **Units for viewers.** DMD shows miles and feet from the browser locale. **Recommend** the
    viewer's locale by default with a km/mi Segmented, and speed bands per unit as the visual
    spec defines.

## Sources (all checked 2026-10-07)

- hub.dmdnavigation.com, 30 public pages captured with Playwright at 1440×900 and 390×844 (paths
  in §1), plus computed styles, script and stylesheet lists (fonts, colours, MapLibre 4.7.1,
  Leaflet, tile and elevation sources) and an interaction pass (embed, report, calendar).
- docs.dmdnavigation.com (DMD2 Next): HUB overview, Trip Sharing & Trip Journals, Riding
  Groups, Discover, Live Event, Locations, GPX Manager; used only for signed-in screens (U).
- Caveats: signed-in screens are inferred from docs and marketing renders, not seen; the feed
  and counters change daily; units followed the capturing browser's locale.
