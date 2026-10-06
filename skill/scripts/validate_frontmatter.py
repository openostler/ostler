#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Lint frontmatter across the repo.

Checks every manifest-eligible Markdown file for required fields, valid area/
status enum values, and an ISO-date `updated` field. Exits non-zero on any
violation so it can gate CI. Stdlib only.

Usage:
    python3 skill/scripts/validate_frontmatter.py
"""

from __future__ import annotations

import re
import sys

import _frontmatter as fm

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_file(path: str):
    """Return a list of error strings for one file (empty if valid)."""
    data, err = fm.load(path)
    if err:
        return [err]

    errors = []
    for field in fm.REQUIRED_FIELDS:
        if field not in data or data[field] in (None, "", []):
            errors.append(f"missing required field: {field}")

    area = data.get("area")
    if area is not None and area not in fm.AREA_ENUM:
        errors.append(f"invalid area {area!r}; expected one of {sorted(fm.AREA_ENUM)}")

    status = data.get("status")
    if status is not None and status not in fm.STATUS_ENUM:
        errors.append(
            f"invalid status {status!r}; expected one of {sorted(fm.STATUS_ENUM)}"
        )

    updated = data.get("updated")
    if updated is not None and not ISO_DATE.match(str(updated)):
        errors.append(f"updated {updated!r} is not an ISO date (YYYY-MM-DD)")

    return errors


def length_warning(path: str):
    """Return a warning string if the file exceeds the one-topic-per-file limit."""
    with open(path, "r", encoding="utf-8") as fh:
        n = sum(1 for _ in fh)
    if n > fm.MAX_LINES:
        return f"{n} lines (> {fm.MAX_LINES}): consider splitting along its seams"
    return None


def main() -> int:
    root = fm.repo_root()
    files = fm.iter_manifest_files(root)
    total_errors = 0
    warnings = 0

    for rel in files:
        warn = length_warning(f"{root}/{rel}")
        if warn:
            warnings += 1
            print(f"WARN {rel}: {warn}")
        errors = validate_file(f"{root}/{rel}")
        if errors:
            total_errors += len(errors)
            print(f"FAIL {rel}")
            for e in errors:
                print(f"     - {e}")

    checked = len(files)
    if total_errors:
        print(f"\n{total_errors} problem(s) across {checked} file(s).")
        return 1
    print(f"OK — {checked} file(s) passed frontmatter validation ({warnings} length warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
