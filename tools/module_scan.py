# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Read-only K-line address scan: who is on the bus, and how do they init?

    PYTHONPATH=src python3 tools/module_scan.py auto
    PYTHONPATH=src python3 tools/module_scan.py /dev/cu.usbserial-XXXX --esp
    PYTHONPATH=src python3 tools/module_scan.py auto --fast 13,29 --slow 18,40,5a,5b

Walks the Discovery 2 diagnostic addresses, tries fast and 5-baud init on each, and
prints who answered with which key bytes — to confirm or rule out the asserted-only
modules (cruise, HEVAC, instrument pack, IDM, the 0x18 responder) before a NanoCom
rental. **Read-only by construction:** it sends only init and StopCommunication, and
releases the link after every probe (see ``CONSTITUTION.md``). The logic is in
:mod:`openostler.modscan` so it is unit-tested against the fake ECU.

Ignition on, car stationary. This takes a while — each address gets a quiet settle so a
link can die before the next init.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from openostler.kline import KLine  # noqa: E402
from openostler.kwp2000 import KWP2000  # noqa: E402
from openostler.modscan import DEFAULT_FAST, DEFAULT_SLOW, AddressScanner, render_table  # noqa: E402
from openostler.transport import EspTransport, SerialTransport  # noqa: E402


def _addrs(spec: "str | None", default: "list[int]") -> "list[int]":
    if not spec:
        return default
    return [int(x, 16) for x in spec.replace(" ", "").split(",") if x]


def main() -> int:
    ap = argparse.ArgumentParser(description="Read-only K-line address scan")
    ap.add_argument("port", help="serial device, or 'auto' to detect the cable")
    ap.add_argument("--esp", action="store_true", help="talk over an ESP32 in cable mode")
    ap.add_argument("--fast", help="comma hex fast-init addresses (default 13,29)")
    ap.add_argument("--slow", help="comma hex 5-baud addresses (default 18,40,5a,5b)")
    ap.add_argument("--settle", type=float, default=2.0, help="quiet seconds between probes")
    args = ap.parse_args()

    port = args.port
    if not args.esp:
        from openostler.ports import resolve_serial_port
        port = resolve_serial_port(args.port)
        if port != args.port:
            print(f"Using cable at {port}")

    transport = EspTransport(port) if args.esp else SerialTransport(port, timeout=1.0)
    kwp = KWP2000(KLine(transport), tolerant=True)
    kwp.open()
    try:
        scanner = AddressScanner(kwp, settle=args.settle, progress=lambda m: print("  ·", m))
        rows = scanner.scan(_addrs(args.fast, DEFAULT_FAST), _addrs(args.slow, DEFAULT_SLOW))
    finally:
        kwp.close()
    print()
    sys.stdout.write(render_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
