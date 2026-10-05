"""The command registry (d2diag.commands) matches what the data sources dispatch, both ways.

A new module action needs a registry entry (status + safety) before the server will run it
(ADR-0008); a registered, runnable action that no source handles would be a dead button.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from d2diag import commands
from d2diag.td5.td5 import _OUTPUTS
from d2diag.web.sources import (
    TD5_ACTIONS,
    _SLABS_ACTUATORS,
    SlabsDataSource,
    Td5DataSource,
)
from tests.fake_sources import FakeInfoSource, FakeSlabsSource, FakeTd5Source


class _StubTd5:
    """A connected Td5 session that records what the source asked of it."""

    def __init__(self) -> None:
        self.calls: "list[tuple]" = []

    def output_test(self, name):
        if name not in _OUTPUTS:
            raise ValueError(name)
        self.calls.append(("output", name))

    def injector_pulse(self, cyl):
        if not 1 <= cyl <= 5:
            raise ValueError(cyl)
        self.calls.append(("injector", cyl))

    def security_status_raw(self):
        self.calls.append(("security",))
        return b"\xc0\x03"

    def read_identity(self):
        self.calls.append(("identity",))
        return {"part_no": "NNN000130", "vin_masked": "*************0000"}

    def release(self):
        pass


def _live_td5():
    src = Td5DataSource(port="x", read_faults=False)
    src._td5 = _StubTd5()
    return src


def _live_slabs():
    src = SlabsDataSource(port="x", read_faults=False)
    src._slabs = MagicMock()  # every actuator method exists and succeeds
    return src


def _sources(module: str):
    """(live, mock) sources for a store module, or None when no source exists yet."""
    if module == "td5":
        return _live_td5(), FakeTd5Source()
    if module == "slabs":
        return _live_slabs(), FakeSlabsSource()
    return None


def _runnable(module: "str | None" = None):
    return [c for c in commands.REGISTRY.values()
            if c.status != "planned" and (module is None or c.module == module)]


def _handled(result: dict) -> bool:
    return bool(result.get("ok")) and "unknown command" not in (result.get("error") or "")


@pytest.mark.parametrize("cmd", _runnable(), ids=lambda c: f"{c.module}:{c.action}")
def test_every_runnable_registry_action_is_dispatched_by_live_and_mock(cmd):
    pair = _sources(cmd.module)
    assert pair is not None, f"no data source for {cmd.module}, yet {cmd.action} is runnable"
    live, mock = pair
    assert _handled(live.command(cmd.action, {})), f"live {cmd.module} ignores {cmd.action}"
    assert _handled(mock.command(cmd.action, {})), f"mock {cmd.module} ignores {cmd.action}"


def test_every_module_action_the_sources_handle_is_registered():
    td5 = {c.action for c in _runnable("td5")}
    slabs = {c.action for c in _runnable("slabs")}
    assert set(TD5_ACTIONS) == td5
    assert set(_SLABS_ACTUATORS) == slabs


@pytest.mark.parametrize("cmd", [c for c in commands.REGISTRY.values() if c.status == "planned"],
                         ids=lambda c: f"{c.module}:{c.action}")
def test_planned_and_gated_actions_are_not_implemented_by_any_source(cmd):
    """Gated means never sent: no source may even know how to send it."""
    for src in (_live_td5(), FakeTd5Source(), _live_slabs(), FakeSlabsSource(),
                FakeInfoSource(cmd.module)):
        r = src.command(cmd.action, {})
        assert not r.get("ok"), f"{type(src).__name__} handles planned {cmd.action}"


@pytest.mark.parametrize("action", ["output_frobnicate", "injector_6", "injector_0",
                                    "raise_centre", "wheel_xx", "pump_maybe"])
def test_unregistered_lookalikes_are_unknown_to_sources(action):
    for src in (_live_td5(), FakeTd5Source(), _live_slabs(), FakeSlabsSource()):
        assert not src.command(action, {}).get("ok")


def test_td5_output_refs_match_the_bytes_sent():
    """The registry's reference string is the IOControl the Td5 layer actually sends."""
    for name, (lid, params) in _OUTPUTS.items():
        c = commands.get("td5", f"output_{name}")
        assert c is not None
        assert c.ref == " ".join(f"{b:02X}" for b in bytes([0x30, lid]) + params)


def test_every_registry_entry_is_well_formed():
    for c in commands.REGISTRY.values():
        assert c.status in commands.STATUSES and c.safety in commands.SAFETIES
        assert c.confirm in commands.CONFIRMS
        if c.stop:
            stop = commands.get(c.module, c.stop)
            assert stop is not None and stop.status != "planned", c.action
        if c.safety == "gated":
            assert c.status == "planned", f"gated {c.action} must never be runnable"


def test_refusal_policy():
    assert commands.refusal("td5", "learn_security_code", trust="experimental")   # gated
    assert commands.refusal("td5", "output_fuel_pump")                            # no trust
    assert commands.refusal("td5", "output_fuel_pump", trust="experimental") is None
    assert commands.refusal("slabs", "buzzer") is None                            # verified
    assert commands.refusal("slabs", "buzzer", public=True)                       # actuator
    assert commands.refusal("td5", "read_identity", trust="experimental",
                            public=True) is None                                  # read
    assert commands.refusal("td5", "clear_faults") is None                        # not registry
