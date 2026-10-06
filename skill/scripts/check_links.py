#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Check that documentation links and doc paths named in code still resolve.

Two checks, both stdlib only:
1. Every relative Markdown link ``[text](path)`` in a tracked ``.md`` file points at
   an existing file or directory (anchors and external URLs are ignored).
2. Every ``docs/…md`` or ``references/…md`` path mentioned in a ``.py`` file exists.

Exits non-zero on any dangling reference so it can gate CI.

Usage:
    python3 skill/scripts/check_links.py
"""

from __future__ import annotations

import os
import re
import sys

import _frontmatter as fm

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODE_PATH = re.compile(r"\b((?:docs|references)/[\w./-]+\.md)\b")
FENCE = re.compile(r"^(```|~~~)")


def _walk(root: str, suffix: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in fm.EXCLUDED_DIRS]
        for name in filenames:
            if name.endswith(suffix):
                yield os.path.join(dirpath, name)


def check_markdown(root: str):
    problems = []
    for path in _walk(root, ".md"):
        in_fence = False
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if FENCE.match(line.strip()):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                for target in MD_LINK.findall(line):
                    if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                        continue
                    target = target.split("#", 1)[0]
                    if not target:
                        continue
                    resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
                    if not os.path.exists(resolved):
                        problems.append(f"{os.path.relpath(path, root)}:{n}: {target}")
    return problems


def check_code(root: str):
    problems = []
    for path in _walk(root, ".py"):
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                for target in CODE_PATH.findall(line):
                    if not os.path.exists(os.path.join(root, target)):
                        problems.append(f"{os.path.relpath(path, root)}:{n}: {target}")
    return problems


def main() -> int:
    root = fm.repo_root()
    problems = check_markdown(root) + check_code(root)
    for p in problems:
        print(f"DANGLING {p}")
    if problems:
        print(f"\n{len(problems)} dangling reference(s).")
        return 1
    print("OK — all documentation links and code doc-paths resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
