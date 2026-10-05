"""Test/dev-only dashboard with a SIMULATED car (ADR-0011: the product has no demo mode).

Builds a ``DiagServer`` from ``tests/fake_sources.py``: the motor, SLABS and info modules
(airbag/ACE/EAT/BCU), the synthetic GPS loop, the simulated fault scan and a looping demo
sniff replay for the admin Decode tab. The geocoder is always off and sessions go to a
throwaway directory (default: a fresh temp dir), seeded with one closed, editable
(non-synthetic) session so Playwright can test inline name/description edits. The two
committed demo logs are listed as usual.

Playwright (run from ui/) and UI development without a car:

    python3 ../tests/e2e_server.py --host 127.0.0.1 --port 8765 --interval 0.3 \
        --replay e2e/sniff-demo.txt --admin-password e2e

``--start disconnected`` starts with polling paused (snapshot ``conn: disconnected``), for
the connection-sheet flows. Never deploy this: it fabricates every value it serves.
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import tempfile
import time

_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
for _p in (os.path.join(_REPO, "src"), _REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from d2diag.web.server import DiagServer  # noqa: E402
from tests.fake_sources import FakeGps, fake_fault_report, fake_modules  # noqa: E402

DEMO_SNIFF = os.path.join(_REPO, "src", "d2diag", "web", "demo", "sniff-demo.txt")
SEED_START_S = 1_788_250_000.0  # 2026-09-01 — the seeded editable session


class _Fix:
    """Just enough of ``gps.Fix`` for the recorder."""

    def __init__(self, lat: float, lon: float, speed_kmh: float, utc_ms: int) -> None:
        self.lat, self.lon, self.speed_kmh = lat, lon, speed_kmh
        self.heading, self.alt_m, self.sats, self.hdop = 45.0, 300.0, 9, 0.9
        self.fix, self.utc_ms, self.mono = True, utc_ms, time.monotonic()


def seed_session(root: str) -> "str | None":
    """Record one short, closed, real (non-synthetic) session into ``root``; its id."""
    from d2diag.logbook.recorder import SessionRecorder

    clock = {"t": SEED_START_S, "m": 1000.0}
    rec = SessionRecorder(root, clock=lambda: clock["t"], mono=lambda: clock["m"],
                          source="live")
    lat, lon = 56.6400, -4.7600  # open moorland (synthetic)
    for i in range(40):
        fix = _Fix(lat, lon, 40.0, int(clock["t"] * 1000))
        rec.feed({"conn": "connected", "status": "connected", "module": "motor",
                  "signals": {"rpm": {"v": 1500 + 10 * i, "u": "rpm"},
                              "speed": {"v": 40.0, "u": "km/h"},
                              "coolant_temp": {"v": 70 + i * 0.3, "u": "°C"}},
                  "faults": []}, fix)
        lat += 0.0002
        lon += 0.0001
        clock["t"] += 0.5
        clock["m"] += 0.5
    sid = (rec.status() or {}).get("session")
    rec.close()
    return sid


def build(args) -> DiagServer:
    sessions_dir = args.sessions_dir or os.path.join(tempfile.mkdtemp(prefix="d2diag-e2e-"),
                                                     "sessions")
    os.makedirs(sessions_dir, exist_ok=True)
    if not args.no_seed and not any(os.scandir(sessions_dir)):
        seed_session(sessions_dir)
    gps = None if args.no_gps else FakeGps()
    sniffer = None
    if args.replay != "off":
        from d2diag.web.sniffer import SnifferFeed
        sniffer = SnifferFeed.from_file(args.replay, delay=0.008, loop=True)
    from d2diag.menus import MENUS
    from d2diag.web.docs import DocLibrary  # the Docs tab, as tools/dashboard.py builds it
    docs = DocLibrary()
    docs.add_file(os.path.join(_REPO, "references", "test_plan.md"), group="Test plan")
    agent_only = {"CLAUDE.md", "muki01_OBD2_K-line_Reader"}
    docs.add_dir(os.path.join(_REPO, "docs"), group="Docs", recursive=True, exclude=agent_only)
    docs.add_dir(os.path.join(_REPO, "references"), group="Reference", recursive=True,
                 exclude={"test_plan.md"} | agent_only)
    srv = DiagServer(
        fake_modules(gps=gps), host=args.host, port=args.port,
        poll_interval=args.interval, stream_interval=args.interval,
        active="slabs" if args.slabs else "motor", menus=MENUS, docs=docs, sniffer=sniffer,
        captures_path=os.path.join(os.path.dirname(sessions_dir), "labeled_captures.jsonl"),
        csv_dir=os.path.dirname(sessions_dir), public=args.public,
        admin_password=args.admin_password, gps=gps, sessions_dir=sessions_dir,
        imu="mock" if args.imu else "none", fault_scan=fake_fault_report, geocoder=None,
    )
    if args.start == "disconnected":
        srv._disconnect()
    return srv


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser(description="Simulated-car dashboard for tests/UI dev")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--interval", type=float, default=0.5, help="poll/stream interval (s)")
    ap.add_argument("--replay", default=DEMO_SNIFF,
                    help="sniff log looped into the Decode tab (default: the demo; off = none)")
    ap.add_argument("--admin-password", default=None)
    ap.add_argument("--public", action="store_true")
    ap.add_argument("--slabs", action="store_true", help="start on the SLABS module")
    ap.add_argument("--sessions-dir", default=None, help="default: a fresh temp dir")
    ap.add_argument("--no-seed", action="store_true", help="do not seed an editable session")
    ap.add_argument("--no-gps", action="store_true", help="no simulated GPS")
    ap.add_argument("--imu", action="store_true", help="a simulated Pi IMU")
    ap.add_argument("--start", choices=("connected", "disconnected"), default="connected")
    args = ap.parse_args(argv)
    srv = build(args)
    print(f"e2e server (SIMULATED car): http://{args.host}:{srv.server_address[1]} "
          f"· sessions → {srv._sessions_dir}", flush=True)

    def _term(_signum, _frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _term)
    except ValueError:
        pass
    try:
        srv.serve()
    except KeyboardInterrupt:
        srv.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
