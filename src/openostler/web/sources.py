"""Data sources for the dashboard: the platform half of the snapshot boundary.

A ``DataSource`` supplies a snapshot (``poll()``) with status, signals
(name → value/unit) and fault codes. The vehicle pack supplies the real readers
(``active_pack().sources(port, …)``, e.g. the Discovery 2 Td5 and SLABS sources);
``InfoDataSource`` stands in for modules not readable yet. This module holds only the
generic pieces the pack sources build on (raw logging, the serial transport, the
``read_block`` primitive) and never imports a vehicle pack.
There is no simulated source in the product (ADR-0011): the fakes the tests and the UI
end-to-end server use live in ``tests/fake_sources.py``.
"""
from __future__ import annotations

import abc
import datetime as _dt
import os

from ..ports import resolve_serial_port  # noqa: F401 — re-exported (core port resolver)


class _RawLogPaused:
    """Suspend a LoggingTransport's raw TX/RX file for one read (the VIN block).

    The raw bus log is for mapping; the ``1A 87`` reply carries the VIN and must never be
    written anywhere. Walks ``session._kwp._k._t`` and, if it is a logging wrapper, swaps
    its file handle out for the duration and writes a redaction marker instead."""

    def __init__(self, session) -> None:
        kwp = getattr(session, "_kwp", None)
        kline = getattr(kwp, "_k", None)
        self._t = getattr(kline, "_t", None)
        self._fh = None
        self._echo = False

    def __enter__(self):
        t = self._t
        if t is not None and hasattr(t, "_fh") and hasattr(t, "_log"):
            self._fh, self._echo = t._fh, getattr(t, "_echo", False)
            if self._fh is not None:
                try:
                    self._fh.write("# 1A identity read — raw bytes redacted (VIN)\n")
                except Exception:  # noqa: BLE001
                    pass
            t._fh, t._echo = None, False
        return self

    def __exit__(self, *exc) -> None:
        t = self._t
        if t is not None and hasattr(t, "_fh") and hasattr(t, "_log"):
            t._fh, t._echo = self._fh, self._echo


def _raw_log_path(module: str, raw_log_dir: "str | None") -> "str | None":
    """Path for a raw TX/RX log, or None if raw logging is off.

    One file per module and dashboard start (``raw-<module>-<time>.log``).
    LoggingTransport opens in append mode, so reconnects (module switch,
    error retry) continue in the SAME file — an unbroken bus log for mapping."""
    if not raw_log_dir:
        return None
    os.makedirs(raw_log_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(raw_log_dir, f"raw-{module}-{stamp}.log")


def _transport(port: str, raw_log_path: "str | None"):
    """SerialTransport, optionally wrapped in LoggingTransport for a raw TX/RX log.

    Lazy import so the package imports without pyserial. When raw logging is on,
    LoggingTransport sits transparently under KLine and captures every byte both ways."""
    from ..transport import SerialTransport
    inner = SerialTransport(port, timeout=1.0)
    if raw_log_path:
        from ..transport import LoggingTransport
        return LoggingTransport(inner, logfile=raw_log_path)
    return inner


def _sleep_kw(hook) -> "dict":
    """``{"sleep": hook}`` if a hook exists, otherwise empty (keep time.sleep)."""
    return {} if hook is None else {"sleep": hook}


class DataSource(abc.ABC):
    """The snapshot API — the defined boundary between interpretation and consumers.

    This is the contract every consumer (the dashboard/SSE, file logging, Influx, the
    ESP's POST payload) is built on; see SCOPE.md. A source produces a normalized
    snapshot from the core (comms + interpretation); consumers never reach below it into
    the protocol stack.

    ``poll()`` returns the snapshot::

        {
          "status": "connected" | "no-cable" | "connecting" | "error" | …,
          "source": <module name>,
          "signals": { <name>: {"v": value, "u": unit, "s": status, "c": confidence} },
          "faults":  [ <fault description>, … ],
          "error":   <message>,          # optional, only on failure
        }

    Per signal: ``v`` value, ``u`` unit, ``s`` status ("ok"/"low"/"high"/"suspect"/None),
    ``c`` confidence ("proven"/"candidate"). ``menu_map()`` and ``command()`` are the
    coverage-map and write-command halves of the same boundary.
    """

    name: str = "source"
    # The signal-store / command-registry module this source talks to (td5, slabs, …);
    # the server uses it for the command gate (openostler.commands.refusal).
    store_module: "str | None" = None
    on_progress = None  # callback(str): live status during blocking establishment (base: none)
    # sleep hook for the establishment's wait times (the SLABS quiet period is 28 s). The server
    # sets an interruptible variant so a module switch doesn't have to wait it out.
    on_sleep = None

    def is_connected(self) -> bool:
        """Does the source have a live session? Base: no."""
        return False

    @abc.abstractmethod
    def poll(self) -> "dict":
        """Return one fresh snapshot — see the class docstring for the exact shape
        ({status, source, signals:{name:{v,u,s,c}}, faults, error?})."""

    def disconnect(self) -> None:
        """Release any K-line session/port (on module switch). Base: nothing to do."""

    def set_port(self, spec: str) -> None:
        """Use this serial port spec (``auto`` or a device path) from the next connect.
        Base: no port (info sources)."""

    def menu_map(self) -> "list":
        """Reference/coverage map (reference tool menu + our status). Base: empty."""
        return []

    def command(self, action: str, params: "dict | None" = None) -> "dict":
        """Perform a write command. Base: unknown. Returns {ok, message|error}.

        Runs on the poller thread (serialized with poll) so K-line access never
        collides. Writes to the ECU are sensitive — only explicitly supported
        actions are allowed; risky ones (actuator tests, settings) aren't exposed here.
        """
        return {"ok": False, "error": f"unknown command: {action}"}


class InfoDataSource(DataSource):
    """A module that has no live-signal reader yet (airbag/ACE/EAT/BCU).

    The UI already lists these modules; this source makes them *selectable* without
    pretending they stream live data: it reports honestly that the module is not readable
    on the car yet, with no fabricated data (data-honesty rule). It carries no signals, so
    the Drive/Inputs/Outputs tabs fall back to their empty/"Coming" state. Simulated
    variants exist only in the tests (tests/fake_sources.py, ADR-0011).
    """

    def __init__(self, module: str, *, live_message: "str | None" = None) -> None:
        self.name = module
        self.store_module = module
        self._live_message = live_message or (
            f"{module} is not readable on the car yet.")

    def poll(self) -> "dict":
        return {"status": "error", "source": self.name, "signals": {},
                "faults": [], "error": self._live_message}


def _parse_lids(params: "dict | None") -> "list[int]":
    """``params.lids`` (hex strings or ints) → LID ints. Raises ValueError when invalid."""
    lids_in = (params or {}).get("lids") or []
    if not isinstance(lids_in, (list, tuple)):
        raise ValueError("lids must be a list")
    try:
        lids = [int(x, 16) if isinstance(x, str) else int(x) for x in lids_in]
    except (ValueError, TypeError):
        raise ValueError("invalid lids (expected hex strings such as \"09\")") from None
    if any(not 0 <= lid <= 0xFF for lid in lids):
        raise ValueError("invalid lids (each LID is one byte, 00-ff)")
    return lids


def _read_block_cmd(session, params: "dict | None") -> "dict":
    """Read a set of LIDs via a live session → {ok, raws:{lidhex:hex}}.

    The read-only primitive behind the active differential mapping in the Map tab
    (baseline/read-again). Shared by the Td5 and SLABS sources."""
    if session is None:
        return {"ok": False, "error": "not connected"}
    try:
        lids = _parse_lids(params)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    try:
        raws = session.read_block(lids)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "raws": {k: v.hex() for k, v in raws.items()}}


__all__ = ["DataSource", "InfoDataSource", "resolve_serial_port"]
