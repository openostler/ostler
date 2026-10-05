"""Discovery 2 Td5 — open, modular diagnostics platform.

Layering (each layer decoupled, built bottom-up):

    Transport  →  K-Line  →  KWP2000  →  Td5

Right now only the transport layer exists. See README.
"""
__version__ = "0.0.1"

# Phase 0 (ADR-0013): the Discovery 2 code moved to ``d2diag.vehicles.lr_d2``; the old
# import paths resolve to the same module objects.
from . import _compat as _compat  # noqa: E402

_compat.install()
