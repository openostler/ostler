"""Regenerate the committed synthetic demo logs (ADR-0009, ADR-0010, ADR-0011).

    PYTHONPATH=src python3 tools/make_demo_session.py [--out DIR]

Writes "Demo log 1" and "Demo log 2" to ``src/d2diag/vehicles/lr_d2/demo/sessions/<id>/`` (data CSV
parts, meta.json with name, description and offline place names, events.jsonl and
notes.jsonl) deterministically: the same code and gazetteer always produce byte-identical
files. The logic lives in ``d2diag.vehicles.lr_d2.synth`` (the pack's ``demo.generate``).
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from d2diag.pack import active_pack  # noqa: E402


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    demo = active_pack().demo
    if demo is None or demo.generate is None:
        raise SystemExit("the active vehicle pack ships no demo generator")
    ap.add_argument("--out", default=str(demo.sessions_dir),
                    help="target root (default: the pack's demo sessions dir)")
    args = ap.parse_args(argv)
    for sid in demo.generate(args.out):
        path = os.path.join(args.out, sid)
        size = sum(os.path.getsize(os.path.join(path, f)) for f in os.listdir(path))
        print(f"wrote {path} ({size / 1024:.0f} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
