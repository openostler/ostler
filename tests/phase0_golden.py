"""Phase 0 golden capture: platform outputs, by value, to prove the VehiclePack move
changes nothing but the ``motor`` → ``td5`` id (specs/2026-10-06-phase0-vehiclepack-decoupling-design.md §8).

``capture()`` computes the cheap, deterministic outputs; ``normalise()`` maps the legacy
``motor`` id to the canonical ``td5`` so the later canonicalisation does not fail the diff.
``tests/test_phase0_golden.py`` compares ``normalise(capture())`` against the committed
fixture. Regenerate (only for a reviewed, intended change):

    python3 tests/phase0_golden.py --write

Test scaffolding for Phase 0 (lives in tests/ because it uses tests.fake_sources);
deleted at the repo split.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

FIXTURE = _REPO / "tests" / "fixtures" / "phase0_golden" / "golden.json"

# Module ids the platform is asked about: the store ids plus every legacy alias in use.
_MODULE_INPUTS = ("td5", "motor", "slabs", "bcu", "ace", "autobox", "eat", "gearbox", "airbag")
_STORE_IDS = ("td5", "slabs", "bcu", "ace", "autobox", "airbag")

# Synthetic lines exercising every detector (authoritative and hint) of ModuleTracker.
_TRACKER_LINES = (
    "72 05 04 00 73",              # EAT request (hint: seeds autobox from None)
    "81 13 f7 81 0c",              # Td5 fast init
    "02 72 04 60 01",              # stray 72 .. 60 inside a Td5 stretch: hint ignored
    "82 5b f7 10 81 ad",           # airbag addressed (authoritative)
    "81 29 f7 81 22",              # SLABS fast init
    "67 67 01 02",                 # ACE pairs (hint ignored: module set)
    "81 40 f7 81 39",              # 0x40 by address (bcu)
    "02 21 cc 0f",                 # BCU EKA
    "81 77 f7 81 70",              # unknown fast-init address
)
_HINT_ONLY = (("67 67 00",), ("02 21 cc",), ("72 04 05 73",), ("00 01 02",))

_WORD = re.compile(r"\bmotor\b")


def normalise(obj):
    """Map ``motor`` → ``td5`` in every string and key (word-bounded)."""
    if isinstance(obj, dict):
        return {normalise(k): normalise(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [normalise(v) for v in obj]
    if isinstance(obj, str):
        return _WORD.sub("td5", obj)
    return obj


def _digest(obj) -> str:
    blob = json.dumps(normalise(obj), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _jsonable(obj):
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str))


def _hexline(s: str) -> "list[int]":
    return [int(t, 16) for t in s.split()]


def _sniff_demo() -> Path:
    hits = sorted((_REPO / "src" / "d2diag").rglob("sniff-demo.txt"))
    if not hits:
        raise FileNotFoundError("sniff-demo.txt not found under src/d2diag")
    return hits[0]


def _signal_store_names() -> "list[str]":
    from d2diag import signals

    d = Path(signals._dir()) if hasattr(signals, "_dir") else Path(signals._DIR)
    names: "set[str]" = set()
    for p in sorted(d.glob("*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            if isinstance(r, dict) and r.get("name"):
                names.add(str(r["name"]))
    return sorted(names)


def capture() -> dict:
    from d2diag import catalog, commands, faultscan, modscan
    from d2diag.logbook import channels
    from d2diag.logbook.store import SessionStore
    from d2diag.sniff import modules
    from d2diag.sniff.capture import parse_log
    from d2diag.web import server

    out: dict = {}

    # ---- catalog -------------------------------------------------------- #
    # Store ids by value; legacy aliases by digest (they must equal their canonical body).
    out["catalog"] = [[m, catalog.build_catalog(m) if m in _STORE_IDS
                       else _digest(catalog.build_catalog(m))] for m in _MODULE_INPUTS]
    out["module_summary"] = catalog.module_summary()
    out["legacy_menu"] = [[m, catalog.legacy_menu(m)] for m in _STORE_IDS]

    # ---- /fields and /faults bodies ------------------------------------- #
    out["fields"] = [[m, server._fields_list(m)] for m in _MODULE_INPUTS]
    # /faults echoes the dtc store file: digest it (the store itself is under review).
    out["faults"] = [[m, _digest(server._faults_list(m))] for m in _MODULE_INPUTS]

    # ---- command registry + refusal matrix ------------------------------ #
    out["registry"] = [[m, [c.as_dict() for c in commands.for_module(m)]] for m in _STORE_IDS]
    actions = sorted({a for (_m, a) in commands.REGISTRY}
                     | {"nonexistent", "select_module", "read_block", "clear_faults"})
    matrix = []
    for m in _STORE_IDS:
        for a in actions:
            for trust in ("", "experimental"):
                for public in (False, True):
                    matrix.append([m, a, trust, public, commands.refusal(m, a, trust, public)])
    out["refusal"] = matrix

    # ---- faultscan ------------------------------------------------------- #
    out["faultscan_unimplemented"] = faultscan.unimplemented_rows()
    import d2diag.ports as ports

    real = ports.resolve_serial_port

    def _boom(_spec):
        raise FileNotFoundError("no cable")

    ports.resolve_serial_port = _boom
    try:
        out["faultscan_no_cable"] = faultscan.read_all("auto", sleep=lambda *_: None)
    finally:
        ports.resolve_serial_port = real
    from tests.fake_sources import fake_fault_report

    out["faultscan_fake_report"] = fake_fault_report()

    # ---- sniff: tracker + scan ------------------------------------------- #
    events = parse_log(str(_sniff_demo()))
    tr = modules.ModuleTracker()
    per_line = []
    for _ms, kind, payload in events:
        if kind != "data":
            per_line.append(["mark", payload])
            continue
        per_line.append([" ".join(f"{x:02x}" for x in payload),
                         [list(t) for t in modules.scan(payload)], tr.feed(payload)])
    out["sniff_demo_tracker_digest"] = _digest(per_line)
    out["sniff_demo_tracker_head"] = per_line[:12]
    tr = modules.ModuleTracker()
    out["tracker_synthetic"] = [[ln, [list(t) for t in modules.scan(_hexline(ln))],
                                 tr.feed(_hexline(ln))] for ln in _TRACKER_LINES]
    hint_rows = []
    for seq in _HINT_ONLY:
        t = modules.ModuleTracker()
        hint_rows.append([list(seq), [t.feed(_hexline(ln)) for ln in seq]])
    out["tracker_hint_seed"] = hint_rows
    out["name_for_address"] = [[a, modules.name_for_address(a)]
                               for a in (0x10, 0x13, 0x18, 0x29, 0x40, 0x5A, 0x5B, 0x77)]
    out["modscan"] = {"DEFAULT_FAST": list(modscan.DEFAULT_FAST),
                      "DEFAULT_SLOW": list(modscan.DEFAULT_SLOW)}

    # ---- logbook: the committed demo sessions ----------------------------- #
    with tempfile.TemporaryDirectory() as empty:
        st = SessionStore(empty)
        lst = st.list()
        out["sessions_list"] = lst
        sess = {}
        for m in lst:
            sid = m["id"]
            sess[sid] = {
                "meta": st.meta(sid),
                "meta_public": st.meta(sid, public=True),
                "events_digest": _digest(st.events(sid)),
                "data_digest": _digest(st.data(sid)),
                "notes_digest": _digest(st.notes(sid)),
            }
        out["sessions"] = sess

    # ---- channels.group_for ----------------------------------------------- #
    names = _signal_store_names() + list(channels.GPS_CHANNELS) + list(channels.ACCEL_CHANNELS) \
        + list(channels.GPS_ACCEL_CHANNELS) + list(channels.TEXT_CHANNELS) \
        + list(channels.TIME_CHANNELS) + ["not_a_channel"]
    out["group_for"] = [[n, channels.group_for(n), channels.confidence_for(n),
                         channels.limits_for(n)] for n in names]

    return normalise(_jsonable(out))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="(re)write the committed fixture")
    args = ap.parse_args()
    got = capture()
    if args.write:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(got, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
                           encoding="utf-8")
        print(f"wrote {os.path.relpath(FIXTURE, _REPO)}")
        return 0
    want = json.loads(FIXTURE.read_text(encoding="utf-8"))
    bad = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))
    print("golden OK" if not bad else "golden DIFF: " + ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
