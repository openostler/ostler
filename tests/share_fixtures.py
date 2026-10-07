# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Sessions for the per-trip sharing tests (trip-sharing spec §8.4, §16).

- :func:`record_node_session` records a node session through the product's
  ``SessionRecorder`` from the **firmware's recorded tap fixture**
  (``tests/fixtures/node/td5-vectors.jsonl``, ADR-0011: recorded shapes, not a simulator),
  on a copy whose header says ``scrub: off`` and with the install option
  ``record_identity`` on, so identity bytes reach the store unscrubbed (ADR-0036 §3: the
  share must scrub them). ``inject`` adds records to the copy: identity replies built at
  run time, and CAN frames taken from the shared ISO-TP vectors' shapes.
- :func:`synthetic_vin` is :func:`tests.obd_fakes.make_vin`: no 17-character VIN literal is
  committed (the UI spec §8.3 CI rule); it is assembled from fragments at run time.
- :func:`write_gps_session` writes a **synthetic** GPS trip (marked ``synthetic: true`` in
  its meta): the repo holds no recorded drive longer than 1 km (``legacy_session_motor`` is
  240 m), and the trim and zone maths need one. Its shape is a plain grid drive with a
  known along-track length so the tests can check the maths exactly.
"""
from __future__ import annotations

import calendar
import json
import math
import os
from typing import Iterable, List, Optional, Sequence

from openostler.logbook.recorder import SessionRecorder, header_cell
from openostler.node import tap as T
from tests.fake_node import tap_messages
from tests.obd_fakes import make_vin

T0 = calendar.timegm((2026, 10, 6, 10, 0, 0)) + 0.0   # the fixture's wall clock start
SPEED = "Vehicle.Speed"


def synthetic_vin() -> str:
    return make_vin()


class Clock:
    def __init__(self) -> None:
        self.m = 0.0

    def wall(self) -> float:
        return T0 + self.m

    def mono(self) -> float:
        return self.m


def _snap(speed: float) -> dict:
    src = {"v": speed, "u": "km/h", "ts_utc": None, "age_s": 0.1, "stale": False,
           "c": "proven"}
    return {"source_kind": "node", "status": "connected", "conn": "connected",
            "module": "alpha", "signals": {},
            "vss": {SPEED: {"sel": "node/kline-diag", "value": speed, "unit": "km/h",
                            "ts_utc": None, "age_s": 0.1, "stale": False, "c": "proven",
                            "sources": {"node/kline-diag": src}}},
            "faults": [], "devices": ["node"],
            "node": {"device": "node", "status": "online", "power": {"state": "awake"}}}


def fixture_tap():
    """``(session id, header dict, records)`` of the firmware's td5 vector run."""
    msgs = tap_messages()
    meta = next(m for m in msgs if m["topic"].endswith("/meta"))
    session = meta["topic"].split("/")[5]
    header = json.loads(meta["payload"].decode())
    records: "List[T.TapRecord]" = []
    for m in msgs:
        if m["topic"].endswith("/data"):
            rs, _ = T.parse_records(m["payload"])
            records += rs
    return session, header, records


def kwp(data: bytes) -> bytes:
    """A length-prefixed KWP2000 frame (format byte = length) with its checksum."""
    body = bytes([len(data)]) + bytes(data)
    return body + bytes([sum(body) & 0xFF])


def kline(t_us: int, payload: bytes, *, tx=False, flags=0, proto=T.PROTO_KLINE_MSG) -> T.TapRecord:
    return T.TapRecord(t_us, 0, T.TYPE_DATA, 0, T.DIR_TX_ECHO if tx else T.DIR_RX, proto,
                       flags, bytes(payload))


def can(t_us: int, can_id: int, data: Sequence[int], *, bus: int = 1, ext=False,
        tx=False) -> T.TapRecord:
    cid = can_id | (0x80000000 if ext else 0)
    return T.TapRecord(t_us, 0, T.TYPE_DATA, bus, T.DIR_TX_ECHO if tx else T.DIR_RX,
                       T.PROTO_CAN, 0, cid.to_bytes(4, "little") + bytes([len(data)])
                       + bytes(data))


def isotp_frames(payload: bytes) -> "List[List[int]]":
    """``payload`` as ISO-TP frames padded with 0x55 (the shared vectors' segmentation)."""
    from openostler.can.isotp import segment

    return [list(f) for f in segment(payload, 0x55)]


def record_node_session(root: str, inject: Iterable[T.TapRecord] = (), *,
                        record_identity: bool = True, header_scrub: str = "off",
                        can_bus: bool = True, seconds: float = 20.0) -> str:
    """A node session recorded from the firmware fixture plus ``inject`` (records keep
    their ``t_us``; ``seq`` is renumbered in time order). Returns the session directory."""
    session, header, records = fixture_tap()
    header = dict(header, scrub=header_scrub)
    if can_bus:
        header["buses"] = list(header["buses"]) + [
            {"idx": 1, "bus_id": "can-diag", "proto": "can", "baud": 500000}]
    allrec = sorted(list(records) + list(inject), key=lambda r: (r.t_us, r.seq))
    allrec = [T.TapRecord(r.t_us, i, r.type, r.bus, r.dir, r.proto, r.flags, r.payload)
              for i, r in enumerate(allrec)]
    c = Clock()
    rec = SessionRecorder(root, clock=c.wall, mono=c.mono, vid="bench-1", min_free_bytes=0,
                          fsync=lambda _fd: None, record_identity=record_identity)
    rec.feed(_snap(0.0))
    sid = rec.session_id
    rec.tap_message("node", session, "meta", json.dumps(header).encode())
    rec.tap_message("node", session, "data", b"".join(T.encode_record(r) for r in allrec))
    steps = int(seconds / 0.5)
    for i in range(1, steps + 1):
        c.m = i * 0.5
        rec.feed(_snap(10.0 + i))
    rec.close()
    return os.path.join(root, sid)


# ---- a synthetic GPS trip (marked synthetic) -------------------------------------------- #
LAT0, LON0 = 53.2000, -1.6000          # an inland grid origin (Derbyshire)
_M_PER_DEG = 111_194.93                # haversine metres per degree of latitude (R 6371008.8)


def offset(lat: float, lon: float, east_m: float, north_m: float):
    return (lat + north_m / _M_PER_DEG,
            lon + east_m / (_M_PER_DEG * math.cos(math.radians(lat))))


def grid_drive(legs=((3000, 0), (0, 2000)), step_m: float = 10.0, speed_kmh: float = 36.0,
               start=(LAT0, LON0), alt0: float = 150.0) -> "List[dict]":
    """Rows of a drive along straight legs ``(east_m, north_m)``: one fix every
    ``step_m`` at a constant speed, altitude rising 1 m per 50 m."""
    rows, t, lat, lon, s = [], 0.0, start[0], start[1], 0.0
    dt = step_m / (speed_kmh / 3.6) * 1000
    rows.append(_row(t, lat, lon, alt0, speed_kmh))
    for east, north in legs:
        n = int(round(math.hypot(east, north) / step_m))
        for _ in range(n):
            lat, lon = offset(lat, lon, east / n, north / n)
            t += dt
            s += step_m
            rows.append(_row(t, lat, lon, alt0 + s / 50.0, speed_kmh))
    return rows


def _row(t, lat, lon, alt, spd) -> dict:
    return {"Interval": t, "Utc": T0 * 1000 + t, "GPS_Latitude": round(lat, 7),
            "GPS_Longitude": round(lon, 7), "GPS_Altitude": round(alt, 2), "GPS_Speed": spd,
            "GPS_HDOP": 0.8, "GPS_Heading": 90.0, "speed": spd, "rpm": 1500 + (t % 7000) / 10}


def write_gps_session(root: str, rows: "List[dict]", sid: str = "20261006T100000Z",
                      extra_meta: Optional[dict] = None) -> str:
    """A session directory in the logbook format (``meta.json`` and ``data-0.csv``),
    marked synthetic."""
    path = os.path.join(root, sid)
    os.makedirs(path, exist_ok=True)
    cols = ["Interval", "Utc", "GPS_Latitude", "GPS_Longitude", "GPS_Altitude", "GPS_Speed",
            "GPS_HDOP", "GPS_Heading", "speed", "rpm", "module", "faults"]
    units = {"Interval": "ms", "Utc": "ms", "GPS_Latitude": "deg", "GPS_Longitude": "deg",
             "GPS_Altitude": "m", "GPS_Speed": "km/h", "speed": "km/h", "rpm": "rpm"}
    with open(os.path.join(path, "data-0.csv"), "w", encoding="utf-8") as fh:
        fh.write(",".join(header_cell(c, units.get(c, ""), 1) for c in cols) + "\n")
        for r in rows:
            fh.write(",".join("" if r.get(c) is None else str(r.get(c)) for c in cols) + "\n")
    meta = {"id": sid, "name": None, "start_utc": "2026-10-06T10:00:00.000Z",
            "end_utc": None, "parts": ["data-0.csv"], "modules": [], "vid": "bench-1",
            "channels": [{"name": c, "units": units.get(c, "")} for c in cols[2:10]],
            "synthetic": True, "recording": False, "source": "live"}
    meta.update(extra_meta or {})
    with open(os.path.join(path, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh)
    return path
