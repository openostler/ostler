---
title: "Accounts, multi-vehicle garage, sharing and social — design"
area: specs
status: stable
version: 0.2
updated: 2026-10-06
depends_on: [decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-u0-seams-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, CONSTITUTION.md, GOALS.md]
summary: >
  Approved by the owner on 2026-10-06 (ADR-0029, with roles and approvals from ADR-0033). Local users on each device with an owner bootstrapped by a physical setup code (phone pairing on Ostler Lite); passkeys through the optional extra openostler[passkeys], scrypt passwords always available, cookie sessions and scoped, revocable tokens (also for AI/MCP clients, RFC 8628 device flow). Roles (Owner, Driver, Viewer, Mechanic) grant action categories, each capped by its tier; the gate takes the intersection of role, share and token categories at the minimum tier, then the transport rule (local links; remote read-only unless the install-level OSTLER_ALLOW_REMOTE_CONTROL override is set) and the driving state. The head-unit kiosk session gets Read and Comfort only. A garage that defaults to the car the node is on, with friends' cars added by invite (link or QR, pinned device key, expiry, revocation, audit) over LAN, Tailscale or the future relay; data stays on each car's device. Per-share privacy: location opt-in; no VIN, HMAC, raw capture or audio ever. Later: groups, rides and convoys for bikers and off-roaders, and outbound share intents, webhooks and bots. Bikes use a guardian-variant or Lite node with the phone as the screen. Phases P1–P5, data model, routes, tests, threats and the remaining open questions.
---

# Accounts, multi-vehicle garage, sharing and social — design

**Status:** approved by the owner on 2026-10-06 (v0.2). The decisions are
[ADR-0029](../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md) and, for
categories, phone approval and the remote rule,
[ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md). Each phase may split
into its own spec; the questions the owner did not take up (§13) block nothing in P1.

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
- **Ostler Lite** (a node with no brain, [ADR-0032](../decisions/adr-0032-one-node-optional-brain.md))
  has no display or console. The owner is bootstrapped by **pairing a phone** with the node
  (a physical step on the node, such as a button press or a code on its label); the pairing
  keys on the phone sign the owner in. There is no Pi CA on Lite; trust comes from pairing.
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
  Tailscale or the relay, MQTT, Home Assistant) are **read-only**, plus arming (never
  disarming) the software alarm, unless the install-level `OSTLER_ALLOW_REMOTE_CONTROL`
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
- **Bikes** carry a guardian-variant or Lite node (ADR-0032), with the phone as the screen.
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
   guardian-variant or Lite node, with the phone as the screen.
8. Should Ostler Cloud ever hold a Meta app for automatic posts, or only share links and
   the owner's own bots?

## Changelog

- 2026-10-06 — v0.1: first draft from the owner's direction (ADR-0029, proposed).
- 2026-10-06 — v0.2: approved by the owner. Q1 (passkeys extra), Q2 (driver role, now
  categories) and Q7 (bikes) answered; roles grant ADR-0033 categories; the one rule gains
  the category; the kiosk session is Read and Comfort; transport is local-only with the
  install override; phone approval of Tier 2–3 over local links; Lite bootstraps by phone
  pairing; the default vehicle is the one the node is on; the confirmation matrix.
