---
title: "ADR-0029 — Accounts, multi-vehicle garage, sharing and social"
area: decisions
status: locked
version: 1.2
updated: 2026-10-06
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0017-open-standards-first.md, decisions/adr-0032-one-node-optional-brain.md, decisions/adr-0033-action-categories-and-approvals.md, CONSTITUTION.md]
summary: >
  Accepted by the owner on 2026-10-06. Each Ostler device gets local users (an owner bootstrapped on first run with a physical setup code, or by phone pairing on Ostler Lite), passkeys through the optional extra openostler[passkeys] with passwords always available, cookie sessions and scoped, revocable API tokens (also for AI/MCP clients). Four roles (Owner, Driver, Viewer, Mechanic, time-boxed) grant action categories, each capped by its tier (ADR-0033); the gate takes the intersection of role, share and token categories and the minimum tier, then transport and driving state, and no role passes a tier gate or a confirmation. The garage defaults to the vehicle the node is on; other cars appear only through shares, and their data stays on their own device, pulled on demand. Invites by link or QR carry a permission level, an expiry and a pinned device key; remote paths are read-only unless the install-level override of ADR-0033 is set. Motorbikes use a guardian-variant or Lite node with the phone as the screen. Shares never carry a VIN, a raw capture or location unless opted in. Social (groups, rides, convoys) and outbound sharing via share intents, webhooks and bots come last, opt-in, with no ads or tracking. Amended 2026-10-06 by ADR-0039: read "Ostler Lite" as "Ostler Diagnostics".
---

# ADR-0029 — Accounts, multi-vehicle garage, sharing and social

> **Amended by [ADR-0038](adr-0038-mesh-car-to-car-and-off-grid.md), 2026-10-06:** §8 gains a **coarse** location level (the mesh default), and §9 names the mesh as a social transport. See [Amendments (mesh)](#amendments-2026-10-06-mesh).
> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** read "Ostler Lite" or "Lite" as "Ostler Diagnostics" (the family is Ostler Diagnostics, Ostler Guardian and Ostler Hub). See [Amendments (product family)](#amendments-2026-10-06-product-family).

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
