# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The device table: node messages in, snapshot pieces out (NodeSource spec §6, §10).

Pure and clock-injected: :meth:`DeviceTable.ingest` takes the Brain's monotonic and wall
time of receipt, :meth:`DeviceTable.view` the Brain's time now. The MQTT reader thread
ingests, the poll thread views; a lock keeps them apart and ``view`` never blocks on I/O.

Honesty rules carried here:

- **Confidence is never raised.** The node's ``c`` and the Brain's installed pack store are
  compared and the lower wins; a mismatch is reported once.
- **Staleness per signal (§6.4).** Age is measured on the node's own clock (``t_us``)
  against the device's latest *live* message, so no clock sync is needed. A retained value
  delivered at subscribe time is the last known value: stale, aged by its ``ts`` when the
  node had SNTP, "age unknown" otherwise, until a live message for it arrives. A value is
  stale past ``max(3 × its observed interval, 2 s)`` (an EMA of its own arrivals).
- **Reboots.** A changed ``boot`` id (exact) or, for nodes without one, ``t_us`` or
  ``power.since_us`` going backwards marks a reboot: older values keep their reading but
  lose their node-clock age and are marked ``before_restart``.
- Nothing is zeroed or invented: a non-numeric value is dropped (and reported once).

Keys are ``(device, leaf, source)``: two modules of one node publishing the same VSS path
(the Discovery 2 battery voltage from the Td5 and from SLABS) share one retained topic,
and keeping the source in the key stops one module's live value replacing the other's.

**The cluster (P3).** Each device's retained capability ``manifest`` and role claims
(``role/<role>[/<scope>]``, ADR-0037 §3) are kept beside its ``status`` and ``power``;
:meth:`DeviceTable.cluster` builds the ``GET /cluster`` view (:mod:`.cluster`). A handover
is a change of holder (by the cluster rules, so void claims never hold) caused by a live
``status``, ``power``, ``manifest`` or claim message; the retained copies a subscribe
delivers never record one, so a reconnect never invents one.
"""
from __future__ import annotations

import datetime as _dt
import threading
from collections import OrderedDict, deque
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import cluster as _cluster
from .messages import (EVENT, FAULTS, MANIFEST, POWER, ROLE, STATUS, VSS, VssValue, feed_states,
                       parse_claim, parse_event, parse_faults, parse_faults_rest, parse_manifest,
                       parse_power, parse_role_rest, parse_status, parse_topic, parse_vss)
from .select import select

STALE_FLOOR_S = 2.0
STALE_FACTOR = 3.0
# Until a field has two live arrivals its interval is unknown; assume this pace (the node's
# slowest module rotation is several seconds per field).
DEFAULT_INTERVAL_S = 5.0
EMA_ALPHA = 0.3
PROVEN, CANDIDATE = "proven", "candidate"
FAULTS_NOTE = "not read by the node yet"
# Events (module-bus spec §6.1): the feed keeps the latest EVENTS_KEEP, de-duplicated by
# ``id`` over the last EVENT_IDS_KEEP ids (a QoS 1 redelivery or a bridge echo).
EVENTS_KEEP = 200
EVENT_IDS_KEEP = 2000
_KINDS = (STATUS, POWER, VSS, MANIFEST, ROLE, FAULTS, EVENT)
# The kinds a device publishes retained (spec §3): what Remove device purges.
RETAINED_KINDS = (STATUS, POWER, VSS, MANIFEST, ROLE, FAULTS)

# (module, field name) → (confidence, limits) from the Brain's installed pack store.
FieldLookup = Callable[[str, str], "Optional[tuple[str, Optional[tuple[float, float]]]]"]


def range_status(value: "float | None", limits) -> "str | None":
    """The pack sources' range rule: ok / low / high, or suspect when outside the range by
    more than its whole span; None without limits."""
    if value is None or not limits:
        return None
    lo, hi = limits
    span = (hi - lo) or 1.0
    if value < lo - span or value > hi + span:
        return "suspect"
    if value < lo:
        return "low"
    if value > hi:
        return "high"
    return "ok"


def lower_confidence(*levels: "str | None") -> str:
    """``proven`` only when every known level is ``proven``; anything else is a candidate."""
    known = [lv for lv in levels if lv is not None]
    if not known or any(lv != PROVEN for lv in known):
        return CANDIDATE
    return PROVEN


def parse_utc(ts: "str | None") -> "float | None":
    if not ts:
        return None
    try:
        return _dt.datetime.strptime(ts.replace("Z", "+0000"),
                                     "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
    except ValueError:
        try:
            return _dt.datetime.strptime(ts.replace("Z", "+0000"),
                                         "%Y-%m-%dT%H:%M:%S%z").timestamp()
        except ValueError:
            return None


def utc(epoch: float) -> str:
    d = _dt.datetime.fromtimestamp(epoch, tz=_dt.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S.") + f"{d.microsecond // 1000:03d}Z"


@dataclass
class Reading:
    device: str
    val: VssValue
    rx: float                    # Brain monotonic receive time
    retained: bool               # still only the stored value from subscribe time
    epoch: int                   # the device's boot epoch when received
    interval: "float | None" = None
    last_live_rx: "float | None" = None
    last_live_t_us: "int | None" = None


@dataclass
class Device:
    id: str
    status: "str | None" = None
    power: "dict | None" = None
    boot: "int | None" = None
    epoch: int = 0
    anchor: "tuple[int, float] | None" = None   # (t_us, Brain rx) of the latest live message
    max_t_us: "int | None" = None
    since_us: "int | None" = None
    last_live_wall: "float | None" = None        # Brain wall time of the latest live message
    last_any_rx: "float | None" = None
    readings: "dict[tuple[str, str], Reading]" = field(default_factory=dict)
    manifest: "dict | None" = None
    manifest_wall: "float | None" = None          # Brain wall time the manifest arrived
    claims: "dict[tuple[str, str | None], dict]" = field(default_factory=dict)
    # (pack, module) → the latest whole fault list (spec §6.2) with ``rx``, ``retained``
    # and ``epoch``; absent = not read.
    faults: "dict[tuple[str, str], dict]" = field(default_factory=dict)
    # Every topic of a retained kind seen from this device (Remove device purges them).
    topics: "set[str]" = field(default_factory=set)


class DeviceTable:
    def __init__(self, vid: str, *, pack_id: "str | None" = None,
                 lookup: "FieldLookup | None" = None,
                 canonical: "Callable[[str], str | None] | None" = None,
                 is_known: "Callable[[str], bool] | None" = None,
                 log: "Callable[[str], None] | None" = None,
                 primary: "Callable[[str], Optional[tuple[str, str]]] | None" = None,
                 allowed: "Callable[[str], Optional[list]] | None" = None) -> None:
        self.vid = vid
        # VSS path → (module, field) the pack marks primary for it (module-bus spec §6);
        # None for a path with no marker (the generic selection rule applies).
        self._primary = primary or (lambda path: None)
        # VSS path → its allowed values (a labelled enum such as the alarm state), from
        # metrics.json; the label for a reading that carries only the index.
        self._allowed = allowed or (lambda path: None)
        self.pack_id = pack_id
        self._lookup = lookup or (lambda module, name: None)
        self._canonical = canonical or (lambda m: m)
        self._is_known = is_known or (lambda path: True)
        self._log = log or (lambda msg: None)
        self._lock = threading.Lock()
        self._devices: "dict[str, Device]" = {}
        self._once: "set[str]" = set()
        # (role, scope) → the last holder change seen live: {from, to, term, at_utc, reason}
        self._handovers: "dict[tuple[str, str | None], dict]" = {}
        self.ignored = 0  # messages on topics the table does not read (tap …)
        self._events: "deque[dict]" = deque(maxlen=EVENTS_KEEP)
        self._event_ids: "OrderedDict[str, None]" = OrderedDict()
        self._event_seq = 0
        self._event_cond = threading.Condition(self._lock)
        self.duplicate_events = 0
        # Devices the owner removed (Remove device): their messages are ignored from now on.
        self._removed: "set[str]" = set()

    # ---- reporting ---------------------------------------------------------------- #
    def _note(self, key: str, msg: str) -> None:
        if key not in self._once:
            self._once.add(key)
            self._log(msg)

    def devices(self) -> "list[str]":
        with self._lock:
            return sorted(self._devices)

    def cluster(self) -> dict:
        """The cluster view (spec §11): ``{devices, roles, alerts}``; see :mod:`.cluster`."""
        with self._lock:
            return _cluster_view(self)

    def device_info(self) -> "dict[str, dict]":
        """``{device: {fw, etag}}`` for every device with a manifest (session meta, §7)."""
        with self._lock:
            return {d.id: {"fw": d.manifest.get("fw"), "etag": d.manifest.get("etag")}
                    for d in sorted(self._devices.values(), key=lambda d: d.id)
                    if d.manifest is not None}

    def forget_liveness(self) -> None:
        """A (re)connect to the broker: drop every device's ``status``, ``power``,
        ``manifest`` and role claims (the broker re-sends the retained ones; a claim
        released meanwhile must not linger) and the node-clock anchors; readings stay, aged
        by their ``ts`` until live messages arrive."""
        with self._lock:
            for dev in self._devices.values():
                dev.status = dev.power = None
                dev.anchor = None
                dev.manifest = dev.manifest_wall = None
                dev.claims = {}
                dev.faults = {}  # retained: re-sent; one cleared meanwhile is "not read"

    # ---- ingest (MQTT reader thread) ------------------------------------------------ #
    def ingest(self, topic: str, payload: bytes, retain: bool, now: float,
               wall: float) -> bool:
        """One message. ``retain`` is the delivered retain flag (with Retain As Published
        off: a stored value sent at subscribe time). True when it was used."""
        t = parse_topic(topic)
        if t is None or t.vid != self.vid or not t.device:
            self.ignored += 1
            return False
        with self._lock:
            dev = self._devices.get(t.device)
            if t.kind not in _KINDS or t.device in self._removed:
                self.ignored += 1
                return False
            if dev is None:
                dev = self._devices[t.device] = Device(t.device)
            dev.last_any_rx = now
            if not retain:
                dev.last_live_wall = wall
            if t.kind in RETAINED_KINDS:
                dev.topics.add(topic)
            if t.kind == VSS:
                return self._ingest_vss(dev, t.rest, payload, retain, now)
            if t.kind == FAULTS:
                return self._ingest_faults(dev, t.rest, payload, retain, now, wall)
            if t.kind == EVENT:
                return self._ingest_event(dev, t.rest, payload, retain, wall)
            # Role holders can change with a status, power, manifest or claim message; a
            # live one that changes a holder is a handover (stored copies never are).
            before = None if retain else self._holders()
            used, why = self._ingest_state(dev, t, payload, retain, wall)
            if used and before is not None:
                self._track(before, why, wall)
            return used

    def _ingest_state(self, dev: Device, t, payload: bytes, retain: bool,
                      wall: float) -> "tuple[bool, str | None]":
        """A ``status``, ``power``, ``manifest`` or ``role`` message: ``(used, why)``,
        ``why`` naming what a handover it causes is due to."""
        if t.kind == STATUS:
            st = parse_status(payload)
            if st is None:
                self._note(f"status:{t.device}", f"{t.device}: unreadable status payload")
                return False, None
            dev.status = st
            return True, f"{dev.id} {st}"
        if t.kind == POWER:
            pw = parse_power(payload)
            if pw is None:
                self._note(f"power:{t.device}", f"{t.device}: unreadable power record")
                return False, None
            since_us = pw.get("since_us")
            if (isinstance(since_us, int) and dev.since_us is not None
                    and since_us < dev.since_us and not retain):
                self._reboot(dev, "power.since_us went backwards")
            if isinstance(since_us, int):
                dev.since_us = since_us
            dev.power = pw
            return True, f"{dev.id} {pw['state']}"
        if t.kind == MANIFEST:
            return self._ingest_manifest(dev, payload, wall), f"{dev.id} manifest changed"
        return self._ingest_claim(dev, t.rest, payload)

    def _holders(self) -> "dict[tuple[str, str | None], tuple[str, int] | None]":
        """Every role's holder now by the cluster rules (void claims never hold)."""
        return {(r["role"], r["scope"]): ((r["holder"], r["term"]) if r["holder"] else None)
                for r in _cluster_view(self)["roles"]}

    def _track(self, before: dict, why: "str | None", wall: float) -> None:
        after = self._holders()
        for key in sorted(set(before) | set(after), key=lambda k: (k[0], k[1] or "")):
            b, a = before.get(key), after.get(key)
            if (b and b[0]) != (a and a[0]):
                self._handovers[key] = {"from": b[0] if b else None, "to": a[0] if a else None,
                                        "term": a[1] if a else None, "at_utc": utc(wall),
                                        "reason": why}

    def _ingest_manifest(self, dev: Device, payload: bytes, wall: float) -> bool:
        if not payload:  # a cleared retained manifest (the device was removed)
            dev.manifest = dev.manifest_wall = None
            return True
        m = parse_manifest(payload)
        if m is None:
            self._note(f"manifest:{dev.id}", f"{dev.id}: unreadable manifest (not a JSON object)")
            return False
        if isinstance(m.get("id"), str) and m["id"] != dev.id:
            self._note(f"manifest-id:{dev.id}", f"{dev.id}: its manifest names device "
                                                f"{m['id']!r}; the topic's id is used")
        dev.manifest, dev.manifest_wall = m, wall
        return True

    def _ingest_claim(self, dev: Device, rest: str, payload: bytes) -> "tuple[bool, str | None]":
        rs = parse_role_rest(rest)
        if rs is None or rs[0] not in _cluster.ROLES:
            self._note(f"role:{dev.id}/{rest}", f"{dev.id}: unknown role topic role/{rest}, ignored")
            return False, None
        claim = parse_claim(payload)
        if claim is None:
            self._note(f"claim:{dev.id}/{rest}", f"{dev.id}: unreadable role claim role/{rest}")
            return False, None
        if claim:
            dev.claims[rs] = claim
            return True, claim.get("reason") or f"{dev.id} claimed"
        dev.claims.pop(rs, None)  # released (ADR-0037 §3: the retained claim is cleared)
        return True, f"{dev.id} released"

    def _ingest_faults(self, dev: Device, rest: str, payload: bytes, retain: bool,
                       now: float, wall: float) -> bool:
        """``faults/<pack>.<module>`` (spec §6.2): the whole current list replaces the last;
        an empty payload clears it (not read again)."""
        key = parse_faults_rest(rest)
        if key is None:
            self._note(f"faults-topic:{dev.id}/{rest}",
                       f"{dev.id}: faults/{rest} is not faults/<pack>.<module>, ignored")
            return False
        if self.pack_id and key[0] != self.pack_id:
            self._note(f"faults-pack:{key[0]}", f"{dev.id}: faults/{rest} names pack "
                                                 f"{key[0]!r}, the Brain runs {self.pack_id!r}")
            return False
        rec = parse_faults(payload)
        if rec is None:
            self._note(f"faults:{dev.id}/{rest}", f"{dev.id}: unreadable fault list faults/{rest}")
            return False
        if not rec:
            dev.faults.pop(key, None)
            return True
        stale_boot = (rec["boot"] is not None and dev.boot is not None
                      and rec["boot"] < dev.boot)
        dev.faults[key] = {**rec, "rx": now, "rx_wall": wall, "retained": retain,
                           "epoch": dev.epoch - 1 if stale_boot else dev.epoch}
        return True

    def _ingest_event(self, dev: Device, name: str, payload: bytes, retain: bool,
                      wall: float) -> bool:
        """``event/<name>`` (spec §6.1): de-duplicated by ``id``. Events are never retained;
        a retained copy (a misbehaving publisher) is still shown, flagged."""
        ev = parse_event(name, payload)
        if ev is None:
            self._note(f"event:{dev.id}/{name}", f"{dev.id}: unreadable event event/{name}")
            return False
        if ev["id"] in self._event_ids:
            self.duplicate_events += 1
            return True
        self._event_ids[ev["id"]] = None
        while len(self._event_ids) > EVENT_IDS_KEEP:
            self._event_ids.popitem(last=False)
        self._event_seq += 1
        ev = {"seq": self._event_seq, "device": dev.id, **ev,
              "received_utc": utc(wall), "retained": bool(retain)}
        self._events.append(ev)
        self._event_cond.notify_all()
        return True

    # ---- events, faults and removal (module-bus spec v1.3) ------------------------- #
    def events(self, after: int = 0, limit: int = EVENTS_KEEP) -> "list[dict]":
        """The events feed, oldest first: those with ``seq`` > ``after`` (at most
        ``limit``, the newest ones)."""
        with self._lock:
            out = [dict(e) for e in self._events if e["seq"] > after]
        return out[-limit:] if limit else []

    def last_event_seq(self) -> int:
        with self._lock:
            return self._event_seq

    def wait_events(self, after: int, timeout: float) -> bool:
        """Block up to ``timeout`` s until an event with ``seq`` > ``after`` exists."""
        with self._event_cond:
            return self._event_cond.wait_for(lambda: self._event_seq > after, timeout)

    def faults_for(self, module: "str | None", prefer: "str | None" = None) -> "dict | None":
        """The latest fault list for ``module`` (a canonical module id): the one from
        ``prefer`` (the device serving the module) when it has one, else the most recently
        received. None when no device has published one (not read)."""
        if module is None:
            return None
        with self._lock:
            found = []
            for dev in self._devices.values():
                for (pack, mod), rec in dev.faults.items():
                    if self._canonical(mod) == module:
                        found.append((dev, pack, mod, rec))
            if not found:
                return None
            chosen = next((f for f in found if f[0].id == prefer), None) or \
                max(found, key=lambda f: (f[3]["rx"], f[0].id))
            dev, pack, mod, rec = chosen
            return {"device": dev.id, "topic_module": f"{pack}.{mod}", "status": rec["status"],
                   "faults": [dict(f) for f in rec["faults"]], "note": rec["note"],
                   "read_utc": rec["ts"], "source": rec["source"],
                   "last_known": bool(rec["retained"]),
                   "before_restart": rec["epoch"] != dev.epoch}

    def remove_device(self, device: str) -> "list[str]":
        """Owner's Remove device (module-bus spec §7.2): forget ``device`` and ignore its
        messages from now on; returns the topics of retained kinds seen from it (sorted),
        for the broker-host purge."""
        with self._lock:
            dev = self._devices.pop(device, None)
            self._removed.add(device)
            return sorted(dev.topics) if dev is not None else []

    def readmit_device(self, device: str) -> None:
        """Undo :meth:`remove_device`'s filter (a re-paired device)."""
        with self._lock:
            self._removed.discard(device)

    def removed_devices(self) -> "list[str]":
        with self._lock:
            return sorted(self._removed)

    def device_topics(self, device: str) -> "list[str]":
        with self._lock:
            dev = self._devices.get(device)
            return sorted(dev.topics) if dev is not None else []

    def _reboot(self, dev: Device, why: str) -> None:
        dev.epoch += 1
        dev.anchor = None
        dev.max_t_us = None
        self._log(f"{dev.id}: node restart detected ({why}); older values are marked "
                  "'before restart'")

    def _ingest_vss(self, dev: Device, leaf: str, payload: bytes, retain: bool,
                    now: float) -> bool:
        if not leaf:
            return False
        val = parse_vss(leaf, payload)
        if val is None:
            self._note(f"json:{dev.id}/{leaf}", f"{dev.id}: {leaf}: not a JSON object, dropped")
            return False
        if val.value is None:
            self._note(f"nan:{dev.id}/{leaf}", f"{dev.id}: {leaf}: non-numeric value dropped")
            return False
        # Reboot detection: the boot id (an NVS counter that only grows) is exact, so a
        # higher id is a newer boot whatever order retained copies arrive in; t_us going
        # backwards in live messages is the fallback for nodes without it.
        if val.boot is not None:
            if dev.boot is not None and val.boot > dev.boot:
                self._reboot(dev, f"boot id {dev.boot} → {val.boot}")
            if dev.boot is None or val.boot > dev.boot:
                dev.boot = val.boot
        elif (not retain and val.t_us is not None and dev.max_t_us is not None
              and val.t_us < dev.max_t_us):
            self._reboot(dev, "t_us went backwards")
        if val.path is not None and not self._is_known(val.path):
            self._note(f"metric:{val.path}", f"unknown VSS path {val.path} (kept, flagged "
                                              "m_unknown)")
        pl = val.pack_leaf
        if pl is not None and self.pack_id and pl[0] != self.pack_id:
            self._note(f"pack:{pl[0]}", f"{dev.id}: pack leaf {leaf} names pack {pl[0]!r}, "
                                        f"the Brain runs {self.pack_id!r}")
        stale_boot = val.boot is not None and dev.boot is not None and val.boot < dev.boot
        epoch = dev.epoch - 1 if stale_boot else dev.epoch
        key = (leaf, val.source)
        old = dev.readings.get(key)
        r = Reading(dev.id, val, now, retain, epoch)
        if old is not None:
            r.interval, r.last_live_rx, r.last_live_t_us = (old.interval, old.last_live_rx,
                                                            old.last_live_t_us)
            if retain and not old.retained:
                return True  # a late stored copy never replaces a live value
        if not retain and not stale_boot:
            if r.last_live_rx is not None:
                same_clock = (val.t_us is not None and r.last_live_t_us is not None
                              and old is not None and old.epoch == dev.epoch
                              and val.t_us > r.last_live_t_us)
                dt = ((val.t_us - r.last_live_t_us) / 1e6 if same_clock
                      else now - r.last_live_rx)
                if dt > 0:
                    r.interval = dt if r.interval is None else (
                        EMA_ALPHA * dt + (1 - EMA_ALPHA) * r.interval)
            r.last_live_rx, r.last_live_t_us = now, val.t_us
            if val.t_us is not None:
                if dev.anchor is None or val.t_us >= dev.anchor[0]:
                    dev.anchor = (val.t_us, now)
                dev.max_t_us = max(dev.max_t_us or 0, val.t_us)
        dev.readings[key] = r
        return True

    # ---- view (poll thread) --------------------------------------------------------- #
    def _age(self, dev: Device, r: Reading, now: float, wall: float) -> "float | None":
        v = r.val
        if (r.epoch == dev.epoch and dev.anchor is not None and v.t_us is not None
                and not (r.retained and v.t_us > dev.anchor[0])):
            node_now = dev.anchor[0] + (now - dev.anchor[1]) * 1e6
            return max(0.0, (node_now - v.t_us) / 1e6)
        t = parse_utc(v.ts)
        if t is not None:
            return max(0.0, wall - t)
        if not r.retained:
            return max(0.0, now - r.rx)  # a lower bound: received live that long ago
        return None

    def _signal(self, dev: Device, r: Reading, now: float, wall: float) -> dict:
        v = r.val
        module = self._canonical(v.module) if v.module else None
        info = self._lookup(module, v.name) if (module and v.name) else None
        store_c, limits = (info if info else (None, None))
        node_c = v.c if v.c in (PROVEN, CANDIDATE) else CANDIDATE
        c = lower_confidence(node_c, store_c)
        if store_c is not None and store_c != node_c:
            self._note(f"conf:{module}.{v.name}",
                       f"{module}.{v.name}: the node says {node_c}, the Brain's pack store "
                       f"says {store_c}; showing {c} (node and Brain on different pack versions?)")
        age = self._age(dev, r, now, wall)
        threshold = max(STALE_FACTOR * (r.interval or DEFAULT_INTERVAL_S), STALE_FLOOR_S)
        stale = r.retained or age is None or age > threshold or r.epoch != dev.epoch
        sig = {"v": v.value, "u": v.unit, "s": range_status(v.value, limits), "c": c,
               "ts_utc": v.ts, "age_s": None if age is None else round(age, 3),
               "stale": stale, "src": f"{dev.id}/{v.source}" if v.source else dev.id}
        label = v.state if v.state is not None else _allowed_label(
            self._allowed(v.path) if v.path else None, v.value)
        if label is not None:
            sig["label"] = label
        if v.raw is not None:
            sig["raw"] = v.raw
        if v.path is not None:
            sig["m"] = v.path
            if not self._is_known(v.path):
                sig["m_unknown"] = True
        if r.epoch != dev.epoch:
            sig["before_restart"] = True
        return sig

    def view(self, module: "str | None", now: float, wall: float) -> dict:
        """``{signals, vss, device, devices}`` for the active module: the pack fields the
        node reads for it (by the source tag's module), every ``Vehicle.*`` path with its
        sources and selection, and the device that serves the module."""
        with self._lock:
            signals: "dict[str, dict]" = {}
            best_rx: "dict[str, float]" = {}
            paths: "dict[str, list]" = {}
            serving: "dict[str, float]" = {}
            for dev in self._devices.values():
                for r in dev.readings.values():
                    v = r.val
                    sig = self._signal(dev, r, now, wall)
                    rmod = self._canonical(v.module) if v.module else None
                    if v.name and module is not None and rmod == module:
                        serving[dev.id] = max(serving.get(dev.id, -1.0), r.rx)
                        cur = signals.get(v.name)
                        if cur is None or (_rank(sig, dev.id) < _rank(cur, best_rx[v.name])):
                            signals[v.name] = sig
                            best_rx[v.name] = dev.id
                    if v.path is not None:
                        prim = self._primary(v.path)
                        paths.setdefault(v.path, []).append(
                            {"device": dev.id, "src": sig["src"], "stale": sig["stale"],
                             "age_s": sig["age_s"], "pack_decoded": v.pack_decoded,
                             "primary": bool(prim and v.pack_decoded
                                             and (rmod, v.name) == tuple(prim)),
                             "sig": sig})
            vss = {}
            for path, cands in sorted(paths.items()):
                chosen = select(cands)
                s = chosen["sig"]
                vss[path] = {
                    "sel": chosen["src"], "value": s["v"], "unit": s["u"],
                    "ts_utc": s["ts_utc"], "age_s": s["age_s"], "stale": s["stale"],
                    "c": s["c"],
                    "sources": {c["src"]: {**{k: c["sig"][k] for k in
                                              ("v", "u", "ts_utc", "age_s", "stale", "c")},
                                           **({"primary": True} if c["primary"] else {})}
                                for c in cands},
                }
            if serving:
                dev_id = max(sorted(serving), key=lambda d: serving[d])
            else:
                # No device reads this module: the node that would, by its manifest (a
                # Diagnostics node, or a device with no manifest yet, like the v0 node),
                # before a guardian, an add-on or the brain (P3; P1 took the lowest id).
                with_status = sorted(
                    (_SERVE_RANK.get(_cluster.device_class(dv.manifest), 3), d)
                    for d, dv in self._devices.items()
                    if dv.status is not None or dv.power is not None)
                dev_id = with_status[0][1] if with_status else None
            dev = self._devices.get(dev_id) if dev_id else None
            device = None
            if dev is not None:
                feed = feed_states({d.id: d.power for d in self._devices.values()}).get(dev.id)
                device = {"device": dev.id, "status": dev.status, "feed": feed,
                          "power": dict(dev.power) if dev.power else None,
                          "boot": dev.boot,
                          "last_seen_utc": utc(dev.last_live_wall) if dev.last_live_wall else None,
                          "fw": (dev.manifest or {}).get("fw"),
                          "etag": (dev.manifest or {}).get("etag")}
            return {"signals": signals, "vss": vss, "device": device,
                    "devices": sorted(self._devices)}


def _allowed_label(allowed, value: "float | None") -> "str | None":
    """A labelled enum's label from its index (module-bus spec §6: ``value`` is the index in
    the path's ``allowed`` list, ``state`` the label) when the node sent no ``state``."""
    if value is None or value != int(value):
        return None
    if isinstance(allowed, list) and 0 <= int(value) < len(allowed):
        return str(allowed[int(value)])
    return None


_SERVE_RANK = {"node": 0, None: 1, "guardian": 2, "module": 3, "brain": 4}


def _cluster_view(table: "DeviceTable") -> dict:
    """``{devices, roles, alerts}`` from the table (its lock held by the caller)."""
    buses: "set[str]" = set()
    recs = []
    for dev in table._devices.values():
        for r in dev.readings.values():
            bus = r.val.source.split("/", 1)[0] if r.val.source else ""
            if bus and "/" in r.val.source:
                buses.add(bus)
        recs.append({"id": dev.id, "status": dev.status,
                     "power": dict(dev.power) if dev.power else None,
                     "last_seen_utc": utc(dev.last_live_wall) if dev.last_live_wall else None,
                     "manifest": dev.manifest,
                     "manifest_utc": utc(dev.manifest_wall) if dev.manifest_wall else None,
                     "claims": {k: dict(v) for k, v in dev.claims.items()}})
    view = _cluster.build(recs, handovers={k: dict(v) for k, v in table._handovers.items()},
                          buses=sorted(buses))
    # The switched supply each device is on, as its feed owner reports it (module-bus spec
    # v1.3 §5); null when no device reports one.
    feeds = feed_states({d.id: d.power for d in table._devices.values()})
    for row in view.get("devices", []):
        row["feed"] = feeds.get(row.get("id"))
    return view


def _rank(sig: dict, device: str):
    age = sig.get("age_s")
    return (bool(sig.get("stale")), age is None, age or 0.0, device)


__all__ = ["DEFAULT_INTERVAL_S", "EVENTS_KEEP", "FAULTS_NOTE", "RETAINED_KINDS", "Device",
           "DeviceTable", "Reading",
           "STALE_FLOOR_S", "lower_confidence", "parse_utc", "range_status", "utc"]
