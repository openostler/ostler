---
title: "Trip and log sharing — per-trip share levels, redaction, export bundles and the help-me-decode flow"
area: references
status: draft
version: 0.1
updated: 2026-10-07
depends_on: [decisions/adr-0009-session-logbook-and-location.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md, decisions/adr-0033-action-categories-and-approvals.md, decisions/adr-0036-vin-and-identity-data-in-recordings.md, decisions/adr-0041-brain-ed25519-signing.md, specs/2026-10-05-session-logbook-design.md, specs/2026-10-06-module-bus-messages-design.md, specs/2026-10-06-node-source-design.md, specs/2026-10-06-accounts-sharing-design.md, specs/2026-10-06-ui-architecture-design.md, specs/2026-10-07-social-addon-design.md, specs/2026-10-07-vehicles-and-map-addon-design.md, references/research/accounts_social_login.md, references/research/social_group_drive_apps.md]
summary: >
  Prior art for sharing one trip at a chosen data level (Strava, Garmin Connect, Komoot, Relive, DMD2 groups and Rumo) and for sharing raw logs to get decoding or diagnostic help (comma connect public routes and openpilot uploads, opendbc and cabana, SavvyCAN and OVMS formats, Torque, motorcycle forums, Home Assistant diagnostics, GitHub issue forms), plus the re-identification research (privacy-zone inference, home/work pairs, speed-only tracking, CAN driver fingerprinting). Proposes five Ostler share levels (Card, Route, Telemetry, Full log, Diagnostics bundle), exact redaction rules per level under ADR-0009 and ADR-0036, a zip bundle format with a verifier, preview, expiry, revoke and audit, and a help-me-decode flow that feeds packs under CC BY-SA. Ends with Styling and Copy / Avoid / Decide.
---

# Trip and log sharing (October 2026)

## 1. Scope and method

The owner wants two things that look alike but are not. The first is **sharing one trip** with
friends, a group or later the public, at a level the owner picks (the DMD Hub and Strava side).
The second is **handing a log to someone** so they can help decode the car or diagnose a fault.
This note surveys prior art for both, live on 2026-10-07. It reads Ostler's recording formats
and privacy rules, then proposes share levels, redaction rules, a bundle format and the flows.
Strava and Beacon are covered for live sharing in [social_group_drive_apps.md](social_group_drive_apps.md)
and [accounts_social_login.md](accounts_social_login.md). This note covers past trips and logs only.
(U) marks an item not verified live.

## 2. What Ostler records today, and the rules already in force

| Artifact | Where | Holds | Identifying content |
|---|---|---|---|
| `data.csv` (parts) | `logs/sessions/<id>/` ([logbook spec](../../specs/2026-10-05-session-logbook-design.md)) | `Interval`, `Utc`, GPS channels, every store signal, `module`, `faults` | GPS, UTC, altitude, odometer-like signals |
| `meta.json` | same | start/end UTC, bbox, rounded start/end (~100 m), distance, devices, pack | session id is `YYYYMMDDTHHMMSSZ`, which is the start time |
| `events.jsonl`, `notes.jsonl`, audio | same ([replay notes spec](../../specs/2026-10-05-replay-notes-capture-design.md)) | state events, notes, voice | free text; audio is `max_audience: me` |
| Raw tap `tap/<ULID>.otap` | same ([node-source spec](../../specs/2026-10-06-node-source-design.md) §7) | v1 records: `t_us`, `seq`, bus, dir, proto, payload; `time` events with `utc_ns` | identity replies (scrubbed by default), node id, `boot_id`; **a ULID starts with its creation time in ms** |
| pcapng export | `fmt=pcapng` | one interface per bus; K-line `LINKTYPE_USER0`, CAN SocketCAN, events `USER1`; UTC from `time` events | as the tap |
| CSV / VBO / GPX exports | `/sessions/<id>/export` | AiM-named channels, VBO, GPX track | full GPS and UTC |

Rules that bind any share:

- **ADR-0009:** real sessions stay on the device; community uploads never carry GPS unless a
  later ADR adds a per-upload opt-in **with trimmed ends and a preview**.
- **ADR-0036 §3:** every export, contribution, share and support bundle scrubs identity data to
  the fixed placeholder, whatever the install option. The node-source spec adds that `unframed`
  records are dropped from every export and the `scrubbed` flag is never cleared.
- **Accounts §5.3 and §14.1:** raw captures and Decode evidence are **never a data class**.
  `trips` has the ladder `summary · full`, its traces follow `location`, and precise location
  grants are capped at **24 h, always**. Every share has an expiry, a revoke button and an audit.
- **UI spec §8.3:** the scrub list for exports and uploads names VIN (Mode 09 `02`, UDS `F190`,
  KWP `1A 87/90`), serials (`F18C`), EKA codes, seed/key pairs, and coarse GPS, time and odometer.
- **ADR-0036 §5:** raw car captures are never committed; fixtures are labelled snippets.

**Gap found.** The Brain's re-check in the node-source spec names only the `5A` and `49` reply
bytes. The UI spec's list (UDS `62 F1 90`, `62 F1 8C`, KWP `5A 87`) is wider. The export scrub
must use the **pack's identity declarations** plus the UI spec list, not a fixed byte pair.

## 3. Prior art: sharing one trip

| Product | Per-activity audience | Location controls | Stats controls | Notes |
|---|---|---|---|---|
| **Strava** | Everyone · Followers · Only you, set per activity [S1] | Hide start/end within a radius of a set address; hide start/end of **every** activity by radius (no address needed); hide the whole map; up to about 1 mile; not retroactive [S1][S2] | Per activity, hide power, heart rate, calories, pace; must be done each time [S3] | Zone centre is **randomly offset** from the address [S2] |
| **Garmin Connect** | Only me … Everyone, per item [S4] | Privacy zones set on the web only; hide **all points inside the zone**, not just ends; 500 m suggested [S4] | Per-field visibility (badges, steps) | Owner always sees the full route |
| **Komoot** | Only you (default) · Close friends · Followers · Anyone [S5] | Privacy zones are **random polygons**, not circles [S6] | — | Private by default is the right default |
| **Relive** | Public / private (U) | Privacy zone hides start and finish, new activities only [S7] | — | The shared object is a rendered video, not data |
| **DMD2 / DMD Hub / Rumo** | Groups on the Hub; Rumo (ADVHub's successor, launched 2026-01-04) shares trips and locations [S8] | Location sharing on or off per group member [S9] | — | Group GPX is encrypted and cannot be re-shared [S9] |

**What the research says about privacy zones.** Dhondt et al. (CCS 2022) studied 1.4 million
Strava activities. They recovered the protected location for **up to 85%** of endpoint privacy
zones. The attack used the distance the app still reported for the hidden part, the street grid
and the points where the trace enters the zone [S10]. Their most effective fix was **coarsening
reported distances**. Regenerating zones **helped** the attacker, because it gave more samples.
The Strava heatmap was also shown to reveal the homes of active users in quiet areas [S11].
Two older results matter as well. A home and work pair known to census-block level has a median
anonymity set of **1** [S12]. Four spatio-temporal points single out 95% of people in a mobility
dataset [S13]. Speed alone plus a known home predicted destinations within 500 m for 24% of
traces [S14]. Ostler takes four rules from this:

1. **Stats must be recomputed from the visible trace.** Distance, duration, average speed and
   elevation are computed from what the viewer sees, so the hidden part leaks nothing.
2. **Trim every trip's ends**, not only those near saved places, because most users never set zones.
3. **Keep each place's cloak fixed.** A randomly offset zone is chosen once per saved place and
   never re-rolled.
4. **Telemetry without GPS is not anonymous.** A speed trace plus a known start can recover the
   route, so shared speed channels need the same time and start handling as a route.

## 4. Prior art: sharing logs for decoding and diagnosis

| Community / tool | What gets shared | How | Privacy handling | Lesson for Ostler |
|---|---|---|---|---|
| **comma connect / openpilot** | A **route**: logs, GPS, speed, timestamps, video [S15] | Upload all rlogs, set Preserved, then a **Public access** toggle gives anyone with the route id access; or share the **whole device** by e-mail [S15][S16] | Guide says to start and end at public places [S15]. openpilot uploads by default; driver camera opt-in; mic not recorded [S17] | Route id is `dongleid\|time` [S18]: the id carries a stable device id and the start time. Never use stable ids in share ids |
| **openpilot issue forms** | A route id is **required** to file a bug [S18] | GitHub issue form with a required `route` input | — | Structured forms make help possible; Ostler can pre-build the request |
| **opendbc + cabana** | DBC files (MIT) from community routes [S19][S20] | Record a route with many events, open it in cabana, edit the DBC, open a PR; bounties for ports [S19] | Route sharing as above | Decodes flow back as data PRs; the log stays with the user |
| **SavvyCAN** | Captures in GVRET, CRTD, candump (read), Vector ASC, BusMaster, PCAN, pcap (read) and more [S21] | Files on forums and issues | None built in | Accept and export **candump** and pcapng; do not invent a CAN text format |
| **OVMS** | CAN logs in crtd, gvret-a/b, pcap, lawicel, raw; to SD or a TCP server for SavvyCAN [S22] | Files | ID filters only | Filters before capture are the first privacy tool |
| **Torque Pro** | `trackLog.csv` with GPS; live upload to any web URL [S23] | E-mail, web upload | None | The anti-pattern: GPS in every log, silent upload targets |
| **BMW bike forums (GS-911, MotoScan)** | Fuelling logs (injection time, lambda factors) posted for experts to read [S24] | Forum attachments | None | Riders already ask "can someone read my log"; give them a safe bundle |
| **Home Assistant diagnostics** | A JSON file per integration or device, downloaded by the user [S25] | Attach to an issue | Integration declares `TO_REDACT` keys; `async_redact_data` replaces them recursively [S25][S26] | The model for Ostler's **Diagnostics bundle**: declared redaction, user-held file |
| **Research datasets (ROAD, CarDS)** | Anonymised CAN | Published | IDs remapped, VINs replaced [S27] | Driver re-identification from CAN signals works even with hidden signal layout [S28] |

**Capture formats** (for the bundle's raw part):

| Format | Open spec | Tools | Use in Ostler |
|---|---|---|---|
| **pcapng** | yes (IETF draft) | Wireshark, tshark | **Native raw export** (already built); K-line as `USER0` needs our dissector |
| **candump `-l`** | de facto, `(sec.usec) iface id#data` [S29] | can-utils, SavvyCAN (read), cabana tooling, python-can | **Second export for CAN buses** |
| GVRET CSV / CRTD | community | SavvyCAN, OVMS | Import only |
| Vector ASC | text, de facto | CANalyzer, python-can | Optional export later |
| Vector BLF | **no public spec** [S30] | Vector, python-can | Import only, never write |
| ASAM MDF4 | yes, ASAM standard [S30] | asammdf (LGPL), CANedge | Later export for decoded channels, an Integrations add-on |

None of these formats carry a redaction record, so the bundle manifest has to carry it.

## 5. Proposal: five per-trip share levels

A share is one trip at one level, given to one audience, for one window. Levels L0–L2 are
**grants** on existing data classes, so they can be pulled, revoked and audited live. L3–L4 hold raw
captures, which accounts §14.1 refuses as a class, so they are **hand-overs**: a sealed bundle
sent to a named person or a pack's maintainers.

| Level | Name | Contents | Registry mapping | Default audience cap | Location default |
|---|---|---|---|---|---|
| **L0** | **Card** | Vehicle card (basic), day, region label, distance and duration (rounded), optional photo; image card for share-out | `trips` summary, `location` coarse or none | person, group, household (public later) | coarse region only |
| **L1** | **Route** | L0 plus trimmed, simplified trace, elevation, stats recomputed on the visible trace | `trips` summary + `location` **route** (new detail, see Decide 1) | as L0 | route (trimmed) |
| **L2** | **Telemetry** | L1 or no route, plus chosen decoded channels (speed, rpm, coolant …), faults seen, replay | `trips` full + `faults`; channel subset | person, group | none unless L1 is also ticked |
| **L3** | **Full log** | All decoded channels, raw tap (pcapng, candump for CAN), filtered events, shareable notes | hand-over only | one person or a pack's maintainers | **none** (route only to a named person, by explicit tick) |
| **L4** | **Diagnostics bundle** | L3 (or L2) plus faults, freeze frames, readiness, scan report, pack and firmware versions, device manifests, link and gap stats, redacted platform log tail and config | hand-over only | one person or a pack's maintainers | none |

### 5.1 Redaction rules per level (applied in this order, on a copy, never in place)

| # | Rule | L0 | L1 | L2 | L3 | L4 |
|---|---|---|---|---|---|---|
| R1 | **Identity scrub** (ADR-0036 §3): pack identity declarations + UI spec §8.3 list (Mode 09 `02`/`04`/`0A`, UDS `62 F1 90`/`F1 8C`, KWP `5A 87`/`5A 90`, EKA codes, seed/key pairs) → fixed placeholder, `scrubbed` kept | n/a | n/a | yes | yes | yes |
| R2 | **ISO-TP-aware scrub**: reassemble multi-frame replies on diagnostic IDs, then placeholder the payload bytes **in every first and consecutive frame** of candump and pcapng | — | — | — | yes | yes |
| R3 | **Broadcast identity frames**: packs declare periodic frames that carry a VIN (some makes broadcast it, U); plus a VIN-pattern detector (17 chars, no I/O/Q) over ASCII windows of reassembled and raw payloads → **block the export** until declared | — | — | yes | yes | yes |
| R4 | Drop `unframed` records (node-source §7) | — | — | — | yes | yes |
| R5 | **Ends trimmed**: hide the first and last **500 m along the track** on every trip, and everything inside saved privacy zones (radius ≥ 500 m, centre offset once per place at random and never re-rolled) | n/a | yes | yes if GPS | yes if GPS | yes if GPS |
| R6 | **Stats from the visible part**: distance, duration, averages and elevation gain recomputed after R5; distance to 0.1 km, duration to 1 min (L0: 1 km, 5 min) | yes | yes | yes | yes | yes |
| R7 | **Trace simplified** (RDP to ~10 m) and timestamps removed from track points | — | yes | — | — | — |
| R8 | **No GPS channel unless a route is granted**: drop `GPS_*`, `Utc`, heading **and altitude** (elevation profiles locate a trip) | yes | n/a | yes | yes | yes |
| R9 | **Time**: L0–L1 show the **day only**; L2–L4 rebase to **relative time** (`t=0` at the first visible sample). Optional "keep real date" tick for L3–L4 to one person. UTC `time` events in the tap are rewritten to the same base | day | day | relative | relative | relative |
| R10 | **Fresh ids**: session id, tap ULIDs, node `device` and `boot_id`, relay ids replaced by per-bundle random ids (a ULID leaks its creation time; a stable id links bundles, the comma `dongleid` lesson) | yes | yes | yes | yes | yes |
| R11 | **Odometer and hours** coarsened to 1,000 km / 100 h; freeze-frame odometer the same | — | — | yes | yes | yes |
| R12 | **People**: driver name, user ids, contacts → "driver"; plate hidden unless ticked (registry); photo EXIF stripped and re-encoded (Vehicles & Map spec §2.2) | yes | yes | yes | yes | yes |
| R13 | **Free text**: only notes marked shareable; audio never (ADR-0010); events kept by type, free-text fields dropped | — | — | notes opt-in | notes opt-in | notes opt-in |
| R14 | **Network identity**: MACs, Wi-Fi SSIDs, Tailscale names, LAN IPs, certificate fingerprints, tokens in config and logs → HA-style `**REDACTED**` by declared keys plus patterns | — | — | — | yes | yes |
| R15 | **Max speed** hidden by default on L0–L1 public-facing cards (speeding evidence); owner may show it | hidden | hidden | shown | shown | shown |
| R16 | **Verifier** (§6.2) passes, or nothing leaves | yes | yes | yes | yes | yes |

**Public destinations** (a public GitHub issue, a later public page) force L3–L4 to location none
and relative time, whatever the ticks (ADR-0009). A route to the public needs the ADR that
ADR-0009 asks for.

## 6. Export bundle format

### 6.1 Layout: `ostler-share-<rand>.zip`

```
share.json          manifest (below)
README.txt          plain-English: what this is, level, what was removed, licence
trip.json           summary after R6 (and the L0 card fields)
data.csv            native logbook CSV after R1, R8, R9, R11 (L2+)
track.geojson, track.gpx   only when a route is granted (L1+)
faults.json         faults, freeze frames, readiness (L2+ / L4)
events.jsonl        filtered events (L3+)
notes.jsonl         shareable notes only, if ticked
tap/bus<N>.pcapng   scrubbed raw tap per bus (L3+)
tap/bus<N>.candump  CAN buses only (L3+)
diag/               L4: versions.json, manifests.json, link_stats.json, log_tail.txt, config.json (redacted)
card.png            L0 image for share-out (Social spec share sheet)
```

**`share.json`:** `{format: "ostler.share/1", id (random 128-bit), level, created_day, expires,
pack: {id, version}, platform_version, vehicle: {make, model, year, engine, market}, time_basis:
"day" | "relative" | "real", location: "none" | "coarse" | "route", files: [{path, sha256, kind}],
redactions: [{rule, count}], verifier: {version, passed}, request: {kind: "decode" | "diagnose" |
"show", question, symptoms, module?}, licence: {derived_data: "CC-BY-SA-4.0" | null},
contribution_consent: bool}`. No device id, no VIN, no masked VIN, no HMAC.

**Not signed with the Brain key.** ADR-0041's device key would link every bundle to one device,
the same problem as comma's `dongleid`. Integrity comes from the hashes. A relay link may sign
with a key made for that one bundle.

### 6.2 The verifier (`ostler share verify`, platform library)

The verifier runs as the last step of every share path and in CI on fixtures. It **fails** on:

- a VIN pattern, or a declared identity DID or reply, in any file;
- an `unframed` record;
- any GPS channel, altitude or `Utc` when `location` is none;
- a ULID or timestamp outside `time_basis`;
- a file not listed in `files`, or a hash mismatch;
- a MAC, IP or token pattern in `diag/`.

On a fail it names the rule. It is the share-side twin of the UI spec's CI rule that fails on a VIN
pattern under `tests/`.

## 7. Preview, delivery, expiry, revoke and audit

- **Preview is the bundle.** The share sheet renders the produced bundle exactly as the recipient
  will see it, through the same filter as `/peer/v1` (accounts §14.7 S8 "View as…"), not a UI
  imitation. For L3–L4 the preview adds a **redaction report**, for example "VIN scrubbed ×3 frames",
  "first and last 500 m hidden", "times made relative", "2 notes excluded". It also offers a
  hex view of each scrubbed frame (before and after, on the owner's device only).
- **Delivery paths:**

| Path | Levels | Revocable | Expiry default / max | Audit |
|---|---|---|---|---|
| **Grant** (pull over LAN, Tailscale or relay, `/peer/v1`) | L0–L2 | yes, at once | registry rules (route and summary may be indefinite; precise ≤ 24 h) | each pull: time, peer, class, coarse size |
| **Relay link** (Ostler Cloud stores ciphertext; key in the URL **fragment**, as invites §5.2) | L0–L4 | until downloaded | L0–L2 7 d / 30 d; L3–L4 72 h / 7 d; downloads ≤ 3 | created, each download, revoked, expired |
| **File** (save or share sheet) | L0–L4 | **no**, and the UI says so | — | "exported to file", level, redaction summary |
| **Pack issue** (§8) | L3–L4 | no, public | — | as file, plus the issue URL |

- **The audit lives in Settings → Sharing (S8)** beside grants. Each trip's "…" menu shows
  "Shared 2× · 1 active", which opens the trip's share history.
- **Ghost does not hide past-trip grants** (non-live, accounts §14.3). The sheet says so.

## 8. The "help me decode / diagnose" flow

1. **Start**: from Diagnose (a fault, a module), Trips (a trip, a time range) or Decode lab (a
   signal). Ostler asks one question: *decode something*, or *diagnose a problem*?
2. **Capture recipe**: for decoding, Ostler suggests a short recording with clear events (the
   cabana method [S20]: switch the item on and off, sweep the control, note each one with ⚑).
   A helper may send a **recipe** (a file listing signals, modules and steps). The owner runs it
   locally. Helpers never get lab requests or actions: remote paths stay read-only (ADR-0033 §6).
3. **Choose level and recipient**: the default is L3 for decoding and L4 for diagnosing, time range
   trimmed to the marked window, location none. Recipients are a contact, the pack's maintainers, or a
   public issue.
4. **Preview** with the redaction report, then the **verifier** runs, then the owner confirms.
5. **Send**: to a contact by relay link or grant. To a pack, Ostler opens the pack repo's GitHub
   **issue form** (a `decode-request` or `diagnose-request` template with required level,
   module, symptoms and bundle id). Form fields can be pre-filled from the URL (U). The owner
   attaches the zip. Ostler never posts on the owner's behalf.
6. **Contribution back**: the bundle itself is **never committed** (ADR-0036 §5). What flows into
   the pack are **derived data**: signal definitions, DTC text and short labelled fixture snippets
   (OBDb-style `response → expected_values`, UI spec §8.3). They come from the bundle by the
   helper or by the owner's own Decode lab ("Contribute previews the exact JSON"). They enter as
   `candidate` and reach `proven` only under the evidence rules. The share sheet's **contribution
   consent** tick licenses those derived data under **CC BY-SA 4.0** (ADR-0012, `LICENSE-DATA`).
   Code needs the CLA. Credit goes in the pack's attribution file under a name the owner chooses.
7. **Close the loop**: when a decode the bundle helped with is merged, the owner's Ostler shows it
   after the next pack update ("Your capture helped decode `fuel_temp`").

## 9. Ostler homes

| Feature | Home | Why |
|---|---|---|
| Redaction pipeline, bundle writer, verifier, candump export | **core platform** (`logbook/share.py`, beside the pcapng export) | Every share path and Export all must use one scrubber (ADR-0036 §3) |
| Share sheet on a trip (L0–L2 grants, file, link) and share history | **core Trips** | Trips owns the trip; grants come from the core registry |
| Grants, audit, View as… | **core shell**, Settings → Sharing (S8) | Already specced |
| "Get help with this fault" → L4 bundle | **core Diagnose** | Faults live there |
| Help-me-decode, recipes, contribute | **core Decode lab** | Already the Detect → … → Contribute pipeline |
| Privacy zones (saved places, fixed cloak) | **core shell** (Settings → Places), read by Trips and Social | One definition for every class with location |
| Relay link storage | **Ostler Cloud** (ADR-0028), optional | No core feature may need it ([obd_telematics_apps.md](obd_telematics_apps.md) Decide 7) |
| Posting trip cards to groups and share-out images | **Social add-on** (`ostler-app-social`) | Its spec already has share-out of trip cards |
| Seeing friends' shared trips on a map | **Vehicles & Map add-on** | Its spec already lists `trips` with trimmed routes |
| Public trip pages, a gallery and a public decode-request board (the DMD Hub / Rumo side) | **new add-on `ostler-app-hub`** (named in [community_hub_architecture.md](community_hub_architecture.md)) | Needs the `public` audience and its own ADR; keeps core free of a public server |
| Push a trip to Strava, Komoot or Rumo | **Integrations** (one repo each) | Third-party accounts; GPX already covers the manual path |
| MDF4 or ASC export | **Integrations** (`ostler-app-mdf`) | Pro tools; asammdf is LGPL, so it is allowed |
| BLF writer | not needed | No public spec |

## 10. Styling

- **The level picker is a ladder**: five stacked rows, L0 at the top. Each row shows chips for what
  it adds (map, chart, raw, wrench) and a single line "what they'll see". Higher rows use the warning
  token only from L3 up. The default row is pre-selected per entry point.
- **The audience is chosen before the level.** The ladder greys out levels the audience can't take
  ("L3 goes to one person").
- **Preview fills the sheet**: the recipient's view of the trip on the Ostler Night map, with
  hidden ends drawn as a dashed fade to the `--bg` token, never as a circle (a circle shows where the zone is).
- **The redaction report is a chip row** ("VIN ×3", "Ends 500 m", "Relative time", "No GPS").
  Tapping a chip opens the rule in plain English. The hex diff uses the mono face with scrubbed
  bytes in the muted token.
- **Expiry is a countdown chip** in the visibility-chip style; "cannot be revoked" on file and
  public paths is a plain sentence in the warning token, not small print.
- **All of it is Parked-only on a driver-facing screen**; a card share from the phone is fine anytime.

## 11. Copy / Avoid / Decide for Ostler

### Copy

- **Per-trip audience with private default** (Komoot, Strava). It maps to the registry's grant,
  with `me` as the default (accounts §14.1).
- **Hide the ends of every trip**, not only near saved places (Strava's "all activities" option),
  plus saved places with a cloak offset once at random (Strava, Komoot) → R5.
- **Declared redaction with a user-held file** (Home Assistant diagnostics) → L4, R14.
- **A public route toggle with plain warnings** (comma: start and end in public places) → the
  preview and report, but with Ostler's trimming done for the user.
- **Required structured fields for help requests** (the openpilot issue form route field) → §8 step 5.
- **The decode loop of record, label, then PR the definition** (opendbc and cabana) → Decode lab,
  CC BY-SA data (ADR-0012).
- **candump as the CAN interchange text** (can-utils, SavvyCAN, python-can) beside pcapng.

### Avoid

- **Reporting stats over the hidden part** of a trip: the 85% privacy-zone break [S10].
- **Re-rolling privacy-zone cloaks**, which gives the attacker more samples [S10].
- **Stable device ids or start times in share ids** (comma `dongleid|time`; ULIDs; our
  `YYYYMMDDTHHMMSSZ` session ids).
- **Signing bundles with the Brain's device key** (ADR-0041): it links every share to one device.
- **Treating telemetry without GPS as anonymous** [S14][S28].
- **Uploading by default** (openpilot) and silent upload URLs (Torque).
- **Whole-device sharing** (comma's e-mail share) when one trip would do.
- **Writing BLF**, or hashing VINs instead of using a placeholder (ADR-0036 already rejects hashing).

### Decide (recommendations for the owner)

1. **A `route` detail on the `location` ladder** for past trips: a trimmed, simplified trace with
   no point timestamps, between `place` and `precise`. It may be indefinite, because the 24 h cap
   fits live and precise history, not a cleaned past route. *Recommend: approve as an accounts §14
   amendment; without it a shared trip map expires after a day.*
2. **Raw logs (L3) and diagnostics bundles (L4) are hand-overs, never grants.** *Recommend:
   approve; keep the §14.1 rule that raw captures are not a class; deliver by file, relay link
   or pack issue with the verifier.* Alternative: a `sensitive` `trips.raw` class capped at one
   person and 72 h.
3. **The ADR that ADR-0009 asks for** (GPS in community uploads): *Recommend: write it as "routes
   only at L1, only after R5–R7, only with preview; never in L3–L4 to a public destination".*
4. **Default trim** of 500 m at both ends of every shared route, plus privacy zones ≥ 500 m with a
   fixed random offset. *Recommend: approve; owner can raise it to 1.5 km, never lower than 200 m.*
5. **Time handling**: day-only for L0–L1, relative for L2–L4, "keep real date" only to one person.
   *Recommend: approve.*
6. **Bundle format `ostler.share/1`** (zip, `share.json` with hashes and a redaction record,
   pcapng + candump, no device signature) and the `ostler share verify` gate on every path.
   *Recommend: approve as a platform spec before any share UI.*
7. **Widen the export scrub** to the pack's identity declarations plus the UI spec §8.3 list, ISO-TP
   reassembly (R2), and a VIN-pattern block (R3). *Recommend: approve; it fixes the `5A`/`49`-only
   gap in the node-source re-check.*
8. **Contribution consent at share time**, licensing derived decodes and fixture snippets under
   CC BY-SA 4.0, never the log itself. *Recommend: approve; it matches ADR-0012 and ADR-0036 §5.*
9. **Public trip pages and a public decode board** as part of `ostler-app-hub`, after club pages and
   the `public` audience. *Recommend: defer to after P4; GitHub issue forms on pack repos cover
   help requests until then.*
10. **Max speed hidden on public-facing cards by default.** *Recommend: approve (R15).*

## 12. Sources (all checked 2026-10-07)

- [S1] Kaspersky, Strava privacy settings: https://www.kaspersky.com/blog/running-apps-privacy-settings-part2-strava/52409
- [S2] road.cc, Strava edit map visibility: https://cdn.road.cc/content/tech-news/stravas-edit-map-visibility-gives-greater-privacy-control-285569 · BikeRumor: https://bikerumor.com/strava-privacy-zones-expand-with-new-edit-map-visibility-functions
- [S3] Velo, Strava hide stats per activity: https://velo.outsideonline.com/2021/08/strava-rolls-out-activity-and-privacy-updates-for-subscribers-and-free-users/ · DC Rainmaker: https://dcrainmaker.com/2021/08/privacy-features-options.html
- [S4] Kaspersky, Garmin privacy settings: https://www.kaspersky.com/blog/garmin-privacy-settings/53920/ · Garmin forum on zones: https://forums.garmin.com/sports-fitness/healthandwellness/f/venu-3-series/409991/how-does-the-privacy-zone-work
- [S5] Komoot privacy help: https://www.komoot.com/help/privacy
- [S6] Dhondt et al. (CCS 2022), §2 on Komoot polygons (below, S10)
- [S7] Relive support, privacy zone: https://support.relive.com/kb/guide/en/how-can-i-add-a-privacy-zone-AqX1Q8xMMJ/Steps/33195 (page blocked to fetch; from the search snippet)
- [S8] Rumo launch: https://rumo.dmdnavigation.com/whats-new/say-hello-to-rumo
- [S9] DMD2 group ride docs: https://docs.dmdnavigation.com/documentation/group-ride/
- [S10] Dhondt, Le Pochat, Voulimeneas, Joosen, Volckaert, "A Run a Day Won't Keep the Hacker Away", CCS 2022: https://lepoch.at/files/epz-inference-attacks-ccs22.pdf
- [S11] Childs, Nolting, Das, "Heat Marks the Spot", ConPro 2023: https://conpro23.ieee-security.org/papers/childs-conpro23.pdf
- [S12] Golle and Partridge, "On the Anonymity of Home/Work Location Pairs", Pervasive 2009: https://crypto.stanford.edu/~pgolle/papers/commute.html
- [S13] de Montjoye et al., "Unique in the Crowd", Sci. Rep. 2013: https://pmc.ncbi.nlm.nih.gov/articles/PMC3607247
- [S14] Gao et al., "Elastic Pathing: Your Speed is Enough to Track You", UbiComp 2014: https://arxiv.org/abs/1401.0052
- [S15] sunnypilot community, Share a Route: https://community.sunnypilot.ai/t/1916
- [S16] comma connect public access and preserve (forum guide): https://www.f150lightningforum.com/forum/attachments/how-to-ask-for-help-pdf.112620
- [S17] openpilot README, user data: https://github.com/commaai/openpilot
- [S18] openpilot bug report issue form: https://github.com/commaai/openpilot/blob/master/.github/ISSUE_TEMPLATE/bug_report.yml
- [S19] opendbc README: https://github.com/commaai/opendbc
- [S20] cabana wiki: https://github.com/commaai/openpilot/wiki/Cabana
- [S21] SavvyCAN formats (SlackBuilds README): https://slackbuilds.org/repository/15.0/system/SavvyCAN/
- [S22] OVMS CAN logging: https://docs.openvehicles.com/en/latest/crtd/can_logging.html
- [S23] Home Assistant Torque integration (upload URL, log): https://www.home-assistant.io/integrations/torque/
- [S24] UKGSER, data logs thread: https://www.ukgser.com/community/threads/data-logs-anyone-an-expert.266135/
- [S25] Home Assistant developer docs, integration diagnostics: https://developers.home-assistant.io/docs/core/integration_diagnostics/
- [S26] Home Assistant `diagnostics/util.py`: https://github.com/home-assistant/core/blob/dev/homeassistant/components/diagnostics/util.py
- [S27] ROAD dataset guide: https://arxiv.org/pdf/2012.14600 · CarDS: https://tudatalib.ulb.tu-darmstadt.de/handle/tudatalib/5080
- [S28] Lestyán et al., "Extracting vehicle sensor signals from CAN logs for driver re-identification", 2019: https://arxiv.org/abs/1902.08956
- [S29] can-utils `log2asc.c` (candump log line format): https://github.com/linux-can/can-utils/blob/master/log2asc.c
- [S30] CSS Electronics, MF4 explained: https://www.csselectronics.com/pages/mf4-mdf4-measurement-data-format · python-can BLF reader: https://python-can.readthedocs.io/en/main/_modules/can/io/blf.html
- GitHub issue forms syntax: https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
