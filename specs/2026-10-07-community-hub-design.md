---
title: "Ostler Community — the community hub, forum, vehicle-development workspace and wiki (closed `ostler-hub` service, open `ostler-app-hub` shell add-on) — design"
area: specs
status: stable
version: 0.4
updated: 2026-10-07
depends_on: [references/research/community_hub_architecture.md, references/research/dmd_hub_features.md, references/research/dmd_hub_ui_teardown.md, references/research/trip_and_log_sharing.md, references/research/dmd2_features.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, specs/2026-10-07-maintenance-garage-addon-design.md, specs/2026-10-07-visual-design-system-design.md, specs/2026-10-07-trip-sharing-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0028-base-hardware-connectivity-and-remote-access.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0035-languages-by-tier.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3; v0.2 followed the owner's direction that the hub is "our own thing, closed not self hostable", also the forum, the place to develop new vehicles, connected to the wiki, in a new repo. Ostler Community is a closed service run by Ostler: one official instance, not self-hostable, in a new private repo `ostler-hub`, separate from the closed `ostler-cloud`, under ADR-0013's cloud boundary (documented API only, no platform code imported, no third-party copyleft code). The shell add-on `ostler-app-hub` stays open (AGPL) and holds the public API contract and the end-to-end encryption. It does four jobs: publish trips, routes, garage cards and events (L0–L2 grants; L3/L4 only as encrypted hand-overs to named helpers); the project forum (categories per make and model, Q&A with "solved", search, notifications, no direct messages); the vehicle-development workspace (help thread → decode cards → vehicle project → pack PR on GitHub under CC BY-SA, through a GitHub App bridge, never required); and the wiki (none exists today), hosted in the hub, with vehicle pages generated from pack releases. User rights hold: export everything, nothing in core depends on the hub (ADR-0042), a public CC BY-SA community dump, OSA/DSA/GDPR duties on Ostler as sole operator, pre-moderation until trusted, 16+ (18+ for live follow and public profiles). No federation. Never charges for safety, sharing or decode help. Screens, phases H0–H4, tests, and the DMD decision items B 7–19 and 19a–19f, all answered as recommended (the private `ostler-hub` repo is created now, empty, after asking the owner). Amended 2026-10-07 (openness round, ADR-0047): the hub API becomes a published, stable contract that clubs may implement and the add-on's hub URL is user-settable, while ostler-hub's own code stays closed; the official hub's no-votes and no-points rules are operator policy.
---

# Ostler Community — design

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings";
> [ADR-0047](../decisions/adr-0047-openness-round.md)):** the hub is no longer the only hub.
> The public hub API contract (`api/hub.openapi.yaml` in `ostler-app-hub`) becomes a stable,
> versioned API that anyone may implement, and the add-on's hub URL is user-settable, so a
> club can run its own compatible hub (§1, §3.3, §4). The official `ostler-hub` code stays
> private and closed, and Ostler Community stays the one official instance under Ostler's
> marks. The official hub's no-points, no-votes and pre-moderation rules are its operator
> policy, not platform rules: other hubs and add-ons decide their own, and the official hub
> may add opt-in reactions, badges or answer upvotes later (§1, §9, §14). Public route delay
> and ends trim follow the trip-sharing defaults (§6). Age limits, operator duties and no
> DMs on the official hub are unchanged.

**Status: approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3.** v0.1 proposed an open,
self-hostable AGPL hub. The owner then decided: *"I think the ostler hub should be our own thing,
closed not self hostable, it's also going to serve as our forum, help us develop and code new
vehicles, be connected to our wiki, we'll need to create a new repo for it."* This version follows
that direction; the open, self-hostable model was the alternative in the decision items at the
end, not chosen. Nothing here is built before accounts P3 and the trip-sharing registry pieces
(§16). The research is linked, not repeated:
[community hub architecture](../references/research/community_hub_architecture.md) (written for
the open model; its stack, storage, moderation and law sections still apply),
[DMD Hub features](../references/research/dmd_hub_features.md),
[DMD Hub UI teardown](../references/research/dmd_hub_ui_teardown.md),
[trip and log sharing](../references/research/trip_and_log_sharing.md),
[DMD2 features](../references/research/dmd2_features.md). Per-trip levels, the bundle format and
the scrubber are owned by the [trip-sharing spec](2026-10-07-trip-sharing-design.md); this spec
only consumes them. ADR text it changes is the approved DMD-round amendment to
[ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md#amendment-2026-10-07-dmd-round-approved),
[ADR-0034](../decisions/adr-0034-repo-boundaries.md#amendment-2026-10-07-dmd-round-approved) and
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md#amendment-2026-10-07-dmd-round-approved).

## 1. Purpose and non-goals

**Purpose.** The owner: "The community hub is exactly what I was talking about for the social
side. Being able to share trips on there too … a user can share a full log, for help decoding,
or diagnostics on their car/motorcycle", and then: it is "our own thing", "our forum", it will
"help us develop and code new vehicles" and "be connected to our wiki". Ostler Community is
Ostler's one place online for people and their vehicles. It has four jobs:

1. **Publish** trips, routes, garage cards and events at a level the owner chooses (§7).
2. **Forum**: the project's discussion and Q&A space, organised by make and model (§9).
3. **Vehicle development**: turning help threads and captures into decodes and pack pull
   requests, so new vehicles get supported (§10).
4. **Wiki**: vehicle pages generated from pack data plus community-written guides (§11).

Everything public is readable from any browser, with no Ostler device needed.

**Non-goals.**

- Not a tunnel to the car. The hub never connects to a device, never holds a key that can
  command anything, never receives a VIN, its HMAC, an identity reply or audio (ADR-0033 §6,
  ADR-0036, ADR-0010). The device pushes; the hub never pulls.
- Not a dependency. Ostler is complete without it (ADR-0042 decision 7); every share in core
  works device to device, and contributing to a pack never needs the hub (§10.6).
- Not a messenger. No direct messages between users; chats, push-to-talk and calls stay in
  Social, peer to peer.
- Not the source of truth for decodes. That stays each pack's signal store and its PR review on
  GitHub; the hub proposes, the pack repo decides.
- The official `ostler-hub` code is not offered for self-hosting, and there is no federation
  in v1 (§3; decision B 18). *Amended 2026-10-07 (openness round):* the hub API is published and
  stable, so others may run a compatible hub under another name, and a device may point at it.
- Not part of `ostler-cloud`: a separate closed service in its own repo (§3).
- Not a sync service for my own devices (Brain and peers already sync).
- On the official hub, by operator policy: no points, ranks, badges, votes, leaderboards or
  speed boards; no public feed for strangers; no ads, analytics or third-party scripts; no
  social-network share buttons. Other hubs and add-ons may choose otherwise, and the official
  hub may add opt-in reactions or badges later (*amended 2026-10-07, openness round*).
- No routing or planning: that is `ostler-app-navigation`; the hub only stores and shows
  routes it publishes.

## 2. Where it sits: Social, Vehicles & Map, Navigation, core, packs

| Piece | Owns | Time shape | Hub's relation |
|---|---|---|---|
| **Core sharing** (accounts §14) | the data-class registry, grants, audiences, ghost, the audit, contacts, groups | live and past | the hub is an **audience and a destination**; it adds no permission vocabulary |
| **Core Trips** | the trip record, the share sheet, levels L0–L4 (trip-sharing spec) | past | Trips' share sheet gains hub audiences; the hub renders shared copies |
| **Diagnose / Decode lab** (core, developer add-on) | "get help with this fault", the help-decode flow, recipes | past | a hub **help thread** is one destination of those flows |
| **Pack repos** (`ostler-pack-<x>`, GitHub) | signals, DTCs, maintenance data, fixtures, review, releases | releases | the hub's **bridge** opens PRs and reads releases; the wiki renders them (§10, §11) |
| **Social** (`ostler-app-social`) | real-time talk among a few known people | now | links out to hub event, ride and thread pages; the hub carries no chat, DMs or calls |
| **Vehicles & Map** (`ostler-app-vehicles`) | live positions, the convoy layer, the §8 relay link | now, ≤ 24 h | the hub's live ride page (P5) is the **web face** of V&M §8 |
| **Maintenance & Garage** | service history, the garage card data | past | hub garage cards are published from it |
| **Navigation** (`ostler-app-navigation`) | routing, GPX library, planner, roadbook, curated routes | plans | publishes routes to the hub and imports hub routes |
| **Ostler Cloud** (`ostler-cloud`, closed) | relay links, hosted storage, remote access (ADR-0028) | live | separate service; no shared database; joins only through the user's own links |
| **Ostler Community** (`ostler-hub` closed, `ostler-app-hub` open) | public pages, forum, vehicle development, wiki, clubs, events, help threads, Discover | persistent | — |

Rule of thumb: **Social is talking now, Vehicles & Map is where we are now, the hub is what we
keep, show, ask and build together.**

## 3. Repos, licences and stack

### 3.1 Repos

| Repo | Visibility, licence | Contents |
|---|---|---|
| **`ostler-hub`** (new) | **private, closed**; proprietary, all rights reserved (Ostler) | API server, web app (publish, forum, vehicle development, wiki), migrations, moderation and staff tools, the GitHub App bridge, the pack-release ingester, deployment, internal server specs and runbooks, policy drafts (terms, privacy notice, OSA risk assessments, DPIA) |
| **`ostler-app-hub`** | public; AGPL-3.0-or-later (CLA, ADR-0012) | the shell add-on (npm `@ostler/app-hub`): link the account, publish, help threads with on-device encryption, forum and Discover in the shell, inbox; **and the public hub API contract** (`api/hub.openapi.yaml`) with its generated TS types |

**Separate from `ostler-cloud`** (owner's direction). Grounds, in ADR-0034's terms: different
purpose and contributors (community staff and moderators, not device services), different
release cadence (a forum and wiki change weekly), and a separate data-protection footprint:
public user-generated content and its moderation records are kept apart from device relay and
telemetry storage, with their own records of processing, DPIA and breach scope. The two may share
company infrastructure and, later, one identity service (§4, B 10).

### 3.2 How it relates to ADR-0013 and ADR-0012

- **ADR-0013 (open core, closed cloud).** The hub becomes Ostler's second closed service and
  takes the same **cloud boundary**: it talks to devices only through a documented HTTPS API;
  the open, device-side client (`ostler-app-hub`) holds that contract publicly; the hub **never
  imports platform code** (`openostler`, pack Python, firmware). It reads pack data and JSON
  Schemas **as data** from published pack releases (CC BY-SA, ADR-0012), never by running pack or
  platform code.
- **ADR-0012 (AGPL + commercial, CC BY-SA data, CLA).** The hub's own code is Ostler's
  proprietary work; no outside contributions are taken into it (staff and contractors assign
  their work). Its dependency tree carries **no third-party copyleft code** (no GPL, AGPL or
  LGPL linked into the server or shipped in the web bundle); separate programs it only talks to,
  such as PostgreSQL with PostGIS, are fine. The one bridge to open code is the shell's **kit
  and tokens** package, which the web app imports for one look: the maintainer may use it there
  because every contribution to it is under the CLA, provided a licence gate shows it contains
  only CLA-covered or permissively licensed code (B 8). User content licences are unchanged by
  the hub being closed (§13). The open client keeps the AGPL network clause meaningful for
  anything that runs on users' devices.
- **Trademark.** "Ostler Community" is the official service under Ostler's marks (TRADEMARKS.md);
  a reimplementation of the open API by others must use another name.

### 3.3 Stack (unchanged from v0.1, now under the licence gate)

Python 3.12+ ASGI (FastAPI or Starlette), SQLAlchemy and Alembic; **PostgreSQL + PostGIS**; a
Postgres-backed job queue; **S3-compatible** object storage (UK/EU region); **PMTiles** for
aggregate layers; PostgreSQL full-text search first (with exact-token indexes for fault codes and
hex). Web: **TypeScript + React**, server-rendered public pages (fast first paint, Open Graph
images), the shell's kit and tokens as a package, MapLibre lazy-loaded. The forum and wiki are
built in, not a third-party engine (B 19a has the alternative). One deployment, one database,
staging plus production; CI fails on a disallowed dependency licence.

**Topology.** One official instance at one domain, run by Ostler. Clubs live as clubs on it
(§12). *Amended 2026-10-07 (openness round):* the hub API (`api/hub.openapi.yaml`) is a
published, versioned contract with the same deprecation rule as the shell's API; a club or
anyone else may run their own implementation (under another name, TRADEMARKS.md) and devices
may point at it. No hub-to-hub traffic in v1.

## 4. Hub accounts and device linking

- **Hub-owned identity:** email plus **passkey** (primary) or password, optional TOTP; one
  person, one account; the same account signs into the forum, the wiki and vehicle development.
  The hub is a public HTTPS site, so it can offer Google or Apple sign-in **on the hub only**
  (B 10). A hub account **never signs anyone into a device**.
- **GitHub link (optional):** a contributor may link a GitHub account (OAuth, `public_repo`
  scope only, revocable) so pack PRs carry them as author (§10.4). Never required.
- **Linking a device user:** OAuth 2.0 **Device Authorization Grant** (RFC 8628) from a head
  unit or Brain ("Go to community.example and enter WXYZ-1234"), or **authorization code +
  PKCE** from the phone. The hub issues a refresh token **per device per local user**, scopes
  `publish`, `read`, `help` only (no admin scope leaves the web), stored in `auth.db` on the
  Brain (accounts §14.10), revocable from either side, listed in Settings → Sharing. The add-on
  points at the official hub by default; the user may set another hub URL (HTTPS, a compatible
  API version) in its settings (*amended 2026-10-07, openness round*; was official hub only,
  staging in developer builds).
- **Pairwise ids:** the hub sees an opaque id per (device, local user), never the device's
  peer-key fingerprint or any `ostler-cloud` id, so the hub cannot correlate a person with peers
  or with cloud records.
- **Household:** each local user links their own hub account; the vehicle owner's grants decide
  which vehicle data a driver may publish (accounts §14.2).
- **Later (P5 at the earliest):** the hub's identity service may become the **one Ostler
  account**, the link-only OIDC broker of accounts §14.8 that `ostler-cloud` also trusts (B 10).

## 5. Exit guarantee and data rights

ADR-0042 decision 7 is a hard rule, and a closed, single-operator hub makes it more important:

1. **Nothing in core depends on the hub.** Core imports and tests pass with `ostler-app-hub`
   absent and with the hub unreachable; the add-on degrades to local function (published items
   stay on the device; help falls back to file, relay link or pack issue form).
2. **Export everything** (Art 20): originals plus JSON, my forum posts and wiki edits as
   Markdown with metadata, decode cards as pack-schema JSON, club data for club owners (members
   list only with each member's consent, events, files), in open formats (GPX, JSON,
   `ostler.share/1`, Markdown, ICS, CSV). One button, one zip, within 24 h.
3. **Contributing never needs the hub.** Pack repos keep their `decode-request` and
   `diagnose-request` issue forms and accept PRs directly (trip-sharing §13).
4. **The knowledge survives Ostler.** Public CC BY-SA content (public forum threads, wiki pages,
   decode cards, public routes) is published as a **monthly public dump** with attribution by
   handle and no other personal data; generated vehicle pages are already in the pack repos.
5. **Shutdown promise.** At least 90 days' notice, export open throughout, a final dump.

## 6. What can be published

| Object | Comes from | Levels and audiences | Notes |
|---|---|---|---|
| **Trip** | core Trips share sheet | **L0 Card**, **L1 Route**: person, group/club, `link`, `public` · **L2 Telemetry**: person, group/club only | grants (trip-sharing spec). Public needs an explicit publish act and, for a route, the owner's delay after the trip ends (default 24 h); max speed hidden on public cards by default; L1 trimmed 500 m by default (the owner may go lower with a warning) with privacy zones |
| **Route** | `ostler-app-navigation` library or planner | private, group/club, `link`, `public` | a plan, not a recording; the same end-trim check warns when it starts or ends in a privacy zone |
| **Garage card** | Maintenance & Garage, Vehicles & Map §2.2 | `vehicle_card` basic; optional `maintenance` history (no costs; "for a buyer" preset) | plate hidden unless ticked, EXIF stripped, never a VIN, masked or not |
| **Event** | a club or a person | group/club, `link`, `public` | ICS, place at the organiser's precision |
| **Forum thread** | the web or the add-on | category audience: public, club or staff | §9; no attachments except parsable track files and E2E help attachments |
| **Help thread** | Diagnose, Trips, Decode lab | thread text: club or public; **attachment: named helpers only** | a forum thread of kind Help; carries **L3 Full log** or **L4 Diagnostics bundle** as a **hand-over**, never a grant (§8) |
| **Decode card** | a helper or the capture owner, in a thread | public, CC BY-SA 4.0 | derived decodes and short fixture snippets only, never the log (ADR-0036 §5); enters a pack only by PR (§10) |
| **Wiki page** | the wiki editor, or generated from a pack release | public, CC BY-SA 4.0 | §11 |

**Publishing is a grant, not a sync.** L0–L2 reach the hub only when the data owner grants the
`trips` class (and `location` at `route` detail for L1) to a hub audience. Ghost does not hide
past-trip grants (accounts §14.3), and the sheet says so. Every upload is scrubbed on the device
and passes `ostler share verify` first; the hub re-checks and **rejects** rather than repairs
(VIN pattern, identity reply, a point inside a declared zone).

## 7. Item states, links and their controls

**States (DMD-style):** **Private → Pending review → Public**. Link-only (`link` audience) items
skip review but are reportable. *Make public* opens an inline checklist (title, description
≥ 50 characters, region, vehicle, licence) and goes to **Pending review** until the account is
trusted (§14). Separate switches: **Allow download** (off) and **Show in Discover and search
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

## 8. Help threads and L3/L4 hand-overs

1. Started from Diagnose ("get help with this fault"), Trips (a time range), Decode lab (a
   signal) or the forum composer. The device builds an `ostler.share/1` bundle, shows the
   preview with its redaction report, runs the verifier, and `ostler-app-hub` uploads it
   **encrypted**; the key travels in the URL fragment of each helper's invite, so the hub stores
   ciphertext only (B 12). Because the operator is closed, the encryption lives in the **open**
   client, where anyone can check it.
2. The thread shows the question, vehicle chips (make, model, engine, year, pack and version),
   the level chip and **"time-boxed access: 6 days left"** (default 7 days, max 30, downloads ≤ 3).
3. Helpers are **named or accepted by the owner** one by one; a club "help desk" or a make's
   volunteer decoders may be offered as a group of helpers. The attachment opens in a
   browser-side viewer (signal plot, faults, freeze frames; later the decode workbench, §10.2);
   download only if the owner ticked it.
4. Helpers reply with text, links to moments ("see 00:12:31 on `Engine.Speed`"), decode cards
   and **recording recipes**; they never send requests or actions to the car (ADR-0033). A
   request for more (another class, a longer window) lands on the owner's device as a card,
   answered there.
5. **Mark as solved** credits the helper ("solved by @ali"); no votes, no points.
6. Expiry, revoke or account deletion destroys the ciphertext; the thread text stays, marked
   "attachment expired".

## 9. The forum

The forum is the hub's spine: help threads, decode work, club talk and announcements are all
threads in it.

- **Categories** follow the pack registry's vehicle taxonomy: **Make → Model**, with engine,
  generation and year range as tags (e.g. Land Rover → Discovery 2, tags `td5`, `v8`, `1998–2004`).
  A make has a "Not yet supported" sub-category for wanted vehicles. General categories:
  Announcements (staff), Getting started, Hardware (nodes, Brain, modules), Platform and add-ons,
  Pack development (cross-make protocols and tooling), Routes and trips (by region), Clubs and
  events, Site feedback. New make and model categories are created by staff when a vehicle
  project (§10.3) opens or on request.
- **Thread kinds:** Discussion · **Question** (Q&A) · **Help** (diagnose or decode, may carry an
  E2E attachment, §8) · **Pack proposal** (§10.5) · Announcement (staff). Every thread may carry
  vehicle chips; threads started from the add-on fill them from the device.
- **Q&A and solved:** a Question or Help thread has one accepted answer, chosen by the asker
  (or a category moderator after 14 days of silence, with a note), shown under the question with
  "Solved by @x". Profiles count "helped with N" only. On the official hub, by operator policy:
  no votes, reactions limited to a private "thanks" the author sees, no reputation score
  (optional answer upvotes may come later; *amended 2026-10-07, openness round*).
- **Search:** one search box over threads, decode cards, wiki pages, routes and events; filters
  for make, model, engine, category, kind, solved or open, has attachment; exact-token matching
  for fault codes (`P0101`, `1192`), hex and service bytes (`21 1B`), part numbers; "similar
  threads" shown while composing a question.
- **Notifications:** watch levels per category, vehicle tag and thread (Watching · Tracking ·
  Normal · Muted); defaults: replies to me, mentions and solved on my threads only. Channels: the
  hub inbox; email (immediate or daily digest, opt-in beyond direct replies); the add-on's Home
  card and inbox (counts while Moving, nothing else; UI spec §12.1); Web Push opt-in. No SMS.
- **Composer:** CommonMark with code blocks (hex dumps), tables, quotes and `@mentions`; links
  `rel="ugc nofollow"`; no images before H4 (§14); attachments only parsable track and log files.
- **No direct messages** between users (B 19b): talking privately belongs in Social; staff can
  message a user about moderation only.
- **Tools for moderators:** lock, move, merge, split, slow mode, pin, close; category moderators
  are trusted community members appointed by staff and working under Ostler's policies.

## 10. Vehicle development: from a help thread to a pack PR

### 10.1 The path

```
Help thread (Question/Help, vehicle chips, E2E capture to named helpers)
  → Decode cards (derived, public, CC BY-SA, evidence links)
    → Vehicle project page (per make/model/engine; status; target pack repo)
      → Bridge opens a PR on ostler-pack-<x> (data files + fixtures, credits, consent records)
        → Review, CI contract tests and merge on GitHub (source of truth)
          → Pack release → hub ingests it → wiki vehicle page regenerates
            → "Your capture helped decode fuel_temp" on the device (trip-sharing §13.7)
```

### 10.2 Decode cards and the workbench

A **decode card** is a structured, public proposal: VSS path or pack signal name, module and
protocol, request and response bytes, byte positions, formula, unit, range, expected values,
status (`candidate` until the pack's evidence rules say `proven`, UI spec §8.3), and evidence:
links to thread moments and **short labelled fixture snippets** (`response → expected_values`)
that pass the verifier. A card never holds a log. It is CC BY-SA 4.0 with the contributor's
own-work tick (ADR-0012). The **decode workbench** (H2) extends the browser-side viewer of §8: on
a decrypted bundle, in the helper's browser only, mark bytes, try a formula against the plot,
and save the result as a card. The workbench parses `ostler.share/1` from its published format
and schema, not from platform code (§3.2; open question 2).

### 10.3 Vehicle projects

One page per make, model and engine family: status **Wanted → Capturing → Decoding → Pack draft →
PR open → Released**; the target pack repo (an existing `ostler-pack-<x>` or "new pack"); the
decode cards; the open help threads; the people who helped (by their chosen credit); what is
still needed ("a capture of the ABS module at idle"). Vehicle projects are how the owner's "help
us develop and code new vehicles" becomes visible work.

### 10.4 The GitHub bridge

- **A GitHub App** ("Ostler Community bridge") installed on the `openostler` pack repos, with the
  narrowest permissions that let it open PRs from its own fork (pull requests: write; contents:
  read on the target; metadata) and receive PR, review and release webhooks.
- **What it sends:** only pack **data** files (signals JSON, DTC JSON, `maintenance.json` rows,
  fixture snippets) generated from accepted decode cards, validated against the pack's published
  JSON Schemas first. **Never** a log, a bundle, a VIN or an identity reply, and **never code**:
  code (Python, C keygen plugins) goes by the contributor's own PR so the CLA check sees them.
- **Who is the author:** if the contributor linked GitHub (§4), the PR is opened as them from
  their fork (they are the author; CLA Assistant checks them as usual). Otherwise the bridge
  opens it from its fork, the PR body lists each contributor by their chosen credit, and the hub
  records their acceptance of the **same CLA text** as `CLA.md` and their CC BY-SA own-work
  consent, linked from the PR (B 19d).
- **What the PR says:** the decode cards, links to the public thread parts (never the
  attachment), the evidence status, the credits for the pack's attribution file, and "Proposed
  through Ostler Community; review happens here."
- **Back to the hub:** webhooks mirror PR state (opened, changes requested, merged, closed) and
  releases onto the cards, the thread ("Decoded in `ostler-pack-lr-d2` 0.9") and the project page.
  Review comments stay on GitHub; the hub links to them.

### 10.5 Pack proposals and new packs

A **Pack proposal** thread (a vehicle with no pack yet) collects the vehicle, buses and
protocols, captures offered and volunteers. When maintainers accept it, a maintainer creates
`ostler-pack-<x>` from the pack template on GitHub (by hand, under ADR-0034's rule); the bridge
never creates repos. The project page then targets that repo.

### 10.6 Without the hub

Every step has a hub-free path: captures by file or relay link, decodes as an issue or PR on the
pack repo, credits in the PR. The hub makes it easier and visible; it is never the gate.

## 11. The wiki

**What exists today.** There is no Ostler wiki. The GitHub wiki feature is switched on for
`openostler/ostler` but has no pages (its wiki repository is not served); it is off for
`ostler-pack-lr-d2`; there is no docs site. Documentation is Markdown in each repo, indexed by
`INDEX.md` (`docs/`, `references/`, specs and ADRs), and vehicle knowledge lives in each pack's
data and `references/`.

**Proposal: the wiki is hosted in the hub** (`/wiki`), on the same accounts, search, moderation
and licence rules, so a forum answer can become a wiki page in one step (B 19c).

| Page kind | Source | Editing | Licence |
|---|---|---|---|
| **Vehicle pages** (make → model → engine) | **generated from each pack release**: modules and protocols, signals with `proven`/`candidate` status, fault codes with meanings and confidence, service schedules (`maintenance.json`), the protocol state, supported features, required hardware, pack version and repo link | read-only on the wiki; "Suggest a change" opens a decode card or a bridge PR (§10) | CC BY-SA 4.0, attributed to the pack and its contributors (the pages adapt pack data) |
| **Community pages** | written on the wiki: fitting guides, wiring, quirks, how-tos, glossary | trusted accounts edit directly; new accounts' edits go to review; full revision history and diff | CC BY-SA 4.0, required |
| **Platform docs** | stay in the repos (source of truth) | not copied; the wiki links to them on GitHub | the repo's licence |

Each vehicle page also shows the live forum category, open help threads and the vehicle project's
"still needed" list. The ingester reads pack releases as data (§3.2); a page regenerates on each
release and keeps its community sections. The owner may switch off the empty GitHub wiki on
`openostler/ostler` so there is one wiki (B 19c).

## 12. Discover, Following, clubs, events, live rides, comments

- **Discover** is the directory: public items, forum threads, wiki pages and clubs that chose to
  be listed. People are findable only through a public profile (18+, opt-in). No ranking
  algorithm: newest, nearest (coarse), most useful (solved count, completions) as explicit sorts.
- **Following** is opt-in, chronological, in `ostler-app-hub` only: new public items from people
  and clubs I follow. Never in Social, never on the web front page.
- **Groups and clubs:** any size; kinds friends · club · ride · safety (accounts §14.6); roles
  owner, moderator, member; join by code, link or approval. A core group may be **linked** to a
  hub club so a group grant can publish there. A club gets a forum category of its own (members
  only, or public) and may show a public face (name, about, events). Clubs replace v0.1's club
  instances.
- **Events:** listing, Going, capacity, ICS, CSV export of attendees for organisers, payment info
  as text only (no money handling), files locked until a start time and fetched ahead.
- **Live ride pages** (H3): **live follow ≤ 24 h**, ride-scoped, ended by ghost or ride end.
  Positions come from the rider's device with V&M §8's options (`trail_window`, `delay` 0–6 h,
  `show_speed`, `show_values`), are held **in memory only** for the session and **never stored**
  after it. **Listing** on Discover's "Live now" is opt-in, off for every ride, 18+, with a
  one-time warning that a listed ride is findable. No viewer chat in v1; members talk in Social.
- **Comments** on routes, trips and events; off by default on new public items; owners can
  close, hide or pin; deleted comments leave a tombstone so threads still read.

## 13. Privacy, law, age and licences

**Privacy.** Data minimisation: the hub keeps what a page shows, plus moderation and security
records. No ads, analytics or third-party scripts; UK/EU hosting; processors under DPAs; IP
addresses kept 30 days for abuse handling; access logs 30 days; no data shared with
`ostler-cloud` except what the user links (§4). L3/L4 stay end to end encrypted (§8).

**Duties: squarely on Ostler as the sole operator** (research §9; legal review before H1 opens
publicly). The forum makes the hub a user-to-user service with search, so: UK **OSA**
illegal-content and children's-access risk assessments (kept current as features ship), a named
**accountable person**, terms, swift takedown, reporting and complaints, records; EU **DSA**
points of contact, an EU legal representative if UK-based, **notice and action**, statements of
reasons, Article 18 notifications; **GDPR/UK GDPR**: consent for location, a **DPIA** before
launch, records of processing (separate from `ostler-cloud`'s), processors under DPAs, a DUAA
**complaints** process (30-day acknowledgement). There are no self-hosters to hand duties to.

**Rights.** **Export** everything (§5). **Deletion** (Art 17) removes originals and personal data
at once, derived tiles at the next rebuild, backups within 35 days; forum answers and wiki edits
become **"[deleted user]"** unless the person chooses "delete everything" (posts removed; wiki
revisions kept without attribution where CC BY-SA allows, after a legal check). Copies already
in a public dump or a merged pack cannot be recalled, and the consent text says so. A hub
deletion never touches the device's copy.

**Age.** Accounts **16+**; **live follow and public profiles 18+**; self-declared at sign-up,
backed by the children's access assessment (B 15).

**Licences** (B 16). Users **keep copyright** and give Ostler a licence to host and show an item
to its chosen audience, ending on deletion. **Public forum posts, wiki pages and decode cards
are CC BY-SA 4.0** (required); **public routes default to CC BY-SA 4.0** (opt out to "all rights
reserved"); club and private content stays the author's with the hosting licence only. OSM is
attributed on every map; OSM-snapped routes may carry ODbL duties (legal check). The hub's code
is Ostler's proprietary code; the client is AGPL with the CLA.

## 14. Moderation and abuse

- **Pre-moderation until trusted:** an account's public items, first forum posts, comments on
  public items and wiki edits wait in a review queue until it has ≥ 30 days and ≥ 3 approved
  items with no upheld report (B 14; the thresholds are operator settings). Trust is a
  moderation flag only, never shown as a score.
- **Report** on every object (reason, text, optional map pin; pinned warnings on routes until the
  owner marks them solved); **block** and **mute** (blocked people cannot see my items, reply to
  me or join my rides); rate limits per account and IP, tighter for new accounts; upload caps;
  strict parsing.
- **Staff review** by Ostler; club moderators handle their club and category moderators their
  category; every decision carries a **statement of reasons**, an **appeal** route to staff and
  an audit entry.
- **Uploads H1–H3:** only parsable track, trip and log files (session, `ostler.share/1`, GPX,
  FIT, KML); **no images or video**. Photos at **H4** only, with perceptual hash matching first
  and **face and plate blur on the device**.
- A code of conduct includes "no reposting other people's decodes or routes as your own", "no
  dealer-database content" (ADR-0012) and, added here, "no help with defeating immobilisers,
  odometers or emissions controls" (legal check before H1).

## 15. Screens

All screens use the [visual design system](2026-10-07-visual-design-system-design.md): dark by
default, one `accent` (primary action and anything live only), `surface-1` cards, sheets on
`surface-glass`, Figtree, Material Symbols, `series-*` for categories, ISO status hues with
words, **Ostler Night** maps (Day for Open Graph previews), flat by default, collapsed ⓘ
attribution, `cooperativeGestures` inside scrolling pages. Every object its owner sees carries
the **visibility chip** (`lock Only me`, `group Peak 4x4`, `link Link · 6 d`, `public Public`),
tapping into the visibility sheet (teardown §7.4). Numbers are honest: smoothed elevation with
its source, "—" for missing, the viewer's units with a km/mi Segmented.

### 15.1 Web app (`ostler-hub`)

Sitemap: `/` · `/t/<id>` · `/r/<id>` · `/g/<slug>` · `/e/<id>` · `/e/<id>/live` ·
`/ride/<token>` · `/forum` · `/forum/<make>/<model>` · `/forum/t/<id>` · `/dev/<project>` ·
`/decode/<id>` · `/wiki/<path>` · `/u/<handle>` · `/search` · `/me/…`.

| Screen | Layout (teardown §7.2 holds the ASCII for P1–P9) |
|---|---|
| **P1 Discover** | one search field; chips Routes · Trips · Events · Help wanted · Threads · Clubs; **make / model / engine / year** filter, region, vehicle type, "has faults", "has telemetry"; card grid with static Ostler Night thumbnails; side column "Help wanted on your vehicles", "Upcoming near you" (coarse region). No people feed |
| **P2 Shared trip** | full-bleed map, title card with level and audience chips, 420 px side sheet (phone: bottom sheet) with HeroStat distance, stat strip, elevation; tabs only for the level granted: Overview (L0+), Signals (L2), Faults (L2 with faults). L0 has no map. Trace `series-1` with casing; speed ramp only if the owner granted `show_speed` |
| **P3 Help thread** | a forum thread (P11) plus the attachment chip with time left, helper list and *Name a helper* |
| **P4 Group or club** | name, kind chip, member count, *Join with code*; tabs Forum · Rides · Routes · Events · Members · Files; a map of shared routes, never members' homes |
| **P5 Live ride** | full-bleed map, one title pill "● LIVE · 4 riding · ends 18:00", member pucks (`accent` for me), leader/sweep badges, delay badge; ends with "This ride has ended" and no positions |
| **P6 Event** | title card, When & where (dates in the event's zone, *Add to calendar*, *Copy coordinates*), Going · Maybe · Not going, files locked until start, comments |
| **P7 Profile** | avatar, name, bio, garage row of cards, public routes and trips, linked GitHub (if shown); counts "helped with 12 decodes", "completed 3 routes"; **no map of the person's places** |
| **P8 Publish** | 1 Choose · 2 Level · 3 Audience and time · 4 Preview rendered **from the scrubbed bundle** · Publish; Public checklist inline |
| **P9 My shares** | one ListRow per link or publication: level chip, audience chip, expiry countdown, views, *Revoke* (two taps), *New link* |
| **P10 Forum** | category list grouped by make, each with model sub-rows, unread counts and "N open questions"; a vehicle switcher pinned to my garage's makes |
| **P11 Thread** | title, kind and solved chips, vehicle chips; posts as ListRows with quote and reply; the accepted answer under the question; watch level control; *Mark as solved* for the asker |
| **P12 Vehicle project** | status stepper (Wanted → Released), target pack repo, decode cards table with status chips, "still needed" list, open threads, PR links with GitHub state |
| **P13 Decode card** | fields as §10.2 in a form-like card, evidence links, fixture snippets in monospace, licence line, *Propose to pack* (trusted accounts) |
| **P14 Wiki page** | generated sections with a "From `ostler-pack-<x>` vX.Y" band and *Suggest a change*; community sections with *Edit* and *History*; side column: forum category, open threads, project status |

Share out: **Web Share API, copy link, QR, embed card**; RSS/Atom for categories and public
routes, ICS for events; no social-network buttons or scripts. Sign-in walls: `public` readable
signed out (forum and wiki included); `link` needs only the link; club content, live rider lists
and help attachments need a signed-in member or a named helper.

### 15.2 In-shell add-on (`ostler-app-hub`)

| Slot | Content | Driving rule |
|---|---|---|
| **More → Community** (`more:hub`, app-model §15) | tabs **Discover · Forum · Help · Mine**; Discover has the opt-in **Following** chip (add-on only); Forum opens my vehicles' categories first | Parked or passenger |
| **Trips share sheet** (core) | adds hub audiences (clubs, `link`, `public`) to the P8 steps; the sheet itself is core Trips | Parked, or Idling with Park evidence |
| **Diagnose → fault → Get help** (core) | adds "Ask on Ostler Community" (a Help thread, preset to L4, vehicle chips and fault codes filled) | Parked |
| **Decode lab → Ask for help decoding** | adds a Help thread preset to L3, linked to the vehicle project if one exists | Parked |
| **Home card** (`home:card`) | "2 replies on your help request", "Event tomorrow 09:00" | hidden while Moving; the strip shows a count only |
| **Settings → Sharing** (core, accounts §14.7) | P9 rows and the linked hub account | — |
| **Head unit** | nothing while Moving; Parked: replies and events as ListRows ≤ 30 characters | UI spec §12.1 |

All add-on screens are reachable with `ShellInput`; the add-on puts nothing in the Drive menu.

## 16. Storage, costs and phases

| Object | Where | Format |
|---|---|---|
| Original upload | object store, private | zstd, SHA-256 key; never served to the public |
| L3/L4 attachment | object store, private | ciphertext only; deleted at access-until |
| Display trace | PostGIS + object store | simplified per zoom, zones cut **before** storage |
| L2 signal series | object store | columnar chunks fetched by range (format chosen at H1) |
| Forum posts, decode cards, wiki revisions | PostgreSQL | Markdown source plus rendered cache; full-text and exact-token indexes |
| Pack releases (for the wiki) | object store | the released data files, as published |
| Public dump | object store, public | monthly, CC BY-SA content only |
| Public route layer, heatmap (H4) | object store, public | PMTiles rebuilt nightly, public routes only, minimum count per cell |
| Live ride positions | server memory | never written to disk |

**Quotas and money** (B 17). Free accounts get a storage quota; the forum, the wiki, vehicle
development, help threads and sharing are free. **Safety, sharing and decode help are never
charged for.** Extra hosted storage is the only paid item (relay stays an `ostler-cloud`
service). Rough cost: objects ~$150/month at 10,000 users × 1 GB, compute $50–150/month; people
(moderation, legal, community) are the real cost, now carried by Ostler alone.

| Phase | Scope | Needs |
|---|---|---|
| **H0 Specs, policy, repo** | this spec; ADR-0029, ADR-0034, ADR-0042 amendments; the private `ostler-hub` repo (B 19e); terms, privacy notice, OSA risk assessments, DPIA drafts; the public API contract draft in `ostler-app-hub` | owner approval |
| **H1 Forum, help and publish** | accounts and device linking; the forum (categories, Q&A, solved, search, notifications); help threads with L3/L4 hand-overs; decode cards; Discover; publish L0/L1 trips and routes (`link`, `public` with review), L2 to clubs; generated wiki vehicle pages (read-only); report/block, export/delete; files only, no images | accounts P1–P3, trip-sharing registry pieces and verifier, core Trips share sheet, legal review |
| **H2 Build vehicles together** | vehicle projects, the GitHub bridge, the decode workbench, wiki community pages, pack proposals, clubs, events, comments, garage cards, the Following chip, Home card, the public dump | H1 moderation queue; GitHub App approval |
| **H3 Live rides** | live ride pages ≤ 24 h, opt-in listing | Vehicles & Map V5 relay link |
| **H4 Media and maps** | photos with hash matching and on-device blur, PMTiles route layer and heatmap | CSAM tooling, DPIA update |

v0.1's **H5 Federation** is dropped (B 18).

## 17. Tests

- `ostler-hub` CI fails on any dependency whose licence is GPL, AGPL or LGPL, and on any import of
  `openostler` or pack code; the kit package passes the licence gate before each bump.
- The core import and network tests pass with `ostler-app-hub` absent and with the hub
  unreachable (ADR-0042 confirmation).
- The server conforms to `ostler-app-hub`'s published OpenAPI document (contract tests in both
  repos).
- No upload route accepts a file that does not parse; images refused before H4.
- Server-side re-check rejects a VIN pattern, an identity reply or a point inside a declared zone;
  no response, log or audit entry ever contains a VIN or HMAC.
- L0/L1 public items: trims ≥ 200 m, no point timestamps, stats recomputed from the visible
  trace, max speed absent; a route cannot go public < 24 h after its trip ends.
- `link` and `public` refused for L2, L3, L4, live location beyond a ride, audio and video.
- L3/L4: the hub stores ciphertext only; unreadable after access-until or revoke; a non-named
  member gets 403.
- Device linking: RFC 8628 and PKCE flows; tokens scoped to `publish`/`read`/`help`; the pairwise
  id differs from every peer fingerprint and cloud id; revoking on either side ends uploads.
- Forum: an untrusted account's first post stays Pending; solved shows one accepted answer;
  exact-token search finds `21 1B` and `P0101`; no route exists for user-to-user messages.
- Bridge: emits only schema-valid data files; refuses a card whose fixture fails the verifier;
  never emits code or a bundle byte; PR body carries credits and consent links; webhooks update
  card state.
- Wiki: generated sections are read-only and carry the pack version and CC BY-SA attribution; a
  pack release regenerates them without touching community sections.
- Live ride: no position row reaches the database; no positions after end or 24 h.
- Moderation: report → decision carries a statement of reasons; block hides items both ways.
- Export contains every original, post, wiki edit and card; deletion leaves tombstones only; the
  public dump contains no e-mail, IP or private item.
- Web pages pass the visual spec's contrast checks and load no third-party script.

## 18. Open questions

1. Which ASGI framework (FastAPI or Starlette) and the L2 series format (Parquet or Arrow IPC).
2. How the browser viewer and workbench parse `ostler.share/1` without pack decoders: decode with
   published pack data in the browser, or show raw frames plus the bundle's own decoded channels.
3. The GitHub App's exact permissions, and whether a bot-opened PR with a hub-recorded CLA
   acceptance satisfies CLA Assistant (or needs a maintainer override each time).
4. Exact OSA children's-access outcome with self-declared age, and the EU representative.
5. Whether CC BY-SA wiki revisions may stay after an author's "delete everything" (legal check).
6. The quota size, measured on real sessions; the dump's format (JSON Lines plus Markdown).

## Changelog

- 2026-10-07: v0.1, first draft (DMD round), from the hub architecture, DMD Hub feature and UI
  research and the trip-sharing positions.
- 2026-10-07: v0.2, revised in place for the owner's direction ("our own thing, closed not self
  hostable", forum, vehicle development, wiki, new repo): `ostler-hub` becomes a private, closed,
  Ostler-run service with one instance, separate from `ostler-cloud`, under ADR-0013's cloud
  boundary; `ostler-app-hub` stays AGPL and holds the public API contract; added the exit
  guarantee section (§5), the forum (§9), vehicle development and the GitHub bridge (§10), the
  wiki (§11, none exists today), privacy and operator duties (§13), screens P10–P14; dropped
  self-hosting, several hubs per device and H5 federation; licences now require CC BY-SA for
  public forum posts and wiki pages; decision items revised (B 7–19) and new items B 19a–19f.
- 2026-10-07: v0.3, approved by the owner on 2026-10-07 ("approve all", DMD round): every
  decision item (B 7–19, 19a–19f) answered as recommended (alternatives not chosen); the
  ADR-0029, ADR-0034 and ADR-0042 DMD-round amendments approved with it.
- 2026-10-07: v0.4, amended (openness round, approved by the owner on 2026-10-07, "apply the
  loosenings", [ADR-0047](../decisions/adr-0047-openness-round.md)): the hub API is a published,
  stable contract others may implement; the add-on's hub URL is user-settable; the official
  hub's no-votes, no-points and moderation thresholds are operator policy; publishing follows
  the trip-sharing defaults. `ostler-hub` stays private and closed.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each recommendation
below is the decision; each alternative was not chosen. The hub's decisions are the items
below; where v0.1's open, self-hostable model is relevant, it was the alternative.

### Items of the DMD decision list (hub, B 7–19)

7. **Build it, and as what?** *Recommend:* yes, as an optional add-on pair after accounts P3: a
   **closed service run by Ostler** (`ostler-hub`, one official instance, not self-hostable) that
   is the publishing hub, the project forum, the vehicle-development workspace and the wiki, with
   the open shell add-on `ostler-app-hub`. *Alternative:* v0.1's open AGPL codebase, self-hostable
   by clubs plus one official instance, devices linking to several hubs. *Alternative 2:* share
   sheets and device-to-device sharing only.
8. **Stack and licence gate?** *Recommend:* Python ASGI, PostgreSQL + PostGIS, S3-compatible
   storage, PMTiles, TS/React web on the shell's kit and tokens (used under the maintainer's
   rights through the CLA, behind a licence gate); no third-party copyleft code in the hub; no
   platform code imported. *Alternative:* release the kit and tokens package under a permissive
   licence (MIT) so any client, open or closed, may use it; or PocketBase/Go as wanderer uses.
9. **Name?** *Recommend:* "Ostler Community" (More → Community), repo `ostler-hub` (private).
   *Alternative:* "Ostler Hub" as the product name, the owner's word, now that the Brain no
   longer uses it (it was the Brain's old name, so old docs may confuse).
10. **Hub accounts?** *Recommend:* hub-owned accounts (passkey first) for the site, forum and
    wiki; devices link by RFC 8628 or PKCE with pairwise ids; optional Google/Apple sign-in on
    the hub site only; optional GitHub link for contributors; later the hub's identity becomes
    the one Ostler account that `ostler-cloud` trusts (accounts §14.8). *Alternative:* identity
    lives in `ostler-cloud` and the hub is its client; or passkeys and passwords only.
11. **Public and link sharing from H1?** *Recommend:* yes, unchanged: trip cards and routes,
    garage cards and events, by explicit publish only, reviewed until trusted (amends ADR-0029).
    *Alternative:* link-only until clubs exist (H2).
12. **Help threads end to end encrypted?** *Recommend:* yes, unchanged, and now essential: the
    open client encrypts, the closed hub stores ciphertext only, named helpers get the key;
    7 days default, 30 max, ≤ 3 downloads. *Alternative:* the server can read attachments, plus a
    second server-side scrub (asks users to trust a closed operator with raw logs).
13. **Feed?** *Recommend:* Discover (make, model, engine filters) for everyone, the forum by
    category, and an opt-in Following chip in the add-on only; no points, ranks or votes;
    "solved" credits only. *Alternative:* a Following tab on the website too.
14. **Moderation?** *Recommend:* staff-run, with appointed club and category moderators;
    pre-moderation of public items, first posts and wiki edits until ≥ 30 days, ≥ 3 approved
    items and no upheld report; trust never shown as a score. *Alternative:* staff promote users
    by hand.
15. **Age?** *Recommend:* accounts 16+; live follow and public profiles 18+. *Alternative:* 13+
    with parental controls (a much heavier OSA children's duty for a forum).
16. **Licences?** *Recommend:* users keep copyright; **CC BY-SA 4.0 required** for public forum
    posts, wiki pages and decode cards, default for public routes, so the knowledge can be dumped
    and survives Ostler; the hub code is proprietary, the client AGPL. *Alternative:* users keep
    copyright with a hosting licence only for forum posts (no public dump of the forum).
17. **Money?** *Recommend:* keep the rule: free accounts, forum, wiki, vehicle development and
    sharing; never charge for safety, sharing or decode help; only extra hosted storage is paid.
    *Flag:* a closed hub run by Ostler alone is a cost (moderation, legal, community) with no
    revenue of its own; it is funded by hardware, cloud and commercial licences.
    *Alternative:* a paid club tier (club categories, events tooling).
18. **Federation?** *Recommend:* none, with no phase; open read paths instead (RSS/Atom, ICS,
    embeds, public GPX where allowed) and the monthly CC BY-SA dump. *Alternative:* outbound-only
    ActivityPub from the official instance later, allowlist mode (v0.1's H5).
19. **Legal duties before H1 opens publicly?** *Recommend:* all on Ostler as sole operator: a
    named accountable person and an EU representative; a DPIA; OSA illegal-content and
    children's-access risk assessments covering the forum and search; DSA notice and action; a UK
    data-protection complaints process; records of processing separate from `ostler-cloud`.
    *Alternative:* open invite-only until the paperwork is done.

**New hub items (labelled 19a–19f so they sit in group B without renumbering the list):**

- **19a.** **Forum engine?** *Recommend:* built into `ostler-hub`, because help threads, E2E attachments,
    vehicle chips and decode cards are the forum's core objects. *Alternative:* run Discourse
    (GPL-2.0, unmodified, as a separate service) with single sign-on from hub accounts, linking
    threads to hub objects.
- **19b.** **Direct messages?** *Recommend:* none between users; Social is the messenger; staff may
    message about moderation only. *Alternative:* DMs between trusted adults (adds grooming and
    harassment duties under the OSA).
- **19c.** **Wiki?** *Recommend:* hosted in the hub at `/wiki`, vehicle pages generated from pack
    releases (read-only, changes go through decode cards or PRs) plus community pages under
    CC BY-SA; platform docs stay in the repos and are linked; switch off the empty GitHub wiki
    on `openostler/ostler`. *Alternative:* a separate wiki engine (Wiki.js or MediaWiki) under
    hub single sign-on at its own subdomain; or the GitHub wiki with GitHub accounts only.
- **19d.** **GitHub bridge?** *Recommend:* a GitHub App that opens data-only PRs (as the contributor if
    they linked GitHub, else from the bridge with credits and a hub-recorded CLA and CC BY-SA
    consent), mirrors PR and release state back, and never sends code, logs or bundles.
    *Alternative:* the hub only drafts a PR description and the contributor opens the PR
    themselves on GitHub (GitHub account required to contribute through the hub).
- **19e.** **Create the private `ostler-hub` repo now or at H1?** *Recommend:* **now**, empty and
    private, so H0's policy drafts, the server-side internals of this spec and the API contract
    work have a home outside the public repos; this spec's public parts (API, rights, client,
    privacy promises) stay public in `ostler`, server internals move there. I ask before
    creating it. *Alternative:* at H1 as v0.1 planned, keeping everything in this public spec
    until then.
- **19f.** **The client add-on open or closed?** *Recommend:* `ostler-app-hub` open (AGPL), so the
    encryption, the verifier call and what leaves the device can be checked, and it bundles into
    the AGPL shell build without a licence exception; the public OpenAPI contract lives there.
    *Alternative:* a closed add-on (more control; breaks E2E auditability and needs a commercial
    licence path to ship inside shell builds).
