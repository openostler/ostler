---
title: "ADR-0014 — Ostler handles: openostler org and package, @ostler npm, @ostler.tech; trademark policy"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md]
summary: >
  Amends ADR-0013's naming: brand and trademark "Ostler" on ostler.tech; GitHub org, PyPI distribution and Python import "openostler"; npm @ostler (+ @openostler); entry-point group "openostler.vehicle" (legacy "ostler.vehicle" read for one release); MQTT root and HA domain "ostler"; Bluesky @ostler.tech; avoid ostler-tech/ostlertech; TRADEMARKS.md policy and a name-protection checklist.
---

# ADR-0014 — Ostler handles and the trademark policy

- **Date:** 2026-10-06
- **Status:** accepted (owner, 2026-10-06). It amends the naming in ADR-0013.

## Context

The owner bought **ostler.tech** and wants to protect the name. Informal checks on
2026-10-05 found the following. They are not a legal clearance search; see
`references/research/` and the agent report in the session.

- **`ostler` is taken** on GitHub (a user account) and on PyPI. The PyPI distribution
  installs a module named `ostler`, so a platform import called `ostler` would collide
  with it.
- **`ostler-tech` / `ostlertech` belong to someone else in practice.** A Turkish app
  developer, OstlerTech, owns ostlertech.com, the YouTube channel @OstlerTech and a GitHub
  repo.
- **`openostler` is free** on GitHub, PyPI, npm and Mastodon. openostler.com, .org, .io and
  .dev look unregistered. The npm scopes `@ostler` and `@openostler` do not exist yet.
- **No OSTLER mark is registered at the USPTO.** UKIPO, EUIPO and WIPO could not be queried
  and need a manual search.
- **Other software already uses the name**, none of it in vehicles:
  - ostler.ai, a Hong Kong AI app that writes "Ostler™";
  - ostler.io, an Australian/New Zealand inventory product;
  - getostler.com, US hotel software.
- **Companies House:** THE OSTLER LTD probably blocks "Ostler Ltd".

## Decision

| Thing | Name |
|---|---|
| Brand and trademark | **Ostler** (OSTLER word mark); website **ostler.tech** |
| GitHub org | **`openostler`**. Repos: `openostler/ostler` (platform), `openostler/ostler-firmware`, `openostler/ostler-cloud` (private). This repo stays `discovery2-diag` as the D2 pack. |
| Python | distribution **and import** **`openostler`** (`src/d2diag` becomes `src/openostler` at the split) |
| Vehicle-pack entry-point group | **`openostler.vehicle`**. `ostler.vehicle` is still read for one release. |
| npm | **`@ostler`** (claimed together with `@openostler`) |
| MQTT topic root and Home Assistant domain | **`ostler`** |
| Socials | **`openostler`** everywhere; Bluesky **`@ostler.tech`** (DNS-verified) |
| Defensive registrations | GitHub orgs `ostler-tech` and `ostlerhq`, the openostler domains, ostler-tech.com |

- **Brand split:**
  - **Ostler** is the product family: Ostler Cloud, Ostler Guardian, Ostler Node.
  - **OpenOstler** is the open-source code and community.
- **Packs:** "Ostler pack *for* Land Rover Discovery 2". JLR marks are never part of our
  brand.
- **`TRADEMARKS.md`:** the AGPL grants no rights to the name. Forks and redistributions
  must rename unless they have permission.

## Name-protection checklist

These are owner actions.

1. **Now:**
   - Create the GitHub org `openostler` (plus `ostler-tech` and `ostlerhq`).
   - Claim npm `@ostler` and `@openostler`, plus a placeholder `ostler` package.
   - Publish a 0.0.1 placeholder for `openostler` on PyPI.
   - Set Bluesky `@ostler.tech`.
   - Take `openostler` on X, Instagram, YouTube, Reddit, Fosstodon and TikTok.
   - Buy openostler.com, .org, .io and .dev, plus ostler-tech.com.
2. **This week:**
   - Run a manual UKIPO, TMview and WIPO search (OSTLER, OSLER, HOSTLER).
   - File the OSTLER word mark at UKIPO with a vehicle-specific specification:

     | Class | Covers |
     |---|---|
     | 9 | Diagnostic and telematics apparatus, trackers, software |
     | 12 | Vehicle alarms and immobilisers |
     | 42 | Telematics and diagnostics SaaS |

     That is about £325 online, at the fees in force from 1 April 2026; confirm before
     filing.
3. **When incorporating:** use e.g. "Ostler Technologies Ltd". A company name gives no
   trademark rights.
4. **Ongoing:**
   - Use "Ostler™" consistently.
   - Keep dated evidence of use.
   - Set a TMview watch alert.
5. **Within 6 months of the UK filing:** extend through Madrid Protocol (EU, US) if selling
   there.

## Consequences

- ADR-0013's `ostler` import and repo names are replaced by the table above.
- `src/d2diag/pack.py` reads `openostler.vehicle`, and `pyproject.toml` registers under it.
- Step 2 of ADR-0013 (the repo split) waits for the `openostler` org to exist.
