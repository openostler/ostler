"""Regenerate the committed synthetic demo session (ADR-0009).

    PYTHONPATH=src python3 tools/make_demo_session.py [--out DIR]

Writes ``src/d2diag/logbook/demo/<id>/`` (data.csv + meta.json) deterministically: the
same code always produces byte-identical files. The logic lives in
``d2diag.logbook.synth``.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from d2diag.logbook.demo import DEMO_ROOT  # noqa: E402
from d2diag.logbook.synth import generate  # noqa: E402


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=DEMO_ROOT, help="target root (default: the package demo dir)")
    args = ap.parse_args(argv)
    sid = generate(args.out)
    path = os.path.join(args.out, sid)
    size = sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path))
    print(f"wrote {path} ({size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
