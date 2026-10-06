# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Public mode needs an admin password, and community writes are guarded (security)."""
from __future__ import annotations

import base64
import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from openostler.pack import use_pack
from tests.fake_pack import FAKE_PACK


class _Community:
    """Records calls; stands in for openostler.community.Community."""

    def __init__(self):
        self.calls: list = []

    def set_consent(self, consent, vehicle=None):
        self.calls.append(("consent", consent))
        return {"ok": True, "consent": consent}

    def contribute(self, record):
        self.calls.append(("contribute", record))
        return {"ok": True}

    def status(self):
        return {"consent": False}


@pytest.fixture
def fake_pack():
    with use_pack(FAKE_PACK) as pack:
        yield pack


def _start(pack, tmp_path, **kw):
    from openostler.web.server import DiagServer

    srv = DiagServer(pack.sources("auto"), host="127.0.0.1", port=0,
                     poll_interval=0.05, stream_interval=0.05, csv_dir=str(tmp_path),
                     menus=pack.menus, geocoder=None, **kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.05)
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _stop(srv):
    srv.shutdown()
    srv.server_close()
    srv.stop()


def _post(base, path, body, password=None):
    req = urllib.request.Request(base + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    if password:
        token = base64.b64encode(f"admin:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def test_public_mode_without_an_admin_password_refuses_to_start(fake_pack, tmp_path):
    from openostler.web.server import DiagServer

    with pytest.raises(ValueError, match="admin password"):
        DiagServer(fake_pack.sources("auto"), host="127.0.0.1", port=0, public=True,
                   csv_dir=str(tmp_path), menus=fake_pack.menus, geocoder=None)


def test_public_mode_refuses_community_writes(fake_pack, tmp_path):
    c = _Community()
    srv, base = _start(fake_pack, tmp_path, public=True, admin_password="pw", community=c)
    try:
        assert _post(base, "/community/consent", {"consent": True}) == 403
        assert _post(base, "/community/contribute", {"x": 1}, password="pw") == 403
        assert c.calls == []
    finally:
        _stop(srv)


def test_contribute_needs_admin_but_consent_is_the_users_own(fake_pack, tmp_path):
    c = _Community()
    srv, base = _start(fake_pack, tmp_path, admin_password="pw", community=c)
    try:
        assert _post(base, "/community/contribute", {"x": 1}) == 401
        assert _post(base, "/community/contribute", {"x": 1}, password="pw") == 200
        assert _post(base, "/community/consent", {"consent": True}) == 200   # first-run screen
        assert c.calls == [("contribute", {"x": 1}), ("consent", True)]
    finally:
        _stop(srv)
