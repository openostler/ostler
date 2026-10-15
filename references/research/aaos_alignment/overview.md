---
title: "Android Automotive alignment: their design philosophy and how Ostler compares"
area: references
status: draft
version: 0.1
updated: 2026-10-15
depends_on: [references/research/aaos_alignment/apps.md, references/research/aaos_alignment/driving.md, references/research/aaos_alignment/platform.md, references/research/driver_distraction_rules.md]
summary: >
  Research only, no decisions (owner, 2026-10-15). It sets out how Android Automotive OS is designed, starting
  from its feature-control page, and checks whether Ostler is aligned. Their philosophy: one checkpoint to the
  car (VHAL behind CarService and permissions), customisation by overlays not forks, the car maker owning the
  frame and the look, apps owning data and drawing their own screens only while parked, the OEM deciding
  restrictions per driving state, and safety kept outside the infotainment system. Ostler shares most of
  this. Notes the deliberate differences and the gaps, and points to the three detailed notes.
---

# Android Automotive alignment: their design philosophy and how Ostler compares

Research only, no decisions. The owner asked on 2026-10-15 for a reading of
[AOSP feature control](https://source.android.com/docs/automotive/feature-control): their design
philosophy, how they handle apps and drive modes, and whether Ostler is aligned with Android
Automotive development.

The detailed notes:

- [apps.md](apps.md): apps;
- [driving.md](driving.md): driving state and distraction;
- [platform.md](platform.md): platform architecture.

## Their design philosophy

1. **One checkpoint to the car.** Apps never touch the vehicle. Data flows like this:
   vehicle networks → **VHAL** (typed properties with areas, access and change modes) →
   **CarService** → Car API, with a permission on every property.
2. **Customise with overlays, not forks.** Car makers shape AAOS with resource overlays, the Car UI
   library and plugins, and design tokens.
   - **Feature control** is the same idea for services. A build-time allowlist
     (`config_allowed_optional_car_features`) and a vehicle-side blocklist (the VHAL property
     `DISABLED_OPTIONAL_FEATURES`) switch optional services such as the cluster, navigation,
     telemetry, EVS and remote access on or off per car.
   - The setting is fixed at boot. Debug builds can toggle it with `cmd car_service`.
3. **The car maker owns the frame and the look; apps own data.**
   - Most third-party apps are drawn by the system from templates: media, messaging, and Car App
     Library navigation, POI, IoT and weather.
   - Apps draw their own screens only while parked, or if a screen is flagged
     *distraction-optimized*. That flag is checked at runtime and by Play review.
   - Video, games and browsers are parked-only.
4. **Restrictions are policy, owned by the car maker.**
   - `car_ux_restrictions_map.xml` sets restrictions per driving state (parked, idling, moving),
     per speed band, per mode and per display.
   - Apps never see the driving state. They see restriction flags and limits: 120-character
     strings, 21 items, depth 3.
   - An unknown state while running means fully restricted.
   - Passengers are handled by display, not by a button.
5. **Safety stays outside Android.** AAOS is QM, with no safety rating. Safety-relevant display
   elements (warning lights, rear camera) run on a separate renderer or OS with a monitor.
   - The cluster is optional (`cluster_home_service`), and AAOS just feeds it navigation.
6. **Software-defined vehicle.** Moving towards a service-oriented car with Android as one
   participant, which is where Ostler's IP-everywhere design also points.

## How Ostler compares

| Area | Verdict |
|---|---|
| One checkpoint to the car (node gate, gateway as permissions controller, VISS tokens) | **Aligned** |
| Data model (VSS/VISS signals vs VHAL properties) | **Aligned.** A VSS→VHAL mapping is straightforward ([platform.md](platform.md)) |
| Optional features (packs, capability manifests vs feature control) | **Aligned, different on purpose.** Ostler decides at runtime, AAOS at boot |
| Customise by data, not forks (packs, themes with locked safety colours) | **Aligned** |
| Unknown motion counts as moving; edit mode and settings refused while moving; tighter text and list limits | **Aligned or stricter** |
| One speed band with hysteresis; per-trip passenger view; locked at boot | **Different on purpose** (AAOS uses several bands, a passenger display, and unlocked at boot) |
| Safety outside the infotainment system (warnings on the node path, a cluster that works without the head unit) | **Aligned in spirit.** Ostler doesn't yet say outright that it is QM |
| Windowing (Scalable UI tiles whole apps; Ostler tiles pages inside one app) | **Different on purpose** |
| Third-party apps drawing freely in tiles while moving | **Gap.** AAOS would require templates or parked-only |

## The gaps worth knowing

- **Driving rules:**
  - no single restrictions file like AAOS's config;
  - no keyboard or video block in the shell;
  - touch targets while moving are 60 dp, against Google's 76 dp guidance;
  - the shell code has three motion states, while the UI spec has four.
- **Apps:**
  - nothing stops a third-party (iframe) page drawing while moving;
  - no limit on how deep a task can go;
  - themes don't reach iframes;
  - the built page contract lacks parts that ADR-0052 describes (per-action safety, data needs, host field).
- **Screens:**
  - no "is this screen visible to the driver" role;
  - no head-unit device type in ADR-0040;
  - no cluster-module spec with heartbeats.
- **Play:** on a car with Google built in, an Ostler web app can't pass distraction review. Only
  the owner's own LineageOS build, or a Car App Library app, can show Ostler pages while driving.

## For the owner's head unit

[ostler-android-automotive](https://github.com/openostler/ostler-android-automotive) is the
practical meeting point. The notes suggest:

- **VHAL:** serve it from the x86 host over AOSP's gRPC VHAL, as a VISS client with its own token.
  - It is read-only at first. Missing or stale values report as UNAVAILABLE.
  - It feeds AAOS **Ostler's own moving, parked or unknown verdict**, not raw speed, so car Maps
    and Waze follow Ostler's rules.
- **Cluster:** Ostler owns it, drawn from VISS. Android passes only the turn card.

## Sources

Listed in each detailed note.
