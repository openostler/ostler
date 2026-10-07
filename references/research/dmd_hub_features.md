---
title: "DMD Hub feature catalogue — the model for Ostler's community side"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, references/research/social_group_drive_apps.md, docs/ecosystem.md]
summary: >
  Live catalogue (2026-10-07) of DMD Hub (hub.dmdnavigation.com), the web and iPhone community side of the DMD2 navigation app: account and profiles, GPX library with Locked and Download share links (dates, limits, revoke), Private / Pending Review / Public items, Signature Tracks with verified completions and owner issue inboxes, locations and a services directory, feed, follows, comments, ratings, events with registration and time-locked files, Live Event with SOS, live trip sharing with delay, trail window and journals, riding groups over LoRa and internet, moderation by trust points, and a licence that gates sync. Maps every feature to Ostler and specifies what a new `ostler-app-hub` community add-on and server need, including per-trip share levels for logs and diagnostics.
---

# DMD Hub feature catalogue

DMD Hub is the "connected side" of the DMD2 navigation app for adventure motorcycles and 4x4s,
run by DMD Navigation Lda (Porto, Portugal; the same people as Thork Racing). The owner sees it as
the model for Ostler's social side, including sharing trips with permission levels. This note
lists everything the public site, the public docs and the store listing show, then maps each
feature to Ostler. It complements the platform's
[social and group-drive research](social_group_drive_apps.md) and the approved
[accounts and sharing spec §14](../../specs/2026-10-06-accounts-sharing-design.md).

**Sources (all checked 2026-10-07):** H = hub.dmdnavigation.com public pages (home, `/mission/`,
`/live-trip/`, `/dmd-events/`, `/openstreetmap/`, `/signature-tracks/` and one track page,
`/locations/`, `/services/`, `/events/`, `/videos/`, `/news/`, `/communities/`, `/users/top/`,
one rider page, `/account/register/`, `/privacy-policy/`, `/terms-of-service/`). D = DMD2 manual
at docs.dmdnavigation.com (`/dmdnext/hub/`, `hub-groups/`, `hub-discover/`, `hub-locations/`,
`map-gpx-manager/`, `map-gpx-recording/`, `map-gpx-planner/`, `license-keys/`, the manual
index's "Free vs. Licensed", `/dev/gpx-extension/`, `/dev/lora-api/`,
`/devicemanuals/OBDM1/`). A = App Store listing "DMD HUB" (id6760008925). Not logged in;
GPX Files, Planner and Live listings are sign-in walls, so their inner screens come from D only.
(U) marks what could not be verified.

## 1. What it is, in numbers

| Fact | Value (H, home and list pages, 2026-10-07) |
|---|---|
| Registered users | 25,567 |
| Public GPX files / Signature Tracks | 589 / 15 |
| Community locations / services | 1,357 / 40 |
| Videos / news articles / upcoming events | 357 / 44 / 7 |
| Communities (clubs) | 0 listed; creation needs ≥ 1,000 existing members |
| iPhone app | free, v1.0.32 (24 Sep), 2.7★ from 3 ratings, iOS 26+, CarPlay (A) |
| DMD2 Android app | 100k+ installs, 4.0★ (third-party store tracker, (U) exact) |

Reading: a large account base (accounts are needed for DMD2 sync and licences) with a thin
layer of public content. Most of the value is private sync, groups and sharing, not the feed.

## 2. Feature catalogue

### 2.1 Account, login and profiles

| Feature | Detail | Src |
|---|---|---|
| Sign-up | display name, email, password (≥ 10 chars, upper, lower, digit, symbol), ToS and privacy tick, a honeypot field | H |
| Login | email and password only; "remember me" cookie 30 days; forgot password. **No social login, no passkeys, no 2FA seen** (U for 2FA) | H, D |
| One account, all devices | sign in per device; profiles, GPX, locations and settings follow the account | D |
| Password change | signs the account out of every device and app; "Sign out all devices" on the web | D |
| One person, one account | ToS §3; minimum age 16 (parental consent under 18) | H |
| Profile | avatar, bio, country, social links; profile **public or private**, but a minimum stays public if you post public content | H |
| Rider page | handle, bio (often the bike), points, followers, awards, Signature Tracks authored and completed, their locations, GPX, videos, posts, reviews; Follow; block | H, D |
| Account page tabs | Account & Security → Licenses (keys, release from a device), DMD Devices (registered units) | D |
| Rider profiles (app) | DMD2 "profiles" (settings sets per vehicle) sync through the account | D |
| Deletion | self-service; posts and comments are **deleted, not anonymised**; licence records, crash reports and logs outlive it | H |
| Data rights | GDPR access, rectify, erase, portability (export GPX and locations), EU-only hosting (OVH France), bcrypt, HMAC tokens, no third-party analytics cookies | H |

### 2.2 Content types and their visibility

| Item | Visibility levels | Notes | Src |
|---|---|---|---|
| GPX file | **Private → Pending Review → Public**; plus **Allow Download** (off by default) and **Allow HUB Indexing** (anonymous planner learning) | Public needs a checklist: description ≥ 50 chars, continent, country, best season, vehicle, Photo 1; then staff review | D |
| GPX share link | **Locked** (stays the owner's file, synced, read-only, revocable, needs an account) or **Download** (a copy, no account to download) | dates: available-from, link expiry, access-until (Locked: file is deleted from recipients' devices, even offline); limits: total collections, downloads per user; states Active / Pending / Full / Expired; per-link revoke; editable on the web | D |
| Location (POI) | the app's own locations are private; a **community location** is public with its coordinates | categories, ground type, vehicle suited, visitor level, best time, warnings, photos, tags | D, H |
| Service | public business listing (workshop, rental, school, tuning, shop, accommodation, transport) | ratings 2+ to 5 stars; owner can be a business | H |
| Event | **Public** or **link-only (hidden)**; published after a quick review | | H |
| Trip (live) | private to the link; **listing on Live is opt-in, off for every new ride** | delay, trail window, numbers on/off, pause (§2.6) | H |
| Trip journal | **anyone with the link** or **only me**; re-issue a fresh link; **allow followers to download the GPX** or not | | H |
| Group content | members only: chat, files, events, locations, drawings | group files: download or copy only if the file owner allows; **view-only shares can always be loaded to the map** | D |
| Feed post | public to signed-in users; All or Following | text, one photo | D |
| Video | YouTube link only, public | categories, duration filter, "only from riders I follow" | H |

### 2.3 Discovery, search and filters

- Every list filters by **continent → country (→ US state)**, sorts newest / closest / most
  collected / most ridden / highest rated / most favourited, and has tag chips (H, D).
- Vehicle communities: Motorcycles, 4x4 & Overlanders, SSVs, ATVs; locations add the vehicle
  suited (road-only vehicle, adventure motorcycle, enduro, 4x4 car/pickup/small van…) and the
  ground (paved, unpaved easy/compacted, medium/loosened…) (H).
- Activity feed on the home page filters by content type (news, video, event, service, GPX,
  location) and region; "Monthly highlights": top contributors, most favourited locations,
  most collected GPX (H).
- Load anything onto the map in DMD2; "Save to collection" keeps a live reference to someone
  else's public file (owner's edits reach you) rather than a copy (D).

### 2.4 Social: feed, follows, comments, likes, ratings, reputation

- **Feed** (Social tab): text and one photo, likes, comments, a bell for replies and likes,
  edit/delete own, report a post, block a rider; All / Following; "Shared Content" mixes in the
  last week's public GPX, places, events, services, news and videos (D).
- **Comments** on tracks, locations, events; **ratings and reviews** on Signature Tracks (only
  verified riders), locations, services and GPX; owners reply (H).
- **Points**: location +1, GPX +3, news +3, video +1, event +3, service +2, awarded on approval
  and revoked if the item goes private or is deleted. **More than 20 points ends pre-moderation**
  (auto-publish). Badges: Spot Expert / Master / God, Trail Expert, Video Expert, Signature Track
  completed. Leaderboard at `/users/top/` (H).
- **News** (articles tagged Independent or Sponsored) was dropped from the iPhone app in v1.0.32
  and from the top navigation; the archive remains (A, H).

### 2.5 Signature Tracks (curated routes with an owner)

A Signature Track is a curated route with a named maintainer (H):
- **Verified completions**: DMD2 compares the ridden trace with the track; **≥ 80 % coverage**
  counts, unlocks a badge and increments a live "ridden by" counter (all-time, year, month, 24 h).
- **Owner analytics**: anonymous counts of completions, season and ratings.
- **Issue reports to the owner's inbox**: reason (inaccurate, illegal/restricted, dangerous,
  spam, other), text, optional map pin; the warning stays pinned on the map for every rider
  until the owner marks it solved.
- Page furniture: distance, tracks, waypoints, off-road %, elevation profile, surface split,
  time needed, expertise, best season, suited vehicles, warnings, weather forecast, active fire
  alerts, comments, share, **embed iframe card** for other websites, "collect" count.
- Progress strip on every GPX: distance covered, time invested, first ridden, personal best,
  view ridden stretches, reset (D).

### 2.6 Live trip sharing and journals (the closest thing to "share a trip")

From `/live-trip/` (H) and the Discover guide (D):
- Start on the unit or the iPhone app; pick **trail shown** (none, last 1/3/6/12/24 h, whole
  trip), **delay** (live or 1–6 h behind; covers photos, messages and places too), **show
  speed** and **show trip values** on or off. Send the link: followers need **no account and
  no app**.
- Follower page: map or satellite with 3D relief, trail coloured by speed, altitude or slope,
  speed and altitude, trip stats in the viewer's own units, a moments timeline, local time with
  zone, watcher count on the rider's button. Stops below 5 km/h add no distance or scribble.
- **Moments**: one-tap quick messages ("All good", "Fuel stop", "Flat tyre, fixing it"…),
  photos (gallery photos placed where taken), YouTube links, places (into the trip GPX, My
  Locations, the Hub, or both); edit, hide, delete. Offline posts queue.
- **Viewer chat**: signed-in followers write; anyone with the link reads; on the unit only a
  count, **never a pop-up or a sound while riding**; quick replies when stopped; delete
  messages; block a follower from all your trips.
- **Listing** on Live Adventures is opt-in and off by default, with a one-time warning that a
  listed ride is findable (advice: delay or link-only for rides from home or alone). A listed
  ride drops off after 2 h without a position; "Recently finished" shows journals over 10 km.
- **Pause** stops positions and clocks, no line across the gap. Auto-ends after 24 h idle.
- **Separate recorder**: trip sharing never touches the GPX recorder, trip meter or odometer.
- **One device posts at a time** per account (a "device conflict" prompt hands over); the phone
  can add moments to the unit's trip at the unit's position.
- **Trip Journal**: track, timeline, chat, final values, GPX in a My Trips folder; **Relive**
  playback (camera follows, moments pop up, long stops skipped, chat replays); on the web edit
  title and description, set who can see it and **whether followers may download the GPX**, and
  add photos or notes at a spot after the ride.
- Licensing: Trip Sharing is part of the paid DMD2 licence; followers are free.

### 2.7 Riding groups (D, `hub-groups`)

- Create (name, description, avatar); roles owner, admin, moderator, member.
- **Invites**: email (lands in the Hub inbox, account not needed yet), **link** with expiry
  (never / 24 h / 7 d / 30 d) and join limit (unlimited / 1 / 5 / 10 / 25), usage count, revoke
  with a two-tap confirm; **Nearby** (joining rider shows a 6-digit code for 5 minutes, inviter
  picks by distance). A link never adds anyone without a tap on Join.
- One **active group**; **Share My Location** switch (label pulses red while off); per-group
  **Share GPX** switch; the group's **active GPX** loads on every member's map, retries until
  fetched, hideable per member.
- **Live tracking over LoRa and internet** at once, merged per buddy (freshest wins), LoRa/NET
  badges, Online / Offline / Timed out, Navigate to member, mute a member.
- Tabs: Members, Chat, Files, Events, Locations; shared **map drawings**.
- **Help Me** beacon to the group over both links, with I'm OK; explicitly not an emergency
  service. Paid (licence) feature.

### 2.8 Events and Live Event (H `/dmd-events/`, D)

- Event page: map place, dates in the event's time zone, vehicle and event types (festival, GPX
  ride, roadbook ride, rally race, meetup, presentation, expo, workshop, training), photos,
  website; **Going** / add to calendar / comments; share buttons with link preview cards and an
  **embeddable event card**.
- **Registration**: external link, email or phone, or Hub-run forms with custom questions,
  automatic or manual confirmation, capacity, downloadable list; payment instructions or link,
  mark paid / waived — **the Hub never touches money**.
- **Files delivered to going riders**: GPX and roadbooks fetched ahead, **locked until a set
  time** (server or GPS time, not the unit clock), shown for as long as the organiser allows.
  24 h reminder card, start card, Navigate to start, roadbook auto-opens without replacing one
  the rider already has open.
- **Live Event**: riders see each other; states Active / Taking a break / Need a hand / SOS /
  Paused / Finish safe with colours; crew roles (sweep, lead, first aid, support van); SOS
  alerts crew and nearest riders, spoken on DMD2, a red alarm on the organiser's dashboard, the
  country's emergency number on the rider's screen; a **board** (announcements read aloud,
  regroup pins with Navigate), **private rider↔crew threads** in one organiser inbox; **event
  points** (briefing, start, lunch, fuel, hotel) with show-from times and "be here by"
  roll-call; organiser dashboard shows state, last seen and **battery**; a **public live page**
  (on by default) shows riders as first name + initial, **only those who said yes in the app**.
- All event features are free for organisers and riders.

### 2.9 Route planner, import and export

- Web planner (sign-in wall): pins, "adventure-friendly" routing profiles (road, scenic,
  off-road), weather warnings along the route, fuel stops, then **send the GPX to the bike**;
  the in-app planner mirrors it (routes vs tracks, sections, waypoints); saved plans land in an
  App Planner folder (H, D, A). An App Store review reports the iPad planner failing with HTTP
  403 in July (A).
- **Import**: GPX from device storage (DMD2), "Open with" from other apps; iPhone imports
  locations from Apple Maps and Google Maps links (D, A). KML/KMZ support: (U).
- **Export**: SHARE FILE writes a plain GPX 1.1 (named after the title); journals export GPX
  with places as waypoints; GDPR export of GPX and locations (D, H).
- **DMD HUB GPX Extension** (`dmd:` namespace, public XSD, v1 April 2026): pre-routed geometry,
  turn instructions, surface, regulations, per-waypoint warning cards, SHA-256 integrity hash so
  an externally edited file is recomputed; ignorable by other GPX readers (D).
- **Send to device**: "Navigate to" on any location on the website sets the destination on the
  rider's DMD2 unit (`/api/navigate-to.php`, seen in page code) (H).

### 2.10 Sync between DMD2 and the Hub (how a track travels)

1. **Record** in DMD2 → on Finish, name it and answer three one-tap questions (vehicle,
   difficulty, off-road %) → saved to My Recordings → **auto-uploads** when licensed and online;
   each recording shows Local / Remote / Remote + Local, "Not Synced" offline; crash recovery
   offers resume or discard (D).
2. **On the web** the same file appears in the GPX Manager: rename, trim, edit details, colour,
   folders (sync both ways), share links, publish (D).
3. **Back to the app**: edits, new plans from the web planner, collected community files and
   Locked shares arrive at the next sync; "Download All From Server" on a new device; offline,
   the Hub shows a cached copy flagged as possibly stale; creations made unlicensed upload on
   the first licensed sync (D).
4. **Planner learning**: a one-time consent, "Help the planner learn": anonymous aggregate of
   ridden ways, only ways ridden by ≥ 3 riders, start and end of each ride cut, per-file opt-out
   (Allow HUB Indexing) and "new uploads only / all my files" when switching off (D).

### 2.11 Moderation and safety

- Pre-moderation for new users until > 20 points; staff review of public GPX, events and
  community requests; **Report** on posts and content; staff may unapprove, remove, suspend or
  ban; block a rider; delete chat messages; block a follower from writing on your trips (H, D).
- **Code of Conduct** (`/mission/`): eight riding rules (hold the line, leave no trace, slow
  through villages…) and seven platform rules: don't repost other projects' GPX (TET, BDR, ACT),
  no duplicate locations, original descriptions only, fill in every field, describe events
  properly, no ads outside paid Services or sponsorship, quality over quantity (H).
- ToS bans scraping, false location data that could endanger riders, and sharing GPX you have no
  right to; group location "is not a safety system" (H).

### 2.12 Business model

- **Hub is free**; core DMD2 is free. A **paid licence** unlocks the server side: sync, share
  links, groups, Discover listings (except Live and Videos), Trip Sharing, online layers, weather,
  worldwide fire list, extra map countries. Ways to licence: built into DMD hardware, register a
  DMD device to the account (licences every device you sign in to), legacy Thork Racing keys
  (one device at a time, release on the web), or **Google Play subscriptions of 6 or 12 months**.
  Prices are per country and not public (U) (D, H ToS §9).
- Events, Live Event, Feed, Live, Videos and rider pages are free with an account. Since 17 Aug
  2026 country legal-closure and fire modules are free "on purpose": a subscription must never
  decide whether a rider gets a safety warning (D).
- Revenue around it: DMD dashes and remotes, LoRa modules, the OBD Scanner M1, paid Services
  listings and sponsorships (H, D). No ads, no data sales, no third-party analytics (H).

### 2.13 APIs and openness

- **No public Hub REST API** is documented; page code calls internal endpoints (`/api/social`,
  `/api/user-posts`, `/api/hub-feed-notifications`, `/api/locations-favorite.php`,
  `/api/navigate-to.php`, share links at `/api/share.php?t=…`), and the ToS forbids scraping (H, D).
- Open pieces: the GPX extension (XSD), the **DMD-LoRa Open API** (Android AIDL and broadcasts,
  raw LoRa bytes, "Open Mode" disables group features while another app holds the radio), embed
  iframes for tracks and events (D, H).
- **Improve the Map**: riders answer surface, smoothness, track type, width, signs and reports
  on the handlebar remote; nothing is sent while riding; review then send under **the rider's
  own OpenStreetMap account**, one changeset per area, `source=survey`, 12-hour undo, never a
  simulated ride, signs only tighten (H `/openstreetmap/`).

### 2.14 Vehicle data on the Hub

Almost none. Vehicles appear only as labels: a community (moto, 4x4, SSV, ATV), "what did you
ride it with" and "largest vehicle it suits" on GPX, suited vehicles on locations, bike model in
free-text bios. DMD2 reads OBD through the OBD Scanner M1 dongle (live sensors, read and clear
ECU faults) and TPMS, but **none of it is synced or shared on the Hub** (D; (U) for any hidden
upload). Crash reports carry device data and counts of GPX layers, never route contents (H).
The organiser's Live Event dashboard shows each rider's phone **battery**. This is the gap
Ostler fills: trips with vehicle signals, faults and decode help.

### 2.15 Tech observed (H page code)

PHP back end, Bootstrap 5 forced dark (`data-bs-theme="dark"`), Leaflet maps, lightGallery,
Swiper, Boxicons, Saira Semi Condensed type, iframes for embeds; DMD2 and the iPhone app use the
same account and storage (an older `advhub.net` storage domain appears in the docs). A beta hub
exists at `betahub.dmdnavigation.com` (search result only, (U)).

## 3. Styling

- **Dark only.** Tokens from `hub-ui-v2.css`: background `#0f141c`, surfaces `#161c26` /
  `#1d2430`, lines `#28303d`, ink `#e6ebf3`, muted `#9aa5b6`, accent blue `#3b76f0`, ok
  `#2f9e63`, warn `#eeb268`, danger `#e05252`; spacing 8/12/16/24/40 px. Close to the platform's
  [visual design spec](../../specs/2026-10-07-visual-design-system-design.md) palette family; nothing
  to borrow beyond confirming dark-first works for this audience.
- **Condensed sans** (Saira Semi Condensed) for headings and numbers: dense stats on cards.
- **Card grids** with a whole-card stretched link, small pills for community, category and
  surface, a corner badge for favourites; list pages share one filter bar (region, type, sort).
- **Map-first detail pages**: map, then stat strip (km, tracks, waypoints, off-road %), then
  elevation, then "About", then social (comments, ratings), then the safety block (warnings,
  weather, fire alerts, report).
- **State as colour on pins and rows** in Live Event (active, break, need a hand, SOS), and a
  red share button with a watcher count while a trip is live.
- **On the unit, no interruptions**: counts on buttons, never pop-ups or sounds while riding;
  announcements are read aloud. Matches our lockouts.
- Screenshots: a headless capture rendered blank behind the page preloader; the styling above is
  read from CSS and markup, not images.

## 4. Feature → Ostler map

Homes: **core** (Trips, Diagnose, Network, Security, shell accounts and sharing), approved
add-ons (**Social**, **Vehicles & Map**, **Maintenance & Garage**, **Cameras**,
**Integrations**), or **NEW** add-ons. Two new ones are proposed: **`ostler-app-hub`** (the
community client, plus a self-hostable server) and **`ostler-app-routes`** (GPX library,
planner, import and export, curated routes). If the DMD2 research names a navigation add-on,
`ostler-app-routes` should merge into it.

| DMD Hub feature | Ostler home | Why / how |
|---|---|---|
| Email + password account, one account all devices | core accounts (exists) + **hub** account link | device accounts stay local (ADR-0029 §1); a Hub identity links to them via the Ostler Cloud OIDC broker (spec §14.8) |
| Password change signs out everywhere | core accounts | copy; already in the spirit of §2.3 sessions |
| Public / private profile, rider page | **ostler-app-hub** | a public profile needs the `public` audience (reserved in §14.2) |
| Follow, feed, likes, comments | **ostler-app-hub** | not Social (Social is messaging and calls); the feed is a Hub list |
| Points, badges, leaderboard | **ostler-app-hub**, trust only | keep the trust threshold for moderation; skip public leaderboards (Avoid 3) |
| GPX library, folders, colours, progress | **NEW ostler-app-routes** | Ostler has no route library; Trips holds recordings, not plans |
| GPX visibility Private / Pending / Public, Allow Download | **ostler-app-hub** publishing flow | maps to registry audience `public` plus a "downloadable" flag on the grant |
| Locked vs Download share links, dates, limits, revoke | core sharing (grant fields) + hub links | Locked = a grant with expiry to a person/link audience; Download = an export with a link; both audited |
| Save to collection (live reference) | **ostler-app-hub** | a read grant that follows the owner's edits |
| Signature Tracks, verified completion ≥ 80 % | **ostler-app-routes** + hub | completion is computed on device from Trips; only the completion fact goes up |
| Issue reports to the owner's inbox | **ostler-app-hub** | the same pattern serves "this decode is wrong" reports on shared decodes |
| Community locations, favourites | **ostler-app-hub** (POIs) + Vehicles & Map (show on map) | public POIs need moderation; private places are core privacy zones / saved places |
| Services directory, ratings | **Maintenance & Garage** (workshops) + hub reviews | "find a Td5 specialist" is a garage feature; reviews live on the Hub |
| Events, registration, Going, calendar | **ostler-app-hub** (listing, forms) + Social (ride channel) | a ride is a core group of kind ride (Vehicles & Map §6.1) |
| Files locked until the start | **ostler-app-hub** + routes | grant with `start` in the future; core grants already carry start |
| Live Event: states, SOS, board, crew threads, roll-call | Social (board, threads) + Vehicles & Map (convoy) + core safety contacts | SOS stays §14.5 (safety contacts only, my device only) |
| Public live event page (opt-in per rider, first name + initial) | Vehicles & Map §8 relay link (V5) | needs the relay and the ADR-0029 §7 amendment |
| Live trip link: delay, trail window, pause, numbers toggle | **Vehicles & Map §8** + core `location` grants | copy the delay and trail-window controls into the grant sheet |
| Listing a live ride for strangers | **ostler-app-hub**, later | `public` + `live` breaks the 24 h precise cap only if bounded; see Decide 4 |
| Moments (quick messages, photos, places) | Social (ride channel) + Trips (notes, ADR-0010) | quick replies only Parked; never typing while Moving |
| Viewer chat, no pop-ups while riding | Social | matches Social §8 driver rules |
| Trip Journal + Relive | **core Trips** (playback exists) + hub publish | the journal is a Trips view; publishing is a grant |
| Separate share recorder vs GPX recorder | core Trips | Ostler already records one logbook; sharing is a view of it, not a second recorder |
| One device posts location at a time | core sharing | copy: per-user "position source" with handover prompt |
| Riding groups, invites by email / link / nearby code | core groups (§14.6) + Social | copy the link expiry and join-limit options, the two-tap revoke and the nearby code |
| LoRa + internet merged tracking | Vehicles & Map §6.2 + ADR-0038 | already designed; DMD validates it |
| Group active GPX, map drawings | **ostler-app-routes** + Vehicles & Map | |
| Web planner, send to the car | **ostler-app-routes** | "send destination to head unit" is a Read-class action to our own device |
| GPX import / export, GPX extension | **ostler-app-routes**; core Trips exports GPX | read the `dmd:` extension, write plain GPX 1.1 |
| Help the planner learn (k ≥ 3, ends cut) | **ostler-app-hub**, off by default | pattern reused for anonymous fault statistics (Decide 6) |
| Improve the Map (OSM, own account, review then send) | **Integrations** | Ostler's analogue is contributing decodes to the CC BY-SA store (ADR-0012) |
| Licence gating sync | not needed | sharing is device-to-device and free; only hosted relay/Hub costs money |
| Safety modules free on purpose | core principle | copy as a rule: no safety alert behind a paywall |
| Report, block, pre-moderation, CoC | **ostler-app-hub** | needed before anything is `public` |
| Embeds and link cards | **ostler-app-hub**, later | |
| GDPR export, delete | core (device data) + hub server | Hub deletion must reach every copy and collection |
| OBD dongle data (not shared) | core Diagnose | Ostler's edge: share it, with levels (§5) |

## 5. Per-trip sharing with permission levels (the owner's ask)

DMD's model is the best public example of per-item sharing: each item has a **visibility** and
each link has a **mode, dates, limits and a revoke**. Ostler needs the same shape, extended to
vehicle data. Proposed trip share levels, each a preset over registry classes (§14.1):

| Level | Classes and detail | Typical audience | Default limits |
|---|---|---|---|
| 1. Card | `trips` summary (distance, time, vehicle card basic), no trace | public, group | indefinite |
| 2. Route | + `location` place or precise trace, **privacy zones trim ends** | person, group, link | precise ≤ 24 h unless the owner republishes a static trace (Decide 4) |
| 3. Stats | + selected `live` signals as aggregates (speed, coolant, boost min/avg/max) | group, link | indefinite |
| 4. Full log | `trips` full: every decoded signal over time, scrubbed (ADR-0036) | person, a "decode help" group | 30 days, revocable, Locked (no download) by default |
| 5. Diagnostics | `faults` + freeze frames + readiness for that trip | person (mechanic), group | 30 days |
| 6. Capture for decoding | raw bus capture, scrubbed: **not a class today** | person or the decode project only | needs a new sensitive class (Decide 2) |

Each level gets DMD's link controls: **Locked** (view in Ostler or the viewer, follows edits,
revocable, deleted on access-until) or **Download** (export file, copies survive revoke),
available-from, link expiry, access-until, total collections, downloads per person, Active /
Pending / Full / Expired states, and one audit trail. A help request ("help me decode this
on my 2003 Td5") attaches level 4 or 6 to a Hub thread whose readers get a time-boxed grant, and
an answer can become a decode contribution under CC BY-SA (ADR-0012).

## 6. What a community hub add-on needs

**`ostler-app-hub`** (client add-on, its own repo, ADR-0042) plus **`ostler-hub-server`**
(self-hostable, AGPL; one flagship instance as an Ostler Cloud product, never the only option,
ADR-0028):

1. **Identity**: Hub accounts linked to device users through the OIDC broker (§14.8); passkeys
   and 2FA from day one (DMD has neither); one person, one account; age floor 16.
2. **Registry changes**: open the reserved `public` audience and add a **link** audience
   (anyone with an unguessable URL), both refused for `audio`, `video`, raw captures and live
   precise location beyond the 24 h cap; VIN never (ADR-0036).
3. **Publish pipeline on the device**: scrub (VIN, plate, privacy-zone trims, EXIF), preview of
   exactly what leaves, then upload a signed bundle; the server never sees unscrubbed data.
4. **Objects**: profiles, posts, trips (levels 1–5), routes, POIs, workshops, events, groups and
   clubs, help threads, decode contributions; each with Private / Pending / Public and
   per-link controls (§5).
5. **Social layer**: follow, feed (All / Following), comments, likes, ratings and reviews with
   owner replies, notifications (counts only on driver screens).
6. **Discovery**: filters by region, **make / model / engine / year**, vehicle type, data
   class (has full log, has faults), tags; sorts newest / closest / most useful.
7. **Moderation**: trust threshold before auto-publish, review queue, report with reasons and a
   pin, block, owner issue inbox, code of conduct (including "no reposting other projects'
   decodes or routes"), takedown and appeals, audit log.
8. **Events and clubs**: listing, Going, registration forms, capacity, CSV export, payment info
   only (no money handling), files locked until start, public live page opt-in per member.
9. **Sync**: offline queue, Local / Remote / Both states, conflict rule "device wins for
   recordings, server wins for metadata edits made on the web" (U for DMD's rule).
10. **Open API** (documented, unlike DMD) with scoped tokens (ADR-0029 §2.4), rate limits,
    and federation left open (ActivityPub-style later, not P1).
11. **Driving rules**: nothing from the Hub on a driver screen while Moving except counts and
    convoy markers (UI spec §12, Vehicles & Map §7).
12. **GDPR**: export everything, delete everywhere including collected Locked copies, EU
    hosting for the flagship instance.

## 7. Copy / Avoid / Decide for Ostler

**Copy**
1. DMD's **Locked vs Download** link model with available-from, expiry, access-until, collection
   and download limits, per-link revoke and state badges — as fields of core grants
   (accounts spec §14.2), not a Hub-only feature.
2. **Live trip controls**: delay (1–6 h), trail window (none, 1–24 h, whole), speed and values
   toggles, pause with no line across the gap, watcher count, auto-end after 24 h idle — into the
   Vehicles & Map visibility sheet and §8 relay link.
3. **Listing off by default** with a one-time "a listed ride is findable" warning; matches
   ghost-by-default (§14.3).
4. **Publish checklist plus review** for public items, and **trust-gated auto-publish**.
5. **Owner issue inbox** with pinned warnings until solved — reused for shared decodes and routes.
6. **Verified completion** computed on the device (≥ 80 % coverage), only the fact uploaded.
7. **Nothing sent while riding**, review then send, under the user's own account, 12-hour undo —
   the Improve the Map rules, applied to decode contributions (Integrations, ADR-0012).
8. **Safety features never behind a paywall.**
9. **One device posts position at a time**, with a visible handover prompt.
10. **Event files locked until a server/GPS time**, fetched ahead for no-signal starts.

**Avoid**
1. **A licence gating sync and sharing**: Ostler sharing is device-to-device and free (ADR-0029);
   only hosting costs.
2. **Email and password only**: keep passkeys first (accounts spec §2.2).
3. **Points per item and a public leaderboard**: DMD needs a code of conduct against volume
   posting; use trust for moderation only.
4. **Location submissions public with no precision choice**: Ostler places carry the §14.5 ladder.
5. **No public API and an anti-scraping clause as the only interface**: document ours.
6. **Hard-deleting a person's comments in other people's threads** without a tombstone: breaks
   help threads (Decide 5).
7. **A separate trip-share recorder**: one logbook in Ostler (ADR-0009); sharing is a view.

**Decide**
1. **Hub topology.** Central only, self-hosted only, or both? **Recommend both**: an AGPL
   `ostler-hub-server` anyone can run, with one flagship instance as an Ostler Cloud product
   (ADR-0028); federation later.
2. **Raw captures for decode help.** Registry forbids raw captures as a class. **Recommend** a new
   `sensitive` class `captures` (scrubbed per ADR-0036, never in a preset, audience person or the
   decode project only, max 30 days, no `public`, no `link`), via an amendment to §14.1.
3. **`link` audience.** Add "anyone with the link" to the registry? **Recommend yes**, for
   `trips` card/route/stats, `faults` and `vehicle_card`; never for `live` location beyond a
   ride's 24 h window, `audio`, `video` or `captures`.
4. **Static traces in public.** Does a published, finished trip trace count as `location`
   precise (≤ 24 h)? **Recommend** a distinct detail `trace_published`: a finished, trimmed,
   delayed-by-at-least-24 h trace may be indefinite at `public`, only by an explicit publish act.
5. **Account deletion.** Delete or anonymise posts? **Recommend** delete personal data and
   replace answers in help threads with "[deleted user]" tombstones, with a per-account choice to
   delete everything.
6. **Anonymous aggregates** (fault frequency by model, like "help the planner learn"). **Recommend**
   off by default, k ≥ 5 vehicles per statistic, no VIN, no trip ends, per-trip opt-out.
7. **Routes and planner home.** **Recommend** a new `ostler-app-routes` add-on (library, planner,
   import/export, curated routes), merged with any navigation add-on the DMD2 research proposes.
8. **Paid tiers.** **Recommend** free Hub accounts and features; charge only for the flagship
   instance's storage and the relay, never for safety, sharing or decode help.

## 8. Caveats

- Not signed in: the GPX list, planner, Live list, rider dashboards, group pages and report
  flows on the web were seen only through the manual; their web UI is (U).
- Subscription prices are not published; ratings and install counts change daily.
- Screenshots failed (blank preloader in headless capture); styling comes from CSS tokens.
- DMD ships often (iPhone app v1.0.23 → v1.0.32 in about three months); recheck before specs.
