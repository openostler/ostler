---
title: "Accounts, sign-in and sharing in practice — first-run owner, passkeys, social login, invites, head-unit profiles, ghost mode"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0037-role-holders-and-handover.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0021-local-https-on-the-device.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, specs/2026-10-06-app-model-design.md, references/research/connectivity_uplink.md, references/research/grant_flow.md, references/research/social_group_drive_apps.md]
summary: >
  Live research (2026-10-07) against the approved accounts spec. First-run: Home Assistant, Immich, Jellyfin and Nextcloud all let the first visitor claim the owner; Ostler's physical setup code is stricter and should stay. Passkeys work offline but only on a trusted-TLS name: friends would have to install our root CA, so offer an optional Plex-style per-device public name issued by Ostler Cloud, a name-constrained local CA otherwise, and never make passkeys the only door. Google, Apple and Facebook login need a public HTTPS redirect, a registered app and (Apple) a paid account, so a device cannot hold them; only an optional Ostler Cloud OIDC broker could, as a linked identity. Proposes one sharing model (audience × data class × precision × time, ghost by default), a head-unit profile switcher with a local PIN, and a Basic Auth migration with a hard end date. Gap list, Copy/Avoid/Decide.
---

# Accounts, sign-in and sharing in practice

**Question (R5).** How do local-first, self-hosted products create the first owner, sign
people in, use passkeys and social logins, invite friends, switch users on a shared screen
and decide who sees what; and what does that mean for the approved
[accounts and sharing spec](../../specs/2026-10-06-accounts-sharing-design.md)
([ADR-0029](../../decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md))? All web
facts were checked on 2026-10-07; anything not verified is marked **(unverified)**.

**Bottom line.**

1. Keep the spec's core: local users, setup code, passwords always, passkeys optional,
   pinned device-to-device shares. It is stricter than every product surveyed.
2. Passkeys are a **naming and certificate** problem, not a crypto problem. Plan the names
   now (ADR-0021 trust spec), or passkeys will work only for the owner on one phone.
3. Social login cannot live on the device. It can only ever be an **optional Ostler Cloud
   identity broker** that links to a local user; never the only way in.
4. The owner's "one permission model" is mostly there, but split across three vocabularies
   (share levels, location levels, token data classes) and one more in the app manifest.
   Unify them into one **data-class registry** with **ghost by default**.

Social-app UX (feeds, convoys, maps) is covered by
[social and group-drive apps](social_group_drive_apps.md); the in-car network and relay by
[connectivity research](connectivity_uplink.md); signed grants by
[grant flow](grant_flow.md). This note does not repeat them.

## 1. First run: who becomes the owner

| Product | How the first owner is made | Physical proof? | Recovery if lost |
|---|---|---|---|
| **Home Assistant** | Open `homeassistant.local:8123`, "Create my smart home", enter name, username, password; that account is the owner and an admin [HA1] | No: the first browser on the LAN wins | None for the owner; re-onboard [HA2] |
| **Immich** | "Getting Started" on the web UI; the first user to register is the admin [IM1] | No | CLI `reset-admin-password` (unverified) |
| **Jellyfin** | Setup wizard: language, admin user, libraries [JF2] | No | Edit the database or re-run the wizard (unverified) |
| **Nextcloud** | Install wizard, or `NEXTCLOUD_ADMIN_USER`/`_PASSWORD` in the container env [NC2] | Env vars only | `occ user:resetpassword` (unverified) |
| **Vaultwarden** | No owner: an admin page behind `ADMIN_TOKEN` (store an Argon2 PHC hash); user sign-ups are open by default, which its own guidance calls a common production mistake [VW1][VW2] | The token is in the server config | Change the token |
| **Ostler (spec §2.1)** | 8-digit setup code on the device's own display or console, single use, 15 min; on Ostler Diagnostics alone, phone pairing with a physical step | **Yes** | `ostler auth reset-owner` on the console |

**Reading.** Every surveyed product trusts "first come, first served" on the LAN, and
Vaultwarden's open sign-up default is a known foot-gun. In a car the LAN is a hotspot that
passengers, a garage's Wi-Fi or a campsite can join, so the spec's setup code is right
(UK PSTI, ADR-0021). What to borrow is the *flow*, not the security model:

- **One screen, three fields.** HA's onboarding is name, username, password, done; then
  optional steps (location, analytics opt-in, integrations). Ostler: setup code, your name,
  then "Add a passkey" (if available) **or** a password, then optional "Name this car" and
  "Invite someone". Never ask for an email: there is nothing to send it.
- **Say plainly what is unrecoverable.** HA tells the user to store the owner credentials
  because there is no way to recover them [HA1]. Ostler can do better (console reset), and
  should say so on the same screen.
- **Separate "people" from "logins".** HA keeps *people* (who) apart from *users* (who can
  sign in), so a child or a car-share driver can be a person without a login [HA2]. That
  maps to Ostler's trip attribution ("who drove") without forcing an account (Gap G7).

## 2. Day-to-day sign-in patterns worth copying

| Pattern | Where | Use in Ostler |
|---|---|---|
| **Per-user "local network only"** switch in the user editor | HA [HA3] | A per-user "local links only" flag on top of ADR-0033 §6: a mechanic or a teen driver can never sign in over Tailscale or the relay |
| **Trusted networks with bypass** (auto sign-in from a range, optionally one fixed user) | HA [HA4]; HA warns it means no password for anyone on that network | Exactly the head-unit **kiosk session**; keep it bound to `localhost`, never an IP range |
| **Quick Connect**: a new client shows a 6-digit code, a signed-in user enters it | Jellyfin 10.7+ [JF1] | The RFC 8628 device flow (spec §2.4) for TVs, a second head unit, a tablet: same UX, standard protocol |
| **Device list with revoke** and per-device app passwords shown once | Nextcloud [NC1] | The spec's sessions and tokens tables; show them as "Signed-in devices" with last place and time |
| **Unused refresh tokens deleted after 90 days** | HA [HA2] | Adopt for sessions on trusted devices (spec says 30-day sliding; add a 90-day hard prune) |
| **Hide users from the login screen** | Jellyfin [JF3] | Head-unit profile tiles show only users who opted in (§6) |
| **Long-lived tokens** to replace a shared API password | HA [HA5] | Spec tokens; also the Basic Auth migration path (§8) |

## 3. Passkeys: what actually works for a car

### 3.1 The constraints

- **Secure context and a domain.** WebAuthn's RP ID must be a registrable domain the page is
  served from; IP addresses and bare public suffixes are not allowed; `http://localhost` is
  the only plain-HTTP exception; ports are ignored [WD1].
- **The certificate must be trusted, not clicked through.** Since Chrome 110 (February
  2023) WebAuthn is refused on pages with TLS certificate errors [BW1]. A self-signed or
  local-CA certificate works only once its root is installed in the OS trust store.
- **Installing a root is real friction.** On iOS a downloaded profile's root is not trusted
  for TLS until the user enables it under Settings → General → About → Certificate Trust
  Settings [AP1]. On Android, apps ignore user CAs since Android 7; Chrome is believed to
  honour them for websites, with a persistent "network may be monitored" notice
  **(unverified; bench)** [AN1]. And asking a *friend* to install your root asks them to
  trust you with all their HTTPS unless the CA is **name-constrained** to your device names
  (browser enforcement of name constraints on user roots: **unverified; bench**).
- **`.local` names cannot get public certificates**; public CAs stopped issuing for internal
  names in 2015 [HL1]. `.local` with a trusted local CA works in principle; Safari and
  Firefox on the bench remain open (spec §2.2).
- **A passkey is bound to one RP ID.** The same Ostler reached as `ostler-ab12.local`, as
  `car.tail1234.ts.net` and through the relay is three RP IDs and three passkeys, unless the
  names share a parent domain or Related Origin Requests are set up [WD1].

### 3.2 Platform vs roaming, online vs offline

| Authenticator | Works with no internet in the car? | Recovery | Fit |
|---|---|---|---|
| **Platform, synced** (iCloud Keychain, Google Password Manager) | **Yes** for sign-in on the same phone: the signature is local; sync is not needed | Comes back with the user's Apple or Google account on a new phone | The default for owners and drivers on their own phones |
| **Cross-device (hybrid, "scan the QR")** | **No**: both devices need internet; Bluetooth is only the proximity check [CB1] | n/a | Do not rely on it for the head unit in a field |
| **Roaming key** (USB/NFC security key) | Yes | Register two; the second is the backup | Owner's backup; mechanics' shops |
| **Head-unit browser** | Unknown: many Android head units are uncertified builds; a platform passkey provider may be missing **(unverified; bench)** | n/a | Do not need it: the head unit uses the kiosk session plus a PIN (§6) |

### 3.3 Naming options, ranked

| Option | How | Offline in the car? | Friends need our CA? | Cost |
|---|---|---|---|---|
| **A. Per-device public name (Plex-style)** | Ostler Cloud issues `*.<device-hash>.<ostler domain>` by DNS-01; LAN addresses are encoded in the label (`192-168-4-1.<hash>…`), so the RP ID `<hash>.<domain>` stays the same when the IP changes. Plex has done this since 2015 with `*.plex.direct` [PX1] | **Yes**, if the Brain's DNS on the in-car AP answers the name locally (public DNS is unreachable offline); routers with DNS-rebind protection need an exception [PX1] | **No** (public CA) | Needs Ostler Cloud at setup and for renewals (90-day certs), never at sign-in |
| **B. Tailscale name** | `tailscale cert` on `*.ts.net` (spec §2.2) | Only on the tailnet | No | Owner uses Tailscale |
| **C. Local CA, name-constrained** | ADR-0021's per-device CA, constrained to the device's names | Yes | **Yes**, a profile per phone | Free; friction per phone |
| **D. `http://localhost`** | Head unit only | Yes | n/a | Head unit only |

**Recommendation.** Ship passwords and the kiosk session at P1; P1b passkeys on C and D;
add A as an **optional** Ostler Cloud service (it is the only option that lets a family's
phones use passkeys with no CA install). Remote friends never need a passkey on *our*
device at all: they use their own device and a pinned share (spec §5.2), which is already
the right design.

### 3.4 Recovery

- Owner: synced passkey, else password, else console `reset-owner` (spec). On **Ostler
  Diagnostics alone** there is no console: recovery must be "hold the node's button and
  re-pair a phone", which keeps data but revokes old pairing keys (Gap G4).
- Others: the owner resets them; offer **printed recovery codes** only for the owner (the
  Nextcloud and Vaultwarden 2FA pattern) **(not checked today)**.
- List passkeys with the name they work on (spec §2.2, already) and warn before deleting
  the last credential of the last owner.

## 4. Social logins (Google, Apple, Facebook)

### 4.1 What each provider needs (checked 2026-10-07)

| Provider | Redirect URI | App registration and review | Cost | Other |
|---|---|---|---|---|
| **Google** | HTTPS; no raw IPs (except loopback); host must end in a Public Suffix List TLD; no wildcards; no fragments [GG1] | An OAuth client per app; unverified apps show a warning screen and are capped at 100 new users until verified; basic sign-in scopes are non-sensitive but brand verification applies to public apps [GG2] | Free | Client secret per app |
| **Apple** | HTTPS on a verified domain (a file under `/.well-known/`); `localhost` and IPs fail [AP2] | A Services ID under a paid developer account [AP2] | **$99/year** (unverified figure from a third-party guide) | Private-relay email addresses; a signed client-secret JWT that expires |
| **Facebook** | Exact-match redirects (Strict Mode, mandatory), HTTPS only [FB1] | `public_profile` and `email` start with Standard Access, usable only by the app's own people; Advanced Access needs Business Verification and App Review [FB2] | Free; verification needs a registered business | Graph API versioning churn |

### 4.2 Can a self-hosted car device use them? No, not directly.

1. **No public redirect.** Every provider wants a fixed, registered HTTPS redirect on a
   public domain; a car on a hotspot has none, and registering one per device is not
   possible at Apple or Facebook scale.
2. **No safe client secret.** One OAuth app shared by every device means one secret copied
   onto every Pi; anyone can extract it and impersonate "Ostler".
3. **Internet at sign-in.** Opening your own car would depend on Google and a mobile
   signal, which breaks local-first (GOALS §2.1; ADR-0029 rejected it for this reason).
4. **Review is for a company.** Facebook's verification and Apple's account need a legal
   entity behind "Ostler".

The self-hosting world's answer is **bring your own OIDC provider**: Immich takes any OIDC
issuer, with auto-register and a role claim [IM2]; Vaultwarden added OIDC SSO in 1.35
[VW3]; homelabs run Pocket ID (a passkey-only OIDC provider, one container on SQLite) [PI1]
or Tailscale's `tsidp`, which turns tailnet identity into OIDC (experimental) [TS2].

### 4.3 The only shape that fits

- **Ostler Cloud as an OIDC broker (optional, later).** Ostler Cloud is the one registered
  app at Google, Apple and Facebook; each device is an ordinary OIDC client of Ostler Cloud
  (authorisation code with PKCE, redirect via the device's public name from §3.3 A or the
  relay). The cloud returns a stable, pairwise subject per device, never the email unless
  asked.
- **Link, never replace.** A social identity is *linked* to an existing local user, as a
  convenience on a new phone; the local passkey or password always works offline. ADR-0029's
  "may come later as an optional link on Ostler Cloud only" already says this.
- **A generic OIDC client** (issuer URL, client id, secret) is cheap once the broker client
  exists and serves homelabbers with Pocket ID, Authentik or tsidp.
- **Not for friend discovery.** "Find friends from Facebook" would leak a social graph into
  the car; contacts stay invite-only (§5).

## 5. Friend invites and contact discovery

- **Invite links and QR are the norm.** Signal added usernames in February 2024 with QR codes
  and links, **no searchable directory**, and a "Nobody" setting for discovery by phone
  number [SG1]. Tailscale shares one machine by link; links are single-use or multi-use (up
  to 1,000), expire after 30 days unused, and a shared machine can answer but not initiate
  connections [TS1]. Immich's public links carry an expiry, a password and an
  allow-download switch [IM3]. The spec's invite (fragment secret, pinned fingerprint, 48 h
  expiry) matches the best of these.
- **Add a short code** for when a link cannot travel: read aloud at a meet-up, typed on a
  head unit while parked, or sent over a mesh text (ADR-0038). Eight characters from a
  no-ambiguity alphabet, valid 10 minutes, bound to the same invite record.
- **No address-book upload, no phone numbers, no global directory.** Nearby discovery stays
  mDNS with advertising off (spec §4).
- **One-way vs mutual.** Immich partner sharing is one-way and exposes *all* metadata,
  GPS included, once granted [IM4]: a useful anti-example. Ostler shares are one-way per
  vehicle (correct), but "friend" is not yet an object: a friend is a **contact** (a peer
  device plus a display name) that shares to and from can attach to (Gap G2).

## 6. User switching on a shared head unit

| Precedent | What it does |
|---|---|
| Android Automotive | Per-profile lock by PIN, pattern or password; a locked-out user can fall back to a guest profile or pick another profile [AA1][AA2] |
| Tesla driver profiles | Seat, mirrors, climate, media and data-sharing preferences per driver, synced via the Tesla account, linked to keys [TE1] |
| Netflix profile lock | A 4-digit PIN per profile on a shared screen [NF1] |
| Jellyfin | Profile tiles on the login screen, each hideable [JF3] |

**Proposal for Ostler.**

- **The car's screen always starts in the kiosk session** (Read, Comfort), as the spec says.
  A profile chip in the status strip shows "Car" until someone signs in.
- **Switching is Parked-only** and opens a tile sheet of users who opted in to appear.
- **A head-unit PIN** (6 digits, set by the user from a full sign-in, stored scrypt-hashed,
  valid only on that head unit over `localhost`, 5 tries then a 15-minute lock) unlocks a
  *session* for that user on that screen. It is a convenience factor, like Netflix's and
  AAOS's: it never works over the network, never mints tokens, and Tier 2–3 still need the
  paired-phone approval (ADR-0033 §6).
- **Approve from your phone** as the stronger option: a paired phone on the in-car LAN
  approves the switch (no internet, unlike passkey hybrid).
- **Auto sign-out** at ignition off or after a trip ends, back to kiosk; a "remember on this
  car" option keeps a driver signed in for days (the Tesla feel) without a PIN each start.
- **Who drove.** Trips record the signed-in user, or "Car" for kiosk, so Maintenance and
  Social can attribute (Gap G7).

## 7. One permission model: who sees what, ghost by default

### 7.1 Precedents

| App | Audience | Precision | Time | Notes |
|---|---|---|---|---|
| Snap Map | All friends, select friends, or only me (**Ghost Mode**); off by default at launch [SN1] | precise | — | See without being seen |
| Apple Find My | per person | precise | 1 hour, end of day, indefinitely [AP3] | Per-person durations |
| Google Maps | per person or link | precise | 15 min to 3 days, or until off [GM1] | Link for non-users |
| Life360 | per circle | **Bubble**: a coarse radius for a set time; members are notified; popped by crash detection [LF1] | per bubble | A safety override that *reveals* location |
| Strava | Everyone, followers, only you, per activity; map hidden or trimmed by privacy zones [ST1] | trimmed start and end | — | Beacon: live link to up to 3 contacts, ends with the activity [ST2] |

### 7.2 The model

```
visible(viewer, field) = not ghost(owner)            # master switch, default ON
                         and audience(field) ∋ viewer   # me · person · group · household · public(later)
                         and now < expiry(grant)
                         then precision(field, viewer)  # for location: none · coarse · place · precise · live
```

- **Data classes are one registry**, declared by core and add-ons: `presence`, `vehicle_card`
  (make, model, photo, nickname), `location`, `live` (telemetry), `trips` (summaries),
  `routes`, `stats` (time-at-speed, sprints), `faults`, `maintenance`, `costs`, `video`,
  `audio`, `notes`. Each add-on's manifest declares the classes it shows and publishes
  (today's `permissions.data` in the app-model spec §4), with a default audience of **only
  me**. The VIN is never a class (ADR-0036).
- **Audiences** are the owner's own words: *only me*, a *person* (contact), a *group*, the
  *household* (local users on the device), and later *public* (club pages).
- **Ghost mode** is the default for every new user and every new add-on: shares exist but
  send nothing until switched on, and one toggle in the status strip turns everything off at
  once (shares, live rides, mesh positions). Turning ghost off shows a one-screen summary of
  what each audience will see.
- **Time first.** Every grant to a person or group offers 1 hour, until end of trip, until
  end of day, or until I stop (Find My and Google Maps durations).
- **"View as…"** preview: pick a contact and see the car exactly as they would.
- **Emergency is a separate, explicit grant**, not a ghost-mode leak: a Strava-Beacon-style
  link to chosen contacts for one trip, or an alarm share (ADR-0033 §7). Unlike Life360's
  crash pop, ghost mode never reveals position by itself.
- **Enforced at the source.** The device answering `/peer/v1` filters by this rule (spec
  §5.3); the UI only previews it.

## 8. Migrating today's single HTTP Basic password

Home Assistant's lesson: the auth system arrived in 0.77 (August 2018), the API password
was deprecated in 0.90–0.91 and its URL form only stopped working in 0.101 (October 2019),
and the legacy provider lingered in configs long after, confusing users [HA6][HA5].

1. **Release N (P1):** on first start with `--admin-password`/`D2DIAG_ADMIN_PW` set and no
   `auth.db`, create user `owner` with that password (scrypt) and **skip the setup code**
   (whoever set the env var already has the console). Banner: "Add a passkey or rename
   your account".
2. Basic Auth keeps working, mapped to the owner, but **only on the old routes**: new
   routes accept sessions and tokens only. Every Basic request is logged with its client so
   the owner can find scripts.
3. **Settings → Scripts** mints a token to replace the password in each script (HA's
   long-lived token path).
4. **Release N+1:** Basic Auth refused; a clear 401 body names the token page. No env
   switch to re-enable it.
5. Public mode keeps its allowlist; its "server password" becomes an owner or mechanic
   sign-in (ADR-0029 Consequences).
6. Basic Auth cannot sign out (the browser caches it); say so in the release note.

## 9. A note on ADR-0037 ("roles" means two things)

ADR-0037's *role holders* (transmit gate, parked broker, time source) are device duties;
ADR-0029's *roles* are user permissions. Its rule "authority is never a role; the executing
gate checks every grant" is exactly what accounts need: a user's role is checked where the
action runs, and holding the broker grants nothing. Two consequences the accounts spec does
not yet state: **where `auth.db` lives** when the Brain sleeps (ADR-0037 keeps pairing
authority on the Brain and "losing the brain only blocks new pairings") and what the node
can verify alone (signed grants per [grant flow](grant_flow.md), not passwords). Suggest
calling user roles "user roles" in new text.

## 10. Gap list against the accounts spec

| # | Gap | Where | Suggested fix |
|---|---|---|---|
| G1 | Four vocabularies for "what data": share levels (`view`, `view+logs`), location levels (+ coarse, ADR-0038), token data classes (`live`, `faults`, `sessions`, `location`, `notes`), app-manifest `permissions.data` (`location`, `video`, `audio`) | spec §2.4, §5.3; app-model §4 | One data-class registry (§7.2), add-on-extensible; levels become presets over it |
| G2 | No "friend" or "group" object: shares attach to a peer key only | spec §5, §8 `peers` | A `contacts` table (peer + display name + groups); grants target a contact, group or household |
| G3 | No ghost mode or global "share nothing" switch; no time presets beyond expiry | spec §5.3 | §7.2: ghost default on, one toggle, duration presets |
| G4 | Owner recovery on Ostler Diagnostics alone not defined | spec §2.1 | Physical button re-pair that revokes old pairing keys and keeps data |
| G5 | Passkey naming plan stops at "a stable name"; no answer for family phones without a CA install | spec §2.2; ADR-0021 | §3.3: options A–D; ask the owner about A |
| G6 | Head-unit switching beyond the kiosk session: no profiles, PIN, auto sign-out | spec §2.3 | §6 |
| G7 | No "person without a login" or "who drove" attribution | spec §3.1, §8 `users` | `users.can_sign_in` false; trips carry `user_id` or `car` |
| G8 | Per-user "local links only" flag | spec §3.2 | HA-style flag, checked in `transport_ok` |
| G9 | Social login path unspecified beyond "rejected" | spec §7; ADR-0029 Alternatives | §4.3: optional Cloud OIDC broker, link-only, plus generic OIDC; a P5+ item |
| G10 | Short invite code for links that cannot travel (voice, mesh, head unit) | spec §5.2 | §5 |
| G11 | Where `auth.db` lives across node, Brain and Guardian; what works with the Brain asleep | spec §8; ADR-0037 §2 | A section in the P1 spec |
| G12 | Basic Auth overlap lacks an end date and a "new routes never accept Basic" rule | spec §2.1 | §8 |
| G13 | Session pruning: 30-day sliding but no hard prune of unused trusted sessions | spec §2.3 | 90-day prune (HA) |

## Copy / Avoid / Decide for Ostler

**Copy**

- HA's three-field onboarding and its people-vs-users split (spec §2.1, G7).
- HA's per-user "local network only" switch (spec §3.2, G8).
- Jellyfin Quick Connect's UX on top of RFC 8628 (spec §2.4).
- Nextcloud's signed-in devices list with per-device revoke (spec §2.3, §8 `sessions`).
- Plex's per-device public wildcard name, as an optional Ostler Cloud service (ADR-0021,
  ADR-0028; G5).
- Signal's no-directory usernames with QR and links; Tailscale's single-use, expiring,
  answer-only shares (spec §5.2, already close).
- Find My and Google Maps duration presets; Snap's "see without being seen" ghost mode;
  Strava's privacy zones and one-trip Beacon link (spec §5.3, §6; G3).
- AAOS and Netflix profile PINs, local to the screen (spec §2.3; G6).

**Avoid**

- First-visitor-claims-owner (HA, Immich, Jellyfin) and open sign-ups by default
  (Vaultwarden). Keep the setup code (spec §2.1).
- Trusted-network bypass by IP range (HA): kiosk stays bound to `localhost` (spec §2.3).
- Social login on the device, a shared OAuth client secret on every device, or social
  identity as the only credential (ADR-0029 Alternatives).
- Passkeys as the only way in, or hybrid cross-device sign-in for the head unit (needs
  internet).
- Asking friends to install our root CA; any un-constrained local CA.
- Immich-style all-or-nothing partner shares that include GPS.
- A safety feature that silently reveals location while in ghost mode (Life360 crash pop).
- A legacy auth path that lingers for a year (HA's API password).

**Decide** (recommendations for the owner)

1. **One data-class registry with ghost by default** (G1, G3). *Recommend yes:* replace the
   share levels, location levels, token data classes and manifest `permissions.data` with
   one add-on-extensible registry; audiences me / person / group / household / public-later;
   ghost on for every new user and add-on; one master toggle. Amend ADR-0029 §8 and the
   app-model spec §4.
2. **Optional per-device public name from Ostler Cloud for passkeys** (G5). *Recommend yes,
   as an optional service:* `*.<device-hash>.<ostler domain>` with DNS-01 certificates and
   local DNS on the Brain's AP; the name-constrained local CA stays the no-cloud path. Record
   in the ADR-0021 trust spec.
3. **Social login** (G9). *Recommend: keep it out of P1–P4;* at P5 at the earliest, only as an
   Ostler Cloud OIDC broker that **links** to a local user, plus a generic OIDC client for
   self-hosters. Never Facebook-first (business verification); Apple only if an iOS
   companion exists.
4. **Head-unit profiles and PIN** (G6, G7). *Recommend yes:* Parked-only switching, a
   6-digit local PIN or phone approval, auto sign-out at ignition off, and trips record who
   drove.
5. **Basic Auth end date** (G12). *Recommend:* accepted in release N on old routes only,
   refused in N+1 with no re-enable switch; the env password seeds the owner and skips the
   setup code.
6. **Contacts and groups as first-class objects** (G2). *Recommend yes,* in the P2 spec,
   with an 8-character, 10-minute short invite code beside link and QR (G10).

## Sources (checked 2026-10-07)

- [HA1] Home Assistant, onboarding: https://www.home-assistant.io/getting-started/onboarding
- [HA2] Home Assistant, authentication: https://www.home-assistant.io/docs/authentication/
- [HA3] Nabu Casa, user restricted to local access: https://www.nabucasa.com/config/troubleshooting/user_restricted_to_local_access
- [HA4] Home Assistant, auth providers: https://www.home-assistant.io/docs/authentication/providers/
- [HA5] Home Assistant 0.101 release notes: https://home-assistant.io/blog/2019/10/30/release-101
- [HA6] Home Assistant 0.77 release notes: https://home-assistant.io/blog/2018/08/29/release-77
- [IM1] Immich, user management: https://docs.immich.app/administration/user-management
- [IM2] Immich, OAuth: https://docs.immich.app/administration/oauth
- [IM3] Immich, sharing: https://docs.immich.app/features/sharing/
- [IM4] Immich, partner sharing: https://docs.immich.app/features/partner-sharing/
- [JF1] Jellyfin, Quick Connect: https://jellyfin.org/docs/general/server/quick-connect
- [JF2] Jellyfin setup wizard walkthrough (third party): https://lumadock.com/knowledgebase/articles/13385002-jellyfin-setup-wizard-walkthrough
- [JF3] Jellyfin forum, hiding users from the login screen: https://forum.jellyfin.org/t-hide-login-page
- [NC1] Nextcloud user manual, session management: https://docs.nextcloud.com/server/latest/user_manual/en/session_management.html
- [NC2] Nitrokey, Nextcloud passwordless and 2FA: https://docs.nitrokey.com/nitrokeys/features/fido2/nextcloud
- [VW1] Vaultwarden wiki, enabling the admin page: https://github.com/dani-garcia/vaultwarden/wiki/Enabling-admin-page
- [VW2] SSD Nodes, is Vaultwarden secure: https://www.ssdnodes.com/learn/lang/pl/is-vaultwarden-secure
- [VW3] Vaultwarden wiki, SSO with OpenID Connect: https://github.com/dani-garcia/vaultwarden/wiki/Enabling-SSO-support-using-OpenId-Connect
- [WD1] web.dev, the RP ID: https://web.dev/articles/webauthn-rp-id
- [BW1] Bitwarden forum, WebAuthn and TLS errors in Chrome 110: https://community.bitwarden.com/t/login-or-2fa-via-webauthn-chrome-plugin-not-working-due-to-tls-certificate-errors/51011
- [AP1] Apple, trust manually installed certificate profiles: https://support.apple.com/en-ca/102390
- [AN1] Android, network security configuration: https://developer.android.com/privacy-and-security/security-config
- [HL1] Homelab internal HTTPS certificates guide: https://homelabrouter.com/homelab-internal-https-certificates-guide/
- [CB1] Corbado, hybrid transport and QR codes: https://www.corbado.com/blog/webauthn-passkey-qr-code
- [PX1] Filippo Valsorda, how Plex does HTTPS for all its users: https://words.filippo.io/how-plex-is-doing-https-for-all-its-users/
- [GG1] Google, OAuth 2.0 for web server apps (redirect URI validation): https://developers.google.com/identity/protocols/oauth2/web-server
- [GG2] Google Cloud help, unverified apps: https://support.google.com/cloud/answer/7454865
- [AP2] Better Auth, Sign in with Apple setup (third party): https://better-auth.com/docs/authentication/apple
- [FB1] Meta, Facebook Login security: https://developers.facebook.com/documentation/facebook-login/security
- [FB2] Nextend, Facebook provider setup (access levels, verification): https://social-login.nextendweb.com/documentation/providers/facebook/
- [PI1] Pocket ID (listing): https://openalternative.co/pocket-id
- [TS1] Tailscale, sharing: https://tailscale.com/kb/1084/sharing
- [TS2] Tailscale, tsidp: https://tailscale.com/docs/features/tsidp
- [SG1] Signal, usernames and phone number privacy: https://signal.org/blog/phone-number-privacy-usernames/
- [AA1] Android for Cars, how profiles work: https://developers.google.com/cars/design/automotive-os/product-experience/system-ui/profiles/how_profiles_work
- [AA2] Android Automotive, profile best practices: https://docs.partner.android.com/drivingux/automotive-os/flows-behaviors-and-patterns/profile-best-practices
- [TE1] Tesla owner's manual, driver profiles: https://www.tesla.com/ownersmanual/2017_2023_model3/en_us/GUID-A2D0403E-3DAC-4695-A4E6-DC875F4DEDC3.html (search summary; page refused fetch)
- [NF1] Netflix help, profile PIN: https://help.netflix.com/en/node/114277
- [SN1] iPhone in Canada, Snap Map launch: https://www.iphoneincanada.ca/news/snapchat-snap-map-location-sharing/
- [AP3] Apple, share your location (Find My): https://support.apple.com/en-ca/guide/imac-pro/apd301677d8c/mac
- [GM1] Google Maps real-time location sharing (press summary): https://www.igeeksblog.com/how-to-share-location-in-google-maps-on-iphone
- [LF1] Life360 legal help, Bubbles: https://legal.corp.life360.com/hc/en-us/articles/16044136535703
- [ST1] Kaspersky, Strava privacy settings: https://www.kaspersky.com/blog/running-apps-privacy-settings-part2-strava/52409
- [ST2] BikeRadar, Strava Beacon: https://bikeradar.com/news/strava-beacon-reassures-your-friends-and-family-that-youre-safe
