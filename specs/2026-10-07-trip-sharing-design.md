---
title: "Per-trip sharing — five share levels, redaction, the ostler.share/1 bundle, the verifier and help me decode or diagnose — design"
area: specs
status: stable
version: 0.4
updated: 2026-10-07
depends_on: [references/research/trip_and_log_sharing.md, references/research/dmd_hub_features.md, references/research/community_hub_architecture.md, decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0011-no-demo-mode-live-only-recording-place-names.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0029-accounts-multi-vehicle-sharing-and-social.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0041-brain-ed25519-signing.md, decisions/adr-0042-ecosystem-small-core-addons-are-the-product.md, decisions/adr-0043-gps-and-logs-in-shared-trips.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md]
summary: >
  Approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3, answering the owner's ask that a single trip can be shared at a chosen data level, up to a full log for decoding help or a diagnostics bundle. Five levels per trip: L0 Card (stats only, no map; max speed hidden on public cards), L1 Route (ends trimmed 500 m by default and never under 200 m, privacy zones of at least 500 m with a fixed random offset, simplified, no point timestamps, stats from the visible trace only), L2 Telemetry (chosen VSS signals on relative time), L3 Full log (the complete recording with the raw tap, scrubbed) and L4 Diagnostics bundle (faults, freeze frames, module info, scrubbed). L0–L2 are grants in the core registry; L3 and L4 are hand-overs, never grants (file, relay link with the key in the URL fragment, or a hub help thread), each passing `ostler share verify` first. Specifies a level × rule redaction table (R1–R16), privacy-zone maths, time handling (day, relative, real only to one person), id re-minting, a widened identity scrub with ISO-TP reassembly and a VIN-pattern block tested on recorded fixtures, the `ostler.share/1` zip and its `share.json` schema (hashes and a redaction record, not signed with the Brain key), DMD-style link controls, preview, expiry, revoke and audit, the seven-step help-me-decode or diagnose flow with CC BY-SA 4.0 contribution consent, where each piece lives (core platform, Trips, Diagnose, Decode lab, `ostler-app-hub`), phases, tests and the decisions for the owner, all answered as recommended (the `captures` class alternative not chosen). Amended 2026-10-07 (openness round, ADR-0047): the floors on the owner's own trips (ends trim, zone radius, short trips, real time, public delay, L2 by link, public L3 for decoding projects, VIN in a named L4 bundle) become defaults with warnings; the verifier and identity scrub are unchanged.
---

# Per-trip sharing — design

> **Amended 2026-10-07 (openness round), approved by the owner on 2026-10-07 ("this should
> be an open system", then "apply the loosenings";
> [ADR-0047](../decisions/adr-0047-openness-round.md)):** the privacy floors on the owner's
> own trips become defaults with a warning: the ends trim may go below 200 m, to 0 ("this
> reveals where you start and stop", §5.1); a privacy zone may be smaller than 500 m (§5.2);
> a trip under 1 km may be shared above L0 after a warning (§3); "Keep real date and time" is
> allowed for any recipient after a warning (§6); a scrubbed L3 bundle may be published for
> an open decoding project, still through the verifier (§3); L2 telemetry may go to `link`
> with an expiry (accounts §15.2); the public route delay is the owner's (0–24 h); the VIN
> may go in an L4 bundle to one named person (§2). No public feed, score or points stays this
> core feature's scope, not a platform rule (§1). The verifier, identity scrub of everyone
> else's data and the hand-over model are unchanged.

**Status: approved by the owner on 2026-10-07 ("approve all", DMD round), v0.3.** Every item
in [Decisions for the owner](#decisions-for-the-owner) is answered as recommended. It
answers the owner's ask: *"we should allow specific trips to be shared with different
permission levels of what data is shared. So for example a user can share a full log, for help
decoding, or diagnostics on their car/motorcycle."* Evidence and prior art are in
[trip and log sharing](../references/research/trip_and_log_sharing.md) (redaction rules R1–R16,
bundle, verifier, help flow), [DMD Hub features](../references/research/dmd_hub_features.md)
§2.2, §2.6 and §5 (link controls, live trip options) and
[community hub architecture](../references/research/community_hub_architecture.md) §5–§7. This
spec does not repeat them. Its companions in the same round are
[ADR-0043](../decisions/adr-0043-gps-and-logs-in-shared-trips.md) (accepted: GPS in shared and
community trips, and the hand-over rule for L3–L4), the approved amendment to the
[accounts spec](2026-10-06-accounts-sharing-design.md#15-amendment-2026-10-07-dmd-round-approved-trip-sharing-in-the-registry)
§15 (registry pieces) and the approved amendment to the
[UI architecture spec](2026-10-06-ui-architecture-design.md#13-amendment-2026-10-07-dmd-round-approved-sharing-screens-places-and-map-theme)
§13 (screens).

## 1. Scope

Two jobs that look alike and are not:

1. **Show a trip** to a friend, a group, anyone with a link or, after publishing, the public
   (the DMD Hub and Strava side). Levels L0–L2. Live, revocable, audited **grants** on the
   core registry (accounts §14.1–§14.4).
2. **Hand over a log** so somebody can help decode the car or diagnose a fault. Levels L3–L4.
   A sealed, scrubbed, verified **bundle** sent once to a named helper, a pack's maintainers or
   a hub help thread. Raw captures stay outside the registry (accounts §14.1).

**Non-goals.** No public feed for strangers, no score, no points in per-trip sharing (Ostler
Community positions, [ecosystem](../docs/ecosystem.md)); an add-on may offer them, opt-in
(*amended 2026-10-07, openness round*). No second recorder: a share is a view of the ADR-0009
session (DMD Avoid 7). No upload by default and no silent upload targets. No remote actions
for helpers: remote paths stay read-only ([ADR-0033](../decisions/adr-0033-action-categories-and-approvals.md)
§6). Live location sharing during a drive stays with the Vehicles & Map add-on; this spec only
adds the live-trip grant options it uses (§12).

## 2. Rules already in force

Binding on every path; the research's §2 has the detail.

- **ADR-0009:** real sessions stay on the device; community uploads carry no GPS unless an ADR
  adds a per-upload opt-in with trimmed ends and a preview. ADR-0043 (accepted) is that ADR.
- **ADR-0036 §3 and §5:** every export, share, contribution and support bundle scrubs
  identity data to the fixed placeholder whatever the install option; the VIN does not leave
  by default (not even masked or hashed); *amended 2026-10-07 (openness round):* the owner may
  include it in an L4 bundle to one named person, with a cloning-risk warning; raw car
  captures are never committed.
- **Accounts §14:** default audience `me`; ghost by default; precise and live location
  ≤ 24 h; every grant has an expiry, a revoke and an audit; raw captures and Decode evidence
  are never a class.
- **Node-source spec §7:** `unframed` tap records are dropped from every export; the
  `scrubbed` flag is never cleared.
- **UI spec §8.3:** the scrub list (VIN, serials, EKA codes, seed/key pairs; GPS, time and
  odometer coarsened) and the CI rule that fails on a VIN pattern under `tests/`.

## 3. The five levels

A **share** is one trip (or a marked time range inside it) at one level, to one audience, for
one window. Each level is a strict superset of the one above it for what it reveals, except
that L2–L4 carry **no location** unless L1 is also ticked (and L3–L4 never to a public
destination, ADR-0043).

| Level | Name | Contains | Never contains | Kind | Audiences |
|---|---|---|---|---|---|
| **L0** | **Card** | vehicle card basic (make, model, year, engine; nickname if ticked; photo re-encoded, EXIF stripped); trip **day**; a **region label** (GeoNames admin-2, e.g. "Derbyshire"); visible distance (1 km), visible duration (5 min), moving time (5 min); average speed (5 km/h); max speed **only if shown** (hidden by default on `link` and `public`, R15); faults-seen count if ticked; `card.png` | any map, trace, place names finer than admin-2, start time, altitude or elevation, plate (unless ticked), signals | grant | me, person, group, household, link, public (explicit publish) |
| **L1** | **Route** | L0 plus the **trimmed, simplified trace** with no point timestamps (§5), elevation profile and gain (10 m) of the visible trace, start and end **region** labels, stats recomputed from the visible trace (distance 0.1 km, duration 1 min) | trimmed ends, anything inside a privacy zone, point times, start and end places, the hidden part's length | grant (`location` `route`) | as L0; `public` only by explicit publish, by default ≥ 24 h after the trip ends (owner-set 0–24 h) |
| **L2** | **Telemetry** | the chosen decoded **VSS signals** (picker; default speed, rpm, coolant) as time series on **relative time** (t = 0 at the first visible sample), faults seen with freeze frames, replay of those channels; route only if L1 is also ticked | GPS channels, `Utc`, heading and altitude (unless L1), unpicked signals, raw bytes, events, notes (unless ticked) | grant (`trips` `full` with a signal subset + `faults`) | me, person, group (a hub club is a group), household; `link` with an expiry and a warning (owner opt-in, amended 2026-10-07); **never `public`** |
| **L3** | **Full log** | every decoded channel, the **raw tap** per bus (`pcapng`, plus `candump` for CAN buses), state events (typed, free text dropped), notes marked shareable if ticked, `meta.json` re-minted; relative time | VIN or any identity reply, `unframed` records, audio, private notes, device ids, network identity; location unless ticked to one named person | **hand-over** | one named person, a pack's maintainers, named helpers on a hub help thread; or, by the owner's explicit publish with a warning, **public** for an open decoding project (location never included; the verifier still runs; amended 2026-10-07) |
| **L4** | **Diagnostics bundle** | faults, freeze frames, readiness, the scan report, **module info** (module names, part and software numbers that are not serials, protocol and link stats), pack, platform and firmware versions, device manifests (re-minted), link and gap stats, the redacted platform log tail and config; plus L2 or L3 channels if ticked | as L3; serials, EKA codes, seed/key pairs | **hand-over** | one named person (a mechanic), a pack's maintainers, named helpers on a hub help thread |

**L0–L2 are grants** in the registry: pulled over `/peer/v1`, LAN, Tailscale or the relay,
revocable at once, audited per pull. **L3–L4 are hand-overs, never grants** (ADR-0043 §2): a
bundle is built once, verified and delivered by file, relay link or hub help thread (§10).
Every level, grant or not, is built through the same pipeline (§4) and passes the verifier
(§9) before its first byte leaves; for a grant the pipeline runs on every pull, on the
serving device, the way `/peer/v1` filters today.

**A short trip** whose visible trace (after §5) is under 1 km is shared at L0 by default; the
card reads "under 1 km" and no duration. *Amended 2026-10-07 (openness round):* the owner may
share it at a higher level after a warning that a short trace points to its ends.

## 4. Redaction pipeline: level × rule

Applied in this order, **on a copy, never in place** (the recording is never changed). R1–R16
are the research's rules with this spec's settings; "—" means the rule has nothing to act on
at that level because the data is not included.

| # | Rule | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| R1 | **Identity scrub** to the ADR-0036 placeholder: pack identity declarations + UI spec §8.3 list (§8) | — | — | yes | yes | yes |
| R2 | **ISO-TP-aware scrub**: reassemble multi-frame replies; placeholder the payload in every first and consecutive frame (§8.2) | — | — | — | yes | yes |
| R3 | **VIN-pattern block** and declared broadcast identity frames: a match **blocks** the share (§8.3) | yes¹ | yes¹ | yes | yes | yes |
| R4 | Drop `unframed` records | — | — | — | yes | yes |
| R5 | **Ends trimmed** and **privacy zones** cut (§5) | n/a² | yes | if L1 ticked | if location ticked | if location ticked |
| R6 | **Stats from the visible part**, then rounded (§5.4) | yes | yes | yes | yes | yes |
| R7 | **Trace simplified** (RDP ε = 10 m), point timestamps removed, coordinates to 5 decimals | — | yes | if L1 ticked | — | — |
| R8 | **No GPS unless a route is granted**: drop `GPS_*`, `Utc`, heading and altitude | yes | n/a | yes | yes | yes |
| R9 | **Time** (§6) | day | day | relative | relative³ | relative³ |
| R10 | **Fresh ids** (§7) | yes | yes | yes | yes | yes |
| R11 | **Odometer and hours** coarsened to 1,000 km and 100 h, freeze frames included | — | — | yes | yes | yes |
| R12 | **People**: names, user ids and contacts → "driver"; plate hidden unless ticked; photos re-encoded, EXIF and PNG text chunks stripped | yes | yes | yes | yes | yes |
| R13 | **Free text**: notes only if marked shareable *and* ticked; audio never (ADR-0010); events kept by type, free-text fields dropped | — | — | opt-in | opt-in | opt-in |
| R14 | **Network identity**: MACs, SSIDs, Tailscale names, IPs, certificate fingerprints, tokens and peer keys → `**REDACTED**` by declared keys plus patterns | — | — | — | yes | yes |
| R15 | **Max speed** hidden on `link` and `public` cards by default; the owner may show it per share | hidden⁴ | hidden⁴ | shown | shown | shown |
| R16 | **Verifier** passes (§9), or nothing leaves | yes | yes | yes | yes | yes |

¹ Over the card text, vehicle nickname and any free text the card carries. ² L0 shows no map,
but R6 still uses the trimmed, zone-cut trace so an L0 and an L1 of the same trip agree.
³ "Keep real date" may be ticked only for one named person (§6). ⁴ Hidden by default for
`link` and `public`; shown by default to a person, group or household.

**Public destinations** (a `public` publish on a hub, a public help thread, a public pack
issue) **force** L3–L4 to location none and relative time whatever the ticks (ADR-0009,
ADR-0043 §3).

## 5. Trimming, privacy zones and stats

### 5.1 Ends trim (every trip, R5)

Let the trip's fixes be p₀ … pₙ with along-track distance s(i) = Σ haversine(p_{k−1}, p_k)
over k ≤ i, after dropping fixes with HDOP > 5 or a jump implying > 300 km/h, and S = s(n).
Hide every fix with **s(i) < T_start** or **s(i) > S − T_end**. Defaults **T_start = T_end =
500 m**; the owner may set 0 to 1,500 m in More → Places. Below 200 m the sheet warns "this
reveals where you start and stop" (*amended 2026-10-07, openness round*; 200 m was a fixed
floor). The cut point is interpolated on the segment so the visible trace starts exactly at
s = T_start (no partial-segment leak).

### 5.2 Privacy zones (saved places, R5)

- A **privacy zone** is a saved place (home, work, a friend's house) with a radius **r**
  (choices 500 m, 1 km, 1.5 km, 2 km; default 1 km for "Home"; a smaller custom radius is
  allowed after a warning, *amended 2026-10-07, openness round*). It lives in core (More →
  Places) and every class with location reads it (Trips, Social, Vehicles & Map, hub
  publishing).
- **Fixed random offset.** When the zone is saved, a centre offset **o** is drawn once from a
  uniform disc of radius **0.5 r** (CSPRNG) and stored. The zone's circle is centred on
  **c′ = c + o**, so the true place is always at least 0.5 r inside the boundary. The offset
  is **never re-rolled** (re-rolling gives an attacker more samples, research §3); editing the
  place keeps it unless the place moves by more than r, which draws a new one and says so.
- **Cut.** Every fix with haversine(p, c′) < r is hidden, at any point in the trip, not only
  the ends. A trip that crosses a zone mid-way becomes **separate segments with no line
  across the gap**. Hidden fixes contribute nothing to any stat.
- **Residual risk, stated in the UI and to the owner:** many shared trips that enter one zone
  let an attacker fit the circle and find c′; the true place is then within 0.5 r of it
  (about 500 m with the default home zone). Larger zones and fewer public routes reduce it.
  Random-polygon zones (Komoot) are a recorded alternative (Decision 6).

### 5.3 Simplify (R7)

Project the visible segments to a local east-north plane; Ramer–Douglas–Peucker with ε = 10 m;
round coordinates to 5 decimal places (about 1 m); drop every point timestamp, speed, heading
and accuracy field. The GPX carries `<trkpt>` with `lat`, `lon` and optional `<ele>` (L1
only, 1 m) and no `<time>`; the GeoJSON carries a `MultiLineString` and no properties per
point.

### 5.4 Stats from the visible trace only (R6)

All figures are computed from the **visible, unsimplified** fixes (after §5.1 and §5.2,
before §5.3), then rounded. Nothing reports the hidden part, its length or the trip's total.

| Figure | Computed from | L0 rounding | L1–L4 rounding |
|---|---|---|---|
| Distance | Σ segment lengths of visible fixes | 1 km | 0.1 km |
| Duration | Σ (last − first) per visible segment | 5 min | 1 min |
| Moving time | visible time at ≥ 5 km/h | 5 min | 1 min |
| Average speed | unrounded distance ÷ unrounded moving time | 5 km/h | 1 km/h |
| Max speed (if shown) | max over visible samples of the trip's speed source | 5 km/h | 1 km/h |
| Elevation gain | visible altitude, 30 s median filter, sum of rises ≥ 3 m | — | 10 m |
| Stops | visible stops ≥ 60 s | — | count |

Per-figure speed source (ECU or GPS) is kept as in Trips §12.2. A trip with no GPS fixes
(K-line only) has no location: L0 shows duration from the recording's relative time and no
distance unless an ECU road-speed signal exists, in which case distance integrates that
signal over the whole trip less its first and last 2 minutes (the time analogue of the trim,
since speed plus a known start can recover a route, research §3 rule 4).

## 6. Time handling (R9)

| Basis | Levels | What changes |
|---|---|---|
| **day** | L0, L1 | Only the local calendar date of the first visible sample. No start time, no weekday-time pairs, no point times. A `public` route is publishable only ≥ 24 h after the trip ended and still shows the day only |
| **relative** | L2, L3, L4 | t = 0 at the first visible sample. `Utc` dropped; `Interval` rebased; tap `t_us` rebased; tap `time` events rewritten to the same base with `utc_ns` removed; pcapng timestamps written as 1970-01-01T00:00:00Z + t; candump `(sec.usec)` from 0; `meta.json` start and end become `0` and the duration; zip entry times fixed at 1980-01-01 00:00 |
| **real** | L3, L4, one named person only | The owner ticks "Keep real date and time" in the sheet, which shows the recipient's name; for a link to several people, a hub thread, a pack issue or a file (no known recipient) it needs a second confirm with a warning (*amended 2026-10-07, openness round*; was refused) |

The day itself is identifying when combined with an event (a club ride); the sheet says so
for `link` and `public`.

## 7. Fresh ids (R10)

Every id that is stable across shares or encodes a time is replaced per bundle:

| Id | Today | In a share |
|---|---|---|
| Session id | `YYYYMMDDTHHMMSSZ` (the start time) | `s-` + 16 random base32 chars |
| Tap file ULIDs | creation time in ms + random | `tap/bus<N>` by bus ordinal |
| Node `device`, `boot_id` | stable hardware id, boot counter | `node-1`, `boot-1` … by order of first appearance |
| `vid` | stable local vehicle id | `vehicle-1` |
| Relay ids, peer key fingerprints, hub ids | stable | dropped |
| User ids | local user id | `driver`, `driver-2` |
| Bundle id | — | 128-bit CSPRNG, never derived from any of the above |

The mapping from new ids back to the real ones is kept **only on the owner's device**, in the
share's audit entry, so the owner can find the source trip; it is never in the bundle, the
relay or the hub. Module addresses, CAN ids and service bytes are bus facts, not identity, and
stay.

## 8. The widened identity scrub (R1–R3)

The Brain's tap check today (`IdentityScrub` in `openostler.node.tap`) knows K-line SIDs `5A`
and `49` and CAN prefixes `49`, `5A`, `62 F1 90` and `62 F1 8C` (research §2 gap). The share
scrubber **extends that one table**; the recorder, every export and every share path use it,
so there is one scrubber (ADR-0036 §3).

### 8.1 Sources of identity

1. **Pack identity declarations** (new, a pack contract field the platform owns; ADR-0036
   Consequences already names it). Proposed shape:
   `identity: {services: [hex], dids: [hex], local_ids: [{service, id}], broadcast_frames:
   [{bus, can_id, bytes}], seed_key: bool}`. The D2 pack declares, for example, its KWP
   identification local ids and the BCU's EKA and seed/key exchange (`27`/`67`).
2. **Platform list** (UI spec §8.3): OBD Mode 09 PIDs `02`, `04`, `0A` replies (`49 …`);
   UDS `62 F1 90` (VIN) and `62 F1 8C` (serial) on **every transport, K-line included**;
   KWP `5A 87` and `5A 90` (and any `5A` reply); SecurityAccess seeds and keys (`67 xx`
   with data, `27 xx` with data).

### 8.2 ISO-TP reassembly (R2)

For CAN buses: track ISO-TP per (bus, CAN id) on the diagnostic ids (`0x7DF`, `0x7E0`–`0x7EF`,
29-bit `0x18DA____`, and any pack-declared diagnostic id). Decide identity on the **reassembled**
message's service and DID (not only the first frame's first bytes, which a first frame with
a 12-bit length can push out of a naive check), then write the placeholder over the data bytes
of the **first frame and every consecutive frame** of that message in both `pcapng` and
`candump`, keeping the PCI bytes and lengths so the capture still parses. Flow-control frames
stay. A message that cannot be reassembled (lost frames) is scrubbed from its first frame to
the next first or single frame on that id.

### 8.3 VIN-pattern block (R3)

The verifier and the scrubber run a detector over **every file** in the bundle: ASCII windows
of raw payloads, of reassembled ISO-TP messages, of concatenated payloads per CAN id (for
broadcast frames that spell a VIN over several frames), CSV string columns, JSON values,
notes and card text. A match is `[A-HJ-NPR-Z0-9]{17}` with at least 3 digits and 3 letters,
or the vehicle's own masked-VIN prefix (WMI) followed by 14 VIN characters. A match **blocks**
the share; it is never silently cut. The block names the file, frame and offset. The way
forward is a pack declaration (the frame becomes identity, R1 scrubs it) or a reviewed
false-positive entry in the pack with a fixture, never a "send anyway" button.

### 8.4 Tests on recorded fixtures (ADR-0011)

- Fixtures are **recorded shapes**, not simulators: the node firmware's host-test tap
  fixtures, labelled K-line snippets from the D2 pack and a CAN ISO-TP capture from the
  generic OBD-II pack, already committed with placeholders.
- The CI rule (UI spec §8.3) forbids a VIN pattern under `tests/`. So a test **builds** a
  synthetic VIN at run time from fragments (no 17-character literal in the repo), injects it
  into a copy of the fixture as a Mode 09 reply, a `62 F1 90` multi-frame reply split across
  a first frame and two consecutive frames, a KWP `5A 90` reply, a declared broadcast frame
  and an undeclared broadcast frame, and asserts: the first four are scrubbed in `pcapng`,
  `candump` and `data.csv`; the undeclared one blocks the share naming the frame; every
  other byte is unchanged; the `scrubbed` flag is set and counted in `redactions`.

## 9. The bundle `ostler.share/1` and the verifier

### 9.1 Layout: `ostler-share-<8 random>.zip`

Stored entries (deflate), entry times fixed at 1980-01-01 00:00, no zip comment, no extra
fields, sorted paths, no directories beyond those below.

```
share.json           manifest (9.2)
README.txt           plain English: what this is, the level, what was removed, the licence
trip.json            summary after R6 (and the L0 card fields)
card.png             L0 image (re-encoded, no metadata)
track.geojson        L1, only when a route is granted
track.gpx            L1, only when a route is granted
data.csv             L2+: native logbook CSV after R1, R8, R9, R11 (only the picked signals at L2)
faults.json          L2+ and L4: faults, freeze frames, readiness
events.jsonl         L3+: events by type, free text dropped
notes.jsonl          L2+: shareable notes, only if ticked
tap/bus<N>.pcapng    L3+: scrubbed raw tap per bus (K-line LINKTYPE_USER0, CAN SocketCAN)
tap/bus<N>.candump   L3+: CAN buses only, `(sec.usec) iface id#data`
diag/versions.json   L4: pack, platform, firmware versions
diag/modules.json    L4: module info (names, part and software numbers, no serials)
diag/manifests.json  L4: device manifests, ids re-minted
diag/link_stats.json L4: link quality, gaps, lost and overflow counts
diag/log_tail.txt    L4: platform log tail, R14 applied
diag/config.json     L4: config, R14 applied by declared keys
```

### 9.2 `share.json`

| Field | Type | Notes |
|---|---|---|
| `format` | `"ostler.share/1"` | readers refuse other majors |
| `id` | 32 hex | 128-bit random |
| `level` | `"L0"` … `"L4"` | |
| `created_day` | ISO date | day only |
| `expires` | ISO date-time or null | the delivery path's expiry; null for a file |
| `pack` | `{id, version}` | |
| `platform_version`, `firmware_versions` | string, list | L4 lists every device's |
| `vehicle` | `{make, model, year, engine, market, kind}` | `kind` is car or motorcycle; no VIN, no masked VIN, no HMAC, no plate unless ticked |
| `time_basis` | `"day"` · `"relative"` · `"real"` | §6 |
| `location` | `"none"` · `"coarse"` · `"route"` | §5 |
| `trim` | `{ends_m, zones: count}` | never the zone positions or radii |
| `signals` | list of VSS paths | L2+ |
| `files` | `[{path, sha256, bytes, kind}]` | every file but `share.json` |
| `redactions` | `[{rule, count, detail}]` | e.g. `{rule: "R2", count: 6, detail: "ISO-TP frames scrubbed"}` |
| `verifier` | `{version, passed, ran_day}` | |
| `request` | `{kind: "decode" · "diagnose" · "show", question, symptoms, module, fault_codes}` or null | help flow (§13) |
| `licence` | `{derived_data: "CC-BY-SA-4.0" · null}` | |
| `contribution_consent` | bool | §13 step 6 |
| `credit` | string or null | the name the owner chose for attribution |

**Not signed with the Brain key** ([ADR-0041](../decisions/adr-0041-brain-ed25519-signing.md)):
a device signature would link every bundle to one device, the comma `dongleid` lesson.
Integrity comes from the hashes. A relay link may add a signature made with a key generated for
that one bundle (ADR-0043 §5).

### 9.3 `ostler share verify` (platform library and CLI)

`ostler share verify <bundle.zip> [--json]`, exit 0 on pass, 1 on fail naming each failing
check and its rule, 2 on an unreadable or wrong-format file. It fails on:

1. a file not in `files`, a file listed but missing, a hash or size mismatch, an unknown
   top-level path, or a zip entry time other than 1980-01-01;
2. a VIN pattern, a declared identity service or DID, or a seed/key exchange with data, in
   any file (R1–R3), including inside reassembled ISO-TP;
3. an `unframed` record in any tap file (R4);
4. any GPS channel, altitude, heading or `Utc` when `location` is `none`; any point
   timestamp in a route; a route fix inside the trim or a zone (checked on the owner's device
   only, which knows the zones);
5. a timestamp, date or ULID outside `time_basis`;
6. a MAC, IP, SSID, certificate fingerprint, bearer token or peer key pattern anywhere (R14);
7. a level-content mismatch (a tap file in L2, `data.csv` in L0, a `diag/` file below L4);
8. a `share.json` with a forbidden field (VIN, HMAC, device id, user id).

**Gate on every path.** The bundle writer runs the verifier on the **final bytes** and refuses
to hand them on unless it passes; the file, relay and hub paths take only a verified bundle and
re-check its hash. A grant (L0–L2) runs the same checks on each response. `ostler-app-hub`
re-runs `verify` before upload. For L0–L1 published to the hub (plaintext by design), the hub
server runs it again on receipt and **rejects, never repairs** (community hub research §7). An
L3–L4 help-thread bundle is end-to-end encrypted, so the server cannot read it: it checks only
the envelope (format, size, expiry, download count), and the helper's browser-side viewer runs
the verifier's format and hash checks after decrypting and refuses a bundle that fails. CI runs
it over every share fixture.

## 10. Delivery paths and link controls

| Path | Levels | Revocable | Default / max expiry | Audit |
|---|---|---|---|---|
| **Grant** (`/peer/v1` over LAN, Tailscale or the relay) | L0–L2 | yes, at once | registry rules: `route` and `summary` may be indefinite; live and precise ≤ 24 h | each pull: time, peer, class, coarse size |
| **Relay link** (Ostler Cloud stores ciphertext; the key in the URL **fragment**, as invites §5.2) | L0–L4 | until downloaded (Download), at once (Locked) | L0–L2 7 d / 30 d; L3–L4 72 h / 7 d | created, each open or download, revoked, expired |
| **File** (save, or the phone share sheet) | L0–L4 | **no**, and the sheet says so | — | "exported to file", level, redaction summary |
| **Hub help thread** (`ostler-app-hub`): the bundle is **end-to-end encrypted** on the owner's device, the hub stores ciphertext only, each **named helper** gets their own link with the key in the URL **fragment**, and a browser-side viewer decrypts it | L3–L4 | yes until expiry; copies already downloaded cannot be recalled | 7 d / 30 d, then deleted from hub storage; **at most 3 downloads** | as relay, plus the thread and each helper who opened or downloaded it |
| **Pack issue** (the owner attaches a file to a GitHub issue form) | L3–L4 | no, public | — | as file, plus the issue URL |

**Link controls** (DMD Hub §2.2, as fields on the grant or link; accounts §15.4):

- **Mode: Locked or Download.** Locked: viewed in Ostler, the hub viewer or the relay viewer;
  follows the owner's edits; revocable; removed from recipients' Ostler devices at
  `access_until`. Download: a copy that survives revoke. The sheet says plainly that Locked
  stops casual copies but anyone who can see data can copy it. L3–L4 default to Locked (viewed in the
  browser-side viewer) on a hub help thread, with download allowed up to 3 times, and to
  Download on a relay link (a bundle is a file).
- **Available from** (start in the future, e.g. an event's route), **link expiry** (last time a
  new person may open it), **access until** (Locked: content withdrawn), **collection limit**
  (distinct recipients), **downloads per recipient**.
- **States:** Pending (before available-from) · Active · Full (limit reached) · Expired ·
  Revoked, each a chip in the visibility-chip style.

## 11. Preview, expiry, revoke and audit

- **Preview is the bundle.** The share sheet renders the produced bundle (or, for a grant, the
  `/peer/v1` response for that audience) through the same code a recipient runs: accounts
  §14.7 S8 "View as…", not an imitation. L3–L4 add the **redaction report** (chips: "VIN ×3
  frames", "Ends 500 m", "2 zones", "Relative time", "No GPS", "2 notes left out") and a hex
  view of each scrubbed frame, before and after, on the owner's device only.
- **Expiry** is required on every relay link and hub thread, shown as a countdown chip.
- **Revoke**: one tap on a grant, link or thread; a revoked relay or hub object is deleted from
  storage at once. File and pack-issue paths say "cannot be revoked" in the warning token.
- **Audit** sits in Settings → Sharing (S8) beside grants. A trip's "…" menu shows "Shared 2× ·
  1 active", which opens its share history (level, audience, path, created, opens, downloads,
  state, revoke).
- **Ghost** hides live classes only (accounts §14.3); past-trip grants and hand-overs are not
  live, so ghost does not hide them; the sheet says so.

## 12. Live trips

A trip still recording is shared live through Vehicles & Map with a `location` `live` grant
(≤ 24 h, ends at trip end), using the grant options added in accounts §15.3: `trail_window`
(none, 1, 3, 6, 12, 24 h or whole trip), `delay` (0–6 h, covering moments too),
`show_speed` and `show_values` (off by default). When the trip ends, the live grant ends; the
owner may then share the finished trip at L0–L1 as usual (no auto-conversion).

## 13. Help me decode or diagnose

1. **Start** from Diagnose ("Get help with this fault", on a fault or a module), Trips (a
   trip or a marked range) or Decode lab ("Ask for help decoding", on a signal or a frame).
   One question: *decode something* or *diagnose a problem*?
2. **Capture recipe.** For decoding, Ostler suggests a short recording with clear events
   (switch the item on and off, sweep the control, mark each with ⚑). A helper may send a
   **recipe**: a file listing signals, modules and steps. The owner runs it locally; it can
   only start a recording and show steps. Helpers never send lab requests or actions; remote
   paths stay read-only (ADR-0033 §6).
3. **Level and recipient.** Defaults: **L3 for decoding, L4 for diagnosing**, the time range
   trimmed to the marked window, location none. Recipients: a contact, **named helpers** on a hub help
   thread (the question may be public; the bundle never is), or a pack's maintainers (issue
   form).
4. **Preview** with the redaction report; the **verifier** runs; the owner confirms.
5. **Send.** To a contact by relay link (or file). To a hub help thread through
   `ostler-app-hub`, which encrypts the verified bundle on the device, uploads the ciphertext
   with the request's structured fields (make, model, engine, year, module, symptoms, fault
   codes, question) and gives each named helper a link with the key in its fragment (7 days by
   default, 30 at most, at most 3 downloads). To a pack, Ostler
   opens the pack repo's `decode-request` or `diagnose-request` issue form with the fields
   pre-filled where the form allows; the owner attaches the zip. Ostler never posts on the
   owner's behalf.
6. **Contribution back.** The bundle is **never committed** and never re-shared by the hub
   (ADR-0036 §5). Only **derived data** flow back: signal definitions, DTC text and short
   labelled fixture snippets (`response → expected_values`). They enter the pack as
   `candidate` and reach `proven` only under the evidence rules (UI spec §8.3). The sheet's
   **contribution consent** tick, off by default, reads: *"If my log helps decode something,
   the decoded definitions and short labelled snippets may be published under CC BY-SA 4.0,
   credited to [name]. The log itself is never published."* (ADR-0012; code still needs the
   CLA.)
7. **Close the loop.** When a decode the bundle helped with is merged, the next pack update
   shows "Your capture helped decode `fuel_temp`", with the credit the owner chose.

## 14. Where each piece lives

| Piece | Home | Why |
|---|---|---|
| Redaction pipeline, widened scrubber, bundle writer, `ostler share verify`, candump export | **core platform** (`openostler.logbook.share`, beside `pcapng`; the scrub table shared with `openostler.node.tap`) | one scrubber for every path (ADR-0036 §3) |
| Privacy zones and the ends trim setting | **core shell**, More → Places | one definition for every class with location |
| Share sheet on a trip (L0–L4), share history | **core Trips** | Trips owns the trip; grants come from the registry |
| Grants, link controls, audit, View as… | **core shell**, Settings → Sharing (S8) | accounts §14 and §15 |
| "Get help with this fault" → L4 | **core Diagnose** | faults live there |
| "Ask for help decoding", recipes, contribute | **Decode lab** | the Detect → … → Contribute pipeline |
| Relay link storage | **Ostler Cloud** (ADR-0028), optional | no core feature may need it |
| Trip cards in groups | **Social** add-on | its share-out of trip cards |
| Friends' shared trips on a map, live trip options | **Vehicles & Map** add-on | its `trips` and live grants |
| Publish to Ostler Community, help threads, link and public audiences on the hub | **`ostler-app-hub`** (open client add-on, which encrypts L3/L4 on the device) and **`ostler-hub`** (server) | the community hub: a closed service run by Ostler, one instance, not self-hostable ([community hub §3](2026-10-07-community-hub-design.md#3-repos-licences-and-stack)) |

## 15. Phases

| Phase | Delivers | Needs |
|---|---|---|
| **TS1 Bundle and verifier** | widened scrubber (§8), pipeline R1–R16, `ostler.share/1` writer, `ostler share verify`, candump export, File path for L2–L4; Export all runs the same scrubber | ADR-0043 accepted; pack `identity` field |
| **TS2 Trips share sheet** | L0–L2 grants to household and persons, preview, audit, share history; privacy zones in More → Places | accounts P2 (contacts, grants) |
| **TS3 Help flow** | Diagnose "Get help with this fault", Decode lab "Ask for help decoding", recipes, issue forms in pack repos, contribution consent | TS1 |
| **TS4 Relay links** | Locked or Download links with the link controls, key in the fragment | Ostler Cloud relay |
| **TS5 Community** | `link` and `public` audiences for L0–L1 (publish), L2 to hub clubs, end-to-end encrypted hub help threads for L3–L4 to named helpers | `ostler-app-hub` H1 |

## 16. Tests

- **Levels:** for each level, a bundle built from a recorded fixture session contains exactly
  the files in §9.1 for that level and nothing else; an L2 without L1 has no GPS, `Utc`,
  heading or altitude anywhere.
- **Trim and zones:** a fixture trip starting and ending inside a home zone shows no fix within
  r of c′ and none within T of either end; a mid-trip zone yields two segments with no joining
  line; T below 200 m is refused; the zone offset is identical across two shares and after an
  app restart; distance, duration and elevation equal those computed from the visible fixes
  alone (the hidden length is not recoverable from any field).
- **L0 and L1 agree:** the L0 card's distance equals the L1 route's distance rounded to 1 km.
- **Time:** an L2–L4 bundle has no date or time other than relative values and the fixed zip
  time; "keep real date" is refused for a link, a hub thread, a pack issue and a file.
- **Ids:** no session id, ULID, node id, boot id, `vid` or peer fingerprint from the source
  appears in the bundle; two bundles of the same trip share no id.
- **Scrub:** the §8.4 synthetic-VIN injection on recorded fixtures (K-line, CAN single and
  multi-frame, broadcast declared and undeclared); seed/key exchanges scrubbed; `unframed`
  dropped.
- **Verifier:** one failing fixture per check in §9.3, each failing with its rule; the writer
  refuses to emit a bundle that fails; the hub path refuses an unverified bundle; a public L3
  bundle carries no location whatever the ticks.
- **Not signed:** no bundle carries the Brain key id or a signature by it.
- **Grants:** L3 or L4 offered as a grant is refused by the registry; an L2 grant to `public`
  is refused, and to `link` it needs the owner's opt-in and an expiry; a `link` grant for live
  location beyond a ride, audio, video or a raw log is refused; a `public` route grant before
  trip end + the owner's delay (default 24 h), or without the publish act, is refused.
- **Help flow:** a helper's recipe cannot carry an action or a lab request (schema refuses it);
  the contribution consent defaults off and its absence sets `licence.derived_data` to null.

## 17. Open questions (do not block TS1)

- The pcapng `USER0` K-line dissector for helpers who use Wireshark (a Lua dissector in the
  platform repo is the likely answer).
- Whether an MDF4 export for pro tools belongs in Integrations (research §9).
- Pre-filling GitHub issue forms from a URL for every field type (research U item).

## Changelog

- 2026-10-07 — v0.1: first draft (DMD round) from the trip and log sharing and DMD Hub
  research, for the owner's approval.
- 2026-10-07 — v0.2: §14 follows the owner's direction that the community hub is a closed,
  Ostler-run service, not self-hostable; the client add-on stays open and does the encryption.
  No level, rule or decision changes.
- 2026-10-07 — v0.3: approved by the owner on 2026-10-07 ("approve all", DMD round): every
  decision answered as recommended (alternatives not chosen, the `captures` class included);
  ADR-0043 accepted; the TS1 bundle and verifier are built first, before any share screen.
- 2026-10-07 — v0.4: amended (openness round, approved by the owner on 2026-10-07, "apply
  the loosenings", [ADR-0047](../decisions/adr-0047-openness-round.md)): ends trim to 0 and
  smaller privacy zones with warnings, short trips above L0, real time with a second confirm,
  public scrubbed L3 for open decoding projects, L2 by `link` with an expiry, the owner's
  public delay, the VIN in a named L4 bundle; no feed or score stays this feature's scope.

## Decisions for the owner

Answered 2026-10-07: approved as recommended ("approve all", DMD round; decision list items
20–32). Each recommendation below is the decision; each alternative was not chosen.

1. **Five levels L0 Card, L1 Route, L2 Telemetry, L3 Full log, L4 Diagnostics bundle, with the
   contents in §3?** Recommend: yes. Alternative: the DMD research's six presets (Card, Route,
   Stats, Full log, Diagnostics, Capture), which split aggregates from series and raw capture
   from the full log.
2. **L3 and L4 as hand-overs, never grants?** Recommend: yes; raw captures stay outside the
   registry, delivered by file, relay link or hub help thread after the verifier (ADR-0043).
   Alternative: a new `sensitive` class **`captures`** (scrubbed per ADR-0036, never in a
   preset, audience one person or the decode project only, ≤ 30 days, never `link` or
   `public`), which would make L3–L4 revocable live grants at the cost of reversing accounts
   §14.1's "raw captures are never a class".
3. **Default ends trim of 500 m on every shared route, adjustable 200 m to 1.5 km, never below
   200 m?** Recommend: yes. Alternative: trim only near saved places (most users never set
   any).
4. **Privacy zones of at least 500 m (1 km default for Home) with a fixed random offset of up
   to half the radius, never re-rolled?** Recommend: yes. Alternative: no offset (the zone is
   exactly centred, so a fitted circle gives the place).
5. **Stats from the visible trace only, with the rounding in §5.4, and L0 using the same
   trimmed trace?** Recommend: yes. Alternative: show whole-trip stats on L0 only (simpler,
   but an L0 and an L1 of the same trip together reveal the hidden length).
6. **Zone shape?** Recommend: circles with the fixed offset (simple to explain and draw in the
   owner's own view). Alternative: random polygons per place (Komoot), harder to fit but harder
   to explain.
7. **Time: day only for L0–L1, relative for L2–L4, real date only to one named person?**
   Recommend: yes. Alternative: hour-rounded real time for L2 to a person.
8. **Bundle `ostler.share/1` (zip, `share.json` with hashes and a redaction record, pcapng plus
   candump, fresh ids, no Brain-key signature) and the `ostler share verify` gate on every
   path, built first (TS1) before any share UI?** Recommend: yes. Alternative: sign bundles with
   the Brain key for provenance (links every bundle to one device).
9. **Widen the scrub to pack identity declarations, the UI spec list on every transport, seed/key
   exchanges, ISO-TP reassembly, and a VIN-pattern block with no "send anyway"?** Recommend: yes.
   Alternative: a VIN-pattern warning the owner can override.
10. **DMD-style link controls (Locked or Download, available-from, expiry, access-until,
    collection and download limits, state chips) as grant and link fields in core?** Recommend:
    yes. Alternative: expiry and revoke only, with limits left to the hub.
11. **Help me decode or diagnose with recipes, L3 or L4 defaults and CC BY-SA 4.0 consent for
    derived data only, off by default?** Recommend: yes. Alternative: consent on by default for
    help threads (more decodes, weaker consent).
12. **Max speed hidden by default on `link` and `public` cards?** Recommend: yes (R15).
    Alternative: shown, with a one-time warning.
