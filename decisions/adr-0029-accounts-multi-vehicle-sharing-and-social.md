---
title: "ADR-0029 — Accounts, multi-vehicle garage, sharing and social"
area: decisions
status: draft
version: 0.1
updated: 2026-10-06
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, decisions/adr-0018-ui-architecture-decisions.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0027-ip-everywhere-ecosystem-architecture.md, decisions/adr-0017-open-standards-first.md, CONSTITUTION.md]
summary: >
  Proposed, from the owner's direction of 2026-10-06. Each Ostler device gets local users (an owner bootstrapped on first run with a physical setup code), passkeys first with passwords as the fallback, cookie sessions and scoped, revocable API tokens (also for AI/MCP clients). Four roles (owner, driver, viewer, mechanic/guest, time-boxed) are ceilings over the existing safety tiers; the server takes the minimum of role, share, token, transport and driving state, and no role passes a tier gate or a confirmation. The garage defaults to the vehicle physically connected; other cars appear only through shares, and their data stays on their own device, pulled on demand. Invites by link or QR carry a permission level, an expiry and a pinned device key; remote paths stay Tier 0. Shares never carry a VIN, a raw capture or location unless opted in. Social (groups, rides, convoys) and outbound sharing via share intents, webhooks and bots come last, opt-in, with no ads or tracking.
---

# ADR-0029 — Accounts, multi-vehicle garage, sharing and social

- **Date:** 2026-10-06
- **Status:** proposed (owner direction, 2026-10-06; awaiting approval of
  [the accounts and sharing spec](../specs/2026-10-06-accounts-sharing-design.md) v0.1,
  which holds the detail and the open questions).

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
- Safety travels with the action: one server gate; roles only narrow it.
- Privacy: VIN, raw captures and location never leave the device by default.
- No new runtime dependency without saying so (GOALS §2.6).

## Decision

1. **Local users per device.** Ostler is multi-user, not multi-tenant: one device serves
   one owner's household and the vehicles it is connected to. The **owner** is created on
   first run with a one-time setup code shown on the device's own display or console (a
   physical step, no default password). An existing `--admin-password` seeds the owner's
   password on upgrade.
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
   to Tier 0.
5. **Roles are ceilings, not keys.** Owner (Tiers 0–3), mechanic/guest (0–3, always
   time-boxed), driver (0–1 plus comfort and alarm arming), viewer (0). The effective
   permission is the **minimum** of role, share, token scope, transport (any remote path is
   Tier 0, as today) and driving state. Tier 4 stays unrunnable. No role skips a confirm,
   a precondition or a lockout; the server enforces all of it.
6. **Garage.** The default vehicle is the one the base hardware is physically connected
   to, identified per UI spec §4.4. Other vehicles appear only through **shares**. A
   nearby Ostler device found by mDNS is shown as "nearby", with no data, until an invite
   is accepted. Shared data stays on its own device and is pulled on demand, never mirrored.
7. **Sharing.** Invites by link or QR carry a role, an expiry, a single-use secret (in the
   URL fragment) and the host device's certificate fingerprint, so device-to-device TLS is
   pinned without a public CA. Every share can be revoked; every grant, use and revocation
   is in an audit log. Transport is the LAN, Tailscale, or the future Ostler Cloud relay
   (ADR-0028, in progress).
8. **Per-share privacy.** Location is off unless granted per share (none, place names,
   precise, or live during a ride). **No share ever carries a VIN or its HMAC** (a masked
   VIN at most, ADR-0018 Q7), a raw capture, or audio.
9. **Social and integrations, later and opt-in.** Groups, clubs, rides and convoys, a
   minimal in-house feed, and outbound "share to" and "notify via" (share sheet, WhatsApp
   and Telegram links, Facebook's share dialog, Discord webhooks, the owner's own Telegram
   bot). Nothing is posted automatically without a per-destination opt-in. No ads, no
   tracking, no third-party login.
10. **Phases.** P1 local users, roles and tokens (may precede U6); P2 garage with LAN
    shares (with U6); P3 remote shares over Tailscale or the relay; P4 groups and rides;
    P5 integrations. Each needs its own approved spec or spec section first.

## Confirmation

- Server tests: every route requires a session or token, except bootstrap, login and the
  public-mode allowlist; each role and each share level is refused above its ceiling;
  a remote principal is refused Tier 1+; Moving refuses Tiers 1–3 for every role, owner
  included; an expired or revoked token or share fails at once.
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
