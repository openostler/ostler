---
title: "Community hub architecture — sharing trips, routes, garages and decoding logs; groups, clubs, events; federation, storage, moderation and law"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-07-social-addon-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-06-logs-at-scale-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md]
summary: >
  Live research (2026-10-07, R6) on building an open community hub for Ostler, the DMD Hub equivalent: shared trips, routes, garages and decoding logs, with groups, clubs, events and comments. Prior art (wanderer, FitTrackee, FitPub, Endurain, Dawarich, traccar, OsmAnd Cloud, GoToSocial, Lemmy) is AGPL Python/TS/Go with PostGIS and object storage. Recommends one AGPL codebase that clubs can self-host and Ostler runs as the official instance; Python + PostgreSQL/PostGIS + S3 storage + PMTiles; device linking by OAuth device flow; per-trip share levels mapped to the `trips` data class; no federation until H5, then outbound-only ActivityPub. Lists UK OSA, EU DSA and GDPR duties of an official instance. Copy/Avoid/Decide.
---

# Community hub architecture

**Question (R6).** How should Ostler build an open community hub where people share trips,
tracks, routes, vehicle garages and decoding logs, and run groups, clubs, events and
comments, in the way [DMD Hub](https://hub.dmdnavigation.com/) serves DMD2 riders? What
stack, which repos, whether to federate, how to store large logs, how hub accounts link to
local Ostler users, and what running an official instance costs in law and in operations.
Web facts were checked on **2026-10-07**; anything not verified is marked **(U)**. Feature
teardown of DMD Hub itself is the sister notes' job; this note is the architecture.

**Bottom line.**

1. **Build it, as one AGPL codebase with two deployments:** an official instance run by
   Ostler for discovery, and self-hosted instances for clubs. Same code, same API; a device
   can link to several hubs. Do **not** put it in the closed `ostler-cloud` (ADR-0013).
2. **Publishing is a grant, not a sync.** A trip reaches a hub only when its owner grants the
   `trips` class (accounts spec §14.1) to a hub audience at a chosen level. Ghost by default;
   the device pushes, the hub never pulls and never reaches the car (ADR-0033 §6).
3. **Python server, TypeScript web, PostgreSQL + PostGIS, S3-compatible object storage,
   PMTiles for aggregate map layers.** This matches ADR-0035 and every Python prior art
   surveyed (FitTrackee, Endurain).
4. **No federation before H5.** ActivityPub is costly (moderation of remote content,
   best-effort deletion, signature plumbing) and buys little for a niche. Later: outbound
   publishing of public routes and events, plus club Group actors, allowlist only.
5. **Running the official instance is a regulated activity.** It is a user-to-user service
   under the UK Online Safety Act 2023 and a hosting service under the EU DSA, and it
   processes location data under (UK) GDPR. The burden is manageable for a small operator if
   H1 allows **no image uploads**, sets a minimum age, and has a named accountable person,
   a report flow, a DPIA and a written risk assessment before launch.

## 1. What the hub is, and is not

| Is | Is not |
|---|---|
| A website and API where people **publish** trips, routes, garages and decoding logs at a chosen level, and **meet**: clubs, events, comments | A relay or tunnel to the car (that is Ostler Cloud, ADR-0028) |
| An optional **add-on**: `ostler-app-hub` in the shell, `ostler-hub` as the server | A dependency: Ostler stays complete without it (GOALS, ADR-0029 "local-first") |
| The **public** audience the accounts spec reserves ("not before club pages", §14.2) | A messenger: chats, PTT and calls stay in Social, peer to peer |
| A place to ask for **decoding help** with a full log, shared with named helpers | The source of truth for decodes: that stays the pack's signal store and PR review |

The Social spec's non-goals ("no feed, likes, followers, public directory", §1) stay true
**for Social**. The hub is where a feed and a directory live, opt-in, so this note asks for
an amendment to ADR-0029 §9 (which allowed "a minimal in-house feed") rather than to Social.

## 2. Prior art

| Project | Licence | Stack | What it shares | Federation | Lessons |
|---|---|---|---|---|---|
| **wanderer** (trail database) | AGPL-3.0 | SvelteKit, PocketBase (Go/SQLite), Meilisearch; Valhalla routing | trails (GPX, KML, FIT…), lists, summit logs, photos, comments; public/private/shared visibility; OAuth2 and OIDC login | **ActivityPub since v0.17**: trails, lists, comments and summit logs as `Note` with the GPX as a `Document` attachment (`application/xml+gpx`); Create/Update/Follow/Like. v0.21 fixed remote actors deleting local trails and reading private ones | Closest analogue. Federation landed security bugs after release; plain `Note` keeps Mastodon compatible but drops the route semantics |
| **FitTrackee** 1.3.5 | AGPL-3.0 | Python/Flask, Vue 3 + TS, PostgreSQL + PostGIS, Leaflet/OSM | workouts from GPX/FIT, equipment, comments, likes; visibility private / followers / public; moderation and admin tools; data export; OAuth 2.0 apps | on the provisional roadmap only (U), discussed with FitPub | The Python + PostGIS shape we want; visibility per workout **and** per map (U, from memory of earlier releases) |
| **FitPub** | open source (U) | Java 25, Spring Boot 4, Thymeleaf, PostgreSQL + PostGIS | FIT/GPX workouts, heatmaps, records | **federates by design**: public / followers / private, **privacy zones** around start and end | Privacy zones are table stakes for public tracks |
| **Endurain** | AGPL-3.0 | Python FastAPI, SQLAlchemy/Alembic, Vue 3 + TS, PostgreSQL | activities (GPX/TCX/FIT), Strava and Garmin import | none | Python + FastAPI works; the project is in a feature freeze to harden foundations, and moved to Codeberg |
| **Dawarich** | AGPL-3.0 | Ruby on Rails | location history, trips, family sharing "with consent", imports from OwnTracks/Google/GPX, GPX/GeoJSON export | none | Per-member consent toggles for live sharing |
| **traccar** | Apache-2.0 (U on this page; long-standing) | Java server, web and phone apps | live tracking of GPS devices and phones, geofences, trip reports, share links | none | The reference for live tracking and device protocols; hosted and self-hosted from one code |
| **OsmAnd Cloud** | app GPL-3 (U); service closed | — | syncs tracks, favourites, settings, OSM edits; Pro 3.15 GB, free 5 MB | none, and **no sharing with others** | Sync is not sharing; keep them separate |
| **Organic Maps / CoMaps** | Apache-2.0 (U) | C++ | no accounts; KML/GPX export only | none | A share sheet is sometimes all people need |
| **DMD Hub** | closed | (U); hosted at OVH, France | GPX tracks (589), locations (1,357), events, live sharing in riding groups, videos, trip planner; 25,567 users; public/private per item | none | Its privacy policy is a good template: OVH under a DPA, live group positions **not stored beyond the active session**, minimum age 16, three cookies, no analytics |
| **GoToSocial** | AGPL-3.0 | Go, SQLite or PostgreSQL, ~250–350 MiB RAM | microblog (Mastodon API) | yes; blocklist default, **allowlist mode** (experimental), interaction policies | Allowlist federation and "who may reply" are the right defaults if we ever federate |
| **Lemmy / Mbin / PieFed** | AGPL-3.0 | Rust / PHP / Python | link aggregation in communities | Group actors (FEP-1b12) (U) | Club = Group actor pattern |
| **Mobilizon** | AGPL-3.0 (U) | Elixir | events and groups | ActivityPub `Event` (U) | The event object model to copy if we federate events |

Sources: [wanderer](https://wanderer.to/), [changelog](https://wanderer.to/changelog),
[federation docs](https://wanderer.to/develop/federation);
[FitTrackee docs](https://docs.fittrackee.org/en/), [features](https://docs.fittrackee.org/en/features);
[FitPub](https://git.arch-linux.cz/Oscloud/fitpub);
[Endurain](https://github.com/endurain-project/endurain);
[Dawarich](https://github.com/Freika/dawarich); [traccar](https://www.traccar.org/);
[OsmAnd Cloud](https://osmand.net/docs/user/personal/osmand-cloud/);
[DMD Hub](https://hub.dmdnavigation.com/), [its privacy policy](https://hub.dmdnavigation.com/privacy-policy/);
[GoToSocial](https://docs.gotosocial.org/en/latest/). All 2026-10-07.

**The cautionary tale.** Komoot was bought by Bending Spoons in March 2025 and lost about
85 % of its staff; users went looking for alternatives
([BikeRadar](https://www.bikeradar.com/news/komoot-acquisition),
[DC Rainmaker](https://dcrainmaker.com/2025/03/komoot-acquired-history-says-this-wont-end-well.html)).
A hub whose code is AGPL and whose content can be exported in full survives its operator.
That is the strongest argument for "self-hostable and official" over "official only".

## 3. Self-hosted, official, or both

| Option | For | Against |
|---|---|---|
| **Official only** (closed, in `ostler-cloud`) | one place to find things; one moderation policy; revenue | single point of failure (Komoot); clubs with private data must trust us; the full OSA/DSA burden lands on us for every club |
| **Self-hosted only** | no regulatory burden on Ostler; club data stays with the club | no discovery; most clubs will not run a server; fragmented |
| **Both, one AGPL code** (recommended) | discovery on the official instance; privacy and control for clubs; survives the operator; matches ADR-0012's "anyone hosting a modified copy publishes it" | two deployment profiles to test; operators of self-hosted hubs carry their own legal duties (we say so in the docs) |

The **device links to hubs, plural**: a club hub for the club's routes and logs, the
official one for public routes. No hub-to-hub federation is needed for that; the device is
the join point, exactly as Ostler devices already pin peers (accounts spec §5).

## 4. Architecture

```
 Ostler device (Brain or phone)                       ostler-hub (official or club)
 ┌─────────────────────────────┐   HTTPS, OAuth     ┌──────────────────────────────┐
 │ Trips (core) ── grant ──────┼──device token────▶ │ API (Python, ASGI)           │
 │ ostler-app-hub (shell add-on)│  upload: tus/S3   │  ├ PostgreSQL + PostGIS      │
 │  publish · link · browse    │  presigned PUT    │  ├ job queue (in Postgres)   │
 │ scrubber: VIN, privacy zones│ ◀── read-only ──── │  ├ S3-compatible objects    │
 └─────────────────────────────┘   (hub never       │  ├ PMTiles (aggregates)     │
                                    calls in)       │  └ web (TypeScript/React)    │
                                                    └──────────────────────────────┘
```

**Components.**

- **API server:** Python 3.12+, an ASGI framework (FastAPI or Starlette), SQLAlchemy and
  Alembic, as Endurain does. OpenAPI generated, so the web and `ostler-app-hub` get
  generated TS types (ADR-0035 "types that cannot drift").
- **Database:** PostgreSQL with PostGIS (FitTrackee, FitPub): bbox and corridor search,
  simplified geometries, clubs, events, comments, reports, audit.
- **Jobs:** a Postgres-backed queue (one less service than Redis) for parsing uploads,
  scrubbing checks, thumbnails, tile builds, deletion fan-out.
- **Objects:** any S3-compatible store (Cloudflare R2, Hetzner, MinIO or Garage for clubs).
  Originals are content-addressed and zstd-compressed; never served directly to the public.
- **Search:** PostgreSQL full-text first; Meilisearch (wanderer) only when measured.
- **Web:** TypeScript + React on the visual design system tokens; MapLibre with the Ostler
  Night/Day styles (ADR-0009 amendment). Server-rendered share pages with Open Graph images,
  because hub links travel through WhatsApp (Social spec §9).
- **Deployment:** one container image plus Postgres and an S3 bucket; a `docker compose`
  for clubs (wanderer's "90 seconds" bar), the same image on the official instance.

**What the hub never does.** It never connects to a device, never holds a device key that
can command anything, and never receives a VIN, its HMAC, a raw identity reply or audio
(ADR-0036, ADR-0010). The device pushes; the hub is a remote path, read only (ADR-0033 §6).

## 5. What can be shared, at which level

The owner wants per-trip sharing with permission levels, including a full log for help with
decoding or diagnostics. Map it onto the one registry (accounts spec §14.1) rather than a
second vocabulary: hub audiences are new **audience kinds**, levels are **class × detail**.

| Hub level | Classes and detail | Default audience allowed | Safeguards |
|---|---|---|---|
| **Card** | `trips` summary; `vehicle_card` basic | public | no trace; distance, duration, region name only |
| **Route** | `trips` summary + `location` place/precise trace | public, club | **privacy zones**: trim 500 m (user-set) around home, work and start/end; time stripped or rounded; never live |
| **Live follow** | `location` live + `presence` | link, club, ride | **≤ 24 h, always** (§14.5); not stored after the session (DMD's rule); off by ghost |
| **Diagnostics** | `faults` + selected `live` signals over a window | named helpers, club "help desk" | time-boxed (7 days default); no location unless also granted |
| **Full log** | `trips` full (signals + trace) | **named helpers only**, never public | time-boxed; helper sees it in the hub viewer; download only if the owner ticks it; scrubbed (§7) |
| **Decode contribution** | scrubbed frames + notes + the owner's hypothesis | public under **CC BY-SA 4.0** | explicit licence tick; ADR-0036 scrub; feeds a pack PR, never the signal store directly |
| **Garage** | `vehicle_card`; `maintenance` history (no costs) | club, public | plate hidden unless ticked; EXIF stripped; "for a buyer" preset (no locations) |

A **help request** is a hub object: "Td5, EGR candidate, full log attached, shared with
@helper until 14 Oct". A helper may ask for more (another class or a longer window); the
request lands on the owner's device as a card and is answered there. Nothing widens by
itself; every grant, view and download is in the device's audit and the hub's access log.

## 6. Linking hub accounts to local users

Hub accounts are **their own identity** on the hub (email plus passkey or password), because
the hub is a public HTTPS site and can do what a device cannot (accounts research: social
login needs a public redirect). That makes the hub the natural home for Google or Apple
login **on the hub**, while devices stay local-first.

- **Device linking:** OAuth 2.0 **Device Authorization Grant** (RFC 8628) from the head unit
  ("Go to hub.example and enter WXYZ-1234"), or authorization code + PKCE from the phone.
  The hub issues a **per-device, per-local-user** refresh token with scopes `publish`,
  `read`, `help` (no admin scope ever leaves the web). Stored in `auth.db` on the Brain
  (§14.10), revocable from both sides.
- **Pairwise identity:** the hub sees a per-device opaque id, never the device's Ostler peer
  key fingerprint used for shares, so hubs cannot correlate a user across hubs or with peers.
- **Link, never log in:** a hub account never signs anyone into a device. This is the same
  shape as the accounts spec §14.8 "link-only OIDC broker", and the official hub can **be**
  that broker later (one identity service, not two). Self-hosters point at their own hub or a
  generic OIDC provider.
- **Household:** each local user links their own hub account; the vehicle owner decides
  which vehicle data a driver may publish (grants, §14.2).

## 7. Storage, scrubbing and tiles

**Sizes (estimates, measure on real sessions).** A session is RaceCapture-style CSV plus
`meta.json` (ADR-0009). At ~10 Hz and ~50 channels, an hour is tens of MB raw and a few MB
with zstd (U). GPS at 1 Hz is ~3,600 points an hour, ~50 KB as compressed GeoJSON.

| Object | Where | Format |
|---|---|---|
| Original upload (session, GPX) | object store, private | as uploaded, zstd, SHA-256 key |
| Display trace | PostGIS + object store | simplified line (Douglas–Peucker per zoom), privacy zones cut **before** storage |
| Signal series for the viewer | object store | columnar chunks (Parquet or Arrow IPC) per trip, fetched by range (U: choose at H2) |
| Public route layer, heatmap | object store, public | **PMTiles** rebuilt nightly with tippecanoe; served by HTTP range requests, no tile server ([PMTiles](https://github.com/protomaps/PMTiles), BSD-3) |
| Basemap | the same PMTiles pipeline as the Brain (ADR-0009) | Ostler Night/Day |

**Uploads** are resumable (tus, or S3 multipart with presigned parts), capped per file and
per account, parsed in a job, and **rejected unless they parse** as a session, GPX, FIT or
KML. Arbitrary files are never accepted, which keeps the hub out of "file-sharing service"
territory (§9).

**Scrubbing happens twice.** On the device before upload (ADR-0036: no VIN, HMAC or identity
replies; privacy zones; EXIF stripped), and on the hub again as a check that **rejects**
rather than repairs (a 17-character VIN pattern in Mode 09 frames, an identity DID, GPS
inside a declared zone).

**Cost (official instance, rough).** R2 standard storage is $0.015 per GB-month with free
egress ([pricing](https://developers.cloudflare.com/r2/pricing/), 2026-10-07): 10,000 users
at 1 GB each is about $150 a month for objects. A small Mastodon-class server runs roughly
$50–150 a month in compute ([bavatuesdays](https://bavatuesdays.com/mastodon-costs/)).
People, not hosting, are the real cost (§9).

## 8. Federation: what it would cost

| Cost | Detail |
|---|---|
| **Remote content is our content** | Whatever we display from other servers is user-to-user content on our service for OSA and DSA purposes; we must moderate it or not show it |
| **Deletion is best-effort** | A `Delete` reaches only servers that honour it; ADR-0029 already rejected AP "now" for this reason |
| **Security surface** | HTTP signatures, actor spoofing, remote deletes: wanderer shipped fixes in v0.21 for remote actors deleting or reading private trails |
| **Semantics loss** | Mastodon renders a route as a `Note`; signal data, privacy levels and grants do not federate |
| **Operations** | remote media cache, defederation decisions, spam waves; small-instance moderation burden is widely reported ([HackerNoon](https://hackernoon.com/mastodon-systemic-sustainability-afe172699cb2)) |
| **Ecosystem is young** | fitness federation exists (wanderer, FitPub) but FitTrackee's is still roadmap (U); no shared vocabulary for tracks |

**Recommendation.** Nothing private or full-log ever federates. In H5 at the earliest:
**outbound-only** publishing of public routes (wanderer's `Note` + GPX `Document` for
compatibility), events as `Event` (Mobilizon-compatible), and each club as a **Group** actor,
in **allowlist** mode (GoToSocial's model), replies limited by interaction policy. A Python
ActivityPub layer is thin; if it becomes the bulk of the work, a separately deployed
federation sidecar is an ADR-0035 question, not a default.

## 9. Moderation, abuse and the law

**Abuse controls (H1, all of them).** Report button on every object (route, comment, event,
profile, help request); block and mute; per-account and per-IP rate limits; tighter limits
for accounts under 7 days old; upload caps; strict file parsing; **no images or video in
H1–H2**; comments off by default on new routes; club admins moderate their club; an admin
queue with statements of reasons and appeals; audit of every action.

**UK Online Safety Act 2023.** A hub with comments, clubs and shared routes is a
**user-to-user service**. For a small service the duties are (Ofcom codes in force since
17 March 2025; [codes](https://www.ofcom.org.uk/siteassets/resources/documents/online-safety/information-for-industry/illegal-harms/illegal-content-codes-of-practice-for-user-to-user-services-24-feb.pdf?v=391889),
[CMS summary](https://cms.law/en/gbr/legal-updates/online-safety-act-illegal-content-duties-are-now-in-force)):

- a written **illegal content risk assessment**, kept up to date and reviewed on change;
- a **children's access assessment**, and a children's risk assessment if children can
  access it (a stated minimum age without age assurance does not by itself exclude them) (U);
- a **named accountable individual**; clear terms of service; a content moderation function
  that takes illegal content down swiftly; easy **reporting and complaints**; record keeping;
- **perceptual hash matching for CSAM** applies to services at high risk with > 700,000 UK
  users, and to **all file-storage and file-sharing services regardless of size**. Keeping
  H1 to parsed tracks and logs, with no images, keeps the image-CSAM risk low; when photos
  arrive, add hash matching first (Cloudflare's CSAM scanning tool is free for its customers,
  operators still file their own reports ([Cloudflare](https://blog.cloudflare.com/the-csam-scanning-tool)));
- **fees** start at £250 m qualifying worldwide revenue, so not us
  ([Ofcom](https://www.ofcom.org.uk/online-safety/online-safety-fees-and-penalties));
  penalties reach £18 m or 10 % of revenue (U on the exact cap wording).

**EU Digital Services Act.** Serving EU users makes the hub a **hosting service** and, with
public posting, an **online platform**. Micro and small enterprises (< 50 staff and
< €10 m turnover) are excused the platform section except Article 24(3) (Article 19). Still
applying: points of contact (Arts 11–12), a **legal representative in the EU** if the
operator has no EU establishment (Art 13; relevant for a UK operator), terms (Art 14),
**notice and action** (Art 16), **statements of reasons** (Art 17), and notifying suspected
threats to life or safety (Art 18) ([Article 19](https://prighter.com/resources/laws/dsa/articles/article-19),
[Art 13](https://www.taylorwessing.com/en/insights-and-events/insights/2022/07/the-need-for-the-appointment-of-representatives-under-european-digital-law)).

**GDPR and UK GDPR.**

- **Lawful basis:** contract for the account and hosting what the user chose to publish;
  **consent** for anything location-based (EDPB connected-vehicles guidance treats
  geolocation as needing specific safeguards and consent as the general basis
  ([Bird & Bird](https://twobirds.com/en/insights/2021/uk/connected-vehicles-finalised-guidelines-from-the-edpb)));
  legitimate interests for security and abuse prevention.
- **Location is the risk:** tracks reveal homes, workplaces and routines (the Strava heatmap
  exposed military sites even with privacy zones). Privacy zones on by default; no global
  heatmap from non-public trips; aggregate tiles only from public routes, with a minimum
  count per cell.
- **A DPIA** before launch (systematic location processing, live tracking).
- **Rights:** full export (Art 20) as originals plus JSON; deletion (Art 17) that removes
  originals, derived tiles at the next rebuild, and backups within a stated window; the
  device's copy is never touched by a hub deletion.
- **UK Data (Use and Access) Act 2025:** from **19 June 2026** controllers must run a data
  protection **complaints** process (acknowledge within 30 days)
  ([Squire Patton Boggs](https://www.squirepattonboggs.com/insights/publications/the-data-use-and-access-act-2025-and-the-new-right-for-individuals-to-complain-to-controllers/)).
- Processors under DPAs, records of processing, UK/EU hosting to avoid transfer paperwork
  (DMD uses OVH in France).

**Third parties in content.** Passengers in a full log, plates and faces in later photos,
other cars in a convoy trace: the uploader confirms they may share, plates and faces are
blurred on device before photos are allowed (Social spec §7, clip export rule).

## 10. Content licences

- **User content:** users keep copyright and grant the operator a licence to host and show it
  to the audience they chose, ending on deletion (the usual shape; mirror the Social spec's
  "nothing posted automatically"). Self-hosters adopt or change the template.
- **Public routes:** offer **CC BY-SA 4.0** as an opt-in default for public routes so they
  can be reused and survive the hub; the uploader can choose "all rights reserved". Routes
  snapped to OSM may carry ODbL obligations; attribute OSM on every map (U: legal check).
- **Decode contributions:** **CC BY-SA 4.0** per ADR-0012, with the contributor's tick that it
  is their own observation and not taken from a dealer database (ADR-0012's DMCA rule). They
  enter a pack only through a PR with the usual review; the hub links the evidence.
- **Code:** `ostler-hub` and `ostler-app-hub` AGPL-3.0-or-later with the CLA, so the
  commercial licence still works (ADR-0012). The network clause means anyone running a
  modified hub publishes it, which is what we want.

## 11. Repos and phases

**Repos** (ADR-0034's rule; grounds named):

| Repo | Licence | Contents | Grounds |
|---|---|---|---|
| `ostler-hub` | AGPL-3.0-or-later + commercial | server, web, compose file, migrations, OpenAPI, moderation tools, policy templates (ToS, privacy, risk assessment) | **toolchain** (server deploy, Postgres), **cadence** (web service releases), **contributors** (web developers) |
| `ostler-app-hub` | AGPL-3.0-or-later | the shell add-on: link a hub, publish from Trips, help requests, browse; npm `@ostler/app-hub` | cadence, contributors (ADR-0034 amendment 2026-10-06) |

The API contract (OpenAPI) lives in `ostler-hub` and is pinned by `ostler-app-hub`.

**Phases.**

| Phase | Scope | Needs |
|---|---|---|
| **H0 Specs and policy** | spec; ADR amendment to ADR-0029 §9 and ADR-0034; draft ToS, privacy notice, OSA risk assessment, DPIA | owner approval |
| **H1 Publish and help** | accounts, device linking, publish Card/Route, help requests with Full log to named helpers, report/block, export/delete; no images, no comments on public routes yet | accounts P1–P3 (grants, `auth.db`), Trips core |
| **H2 Clubs and events** | clubs (roles: owner, moderator, member), club-only routes, events with RSVP, comments, garages | H1 moderation queue |
| **H3 Live follow** | time-boxed live link (≤ 24 h), not stored after the session; group live view links to Vehicles & Map | Vehicles & Map V1 |
| **H4 Media and maps** | photos with hash matching and blur, PMTiles route layer and public heatmap | CSAM tooling; DPIA update |
| **H5 Federation (maybe)** | outbound ActivityPub for public routes, events, club Groups; allowlist | a measured demand |

## 12. Styling

- **One look with the app.** The web uses the visual design system's tokens (dark by default,
  one cyan accent, `radius-md` cards, Chips for filters), Ostler Night/Day maps on PMTiles,
  and the same **trip card** as Trips so a published trip looks identical in both.
- **Audience is always visible.** Every object shows an audience chip ("Public · Route",
  "Helpers · Full log · until 14 Oct") in the status-tone style; never a hidden default.
- **Share pages are light-first** for previews in WhatsApp and browsers: an Open Graph image
  of the route on Ostler Day, the card stats, no personal data beyond the display name.
- **Help-request pages** read like a lab notebook: the signal plot, the owner's hypothesis,
  confidence words from ADR-0006, and "candidate" vs "proven" labels.
- **Phone first, head unit never:** browsing the hub is a Parked or passenger activity; the
  add-on contributes no Drive-mode content (driver-distraction rules).

## 13. Feature homes

| Feature | Ostler home | Why |
|---|---|---|
| Publish a trip at a level, privacy zones | `ostler-app-hub` (publish), core Trips (grant) | the grant is core's; publishing UI is optional |
| Hub server, web, clubs, events, comments | `ostler-hub` (NEW repo) | server toolchain and cadence |
| Help requests and full-log viewer | `ostler-hub` web + `ostler-app-hub` request cards | needs both ends |
| Live follow link | `ostler-hub` (link page) + Vehicles & Map (positions) | V&M owns live positions |
| Garage pages | `ostler-hub`, fed by Maintenance & Garage | maintenance owns the data |
| Decode contribution to a pack | `ostler-hub` evidence + pack repo PR | the signal store stays the source of truth |
| Messaging, PTT, calls | Social (not the hub) | already specced, peer to peer |
| Track sync between my own devices | not needed in the hub | Brain and peers already sync (accounts spec) |
| Trip planner / routing | NEW add-on `ostler-app-routes` later (Valhalla or BRouter), not the hub | different toolchain; out of scope here |

## 14. Copy / Avoid / Decide for Ostler

**Copy.**

- wanderer: AGPL, one compose file, GPX as an attachment, public/private/shared per item.
- FitTrackee/Endurain: Python + PostgreSQL/PostGIS + TS web (fits ADR-0035).
- FitPub and Strava's lesson: **privacy zones** on by default, applied before storage.
- DMD Hub: live group positions not stored after the session; minimum age; three cookies, no
  analytics; EU hosting under a DPA.
- GoToSocial: allowlist federation and interaction policies, if we ever federate.
- traccar: one code for hosted and self-hosted.

**Avoid.**

- Putting the hub in closed `ostler-cloud` (Komoot shows the cost of a single owner).
- Federation before moderation, export and deletion work (wanderer's v0.21 fixes).
- Accepting arbitrary files or images in H1 (OSA hash-matching duty, CSAM risk).
- A second permission vocabulary: hub levels are registry classes and details (§14.1).
- The hub reaching into a device, holding a VIN, or storing live positions.
- A public heatmap built from anything but public routes (Strava 2018).

**Decide** (each with a recommendation).

1. **Build a community hub at all?** Recommend yes, as an optional add-on pair, after
   accounts P3. Alternative: rely on share sheets and device-to-device shares only.
2. **Official, self-hosted or both?** Recommend both from one AGPL codebase; devices may
   link to several hubs. Alternative: official only, closed, in `ostler-cloud`.
3. **Repos?** Recommend `ostler-hub` (server + web) and `ostler-app-hub` (shell add-on),
   amending ADR-0034 on toolchain, cadence and contributor grounds. Alternative: hub web
   inside `ostler-cloud`, add-on inside Social.
4. **Name?** Recommend the product name **"Ostler Community"** with repo `ostler-hub`, because
   "Ostler Hub" was the old name of the Brain (ADR-0039 rename) and would confuse readers.
   Alternative: reuse "Ostler Hub" for the community now the Brain is renamed.
5. **Stack?** Recommend Python (ASGI, SQLAlchemy), PostgreSQL + PostGIS, S3-compatible
   storage, PMTiles, TypeScript/React web on the design-system tokens. Alternative:
   PocketBase/Go as wanderer does (a new server language against ADR-0035).
6. **Share levels?** Recommend Card · Route · Live follow · Diagnostics · Full log · Decode
   contribution · Garage, each a registry class × detail; Full log to named helpers only and
   time-boxed; public needs privacy zones. Alternative: public/private per trip only.
7. **Hub identity and device linking?** Recommend hub-owned accounts (passkey, password,
   optional Google/Apple on the hub), devices linked by RFC 8628 device flow or PKCE with a
   pairwise id; the official hub later doubles as the §14.8 link-only broker. Alternative:
   accounts only on devices, the hub trusting device signatures.
8. **Federation?** Recommend none before H5; then outbound-only ActivityPub for public
   routes, events and club Groups, allowlist mode. Alternative: ActivityPub from H1, like
   wanderer.
9. **Images and video?** Recommend none in H1–H2; photos in H4 only with perceptual hash
   matching and on-device face/plate blur. Alternative: photos from H1 with manual review.
10. **Minimum age?** Recommend 16 for accounts (as DMD), with live follow and public profiles
    at 18, plus the children's access assessment. Alternative: 13 with parental controls.
11. **Licence of public content?** Recommend users keep copyright; CC BY-SA 4.0 offered as
    the default for public routes and required for decode contributions. Alternative: an
    all-rights licence to the operator only.
12. **Who carries the legal burden of the official instance?** Recommend the Ostler company
    with a named accountable person, an EU representative if UK-based, a DPIA, an OSA risk
    assessment, DSA notice-and-action and a DUAA complaints process before H1 goes public;
    self-hosters get templates and carry their own. Alternative: launch invite-only until the
    paperwork is done.

## Caveats

- Legal points are a researcher's reading, not legal advice; an OSA/DSA/GDPR review is
  needed before the official instance opens.
- FitTrackee's per-map visibility, its federation status, Mobilizon and Lemmy details, traccar
  and OsmAnd licences and the log size estimates are marked (U).
- DMD Hub's internal stack is unknown; only its public pages and privacy policy were read.

## Changelog

- 2026-10-07: v0.1, first draft (R6, DMD research batch).
