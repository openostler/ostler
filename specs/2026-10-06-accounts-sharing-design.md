---
title: "Accounts, multi-vehicle garage, sharing and social — design"
area: specs
status: stable
version: 0.7
updated: 2026-10-07
depends_on: [decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-u0-seams-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, CONSTITUTION.md, GOALS.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, decisions/adr-0041-brain-ed25519-signing.md, specs/2026-10-06-app-model-design.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md, references/research/calls_video_camera_sharing.md, references/research/maintenance_trackers.md, specs/2026-10-07-trip-sharing-design.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, references/research/dmd_hub_features.md]
summary: >
  Approved by the owner on 2026-10-06 (ADR-0029, with roles and approvals from ADR-0033). Local users on each device with an owner bootstrapped by a physical setup code (phone pairing on Ostler Diagnostics alone); passkeys through the optional extra openostler[passkeys], scrypt passwords always available, cookie sessions and scoped, revocable tokens (also for AI/MCP clients, RFC 8628 device flow). Roles (Owner, Driver, Viewer, Mechanic) grant action categories, each capped by its tier; the gate takes the intersection of role, share and token categories at the minimum tier, then the transport rule (local links; remote read-only unless the install-level OSTLER_ALLOW_REMOTE_CONTROL override is set) and the driving state. The head-unit kiosk session gets Read and Comfort only. A garage that defaults to the car the node is on, with friends' cars added by invite (link or QR, pinned device key, expiry, revocation, audit) over LAN, Tailscale or the future relay; data stays on each car's device. Per-share privacy: location opt-in; no VIN, HMAC, raw capture or audio ever. Later: groups, rides and convoys for bikers and off-roaders, and outbound share intents, webhooks and bots. Bikes use a guardian-variant or Ostler Diagnostics node with the phone as the screen. Phases P1–P5, data model, routes, tests, threats and the remaining open questions. Amendment (2026-10-07, §14), approved by the owner on 2026-10-07 ("approve all"): one add-on-extensible data-class registry (presence, vehicle card, location, live signals, trips, faults, notes, maintenance, video as per-camera grants, audio) with audiences me, person, group, household and public-later; ghost mode on by default for every user and add-on with one master toggle; precise location always expires within 24 h and nobody raises another's precision except one's own SOS to safety contacts; contacts, groups and rides (ride-scoped grants end at ride end) and 8-character invite codes; the shell screens (first run, sign-in, passkeys, head-unit profiles, users, devices, sharing with View as, ghost chip, safety contacts); social login later as a link-only OIDC broker; a hard Basic Auth end; auth.db on the Brain with a signed roster on the node. Proposed amendment (2026-10-07, DMD round, §15, v0.7, awaiting the owner): a `route` detail on the `location` ladder (finished, trimmed, simplified, no timestamps; may be indefinite; public only by explicit publish ≥ 24 h after the trip); a `link` audience for L0–L1 trips, `faults` and `vehicle_card` only; `public` brought forward for Ostler Community by explicit publish only; live-trip grant options trail_window, delay (0–6 h), show_speed and show_values; DMD-style link controls (Locked or Download, available-from, expiry, access-until, collection and download limits, states); L3–L4 stay hand-overs, never grants.
---

# Accounts, multi-vehicle garage, sharing and social — design

**Status:** approved by the owner on 2026-10-06 (v0.2). The decisions are
[ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) and, for
categories, phone approval and the remote rule,
[ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md). Each phase may split
into its own spec; the questions the owner did not take up (§13) block nothing in P1.
**Amendment (2026-10-07), approved:** [§14](#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens),
approved by the owner on 2026-10-07 ("approve all") (v0.6), unifies the permission
vocabulary and specifies the shell screens.
**Proposed amendment (2026-10-07, DMD round), awaiting the owner:**
[§15](#15-proposed-amendment-2026-10-07-dmd-round-trip-sharing-in-the-registry) (v0.7) adds the
registry pieces per-trip sharing needs. Until the owner answers, §14 stands unchanged.

## 1. Where we are, plainly

- **Is it multi-tenant? No.** One device, one process, no notion of a user. Every logbook
  session carries a `vid` (U0), with one local vehicle in `logs/vehicle.json`. The garage,
  switcher and `/vehicles/<vid>/…` are designed (UI spec §4.1, U6) but **not built**.
- **There are no users, roles, sharing or invites.** Auth is one admin password checked by
  HTTP Basic (`_admin_ok`); with no password, admin is ungated. Public mode refuses writes,
  hides real sessions and requires that password. Everything else is open to the LAN.

**Target:** multi-user, multi-vehicle devices sharing with each other, with no central
account. Ostler Cloud (ADR-0028) may later be the one multi-tenant piece, as
an optional relay and directory, never the source of truth.

## 2. Users and authentication

### 2.1 Bootstrap

- On first run with no owner, the server prints a **setup code** (8 digits, single use,
  15 min) on the device's own display and console, and every page shows "Set up this
  Ostler". Entering it creates the **owner**. No default password exists (UK PSTI;
  ADR-0027 §8 uses the same physical-confirmation idea for pairing).
- Upgrade: an existing `--admin-password` / `D2DIAG_ADMIN_PW` becomes the owner's password
  (user `owner`, prompted to rename and add a passkey). Basic Auth keeps working for one
  release, mapped to the owner, then goes.
- **Ostler Diagnostics alone** (a node with no Brain, [ADR-0032](../decisions/adr-0032-one-node-optional-brain.md))
  has no display or console. The owner is bootstrapped by **pairing a phone** with the node
  (a physical step on the node, such as a button press or a code on its label); the pairing
  keys on the phone sign the owner in. There is no Pi CA without a Brain; trust comes from pairing.
- Lost owner: `ostler auth reset-owner` on the device console (physical or SSH) issues a
  new setup code and deletes no data.

### 2.2 Passkeys first, passwords always

- **Passkeys (WebAuthn L3):** discoverable credentials, user verification required,
  attestation `none`. Secure context only: HTTPS from the device CA (ADR-0021) or
  `http://localhost` on the head unit.
- **The RP ID constraint.** The RP ID must be a domain the page is served from; IP
  addresses are not allowed ([web.dev](https://web.dev/articles/webauthn-rp-id)). So:
  - the device needs a **stable name**: its mDNS name (`ostler-xxxx.local`, to be checked
    on Chrome, Safari and Firefox on the bench), its Tailscale name (`*.ts.net`, with a
    real certificate from `tailscale cert`), or the relay's name;
  - a passkey works only on the name it was made on. The account page lists each
    passkey with its name, and the login page offers the password when none matches.
    Related Origin Requests (WebAuthn L3 §5.11) can join names under one domain later.
- **Passwords:** at least 12 characters, checked against a small bundled breached-list
  sample, hashed with `hashlib.scrypt` (n=2^17, r=8, p=1, 16-byte salt, per the OWASP
  password storage guidance). Login is rate-limited per user and per address. Optional
  TOTP second factor (stdlib `hmac`), as Home Assistant's MFA modules offer.
- **Verification library:** passkeys need ES256/EdDSA verification and CBOR, which stdlib
  lacks. They ship as the optional extra `openostler[passkeys]` (`cryptography`, packaged
  by Debian as `python3-cryptography`); CBOR decoding is a small stdlib module of our own.
  Without the extra, the UI hides passkeys. Passwords are always available. (Q1, answered.)

### 2.3 Sessions

- A random id in a `__Host-ostler` cookie (Secure, HttpOnly, SameSite=Strict), stored
  hashed; 30 days sliding on a trusted device, else 12 h. Writes check `Origin` (CSRF).
- The head unit can hold a **kiosk session**: a session with no sign-in, bound to
  localhost, that survives reboots, so the car's own screen never asks for a login while
  driving. It gets the **Read and Comfort** categories only (ADR-0033 §2). Clearing codes,
  Security and everything above need a signed-in user, such as a driver.

### 2.4 Tokens

- Modelled on Home Assistant's refresh and long-lived tokens: `ost_` + 32 random bytes,
  shown once, stored as SHA-256. Each has a name, owner user, scopes, expiry (default 90
  days, maximum 1 year), `last_used` and the address it was last used from.
- **Scopes:** `vehicles` (list of vids or `*`), `categories` (default Read), `max_tier`
  (default 0), data classes
  (`live`, `faults`, `sessions`, `location`, `notes`), and `admin` (users, shares).
- **AI and MCP clients** use the same tokens (ADR-0030), Read only unless the owner widens
  them, never beyond the user's role. A token never approves anything (ADR-0033 §6). Headless clients pair by the OAuth 2.0
  device grant (RFC 8628): a short code, approved with chosen scopes in Settings.

## 3. Roles and permissions

### 3.1 Roles

Roles grant **action categories** ([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)
§1, which holds the category table); each category is capped by its tier and has its own
driving-state rule.

| Role | Categories | Can also | Lifetime |
|---|---|---|---|
| **Owner** | all, up to Tier 3 | users, shares, tokens, service mode, delete data | permanent; at least one |
| **Mechanic** | Read, Maintenance, Actuator tests, Procedures | service mode; read sessions of the shared vehicle | **always time-boxed** (default 24 h, max 14 days) |
| **Driver** | Read, Comfort, Security, Maintenance; Accessories if granted | Mark, notes, start and stop logs, clear codes | permanent or time-boxed |
| **Viewer** | Read | location only if granted | permanent or time-boxed |
| *Kiosk session* | Read, Comfort | head unit only, no sign-in | until revoked |

The owner can add or remove categories per user (never Coding). Tier 4 is runnable by
nobody (ADR-0018 Q11). A device may have several owners.

### 3.2 The one rule

```
allowed(action) = action.category in (role.categories ∩ share.categories ∩ token.categories)
                  and action.tier <= min(category_cap(action.category), role.max_tier,
                                         share.max_tier, token.max_tier)
                  and transport_ok(transport, action)
                  and state_ok(driving_state, action.category, action.tier)
                  and every existing precondition, confirm and lockout passes
```

- `transport_ok` is ADR-0033 §6. **Local links** (the head unit, the in-car LAN, the node's
  Wi-Fi AP, BLE to the node) allow everything the rest allows. **Remote paths** (a share over
  Tailscale or the relay, MQTT, Home Assistant) are **read-only**, plus arming and disarming the software alarm (owner, 2026-10-06:
  disarm over the air is allowed; it needs a user or token whose role grants Security, and
  every remote disarm is audited and notified to the owner), unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL`
  override is on; it is set only in the environment or install config, defaults off and can
  never be set remotely. MQTT and Home Assistant never reach Tier 2+.
- `state_ok` is the category's while-moving rule (ADR-0033 §1) over UI spec §3.5: Comfort
  and Security arming are allowed while Moving (driver-safe UI; anything that transmits on a
  vehicle bus stays Parked-only); Maintenance is Parked or Idling; Actuator tests and
  Procedures are Parked only (Idling where `engine_running_ok`); Moving or unknown speed on
  a head unit locks everything else for **every** role, the owner included.
- **Phone approval.** A paired phone of a user whose role grants the category may approve
  Tier 2–3 over a local link; the node gate re-checks Parked at execution and the phone
  shows Stop. An accept inside an AI client never counts (ADR-0033 §6).
- Roles narrow; they never widen. No role skips a confirm, a typed confirm, a precondition
  checklist, the ActiveTestBanner or the 12 V floor. Every Tier 1+ action is logged with
  the user, as today plus `user_id`.
- The check lives in the gate: the node's transmit gate for car-touching actions
  ([ADR-0032](../decisions/adr-0032-one-node-optional-brain.md)), the server gate
  (`commands.py` path) for the rest; the UI only hides buttons.

## 4. Multi-vehicle garage

- **Default vehicle:** the one the node is on, found by the
  connection ladder and identified per UI spec §4.4 (the HMAC fingerprint matches a garage
  entry, else a new local vehicle is offered). This is `garage.active`, and it owns the
  port (one live link per port, never interleaved).
- **Viewing ≠ connecting.** Viewing a shared vehicle leaves the local one on the port. The
  switcher groups "This car", "My other cars" (last-known summary with age), "Shared with me".
- **Nearby devices:** Ostler devices on the same network (a campsite Wi-Fi, a phone
  hotspot in a convoy) are found by mDNS and listed as **nearby**, showing only the name
  their owner chose to advertise. Advertising is off by default and carries no `vid`.
  Nearby gives no data; an invite does.
- **Data stays home.** A shared vehicle's data is fetched on demand from its own device
  through the share and cached in memory only (no copy on disk), so revocation is real.
  An offline one shows "Offline since …".

## 5. Sharing and invites

### 5.1 Two kinds of invite

| Kind | For | Result |
|---|---|---|
| **Person invite** | someone who will use *this* device: a family driver, a mechanic at the car | a local user with a role; they set their own passkey or password |
| **Vehicle share** | another Ostler device or person elsewhere: a friend, a club | a share on one vehicle with a level; their device pulls through it |

### 5.2 Invite payload

A link or QR: `https://<device-name>/invite#v1.<payload>`, the payload in the fragment so
it never reaches a server log. It holds: kind, role or share level, expiry, a single-use
secret (128 bit), the device's endpoints (LAN name, Tailscale name, relay id) and its
**certificate fingerprint**, which the redeeming device pins (device-to-device TLS needs no
public CA). Unredeemed invites expire (default 48 h). The owner can revoke them.

### 5.3 Share levels and privacy

- **Levels:** `view` (Read: live, faults, ident), `view+logs` (adds sessions and
  replay), `driver` and `mechanic` (local person invites only, since remote paths are
  read-only, ADR-0033 §6).
- **Location**, per share, off by default: `none` · `place names` · `precise history` ·
  `live during a ride`. Sessions shared without location have traces removed server-side.
- **Never shared:** the VIN and its HMAC (a masked VIN at most, ADR-0018 Q7), raw captures
  (`logs/`, `captures/`), audio (ADR-0010), Decode evidence, private notes, other vehicles.
- Each share has an expiry (optional for `view`), a revoke button and an **audit log**:
  created, redeemed, each pull (time, peer, data class, coarse size), revoked.

### 5.4 Transports

| Transport | When | Notes |
|---|---|---|
| **LAN** | same network | mDNS name, pinned certificate |
| **Tailscale** | owner already uses it | Tailscale node sharing gives a friend reach to one device; `*.ts.net` names suit passkeys |
| **Ostler Cloud relay** | no VPN, phones on mobile data | ADR-0028; the relay should carry end-to-end TLS it cannot read |

## 6. Social (long-term, all opt-in)

- **Groups and clubs:** a group is a set of shares to and from members, with a group
  owner; hosted on one member's device or the relay. No global directory by default.
- **Rides and convoys** (bikers, off-road trips): a ride has members, a time window and a
  route. During the ride, members may share **live position** to the group only; it stops
  at ride end. Glanceable on head units (Moving lockouts apply: no text entry, no lists
  over six items); on bikes the phone or a small display shows only distance to the
  leader and the sweep.
- **Bikes** carry a guardian-variant or Ostler Diagnostics node (ADR-0032), with the phone as the screen.
- **Ride summaries:** route, distance, duration, stops and chosen vehicle data (coolant
  peaks, low-range time). **Privacy zones** trim the ends near saved places, as fitness
  apps do. GPX export exists.
- **In-house, minimal:** a group feed of ride summaries and comments, member list, ride
  invites. No likes economy, no algorithmic feed, no ads, no tracking, no analytics.
- **Federation:** ActivityPub (W3C) is public by default, deletion is best-effort, and it
  needs a server per group. Reference only; a candidate later for **public** club pages.

## 7. Integrations, the Spotify pattern

Spotify's pattern: every thing is a rich card with a link back, handed to the share sheet
and the big networks, plus a small in-house social layer. For Ostler, in order of cost:

| Way out | Examples | Needs |
|---|---|---|
| **Share sheet** | Web Share API (secure context, user gesture): reaches WhatsApp, Signal, Telegram, Messages on phones | nothing |
| **Share links** | WhatsApp click-to-chat (`wa.me/?text=`), Telegram `t.me/share/url`, Facebook Share dialog | no review; Facebook needs an app id for its dialog |
| **Owner's own bot or webhook** | Discord incoming webhook, a Telegram bot from BotFather, ntfy, Matrix, Home Assistant notify | the owner pastes their own URL or token; no review |
| **Business APIs** | WhatsApp Business Platform, posting to Facebook pages or groups, Instagram | Meta app review and business verification; only ever through Ostler Cloud, if at all |

- Cards (ride summary, "fault fixed", trip map) are drawn in the browser (canvas) and show
  only what the share allows (no VIN, no precise home).
- Outbound is **user-initiated** by default. Automatic notifications ("convoy stopped",
  "alarm") need a per-destination opt-in and use the owner's own webhook or bot.
- **No third-party login.** "Sign in with Facebook" is rejected (ADR-0029).

## 8. Data model sketch

`<state dir>/auth.db`, stdlib `sqlite3` (the logbook index already uses SQLite), WAL,
schema-versioned. JSON files were considered; SQLite wins on atomic revocation and the
audit log. (Open question 4.)

| Table | Columns (main) |
|---|---|
| `users` | id, name, role, created, expires, disabled |
| `passkeys` | id, user_id, credential_id, public_key, sign_count, rp_id, label, created, last_used |
| `passwords` | user_id, scrypt params, salt, hash, changed |
| `sessions` | id_hash, user_id, created, expires, kiosk, user_agent |
| `tokens` | id, hash, user_id, name, scopes (JSON), expires, last_used, revoked |
| `invites` | id, secret_hash, kind, vid, level, location, expires, created_by, redeemed_by, revoked |
| `shares` | id, vid, grantee (user id or peer key), level, location, expires, revoked |
| `peers` | id, display_name, cert_fingerprint, endpoints (JSON), first_seen |
| `remote_vehicles` | vid, peer_id, share_token (encrypted at rest), name, last_seen |
| `audit` | ts, actor, action, target, detail (no secrets, no VIN) |

## 9. API sketch

All JSON, all in `api/openapi.yaml`, all behind a session or token except where marked.

| Route | Notes |
|---|---|
| `POST /auth/setup` | setup code → owner (open only while no owner exists) |
| `POST /auth/login`, `POST /auth/logout` | password, optional TOTP |
| `POST /auth/passkey/options`, `POST /auth/passkey/verify` | WebAuthn login and registration ceremonies |
| `GET /me` | user, role, effective caps for the active vehicle |
| `GET/POST /users`, `PATCH/DELETE /users/<id>` | owner only |
| `GET/POST /tokens`, `DELETE /tokens/<id>` | own tokens; owner sees all |
| `POST /device/code`, `POST /device/token` | RFC 8628 (open; rate-limited) |
| `GET/POST /vehicles/<vid>/shares`, `DELETE …/shares/<id>` | owner |
| `POST /invites`, `GET /invites`, `DELETE /invites/<id>` | owner |
| `POST /invites/redeem` | open; the secret is the credential |
| `GET /garage` | local, other and shared vehicles; nearby devices |
| `GET /audit` | owner; filter by share, user, vehicle |
| `/peer/v1/…` | device-to-device, share token plus pinned TLS; Tier 0 reads only |

## 10. Phases

| Phase | Ships | Depends on |
|---|---|---|
| **P1 Local users** | bootstrap, passwords, sessions, kiosk session, roles in the gate, tokens, RFC 8628, audit; Basic Auth overlap | none; may precede U6 |
| **P1b Passkeys** | `[passkeys]` extra, device names | ADR-0021 trust spec |
| **P2 Garage with shares** | person invites, LAN vehicle shares, pinned peers, `/peer/v1`, switcher groups | U6 |
| **P3 Remote shares** | Tailscale, then the relay | ADR-0028 |
| **P4 Social** | groups, rides, live convoy, summaries, privacy zones, feed | P3 |
| **P5 Integrations** | share sheet and links (may move earlier), webhooks, bots | P4 for rides |

## 11. Tests

- Bootstrap: setup code single use, expires, refused once an owner exists.
- Every route without a session or token gets 401, except the open list above; public
  mode's allowlist stays as it is.
- **The confirmation matrix** (ADR-0033): role × category × tier × driving state (Parked,
  Idling, Moving, unknown speed) × transport (local; remote with the override off; remote
  with it on) against the gate. Each cell matches §3; Moving refuses Actuator tests,
  Procedures and Maintenance for the owner too; remote refuses everything above Read and
  arming with the override off; Tier 4 always refused; the kiosk session refused outside
  Read and Comfort.
- Phone approval: honoured from a paired phone on a local link, refused remotely without
  the override; an AI-client accept never honoured.
- Tokens: scope narrows; expired and revoked fail at once; never stored in clear.
- Passwords: scrypt parameters stored; timing-safe compare; rate limit. Passkeys (with
  the extra): fixed WebAuthn vectors; a wrong RP ID, origin or counter fails.
- Invites: single use, expiry, fingerprint mismatch refused, secret never logged.
- Shares: a scrub test over every `/peer/v1` route, with a fixture holding a VIN, HMAC,
  raw capture, audio and private note, finds none; location stripped unless granted;
  revocation stops the next pull.
- Audit entries for every grant, pull and revoke, with no secrets. Two fake devices on
  loopback: share, pull, revoke.

## 12. Threat notes (feed `references/threat_model.md`)

- **Spoofing:** stolen invite links (single use, short expiry, fragment-only secret);
  passkeys resist phishing by design, passwords do not (offer passkeys first).
- **Elevation:** a remote friend reaching above Read (transport rule); the remote override
  left on (install-only, badge in every UI, logged at start); a token minted above
  its user (minimum rule); a stale mechanic (forced expiry).
- **Information disclosure:** location through session traces (stripped unless granted);
  tracking through mDNS advertisements (off by default, no vid); VIN through anything
  (never stored in shareable tables).
- **Tampering:** a peer pretending to be a known device (pinned fingerprint).
  **Repudiation:** the audit log; Tier 1+ actions carry the user.
- **Denial of service:** pulls are rate-limited per share and read the normal poll's
  values; a remote pull never opens a new ECU session.
- **A lost or sold device:** `auth.db` holds no secrets usable elsewhere; factory reset
  wipes it with the garage.

## 13. Questions for the owner

Q1, Q2 and Q7 are answered; the rest stay open and block nothing in P1.

1. ~~Passkeys need `cryptography` as an optional extra?~~ **Answered:** yes, as
   `openostler[passkeys]`; passwords always available.
2. ~~Driver role: Tier 1 only, or Tier 2 too?~~ **Answered:** replaced by action
   categories (ADR-0033); drivers may clear codes, never run actuator tests.
3. Mechanic default length: 24 h? Should a mechanic see past sessions, or only live?
4. SQLite `auth.db`, or JSON files (`users.json`, `shares.json`)?
5. Should a nearby friend's car appear before any invite (with mDNS advertising on), or
   only after?
6. Social hosting: on a member's device, or only once Ostler Cloud exists?
7. ~~For bikers: base hardware on bikes, or the phone only?~~ **Answered:** a
   guardian-variant or Ostler Diagnostics node, with the phone as the screen.
8. Should Ostler Cloud ever hold a Meta app for automatic posts, or only share links and
   the owner's own bots?

## 14. Amendment (2026-10-07), approved: one permission model and the shell screens

**Status: approved by the owner on 2026-10-07 ("approve all").** Where this section differs
from §2–§10, this section wins. It is the one
permission model that **Social** and **Vehicles & Map** (add-ons under
[ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md), accepted)
consume: they read it through the shell API and store no permissions of their own. Evidence:
[accounts and sign-in in practice](../references/research/accounts_social_login.md),
[social and group-drive apps](../references/research/social_group_drive_apps.md) (D1–D9),
[calls, video and cameras](../references/research/calls_video_camera_sharing.md) §8 (camera
scope), [maintenance trackers](../references/research/maintenance_trackers.md) §4 (maintenance
class). ADR text it touches: [ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md#amendment-2026-10-07-approved)
§1, §2, §4, §7, §8, §9.

### 14.1 The data-class registry

One registry replaces the four overlapping vocabularies: the share levels (`view`,
`view+logs`, §5.3), the location levels (§5.3 plus ADR-0038's coarse), the token data classes
(§2.4) and the manifest's `permissions.data` ([app-model spec §4.2](2026-10-06-app-model-design.md)).
The old levels survive only as **presets** (named bundles of grants).

**Entry shape** (core declares its classes in code; an add-on in its manifest under
`contributes.data_classes`, so the registry is add-on-extensible):

| Field | Meaning |
|---|---|
| `id` | `presence`, `location` …; an add-on's own classes are `<app id>.<name>` unless first party |
| `owner` | `core` or the app id that registers it |
| `live` | true if it is present-tense (ghost hides it, §14.3) |
| `detail` | its precision ladder, lowest first (§14.5); `["on"]` if it has none |
| `max_window` | the longest a grant may last at each detail (`null` = may be indefinite) |
| `max_audience` | the widest audience it may ever reach; `me` makes it unshareable |
| `sensitive` | shown with a warning and never included by a preset |

The registry refuses an entry whose default audience is not `me`, a live class without a
window rule, or any class carrying an identity (the VIN and its HMAC are never a class,
ADR-0036; nor are raw captures or Decode evidence).

**Core and first-party classes:**

| Class | What it covers | Live | Detail ladder | Window / cap |
|---|---|---|---|---|
| `presence` | online, driving, parked, "in a ride" | yes | on | any |
| `vehicle_card` | make, model, year, nickname, photo (EXIF stripped); plate hidden unless ticked | no | basic · with plate | any |
| `location` | position and traces | yes | none · coarse · place · precise · live | precise and live **≤ 24 h, always**; others may be indefinite |
| `live` | live signals from the VSS stream | yes | on (a signal subset may be named) | any |
| `trips` | trip summaries, stats, records; full recordings and replay | no | summary · full | any; traces follow `location` |
| `faults` | fault codes, freeze frames, readiness | no | on | any |
| `notes` | notes the author marked shareable (private notes are never a class) | no | on | any |
| `maintenance` | service records, reminders, fuel; costs at the top level (Maintenance & Garage) | no | history · with costs | any; "for a buyer" preset has no locations |
| `video` | live view of one named camera, granted per camera (`video:<camera>`); a **camera grant** is this class at per-camera granularity (Cameras add-on) | yes | live only (no recording, no scrub-back) | default "this ride" or 1 h; interior never indefinite and needs occupant consent at the head unit; "being viewed by N" badge; every view audited |
| `audio` | cabin audio, voice notes, camera audio (off by default; a camera grant never implies it) | — | — | `max_audience: me` (ADR-0010); call audio is a Social call, consented per call, not a share |

**Presets** map the old words: `view` = vehicle_card + live + faults; `view+logs` = that + trips
(full); location levels = `location` at that detail; a token's `data` scope is a list of
class ids. `maintenance` is off by default and never in a preset (maintenance research §4.4).
Recorded clips are not shared through grants in P1–P4 (export only); a later clip grant
would be its own class.

### 14.2 Audiences and grants

- **Audiences:** **me** · a **person** (a contact, §14.6) · a **group** (a ride is a group
  audience whose grants end at ride end) · the **household**
  (the local users and people of this device) · **public** (reserved; not before club pages,
  after P4).
- A **grant** is (data owner, vehicle or `*`, class, detail, audience, start, expiry). Only the
  **data owner** makes a grant: the vehicle's owner for the vehicle's data; the signed-in
  driver for their own presence and live location in a trip. Every grant offers durations
  first: 1 h, until end of trip, until end of day, until I stop (where `max_window` allows).
- A user's **user role** on this device (§3, ADR-0029 §5) is not a share: it decides what they
  can read and do here. Grants decide what leaves anyone's control to anyone else, including
  household members beyond their role (a Viewer sees location only through a grant).
- Shares (§5) remain the **link** to a peer (pinned key, endpoints, transport); grants ride on
  them. The `shares.level` and `shares.location` columns go; a `grants` table takes them.

### 14.3 Ghost mode

- **Default on** for every new user, and for every class an add-on registers when it is
  installed. A grant made while ghosted exists but sends nothing that ghost hides.
- **One master toggle** per user. Going ghost is one tap, anywhere, always allowed, and ends
  every live share, live ride position, camera grant and mesh position at once. Becoming
  visible offers **1 h · 24 h · until I go ghost**, and first shows a one-screen summary of
  what each audience will see. **Timers only ever move toward ghost**: ghost never ends by
  itself.
- **What it hides:** every `live: true` class (presence, location, live signals, video, and
  any live add-on class). Non-live grants (trips, faults, notes, maintenance, video,
  vehicle card) stay as each grant says (social research D1).
- **What it does not cost:** ghost never blocks messaging or calls; you still see others,
  message and call (Snap, not Waze).
- It applies on every transport, the mesh included; the device that answers enforces it.

### 14.4 The visibility rule

```
visible(viewer, vid, class) =
      not ghosted(data_owner, class)                 # master toggle or the class's own ghost
  and viewer ∈ audience(g)    for some grant g on (vid, class), not revoked
  and g.start <= now < g.expires                     # precise/live: expires - start <= 24 h
  and transport_ok(viewer's path)                    # §3.2, plus the per-user local-only flag
  then deliver at min(max detail over passing grants, class cap, path cap)
```

- Path cap: a mesh carries `coarse` at most outside a ride's private channel (ADR-0038 §5;
  coarse = Meshtastic 13 bits).
- Enforced where the data lives (`/peer/v1`, the token API, the Social and Map feeds served by
  core), never only in the UI.

### 14.5 Precision, and who can raise it

- **Location ladder:** none · coarse (about ±3 km) · place (town or a named place) · precise ·
  live (precise, streamed). Privacy zones trim trip ends at saved places at every level.
- **Precise and live always expire within 24 h** (timer, arrival, trip or ride end). Renewing
  is a new act by the data owner; nothing auto-renews.
- **Nobody can raise another person's precision**: not the device owner, a group admin or a
  ride leader. A group admin manages members, never members' grants.
- **The one exception is my own SOS or crash alert**, from my own device, to my **safety
  contacts only** (§14.7): a precise position (and live position until I mark safe, at most
  24 h), even in ghost. It is audited and shown to me afterwards. No one else's action
  can trigger it, and ghost never leaks by itself (the Life360 "pop" is rejected). Theft
  alarms to the owner stay ADR-0033 §7 paths, not shares.

### 14.6 Contacts, groups and invites

- **Contacts** are first-class: a display name I choose, the peer link (pinned key), the groups
  they are in, what I grant them and what they grant me, and a block flag. A **person
  without a login** (a child, a car-share driver) is a household contact used for "who drove"
  only (`users.can_sign_in = false`).
- **Groups:** a name, a kind (friends, club, **safety**), a host (my device, a member's
  device or the relay, §13 Q6), admins and members. Removing a member stops their view at
  the next pull.
- **Rides** are first-class too: a group-like object with members, a leader, a time window
  and a route (§6). A **ride-scoped grant** (audience: the ride) carries live location or
  other live classes to ride members only and **ends at ride end** (or 24 h, whichever is
  first); leaving the ride ends it for that member.
- **Invites**, one record with three carriers:
  - **link** and **QR** as §5.2 (fragment secret, pinned fingerprint, 48 h default);
  - an **8-character code** from a no-ambiguity alphabet (Crockford base32), single use,
    **10 minutes**, five wrong tries per address then a lock; for links that cannot travel
    (read aloud, typed on a parked head unit, a mesh text). A code carries no fingerprint,
    so both screens then show the same short check (six digits from both keys) and the
    share activates only on a match.
- Accepting an invite creates the contact and shows the inviter's offered preset; nothing live
  flows until each side leaves ghost. Friends appear only after an invite (answers §13 Q5).
  No address-book upload, phone numbers or global directory.

### 14.7 Shell screens: gap list and short specs

All are core shell (ADR-0042). Today none exists except the Basic Auth prompt.

| # | Screen | Host | Phase |
|---|---|---|---|
| S1 | First run (owner creation) | any | P1 |
| S2 | Sign in | phone, desktop | P1 |
| S3 | Passkeys | phone, desktop | P1b |
| S4 | Profile switcher (head unit) | head unit | P1 |
| S5 | Users and roles | owner | P1 |
| S6 | Signed-in devices | own; owner sees all | P1 |
| S7 | Contacts, groups and invites | phone, desktop | P2 |
| S8 | Sharing ("who sees what") with View as… | phone, desktop | P1 (household), P2 |
| S9 | Ghost toggle | status strip, every host | P1 |
| S10 | Safety contacts | phone, desktop | P2 |

- **S1 First run.** Keep the physical setup code (§2.1). One screen, Home Assistant style:
  setup code, your name, then "Add a passkey" (when available) or a password; a line saying
  how to recover (console `reset-owner`). Then optional "Name this car" and "Invite someone".
  No email. On Ostler Diagnostics alone the phone app's pairing is the same screen.
- **S2 Sign in.** Password (plus TOTP if set), a passkey button only when this origin can
  hold one, and "Sign in with a code" (RFC 8628, Jellyfin Quick Connect UX) for TVs and second
  screens. A local-only user on a remote path gets "This account works only in the car".
- **S3 Passkeys.** Each passkey with the name it works on, created, last used; add; delete
  with a warning on the last credential of the last owner. Names, in order of reach: an
  optional **per-device public name from Ostler Cloud** (`*.<device-hash>.<domain>`, DNS-01,
  answered locally by the Brain's DNS offline); Tailscale names; and the no-cloud path, the
  device CA **name-constrained** to its own names, with a guided install per phone
  (ADR-0021's trust spec records the choice). The head unit uses `http://localhost` and needs
  none. Remote friends never need a passkey here: they use their own device.
- **S4 Profile switcher (head unit).** The head unit always starts in the **kiosk session**
  (Read and Comfort, bound to `localhost`, never an IP range); a profile chip in the status
  strip reads "Car". **Switching is Parked-only**: a tile sheet of users who opted in to
  appear, unlocked by a **6-digit local PIN** (set from a full sign-in, scrypt-hashed, valid
  on that head unit over `localhost` only, five tries then 15 minutes locked, never mints a
  token) or by **approval from a paired phone** on a local link. **Sign-out at ignition off**,
  back to kiosk. **Trips record who drove**: the user, a person without a login picked from
  the tiles (no rights), or "Car". Tier 2–3 still need phone approval (ADR-0033 §6).
- **S5 Users and roles.** People and users in one list; per user: user role, categories added
  or removed, expiry (Mechanic always), **"local links only"** (checked in `transport_ok`),
  can sign in, show on the head unit, head-unit PIN reset, disable, delete (trips keep
  "former user"). Reset sends a one-time person invite; the last owner cannot be removed.
- **S6 Signed-in devices.** Every session and token: device label, last used, last path
  (head unit, LAN, Tailscale, relay); revoke one, or "sign out everywhere else". Trusted
  sessions slide 30 days and are **pruned after 90 days unused**.
- **S7 Contacts, groups and invites.** Contacts (online state, what I share, what they share),
  groups, pending invites sent and received with countdowns and revoke; "Add" shows QR, link
  and code; "Enter code" or scan.
- **S8 Sharing.** A matrix of audiences × classes for each vehicle and for me, each cell its
  detail and countdown; add a grant as who → what → how precise → how long; presets; the
  audit of pulls. **View as…** picks a contact, group or household member and renders the
  car through the same server filter `/peer/v1` uses, not a UI imitation.
- **S9 Ghost toggle.** The **visibility chip** in the status strip on every host ("Ghost", or "Visible to
  Ride: Peak District · 1 h 20 m"), also in Settings → Sharing and in the Social and Vehicles &
  Map headers (they read it through the shell API). On a driver-facing head unit while
  Moving, going ghost is one tap; becoming visible waits for Parked or the phone.
- **S10 Safety contacts.** Choose contacts (later, a non-Ostler viewer through a relay link,
  social research D4); what each receives (SOS, crash alert, opt-in ride start and end); the
  channel (paired-app push, the owner's notify endpoint, the guardian's SMS, ADR-0033 §7); a
  test button.

### 14.8 Social login

Out of P1–P4. Later (P5 at the earliest), an optional **Ostler Cloud OIDC broker**
(authorisation code with PKCE, a pairwise subject per device) that **links** a Google, Apple
or Facebook identity to an existing local user, as a convenience on a new phone; the local
passkey or password always works offline; never the only credential, never friend discovery.
Beside it, a **generic OIDC client** (issuer, client id, secret) for self-hosters (Pocket ID,
Authentik, Tailscale's tsidp). Never Facebook first; Apple only with an iOS companion.

### 14.9 Basic Auth migration (replaces the overlap line in §2.1)

1. **Release N (P1):** with `--admin-password` / `D2DIAG_ADMIN_PW` set and no `auth.db`,
   create user `owner` with that password (scrypt) and **skip the setup code**; banner "Add a
   passkey or rename your account".
2. Basic Auth is accepted in release N **on the old routes only**, mapped to the owner; new
   routes take sessions and tokens only. Each Basic request is logged with its client.
3. Settings → Scripts mints a token per script to replace the password.
4. **Release N+1:** Basic Auth refused, with a 401 body naming the token page. **No switch
   re-enables it.** Public mode's "server password" becomes an owner or mechanic sign-in.

### 14.10 Where `auth.db` lives, and recovery

- **With a Brain:** `auth.db` (users, credentials, sessions, tokens, contacts, groups, grants,
  audit) lives on the Brain, with the CA and pairing authority (ADR-0037 §2). It pushes a
  **signed roster** (user ids, user-role categories, pairing-key public keys, revocations,
  an epoch; ADR-0041 signing) to the node and guardian on change and at wake.
- **With the Brain asleep:** nothing verifies passwords. The node and guardian accept only
  pairing-key sign-in and signed grants against the latest roster
  ([grant flow](../references/research/grant_flow.md)); alarm paths need neither (ADR-0033
  §7). An owner may revoke a phone directly at the node over a local link, signed by their
  own pairing key; the Brain reconciles at wake. Losing the Brain blocks new users and
  pairings only.
- **Ostler Diagnostics alone:** no `auth.db`; the node holds the roster (paired phones as
  users). **Recovery:** the physical step on the node (button or label code, held with the
  ignition on) re-pairs a phone as owner, **revokes every old pairing key** and keeps all
  recorded data; previously paired phones are told when they next connect. A Brain added
  later imports the roster at pairing.
- **Ostler Cloud never holds `auth.db`**: at most the optional public name (S3) and, later,
  the OIDC link (§14.8).

### 14.11 "Role" means two things

ADR-0037's **role holders** (transmit gate, parked broker, time source…) are device duties;
§3's roles are user permissions. New text and code say **user role** (`user_role`) for the
latter and **device role** or role holder for the former. Both obey ADR-0037's rule:
holding a role grants no authority; the executing gate checks every grant.

### 14.12 Data model, API and tests (deltas)

- **Tables:** `users` + `can_sign_in`, `local_only`, `show_on_head_unit`, `hu_pin` (scrypt);
  `sessions` + `label`, `last_path`, `last_used`; new `contacts`, `groups`, `group_members`,
  `grants` (owner, vid, class, detail, audience kind and id, start, expires, revoked),
  `ghost` (user, on, until, per-class), `roster` (epoch, signature); `invites` + `code_hash`,
  `preset`, `max_uses`; `shares` loses `level` and `location`; trips carry `driver`.
- **Routes:** `GET /data-classes`; `GET/POST /grants`, `DELETE /grants/<id>`; `GET/PUT
  /me/ghost`; `GET/POST /contacts`, `/groups`; `POST /invites/code/redeem` (open,
  rate-limited); `GET /me/sessions`, `DELETE /me/sessions/<id>`; `GET /view-as/<audience>`;
  `GET/PUT /me/safety-contacts`; `POST /auth/hu/switch` (localhost only).
- **Tests:** ghost on for a new user and a new add-on's classes; a precise or live grant
  without an expiry, or over 24 h, refused; a grant by anyone but the data owner refused;
  SOS reaches only safety contacts and is audited; View as… equals `/peer/v1` for that viewer;
  a manifest class with a default audience other than `me` refused; code single use, 10
  minutes, lockout; head-unit PIN refused off `localhost` and switching refused unless
  Parked; sign-out at ignition off; Basic refused on new routes in N and everywhere in N+1;
  a local-only user refused on every remote path.

### 14.13 Accounts research gap list G1–G13, where each is addressed

| # | Gap | Addressed in |
|---|---|---|
| G1 | Four vocabularies for "what data" | §14.1 registry; presets |
| G2 | No friend or group object | §14.6 contacts and groups; S7 |
| G3 | No ghost mode or duration presets | §14.3, §14.2 durations; S9 |
| G4 | Owner recovery on Ostler Diagnostics alone | §14.10 |
| G5 | Passkey naming for family phones | S3 (public name, name-constrained CA); ADR-0021 trust spec |
| G6 | Head-unit switching, PIN, sign-out | S4 |
| G7 | Person without a login; who drove | §14.6, S4, S5; `trips.driver` |
| G8 | Per-user local links only | S5; §14.4 `transport_ok` |
| G9 | Social login path | §14.8 |
| G10 | Short invite code | §14.6 |
| G11 | `auth.db` across node, Brain, guardian | §14.10 |
| G12 | Basic Auth end date | §14.9 |
| G13 | Session pruning | S6 (90 days) |

### 14.14 Phases (deltas)

P1 gains the registry, grants to me and household, ghost, S1, S2, S4–S6, S8 (household),
S9 and the migration. P1b passkeys with S3. P2 gains contacts, groups, codes, S7, S8 and S10.
Public audiences and non-Ostler viewers wait for P4 or later. Social login is P5 at the
earliest.

### 14.15 Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen. Ghost mode never blocks messaging or calls.

1. **One data-class registry replacing levels, location levels, token classes and
   `permissions.data`?** Recommend yes, add-on-extensible, levels kept as presets.
   Alternative: keep levels and bolt new classes (video per camera, maintenance) onto them.
2. **What ghost hides?** Recommend live classes only (presence, location, live signals,
   video), non-live grants untouched. Alternative: ghost hides every class.
3. **Ghost timers?** Recommend timers only toward ghost (visible for 1 h, 24 h or until off;
   ghost never expires). Alternative: Snap-style "ghost for 3 h" that turns visible again.
4. **Precise and live location capped at 24 h, no auto-renew?** Recommend yes.
   Alternative: allow "until I stop" for household only.
5. **Can anyone raise my precision?** Recommend no one; only my own SOS or crash alert to my
   safety contacts, audited. Alternative: a household owner may raise it for under-18 drivers.
6. **Does a driver's ghost hide the car from the vehicle's owner?** Recommend no: the owner's
   user role still reads their own car, and the driver is told so. Alternative: ghost hides
   from the owner too.
7. **8-character, 10-minute invite code with a six-digit key check?** Recommend yes.
   Alternative: links and QR only.
8. **Head-unit profiles: Parked-only switching, 6-digit local PIN or phone approval,
   sign-out at ignition off?** Recommend yes. Alternative: a "remember on this car" option of
   up to 7 days.
9. **Optional per-device public name from Ostler Cloud for passkeys?** Recommend yes as an
   option, with the name-constrained CA as the no-cloud path. Alternative: CA only.
10. **Social login?** Recommend out of P1–P4; later only a link-only Ostler Cloud OIDC broker
    plus a generic OIDC client. Alternative: never.
11. **Basic Auth end?** Recommend release N on old routes only, refused in N+1, no re-enable.
    Alternative: two releases of overlap.
12. **`auth.db` on the Brain with a signed roster on the node and guardian?** Recommend yes.
    Alternative: a replicated `auth.db` on the node too (more flash writes, two sources of
    truth).
13. **Say "user role" and "device role" from now on?** Recommend yes. Alternative: rename
    ADR-0037's term to "duty".

## 15. Proposed amendment (2026-10-07, DMD round): trip sharing in the registry

**Status: proposed, awaiting the owner's answers (v0.7).** Nothing in §1–§14 changes until
then; once approved, where §15 differs from §14 it wins. Detail and tests are in the draft
[per-trip sharing spec](2026-10-07-trip-sharing-design.md) and
[ADR-0043](../decisions/adr-0043-gps-and-logs-in-shared-trips.md) (proposed). Evidence:
[trip and log sharing](../references/research/trip_and_log_sharing.md) §5–§7 and
[DMD Hub features](../references/research/dmd_hub_features.md) §2.2, §2.6 and §5. It answers the
owner's ask that a single trip can be shared at a chosen level (L0 Card, L1 Route, L2
Telemetry as grants; L3 Full log and L4 Diagnostics bundle as hand-overs).

### 15.1 A `route` detail on the `location` ladder (changes §14.1 and §14.5)

- The ladder becomes **none · coarse · place · route · precise · live**.
- **`route`** is a **finished** trip's trace after the ends trim (500 m default, never below
  200 m), privacy zones (≥ 500 m, fixed random offset), simplification (about 10 m) and the
  removal of point timestamps, with stats from the visible trace only (sharing spec §5). It is
  never live and never a position "now".
- `max_window` for `route` is **null** (may be indefinite): the 24 h cap stays for `precise`
  and `live` only, which are present-tense or unprocessed.
- `route` reaches `public` only by an **explicit publish act** at least **24 h after the trip
  ended** (ADR-0043 §3); a preset never includes it.
- `trips` traces follow `location` as before; a `trips` grant at `summary` with `location`
  `route` is the L1 level.

### 15.2 Audiences: `link` added, `public` brought forward (changes §14.2)

- **`link`** — anyone holding an unguessable URL (key in the fragment, as invites §5.2). Allowed
  only for `trips` at L0–L1 (`summary`, `location` at most `route`), `faults` and
  `vehicle_card` (plate only if ticked). **Refused** for `live` location beyond a ride's
  window, `presence`, `live`, `trips` `full` (so L2 never goes to `link`), `notes`,
  `maintenance`, `audio`, `video` and any raw log. Every `link` grant has an expiry.
- **`public`** — brought forward from "after P4" for **Ostler Community** (`ostler-app-hub`), by
  **explicit publish only**: never a default, never through a preset, never by an add-on on
  its own. Allowed for `trips` L0–L1 and `vehicle_card`; L2 Telemetry goes to a person, a group
  (a hub club is a group) or the household only, never `link` or `public`.
- The registry gains a per-class `max_audience` check for both, and the visibility rule (§14.4)
  treats `link` as "holds a valid token for this grant".

### 15.3 Live-trip grant options (changes §14.2; used by Vehicles & Map)

A `location` `live` grant (≤ 24 h, ending at trip or ride end) may carry: **`trail_window`**
(none, 1, 3, 6, 12, 24 h, whole trip), **`delay`** (0–6 h; it also delays moments and
values), **`show_speed`** and **`show_values`** (both off by default). Ghost still ends it at
once. These are grant fields, not add-on settings, so `/peer/v1` enforces them.

### 15.4 Link controls (changes §14.2 and §14.12)

Every grant to a `person`, `group` or `link`, and every relay or hub link, carries DMD-style
controls: **mode** `locked` (viewed in Ostler or a viewer, follows edits, revocable, withdrawn
from recipients' Ostler devices at `access_until`) or `download` (a copy that survives revoke);
**`available_from`**; **`expires`** (last time a new recipient may open it); **`access_until`**;
**`max_collections`** (distinct recipients); **`max_downloads`** per recipient; and a derived
**state** Pending · Active · Full · Expired · Revoked. The sheet says that `locked` deters
casual copying and is not a guarantee. `grants` gains `mode`, `available_from`,
`access_until`, `max_collections`, `max_downloads` and the live options of §15.3; a new
`grant_access` table records each open and download for the audit (S8).

### 15.5 L3 and L4 stay outside the registry (confirms §14.1)

Raw logs and diagnostics bundles are **hand-overs, never grants** (ADR-0043 §2): an
`ostler.share/1` bundle that passes `ostler share verify`, sent by file, relay link with the key
in the fragment, or an end-to-end encrypted hub help thread to named helpers (7 days default,
30 at most, at most 3 downloads). The registry refuses any class that carries raw captures, as
§14.1 says. The audit in S8 lists hand-overs beside grants.

### 15.6 Tests (deltas)

A `route` grant on a trip still recording refused; a `public` route before trip end + 24 h or
without the publish act refused; a `link` grant for `trips` `full`, `live`, `audio`, `video`
or `presence` refused; a `link` grant without expiry refused; `delay` above 6 h refused;
`show_speed` off removes speed from every `/peer/v1` response for that grant; a `locked` grant
past `access_until` returns nothing; `max_collections` reached gives Full.

### 15.7 Decisions for the owner (DMD round)

1. **Add a `route` detail between `place` and `precise`, possibly indefinite?** Recommend: yes;
   without it a shared trip map expires after a day. Alternative: a separate `trace_published`
   detail used only for `public` (DMD research Decide 4).
2. **Add a `link` audience, limited to L0–L1 trips, `faults` and `vehicle_card`?** Recommend:
   yes. Alternative: no `link`; recipients must be contacts.
3. **Bring `public` forward for Ostler Community by explicit publish only, L0–L1 and
   `vehicle_card` only?** Recommend: yes. Alternative: keep `public` after P4 as §14.2 says.
4. **Live-trip options `trail_window`, `delay` (0–6 h), `show_speed`, `show_values` as grant
   fields?** Recommend: yes, enforced by `/peer/v1`. Alternative: Vehicles & Map settings only
   (enforced in the add-on's UI).
5. **DMD-style link controls as core grant fields?** Recommend: yes. Alternative: expiry and
   revoke only.
6. **L3 and L4 as hand-overs, keeping raw captures out of the registry?** Recommend: yes.
   Alternative: a `sensitive` `captures` class (one person or the decode project only, ≤ 30
   days, never `link` or `public`).

## Changelog

- 2026-10-06 — v0.1: first draft from the owner's direction (ADR-0029, proposed).
- 2026-10-06 — v0.2: approved by the owner. Q1 (passkeys extra), Q2 (driver role, now
  categories) and Q7 (bikes) answered; roles grant ADR-0033 categories; the one rule gains
  the category; the kiosk session is Read and Comfort; transport is local-only with the
  install override; phone approval of Tier 2–3 over local links; Lite bootstraps by phone
  pairing; the default vehicle is the one the node is on; the confirmation matrix.
- 2026-10-06 — v0.3: wording only: "Ostler Lite" reads Ostler Diagnostics (ADR-0039).
- 2026-10-06 — v0.4, product name per the ADR-0039 amendment: "Ostler Hub" is now **Ostler Brain**; "hub" (our compute box) reads "Brain".
- 2026-10-07 — v0.5 (proposed, awaiting the owner): §14 added: the data-class registry, audiences, ghost mode, the visibility rule, precision limits, contacts, groups and invite codes, the shell screens S1–S10, social login, the Basic Auth end, `auth.db` placement and recovery, "user role", and the research gaps G1–G13 mapped. Sections 1–13 unchanged.
- 2026-10-07 — v0.6: §14 approved by the owner on 2026-10-07 ("approve all"): renamed
  "Amendment (2026-10-07), approved"; where it differs from §2–§10 it wins; every §14.15
  decision answered as recommended (alternatives not chosen); ADR-0042 cited as accepted.
- 2026-10-07 — v0.7 (proposed amendment, DMD round, awaiting the owner): §15 adds the `route`
  detail on the `location` ladder, the `link` audience, `public` brought forward for Ostler
  Community by explicit publish only, live-trip grant options and link controls, and confirms
  L3–L4 as hand-overs. §1–§14 unchanged.
