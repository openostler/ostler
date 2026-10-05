"""Regenerate the offline place-name table ``src/d2diag/geo/places.tsv.gz`` from GeoNames.

    PYTHONPATH=src python3 tools/build_places.py [--cache DIR] [--out FILE] [--no-download]

Downloads ``cities1000.zip``, ``admin1CodesASCII.txt``, ``admin2Codes.txt`` and
``countryInfo.txt`` into the cache dir (skipped when present), then writes the trimmed,
deterministic table. Data: GeoNames, CC BY 4.0. Logic lives in ``d2diag.geo.build``.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from d2diag.geo.build import DEFAULT_CACHE, DEFAULT_OUT, build, download  # noqa: E402


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cache", default=DEFAULT_CACHE, help=f"download cache (default: {DEFAULT_CACHE})")
    ap.add_argument("--out", default=DEFAULT_OUT, help="output file (default: the package copy)")
    ap.add_argument("--no-download", action="store_true", help="use only what is already cached")
    args = ap.parse_args(argv)
    if not args.no_download:
        download(args.cache)
    info = build(args.cache, args.out)
    print(f"wrote {args.out}: {info['rows']} places, {info['bytes'] / 1e6:.2f} MB, dump {info['date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
