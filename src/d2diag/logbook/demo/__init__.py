"""The committed synthetic demo logs, built by ``tools/make_demo_session.py``.

"Demo log 1" (``20261005T090000Z``, Rannoch Moor) and "Demo log 2" (``20261004T153000Z``,
north Dartmoor, SLABS). Never edit the files here by hand: regenerate them. Each route is
a parametric loop over empty moorland, not a real drive (ADR-0009, ADR-0011). They are
read-only and the only sessions the public server lists.
"""
import os

DEMO_ROOT = os.path.dirname(os.path.abspath(__file__))
