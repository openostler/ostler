---
title: "ADR-0012 — AGPL-3.0-or-later code with a commercial licence; CC BY-SA 4.0 vehicle data; CLA"
area: decisions
status: locked
version: 1.0
updated: 2026-10-06
depends_on: [CONSTITUTION.md, THIRD_PARTY_LICENSES.md]
summary: >
  The project moves from MIT to AGPL-3.0-or-later for code, with a paid commercial licence on request (dual licensing), CC BY-SA 4.0 for vehicle data, and a contributor licence agreement; funding is planned through hardware sales and a cloud subscription, protected by a trademark.
---

# ADR-0012 — AGPL code + commercial licence; CC BY-SA data; CLA

- **Date:** 2026-10-06
- **Status:** accepted (owner decision, 2026-10-05)

## Context

- **The project is changing shape.** It is growing from a D2 Td5 reader into an open
  vehicle platform covering diagnostics, logging, telemetry, tracking and alarm
  ([platform research](../references/research/platform.md)).
- **How the owner wants to fund it:**
  - keep it open source;
  - fund it later through **hardware sales** and a **cloud subscription**;
  - not allow closed commercial use for free.
- **Why MIT no longer fits:** it allows anyone to ship a closed fork or host a paid copy.
- **Why a non-commercial licence doesn't fit:** licences such as PolyForm NC or CC BY-NC
  are not open source, and they would stop us reusing GPL code from the ecosystem.

## Decision

**Code is AGPL-3.0-or-later** (`LICENSE`).
- The network clause makes anyone hosting a modified copy publish its source.
- That covers the planned cloud.

**A commercial licence is available on request.**
- It is for companies that want closed, embedded or hosted use without the AGPL obligations.
- This dual licensing is the funding route, alongside hardware sales and the cloud subscription.

**Vehicle data is CC BY-SA 4.0** (`LICENSE-DATA`). This covers:
- signals JSON;
- DTC JSON;
- fault-code tables;
- future vehicle packs.

CC BY-SA is share-alike, and it is the same licence OBDb uses, so we can exchange
packs with it.

**A Contributor License Agreement** (`CLA.md`, Apache-ICLA style) is signed through the
CLA Assistant bot. Contributors keep their copyright, and the maintainer may relicense
their contributions, which is what makes the commercial licence possible.

**The name will be protected as a UK trademark**, to cover "official hardware" and the
"official cloud".

**What third-party code we may reuse:**

| Licence | Reuse? |
|---|---|
| MIT, BSD, Apache-2.0, ISC | Yes |
| LGPL, MPL-2.0 | Yes |
| GPL-3.0, GPL-2.0-or-later, AGPL-3.0 | Yes |
| GPL-2.0-only | No |
| Non-commercial (CC BY-NC, PolyForm NC) | No |
| No licence at all | No |
| Dealer or proprietary databases | No (see the DMCA precedent below) |

Every reuse is recorded in `THIRD_PARTY_LICENSES.md`.

## Consequences

- **Earlier releases stay MIT.** Anything published before 2026-10-06 remains MIT for
  whoever obtained it. Contributions already merged under MIT, including the outside
  contributor `leijoma`, may be relicensed, because MIT allows sublicensing. Their notices
  are kept.
- **GPL-3 projects become usable**, with attribution: freediag, AndrOBD, WiCAN,
  rovergauge/libcomm14cux, ddt4all, CanZE and the BinOwl Td5 gauge.
- **Still off-limits:** python-OBD (its GPL-2.0-only vs -or-later status must be
  verified first), Navit, OwnTracks-Android (EPL-1.0), and all non-commercial or
  unlicensed repos.
- **DMCA lesson:** OpenVehicleDiag's SMR-D parser was removed after a DMCA takedown. We
  ship only our own declarative data, never converted dealer databases.
- **Open question:** is the cloud fully AGPL (like Home Assistant / Nabu Casa), or a
  separate proprietary service behind a documented MQTT/HTTP protocol (open core)?
  Deciding this settles where the cloud code lives. It needs its own ADR.

## Alternatives considered

- **Keep MIT.** Rejected: it gives no protection for the hardware and cloud model.
- **GPL-3.0.** Rejected: hosted copies don't have to share source.
- **PolyForm Noncommercial / CC BY-NC.** Rejected: not open source, and it blocks GPL
  reuse and drives away contributors.
- **FSL/BSL with delayed open source.** Rejected: not open source until each release
  converts.
