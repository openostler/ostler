"""Session audio: phone chunk ordering, Pi arecord, meta.audio, never public (ADR-0010)."""

import pytest

from openostler.logbook import audio
from openostler.logbook.audio import AudioTrackWriter, PiAudio, ext_for, mime_for
from openostler.logbook.recorder import SessionRecorder
from openostler.logbook.store import SessionStore

pytestmark = pytest.mark.fake_pack

T0 = 1791277200.0


def test_ext_from_mime():
    assert ext_for("audio/webm;codecs=opus") == "webm"
    assert ext_for("audio/mp4") == "m4a" and ext_for("audio/x-m4a") == "m4a"
    assert ext_for("audio/wav") == "wav"
    with pytest.raises(ValueError):
        ext_for("text/html")
    assert mime_for("/x/audio-a.m4a") == "audio/mp4"


def test_chunks_written_in_seq_order(tmp_path):
    w = AudioTrackWriter(str(tmp_path), "trk1", "audio/webm", 1000)
    assert w.put(1, b"B") == 0 and w.put(2, b"C") == 0  # held until 0 arrives
    assert w.put(0, b"A") == 3
    assert w.put(1, b"dup") == 0  # repeated seq ignored
    w.put(3, b"D")
    w.close(end_ms=5000)
    assert (tmp_path / "audio-trk1.webm").read_bytes() == b"ABCD"
    assert w.entry() == {"track": "trk1", "mime": "audio/webm", "start_ms": 1000,
                         "end_ms": 5000, "source": "phone", "bytes": 4}
    with pytest.raises(ValueError):
        w.put(4, b"E")
    with pytest.raises(ValueError):
        AudioTrackWriter(str(tmp_path), "../evil", "audio/webm", 0)


def test_holds_at_most_ten_early_chunks(tmp_path):
    w = AudioTrackWriter(str(tmp_path), "t", "audio/mp4", 0)
    w.put(0, b"0")
    for s in range(2, 12):  # seq 1 lost; 10 early chunks are held
        assert w.put(s, bytes([65 + s])) == 0
    assert w.put(12, b"M") > 0  # the 11th: give up on seq 1 and continue
    assert w.gaps == 1 and w.next_seq == 13
    w.close()
    assert (tmp_path / "audio-t.m4a").read_bytes() == b"0" + bytes(range(67, 77)) + b"M"


def test_close_flushes_held_chunks_in_order(tmp_path):
    w = AudioTrackWriter(str(tmp_path), "t", "audio/wav", 0)
    w.put(2, b"c")
    w.put(1, b"b")
    w.close()
    assert (tmp_path / "audio-t.wav").read_bytes() == b"bc" and w.bytes == 2


class FakeProc:
    def __init__(self, args, **kw):
        self.args, self.alive, self.terminated = args, True, False
        open(args[-1], "wb").write(b"RIFF" + b"\0" * 40)

    def poll(self):
        return None if self.alive else 1

    def terminate(self):
        self.terminated, self.alive = True, False

    def wait(self, timeout=None):
        return 0


def test_pi_audio_missing_binary_never_crashes(tmp_path):
    pi = PiAudio(which=lambda name: None)
    ok, reason = pi.available()
    assert ok is False and "arecord" in reason
    assert pi.start(str(tmp_path)) is None and pi.stop() == 0

    def boom(*a, **k):
        raise OSError("no device")
    pi = PiAudio(which=lambda n: "/usr/bin/arecord", popen=boom)
    assert pi.start(str(tmp_path)) is None
    assert pi.available()[0] is False and "no device" in pi.available()[1]


def test_pi_audio_runs_arecord(tmp_path):
    procs = []

    def popen(args, **kw):
        procs.append(FakeProc(args))
        return procs[-1]
    pi = PiAudio(which=lambda n: "/usr/bin/arecord", popen=popen)
    assert pi.available() == (True, None)
    track = pi.start(str(tmp_path))
    assert procs[0].args[:8] == ["/usr/bin/arecord", "-q", "-f", "S16_LE", "-r", "16000",
                                 "-c", "1"]
    assert procs[0].args[8] == str(tmp_path / f"audio-{track}.wav") and pi.running
    assert pi.stop() == 44 and procs[0].terminated and not pi.running


def _rec(tmp_path):
    c = {"t": 0.0}
    r = SessionRecorder(str(tmp_path / "s"), clock=lambda: T0 + c["t"], mono=lambda: c["t"],
                        min_free_bytes=0)
    r.feed({"conn": "connected", "module": "motor", "signals": {"rpm": {"v": 800}},
            "faults": []}, None)
    return c, r


def test_recorder_phone_track_meta_events_and_store(tmp_path):
    c, r = _rec(tmp_path)
    sid = r.status()["session"]
    with pytest.raises(KeyError):
        r.audio_put("trk", 0, b"x", "audio/webm", session="20000101T000000Z")
    c["t"] = 2.0
    r.audio_put("trk", 1, b"BB", "audio/webm", start_ms=(T0 + 1.5) * 1000, session=sid)
    e = r.audio_put("trk", 0, b"AA", "audio/webm")
    assert e["start_ms"] == 1500 and e["bytes"] == 4 and e["source"] == "phone"
    c["t"] = 6.0
    done = r.audio_stop("trk")
    assert done["end_ms"] == 6000
    r.audio_put("trk2", 0, b"Z", "audio/mp4")  # open at session end
    c["t"] = 7.0
    r.close()
    store = SessionStore(str(tmp_path / "s"), demo_root=None)
    meta = store.meta(sid)
    assert [(a["track"], a["bytes"], a["end_ms"]) for a in meta["audio"]] == [
        ("trk", 4, 6000), ("trk2", 1, 7000)]
    ev = [(x["track"], x["state"]) for x in store.events(sid) if x["type"] == "audio"]
    assert ev == [("trk", "start"), ("trk", "stop"), ("trk2", "start"), ("trk2", "stop")]
    p = store.audio_path(sid, "trk")
    assert p.endswith("audio-trk.webm") and open(p, "rb").read() == b"AABB"
    assert store.audio_mime(p) == "audio/webm"
    for bad in (lambda: store.audio_path(sid, "trk", public=True),
                lambda: store.audio_path(sid, "nope"),
                lambda: store.audio_path(sid, "../meta"),
                lambda: store.audio_path("20261005T090000Z", "trk", public=True)):
        with pytest.raises(KeyError):
            bad()


def test_recorder_pi_audio_start_lost_and_stop(tmp_path):
    procs = []

    def popen(args, **kw):
        procs.append(FakeProc(args))
        return procs[-1]
    c, r = _rec(tmp_path)
    sid = r.status()["session"]
    r.set_pi_audio(PiAudio(which=lambda n: "/usr/bin/arecord", popen=popen))
    assert len(procs) == 1
    c["t"] = 3.0
    procs[0].alive = False  # arecord died (USB mic unplugged)
    r.feed({"conn": "connected", "module": "motor", "signals": {}, "faults": []}, None)
    r.close()
    store = SessionStore(str(tmp_path / "s"), demo_root=None)
    states = [x["state"] for x in store.events(sid) if x["type"] == "audio"]
    assert states == ["start", "lost"]
    (a,) = store.meta(sid)["audio"]
    assert a["source"] == "pi" and a["mime"] == "audio/wav" and a["end_ms"] == 3000
    # next session starts Pi audio by itself; turning it off stops it
    c["t"] = 10.0
    r.feed({"conn": "connected", "module": "motor", "signals": {"rpm": {"v": 1}},
            "faults": []}, None)
    assert len(procs) == 2 and procs[1].alive
    r.set_pi_audio(None)
    assert procs[1].terminated
    r.close()
    assert audio.MAX_EARLY == 10
