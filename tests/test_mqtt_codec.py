# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The MQTT 5 codec against the standard (OASIS MQTT Version 5.0, 2019): byte-exact
encodings worked out from the spec's field tables, round trips of every packet type and
property the NodeSource spec uses (§12, §13), the malformed cases a receiver must reject,
and the topic matching rules of §4.7."""
from __future__ import annotations

import pytest

from openostler.mqtt import codec
from openostler.mqtt.codec import (Connack, Connect, Disconnect, MalformedPacket, MqttError,
                                   PacketReader, Pingreq, Pingresp, ProtocolError, Puback,
                                   Publish, Suback, Subscribe, SubOptions, Unsuback,
                                   Unsubscribe, Will, decode, encode)


# ---- §1.5.5 variable byte integer ------------------------------------------------------- #
@pytest.mark.parametrize("n, wire", [
    (0, "00"), (127, "7f"), (128, "8001"), (16_383, "ff7f"), (16_384, "808001"),
    (2_097_151, "ffff7f"), (2_097_152, "80808001"), (268_435_455, "ffffff7f"),
])
def test_varint_boundaries(n, wire):
    assert codec.encode_varint(n).hex() == wire
    assert codec.decode_varint(bytes.fromhex(wire)) == (n, len(wire) // 2)


def test_varint_limits():
    with pytest.raises(ValueError):
        codec.encode_varint(268_435_456)
    with pytest.raises(MalformedPacket):
        codec.decode_varint(bytes.fromhex("ffffffff7f"))  # five bytes
    with pytest.raises(MalformedPacket):
        codec.decode_varint(bytes.fromhex("ff"))  # cut


# ---- byte-exact packets ------------------------------------------------------------------ #
def test_fixed_two_byte_packets():
    assert encode(Pingreq()).hex() == "c000"
    assert encode(Pingresp()).hex() == "d000"
    assert encode(Disconnect()).hex() == "e000"            # reason 0 and no properties: omitted
    assert encode(Disconnect(codec.DISCONNECT_WITH_WILL)).hex() == "e0020400"


def test_connect_bytes_with_will():
    pkt = Connect("n", keep_alive=10, clean_start=True, will=Will("s", b"off", qos=1, retain=True))
    want = ("10" "17"                      # CONNECT, remaining length 23
            "00044d515454" "05"            # "MQTT", level 5
            "2e"                           # will retain | will QoS 1 | will | clean start
            "000a" "00"                    # keep-alive 10, no properties
            "00016e"                       # client id "n"
            "00" "000173" "0003" "6f6666")  # will props, will topic "s", payload "off"
    assert encode(pkt).hex() == want
    assert decode(bytes.fromhex(want)) == pkt


def test_subscribe_option_byte():
    sub = SubOptions("a/+", qos=1, no_local=True, retain_as_published=False, retain_handling=2)
    assert sub.byte() == 0b0010_0101
    wire = encode(Subscribe(7, [sub])).hex()
    assert wire == "82" "09" "0007" "00" "0003612f2b" "25"   # SUBSCRIBE flags 0010
    assert decode(bytes.fromhex(wire)).subscriptions == [sub]


def test_publish_bytes_qos1_retained_with_expiry():
    pkt = Publish("t", b"hi", qos=1, retain=True, packet_id=1,
                  properties={"message_expiry_interval": 120})
    want = "33" "0d" "000174" "0001" "05" "0200000078" "6869"
    assert encode(pkt).hex() == want
    assert decode(bytes.fromhex(want)) == pkt


def test_short_forms_decode():
    # PUBACK with only the packet id means success; DISCONNECT with no body means 0.
    assert decode(bytes.fromhex("40020005")) == Puback(5)
    assert decode(bytes.fromhex("e000")) == Disconnect()
    assert decode(bytes.fromhex("20020000")) == Connack(0, False, {})


# ---- round trips ------------------------------------------------------------------------- #
ALL_PROPS = {
    "payload_format_indicator": 1, "message_expiry_interval": 90, "content_type": "application/json",
    "response_topic": "ostler/v1/v/node/act/01J", "correlation_data": b"\x01\x02",
    "subscription_identifier": [3, 70000], "session_expiry_interval": 60,
    "assigned_client_identifier": "x", "server_keep_alive": 5, "authentication_method": "m",
    "authentication_data": b"d", "request_problem_information": 0, "will_delay_interval": 2,
    "request_response_information": 1, "response_information": "r", "server_reference": "s",
    "reason_string": "why", "receive_maximum": 10, "topic_alias_maximum": 0, "topic_alias": 1,
    "maximum_qos": 1, "retain_available": 1, "user_property": [("k", "v"), ("k", "w")],
    "maximum_packet_size": 1 << 20, "wildcard_subscription_available": 1,
    "subscription_identifier_available": 0, "shared_subscription_available": 0,
}


def test_every_property_round_trips():
    assert set(ALL_PROPS) == {name for name, _ in codec.PROPERTIES.values()}
    pkt = Publish("p", b"", properties=ALL_PROPS)
    assert decode(encode(pkt)).properties == ALL_PROPS


@pytest.mark.parametrize("pkt", [
    Connect("brain-nodesource", 10, True, {"session_expiry_interval": 0}),
    Connect("tap", 10, False, {"session_expiry_interval": 60}, username="u", password=b"p"),
    Connect("n", 10, True, {}, Will("ostler/v1/v/n/status", b"offline", 1, True,
                                    {"message_expiry_interval": 5})),
    Connack(0, True, {"server_keep_alive": 5}), Connack(codec.NOT_AUTHORIZED),
    Publish("a/b", b"\x00\xff", 0), Publish("a/b", b"x", 1, True, True, 65535),
    Puback(9), Puback(9, codec.NOT_AUTHORIZED, {"reason_string": "acl"}),
    Subscribe(1, [SubOptions("a/#", 1, True, True, 1), SubOptions("+/b", 0)],
              {"subscription_identifier": [4]}),
    Suback(1, [1, 0, codec.NOT_AUTHORIZED]), Unsubscribe(2, ["a/#", "b"]), Unsuback(2, [0, 0x11]),
    Pingreq(), Pingresp(), Disconnect(codec.KEEP_ALIVE_TIMEOUT, {"reason_string": "late"}),
])
def test_packets_round_trip(pkt):
    assert decode(encode(pkt)) == pkt


# ---- receivers reject malformed input ---------------------------------------------------- #
@pytest.mark.parametrize("wire, err", [
    ("c100", MalformedPacket),                     # PINGREQ with reserved flags
    ("8005000100", MalformedPacket),               # SUBSCRIBE with flags 0000
    ("36050001740000", MalformedPacket),           # PUBLISH QoS 3
    ("34070001740001" "00", MqttError),            # PUBLISH QoS 2: not supported
    ("30060001740302", MalformedPacket),           # property length past the end
    ("300700017402" "7f00", MalformedPacket),      # unknown property 0x7f
    ("300a00017406" "0200000001" "02", MalformedPacket),  # truncated second property
    ("c00100", MalformedPacket),                   # PINGREQ with a body
    ("f000", ProtocolError),                       # AUTH: not supported
    ("8203000100", ProtocolError),                 # SUBSCRIBE without filters
])
def test_malformed(wire, err):
    with pytest.raises(err):
        decode(bytes.fromhex(wire))


def test_duplicate_property_is_a_protocol_error():
    props = codec.encode_varint(10) + bytes.fromhex("0200000001" "0200000002")
    body = codec.encode_str("t") + props
    with pytest.raises(ProtocolError):
        decode(bytes([0x30]) + codec.encode_varint(len(body)) + body)


def test_strings_reject_nul_and_bad_utf8():
    with pytest.raises(ValueError):
        codec.encode_str("a\x00b")
    with pytest.raises(MalformedPacket):
        decode(bytes.fromhex("3005" "0002" "c328" "00"))


def test_encoder_refuses_what_the_subset_lacks():
    with pytest.raises(ValueError):
        encode(Publish("t", b"", qos=2, packet_id=1))
    with pytest.raises(ValueError):
        encode(Publish("a/+", b""))                # wildcard in a topic name
    with pytest.raises(ValueError):
        encode(Publish("t", b"", qos=1))           # QoS 1 without a packet id
    with pytest.raises(ValueError):
        encode(Publish("t", b"", properties={"nonsense": 1}))


# ---- the stream reader -------------------------------------------------------------------- #
def test_reader_splits_and_joins_across_reads():
    big = Publish("t/x", bytes(range(256)) * 2, 1, packet_id=3)
    stream = encode(Pingresp()) + encode(big) + encode(Suback(1, [0]))
    for chunk in (1, 2, 3, 7, 64, len(stream)):
        r = PacketReader()
        got = []
        for i in range(0, len(stream), chunk):
            got += r.feed(stream[i:i + chunk])
        assert got == [Pingresp(), big, Suback(1, [0])], chunk


def test_reader_refuses_oversized_packets():
    with pytest.raises(MqttError):
        PacketReader(max_packet=10).feed(encode(Publish("t", b"x" * 20)))


# ---- §4.7 topic names and filters --------------------------------------------------------- #
@pytest.mark.parametrize("flt, topic, match", [
    ("sport/tennis/player1/#", "sport/tennis/player1", True),
    ("sport/tennis/player1/#", "sport/tennis/player1/ranking", True),
    ("sport/tennis/player1/#", "sport/tennis/player1/score/wimbledon", True),
    ("sport/#", "sport", True),
    ("sport/tennis/+", "sport/tennis/player1", True),
    ("sport/tennis/+", "sport/tennis/player1/ranking", False),
    ("sport/+", "sport", False),
    ("sport/+", "sport/", True),
    ("+/+", "/finance", True),
    ("/+", "/finance", True),
    ("+", "/finance", False),
    ("#", "$SYS/x", False),
    ("+/monitor/Clients", "$SYS/monitor/Clients", False),
    ("$SYS/#", "$SYS/monitor/Clients", True),
    ("ostler/v1/v/+/vss/+", "ostler/v1/v/node/vss/Vehicle.Speed", True),
    ("ostler/v1/v/+/vss/+", "ostler/v1/v/node/tap/01J/data", False),
])
def test_topic_matching(flt, topic, match):
    assert codec.topic_matches(flt, topic) is match


@pytest.mark.parametrize("flt, ok", [
    ("#", True), ("a/#", True), ("a/+/b", True), ("+", True),
    ("a/#/b", False), ("a#", False), ("a/b+", False), ("", False), ("a\x00", False),
])
def test_filter_validity(flt, ok):
    assert codec.valid_topic_filter(flt) is ok


def test_topic_name_validity():
    assert codec.valid_topic_name("ostler/v1/v/node/status")
    assert not codec.valid_topic_name("a/+")
    assert not codec.valid_topic_name("a/#")
    assert not codec.valid_topic_name("")
