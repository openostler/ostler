# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The ``ostler`` command (``[project.scripts]``).

- ``ostler share verify <bundle.zip> [--json]`` (trip-sharing spec §9.3): exit 0 when the
  bundle passes, 1 when it fails (each failing check and its rule are printed), 2 when the
  file is unreadable or not ``ostler.share/1``.
- ``ostler share build --session <session dir> --level L0..L4 [...]`` (TS1, the File
  path): builds, verifies and saves one bundle on the owner's device, and appends the
  owner-only audit entry (the map from the bundle's fresh ids back to the real ones) to
  ``<state dir>/share_audit.jsonl``. Exit 0 with the bundle's path, 1 when the share is
  refused or blocked by the verifier.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import List, Optional


def _verify(args) -> int:
    from .logbook.share import verify_bundle

    res = verify_bundle(args.bundle, wmi=args.wmi)
    if args.json:
        print(json.dumps(res.to_json(), indent=1))
    else:
        print(res.report())
    return res.exit_code


def _audit(state_dir: str, path: str, bundle, options) -> None:
    os.makedirs(state_dir, exist_ok=True)
    entry = {"created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "file": os.path.basename(path), "bundle_id": bundle.manifest["id"],
             "level": options.level, "audience": options.audience, "path": options.path,
             "redactions": bundle.report, "id_map": bundle.id_map}
    fd = os.open(os.path.join(state_dir, "share_audit.jsonl"),
                 os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _build(args) -> int:
    from .logbook.share import (ShareBlocked, ShareOptions, ShareRefused, ZoneStore,
                                build_share, write_share)
    from .logbook.share.trace import TrimRefused

    session = os.path.abspath(args.session)
    state_dir = args.state_dir or os.path.dirname(os.path.dirname(session))
    vehicle = {k: getattr(args, k) for k in ("make", "model", "year", "engine", "market",
                                             "kind") if getattr(args, k)}
    opts = ShareOptions(
        level=args.level, audience=args.audience, path="file", recipient=args.recipient,
        route=args.route, ends_m=args.ends, zones=ZoneStore(state_dir).list(),
        signals=args.signals.split(",") if args.signals else None,
        include_notes=args.notes, public_destination=args.public_destination,
        vehicle=vehicle, request={"kind": args.request} if args.request else None,
        contribution_consent=args.consent, credit=args.credit, wmi=args.wmi)
    try:
        bundle = build_share(session, opts)
    except (ShareRefused, TrimRefused) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    except ShareBlocked as exc:
        print("blocked by the verifier (nothing was written):", file=sys.stderr)
        for f in exc.failures:
            print(f"  check {f.check} ({f.rule}) {f.file or ''}: {f.detail}", file=sys.stderr)
        return 1
    path = write_share(bundle, args.out)
    _audit(state_dir, path, bundle, opts)
    print(path)
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ostler", description="Ostler command line")
    sub = p.add_subparsers(dest="cmd", required=True)
    share = sub.add_parser("share", help="per-trip sharing bundles (ostler.share/1)")
    ss = share.add_subparsers(dest="share_cmd", required=True)

    v = ss.add_parser("verify", help="verify a bundle: exit 0 pass, 1 fail, 2 unreadable")
    v.add_argument("bundle")
    v.add_argument("--json", action="store_true", help="print the result as JSON")
    v.add_argument("--wmi", help="the vehicle's own WMI (owner's device only)")
    v.set_defaults(fn=_verify)

    b = ss.add_parser("build", help="build, verify and save one bundle (the File path)")
    b.add_argument("--session", required=True, help="a recorded session directory")
    b.add_argument("--level", required=True, choices=["L0", "L1", "L2", "L3", "L4"])
    b.add_argument("--audience", default="me",
                   choices=["me", "person", "group", "household", "maintainers", "helpers"])
    b.add_argument("--recipient", help="the one named person's name")
    b.add_argument("--route", action="store_true", help="tick L1 (route) on L2–L4")
    b.add_argument("--ends", type=int, default=500, help="ends trim in metres (200–1500)")
    b.add_argument("--signals", help="L2: comma-separated channels or VSS paths")
    b.add_argument("--notes", action="store_true", help="include notes marked shareable")
    b.add_argument("--public-destination", action="store_true",
                   help="a public thread or issue: no location, relative time")
    b.add_argument("--request", choices=["decode", "diagnose", "show"])
    b.add_argument("--consent", action="store_true",
                   help="CC BY-SA 4.0 for derived data (off by default)")
    b.add_argument("--credit", help="the name for attribution (with --consent)")
    for k in ("make", "model", "year", "engine", "market"):
        b.add_argument(f"--{k}")
    b.add_argument("--kind", choices=["car", "motorcycle"])
    b.add_argument("--wmi", help="the vehicle's own WMI (owner's device only)")
    b.add_argument("--state-dir", help="where privacy zones and the share audit live "
                                       "(default: the logs directory)")
    b.add_argument("--out", default=".", help="directory to save the bundle in")
    b.set_defaults(fn=_build)
    return p


def main(argv: "Optional[List[str]]" = None) -> int:
    args = parser().parse_args(argv)
    try:
        return int(args.fn(args))
    except BrokenPipeError:  # pragma: no cover
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
