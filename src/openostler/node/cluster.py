# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The cluster view: devices, power, last seen and role holders (NodeSource spec §11, P3;
ADR-0037, ADR-0040; UI spec §3.7, §3.8; app-model spec §12.2, §13.2).

Built, never authoritative (ADR-0037 §1): every row comes from what the devices publish
(their retained ``manifest``, ``status``, ``power`` and ``role/<role>[/<scope>]`` claims).
Pure: :func:`build` takes plain device records and returns the ``GET /cluster`` body.

**Void claims** (ADR-0037 §3, Amendments 8 and 14; spec §11). A claim is shown but void,
with every reason in ``flags``, when its device is ``offline`` or ``asleep`` (status or
power state), when no manifest is known for it (``no_manifest``: it cannot be checked),
when the manifest does not list the role (``not_declared``; the owner's order is what the
install configuration publishes in the manifest, ADR-0037 §3; a gate needs ``transmit`` on
its bus), when the device is not a candidate for the role (``not_eligible``: the brain for
the parked broker or PLCA, an add-on module that fails Amendment 14's rules), or when the
payload names another role or scope than its topic (``mismatch``). Among the claims left
the higher ``term`` wins, then the higher ``priority`` (ADR-0037 §5); the loser is
``superseded``. **Two live gate claims on one bus are never resolved**: both are flagged
``conflict``, the bus has no holder, and an alert says both refuse to transmit.

**The serial-source rule** (owner answer 7): :func:`kline_gate_holders` lists the devices
that hold, or by their manifest are wired to, a K-line transmit gate; a serial source on
that vehicle refuses to start beside them.
"""
from __future__ import annotations

from typing import Iterable

GATE, PBROKER, TIME, PLCA, UPLINK = "gate", "pbroker", "time", "plca", "uplink"
# Role id → (scoped?, title). The ids are the mDNS TXT ``roles=`` keys (ADR-0037 §3.3).
ROLES = {
    GATE: (True, "Transmit gate"),
    PBROKER: (False, "Parked broker"),
    TIME: (False, "Time source"),
    PLCA: (True, "PLCA coordinator"),
    UPLINK: (False, "Uplink manager"),
}
VEHICLE_ROLES = (PBROKER, TIME, UPLINK)  # one per vehicle: always listed, "No holder" if none
# Candidate order by device class (ADR-0037 §2 and Amendment 13); a class not listed is
# never a candidate. Gate and time have no device order (wiring; best clock first).
ORDER = {
    PBROKER: ("node", "guardian", "module"),
    PLCA: ("node", "guardian"),
    UPLINK: ("brain", "node"),
}
PBROKER_PSRAM_KB = 2048    # ADR-0037 Amendment 14
PBROKER_MAX_CLIENTS = 5
ASLEEP_STATES = ("asleep", "off", "shutting_down")


def device_class(manifest: "dict | None") -> "str | None":
    """``brain``, ``node`` (the Diagnostics node), ``guardian`` or ``module`` (any add-on,
    sensor nodes included), from the manifest's ``kind`` and ``variant`` (ADR-0039 §1);
    None without a manifest."""
    if not isinstance(manifest, dict):
        return None
    kind, variant = manifest.get("kind"), manifest.get("variant")
    if kind == "brain":
        return "brain"
    if kind == "guardian" or variant == "guardian":
        return "guardian"
    if kind == "node" and variant in (None, "diag-port", "diagnostics"):
        return "node"
    return "module"


def _role_entries(manifest: dict, role: str) -> "list[dict]":
    return [r for r in manifest.get("roles") or []
            if isinstance(r, dict) and r.get("role") == role]


def _transmit_buses(manifest: "dict | None") -> "list[str]":
    if not isinstance(manifest, dict):
        return []
    return [t["bus_id"] for t in manifest.get("transmit") or []
            if isinstance(t, dict) and isinstance(t.get("bus_id"), str)]


def declares(manifest: dict, role: str, scope: "str | None") -> bool:
    """Does the manifest list this role (and scope)? A gate is declared by ``transmit``."""
    if role == GATE:
        return scope in _transmit_buses(manifest)
    for r in _role_entries(manifest, role):
        if not ROLES.get(role, (False,))[0] or r.get("scope") == scope:
            return True
    return False


def eligibility(manifest: dict, role: str, scope: "str | None") -> "list[str]":
    """Why a device may not hold the role (empty: it may), beyond declaring it."""
    cls = device_class(manifest)
    if role in ORDER and cls not in ORDER[role]:
        return [f"{cls} is never a {ROLES[role][1].lower()} candidate"]
    if role == PBROKER and cls == "module":
        why = []
        power = manifest.get("power") if isinstance(manifest.get("power"), dict) else {}
        if power.get("class") != "always":
            why.append("its power class is not always")
        psram = (manifest.get("memory") or {}).get("psram_kb")
        if not isinstance(psram, (int, float)) or psram < PBROKER_PSRAM_KB:
            why.append(f"less than {PBROKER_PSRAM_KB} kB PSRAM declared")
        entry = (_role_entries(manifest, PBROKER) or [{}])[0]
        mc = entry.get("max_clients")
        if not isinstance(mc, int) or isinstance(mc, bool) or not 1 <= mc <= PBROKER_MAX_CLIENTS:
            why.append(f"max_clients not declared as 1 to {PBROKER_MAX_CLIENTS}")
        return why
    return []


def _priority(manifest: "dict | None", role: str) -> float:
    """The owner's priority (higher first): the role entry's, else the device's."""
    if not isinstance(manifest, dict):
        return float("-inf")
    for r in _role_entries(manifest, role):
        p = r.get("priority")
        if isinstance(p, (int, float)) and not isinstance(p, bool):
            return float(p)
    p = manifest.get("priority")
    return float(p) if isinstance(p, (int, float)) and not isinstance(p, bool) else float("-inf")


def _asleep(dev: dict) -> bool:
    return dev.get("status") == "asleep" or (dev.get("power") or {}).get("state") in ASLEEP_STATES


def _claim_flags(dev: dict, role: str, scope: "str | None", claim: dict) -> "list[str]":
    flags = []
    if dev.get("status") == "offline":
        flags.append("offline")
    elif _asleep(dev):
        flags.append("asleep")
    scoped = ROLES[role][0]
    if (claim.get("role") not in (None, role)
            or (scoped and claim.get("scope") not in (None, scope))
            or (not scoped and scope is not None)):
        flags.append("mismatch")  # an unscoped role's payload scope (the vehicle) is not checked
    manifest = dev.get("manifest")
    if not isinstance(manifest, dict):
        flags.append("no_manifest")
    elif not declares(manifest, role, scope):
        flags.append("not_declared")
    elif eligibility(manifest, role, scope):
        flags.append("not_eligible")
    return flags


def _scopes(devices: "list[dict]", buses: "Iterable[str]") -> "list[tuple[str, str | None]]":
    keys: "set[tuple[str, str | None]]" = set()
    if devices:
        keys.update((r, None) for r in VEHICLE_ROLES)
    for bus in buses:
        keys.add((GATE, bus))
    for dev in devices:
        keys.update(k for k in (dev.get("claims") or {}) if k[0] in ROLES)
        m = dev.get("manifest")
        if isinstance(m, dict):
            keys.update((GATE, b) for b in _transmit_buses(m))
            for r in m.get("roles") or []:
                if isinstance(r, dict) and r.get("role") in ROLES and r["role"] != GATE:
                    scoped = ROLES[r["role"]][0]
                    if not scoped or isinstance(r.get("scope"), str):
                        keys.add((r["role"], r.get("scope") if scoped else None))
    order = list(ROLES)
    return sorted(keys, key=lambda k: (order.index(k[0]) if k[0] in order else len(order),
                                       k[0], k[1] or ""))


def _candidates(devices: "list[dict]", role: str, scope: "str | None") -> "list[dict]":
    rows = []
    for dev in devices:
        m = dev.get("manifest")
        if not isinstance(m, dict) or not declares(m, role, scope) or eligibility(m, role, scope):
            continue
        cls = device_class(m)
        rank = ORDER[role].index(cls) if role in ORDER else 0
        rows.append((rank, -_priority(m, role), dev["id"],
                     {"device": dev["id"], "class": cls, "status": dev.get("status"),
                      "power_state": (dev.get("power") or {}).get("state")}))
    return [r[-1] for r in sorted(rows, key=lambda r: r[:3])]


def build(devices: "list[dict]", *, handovers: "dict | None" = None,
          buses: "Iterable[str]" = ()) -> dict:
    """The ``devices``, ``roles`` and ``alerts`` of ``GET /cluster``.

    ``devices``: ``{id, status, power, last_seen_utc, manifest, manifest_utc, claims:
    {(role, scope): claim}}`` each. ``handovers``: ``{(role, scope): {from, to, term,
    at_utc, reason}}``, the last change of holder a live message caused (kept by
    :class:`~openostler.node.table.DeviceTable`). ``buses``: the bus ids the
    devices' readings came from (a gate row with no holder reads "No gate for this bus")."""
    devices = sorted(devices, key=lambda d: d["id"])
    handovers = handovers or {}
    alerts: "list[dict]" = []
    claim_rows: "dict[tuple[str, str | None], list[dict]]" = {}
    per_device: "dict[str, list[dict]]" = {d["id"]: [] for d in devices}
    for dev in devices:
        for (role, scope), claim in sorted((dev.get("claims") or {}).items(),
                                           key=lambda kv: (kv[0][0], kv[0][1] or "")):
            if role not in ROLES:
                continue
            row = {"role": role, "scope": scope, "term": claim.get("term", 0),
                   "priority": claim.get("priority"), "since": claim.get("since"),
                   "reason": claim.get("reason"), "flags": _claim_flags(dev, role, scope, claim)}
            row["void"] = bool(row["flags"])
            claim_rows.setdefault((role, scope), []).append({"device": dev["id"], "row": row})
            per_device[dev["id"]].append(row)
    roles = []
    for role, scope in _scopes(devices, buses):
        claims = claim_rows.get((role, scope), [])
        live = [c for c in claims if not c["row"]["void"]]
        holder = None
        conflict = False
        if role == GATE and len(live) > 1:
            conflict = True
            for c in live:
                c["row"]["flags"].append("conflict")
            alerts.append({"code": "gate_conflict", "role": role, "scope": scope,
                           "devices": [c["device"] for c in live],
                           "message": f"Two devices claim the transmit gate for {scope}: "
                                      "both refuse to transmit until the owner removes one "
                                      "(ADR-0037 §5)"})
        elif live:
            # Higher term, then higher priority (ADR-0037 §5), then the lowest device id.
            best = min(live, key=lambda c: (-c["row"]["term"],
                                            -(c["row"]["priority"] if c["row"]["priority"]
                                              is not None else float("-inf")),
                                            c["device"]))
            holder = best
            for c in live:
                if c is not best:
                    c["row"]["flags"].append("superseded")
        for c in claims:
            if c["row"]["void"]:
                alerts.append({"code": "void_claim", "role": role, "scope": scope,
                               "devices": [c["device"]], "flags": list(c["row"]["flags"]),
                               "message": f"{c['device']} claims {ROLES[role][1].lower()}"
                                          f"{' ' + scope if scope else ''} but the claim is "
                                          f"void ({', '.join(c['row']['flags'])})"})
        hrow = holder["row"] if holder else None
        roles.append({
            "role": role, "scope": scope, "title": ROLES[role][1],
            "holder": holder["device"] if holder else None,
            "term": hrow["term"] if hrow else None,
            "since": hrow["since"] if hrow else None,
            "reason": hrow["reason"] if hrow else None,
            "conflict": conflict,
            "no_holder": holder is None,
            "hands_over": role != GATE,
            "candidates": _candidates(devices, role, scope),
            "claims": [{"device": c["device"], **{k: c["row"][k] for k in
                                                 ("term", "priority", "since", "void", "flags")}}
                       for c in claims],
            "last_handover": handovers.get((role, scope)),
        })
    rows = []
    for dev in devices:
        m = dev.get("manifest") if isinstance(dev.get("manifest"), dict) else None
        power = dev.get("power")
        rows.append({
            "id": dev["id"],
            "kind": (m or {}).get("kind"), "variant": (m or {}).get("variant"),
            "class": device_class(m), "model": (m or {}).get("model"),
            "board": (m or {}).get("board"), "fw": (m or {}).get("fw"),
            "etag": (m or {}).get("etag"),
            "manifest_utc": dev.get("manifest_utc") if m else None,
            "links": (m or {}).get("links") or [],
            "status": dev.get("status"),
            "power": dict(power) if isinstance(power, dict) else None,
            "last_seen_utc": dev.get("last_seen_utc"),
            "since": (power or {}).get("since") if isinstance(power, dict) else None,
            "roles_declared": [r for r in (m or {}).get("roles") or [] if isinstance(r, dict)],
            "transmit": [t for t in (m or {}).get("transmit") or [] if isinstance(t, dict)],
            "memory": (m or {}).get("memory"),
            "items": [i for i in (m or {}).get("items") or [] if isinstance(i, dict)],
            "claims": per_device[dev["id"]],
        })
    return {"devices": rows, "roles": roles, "alerts": alerts}


def kline_gate_holders(cluster: dict) -> "list[dict]":
    """Devices that hold a K-line transmit gate (a claim, void or not: a claim says the
    device is wired to that bus) or whose manifest declares ``transmit`` on one (the gate
    is the wiring and never hands over, ADR-0037 §2): ``[{device, bus_id, by, status}]``
    with ``by`` ``claim`` or ``manifest``. A bus id is a K-line when it starts with
    ``kline`` (``kline-diag``)."""
    out: "dict[tuple[str, str], dict]" = {}
    for dev in cluster.get("devices") or []:
        for c in dev.get("claims") or []:
            if c.get("role") == GATE and str(c.get("scope") or "").startswith("kline"):
                out[(dev["id"], c["scope"])] = {"device": dev["id"], "bus_id": c["scope"],
                                                "by": "claim", "status": dev.get("status")}
        for t in dev.get("transmit") or []:
            bus = t.get("bus_id")
            if isinstance(bus, str) and bus.startswith("kline"):
                out.setdefault((dev["id"], bus), {"device": dev["id"], "bus_id": bus,
                                                  "by": "manifest", "status": dev.get("status")})
    return [out[k] for k in sorted(out)]


def serial_refusal(cluster: dict) -> "str | None":
    """The reason a serial (K-line cable) source must not start on this vehicle, or None
    (owner answer 7: one tester on a shared K-line; the node's gate is the only path)."""
    held = kline_gate_holders(cluster)
    if not held:
        return None
    who = ", ".join(f"{h['device']} ({h['bus_id']}, by its {h['by']}, status "
                    f"{h['status'] or 'unknown'})" for h in held)
    return ("a node on this vehicle holds the K-line transmit gate: " + who + ". A cable "
            "beside it would collide on the shared K-line and bypass its gate; read the car "
            "through the node (--source node), or remove the node first")


__all__ = ["ASLEEP_STATES", "GATE", "ORDER", "PBROKER", "PLCA", "ROLES", "TIME", "UPLINK",
           "VEHICLE_ROLES", "build", "declares", "device_class", "eligibility",
           "kline_gate_holders", "serial_refusal"]
