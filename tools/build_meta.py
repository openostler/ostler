#!/usr/bin/env python3
"""Write BUILD_COMMIT and BUILD_TIME into a source tree (the Docker build's meta stage).

The image keeps no ``.git``, so ``openostler.version`` reads these files instead. The commit
is read straight from ``.git`` (HEAD, a loose ref or packed-refs), so no git binary is
needed. A missing or unreadable ``.git`` writes an empty BUILD_COMMIT ("unknown").

    python tools/build_meta.py /src
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path


def head_commit(git: Path) -> str:
    try:
        head = (git / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not head.startswith("ref: "):
        return head                                    # detached HEAD: the sha itself
    ref = head[5:]
    loose = git / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    packed = git / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            sha, _, name = line.partition(" ")
            if name == ref:
                return sha
    return ""


def main(root: str) -> int:
    base = Path(root)
    sha = head_commit(base / ".git")
    (base / "BUILD_COMMIT").write_text(sha + "\n" if sha else "", encoding="utf-8")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (base / "BUILD_TIME").write_text(now + "\n", encoding="utf-8")
    print(f"build meta: commit {sha or 'unknown'}, built {now}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
