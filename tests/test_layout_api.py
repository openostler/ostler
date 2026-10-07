# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stored UI layouts over HTTP (drive-modes spec §8.1 R1/R7, §8.3, §10 "Server"; DM2):
``/ui/layouts/…`` and ``/ui/drive-mode/…`` on a fake-pack ``DiagServer``.

Park to edit: every layout write is refused with 409 ``park_to_edit`` (and the
``driving_state``) unless the car is Parked or Idling, when the requesting class
(``Ostler-Layout-Class``) is driver-facing; tablet and desktop may write, and a write for a
driver-facing class is then held until Parked (R7). Switching modes is allowed in every
state."""
from __future__ import annotations

import http.client
import json
import threading

import pytest

from tests.test_layout_store import user_mode

HU = {"Ostler-Layout-Class": "hu7"}
DESK = {"Ostler-Layout-Class": "desktop"}
BASE = "/ui/layouts/current/car/hu7"
ONE = f"{BASE}/drive_mode/user.my-dash"


class State:
    def __init__(self) -> None:
        self.value = "unknown"

    def __call__(self) -> str:
        return self.value


@pytest.fixture
def driving():
    return State()


def _server(tmp_path, driving, **kw):
    from openostler.pack import use_pack
    from openostler.web.server import DiagServer
    from tests.fake_pack import FAKE_PACK

    with use_pack(FAKE_PACK) as pack:
        srv = DiagServer(pack.sources("auto"), host="127.0.0.1", port=0, poll_interval=0.05,
                         stream_interval=0.05, csv_dir=str(tmp_path), menus=pack.menus,
                         geocoder=None, record_sessions=False, driving_state=driving,
                         state_dir=str(tmp_path / "state"), **kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


@pytest.fixture
def srv(tmp_path, driving, monkeypatch):
    monkeypatch.setenv("OSTLER_VEHICLE_ID", "v-test")
    s = _server(tmp_path, driving)
    try:
        yield s
    finally:
        s.shutdown()
        s.server_close()
        s.stop()


def call(srv, method, path, body=None, headers=None, raw: "bytes | None" = None):
    conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=15)
    hdrs = dict(headers or {})
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    try:
        conn.request(method, path, body=data, headers=hdrs)
        resp = conn.getresponse()
        return resp.status, dict(resp.getheaders()), json.loads(resp.read() or b"null")
    finally:
        conn.close()


def test_an_empty_store_resolves_to_generated(srv):
    status, _, body = call(srv, "GET", BASE)
    assert status == 200
    assert body["vid"] == "v-test" and body["profile"] == "car" and body["class"] == "hu7"
    assert body["layouts"] == [] and body["held"] == [] and body["snapshot"] is None
    assert body["driving_state"] == "unknown"
    status, headers, body = call(srv, "GET", f"{BASE}/drive_mode/ostler.dashboard")
    assert status == 200 and body["source"] == "generated" and body["layout"] is None
    assert headers["ETag"] == '"generated"'


def test_park_to_edit_refuses_driver_facing_writes_unless_parked(srv, driving):
    for state in ("unknown", "moving"):
        driving.value = state
        for hdr in (HU, {"Ostler-Layout-Class": "phone"}, {}, {"Ostler-Layout-Class": "fridge"}):
            for method, path, body in (("PUT", ONE, user_mode()), ("DELETE", ONE, None),
                                       ("POST", f"{BASE}/reset", {}),
                                       ("POST", f"{BASE}/undo-reset", {})):
                status, _, reply = call(srv, method, path, body, hdr)
                assert status == 409, (state, hdr, method, path)
                assert reply["ok"] is False and reply["code"] == "park_to_edit"
                assert reply["driving_state"] == state and reply["error"].startswith("Park to edit")
    assert call(srv, "GET", BASE)[2]["layouts"] == []
    for state in ("parked", "idling"):
        driving.value = state
        status, headers, reply = call(srv, "PUT", ONE, user_mode(), HU)
        assert status == 200 and reply["ok"] and reply["source"] == "car", reply
        assert headers["ETag"] == reply["etag"]


def test_tablet_and_desktop_write_and_driver_facing_targets_are_held(srv, driving):
    # a desktop editing the desktop class: applied at once
    status, _, reply = call(srv, "PUT", "/ui/layouts/current/car/desktop/drive_mode/user.my-dash",
                            user_mode(), DESK)
    assert status == 200 and reply["rev"] == 1
    # a tablet editing the head unit's class while not Parked: held (R7), 202
    status, _, reply = call(srv, "PUT", ONE, user_mode(), {"Ostler-Layout-Class": "tablet"})
    assert status == 202 and reply["ok"] and reply["queued"] and reply["held"]
    listing = call(srv, "GET", BASE)[2]
    assert listing["layouts"] == [] and [h["op"] for h in listing["held"]] == ["put"]
    # parked: the next layouts request applies it
    driving.value = "parked"
    listing = call(srv, "GET", BASE)[2]
    assert [x["id"] for x in listing["layouts"]] == ["user.my-dash"] and listing["held"] == []


def test_a_held_write_is_still_validated(srv):
    bad = user_mode()
    bad.pop("base")
    status, _, reply = call(srv, "PUT", ONE, bad, DESK)
    assert status == 400 and reply["code"] == "base_missing"
    assert call(srv, "GET", BASE)[2]["held"] == []


def test_put_refusals_carry_the_validators_errors(srv, driving):
    driving.value = "parked"
    doc = user_mode()
    doc["classes"]["hu7"][0]["widgets"][0]["style"] = "sparkline"
    status, _, reply = call(srv, "PUT", ONE, doc, HU)
    assert status == 400 and reply["code"] == "layout_invalid"
    assert reply["error"].startswith("The layout was refused")
    rules = {e["rule"] for e in reply["errors"]}
    assert rules and all(e.get("class") for e in reply["errors"] if e["rule"].startswith("moving."))
    assert isinstance(reply["warnings"], list)
    # the key must match the document
    status, _, reply = call(srv, "PUT", f"{BASE}/drive_mode/user.other", user_mode(), HU)
    assert status == 400 and reply["code"] == "layout_key"
    status, _, reply = call(srv, "PUT", "/ui/layouts/current/car/tablet/drive_mode/user.my-dash",
                            {**user_mode(), "classes": {"hu7": user_mode()["classes"]["hu7"]}}, HU)
    assert status == 400 and reply["code"] == "layout_class"
    status, _, reply = call(srv, "PUT", ONE, None, HU, raw=b"{nope")
    assert status == 400 and reply["code"] == "bad_request"
    status, _, reply = call(srv, "PUT", ONE, None, HU, raw=b"x" * (256 * 1024 + 1))
    assert status == 413 and reply["code"] == "too_large"


def test_rail_strip_and_home_wait_for_their_guardrails(srv, driving):
    driving.value = "parked"
    rail = {"format": "ostler.layout/1", "kind": "rail", "id": "user.rail", "name": "Rail",
            "base": {"preset": "ostler.rail", "version": 1},
            "classes": {"hu7": [{"face": "rail", "items": []}]}}
    status, _, reply = call(srv, "PUT", f"{BASE}/rail/user.rail", rail, HU)
    assert status == 403 and reply["code"] == "kind_not_writable"


def test_etag_and_if_match(srv, driving):
    driving.value = "parked"
    _, headers, first = call(srv, "PUT", ONE, user_mode(), HU)
    _, headers2, got = call(srv, "GET", ONE)
    assert headers2["ETag"] == first["etag"] == got["etag"]
    status, _, reply = call(srv, "PUT", ONE, {**user_mode(), "name": "Two"},
                            {**HU, "If-Match": '"stale"'})
    assert status == 409 and reply["code"] == "etag_mismatch" and reply["etag"] == got["etag"]
    status, _, reply = call(srv, "PUT", ONE, {**user_mode(), "name": "Two"},
                            {**HU, "If-Match": got["etag"]})
    assert status == 200 and reply["rev"] == 2


def test_resolution_order_over_http(srv, driving):
    driving.value = "parked"
    lid = "ostler.dashboard"
    path = f"/ui/layouts/current/alice/hu7/drive_mode/{lid}"
    assert call(srv, "GET", path)[2]["source"] == "generated"
    call(srv, "PUT", f"{BASE}/drive_mode/{lid}", user_mode(lid, "Car's"), HU)
    r = call(srv, "GET", path)[2]
    assert (r["source"], r["profile"], r["layout"]["name"]) == ("car", "car", "Car's")
    call(srv, "PUT", path, user_mode(lid, "Alice's"), HU)
    r = call(srv, "GET", path)[2]
    assert (r["source"], r["profile"], r["layout"]["name"]) == ("user", "alice", "Alice's")
    # DELETE reverts Alice's to what lies beneath: the car's
    status, _, reply = call(srv, "DELETE", path, None, HU)
    assert status == 200 and reply["deleted"] and reply["resolved"]["source"] == "car"


def test_pack_layouts_are_tier_two(tmp_path, driving, monkeypatch):
    monkeypatch.setenv("OSTLER_VEHICLE_ID", "v-test")
    s = _server(tmp_path, driving)
    try:
        import openostler.pack as pack_mod

        good = user_mode("pack.trail", "Trail")
        bad = {**user_mode("pack.bad", "Bad"), "format": "nope"}

        class Pack:
            layout = {"layouts": [good, bad]}

        monkeypatch.setattr(pack_mod, "active_pack", lambda: Pack())
        s._pack_docs = None
        r = call(s, "GET", f"{BASE}/drive_mode/pack.trail")[2]
        assert r["source"] == "pack" and r["layout"]["name"] == "Trail"
        # the invalid one is ignored, never served
        assert [(x["id"], x["source"]) for x in call(s, "GET", BASE)[2]["layouts"]] == [
            ("pack.trail", "pack")]
        assert call(s, "GET", f"{BASE}/drive_mode/pack.bad")[2]["source"] == "generated"
    finally:
        s.shutdown()
        s.server_close()
        s.stop()


def test_reset_and_undo_reset(srv, driving):
    driving.value = "parked"
    call(srv, "PUT", ONE, user_mode(), HU)
    call(srv, "PUT", f"{BASE}/drive_mode/user.two", user_mode("user.two", "Two"), HU)
    status, _, reply = call(srv, "POST", f"{BASE}/reset", {"kind": "drive_mode"}, HU)
    assert status == 200 and reply["reset"] == 2 and reply["snapshot"]["scope"] == "drive_mode"
    assert call(srv, "GET", BASE)[2]["layouts"] == []
    assert call(srv, "GET", BASE)[2]["snapshot"]["layouts"]
    # Reset is an edit: refused while Moving (R1)
    driving.value = "moving"
    assert call(srv, "POST", f"{BASE}/undo-reset", {}, HU)[0] == 409
    driving.value = "parked"
    status, _, reply = call(srv, "POST", f"{BASE}/undo-reset", {}, HU)
    assert status == 200 and reply["restored"] == 2
    assert len(call(srv, "GET", BASE)[2]["layouts"]) == 2
    status, _, reply = call(srv, "POST", f"{BASE}/undo-reset", {}, HU)
    assert status == 404 and reply["code"] == "not_found"
    status, _, reply = call(srv, "POST", f"{BASE}/reset", {"kind": "widgets"}, HU)
    assert status == 400


def test_switching_modes_is_allowed_in_every_state(srv, driving):
    path = "/ui/drive-mode/current/car/headunit/hu7"
    assert call(srv, "GET", path)[2]["selection"] is None
    for state in ("unknown", "moving", "parked"):
        driving.value = state
        status, _, reply = call(srv, "PUT", path, {"mode": "ostler.map"}, HU)
        assert status == 200 and reply["selection"]["mode"] == "ostler.map", state
    status, _, reply = call(srv, "PUT", path, {"mode": "ostler.offroad", "faces": {"ostler.offroad": 1},
                                               "rotation": ["ostler.dashboard", "ostler.map"]}, HU)
    assert status == 200
    got = call(srv, "GET", path)[2]
    assert got["vid"] == "v-test" and got["display"] == "headunit"
    assert got["selection"]["faces"] == {"ostler.offroad": 1}
    driving.value = "moving"
    # a pick that joins the rotation appends to it: allowed
    status, _, _ = call(srv, "PUT", path, {"mode": "ostler.offroad",
                                           "rotation": ["ostler.dashboard", "ostler.map", "ostler.offroad"]}, HU)
    assert status == 200
    # reordering the stored rotation is an edit: Park to edit
    status, _, reply = call(srv, "PUT", path, {"mode": "ostler.map",
                                               "rotation": ["ostler.map", "ostler.dashboard"]}, HU)
    assert status == 409 and reply["code"] == "park_to_edit"
    # a selection without a rotation keeps the stored one
    call(srv, "PUT", path, {"mode": "ostler.map"}, HU)
    assert call(srv, "GET", path)[2]["selection"]["rotation"] == [
        "ostler.dashboard", "ostler.map", "ostler.offroad"]


@pytest.mark.parametrize("method,path,body", [
    ("GET", "/ui/layouts/current/Car/hu7", None),
    ("GET", "/ui/layouts/current/car/hu11", None),
    ("GET", "/ui/layouts/current/car/hu7/widgets/x", None),
    ("GET", "/ui/layouts/bad vid!/car/hu7", None),
    ("GET", "/ui/drive-mode/current/car/Head Unit/hu7", None),
    ("PUT", "/ui/drive-mode/current/car/headunit/hu7", {"mode": 3}),
])
def test_bad_keys_are_400(srv, method, path, body):
    status, headers, reply = call(srv, method, path.replace(" ", "%20"), body, HU)
    assert status == 400 and reply["ok"] is False and reply["code"] == "bad_request", reply


@pytest.mark.parametrize("method,path", [
    ("GET", "/ui/nothing"), ("GET", "/ui/layouts/current/car"), ("PUT", "/ui/layouts/current/car/hu7"),
    ("DELETE", "/ui/layouts/current/car/hu7"), ("POST", "/ui/layouts/current/car/hu7/nope"),
    ("PUT", "/snapshot"),
])
def test_unknown_ui_routes_are_404_envelopes(srv, method, path):
    status, headers, reply = call(srv, method, path, {} if method != "GET" else None, HU)
    assert status == 404 and reply["code"] == "not_found"
    assert headers["Content-Type"] == "application/json"


def test_public_mode_reads_but_never_writes(tmp_path, driving, monkeypatch):
    monkeypatch.setenv("OSTLER_VEHICLE_ID", "v-test")
    driving.value = "parked"
    s = _server(tmp_path, driving, public=True, admin_password="pw")
    try:
        assert call(s, "GET", BASE)[0] == 200
        for method, path, body in (("PUT", ONE, user_mode()), ("DELETE", ONE, None),
                                   ("POST", f"{BASE}/reset", {}),
                                   ("PUT", "/ui/drive-mode/current/car/headunit/hu7", {"mode": "ostler.map"})):
            status, _, reply = call(s, method, path, body, HU)
            assert status == 403 and reply["code"] == "public_mode", (method, path)
    finally:
        s.shutdown()
        s.server_close()
        s.stop()


def test_the_store_lives_in_the_state_dir(srv, tmp_path, driving):
    driving.value = "parked"
    call(srv, "PUT", ONE, user_mode(), HU)
    assert (tmp_path / "state" / "settings.sqlite").exists()


def test_replies_match_the_openapi_schemas(srv, driving):
    """Real replies of every /ui/ operation validate against api/openapi.yaml."""
    from tests.test_api_contracts import OPENAPI, _load, _response_pointer, _validator

    doc = _load(OPENAPI)
    one = "/ui/layouts/{vid}/{profile}/{class}/{kind}/{id}"
    base = "/ui/layouts/{vid}/{profile}/{class}"
    sel = "/ui/drive-mode/{vid}/{profile}/{display}/{class}"
    bad = user_mode()
    bad["classes"]["hu7"][0]["widgets"][0]["style"] = "sparkline"
    steps = [
        ("GET", one, ONE, None, HU, "200", None),
        ("PUT", one, ONE, user_mode(), HU, "409", None),
        ("PUT", one, ONE, user_mode(), {"Ostler-Layout-Class": "tablet"}, "202", None),
        ("PUT", one, ONE, user_mode(), HU, "200", "parked"),
        ("PUT", one, ONE, bad, HU, "400", None),
        ("GET", base, BASE, None, HU, "200", None),
        ("DELETE", one, ONE, None, HU, "200", None),
        ("POST", f"{base}/reset", f"{BASE}/reset", {}, HU, "200", None),
        ("POST", f"{base}/undo-reset", f"{BASE}/undo-reset", None, HU, "200", None),
        ("GET", base, BASE, None, HU, "200", None),
        ("PUT", sel, "/ui/drive-mode/current/car/headunit/hu7", {"mode": "ostler.map"}, HU, "200", None),
        ("GET", sel, "/ui/drive-mode/current/car/headunit/hu7", None, HU, "200", None),
    ]
    for method, tpl, path, body, hdr, want, state in steps:
        if state:
            driving.value = state
        status, _, reply = call(srv, method, path, body, hdr)
        assert str(status) == want, (method, path, status, reply)
        v = _validator(doc, _response_pointer(doc, tpl, method.lower(), want))
        errors = list(v.iter_errors(reply))
        assert not errors, (method, path, errors[0].message)
