"""The committed synthetic demo logs, now shipped by the vehicle pack (ADR-0013).

``DEMO_ROOT`` resolves lazily to ``active_pack().demo.sessions_dir`` (``None`` when the
pack has no demo). For the Discovery 2 pack that is
``d2diag/vehicles/lr_d2/demo/sessions/``: "Demo log 1" (``20261005T090000Z``, Rannoch
Moor) and "Demo log 2" (``20261004T153000Z``, north Dartmoor, SLABS), built by
``tools/make_demo_session.py``. Never edit those files by hand: regenerate them. Each route
is a parametric loop over empty moorland, not a real drive (ADR-0009, ADR-0011). They are
read-only and the only sessions the public server lists.
"""
from __future__ import annotations


def demo_root() -> "str | None":
    """The active pack's demo session directory, or None if it ships no demo."""
    from ...pack import active_pack

    demo = active_pack().demo
    return str(demo.sessions_dir) if demo is not None else None


def __getattr__(name: str):
    if name == "DEMO_ROOT":
        return demo_root()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
