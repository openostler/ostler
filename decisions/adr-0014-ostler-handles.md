---
title: "ADR-0014 — Ostler handles: openostler org and package, @ostler npm, @ostler.tech; trademark policy"
area: decisions
status: locked
version: 1.3
updated: 2026-10-06
depends_on: [decisions/adr-0013-repo-split-and-vehicle-pack-contract.md, decisions/adr-0012-licence-agplv3-dual-and-cc-by-sa-data.md]
summary: >
  Amends ADR-0013's naming: brand and trademark "Ostler" on ostler.tech; GitHub org, PyPI distribution and Python import "openostler"; npm @ostler (+ @openostler); entry-point group "openostler.vehicle" (legacy "ostler.vehicle" read for one release); MQTT root and HA domain "ostler"; Bluesky @ostler.tech; avoid ostler-tech/ostlertech; TRADEMARKS.md policy and a name-protection checklist.
---

# ADR-0014 — Ostler handles and the trademark policy

> **Amended 2026-10-06 ([ADR-0032](adr-0032-one-node-optional-brain.md), ADR-0034):** the product family adds "Ostler Lite" and "Ostler"; "node" and "brain" are working names; the guardian is a node variant.
> **Amended by [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md), 2026-10-06:** the product family is Ostler Diagnostics, Ostler Guardian and Ostler Hub; read "Ostler Lite" as "Ostler Diagnostics". See [Amendments (product family)](#amendments-2026-10-06-product-family).
> **Amended 2026-10-06 (Brain rename, [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)):** read "Ostler Hub" and "Hub" (the product, also "hub" for the box) as "Ostler Brain" and "Brain". See [Amendments (Brain rename)](#amendments-2026-10-06-brain-rename).

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

## Amendments (2026-10-06)

Amended with the owner's direction of 2026-10-06 (ADR-0032, one node with an optional
brain; [ADR-0034](adr-0034-repo-boundaries.md), repo boundaries). The handles above stand.
1. **Product family.** The brand split adds two tiers: **Ostler Lite** (the ESP32 node
   alone, with the phone app or Ostler Cloud) and **Ostler** (the node plus a Pi brain).
   Ostler Cloud stays as named.
2. **Working names.** "Node" and "brain" are working names, not yet product names;
   "Ostler Node" above is one of them.
3. **The guardian is a node variant.** "Ostler Guardian" names a hardware variant of the
   node (same firmware, built for security), not a separate product line or an add-on.
4. **Repos.** The org also gets `ostler-pack-<x>` repos, and later `ostler-hardware` and a
   module contract repo (ADR-0034).

## Amendments (2026-10-06, product family)

With [ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md) (accepted with the owner's answers of 2026-10-06). The handles and the Amendments
above stand; where this entry differs, it wins.

5. **Product family renamed.** The family is **Ostler Diagnostics** (the OBD-port node,
   standalone with a phone or linked to a hub; was "Ostler Lite"), **Ostler Guardian** (the
   hidden node variant) and **Ostler Hub** (the brain; was the "Ostler" tier). Read "Ostler
   Lite" in Amendment 1 as "Ostler Diagnostics", and "Ostler" there as "Ostler Diagnostics +
   Ostler Hub". "Node" and "brain" stay the internal terms (Amendment 2); "brain" is also an
   informal synonym for the Hub. Ostler Cloud stays as named.

## Amendments (2026-10-06, Brain rename)

- **Names.** Read "Ostler Hub" and "Hub" above (and "hub" where it means our compute box) as
  "Ostler Brain" and "Brain" ([ADR-0039](adr-0039-product-family-diagnostics-guardian-hub.md#amendments-2026-10-06-brain-rename)). The decision text and the Amendments above are
  unchanged.
