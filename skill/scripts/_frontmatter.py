# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Shared helpers for Vibes as Code tooling (stdlib only).

Parses the minimal YAML frontmatter subset this repo uses and decides which
files are manifest-eligible. Single source of truth for both build_index.py and
validate_frontmatter.py. Schema mirrors the upstream Vibes as Code conventions/frontmatter.md; vendored
from https://github.com/JamesWrightDavid/Vibes-as-Code and adapted for this repo.
"""

from __future__ import annotations

import os

# Schema (upstream: Vibes-as-Code conventions/frontmatter.md; area enum is project-specific).
REQUIRED_FIELDS = ["title", "area", "status", "version", "updated", "summary"]
AREA_ENUM = {
    "root",
    "docs",
    "references",
    "hardware",
    "decisions",
    "specs",
}
STATUS_ENUM = {"stable", "draft", "locked", "superseded"}

# Files excluded from the manifest (no frontmatter expected).
EXCLUDED_BASENAMES = {"README.md", "CLAUDE.md", "INDEX.md"}
# Directories never scanned (process artifacts / VCS).
# Vendored third-party trees, build output and raw car data are not ours to index.
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "logs", "captures", "dist", "build",
    "muki01_OBD2_K-line_Reader", "__pycache__", ".pytest_cache",
}
# Project-specific: legal text, not documentation.
EXCLUDED_BASENAMES |= {"THIRD_PARTY_LICENSES.md"}
# Soft limit from the method (one topic per file); reported as a warning only.
MAX_LINES = 300


def repo_root() -> str:
    """Repo root, two levels up from this file (skill/scripts/ -> root)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def iter_manifest_files(root: str):
    """Yield repo-relative paths of manifest-eligible .md files, sorted."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for name in filenames:
            if not name.endswith(".md") or name in EXCLUDED_BASENAMES:
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def parse_frontmatter(text: str):
    """Parse leading YAML frontmatter.

    Returns (data, error). data is a dict of the minimal subset supported:
    plain scalars, folded scalars (``key: >``), and inline lists
    (``key: [a, b]``). error is None on success or a human-readable string.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "missing opening '---' frontmatter delimiter"

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "missing closing '---' frontmatter delimiter"

    data = {}
    i = 1
    while i < end:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in raw:
            return None, f"malformed frontmatter line: {raw!r}"

        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()

        if value == ">" or value == "|":
            # Folded/literal scalar: collect more-indented following lines.
            parts = []
            i += 1
            while i < end and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
                parts.append(lines[i].strip())
                i += 1
            data[key] = " ".join(p for p in parts if p).strip()
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            data[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        else:
            data[key] = value.strip().strip('"').strip("'")
        i += 1

    return data, None


def load(path: str):
    """Read a file and parse its frontmatter. Returns (data, error)."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_frontmatter(fh.read())
    except OSError as exc:  # pragma: no cover - defensive
        return None, f"could not read file: {exc}"
