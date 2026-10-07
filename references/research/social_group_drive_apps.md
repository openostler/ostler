---
title: "Social, group-ride and location-sharing apps — what Vehicles & Map and Social should copy"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, references/research/mesh_networking.md, references/research/addons_catalogue.md, references/vision.md]
summary: >
  Live research (2026-10-07) for the planned Vehicles & Map and Social add-ons. Surveys REVER (LiveRIDE, friend tracking, RLINK bike telemetry), Calimoto and Scenic, Waze (Share Drive, invisible mode, the Facebook-era friends list and its 2026 removal from the privacy policy), Life360 (circles, pause, Bubbles, the 2021 data-sale scandal), Glympse, Google Maps and Apple Find My sharing, Snap Map ghost mode, Strava Beacon, the Harley-Davidson app, Meshtastic (per-channel position precision), Cardo/Sena, Zello and RideMesh for voice, and car-club apps (Roadstr, Strada1, the closed DriveTribe). Finds that the best privacy model is audience × data class × precision × time window, that time-boxed precise sharing beats always-on, that nobody else shows friends' live vehicle data, and that ad-funded car socials die. Ends with styling notes and Copy / Avoid / Decide items mapped to ADR-0009, 0029, 0033, 0036, 0038 and the accounts-sharing spec.
---

# Social, group-ride and location-sharing apps

Research for two planned add-ons: **Vehicles & Map** (browse friends' vehicles on a built-in
live map, opted-in stats, **ghost mode by default**, visibility decided by the accounts and
sharing permissions) and **Social** (friends and groups, messaging, voice and later video,
integrations, over the internet and off-grid meshes). It builds on
[ADR-0029](../../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md), the
[accounts and sharing spec](../../specs/2026-10-06-accounts-sharing-design.md) (§4–§7),
[ADR-0038](../../decisions/adr-0038-mesh-car-to-car-and-off-grid.md) and
[mesh networking](mesh_networking.md); it does not repeat them.

Facts were checked live on **2026-10-07** (sources in §8). Everything is paraphrased.
**(U)** marks what could not be verified today; styling notes are general impressions of
the apps, not checked against current screenshots.

## 1. The apps at a glance

| App | Friends / groups | Live location | Expiry | Privacy controls | Vehicle data to others | Offline | Talk |
|---|---|---|---|---|---|---|---|
| **REVER** (moto) | friends; private or public communities | LiveRIDE: friends on a map, copyable link | ride start/end SMS to safety contacts | per-friend "Friend Tracking" permission | RLINK device: own bike's location, diagnostics, security alerts (owner only) | no | no |
| **Calimoto** (moto) | invite by username to a planned ride | "Group Rides" (beta): opt-in at navigation start, blue dots | per ride | opt-in per ride | none | no; needs signal and movement | no |
| **Scenic** (moto, iOS) | share routes, comments, photos | (U) no group live tracking found | n/a | n/a | none | offline maps (premium) | no |
| **Waze** | historically Facebook / contacts friends | Share Drive: followers see you live until arrival | ends on arrival | invisible mode (hides you, but blocks reports and messages) | none | no | messages (not when invisible) |
| **Life360** | circles | continuous, per circle | Pause (timed); Bubbles 1–6 h | per-circle toggle; Bubble = coarse 1–25 mi radius | driving reports (U) | no | circle chat |
| **Glympse** | none needed | link by SMS, email, WhatsApp | user-set (5 min to 12 h); ends on arrival | viewer needs no account; data deleted 48 h after | none | no | no |
| **Google Maps** | Google account contacts or a link | until arrival, a timer, or indefinite | link max 24 h; account share can be indefinite | per person; reminder emails; on-screen "sharing" icon | battery level | no | no |
| **Apple Find My / Messages** | contacts | Live Location, ETA, Check In | 1 h, end of day, custom, indefinite | per person; arrive/leave alerts set by viewer | battery (U) | **satellite** Live Location | Messages |
| **Snap Map** | friends | always while app used, unless ghost | ghost timer 3 h, 24 h, or until off | **Ghost Mode**; "Select friends" / "all except" | none | no | chat |
| **Strava Beacon** | up to 3 safety contacts | random web URL, 15 s updates, route so far, battery | link dies when the activity ends | contacts need no account | none | no | no |
| **Harley-Davidson app** | groups, events, H.O.G. chapters | (U) live rider tracking reported by third parties, not on the official page | n/a | (U) | H-D Connect: stolen bike's location, shareable (U on detail) | no | no |
| **Meshtastic app** | channels (shared key) and direct messages | node positions on a map with history | none; position interval | **per-channel precision**: 0 = never, 32 = full, 10–19 bits ≈ 23 km to 45 m | telemetry (battery, env.) | **yes, LoRa** | text, delivery ACKs, waypoints |
| **Roadstr / Strada1** (car clubs) | clubs, convoys, RSVP | (U) | n/a | (U) | **virtual garage**: car profiles, mods, drive stats | no | (U) |
| **DriveTribe** (closed Jan 2022) | "tribes" by topic | none | n/a | n/a | posts only | n/a | n/a |
| **Cardo / Sena** | mesh intercom groups in helmets; Cardo bridges to Sena | none | n/a | n/a | none | **yes, own radio mesh** | full-duplex group voice |
| **Zello** | channels (group PTT) | none | n/a | n/a | none | no | PTT, hands-free buttons, VOX |
| **RideMesh** (new) | ride invite codes, no extra sign-up | shared group map | per ride | (U) | none | cloud only, despite the name | group PTT, 1:1 calls without numbers, SOS, crash detection |

## 2. Per-app notes worth keeping

- **REVER.** Two separate trust levels: *safety contacts* get SMS at ride start and end;
  *friends* may be granted live tracking. RLINK, a hidden GPS box on the bike battery, sends
  location, diagnostics and security alerts to the owner's app — the closest commercial
  cousin of Ostler Guardian, but its data stays owner-only (no friend sees your bike's
  stats).
- **Calimoto.** The simplest group model: a planned ride is the group, invites are by
  username, and sharing is asked **at the moment you press Start**, not in settings. It is
  still beta after years, and it needs signal and movement to update, so a stopped rider
  freezes on the map with no age shown (from Calimoto's own help).
- **Scenic.** Social means **routes and ride logs**: share a route before the ride, leave
  photos and comments, get a personal web page of rides. No live group layer was found.
- **Waze.** The cautionary tale. Friends once came only through Facebook, later contacts
  upload; invisible mode hides you after a few minutes but also **takes features away**
  (no reports, no messages), which punishes privacy. The privacy policy dropped the
  find-friends and social-network sections in 2026; Waze Carpool closed in 2022. What
  survives is **Share Drive**: a per-trip live link that ends on arrival.
- **Life360.** The richest controls and the worst trust record. Per-circle sharing, a
  timed pause, and **Bubbles**: a temporary coarse circle (1–25 mi, 1–6 h) per circle,
  which members can "pop" and which auto-pops on a crash. In December 2021 The Markup
  reported that it sold precise location to about a dozen brokers; it then stopped most
  sales but kept one insurer-owned buyer.
- **Glympse and Strava Beacon.** The best "no account needed" pattern: an unguessable link,
  live position plus ETA or route so far, and **automatic expiry** (on arrival, on a timer,
  or when the activity ends). Glympse deletes the data 48 h after.
- **Google Maps and Find My.** Mainstream defaults to copy: choose a duration at share
  time (1 h, end of day, custom, until off), stop per person, a visible "you are sharing"
  indicator, and **reminders** when a share is indefinite. Google caps link shares at
  24 h. Apple can send Live Location **by satellite** when there is no signal, and lets
  viewers set arrive/leave alerts.
- **Snap Map.** Where "Ghost Mode" comes from: one switch hides you from everyone, with a
  timer (3 h, 24 h, until off), plus allow-lists and deny-lists of friends.
- **Harley-Davidson app.** Ride planning and sharing, groups and events, H.O.G. chapters,
  challenges and leaderboards; H-D Connect lets you share a **stolen** bike's location.
  The official page does not mention live group tracking (U).
- **Meshtastic.** Proves off-grid group maps work. Its **position precision per channel**
  (0 to 32 bits; by halving from 10 bits ≈ 23.3 km, 13 bits is about 2.9 km, close to our "coarse ±3 km") is exactly the
  knob ADR-0038 §5 wants. Direct messages show delivery ACKs; waypoints can go to a channel
  or one node.
- **Car-club apps.** Roadstr (about 300k users, 2024) and Strada1 centre on a **virtual
  garage** (cars, mods, drive history, stats) plus convoys and RSVP. DriveTribe, the
  best-funded car social, closed in January 2022 because it was ad-funded and car
  marketing budgets fell.
- **Voice.** Riders already own helmet intercoms (Cardo DMC and Sena Mesh, now bridged);
  Zello is the reference for channel PTT with hardware buttons and VOX; RideMesh bundles
  PTT, 1:1 calls without phone numbers, SOS and crash detection in one ride app.

## 3. Patterns across the field

1. **Visibility is four axes, not one switch:** *audience* (person, group/circle, ride,
   anyone with a link) × *data class* (presence, location, ETA, battery, vehicle stats) ×
   *precision* (none, coarse, place, precise) × *time window* (timer, until arrival, ride,
   indefinite). The spec already has three of them (§5.3 levels, location levels, expiry);
   it lacks a **timer chosen at share time** and **"until arrival"**.
2. **Time-boxed beats always-on.** Every app that is trusted (Glympse, Beacon, Share Drive,
   Find My's one hour) ends sharing by itself; the app with the scandal (Life360) is the
   always-on one.
3. **Ghost must not cost features.** Waze's invisible mode removes reporting and messaging;
   Snap's ghost mode removes nothing but your pin. Users read the first as a penalty.
4. **Ask at the moment of use.** Calimoto asks "share location with the group?" when you
   press Start; Find My asks for a duration when you share. Settings-page toggles get
   forgotten (hence Google's reminder emails).
5. **Nobody shows friends' live vehicle data.** REVER and H-D Connect keep bike telemetry
   owner-only; club apps show a static garage. Opted-in live stats of a friend's vehicle
   (coolant on a hot climb, fuel range in a convoy) is open ground for Ostler.
6. **A viewer without an account matters** for safety contacts (Glympse, Beacon, Google
   links); groups of riders install the app.
7. **Stale positions lie.** Calimoto freezes stopped riders; Meshtastic shows "last heard".
   Showing position **age** is essential off-grid.
8. **Social apps that need a big network die** (DriveTribe, Waze's friends, Waze Carpool).
   Ostler's social layer must be useful with **two people and no server**.
9. **Voice lives in hardware riders already own.** In-app PTT (Zello, RideMesh) is the
   software option; intercom meshes are the norm on bikes.

## 4. Vehicles & Map add-on — sketch

- **Map first.** Full-bleed MapLibre map (ADR-0009: bundled, OpenFreeMap tiles) with *my*
  vehicles and the vehicles shared with me. A bottom sheet lists them: name, vehicle
  silhouette or photo, status (driving, parked, offline since…), position age.
- **Vehicle page** per shared vehicle: the **garage card** (owner-curated: name, model,
  year, photo, mods, a mileage band) plus whichever data classes the share grants (`live`,
  `faults`, `sessions`, `location`, spec §2.4 scopes). Data is pulled on demand and cached
  in memory only (spec §4), so revocation is real.
- **Ghost by default.** A new install shares nothing live. The visibility chip lives in the
  shell's status strip ("Ghost", "Visible to Ride: Peak District · 1 h 20 m left").
- **Visibility sheet** = the four axes of §3.1 over the spec's share levels: who
  (person, group, ride, link), what (data classes), how precise (none, coarse, place names,
  precise, live during a ride — ADR-0029 amendment), how long (timer, until arrival, ride
  end, until off for non-precise levels only).
- **Who looked.** The share audit (spec §5.3) shown to the owner as "Seen by" per share.
- **Head unit while moving:** the shell's map template only, ≤ 6 pins, distance to leader
  and sweep (spec §6); no lists to scroll, no garage pages.

## 5. Social add-on — sketch

- **Groups** (friends, a club, a family) and **rides** (a group + a window + a route), per
  spec §6. A ride is the unit for live precise position, exactly as Calimoto and REVER do.
- **Messaging:** group and 1:1 text, delivery ticks (as Meshtastic), canned replies and
  read-aloud on the driver's head unit while moving; full text for passengers and parked.
- **Voice:** PTT per group first, then calls; video only when parked. Route audio to an
  intercom over the phone's Bluetooth rather than replacing it.
- **Transports:** LAN, Tailscale, the relay (spec §5.4), and the mesh for text, positions
  and alerts only (ADR-0038 §2). Voice and video never over LoRa.
- **Integrations:** invite and share through the share sheet and links (spec §7); no
  contact upload, no Facebook login.
- **Safety contacts:** a ride may notify chosen people at start, end, and on an alert —
  REVER's split of "safety contact" from "friend".

## 6. Styling

What they look like, and what to borrow (impressions, not re-checked against screenshots):

- **Find My, Life360, Google Maps sharing:** a full-bleed map with **round avatar pins**,
  a draggable **bottom sheet** listing people with place name, "updated 2 min ago" and
  battery. Clean, calm, light by default. *Borrow:* the bottom-sheet list and the
  "updated … ago" line under every name.
- **Snap Map:** playful, avatar-led, heat-map of activity. *Borrow:* the one-tap ghost
  toggle with a timer picker in the map's own settings, not buried in account settings.
- **Calimoto, REVER, Scenic:** dark or terrain maps, bright route lines, rider dots in one
  accent colour, ride cards with distance and duration. *Borrow:* the ride summary card
  (it is our trip card, shareable per spec §7).
- **Meshtastic:** utilitarian; node list with SNR, hops and "last heard", map secondary.
  *Avoid* its density on a driver screen; *borrow* "last heard" and signal badges for the
  passenger or parked view.
- **Glympse / Beacon viewer:** a single web page, live dot, ETA or route so far, a
  countdown to expiry. *Borrow* the visible countdown for every time-boxed share.
- **For Ostler:** match the owner's Speedometer reference — **dark full-bleed map**,
  vehicle-silhouette pins (car, bike, truck) with a **heading arrow** and an **age ring**
  that greys out as the fix gets old; presence colour from the unified status vocabulary;
  speed-coloured traces only on one's own trips. The visibility chip uses one distinct
  colour ("visible") against a neutral ghost state, so being visible is never subtle.

## 7. Copy / Avoid / Decide for Ostler

### Copy

| # | What | From | Maps to |
|---|---|---|---|
| C1 | Choose a duration when sharing (1 h, end of day, until arrival, ride end); visible countdown | Find My, Glympse, Google, Share Drive | ADR-0029 §7–§8; spec §5.3 (expiry per share) |
| C2 | Ask "share with the group?" when a ride starts, not only in settings | Calimoto | spec §6 rides; ADR-0029 §9 opt-in |
| C3 | Per-group visibility with allow and deny lists; one ghost switch over everything | Snap, Life360 circles | ADR-0029 §8; spec §5.3 |
| C4 | A coarse level as a first-class choice (Bubble-like); map it to Meshtastic precision bits | Life360, Meshtastic | ADR-0029 amendment (coarse ±3 km); ADR-0038 §5 |
| C5 | "You are visible" indicator always on screen; reminders for long shares | Google Maps | app-model spec §2 (status strip); ADR-0029 §7 audit |
| C6 | Position age on every pin and row; grey out stale fixes | Meshtastic, Find My | ADR-0038 §4 rates; spec §4 "Offline since …" |
| C7 | Safety contacts separate from friends (start, end, alert notices) | REVER, Strava Beacon | ADR-0033 alerts; spec §7 notify-via |
| C8 | Owner-curated garage card (model, mods, photo) as the face of a shared vehicle | Roadstr, Strada1 | spec §4 garage; ADR-0036 (no VIN) |
| C9 | Group PTT with hardware buttons; delivery ticks on messages | Zello, Meshtastic | ADR-0033 driving rules; app-model §4.4 templates |

### Avoid

| # | What | Seen in | Why / maps to |
|---|---|---|---|
| A1 | Selling or "aggregating" location for revenue | Life360 (2021) | ADR-0029 §9 no ads, no tracking; ADR-0009 location stays on device |
| A2 | Friends found by uploading contacts or Facebook login | Waze (old) | ADR-0029 alternatives: no third-party login |
| A3 | Ghost or invisible mode that removes unrelated features | Waze | ADR-0029 §8 privacy must be free |
| A4 | Letting others override your privacy ("pop the bubble") | Life360 | ADR-0029 §8; only your own device's SOS may raise it |
| A5 | Indefinite precise live location by default | Life360, Google account shares | ADR-0029 §8 "live during a ride"; ADR-0009 |
| A6 | A social layer that needs a large network or ad revenue | DriveTribe, Waze friends | ADR-0029 §9 minimal in-house; spec §6 |
| A7 | Plates, VINs or account names on maps or over the air | — | ADR-0036; ADR-0038 §5; spec §5.3 never-shared list |
| A8 | Freezing stopped riders with no age shown | Calimoto | C6 |
| A9 | Anything from a friend or mesh that acts on my car | — | ADR-0033 §6 remote read-only; ADR-0038 §2 |

### Decide (recommendations for the owner)

- **D1 — What ghost hides.** *Recommend:* Ghost (the default) hides **presence, location
  and live signals** from everyone; data classes granted per share that are not live
  (`sessions`, `faults`) stay as each share says. One switch, with a timer (1 h, 24 h,
  until off) when turning visibility on. Maps to ADR-0029 §8 and spec §5.3.
- **D2 — Time limits on precise location.** *Recommend:* `precise` and `live during a
  ride` always have an end (timer, arrival, ride end; at most 24 h); only `none`, `coarse`
  and `place names` may be indefinite. Amends spec §5.3.
- **D3 — Can anyone raise my precision?** *Recommend:* no one else; only my own device's
  SOS or crash alert sends a precise position to my safety contacts, logged. Maps to
  ADR-0033 alerts and ADR-0029 §8.
- **D4 — Viewers without Ostler.** *Recommend:* later, through the relay only: an
  unguessable expiring link showing position, ETA and route so far, no vehicle data, at
  most 24 h, revocable, audited (Glympse/Beacon pattern). Needs an ADR-0029 §7 amendment,
  since shares today are device-to-device.
- **D5 — Garage card contents.** *Recommend:* owner-curated fields only; masked VIN never
  shown to friends, plate hidden by default, photo EXIF stripped; live stats only through
  the share's data classes. Maps to ADR-0036 and spec §4–§5.3.
- **D6 — Discovery.** *Recommend:* friends appear only after an invite (answers spec §13
  Q5 "only after"); no public directory; a club directory on the relay later, opt-in.
- **D7 — Where visibility rules live.** *Recommend:* in core accounts and sharing (one
  permission model, one audit), with Vehicles & Map and Social as two optional apps
  (app-model §3) that only read it. Neither add-on stores its own permissions.
- **D8 — Voice and video.** *Recommend:* PTT first per group over WebRTC on LAN,
  Tailscale or relay; calls next; video only when parked or for passengers; never voice
  over LoRa; on the driver head unit only via a hardware or steering button and the shell's
  driver-safe templates (app-model §4.4, ADR-0033 driving rules).
- **D9 — Mesh precision mapping.** *Recommend:* the bridge sends `coarse` as Meshtastic
  13-bit precision (~2.9 km) and `live during a ride` as full precision on the ride's
  private channel only; `none` is precision 0. Maps to ADR-0038 §4–§5.

## 8. Sources (checked 2026-10-07)

- REVER: [LiveRIDE, ADVPulse](https://www.advpulse.com/adv-news/rever-liveride);
  [RLINK](https://www.motorcyclepowersportsnews.com/rever-announces-new-rlink-connected-motorcycle-device/);
  [communities and friend tracking, Expedition Portal](https://expeditionportal.com/rever-is-the-motorcycle-mapp-for-the-millennials/).
- Calimoto: [Group Rides help](https://support.calimoto.com/hc/en-us/articles/17480044307356-Group-Rides-How-to-Plan-a-Group-Ride);
  [blog](https://calimoto.com/en/blog/article/group-riding).
- Scenic: [App Store](https://apps.apple.com/us/app/-/id1089668246);
  [SlashGear round-up](https://www.slashgear.com/1755865/motorcycle-apps-find-routes-track-rides).
- Waze: [Share Drive and history](https://support.google.com/waze/answer/6262570?hl=en);
  [invisible mode, policy record](https://conductatlas.com/platform/waze/waze-privacy-policy/provision/CA-P-039927/invisible-mode-may-disable-certain-features/);
  [2026 policy change](https://conductatlas.com/change/2026-04-19-waze-waze-privacy-policy-562/);
  [Facebook-only friends, forum](https://www.waze.com/discuss/t/cant-find-facebook-friends/35351);
  [Carpool shut down, 9to5Google](https://9to5google.com/2022/08/25/waze-carpool-shut-down/).
- Life360: [Bubbles, TechCrunch](https://techcrunch.com/2020/10/12/family-tracking-app-life360-launches-bubbles-a-location-sharing-feature-inspired-by-teens-on-tiktok);
  [Bubbles terms](https://legal.corp.life360.com/hc/en-us/articles/16044136535703);
  [data sales, The Markup](https://themarkup.org/privacy/2021/12/06/the-popular-family-safety-app-life360-is-selling-precise-location-data-on-its-tens-of-millions-of-user).
- Glympse: [how it works](https://support.glympse.com/faq/how-does-glympse-work/).
- Google Maps: [location sharing help](https://support.google.com/maps/answer/7326816?hl=en);
  [24 h link limit, 9to5Google](https://9to5google.com/2021/12/07/how-to-share-your-location-with-friends-and-family-using-google-maps/).
- Apple: [share your location](https://support.apple.com/en-us/105104).
- Snap Map: [Ghost Mode, Guiding Tech](https://www.guidingtech.com/use-snapchat-ghost-mode/).
- Strava Beacon: [MBR](https://www.mbr.co.uk/news/strava-introduces-beacon-safety-feature-347131).
- Harley-Davidson: [the app](https://www.harley-davidson.com/us/en/explore/discover/harley-davidson-app.html);
  [H-D Connect stolen-bike sharing](https://harley-davidson.getanchor.io/ca/en/content/h-d-connect.html) (U on detail).
- Meshtastic: [channel position precision](https://meshtastic.org/docs/configuration/radio/channels/);
  [map and waypoints](https://meshtastic.org/docs/software/android/user/map-and-waypoints/).
- Car clubs: [Roadstr, CB Insights](https://www.cbinsights.com/compare/roadstr-vs-waze);
  [Strada1](https://apps.apple.com/app/strada1/id6752026119);
  [DriveTribe closure, The Drive](https://www.thedrive.com/news/43814/drivetribe-is-finally-shutting-down-for-good).
- Voice: [Cardo–Sena live bridge, RideApart](https://www.rideapart.com/news/689551/cardo-update-improved-sena-compatibility/);
  [Zello channels and hands-free, BigRoad](https://bigroad.com/blog/bigroad-review-zello-walkie-talkie-app/);
  [RideMesh](https://mwm.ai/apps/ridemesh/6768055572).
