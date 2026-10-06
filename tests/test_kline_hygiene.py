# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Session hygiene and ISO 9141-2 framing (spec K-line profiles §3, §4, §7): P3min,
keep-alive, release, abandoned sessions, and the ISO 9141 burst split (muki01 regressions).
All timing runs on a FakeClock; nothing sleeps."""
import pytest

from openostler.kline import KLine
from openostler.kline.frame_iso9141 import Iso9141FrameError, encode, split, strip_echo
from openostler.kline.iso9141 import Iso9141Session
from openostler.kline.profiles import BUILTIN, resolve
from openostler.kwp2000 import KWP2000
from openostler.session import EcuSession
from tests.fakes import FakeClock, FakeIso9141Ecu, FakeKLineEcu, iso9141_reply

READ = bytes.fromhex("022101") + bytes([0x24])          # 02 21 01 cs (unaddressed)
READ_REPLY = bytes.fromhex("026101") + bytes([0x64])
STOP = bytes.fromhex("018283")                          # 01 82 83
STOP_OK = bytes.fromhex("01C2C3")


def _kwp_link(profile=None, responses=None, clock=None):
    clock = clock or FakeClock()
    ecu = FakeKLineEcu(responses or {READ: READ_REPLY, STOP: STOP_OK})
    p = profile or BUILTIN["kwp2000_fast"]
    k = KLine.from_profile(ecu, p, clock=clock, sleep=clock.sleep)
    k.open()
    kwp = KWP2000.from_profile(k, p)
    return ecu, k, EcuSession(kwp, p), clock


# ---- P3 minimum (§4.4) ------------------------------------------------------------- #
def test_p3_min_waits_after_the_reply_end():
    ecu, k, s, clock = _kwp_link()
    s._kwp.request(0x21, b"\x01")
    end = k.last_rx_end
    clock.advance(0.010)
    clock.sleeps.clear()
    s._kwp.request(0x21, b"\x01")
    assert clock.sleeps[0] == pytest.approx(0.045)
    assert k.last_tx == pytest.approx(end + 0.055)


def test_p3_min_zero_sends_at_once():
    ecu, k, s, clock = _kwp_link(resolve("kwp2000_fast", {"timing": {"p3_min": 0.0}}))
    s._kwp.request(0x21, b"\x01")
    clock.advance(0.010)
    clock.sleeps.clear()
    s._kwp.request(0x21, b"\x01")
    assert clock.sleeps == []


def test_legacy_kline_has_no_p3_guard():
    k = KLine(FakeKLineEcu({READ: READ_REPLY}))
    assert k.p3_min == 0.0 and k.profile is None


# ---- keep-alive (§4.1) --------------------------------------------------------------- #
def _idle(session, clock, k, seconds=10.0, step=0.5):
    sent_at = []
    t0 = clock.now()
    while clock.now() - t0 < seconds - 1e-9:
        clock.advance(step)
        if session.keepalive_if_due():
            sent_at.append(round(k.last_tx - t0, 3))
    return sent_at


def test_kwp_keepalive_on_a_10s_idle_session():
    ecu, k, s, clock = _kwp_link(responses={READ: READ_REPLY,
                                            bytes.fromhex("023E0141"): bytes.fromhex("017E7F")})
    s._kwp.request(0x21, b"\x01")
    before = len(ecu.sent)
    times = _idle(s, clock, k, seconds=9.5)
    assert times == [2.0, 4.0, 6.0, 8.0]
    assert ecu.sent[before:] == [bytes.fromhex("023E0141")] * 4       # 3E 01
    gaps = [b - a for a, b in zip([0.0] + times, times)]
    assert max(gaps) < BUILTIN["kwp2000_fast"].timing.p3_max          # inside P3max


def test_iso9141_keepalive_on_a_10s_idle_session():
    clock = FakeClock()
    ecu = FakeIso9141Ecu()
    k = KLine.from_profile(ecu, BUILTIN["iso9141_2"], clock=clock, sleep=clock.sleep)
    k.open()
    s = Iso9141Session(k)
    s.init()
    before = len(ecu.sent)
    times = _idle(s, clock, k, seconds=9.5)
    assert times == [2.0, 4.0, 6.0, 8.0]
    assert ecu.sent[before:] == [bytes.fromhex("686AF10100C4")] * 4


def test_continuous_polling_sends_no_extra_keepalive():
    ecu, k, s, clock = _kwp_link()
    for _ in range(20):
        clock.advance(0.5)
        s._kwp.request(0x21, b"\x01")
        assert s.keepalive_if_due() is False
    assert all(f == READ for f in ecu.sent)


def test_bare_3e_override():
    p = resolve("kwp2000_fast", {"keepalive": b"\x3E", "keepalive_interval": 1.0})
    ecu, k, s, clock = _kwp_link(p)
    s._kwp.request(0x21, b"\x01")
    clock.advance(1.0)
    assert s.keepalive_if_due() is True
    assert ecu.sent[-1] == bytes.fromhex("013E3F")                   # bare 3E, never 3E 01


def test_failed_keepalive_is_logged_not_raised():
    events = []
    ecu, k, s, clock = _kwp_link(responses={})
    k.on_event = lambda kind, **f: events.append((kind, f))
    clock.advance(3.0)
    assert s.keepalive_if_due() is True
    assert events[-1][0] == "keepalive" and events[-1][1]["ok"] is False


def test_no_keepalive_when_the_profile_has_none():
    ecu, k, s, clock = _kwp_link(resolve("kwp2000_fast", {"keepalive": None}))
    clock.advance(10.0)
    assert s.keepalive_if_due() is False and ecu.sent == []


# ---- tester_present follows the profile (migration step 2) --------------------------- #
TP_BARE = bytes.fromhex("013E3F")                       # 01 3E 3F (bare 3E)
TP_SUB = bytes.fromhex("023E0141")                      # 02 3E 01 41


class _BareSubSession(EcuSession):
    _keepalive_sub = None                               # the legacy SLABS setting


def test_tester_present_sends_the_profiles_bare_3e():
    p = resolve("kwp2000_fast", {"keepalive": b"\x3E"})
    ecu, k, s, clock = _kwp_link(p, responses={TP_BARE: bytes.fromhex("017E7F")})
    s.tester_present()
    assert ecu.sent == [TP_BARE]


def test_tester_present_profile_wins_over_the_legacy_sub():
    ecu, k, _s, clock = _kwp_link(responses={TP_SUB: bytes.fromhex("017E7F")})
    s = _BareSubSession(_s._kwp, BUILTIN["kwp2000_fast"])
    s.tester_present()
    assert ecu.sent == [TP_SUB]                         # 3E 01 from the profile


def test_tester_present_without_a_profile_keepalive_uses_the_legacy_sub():
    p = resolve("kwp2000_fast", {"keepalive": None})
    ecu, k, _s, clock = _kwp_link(p, responses={TP_BARE: bytes.fromhex("017E7F")})
    _BareSubSession(_s._kwp, p).tester_present()
    _BareSubSession(_s._kwp).tester_present()           # no profile at all
    assert ecu.sent == [TP_BARE, TP_BARE]


# ---- release and abandoned sessions (§4.2, §4.3) ------------------------------------ #
def test_kwp_close_sends_82_and_a_confirmed_c2_means_only_w5():
    ecu, k, s, clock = _kwp_link()
    k.abandoned = True                      # a link is open
    s.release()
    assert STOP in ecu.sent and k.abandoned is False
    clock.sleeps.clear()
    k._pre_init_idle()
    assert clock.sleeps == [pytest.approx(0.3)]                       # W5 only


def test_kwp_release_without_c2_leaves_the_session_abandoned():
    ecu, k, s, clock = _kwp_link(responses={READ: READ_REPLY})
    s._kwp.request(0x21, b"\x01")
    k.abandoned = True
    s.release()
    assert STOP in ecu.sent and k.abandoned is True
    clock.advance(1.0)
    clock.sleeps.clear()
    k._pre_init_idle()
    assert clock.sleeps == [pytest.approx(4.0)]                       # P3max since last_tx


def test_iso9141_close_sends_nothing_and_next_init_waits_p3max():
    clock = FakeClock()
    ecu = FakeIso9141Ecu()
    k = KLine.from_profile(ecu, BUILTIN["iso9141_2"], clock=clock, sleep=clock.sleep)
    k.open()
    s = Iso9141Session(k)
    s.init()
    s.request(b"\x01\x00")
    n = len(ecu.sent)
    s.release()
    assert len(ecu.sent) == n                                         # nothing sent
    clock.sleeps.clear()
    s.init()
    assert clock.sleeps[0] == pytest.approx(5.0)                      # waits P3max


def test_first_init_waits_only_w5_not_the_muki01_5_5s():
    clock = FakeClock()
    k = KLine.from_profile(FakeIso9141Ecu(), BUILTIN["iso9141_2"], clock=clock,
                           sleep=clock.sleep)
    k.open()
    k.slow_init_reply()
    assert clock.sleeps[0] == pytest.approx(0.3)


def test_d2_style_abandoned_idle_zero_keeps_its_own_idle():
    p = resolve("kwp2000_fast", {"pre_init_idle": 0.3, "abandoned_idle": 0.0})
    ecu, k, s, clock = _kwp_link(p)
    k.abandoned, k.last_tx = True, clock.now()
    clock.sleeps.clear()
    k._pre_init_idle()
    assert clock.sleeps == [pytest.approx(0.3)]


# ---- ISO 9141-2 framing (§3) ----------------------------------------------------------- #
def test_encode_checksum():
    assert encode(b"\x01\x00") == bytes.fromhex("686AF10100C4")
    with pytest.raises(Iso9141FrameError):
        encode(b"")
    with pytest.raises(Iso9141FrameError):
        encode(bytes(8))


def test_echo_is_stripped():
    req = encode(b"\x01\x00")
    reply = iso9141_reply(0x10, b"\x41\x00\xbe\x1f\xa8\x13")
    frames = split(req + reply, sent=req)
    assert [f.data for f in frames] == [b"\x41\x00\xbe\x1f\xa8\x13"]
    assert strip_echo(req + reply, req) == reply


def test_bad_checksum_is_rejected():
    bad = bytearray(iso9141_reply(0x10, b"\x41\x0c\x1a\xf8"))
    bad[-1] ^= 0xFF
    dropped = []
    assert split(bytes(bad), on_drop=dropped.append) == []
    assert dropped == [bytes(bad)]


def test_dtcs_over_two_frames_split_into_two_frames():
    """4+ DTCs: two 48 6B frames in one burst. Header bytes never read as DTCs."""
    f1 = iso9141_reply(0x10, bytes.fromhex("43 01 33 02 44 03 55"))
    f2 = iso9141_reply(0x10, bytes.fromhex("43 04 66 00 00 00 00"))
    frames = split(f1 + f2)
    assert [f.data for f in frames] == [bytes.fromhex("43 01 33 02 44 03 55"),
                                        bytes.fromhex("43 04 66 00 00 00 00")]
    dtcs = [f.data[i:i + 2] for f in frames for i in (1, 3, 5)]
    assert bytes.fromhex("486B") not in dtcs


def test_merged_two_ecu_burst_keeps_both_addresses():
    a = iso9141_reply(0x10, b"\x41\x00\xbe\x1f\xa8\x13")
    b = iso9141_reply(0x1A, b"\x41\x00\x80\x00\x00\x01")
    frames = split(a + b)
    assert [f.ecu for f in frames] == [0x10, 0x1A]


def test_checksum_verified_not_fixed_offsets():
    """A data byte pair 48 6B inside a frame does not cut it: only a verifying split does."""
    tricky = iso9141_reply(0x10, b"\x41\x0c\x48\x6b")
    frames = split(tricky)
    assert len(frames) == 1 and frames[0].data == b"\x41\x0c\x48\x6b"


def test_trailing_glitch_after_a_frame():
    f = iso9141_reply(0x10, b"\x41\x0d\x00")
    assert [x.data for x in split(f + b"\xf8")] == [b"\x41\x0d\x00"]


def test_kline_request_iso9141_returns_frames():
    clock = FakeClock()
    ecu = FakeIso9141Ecu()
    k = KLine.from_profile(ecu, BUILTIN["iso9141_2"], clock=clock, sleep=clock.sleep)
    k.open()
    frames = k.request_iso9141(b"\x01\x00")
    assert ecu.sent[-1] == bytes.fromhex("686AF10100C4")
    assert frames[0].ecu == 0x10 and frames[0].data[:2] == b"\x41\x00"


def test_iso9141_session_needs_an_iso_profile():
    with pytest.raises(ValueError):
        Iso9141Session(KLine(FakeKLineEcu()))
