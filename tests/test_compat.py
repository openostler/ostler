"""The Phase 0 import shim (d2diag/_compat.py): old D2 import paths resolve to the SAME
module objects under d2diag.vehicles.lr_d2 — no duplicate copies, so monkeypatch works
through either name (specs/2026-10-06-phase0-vehiclepack-decoupling-design.md §3)."""
import importlib
import sys

import pytest

import d2diag
from d2diag import _compat

_PAIRS = [
    ("d2diag.td5", "d2diag.vehicles.lr_d2.td5"),
    ("d2diag.td5.td5", "d2diag.vehicles.lr_d2.td5.td5"),
    ("d2diag.td5.identifiers", "d2diag.vehicles.lr_d2.td5.identifiers"),
    ("d2diag.td5.keygen", "d2diag.vehicles.lr_d2.td5.keygen"),
    ("d2diag.slabs.slabs", "d2diag.vehicles.lr_d2.slabs.slabs"),
    ("d2diag.bcu.scan", "d2diag.vehicles.lr_d2.bcu.scan"),
    ("d2diag.airbag.faults", "d2diag.vehicles.lr_d2.airbag.faults"),
    ("d2diag.ace.menu", "d2diag.vehicles.lr_d2.ace.menu"),
    ("d2diag.autobox.menu", "d2diag.vehicles.lr_d2.autobox.menu"),
    ("d2diag.sniff.library", "d2diag.vehicles.lr_d2.sniff.library"),
    ("d2diag.sniff.emulator_map", "d2diag.vehicles.lr_d2.sniff.emulator_map"),
    ("d2diag.sniff.importer", "d2diag.vehicles.lr_d2.sniff.importer"),
    ("d2diag.sniff.fault_import", "d2diag.vehicles.lr_d2.sniff.fault_import"),
    ("d2diag.logbook.synth", "d2diag.vehicles.lr_d2.synth"),
]


def test_spec_identity_example():
    import d2diag.td5.td5 as a
    import d2diag.vehicles.lr_d2.td5.td5 as b

    assert a is b


@pytest.mark.parametrize("old,new", _PAIRS)
def test_old_path_is_the_same_module(old, new):
    a = importlib.import_module(old)
    b = importlib.import_module(new)
    assert a is b
    assert sys.modules[old] is sys.modules[new]
    assert a.__name__ == new and a.__spec__.name == new   # the real spec, not the alias


def test_from_import_and_attribute_access():
    from d2diag.td5 import Td5
    from d2diag.vehicles.lr_d2.td5.td5 import Td5 as Td5b

    assert Td5 is Td5b
    assert d2diag.td5 is importlib.import_module("d2diag.vehicles.lr_d2.td5")


def test_monkeypatch_through_old_name_is_seen_by_new(monkeypatch):
    import d2diag.td5.keygen as old
    import d2diag.vehicles.lr_d2.td5.keygen as new

    monkeypatch.setattr(old, "key_from_seed", lambda seed: 42)
    assert new.key_from_seed(1) == 42


def test_unknown_submodule_still_fails():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("d2diag.td5.does_not_exist")


def test_target_for_and_unaliased_names():
    assert _compat.target_for("d2diag.slabs") == "d2diag.vehicles.lr_d2.slabs"
    assert _compat.target_for("d2diag.slabs.faults") == "d2diag.vehicles.lr_d2.slabs.faults"
    assert _compat.target_for("d2diag.slabsx") is None
    assert _compat.target_for("d2diag.sniff.modules") is None      # platform, not moved
    assert _compat.target_for("d2diag.logbook.store") is None


def test_install_is_idempotent():
    _compat.install()
    _compat.install()
    assert sum(isinstance(f, _compat.AliasFinder) for f in sys.meta_path) == 1
