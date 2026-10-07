---
title: "Ostler Community — the community hub (`ostler-hub` server and web, `ostler-app-hub` shell add-on) — design"
area: specs
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [references/research/community_hub_architecture.md, references/research/dmd_hub_features.md, references/research/dmd_hub_ui_teardown.md, references/research/trip_and_log_sharing.md, references/research/dmd2_features.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-visual-design-system-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  DRAFT for the owner (DMD round, 2026-10-07). Ostler Community is the DMD Hub equivalent the owner asked for: a place to publish trips, routes, garage cards and events, ask for decoding and diagnostic help with a full log, and meet in groups and clubs. Two AGPL repos: `ostler-hub` (Python ASGI server, PostgreSQL + PostGIS, S3-compatible storage, PMTiles, TS/React web on the shell's kit and tokens) and `ostler-app-hub` (the shell add-on). Self-hostable, one official instance, a device may link to several hubs, no federation before H5. Hub-owned accounts; devices link by RFC 8628 device flow or PKCE with pairwise ids. Trips publish as L0–L2 grants; L3/L4 travel only as hand-overs into help threads. Items move Private → Pending review → Public; Locked vs Download links. Discover (make/model/engine), opt-in Following feed in the add-on only, small clubs, events, live ride pages (≤ 24 h, not stored), comments and help threads with "solved" credit and no points. Pre-moderation until trusted, OSA/DSA/GDPR duties, minimum age 16 (18 for live follow and public profiles), CC BY-SA defaults. Screens P1–P9 and shell slots, storage and costs, phases H0–H5, tests, decisions.
---

# Ostler Community — design

**Status: draft for the owner's approval (DMD round, 2026-10-07).** Nothing here is built
before accounts P3 and the trip-sharing registry pieces (§13). The research is linked, not
repeated: [community hub architecture](../references/research/community_hub_architecture.md),
[DMD Hub features](../references/research/dmd_hub_features.md),
[DMD Hub UI teardown](../references/research/dmd_hub_ui_teardown.md),
[trip and log sharing](../references/research/trip_and_log_sharing.md),
[DMD2 features](../references/research/dmd2_features.md). Per-trip levels, the bundle format
and the scrubber are owned by the sibling trip-sharing spec
(`specs/2026-10-07-trip-sharing-design.md`, being drafted in this round); this spec only
consumes them. ADR text it changes is a proposed amendment to
[ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md#proposed-amendment-2026-10-07-dmd-round).

## 1. Purpose and non-goals

**Purpose.** The owner: "The community hub is exactly what I was talking about for the social
side. Being able to share trips on there too … a user can share a full log, for help
decoding, or diagnostics on their car/motorcycle." Ostler Community lets people **publish**
trips, routes, garage cards and events at a level they choose, **ask for help** decoding or
diagnosing with a log handed to named helpers, and **meet** in groups, clubs and rides, from
any browser, with no Ostler device needed to read.

**Non-goals.**

- Not a tunnel to the car. The hub never connects to a device, never holds a key that can
  command anything, never receives a VIN, its HMAC, an identity reply or audio (ADR-0033 §6,
  ADR-0036, ADR-0010). The device pushes; the hub never pulls.
- Not a dependency. Ostler is complete without it (ADR-0042); every share in core works device
  to device.
- Not a messenger. Chats, push-to-talk and calls stay in Social, peer to peer.
- Not the source of truth for decodes. That stays each pack's signal store and its PR review.
- Not a sync service for my own devices (Brain and peers already sync).
- No points, ranks, badges, leaderboards or speed boards; no public feed for strangers; no
  ads, analytics or third-party scripts; no social-network share buttons.
- No federation before H5. Not in the closed `ostler-cloud` repo (ADR-0013, ADR-0034).
- No routing or planning: that is `ostler-app-navigation`; the hub only stores and shows
  routes it publishes.

## 2. Where it sits: Social, Vehicles & Map, Navigation, core

| Piece | Owns | Time shape | Hub's relation |
|---|---|---|---|
| **Core sharing** (accounts §14) | the data-class registry, grants, audiences, ghost, the audit, contacts, groups | live and past | the hub is an **audience and a destination**; it adds no permission vocabulary |
| **Core Trips** | the trip record, the share sheet, levels L0–L4 (trip-sharing spec) | past | Trips' share sheet gains hub audiences; the hub renders shared copies |
| **Diagnose / Decode lab** (core, developer add-on) | "get help with this fault", the help-decode flow, recipes | past | a hub **help thread** is one destination of those flows |
| **Social** (`ostler-app-social`) | real-time talk among a few known people | now | links out to hub event and ride pages; the hub never carries chat or calls |
| **Vehicles & Map** (`ostler-app-vehicles`) | live positions, the convoy layer, the §8 relay link | now, ≤ 24 h | the hub's live ride page (P5) is the **web face** of V&M §8 |
| **Maintenance & Garage** | service history, the garage card data | past | hub garage cards are published from it |
| **Navigation** (`ostler-app-navigation`) | routing, GPX library, planner, roadbook, curated routes | plans | publishes routes to the hub and imports hub routes |
| **Ostler Community** (`ostler-hub`, `ostler-app-hub`) | **persistent** sharing to people beyond my contacts: public pages, clubs, events, help threads, Discover | persistent | — |

Rule of thumb: **Social is talking now, Vehicles & Map is where we are now, the hub is what we
keep and show.**

## 3. Repos and stack

| Repo | Licence | Contents |
|---|---|---|
| **`ostler-hub`** | AGPL-3.0-or-later + commercial (CLA, ADR-0012) | API server, web app, migrations, OpenAPI contract, moderation tools, `docker compose` for clubs, policy templates (terms, privacy notice, OSA risk assessment, DPIA) |
| **`ostler-app-hub`** | AGPL-3.0-or-later | the shell add-on (npm `@ostler/app-hub`): link hubs, publish, help threads, Discover, Following, events, inbox |

ADR-0034 grounds: server toolchain (Postgres, deployment), release cadence (a web service) and
contributors (web developers). The OpenAPI contract lives in `ostler-hub` and is pinned by
`ostler-app-hub`; both get generated TS types (ADR-0035).

**Stack** (architecture research §4): Python 3.12+ ASGI (FastAPI or Starlette), SQLAlchemy and
Alembic; **PostgreSQL + PostGIS**; a Postgres-backed job queue; **S3-compatible** object
storage (R2, Hetzner, MinIO or Garage for clubs); **PMTiles** for aggregate layers;
PostgreSQL full-text search first. Web: **TypeScript + React**, server-rendered public and link
pages (fast first paint, Open Graph images), importing the shell's kit and tokens as a package,
MapLibre lazy-loaded. One container image for both deployments.

**Topology.** Self-hostable by any club, plus **one official instance** run by Ostler. A
device may link to **several hubs** (club and official); the device is the join point, so no
hub-to-hub traffic is needed before H5.

## 4. Hub accounts and device linking

- **Hub-owned identity:** email plus **passkey** (primary) or password, optional TOTP; one
  person, one account. The hub is a public HTTPS site, so it can offer Google or Apple sign-in
  **on the hub only** (Decision 6). A hub account **never signs anyone into a device**.
- **Linking a device user:** OAuth 2.0 **Device Authorization Grant** (RFC 8628) from a head
  unit or Brain ("Go to community.example and enter WXYZ-1234"), or **authorization code +
  PKCE** from the phone. The hub issues a refresh token **per device per local user**, scopes
  `publish`, `read`, `help` only (no admin scope leaves the web), stored in `auth.db` on the
  Brain (accounts §14.10), revocable from either side, listed in Settings → Sharing.
- **Pairwise ids:** the hub sees an opaque id per (hub, device, local user), never the device's
  peer-key fingerprint, so hubs cannot correlate a person across hubs or with peers.
- **Household:** each local user links their own hub account; the vehicle owner's grants decide
  which vehicle data a driver may publish (accounts §14.2).
- **Later (P5 at the earliest):** the official hub can **be** the accounts §14.8 link-only OIDC
  broker, so there is one identity service, not two. Self-hosters point at their own hub or a
  generic OIDC provider.

## 5. What can be published

| Object | Comes from | Levels and audiences | Notes |
|---|---|---|---|
| **Trip** | core Trips share sheet | **L0 Card**, **L1 Route**: person, group/club, `link`, `public` · **L2 Telemetry**: person, group/club only | grants (trip-sharing spec). Public needs an explicit publish act and, for a route, ≥ 24 h after the trip ends; max speed hidden on public cards; L1 trimmed 500 m (never < 200 m) with privacy zones |
| **Route** | `ostler-app-navigation` library or planner | private, group/club, `link`, `public` | a plan, not a recording; the same end-trim check warns when it starts or ends in a privacy zone |
| **Garage card** | Maintenance & Garage, Vehicles & Map §2.2 | `vehicle_card` basic; optional `maintenance` history (no costs; "for a buyer" preset) | plate hidden unless ticked, EXIF stripped, never a VIN, masked or not |
| **Event** | a club or a person | group/club, `link`, `public` | ICS, place at the organiser's precision |
| **Help thread** | Diagnose, Trips, Decode lab | thread text: club or public; **attachment: named helpers only** | carries **L3 Full log** or **L4 Diagnostics bundle** as a **hand-over**, never a grant (§6) |
| **Decode contribution** | the solved answer of a help thread | public, CC BY-SA 4.0 | derived decodes and short fixture snippets only, never the log (ADR-0036 §5); enters a pack only by PR |

**Publishing is a grant, not a sync.** L0–L2 reach a hub only when the data owner grants the
`trips` class (and `location` at `route` detail for L1) to a hub audience. Ghost does not hide
past-trip grants (accounts §14.3), and the sheet says so. Every upload is scrubbed on the device
and passes `ostler share verify` first; the hub re-checks and **rejects** rather than repairs
(VIN pattern, identity reply, a point inside a declared zone).

## 6. Help threads and L3/L4 hand-overs

1. Started from Diagnose ("get help with this fault"), Trips (a time range) or Decode lab (a
   signal). The device builds an `ostler.share/1` bundle, shows the preview with its redaction
   report, runs the verifier, and uploads it **encrypted**; the key travels in the URL fragment
   of each helper's invite, so the hub stores ciphertext only (Decision 4).
2. The thread page shows the question, vehicle chips (make, model, engine, year, pack), the
   level chip and **"time-boxed access: 6 days left"** (default 7 days, max 30, downloads ≤ 3).
3. Helpers are **named or accepted by the owner** one by one; a club "help desk" may be offered
   as a group of helpers. The attachment opens in a browser-side viewer (signal plot, faults,
   freeze frames); download only if the owner ticked it.
4. Helpers reply with text, links to moments ("see 00:12:31 on `Engine.Speed`") and **recording
   recipes**; they never send requests or actions to the car (ADR-0033). A request for more
   (another class, a longer window) lands on the owner's device as a card, answered there.
5. **Mark as solved** credits the helper ("solved by @ali"); no votes, no points. A solved
   answer can become a decode contribution under CC BY-SA 4.0 with the contributor's own-work
   tick (ADR-0012); its evidence page links the pack PR.
6. Expiry, revoke or account deletion destroys the ciphertext; the thread text stays, marked
   "attachment expired".

## 7. Item states, links and their controls

**States (DMD-style):** **Private → Pending review → Public**. Link-only (`link` audience) items
skip review but are reportable. *Make public* opens an inline checklist (title, description
≥ 50 characters, region, vehicle, licence) and goes to **Pending review** until the account is
trusted (§10). Separate switches: **Allow download** (off) and **Show in Discover and search
engines** (off for routes from home regions until ticked). *Make private now* is always one tap.

**Links** (fields of core grants, accounts §14.2, as the trip-sharing spec defines them):

| Mode | What the recipient gets | On revoke or access-until |
|---|---|---|
| **Locked** | view in the hub viewer or in Ostler; follows the owner's edits; read-only | gone everywhere, cached copies in `ostler-app-hub` deleted |
| **Download** | a file copy (GPX, card image) | the link dies; copies already taken survive, and the sheet says so first |

Controls: available-from, link expiry, access-until, collection limit, downloads per person;
states **Active · Pending · Full · Expired**; per-link revoke; every view and download in the
device audit and the hub access log. `link` is never offered for live location beyond a ride,
audio, video or raw logs.

## 8. Screens

All screens use the [visual design system](2026-10-07-visual-design-system-design.md): dark
by default, one `accent` (primary action and anything live only), `surface-1` cards, sheets on
`surface-glass`, Figtree, Material Symbols, `series-*` for categories, ISO status hues with
words, **Ostler Night** maps (Day for Open Graph previews), flat by default, collapsed ⓘ
attribution, `cooperativeGestures` inside scrolling pages. Every object its owner sees carries
the **visibility chip** (`lock Only me`, `group Peak 4x4`, `link Link · 6 d`, `public
Public`), tapping into the visibility sheet (teardown §7.4). Numbers are honest: smoothed
elevation with its source, "—" for missing, the viewer's units with a km/mi Segmented.

### 8.1 Web app (`ostler-hub`)

Sitemap: `/` · `/t/<id>` · `/r/<id>` · `/g/<slug>` · `/e/<id>` · `/e/<id>/live` ·
`/ride/<token>` · `/help/<id>` · `/u/<handle>` · `/v/<id>` · `/search` · `/me/…`.

| Screen | Layout (teardown §7.2 holds the ASCII) |
|---|---|
| **P1 Discover** | one search field; chips Routes · Trips · Events · Help wanted · Clubs; **make / model / engine / year** filter, region, vehicle type, "has faults", "has telemetry"; card grid with static Ostler Night thumbnails; side column "Help wanted on your vehicles", "Upcoming near you" (coarse region). No people feed |
| **P2 Shared trip** | full-bleed map, title card with the level and audience chips, 420 px side sheet (phone: bottom sheet) with HeroStat distance, stat strip, elevation; tabs only for the level granted: Overview (L0+), Signals (L2), Faults (L2 with faults). L0 has no map: vehicle silhouette, numbers, a place name per end. Trace `series-1` with casing; speed ramp only if the owner granted `show_speed` |
| **P3 Help thread** | question, vehicle chips, attachment chip with time left; replies as ListRows; *Mark as solved*; contribution panel |
| **P4 Group or club** | name, kind chip, member count, *Join with code*; tabs Rides · Routes · Events · Members · Files; a map of shared routes, never members' homes |
| **P5 Live ride** | full-bleed map, one title pill "● LIVE · 4 riding · ends 18:00", member pucks (`accent` for me), leader/sweep badges, delay badge, "Riders appear here as they set off"; ends with "This ride has ended" and no positions |
| **P6 Event** | title card, When & where card (dates in the event's zone, *Add to calendar* ICS, *Copy coordinates*), Going · Maybe · Not going, files locked until start, comments |
| **P7 Profile** | avatar, name, bio, garage row of cards, public routes and trips; counts "helped with 12 decodes", "completed 3 routes"; **no map of the person's places** |
| **P8 Publish** | 1 Choose · 2 Level · 3 Audience and time (Locked/Download, expiry, delay) · 4 Preview rendered **from the scrubbed bundle** · Publish; Public checklist inline |
| **P9 My shares** | one ListRow per link or publication: level chip, audience chip, expiry countdown, views, *Revoke* (two taps), *New link* |

Share out: **Web Share API, copy link, QR, embed card**; no social-network buttons or scripts.
Sign-in walls: `public` readable signed out; `link` needs only the link; club content, live
rider lists and help attachments need a signed-in member or a named helper.

### 8.2 In-shell add-on (`ostler-app-hub`)

| Slot | Content | Driving rule |
|---|---|---|
| **More → Community** (new `more:hub` slot, platform proposal to app-model §4.2) | tabs **Discover · Following · Help · Mine**; P1 in a phone column; the opt-in **Following** feed lives here only | Parked or passenger |
| **Trips share sheet** (core) | adds hub audiences (clubs, `link`, `public`) to the P8 steps; the sheet itself is core Trips | Parked, or Idling with Park evidence |
| **Diagnose → fault → Get help** (core) | adds "Post to a help thread on <hub>" as a destination, preset to L4 | Parked |
| **Home card** (`home:card`) | "2 replies on your help request", "Event tomorrow 09:00" | hidden while Moving; the strip shows a count only |
| **Settings → Sharing** (core, accounts §14.7) | P9 rows and linked hubs | — |
| **Head unit** | nothing while Moving; Parked: help replies and events as ListRows ≤ 30 characters | UI spec §12.1 |

All add-on screens are reachable with `ShellInput` (D-pad focus zones); the add-on puts nothing
in the Drive menu.

## 9. Discover, Following, clubs, events, live rides, comments

- **Discover** is the directory: public items and clubs that chose to be listed. People are
  findable only through a public profile (18+, opt-in). No ranking algorithm: newest, nearest
  (coarse), most useful (solved count, completions) as explicit sorts.
- **Following** is opt-in, chronological, in `ostler-app-hub` only: new public items from people
  and clubs I follow. Never in Social, never on the web front page.
- **Groups and clubs:** any size (no 1,000-member floor); kinds friends · club · ride · safety
  (accounts §14.6); roles owner, moderator, member; join by code, link or approval. A core group
  may be **linked** to a hub club so a group grant can publish there. A club may show a public
  face (name, about, events) when it chooses.
- **Events:** listing, Going, capacity, ICS, CSV export of attendees for organisers, payment info
  as text only (no money handling), files locked until a start time and fetched ahead.
- **Live ride pages** (H3): **live follow ≤ 24 h**, ride-scoped, ended by ghost or ride end.
  Positions come from the rider's device with V&M §8's options (`trail_window`, `delay` 0–6 h,
  `show_speed`, `show_values`), are held **in memory only** for the session and **never stored**
  after it. **Listing** on Discover's "Live now" is opt-in, off for every ride, 18+, with a
  one-time warning that a listed ride is findable (advice: delay or link-only from home or
  alone). No viewer chat in v1; members talk in Social.
- **Comments** on routes, trips, events and help threads; off by default on new public items;
  owners can close, hide or pin; deleted comments leave a tombstone so threads still read.

## 10. Moderation and abuse

- **Pre-moderation until trusted:** an account's public items and comments on public items wait
  in a review queue until it has ≥ 30 days and ≥ 3 approved items with no upheld report
  (Decision 8). Trust is a moderation flag only, never shown as a score.
- **Report** on every object (reason, text, optional map pin; pinned warnings on routes until the
  owner marks them solved); **block** and **mute** (blocked people cannot see my items or join my
  rides); rate limits per account and IP, tighter for new accounts; upload caps; strict parsing.
- **Staff review** on the official instance; club moderators handle their club; every decision
  carries a **statement of reasons**, an **appeal** route and an audit entry.
- **Uploads H1–H3:** only parsable track, trip and log files (session, `ostler.share/1`, GPX,
  FIT, KML); **no images or video**. Photos at **H4** only, with perceptual hash matching first
  and **face and plate blur on the device**.
- A code of conduct includes "no reposting other people's decodes or routes as your own" and
  "no dealer-database content" (ADR-0012).

## 11. Law, age and licences

**Duties of the official instance** (research §9; legal review before H1 opens publicly):
UK **OSA** illegal-content and children's-access risk assessments, a named **accountable
person**, terms, swift takedown, reporting and complaints, records; EU **DSA** points of
contact, an EU legal representative if UK-based, **notice and action**, statements of reasons,
Article 18 notifications; **GDPR/UK GDPR**: consent for location, a **DPIA** before launch,
records of processing, processors under DPAs, UK/EU hosting, a DUAA **complaints** process
(30-day acknowledgement). Self-hosters get the templates and carry their own duties; the docs
say so.

**Rights.** **Export** everything (originals plus JSON, Art 20). **Deletion** (Art 17) removes
originals and personal data at once, derived tiles at the next rebuild, backups within 35 days;
help-thread answers become **"[deleted user]" tombstones** unless the person chooses "delete
everything". A hub deletion never touches the device's copy.

**Age.** Accounts **16+**; **live follow and public profiles 18+**; self-declared at sign-up,
backed by the children's access assessment (Decision 10).

**Licences.** Users **keep copyright** and give the operator a licence to host and show an item
to its chosen audience, ending on deletion. **Public routes default to CC BY-SA 4.0** (opt out
to "all rights reserved"); **decode contributions require CC BY-SA 4.0** (ADR-0012). OSM is
attributed on every map; OSM-snapped routes may carry ODbL duties (legal check). Code is
AGPL-3.0-or-later with the CLA.

## 12. Storage and costs

| Object | Where | Format |
|---|---|---|
| Original upload | object store, private | zstd, SHA-256 key; never served to the public |
| L3/L4 attachment | object store, private | ciphertext only; deleted at access-until |
| Display trace | PostGIS + object store | simplified per zoom, zones cut **before** storage |
| L2 signal series | object store | columnar chunks fetched by range (format chosen at H1) |
| Public route layer, heatmap (H4) | object store, public | PMTiles rebuilt nightly, public routes only, minimum count per cell |
| Live ride positions | server memory | never written to disk |

**Quotas and money.** Free accounts get a storage quota on the official instance; paid plans
buy **hosted storage and relay** only. **Safety, sharing and decode help are never charged
for.** Rough official-instance cost: objects ~$150/month at 10,000 users × 1 GB (R2), compute
$50–150/month; people (moderation, legal) are the real cost.

## 13. Phases

| Phase | Scope | Needs |
|---|---|---|
| **H0 Specs and policy** | this spec; ADR-0029 and ADR-0034 amendments; terms, privacy notice, OSA risk assessment, DPIA drafts | owner approval |
| **H1 Publish and help** | accounts, device linking, Discover, publish L0/L1 trips and routes (`link`, `public` with review), L2 to clubs, help threads with L3/L4 hand-overs, report/block, export/delete; files only, no images; comments only in help threads | accounts P1–P3, trip-sharing registry pieces and verifier, core Trips share sheet |
| **H2 Clubs and events** | clubs, events, comments, garage cards, Following feed in the add-on, Home card | H1 moderation queue |
| **H3 Live rides** | live ride pages ≤ 24 h, opt-in listing | Vehicles & Map V5 relay link |
| **H4 Media and maps** | photos with hash matching and on-device blur, PMTiles route layer and heatmap | CSAM tooling, DPIA update |
| **H5 Federation (maybe)** | outbound-only ActivityPub for public routes, events and club Groups, allowlist | measured demand |

## 14. Tests

- No upload route accepts a file that does not parse; images refused before H4.
- Server-side re-check rejects a VIN pattern, an identity reply or a point inside a declared zone;
  no response, log or audit entry ever contains a VIN or HMAC.
- L0/L1 public items: trims ≥ 200 m, no point timestamps, stats recomputed from the visible trace,
  max speed absent; a route cannot go public < 24 h after its trip ends.
- `link` and `public` refused for L2, L3, L4, live location beyond a ride, audio and video.
- L3/L4: the hub stores ciphertext only; the attachment is unreadable after access-until or revoke;
  a non-named member gets 403.
- Locked links: revoke removes add-on caches; Download links state copies survive.
- Device linking: RFC 8628 and PKCE flows; tokens scoped to `publish`/`read`/`help`; pairwise ids
  differ across hubs; revoking on either side ends uploads.
- Live ride: no position row reaches the database; the page shows no positions after end or 24 h.
- Moderation: an untrusted account's public item stays Pending; report → decision carries a
  statement of reasons; block hides items both ways.
- Export contains every original; deletion leaves tombstones in help threads and nothing else.
- Web pages pass the visual spec's contrast checks and load no third-party script.

## 15. Open questions

1. Which ASGI framework (FastAPI or Starlette) and the L2 series format (Parquet or Arrow IPC).
2. How the browser-side L3/L4 viewer parses `ostler.share/1` without the device's pack decoders.
3. Whether a club hub can show official-hub public routes (device-mediated import only, or links).
4. Exact OSA children's-access outcome with self-declared age, and the EU representative.
5. The quota size on the official instance, measured on real sessions.

## Changelog

- 2026-10-07: v0.1, first draft (DMD round), from the hub architecture, DMD Hub feature and UI
  research and the trip-sharing positions.

## Decisions for the owner

1. **Build Ostler Community at all?** *Recommend:* yes, as an optional pair (`ostler-hub`,
   `ostler-app-hub`) after accounts P3. *Alternative:* share sheets and device-to-device shares only.
2. **Topology?** *Recommend:* one AGPL codebase, self-hostable plus one official instance; devices link
   to several hubs; no federation before H5. *Alternative:* official only, closed, in `ostler-cloud`.
3. **Repos and stack?** *Recommend:* `ostler-hub` (Python ASGI, PostgreSQL + PostGIS, S3, PMTiles,
   TS/React web on the shell kit) and `ostler-app-hub`, via an ADR-0034 amendment. *Alternative:* the
   web inside `ostler-cloud` and the add-on inside Social.
4. **L3/L4 on the hub encrypted end to end** (key in the helper's URL fragment, browser-side viewer,
   the device verifier as the only gate)? *Recommend:* yes. *Alternative:* server-readable attachments
   with a second server-side scrub check.
5. **Public and `link` audiences on the hub at H1** (L0/L1 trips, routes, garage cards, events; explicit
   publish; review until trusted)? *Recommend:* yes, via the ADR-0029 amendment. *Alternative:* `link`
   only until clubs exist (H2).
6. **Third-party sign-in on the hub site** (Google, Apple), never on devices? *Recommend:* yes, optional,
   beside passkeys. *Alternative:* passkeys and passwords only.
7. **Feed?** *Recommend:* Discover for everyone; an opt-in chronological Following feed in
   `ostler-app-hub` only. *Alternative:* a Following tab on the web too.
8. **Trust rule for leaving pre-moderation?** *Recommend:* ≥ 30 days and ≥ 3 approved items, no upheld
   report, never shown as a score. *Alternative:* manual promotion by staff only.
9. **Images?** *Recommend:* none before H4; then hash matching plus on-device face and plate blur.
   *Alternative:* photos from H1 with manual review.
10. **Age?** *Recommend:* 16 for accounts, 18 for live follow and public profiles, self-declared.
    *Alternative:* 13 with parental controls.
11. **Licences?** *Recommend:* users keep copyright; CC BY-SA 4.0 default for public routes, required for
    decode contributions. *Alternative:* an all-rights licence to the operator.
12. **Money?** *Recommend:* free accounts and features; charge only for hosted storage and relay, never
    for safety, sharing or decode help. *Alternative:* a paid tier for clubs.
13. **Name?** *Recommend:* "Ostler Community" (not "Ostler Hub", the Brain's old name), repo `ostler-hub`,
    shell page More → Community. *Alternative:* reuse "Ostler Hub".
