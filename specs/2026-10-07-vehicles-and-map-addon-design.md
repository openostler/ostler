---
title: "Vehicles & Map add-on — browse friends' vehicles on a built-in live map, ghost by default — design"
area: specs
status: stable
version: 0.2
updated: 2026-10-07
depends_on: [specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-app-model-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-06-module-bus-messages-design.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0034-repo-boundaries.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0038-mesh-car-to-car-and-off-grid.md, references/research/social_group_drive_apps.md, references/research/accounts_social_login.md, references/research/mesh_transports.md, references/research/driver_distraction_rules.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all"). Vehicles & Map (`ostler-app-vehicles`, optional first-party add-on) is one feature: browsing the vehicles your friends and groups share with you, with the full-screen dark map built into it. It lists shared vehicles as garage cards (owner-curated fields; no VIN, masked or not; plate hidden by default; photo EXIF stripped; live stats only through granted data classes) and draws them on the map as vehicle pins with heading, an age ring and "updated … ago", a bottom sheet, the share countdown and a visible/ghost chip. Ghost mode is the default (one switch; turning visible offers 1 h, 24 h or until I go ghost; ghost hides presence, location and live signals). Who sees what comes from the core data-class registry of the accounts-sharing amendment (audience, class, detail, window; accounts §14); this app only reads it. Group drives share live position for the ride only and end at ride end. Positions arrive over shares and the Social link router (internet, Wi-Fi mesh, HaLow, LoRa), with coarse = Meshtastic 13-bit precision. On a head unit while Moving: no other vehicles, except opted-in convoy members as plain markers. Viewers without Ostler come later, through a relay link of at most 24 h. ADR-0009/0029/0033/0036/0038 compliance, phases, tests and decisions.
---

# Vehicles & Map add-on — design

**Status:** approved by the owner on 2026-10-07 ("approve all"), v0.2. Nothing here is built before U1 and accounts P2.
**Owner direction (2026-10-07):** "the map feature should be built into the feature that
allows you to browse other people's vehicles"; ghost mode by default; the permissions system
decides who sees what (friend, group…). Evidence:
[social and group-drive apps](../references/research/social_group_drive_apps.md),
[accounts and sign-in](../references/research/accounts_social_login.md) §7,
[mesh transports](../references/research/mesh_transports.md) §5,
[driver-distraction rules](../references/research/driver_distraction_rules.md) §7.
Ecosystem framing: [ADR-0042](../decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md)
(accepted), "small core, add-ons are the product". Sibling add-on: [Social](2026-10-07-social-addon-design.md).

## 1. Scope and boundaries

| Owns | Does not own (reads from) |
|---|---|
| The **Vehicles** list, the shared-vehicle page with its garage card, the **Map** (peer layer, pins, bottom sheet, visibility sheet), the convoy layer of an active ride, the head-unit convoy markers | **Permissions:** the core data-class registry, audiences, ghost master toggle, grants and audit ([accounts-sharing spec §14](2026-10-06-accounts-sharing-design.md#14-amendment-2026-10-07-approved-one-permission-model-and-the-shell-screens), amendment 2026-10-07, approved). This app **stores no permissions** |
| The garage-card editor for *my* vehicles (which curated fields exist) | **Groups and rides:** groups (kinds friends, club, ride, safety) are core (accounts §14.6); [Social](2026-10-07-social-addon-design.md) runs ride channels and talk; this app shows rides on the map |
| — | **Transport:** the Social link router (mesh transports §5) and `/peer/v1` shares (accounts spec §9) |
| — | **My own trips and replay:** core **Trips**; **find my car / tracker map:** core Security |
| — | **Map styles and tokens:** the visual design system spec (2026-10-07): "Ostler Night/Day" Protomaps flavours on self-hosted PMTiles, OpenFreeMap fallback |

It is an optional first-party app in its own repo `ostler-app-vehicles` (ADR-0034, app model
§3, §7). It declares **no actions** (§9): nothing in it can touch any car, mine or a friend's.

## 2. Browsing shared vehicles

### 2.1 Vehicles list

- **Groups** as the switcher already has them (UI spec §4.1, accounts spec §4): *Mine*,
  *Shared with me* (per person), and per group. Each row: silhouette or photo, nickname,
  owner's display name, status word (Driving, Parked, Offline since …, Hidden), place at the
  precision granted, **age** of the newest datum ("updated 4 min ago · via LoRa").
- Hidden is honest: a vehicle whose owner is in ghost mode shows "Hidden" with no last
  position, never a stale pin presented as current.
- Data is pulled on demand through the share and **cached in memory only** (accounts spec §4),
  so revocation is real; positions received over a mesh expire as in §6.2.

### 2.2 Garage card (the face of a shared vehicle)

Owner-curated fields only, under the `vehicle_card` class of the registry (accounts §14.1,
detail `basic · with plate`). Mods, the "about" text and the mileage band are fields this app
adds to that class, each with its own tick per grant (Decision 9):

| Field | Default to others | Rule |
|---|---|---|
| Nickname, make, model, year, body/vehicle type (drives the silhouette) | shown | typed by the owner; never read from identity data |
| Photo | shown if set | **EXIF and all metadata stripped and the image re-encoded on my device before it is offered** to any share; never the original file |
| Mods / equipment list, free text "about" | shown if set | owner text, length-capped |
| Mileage band (e.g. "150–200k km") | hidden | a band, never the odometer value |
| Plate | **hidden** | owner may tick it per audience; never on a map, never over a mesh (ADR-0038 §5) |
| VIN | **never** | not even masked: the masked VIN stays in my own garage (ADR-0018 Q7, ADR-0036) |

**Live stats** appear on the card only through granted data classes: `live` (an owner-picked
set of VSS signals, e.g. coolant temperature, fuel range, ≤ 6), `faults` (count and severity
word, codes only if granted), `trips` (summaries, routes trimmed by privacy zones). Nothing
else is fetched. A **"View as…"** preview (accounts research §7.2) shows my card exactly as a
chosen contact or group would see it.

## 3. The map (built into Vehicles)

The Vehicles feature opens on the map; the list is its bottom sheet. Visual values come from
the visual design system's tokens and map styles; this spec names only roles.

- **Full-screen dark map** ("Ostler Night" by default in dark theme, "Ostler Day" in light),
  floating chrome, my own vehicle(s) plus every shared vehicle I may see.
- **Pins:** vehicle silhouette (car, bike, truck, van) in a round badge; **heading arrow** when
  moving and the heading is known; an **age ring** that drains and greys as the fix ages
  (fresh < 2 min, ageing < 15 min, stale < 1 h, then "last seen" dashed); presence colour from
  the unified status vocabulary (ADR-0008). Precision is drawn, not hidden: a **coarse**
  position is a soft disc of its radius with no pin point, a place-name position snaps to the
  place label.
- **Under every pin and row:** "updated … ago", plus the source when not internet ("via LoRa,
  ±3 km").
- **Bottom sheet** (peek / half / full): peek shows count visible to me and my visibility chip;
  half is the list (§2.1); full is the vehicle page (§2.2). Tapping a pin opens the half sheet
  on that vehicle.
- **Visibility chip** on the map, mirroring the shell's strip chip: neutral **Ghost**, or the
  accent "Visible to Peak District ride · 1 h 20 m left" with a **live countdown** for every
  time-boxed share. Being visible is never subtle.
- **"Seen by"** per share: the share audit (accounts spec §5.3) shown to the owner.
- No speed-coloured traces of other people; speed traces are for my own trips in Trips only.
  No leaderboards, no speed of others unless the `live` grant includes `Vehicle.Speed`.

## 4. Ghost mode and the visibility sheet

- **Ghost is the default** for every new user and every add-on (accounts §14.3). In ghost:
  **presence, location and live signals** are sent to no one on any path (`/peer/v1`
  answers, router `position` and `telemetry` on every link). Non-live grants (`trips`,
  `faults`, `vehicle_card`) stay as each grant says (social research D1).
- **Ghost costs nothing else:** I still see others, message, join rides (Waze's penalty
  avoided, research §3.3).
- **One switch.** Turning ghost **off** asks how long: **1 h**, **24 h**, or **until I go
  ghost**, and shows a one-screen summary of what each audience will see. Timers only ever
  move toward ghost (accounts §14.3); precise and live grants keep their own end (≤ 24 h, §5).
- The master toggle itself lives in core (strip chip, accounts §14); this app renders it on the map and
  in its sheet and never keeps a second state.

## 5. Per-friend, group and field sharing

This app **consumes** the core data-class registry and visibility rule (accounts §14.1–§14.5:
audience × class × detail × window) and redefines nothing. What it adds is the sheet that edits grants for the classes
it declares, and their rendering:

| Class (registry) | Fields this app uses | Precision levels | Expiry |
|---|---|---|---|
| `presence` | status word, last-seen time | — | any |
| `location` | position, heading | none · coarse (≈ ±3 km) · place · precise · live | precise and live **always end, ≤ 24 h**; others may be indefinite |
| `vehicle_card` | §2.2 fields | basic · with plate | any |
| `live` | owner-picked VSS signals | — | follows `location` if both granted on a ride |
| `trips`, `faults` | summaries; counts or codes | summary · full; on | any; traces follow `location` |

- Audiences: me, person (contact), group, household; public later (registry).
- **Ask at the moment of use** (research C2): starting a ride offers "Share live position with
  this ride until it ends?"; sharing a vehicle offers a duration (1 h, end of trip, end of
  day, until I stop where the class window allows).
- **No one can raise my precision**; only my own SOS or crash alert sends a precise position to
  my safety contacts, logged (registry rule). Nothing here pops a ghost.
- Enforcement is at the source (the answering device and the router), not in this UI.

## 6. Group drives, convoys and transports

### 6.1 Rides

A ride (a core group of kind ride: members, window, route; talk and channels in Social) is the only unit for **live** precise
position. During the ride the map gains a **convoy layer**: members' pins, leader and sweep
badges, distance to leader and to sweep, a meeting point. At **ride end** (or its window's
end, at most 24 h) sharing stops on every link and the convoy positions held on my device are
**deleted** (speedometer teardown C8). Ride summaries belong to Trips and Social.

### 6.2 Routes and precision

- Positions arrive by **pull** over shares (`/peer/v1`, LAN, Tailscale, relay) and by
  **push** from the Social link router's `social/inbox/position` (mesh transports §5). The
  peer layer merges by peer: **freshest wins**, each dot keeps source and age.
- Outbound, this app never transmits; the router sends `position`/`telemetry` only when the
  registry says the audience may see them, on the link the class rules allow.
- **Meshtastic precision mapping** (ADR-0038 §5; social research D9): `none` → precision 0
  (not sent); `coarse` → **13 bits** (≈ 2.9 km); `place` → coarse on LoRa; `precise` →
  not sent on LoRa unless on a ride; `live` (a ride) → full precision on the ride's
  private channel only. MeshCore follows the same table when its bridge exists. Rates stay
  ADR-0038 §4 (≥ 60 s; 2 min moving).
- Inbound mesh positions are untrusted data, retained with expiry (module-bus spec §16) and
  **not written to my logbook**; they fade from the map when the retained message expires.

## 7. Head units and driving

Per the lockout positions (driver-distraction rules §7.1 item 9 and Decide D5):

| Display and state | What Vehicles & Map shows |
|---|---|
| Head unit, **Moving** | **No other vehicles by default.** If the driver opted in for an active ride: convoy members as **plain markers** (no names, avatars, photos or plates), ≤ 6, in the shell's `map` template, plus distance to leader/sweep as a `tiles` value. No lists, no garage cards, no sheet |
| Head unit, Moving, passenger view | Unchanged: other people's vehicles are non-driving content (UK reg 109), so they are **never** unlocked on a driver-facing screen; **Open on phone** instead |
| Head unit, Idling with Park evidence, or Parked | Full map and lists; no text entry while Idling without Park evidence |
| Phone, desktop, cloud | Full app; the phone keeps the shell's Moving banner |

Message or arrival alerts from riders use `alert_card` with no content ("Convoy: a member
stopped"). Task depth ≤ 3 on head units.

## 8. Viewers without Ostler (later)

A Glympse/Beacon-style **relay link** (research D4): an unguessable, expiring URL showing
position, ETA and route so far, no vehicle data, **at most 24 h**, revocable, audited, ended
by ghost. It needs the relay (accounts P3) and an ADR-0029 §7 amendment, since shares today are
device-to-device. Not before phase V5.

## 9. Manifest sketch

```jsonc
{ "id": "ostler.vehicles", "name": "Vehicles & Map", "trust": "first_party",
  "source": { "repo": "https://github.com/openostler/ostler-app-vehicles",
              "license": "AGPL-3.0-or-later", "publisher": "openostler" },
  "entry": { "kind": "bundled", "module": "@ostler/app-vehicles" },
  "hosts": ["head_unit", "phone", "desktop", "cloud"],
  "requires": { "product": ["ostler", "diagnostics"], "api": ["garage.read", "peer.read"] },
  "contributes": { "slots": [ { "slot": "more:vehicles", "view": "map", "order": 20 },
                              { "slot": "home:card", "view": "nearby_card" } ] },
  "actions": [],
  "views": [
    { "id": "map",     "driving": { "parked": "full", "idling": "full",
                                    "moving": { "template": "map", "layer": "convoy_markers" } } },
    { "id": "list",    "driving": { "parked": "full", "idling": "full", "moving": false } },
    { "id": "vehicle", "driving": { "parked": "full", "idling": "full", "moving": false } } ],
  "permissions": { "data": ["presence", "location", "vehicle_card", "live", "trips", "faults"],
                   "notifications": true, "storage": "memory" } }
```

`more:vehicles` and `home:card` are new slot names (platform change, Decision 7, added to
app-model §4.2 by its §14.7; Social adds `more:social` the same way); `storage:
"memory"` means peer data is never written to disk.

## 10. Compliance

| Rule | How this design meets it |
|---|---|
| **ADR-0009** location stays on the device | My location leaves only through an explicit, time-bounded grant; peers' data is pulled, held in memory, deleted at revoke or ride end; the relay carries end-to-end TLS it cannot read |
| **ADR-0029** shares, privacy, social opt-in | Grants come only from the core registry; no contact upload, no third-party login, no directory; ghost default |
| **ADR-0033** remote paths read-only | No actions in the manifest; nothing a friend or mesh sends can act on my car; Read only |
| **ADR-0036** identity | No VIN (masked or not), `vid` or plate on any card, map, link or air field by default; plate only by owner tick, never on a mesh |
| **ADR-0038** mesh | Remote path; coarse by default; full precision only on a ride's private channel; mesh ids bound, never derived |

## 11. Phases

| Phase | Ships | Depends on |
|---|---|---|
| **V0 Seams** | registry classes used; slots `more:vehicles`, `home:card`; shell `map` template | accounts §14 registry; app model UA; U1 templates |
| **V1 Browse** | list, garage cards, my card editor with EXIF strip, map with last-known positions over LAN/Tailscale shares, ghost chip and visibility sheet, "Seen by" | accounts P2 (P3 for Tailscale) |
| **V2 Rides** | convoy layer, ask-at-start, ride-end deletion, head-unit convoy markers | Social rides (accounts P4) |
| **V3 Mesh** | router positions, Meshtastic precision table, source and age badges | Social router; `ostler-bridge-meshtastic` |
| **V4 MeshCore** | same table over MeshCore | ADR-0038 amendment (MeshCore bridge) |
| **V5 Link viewers** | relay link ≤ 24 h | relay; ADR-0029 §7 amendment |

## 12. Tests

- With ghost on, no `presence`, `location` or `live` value leaves through `/peer/v1` or any
  router link (fake router, all links).
- A precise or live grant without an end, or ending after 24 h, is refused.
- A shared photo has no EXIF/XMP/IPTC block and differs byte-wise from the original.
- No VIN, masked VIN, `vid` or plate (unless ticked) in any card, list, map tile or air frame.
- Coarse positions over Meshtastic are encoded at 13 bits; none emits nothing.
- Ride end deletes convoy positions and stops outbound positions on every link.
- Head unit Moving: no peer markers unless opted in to an active ride; then no names or images.
- Revoking a share removes the vehicle from list and map on the next render, with no disk copy.

## Changelog

- 2026-10-07: v0.1, first draft for owner review (ecosystem drafts).
- 2026-10-07: v0.2, approved by the owner on 2026-10-07 ("approve all"): every §13 decision
  answered as recommended (alternatives not chosen); slots `more:vehicles` and `home:card`
  added to app-model §4.2 (§14.7); ADR-0038 §2 narrowed so inbound mesh positions are never
  written to the logbook (ADR-0038 amendment item 10).

## 13. Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all"). Each recommendation below is
the decision; each alternative was not chosen.

1. **One add-on for browsing and the map?** Recommend: yes, `ostler-app-vehicles` opens on
   the map with the list as its bottom sheet. Alternative: a separate core map destination.
2. **What does ghost hide?** Recommend: presence, location and live signals; non-live grants
   stay. Alternative: ghost hides every grant, card included.
3. **Visible timers.** Recommend: 1 h, 24 h, until I go ghost (precise and live still end
   within 24 h). Alternative: add 3 h and end of day, as Snap and Find My do.
4. **Masked VIN on friends' cards?** Recommend: never shown; plate hidden by default.
   Alternative: let the owner tick the masked VIN per audience.
5. **Other vehicles on the head unit while Moving.** Recommend: none, except opted-in convoy
   members of an active ride as plain markers. Alternative: none at all.
6. **Inbound mesh positions: recorded or not?** Recommend: kept only as expiring retained
   state, never written to the logbook (narrows ADR-0038 §2 "recorded"). Alternative: record
   them in the session as untrusted data, as ADR-0038 §2 says today.
7. **New slots `more:vehicles` and `home:card`.** Recommend: add both by platform change
   (as Social adds `more:social`). Alternative: put Vehicles & Map under the Garage page only.
8. **Viewers without Ostler.** Recommend: later (V5), relay link ≤ 24 h, position, ETA and
   route only. Alternative: never; viewers must install Ostler.
9. **Card fields and live stats.** Recommend: add mods, "about" and a mileage band to
   `vehicle_card` as separately ticked fields, and let the owner pick ≤ 6 VSS signals per
   audience for `live`. Alternative: the registry's `vehicle_card` as is and fixed `live`
   presets (temperatures, fuel range).
