---
title: "ADR-0043 — GPS and logs in shared trips: routes only after trimming, with preview; full logs and diagnostics only as verified hand-overs"
area: decisions
status: locked
version: 1.0
updated: 2026-10-07
depends_on: [CONSTITUTION.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0041-brain-ed25519-signing.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, specs/2026-10-07-trip-sharing-design.md, specs/2026-10-06-accounts-sharing-design.md, references/research/trip_and_log_sharing.md, references/research/dmd_hub_features.md, references/research/community_hub_architecture.md]
summary: >
  Accepted: approved by the owner on 2026-10-07 ("approve all", DMD round). The ADR that ADR-0009 asks for before any community upload carries GPS. A shared or published trip may carry a route only at level L1 (or L2 with L1 ticked), only after the ends trim (500 m default, never under 200 m), privacy zones (at least 500 m, fixed random offset), simplification and the removal of point timestamps, with stats from the visible trace only, and only after the owner has seen a preview of exactly what leaves. A route reaches the `public` audience only by an explicit publish act at least 24 h after the trip. Full logs (L3) and diagnostics bundles (L4) are hand-overs, never registry grants: a scrubbed `ostler.share/1` bundle that passes `ostler share verify`, delivered by file, relay link with the key in the URL fragment, or an end-to-end encrypted hub help thread to named helpers; to any public destination they carry no location and relative time only. Bundles are not signed with the Brain key. The `captures` class was the alternative, not chosen.
---

# ADR-0043 — GPS and logs in shared trips

- **Date:** 2026-10-07
- **Status:** accepted. Approved by the owner on 2026-10-07 ("approve all", DMD round;
  decision list items 20–32). Completes
  [ADR-0009](adr-0009-session-logbook-and-location.md)'s condition ("community uploads never
  include GPS channels unless a later ADR adds a per-upload opt-in, with trimmed ends and a
  preview") without changing ADR-0009's default: real sessions still stay on the device.
  Detail in the approved [per-trip sharing spec](../specs/2026-10-07-trip-sharing-design.md).
  Evidence: [trip and log sharing](../references/research/trip_and_log_sharing.md),
  [DMD Hub features](../references/research/dmd_hub_features.md) §5 and
  [community hub architecture](../references/research/community_hub_architecture.md) §5–§7.

## Context

- The owner asked for trips to be shared "with different permission levels of what data is
  shared", including "a full log, for help decoding, or diagnostics". Sharing to friends,
  groups, anyone with a link and, through Ostler Community, the public all need a route and,
  for help, a raw log.
- ADR-0009 forbids GPS in community uploads until an ADR adds a per-upload opt-in with
  trimmed ends and a preview. None exists.
- Research on endpoint privacy zones recovered the protected place for up to 85 % of zones
  from stats over the hidden part, the street grid and entry points; re-rolled zones helped
  the attacker; speed alone plus a known start recovers routes (research §3).
- The core registry (accounts §14.1) refuses raw captures as a data class, so a full log
  cannot simply be a grant. Precise and live location are capped at 24 h (§14.5), which a
  finished, cleaned route does not need.
- ADR-0036 keeps the VIN and identity data on the device on every path; the Brain's Ed25519
  key ([ADR-0041](adr-0041-brain-ed25519-signing.md)) is stable per device.

## Decision drivers

- Private by default; every widening is an explicit, previewed act by the data owner.
- Nothing about the hidden part of a trip may be computable from what is shared.
- One scrubber and one verifier for every path, so no path is weaker than another.
- Raw logs help decoding only if they reach a helper; they must not become a public dataset.
- No share may link back to a device across bundles.

## Decision

1. **Routes (GPS) may leave only as an L1 route.** A shared trip carries location only at L1
   (or L2 with L1 ticked), and only after, in order: the **ends trim** (first and last 500 m
   along the track by default, owner-adjustable to 1.5 km, never below 200 m), **privacy
   zones** (radius at least 500 m, centre offset once at random by up to half the radius and
   never re-rolled), **stats recomputed from the visible trace only**, **simplification**
   (about 10 m) and **removal of point timestamps**. The time basis is the day only.
2. **L3 Full log and L4 Diagnostics bundle are hand-overs, never grants.** They are built as
   an `ostler.share/1` bundle, scrubbed (ADR-0036 widened: pack identity declarations, the UI
   spec §8.3 list on every transport, seed/key exchanges, ISO-TP reassembly, and a VIN-pattern
   **block**), and delivered only by **file**, **relay link** with the key in the URL fragment,
   or a **hub help thread** that is end-to-end encrypted to **named helpers** (key in each
   helper's URL fragment; default 7 days, at most 30; at most 3 downloads). A pack's
   maintainers may receive one through an issue form the owner fills. The registry keeps
   refusing raw captures as a class.
3. **Public destinations.** A route reaches `public` only by an explicit **publish** act, at
   least **24 h after the trip ended**, with the preview shown. L3–L4 to any public
   destination (a public issue, a public thread) carry **no location** and **relative time**,
   whatever the owner ticked. L2 never goes to `link` or `public`.
4. **The gate.** Every path, grant or hand-over, runs the redaction pipeline on a copy and
   passes **`ostler share verify`** on the final bytes before anything leaves; a bundle that
   fails is not written. The preview the owner sees is rendered from that output, not from a
   UI imitation. Real date and time may be kept in L3–L4 only for one named person.
5. **No device signature.** Bundles are **not signed with the Brain key**; integrity comes from
   per-file SHA-256 in `share.json`. A relay link may sign with a key generated for that one
   bundle and then discarded. Every id is re-minted per bundle.
6. **Derived data only flow back.** A bundle is never committed and never republished by a
   hub. With the owner's separate consent (off by default) decoded definitions and short
   labelled fixture snippets derived from it are published under CC BY-SA 4.0
   ([ADR-0012](adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md)). Helpers send recording
   recipes, never remote actions ([ADR-0033](adr-0033-action-categories-and-approvals.md) §6).

## Confirmation

- Tests in the per-trip sharing spec §16: trims and zones on a recorded fixture trip, zone
  offsets stable across shares and restarts, stats equal to those of the visible fixes alone,
  no GPS, `Utc`, heading or altitude without a route, the synthetic-VIN injection on recorded
  K-line and CAN ISO-TP fixtures (built at run time so no VIN literal is committed), one
  failing fixture per verifier check, L3 or L4 refused as a grant, L2 refused for `link` and
  `public`, a public route refused before trip end + 24 h, and no bundle carrying the Brain's
  key id.
- CI runs `ostler share verify` over every share fixture.

## Consequences

- ADR-0009's condition is met for L1 routes; ADR-0009 itself is unchanged and gains a pointer.
- The accounts spec gains a `route` detail on the `location` ladder, a `link` audience, the
  `public` audience brought forward for the hub by explicit publish, live-trip grant options
  and link controls (its §15 amendment, approved).
- Packs gain an `identity` declaration (ADR-0036 Consequences); the platform's scrub table
  widens and is shared by the recorder, exports and shares.
- A K-line `USER0` pcapng dissector becomes useful to helpers (open question in the spec).

## Alternatives considered

- **A `sensitive` `captures` class** (scrubbed, never in a preset, audience one person or the
  decode project only, at most 30 days, never `link` or `public`). Not chosen (the owner
  approved the recommendation, decision list item 21): it reverses accounts §14.1 and puts raw bytes behind a live pull path; recorded as the
  owner's alternative in the spec's Decision 2.
- **Trim only near saved places** (Strava's default). Rejected: most users never set a place.
- **Re-roll zone offsets per trip.** Rejected: more samples help the attacker.
- **Hash or mask the VIN in bundles.** Rejected by ADR-0036.
- **Sign bundles with the Brain key.** Rejected: links every bundle to one device.
- **Keep ADR-0009's ban.** Rejected: it blocks the owner's ask entirely.

## Relation to other ADRs

- **ADR-0009:** fulfils its "later ADR" condition; its default stands.
- **ADR-0029 / accounts spec:** extends the registry (route detail, `link`, `public`), keeps
  the 24 h cap for precise and live location.
- **ADR-0036:** applied on every share; the scrub is widened, never relaxed.
- **ADR-0041:** the Brain key is not used for shares.
- **ADR-0012, ADR-0033:** derived data under CC BY-SA 4.0; helpers get no actions.

## Changelog

- 2026-10-07 — v0.1, proposed (DMD round), drafted with the per-trip sharing spec.
- 2026-10-07 — v1.0, accepted: approved by the owner on 2026-10-07 ("approve all", DMD
  round); the recommendations are the decision, the `captures` class and the other
  alternatives were not chosen.
