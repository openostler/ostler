---
title: "ADR-0029 — Accounts, multi-vehicle garage, sharing and social"
area: decisions
status: locked
version: 1.8
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, CONSTITUTION.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md]
summary: >
  Accepted by the owner on 2026-10-06. Each Ostler device gets local users (an owner bootstrapped on first run with a physical setup code, or by phone pairing on Ostler Lite), passkeys through the optional extra openostler[passkeys] with passwords always available, cookie sessions and scoped, revocable API tokens (also for AI/MCP clients). Four roles (Owner, Driver, Viewer, Mechanic, time-boxed) grant action categories, each capped by its tier (ADR-0033); the gate takes the intersection of role, share and token categories and the minimum tier, then transport and driving state, and no role passes a tier gate or a confirmation. The garage defaults to the vehicle the node is on; other cars appear only through shares, and their data stays on their own device, pulled on demand. Invites by link or QR carry a permission level, an expiry and a pinned device key; remote paths are read-only unless the install-level override of ADR-0033 is set. Motorbikes use a guardian-variant or Lite node with the phone as the screen. Shares never carry a VIN, a raw capture or location unless opted in. Social (groups, rides, convoys) and outbound sharing via share intents, webhooks and bots come last, opt-in, with no ads or tracking. Amended 2026-10-06 by ADR-0039: read "Ostler Lite" as "Ostler Diagnostics". Amended 2026-10-07, approved by the owner on 2026-10-07 ("approve all"): §8's levels give way to one data-class registry with ghost mode on by default and precise location capped at 24 h; §7 gains contacts, groups and an 8-character invite code; §9 allows a later link-only social login through an Ostler Cloud OIDC broker; Basic Auth ends one release after P1 with no re-enable; `auth.db` lives on the Brain with a signed roster on the node; "user role" and "device role". Amended 2026-10-07 (DMD round), approved by the owner on 2026-10-07 ("approve all", DMD round): Ostler Community, the opt-in community hub (a closed service run by Ostler, one instance, not self-hostable, reached through the open `ostler-app-hub`; also the project forum and wiki), holds the directory (Discover) and an opt-in Following feed in place of §9's minimal in-house feed, brings the `public` audience forward for explicit publishing, adds hub accounts linked to devices, and drops federation.
---

# ADR-0029 — Accounts, multi-vehicle garage, sharing and social

> **Amended by [ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md), 2026-10-06:** §8 gains a **coarse** location level (the mesh default), and §9 names the mesh as a social transport. See [Amendments (mesh)](#amendments-2026-10-06-mesh).
> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** read "Ostler Lite" or "Lite" as "Ostler Diagnostics" (the family is Ostler Diagnostics, Ostler Guardian and Ostler Hub). See [Amendments (product family)](#amendments-2026-10-06-product-family).
> **Amended 2026-10-06 (Brain rename, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)):** read "Ostler Hub" and "Hub" (the product, also "hub" for the box) as "Ostler Brain" and "Brain". See [Amendments (Brain rename)](#amendments-2026-10-06-brain-rename).
> **Amended 2026-10-07, approved by the owner on 2026-10-07 ("approve all"):** one permission model (§4, §8), contacts and invite codes (§7), a later link-only social login (§9), the Basic Auth end and `auth.db` placement (§1, Consequences). See [Amendment (2026-10-07), approved](#amendment-2026-10-07-approved).
> **Amended 2026-10-07 (DMD round), approved by the owner on 2026-10-07 ("approve all", DMD round):** §9's feed and directory move to the opt-in community hub, Ostler Community (closed, Ostler-run, not self-hostable; also the forum and wiki); `public` comes forward for explicit publishing; hub accounts link to devices; no federation. See [Amendment (2026-10-07, DMD round), approved](#amendment-2026-10-07-dmd-round-approved).

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06). It approves
  [the accounts and sharing spec](../specs/2026-10-06-accounts-sharing-design.md) v0.2,
  which holds the detail. Amended in place on acceptance with the owner's answers and
  [ADR-0033](adr-0033-action-categories-and-approvals.md) (see
  [Amendments](#amendments-2026-10-06-owner-answers)).

## Context

- **Today Ostler is single-user and single-tenant.** Every logbook session carries a
  `vid` (U0, `logbook/vehicle.py`), and the garage and switcher are designed (UI spec
  §4.1, phase U6) but not built. There are **no users, roles, sharing or invites**: auth
  is one admin password over HTTP Basic (`_admin_ok` in `web/server.py`), required when
  public mode is on. Anyone who can reach a non-public server reads everything.
- **The owner asked** whether this is multi-tenant, and set the direction:
  - select the vehicle at the start, defaulting to the car you are in;
  - other cars, friends' included, appear in the list so their data can be pulled;
  - share and invite people with permission levels;
  - later, a social layer ("great for bikers") and a full platform with integrations
    (Facebook, WhatsApp and others) plus basic in-house features, "sort of how Spotify
    did it";
  - security is standard practice: passkeys and passwords for people, no custom schemes.
- **Passkeys need a domain.** WebAuthn runs only in a secure context, and its RP ID must
  be a domain the origin belongs to; an IP address is not allowed
  ([web.dev, RP ID](https://web.dev/articles/webauthn-rp-id)). A Pi reached by IP, by
  mDNS name, over Tailscale or through a relay is several origins, so a passkey made on
  one does not work on another. Local HTTPS is ADR-0021.
- **Verifying a passkey needs public-key signatures** (ES256, EdDSA), which the Python
  standard library lacks (ADR-0002 keeps runtime dependencies to pyserial).

## Decision drivers

- Local-first: accounts live on the device and work with no internet and no cloud.
- Standard practice only: WebAuthn, scrypt, OAuth-style tokens, RFC 8628, TLS.
- Safety travels with the action: one gate (on the node for car-touching actions); roles only narrow it.
- Privacy: VIN, raw captures and location never leave the device by default.
- No new runtime dependency without saying so (GOALS §2.6).

## Decision

1. **Local users per device.** Ostler is multi-user, not multi-tenant: one device serves
   one owner's household and the vehicles it is connected to. The **owner** is created on
   first run with a one-time setup code shown on the device's own display or console (a
   physical step, no default password). **Ostler Lite** (a node with no brain,
   [ADR-0032](adr-0032-one-node-optional-brain.md)) has no display or console: the owner is
   bootstrapped by **pairing a phone** with the node, a physical step on the node itself, and
   the pairing keys on the phone sign the owner in. An existing `--admin-password` seeds the
   owner's password on upgrade.
2. **Authentication.** Passkeys (WebAuthn) are the primary method and **passwords are
   always available** as the fallback, hashed with `hashlib.scrypt`. Sessions are
   `__Host-` cookies (Secure, HttpOnly, SameSite=Strict) plus an Origin check. Passkeys
   are registered per origin; the UI says which names it works on.
3. **Passkey verification** ships as the optional extra `openostler[passkeys]`, using the
   distribution's packaged `cryptography` (an OS package on the Pi). Without it, passwords
   work and the UI hides passkeys. This is the ADR the dependency rule asks for.
4. **Tokens.** Scoped, revocable, expiring API tokens, stored as hashes only. Scopes name
   vehicles, a maximum tier and data classes. AI and MCP clients use them (ADR-0030, in
   progress); headless clients pair with the OAuth device flow (RFC 8628). Tokens default
   to the Read category (Tier 0).
5. **Roles grant categories; tiers cap them.** Roles grant the action categories of
   [ADR-0033](adr-0033-action-categories-and-approvals.md), each capped by its tier:
   Owner (all categories, up to Tier 3), Driver (Read, Comfort, Security, Maintenance, plus
   Accessories if granted), Viewer (Read; location only if shared), Mechanic (Read,
   Maintenance, Actuator tests, Procedures; always time-boxed). The effective permission is
   the **intersection** of the role's, share's and token's categories at the **minimum**
   tier, then the transport rule (ADR-0033 §6: local links; remote paths read-only unless
   the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override is set) and the driving-state
   rule. The head-unit kiosk session gets Read and Comfort only. Tier 4 stays unrunnable.
   No role skips a confirm, a precondition or a lockout; the gate enforces all of it, on the
   node for car-touching actions (ADR-0032).
6. **Garage.** The default vehicle is the one the node is on, identified per UI spec §4.4. Other vehicles appear only through **shares**. A
   nearby Ostler device found by mDNS is shown as "nearby", with no data, until an invite
   is accepted. Shared data stays on its own device and is pulled on demand, never mirrored.
7. **Sharing.** Invites by link or QR carry a role, an expiry, a single-use secret (in the
   URL fragment) and the host device's certificate fingerprint, so device-to-device TLS is
   pinned without a public CA. Every share can be revoked; every grant, use and revocation
   is in an audit log. Transport is the LAN, Tailscale, or the Ostler Cloud relay
   (ADR-0028); shares over Tailscale or the relay are remote paths under ADR-0033 §6.
8. **Per-share privacy.** Location is off unless granted per share (none, place names,
   precise, or live during a ride). **No share ever carries a VIN or its HMAC** (a masked
   VIN at most, ADR-0018 Q7), a raw capture, or audio.
9. **Social and integrations, later and opt-in.** Groups, clubs, rides and convoys, a
   minimal in-house feed, and outbound "share to" and "notify via" (share sheet, WhatsApp
   and Telegram links, Facebook's share dialog, Discord webhooks, the owner's own Telegram
   bot). Nothing is posted automatically without a per-destination opt-in. No ads, no
   tracking, no third-party login.
10. **Motorbikes.** Bikes are served by a guardian-variant or Lite node, with the phone as
    the screen (ADR-0032).
11. **Phases.** P1 local users, roles and tokens (may precede U6); P2 garage with LAN
    shares (with U6); P3 remote shares over Tailscale or the relay; P4 groups and rides;
    P5 integrations. Each needs its own approved spec or spec section first.

## Confirmation

- Server tests: every route requires a session or token, except bootstrap, login and the
  public-mode allowlist; each role and each share level is refused above its ceiling;
  the ADR-0033 matrix (role × category × tier × driving state × transport, override off and
  on) holds; the kiosk session is refused outside Read and Comfort; an expired or revoked
  token or share fails at once.
- A test that no VIN, HMAC fingerprint, raw capture or audio appears in any share
  response, invite payload or audit entry.
- A test that no credential, token or invite secret is stored or logged in clear.
- The threat model (`references/threat_model.md`, needed by U5) gains the accounts and
  sharing data flows before P2.

## Consequences

- HTTP Basic admin goes, after one release of overlap. Service mode (ADR-0018 Q8) asks
  for an owner or mechanic credential instead of "the server password".
- `/vehicles/<vid>/…` (U6) gains a share-aware resolver; P1 can ship before U6 on the
  existing routes.
- A new state file, `auth.db` (stdlib `sqlite3`, as the logbook index already uses).
- Passkeys depend on stable device names; the ADR-0021 trust spec must name them.
- On Ostler Lite there is no Pi CA; trust comes from pairing (ADR-0032), so passkeys need a
  device name the phone app can reach; until then Lite uses pairing keys and passwords.

## Alternatives considered

- **Cloud-only accounts.** Rejected: breaks local-first and offline use, and makes the
  cloud a dependency (GOALS §2.1).
- **Login with Facebook or Google (OAuth only).** Rejected: needs internet and a third
  party to open your own car, and leaks a social identity. May come later as an optional
  link on Ostler Cloud only.
- **A custom pairing or crypto scheme for people.** Rejected (owner): standard methods only.
- **Mirroring friends' data onto my device.** Rejected: copies location and logs out of
  the owner's control; on-demand pulls keep revocation real.
- **ActivityPub federation now.** Deferred: public-by-default, no reliable deletion, heavy.
  Kept as a candidate for public club pages only.

## Amendments (2026-10-06, owner answers)

Recorded on acceptance; the statements above already read this way.

- **Passkeys:** accepted as the optional extra `openostler[passkeys]` (`cryptography`);
  passwords are always available.
- **Driver tier:** replaced by action categories
  ([ADR-0033](adr-0033-action-categories-and-approvals.md)); roles grant categories, each
  capped by its tier (§5). Drivers may clear codes (Maintenance), never actuator tests.
- **Phone approval:** a paired phone may approve Tier 2–3 over local links only, per
  ADR-0033 §6, with the install-level `OSTLER_ALLOW_REMOTE_CONTROL` override for remote use.
- **Transport rule:** "any remote path is Tier 0" is replaced by ADR-0033 §6.
- **Lite bootstrap:** Ostler Lite has no display or console, so the owner is created by
  phone pairing (§1).
- **Gate wording:** the gate for car-touching actions is on the node (ADR-0032).
- **Garage:** "the base hardware physically connected" now reads "the node" (§6).
- **Motorbikes:** a guardian-variant or Lite node with the phone as the screen (§10).

## Amendments (2026-10-06, mesh)

With [ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md) (accepted with the owner's answers
of 2026-10-06). The decision text above is unchanged; where these entries differ, they win.

- **A coarse location level** (§8). The per-share location levels become: none, **coarse**
  (about ±3 km), place names, precise, or live during a ride. Coarse is the default when
  position sharing over a mesh is first enabled (ADR-0038 §5); a live ride may raise it.
- **The mesh is a social transport** (§7, §9). Groups, rides and convoys may use the
  car-to-car mesh of ADR-0038 (the Meshtastic-compatible LoRa add-on first) beside the LAN,
  Tailscale and the Ostler Cloud relay. A mesh is a remote path (ADR-0033 §6): Read and
  alerts only, positions off until opted in per channel, never a VIN, `<vid>`, plate or
  account name on air, and mesh identities never stand in for Ostler accounts, tokens or
  device keys (ADR-0038 §6).

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The decision text and the
Amendments above are unchanged.

- **Names.** Read "Ostler Lite" and "Lite" above as "Ostler Diagnostics" (the OBD-port node, standalone with a phone), and "Ostler" where it names the tier with a brain as "Ostler Diagnostics + Ostler Hub". "Node" and "brain" stay the internal terms.

## Amendments (2026-10-06, Brain rename)

- **Names.** Read "Ostler Hub" and "Hub" above (and "hub" where it means our compute box) as
  "Ostler Brain" and "Brain" ([ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)). The decision text and the Amendments above are
  unchanged.

## Amendment (2026-10-07), approved

**Approved by the owner on 2026-10-07 ("approve all").** Where these entries differ from the
decision text above, they win. The detail is
[accounts spec §14](../specs/2026-10-06-accounts-sharing-design.md#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens),
from the [accounts](../references/research/accounts_social_login.md) and
[social](../references/research/social_group_drive_apps.md) research. Only the decision text
that changes is listed.

- **§1 Local users.** The env admin password seeds the owner and skips the setup code. On
  Ostler Diagnostics alone, recovery is the node's physical step with the ignition on: it
  re-pairs a phone as owner, revokes every old pairing key and keeps the data. A person
  without a login may exist for "who drove" only.
- **§2 Authentication.** On the head unit, a 6-digit local PIN or a paired phone's approval
  switches users, Parked only, over `localhost` only; sign-out at ignition off. Unused
  trusted sessions are pruned after 90 days.
- **§4 and §8 One permission model.** The share levels, location levels, token data classes
  and the manifest's `permissions.data` become one add-on-extensible **data-class registry**
  (presence, vehicle card, location, live signals, trips, faults, notes, maintenance (off by
  default), video (camera grants, per camera, live only); audio stays unshareable). Grants target me, a person, a group, the household or
  (later) the public. **Ghost mode** is on by default for every new user and add-on, with one
  master toggle, and hides every live class. **Precise and live location always expire
  within 24 h; nobody can raise another's precision**, except one's own SOS or crash alert
  to one's own safety contacts, audited. Core holds it; Social and Vehicles & Map only read it.
- **§7 Sharing.** Contacts, groups and rides are first-class objects (a ride-scoped grant
  ends at ride end); invites gain an 8-character,
  10-minute code with a six-digit key check beside link and QR.
- **§9 Social and integrations.** "No third-party login" becomes "no third-party login as the
  way in": later (P5 at the earliest) an optional Ostler Cloud OIDC broker may **link** a
  social identity to an existing local user, plus a generic OIDC client; local credentials
  always work offline.
- **Consequences.** HTTP Basic is accepted in the P1 release on the old routes only and
  refused in the next, with no switch to re-enable it. `auth.db` lives on the Brain, which
  pushes a signed roster to the node and guardian; with the Brain asleep they accept pairing
  keys and signed grants only. New text says "user role", keeping "role holder" for
  ADR-0037's device duties.
- **Decisions for the owner:** answered 2026-10-07: approved as recommended (alternatives
  not chosen). The thirteen items in
  [spec §14.15](../specs/2026-10-06-accounts-sharing-design.md#1415-decisions-for-the-owner)
  (registry, ghost scope and timers, the 24 h cap, no raising, owner vs driver ghost, invite
  code, head-unit profiles, public name, social login, Basic Auth end, `auth.db` placement,
  "user role").

## Amendment (2026-10-07, DMD round), approved

**Approved by the owner on 2026-10-07 ("approve all", DMD round).** Where these entries
differ from the decision text and the amendments above, they win. Detail:
[Ostler Community spec](../specs/2026-10-07-community-hub-design.md) (approved), from the
[community hub architecture](../references/research/community_hub_architecture.md),
[DMD Hub features](../references/research/dmd_hub_features.md) and
[DMD Hub UI teardown](../references/research/dmd_hub_ui_teardown.md) research; per-trip levels
are the [trip-sharing spec](../specs/2026-10-07-trip-sharing-design.md)'s (approved) and
[ADR-0043](adr-0043-gps-and-logs-in-shared-trips.md)'s. Only the text that changes is listed.

- **§9 Social and integrations: the feed and the directory.** "A minimal in-house feed" is
  replaced: neither core nor Social has a feed or a directory (Social spec §1 stays true). The
  opt-in community hub, **Ostler Community** (the `ostler-hub` service: closed, run only by
  Ostler as one official instance, not self-hostable, in its own private repo separate from
  `ostler-cloud`; reached through the open AGPL shell add-on `ostler-app-hub`), holds
  **Discover** (public items and clubs that chose to be listed, filtered by make, model and
  engine; no feed for strangers) and an opt-in, chronological **Following** feed in
  `ostler-app-hub` only. No points, ranks or leaderboards. Hub pages share out by Web Share,
  copy link, QR and embed, never social-network buttons or scripts; §9's share sheet,
  click-to-chat and webhook integrations are unchanged.
- **§9 Forum and wiki.** The hub is also the project's forum (categories per make and model,
  Q&A with "solved", search, notifications) and wiki; it has **no direct messages** between
  users, so Social stays the only messenger. Nothing in core depends on any of it (ADR-0042
  decision 7), and everything a user put on it can be exported.
- **§9 "No third-party login as the way in"** stays for devices. A hub account is the hub's own
  identity (passkey first, password, optionally Google or Apple **on the hub site only**) and
  never signs anyone into a device. A device user links to a hub by RFC 8628 device flow or
  PKCE, with a per-device, per-user token (`publish`, `read`, `help`) in `auth.db` and a
  pairwise id per device and local user (never a peer fingerprint or an `ostler-cloud` id).
  There is one hub; a device does not link to several. The hub's identity may later serve as
  the link-only OIDC broker of accounts §14.8, the one Ostler account `ostler-cloud` also
  trusts.
- **§8 and accounts §14.2: the `public` audience.** "Public (reserved; not before club pages,
  after P4)" is brought forward **for the hub only**, at hub phase H1: reachable only by an
  explicit publish act, with a checklist and review until the account is trusted, for trip
  cards and routes (L0–L1), routes, garage cards and events; never for live location, L2,
  raw logs, audio or video. The `link` audience (anyone with the link) is added with it; both
  are defined in the trip-sharing spec.
- **§8 "No share ever carries … a raw capture".** Unchanged: full logs (L3) and diagnostics
  bundles (L4) reach a hub only as **hand-overs** into a help thread, encrypted for named
  helpers, time-boxed, never as grants and never public.
- **§9 rides on the web.** A live ride may have a hub page: ride-scoped, at most 24 h,
  positions held in memory only and not stored after the session; listing it publicly is
  opt-in per ride, off by default, 18+, with a one-time warning.
- **§11 Phases.** Hub phases H0–H4 follow the P-phases: H1 needs P3. Groups and rides (P4)
  stay core; the forum and help threads are the hub's H1, clubs, events and the GitHub bridge
  its H2.
- **Alternatives: "ActivityPub federation now. Deferred."** Becomes: **no federation**, with no
  phase: there is one closed instance and no self-hosted hubs to federate with. Open read paths
  replace it (RSS/Atom, ICS, embeds) plus a monthly public dump of CC BY-SA content; nothing
  private, no full log and no help attachment ever leaves except by the owner's hand-over.
- **Age.** Hub accounts 16+; live follow and public profiles 18+.

## Changelog

- 2026-10-07: v1.4, adds the proposed amendment (2026-10-07) for owner approval.
- 2026-10-07: v1.5, the amendment is approved by the owner on 2026-10-07 ("approve all") and
  renamed "Amendment (2026-10-07), approved"; its decisions (accounts spec §14.15) answered
  as recommended.
- 2026-10-07: v1.6, adds the proposed amendment (2026-10-07, DMD round) for Ostler Community,
  for owner approval.
- 2026-10-07: v1.7, that proposed amendment revised in place for the owner's direction: the hub
  is closed, Ostler-run and not self-hostable (one instance, devices link to it alone), also the
  forum and wiki with no direct messages; federation dropped; decision 4 revised, decision 5
  added.
- 2026-10-07: v1.8, the DMD-round amendment is approved by the owner on 2026-10-07
  ("approve all", DMD round) and renamed "Amendment (2026-10-07, DMD round), approved";
  its five decisions answered as recommended (alternatives not chosen).

## Decisions for the owner (amendment, 2026-10-07, DMD round)

Answered 2026-10-07: approved as recommended ("approve all", DMD round). Each
recommendation below is the decision; each alternative was not chosen.

1. **Feed and directory** — move §9's "minimal in-house feed" to the hub as Discover plus an
   opt-in Following feed in `ostler-app-hub` only? *Recommend:* yes. *Alternative:* keep a
   minimal ride-summary feed in Social for groups.
2. **`public` audience timing** — bring `public` (with `link`) forward to hub H1, explicit publish
   and review only? *Recommend:* yes. *Alternative:* keep `public` until after P4 club pages and
   use `link` only at H1.
3. **Hub identity** — hub-owned accounts linked to devices by RFC 8628 or PKCE with pairwise ids,
   optional Google or Apple sign-in on the hub site only? *Recommend:* yes. *Alternative:* no hub
   accounts; the hub trusts device signatures.
4. **Federation** — none, with no phase (one closed instance), open read paths and a public
   CC BY-SA dump instead? *Recommend:* yes. *Alternative:* outbound-only ActivityPub from the
   official instance later, allowlist mode (the previous draft's H5).
5. **Self-hosting** — the hub is closed and run only by Ostler, with the exit guarantee (export
   everything, nothing in core depends on it)? *Recommend:* yes (owner's direction).
   *Alternative:* the previous draft's open AGPL hub that clubs could self-host, with devices
   linking to several hubs.
