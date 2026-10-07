# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Node topics and payloads (NodeSource spec §1, §4, §6.3; ``ostler-firmware``
``firmware/README.md``, ``components/poll/src/poll.c``).

Topics live under ``ostler/v1/<vid>/<device>/``: ``status`` (plain text ``online``, will
``offline``, ``asleep`` before a clean sleep), ``power`` (the ADR-0040 record),
``vss/<leaf>`` where the leaf is a VSS path (``Vehicle.…``) or a pack leaf
``<pack>.<module>.<field>``, and (P3) the retained capability ``manifest`` and role claims
``role/<role>[/<scope>]`` (ADR-0037 §3), and (module-bus spec v1.3) the retained whole
fault list ``faults/<pack>.<module>`` (§6.2) and the QoS 1 events ``event/<name>`` (§6.1).
Pure functions: no I/O.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

PREFIX = "ostler/v1"
STATUS, POWER, VSS, TAP = "status", "power", "vss", "tap"
MANIFEST, ROLE = "manifest", "role"
FAULTS, EVENT = "faults", "event"
# Module-bus spec §6: the one reading published at QoS 1 (owner answer 7), a written
# exception to the ``vss`` QoS 0 rule; the Brain subscribes to it at QoS 1 as well.
ALARM_STATE = "Vehicle.Ostler.Security.Alarm.State"
FAULT_STATUSES = ("ok", "faults", "error", "unimplemented")
EVENT_SEVERITIES = ("info", "warning", "alarm")
# ADR-0037 §3 and its Amendment 8 (ADR-0040 §1): ``asleep`` is a clean sleep, ``offline``
# the will (an unexpected loss).
STATUS_VALUES = ("online", "offline", "asleep")
# ADR-0040 §1 power states. The node publishes awake, asleep and shutting_down today;
# ``off`` (no supply) is announced by each device itself before its supply is cut, and its
# feed owner reports the cut in its own ``feeds`` (module-bus spec v1.3 §5, owner answer 6).
POWER_STATES = ("off", "awake", "held", "waking", "asleep", "shutting_down")
FEED_STATES = ("on", "off")  # a feed owner's switched supply (module-bus spec v1.3 §5)
# ADR-0033's user action categories, and ``system``: a device-to-device power order (the
# ``shutdown`` act, module-bus spec v1.3 §11) that is not one of them and no role grants.
USER_CATEGORIES = ("read", "comfort", "security", "accessories", "maintenance",
                   "actuator_tests", "procedures")
SYSTEM_CATEGORY = "system"
ACT_CATEGORIES = (*USER_CATEGORIES, SYSTEM_CATEGORY)

# A VIN: 17 characters, digits and capitals without I, O, Q (ISO 3779). A ``vid`` that looks
# like one is refused, as the node refuses it (ADR-0036).
_VIN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
_LEVEL = re.compile(r"^[^/+#\x00]+$")


def vin_shaped(s: str) -> bool:
    return bool(_VIN.match((s or "").upper()))


def check_vid(vid: str) -> str:
    """The vehicle id for topics; raises ValueError when empty, not one topic level, or
    VIN-shaped."""
    if not isinstance(vid, str) or not _LEVEL.match(vid):
        raise ValueError(f"invalid vehicle id for MQTT topics: {vid!r}")
    if vin_shaped(vid):
        raise ValueError("the vehicle id looks like a VIN; a VIN is never a topic (ADR-0036)")
    return vid


def subscriptions(vid: str) -> "list[tuple[str, int]]":
    """The read-only subscription set (spec §4): ``(filter, max QoS)``: P1's ``status``,
    ``power`` and ``vss/+``, P3's ``manifest`` and ``role/#``, and the module-bus spec
    v1.3 topics ``faults/+`` and ``event/+`` (QoS 1, §6.1, §6.2) plus the alarm state at
    QoS 1 (§6: its one QoS 1 reading; ``vss/+`` caps the rest at 0). Never ``#`` on the
    vehicle, never a request topic."""
    base = f"{PREFIX}/{check_vid(vid)}/+"
    return [(f"{base}/status", 1), (f"{base}/power", 1), (f"{base}/vss/+", 0),
            (f"{base}/manifest", 1), (f"{base}/role/#", 1),
            (f"{base}/{VSS}/{ALARM_STATE}", 1), (f"{base}/{FAULTS}/+", 1),
            (f"{base}/{EVENT}/+", 1)]


def tap_subscriptions(vid: str) -> "list[tuple[str, int]]":
    """The raw-tap filters (spec §4, P2): headers and batches, QoS 1. Subscribed only while
    a session records (owner answer 9), on their own connection (session expiry 60 s)."""
    base = f"{PREFIX}/{check_vid(vid)}/+/tap/+"
    return [(f"{base}/meta", 1), (f"{base}/data", 1)]


def parse_tap_rest(rest: str) -> "Optional[tuple[str, str]]":
    """``<session>/meta`` or ``<session>/data`` (a ``tap`` topic's remainder) →
    ``(session, part)``; None for anything else (``tap/ctl`` is never read)."""
    session, sep, part = rest.partition("/")
    if not sep or part not in ("meta", "data") or not session:
        return None
    return session, part


@dataclass(frozen=True)
class Topic:
    vid: str
    device: str
    kind: str          # status | power | vss | tap | manifest | role | anything later
    rest: str = ""     # the vss leaf, or the remainder for other kinds


def parse_topic(topic: str) -> "Optional[Topic]":
    parts = topic.split("/")
    if len(parts) < 5 or "/".join(parts[:2]) != PREFIX:
        return None
    return Topic(parts[2], parts[3], parts[4], "/".join(parts[5:]))


def parse_status(payload: bytes) -> "Optional[str]":
    """``online`` / ``offline`` (plain text, not JSON); anything else is None."""
    try:
        s = payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None
    return s if s in STATUS_VALUES else None


def _json_obj(payload: bytes) -> "Optional[dict]":
    try:
        obj = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None
    return obj if isinstance(obj, dict) else None


def parse_power(payload: bytes) -> "Optional[dict]":
    """The power record when it is an object with a known ``state``; else None. ``feeds``
    (module-bus spec v1.3 §5, a feed owner's switched supplies) is kept as a list of
    ``{target, state: on | off, since}``; an entry of the wrong shape is dropped, and a
    ``feeds`` that is not a list is removed (the rest of the record is kept)."""
    obj = _json_obj(payload)
    if obj is None or obj.get("state") not in POWER_STATES:
        return None
    if "feeds" in obj:
        feeds = obj["feeds"]
        if not isinstance(feeds, list):
            del obj["feeds"]
        else:
            obj["feeds"] = [
                {"target": f["target"], "state": f["state"],
                 "since": f.get("since") if isinstance(f.get("since"), str) else None}
                for f in feeds
                if isinstance(f, dict) and isinstance(f.get("target"), str) and f["target"]
                and f.get("state") in FEED_STATES]
    return obj


def feed_states(powers: "dict[str, dict | None]") -> "dict[str, dict]":
    """``{target: {owner, state, since}}`` from every device's power record (spec §5): who
    reports each switched supply. With two owners reporting one target, ``off`` wins (a
    consumer never reads a cut supply as on)."""
    out: "dict[str, dict]" = {}
    for owner in sorted(powers):
        for f in (powers[owner] or {}).get("feeds") or []:
            cur = out.get(f["target"])
            if cur is None or (f["state"] == "off" and cur["state"] != "off"):
                out[f["target"]] = {"owner": owner, "state": f["state"], "since": f["since"]}
    return out


def parse_shutdown(payload: bytes) -> "Optional[dict]":
    """A ``shutdown`` order (module-bus spec v1.3 §11, owner answer 6), read for the record
    only (the Brain sends none; P4): ``{id, target, action: "shutdown", params: {timeout_s,
    reason}, category: "system", tier: 0, …}`` on the power owner's own ``act/<id>``.
    ``system`` marks a device-to-device power order: not an ADR-0033 user category, never
    granted by a role. None for anything else."""
    obj = _json_obj(payload)
    if (obj is None or obj.get("action") != "shutdown" or obj.get("category") != SYSTEM_CATEGORY
            or obj.get("tier") != 0 or not isinstance(obj.get("id"), str)
            or not isinstance(obj.get("target"), str)):
        return None
    params = obj.get("params") if isinstance(obj.get("params"), dict) else {}
    timeout = _int(params.get("timeout_s"))
    return {**obj, "params": {"timeout_s": timeout,
                              "reason": params.get("reason")
                              if isinstance(params.get("reason"), str) else None}}


def role_grantable(category: "str | None") -> bool:
    """Whether a user role can ever grant ``category`` (ADR-0033): the user categories
    yes, ``system`` (a device-to-device power order, spec §11) never."""
    return category in USER_CATEGORIES


def parse_manifest(payload: bytes) -> "Optional[dict]":
    """A device's capability manifest (UI spec §5.1 device entry; the firmware's
    sensor-detection spec §7 in ``ostler-firmware``): a JSON object. The list and object fields the
    cluster view reads are checked for their type; a wrong one is dropped (the rest is
    kept). None when it is not a JSON object."""
    obj = _json_obj(payload)
    if obj is None:
        return None
    for key in ("roles", "transmit", "items", "links", "actions", "signals", "problems"):
        if key in obj and not isinstance(obj[key], list):
            del obj[key]
    for key in ("memory", "power"):
        if key in obj and not isinstance(obj[key], dict):
            del obj[key]
    for key in ("id", "kind", "variant", "model", "board", "fw", "etag"):
        if key in obj and not isinstance(obj[key], str):
            del obj[key]
    if "priority" in obj and not isinstance(_num(obj["priority"]), (int, float)):
        del obj["priority"]
    return obj


def parse_role_rest(rest: str) -> "Optional[tuple[str, str | None]]":
    """``<role>`` or ``<role>/<scope>`` (a ``role`` topic's remainder) → ``(role, scope)``;
    None for anything deeper or empty."""
    parts = rest.split("/") if rest else []
    if not parts or not parts[0] or len(parts) > 2 or (len(parts) == 2 and not parts[1]):
        return None
    return parts[0], (parts[1] if len(parts) == 2 else None)


def parse_claim(payload: bytes) -> "Optional[dict]":
    """A role claim ``{role, scope, term, priority, since, reason}`` (ADR-0037 §3). An
    empty payload is a release (returns ``{}``); None when unreadable."""
    if not payload:
        return {}
    obj = _json_obj(payload)
    if obj is None:
        return None
    term = _int(obj.get("term"))
    return {"role": obj.get("role") if isinstance(obj.get("role"), str) else None,
            "scope": obj.get("scope") if isinstance(obj.get("scope"), str) else None,
            "term": term if term is not None else 0,
            "priority": _num(obj.get("priority")),
            "since": obj.get("since") if isinstance(obj.get("since"), str) else None,
            "reason": obj.get("reason") if isinstance(obj.get("reason"), str) else None}


def _num(v) -> "int | float | None":
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _int(v) -> "Optional[int]":
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def parse_faults_rest(rest: str) -> "Optional[tuple[str, str]]":
    """``<pack>.<module>`` (a ``faults`` topic's remainder, spec §6.2) → ``(pack,
    module)``; None for anything else (no dot, an empty part, a deeper topic)."""
    if not rest or "/" in rest:
        return None
    pack, sep, module = rest.partition(".")
    if not sep or not pack or not module:
        return None
    return pack, module


def parse_faults(payload: bytes) -> "Optional[dict]":
    """A whole fault list (module-bus spec §6.2): ``{module, status, faults: [{code, text?,
    state?, c}], note?, ts, t_us, boot, source}``. An empty payload is a cleared topic
    (returns ``{}``: "not read" again). None when unreadable: not a JSON object, a
    ``status`` outside ``ok | faults | error | unimplemented``, or ``faults`` not a list.
    A fault without a string ``code`` is dropped; its confidence is ``candidate`` unless
    the node says ``proven`` (never raised)."""
    if not payload:
        return {}
    obj = _json_obj(payload)
    if obj is None or obj.get("status") not in FAULT_STATUSES:
        return None
    raw = obj.get("faults", [])
    if not isinstance(raw, list):
        return None
    faults = []
    for f in raw:
        if not isinstance(f, dict) or not isinstance(f.get("code"), str) or not f["code"]:
            continue
        item = {"code": f["code"], "c": "proven" if f.get("c") == "proven" else "candidate"}
        for k in ("text", "state"):
            if isinstance(f.get(k), str) and f[k]:
                item[k] = f[k]
        faults.append(item)
    return {"module": obj.get("module") if isinstance(obj.get("module"), str) else None,
            "status": obj["status"], "faults": faults,
            "note": obj.get("note") if isinstance(obj.get("note"), str) else None,
            "ts": obj.get("ts") if isinstance(obj.get("ts"), str) else None,
            "t_us": _int(obj.get("t_us")), "boot": _int(obj.get("boot")),
            "source": obj.get("source") if isinstance(obj.get("source"), str) else None}


_EVENT_NAME = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)*$")


def parse_event(name: str, payload: bytes) -> "Optional[dict]":
    """One event (module-bus spec §6.1) on ``event/<name>``: ``{id, name, class, severity,
    ts, t_us, boot, source?, cause?, text?}``. ``name`` is the topic's (dotted, lower
    case); ``id`` (a ULID) is required, since consumers de-duplicate by it. A severity
    outside ``info | warning | alarm`` reads as None (shown, never upgraded). None when
    unreadable."""
    if not name or not _EVENT_NAME.match(name):
        return None
    obj = _json_obj(payload)
    if obj is None or not isinstance(obj.get("id"), str) or not obj["id"]:
        return None

    def text(k: str) -> "str | None":
        v = obj.get(k)
        return v if isinstance(v, str) and v else None

    sev = obj.get("severity")
    return {"id": obj["id"], "name": name, "class": text("class"),
            "severity": sev if sev in EVENT_SEVERITIES else None,
            "ts": text("ts"), "t_us": _int(obj.get("t_us")), "boot": _int(obj.get("boot")),
            "source": text("source"), "cause": text("cause"), "text": text("text")}


@dataclass(frozen=True)
class VssValue:
    """One parsed ``vss/<leaf>`` payload."""

    leaf: str
    value: "float | None"        # None: not a number (dropped from the snapshot, logged)
    unit: str
    ts: "str | None"             # RFC 3339 UTC, null until SNTP
    t_us: "int | None"           # the node's monotonic clock
    boot: "int | None"           # the node's boot counter (exact reboot detection)
    source: str                  # "<bus_id>/<module>/<request>", e.g. "kline-diag/td5/21 10"
    name: "str | None"           # the pack field name
    c: "str | None"
    raw: "int | float | None"
    state: "str | None"          # the field's enumeration label

    @property
    def path(self) -> "str | None":
        """The VSS path when the leaf is one (``Vehicle.…``)."""
        return self.leaf if self.leaf.startswith("Vehicle.") else None

    @property
    def pack_leaf(self) -> "Optional[tuple[str, str, str]]":
        """``(pack, module, field)`` for a pack leaf, else None."""
        if self.path is not None:
            return None
        parts = self.leaf.split(".")
        return (parts[0], parts[1], ".".join(parts[2:])) if len(parts) >= 3 else None

    @property
    def module(self) -> "str | None":
        """The module: the source tag's middle segment (spec §6.2)."""
        parts = self.source.split("/")
        return parts[1] if len(parts) >= 3 and parts[1] else None

    @property
    def pack_decoded(self) -> bool:
        return bool(self.name) and self.module is not None


def parse_vss(leaf: str, payload: bytes) -> "Optional[VssValue]":
    """A VSS value payload, or None when it is not a JSON object."""
    obj = _json_obj(payload)
    if obj is None:
        return None
    v = obj.get("value")
    value = float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None
    ts = obj.get("ts") if isinstance(obj.get("ts"), str) else None
    raw = obj.get("raw")
    raw = raw if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None
    unit = obj.get("unit") if isinstance(obj.get("unit"), str) else ""
    name = obj.get("name") if isinstance(obj.get("name"), str) and obj.get("name") else None
    state = obj.get("state") if isinstance(obj.get("state"), str) else None
    c = obj.get("c") if isinstance(obj.get("c"), str) else None
    source = obj.get("source") if isinstance(obj.get("source"), str) else ""
    return VssValue(leaf, value, unit, ts, _int(obj.get("t_us")), _int(obj.get("boot")),
                    source, name, c, raw, state)


__all__ = ["ACT_CATEGORIES", "ALARM_STATE", "EVENT", "EVENT_SEVERITIES", "FAULTS",
           "FAULT_STATUSES", "FEED_STATES", "MANIFEST", "SYSTEM_CATEGORY", "USER_CATEGORIES",
           "feed_states", "parse_shutdown", "role_grantable",
           "POWER_STATES", "PREFIX", "ROLE", "STATUS_VALUES", "TAP", "Topic", "VssValue",
           "check_vid", "parse_claim", "parse_event", "parse_faults", "parse_faults_rest",
           "parse_manifest", "parse_power", "parse_role_rest", "parse_status",
           "parse_tap_rest", "parse_topic", "parse_vss", "subscriptions", "tap_subscriptions",
           "vin_shaped"]
