#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build ``src/openostler/metrics.json`` and ``src/openostler/vss_leaves.json`` from the
pinned COVESA VSS release and the Ostler overlay (ADR-0016).

Dev-only: it needs vss-tools (``pip install -e ".[dev]"`` on Python >= 3.11), which runs
``vspec export json`` over ``vss/upstream/model.vspec`` with ``vss/ostler.vspec`` and the
extended attributes. The Pi never runs this; it reads the committed JSON.

* ``metrics.json`` lists every leaf the overlay names (annotated VSS nodes and the
  ``Vehicle.Ostler.*`` extensions): path, type, datatype, unit, description,
  ``ostler_role`` and the aliases (OVMS, Home Assistant, OBDb). Sorted by path.
* ``vss_leaves.json`` lists every leaf of the pinned upstream tree with its unit (null when
  it has none), so ``openostler.metrics.is_known`` accepts any standard VSS path.

Checks (any failure exits 1): the vendored ``model.vspec`` still exports to the vendored
release ``vss.json``; an overlay entry for an existing node restates its upstream ``type``;
every unit is a verbatim key of ``vss/upstream/units.yaml``; the OVMS and OBDb aliases are
unique; no fuel node takes an OVMS ``v.b.*`` alias (fuel is never ``v.b.soc``).

    python tools/build_metrics.py           # regenerate both files
    python tools/build_metrics.py --check   # exit 1 if either committed file is stale
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VSS = ROOT / "vss"
UPSTREAM = VSS / "upstream"
OVERLAY = VSS / "ostler.vspec"
METRICS = ROOT / "src" / "openostler" / "metrics.json"
LEAVES = ROOT / "src" / "openostler" / "vss_leaves.json"

# The overlay's extended attributes (ADR-0016). Order is the order they appear in output.
ALIASES = ("ovms", "ha_device_class", "ha_state_class", "obdb", "ha_domain")
ATTRIBUTES = ("ostler_role", *ALIASES)
UNIQUE_ALIASES = ("ovms", "obdb")          # names of one meaning; HA classes are shared
EXTENSION = "Vehicle.Ostler"
FUEL = "Vehicle.Powertrain.FuelSystem."


class BuildError(Exception):
    pass


def vss_tools_available() -> bool:
    return importlib.util.find_spec("vss_tools") is not None


def _vspec() -> str:
    exe = shutil.which("vspec") or os.path.join(os.path.dirname(sys.executable), "vspec")
    if not os.path.exists(exe):
        raise BuildError("vss-tools is not installed: pip install -e '.[dev]' (Python >= 3.11)")
    return exe


def export(overlay: "Path | None" = None) -> dict:
    """``vspec export json`` over the vendored release (plus ``overlay``) → the tree."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        cmd = [_vspec(), "export", "json", "-s", str(UPSTREAM / "model.vspec"),
               "-u", str(UPSTREAM / "units.yaml"), "-q", str(UPSTREAM / "quantities.yaml"),
               "-o", str(out)]
        if overlay is not None:
            cmd += ["-l", str(overlay)]
            for a in ATTRIBUTES:
                cmd += ["-e", a]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out.exists():
            raise BuildError(f"vspec export failed ({proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
        return json.loads(out.read_text(encoding="utf-8"))


def leaves(tree: dict) -> "dict[str, dict]":
    """Every leaf of an exported tree: path → node (without ``children``)."""
    out: "dict[str, dict]" = {}

    def walk(node: dict, path: str) -> None:
        kids = node.get("children")
        if kids is None:
            out[path] = node
            return
        for name, child in kids.items():
            walk(child, f"{path}.{name}")

    for name, node in tree.items():
        walk(node, name)
    return out


def unit_keys(path: Path = UPSTREAM / "units.yaml") -> "set[str]":
    import yaml  # a vss-tools dependency (dev-only)

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return set(data)


def overlay_entries(path: Path = OVERLAY) -> dict:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BuildError(f"{path}: not a mapping")
    return data


def build_metrics(overlaid: dict, upstream: dict, entries: dict, units: "set[str]") -> dict:
    """The metrics.json document. Raises BuildError on any rule violation."""
    errors: "list[str]" = []
    up = leaves(upstream)
    ov = leaves(overlaid)
    rows = []
    for path, entry in entries.items():
        entry = entry or {}
        if entry.get("type") == "branch":
            continue
        if path not in ov:
            errors.append(f"{path}: not a leaf after the overlay")
            continue
        if not path.startswith(EXTENSION + "."):
            if path not in up:
                errors.append(f"{path}: not in the pinned VSS tree (extensions go under {EXTENSION})")
                continue
            if entry.get("type") != up[path].get("type"):
                errors.append(f"{path}: restated type {entry.get('type')!r} differs from "
                              f"upstream {up[path].get('type')!r}")
            for k in ("datatype", "unit", "description"):
                if k in entry and entry[k] != up[path].get(k):
                    errors.append(f"{path}: the overlay changes upstream {k!r}")
        node = ov[path]
        unit = node.get("unit")
        if unit is not None and unit not in units:
            errors.append(f"{path}: unit {unit!r} is not a key of units.yaml")
        row = {
            "path": path,
            "type": node.get("type"),
            "datatype": node.get("datatype"),
            "unit": unit,
            "description": node.get("description", ""),
            "ostler_role": node.get("ostler_role"),
            "aliases": {a: node[a] for a in ALIASES if node.get(a)},
            "extension": path.startswith(EXTENSION + "."),
        }
        if node.get("allowed"):  # a fixed value set (a labelled enum on the module bus)
            row["allowed"] = list(node["allowed"])
        rows.append(row)
    for a in UNIQUE_ALIASES:
        seen: "dict[str, str]" = {}
        for r in rows:
            v = r["aliases"].get(a)
            if v is None:
                continue
            if v in seen:
                errors.append(f"{a} alias {v!r} on both {seen[v]} and {r['path']}")
            seen[v] = r["path"]
    for r in rows:
        ovms = r["aliases"].get("ovms", "")
        if ovms == "v.b.soc" or (r["path"].startswith(FUEL) and ovms.startswith("v.b.")):
            errors.append(f"{r['path']}: fuel is never published as an OVMS battery metric")
    if errors:
        raise BuildError("\n".join(errors))
    rows.sort(key=lambda r: r["path"])
    return {
        "vss_version": (VSS / "VERSION").read_text(encoding="utf-8").strip(),
        "generated_by": "tools/build_metrics.py from vss/ostler.vspec over vss/upstream",
        "metrics": rows,
    }


def build_leaves(upstream: dict) -> dict:
    up = leaves(upstream)
    return {
        "vss_version": (VSS / "VERSION").read_text(encoding="utf-8").strip(),
        "generated_by": "tools/build_metrics.py from vss/upstream/vss.json",
        "leaves": {p: up[p].get("unit") for p in sorted(up)},
    }


def render(doc: dict, compact: bool = False) -> str:
    if compact:   # one leaf per line: small and diff-friendly
        return json.dumps(doc, indent=0, ensure_ascii=False, sort_keys=True) + "\n"
    return json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def generate() -> "dict[Path, str]":
    """Run vss-tools and return {output path: file text}."""
    release = json.loads((UPSTREAM / "vss.json").read_text(encoding="utf-8"))
    if export() != release:
        raise BuildError("vss/upstream/model.vspec no longer exports to vss/upstream/vss.json: "
                         "the vendored release files disagree")
    overlaid = export(OVERLAY)
    metrics = build_metrics(overlaid, release, overlay_entries(), unit_keys())
    return {METRICS: render(metrics), LEAVES: render(build_leaves(release), compact=True)}


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if a committed file differs from a fresh build")
    args = ap.parse_args(argv)
    try:
        out = generate()
    except BuildError as exc:
        print(f"build_metrics: {exc}", file=sys.stderr)
        return 1
    stale = []
    for path, text in out.items():
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old == text:
            continue
        if args.check:
            stale.append(path.relative_to(ROOT))
        else:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("build_metrics: stale, run python tools/build_metrics.py: "
              + ", ".join(map(str, stale)), file=sys.stderr)
        return 1
    if args.check:
        print("build_metrics: metrics.json and vss_leaves.json are current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
