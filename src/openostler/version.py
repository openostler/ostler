"""What is running: the platform and vehicle-pack versions and commits (``GET /version``).

The Settings sheet shows this so a dev server can be matched to a commit at a glance.
A commit is found, in order, from:

1. the ``OSTLER_COMMIT`` / ``OSTLER_PACK_COMMIT`` environment variable;
2. a ``BUILD_COMMIT`` file at the source root (the Docker image writes one, because the
   image keeps no ``.git``);
3. ``git rev-parse HEAD`` in a source checkout.

Otherwise it is ``None``. The build time comes the same way (``OSTLER_BUILT``, or a
``BUILD_TIME`` file). Nothing here reads the vehicle or leaves the device.
"""
from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__

PLATFORM_SOURCE = "https://github.com/openostler/ostler"
_STARTED = time.time()


def _read(path: Path) -> "str | None":
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return text or None


def _git_head(root: Path) -> "str | None":
    if not (root / ".git").exists():
        return None
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.SubprocessError):
        return None
    sha = out.stdout.strip()
    return sha if out.returncode == 0 and sha else None


def _source_root(start: Path) -> "Path | None":
    """The nearest ancestor of ``start`` holding a ``pyproject.toml`` (a source tree)."""
    for p in [start, *start.parents][:5]:
        if (p / "pyproject.toml").is_file():
            return p
    return None


def _commit(env: str, roots: "list[Path | None]") -> "str | None":
    sha = os.environ.get(env, "").strip()
    if sha:
        return sha
    for root in roots:
        if root is None:
            continue
        sha = _read(root / "BUILD_COMMIT") or _git_head(root)
        if sha:
            return sha
    return None


def _dist_version(name: str) -> "str | None":
    from importlib import metadata
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def _source_url(dist) -> "str | None":
    """The distribution's ``Source`` project URL, if it declares one."""
    for entry in (dist.metadata.get_all("Project-URL") or []):
        label, _, url = entry.partition(",")
        if label.strip().lower() in ("source", "repository"):
            return url.strip() or None
    return None


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _platform_roots() -> "list[Path | None]":
    # A source checkout (editable install, PYTHONPATH=src), then the working directory:
    # the Docker image installs the package into site-packages but runs from /app.
    return [_source_root(Path(__file__).resolve().parent), _source_root(Path.cwd())]


def _pack_info(pack) -> dict:
    """The active pack's id, name, version, commit and source URL."""
    from importlib import import_module

    from .pack import _entry_points

    info = {"id": pack.id, "name": pack.name, "version": None, "commit": None, "source": None}
    for ep in _entry_points():
        try:
            if ep.load() is not pack:
                continue
        except Exception:  # noqa: BLE001 - a broken sibling entry point is not ours
            continue
        dist = getattr(ep, "dist", None)
        if dist is not None:
            info["version"] = dist.version
            info["source"] = _source_url(dist)
        mod = import_module(ep.value.partition(":")[0])
        root = _source_root(Path(mod.__file__).resolve().parent) if getattr(mod, "__file__", None) else None
        info["commit"] = _commit("OSTLER_PACK_COMMIT", [root])
        break
    return info


def build_info(pack=None) -> dict:
    """The ``GET /version`` body."""
    if pack is None:
        from .pack import active_pack
        pack = active_pack()
    built = os.environ.get("OSTLER_BUILT", "").strip() or next(
        (t for t in (_read(r / "BUILD_TIME") for r in _platform_roots() if r) if t), None)
    return {
        "platform": {
            "name": "Ostler",
            "version": _dist_version("openostler") or __version__,
            "commit": _commit("OSTLER_COMMIT", _platform_roots()),
            "source": PLATFORM_SOURCE,
        },
        "pack": _pack_info(pack),
        "built": built,
        "started": _iso(_STARTED),
    }
