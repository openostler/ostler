---
title: "Security policy"
area: root
status: stable
version: 1.0
updated: 2026-10-06
summary: >
  How to report a vulnerability (GitHub private vulnerability reporting), what is in scope (platform, vehicle packs, device-side code, release artefacts), the 14-day acknowledgement target, supported versions (main plus the latest release), coordinated disclosure, EU CRA and UK PSTI readiness, and the hard safety lines for testing against vehicles.
---

# Security policy

Ostler talks to real vehicles, so a security bug can be a safety bug. Thank you for
reporting responsibly.

## Reporting a vulnerability

**Report privately** through GitHub private vulnerability reporting:
[Security → Report a vulnerability](https://github.com/openostler/ostler/security/advisories/new)
on this repository. For a bug that is only in a vehicle pack you may report it on that
pack's repository instead (the Discovery 2 pack:
[discovery2-diag](https://github.com/JamesWrightDavid/discovery2-diag/security/advisories/new));
either way reaches the maintainer.

**Do not** open a public issue, pull request or discussion for a vulnerability.

Please include:
- the affected component, version or commit;
- the impact as you understand it (for example remote code execution on the device, an
  unauthenticated write to the car, leaked VIN or location data);
- steps to reproduce, ideally against the hardware-free test fakes
  (`tests/fakes.py::FakeKLineEcu`) rather than a car;
- whether you want to be credited, and how.

## In scope

- **The platform** (this repository): the K-line/KWP2000 comms core, the `VehiclePack`
  contract, the session logbook, the local HTTP server and its API, and the dashboard UI
  (including the committed build in `src/openostler/web/static/`).
- **Vehicle packs** published by the project, starting with the Discovery 2 pack
  (`d2diag`): its decoders, menus, actions and safety gates.
- **Device-side code**: Pi install and deploy scripts, the Docker image, and ESP32
  firmware (for example the K-line node and the planned guardian).
- **Release artefacts**: the sdist and wheel, SBOMs and build provenance attached to
  releases.

Particularly interesting: anything that bypasses a safety gate (an actuator test, a
write, coding or SecurityAccess without its explicit confirmation), any write path to an
airbag/SRS module, authentication bypass on the local server, and leaks of VIN, EKA or
location data.

**Out of scope:** third-party services (map tile servers, OpenStreetMap Nominatim, Google
Fonts), vulnerabilities in a vehicle's own ECUs (report those to the manufacturer), and
third-party forks or hosted copies.

## What to expect

- **Acknowledgement within 14 days** of your report.
- An initial assessment and severity, then regular updates until the fix ships. We aim to
  fix high and critical issues within 60 days.
- **Coordinated disclosure:** we agree a disclosure date with you, normally once a fixed
  release is out and no later than 90 days after the report unless we agree otherwise. We
  publish a GitHub Security Advisory (with a CVE where warranted), list the fix in
  [CHANGELOG.md](CHANGELOG.md), and credit you if you wish.
- If a report shows an actively exploited issue or a risk to people on the road, we may
  publish mitigations sooner.

## Supported versions

| Version | Supported |
|---|---|
| `main` | Yes |
| The latest release | Yes |
| Older releases | No; please upgrade |

The platform is pre-1.0 ([CHANGELOG.md](CHANGELOG.md) has the versioning policy). Until
the first tagged release, only `main` is supported. Versions published before
2026-10-06 under the MIT licence are not maintained.

## Hard safety lines for researchers

These are not negotiable, and the same rules bind the project
([CONSTITUTION.md](CONSTITUTION.md)):

- **Never test against a vehicle on a public road** or while it is moving. Test with the
  vehicle stationary, off the road, with the ignition on and the engine off unless a test
  needs it running.
- Test only on a vehicle you own or have the owner's written permission to test.
- Never write to an airbag/SRS module; never replay sniffed write, coding or
  SecurityAccess traffic to a car.
- Prefer the hardware-free fakes and the fake pack for proofs of concept.
- Do not access, keep or publish other people's data (VINs, locations, session logs). If
  you come across any, stop, tell us, and delete it.

Good-faith research that follows this policy is welcome; we will not pursue it.

## Regulatory readiness

- **EU Cyber Resilience Act.** CRA reporting obligations apply from 2026-09-11 and the
  full requirements from 2027-12-11. Today the project publishes free open-source
  software; once official hardware is sold it acts as a manufacturer, and its exact CRA
  role still needs legal advice (standards research §8.4). We are building the
  groundwork now: this vulnerability-handling policy, a stated support period, SBOMs
  (SPDX and CycloneDX) and signed build provenance on every release, pinned and
  monitored dependencies (Dependabot, OpenSSF Scorecard), and machine-readable licences
  (REUSE).
- **UK PSTI** (connectable products): this page is the vulnerability-disclosure policy;
  the admin password is set per install and is never a shared default (with none set,
  admin is ungated, which is meant for local development only), and hardware will ship
  with unique per-device credentials.
