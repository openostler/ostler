"""Serial-port resolution — find the KKL/OBD USB cable's device path.

Core utility: given a spec or ``"auto"``, return a concrete serial device path.
Deliberately kept OUT of the ``transport`` package (which imports pyserial) so it
stays importable without pyserial — the mock data sources depend on that. No protocol
knowledge, no web/storage: just device discovery.
"""
from __future__ import annotations

import glob

# Chip hints for recognising a KKL/OBD cable among several USB serial devices.
_KKL_HINTS = ("ft232", "ftdi", "ch340", "cp210", "usb-serial", "usb_uart", "obd", "kkl")

# macOS call-out ports (use cu.*, NEVER tty.* — tty blocks on DCD).
_MAC_GLOBS = (
    "/dev/cu.usbserial-*", "/dev/cu.usbmodem*",
    "/dev/cu.wchusbserial*", "/dev/cu.SLAB_USBtoUART*",
)


def resolve_serial_port(spec: "str | None") -> str:
    """Return a concrete serial port.

    A ``spec`` that is a real path is returned unchanged. ``None`` or
    ``"auto"`` auto-detects a USB serial device. Order: **stable**
    ``/dev/serial/by-id/`` links (Linux) → ``/dev/cu.*`` (macOS) → ``ttyUSB*`` /
    ``ttyACM*``. Within by-id and cu.*, a known KKL chip (``_KKL_HINTS``) is preferred.
    Raises :class:`FileNotFoundError` if none is found (e.g. the cable not plugged in
    yet) — called again on every connection attempt.
    """
    if spec and spec != "auto":
        return spec
    by_id = sorted(glob.glob("/dev/serial/by-id/*"))
    mac = sorted(p for pat in _MAC_GLOBS for p in glob.glob(pat))
    preferred_id = [p for p in by_id if any(h in p.lower() for h in _KKL_HINTS)]
    preferred_mac = [p for p in mac if any(h in p.lower() for h in _KKL_HINTS)]
    for candidates in (preferred_id, by_id, preferred_mac, mac,
                       sorted(glob.glob("/dev/ttyUSB*")),
                       sorted(glob.glob("/dev/ttyACM*"))):
        if candidates:
            return candidates[0]
    raise FileNotFoundError("no USB serial device found (KKL not connected?)")


def list_serial_ports() -> "list[str]":
    """Every plausible KKL/OBD serial device, best candidates first (for a port picker).

    Stdlib globs: ``/dev/serial/by-id/*`` (stable Linux links), the macOS ``/dev/cu.*``
    call-out ports, then ``/dev/ttyUSB*`` and ``/dev/ttyACM*``. When pyserial is installed
    its ``list_ports`` adds USB devices the globs miss (only ones with a USB VID, so the
    dozens of legacy ``/dev/ttyS*`` never show). macOS ``/dev/tty.*`` is never offered
    (it blocks on DCD). Never raises: an empty list means no cable is plugged in.
    """
    by_id = sorted(glob.glob("/dev/serial/by-id/*"))
    mac = sorted(p for pat in _MAC_GLOBS for p in glob.glob(pat))
    groups = [
        [p for p in by_id if any(h in p.lower() for h in _KKL_HINTS)], by_id,
        [p for p in mac if any(h in p.lower() for h in _KKL_HINTS)], mac,
        sorted(glob.glob("/dev/ttyUSB*")), sorted(glob.glob("/dev/ttyACM*")),
    ]
    try:  # optional: pyserial is the one allowed runtime dependency, but not required here
        from serial.tools import list_ports  # type: ignore[import-not-found]

        groups.append(sorted(p.device for p in list_ports.comports()
                             if getattr(p, "vid", None) is not None))
    except Exception:  # noqa: BLE001 — no pyserial, or enumeration failed: globs suffice
        pass
    out: "list[str]" = []
    for group in groups:
        for p in group:
            if p not in out and not p.startswith("/dev/tty."):
                out.append(p)
    return out
