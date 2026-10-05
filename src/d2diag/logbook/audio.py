"""Session audio (ADR-0010; spec §3). Core: never imports web.

Contract:
* ``AudioTrackWriter(session_dir, track, mime, start_ms, source="phone")``:
  ``put(seq, data: bytes)`` appends chunks in seq order (holds up to 10 early chunks),
  ``close()``; files ``audio-<track>.<ext>`` (webm | m4a | wav).
* ``PiAudio(arecord="arecord")``: ``available() -> (bool, reason)``, ``start(session_dir) ->
  track | None``, ``stop()`` — runs ``arecord -q -f S16_LE -r 16000 -c 1`` as a subprocess.
* Tracks are registered in ``meta.audio[]``: ``{track, mime, start_ms, end_ms, source, bytes}``.

``start_ms``/``end_ms`` in ``meta.audio`` are SESSION milliseconds (the replay timeline), so a
player seeks to ``(t - start_ms) / 1000`` s. Audio never leaves the device and is never
served in public mode (the store refuses it).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid

MAX_EARLY = 10  # out-of-order chunks held while waiting for a predecessor
MAX_CHUNK = 4 * 1024 * 1024
TRACK_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,63}$")
_EXT = {"audio/webm": "webm", "video/webm": "webm", "audio/mp4": "m4a", "audio/m4a": "m4a",
        "audio/x-m4a": "m4a", "audio/aac": "m4a", "video/mp4": "m4a", "audio/wav": "wav",
        "audio/wave": "wav", "audio/x-wav": "wav", "audio/vnd.wave": "wav",
        "audio/ogg": "ogg"}
MIME_BY_EXT = {"webm": "audio/webm", "m4a": "audio/mp4", "wav": "audio/wav", "ogg": "audio/ogg"}
FILE_RE = re.compile(r"^audio-([0-9A-Za-z][0-9A-Za-z_-]{0,63})\.(webm|m4a|wav|ogg)$")


def ext_for(mime: str) -> str:
    """File extension for a MediaRecorder mime type (codec parameters ignored);
    ``ValueError`` for an unsupported type."""
    base = str(mime or "").split(";")[0].strip().lower()
    if base not in _EXT:
        raise ValueError(f"unsupported audio type: {mime!r}")
    return _EXT[base]


def mime_for(path: str) -> str:
    """The Content-Type to serve an ``audio-*.<ext>`` file with."""
    return MIME_BY_EXT.get(path.rsplit(".", 1)[-1].lower(), "application/octet-stream")


def track_file(session_dir: str, track: str) -> "str | None":
    """The existing ``audio-<track>.<ext>`` file in ``session_dir``, or None."""
    if not TRACK_RE.match(str(track or "")):
        return None
    try:
        names = os.listdir(session_dir)
    except OSError:
        return None
    for n in sorted(names):
        m = FILE_RE.match(n)
        if m and m.group(1) == track:
            return os.path.join(session_dir, n)
    return None


class AudioTrackWriter:
    """Appends one track's chunks, in ``seq`` order, to ``audio-<track>.<ext>``.

    A chunk that arrives early is held until its predecessor arrives. If more than
    ``MAX_EARLY`` are waiting, the missing chunk is given up as lost (``gaps`` counts them)
    and writing continues from the oldest held chunk. Repeated sequence numbers are ignored.
    """

    def __init__(self, session_dir: str, track: str, mime: str, start_ms: float = 0,
                 source: str = "phone") -> None:
        if not TRACK_RE.match(str(track or "")):
            raise ValueError("track must be 1–64 letters, digits, '-' or '_'")
        self.ext = ext_for(mime)
        self.track, self.mime = str(track), str(mime).split(";")[0].strip().lower()
        self.start_ms, self.end_ms = start_ms, None
        self.source = source
        self.path = os.path.join(session_dir, f"audio-{self.track}.{self.ext}")
        self._fh = open(self.path, "ab")
        self.bytes = self._fh.tell()
        self.next_seq = 0
        self.gaps = 0
        self._held: "dict[int, bytes]" = {}

    @property
    def closed(self) -> bool:
        return self._fh is None

    def put(self, seq: int, data: bytes) -> int:
        """Accept chunk ``seq``; returns the bytes written to the file by this call."""
        if self._fh is None:
            raise ValueError("track is closed")
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            raise ValueError("seq must be a non-negative integer")
        if len(data) > MAX_CHUNK:
            raise ValueError("audio chunk too large")
        if seq < self.next_seq or seq in self._held:
            return 0
        self._held[seq] = bytes(data)
        if len(self._held) > MAX_EARLY and self.next_seq not in self._held:
            self.gaps += min(self._held) - self.next_seq
            self.next_seq = min(self._held)
        return self._drain()

    def _drain(self) -> int:
        n = 0
        while self.next_seq in self._held:
            chunk = self._held.pop(self.next_seq)
            self._fh.write(chunk)
            n += len(chunk)
            self.next_seq += 1
        if n:
            self._fh.flush()
            self.bytes += n
        return n

    def sync(self, fsync=os.fsync) -> None:
        if self._fh is not None:
            self._fh.flush()
            try:
                fsync(self._fh.fileno())
            except OSError:
                pass

    def close(self, end_ms: "float | None" = None) -> None:
        """Flush whatever is held, in order (gaps are skipped), and close the file."""
        if self._fh is None:
            return
        for seq in sorted(self._held):
            chunk = self._held.pop(seq)
            self._fh.write(chunk)
            self.bytes += len(chunk)
        self._held.clear()
        self.sync()
        self._fh.close()
        self._fh = None
        if end_ms is not None:
            self.end_ms = end_ms

    def entry(self) -> dict:
        """The ``meta.audio[]`` entry."""
        return {"track": self.track, "mime": self.mime, "start_ms": self.start_ms,
                "end_ms": self.end_ms, "source": self.source, "bytes": self.bytes}


class PiAudio:
    """Cabin audio from the Pi's own microphone through ``arecord`` (ALSA). Never raises:
    a missing binary or a failed start is reported through ``available()``/``reason``."""

    ARGS = ("-q", "-f", "S16_LE", "-r", "16000", "-c", "1")
    MIME = "audio/wav"

    def __init__(self, arecord: str = "arecord", popen=subprocess.Popen,
                 which=shutil.which) -> None:
        self.arecord = arecord
        self._popen, self._which = popen, which
        self._proc = None
        self.track: "str | None" = None
        self.path: "str | None" = None
        self.reason: "str | None" = None

    def available(self) -> "tuple[bool, str | None]":
        try:
            found = self._which(self.arecord)
        except Exception:  # noqa: BLE001
            found = None
        if not found:
            return False, f"{self.arecord} not found (install alsa-utils)"
        if self.reason:
            return False, self.reason
        return True, None

    @property
    def running(self) -> bool:
        p = self._proc
        if p is None:
            return False
        try:
            return p.poll() is None
        except Exception:  # noqa: BLE001
            return False

    def start(self, session_dir: str) -> "str | None":
        """Start recording ``<session_dir>/audio-<track>.wav``; the track id, or None."""
        if self.running:
            return self.track
        try:
            exe = self._which(self.arecord)
        except Exception:  # noqa: BLE001
            exe = None
        if not exe:
            self.reason = None
            return None
        track = uuid.uuid4().hex[:12]
        path = os.path.join(session_dir, f"audio-{track}.wav")
        try:
            self._proc = self._popen([exe, *self.ARGS, path], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:  # noqa: BLE001
            self._proc = None
            self.reason = f"arecord failed to start ({type(exc).__name__}: {exc})"
            return None
        self.reason = None
        self.track, self.path = track, path
        return track

    def stop(self) -> "int":
        """Stop recording; returns the file size in bytes (0 if none)."""
        p, self._proc = self._proc, None
        if p is not None:
            try:
                p.terminate()
                p.wait(timeout=2.0)
            except Exception:  # noqa: BLE001
                try:
                    p.kill()
                except Exception:  # noqa: BLE001
                    pass
        try:
            return os.path.getsize(self.path) if self.path else 0
        except OSError:
            return 0


__all__ = ["AudioTrackWriter", "PiAudio", "ext_for", "mime_for", "track_file", "MAX_EARLY"]
