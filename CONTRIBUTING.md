---
title: "Contributing"
area: root
status: stable
version: 1.1
updated: 2026-10-06
summary: >
  How to contribute: read order, AGPL/CC BY-SA licences and the CLA, REUSE/SPDX headers, which third-party licences may be reused, design-first, commit messages (Conventional Commits recommended), pre-commit and the checks to run before committing; vulnerabilities go to SECURITY.md.
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
- **Licence headers (REUSE).** Every file states its licence
  ([REUSE 3.3](https://reuse.software/spec-3.3/)). Give a new source file an SPDX header,
  for example
  `reuse annotate --copyright "OpenOstler contributors" --year 2026 --license AGPL-3.0-or-later <file>`;
  data, generated and binary files are covered by globs in [REUSE.toml](REUSE.toml)
  instead. Keep existing copyright lines, including leijoma's on MIT-era code.
  `reuse lint` must pass.
- **Design first.** Non-trivial changes start as a spec in `specs/`.
- **Commit messages.** Keep commits small and logical, with a short summary line. The
  history uses "Area: sentence"; [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  (`feat(ui): …`, `fix: …`, `docs: …`, `BREAKING CHANGE:`) are recommended but not
  enforced until releases are automated (ADR-0017). Add notable changes to
  [CHANGELOG.md](CHANGELOG.md) under *Unreleased*.
- **Security issues** never go in public issues or pull requests; see
  [SECURITY.md](SECURITY.md).
- **pre-commit.** `pip install -e ".[dev]" pre-commit && pre-commit install` runs ruff,
  `reuse lint`, the frontmatter validator and the `INDEX.md` freshness check on each
  commit (`pre-commit run --all-files` to run them by hand).
- **Before committing:** `pytest -q`, `ruff check .` and `reuse lint`; for UI changes
  `cd ui && npm run check`; after doc edits
  `python3 skill/scripts/validate_frontmatter.py && python3 skill/scripts/build_index.py`.
