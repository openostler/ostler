"""Fault-code **meaning** store — what each DTC means, in plain English.

The module decoders (:mod:`d2diag.td5.faults`, :mod:`d2diag.slabs.faults`,
:mod:`d2diag.airbag.faults`) already turn a raw status block into a stable **key + name**
per fault. This layer adds the *meaning* — description, likely cause, severity, the ECU
system, and an inferred OBD-II P-code — without bloating the decoders, exactly as
:mod:`d2diag.signals` separates field data from the comms core.

One ``dtc/<module>.json`` per ECU, a JSON array of records keyed by that module's stable
fault key:

* **td5** — ``"offset.bit"`` (matches ``td5/faultmap.json`` and the generic
  ``byte<off>.bit<n>`` the decoder emits for unmapped bits).
* **slabs** — the reference-tool display number (``"020"``).
* **airbag** — the fault number.

Meanings are documented facts (factory/community/vendor sources), carried with a
``source`` note. They are NOT gated by the signal store's ``proven``/``candidate`` rule —
that rule governs whether a *bit→fault mapping* is verified on the car, which lives with the
decoder. A meaning can be refined freely as better descriptions are found.

This is what Land Rover's RAVE fault-finding section gave, rebuilt as a searchable store:
``tools/gen_fault_docs.py`` renders it to a browsable doc, and the web ``/faults`` endpoint
serves it to the dashboard so a live fault shows its meaning, not just a code.
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class FaultMeaning:
    """The meaning of one fault code."""

    key: str                 # module-stable key: "offset.bit" (td5) / number (slabs/airbag)
    name: str                # short fault name (matches the decoder's output)
    description: str = ""     # what the fault means, plain English
    cause: str = ""           # likely cause / what to check
    severity: str = ""        # "current" | "logged" | "info" (blank = unspecified)
    system: str = ""          # engine / fuelling / brakes / body / comms …
    pcode: str = ""           # inferred OBD-II P-code, where one applies ("" = none)
    source: str = ""          # provenance of the meaning text

    def as_dict(self) -> "dict":
        return {k: v for k, v in self.__dict__.items() if v != ""}


def _path(module: str) -> Path:
    return _DIR / f"{module}.json"


def load_records(module: str) -> "list[dict]":
    """Raw JSON records for a module (empty list if the file is missing)."""
    p = _path(module)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


_CACHE: "dict[str, dict[str, FaultMeaning]]" = {}


def load_meanings(module: str) -> "dict[str, FaultMeaning]":
    """Load a module's fault meanings as ``{key: FaultMeaning}`` (cached per module)."""
    if module not in _CACHE:
        _CACHE[module] = {
            r["key"]: FaultMeaning(
                key=r["key"], name=r.get("name", ""), description=r.get("description", ""),
                cause=r.get("cause", ""), severity=r.get("severity", ""),
                system=r.get("system", ""), pcode=r.get("pcode", ""), source=r.get("source", ""),
            )
            for r in load_records(module)
        }
    return _CACHE[module]


def meaning(module: str, key: str) -> "FaultMeaning | None":
    """Look up one fault's meaning by its module key (``None`` if unknown)."""
    return load_meanings(module).get(key)


def upsert_meaning(module: str, record: dict) -> None:
    """Write a meaning to the store (keyed on ``key``); atomic rewrite, cache invalidated."""
    rec = {k: v for k, v in record.items() if v not in (None, "")}
    if "key" not in rec or "name" not in rec:
        raise ValueError("a fault meaning needs at least 'key' and 'name'")
    rows = load_records(module)
    for i, r in enumerate(rows):
        if r.get("key") == rec["key"]:
            rows[i] = rec
            break
    else:
        rows.append(rec)
    p = _path(module)
    fd, tmp = tempfile.mkstemp(dir=str(_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, p)
        _CACHE.pop(module, None)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def enrich(module: str, decoded: "list[str]") -> "list[dict]":
    """Join a decoder's output to its meanings.

    ``decoded`` is what a module's ``decode_faults`` returns — for td5 a list of names
    (and ``byte<off>.bit<n>`` for unmapped bits); for slabs ``"<nr>: <text>"`` strings.
    Returns one dict per fault: ``{raw, key, name, description, cause, severity, system,
    pcode}`` with meaning fields filled where known, so an unmapped or meaning-less fault is
    still passed through (never dropped).
    """
    meanings = load_meanings(module)
    by_name = {m.name: m for m in meanings.values()}
    out: "list[dict]" = []
    for raw in decoded:
        m = _match(raw, module, meanings, by_name)
        row = {"raw": raw, "key": m.key if m else "", "name": m.name if m else raw}
        if m:
            for fld in ("description", "cause", "severity", "system", "pcode"):
                val = getattr(m, fld)
                if val:
                    row[fld] = val
        out.append(row)
    return out


def _match(raw, module, meanings, by_name) -> "FaultMeaning | None":
    """Resolve one decoded fault string to a FaultMeaning via its module key or name."""
    if raw in by_name:                       # td5: decoder emits the name directly
        return by_name[raw]
    if raw.startswith("byte") and "." in raw:  # td5 generic: byte<off>.bit<n> → "off.bit"
        try:
            off = int(raw[4:raw.index(".bit")])
            bit = int(raw[raw.index(".bit") + 4:])
            return meanings.get(f"{off}.{bit}")
        except ValueError:
            return None
    if ":" in raw:                           # slabs: "<nr>: <text>" → number key
        return meanings.get(raw.split(":", 1)[0].strip())
    return meanings.get(raw)                  # fall back to a direct key hit
