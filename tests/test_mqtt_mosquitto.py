# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Conformance of the stdlib MQTT 5 client against a real Mosquitto (NodeSource spec §12,
§13: the fallback to paho is taken only if this fails). Marked ``needs_broker``: it runs
where a ``mosquitto`` binary is installed and is skipped otherwise."""
from __future__ import annotations

import shutil
import socket
import subprocess
import time

import pytest

from openostler.mqtt import StdlibMqttClient, SubOptions, Will, codec

pytestmark = [pytest.mark.needs_broker,
              pytest.mark.skipif(shutil.which("mosquitto") is None,
                                 reason="needs a mosquitto binary (Mosquitto 2.x)")]


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def mosquitto(tmp_path_factory):
    port = _free_port()
    conf = tmp_path_factory.mktemp("mosq") / "m.conf"
    conf.write_text(f"listener {port} 127.0.0.1\nallow_anonymous true\npersistence false\n")
    proc = subprocess.Popen(["mosquitto", "-c", str(conf)], stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    end = time.monotonic() + 5
    while time.monotonic() < end:
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.05)
    yield ("127.0.0.1", port)
    proc.terminate()
    proc.wait(timeout=5)


def _wait(cond, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not cond():
        time.sleep(0.01)
    return cond()


def test_retained_flags_no_local_and_qos1(mosquitto):
    host, port = mosquitto
    node = StdlibMqttClient("conf-node", timeout=3)
    node.connect(host, port)
    node.publish("conf/v/node/status", b"online", qos=1, retain=True)
    brain = StdlibMqttClient("conf-brain", timeout=3)
    got = []
    brain.on_message = got.append
    brain.connect(host, port)
    assert brain.subscribe([SubOptions("conf/v/+/status", qos=1, no_local=True)]) == [1]
    assert _wait(lambda: len(got) == 1) and got[0].retain is True
    node.publish("conf/v/node/status", b"again", qos=1, retain=True)
    assert _wait(lambda: len(got) == 2) and got[1].retain is False and got[1].qos == 1
    brain.publish("conf/v/brain/status", b"self", qos=1)
    time.sleep(0.2)
    assert len(got) == 2  # No Local
    node.publish("conf/v/node/status", b"", qos=1, retain=True)  # clean up
    node.disconnect()
    brain.disconnect()


def test_will_on_abort(mosquitto):
    host, port = mosquitto
    watcher = StdlibMqttClient("conf-w", timeout=3)
    got = []
    watcher.on_message = got.append
    watcher.connect(host, port)
    watcher.subscribe([SubOptions("conf/w/+/status", qos=1)])
    n = StdlibMqttClient("conf-n", timeout=3,
                         will=Will("conf/w/n/status", b"offline", qos=1, retain=True))
    n.connect(host, port)
    n.abort()
    assert _wait(lambda: [m.payload for m in got] == [b"offline"])
    watcher.publish("conf/w/n/status", b"", qos=1, retain=True)
    watcher.disconnect(codec.SUCCESS)
