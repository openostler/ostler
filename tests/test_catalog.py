# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The catalog (ADR-0008): derivation rules on synthetic menus + invariants on the real ones."""
from __future__ import annotations

import pytest

import dataclasses

from openostler import catalog, pack, signals
from openostler.commands import Command
from openostler.signals import Signal
from tests.fake_pack import FAKE_PACK

FAKE = "fake"


@pytest.fixture
def fake(monkeypatch):
    """A synthetic module in a pack of its own: a tiny store, a few registry actions, and a
    menu set per test (the derivation rules are platform logic, not Discovery 2 data)."""
    store = [
        Signal("good", 0x10, 0, confidence="proven"),
        Signal("meh", 0x11, 0, confidence="candidate"),
        Signal("dup", 0x1B, 4, confidence="candidate", length=8),
        Signal("dup", 0x1B, 6, confidence="proven", length=10),
    ]
    real_load = signals.load_signals
    monkeypatch.setattr(catalog.signals, "load_signals",
                        lambda m: store if m == FAKE else real_load(m))
    actions = (
        Command("ok_act", FAKE, "Verified", status="verified", safety="actuator"),
        Command("exp_act", FAKE, "Experimental", status="experimental", safety="read"),
        Command("plan_act", FAKE, "Planned", status="planned", safety="service"),
        Command("gate_act", FAKE, "Gated", status="planned", safety="gated"),
        Command("gate2_act", FAKE, "Gated 2", status="planned", safety="gated"),
    )
    menus: "dict[str, list]" = {}
    p = dataclasses.replace(FAKE_PACK, actions=actions, menus=menus)

    def set_menu(groups):
        menus[FAKE] = groups
        return groups
    with pack.use_pack(p):
        yield set_menu


def _items(cat: dict) -> "list[dict]":
    return [i for p in cat["pages"] for g in p["groups"] for i in g["items"]]


def _one(fake, item: dict, page: str = "inputs") -> dict:
    fake([{"id": "g", "page": page, "cat": "G", "items": [{"id": "x", "name": "X", **item}]}])
    return _items(catalog.build_catalog(FAKE))[0]


# ---- derivation rules -------------------------------------------------------------------- #
def test_sig_proven_is_verified_and_read(fake):
    it = _one(fake, {"sig": "good"})
    assert (it["status"], it["safety"], it["lid"], it["actions"]) == ("verified", "read", "10", [])


def test_sig_candidate_is_candidate(fake):
    assert _one(fake, {"sig": "meh"})["status"] == "candidate"


def test_sig_first_record_without_at(fake):
    assert _one(fake, {"sig": "dup"})["status"] == "candidate"  # 1B@4 comes first


def test_sig_at_picks_the_variant(fake):
    assert _one(fake, {"sig": "dup", "at": "1B@6"})["status"] == "verified"
    assert _one(fake, {"sig": "dup", "at": "1b@4"})["status"] == "candidate"


def test_unknown_sig_or_at_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"sig": "nope"})
    with pytest.raises(ValueError):
        _one(fake, {"sig": "dup", "at": "1B@9"})


def test_actions_all_verified(fake):
    it = _one(fake, {"actions": ["ok_act"]}, page="outputs")
    assert (it["status"], it["safety"]) == ("verified", "actuator")
    assert it["actions"][0]["action"] == "ok_act"


def test_actions_worst_non_gated_wins(fake):
    assert _one(fake, {"actions": ["ok_act", "exp_act"]}, "outputs")["status"] == "candidate"
    assert _one(fake, {"actions": ["ok_act", "exp_act", "plan_act"]}, "outputs")["status"] == "sniff"
    # a gated action does not drag the status down, but it sets the safety
    it = _one(fake, {"actions": ["ok_act", "gate_act"]}, "utilities")
    assert (it["status"], it["safety"]) == ("verified", "gated")


def test_actions_all_gated_is_sniff_and_gated(fake):
    it = _one(fake, {"actions": ["gate_act", "gate2_act"]}, "utilities")
    assert (it["status"], it["safety"]) == ("sniff", "gated")


def test_action_safety_is_most_severe(fake):
    assert _one(fake, {"actions": ["exp_act", "plan_act"]}, "utilities")["safety"] == "service"


def test_unregistered_action_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"actions": ["missing"]}, "outputs")


def test_hand_status_and_placeholder(fake):
    assert _one(fake, {"status": "sniff"})["status"] == "sniff"
    it = _one(fake, {"untranscribed": True, "pages": 4})
    assert (it["status"], it["placeholder"], it["pages"]) == ("untranscribed", True, 4)
    with pytest.raises(ValueError):
        _one(fake, {"status": "ok"})  # legacy vocabulary is not accepted


def test_hand_verified_only_on_session_and_faults(fake):
    assert _one(fake, {"status": "verified"}, "session")["status"] == "verified"
    assert _one(fake, {"status": "verified"}, "faults")["status"] == "verified"
    with pytest.raises(ValueError):
        _one(fake, {"status": "verified"}, "inputs")


def test_link_plus_hand_status_is_an_error(fake):
    with pytest.raises(ValueError):
        _one(fake, {"sig": "good", "status": "sniff"})
    with pytest.raises(ValueError):
        _one(fake, {"actions": ["ok_act"], "status": "verified"}, "outputs")


def test_pages_fixed_order_session_folds_into_faults(fake):
    fake([
        {"id": "u", "page": "utilities", "cat": "U", "items": [{"id": "a", "name": "A", "status": "sniff"}]},
        {"id": "s", "page": "session", "cat": "S", "items": [{"id": "b", "name": "B", "status": "verified"}]},
    ])
    cat = catalog.build_catalog(FAKE)
    assert [p["id"] for p in cat["pages"]] == ["faults", "inputs", "outputs", "settings", "utilities"]
    faults = cat["pages"][0]
    assert [g["id"] for g in faults["groups"]] == ["s"]
    assert faults["coverage"]["verified"] == 1
    empty = cat["pages"][1]
    assert empty["groups"] == [] and empty["coverage"]["total"] == 0
    assert cat["coverage"] == {"verified": 1, "candidate": 0, "sniff": 1, "untranscribed": 0, "total": 2}


def test_item_and_group_shape(fake):
    fake([{"id": "g", "page": "inputs", "cat": "Inputs — X", "nanocom": "m/inputs", "items": [
        {"id": "x", "name": "X", "sig": "good", "ref": "21 10", "note": "n"}]}])
    cat = catalog.build_catalog(FAKE)
    assert set(cat) == {"store_module", "coverage", "pages"}
    group = cat["pages"][1]["groups"][0]
    assert group == {"id": "g", "title": "Inputs — X", "parent": None, "nanocom": "m/inputs",
                     "items": group["items"]}
    assert set(group["items"][0]) == {"id", "name", "status", "safety", "sig", "lid", "ref", "note",
                                      "placeholder", "pages", "actions"}


def test_legacy_status_and_menu(fake):
    assert [catalog.legacy_status(s) for s in catalog.STATUSES] == ["ok", "maybe", "todo", "todo"]
    fake([{"id": "g", "page": "inputs", "cat": "G", "items": [
        {"id": "a", "name": "A", "sig": "good", "lid": "10"},
        {"id": "b", "name": "B", "sig": "meh"},
        {"id": "c", "name": "C", "status": "sniff"}]}])
    assert catalog.legacy_menu(FAKE) == [{"cat": "G", "items": [
        {"name": "A", "status": "ok", "ref": "", "lid": "10", "sig": "good"},
        {"name": "B", "status": "maybe", "ref": "", "sig": "meh"},
        {"name": "C", "status": "todo", "ref": ""}]}]
