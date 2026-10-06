# SPDX-FileCopyrightText: 2026 OpenOstler contributors
# SPDX-FileCopyrightText: 2026 leijoma
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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

    # a Brain: read the car through the node's MQTT messages instead of a cable
    # (NodeSource, specs/2026-10-06-node-source-design.md; read-only, phase P1)
    PYTHONPATH=src python3 tools/dashboard.py --source node --mqtt mqtts://brain.local:8883 \
        --mqtt-ca ca.pem --mqtt-cert brain.crt --mqtt-key brain.key

    # a sniff feed for the admin Decode tab without a car (the homelab runs this):
    # ``pack`` loops the installed vehicle pack's demo sniff log (``demo.sniff_log``)
    PYTHONPATH=src python3 tools/dashboard.py --replay pack

Then open http://localhost:8080 (or the Pi's address in the car from your phone).
"""
import argparse
import os
import sys

# Make the tool runnable as "python3 tools/dashboard.py" without PYTHONPATH=src.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from openostler.pack import active_pack, canonical_module  # noqa: E402
from openostler.web.server import DiagServer  # noqa: E402


REPLAY_PACK = "pack"


def pack_replay_log(pack) -> "str | None":
    """The pack's demo sniff log (``--replay pack``), or None when it ships none. Keeps
    deploys (Dockerfile, compose) free of site-packages paths."""
    demo = pack.demo
    if demo is None or demo.sniff_log is None or not os.path.exists(demo.sniff_log):
        return None
    return str(demo.sniff_log)


def build_docs(pack, dict_path: "str | None" = None, extra_dirs=()):
    """The Docs tab from the pack's ``docs`` sources (canonical files, not copies).

    ``dict_path`` (``--dict``) replaces the path of the pack's optional answer-key source;
    any other optional source whose path is missing is skipped."""
    from openostler.web.docs import DocLibrary

    docs = DocLibrary()
    for src in pack.docs:
        path = src.path
        if src.optional:
            if dict_path:
                path = dict_path
            elif not os.path.exists(path):
                continue
        if src.recursive or os.path.isdir(path):
            docs.add_dir(path, group=src.group, recursive=src.recursive,
                         exclude=set(src.exclude))
        else:
            docs.add_file(path, title=src.title, group=src.group)
    for extra in extra_dirs:
        docs.add_dir(extra, group="Extra")
    return docs


def main() -> int:
    pack = active_pack()
    ap = argparse.ArgumentParser(description=f"{pack.name} realtime dashboard")
    ap.add_argument("--source", choices=("serial", "node"), default="serial",
                    help="serial (default): the K-line cable, the lab and dev path; node: the "
                         "node's MQTT messages (a Brain; read-only)")
    ap.add_argument("--serial", help="serial port of the K-line cable (omit → auto-detect)")
    ap.add_argument("--mqtt", metavar="URL",
                    help="--source node: the broker, mqtts://host[:8883] (the Brain's broker, "
                         "or the node's in the lab); there is no default address")
    ap.add_argument("--mqtt-ca", help="--source node: the CA certificate (PEM) of the broker")
    ap.add_argument("--mqtt-cert", help="--source node: this Brain's client certificate (PEM)")
    ap.add_argument("--mqtt-key", help="--source node: the client certificate's key (PEM)")
    ap.add_argument("--mqtt-client-id", default=None,
                    help="--source node: the MQTT client id (default <host>-nodesource)")
    ap.add_argument("--mqtt-insecure-lab", action="store_true",
                    help="--source node: allow a plain mqtt:// lab broker (no TLS); never in a car")
    ap.add_argument("--vid", default=None,
                    help="--source node: the vehicle id in the node's topics (default: "
                         "OSTLER_VEHICLE_ID, else this device's logs/vehicle.json vid)")
    ap.add_argument("--module", default=None,
                    help="module to start on (default: the vehicle pack's default, "
                         f"{pack.default_module}; one of {', '.join(pack.module_ids())})")
    # Old spelling of ``--module slabs`` (kept working, not advertised).
    ap.add_argument("--slabs", action="store_const", const="slabs", dest="slabs_alias",
                    help=argparse.SUPPRESS)
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
                    help="path to the fault-code dictionary (replaces the pack's optional "
                         "answer-key document)")
    ap.add_argument("--docs", action="append", default=[],
                    help="extra directory of .md files to show in the Docs tab (repeatable)")
    ap.add_argument("--sniff", metavar="PORT",
                    help="ESP32 sniff port for the Map tab (passive RX-only; reference tool polls)")
    ap.add_argument("--replay", metavar="FILE|pack",
                    help="replay a sniff log in the Map tab (for testing without a vehicle); "
                         "'pack' replays the vehicle pack's demo sniff log")
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
    ap.add_argument("--kline-detect", action="store_true",
                    help="allow K-line protocol detection and module-scan sweeps (probing an "
                         "unknown car), each only with a 'Vehicle parked?' confirmation and "
                         "no sign of motion; interim until the driving state (U2)")
    ap.add_argument("--kline-profile", metavar="NAME", default=None,
                    help="use this built-in K-line profile (iso9141_2, kwp2000_slow, "
                         "kwp2000_fast) for sources without a pack profile, for this process")
    args = ap.parse_args()
    if args.public and not args.admin_password:
        print("--public needs an admin password (--admin-password or D2DIAG_ADMIN_PW): "
              "without one every admin route would be open on a public bind.", file=sys.stderr)
        return 2
    if bool(args.tls_cert) != bool(args.tls_key):
        ap.error("--tls-cert and --tls-key must be given together")
    if args.source == "node" and args.serial:
        # One bus, one tester: the node holds the K-line; a cable beside it would collide
        # and bypass its transmit gate (NodeSource spec §14, owner answer 7).
        ap.error("--serial and --source node exclude each other: the node reads the car")
    if args.source == "node" and not args.mqtt:
        ap.error("--source node needs --mqtt mqtts://host[:port] (no hard-coded broker)")
    if args.gps.strip().lower() == "mock":
        ap.error("--gps mock was removed (ADR-0011: no demo mode); "
                 "use tests/e2e_server.py for a simulated car")
    geocoder = args.geocoder
    if geocoder is None:
        from openostler.geo.nominatim import DEFAULT_URL
        geocoder = DEFAULT_URL
    if geocoder.strip().lower() in ("", "off", "none"):
        geocoder = None

    # Raw bus log (TX/RX) for mapping — off by default, on with --raw-log.
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_log_dir = os.path.join(_repo, "logs") if args.raw_log else None
    # Pack state (e.g. the Td5 fuel computer's lifetime total, fuel_totals.json) lives in the
    # repo root (survives restart; gitignored).

    # The car's sources, one per module. They autodetect the port (``auto``) if none is
    # given → fail softly at poll time if the cable is missing. Only ONE module is active
    # at a time (K-line = shared bus). No simulated source exists in the product (ADR-0011).
    port = args.serial or "auto"
    gps_spec = args.gps
    gps = None
    try:
        from openostler.gps.reader import open_gps
        gps = open_gps(gps_spec)
    except Exception as exc:  # noqa: BLE001 — no GPS must never stop the dashboard
        print(f"GPS: unavailable for {gps_spec!r} ({type(exc).__name__}: {exc}) — continuing without")
    feed = None
    if args.source == "node":
        from openostler.logbook.vehicle import local_vid, state_dir_for
        from openostler.web.node_source import build_feed, node_sources
        vid = args.vid or local_vid(state_dir_for(args.sessions_dir or
                                                  os.path.join(_repo, "logs", "sessions")))
        try:
            feed = build_feed(args.mqtt, vid, ca=args.mqtt_ca, cert=args.mqtt_cert,
                              key=args.mqtt_key, insecure_lab=args.mqtt_insecure_lab,
                              client_id=args.mqtt_client_id)
        except (ValueError, OSError) as exc:  # ssl.SSLError is an OSError
            ap.error(f"--source node: {exc}")
        modules = node_sources(feed, pack.module_ids())
    else:
        modules = pack.sources(port, raw_log_dir=raw_log_dir, state_dir=_repo)
    active = canonical_module(args.module or args.slabs_alias) or pack.default_module
    if active not in modules:
        ap.error(f"unknown module {args.module or args.slabs_alias!r} "
                 f"(one of {', '.join(modules)})")

    logger = None
    log_path = args.log_file
    if not log_path and args.log_dir:
        import datetime as _dt
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        log_path = os.path.join(args.log_dir, f"session-{stamp}.jsonl")
    if log_path:
        from openostler.web.logger import SnapshotLogger
        logger = SnapshotLogger(log_path, min_interval=args.log_interval)

    # The Docs tab mirrors the CANONICAL source files the pack lists (not a copy).
    repo_root = _repo
    docs = build_docs(pack, args.dict_path, args.docs)

    # Map tab: passive sniff feed (live ESP32 or replayed log).
    sniffer = None
    if args.sniff:
        from openostler.web.sniffer import SnifferFeed
        sniffer = SnifferFeed.from_serial(args.sniff)
        print(f"Sniff (live): {args.sniff} → Map tab")
    elif args.replay:
        from openostler.web.sniffer import SnifferFeed
        if args.replay == REPLAY_PACK:
            args.replay = pack_replay_log(pack)
            if args.replay is None:
                ap.error(f"--replay {REPLAY_PACK}: the {pack.name} pack ships no demo sniff log")
        # looping replay so the freshness badge shows "LIVE" in the preview
        sniffer = SnifferFeed.from_file(args.replay, delay=0.008, loop=True)
        print(f"Sniff (replay): {args.replay} → Map tab (freshness demo)")

    # Labeled live captures (Capture tab) → durable JSONL dataset.
    captures_path = os.path.join(repo_root, "logs", "labeled_captures.jsonl")
    os.makedirs(os.path.dirname(captures_path), exist_ok=True)

    csv_dir = os.path.join(repo_root, "logs")
    sessions_dir = args.sessions_dir or os.path.join(csv_dir, "sessions")
    from openostler.community import Community  # opt-in community sharing (default OFF)
    community = Community()
    srv = DiagServer(
        host=args.host, port=args.port,
        poll_interval=args.interval, stream_interval=args.interval, logger=logger,
        active=active, menus=pack.menus, docs=docs, sniffer=sniffer, captures_path=captures_path,
        source=modules, scan_port=port, csv_dir=csv_dir, community=community,
        public=args.public, fault_watch=args.fault_watch,
        admin_password=args.admin_password,
        allow_shutdown=args.allow_shutdown,
        gps=gps, sessions_dir=sessions_dir,
        # Recording a node's values (sessions driven by its power and status, the raw tap)
        # is phase P2 of the NodeSource spec; until then a node source records nothing.
        record_sessions=feed is None,
        audio=args.audio, imu=args.imu, geocoder=geocoder,
        kline_detect=args.kline_detect, kline_profile=args.kline_profile,
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
    if feed is not None:
        feed.log = lambda msg: srv._conn_log(f"node: {msg}")
        feed.start()
        print(f"Node source: {args.mqtt} · vehicle {feed.vid} · read-only, not recording (P1)")
    else:
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
    finally:
        if feed is not None:
            feed.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
