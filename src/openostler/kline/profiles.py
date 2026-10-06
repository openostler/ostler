# SPDX-FileCopyrightText: 2026 OpenOstler contributors
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""K-line protocol profiles as data (ADR-0022, spec 2026-10-06 K-line profiles §1).

A :class:`KLineProfile` holds everything that differs between K-line protocols: the line
format, the framing (ISO 9141-2 or KWP2000), header and length modes, the checksum, the
ISO 14230-2 / ISO 9141-2 timing (P1–P4, W1–W5), the idle before an init, keep-alive and
release, and the init method (``fast``, ``5baud`` or ``none``) as its own field.

The platform ships generic profiles only (:data:`BUILTIN`): ``iso9141_2``,
``kwp2000_slow`` and ``kwp2000_fast``. A vehicle pack overrides any field through
``ModuleSpec.kline`` (see :func:`resolve`); manufacturer framings are profiles a pack
declares and are never auto-probed. This module is pure and stdlib-only, and it never
imports ``pack.py``.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from functools import reduce
from types import MappingProxyType
from typing import Any, Literal, Mapping

Framing = Literal["iso9141", "kwp2000"]
InitMethod = Literal["fast", "5baud", "none"]


@dataclass(frozen=True)
class Timing:
    """Timing in seconds; the ISO 14230-2 normal set unless noted."""

    p1_max: float = 0.020           # ECU inter-byte gap; ends a reply (ISO 9141 burst split)
    p2_min: float = 0.025           # request end → reply start
    p2_max: float = 0.050
    p3_min: float = 0.055           # reply end → next request
    p3_max: float = 5.0
    p4: float = 0.0                 # tester inter-byte gap (KLine.write_gap; 0 = one sweep)
    w1_max: float = 0.300           # 5-baud address end → 0x55
    w2_max: float = 0.020           # 0x55 → KW1
    w3_max: float = 0.020           # KW1 → KW2
    w4: float = 0.030               # KW2 → ~KW2 (spec window 25–50 ms)
    w5: float = 0.300               # bus idle before any init
    reply_timeout: float = 1.0      # KLine timeout; covers an extended P2


@dataclass(frozen=True)
class KLineProfile:
    """One K-line protocol, as data. See the spec §1 for every field."""

    name: str
    framing: Framing
    init: InitMethod
    init_address: int = 0x33                    # 5-baud address, or fast-init target
    init_address_parity: Literal["none", "odd", "even"] = "none"   # 8N1 (spec §5)
    init_functional: bool = True                # fast init C1 vs 81 format byte
    target: int = 0x33
    source: int = 0xF1
    baud: int = 10400
    parity: Literal["N", "E", "O"] = "N"        # 8 data bits, 1 stop
    header: Literal["auto", "none", "physical", "functional", "iso9141"] = "auto"
    length: Literal["auto", "format", "separate", "none"] = "auto"
    iso9141_header: bytes = b"\x68\x6A\xF1"     # request header (iso9141 framing only)
    checksum: Literal["sum8", "xor", "twos_complement"] = "sum8"
    timing: Timing = field(default_factory=Timing)
    timing_set: Literal["normal", "extended"] = "normal"
    init_low: float = 0.025                     # fast-init TiniL
    init_high: float = 0.025                    # fast-init TiniH
    pre_init_idle: "float | None" = None        # None → timing.w5
    abandoned_idle: "float | None" = None       # None → timing.p3_max (spec §4.3)
    keepalive: "bytes | None" = b"\x3E\x01"     # None = no keep-alive
    keepalive_interval: float = 2.0             # must be < p3_max / 2
    release: "bytes | None" = b"\x82"           # None = stop and wait (ISO 9141)
    confirm_address: Literal["require", "report"] = "require"      # 5-baud ~address
    tolerant: bool = True                       # CONSTITUTION: keep for KKL cables
    evidence: str = ""                          # car result behind a non-default parity

    # ---- derived ------------------------------------------------------- #
    @property
    def protocol(self) -> str:
        """``iso9141_2`` or ``kwp2000`` (the snapshot ``link.protocol``)."""
        return "iso9141_2" if self.framing == "iso9141" else "kwp2000"

    @property
    def idle_before_init(self) -> float:
        """The idle before an init after a clean release (W5 unless overridden)."""
        return self.timing.w5 if self.pre_init_idle is None else self.pre_init_idle

    @property
    def idle_after_abandoned(self) -> float:
        """The idle before an init after an abandoned session (P3max unless overridden)."""
        return self.timing.p3_max if self.abandoned_idle is None else self.abandoned_idle

    @property
    def addressed(self) -> bool:
        """KWP2000 session frames carry target and source (header physical/functional)."""
        return self.header in ("physical", "functional")

    def to_dict(self) -> dict:
        """A JSON-able dict (bytes as spaced hex, the timing as a nested dict)."""
        out: dict = {}
        for f in dataclasses.fields(self):
            v = getattr(self, f.name)
            if isinstance(v, Timing):
                v = dataclasses.asdict(v)
            elif isinstance(v, (bytes, bytearray)):
                v = bytes(v).hex(" ").upper()
            out[f.name] = v
        return out


# ------------------------------------------------------------------ checksums -- #

def checksum_sum8(data: bytes) -> int:
    """Sum of all bytes, modulo 256 (ISO 9141-2 and ISO 14230-2)."""
    return sum(data) & 0xFF


def checksum_xor(data: bytes) -> int:
    """XOR of all bytes (for pack-declared manufacturer profiles)."""
    return reduce(lambda a, b: a ^ b, data, 0)


def checksum_twos_complement(data: bytes) -> int:
    """Two's complement of the byte sum, so that the sum including it is 0."""
    return (-sum(data)) & 0xFF


CHECKSUMS = MappingProxyType({
    "sum8": checksum_sum8,
    "xor": checksum_xor,
    "twos_complement": checksum_twos_complement,
})


def checksum(profile: KLineProfile, data: bytes) -> int:
    """The checksum of ``data`` as ``profile`` defines it."""
    return CHECKSUMS[profile.checksum](bytes(data))


# ------------------------------------------------------------------ validation -- #

_CHOICES: "dict[str, tuple]" = {
    "framing": ("iso9141", "kwp2000"),
    "init": ("fast", "5baud", "none"),
    "init_address_parity": ("none", "odd", "even"),
    "parity": ("N", "E", "O"),
    "header": ("auto", "none", "physical", "functional", "iso9141"),
    "length": ("auto", "format", "separate", "none"),
    "checksum": tuple(CHECKSUMS),
    "timing_set": ("normal", "extended"),
    "confirm_address": ("require", "report"),
}
_BYTE_FIELDS = ("init_address", "target", "source")
_INT_FIELDS = ("baud",)
_BOOL_FIELDS = ("init_functional", "tolerant")
_FLOAT_FIELDS = ("init_low", "init_high", "keepalive_interval")
_OPT_FLOAT_FIELDS = ("pre_init_idle", "abandoned_idle")
_BYTES_FIELDS = ("iso9141_header",)
_OPT_BYTES_FIELDS = ("keepalive", "release")
_STR_FIELDS = ("name", "evidence")
_TIMING_FIELDS = tuple(f.name for f in dataclasses.fields(Timing))
_PROFILE_FIELDS = tuple(f.name for f in dataclasses.fields(KLineProfile))


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _as_bytes(key: str, v: Any) -> bytes:
    """bytes, a list of byte ints, or a hex string (``"3E 01"``, the manifest form)."""
    if isinstance(v, (bytes, bytearray)):
        return bytes(v)
    if isinstance(v, str):
        try:
            return bytes.fromhex(v.replace(" ", ""))
        except ValueError:
            raise ValueError(f"kline.{key}: not a hex byte string: {v!r}") from None
    if isinstance(v, (list, tuple)) and all(isinstance(b, int) and not isinstance(b, bool)
                                            and 0 <= b <= 0xFF for b in v):
        return bytes(v)
    raise ValueError(f"kline.{key}: expected bytes or a hex string, got {type(v).__name__}")


def _coerce(key: str, v: Any) -> Any:
    """Type-check (and normalize) one override value; raises ValueError."""
    if key in _CHOICES:
        if v not in _CHOICES[key]:
            raise ValueError(f"kline.{key}: {v!r} is not one of {list(_CHOICES[key])}")
        return v
    if key in _BYTE_FIELDS:
        if not (isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 0xFF):
            raise ValueError(f"kline.{key}: expected a byte (0–255), got {v!r}")
        return v
    if key in _INT_FIELDS:
        if not (isinstance(v, int) and not isinstance(v, bool) and v > 0):
            raise ValueError(f"kline.{key}: expected a positive int, got {v!r}")
        return v
    if key in _BOOL_FIELDS:
        if not isinstance(v, bool):
            raise ValueError(f"kline.{key}: expected a bool, got {v!r}")
        return v
    if key in _FLOAT_FIELDS:
        if not _is_number(v) or v < 0:
            raise ValueError(f"kline.{key}: expected seconds >= 0, got {v!r}")
        return float(v)
    if key in _OPT_FLOAT_FIELDS:
        if v is None:
            return None
        if not _is_number(v) or v < 0:
            raise ValueError(f"kline.{key}: expected seconds >= 0 or null, got {v!r}")
        return float(v)
    if key in _BYTES_FIELDS:
        b = _as_bytes(key, v)
        if not b:
            raise ValueError(f"kline.{key}: must not be empty")
        return b
    if key in _OPT_BYTES_FIELDS:
        if v is None:
            return None
        b = _as_bytes(key, v)
        if not b:
            raise ValueError(f"kline.{key}: must not be empty (use null for none)")
        return b
    if key in _STR_FIELDS:
        if not isinstance(v, str):
            raise ValueError(f"kline.{key}: expected a string, got {v!r}")
        return v
    raise ValueError(f"kline: unknown key {key!r}")  # pragma: no cover — guarded by caller


def _timing(base: Timing, overrides: Any) -> Timing:
    if isinstance(overrides, Timing):
        return overrides
    if not isinstance(overrides, Mapping):
        raise ValueError(f"kline.timing: expected a mapping, got {type(overrides).__name__}")
    changes = {}
    for k, v in overrides.items():
        if k not in _TIMING_FIELDS:
            raise ValueError(f"kline.timing: unknown key {k!r}")
        if not _is_number(v) or v < 0:
            raise ValueError(f"kline.timing.{k}: expected seconds >= 0, got {v!r}")
        changes[k] = float(v)
    return dataclasses.replace(base, **changes)


def validate(p: KLineProfile) -> KLineProfile:
    """Check a whole profile's cross-field rules; returns it unchanged or raises ValueError."""
    if p.keepalive is not None and p.keepalive_interval >= p.timing.p3_max / 2:
        raise ValueError(f"profile {p.name}: keepalive_interval {p.keepalive_interval} s must "
                         f"be < p3_max / 2 ({p.timing.p3_max / 2} s)")
    if p.framing == "iso9141":
        if p.release is not None:
            raise ValueError(f"profile {p.name}: ISO 9141 has no release frame (release must "
                             "be null)")
        if p.header != "iso9141":
            raise ValueError(f"profile {p.name}: ISO 9141 framing needs header 'iso9141'")
    elif p.header == "iso9141":
        raise ValueError(f"profile {p.name}: header 'iso9141' needs iso9141 framing")
    if p.init_address_parity != "none" and not p.evidence.strip():
        raise ValueError(f"profile {p.name}: a 5-baud address parity other than 'none' needs "
                         "'evidence' (a car result; ADR-0022)")
    return p


def resolve(base: "KLineProfile | str", overrides: "Mapping[str, Any] | None" = None
            ) -> KLineProfile:
    """``base`` (a profile or a :data:`BUILTIN` name) with ``overrides`` applied and checked.

    ``overrides`` may name another base (``{"base": "iso9141_2"}``) and carries the timing
    as a nested mapping (``{"timing": {"p3_min": 0.0}}``). Unknown keys, wrong types and
    the cross-field rules of :func:`validate` raise :class:`ValueError` (at pack load)."""
    overrides = dict(overrides or {})
    if "base" in overrides:
        base = overrides.pop("base")
    if isinstance(base, str):
        if base not in BUILTIN:
            raise ValueError(f"kline.base: unknown profile {base!r} (built-ins: "
                             f"{sorted(BUILTIN)})")
        base = BUILTIN[base]
    if not isinstance(base, KLineProfile):
        raise ValueError(f"kline: base must be a KLineProfile or a name, got {base!r}")
    changes: dict = {}
    for k, v in overrides.items():
        if k == "timing":
            changes["timing"] = _timing(base.timing, v)
        elif k in _PROFILE_FIELDS:
            changes[k] = _coerce(k, v)
        else:
            raise ValueError(f"kline: unknown key {k!r}")
    return validate(dataclasses.replace(base, **changes))


# ------------------------------------------------------------------ built-ins -- #

BUILTIN: Mapping[str, KLineProfile] = MappingProxyType({
    "iso9141_2": validate(KLineProfile(
        name="iso9141_2", framing="iso9141", init="5baud", init_address=0x33,
        target=0x33, source=0xF1, header="iso9141", length="none",
        keepalive=b"\x01\x00", release=None)),
    "kwp2000_slow": validate(KLineProfile(
        name="kwp2000_slow", framing="kwp2000", init="5baud", init_address=0x33,
        header="auto", length="auto", keepalive=b"\x3E\x01", release=b"\x82")),
    "kwp2000_fast": validate(KLineProfile(
        name="kwp2000_fast", framing="kwp2000", init="fast", init_address=0x33,
        init_functional=True, header="auto", length="auto", keepalive=b"\x3E\x01",
        release=b"\x82")),
})

# ``ModuleSpec.init`` → the built-in a pack module starts from.
BASE_FOR_INIT: Mapping[str, "str | None"] = MappingProxyType({
    "fast": "kwp2000_fast", "slow": "kwp2000_slow", "none": None})


def profile_for_module(module_id: str, address: "int | None", init: str,
                       overrides: "Mapping[str, Any] | None" = None
                       ) -> "KLineProfile | None":
    """The profile of one pack module (``ModuleSpec.kline_profile``): the base from
    ``init`` (unless ``overrides`` names one), ``init_address``/``target`` from
    ``address``, then ``overrides``; named after the module. ``init="none"`` (and no
    ``base`` override) → None."""
    overrides = dict(overrides or {})
    base = overrides.pop("base", None) or BASE_FOR_INIT.get(init)
    if base is None:
        if init not in BASE_FOR_INIT:
            raise ValueError(f"module {module_id}: unknown init {init!r}")
        return None
    changes: dict = {"name": module_id}
    if address is not None:
        changes.update(init_address=address, target=address)
    changes.update(overrides)
    return resolve(base, changes)


__all__ = ["Timing", "KLineProfile", "BUILTIN", "BASE_FOR_INIT", "CHECKSUMS", "checksum",
           "checksum_sum8", "checksum_xor", "checksum_twos_complement", "resolve",
           "validate", "profile_for_module"]
