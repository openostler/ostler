# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""FAKE_PACK: a minimal second vehicle pack, so platform tests prove the platform is
generic (specs/2026-10-06-phase0-vehiclepack-decoupling-design.md §1, §6).

Two modules: ``alpha`` (fast init 0x10, live, alias ``a``) and ``beta`` (no live reader).
Data lives in ``tests/fixtures/fake_pack/{signals,dtc}/alpha.json``. Use it with
``openostler.pack.use_pack(FAKE_PACK)`` (or ``set_active_pack``). Nothing here names a
Discovery 2 module.
"""
from __future__ import annotations

from pathlib import Path

from openostler.commands import Command
from openostler.pack import (PACK_API_VERSION, Detector, FaultReader, ModuleSpec, SniffSpec,
                         VehiclePack)

ROOT = Path(__file__).resolve().parent / "fixtures" / "fake_pack"

ACTIONS = (
    Command("ping", "alpha", "Ping", status="verified", safety="read", confirm="none",
            preconditions=(), ref="fake 3E"),
    Command("zap", "alpha", "Zap", status="planned", safety="gated", confirm="typed",
            ref="never sent"),
)

MENUS = {
    "alpha": [
        {"id": "faults", "page": "faults", "cat": "Fault codes", "items": [
            {"id": "read-faults", "name": "Read faults", "status": "verified"},
        ]},
        {"id": "inputs", "page": "inputs", "cat": "Inputs", "items": [
            {"id": "speed", "name": "Speed", "sig": "alpha_speed"},
            {"id": "temp", "name": "Temperature", "sig": "alpha_temp"},
        ]},
        {"id": "outputs", "page": "outputs", "cat": "Outputs", "items": [
            {"id": "ping", "name": "Ping", "actions": ["ping"]},
        ]},
        {"id": "utilities", "page": "utilities", "cat": "Utilities", "items": [
            {"id": "zap", "name": "Zap", "actions": ["zap"]},
        ]},
    ],
}

LAYOUT = {
    "drive": {"alpha": {"kind": "tiles", "tiles": [
        {"signal": "alpha_speed", "label": "Speed", "gauge": True, "dec": 0},
        {"signal": "alpha_temp", "label": "Temp", "dec": 0},
    ]}},
}


def _alpha_line(b: "list[int]") -> bool:
    return len(b) >= 2 and b[0] == 0xAA and b[1] == 0x10


def _sources(port, *, raw_log_dir=None, state_dir=None):
    from openostler.web.sources import DataSource, InfoDataSource

    class FakeAlphaSource(DataSource):
        name = "alpha"
        store_module = "alpha"

        def __init__(self) -> None:
            self.port = port
            self.polls = 0

        def is_connected(self) -> bool:
            return True

        def poll(self) -> dict:
            self.polls += 1
            return {"status": "connected", "source": "alpha",
                    "signals": {"alpha_speed": {"v": 1000.0 + self.polls, "u": "rpm",
                                                "s": "ok", "c": "proven"}},
                    "faults": []}

        def command(self, action: str, params=None) -> dict:
            if action == "ping":
                return {"ok": True, "message": "pong"}
            return super().command(action, params)

    return {"alpha": FakeAlphaSource(),
            "beta": InfoDataSource("beta", live_message="beta has no live reader")}


FAKE_PACK = VehiclePack(
    id="fake",
    name="Fake test vehicle",
    api_version=PACK_API_VERSION,
    modules=(
        ModuleSpec("alpha", "ALPHA (fake engine)", address=0x10, init="fast", aliases=("a",),
                   live=True, fault_label="ALPHA"),
        ModuleSpec("beta", "BETA (fake body)", live=False, fault_label="BETA"),
    ),
    default_module="alpha",
    sources=_sources,
    signals_dir=ROOT / "signals",
    dtc_dir=ROOT / "dtc",
    actions=ACTIONS,
    menus=MENUS,
    unlinked_ok={"alpha": frozenset()},
    derived_fields={"alpha": {"alpha_rate": {"unit": "/s", "c": "candidate", "label": "Alpha rate",
                                             "group": "Engine", "description": "Derived (fake)."}}},
    writable_signal_modules=("alpha",),
    module_command_prefixes=("zap_",),
    faultscan=(FaultReader("ALPHA", lambda p: ["A1"]),),
    faultscan_unimplemented=(("BETA", "no fault reader in the fake pack"),),
    sniff=SniffSpec(fast_init={0x10: "alpha"}, slow_init={},
                    hints=(Detector("alpha", "aa-10 marker", _alpha_line),)),
    demo=None,
    docs=(),
    layout=LAYOUT,
    root=ROOT,
)
