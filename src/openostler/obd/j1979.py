# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""The J1979 service layer (spec §4–§7): discovery, the reads and ``clear_dtcs``.

It talks to any :class:`~openostler.obd.link.ObdRequestLink` (K-line or, later, CAN),
collects every responder keyed by ECU address, and decodes through the pure decoders in
:mod:`openostler.obd.decode`. PID formulas come from a pack's store (:class:`PidTable`).
Mode 08 is never sent; Mode 04 is sent only by :meth:`J1979.clear_dtcs` with a
:class:`~openostler.obd.clear.ClearGrant`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Tuple

from . import vin as _vin
from .clear import (
    NRC22_MESSAGE,
    PERMANENT_NOTE,
    ClearGate,
    ClearGrant,
    ClearRefused,
)
from .decode import (
    BITMAP_BLOCKS,
    COUNT_INFOTYPE,
    DtcRead,
    MonitorTest,
    PidError,
    PidValue,
    Readiness,
    bitmap_chains,
    bitmap_pids,
    calid_strings,
    cvn_strings,
    decode_dtcs,
    decode_freeze_trigger,
    decode_mode06_can,
    decode_readiness,
    ecu_name,
    info_count,
    info_payload,
    vin_text,
    walk_pids,
)
from .diagnostics import ENGINE_ECUS, Diagnostics, derive
from .link import (
    CAN_FLAVORS,
    NRC_CONDITIONS_NOT_CORRECT,
    EcuStatus,
    ObdError,
    ObdRequestLink,
    PacedLink,
    Pacer,
    classify,
    guard_payload,
)
from .pids import PidTable

BITMAP_PIDS = frozenset(BITMAP_BLOCKS)
DTC_MODES = {"stored": 0x03, "pending": 0x07, "permanent": 0x0A}


# ------------------------------------------------------------------ results -- #

@dataclass(frozen=True)
class EcuSupport:
    modes: "Dict[int, frozenset]" = field(default_factory=dict)
    partial: "Tuple[int, ...]" = ()
    calid: "Tuple[str, ...]" = ()
    cvn: "Tuple[str, ...]" = ()
    name: "Dict[str, str] | None" = None
    obd_standard: "int | None" = None
    fuel_type: "int | None" = None

    def supports(self, mode: int, pid: "int | None" = None) -> bool:
        if mode not in self.modes:
            return False
        return pid is None or pid in self.modes[mode]


@dataclass(frozen=True)
class SupportReport:
    """The connect-time capability input (spec §7). It never holds the VIN."""

    flavor: str
    ecus: "Dict[str, EcuSupport]"

    def ecus_supporting(self, mode: int, pid: "int | None" = None) -> "Tuple[str, ...]":
        return tuple(e for e, s in sorted(self.ecus.items()) if s.supports(mode, pid))

    def to_dict(self) -> dict:
        out: dict = {"flavor": self.flavor, "ecus": {}}
        for ecu, s in sorted(self.ecus.items()):
            out["ecus"][ecu] = {
                "modes": {f"{m:02X}": [f"{p:02X}" for p in sorted(pids)]
                          for m, pids in sorted(s.modes.items())},
                "partial": [f"{m:02X}" for m in s.partial],
                "calid": list(s.calid), "cvn": list(s.cvn), "name": s.name,
                "obd_standard": s.obd_standard, "fuel_type": s.fuel_type,
            }
        return out


@dataclass(frozen=True)
class PidRead:
    values: "Tuple[PidValue, ...]" = ()
    errors: "Tuple[PidError, ...]" = ()

    def get(self, pid: int, signal: str, ecu: "str | None" = None) -> "PidValue | None":
        for v in self.values:
            if v.pid == pid and v.signal == signal and (ecu is None or v.ecu == ecu):
                return v
        return None


@dataclass(frozen=True)
class DtcResult:
    reads: "Tuple[DtcRead, ...]" = ()
    errors: "Tuple[PidError, ...]" = ()

    def codes(self, ecu: "str | None" = None) -> "List[str]":
        return [d.code for r in self.reads if ecu is None or r.ecu == ecu for d in r.dtcs]


@dataclass(frozen=True)
class FreezeFrame:
    ecu: str
    frame: int
    trigger: "object | None"            # a Dtc, or None: "no frame stored"
    values: "Tuple[PidValue, ...]" = ()
    errors: "Tuple[PidError, ...]" = ()

    @property
    def stored(self) -> bool:
        return self.trigger is not None


@dataclass(frozen=True)
class RawMonitorTest:
    """Mode 06 on K-line (TID layout) and Mode 05: raw until a car fixture (spec §4.5)."""

    ecu: str
    mode: int
    id: int
    data: bytes
    confidence: str = "candidate"


@dataclass(frozen=True)
class MonitorResult:
    tests: "Tuple[MonitorTest, ...]" = ()
    raw: "Tuple[RawMonitorTest, ...]" = ()
    errors: "Tuple[PidError, ...]" = ()


@dataclass(frozen=True)
class EcuIdentity:
    calid: "Tuple[str, ...]" = ()
    cvn: "Tuple[str, ...]" = ()
    name: "Dict[str, str] | None" = None


@dataclass(frozen=True)
class Identity:
    """CALID, CVN and ECU name per ECU. ``vin_delivered`` says whether ``on_vin`` got a
    VIN; the VIN itself is never part of this result."""

    ecus: "Dict[str, EcuIdentity]" = field(default_factory=dict)
    vin_delivered: bool = False
    errors: "Tuple[PidError, ...]" = ()


@dataclass(frozen=True)
class ClearOutcome:
    ecu: str
    status: str                 # cleared | negative | no_reply
    nrc: "int | None" = None
    message: str = ""


@dataclass(frozen=True)
class ClearResult:
    grant_id: str
    snapshot: str               # the logbook link of the "before clear" snapshot
    outcomes: "Tuple[ClearOutcome, ...]"
    before: dict
    after: dict
    notes: "Tuple[str, ...]" = ()

    @property
    def cleared(self) -> "Tuple[str, ...]":
        return tuple(o.ecu for o in self.outcomes if o.status == "cleared")


# ------------------------------------------------------------- the service -- #

def _err(ecu: str, mode: int, pid: "int | None", st: EcuStatus) -> PidError:
    return PidError(ecu, mode, pid, st.status, st.reason, st.nrc)


class J1979:
    """The J1979 service layer over one :class:`ObdRequestLink`."""

    def __init__(self, link: ObdRequestLink, table: "Optional[PidTable]" = None, *,
                 pacer: "Optional[Pacer]" = None,
                 clock: "Callable[[], float]" = time.time) -> None:
        self._link = link if isinstance(link, PacedLink) else PacedLink(link, pacer)
        self.flavor = link.flavor
        self.table = table if table is not None else PidTable({})
        self.report: "SupportReport | None" = None
        self.dropped = 0            # late or foreign frames dropped (spec §2.1, F5)
        self._clock = clock
        self._clearing = False

    def __repr__(self) -> str:
        return f"J1979(flavor={self.flavor!r}, ecus={self.ecus()!r})"

    @property
    def can(self) -> bool:
        return self.flavor in CAN_FLAVORS

    def ecus(self) -> "Tuple[str, ...]":
        return tuple(sorted(self.report.ecus)) if self.report else ()

    # ---- request ------------------------------------------------------- #
    def _request(self, payload: bytes, *, target: "str | None" = None,
                 expect_messages: "int | None" = None,
                 expected: "Iterable[str]" = ()) -> "Dict[str, EcuStatus]":
        payload = bytes(payload)
        guard_payload(payload, allow_clear=self._clearing)
        replies = self._link.request(payload, target=target, expect_messages=expect_messages,
                                     allow_clear=self._clearing)
        if target is not None:
            replies = {e: r for e, r in replies.items() if e == target}
            expected = (target,)
        results, dropped = classify(payload, replies, tuple(expected))
        self.dropped += dropped
        return results

    # ---- discovery (spec §4.1, §7) ------------------------------------- #
    def _chain(self, mode: int, target: "str | None" = None,
               sup: "Optional[Dict[str, Dict[int, set]]]" = None,
               partial: "Optional[Dict[str, set]]" = None) -> "Dict[str, set]":
        """Walk one mode's support-bitmap chain, per ECU. → ``{ecu: pids}``."""
        found: "Dict[str, set]" = {}
        pending: "set[str] | None" = None if target is None else {target}
        for block in BITMAP_BLOCKS:
            payload = bytes([mode, block, 0x00]) if mode == 0x02 else bytes([mode, block])
            res = self._request(payload, target=target,
                                expected=sorted(pending) if pending else ())
            nxt: "set[str]" = set()
            for ecu, st in res.items():
                if pending is not None and ecu not in pending:
                    continue
                data = st.messages[0][3:7] if st.ok and mode == 0x02 else \
                    st.messages[0][2:6] if st.ok else b""
                if len(data) < 4:
                    if pending is not None and partial is not None:
                        partial.setdefault(ecu, set()).add(mode)
                    continue
                pids = bitmap_pids(block, data)
                found.setdefault(ecu, set()).update(pids)
                if bitmap_chains(block, pids):
                    nxt.add(ecu)
            if not nxt:
                break
            pending = nxt
        if sup is not None:
            for ecu, pids in found.items():
                sup.setdefault(ecu, {})[mode] = pids
        return found

    def supported(self) -> SupportReport:
        """Run once per connection (spec §7): the 01 chain (which enumerates the ECUs), 02,
        06 and 09 chains, one ``0A`` probe, CALID/CVN/ECU names, PIDs ``1C`` and ``51``."""
        sup: "Dict[str, Dict[int, set]]" = {}
        partial: "Dict[str, set]" = {}
        self._chain(0x01, sup=sup, partial=partial)
        for mode in (0x02, 0x06, 0x09):
            self._chain(mode, sup=sup, partial=partial)
        for ecu, st in self._request(b"\x0A").items():
            if st.ok:
                sup.setdefault(ecu, {})[0x0A] = set()
        ecus = {e: EcuSupport({m: frozenset(p) for m, p in modes.items()},
                              tuple(sorted(partial.get(e, ()))))
                for e, modes in sup.items()}
        self.report = SupportReport(self.flavor, ecus)
        ident = self.read_identity()
        extra: "Dict[str, Dict[str, int]]" = {}
        for pid, key in ((0x1C, "obd_standard"), (0x51, "fuel_type")):
            for ecu in self.report.ecus_supporting(0x01, pid):
                st = self._request(bytes([0x01, pid]), target=ecu).get(ecu)
                if st is not None and st.ok and len(st.messages[0]) >= 3:
                    extra.setdefault(ecu, {})[key] = st.messages[0][2]
        for ecu, s in list(ecus.items()):
            i = ident.ecus.get(ecu, EcuIdentity())
            ecus[ecu] = EcuSupport(s.modes, s.partial, i.calid, i.cvn, i.name,
                                   extra.get(ecu, {}).get("obd_standard"),
                                   extra.get(ecu, {}).get("fuel_type"))
        self.report = SupportReport(self.flavor, ecus)
        return self.report

    # ---- Mode 01 values (spec §4.2) ------------------------------------- #
    def read_pids(self, pids: "Iterable[int]", *, ecu: "str | None" = None,
                  mode: int = 0x01) -> PidRead:
        """Read Mode 01 PIDs (up to 6 per request on CAN, 1 on K-line). An unsupported PID
        is absent from the result, never zero."""
        want = [p for p in dict.fromkeys(pids) if p not in BITMAP_PIDS]
        if self.report is not None:
            want = [p for p in want if (self.report.ecus.get(ecu).supports(mode, p)
                                        if ecu is not None and ecu in self.report.ecus
                                        else self.report.ecus_supporting(mode, p))]
        per = 6 if self.can else 1
        values: "List[PidValue]" = []
        errors: "List[PidError]" = []
        for i in range(0, len(want), per):
            chunk = want[i:i + per]
            expected: "Tuple[str, ...]" = ()
            if self.report is not None and ecu is None:
                expected = tuple(sorted({e for p in chunk
                                         for e in self.report.ecus_supporting(mode, p)}))
            res = self._request(bytes([mode, *chunk]), target=ecu, expected=expected)
            ts = self._clock()
            for e, st in sorted(res.items()):
                if not st.ok:
                    errors.append(_err(e, mode, chunk[0] if len(chunk) == 1 else None, st))
                    continue
                for msg in st.messages:
                    v, er = walk_pids(self.table, mode, msg, e, ts)
                    values += v
                    errors += er
        return PidRead(tuple(values), tuple(errors))

    def read_readiness(self, pid: int = 0x01) -> "Dict[str, Readiness]":
        """PID 01 (since clear) or 41 (this drive cycle) per ECU (spec §4.3)."""
        out: "Dict[str, Readiness]" = {}
        for ecu, st in sorted(self._request(bytes([0x01, pid])).items()):
            if st.ok and len(st.messages[0]) >= 6:
                out[ecu] = decode_readiness(st.messages[0][2:6], ecu, pid)
        return out

    def diagnostics(self) -> Diagnostics:
        """The ``Vehicle.Ostler.Diagnostics.*`` leaves (spec §6)."""
        ready = self.read_readiness(0x01)
        pending = self.read_dtcs("pending").reads
        dist: "Dict[str, float]" = {}
        if self.table.entry(0x01, 0x31) is not None:
            # PID 31 decodes through the pack's record; the importer folds km → m into
            # the scale (spec §6), and a record still in km is converted here.
            for v in self.read_pids([0x31]).values:
                dist.setdefault(v.ecu, v.value * (1000.0 if v.unit == "km" else 1.0))
        return derive(ready, pending, dist)

    # ---- DTCs (spec §4.4) ---------------------------------------------- #
    def read_dtcs(self, kind: str = "stored") -> DtcResult:
        mode = DTC_MODES[kind]
        expected = ()
        if self.report is not None:
            expected = self.report.ecus_supporting(0x0A) if mode == 0x0A else self.ecus()
        reads: "List[DtcRead]" = []
        errors: "List[PidError]" = []
        for ecu, st in sorted(self._request(bytes([mode]), expected=expected).items()):
            if st.ok:
                reads.append(decode_dtcs(self.flavor, mode, st.messages, ecu))
            else:
                errors.append(_err(ecu, mode, None, st))
        return DtcResult(tuple(reads), tuple(errors))

    # ---- freeze frame (spec §4.2) -------------------------------------- #
    def read_freeze_frame(self, ecu: str, frame: int = 0) -> FreezeFrame:
        """PID ``02`` first (the DTC that stored the frame; ``00 00`` = none stored), then
        the Mode 02 PIDs the ECU supports."""
        st = self._request(bytes([0x02, 0x02, frame]), target=ecu)[ecu]
        if not st.ok:
            return FreezeFrame(ecu, frame, None, (), (_err(ecu, 0x02, 0x02, st),))
        msg = st.messages[0]
        trigger = decode_freeze_trigger(msg[3:5], ecu)
        if trigger is None:
            return FreezeFrame(ecu, frame, None)
        if self.report is not None and ecu in self.report.ecus and \
                0x02 in self.report.ecus[ecu].modes:
            pids = set(self.report.ecus[ecu].modes[0x02])
        else:
            pids = self._chain(0x02, target=ecu).get(ecu, set())
        pids = sorted(p for p in pids if p not in BITMAP_PIDS and p != 0x02)
        per = 3 if self.can else 1
        values: "List[PidValue]" = []
        errors: "List[PidError]" = []
        for i in range(0, len(pids), per):
            chunk = pids[i:i + per]
            payload = bytes([0x02]) + b"".join(bytes([p, frame]) for p in chunk)
            st = self._request(payload, target=ecu)[ecu]
            if not st.ok:
                errors.append(_err(ecu, 0x02, chunk[0], st))
                continue
            ts = self._clock()
            for m in st.messages:
                v, er = walk_pids(self.table, 0x02, m, ecu, ts, frame)
                values += v
                errors += er
        return FreezeFrame(ecu, frame, trigger, tuple(values), tuple(errors))

    # ---- Mode 06 (spec §4.5) ------------------------------------------- #
    def read_monitor_tests(self, mids: "Iterable[int] | None" = None, *,
                           ecu: "str | None" = None) -> MonitorResult:
        if mids is None:
            mids = sorted({m for e in (self.report.ecus.values() if self.report else ())
                           for m in e.modes.get(0x06, ())} - BITMAP_PIDS)
        tests: "List[MonitorTest]" = []
        raw: "List[RawMonitorTest]" = []
        errors: "List[PidError]" = []
        for mid in mids:
            for e, st in sorted(self._request(bytes([0x06, mid]), target=ecu).items()):
                if not st.ok:
                    errors.append(_err(e, 0x06, mid, st))
                    continue
                for m in st.messages:
                    if self.can:
                        t, er = decode_mode06_can(m, e)
                        tests += t
                        errors += [PidError(e, 0x06, mid, "malformed", r) for r in er]
                    else:
                        raw.append(RawMonitorTest(e, 0x06, mid, bytes(m[2:])))
        return MonitorResult(tuple(tests), tuple(raw), tuple(errors))

    # ---- Mode 09 identity (spec §4.6–4.7) ------------------------------ #
    def _info(self, infotype: int, ecus: "Tuple[str, ...]") -> "Dict[str, bytes | EcuStatus]":
        """One InfoType from each ECU → reassembled payload (or the failed status)."""
        out: "Dict[str, bytes | EcuStatus]" = {}
        targets: "Tuple[Optional[str], ...]" = ecus if ecus else (None,)
        for target in targets:
            expect = None
            if not self.can and infotype in COUNT_INFOTYPE:
                cst = self._request(bytes([0x09, COUNT_INFOTYPE[infotype]]), target=target)
                counts = [info_count(s.messages[0]) for s in cst.values() if s.ok]
                expect = max((c for c in counts if c), default=None)
            res = self._request(bytes([0x09, infotype]), target=target,
                                expect_messages=expect)
            for e, st in res.items():
                out[e] = info_payload(self.flavor, st.messages) if st.ok else st
        return out

    def read_identity(self, on_vin: "Optional[Callable[[str], object]]" = None) -> Identity:
        """CALID, CVN and ECU name per ECU. The VIN is read only when ``on_vin`` is given;
        it is reassembled, passed to ``on_vin`` synchronously and dropped: it is never in
        the result, a ``repr``, an exception or a log line (spec §4.7, ADR-0036)."""
        rep = self.report
        found: "Dict[str, Dict[str, object]]" = {}
        errors: "List[PidError]" = []
        for infotype, key in ((0x04, "calid"), (0x06, "cvn"), (0x0A, "name")):
            ecus = rep.ecus_supporting(0x09, infotype) if rep else ()
            if rep is not None and not ecus:
                continue
            for e, got in sorted(self._info(infotype, ecus if self.can else ()).items()):
                if isinstance(got, EcuStatus):
                    errors.append(_err(e, 0x09, infotype, got))
                    continue
                val: object = (calid_strings(got) if infotype == 0x04 else
                               cvn_strings(got) if infotype == 0x06 else ecu_name(got))
                found.setdefault(e, {})[key] = val
        delivered = False
        if on_vin is not None:
            delivered = self._deliver_vin(on_vin, errors)
        ecus_out = {e: EcuIdentity(tuple(v.get("calid") or ()), tuple(v.get("cvn") or ()),
                                   v.get("name"))  # type: ignore[arg-type]
                    for e, v in found.items()}
        return Identity(ecus_out, delivered, tuple(errors))

    def _deliver_vin(self, on_vin: "Callable[[str], object]", errors: "List[PidError]") -> bool:
        got = self._info(0x02, ())
        order = sorted(got, key=lambda e: (e not in ENGINE_ECUS, e))
        try:
            for e in order:
                payload = got[e]
                if isinstance(payload, EcuStatus):
                    errors.append(_err(e, 0x09, 0x02, payload))
                    continue
                text = vin_text(payload)
                if text is None:
                    errors.append(PidError(e, 0x09, 0x02, "malformed", "vin_format"))
                    continue
                _vin.handle(text, on_vin)
                del text
                return True
            return False
        finally:
            got.clear()

    # ---- the "before clear" snapshot (spec §5.3) ------------------------ #
    def snapshot(self) -> dict:
        """03, 07, 0A, freeze frames and readiness, JSON-able, with no identity data."""
        snap: dict = {"flavor": self.flavor, "codes": {}, "warnings": {},
                      "freeze_frames": {}, "readiness": {}}
        stored_ecus: "set[str]" = set()
        for kind in ("stored", "pending", "permanent"):
            res = self.read_dtcs(kind)
            snap["codes"][kind] = {r.ecu: r.codes for r in res.reads}
            for r in res.reads:
                if r.warnings:
                    snap["warnings"].setdefault(kind, {})[r.ecu] = list(r.warnings)
                if kind == "stored" and r.dtcs:
                    stored_ecus.add(r.ecu)
        ff_ecus = stored_ecus
        if self.report is not None:
            ff_ecus = stored_ecus & set(self.report.ecus_supporting(0x02)) or stored_ecus
        for ecu in sorted(ff_ecus):
            ff = self.read_freeze_frame(ecu)
            snap["freeze_frames"][ecu] = {
                "frame": ff.frame,
                "trigger": ff.trigger.code if ff.trigger is not None else None,  # type: ignore[attr-defined]
                "values": [{"pid": f"{v.pid:02X}", "signal": v.signal, "value": v.value,
                            "unit": v.unit} for v in ff.values]}
        for ecu, r in self.read_readiness(0x01).items():
            snap["readiness"][ecu] = {
                "mil": r.mil, "dtc_count": r.dtc_count, "ignition": r.ignition,
                "monitors": {n: [m.supported, m.complete] for n, m in r.monitors.items()}}
        return snap

    # ---- Mode 04 (spec §5) --------------------------------------------- #
    def clear_dtcs(self, grant: "ClearGrant | None", *, gate: ClearGate,
                   snapshot_sink: "Callable[[dict], object]",
                   audit: "Optional[Callable[[dict], object]]" = None,
                   driving_state: "str | Callable[[], str] | None" = None,
                   names: "Optional[Mapping[str, str]]" = None) -> ClearResult:
        """Clear DTCs with a grant from ``gate``: redeem it (re-checking the driving state),
        write the automatic snapshot (no snapshot, no clear), send ``04`` (functional, or
        physical per ECU when a read-only ECU is on the link), record each ECU's ``44`` or
        NRC, re-read, and audit the attempt."""
        audit = audit if audit is not None else gate.audit
        names = dict(names or {})
        ctx = grant.context.to_dict() if isinstance(grant, ClearGrant) else {}

        def _audit(entry: dict) -> None:
            if audit is not None:
                audit({"type": "obd_clear", "t": self._clock(), **ctx, **entry})

        state = driving_state() if callable(driving_state) else driving_state
        try:
            gate.redeem(grant, driving_state=state)
        except ClearRefused as exc:
            _audit({"outcome": "refused", "stage": "redeem", "reason": exc.code,
                    "driving_state": state or ctx.get("driving_state")})
            raise
        assert grant is not None
        p = grant.plan
        base = {"ecus": list(p.ecus), "codes": {e: list(c) for e, c in p.codes.items()},
                "read_only": list(p.read_only), "driving_state": state or ctx["driving_state"]}
        try:
            before = self.snapshot()
            link = snapshot_sink(before)
            if not link:
                raise ObdError("the snapshot sink returned no link")
        except Exception as exc:  # any failure blocks the clear (spec §5.3)
            _audit({"outcome": "blocked", "stage": "snapshot", "reason": "snapshot_failed",
                    **base})
            raise ClearRefused("snapshot_failed", "The snapshot could not be saved to the "
                                                  "logbook, so nothing was cleared.") from exc
        self._clearing = True
        try:
            if p.read_only:
                res: "Dict[str, EcuStatus]" = {}
                for ecu in p.ecus:
                    res.update(self._request(b"\x04", target=ecu))
            else:
                res = self._request(b"\x04", expected=p.ecus)
        finally:
            self._clearing = False
        outcomes = []
        for ecu, st in sorted(res.items()):
            label = names.get(ecu) or ("The engine ECU" if ecu in ENGINE_ECUS else f"ECU {ecu}")
            if st.ok:
                outcomes.append(ClearOutcome(ecu, "cleared", message=f"{label}: cleared."))
            elif st.status == "negative":
                msg = (NRC22_MESSAGE.format(name=label) if st.nrc == NRC_CONDITIONS_NOT_CORRECT
                       else f"{label} refused the clear (NRC 0x{st.nrc:02X}).")
                outcomes.append(ClearOutcome(ecu, "negative", st.nrc, msg))
            else:
                outcomes.append(ClearOutcome(ecu, st.status, message=f"{label}: no reply."))
        after = {"codes": {k: {r.ecu: r.codes for r in self.read_dtcs(k).reads}
                           for k in ("stored", "pending", "permanent")},
                 "readiness": {e: {"mil": r.mil, "dtc_count": r.dtc_count,
                                   "incomplete": r.incomplete}
                               for e, r in self.read_readiness(0x01).items()}}
        notes = []
        if any(after["codes"]["permanent"].values()):
            notes.append(PERMANENT_NOTE)
        _audit({"outcome": "sent", **base, "snapshot": str(link),
                "results": {o.ecu: (o.status if o.nrc is None else f"nrc 0x{o.nrc:02X}")
                            for o in outcomes},
                "after": after["codes"]})
        return ClearResult(grant.id, str(link), tuple(outcomes), before, after, tuple(notes))


__all__ = ["J1979", "SupportReport", "EcuSupport", "PidRead", "DtcResult", "FreezeFrame",
           "MonitorResult", "RawMonitorTest", "Identity", "EcuIdentity", "ClearOutcome",
           "ClearResult", "DTC_MODES"]
