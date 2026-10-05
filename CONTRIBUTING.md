---
title: "Contributing"
area: root
status: stable
version: 1.0
updated: 2026-10-06
summary: >
  How to contribute: read order, AGPL/CC BY-SA licences and the CLA, which third-party licences may be reused, design-first, and the checks to run before committing.
---

# Contributing

Thanks for helping. Start with [CLAUDE.md](CLAUDE.md) → [INDEX.md](INDEX.md) →
[CONSTITUTION.md](CONSTITUTION.md); the constitution's hard rules (safety gates, data
honesty, no writes to the car without a gate) apply to every change.

- **Licences.** Code is AGPL-3.0-or-later ([LICENSE](LICENSE)); vehicle data is
  CC BY-SA 4.0 ([LICENSE-DATA](LICENSE-DATA)). By opening a pull request you agree to the
  [Contributor License Agreement](CLA.md) — the CLA Assistant bot asks you to sign once.
- **Third-party material.** Only reuse code whose licence is compatible with AGPL-3.0
  (MIT, BSD, Apache-2.0, ISC, MPL-2.0, LGPL, GPL-3.0, GPL-2.0-*or-later*, AGPL-3.0).
  GPL-2.0-*only*, non-commercial (CC BY-NC), unlicensed and dealer/proprietary material
  must not be copied — facts may be re-derived and verified against our own captures.
  Record every reuse in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
- **Design first.** Non-trivial changes start as a spec in `specs/`.
- **Before committing:** `pytest -q`; for UI changes `cd ui && npm run check`; after doc
  edits `python3 skill/scripts/validate_frontmatter.py && python3 skill/scripts/build_index.py`.
