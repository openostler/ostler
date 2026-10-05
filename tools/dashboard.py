"""Start the realtime dashboard (always against the car — there is no demo mode, ADR-0011).

    # the car (the port is auto-detected when --serial is omitted):
    PYTHONPATH=src python3 tools/dashboard.py --serial /dev/cu.usbserial-12345678

    # GPS for the session logbook: USB receiver (default: auto-probe, none when absent),
    # off, or replay an .nmea file:
    PYTHONPATH=src python3 tools/dashboard.py --serial /dev/ttyUSB0 --gps /dev/ttyACM0

    # UI development without a car: the test-only server with simulated sources
    PYTHONPATH=src python3 tests/e2e_server.py --port 8080

Every connected period is recorded to --sessions-dir (default logs/sessions) and browsed
in the Logs tab (specs/2026-10-05-session-logbook-design.md); the session index is
<sessions-dir>.sqlite and place names are refined via --geocoder (default: OSM Nominatim;
``off`` disables it).

    # opt-in cabin audio (arecord) and a Pi IMU; HTTPS so the phone mic/motion work
    # (ADR-0010; switched on per device from the Logs tab's recording options):
    PYTHONPATH=src python3 tools/dashboard.py --audio pi --imu auto \
        --tls-cert pi.crt --tls-key pi.key

    # a sniff feed for the admin Decode tab without a car (the homelab runs this):
    PYTHONPATH=src python3 tools/dashboard.py --replay src/d2diag/vehicles/lr_d2/demo/sniff-demo.txt

Then open http://localhost:8080 (or the Pi's address in the car from your phone).
"""
import argparse
import os
import sys

# Make the tool runnable as "python3 tools/dashboard.py" without PYTHONPATH=src.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from d2diag.web import InfoDataSource, SlabsDataSource, Td5DataSource  # noqa: E402
from d2diag.web.server import DiagServer  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Discovery 2 realtime dashboard")
    ap.add_argument("--serial", help="serial port of the K-line cable (omit → auto-detect)")
    ap.add_argument("--slabs", action="store_true",
                    help="SLABS source instead of Td5 (fast init 0x29; requires a transmitting cable)")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080, help="HTTP port (default 8080)")
    ap.add_argument("--interval", type=float, default=0.5, help="poll/stream interval (s)")
    ap.add_argument("--log-file", help="log data to this JSONL file")
    ap.add_argument("--log-dir", help="log to DIR/session-<time>.jsonl (auto-named)")
    ap.add_argument("--log-interval", type=float, default=2.0,
                    help="min seconds between log rows (a fault change is always logged)")
    ap.add_argument("--csv", action="store_true",
                    help="start CSV live-data logging immediately (logs/livedata-<time>.csv)")
    ap.add_argument("--public", action="store_true",
                    help="public/simple UI: home page + TD5/SLABS/Faults only "
                         "(hide Map/Capture/Docs + actuators)")
    ap.add_argument("--fault-watch", action="store_true",
                    help="poll fault codes every cycle (~0.5s) to catch intermittent faults")
    ap.add_argument("--admin-password", default=os.environ.get("D2DIAG_ADMIN_PW"),
                    help="password for the /admin mapping console (Basic Auth). "
                         "Also read from D2DIAG_ADMIN_PW. Unset → admin is ungated "
                         "(fine on localhost, NOT on a public bind).")
    ap.add_argument("--dict", dest="dict_path",
                    help="path to the fault-code dictionary (default: sibling repo 'Discovery 2/')")
    ap.add_argument("--docs", action="append", default=[],
                    help="extra directory of .md files to show in the Docs tab (repeatable)")
    ap.add_argument("--sniff", metavar="PORT",
                    help="ESP32 sniff port for the Map tab (passive RX-only; reference tool polls)")
    ap.add_argument("--replay", metavar="FILE",
                    help="replay a sniff log in the Map tab (for testing without a vehicle)")
    ap.add_argument("--raw-log", action="store_true",
                    help="log ALL raw TX/RX to logs/raw-<module>-<time>.log (for mapping). "
                         "Appends across reconnects; one file per module per run.")
    ap.add_argument("--allow-shutdown", action="store_true",
                    help="expose a 'Shut down Pi' button in Settings (set on the Pi's "
                         "systemd unit; needs passwordless sudo for shutdown)")
    ap.add_argument("--gps", default="auto", metavar="auto|none|PATH",
                    help="GPS source for the session logbook: auto (probe a USB NMEA "
                         "receiver; none if absent, the default), none, or a serial port / "
                         ".nmea replay file")
    ap.add_argument("--sessions-dir", default=None,
                    help="where recorded sessions go (default: <repo>/logs/sessions)")
    ap.add_argument("--audio", choices=("off", "pi"), default="off",
                    help="cabin audio on the Pi: off (default) or pi (arecord, 16 kHz mono; "
                         "still opt-in per session from the recording options)")
    ap.add_argument("--imu", choices=("auto", "none"), default="auto",
                    help="Pi IMU for acceleration: auto (LSM6DS on /dev/i2c-1; none if "
                         "absent, the default) or none")
    ap.add_argument("--geocoder", default=None, metavar="URL|off",
                    help="reverse geocoder that refines session place names (OSM Nominatim "
                         "API; ≤1 request/s, cached). Default: "
                         "https://nominatim.openstreetmap.org; off disables it")
    ap.add_argument("--tls-cert", help="serve HTTPS with this certificate (PEM); needs "
                                       "--tls-key. The phone mic and motion sensors need HTTPS")
    ap.add_argument("--tls-key", help="private key (PEM) for --tls-cert")
    args = ap.parse_args()
    if bool(args.tls_cert) != bool(args.tls_key):
        ap.error("--tls-cert and --tls-key must be given together")
    if args.gps.strip().lower() == "mock":
        ap.error("--gps mock was removed (ADR-0011: no demo mode); "
                 "use tests/e2e_server.py for a simulated car")
    geocoder = args.geocoder
    if geocoder is None:
        from d2diag.geo.nominatim import DEFAULT_URL
        geocoder = DEFAULT_URL
    if geocoder.strip().lower() in ("", "off", "none"):
        geocoder = None

    # Raw bus log (TX/RX) for mapping — off by default, on with --raw-log.
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_log_dir = os.path.join(_repo, "logs") if args.raw_log else None
    # The fuel computer's lifetime total is persisted here (survives restart). Gitignored.
    fuel_state_path = os.path.join(_repo, "fuel_totals.json")

    # The car's sources, one per module. They autodetect the port (``auto``) if none is
    # given → fail softly at poll time if the cable is missing. Only ONE module is active
    # at a time (K-line = shared bus). No simulated source exists in the product (ADR-0011).
    port = args.serial or "auto"
    gps_spec = args.gps
    gps = None
    try:
        from d2diag.gps.reader import open_gps
        gps = open_gps(gps_spec)
    except Exception as exc:  # noqa: BLE001 — no GPS must never stop the dashboard
        print(f"GPS: unavailable for {gps_spec!r} ({type(exc).__name__}: {exc}) — continuing without")
    modules = {
        "motor": Td5DataSource(port, raw_log_dir=raw_log_dir, fuel_state_path=fuel_state_path),
        "slabs": SlabsDataSource(port, raw_log_dir=raw_log_dir),
        # Modules with no live-signal reader yet (faults/info only): selectable, and they
        # report honestly that they aren't readable on the car yet — nothing fabricated.
        "airbag": InfoDataSource("airbag", live_message=(
            "Airbag/SRS is read-only by construction; live fault read is experimental "
            "and not wired into the dashboard yet. Use 'Scan all modules'.")),
        "ace": InfoDataSource("ace", live_message=(
            "ACE uses a proprietary bulk protocol that isn't decoded yet.")),
        "autobox": InfoDataSource("autobox", live_message=(
            "The EAT gearbox answers but its fault payload isn't decoded yet.")),
        "bcu": InfoDataSource("bcu", live_message=(
            "The BCU has no conventional fault memory; its inputs/outputs aren't "
            "wired into the dashboard yet.")),
    }
    active = "slabs" if args.slabs else "motor"

    logger = None
    log_path = args.log_file
    if not log_path and args.log_dir:
        import datetime as _dt
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = os.path.join(args.log_dir, f"session-{stamp}.jsonl")
    if log_path:
        from d2diag.web.logger import SnapshotLogger
        logger = SnapshotLogger(log_path, min_interval=args.log_interval)

    from d2diag.menus import MENUS  # module menu registry for the Map tab
    from d2diag.web.docs import DocLibrary  # markdown view for the Docs tab

    # The Docs tab mirrors the CANONICAL source files (not a copy):
    #   Answer key = the fault-code dictionary in the register repo (sibling folder 'Discovery 2/')
    #   Docs = the curated knowledge base docs/**.md; Reference = references/**.md
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dict_path = args.dict_path or os.path.join(
        os.path.dirname(repo_root), "Discovery 2", "discovery2_reference tool_fault_dictionary.md")
    docs = DocLibrary()
    # The test backlog first: it is what you read on the phone while sitting in the car.
    docs.add_file(os.path.join(repo_root, "references", "test_plan.md"), group="Test plan")
    docs.add_file(dict_path, title="reference tool fault-code dictionary (answer key)", group="Answer key")
    agent_only = {"CLAUDE.md", "muki01_OBD2_K-line_Reader"}
    docs.add_dir(os.path.join(repo_root, "docs"), group="Docs", recursive=True,
                 exclude=agent_only)
    docs.add_dir(os.path.join(repo_root, "references"), group="Reference", recursive=True,
                 exclude={"test_plan.md"} | agent_only)
    for extra in args.docs:
        docs.add_dir(extra, group="Extra")

    # Map tab: passive sniff feed (live ESP32 or replayed log).
    sniffer = None
    if args.sniff:
        from d2diag.web.sniffer import SnifferFeed
        sniffer = SnifferFeed.from_serial(args.sniff)
        print(f"Sniff (live): {args.sniff} → Map tab")
    elif args.replay:
        from d2diag.web.sniffer import SnifferFeed
        # looping replay so the freshness badge shows "LIVE" in the preview
        sniffer = SnifferFeed.from_file(args.replay, delay=0.008, loop=True)
        print(f"Sniff (replay): {args.replay} → Map tab (freshness demo)")

    # Labeled live captures (Capture tab) → durable JSONL dataset.
    captures_path = os.path.join(repo_root, "logs", "labeled_captures.jsonl")
    os.makedirs(os.path.dirname(captures_path), exist_ok=True)

    csv_dir = os.path.join(repo_root, "logs")
    sessions_dir = args.sessions_dir or os.path.join(csv_dir, "sessions")
    from d2diag.community import Community  # opt-in community sharing (default OFF)
    community = Community()
    srv = DiagServer(
        host=args.host, port=args.port,
        poll_interval=args.interval, stream_interval=args.interval, logger=logger,
        active=active, menus=MENUS, docs=docs, sniffer=sniffer, captures_path=captures_path,
        source=modules, scan_port=port, csv_dir=csv_dir, community=community,
        public=args.public, fault_watch=args.fault_watch,
        admin_password=args.admin_password,
        allow_shutdown=args.allow_shutdown,
        gps=gps, sessions_dir=sessions_dir,
        audio=args.audio, imu=args.imu, geocoder=geocoder,
    )
    scheme = "http"
    if args.tls_cert:
        try:
            srv.enable_tls(args.tls_cert, args.tls_key)
        except (OSError, ValueError) as exc:  # ssl.SSLError is an OSError
            srv.server_close()
            print(f"TLS: cannot load {args.tls_cert} / {args.tls_key} "
                  f"({type(exc).__name__}: {exc})")
            return 2
        scheme = "https"
    if raw_log_dir:
        print(f"Raw TX/RX log → {raw_log_dir}/raw-<module>-<time>.log")
    if args.admin_password:
        print("Admin: /admin (mapping console) — password protected")
    elif args.host not in ("127.0.0.1", "localhost"):
        print("Admin: /admin OPEN (no --admin-password) — set one for a public bind")
    print(f"Docs: {len(docs.index())} in the Docs tab")
    print(f"Captures → {captures_path}")
    rs = srv.recording_sources()
    print(f"Recording sources: Pi audio {rs['pi_audio']['state']}"
          f"{' (' + rs['pi_audio']['reason'] + ')' if rs['pi_audio'].get('reason') else ''}"
          f" · IMU {rs['imu']['state']}"
          f"{' (' + rs['imu']['reason'] + ')' if rs['imu'].get('reason') else ''}")
    print(f"Dashboard: {scheme}://localhost:{args.port}   (modules: {', '.join(modules)} · active: {active})")
    print(f"Live port: {port}")
    print(f"Place names: {'geocoder ' + geocoder if geocoder and not args.public else 'offline only'}")
    print(f"GPS: {gps_spec} → {getattr(gps, 'src', None) or 'none'} · sessions → {sessions_dir}"
          f"{'' if srv._recorder is not None else ' (recording unavailable)'}")
    if log_path:
        print(f"Logging data → {log_path}")
    if args.csv:
        print(f"CSV live log → {srv.start_csv().get('path')}")
    print("Ctrl-C to quit.")
    # `docker stop` / systemd send SIGTERM: treat it like Ctrl-C so the open logbook
    # session is closed (meta.json end_utc) instead of being left "recording".
    import signal

    def _term(_signum, _frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _term)
    except ValueError:  # not on the main thread (e.g. embedded) — keep the default
        pass
    try:
        srv.serve()
    except KeyboardInterrupt:
        srv.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
